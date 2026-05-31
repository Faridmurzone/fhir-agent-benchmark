"""Generador sintético de casos para el FHIR Agent Benchmark.

Produce casos en la misma forma que ``cases/pf-fhir-agent-0001`` y que pasan
``benchmark_runner.validate_case.validate_case``. El objetivo primario es la
capacidad MR-01 (``medication_reconciliation.active_medication_list``).

El generador es totalmente determinista: misma semilla + mismos parámetros
producen un caso byte-idéntico. No usa ``datetime.now()`` ni estado global de
aleatoriedad; toda la aleatoriedad pasa por ``random.Random(seed)`` y las
fechas se derivan de la semilla a partir de un año base fijo (2025).
"""

from __future__ import annotations

from .patient_generator import build_patient
from .emit_case import emit_case, main

__all__ = ["build_patient", "emit_case", "main"]
