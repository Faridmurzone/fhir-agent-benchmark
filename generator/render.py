"""Renderizado de un :class:`GeneratedPatient` a las 4 vistas del benchmark.

Produce las mismas vistas que el caso semilla 0001:

- ``bundle.json``  : FHIR R4 Bundle (type collection, entries con fullUrl + id)
- ``narrative.md`` : narrativa clínica en prosa
- ``timeline.md``  : línea de tiempo cronológica en tabla
- ``table.md``     : resumen tabular por tipo de recurso

Todas las vistas describen LOS MISMOS hechos (mismos recursos de entrada).
El renderizado es puro y determinista: no introduce aleatoriedad ni fechas
nuevas.
"""

from __future__ import annotations

from .patient_generator import GeneratedPatient


def _ref(res: dict) -> str:
    return f"{res['resourceType']}/{res['id']}"


def build_bundle(gp: GeneratedPatient, *, bundle_id: str) -> dict:
    """Ensambla el FHIR Bundle (type collection) a partir de los recursos."""
    entries = []
    for res in gp.resources():
        entries.append({
            "fullUrl": _ref(res),
            "resource": res,
        })
    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "collection",
        "entry": entries,
    }


def _patient_summary(p: dict) -> tuple[str, int]:
    """Devuelve (nombre, edad aproximada) — edad derivada del año base 2025."""
    name = p["name"][0]
    full = f"{name['given'][0]} {name['family']}"
    birth_year = int(p["birthDate"][:4])
    age = 2025 - birth_year
    return full, age


def render_narrative(gp: GeneratedPatient) -> str:
    p = gp.patient
    full, age = _patient_summary(p)
    pid = _ref(p)

    lines: list[str] = []
    lines.append("# Clinical Narrative")
    lines.append("")
    lines.append(
        f"**Patient:** {full} — {p['gender']}, born {p['birthDate']} (`{pid}`)."
    )
    lines.append("")

    # Condiciones.
    if gp.conditions:
        cond_phrases = []
        for c in gp.conditions:
            disp = c["code"]["text"]
            onset_year = c["onsetDateTime"][:4]
            cond_phrases.append(f"**{disp.lower()}** (since {onset_year}, `{_ref(c)}`)")
        joined = "; ".join(cond_phrases)
        lines.append(
            f"{full.split()[0]} is a {age}-year-old {p['gender']} patient with a "
            f"history of {joined}. All listed conditions are currently active."
        )
        lines.append("")

    # Encuentros y medicamentos activos iniciados.
    enc1 = gp.encounters[0]
    enc2 = gp.encounters[1]
    enc3 = gp.encounters[2]

    active = gp.active_medications
    stopped = gp.stopped_medications

    active_phrases = []
    for m in active:
        active_phrases.append(
            f"**{m['medicationCodeableConcept']['text']}** "
            f"({m['dosageInstruction'][0]['text']}, `{_ref(m)}`)"
        )
    lines.append(
        f"At the initial outpatient evaluation on **{enc1['period']['start']}** "
        f"(`{_ref(enc1)}`), therapy was reviewed and the following active "
        f"medications are on the current regimen: " + "; ".join(active_phrases) + "."
    )
    lines.append("")

    if stopped:
        stop_phrases = []
        for m in stopped:
            note = m.get("note", [{}])[0].get("text", "")
            stop_phrases.append(
                f"**{m['medicationCodeableConcept']['text']}** "
                f"(`{_ref(m)}`, {m['status']}; {note})"
            )
        lines.append(
            f"At the medication review follow-up on **{enc2['period']['start']}** "
            f"(`{_ref(enc2)}`), the following medications were **discontinued** and "
            f"are no longer part of the active regimen: " + "; ".join(stop_phrases)
        )
        lines.append("")

    # Observaciones recientes.
    obs_phrases = []
    for o in gp.observations:
        if o["id"] == "obs-hba1c":
            v = o["valueQuantity"]
            obs_phrases.append(f"HbA1c was {v['value']}{v['unit']} (`{_ref(o)}`)")
        elif o["id"] == "obs-bp":
            comps = o["component"]
            sys_v = comps[0]["valueQuantity"]["value"]
            dia_v = comps[1]["valueQuantity"]["value"]
            obs_phrases.append(f"blood pressure was {sys_v}/{dia_v} mmHg (`{_ref(o)}`)")
    if obs_phrases:
        lines.append(
            f"At the most recent routine follow-up on **{enc3['period']['start']}** "
            f"(`{_ref(enc3)}`), " + " and ".join(obs_phrases) + "."
        )
        lines.append("")

    lines.append("No drug allergies are documented in this record.")
    lines.append("")
    return "\n".join(lines)


