"""Punto de entrada CLI: ``python -m generator ...``."""

from __future__ import annotations

from .emit_case import main

if __name__ == "__main__":
    raise SystemExit(main())
