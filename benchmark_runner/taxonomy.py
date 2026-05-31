"""Acceso a la taxonomía machine-readable (taxonomy/taxonomy.json)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = ROOT / "taxonomy" / "taxonomy.json"


@lru_cache(maxsize=1)
def load_taxonomy() -> dict:
    with TAXONOMY_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def capabilities_by_id() -> dict[str, dict]:
    return {c["id"]: c for c in load_taxonomy()["capabilities"]}


def get_capability(cap_id: str) -> dict | None:
    return capabilities_by_id().get(cap_id)
