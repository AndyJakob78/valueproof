import json
import shutil
import subprocess
import sys
from pathlib import Path

from costproof import Run, Score, print_table, run_levers, save, summarize
from costproof.cli import main

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
