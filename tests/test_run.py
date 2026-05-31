"""Tests del baseline run harness (adaptadores oracle/empty, sin red)."""

from pathlib import Path

from benchmark_runner.adapters import EmptyAdapter, OracleAdapter, parse_model_json
from benchmark_runner.report import build_report
from benchmark_runner.run import run_case, run_model

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "cases"


# --- Oracle: cota superior, debe puntuar perfecto en todos los casos ---

def test_oracle_perfect_on_seed_case():
    card = run_case(OracleAdapter(), CASES / "pf-fhir-agent-0001")
    assert card["CC"] == 100
    assert card["TRC"] == 100
    assert card["SR"] == 100
    assert card["overall"] == 100


def test_oracle_all_cases_high():
    res = run_model(OracleAdapter())
    assert res["aggregate"]["n_cases"] >= 4
    # El oracle copia el ground truth: CC y SF deben ser perfectos en todos.
    assert res["aggregate"]["CC"] == 100
    assert res["aggregate"]["SF"] == 100
    for card in res["cases"]:
        assert card["overall"] == 100


# --- Empty: cota inferior; en el caso de safety gatea el overall ---

def test_empty_misses_safety_case():
    # 0004 es MR-04 con un hazard crítico; el adaptador vacío no lo marca.
    card = run_case(EmptyAdapter(), CASES / "pf-fhir-agent-0004")
    assert card["SF"] < 100
    assert card["breakdown"]["critical_uncaught"] is True
    assert card["overall"] <= 40  # hard cap por crítico no atrapado


def test_empty_low_overall():
    res = run_model(EmptyAdapter())
    assert res["aggregate"]["overall"] < res["aggregate"]["n_cases"] * 100
    assert (res["aggregate"]["overall"] or 0) < 60


# --- Reporte ---

def test_report_renders():
    res = run_model(OracleAdapter())
    md = build_report(res)
    assert "# FHIR Agent Benchmark — Results" in md
    assert "## Scorecard" in md
    assert "By family" in md and "By case" in md
    assert "Overall" in md


# --- Parser de JSON del modelo ---

def test_parse_model_json_with_fences():
    assert parse_model_json('```json\n{"items": []}\n```') == {"items": []}
    assert parse_model_json('Sure!\n{"flags": [{"type": "x"}]}\ndone') == {"flags": [{"type": "x"}]}
    assert parse_model_json("no json here") == {}
