"""Entorno FHIR en memoria para tareas AGÉNTICAS (Fase 4).

A diferencia del régimen single-shot (se le entrega el bundle entero al modelo),
acá el agente NO ve los recursos: debe descubrirlos llamando a herramientas
(`search` / `read`). El entorno registra un LOG DE ACCESOS para puntuar el uso
de herramientas (dimensión AE): ¿buscó la evidencia correcta?, ¿hizo llamadas
innecesarias?, ¿respondió sin mirar datos críticos (inseguro)?

Read-only en v0.1 (sin mutaciones); escribir/actuar llega después.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


def _ref(resource: dict) -> str:
    return f"{resource['resourceType']}/{resource['id']}"


def _summary(resource: dict) -> str:
    """Resumen corto de un recurso para resultados de búsqueda."""
    rt = resource.get("resourceType")
    if rt == "MedicationRequest":
        return f"{resource['medicationCodeableConcept'].get('text','?')} · status={resource.get('status')}"
    if rt == "AllergyIntolerance":
        code = (resource.get("code") or {}).get("text", "?")
        vs = (resource.get("verificationStatus") or {}).get("coding", [{}])[0].get("code", "?")
        return f"allergy to {code} · verification={vs}"
    if rt == "MedicationStatement":
        med = (resource.get("medicationCodeableConcept") or {}).get("text", "?")
        taken = resource.get("status", "?")
        when = resource.get("effectiveDateTime") or (resource.get("effectivePeriod") or {}).get("start", "?")
        return f"{med} · status={taken} · effective={when}"
    if rt == "Condition":
        st = (resource.get("clinicalStatus") or {}).get("coding", [{}])[0].get("code", "?")
        return f"{resource['code'].get('text','?')} · clinicalStatus={st}"
    if rt == "DiagnosticReport":
        return f"{(resource.get('code') or {}).get('text','?')} · status={resource.get('status','?')}"
    if rt == "Observation":
        return f"{resource['code'].get('text','?')}"
    if rt == "Patient":
        return f"{resource.get('gender','?')} born {resource.get('birthDate','?')}"
    if rt == "Encounter":
        return f"{(resource.get('type') or [{}])[0].get('text','?')} · {resource.get('period',{}).get('start','?')}"
    return rt or "?"


@dataclass
class FhirEnv:
    """Entorno consultable sobre un bundle FHIR, con log de accesos."""

    resources: dict[str, dict]                       # ref -> resource
    by_type: dict[str, list[str]]                    # resourceType -> [refs]
    searched_types: list[str] = field(default_factory=list)
    surfaced: set[str] = field(default_factory=set)  # refs vistos por el agente
    read_refs: list[str] = field(default_factory=list)
    call_log: list[dict] = field(default_factory=list)

    @classmethod
    def from_bundle(cls, bundle: dict) -> "FhirEnv":
        resources: dict[str, dict] = {}
        by_type: dict[str, list[str]] = {}
        for entry in bundle.get("entry", []):
            r = entry.get("resource") or {}
            if r.get("resourceType") and r.get("id"):
                ref = _ref(r)
                resources[ref] = r
                by_type.setdefault(r["resourceType"], []).append(ref)
        return cls(resources=resources, by_type=by_type)

    @classmethod
    def from_case(cls, case_dir: str | Path) -> "FhirEnv":
        bundle = json.loads((Path(case_dir) / "bundle.json").read_text(encoding="utf-8"))
        return cls.from_bundle(bundle)

    # --- Herramientas expuestas al agente ---------------------------------- #

    def list_resource_types(self) -> dict:
        self.call_log.append({"tool": "list_resource_types"})
        return {"resource_types": {t: len(refs) for t, refs in self.by_type.items()}}

    def search(self, resourceType: str, text: str | None = None) -> dict:
        self.call_log.append({"tool": "search", "resourceType": resourceType, "text": text})
        self.searched_types.append(resourceType)
        refs = self.by_type.get(resourceType, [])
        results = []
        for ref in refs:
            res = self.resources[ref]
            summ = _summary(res)
            if text and text.lower() not in (summ.lower() + " " + json.dumps(res).lower()):
                continue
            self.surfaced.add(ref)
            results.append({"reference": ref, "summary": summ})
        return {"count": len(results), "results": results}

    def read(self, reference: str) -> dict:
        self.call_log.append({"tool": "read", "reference": reference})
        res = self.resources.get(reference)
        if res is None:
            return {"error": f"no resource '{reference}'"}
        self.surfaced.add(reference)
        self.read_refs.append(reference)
        return {"resource": res}

    # --- Métricas para AE --------------------------------------------------- #

    @property
    def n_calls(self) -> int:
        return len(self.call_log)

    def accessed(self) -> set[str]:
        """Refs que el agente llegó a ver (vía search o read)."""
        return set(self.surfaced)
