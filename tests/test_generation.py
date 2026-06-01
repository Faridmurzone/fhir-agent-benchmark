"""Tests del CC de generación FHIR (aserciones por path) y validez (FV)."""

from pathlib import Path

from benchmark_runner.load_case import load_case
from benchmark_runner.score_case import _resolve_path, score_case, score_fv
from benchmark_runner.validate_case import validate_case

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "cases"


# --- path resolver ---

def test_resolve_path_index_and_wildcard():
    obj = {"code": {"coding": [{"system": "x", "code": "4548-4"}, {"system": "y", "code": "z"}]}}
    assert _resolve_path(obj, "code.coding[0].code") == (True, "4548-4")
    found, vals = _resolve_path(obj, "code.coding[*].code")
    assert found and set(vals) == {"4548-4", "z"}
    assert _resolve_path(obj, "code.coding[5].code") == (False, None)
    assert _resolve_path(obj, "nope.here") == (False, None)


# --- FG cases válidos y oracle perfecto en CC ---

def test_fg_cases_valid():
    for c in ("0020", "0021", "0022"):
        assert validate_case(CASES / f"pf-fhir-agent-{c}") == []


def test_generation_cc_via_assertions():
    case = load_case(CASES / "pf-fhir-agent-0020")
    ref = case.ground_truth["expected"]["reference_resource"]
    card = score_case(case.ground_truth, case.scoring, {"narrative": {"resource": ref}})
    assert card["CC"] == 100         # el recurso de referencia satisface las aserciones
    assert card["TRC"] == 100        # referencia subject + encounter presentes
    assert card["FV"] == 90          # válido salvo capa de perfil (deferida)


def test_generation_cc_partial_when_wrong_code():
    case = load_case(CASES / "pf-fhir-agent-0020")
    ref = dict(case.ground_truth["expected"]["reference_resource"])
    # Rompemos el LOINC code: una aserción debe fallar -> CC < 100.
    ref["code"] = {"coding": [{"system": "http://loinc.org", "code": "0000-0"}]}
    card = score_case(case.ground_truth, case.scoring, {"narrative": {"resource": ref}})
    assert card["CC"] < 100


# --- FV: gates y validez estructural ---

def test_fv_gates():
    assert score_fv({"resource": "not-an-object"}).score == 0.0      # capa 1
    assert score_fv({"resource": {"resourceType": "Nope"}}).score == 0.0  # capa 2
    good = {"resource": {"resourceType": "Observation", "status": "final",
                         "code": {"coding": [{"system": "http://loinc.org", "code": "4548-4"}]},
                         "subject": {"reference": "Patient/p1"}}}
    assert score_fv(good).score >= 80   # válido salvo perfil (capa 7)
