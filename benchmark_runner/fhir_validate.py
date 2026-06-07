"""Validación FHIR R4 INDEPENDIENTE vía `fhir.resources` (modelos oficiales HL7).

Por qué existe: la dimensión FV no debe depender de un validador casero (sería
juez y parte — el mismo proyecto que produce el benchmark decidiría qué es FHIR
válido). `fhir.resources` genera sus modelos a partir de las StructureDefinitions
oficiales de FHIR R4B, así que valida cardinalidades, choice types (`value[x]`,
`medication[x]`), datatypes y elementos requeridos contra el spec real.

Es OPCIONAL: si la librería no está instalada, `available()` es False y el
scorer cae a su validador heurístico (degradación documentada, sin romper la
portabilidad del repo).
"""

from __future__ import annotations

import importlib
from functools import lru_cache


@lru_cache(maxsize=1)
def available() -> bool:
    try:
        importlib.import_module("fhir.resources.R4B.fhirtypes")
        return True
    except Exception:
        return False


def validate(resource: dict, version: str = "R4") -> tuple[bool, list[str]]:
    """Valida un recurso contra los modelos oficiales FHIR.

    ``version``: "R4" (modelos R4B, default) o "R5" (modelos top-level de
    `fhir.resources`, que desde 7.x son R5). Permite scorear tareas de
    migración R4→R5 (TX-05) con la misma autoridad independiente.

    Devuelve (ok, errores). Si la librería no está disponible, devuelve
    (True, ["validator_unavailable"]) para que el caller use su fallback.
    """
    if not available():
        return True, ["validator_unavailable"]
    rt = (resource or {}).get("resourceType")
    if not rt:
        return False, ["missing resourceType"]
    pkg = "fhir.resources" if version == "R5" else "fhir.resources.R4B"
    try:
        mod = importlib.import_module(f"{pkg}.{rt.lower()}")
    except ModuleNotFoundError:
        return False, [f"unknown {version} resourceType '{rt}'"]
    cls = getattr(mod, rt, None)
    if cls is None:
        return False, [f"unknown {version} resourceType '{rt}'"]
    try:
        cls.model_validate(resource)
        return True, []
    except Exception as exc:  # pydantic ValidationError u otros
        errs = [l.strip() for l in str(exc).splitlines() if l.strip()]
        # Compactar: primera línea (conteo) + hasta 6 mensajes de error.
        return False, errs[:8]
