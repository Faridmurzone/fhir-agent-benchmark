# Tabular Summary

## Patient
| Field | Value |
|-------|-------|
| id | `Patient/pat-012` |
| sex | male |
| birthDate | 1971-02-08 |

## Conditions
| Resource | Condition | SNOMED | Clinical status | Onset | Abatement |
|----------|-----------|--------|-----------------|-------|-----------|
| `Condition/cond-mdd` | Major depressive disorder | 370143000 | recurrence | 2022-04-12 | — |
| `Condition/cond-htn` | Essential hypertension | 59621000 | active | 2018-09-01 | — |
| `Condition/cond-pneumonia` | Community-acquired pneumonia | 385093006 | resolved | 2024-01-15 | 2024-02-10 |
| `Condition/cond-migraine` | Migraine | 37796009 | remission | 2010-06-01 | — |

> Note on `cond-mdd`: history is **active (2022) → resolved (2023-08-30) → recurrence (2026-03-09)**. The current `clinicalStatus` is `recurrence`.

## Encounters
| Resource | Type | Date |
|----------|------|------|
| `Encounter/enc-2022` | Behavioral health intake | 2022-04-12 |
| `Encounter/enc-2026` | Behavioral health follow-up | 2026-03-09 |
