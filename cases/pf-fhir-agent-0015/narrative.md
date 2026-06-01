# Clinical Narrative

**Patient:** Robert Synthetic — male, born 1965-02-18 (`Patient/pat-015`).

Robert is a 61-year-old man on chronic therapy for type 2 diabetes,
hypertension, and dyslipidemia. At a chronic disease management visit on
**2025-03-12** (`Encounter/enc-050`) he was prescribed **metformin 500 mg twice
daily** (`MedicationRequest/mr-metformin`), **lisinopril 10 mg once daily**
(`MedicationRequest/mr-lisinopril`), and **atorvastatin 20 mg at bedtime**
(`MedicationRequest/mr-atorvastatin`). All three remain active.

His chart contains a **penicillin allergy** entry
(`AllergyIntolerance/allergy-pcn`), recorded 2024-08-10. However, that allergy
record carries `verificationStatus = entered-in-error`: it was entered on
Robert's chart **by mistake** (it belonged to another patient's record) and was
**corrected and retracted on 2025-11-30**. An `entered-in-error` allergy is not a
valid clinical fact and must be treated as if it does not exist. The note further
records that Robert has tolerated penicillin-class antibiotics previously.

At an acute care visit on **2026-05-24** (`Encounter/enc-051`) for
**streptococcal pharyngitis** (`Condition/cond-pharyngitis`), he was prescribed
**amoxicillin 500 mg three times daily** (`MedicationRequest/mr-amoxicillin`), a
penicillin-class antibiotic.

Although amoxicillin is a penicillin and the chart contains a penicillin allergy
entry, that entry is **entered-in-error** and therefore does **not** represent a
real allergy. There is consequently **no genuine allergy–medication conflict**
here. Flagging one would be a false alarm.
