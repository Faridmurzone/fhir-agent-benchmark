# Tabular Summary

## Patient
| Field | Value |
|-------|-------|
| id | `Patient/pat-002` |
| sex | male |
| birthDate | 1971-02-23 |

## Conditions
| Resource | Condition | Clinical status | Onset | Abatement |
|----------|-----------|-----------------|-------|-----------|
| `Condition/cond-copd` | Chronic obstructive pulmonary disease (SNOMED 13645005) | active | 2020-08-15 | — |
| `Condition/cond-gerd` | Gastroesophageal reflux disease (SNOMED 235595009) | active | 2022-04-10 | — |
| `Condition/cond-pneumonia` | Community-acquired pneumonia (SNOMED 233604007) | resolved | 2024-11-12 | 2024-12-05 |

## Observations
| Resource | Observation | Value | Date |
|----------|-------------|-------|------|
| `Observation/obs-spo2` | Oxygen saturation (LOINC 2708-6) | 94 % | 2026-05-18 |

## Encounters
| Resource | Type | Date |
|----------|------|------|
| `Encounter/enc-010` | Inpatient admission for pneumonia | 2024-11-12 to 2024-11-18 |
| `Encounter/enc-011` | Pulmonary follow-up | 2026-05-18 |
