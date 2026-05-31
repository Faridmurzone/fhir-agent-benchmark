# Tabular Summary

## Patient
| Field | Value |
|-------|-------|
| id | `Patient/pat-004` |
| sex | female |
| birthDate | 1989-07-30 |

## Allergies & Intolerances
| Resource | Substance | Type | Criticality | Clinical status | Reaction |
|----------|-----------|------|-------------|-----------------|----------|
| `AllergyIntolerance/allergy-pcn` | Penicillin (SNOMED 373270004) | medication allergy | high | active | Severe urticaria / angioedema |

## Conditions
| Resource | Condition | Clinical status | Onset |
|----------|-----------|-----------------|-------|
| `Condition/cond-hypothyroid` | Hypothyroidism (SNOMED 40930008) | active | 2025-09-15 |
| `Condition/cond-pharyngitis` | Streptococcal pharyngitis (SNOMED 43878008) | active | 2026-05-22 |

## Medication Requests
| Resource | Medication | RxNorm | Status | authoredOn | Encounter |
|----------|------------|--------|--------|------------|-----------|
| `MedicationRequest/mr-amoxicillin` | Amoxicillin 500 mg | 308182 | active | 2026-05-22 | `Encounter/enc-021` |
| `MedicationRequest/mr-ibuprofen` | Ibuprofen 400 mg | 197805 | active | 2026-05-22 | `Encounter/enc-021` |
| `MedicationRequest/mr-levothyroxine` | Levothyroxine 50 mcg | 966222 | active | 2025-10-01 | `Encounter/enc-020` |
| `MedicationRequest/mr-cetirizine` | Cetirizine 10 mg | 1014676 | active | 2025-10-01 | `Encounter/enc-020` |

## Encounters
| Resource | Type | Date |
|----------|------|------|
| `Encounter/enc-020` | Primary care visit | 2025-10-01 |
| `Encounter/enc-021` | Acute care visit for sore throat | 2026-05-22 |

> **Note:** Amoxicillin (`MedicationRequest/mr-amoxicillin`) is a penicillin-class
> antibiotic and conflicts with the documented high-criticality penicillin allergy
> (`AllergyIntolerance/allergy-pcn`).
