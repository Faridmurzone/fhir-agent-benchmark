"""Adaptadores de modelo.

Un adaptador toma (case, rendering, prompt) y devuelve un model_output (dict)
con el shape del output_contract. Hay dos baselines que corren SIN credenciales
(oracle y empty) más un adaptador real para Anthropic, gated por API key.
"""

from __future__ import annotations

import json
import os
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
            # Para generación, el gold puede traer un recurso de referencia
            # ejemplar (reference_resource) que satisface las aserciones.
            return {"resource": expected.get("reference_resource") or expected.get("resource", {})}
        return {}


def parse_model_json(text: str) -> dict:
    """Extrae el primer objeto JSON de la respuesta del modelo (tolera ```fences```).

    Usa ``raw_decode`` para tomar el PRIMER objeto JSON completo a partir de la
    primera ``{``, ignorando lo que venga después. Esto tolera dos defectos
    comunes de serialización que de otro modo el scorer convertiría en un 0
    espurio (sesgo del instrumento, no del modelo — METHODOLOGY_LESSONS):
      - prosa o texto extra después del JSON,
      - una llave de cierre de más al final (observado en GPT-5.5: ``...}}}``).
    Antes el regex greedy ``\\{.*\\}`` capturaba hasta la ÚLTIMA llave, así que
    una ``}`` sobrante invalidaba todo el objeto.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):] if "{" in text else text
    start = text.find("{")
    if start == -1:
        return {}
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
        return obj if isinstance(obj, dict) else {}
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


class OpenAIAdapter:
    """Adaptador para OpenAI (GPT). Gated por OPENAI_API_KEY."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.5")
        self.name = f"openai:{self.model}"
        self._client = None
        key = os.getenv("OPENAI_API_KEY")
        if key:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=key)
            except Exception:
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def answer(self, case: Case, rendering: str, prompt: str) -> dict:
        if not self.available:
            raise RuntimeError("OpenAIAdapter no disponible (falta OPENAI_API_KEY o SDK)")
        from .prompts import system_prompt

        messages = [
            {"role": "system", "content": system_prompt()},
            {"role": "user", "content": prompt},
        ]
        # Los modelos GPT-5.x / o-series usan `max_completion_tokens` (y no
        # aceptan `max_tokens`); los GPT-4.x usan `max_tokens`. Probamos el nuevo
        # parámetro y caemos al viejo si el modelo lo rechaza.
        budget = 4000  # los modelos razonadores gastan tokens en reasoning
        try:
            resp = self._client.chat.completions.create(  # type: ignore[union-attr]
                model=self.model, max_completion_tokens=budget, messages=messages)
        except Exception as exc:
            if "max_completion_tokens" in str(exc) or "max_tokens" in str(exc):
                resp = self._client.chat.completions.create(  # type: ignore[union-attr]
                    model=self.model, max_tokens=1500, messages=messages)
            else:
                raise
        return parse_model_json(resp.choices[0].message.content or "")


class GeminiAdapter:
    """Adaptador para Google Gemini. Gated por GOOGLE_API_KEY."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        self.name = f"gemini:{self.model}"
        self._client = None
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if key:
            try:
                from google import genai

                self._client = genai.Client(api_key=key)
            except Exception:
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def answer(self, case: Case, rendering: str, prompt: str) -> dict:
        if not self.available:
            raise RuntimeError("GeminiAdapter no disponible (falta GOOGLE_API_KEY o SDK)")
        from google.genai import types

        from .prompts import system_prompt

        resp = self._client.models.generate_content(  # type: ignore[union-attr]
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt()),
        )
        return parse_model_json(resp.text or "")


def get_adapter(name: str) -> Adapter:
    if name == "empty":
        return EmptyAdapter()
    if name == "oracle":
        return OracleAdapter()
    if name.startswith("anthropic"):
        return AnthropicAdapter(name.split(":", 1)[1] if ":" in name else None)
    if name.startswith("openai"):
        return OpenAIAdapter(name.split(":", 1)[1] if ":" in name else None)
    if name.startswith("gemini"):
        return GeminiAdapter(name.split(":", 1)[1] if ":" in name else None)
    raise ValueError(f"adaptador desconocido: {name}")
