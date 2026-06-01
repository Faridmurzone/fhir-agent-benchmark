# Chronological Timeline

| Date | Event | Resource |
|------|-------|----------|
| 2024-08-10 | Penicillin allergy entry created on chart (later found to be recorded in error) | `AllergyIntolerance/allergy-pcn` |
| 2025-03-12 | Chronic disease management visit | `Encounter/enc-050` |
| 2025-03-12 | Start metformin 500 mg twice daily | `MedicationRequest/mr-metformin` |
| 2025-03-12 | Start lisinopril 10 mg once daily | `MedicationRequest/mr-lisinopril` |
| 2025-03-12 | Start atorvastatin 20 mg at bedtime | `MedicationRequest/mr-atorvastatin` |
| 2025-11-30 | **Penicillin allergy retracted — verificationStatus set to `entered-in-error`** (belonged to another patient's chart) | `AllergyIntolerance/allergy-pcn` |
| 2026-05-24 | Acute care visit for streptococcal pharyngitis | `Encounter/enc-051`, `Condition/cond-pharyngitis` |
| 2026-05-24 | Order amoxicillin 500 mg three times daily (penicillin-class) — no valid allergy on file, so no conflict | `MedicationRequest/mr-amoxicillin` |
