"""Construcción de un paciente sintético para casos MR-01.

Genera demografía, condiciones, un conjunto de ``MedicationRequest`` (algunos
``active`` y algunos ``stopped``/``completed`` para que MR-01 tenga una
discriminación real activo-vs-discontinuado), más un par de ``Observation`` y
``Encounter``.

Todos los códigos (SNOMED / LOINC / RxNorm) provienen de un pequeño catálogo
incorporado con códigos de aspecto válido. No hay PHI real: los nombres son
sintéticos y las fechas se derivan de la semilla.

Determinismo: toda la aleatoriedad pasa por un ``random.Random`` sembrado y las
fechas se derivan de un año base fijo (``BASE_YEAR = 2025``). Misma semilla =>
mismos recursos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from random import Random

# Año base fijo para derivar fechas plausibles (NO usar datetime.now()).
BASE_YEAR = 2025

RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SNOMED = "http://snomed.info/sct"
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"

# --- Catálogo de medicamentos (RxNorm, código de aspecto válido) ------------
# Cada entrada: clave -> (rxnorm, display, texto corto, instrucción de dosis,
# condición asociada por slug).
MED_CATALOG: dict[str, dict] = {
    "metformin": {
        "rxnorm": "860975",
        "display": "Metformin hydrochloride 500 MG Oral Tablet",
        "text": "Metformin 500 mg",
        "dosage": "500 mg orally twice daily",
        "treats": "diabetes",
    },
    "lisinopril": {
        "rxnorm": "314076",
        "display": "Lisinopril 10 MG Oral Tablet",
        "text": "Lisinopril 10 mg",
        "dosage": "10 mg orally once daily",
        "treats": "hypertension",
    },
    "atorvastatin": {
        "rxnorm": "617312",
        "display": "Atorvastatin 20 MG Oral Tablet",
        "text": "Atorvastatin 20 mg",
        "dosage": "20 mg orally at night",
        "treats": "hyperlipidemia",
    },
    "amlodipine": {
        "rxnorm": "197361",
        "display": "Amlodipine 5 MG Oral Tablet",
        "text": "Amlodipine 5 mg",
        "dosage": "5 mg orally once daily",
        "treats": "hypertension",
    },
    "levothyroxine": {
        "rxnorm": "966224",
        "display": "Levothyroxine sodium 0.05 MG Oral Tablet",
        "text": "Levothyroxine 50 mcg",
        "dosage": "50 mcg orally once daily in the morning",
        "treats": "hypothyroidism",
    },
    "glyburide": {
        "rxnorm": "310537",
        "display": "Glyburide 5 MG Oral Tablet",
        "text": "Glyburide 5 mg",
        "dosage": "5 mg orally once daily",
        "treats": "diabetes",
    },
    "hydrochlorothiazide": {
        "rxnorm": "310798",
        "display": "Hydrochlorothiazide 25 MG Oral Tablet",
        "text": "Hydrochlorothiazide 25 mg",
        "dosage": "25 mg orally once daily",
        "treats": "hypertension",
    },
    "omeprazole": {
        "rxnorm": "402014",
        "display": "Omeprazole 20 MG Delayed Release Oral Capsule",
        "text": "Omeprazole 20 mg",
        "dosage": "20 mg orally once daily before breakfast",
        "treats": "gerd",
    },
}

# Pools de medicamentos que se mantienen activos vs. los que se discontinúan.
_ACTIVE_POOL = ["metformin", "lisinopril", "atorvastatin", "amlodipine", "levothyroxine"]
_STOPPED_POOL = ["glyburide", "hydrochlorothiazide", "omeprazole"]

# --- Catálogo de condiciones (SNOMED) ---------------------------------------
CONDITION_CATALOG: dict[str, dict] = {
    "diabetes": {"snomed": "44054006", "display": "Type 2 diabetes mellitus"},
    "hypertension": {"snomed": "59621000", "display": "Essential hypertension"},
    "hyperlipidemia": {"snomed": "55822004", "display": "Hyperlipidemia"},
    "hypothyroidism": {"snomed": "40930008", "display": "Hypothyroidism"},
    "gerd": {"snomed": "235595009", "display": "Gastroesophageal reflux disease"},
}

# --- Catálogo de observaciones (LOINC) --------------------------------------
# Razones de discontinuación plausibles para las notas.
_STOP_REASONS = [
    "due to hypoglycemia",
    "due to persistent cough",
    "due to inadequate response",
    "after dose adjustment",
    "due to gastrointestinal intolerance",
]

# Nombres sintéticos (sin PHI real).
_GIVEN_NAMES = ["Maria", "John", "Aisha", "Carlos", "Elena", "David", "Priya", "Omar"]
_FAMILY_NAME = "Synthetic"


@dataclass
class GeneratedPatient:
    """Recursos sintéticos generados, listos para renderizar."""

    patient: dict
    conditions: list[dict] = field(default_factory=list)
    medications: list[dict] = field(default_factory=list)
    observations: list[dict] = field(default_factory=list)
    encounters: list[dict] = field(default_factory=list)

    def resources(self) -> list[dict]:
        """Recursos en orden canónico (mismo orden que el caso semilla)."""
        return (
            [self.patient]
            + self.conditions
            + self.medications
            + self.observations
            + self.encounters
        )

    @property
    def active_medications(self) -> list[dict]:
        return [m for m in self.medications if m["status"] == "active"]

    @property
    def stopped_medications(self) -> list[dict]:
        return [m for m in self.medications if m["status"] != "active"]


def _fmt(d: date) -> str:
    return d.isoformat()


def build_patient(
    seed: int,
    *,
    n_active: int = 3,
    n_stopped: int = 1,
) -> GeneratedPatient:
    """Construye un paciente sintético determinista a partir de ``seed``.

    ``n_active`` medicamentos quedan en estado ``active`` y ``n_stopped`` quedan
    discontinuados (``stopped`` / ``completed``), de modo que MR-01 tenga una
    discriminación real. Devuelve un :class:`GeneratedPatient`.
    """
    rng = Random(seed)

    n_active = max(1, min(n_active, len(_ACTIVE_POOL)))
    n_stopped = max(1, min(n_stopped, len(_STOPPED_POOL)))

    # --- Demografía ---------------------------------------------------------
    given = _GIVEN_NAMES[seed % len(_GIVEN_NAMES)]
    gender = "female" if rng.random() < 0.5 else "male"
    # Edad entre 45 y 80; fecha de nacimiento derivada del año base.
    age = rng.randint(45, 80)
    birth_year = BASE_YEAR - age
    birth_month = rng.randint(1, 12)
    birth_day = rng.randint(1, 28)
    birth_date = date(birth_year, birth_month, birth_day)

    pat_id = "pat-001"
    patient = {
        "resourceType": "Patient",
        "id": pat_id,
        "gender": gender,
        "birthDate": _fmt(birth_date),
        "name": [{"use": "official", "family": _FAMILY_NAME, "given": [given]}],
    }
    pat_ref = f"Patient/{pat_id}"

    # --- Selección de medicamentos -----------------------------------------
    active_keys = rng.sample(_ACTIVE_POOL, n_active)
    stopped_keys = rng.sample(_STOPPED_POOL, n_stopped)

    # --- Fechas de las visitas (derivadas del año base) ---------------------
    # Visita inicial, visita de seguimiento (discontinuación) y visita reciente.
    enc1_date = date(BASE_YEAR, rng.randint(1, 4), rng.randint(1, 28))
    enc2_date = enc1_date + timedelta(days=rng.randint(120, 200))
    enc3_date = enc2_date + timedelta(days=rng.randint(120, 200))

    encounters = [
        {
            "resourceType": "Encounter",
            "id": "enc-001",
            "status": "finished",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                      "code": "AMB", "display": "ambulatory"},
            "type": [{"text": "Initial outpatient evaluation"}],
            "subject": {"reference": pat_ref},
            "period": {"start": _fmt(enc1_date), "end": _fmt(enc1_date)},
        },
        {
            "resourceType": "Encounter",
            "id": "enc-002",
            "status": "finished",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                      "code": "AMB", "display": "ambulatory"},
            "type": [{"text": "Medication review follow-up"}],
            "subject": {"reference": pat_ref},
            "period": {"start": _fmt(enc2_date), "end": _fmt(enc2_date)},
        },
        {
            "resourceType": "Encounter",
            "id": "enc-003",
            "status": "finished",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                      "code": "AMB", "display": "ambulatory"},
            "type": [{"text": "Routine follow-up"}],
            "subject": {"reference": pat_ref},
            "period": {"start": _fmt(enc3_date), "end": _fmt(enc3_date)},
        },
    ]

    # --- Condiciones (derivadas de los medicamentos elegidos) ---------------
    cond_slugs: list[str] = []
    for key in active_keys + stopped_keys:
        treats = MED_CATALOG[key]["treats"]
        if treats in CONDITION_CATALOG and treats not in cond_slugs:
            cond_slugs.append(treats)

    conditions: list[dict] = []
    for slug in cond_slugs:
        cat = CONDITION_CATALOG[slug]
        onset_year = BASE_YEAR - rng.randint(2, 12)
        onset = date(onset_year, rng.randint(1, 12), rng.randint(1, 28))
        conditions.append({
            "resourceType": "Condition",
            "id": f"cond-{slug}",
            "clinicalStatus": {"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "active"}]},
            "verificationStatus": {"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": "confirmed"}]},
            "category": [{"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                "code": "problem-list-item"}]}],
            "code": {"coding": [{"system": SNOMED, "code": cat["snomed"],
                                 "display": cat["display"]}], "text": cat["display"]},
            "subject": {"reference": pat_ref},
            "onsetDateTime": _fmt(onset),
            "recordedDate": _fmt(enc1_date),
        })

    # --- Medicamentos -------------------------------------------------------
    medications: list[dict] = []

    # Activos: autorizados en la visita inicial o en la de seguimiento.
    for i, key in enumerate(active_keys):
        info = MED_CATALOG[key]
        authored = enc1_date if i % 2 == 0 else enc2_date
        enc_ref = "Encounter/enc-001" if authored == enc1_date else "Encounter/enc-002"
        medications.append({
            "resourceType": "MedicationRequest",
            "id": f"mr-{key}",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{"system": RXNORM, "code": info["rxnorm"],
                            "display": info["display"]}],
                "text": info["text"],
            },
            "subject": {"reference": pat_ref},
            "authoredOn": _fmt(authored),
            "encounter": {"reference": enc_ref},
            "dosageInstruction": [{"text": info["dosage"]}],
        })

    # Discontinuados: autorizados en la visita inicial, detenidos en la segunda.
    for i, key in enumerate(stopped_keys):
        info = MED_CATALOG[key]
        # Alterna entre "stopped" y "completed" para variedad.
        status = "stopped" if i % 2 == 0 else "completed"
        reason = _STOP_REASONS[(seed + i) % len(_STOP_REASONS)]
        medications.append({
            "resourceType": "MedicationRequest",
            "id": f"mr-{key}",
            "status": status,
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{"system": RXNORM, "code": info["rxnorm"],
                            "display": info["display"]}],
                "text": info["text"],
            },
            "subject": {"reference": pat_ref},
            "authoredOn": _fmt(enc1_date),
            "encounter": {"reference": "Encounter/enc-001"},
            "dosageInstruction": [{"text": info["dosage"]}],
            "note": [{"text": f"Discontinued {_fmt(enc2_date)} {reason}."}],
        })

    # --- Observaciones ------------------------------------------------------
    observations: list[dict] = []
    # HbA1c si hay diabetes, si no un panel metabólico genérico.
    a1c_value = round(rng.uniform(6.2, 9.1), 1)
    observations.append({
        "resourceType": "Observation",
        "id": "obs-hba1c",
        "status": "final",
        "category": [{"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
            "code": "laboratory"}]}],
        "code": {"coding": [{"system": LOINC, "code": "4548-4",
                             "display": "Hemoglobin A1c/Hemoglobin.total in Blood"}],
                 "text": "HbA1c"},
        "subject": {"reference": pat_ref},
        "effectiveDateTime": _fmt(enc3_date),
        "encounter": {"reference": "Encounter/enc-003"},
        "valueQuantity": {"value": a1c_value, "unit": "%", "system": UCUM, "code": "%"},
    })

    systolic = rng.randint(118, 152)
    diastolic = rng.randint(72, 94)
    observations.append({
        "resourceType": "Observation",
        "id": "obs-bp",
        "status": "final",
        "category": [{"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
            "code": "vital-signs"}]}],
        "code": {"coding": [{"system": LOINC, "code": "85354-9",
                             "display": "Blood pressure panel"}],
                 "text": "Blood pressure"},
        "subject": {"reference": pat_ref},
        "effectiveDateTime": _fmt(enc3_date),
        "encounter": {"reference": "Encounter/enc-003"},
        "component": [
            {"code": {"coding": [{"system": LOINC, "code": "8480-6",
                                  "display": "Systolic blood pressure"}]},
             "valueQuantity": {"value": systolic, "unit": "mmHg", "system": UCUM,
                               "code": "mm[Hg]"}},
            {"code": {"coding": [{"system": LOINC, "code": "8462-4",
                                  "display": "Diastolic blood pressure"}]},
             "valueQuantity": {"value": diastolic, "unit": "mmHg", "system": UCUM,
                               "code": "mm[Hg]"}},
        ],
    })

    return GeneratedPatient(
        patient=patient,
        conditions=conditions,
        medications=medications,
        observations=observations,
        encounters=encounters,
    )
