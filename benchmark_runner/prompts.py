"""Construcción del prompt que se le envía al modelo, por rendering.

El prompt combina: la instrucción de la tarea + los datos del paciente en el
rendering elegido + una especificación EXACTA del formato JSON de salida según
el output_contract. El objetivo es que el output del modelo sea parseable y
comparable de forma determinística (ver SCORING.md).
"""

from __future__ import annotations

from .load_case import Case

# Especificación del shape de salida por contrato (lo que se le pide al modelo).
_CONTRACT_SPEC = {
    "entity_list": (
        '{"items": [{"label": "...", '
        '"code": {"system": "<url>", "code": "<code>"}, '
        '"status": "active", "evidence": ["ResourceType/id", ...]}]}'
    ),
    "flag_list": (
        '{"flags": [{"type": "...", "severity": "critical|major|minor", '
        '"description": "...", "evidence": ["ResourceType/id", ...]}]}  '
        '(devolvé {"flags": []} si no hay nada que marcar)'
    ),
    "scalar": '{"value": "<value or ResourceType/id>", "evidence": ["ResourceType/id"]}',
    "structured": '{"fields": {"<field>": <value>}, "evidence": ["ResourceType/id"]}',
    "ordered_list": '{"sequence": ["ResourceType/id", ...]}  (en el orden correcto)',
    "abstention": (
        '{"abstained": true|false, "answer": <answer or null>, '
        '"reason": "...", "missing": ["..."]}'
    ),
    "fhir_resource": '{"resource": { ...recurso FHIR válido (R4 salvo que la instrucción pida otra versión)... }}',
    "fhir_bundle": '{"resource": { "resourceType": "Bundle", ... }}',
}

_SYSTEM = (
    "You are a clinical data agent operating over HL7 FHIR resources "
    "(R4 unless the task specifies another version). "
    "Answer strictly from the data provided. Cite source resources as evidence "
    "using \"ResourceType/id\" references. Do not invent clinical facts. "
    "If the data is insufficient to answer safely, say so."
)


def system_prompt() -> str:
    return _SYSTEM


def render_prompt(case: Case, rendering: str) -> str:
    """Prompt de usuario para un caso y un rendering dado."""
    path = case.renderings.get(rendering)
    if path is None or not path.exists():
        raise ValueError(f"rendering '{rendering}' no disponible para {case.case_id}")
    content = path.read_text(encoding="utf-8")

    contract = case.task["output_contract"]
    spec = _CONTRACT_SPEC.get(contract, "{}")
    instruction = case.task["instruction"]

    return (
        f"# Task\n{instruction}\n\n"
        f"# Patient data (format: {rendering})\n{content}\n\n"
        f"# Response format\n"
        f"Respond with ONLY a single JSON object, no prose, matching exactly:\n"
        f"{spec}\n"
    )
