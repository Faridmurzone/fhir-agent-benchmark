"""Ensamblado de una carpeta de caso completa para MR-01.

Escribe ``bundle.json`` + las 3 vistas markdown + ``task.json`` +
``ground_truth.json`` + ``scoring.json``, con ``ground_truth.expected.items``
igual a los medicamentos ACTIVOS (codificados, con evidencia
``[MedicationRequest/<id>]``) y un ``must_exclude`` con los medicamentos
discontinuados. La task y el scoring se rellenan para coincidir con la
taxonomía (output_contract ``entity_list``, dimensiones ``[CC, TRC, SR]``).

Determinismo: mismo seed + mismos parámetros => caso byte-idéntico. El JSON se
serializa con ``sort_keys=False`` pero estructura estable y orden de inserción
fijo, por lo que la salida es reproducible.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .patient_generator import GeneratedPatient, build_patient
from .render import render_all

CAPABILITY_ID = "MR-01"
CAPABILITY_SLUG = "medication_reconciliation.active_medication_list"
OUTPUT_CONTRACT = "entity_list"
DIMENSIONS = ["CC", "TRC", "SR"]
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"


def _med_code(m: dict) -> dict:
    coding = m["medicationCodeableConcept"]["coding"][0]
    return {"system": coding["system"], "code": coding["code"]}


def build_ground_truth(gp: GeneratedPatient, *, case_id: str) -> dict:
    """ground_truth con activos en ``items`` y discontinuados en ``must_exclude``."""
    items = []
    for m in gp.active_medications:
        items.append({
            "label": m["medicationCodeableConcept"]["text"],
            "code": _med_code(m),
            "status": "active",
            "evidence": [f"MedicationRequest/{m['id']}"],
        })

    must_exclude = []
    for m in gp.stopped_medications:
        note = m.get("note", [{}])[0].get("text", "")
        must_exclude.append({
            "label": m["medicationCodeableConcept"]["text"],
            "code": _med_code(m),
            "reason": f"status = {m['status']} ({note})" if note else f"status = {m['status']}",
            "evidence": [f"MedicationRequest/{m['id']}"],
        })

    n_active = len(items)
    n_stopped = len(must_exclude)
    return {
        "case_id": case_id,
        "capability_id": CAPABILITY_ID,
        "output_contract": OUTPUT_CONTRACT,
        "expected": {"items": items, "must_exclude": must_exclude},
        "safety_events": [],
        "notes": (
            f"Synthetic medication reconciliation case. The discriminating skill "
            f"is keeping the {n_active} active medication(s) while excluding the "
            f"{n_stopped} discontinued one(s). No safety hazards present, so SF "
            f"should be 100 for any answer that does not fabricate a hazard."
        ),
    }


def build_task(gp: GeneratedPatient, *, case_id: str) -> dict:
    p = gp.patient
    birth_year = int(p["birthDate"][:4])
    age = 2025 - birth_year
    cond_names = [c["code"]["text"].lower() for c in gp.conditions]
    cond_text = " and ".join(cond_names) if cond_names else "chronic conditions"

    # resource_types presentes (en orden canónico).
    present: list[str] = []
    for res in gp.resources():
        rt = res["resourceType"]
        if rt not in present:
            present.append(rt)

    return {
        "case_id": case_id,
        "schema_version": "0.1",
        "taxonomy_version": "0.1",
        "capability": {"id": CAPABILITY_ID, "slug": CAPABILITY_SLUG},
        "language": "en",
        "scenario": (
            f"A {age}-year-old {p['gender']} patient with {cond_text}, with "
            f"{len(gp.stopped_medications)} medication(s) discontinued during "
            f"follow-up."
        ),
        "instruction": (
            "List the patient's currently active medications. Exclude any "
            "medication that has been discontinued or stopped. For each active "
            "medication, provide its code and cite the source resource(s) as "
            "evidence."
        ),
        "output_contract": OUTPUT_CONTRACT,
        "available_renderings": ["fhir_json", "narrative", "timeline", "table"],
        "rendering_files": {
            "fhir_json": "bundle.json",
            "narrative": "narrative.md",
            "timeline": "timeline.md",
            "table": "table.md",
        },
        "resource_types": present,
        "tags": ["medication-reconciliation", "active-vs-discontinued",
                 "synthetic", "generated"],
    }


def build_scoring(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "capability_id": CAPABILITY_ID,
        "scoring_version": "0.1",
        "dimensions": DIMENSIONS,
        "options": {
            "label_fallback": False,
            "date_granularity": "day",
            "code_systems_priority": [RXNORM],
        },
    }


def _write_json(path: Path, data: object) -> None:
    # ensure_ascii=False para texto legible; indent=2 + newline final para
    # reproducibilidad byte-a-byte.
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def emit_case(
    out_dir: str | Path,
    *,
    seed: int,
    case_id: str,
    n_active: int = 3,
    n_stopped: int = 1,
) -> Path:
    """Genera la carpeta de caso completa en ``out_dir``. Devuelve la ruta."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    gp = build_patient(seed, n_active=n_active, n_stopped=n_stopped)
    bundle_id = f"{case_id}-bundle"
    views = render_all(gp, bundle_id=bundle_id)

    _write_json(out_dir / "bundle.json", views["bundle"])
    (out_dir / "narrative.md").write_text(views["narrative"], encoding="utf-8")
    (out_dir / "timeline.md").write_text(views["timeline"], encoding="utf-8")
    (out_dir / "table.md").write_text(views["table"], encoding="utf-8")

    _write_json(out_dir / "task.json", build_task(gp, case_id=case_id))
    _write_json(out_dir / "ground_truth.json", build_ground_truth(gp, case_id=case_id))
    _write_json(out_dir / "scoring.json", build_scoring(case_id))

    return out_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generator",
        description="Generador sintético de casos MR-01 para el FHIR Agent Benchmark.",
    )
    parser.add_argument("--out", required=True,
                        help="Directorio de salida del caso (p. ej. cases/pf-fhir-agent-0900).")
    parser.add_argument("--seed", type=int, required=True,
                        help="Semilla entera para la generación determinista.")
    parser.add_argument("--case-id", required=True,
                        help="case_id (debe coincidir con ^pf-fhir-agent-[0-9]{4}$ y el nombre de carpeta).")
    parser.add_argument("--n-active", type=int, default=3,
                        help="Número de medicamentos activos (default 3).")
    parser.add_argument("--n-stopped", type=int, default=1,
                        help="Número de medicamentos discontinuados (default 1).")
    args = parser.parse_args(argv)

    out = emit_case(args.out, seed=args.seed, case_id=args.case_id,
                    n_active=args.n_active, n_stopped=args.n_stopped)
    print(f"Caso generado en {out} (seed={args.seed}, case_id={args.case_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
