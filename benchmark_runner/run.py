"""Corrida de un modelo contra el benchmark: render -> answer -> score -> report."""

from __future__ import annotations

import json
from pathlib import Path

from .adapters import Adapter
from .load_case import load_case
from .prompts import render_prompt
from .report import build_report
from .score_case import aggregate_model, score_case
from .taxonomy import ROOT
from .validate_case import discover_cases


def run_case(adapter: Adapter, case_dir: str | Path) -> dict:
    """Corre el adaptador sobre todas las renderings de un caso y lo puntúa.

    Robusto a errores por llamada: si una rendering falla (rate limit, timeout,
    etc.) se registra y se sigue. Si TODAS fallan, el caso queda marcado con
    ``error`` y se excluye de la agregación (no se confunde con "modelo malo").
    """
    case = load_case(case_dir)
    outputs_by_rendering: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for rendering in case.task.get("available_renderings", ["fhir_json"]):
        try:
            prompt = render_prompt(case, rendering)
            outputs_by_rendering[rendering] = adapter.answer(case, rendering, prompt)
        except Exception as exc:  # noqa: BLE001 — cualquier fallo del adaptador
            errors[rendering] = f"{type(exc).__name__}: {exc}"[:200]

    if not outputs_by_rendering:
        return {
            "case_id": case.case_id,
            "capability_id": case.ground_truth.get("capability_id"),
            "error": "; ".join(f"{r}: {e}" for r, e in errors.items())[:400],
            "CC": None, "FV": None, "SF": None, "TRC": None, "SR": None, "overall": None,
        }

    card = score_case(case.ground_truth, case.scoring, outputs_by_rendering)
    if errors:
        card["partial_errors"] = errors
    return card


def run_case_sampled(adapter: Adapter, case_dir: str | Path, n_samples: int) -> dict:
    """Corre un caso ``n_samples`` veces y agrega la varianza del overall.

    Necesario para modelos no determinísticos: una sola corrida no es confiable.
    Devuelve el scorecard de la última muestra exitosa enriquecido con
    overall_mean / overall_std / overall_min / overall_max / n_samples.
    """
    cards = [run_case(adapter, case_dir) for _ in range(max(1, n_samples))]
    scored = [c for c in cards if c.get("error") is None]
    base = (scored or cards)[-1]
    if not scored:
        return base
    overalls = [c["overall"] for c in scored]
    mean = sum(overalls) / len(overalls)
    var = sum((o - mean) ** 2 for o in overalls) / len(overalls)
    n_perfect = sum(1 for o in overalls if o >= 100)
    base = dict(base)
    base.update({
        "overall": round(mean),
        "overall_mean": mean,
        "overall_std": round(var ** 0.5, 1),
        "overall_min": min(overalls),          # peor caso: lo que ves en producción
        "overall_max": max(overalls),
        "pass_rate": round(100 * n_perfect / len(scored)),  # % de corridas perfectas
        "n_samples": len(scored),
        "samples": overalls,
    })
    return base


def run_model(adapter: Adapter, cases_dir: str | Path | None = None,
              n_samples: int = 1) -> dict:
    """Corre el adaptador sobre todos los casos y agrega un scorecard de modelo.

    Con ``n_samples`` > 1, cada caso se corre varias veces (captura la varianza
    de modelos no determinísticos). Los casos con error se excluyen de la media.
    """
    cases = discover_cases(cases_dir or (ROOT / "cases"))
    if n_samples > 1:
        per_case = [run_case_sampled(adapter, c, n_samples) for c in cases]
    else:
        per_case = [run_case(adapter, c) for c in cases]
    scored = [c for c in per_case if c.get("error") is None]
    aggregate = aggregate_model(scored)
    errored = [c for c in per_case if c.get("error") is not None]
    # Métricas de consistencia (cuando n_samples > 1): lo que predice errores
    # de producción mejor que la media — tasa de aprobación y peor caso.
    stds = [c["overall_std"] for c in scored if c.get("overall_std") is not None]
    prates = [c["pass_rate"] for c in scored if c.get("pass_rate") is not None]
    worst = [c["overall_min"] for c in scored if c.get("overall_min") is not None]
    return {
        "model": adapter.name,
        "aggregate": aggregate,
        "cases": per_case,
        "n_errored": len(errored),
        "n_scored": len(scored),
        "n_samples": n_samples,
        "mean_overall_std": round(sum(stds) / len(stds), 1) if stds else 0.0,
        "pass_rate": round(sum(prates) / len(prates)) if prates else None,
        "worst_case": min(worst) if worst else None,
    }


def write_results(results: dict, out_dir: str | Path | None = None) -> tuple[Path, Path]:
    out_dir = Path(out_dir or (ROOT / "results"))
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = results["model"].replace(":", "_").replace("/", "_")
    json_path = out_dir / f"{safe}.json"
    md_path = out_dir / f"{safe}.md"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_report(results), encoding="utf-8")
    return json_path, md_path
