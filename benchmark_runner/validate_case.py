"""Chequeos de consistencia interna de un caso (más allá del JSON Schema).

Verifica:
- coherencia de case_id entre archivos y nombre de carpeta;
- la capacidad existe en la taxonomía y slug/contrato/dimensiones coinciden;
- el bundle es un FHIR Bundle y se puede indexar por "ResourceType/id";
- TODA referencia de evidencia (en expected, must_exclude y safety_events)
  resuelve a un recurso presente en el bundle (integridad referencial);
- los resource_types declarados en task aparecen en el bundle;
- los renderings declarados existen en disco;
- la forma de `expected` coincide con el output_contract de la capacidad.
"""

from __future__ import annotations

from pathlib import Path

from .load_case import Case, load_case
from .taxonomy import get_capability

# Validadores de forma por contrato de output.
_CONTRACT_REQUIRED = {
    "entity_list": ("items", list),
    "flag_list": ("flags", list),
    "scalar": ("value", None),
    "structured": ("fields", dict),
    "ordered_list": ("sequence", list),
    "fhir_resource": ("resource", dict),
    "fhir_bundle": ("resource", dict),
}


def _bundle_index(bundle: dict) -> set[str]:
    """Conjunto de referencias "ResourceType/id" presentes en el bundle."""
    refs: set[str] = set()
    for entry in bundle.get("entry", []):
        res = entry.get("resource") or {}
        rtype, rid = res.get("resourceType"), res.get("id")
        if rtype and rid:
            refs.add(f"{rtype}/{rid}")
    return refs


def _bundle_resource_types(bundle: dict) -> set[str]:
    return {(e.get("resource") or {}).get("resourceType")
            for e in bundle.get("entry", [])} - {None}


def _collect_evidence(ground_truth: dict) -> list[str]:
    refs: list[str] = []
    expected = ground_truth.get("expected") or {}
    for key in ("items", "flags", "must_exclude"):
        for item in expected.get(key, []) or []:
            refs += item.get("evidence", []) or []
    for ref in ("value",):  # scalar evidence lives alongside the value
        pass
    refs += expected.get("evidence", []) or []
    for ev in ground_truth.get("safety_events", []) or []:
        refs += ev.get("evidence", []) or []
    return refs


def _check_expected_shape(contract: str, expected: dict) -> list[str]:
    if contract == "abstention":
        if not isinstance(expected.get("abstained"), bool):
            return ["expected.abstained must be a boolean for abstention contract"]
        return []
    # Generación: el gold puede declarar el recurso esperado, o aserciones por
    # path, o campos planos. Cualquiera de los tres es válido.
    if contract in ("fhir_resource", "fhir_bundle"):
        if not any(k in expected for k in ("resource", "assertions", "fields")):
            return [f"expected for '{contract}' needs one of: resource, assertions, fields"]
        if "assertions" in expected and not isinstance(expected["assertions"], list):
            return ["expected.assertions must be a list"]
        return []
    spec = _CONTRACT_REQUIRED.get(contract)
    if not spec:
        return [f"unknown output_contract '{contract}'"]
    key, typ = spec
    if key not in expected:
        return [f"expected.{key} is required for contract '{contract}'"]
    if typ is not None and not isinstance(expected[key], typ):
        return [f"expected.{key} must be of type {typ.__name__} for contract '{contract}'"]
    return []


def validate_case(case_dir: str | Path) -> list[str]:
    """Devuelve una lista de errores (vacía = caso válido)."""
    case_dir = Path(case_dir)
    errors: list[str] = []

    try:
        case: Case = load_case(case_dir)
    except ValueError as exc:
        return str(exc).splitlines()

    # 1. Coherencia de case_id.
    expected_id = case_dir.name
    for label, doc in (("task", case.task), ("ground_truth", case.ground_truth),
                       ("scoring", case.scoring)):
        if doc["case_id"] != expected_id:
            errors.append(f"{label}.case_id '{doc['case_id']}' != folder name '{expected_id}'")

    # 2. Capacidad / contrato / dimensiones contra la taxonomía.
    cap_id = case.task["capability"]["id"]
    cap = get_capability(cap_id)
    if cap is None:
        errors.append(f"capability '{cap_id}' not found in taxonomy")
    else:
        if case.task["capability"]["slug"] != cap["slug"]:
            errors.append(f"task capability slug '{case.task['capability']['slug']}' "
                          f"!= taxonomy slug '{cap['slug']}'")
        if case.task["output_contract"] != cap["output_contract"]:
            errors.append(f"task output_contract '{case.task['output_contract']}' "
                          f"!= taxonomy '{cap['output_contract']}' for {cap_id}")
        if case.ground_truth["output_contract"] != cap["output_contract"]:
            errors.append(f"ground_truth output_contract != taxonomy '{cap['output_contract']}'")
        extra_dims = set(case.scoring["dimensions"]) - set(cap["dimensions"])
        if extra_dims:
            errors.append(f"scoring dimensions {sorted(extra_dims)} not allowed for "
                          f"{cap_id} (allowed: {cap['dimensions']})")
    for doc_label in ("ground_truth", "scoring"):
        if getattr(case, doc_label)["capability_id"] != cap_id:
            errors.append(f"{doc_label}.capability_id != task capability id '{cap_id}'")

    # 3. Bundle.
    if case.bundle.get("resourceType") != "Bundle":
        errors.append("bundle.json resourceType is not 'Bundle'")
    index = _bundle_index(case.bundle)
    if not index:
        errors.append("bundle has no resolvable resources (ResourceType/id)")

    # 4. Integridad referencial de la evidencia.
    for ref in _collect_evidence(case.ground_truth):
        if ref not in index:
            errors.append(f"evidence reference '{ref}' does not resolve in bundle")

    # 5. resource_types declarados presentes.
    present = _bundle_resource_types(case.bundle)
    for rtype in case.task.get("resource_types", []):
        if rtype not in present:
            errors.append(f"declared resource_type '{rtype}' absent from bundle")

    # 6. Renderings existen.
    for name in case.task.get("available_renderings", []):
        path = case.renderings.get(name)
        if path is None:
            errors.append(f"rendering '{name}' has no entry in rendering_files")
        elif not path.exists():
            errors.append(f"rendering file for '{name}' not found: {path.name}")

    # 7. Forma de expected vs contrato.
    errors += _check_expected_shape(case.ground_truth["output_contract"],
                                    case.ground_truth.get("expected") or {})

    return errors


def discover_cases(cases_dir: str | Path) -> list[Path]:
    cases_dir = Path(cases_dir)
    return sorted(p for p in cases_dir.glob("pf-fhir-agent-*") if p.is_dir())
