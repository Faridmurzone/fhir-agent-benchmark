"""Tests del generador adversarial (gold por construcción, determinismo, validez)."""

import json

from benchmark_runner.validate_case import validate_case
from generator.adversarial import (_class_of, build_hard_mr01, emit_hard_case,
                                    emit_hard_mr03)


def _bundle_status(bundle: dict) -> dict[str, str]:
    """Mapea 'ResourceType/id' -> status para MedicationRequests."""
    out = {}
    for e in bundle["entry"]:
        r = e["resource"]
        if r["resourceType"] == "MedicationRequest":
            out[f"MedicationRequest/{r['id']}"] = r["status"]
    return out


# --- MR-01 adversarial ---

def test_mr01_valid_and_gold_by_construction(tmp_path):
    d = tmp_path / "pf-fhir-agent-0920"
    emit_hard_case(d, seed=42, case_id="pf-fhir-agent-0920", n_meds=24)
    assert validate_case(d) == []

    bundle = json.loads((d / "bundle.json").read_text())
    gt = json.loads((d / "ground_truth.json").read_text())
    status = _bundle_status(bundle)

    # Cada item del gold apunta a un MedicationRequest con status active.
    for item in gt["expected"]["items"]:
        for ref in item["evidence"]:
            assert status[ref] == "active", f"{ref} should be active"
    # Cada must_exclude apunta a uno NO active.
    for ex in gt["expected"]["must_exclude"]:
        for ref in ex["evidence"]:
            assert status[ref] != "active"
    # El conjunto activo del gold == los MedicationRequest active del bundle.
    gold_active = {r for it in gt["expected"]["items"] for r in it["evidence"]}
    bundle_active = {ref for ref, s in status.items() if s == "active"}
    assert gold_active == bundle_active


def test_mr01_deterministic(tmp_path):
    a = tmp_path / "a"; b = tmp_path / "b"
    emit_hard_case(a, seed=7, case_id="pf-fhir-agent-0920", n_meds=20)
    emit_hard_case(b, seed=7, case_id="pf-fhir-agent-0920", n_meds=20)
    assert (a / "bundle.json").read_text() == (b / "bundle.json").read_text()


def test_mr01_scale_knob(tmp_path):
    gp = build_hard_mr01(1, n_meds=28, active_frac=0.4)
    assert len(gp.medications) == 28
    n_active = sum(1 for m in gp.medications if m["status"] == "active")
    assert 1 <= n_active < 28  # hay mezcla activo / no-activo


# --- MR-03 adversarial (duplicación terapéutica) ---

def test_mr03_valid_and_pairs_same_class(tmp_path):
    d = tmp_path / "pf-fhir-agent-0953"
    emit_hard_mr03(d, seed=13, case_id="pf-fhir-agent-0953", n_pairs=3, n_singletons=10)
    assert validate_case(d) == []

    bundle = json.loads((d / "bundle.json").read_text())
    gt = json.loads((d / "ground_truth.json").read_text())
    by_id = {f"MedicationRequest/{e['resource']['id']}": e["resource"]
             for e in bundle["entry"] if e["resource"]["resourceType"] == "MedicationRequest"}

    assert len(gt["expected"]["flags"]) == 3
    for flag in gt["expected"]["flags"]:
        refs = flag["evidence"]
        assert len(refs) == 2
        # Las dos meds del par comparten clase farmacológica (gold por construcción).
        classes = {_class_of(by_id[r]["medicationCodeableConcept"]["coding"][0]["code"]) for r in refs}
        assert len(classes) == 1 and "singleton" not in classes


def test_mr03_deterministic(tmp_path):
    a = tmp_path / "a"; b = tmp_path / "b"
    emit_hard_mr03(a, seed=5, case_id="pf-fhir-agent-0953", n_pairs=4)
    emit_hard_mr03(b, seed=5, case_id="pf-fhir-agent-0953", n_pairs=4)
    assert (a / "bundle.json").read_text() == (b / "bundle.json").read_text()
