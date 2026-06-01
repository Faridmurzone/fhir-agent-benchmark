#!/usr/bin/env python3
"""Verifica TODOS los códigos terminológicos del benchmark contra fuentes OFICIALES.

Por qué existe: un benchmark cuyos datos los redacta (parcialmente) un LLM puede
contener códigos plausibles pero incorrectos — el código existe pero apunta a otro
fármaco/dosis/concepto que el `display` que lo acompaña. Como el scorer matchea por
código, un modelo que repite el mismo error de memoria "acierta" un gold erróneo
(sesgo de errores correlacionados). Este verificador rompe ese sesgo usando
autoridades externas, independientes del proyecto:

  - RxNorm  -> RxNav REST (https://rxnav.nlm.nih.gov), sin auth.
  - LOINC   -> NLM clinical-tables (https://clinicaltables.nlm.nih.gov), sin auth.
  - SNOMED  -> FHIR $lookup en tx.fhir.org (servidor de terminología HL7).

Recolecta cada coding {system, code, display} de cases/ y agentic_tasks/, resuelve
el nombre oficial del código y marca:
  - INVALID : el código no existe en la fuente.
  - MISMATCH: existe, pero el nombre oficial difiere del display (posible código
              equivocado). Heurística de similitud de tokens; revisar a mano.

Uso:
    python scripts/verify_terminology.py                # verifica todo (red)
    python scripts/verify_terminology.py --json out.json
Salida con código 1 si hay algún INVALID (apto para CI con red).
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
LOINC = "http://loinc.org"
SNOMED = "http://snomed.info/sct"
TIMEOUT = 25


def collect_codings(paths: list[str]) -> dict[str, set[tuple[str, str]]]:
    by_system: dict[str, set[tuple[str, str]]] = {}

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("coding"), list):
                for c in node["coding"]:
                    if isinstance(c, dict) and c.get("system") and c.get("code"):
                        by_system.setdefault(c["system"], set()).add(
                            (str(c["code"]), c.get("display") or ""))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for f in paths:
        try:
            walk(json.load(open(f)))
        except Exception:
            pass
    return by_system


# --- Resolución oficial por sistema ---------------------------------------- #

def resolve_rxnorm(code: str) -> str | None:
    r = requests.get(f"https://rxnav.nlm.nih.gov/REST/rxcui/{code}/property.json",
                     params={"propName": "RxNorm Name"}, timeout=TIMEOUT)
    props = (r.json().get("propConceptGroup") or {}).get("propConcept") or []
    return props[0]["propValue"] if props else None


def resolve_loinc(code: str) -> str | None:
    r = requests.get("https://clinicaltables.nlm.nih.gov/api/loinc_items/v3/search",
                     params={"terms": code, "df": "LOINC_NUM,LONG_COMMON_NAME", "maxList": 7},
                     timeout=TIMEOUT)
    rows = r.json()[3] if len(r.json()) > 3 else []
    hit = [x for x in rows if x[0] == code]
    return hit[0][1] if hit else None


def resolve_snomed(code: str) -> str | None:
    for srv in ("https://tx.fhir.org/r4", "https://r4.ontoserver.csiro.au/fhir"):
        try:
            r = requests.get(f"{srv}/CodeSystem/$lookup",
                             params={"system": SNOMED, "code": code},
                             headers={"Accept": "application/json"}, timeout=TIMEOUT)
            if r.status_code == 200:
                for p in r.json().get("parameter", []):
                    if p.get("name") == "display":
                        return p.get("valueString")
        except requests.RequestException:
            continue
    return None


UNREACHABLE = object()  # sentinel: no se pudo consultar la fuente (≠ inexistente)


def _safe(resolver, code):
    """Envuelve un resolver: ante error de red devuelve UNREACHABLE (no None)."""
    for _ in range(3):
        try:
            return resolver(code)
        except requests.RequestException:
            continue
        except Exception:
            return None
    return UNREACHABLE


_RESOLVERS = {RXNORM: resolve_rxnorm, LOINC: resolve_loinc, SNOMED: resolve_snomed}
_STOP = {"oral", "tablet", "mg", "ml", "in", "of", "the", "and", "by", "or", "blood",
         "serum", "plasma", "hr", "release", "delayed", "capsule"}


def _tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in _STOP and len(t) > 2}


def classify(display: str, official) -> str:
    if official is UNREACHABLE:
        return "UNKNOWN"
    if official is None:
        return "INVALID"
    dt, ot = _tokens(display), _tokens(official)
    if not dt:
        return "OK"
    overlap = len(dt & ot) / len(dt)
    return "OK" if overlap >= 0.5 else "MISMATCH"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="volcar el reporte completo a un archivo")
    args = ap.parse_args(argv)

    paths = glob.glob(str(ROOT / "cases" / "*" / "*.json")) + \
        glob.glob(str(ROOT / "agentic_tasks" / "*.json"))
    by_system = collect_codings(paths)

    report = []
    n = {"INVALID": 0, "MISMATCH": 0, "UNKNOWN": 0, "OK": 0}
    for system, items in by_system.items():
        resolver = _RESOLVERS.get(system)
        if not resolver:
            continue
        label = {RXNORM: "RxNorm", LOINC: "LOINC", SNOMED: "SNOMED"}[system]
        for code, display in sorted(items):
            official = _safe(resolver, code)
            verdict = classify(display, official)
            n[verdict] += 1
            if verdict != "OK":
                off = "(unreachable)" if official is UNREACHABLE else official
                print(f"[{verdict}] {label} {code}: benchmark='{display}'  official='{off}'")
            report.append({"system": label, "code": code, "display": display,
                           "official": None if official is UNREACHABLE else official,
                           "verdict": verdict})

    total = len(report)
    print(f"\n{total} codings · OK={n['OK']} MISMATCH={n['MISMATCH']} "
          f"INVALID={n['INVALID']} UNKNOWN(net)={n['UNKNOWN']}")
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if n["INVALID"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
