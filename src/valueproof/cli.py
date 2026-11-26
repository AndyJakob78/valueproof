"""The `valueproof` command.

    valueproof init my_test.py               # write a starter test that runs offline straight away
    valueproof compare my_test.py            # run every setup on every case, print the table
    valueproof compare my_test.py --live     # your file decides what "live" means (real API calls)
    valueproof compare my_test.py --out dir  # where results and the blind review sheet go
    valueproof compare my_test.py --live --estimate        # run 2 cases, print the projected bill
    valueproof compare my_test.py --live --max-spend 5     # stop once $5 is spent

Your test file is plain Python and defines one function:

    def build(live: bool, args: list[str]) -> dict:
        return {
            "cases":    [...],                       # your test requests
            "setups":   {"baseline": run, ...},     # name -> run(case) -> Run; first is the baseline
            "judge":    judge,                       # optional: judge(case, text) -> Score
            "checks":   {"my new check": fn},        # optional: candidate eval checks to rate, fn(case, text)
            "describe": lambda case: str(case),      # optional: how a case shows on the review sheet
        }

Checks stay in code, inside your setups - that is what makes them reliable.
Any extra arguments after the file are passed to build() as `args`.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

from . import __version__
from .lever_runner import estimate, print_check_ratings, print_table, rate_checks, run_levers, save
from .starter import STARTER


def _load(path: Path):
    sys.path.insert(0, str(path.parent))  # let the test file import its neighbours
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses in the test file need this
    spec.loader.exec_module(module)
    if not hasattr(module, "build"):
        raise SystemExit(f"{path} must define build(live, args) -> dict. See: valueproof compare --help")
    return module


def compare(file: str, live: bool = False, out: str | None = None, extra: list[str] | None = None,
            max_spend: float | None = None, estimate_only: bool = False, sample: int = 2) -> None:
    path = Path(file).resolve()
    spec = _load(path).build(live, extra or [])
    cases, setups, judge = spec["cases"], spec["setups"], spec.get("judge")
    mode = "LIVE" if live else "OFFLINE"
    if estimate_only:
        print(f"{mode} ESTIMATE: running {min(sample, len(cases))} of {len(cases)} cases x {len(setups)} setups for real")
        e = estimate(cases, setups, judge, sample)
        print(f"\nSpent on the sample: ${e['sample_spent']:.4f} for {e['sample_cases']} cases (${e['per_case']:.4f} per case)")
        print(f"Projected full run:  ${e['projected_total']:.2f} for {e['cases']} cases, including the review")
        print("A rough guide: hard cases and rescues cost more. Set a ceiling with --max-spend.")
        return
    limit = f", stops at ${max_spend:.2f}" if max_spend is not None else ""
    print(f"{mode}: {len(cases)} cases x {len(setups)} setups{limit}")
    report = run_levers(cases, setups, judge=judge, max_spend=max_spend)
    if not report.rows:
        print(f"Nothing ran: {report.stopped}")
        return
    print()
    print_table(report, list(setups))
    ratings = rate_checks(report, cases, list(setups), spec["checks"]) if spec.get("checks") and judge else {}
    print_check_ratings(ratings)
    out_dir = Path(out) if out else path.parent / "results" / datetime.now().strftime("%Y%m%d-%H%M%S")
    save(report, cases, out_dir, describe=spec.get("describe", str))
    if ratings:
        (out_dir / "check_ratings.json").write_text(json.dumps(ratings, indent=2))
        print(f"Spent including the check ratings: ${report.spent_usd:.4f}")
    print(f"\nSaved to {out_dir}")


def init(file: str) -> None:
    path = Path(file)
    if path.exists():
        raise SystemExit(f"{path} already exists - pick another name: valueproof init my_test.py")
    path.write_text(STARTER.format(name=path.name))
    print(f"Wrote {path}. Try it: valueproof compare {path}\nThen edit the four parts marked EDIT.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="valueproof", description="Test cheaper AI setups against your current one.")
    parser.add_argument("--version", action="version", version=f"valueproof {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    cmp_ = sub.add_parser("compare", help="run setups side by side and print a keep-or-drop table",
                          description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cmp_.add_argument("file", help="your test file, defining build(live, args)")
    cmp_.add_argument("--live", action="store_true", help="tell build() to use real models")
    cmp_.add_argument("--out", help="folder for results (default: results/<time> next to the file)")
    cmp_.add_argument("--max-spend", type=float, metavar="USD",
                      help="stop starting new cases once this much is spent (runs + review)")
    cmp_.add_argument("--estimate", action="store_true",
                      help="run only a small sample for real and print the projected cost of the full run")
    cmp_.add_argument("--sample", type=int, default=2, help="cases to run for --estimate (default: 2)")
    ini = sub.add_parser("init", help="write a starter test file that runs offline straight away")
    ini.add_argument("file", nargs="?", default="valueproof_test.py", help="file to create (default: valueproof_test.py)")
    args, extra = parser.parse_known_args(argv)
    if args.command == "compare":
        compare(args.file, args.live, args.out, extra, args.max_spend, args.estimate, args.sample)
    elif args.command == "init":
        init(args.file)



def main_mmco(argv: list[str] | None = None) -> None:
    """The old command name. Kept so existing scripts keep working; removed in version 1.0."""
    print("Note: the `mmco` command is now `valueproof`. `mmco` will be removed in version 1.0.", file=sys.stderr)
    main(argv)


if __name__ == "__main__":
    main()
