"""Tests del generador sintético de casos. Sin red, determinísticos."""

from __future__ import annotations

from pathlib import Path

from benchmark_runner.load_case import load_case
from benchmark_runner.validate_case import validate_case

from generator.emit_case import emit_case

SEED = 42
CASE_ID = "pf-fhir-agent-0900"


def _emit(tmp_path: Path, seed: int = SEED, case_id: str = CASE_ID) -> Path:
    out = tmp_path / case_id
    return emit_case(out, seed=seed, case_id=case_id)


def test_generated_case_is_valid(tmp_path):
    """Un caso generado con semilla fija pasa validate_case (errors == [])."""
    case_dir = _emit(tmp_path)
    errors = validate_case(case_dir)
    assert errors == [], f"generated case should be valid, got: {errors}"


def test_determinism_identical_bundle(tmp_path):
    """Generar dos veces con la misma semilla produce bundle.json idéntico."""
    a = emit_case(tmp_path / "a", seed=SEED, case_id=CASE_ID)
    b = emit_case(tmp_path / "b", seed=SEED, case_id=CASE_ID)
    for fname in ("bundle.json", "task.json", "ground_truth.json",
                  "scoring.json", "narrative.md", "timeline.md", "table.md"):
        assert (a / fname).read_bytes() == (b / fname).read_bytes(), \
            f"{fname} differs between two runs with the same seed"


def test_different_seed_changes_bundle(tmp_path):
    """Semillas distintas producen bundles distintos (sanity check)."""
    a = emit_case(tmp_path / "a", seed=1, case_id=CASE_ID)
    b = emit_case(tmp_path / "b", seed=999, case_id=CASE_ID)
    assert (a / "bundle.json").read_bytes() != (b / "bundle.json").read_bytes()


def test_active_vs_stopped_separation(tmp_path):
    """Los activos van en items, los discontinuados en must_exclude y NO en items."""
    case_dir = _emit(tmp_path)
    case = load_case(case_dir)
    expected = case.ground_truth["expected"]

    item_codes = {i["code"]["code"] for i in expected["items"]}
    excluded_codes = {i["code"]["code"] for i in expected["must_exclude"]}

    assert item_codes, "must have at least one active medication"
    assert excluded_codes, "must have at least one discontinued medication"
    # Ningún código discontinuado aparece entre los activos.
    assert item_codes.isdisjoint(excluded_codes)

    # Cruzar con el bundle: la separación coincide con el status real del recurso.
    by_id = {
        e["resource"]["id"]: e["resource"]
        for e in case.bundle["entry"]
        if e["resource"]["resourceType"] == "MedicationRequest"
    }
    for item in expected["items"]:
        mr_id = item["evidence"][0].split("/", 1)[1]
        assert by_id[mr_id]["status"] == "active"
    for item in expected["must_exclude"]:
        mr_id = item["evidence"][0].split("/", 1)[1]
        assert by_id[mr_id]["status"] != "active"


def test_evidence_references_resolve(tmp_path):
    """Toda evidencia en ground_truth resuelve a un recurso del bundle."""
    case_dir = _emit(tmp_path)
    case = load_case(case_dir)
    index = {
        f"{e['resource']['resourceType']}/{e['resource']['id']}"
        for e in case.bundle["entry"]
    }
    expected = case.ground_truth["expected"]
    for key in ("items", "must_exclude"):
        for item in expected.get(key, []):
            for ref in item["evidence"]:
                assert ref in index, f"evidence {ref} does not resolve in bundle"
