# Tabular Summary

## Patient
| Field | Value |
|-------|-------|
| id | `Patient/pat-015` |
| sex | male |
| birthDate | 1965-02-18 |

## Allergies & Intolerances
| Resource | Substance | Verification status | Clinical status | Valid? |
|----------|-----------|---------------------|-----------------|--------|
| `AllergyIntolerance/allergy-pcn` | Penicillin (SNOMED 373270004) | **entered-in-error** | inactive | **No — retracted, recorded by mistake** |

## Conditions
| Resource | Condition | Clinical status | Onset |
|----------|-----------|-----------------|-------|
| `Condition/cond-pharyngitis` | Streptococcal pharyngitis (SNOMED 43878008) | active | 2026-05-24 |

## Medication Requests
| Resource | Medication | RxNorm | Status | authoredOn | Encounter |
|----------|------------|--------|--------|------------|-----------|
| `MedicationRequest/mr-amoxicillin` | Amoxicillin 500 mg | 308182 | active | 2026-05-24 | `Encounter/enc-051` |
| `MedicationRequest/mr-metformin` | Metformin 500 mg | 860975 | active | 2025-03-12 | `Encounter/enc-050` |
| `MedicationRequest/mr-lisinopril` | Lisinopril 10 mg | 314076 | active | 2025-03-12 | `Encounter/enc-050` |
| `MedicationRequest/mr-atorvastatin` | Atorvastatin 20 mg | 617312 | active | 2025-03-12 | `Encounter/enc-050` |

## Encounters
| Resource | Type | Date |
|----------|------|------|
| `Encounter/enc-050` | Chronic disease management visit | 2025-03-12 |
| `Encounter/enc-051` | Acute care visit for sore throat | 2026-05-24 |

> **Note:** The only allergy on file (`AllergyIntolerance/allergy-pcn`) has
> `verificationStatus = entered-in-error`, meaning it was recorded by mistake and
> retracted. It is NOT a valid allergy. The active amoxicillin order therefore
> does NOT conflict with any documented allergy, and no flag should be raised.
> Metformin, lisinopril, and atorvastatin are unrelated chronic medications.
