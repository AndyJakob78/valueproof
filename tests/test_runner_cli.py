import json
import shutil
import subprocess
import sys
from pathlib import Path

from valueproof import Run, Score, check_quality, estimate, rate_checks, print_table, run_levers, save, summarize
from valueproof.cli import main

ROOT = Path(__file__).resolve().parent.parent


def test_run_levers_table_and_files(tmp_path, capsys):
    cases = ["a", "b"]
    setups = {
        "base": lambda c: Run("x" + c, 0.01, 1.0, "single"),
        "new": lambda c: Run("y" + c, 0.002, 0.5, "rescue" if c == "b" else "scout"),
    }
    report = run_levers(cases, setups, judge=lambda c, t: Score(30, 40))
    assert len(report.rows) == 4 and all(r.score.points == 30 for r in report.rows)
    print_table(report, list(setups))
    out = capsys.readouterr().out
    assert "-80%" in out and "1/2" in out and "cost/outcome" in out
    save(report, cases, tmp_path, describe=str)
    assert len(json.loads((tmp_path / "results.json").read_text())) == 4
    assert (tmp_path / "blind_review.csv").exists() and (tmp_path / "blind_key.csv").exists()


def test_cost_per_outcome_counts_failures_as_spent_but_not_delivered():
    setups = {
        "base": lambda c: Run("ok", 0.01, 1.0),
        "cheap": lambda c: Run("bad" if c == "b" else "ok", 0.002, 1.0, final_check="too short" if c == "b" else None),
    }
    judge = lambda c, t: Score(30, 40, hard_failure=(c == "c"))
    s = {x["setup"]: x for x in summarize(run_levers(["a", "b", "c", "d"], setups, judge=judge), list(setups))}
    # base: 4 x 0.01 spent, request "c" has a hard failure -> 3 outcomes
    assert s["base"]["outcomes"] == 3 and abs(s["base"]["cost_per_outcome"] - 0.04 / 3) < 1e-12
    # cheap: "b" fails the check, "c" has a hard failure -> 2 outcomes for 0.008
    assert s["cheap"]["outcomes"] == 2 and abs(s["cheap"]["cost_per_outcome"] - 0.004) < 1e-12


def test_init_then_compare(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["init", "my_test.py"])
    main(["compare", "my_test.py", "--out", str(tmp_path / "out")])
    out = capsys.readouterr().out
    assert "Scout & Rescue" in out and "1/3" in out  # the fake cheap model fails one request
    assert (tmp_path / "out" / "results.json").exists()


def test_bundled_examples_run_offline(tmp_path):
    results = ROOT / "examples" / "results"
    before = set(results.iterdir()) if results.exists() else set()
    for args in (["examples/demo_support.py"], ["examples/test_levers_support.py", "--hard"]):
        r = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
    for new in set(results.iterdir()) - before:  # remove only what this test wrote
        shutil.rmtree(new)


def test_max_spend_stops_between_cases_and_keeps_pairs():
    setups = {"a": lambda c: Run("x", 0.01, 0.1), "b": lambda c: Run("y", 0.02, 0.1)}
    report = run_levers(list(range(10)), setups, max_spend=0.05)
    # each case costs 0.03; after 2 cases (0.06) no new case starts
    assert len({r.case for r in report.rows}) == 2 and len(report.rows) == 4
    assert report.stopped and abs(report.spent_usd - 0.06) < 1e-12


def test_review_skipped_when_it_would_pass_the_limit():
    setups = {"a": lambda c: Run("x" + str(c), 0.01, 0.1)}
    report = run_levers([1, 2], setups, judge=lambda c, t: Score(30, 40, cost_usd=0.05), max_spend=0.04)
    assert all(r.score is None for r in report.rows) and "review" in report.stopped


def test_estimate_projects_from_a_sample():
    setups = {"a": lambda c: Run("x", 0.01, 0.1), "b": lambda c: Run("y", 0.03, 0.1)}
    e = estimate(list(range(50)), setups, judge=lambda c, t: Score(30, 40, cost_usd=0.005), sample=2)
    # per case: 0.04 runs + 2 reviews x 0.005 = 0.05 -> 50 cases = 2.50
    assert e["sample_cases"] == 2 and abs(e["projected_total"] - 2.5) < 1e-9


def test_rejection_reasons_are_grouped(capsys):
    reasons = ["does not cite §1", "does not cite §5, §6", None, "too short"]
    setups = {"s&r": lambda c: Run("t", 0.01, 0.1, "rescue" if reasons[c] else "scout",
                                    rejected_because=reasons[c])}
    report = run_levers(list(range(4)), setups)
    s = summarize(report, ["s&r"])[0]
    assert s["first_try_rejections"]["does not cite #"] == 2 and s["first_try_pass"] == 1
    print_table(report, ["s&r"])
    assert "does not cite # (2)" in capsys.readouterr().out


def test_check_quality_counts_caught_missed_and_false_alarms(capsys):
    # request: (text, check verdict, judge points, judge hard failure) for the cheap setup
    cheap = {0: ("a", None, 36, False),          # fine, passed
             1: ("b", "too short", 20, True),    # bad, caught
             2: ("c", None, 22, True),           # bad, missed
             3: ("d", "no id", 35, False),       # fine, false alarm
             4: ("e", None, 30, False)}          # passed, but clearly weaker than the baseline
    setups = {"base": lambda c: Run("base" + str(c), 0.01, 0.1),
              "cheap": lambda c: Run(cheap[c][0], 0.001, 0.1, final_check=cheap[c][1])}
    def judge(c, text):
        if text.startswith("base"):
            return Score(36, 40)
        _, _, pts, hard = cheap[c]
        return Score(pts, 40, hard)
    report = run_levers(list(range(5)), setups, judge=judge)
    q = check_quality(report, list(setups))
    assert (q["hard_failures"], q["caught"], q["missed"], q["false_alarms"]) == (2, 1, 1, 1)
    assert (q["weaker"], q["weaker_flagged"]) == (3, 1)  # b, c and e are 5+ points below; only b was flagged
    print_table(report, list(setups))
    assert "caught 1, missed 1" in capsys.readouterr().out
    assert check_quality(run_levers([0], setups), list(setups)) is None  # no judge, no verdict


def test_rate_checks_compares_candidates_and_counts_their_cost():
    setups = {"base": lambda c: Run("good", 0.01, 0.1), "cheap": lambda c: Run("bad" if c == 1 else "fine", 0.001, 0.1)}
    judge = lambda c, text: Score(10 if text == "bad" else 36, 40, hard_failure=(text == "bad"))
    report = run_levers([0, 1], setups, judge=judge)
    before = report.spent_usd
    ratings = rate_checks(report, [0, 1], list(setups), {
        "blind check": lambda case, text: None,
        "sharp check": lambda case, text: ("is bad", 0.002) if text == "bad" else (None, 0.002),
    })
    assert (ratings["blind check"]["caught"], ratings["blind check"]["missed"]) == (0, 1)
    assert (ratings["sharp check"]["caught"], ratings["sharp check"]["missed"], ratings["sharp check"]["false_alarms"]) == (1, 0, 0)
    assert abs(report.spent_usd - before - 0.008) < 1e-12  # 4 distinct replies x 0.002
