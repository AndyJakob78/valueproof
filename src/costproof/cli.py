"""The `costproof` command.

    costproof init my_test.py               # write a starter test that runs offline straight away
    costproof compare my_test.py            # run every setup on every case, print the table
    costproof compare my_test.py --live     # your file decides what "live" means (real API calls)
    costproof compare my_test.py --out dir  # where results and the blind review sheet go

Your test file is plain Python and defines one function:

    def build(live: bool, args: list[str]) -> dict:
        return {
            "cases":    [...],                       # your test requests
            "setups":   {"baseline": run, ...},     # name -> run(case) -> Run; first is the baseline
            "judge":    judge,                       # optional: judge(case, text) -> Score
            "describe": lambda case: str(case),      # optional: how a case shows on the review sheet
        }

Checks stay in code, inside your setups - that is what makes them reliable.
Any extra arguments after the file are passed to build() as `args`.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from datetime import datetime
from pathlib import Path

from . import __version__
from .lever_runner import print_table, run_levers, save
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
        raise SystemExit(f"{path} must define build(live, args) -> dict. See: costproof compare --help")
    return module


def compare(file: str, live: bool = False, out: str | None = None, extra: list[str] | None = None) -> None:
    path = Path(file).resolve()
    spec = _load(path).build(live, extra or [])
    cases, setups = spec["cases"], spec["setups"]
    print(f"{'LIVE' if live else 'OFFLINE'}: {len(cases)} cases x {len(setups)} setups")
    report = run_levers(cases, setups, judge=spec.get("judge"))
    print()
    print_table(report, list(setups))
    out_dir = Path(out) if out else path.parent / "results" / datetime.now().strftime("%Y%m%d-%H%M%S")
    save(report, cases, out_dir, describe=spec.get("describe", str))
    print(f"\nSaved to {out_dir}")


def init(file: str) -> None:
    path = Path(file)
    if path.exists():
        raise SystemExit(f"{path} already exists - pick another name: costproof init my_test.py")
    path.write_text(STARTER.format(name=path.name))
    print(f"Wrote {path}. Try it: costproof compare {path}\nThen edit the four parts marked EDIT.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="costproof", description="Test cheaper AI setups against your current one.")
    parser.add_argument("--version", action="version", version=f"costproof {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    cmp_ = sub.add_parser("compare", help="run setups side by side and print a keep-or-drop table",
                          description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cmp_.add_argument("file", help="your test file, defining build(live, args)")
    cmp_.add_argument("--live", action="store_true", help="tell build() to use real models")
    cmp_.add_argument("--out", help="folder for results (default: results/<time> next to the file)")
    ini = sub.add_parser("init", help="write a starter test file that runs offline straight away")
    ini.add_argument("file", nargs="?", default="costproof_test.py", help="file to create (default: costproof_test.py)")
    args, extra = parser.parse_known_args(argv)
    if args.command == "compare":
        compare(args.file, args.live, args.out, extra)
    elif args.command == "init":
        init(args.file)



def main_mmco(argv: list[str] | None = None) -> None:
    """The old command name. Kept so existing scripts keep working; removed in version 1.0."""
    print("Note: the `mmco` command is now `costproof`. `mmco` will be removed in version 1.0.", file=sys.stderr)
    main(argv)


if __name__ == "__main__":
    main()
