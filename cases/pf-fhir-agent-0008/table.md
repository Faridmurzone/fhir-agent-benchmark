# Tabular Summary

## Patient
| Field | Value |
|-------|-------|
| id | `Patient/pat-008` |
| sex | male |
| birthDate | 1965-12-04 |

## Conditions
| Resource | Condition | Clinical status | Onset |
|----------|-----------|-----------------|-------|
| `Condition/cond-ckd` | Chronic kidney disease stage 3 (SNOMED 431855005) | active | 2021-06-01 |

## Medication Requests
| Resource | Medication | RxNorm | Status | authoredOn |
|----------|------------|--------|--------|------------|
| `MedicationRequest/mr-furosemide` | Furosemide 40 mg | 310429 | active | 2025-08-14 |

## Observations
| Resource | Observation | Value | Date | subject |
|----------|-------------|-------|------|---------|
| `Observation/obs-creatinine` | Serum creatinine (LOINC 2160-0) | 1.6 mg/dL | 2026-05-10 | `Patient/pat-008` |
| `Observation/obs-egfr` | eGFR (LOINC 33914-3) | 48 mL/min/1.73m² | 2026-05-10 | `Patient/pat-999` (**missing — broken reference**) |

## Encounters
| Resource | Type | Date |
|----------|------|------|
| `Encounter/enc-030` | Nephrology evaluation | 2025-08-14 |
| `Encounter/enc-031` | Nephrology follow-up | 2026-05-10 |

> **Note:** `Observation/obs-egfr` references `Patient/pat-999` as its subject,
> but that patient is not present in the bundle. This is the only broken
> reference; all other references resolve to existing resources.
