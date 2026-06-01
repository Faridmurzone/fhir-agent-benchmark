# Tabular Summary

## Patient
| Field | Value |
|-------|-------|
| id | `Patient/pat-010` |
| sex | male |
| birthDate | 1962-04-22 |

## Conditions
| Resource | Condition | Clinical status | Onset |
|----------|-----------|-----------------|-------|
| `Condition/cond-htn` | Essential hypertension (SNOMED 59621000) | active | 2015-08-12 |

## Medication Requests
| Resource | Medication | RxNorm | Status | authoredOn |
|----------|------------|--------|--------|------------|
| `MedicationRequest/mr-amlodipine` | Amlodipine 5 mg | 197361 | active | 2025-09-01 |
| `MedicationRequest/mr-metoprolol` | Metoprolol 50 mg | 866412 | active | 2025-09-01 |
| `MedicationRequest/mr-amoxicillin` | Amoxicillin 500 mg | 308182 | completed | 2026-01-15 |
| `MedicationRequest/mr-prednisone` | Prednisone 20 mg | 312615 | on-hold | 2026-02-10 |
| `MedicationRequest/mr-omeprazole` | Omeprazole 20 mg | 402014 | entered-in-error | 2026-02-10 |
| `MedicationRequest/mr-warfarin` | Warfarin 5 mg | 855332 | stopped | 2025-09-01 |

## Encounters
| Resource | Type | Date |
|----------|------|------|
| `Encounter/enc-001` | Initial cardiology evaluation | 2025-09-01 |
| `Encounter/enc-002` | Acute sinusitis visit | 2026-01-15 |
| `Encounter/enc-003` | Follow-up visit | 2026-02-10 |
