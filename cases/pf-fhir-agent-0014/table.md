# Tabular Summary

## Patient
| Field | Value |
|-------|-------|
| id | `Patient/pat-014` |
| sex | male |
| birthDate | 1972-11-04 |

## Encounters
| Resource | Type | Date |
|----------|------|------|
| `Encounter/enc-040` | Primary care visit with routine bloodwork | 2026-05-20 |

## Laboratory Observations (2026-05-20)
| Resource | Analyte | LOINC | Value | Unit | Reference range | Within range? |
|----------|---------|-------|-------|------|-----------------|---------------|
| `Observation/obs-potassium` | Potassium, serum | 2823-3 | 54 | mmol/L | 3.5–5.1 | **No — physiologically impossible** |
| `Observation/obs-sodium` | Sodium, serum | 2951-2 | 140 | mmol/L | 135–145 | Yes (normal) |
| `Observation/obs-glucose` | Glucose, fasting | 1558-6 | 95 | mg/dL | 70–99 | Yes (normal) |
| `Observation/obs-creatinine` | Creatinine, serum | 2160-0 | 0.9 | mg/dL | 0.7–1.3 | Yes (normal) |

> **Note:** A serum potassium of 54 mmol/L (`Observation/obs-potassium`) is not a
> survivable concentration and is almost certainly a decimal/unit data-entry error
> for **5.4 mmol/L**. Sodium, glucose, and creatinine are all within normal limits
> and must NOT be flagged.
