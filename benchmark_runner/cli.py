"""CLI del runner.

  python -m benchmark_runner.cli validate cases/pf-fhir-agent-0001
  python -m benchmark_runner.cli validate-all
  python -m benchmark_runner.cli score cases/pf-fhir-agent-0001 submission.json
  python -m benchmark_runner.cli generate --out cases/pf-fhir-agent-0901 --seed 7
"""

from __future__ import annotations

import argparse
import json
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


def cmd_score(args: argparse.Namespace) -> int:
    """Puntúa un caso a partir de un archivo de submission.

    El submission JSON puede ser:
      - {rendering: model_output, ...}  (un output por rendering), o
      - un único model_output, que se aplica a todas las renderings del caso.
    """
    from .load_case import load_case
    from .score_case import score_case

    case = load_case(args.case_dir)
    submission = json.loads(Path(args.submission).read_text(encoding="utf-8"))

    renderings = case.task.get("available_renderings", ["fhir_json"])
    if isinstance(submission, dict) and set(submission) <= set(renderings):
        outputs = submission
    else:
        outputs = {r: submission for r in renderings}

    scorecard = score_case(case.ground_truth, case.scoring, outputs)
    print(f"Scorecard — {case.case_id} ({case.task['capability']['id']})")
    for dim in ("CC", "FV", "SF", "TRC", "SR"):
        val = scorecard.get(dim)
        print(f"  {dim:4} {'· n/a' if val is None else round(val):>4}")
    print(f"  {'Overall':4} {scorecard.get('overall')}")
    if args.json:
        print(json.dumps(scorecard, ensure_ascii=False, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from .adapters import AnthropicAdapter, get_adapter
    from .run import run_model, write_results

    adapter = get_adapter(args.model)
    if isinstance(adapter, AnthropicAdapter) and not adapter.available:
        print("Adaptador Anthropic no disponible: falta ANTHROPIC_API_KEY o el SDK. "
              "Probá --model oracle o --model empty.", file=sys.stderr)
        return 1

    results = run_model(adapter, args.cases_dir)
    json_path, md_path = write_results(results, args.out)
    agg = results["aggregate"]
    print(f"Modelo: {results['model']} · {agg.get('n_cases', 0)} casos")
    for dim in ("CC", "FV", "SF", "TRC", "SR"):
        v = agg.get(dim)
        print(f"  {dim:4} {'· n/a' if v is None else round(v):>4}")
    print(f"  Overall {round(agg['overall']) if agg.get('overall') is not None else 'n/a'}")
    print(f"Reporte: {md_path}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    from generator.emit_case import emit_case

    case_id = args.case_id or Path(args.out).name
    out = emit_case(args.out, seed=args.seed, case_id=case_id,
                    n_active=args.n_active, n_stopped=args.n_stopped)
    print(f"Caso generado en {out}")
    return 0 if _report(Path(out)) else 1


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

    p_score = sub.add_parser("score", help="Puntúa un caso con un submission JSON")
    p_score.add_argument("case_dir")
    p_score.add_argument("submission", help="JSON con el/los output(s) del modelo")
    p_score.add_argument("--json", action="store_true", help="Imprime el scorecard completo en JSON")
    p_score.set_defaults(func=cmd_score)

    p_run = sub.add_parser("run", help="Corre un modelo contra el benchmark y emite un reporte")
    p_run.add_argument("--model", default="oracle",
                       help="oracle | empty | anthropic[:<model>]")
    p_run.add_argument("--cases-dir", default=None)
    p_run.add_argument("--out", default=None, help="Carpeta de resultados (default: results/)")
    p_run.set_defaults(func=cmd_run)

    p_gen = sub.add_parser("generate", help="Genera un caso sintético (MR-01)")
    p_gen.add_argument("--out", required=True, help="Carpeta destino del caso")
    p_gen.add_argument("--seed", type=int, required=True)
    p_gen.add_argument("--case-id", default=None, help="Default: nombre de la carpeta --out")
    p_gen.add_argument("--n-active", type=int, default=3)
    p_gen.add_argument("--n-stopped", type=int, default=1)
    p_gen.set_defaults(func=cmd_generate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
