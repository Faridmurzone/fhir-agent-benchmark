"""Tests del runner y del caso semilla. Sin red, determinísticos."""

import json
import shutil
from pathlib import Path

import pytest

from benchmark_runner.load_case import load_case, schema_errors
from benchmark_runner.taxonomy import load_taxonomy
from benchmark_runner.validate_case import validate_case

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "cases" / "pf-fhir-agent-0001"


# --- Taxonomía ---

def test_taxonomy_well_formed():
    tax = load_taxonomy()
    ids = [c["id"] for c in tax["capabilities"]]
    assert len(ids) == len(set(ids)), "capability ids must be unique"
    assert len(ids) == 36
    contracts = set(tax["output_contracts"])
    dims = set(tax["dimensions"])
    for c in tax["capabilities"]:
        assert c["output_contract"] in contracts
        assert set(c["dimensions"]) <= dims
        assert c["tier"] in ("core", "ext")
        assert c["family"] in tax["families"]


def test_taxonomy_core_count():
    core = [c for c in load_taxonomy()["capabilities"] if c["tier"] == "core"]
    assert len(core) == 28


# --- Caso semilla ---

def test_seed_case_loads():
    case = load_case(SEED)
    assert case.case_id == "pf-fhir-agent-0001"
    assert case.task["capability"]["id"] == "MR-01"
    assert set(case.renderings) == {"fhir_json", "narrative", "timeline", "table"}


def test_seed_case_is_valid():
    errors = validate_case(SEED)
    assert errors == [], f"seed case should be valid, got: {errors}"


def test_seed_case_renderings_exist():
    case = load_case(SEED)
    for name, path in case.renderings.items():
        assert path.exists(), f"missing rendering file for {name}"


def test_ground_truth_excludes_discontinued():
    case = load_case(SEED)
    expected = case.ground_truth["expected"]
    active_codes = {i["code"]["code"] for i in expected["items"]}
    excluded_codes = {i["code"]["code"] for i in expected["must_exclude"]}
    assert "310537" in excluded_codes  # glyburide stopped -> excluded
    assert "310537" not in active_codes
    assert active_codes == {"860975", "314076", "617312"}  # metformin, lisinopril, atorvastatin


# --- Detección de errores (caso roto en tmp) ---

@pytest.fixture
def broken_case(tmp_path):
    dst = tmp_path / "pf-fhir-agent-0001"
    shutil.copytree(SEED, dst)
    return dst


def test_detects_dangling_evidence(broken_case):
    gt_path = broken_case / "ground_truth.json"
    gt = json.loads(gt_path.read_text())
    gt["expected"]["items"][0]["evidence"] = ["MedicationRequest/does-not-exist"]
    gt_path.write_text(json.dumps(gt))
    errors = validate_case(broken_case)
    assert any("does-not-exist" in e and "does not resolve" in e for e in errors)


def test_detects_contract_mismatch(broken_case):
    task_path = broken_case / "task.json"
    task = json.loads(task_path.read_text())
    task["output_contract"] = "flag_list"  # MR-01 is entity_list in taxonomy
    task_path.write_text(json.dumps(task))
    errors = validate_case(broken_case)
    assert any("output_contract" in e and "taxonomy" in e for e in errors)


def test_detects_missing_resource_type(broken_case):
    task_path = broken_case / "task.json"
    task = json.loads(task_path.read_text())
    task["resource_types"].append("CarePlan")  # not present in bundle
    task_path.write_text(json.dumps(task))
    errors = validate_case(broken_case)
    assert any("CarePlan" in e and "absent" in e for e in errors)


def test_detects_disallowed_dimension(broken_case):
    sc_path = broken_case / "scoring.json"
    sc = json.loads(sc_path.read_text())
    sc["dimensions"].append("FV")  # FV not allowed for MR-01
    sc_path.write_text(json.dumps(sc))
    errors = validate_case(broken_case)
    assert any("FV" in e or "not allowed" in e for e in errors)


# --- JSON Schema ---

def test_schema_rejects_bad_capability_id():
    bad = {
        "case_id": "pf-fhir-agent-0001", "schema_version": "0.1", "taxonomy_version": "0.1",
        "capability": {"id": "MR1", "slug": "x"}, "language": "en",
        "instruction": "list the active medications please",
        "output_contract": "entity_list", "available_renderings": ["fhir_json"],
        "resource_types": ["Patient"],
    }
    errors = schema_errors("task", bad)
    assert errors, "malformed capability id should fail schema"
