"""Generador ADVERSARIAL para MR-01 (lista de medicación activa).

Idea (ver la discusión de diseño): un modelo puede *fallar* una tarea one-shot
que él mismo es capaz de *construir y verificar*. La asimetría generación↔
verificación se explota así:

- El gold es CORRECTO POR CONSTRUCCIÓN: el generador decide el estado de cada
  MedicationRequest, así que "activo" = ``status == "active"`` es verdad por
  definición, no por juicio falible.
- La DIFICULTAD viene de la escala y el ruido one-shot: muchas medicaciones,
  variedad de estados confusos (completed/stopped/on-hold/cancelled/
  entered-in-error/draft), pares de titulación (mismo fármaco, dos potencias,
  distinto estado), repartidas en una historia larga y enterradas en 4
  renderings. El modelo debe extraer EXACTAMENTE el conjunto activo (precisión y
  recall) sobre N ítems.

Determinismo: toda la aleatoriedad pasa por ``random.Random(seed)``; fechas
derivadas de ``BASE_YEAR``. Misma semilla => caso byte-idéntico.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from random import Random

from .patient_generator import GeneratedPatient
from .render import render_all

BASE_YEAR = 2024
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SNOMED = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"

# Catálogo ampliado. Los códigos RxNorm reutilizados en casos publicados están
# verificados contra RxNav; el resto de este catálogo debe pasar
# scripts/verify_terminology.py antes de usar sus casos en resultados publicados.
# Incluye pares de titulación del mismo fármaco a distinta potencia como distractores.
HARD_MED_CATALOG: list[dict] = [
    {"rxnorm": "861007", "text": "Metformin 500 mg", "dosage": "500 mg PO BID"},
    {"rxnorm": "861004", "text": "Metformin 1000 mg", "dosage": "1000 mg PO BID"},
    {"rxnorm": "314076", "text": "Lisinopril 10 mg", "dosage": "10 mg PO daily"},
    {"rxnorm": "314077", "text": "Lisinopril 20 mg", "dosage": "20 mg PO daily"},
    {"rxnorm": "617310", "text": "Atorvastatin 20 mg", "dosage": "20 mg PO QHS"},
    {"rxnorm": "617314", "text": "Atorvastatin 40 mg", "dosage": "40 mg PO QHS"},
    {"rxnorm": "197361", "text": "Amlodipine 5 mg", "dosage": "5 mg PO daily"},
    {"rxnorm": "197362", "text": "Amlodipine 10 mg", "dosage": "10 mg PO daily"},
    {"rxnorm": "866924", "text": "Metoprolol tartrate 25 mg", "dosage": "25 mg PO BID"},
    {"rxnorm": "866516", "text": "Metoprolol tartrate 50 mg", "dosage": "50 mg PO BID"},
    {"rxnorm": "310798", "text": "Hydrochlorothiazide 25 mg", "dosage": "25 mg PO daily"},
    {"rxnorm": "966221", "text": "Levothyroxine 50 mcg", "dosage": "50 mcg PO daily"},
    {"rxnorm": "892244", "text": "Levothyroxine 75 mcg", "dosage": "75 mcg PO daily"},
    {"rxnorm": "198051", "text": "Omeprazole 20 mg", "dosage": "20 mg PO daily"},
    {"rxnorm": "311354", "text": "Pantoprazole 40 mg", "dosage": "40 mg PO daily"},
    {"rxnorm": "310537", "text": "Glyburide 5 mg", "dosage": "5 mg PO daily"},
    {"rxnorm": "861760", "text": "Sitagliptin 100 mg", "dosage": "100 mg PO daily"},
    {"rxnorm": "1539463", "text": "Empagliflozin 10 mg", "dosage": "10 mg PO daily"},
    {"rxnorm": "351250", "text": "Gabapentin 300 mg", "dosage": "300 mg PO TID"},
    {"rxnorm": "856980", "text": "Sertraline 50 mg", "dosage": "50 mg PO daily"},
    {"rxnorm": "312961", "text": "Simvastatin 40 mg", "dosage": "40 mg PO QHS"},
    {"rxnorm": "855332", "text": "Warfarin 5 mg", "dosage": "5 mg PO daily"},
    {"rxnorm": "855288", "text": "Apixaban 5 mg", "dosage": "5 mg PO BID"},
    {"rxnorm": "763025", "text": "Furosemide 40 mg", "dosage": "40 mg PO daily"},
    {"rxnorm": "197517", "text": "Clopidogrel 75 mg", "dosage": "75 mg PO daily"},
    {"rxnorm": "198211", "text": "Prednisone 20 mg", "dosage": "20 mg PO daily"},
    {"rxnorm": "905395", "text": "Aspirin 81 mg", "dosage": "81 mg PO daily"},
    {"rxnorm": "311036", "text": "Losartan 50 mg", "dosage": "50 mg PO daily"},
]

# Estados no-activos (confusos a propósito). Solo "active" cuenta para el gold.
_INACTIVE_STATUSES = ["completed", "stopped", "on-hold", "cancelled",
                      "entered-in-error", "draft"]
_GIVEN_NAMES = ["Maria", "John", "Aisha", "Carlos", "Elena", "David", "Priya", "Omar"]


def _fmt(d: date) -> str:
    return d.isoformat()


def build_hard_mr01(seed: int, *, n_meds: int = 24, active_frac: float = 0.4) -> GeneratedPatient:
    """Construye un paciente con muchas medicaciones de estados variados.

    Gold por construcción: las medicaciones con ``status == "active"`` son la
    respuesta correcta. ``n_meds`` controla la escala (dificultad).
    """
    rng = Random(seed)
    n_meds = max(4, min(n_meds, len(HARD_MED_CATALOG)))

    pat_id = "pat-001"
    pat_ref = f"Patient/{pat_id}"
    given = _GIVEN_NAMES[seed % len(_GIVEN_NAMES)]
    age = rng.randint(55, 85)
    birth = date(BASE_YEAR - age, rng.randint(1, 12), rng.randint(1, 28))
    patient = {
        "resourceType": "Patient", "id": pat_id, "gender": rng.choice(["female", "male"]),
        "birthDate": _fmt(birth),
        "name": [{"use": "official", "family": "Synthetic", "given": [given]}],
    }

    # Historia larga: varios encuentros a lo largo de ~3 años.
    n_enc = 6
    enc_dates = []
    d = date(BASE_YEAR, 1, 10)
    for _ in range(n_enc):
        enc_dates.append(d)
        d = d + timedelta(days=rng.randint(120, 210))
    encounters = [{
        "resourceType": "Encounter", "id": f"enc-{i+1:03d}", "status": "finished",
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                  "code": "AMB", "display": "ambulatory"},
        "type": [{"text": "Outpatient visit"}],
        "subject": {"reference": pat_ref},
        "period": {"start": _fmt(dt), "end": _fmt(dt)},
    } for i, dt in enumerate(enc_dates)]

    # Selección de fármacos y asignación de estados.
    chosen = rng.sample(HARD_MED_CATALOG, n_meds)
    n_active = max(1, round(n_meds * active_frac))
    # Marca cuáles serán activos (posiciones barajadas para que no queden juntos).
    idx = list(range(n_meds))
    rng.shuffle(idx)
    active_idx = set(idx[:n_active])

    medications: list[dict] = []
    for i, info in enumerate(chosen):
        active = i in active_idx
        status = "active" if active else rng.choice(_INACTIVE_STATUSES)
        enc_i = rng.randrange(n_enc)
        authored = enc_dates[enc_i]
        slug = info["text"].lower().split()[0]
        mr = {
            "resourceType": "MedicationRequest",
            "id": f"mr-{i+1:03d}-{slug}",
            "status": status,
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{"system": RXNORM, "code": info["rxnorm"], "display": info["text"]}],
                "text": info["text"],
            },
            "subject": {"reference": pat_ref},
            "authoredOn": _fmt(authored),
            "encounter": {"reference": f"Encounter/enc-{enc_i+1:03d}"},
            "dosageInstruction": [{"text": info["dosage"]}],
        }
        if not active:
            mr["note"] = [{"text": f"Marked {status} on {_fmt(authored)}."}]
        medications.append(mr)

    # Un par de condiciones activas de contexto (no afectan el gold de MR-01).
    conditions = [{
        "resourceType": "Condition", "id": "cond-htn",
        "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
        "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]},
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "problem-list-item"}]}],
        "code": {"coding": [{"system": SNOMED, "code": "59621000", "display": "Essential hypertension"}], "text": "Essential hypertension"},
        "subject": {"reference": pat_ref}, "onsetDateTime": _fmt(date(BASE_YEAR - 5, 3, 1)),
        "recordedDate": _fmt(enc_dates[0]),
    }]

    # Observación de contexto (no relevante para el gold).
    observations = [{
        "resourceType": "Observation", "id": "obs-bp", "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
        "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"}], "text": "Blood pressure"},
        "subject": {"reference": pat_ref}, "effectiveDateTime": _fmt(enc_dates[-1]),
        "encounter": {"reference": f"Encounter/enc-{n_enc:03d}"},
        "component": [
            {"code": {"coding": [{"system": "http://loinc.org", "code": "8480-6"}]}, "valueQuantity": {"value": rng.randint(120, 150), "unit": "mmHg", "system": UCUM, "code": "mm[Hg]"}},
            {"code": {"coding": [{"system": "http://loinc.org", "code": "8462-4"}]}, "valueQuantity": {"value": rng.randint(70, 92), "unit": "mmHg", "system": UCUM, "code": "mm[Hg]"}},
        ],
    }]

    return GeneratedPatient(patient=patient, conditions=conditions,
                            medications=medications, observations=observations,
                            encounters=encounters)


def _ref(res: dict) -> str:
    return f"{res['resourceType']}/{res['id']}"


def build_ground_truth(gp: GeneratedPatient, *, case_id: str) -> dict:
    active = [m for m in gp.medications if m["status"] == "active"]
    inactive = [m for m in gp.medications if m["status"] != "active"]
    items = [{
        "label": m["medicationCodeableConcept"]["text"],
        "code": {"system": RXNORM, "code": m["medicationCodeableConcept"]["coding"][0]["code"]},
        "status": "active",
        "evidence": [_ref(m)],
    } for m in active]
    must_exclude = [{
        "label": m["medicationCodeableConcept"]["text"],
        "code": {"system": RXNORM, "code": m["medicationCodeableConcept"]["coding"][0]["code"]},
        "reason": f"status = {m['status']}",
        "evidence": [_ref(m)],
    } for m in inactive]
    return {
        "case_id": case_id, "capability_id": "MR-01", "output_contract": "entity_list",
        "expected": {"items": items, "must_exclude": must_exclude},
        "safety_events": [],
        "notes": (f"Adversarial MR-01, gold by construction: {len(items)} active of "
                  f"{len(gp.medications)} medication requests. 'Active' means "
                  f"MedicationRequest.status == 'active'; all other statuses "
                  f"(completed/stopped/on-hold/cancelled/entered-in-error/draft) are excluded."),
    }


def build_task(gp: GeneratedPatient, *, case_id: str) -> dict:
    n = len(gp.medications)
    return {
        "case_id": case_id, "schema_version": "0.1", "taxonomy_version": "0.1",
        "capability": {"id": "MR-01", "slug": "medication_reconciliation.active_medication_list"},
        "language": "en",
        "scenario": f"A patient with a long medication history: {n} MedicationRequests across many visits, in mixed statuses.",
        "instruction": ("List the patient's CURRENTLY ACTIVE medications. A medication is "
                        "active only if its MedicationRequest has status 'active'. Exclude "
                        "every medication whose status is completed, stopped, on-hold, "
                        "cancelled, entered-in-error or draft. For each active medication give "
                        "its code and cite the source MedicationRequest as evidence."),
        "output_contract": "entity_list",
        "available_renderings": ["fhir_json", "narrative", "timeline", "table"],
        "rendering_files": {"fhir_json": "bundle.json", "narrative": "narrative.md",
                            "timeline": "timeline.md", "table": "table.md"},
        "resource_types": ["Patient", "Condition", "MedicationRequest", "Observation", "Encounter"],
        "tags": ["medication-reconciliation", "adversarial", "scale", "generated", "hard"],
    }


def build_scoring(case_id: str) -> dict:
    return {
        "case_id": case_id, "capability_id": "MR-01", "scoring_version": "0.1",
        "dimensions": ["CC", "TRC", "SR"],
        "options": {"label_fallback": False, "date_granularity": "day",
                    "code_systems_priority": [RXNORM]},
    }


def _write(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def emit_hard_case(out_dir: str | Path, *, seed: int, case_id: str,
                   n_meds: int = 24, active_frac: float = 0.4) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gp = build_hard_mr01(seed, n_meds=n_meds, active_frac=active_frac)
    views = render_all(gp, bundle_id=f"{case_id}-bundle")
    _write(out_dir / "bundle.json", views["bundle"])
    (out_dir / "narrative.md").write_text(views["narrative"], encoding="utf-8")
    (out_dir / "timeline.md").write_text(views["timeline"], encoding="utf-8")
    (out_dir / "table.md").write_text(views["table"], encoding="utf-8")
    _write(out_dir / "task.json", build_task(gp, case_id=case_id))
    _write(out_dir / "ground_truth.json", build_ground_truth(gp, case_id=case_id))
    _write(out_dir / "scoring.json", build_scoring(case_id))
    return out_dir


# --------------------------------------------------------------------------- #
# MR-03 adversarial: encontrar TODAS las duplicaciones terapéuticas por clase
# --------------------------------------------------------------------------- #

# Clases con >=2 miembros (para plantar pares duplicados).
_CLASSES: dict[str, list[tuple[str, str]]] = {
    "ACE inhibitor": [("314076", "Lisinopril 10 mg"), ("858817", "Enalapril 10 mg"), ("310405", "Ramipril 5 mg")],
    "ARB": [("311036", "Losartan 50 mg"), ("349199", "Valsartan 80 mg")],
    "PPI": [("198051", "Omeprazole 20 mg"), ("311354", "Pantoprazole 40 mg"), ("389181", "Esomeprazole 40 mg")],
    "statin": [("617310", "Atorvastatin 20 mg"), ("312961", "Simvastatin 40 mg"), ("301542", "Rosuvastatin 10 mg")],
    "beta blocker": [("866516", "Metoprolol 50 mg"), ("197379", "Atenolol 50 mg"), ("200031", "Carvedilol 12.5 mg")],
}
# Singletons de clases DISTINTAS (no forman par): distractores.
_SINGLETONS: list[tuple[str, str]] = [
    ("860975", "Metformin 500 mg"), ("966221", "Levothyroxine 50 mcg"),
    ("351250", "Gabapentin 300 mg"), ("763025", "Furosemide 40 mg"),
    ("905395", "Aspirin 81 mg"), ("855332", "Warfarin 5 mg"),
    ("197361", "Amlodipine 5 mg"), ("861760", "Sitagliptin 100 mg"),
    ("198211", "Prednisone 20 mg"), ("856980", "Sertraline 50 mg"),
]


def build_hard_mr03(seed: int, *, n_pairs: int = 3, n_singletons: int = 10):
    """Paciente con varias meds activas, de las cuales ``n_pairs`` son
    duplicaciones terapéuticas (2 fármacos de la misma clase) enterradas entre
    ``n_singletons`` distractores de clases distintas. Devuelve (gp, pairs)
    donde ``pairs`` es la lista de pares duplicados (gold por construcción)."""
    rng = Random(seed)
    pat_id = "pat-001"
    pat_ref = f"Patient/{pat_id}"
    patient = {"resourceType": "Patient", "id": pat_id, "gender": rng.choice(["female", "male"]),
               "birthDate": "1955-06-15", "name": [{"use": "official", "family": "Synthetic",
               "given": [_GIVEN_NAMES[seed % len(_GIVEN_NAMES)]]}]}
    enc_dates = [f"{BASE_YEAR-1}-03-10", f"{BASE_YEAR-1}-11-02", f"{BASE_YEAR}-05-20"]
    encs = [{"resourceType": "Encounter", "id": f"enc-{i+1:03d}", "status": "finished",
             "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory"},
             "type": [{"text": "Medication review"}], "subject": {"reference": pat_ref},
             "period": {"start": dt, "end": dt}} for i, dt in enumerate(enc_dates)]

    n_pairs = max(1, min(n_pairs, len(_CLASSES)))
    classes = rng.sample(list(_CLASSES), n_pairs)
    singles = rng.sample(_SINGLETONS, min(n_singletons, len(_SINGLETONS)))

    # Construye las entradas (clase, rxnorm, text). Los pares comparten clase.
    entries: list[tuple[str, str, str]] = []
    pair_groups: list[list[str]] = []  # ids de cada par
    for cls in classes:
        members = rng.sample(_CLASSES[cls], 2)
        pair_groups.append([])
        for (rx, text) in members:
            entries.append((cls, rx, text))
    for (rx, text) in singles:
        entries.append(("singleton", rx, text))
    rng.shuffle(entries)

    medications: list[dict] = []
    by_rx_to_id: dict[str, str] = {}
    for i, (cls, rx, text) in enumerate(entries):
        mid = f"mr-{i+1:03d}"
        by_rx_to_id[f"{cls}|{rx}|{text}"] = mid
        medications.append({
            "resourceType": "MedicationRequest", "id": mid, "status": "active", "intent": "order",
            "medicationCodeableConcept": {"coding": [{"system": RXNORM, "code": rx, "display": text}], "text": text},
            "subject": {"reference": pat_ref}, "authoredOn": f"{BASE_YEAR}-05-20",
            "encounter": {"reference": "Encounter/enc-001"},
            "dosageInstruction": [{"text": "as directed"}],
        })
    # Reconstruye los pares (ids) por clase.
    pairs: list[dict] = []
    for cls in classes:
        ids = [m["id"] for m in medications
               if any(e for e in entries if e[1] == m["medicationCodeableConcept"]["coding"][0]["code"]
                      and e[0] == cls and e[2] == m["medicationCodeableConcept"]["text"])]
        # ids de las 2 meds de esta clase
        cls_ids = [m["id"] for m in medications
                   if _class_of(m["medicationCodeableConcept"]["coding"][0]["code"]) == cls]
        if len(cls_ids) >= 2:
            pairs.append({"class": cls, "ids": cls_ids[:2]})

    gp = GeneratedPatient(patient=patient, conditions=[], medications=medications,
                          observations=[], encounters=encs)
    return gp, pairs


def _class_of(rx: str) -> str:
    for cls, members in _CLASSES.items():
        if any(m[0] == rx for m in members):
            return cls
    return "singleton"


def emit_hard_mr03(out_dir: str | Path, *, seed: int, case_id: str,
                   n_pairs: int = 3, n_singletons: int = 10) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gp, pairs = build_hard_mr03(seed, n_pairs=n_pairs, n_singletons=n_singletons)
    views = render_all(gp, bundle_id=f"{case_id}-bundle")
    _write(out_dir / "bundle.json", views["bundle"])
    (out_dir / "narrative.md").write_text(views["narrative"], encoding="utf-8")
    (out_dir / "timeline.md").write_text(views["timeline"], encoding="utf-8")
    (out_dir / "table.md").write_text(views["table"], encoding="utf-8")
    flags = [{
        "type": "duplicate_therapy", "severity": "major",
        "description": f"Therapeutic duplication: two {p['class']}s prescribed concurrently.",
        "evidence": [f"MedicationRequest/{i}" for i in p["ids"]],
    } for p in pairs]
    safety = [{
        "id": f"se-{n+1}", "kind": "hazard", "severity": "major",
        "description": f"Duplicate {p['class']} therapy.",
        "evidence": [f"MedicationRequest/{i}" for i in p["ids"]],
    } for n, p in enumerate(pairs)]
    _write(out_dir / "task.json", {
        "case_id": case_id, "schema_version": "0.1", "taxonomy_version": "0.1",
        "capability": {"id": "MR-03", "slug": "medication_reconciliation.duplicate_therapy"},
        "language": "en",
        "scenario": f"A patient on {len(gp.medications)} active medications; some are therapeutic duplications within the same drug class.",
        "instruction": ("Identify ALL therapeutic duplications: pairs of active medications that "
                        "belong to the SAME pharmacologic class (e.g., two ACE inhibitors, two PPIs, "
                        "two statins). Emit one flag per duplicated class, citing both MedicationRequests "
                        "as evidence."),
        "output_contract": "flag_list",
        "available_renderings": ["fhir_json", "narrative", "timeline", "table"],
        "rendering_files": {"fhir_json": "bundle.json", "narrative": "narrative.md",
                            "timeline": "timeline.md", "table": "table.md"},
        "resource_types": ["Patient", "MedicationRequest", "Encounter"],
        "tags": ["duplicate-therapy", "adversarial", "reasoning", "generated", "hard"],
    })
    _write(out_dir / "ground_truth.json", {
        "case_id": case_id, "capability_id": "MR-03", "output_contract": "flag_list",
        "expected": {"flags": flags}, "safety_events": safety,
        "notes": f"Gold by construction: {len(pairs)} same-class duplicate pairs among {len(gp.medications)} active meds.",
    })
    _write(out_dir / "scoring.json", {
        "case_id": case_id, "capability_id": "MR-03", "scoring_version": "0.1",
        "dimensions": ["CC", "SF", "TRC", "SR"], "options": {"label_fallback": False},
    })
    return out_dir


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="generator.adversarial",
                                description="Genera un caso MR-01 adversarial (escala/ruido).")
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--case-id", required=True)
    p.add_argument("--n-meds", type=int, default=24)
    p.add_argument("--active-frac", type=float, default=0.4)
    a = p.parse_args(argv)
    out = emit_hard_case(a.out, seed=a.seed, case_id=a.case_id,
                         n_meds=a.n_meds, active_frac=a.active_frac)
    print(f"Caso adversarial generado en {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
