# Clinical Narrative

**Patient:** Robert Synthetic — male, born 1965-12-04 (`Patient/pat-008`).

Robert is a 60-year-old man with **chronic kidney disease stage 3**
(diagnosed 2021, `Condition/cond-ckd`). He was first evaluated by nephrology on
**2025-08-14** (`Encounter/enc-030`) and started on **furosemide 40 mg once
daily** (`MedicationRequest/mr-furosemide`).

At his nephrology follow-up on **2026-05-10** (`Encounter/enc-031`), two labs
were drawn: **serum creatinine 1.6 mg/dL** (`Observation/obs-creatinine`) and
**eGFR 48 mL/min/1.73m²** (`Observation/obs-egfr`).

**Data quality note:** the eGFR Observation (`Observation/obs-egfr`) records its
`subject` as `Patient/pat-999`, but no such patient exists in this bundle — the
only patient present is `Patient/pat-008`. This is a dangling (broken)
reference. Every other reference in the bundle resolves correctly.
