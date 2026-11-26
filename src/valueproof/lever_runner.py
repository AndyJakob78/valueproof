"""Lever runner: test one change (a "lever") against your current setup on the
same requests, at the same time, and print a keep-or-drop table.

You give it:
    cases   - a list of test requests (any objects)
    setups  - {name: run(case) -> Run}; the first one is the baseline
    judge   - optional: judge(case, text) -> Score, for a blind quality review

Every case runs through every setup before the next case starts (in a shuffled
order), so all setups see the same moment - same web, same API load.
The judge sees one reply at a time and never the setup's name.
"""

from __future__ import annotations

import csv
import json
import random
import re
import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


@dataclass
class Run:
    text: str
    cost_usd: float
    seconds: float
    path: str = "single"  # "scout", "rescue" or "single"
    final_check: Optional[str] = None  # None if the final text passes your check
    rejected_because: Optional[str] = None  # why the first attempt failed its check, if it did


@dataclass
class Score:
    points: int  # on your fixed rubric
    max_points: int
    hard_failure: bool = False  # wrong policy, invented promise, no answer ...
    note: str = ""
    cost_usd: float = 0.0  # what the review itself cost, if a model did it


@dataclass
class Row:
    case: int
    setup: str
    run: Run
    score: Optional[Score] = None


@dataclass
class Report:
    rows: list[Row] = field(default_factory=list)
    spent_usd: float = 0.0  # runs plus reviews
    stopped: Optional[str] = None  # why the run stopped early, if it did

    def for_setup(self, name: str) -> list[Row]:
        return [r for r in self.rows if r.setup == name]


def run_levers(
    cases: list[Any],
    setups: dict[str, Callable[[Any], Run]],
    judge: Optional[Callable[[Any, str], Score]] = None,
    seed: int = 1,
    max_spend: Optional[float] = None,
) -> Report:
    """Run every setup on every case, then review blind.

    max_spend (USD): stop starting new cases once runs have spent this much, and
    skip the review if it would push past it. A case in progress is finished, so
    the results stay paired. The table then covers the finished cases only.
    """
    rng = random.Random(seed)
    report = Report()
    for i, case in enumerate(cases):
        if max_spend is not None and report.spent_usd >= max_spend:
            report.stopped = f"spend limit ${max_spend:.2f} reached after {i} of {len(cases)} cases"
            print(f"  STOPPED: {report.stopped}", flush=True)
            break
        names = list(setups)
        rng.shuffle(names)  # no setup always goes first
        for name in names:
            run = setups[name](case)
            report.spent_usd += run.cost_usd
            report.rows.append(Row(i, name, run))
        print(f"  case {i + 1}/{len(cases)} done, ${report.spent_usd:.4f} spent", flush=True)

    if judge:
        # Score each distinct reply once, in random order, without the setup name.
        unique = {(r.case, r.run.text) for r in report.rows}
        order = sorted(unique)
        rng.shuffle(order)
        scores = {}
        for n, (i, text) in enumerate(order, 1):
            if max_spend is not None and report.spent_usd >= max_spend:
                report.stopped = f"spend limit ${max_spend:.2f} reached during the review; no quality scores shown"
                print(f"  STOPPED: {report.stopped}", flush=True)
                scores = None
                break
            scores[(i, text)] = judge(cases[i], text)
            report.spent_usd += scores[(i, text)].cost_usd
            print(f"  reviewed {n}/{len(order)}", flush=True)
        if scores is not None:
            for r in report.rows:
                r.score = scores[(r.case, r.run.text)]
    return report


def load_report(path: Path) -> Report:
    """Read a results.json written by save(). Lets you rate new eval checks on replies you already paid for."""
    report = Report()
    for r in json.loads(Path(path).read_text()):
        run = Run(**{k: v for k, v in r["run"].items() if k in Run.__dataclass_fields__})
        score = Score(**{k: v for k, v in r["score"].items() if k in Score.__dataclass_fields__}) if r.get("score") else None
        report.rows.append(Row(r["case"], r["setup"], run, score))
    return report


def estimate(
    cases: list[Any],
    setups: dict[str, Callable[[Any], Run]],
    judge: Optional[Callable[[Any, str], Score]] = None,
    sample: int = 2,
) -> dict:
    """Run the first `sample` cases for real and project the cost of the full run.

    This spends a little money on purpose: a real call is the only reliable price.
    """
    trial = run_levers(cases[:sample], setups, judge)
    done = len({r.case for r in trial.rows})
    per_case = trial.spent_usd / done if done else 0.0
    return {"sample_cases": done, "sample_spent": trial.spent_usd, "per_case": per_case,
            "projected_total": per_case * len(cases), "cases": len(cases)}


