"""CLI del runner.

  python -m benchmark_runner.cli validate cases/pf-fhir-agent-0001
  python -m benchmark_runner.cli validate-all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .taxonomy import ROOT
from .validate_case import discover_cases, validate_case


def _report(case_dir: Path) -> bool:
    errors = validate_case(case_dir)
    if errors:
        print(f"✗ {case_dir.name}")
        for e in errors:
            print(f"    - {e}")
        return False
    print(f"✓ {case_dir.name}")
    return True


def cmd_validate(args: argparse.Namespace) -> int:
    return 0 if _report(Path(args.case_dir)) else 1


def cmd_validate_all(args: argparse.Namespace) -> int:
    cases = discover_cases(args.cases_dir or (ROOT / "cases"))
    if not cases:
        print("No se encontraron casos.", file=sys.stderr)
        return 1
    ok = sum(_report(c) for c in cases)
    print(f"\n{ok}/{len(cases)} casos válidos.")
    return 0 if ok == len(cases) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="benchmark-runner",
                                     description="FHIR Agent Benchmark — runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Valida un caso")
    p_val.add_argument("case_dir")
    p_val.set_defaults(func=cmd_validate)

    p_all = sub.add_parser("validate-all", help="Valida todos los casos en cases/")
    p_all.add_argument("--cases-dir", default=None)
    p_all.set_defaults(func=cmd_validate_all)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
