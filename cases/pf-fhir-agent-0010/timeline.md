# Chronological Timeline

| Date | Event | Resource |
|------|-------|----------|
| 2015-08-12 | Onset: essential hypertension | `Condition/cond-htn` |
| 2025-09-01 | Initial cardiology evaluation | `Encounter/enc-001` |
| 2025-09-01 | Start amlodipine 5 mg once daily (status: active) | `MedicationRequest/mr-amlodipine` |
| 2025-09-01 | Start metoprolol 50 mg twice daily (status: active) | `MedicationRequest/mr-metoprolol` |
| 2025-09-01 | Start warfarin 5 mg once daily | `MedicationRequest/mr-warfarin` |
| 2026-01-15 | Acute sinusitis visit | `Encounter/enc-002` |
| 2026-01-15 | Start amoxicillin 500 mg three times daily (7-day course) | `MedicationRequest/mr-amoxicillin` |
| 2026-01-15 | **Stop** warfarin (no longer indicated) → status: stopped | `MedicationRequest/mr-warfarin` |
| 2026-01-22 | Amoxicillin course **completed** → status: completed | `MedicationRequest/mr-amoxicillin` |
| 2026-02-10 | Follow-up visit | `Encounter/enc-003` |
| 2026-02-10 | Start prednisone 20 mg once daily | `MedicationRequest/mr-prednisone` |
| 2026-02-10 | Omeprazole 20 mg order entered on wrong chart → voided, status: entered-in-error | `MedicationRequest/mr-omeprazole` |
| 2026-03-01 | Prednisone **placed on hold** (temporarily suspended) → status: on-hold | `MedicationRequest/mr-prednisone` |