def is_outcome(row: Row) -> bool:
    """A request counts as an outcome when the final result passes your check and,
    if a judge ran, has no hard failure - the result a user could actually rely on."""
    return row.run.final_check is None and not (row.score and row.score.hard_failure)


def _reason(text: str) -> str:
    """Group similar reasons: 'does not cite §1, §6' and 'does not cite §5' are the same rule."""
    short = re.sub(r"[§#]?\d[\d.,§ ]*", "#", text)
    return short.strip(" :,")


def summarize(report: Report, setups: list[str]) -> list[dict]:
    """The numbers behind the table, one dict per setup.

    cost_per_outcome = everything the setup spent / requests that ended in an outcome.
    Failed attempts and bad results still cost money, so they raise it.
    """
    out = []
    for name in setups:
        rows = report.for_setup(name)
        costs = [r.run.cost_usd for r in rows]
        outcomes = sum(is_outcome(r) for r in rows)
        scored = [r.score for r in rows if r.score]
        out.append({
            "setup": name,
            "requests": len(rows),
            "avg_cost": statistics.mean(costs),
            "median_cost": statistics.median(costs),
            "outcomes": outcomes,
            "cost_per_outcome": sum(costs) / outcomes if outcomes else float("inf"),
            "rescued": sum(r.run.path == "rescue" for r in rows),
            "avg_seconds": statistics.mean(r.run.seconds for r in rows),
            "check_fail": sum(r.run.final_check is not None for r in rows),
            "quality": sum(s.points for s in scored) if scored else None,
            "quality_max": sum(s.max_points for s in scored) if scored else None,
            "hard_fail": sum(s.hard_failure for s in scored) if scored else None,
            "first_try_pass": sum(r.run.rejected_because is None and r.run.path != "rescue" for r in rows),
            "first_try_rejections": Counter(_reason(r.run.rejected_because) for r in rows if r.run.rejected_because),
            "final_failures": Counter(_reason(r.run.final_check) for r in rows if r.run.final_check),
        })
    return out


def check_quality(report: Report, setups: list[str], weaker_by: float = 0.125,
                  flagged_by: Optional[Callable[[Row], bool]] = None) -> Optional[dict]:
    """How good are your eval checks? Compares each check verdict with the judge's verdict.

    Counted over every distinct reply in the run (the same reply from two setups counts once):
      caught        the check failed a reply the judge called a hard failure
      missed        the check passed a reply the judge called a hard failure   <- the costly case
      false_alarms  the check failed a reply the judge found acceptable        <- pays for a rescue for nothing
    Also: replies clearly weaker than the baseline's reply to the same request (by `weaker_by` of the
    scale or more), and how many of those a check flagged. Returns None if no judge ran.
    """
    scored = [r for r in report.rows if r.score]
    if not scored:
        return None
    base = {r.case: r.score.points for r in scored if r.setup == setups[0]}
    seen, q = set(), dict(replies=0, hard_failures=0, caught=0, missed=0, false_alarms=0, weaker=0, weaker_flagged=0)
    for r in scored:
        key = (r.case, r.run.text)
        if key in seen:
            continue
        seen.add(key)
        flagged = flagged_by(r) if flagged_by else r.run.final_check is not None
        bad = r.score.hard_failure
        q["replies"] += 1
        q["hard_failures"] += bad
        q["caught"] += flagged and bad
        q["missed"] += (not flagged) and bad
        q["false_alarms"] += flagged and not bad
        if r.case in base and base[r.case] - r.score.points >= weaker_by * r.score.max_points:
            q["weaker"] += 1
            q["weaker_flagged"] += flagged
    return q


