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
    """Corre el adaptador sobre todas las renderings de un caso y lo puntúa."""
    case = load_case(case_dir)
    outputs_by_rendering: dict[str, dict] = {}
    for rendering in case.task.get("available_renderings", ["fhir_json"]):
        prompt = render_prompt(case, rendering)
        outputs_by_rendering[rendering] = adapter.answer(case, rendering, prompt)
    return score_case(case.ground_truth, case.scoring, outputs_by_rendering)


def run_model(adapter: Adapter, cases_dir: str | Path | None = None) -> dict:
    """Corre el adaptador sobre todos los casos y agrega un scorecard de modelo."""
    cases = discover_cases(cases_dir or (ROOT / "cases"))
    per_case = [run_case(adapter, c) for c in cases]
    aggregate = aggregate_model(per_case)
    return {"model": adapter.name, "aggregate": aggregate, "cases": per_case}


def write_results(results: dict, out_dir: str | Path | None = None) -> tuple[Path, Path]:
    out_dir = Path(out_dir or (ROOT / "results"))
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = results["model"].replace(":", "_").replace("/", "_")
    json_path = out_dir / f"{safe}.json"
    md_path = out_dir / f"{safe}.md"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_report(results), encoding="utf-8")
    return json_path, md_path
