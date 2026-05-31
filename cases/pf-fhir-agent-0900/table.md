# Tabular Summary

## Patient
| Field | Value |
|-------|-------|
| id | `Patient/pat-001` |
| sex | male |
| birthDate | 1979-12-09 |

## Conditions
| Resource | Condition | Clinical status | Onset |
|----------|-----------|-----------------|-------|
| `Condition/cond-hypertension` | Essential hypertension (SNOMED 59621000) | active | 2014-07-02 |
| `Condition/cond-hypothyroidism` | Hypothyroidism (SNOMED 40930008) | active | 2023-02-07 |
| `Condition/cond-diabetes` | Type 2 diabetes mellitus (SNOMED 44054006) | active | 2020-09-20 |
| `Condition/cond-gerd` | Gastroesophageal reflux disease (SNOMED 235595009) | active | 2023-09-07 |

## Medication Requests
| Resource | Medication | RxNorm | Status | authoredOn |
|----------|------------|--------|--------|------------|
| `MedicationRequest/mr-lisinopril` | Lisinopril 10 mg | 314076 | active | 2025-01-22 |
| `MedicationRequest/mr-levothyroxine` | Levothyroxine 50 mcg | 966224 | active | 2025-07-30 |
| `MedicationRequest/mr-metformin` | Metformin 500 mg | 860975 | active | 2025-01-22 |
| `MedicationRequest/mr-omeprazole` | Omeprazole 20 mg | 402014 | stopped | 2025-01-22 |

## Observations
| Resource | Observation | Value | Date |
|----------|-------------|-------|------|
| `Observation/obs-hba1c` | HbA1c (LOINC 4548-4) | 8.3 % | 2025-12-08 |
| `Observation/obs-bp` | Blood pressure (LOINC 85354-9) | 152/85 mmHg | 2025-12-08 |

## Encounters
| Resource | Type | Date |
|----------|------|------|
| `Encounter/enc-001` | Initial outpatient evaluation | 2025-01-22 |
| `Encounter/enc-002` | Medication review follow-up | 2025-07-30 |
| `Encounter/enc-003` | Routine follow-up | 2025-12-08 |
