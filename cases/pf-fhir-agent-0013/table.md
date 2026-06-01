# Tabular Summary

## Patient
| Field | Value |
|-------|-------|
| id | `Patient/pat-013` |
| sex | female |
| birthDate | 1965-11-22 |

## Conditions
| Resource | Condition | SNOMED | Clinical status | Onset | Abatement |
|----------|-----------|--------|-----------------|-------|-----------|
| `Condition/cond-htn` | Essential hypertension | 59621000 | resolved | 2019-05-03 | 2025-01-15 |

## Medication Requests
| Resource | Medication | RxNorm | Status | authoredOn | reasonReference |
|----------|------------|--------|--------|------------|-----------------|
| `MedicationRequest/mr-lisinopril` | Lisinopril 10 mg | 314076 | active | 2026-02-01 | `Condition/cond-htn` |

## Observations
| Resource | Observation | Value | Date |
|----------|-------------|-------|------|
| `Observation/obs-bp` | Blood pressure (LOINC 85354-9) | 128/80 mmHg | 2026-02-01 |
| `Observation/obs-k` | Serum potassium (LOINC 2823-3) | 4.3 mmol/L | 2026-02-01 |

## Encounters
| Resource | Type | Date |
|----------|------|------|
| `Encounter/enc-013` | Primary care follow-up | 2026-02-01 |

> Inconsistency to note: the **active** lisinopril order (authored 2026-02-01) has `reasonReference` → `Condition/cond-htn`, but that condition is marked **resolved** as of 2025-01-15.
