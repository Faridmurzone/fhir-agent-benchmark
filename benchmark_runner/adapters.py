"""Adaptadores de modelo.

Un adaptador toma (case, rendering, prompt) y devuelve un model_output (dict)
con el shape del output_contract. Hay dos baselines que corren SIN credenciales
(oracle y empty) más un adaptador real para Anthropic, gated por API key.
"""

from __future__ import annotations

import json
import os
import re
from typing import Protocol

from .load_case import Case


class Adapter(Protocol):
    name: str

    def answer(self, case: Case, rendering: str, prompt: str) -> dict: ...


def _empty_output(contract: str) -> dict:
    return {
        "entity_list": {"items": []},
        "flag_list": {"flags": []},
        "scalar": {"value": None, "evidence": []},
        "structured": {"fields": {}, "evidence": []},
        "ordered_list": {"sequence": []},
        "abstention": {"abstained": False, "answer": None, "reason": "", "missing": []},
        "fhir_resource": {"resource": {}},
        "fhir_bundle": {"resource": {}},
    }.get(contract, {})


class EmptyAdapter:
    """Baseline cota-inferior: nunca responde nada. Útil como piso y sanity check."""

    name = "empty"

    def answer(self, case: Case, rendering: str, prompt: str) -> dict:
        return _empty_output(case.task["output_contract"])


class OracleAdapter:
    """Baseline cota-superior: copia el ground truth. Mide el techo del harness.

    No es un modelo: sirve para verificar el pipeline y como referencia 100%.
    """

    name = "oracle"

    def answer(self, case: Case, rendering: str, prompt: str) -> dict:
        contract = case.task["output_contract"]
        expected = case.ground_truth.get("expected") or {}
        if contract == "entity_list":
            return {"items": expected.get("items", [])}
        if contract == "flag_list":
            return {"flags": expected.get("flags", [])}
        if contract == "ordered_list":
            return {"sequence": expected.get("sequence", [])}
        if contract == "scalar":
            return {"value": expected.get("value"), "evidence": expected.get("evidence", [])}
        if contract == "structured":
            return {"fields": expected.get("fields", {}), "evidence": expected.get("evidence", [])}
        if contract == "abstention":
            return {
                "abstained": expected.get("abstained", False),
                "answer": expected.get("answer"),
                "reason": expected.get("reason", ""),
                "missing": expected.get("missing", []),
            }
        if contract in ("fhir_resource", "fhir_bundle"):
            return {"resource": expected.get("resource", {})}
        return {}


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def parse_model_json(text: str) -> dict:
    """Extrae el primer objeto JSON de la respuesta del modelo (tolera ```fences```)."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):] if "{" in text else text
    m = _JSON_BLOCK.search(text)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


class AnthropicAdapter:
    """Adaptador real para Claude. Gated por ANTHROPIC_API_KEY.

    Si no hay API key o el SDK no está instalado, `available` es False y el
    runner lo saltea limpiamente (igual patrón de degradación que el resto).
    """

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("LLM_MODEL", "claude-opus-4-8")
        self.name = f"anthropic:{self.model}"
        self._client = None
        key = os.getenv("ANTHROPIC_API_KEY")
        if key:
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=key)
            except Exception:
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def answer(self, case: Case, rendering: str, prompt: str) -> dict:
        if not self.available:
            raise RuntimeError("AnthropicAdapter no disponible (falta ANTHROPIC_API_KEY o SDK)")
        from .prompts import system_prompt

        msg = self._client.messages.create(  # type: ignore[union-attr]
            model=self.model,
            max_tokens=1500,
            system=system_prompt(),
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return parse_model_json(text)


def get_adapter(name: str) -> Adapter:
    if name == "empty":
        return EmptyAdapter()
    if name == "oracle":
        return OracleAdapter()
    if name.startswith("anthropic"):
        model = name.split(":", 1)[1] if ":" in name else None
        return AnthropicAdapter(model)
    raise ValueError(f"adaptador desconocido: {name}")