def rate_checks(report: Report, cases: list[Any], setups: list[str],
                checks: dict[str, Callable[[Any, str], Any]], weaker_by: float = 0.125) -> dict[str, dict]:
    """Try candidate eval checks on every distinct reply of a finished run and rate each against the judge.

    checks: {name: fn(case, text)}; fn returns None if the reply is usable, else a reason -
    or a tuple (that, cost_usd) when the check itself costs money (a model call).
    Lets you compare checks before you build a setup around one.
    """
    ratings = {}
    for name, fn in checks.items():
        verdicts: dict = {}
        cost = 0.0

        def flagged(r: Row) -> bool:
            nonlocal cost
            key = (r.case, r.run.text)
            if key not in verdicts:
                v = fn(cases[r.case], r.run.text)
                if isinstance(v, tuple):
                    v, c = v
                    cost += c
                verdicts[key] = v is not None
                if len(verdicts) % 20 == 0:
                    print(f"    {name}: {len(verdicts)} replies checked", flush=True)
            return verdicts[key]

        q = check_quality(report, setups, weaker_by, flagged)
        if q is None:
            return {}
        q["flagged"], q["cost_usd"] = sum(verdicts.values()), cost
        report.spent_usd += cost
        ratings[name] = q
        print(f"  rated check: {name}", flush=True)
    return ratings


def print_check_ratings(ratings: dict[str, dict]) -> None:
    if not ratings:
        return
    first = next(iter(ratings.values()))
    print(f"\nCandidate eval checks, rated against the judge ({first['replies']} distinct replies, "
          f"{first['hard_failures']} hard failures, {first['weaker']} clearly weaker):")
    print(f"{'check':<34}{'caught':>8}{'missed':>8}{'false alarms':>14}{'weaker flagged':>16}{'cost per check':>16}")
    for name, q in ratings.items():
        per = q["cost_usd"] / q["replies"] * 100 if q["replies"] else 0
        print(f"{name:<34}{q['caught']:>8}{q['missed']:>8}{q['false_alarms']:>14}"
              f"{str(q['weaker_flagged']) + '/' + str(q['weaker']):>16}{per:>14.3f}c")


def lever_ledger(report: Report, levers: dict[str, dict], tolerance: float = 0.01) -> list[dict]:
    """The keep-or-drop ledger: each lever against the setup it changes.

    levers: {setup_name: {"baseline": other_setup_name, "estimate": "what you expected, written before the test"}}
    A lever is kept when it costs less per request, quality did not fall by more than `tolerance` of the
    maximum score (default 1%, about the noise between runs), and it has no more hard failures.
    A lever that costs more but improves quality or removes hard failures is flagged as the owner's call.
    Without a judge the verdict rests on cost alone and says so.
    """
    names = {r.setup for r in report.rows}
    rows = []
    for name, info in levers.items():
        base = info.get("baseline")
        if name not in names or base not in names:
            continue
        s = {x["setup"]: x for x in summarize(report, [base, name])}
        b, l = s[base], s[name]
        cost = l["avg_cost"] / b["avg_cost"] - 1 if b["avg_cost"] else 0.0
        row = {"lever": name, "baseline": base, "estimate": info.get("estimate", ""),
               "cost_change": cost, "seconds_change": l["avg_seconds"] - b["avg_seconds"],
               "rescued": f"{b['rescued']} -> {l['rescued']}", "quality_change": None, "hard_fail_change": None}
        if l["quality"] is not None and b["quality"] is not None:
            row["quality_change"] = l["quality"] - b["quality"]
            row["hard_fail_change"] = l["hard_fail"] - b["hard_fail"]
            held = row["quality_change"] >= -tolerance * l["quality_max"] and row["hard_fail_change"] <= 0
            better = row["quality_change"] > tolerance * l["quality_max"] or row["hard_fail_change"] < 0
            row["verdict"] = ("keep" if cost < 0 and held else "drop: quality fell" if cost < 0
                              else "costs more, buys quality: your call" if better else "drop: not cheaper")
        else:
            row["verdict"] = "cheaper (quality not reviewed)" if cost < 0 else "drop: not cheaper"
        rows.append(row)
    return rows


