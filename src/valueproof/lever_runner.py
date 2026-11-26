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
