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
    # El oracle copia el ground truth: CC y SF perfectos en todos.
    assert res["aggregate"]["CC"] == 100
    assert res["aggregate"]["SF"] == 100
    for card in res["cases"]:
        # Casos de extracción: oracle perfecto. Casos de generación (FG): FV está
        # capeado a 90 porque la capa de validación de perfil está deferida (v0.1),
        # así que el overall del oracle es 98, no 100. Ambos son correctos.
        if card.get("FV") is not None:
            assert card["overall"] >= 95
        else:
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

class _FailingAdapter:
    name = "failing"

    def answer(self, case, rendering, prompt):
        raise RuntimeError("simulated API error")


def test_run_handles_adapter_errors():
    # Un adaptador que siempre falla no debe tumbar la corrida.
    res = run_model(_FailingAdapter())
    assert res["n_errored"] == res["aggregate"]["n_cases"] + res["n_errored"]  # todos errored
    assert res["n_scored"] == 0
    assert res["aggregate"]["overall"] is None
    assert all(c.get("error") for c in res["cases"])
    # El reporte se renderiza igual.
    md = build_report(res)
    assert "errored" in md and "ERR" in md


def test_adapter_routing():
    import pytest

    from benchmark_runner.adapters import (AnthropicAdapter, GeminiAdapter,
                                           OpenAIAdapter, get_adapter)
    assert isinstance(get_adapter("openai:gpt-4o"), OpenAIAdapter)
    assert get_adapter("openai:gpt-4o").model == "gpt-4o"
    assert isinstance(get_adapter("gemini"), GeminiAdapter)
    assert isinstance(get_adapter("anthropic:claude-sonnet-4-6"), AnthropicAdapter)
    assert get_adapter("anthropic:claude-sonnet-4-6").model == "claude-sonnet-4-6"
    with pytest.raises(ValueError):
        get_adapter("nope")


def test_parse_model_json_with_fences():
    assert parse_model_json('```json\n{"items": []}\n```') == {"items": []}
    assert parse_model_json('Sure!\n{"flags": [{"type": "x"}]}\ndone') == {"flags": [{"type": "x"}]}
    assert parse_model_json("no json here") == {}