def render_timeline(gp: GeneratedPatient) -> str:
    """Tabla cronológica con todos los eventos datados, ordenada por fecha."""
    rows: list[tuple[str, str, str]] = []

    for c in gp.conditions:
        rows.append((c["onsetDateTime"], f"Onset: {c['code']['text'].lower()}",
                     f"`{_ref(c)}`"))
    for e in gp.encounters:
        rows.append((e["period"]["start"], e["type"][0]["text"], f"`{_ref(e)}`"))
    for m in gp.medications:
        text = m["medicationCodeableConcept"]["text"]
        if m["status"] == "active":
            rows.append((m["authoredOn"], f"Start {text} ({m['dosageInstruction'][0]['text']})",
                         f"`{_ref(m)}`"))
        else:
            rows.append((m["authoredOn"], f"Start {text} ({m['dosageInstruction'][0]['text']})",
                         f"`{_ref(m)}`"))
            note = m.get("note", [{}])[0].get("text", "")
            # La fecha de discontinuación se extrae de la nota ("Discontinued YYYY-MM-DD ...").
            stop_date = note.split(" ", 2)[1] if note.startswith("Discontinued ") else m["authoredOn"]
            rows.append((stop_date, f"**Stop** {text} ({m['status']})", f"`{_ref(m)}`"))
    for o in gp.observations:
        if o["id"] == "obs-hba1c":
            v = o["valueQuantity"]
            rows.append((o["effectiveDateTime"], f"HbA1c {v['value']}{v['unit']}",
                         f"`{_ref(o)}`"))
        elif o["id"] == "obs-bp":
            comps = o["component"]
            sys_v = comps[0]["valueQuantity"]["value"]
            dia_v = comps[1]["valueQuantity"]["value"]
            rows.append((o["effectiveDateTime"], f"Blood pressure {sys_v}/{dia_v} mmHg",
                         f"`{_ref(o)}`"))

    # Orden estable por fecha, manteniendo el orden de inserción en empates.
    rows.sort(key=lambda r: r[0])

    lines = ["# Chronological Timeline", "", "| Date | Event | Resource |",
             "|------|-------|----------|"]
    for d, event, ref in rows:
        lines.append(f"| {d} | {event} | {ref} |")
    lines.append("")
    return "\n".join(lines)


def render_table(gp: GeneratedPatient) -> str:
    p = gp.patient
    lines: list[str] = ["# Tabular Summary", ""]

    # Patient.
    lines += ["## Patient", "| Field | Value |", "|-------|-------|",
              f"| id | `{_ref(p)}` |",
              f"| sex | {p['gender']} |",
              f"| birthDate | {p['birthDate']} |", ""]

    # Conditions.
    if gp.conditions:
        lines += ["## Conditions",
                  "| Resource | Condition | Clinical status | Onset |",
                  "|----------|-----------|-----------------|-------|"]
        for c in gp.conditions:
            coding = c["code"]["coding"][0]
            status = c["clinicalStatus"]["coding"][0]["code"]
            lines.append(
                f"| `{_ref(c)}` | {coding['display']} (SNOMED {coding['code']}) "
                f"| {status} | {c['onsetDateTime']} |"
            )
        lines.append("")

    # Medication Requests.
    lines += ["## Medication Requests",
              "| Resource | Medication | RxNorm | Status | authoredOn |",
              "|----------|------------|--------|--------|------------|"]
    for m in gp.medications:
        coding = m["medicationCodeableConcept"]["coding"][0]
        lines.append(
            f"| `{_ref(m)}` | {m['medicationCodeableConcept']['text']} "
            f"| {coding['code']} | {m['status']} | {m['authoredOn']} |"
        )
    lines.append("")

    # Observations.
    lines += ["## Observations",
              "| Resource | Observation | Value | Date |",
              "|----------|-------------|-------|------|"]
    for o in gp.observations:
        coding = o["code"]["coding"][0]
        if o["id"] == "obs-hba1c":
            v = o["valueQuantity"]
            value = f"{v['value']} {v['unit']}"
        else:
            comps = o["component"]
            sys_v = comps[0]["valueQuantity"]["value"]
            dia_v = comps[1]["valueQuantity"]["value"]
            value = f"{sys_v}/{dia_v} mmHg"
        lines.append(
            f"| `{_ref(o)}` | {o['code']['text']} (LOINC {coding['code']}) "
            f"| {value} | {o['effectiveDateTime']} |"
        )
    lines.append("")

    # Encounters.
    lines += ["## Encounters",
              "| Resource | Type | Date |",
              "|----------|------|------|"]
    for e in gp.encounters:
        lines.append(f"| `{_ref(e)}` | {e['type'][0]['text']} | {e['period']['start']} |")
    lines.append("")
    return "\n".join(lines)


def render_all(gp: GeneratedPatient, *, bundle_id: str) -> dict[str, object]:
    """Devuelve las 4 vistas: bundle (dict) y los 3 markdown (str)."""
    return {
        "bundle": build_bundle(gp, bundle_id=bundle_id),
        "narrative": render_narrative(gp),
        "timeline": render_timeline(gp),
        "table": render_table(gp),
    }
