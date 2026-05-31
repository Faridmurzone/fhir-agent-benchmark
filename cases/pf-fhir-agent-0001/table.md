# Tabular Summary

## Patient
| Field | Value |
|-------|-------|
| id | `Patient/pat-001` |
| sex | female |
| birthDate | 1958-09-14 |

## Conditions
| Resource | Condition | Clinical status | Onset |
|----------|-----------|-----------------|-------|
| `Condition/cond-dm` | Type 2 diabetes mellitus (SNOMED 44054006) | active | 2019-03-01 |
| `Condition/cond-htn` | Essential hypertension (SNOMED 59621000) | active | 2017-11-20 |

## Medication Requests
| Resource | Medication | RxNorm | Status | authoredOn |
|----------|------------|--------|--------|------------|
| `MedicationRequest/mr-metformin` | Metformin 500 mg | 860975 | active | 2025-12-03 |
| `MedicationRequest/mr-lisinopril` | Lisinopril 10 mg | 314076 | active | 2025-06-10 |
| `MedicationRequest/mr-atorvastatin` | Atorvastatin 20 mg | 617312 | active | 2025-06-10 |
| `MedicationRequest/mr-glyburide` | Glyburide 5 mg | 310537 | stopped | 2025-06-10 |

## Observations
| Resource | Observation | Value | Date |
|----------|-------------|-------|------|
| `Observation/obs-hba1c` | HbA1c (LOINC 4548-4) | 7.2 % | 2026-05-20 |
| `Observation/obs-bp` | Blood pressure (LOINC 85354-9) | 138/86 mmHg | 2026-05-20 |

## Encounters
| Resource | Type | Date |
|----------|------|------|
| `Encounter/enc-001` | Initial outpatient evaluation | 2025-06-10 |
| `Encounter/enc-002` | Diabetes follow-up | 2025-12-03 |
| `Encounter/enc-003` | Routine follow-up | 2026-05-20 |
