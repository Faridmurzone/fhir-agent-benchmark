"""Primitivas de métricas para el scoring del benchmark.

Implementa fielmente las primitivas descritas en docs/SCORING.md:

- ``set_f1``        : F1 de conjuntos sobre identidad codificada (system+code),
                      con label_fallback opcional. Maneja la regla del gold vacío.
- ``scalar_match``  : igualdad exacta normalizada (fechas a la granularidad
                      declarada, códigos por system+code).
- ``ordered_score`` : score de orden por pares (estilo Kendall-τ).
- ``structured_match``: igualdad exacta por campo, promediada.

Todas devuelven un float 0..100 más un dict con detalle suficiente para
depurar. Solo stdlib.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Iterable


# --------------------------------------------------------------------------- #
# Resultado común
# --------------------------------------------------------------------------- #

@dataclass
class MetricResult:
    """Resultado de una primitiva: score 0..100 + detalle de depuración."""

    score: float
    detail: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Normalización
# --------------------------------------------------------------------------- #

def normalize_label(value: Any) -> str:
    """Normaliza una etiqueta de texto: minúsculas, espacios colapsados, trim."""
    if value is None:
        return ""
    text = str(value).strip().lower()
    return re.sub(r"\s+", " ", text)


def normalize_date(value: str, granularity: str = "day") -> str:
    """Trunca una fecha/datetime ISO a la granularidad declarada.

    Granularidades: year | month | day | instant. Si el valor no parece una
    fecha ISO, se devuelve normalizado como texto.
    """
    if value is None:
        return ""
    text = str(value).strip()
    # Captura el prefijo de fecha YYYY[-MM[-DD]] y opcional hora.
    m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", text)
    if not m:
        return normalize_label(text)
    year, month, day = m.group(1), m.group(2), m.group(3)
    if granularity == "year":
        return year
    if granularity == "month":
        return f"{year}-{month}" if month else year
    if granularity == "day":
        parts = [year]
        if month:
            parts.append(month)
        if day:
            parts.append(day)
        return "-".join(parts)
    # instant: compara la cadena completa normalizada.
    return text


def _code_key(code: Any) -> tuple[str, str] | None:
    """Clave de identidad codificada (system, code) si el código está presente."""
    if not isinstance(code, dict):
        return None
    system = code.get("system")
    value = code.get("code")
    if system is None or value is None:
        return None
    return (str(system).strip(), str(value).strip())


def entity_identity(entity: dict, label_fallback: bool = False) -> Any:
    """Identidad de una entidad para el matcheo de conjuntos.

    Prioriza la identidad codificada (system+code). Si no hay código y
    ``label_fallback`` está activo, usa la etiqueta normalizada. Si no hay
    nada utilizable, devuelve un objeto único (nunca matchea).
    """
    key = _code_key(entity.get("code"))
    if key is not None:
        return ("code", key)
    if label_fallback:
        label = normalize_label(entity.get("label"))
        if label:
            return ("label", label)
    return ("unmatchable", id(entity))


def _evidence_set(entity: dict) -> set[str]:
    return {str(r).strip() for r in (entity.get("evidence") or []) if str(r).strip()}


def entities_match(pred: dict, gold: dict) -> bool:
    """Predicado de match para entidades clínicas (entity_list).

    Dos entidades refieren al mismo hecho clínico si coincide CUALQUIERA de:
      - el código (system+code),
      - alguna referencia de evidencia (mismo recurso FHIR citado),
      - la etiqueta normalizada.
    Esto vuelve comparables los renderings que no exponen códigos (narrativa,
    timeline) con los que sí (FHIR JSON, tabla). Ver docs/SCORING.md.
    """
    pk, gk = _code_key(pred.get("code")), _code_key(gold.get("code"))
    if pk is not None and pk == gk:
        return True
    if _evidence_set(pred) & _evidence_set(gold):
        return True
    pl, gl = normalize_label(pred.get("label")), normalize_label(gold.get("label"))
    return bool(pl) and pl == gl


def flags_match(pred: dict, gold: dict) -> bool:
    """Predicado de match para flags (flag_list).

    Un flag matchea el gold si comparten al menos una referencia de evidencia
    (marcaron el/los mismo(s) recurso(s)). No se exige que el `type` en texto
    libre coincida: lo importante es señalar los recursos correctos. La
    severidad se evalúa en la dimensión de Safety, no acá.
    """
    return bool(_evidence_set(pred) & _evidence_set(gold))


# --------------------------------------------------------------------------- #
# Set F1 (entity_list / flag_list)
# --------------------------------------------------------------------------- #

def set_f1(
    predicted: Iterable[dict],
    gold: Iterable[dict],
    *,
    label_fallback: bool = False,
    identity_fn=None,
    match_fn=None,
) -> MetricResult:
    """F1 de conjuntos.

    - ``predicted`` / ``gold`` son listas de entidades (dicts con ``code`` y/o
      ``label``, opcionalmente ``evidence``).
    - Si se pasa ``match_fn(pred, gold) -> bool`` se usa matcheo por predicado
      (greedy, 1-a-1); si no, por identidad codificada (system+code) con
      ``label_fallback`` opcional.
    - Regla del gold vacío: gold ∅ y predicho ∅ -> 100; gold ∅ y predicho no
      vacío -> 0.

    Devuelve score = 100·F1 y detalle con precision/recall y los matches.
    """
    pred = list(predicted or [])
    gld = list(gold or [])

    if match_fn is not None:
        used = [False] * len(gld)
        tp = 0
        for p in pred:
            for i, g in enumerate(gld):
                if not used[i] and match_fn(p, g):
                    used[i] = True
                    tp += 1
                    break
        matched_ids = [f"match_{i}" for i in range(tp)]  # placeholder para detalle
    else:
        ident = identity_fn or (lambda e: entity_identity(e, label_fallback))
        pred_ids = [ident(e) for e in pred]
        gold_pool = [ident(e) for e in gld]
        matched_ids = []
        for pid in pred_ids:
            if pid in gold_pool:
                gold_pool.remove(pid)
                matched_ids.append(pid)
        tp = len(matched_ids)

    # Regla del gold vacío.
    if not gld:
        score = 100.0 if not pred else 0.0
        return MetricResult(
            score,
            {
                "rule": "empty_gold",
                "predicted_n": len(pred),
                "gold_n": 0,
                "precision": (0.0 if pred else 1.0),
                "recall": 1.0,
                "f1": (0.0 if pred else 1.0),
                "tp": 0,
            },
        )

    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(gld) if gld else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return MetricResult(
        100.0 * f1,
        {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "predicted_n": len(pred),
            "gold_n": len(gld),
            "matched_identities": [list(m) if isinstance(m, tuple) else m for m in matched_ids],
        },
    )


def matched_gold_elements(
    predicted: Iterable[dict],
    gold: Iterable[dict],
    *,
    label_fallback: bool = False,
    identity_fn=None,
    match_fn=None,
) -> list[tuple[dict, dict]]:
    """Empareja elementos gold con su predicho correspondiente.

    Con ``match_fn`` usa matcheo por predicado (greedy); si no, por identidad.
    Devuelve pares (gold_element, predicted_element) cuyo answer es correcto.
    Usado por TRC: la evidencia solo se acredita en elementos correctos.
    """
    pred = list(predicted or [])
    gld = list(gold or [])

    if match_fn is not None:
        used = [False] * len(pred)
        pairs: list[tuple[dict, dict]] = []
        for g in gld:
            for i, p in enumerate(pred):
                if not used[i] and match_fn(p, g):
                    used[i] = True
                    pairs.append((g, p))
                    break
        return pairs

    ident = identity_fn or (lambda e: entity_identity(e, label_fallback))
    pred_by_id: dict[Any, list[dict]] = {}
    for e in pred:
        pred_by_id.setdefault(ident(e), []).append(e)

    pairs = []
    for g in gld:
        gid = ident(g)
        bucket = pred_by_id.get(gid)
        if bucket:
            pairs.append((g, bucket.pop(0)))
    return pairs


# --------------------------------------------------------------------------- #
# Scalar
# --------------------------------------------------------------------------- #

def scalar_match(
    predicted: Any,
    gold: Any,
    *,
    date_granularity: str = "day",
    is_date: bool | None = None,
) -> MetricResult:
    """Igualdad exacta normalizada de un escalar.

    - Códigos (dicts con system+code) se comparan por identidad codificada.
    - Fechas se comparan a la granularidad declarada.
    - El resto se compara como texto normalizado.
    """
    # Código.
    pk, gk = _code_key(predicted), _code_key(gold)
    if gk is not None or pk is not None:
        match = pk is not None and pk == gk
        return MetricResult(
            100.0 if match else 0.0,
            {"kind": "code", "predicted": pk, "gold": gk, "match": match},
        )

    def _looks_like_date(v: Any) -> bool:
        return isinstance(v, str) and bool(re.match(r"^\d{4}(-\d{2}){0,2}", v.strip()))

    use_date = is_date if is_date is not None else (_looks_like_date(gold) and _looks_like_date(predicted))
    if use_date:
        np = normalize_date(predicted, date_granularity)
        ng = normalize_date(gold, date_granularity)
        match = np == ng and ng != ""
        return MetricResult(
            100.0 if match else 0.0,
            {"kind": "date", "predicted": np, "gold": ng, "granularity": date_granularity, "match": match},
        )

    np_, ng_ = normalize_label(predicted), normalize_label(gold)
    match = np_ == ng_
    return MetricResult(
        100.0 if match else 0.0,
        {"kind": "scalar", "predicted": np_, "gold": ng_, "match": match},
    )


# --------------------------------------------------------------------------- #
# Ordered list (Kendall-τ por pares)
# --------------------------------------------------------------------------- #

def ordered_score(predicted: list[Any], gold: list[Any]) -> MetricResult:
    """Fracción de pares correctamente ordenados (estilo Kendall-τ).

    Se consideran únicamente los pares del gold cuyos dos elementos están
    presentes en el predicho. Un par (a, b) (a antes que b en el gold) está
    bien ordenado si a aparece antes que b en el predicho.

    - Gold con < 2 elementos: no hay pares que ordenar -> 100 si el conjunto de
      elementos presentes coincide razonablemente; aquí devolvemos 100 si el
      predicho contiene exactamente esos elementos, si no la fracción presente.
    """
    pred = list(predicted or [])
    gold = list(gold or [])

    pred_pos = {item: i for i, item in enumerate(pred)}

    pairs = list(combinations(gold, 2))
    if not pairs:
        # 0 o 1 elemento: no hay orden que evaluar; puntúa por presencia.
        if not gold:
            score = 100.0 if not pred else 0.0
            return MetricResult(score, {"reason": "empty_gold", "pred_n": len(pred)})
        present = 1.0 if gold[0] in pred_pos else 0.0
        return MetricResult(100.0 * present, {"reason": "single_element", "present": bool(present)})

    correct = 0
    evaluable = 0
    for a, b in pairs:
        if a in pred_pos and b in pred_pos:
            evaluable += 1
            if pred_pos[a] < pred_pos[b]:
                correct += 1

    if evaluable == 0:
        # Ningún par del gold es evaluable (faltan elementos) -> 0.
        return MetricResult(0.0, {"total_pairs": len(pairs), "evaluable_pairs": 0, "correct_pairs": 0})

    frac = correct / evaluable
    return MetricResult(
        100.0 * frac,
        {
            "total_pairs": len(pairs),
            "evaluable_pairs": evaluable,
            "correct_pairs": correct,
            "fraction": frac,
        },
    )


# --------------------------------------------------------------------------- #
# Structured (igualdad por campo, promediada)
# --------------------------------------------------------------------------- #

def structured_match(
    predicted: dict,
    gold: dict,
    *,
    date_granularity: str = "day",
    field_weights: dict[str, float] | None = None,
) -> MetricResult:
    """Igualdad exacta por campo, promediada sobre los campos del gold.

    Cada campo del gold se compara con ``scalar_match`` (códigos, fechas y
    texto). Por defecto todos pesan igual; ``field_weights`` permite override.
    """
    pred = predicted or {}
    gld = gold or {}

    if not gld:
        return MetricResult(100.0, {"reason": "empty_gold_fields"})

    weights = field_weights or {}
    per_field: dict[str, dict[str, Any]] = {}
    total_w = 0.0
    acc = 0.0
    for key, gold_val in gld.items():
        w = float(weights.get(key, 1.0))
        res = scalar_match(pred.get(key), gold_val, date_granularity=date_granularity)
        per_field[key] = {"score": res.score, **res.detail, "weight": w}
        acc += w * res.score
        total_w += w

    score = acc / total_w if total_w else 0.0
    return MetricResult(score, {"fields": per_field, "n_fields": len(gld)})


# --------------------------------------------------------------------------- #
# Evidence helpers (TRC)
# --------------------------------------------------------------------------- #

def _ref_entity(ref: str) -> dict:
    """Envuelve una referencia FHIR como entidad con label = la referencia.

    Permite reutilizar set_f1 con label_fallback para comparar conjuntos de
    referencias de evidencia.
    """
    return {"label": str(ref).strip(), "code": None}


def evidence_f1(predicted_refs: Iterable[str], gold_refs: Iterable[str]) -> MetricResult:
    """F1 de conjuntos sobre referencias de evidencia (cadenas 'Type/id')."""
    pred = [_ref_entity(r) for r in (predicted_refs or [])]
    gold = [_ref_entity(r) for r in (gold_refs or [])]
    return set_f1(pred, gold, label_fallback=True)
