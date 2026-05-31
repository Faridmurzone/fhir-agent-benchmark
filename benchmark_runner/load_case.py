"""Carga de un caso del benchmark y validación contra los JSON Schemas."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"

_SCHEMA_FILES = {
    "task": "task.schema.json",
    "ground_truth": "ground_truth.schema.json",
    "scoring": "scoring.schema.json",
}


@lru_cache(maxsize=None)
def _validator(kind: str) -> Draft202012Validator:
    with (SCHEMAS_DIR / _SCHEMA_FILES[kind]).open("r", encoding="utf-8") as fh:
        return Draft202012Validator(json.load(fh))


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@dataclass
class Case:
    case_id: str
    path: Path
    task: dict
    ground_truth: dict
    scoring: dict
    bundle: dict
    renderings: dict[str, Path] = field(default_factory=dict)


def schema_errors(kind: str, instance: dict) -> list[str]:
    """Errores de JSON Schema (lista vacía = válido)."""
    v = _validator(kind)
    return [f"{kind}: {e.message} at /{'/'.join(map(str, e.path))}"
            for e in sorted(v.iter_errors(instance), key=lambda e: list(e.path))]


def load_case(case_dir: str | Path) -> Case:
    """Carga los archivos del caso y valida los tres JSON contra sus schemas.

    Lanza ValueError con todos los errores de schema acumulados si alguno falla.
    """
    case_dir = Path(case_dir)
    task = _read_json(case_dir / "task.json")
    ground_truth = _read_json(case_dir / "ground_truth.json")
    scoring = _read_json(case_dir / "scoring.json")
    bundle = _read_json(case_dir / "bundle.json")

    errors: list[str] = []
    errors += schema_errors("task", task)
    errors += schema_errors("ground_truth", ground_truth)
    errors += schema_errors("scoring", scoring)
    if errors:
        raise ValueError("Schema validation failed:\n  - " + "\n  - ".join(errors))

    renderings = {
        name: case_dir / fname
        for name, fname in (task.get("rendering_files") or {}).items()
    }

    return Case(
        case_id=task["case_id"],
        path=case_dir,
        task=task,
        ground_truth=ground_truth,
        scoring=scoring,
        bundle=bundle,
        renderings=renderings,
    )