def ledger_markdown(rows: list[dict]) -> str:
    out = ["| Lever | Against | Estimate before the test | Cost | Time | Rescues | Quality | Hard failures | Verdict |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        q = "not reviewed" if r["quality_change"] is None else f"{r['quality_change']:+d} points"
        h = "" if r["hard_fail_change"] is None else f"{r['hard_fail_change']:+d}"
        out.append(f"| {r['lever']} | {r['baseline']} | {r['estimate']} | {r['cost_change'] * 100:+.0f}% | "
                   f"{r['seconds_change']:+.1f} s | {r['rescued']} | {q} | {h} | **{r['verdict']}** |")
    return "\n".join(out)


def print_ledger(rows: list[dict]) -> None:
    if not rows:
        return
    print("\nLever ledger (each lever against the setup it changes):")
    print(f"{'lever':<28}{'cost':>7}{'time':>8}{'rescues':>10}{'quality':>9}{'hard':>6}  verdict   | estimate before the test")
    for r in rows:
        q = "n/a" if r["quality_change"] is None else f"{r['quality_change']:+d}"
        h = "" if r["hard_fail_change"] is None else f"{r['hard_fail_change']:+d}"
        print(f"{r['lever']:<28}{r['cost_change'] * 100:>+6.0f}%{r['seconds_change']:>+7.1f}s{r['rescued']:>10}{q:>9}{h:>6}"
              f"  {r['verdict']} | {r['estimate']}")


def print_table(report: Report, setups: list[str]) -> None:
    rows = summarize(report, setups)
    base = rows[0]["cost_per_outcome"]
    has_scores = rows[0]["quality"] is not None
    head = (f"{'setup':<26}{'cost/outcome':>13}{'vs base':>9}{'outcomes':>10}{'avg cost':>10}{'median':>9}"
            f"{'rescued':>9}{'avg s':>7}{'check fail':>11}")
    if has_scores:
        head += f"{'quality':>12}{'hard fail':>10}"
    print(head)
    for s in rows:
        cpo = s["cost_per_outcome"]
        vs = f"{(cpo / base - 1) * 100:>+8.0f}%" if cpo != float("inf") and base not in (0, float("inf")) else f"{'-':>9}"
        line = (
            f"{s['setup']:<26}{(f'{cpo * 100:.3f}c' if cpo != float('inf') else 'none'):>13}{vs}"
            f"{s['outcomes']:>6}/{s['requests']:<3}{s['avg_cost'] * 100:>9.3f}c{s['median_cost'] * 100:>8.3f}c"
            f"{s['rescued']:>5}/{s['requests']:<3}{s['avg_seconds']:>7.1f}{s['check_fail']:>11}"
        )
        if has_scores:
            line += f"{s['quality']:>7}/{s['quality_max']:<4}{s['hard_fail']:>10}"
        print(line)
    print("\ncost/outcome = everything spent / requests whose final result passed the check"
          + (" and had no hard failure" if has_scores else "") + ". It is the number to compare.")
    reasons = [s for s in rows if s["first_try_rejections"] or s["final_failures"]]
    if reasons:
        print("\nWhy results were rejected (which check rule fired, most frequent first):")
        for s in reasons:
            print(f"  {s['setup']}: first try passed {s['first_try_pass']}/{s['requests']}")
            for label, counts in (("first try rejected", s["first_try_rejections"]), ("final result failed", s["final_failures"])):
                if counts:
                    top = ", ".join(f"{why} ({n})" for why, n in counts.most_common(5))
                    print(f"    {label}: {top}")
    q = check_quality(report, setups)
    if q:
        print(f"\nHow good are the eval checks? (check verdict vs. the judge, over {q['replies']} distinct replies)")
        print(f"  hard failures: {q['hard_failures']}  ->  caught {q['caught']}, missed {q['missed']}")
        print(f"  false alarms (check failed a reply the judge accepted): {q['false_alarms']}")
        print(f"  replies clearly weaker than '{setups[0]}': {q['weaker']}  ->  flagged by a check: {q['weaker_flagged']}")
        if q["missed"] or q["weaker"] > q["weaker_flagged"]:
            print("  Missed and unflagged replies reach users as they are: write checks for those mistakes.")
    if report.stopped:
        print(f"\nNote: {report.stopped}.")
    print(f"Spent on this run: ${report.spent_usd:.4f}")


def save(report: Report, cases: list[Any], out_dir: Path, describe: Callable[[Any], str]) -> None:
    """Write all results, plus a blind review sheet a person can score by hand."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(
        json.dumps([asdict(r) for r in report.rows], indent=2, ensure_ascii=False)
    )
    rng = random.Random(7)
    rows = report.rows[:]
    rng.shuffle(rows)
    with open(out_dir / "blind_review.csv", "w", newline="") as f, open(out_dir / "blind_key.csv", "w", newline="") as k:
        sheet, key = csv.writer(f), csv.writer(k)
        sheet.writerow(["id", "request", "reply", "your score", "hard failure?"])
        key.writerow(["id", "case", "setup"])
        for n, r in enumerate(rows, 1):
            sheet.writerow([n, describe(cases[r.case]), r.run.text, "", ""])
            key.writerow([n, r.case, r.setup])
