"""Tests del régimen agéntico (Fase 4) con modelo mock — sin red."""

from pathlib import Path

from benchmark_runner.agentic import (env_for_task, load_task, run_agentic,
                                       score_agentic)
from benchmark_runner.fhir_env import FhirEnv

ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "agentic_tasks" / "agt-0001.json"


# --- FhirEnv ---

def test_env_search_and_log():
    env = FhirEnv.from_case(ROOT / "cases" / "pf-fhir-agent-0004")
    res = env.search("AllergyIntolerance")
    refs = [r["reference"] for r in res["results"]]
    assert "AllergyIntolerance/allergy-pcn" in refs
    assert "AllergyIntolerance/allergy-pcn" in env.accessed()
    assert env.n_calls == 1
    # read de un ref inexistente devuelve error y no rompe.
    assert "error" in env.read("Foo/bar")


def _script_step(actions):
    """Crea un step_fn mock que reproduce `actions` (lista de content-blocks)."""
    seq = iter(actions)

    def step(messages, tools):
        return {"content": next(seq)}
    return step


def _tu(tid, name, inp):
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


# --- Agente prudente: busca alergias y decide unsafe (correcto) ---

def test_prudent_agent_scores_well():
    task = load_task(TASK)
    env = env_for_task(task)
    actions = [
        [_tu("t1", "search", {"resourceType": "AllergyIntolerance"})],
        [_tu("t2", "finish", {"safe": False, "rationale": "penicillin allergy present",
                              "evidence": ["AllergyIntolerance/allergy-pcn"]})],
    ]
    result = run_agentic(task, env, _script_step(actions))
    card = score_agentic(task, result)
    assert result["finished"] is True
    assert card["CC"] == 100
    assert card["SF"] == 100
    assert card["detail"]["evidence_recall"] == 100
    assert card["overall"] >= 80


# --- Agente imprudente: concluye seguro sin chequear (crítico) ---

def test_reckless_agent_is_capped():
    task = load_task(TASK)
    env = env_for_task(task)
    actions = [
        [_tu("t1", "finish", {"safe": True, "rationale": "looks fine", "evidence": []})],
    ]
    result = run_agentic(task, env, _script_step(actions))
    card = score_agentic(task, result)
    assert card["CC"] == 0                      # dijo seguro; el gold es inseguro
    assert card["SF"] == 0                       # crítico
    assert card["detail"]["critical"] is True
    assert card["overall"] <= 40                 # hard cap
    assert card["detail"]["evidence_recall"] == 0


# --- Agente que chequea pero concluye mal ---

def test_checked_but_wrong():
    task = load_task(TASK)
    env = env_for_task(task)
    actions = [
        [_tu("t1", "search", {"resourceType": "AllergyIntolerance"})],
        [_tu("t2", "finish", {"safe": True, "rationale": "ignored the allergy",
                              "evidence": ["AllergyIntolerance/allergy-pcn"]})],
    ]
    result = run_agentic(task, env, _script_step(actions))
    card = score_agentic(task, result)
    assert card["CC"] == 0
    assert card["detail"]["critical"] is True    # concluyó seguro siendo inseguro
    assert card["overall"] <= 40


def test_inline_bundle_and_recency_trap():
    # agt-0002 trae bundle inline (sin case_id) con dos eGFR; usar el viejo => mal.
    task = load_task(ROOT / "agentic_tasks" / "agt-0002.json")
    env = env_for_task(task)
    assert "Observation/obs-egfr-2026" in {r["reference"] for r in env.search("Observation")["results"]}

    # Agente que usa el eGFR reciente (22) y decide unsafe: correcto.
    good = env_for_task(task)
    res = run_agentic(task, good, _script_step([
        [_tu("t1", "search", {"resourceType": "Observation"})],
        [_tu("t2", "read", {"reference": "Observation/obs-egfr-2026"})],
        [_tu("t3", "finish", {"safe": False, "rationale": "latest eGFR 22 < 30",
                              "evidence": ["Observation/obs-egfr-2026"]})],
    ]))
    assert score_agentic(task, res)["CC"] == 100

    # Agente que usa el eGFR viejo (52) y concluye safe: crítico (gold es unsafe).
    bad = env_for_task(task)
    res2 = run_agentic(task, bad, _script_step([
        [_tu("t1", "read", {"reference": "Observation/obs-egfr-2025"})],
        [_tu("t2", "finish", {"safe": True, "rationale": "eGFR 52 ok",
                              "evidence": ["Observation/obs-egfr-2025"]})],
    ]))
    card2 = score_agentic(task, res2)
    assert card2["CC"] == 0 and card2["detail"]["critical"] is True


def test_step_budget_terminates():
    # Un modelo que nunca llama finish no debe colgar: corta en max_steps.
    task = load_task(TASK)
    env = env_for_task(task)

    def loop_step(messages, tools):
        return {"content": [_tu("t", "search", {"resourceType": "Condition"})]}
    result = run_agentic(task, env, loop_step, max_steps=3)
    assert result["finished"] is False
    assert result["n_calls"] == 3
