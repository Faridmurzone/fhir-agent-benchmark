"""Tests de la familia TX (Transformation & Mapping): casos 0030-0034.

Cubre lo que FG no mide: identificación de recurso destino, mapeo de campos
desde JSON no estandarizado / texto plano, selección de terminología de
memoria, conformidad US Core sin perfil dado, y migración R4->R5.
"""

from pathlib import Path

import pytest

from benchmark_runner import fhir_validate
from benchmark_runner.adapters import OracleAdapter
from benchmark_runner.run import run_case
from benchmark_runner.score_case import _score_assertions, score_fv, score_rendering
from benchmark_runner.validate_case import validate_case

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "cases"
TX_CASES = ["pf-fhir-agent-0030", "pf-fhir-agent-0031", "pf-fhir-agent-0032",
            "pf-fhir-agent-0033", "pf-fhir-agent-0034"]


# --- Validez de los casos y techo del oracle ---

@pytest.mark.parametrize("case_id", TX_CASES)
def test_tx_case_is_valid(case_id):
    assert validate_case(CASES / case_id) == []


@pytest.mark.parametrize("case_id", TX_CASES)
def test_oracle_perfect_on_tx_case(case_id):
    # Si el gold no pasa su propio scorer, el sesgo está en el instrumento.
    card = run_case(OracleAdapter(), CASES / case_id)
    assert card["CC"] == 100
    assert card["FV"] == 100
    assert card["overall"] == 100


# --- equals_any: tolerancia deliberada en coding un-guided ---

def test_assertion_equals_any_accepts_alternatives():
    a = [{"path": "code.coding[*].code", "equals_any": ["59621000", "38341003"]}]
    res_precise = {"code": {"coding": [{"code": "59621000"}]}}
    res_general = {"code": {"coding": [{"code": "38341003"}]}}
    res_wrong = {"code": {"coding": [{"code": "44054006"}]}}
    assert _score_assertions(res_precise, a, "day").score == 100.0
    assert _score_assertions(res_general, a, "day").score == 100.0
    assert _score_assertions(res_wrong, a, "day").score == 0.0


def test_assertion_equals_still_works():
    a = [{"path": "status", "equals": "final"}]
    assert _score_assertions({"status": "final"}, a, "day").score == 100.0
    assert _score_assertions({"status": "F"}, a, "day").score == 0.0


# --- Mapeo de vocabulario: el status del vendor NO debe filtrarse ---

def test_vendor_status_leak_fails_cc():
    # Un modelo que copia el status propietario "F" en vez de mapear a "final"
    # debe perder la aserción de status en 0030.
    from benchmark_runner.load_case import load_case
    case = load_case(CASES / "pf-fhir-agent-0030")
    leaked = dict(case.ground_truth["expected"]["reference_resource"])
    leaked["status"] = "F"
    result = score_rendering(case.ground_truth, case.scoring, {"resource": leaked})
    assert result["CC"] < 100


# --- R4 -> R5: la validación oficial debe discriminar versiones ---

R4_SHAPE = {
    "resourceType": "MedicationRequest",
    "status": "active",
    "intent": "order",
    "medicationCodeableConcept": {
        "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "314076"}]
    },
    "subject": {"reference": "Patient/pat-001"},
    "authoredOn": "2026-05-20",
}

R5_SHAPE = {
    "resourceType": "MedicationRequest",
    "status": "active",
    "intent": "order",
    "medication": {
        "concept": {
            "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "314076"}]
        }
    },
    "subject": {"reference": "Patient/pat-001"},
    "authoredOn": "2026-05-20",
}


@pytest.mark.skipif(not fhir_validate.available(), reason="fhir.resources no instalado")
def test_official_validator_discriminates_r4_vs_r5():
    ok_r5, _ = fhir_validate.validate(R5_SHAPE, version="R5")
    ok_r4_as_r5, _ = fhir_validate.validate(R4_SHAPE, version="R5")
    ok_r4, _ = fhir_validate.validate(R4_SHAPE, version="R4")
    ok_r5_as_r4, _ = fhir_validate.validate(R5_SHAPE, version="R4")
    assert ok_r5 and ok_r4
    assert not ok_r4_as_r5
    assert not ok_r5_as_r4


@pytest.mark.skipif(not fhir_validate.available(), reason="fhir.resources no instalado")
def test_unmigrated_r4_shape_fails_fv_on_0034():
    # Un modelo que devuelve la forma R4 sin migrar pierde la capa estructural
    # de FV (70 pts) y la aserción medication.concept.* de CC.
    fv = score_fv({"resource": R4_SHAPE}, fhir_version="R5")
    assert fv.score < 50
    from benchmark_runner.load_case import load_case
    case = load_case(CASES / "pf-fhir-agent-0034")
    result = score_rendering(case.ground_truth, case.scoring, {"resource": R4_SHAPE})
    assert result["CC"] < 100
    assert result["FV"] < 50


# --- US Core un-guided: sin meta.profile no hay techo de 100 en FV ---

def test_us_core_unguided_requires_profile_declaration():
    from benchmark_runner.load_case import load_case
    case = load_case(CASES / "pf-fhir-agent-0033")
    gold = dict(case.ground_truth["expected"]["reference_resource"])
    stripped = {k: v for k, v in gold.items() if k != "meta"}
    result = score_rendering(case.ground_truth, case.scoring, {"resource": stripped})
    # Pierde la aserción meta.profile en CC y los puntos de capa 7 en FV.
    assert result["CC"] < 100
    assert result["FV"] < 100


# --- Bundle: aserciones multi-wildcard y consistencia referencial ---

def test_bundle_multiwildcard_assertions():
    a = [
        {"path": "entry[*].resource.code.coding[*].code", "equals": "2951-2"},
        {"path": "entry[*].resource.code.coding[*].code", "equals": "2823-3"},
    ]
    bundle = {
        "entry": [
            {"resource": {"code": {"coding": [{"code": "2951-2"}]}}},
            {"resource": {"code": {"coding": [{"code": "2823-3"}]}}},
        ]
    }
    assert _score_assertions(bundle, a, "day").score == 100.0
    missing_k = {"entry": [{"resource": {"code": {"coding": [{"code": "2951-2"}]}}}]}
    assert _score_assertions(missing_k, a, "day").score == 50.0
