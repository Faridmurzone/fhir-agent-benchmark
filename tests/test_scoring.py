"""Tests del motor de scoring. Determinísticos, sin red.

Solo dependen del caso semilla pf-fhir-agent-0001 (que existe). Los escenarios
de safety / flag_list se construyen con ground_truth y outputs sintéticos
inline, porque otros casos se están construyendo en paralelo y pueden no existir.
"""

import json
from pathlib import Path

from benchmark_runner import metrics
from benchmark_runner.load_case import load_case
from benchmark_runner.score_case import (
    aggregate_model,
    load_defaults,
    score_case,
    score_cc,
    score_fv,
    score_rendering,
)

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "cases" / "pf-fhir-agent-0001"
DEFAULTS = load_defaults()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _seed():
    case = load_case(SEED)
    return case.ground_truth, case.scoring


def _perfect_mr01_output():
    """Las 3 meds activas con código + evidencia correctos, sin glyburide."""
    return {
        "items": [
            {
                "label": "Metformin 500 mg",
                "code": {"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "860975"},
                "status": "active",
                "evidence": ["MedicationRequest/mr-metformin"],
            },
            {
                "label": "Lisinopril 10 mg",
                "code": {"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "314076"},
                "status": "active",
                "evidence": ["MedicationRequest/mr-lisinopril"],
            },
            {
                "label": "Atorvastatin 20 mg",
                "code": {"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "617312"},
                "status": "active",
                "evidence": ["MedicationRequest/mr-atorvastatin"],
            },
        ]
    }


# --------------------------------------------------------------------------- #
# Primitivas
# --------------------------------------------------------------------------- #

def test_set_f1_perfect():
    items = _perfect_mr01_output()["items"]
    res = metrics.set_f1(items, items)
    assert res.score == 100.0
    assert res.detail["precision"] == 1.0
    assert res.detail["recall"] == 1.0


def test_set_f1_empty_gold_empty_pred():
    res = metrics.set_f1([], [])
    assert res.score == 100.0


def test_set_f1_empty_gold_nonempty_pred():
    res = metrics.set_f1([{"code": {"system": "s", "code": "1"}}], [])
    assert res.score == 0.0


def test_ordered_score_pairs():
    gold = ["A", "B", "C"]
    assert metrics.ordered_score(["A", "B", "C"], gold).score == 100.0
    # Un par invertido de tres -> 2/3.
    res = metrics.ordered_score(["A", "C", "B"], gold)
    assert abs(res.score - (100.0 * 2 / 3)) < 1e-6


def test_scalar_date_granularity():
    res = metrics.scalar_match("2025-12-03T10:00:00Z", "2025-12-03", date_granularity="day")
    assert res.score == 100.0
    res2 = metrics.scalar_match("2025-12-04", "2025-12-03", date_granularity="day")
    assert res2.score == 0.0
    res3 = metrics.scalar_match("2025-12-04", "2025-12-03", date_granularity="month")
    assert res3.score == 100.0


def test_structured_per_field():
    gold = {"age": 67, "sex": "female"}
    res = metrics.structured_match({"age": 67, "sex": "male"}, gold)
    assert res.score == 50.0


# --------------------------------------------------------------------------- #
# Caso semilla MR-01: perfecto y con glyburide
# --------------------------------------------------------------------------- #

def test_seed_perfect_cc_trc():
    gt, sc = _seed()
    out = _perfect_mr01_output()
    cc = score_cc(gt, sc, out)
    assert cc.score == 100.0
    rendering = score_rendering(gt, sc, out, DEFAULTS)
    assert rendering["TRC"] == 100.0
    assert rendering["SF"] == 100.0  # caso limpio


def test_seed_perfect_sr_across_four_renderings():
    gt, sc = _seed()
    out = _perfect_mr01_output()
    outputs = {r: out for r in ("fhir_json", "narrative", "timeline", "table")}
    card = score_case(gt, sc, outputs, DEFAULTS)
    assert card["CC"] == 100.0
    assert card["TRC"] == 100.0
    assert card["SR"] == 100.0
    assert card["SF"] == 100.0
    assert card["overall"] == 100


def test_seed_including_glyburide_drops_cc():
    gt, sc = _seed()
    out = _perfect_mr01_output()
    out["items"].append({
        "label": "Glyburide 5 mg",
        "code": {"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "310537"},
        "status": "active",
        "evidence": ["MedicationRequest/mr-glyburide"],
    })
    cc = score_cc(gt, sc, out)
    # 3 verdaderos positivos, 1 falso positivo: precision 3/4, recall 3/3.
    assert cc.score < 100.0
    assert abs(cc.detail["precision"] - 0.75) < 1e-9
    assert cc.detail["recall"] == 1.0


# --------------------------------------------------------------------------- #
# Safety: flag_list con hazard crítico
# --------------------------------------------------------------------------- #

def _allergy_conflict_gt():
    """Ground truth sintético SA-01: un hazard crítico que DEBE flaggearse."""
    return {
        "case_id": "pf-fhir-agent-9001",
        "capability_id": "SA-01",
        "output_contract": "flag_list",
        "expected": {
            "flags": [
                {
                    "type": "allergy_med_conflict",
                    "severity": "critical",
                    "evidence": ["MedicationRequest/mr-amox", "AllergyIntolerance/allergy-pcn"],
                }
            ]
        },
        "safety_events": [
            {
                "id": "haz-1",
                "kind": "hazard",
                "severity": "critical",
                "description": "Amoxicillin ordered despite penicillin allergy.",
                "evidence": ["MedicationRequest/mr-amox", "AllergyIntolerance/allergy-pcn"],
            }
        ],
    }


def _allergy_conflict_scoring():
    return {
        "case_id": "pf-fhir-agent-9001",
        "capability_id": "SA-01",
        "scoring_version": "0.1",
        "dimensions": ["SF", "CC", "TRC", "SR"],
        "options": {"label_fallback": False},
    }


def test_safety_missed_critical_hazard_caps_overall():
    gt = _allergy_conflict_gt()
    sc = _allergy_conflict_scoring()
    # El modelo NO flaggea nada -> pierde el hazard crítico.
    out = {"flags": []}
    outputs = {r: out for r in ("fhir_json", "narrative", "timeline", "table")}
    card = score_case(gt, sc, outputs, DEFAULTS)
    assert card["SF"] == 40.0  # 100 - 60 (crítico)
    assert card["breakdown"]["critical_uncaught"] is True
    # Hard cap: el overall NUNCA puede superar 40 con un crítico no atrapado.
    # Aquí además el gate de safety y un CC=0 (no flaggeó) lo hunden más.
    assert card["overall"] <= 40


def test_hard_cap_binds_when_other_dims_high():
    """Un crítico no atrapado limita el overall a 40 aunque CC/TRC sean altos.

    El modelo flaggea un hazard CORRECTO (gana CC/TRC) pero omite un SEGUNDO
    hazard crítico declarado: el hard cap debe activarse y limitar a 40.
    """
    gt = _allergy_conflict_gt()
    gt["expected"]["flags"].append({
        "type": "allergy_med_conflict",
        "severity": "critical",
        "evidence": ["MedicationRequest/mr-sulfa", "AllergyIntolerance/allergy-sulfa"],
    })
    gt["safety_events"].append({
        "id": "haz-2", "kind": "hazard", "severity": "critical",
        "description": "Sulfa drug despite sulfa allergy.",
        "evidence": ["MedicationRequest/mr-sulfa", "AllergyIntolerance/allergy-sulfa"],
    })
    sc = _allergy_conflict_scoring()
    # Solo flaggea el primero (correcto); omite el segundo crítico.
    out = {"flags": [{
        "type": "allergy_med_conflict", "severity": "critical",
        "evidence": ["MedicationRequest/mr-amox", "AllergyIntolerance/allergy-pcn"],
    }]}
    outputs = {r: out for r in ("fhir_json", "narrative", "timeline", "table")}
    card = score_case(gt, sc, outputs, DEFAULTS)
    assert card["breakdown"]["critical_uncaught"] is True
    # CC/TRC altos, pero el crítico omitido limita el overall a <= 40.
    assert card["CC"] > 50.0
    assert card["TRC"] == 100.0
    assert card["overall"] <= 40


def test_safety_caught_hazard_high_overall():
    gt = _allergy_conflict_gt()
    sc = _allergy_conflict_scoring()
    correct_flag = {
        "type": "allergy_med_conflict",
        "severity": "critical",
        "description": "Amoxicillin ordered despite documented penicillin allergy.",
        "evidence": ["MedicationRequest/mr-amox", "AllergyIntolerance/allergy-pcn"],
    }
    out = {"flags": [correct_flag]}
    outputs = {r: out for r in ("fhir_json", "narrative", "timeline", "table")}
    card = score_case(gt, sc, outputs, DEFAULTS)
    assert card["SF"] == 100.0
    assert card["CC"] == 100.0
    assert card["TRC"] == 100.0
    assert card["breakdown"]["critical_uncaught"] is False
    assert card["overall"] == 100


def test_empty_gold_flag_list_no_flags_is_perfect():
    gt = {
        "case_id": "pf-fhir-agent-9002",
        "capability_id": "MR-03",
        "output_contract": "flag_list",
        "expected": {"flags": []},
        "safety_events": [],
    }
    sc = {
        "case_id": "pf-fhir-agent-9002", "capability_id": "MR-03",
        "scoring_version": "0.1", "dimensions": ["CC", "SF", "TRC", "SR"],
    }
    out = {"flags": []}
    cc = score_cc(gt, sc, out)
    assert cc.score == 100.0
    card = score_case(gt, sc, {"fhir_json": out}, DEFAULTS)
    assert card["CC"] == 100.0
    assert card["SF"] == 100.0


# --------------------------------------------------------------------------- #
# SR: caso frágil
# --------------------------------------------------------------------------- #

def test_sr_brittle_case():
    gt, sc = _seed()
    good = _perfect_mr01_output()
    # En 'table' el modelo solo acierta 1 de 3 (recall bajo) -> CC bajo.
    bad = {"items": [good["items"][0]]}
    outputs = {
        "fhir_json": good,
        "narrative": good,
        "timeline": good,
        "table": bad,
    }
    card = score_case(gt, sc, outputs, DEFAULTS)
    # CC table = F1(prec=1, rec=1/3) = 50.
    assert card["CC_per_rendering"]["table"] == 50.0
    # SR = 100 * (1 - (100-50)/100) = 50.
    assert card["SR"] == 50.0
    assert card["SR"] < 100.0


# --------------------------------------------------------------------------- #
# FV: validador estructural ligero
# --------------------------------------------------------------------------- #

def test_fv_valid_observation():
    out = {
        "resource": {
            "resourceType": "Observation",
            "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": "718-7"}]},
            "subject": {"reference": "Patient/pat-1"},
            "effectiveDateTime": "2025-01-01",
        }
    }
    res = score_fv(out)
    assert res.score >= 90.0  # capa 7 (perfil, 10pts) no implementada en v0.1


def test_fv_invalid_json_object():
    assert score_fv({"resource": "not an object"}).score == 0.0


def test_fv_bad_resource_type():
    assert score_fv({"resource": {"resourceType": "Nonsense"}}).score == 0.0


# --------------------------------------------------------------------------- #
# Agregación a nivel modelo
# --------------------------------------------------------------------------- #

def test_aggregate_model():
    gt, sc = _seed()
    out = _perfect_mr01_output()
    outputs = {r: out for r in ("fhir_json", "narrative", "timeline", "table")}
    card = score_case(gt, sc, outputs, DEFAULTS)
    agg = aggregate_model([card, card])
    assert agg["n_cases"] == 2
    assert agg["CC"] == 100.0
    assert agg["overall"] == 100
    assert "MR" in agg["per_family"]
    assert agg["per_family"]["MR"]["n_cases"] == 2
