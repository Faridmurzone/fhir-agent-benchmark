# Tabular Summary

## Patient
| Field | Value |
|-------|-------|
| id | `Patient/pat-011` |
| sex | female |
| birthDate | 1955-12-03 |

## Conditions
| Resource | Condition | Clinical status | Onset |
|----------|-----------|-----------------|-------|
| `Condition/cond-htn` | Essential hypertension (SNOMED 59621000) | active | 2014-05-19 |
| `Condition/cond-dm` | Type 2 diabetes mellitus (SNOMED 44054006) | active | 2018-02-11 |

## Medication Requests
| Resource | Medication | RxNorm | Drug class | Status | authoredOn |
|----------|------------|--------|------------|--------|------------|
| `MedicationRequest/mr-lisinopril` | Lisinopril 10 mg | 314076 | ACE inhibitor | active | 2025-10-05 |
| `MedicationRequest/mr-enalapril` | Enalapril 10 mg | 199351 | ACE inhibitor | active | 2026-03-18 |
| `MedicationRequest/mr-metformin` | Metformin 500 mg | 860975 | Biguanide (antidiabetic) | active | 2025-10-05 |
| `MedicationRequest/mr-atorvastatin` | Atorvastatin 20 mg | 617312 | Statin | active | 2025-10-05 |

## Encounters
| Resource | Type | Date |
|----------|------|------|
| `Encounter/enc-001` | Initial outpatient evaluation | 2025-10-05 |
| `Encounter/enc-002` | Hypertension follow-up (covering clinician) | 2026-03-18 |

> Note: lisinopril and enalapril are both ACE inhibitors and are both active —
> a therapeutic duplication. The two drugs have different names and different
> RxNorm codes, so the duplication cannot be detected by code equality alone.
