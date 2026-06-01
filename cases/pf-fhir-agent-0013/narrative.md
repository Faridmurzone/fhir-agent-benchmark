# Clinical Narrative

**Patient:** Rosa Synthetic — female, born 1965-11-22 (`Patient/pat-013`).

Rosa is a 60-year-old woman with a documented history of **essential
hypertension** (`Condition/cond-htn`), onset 2019. In the record, this condition
is marked **resolved**, with an abatement date of **2025-01-15**.

At a primary care follow-up on **2026-02-01** (`Encounter/enc-013`), she was
prescribed **lisinopril 10 mg once daily** (`MedicationRequest/mr-lisinopril`).
The order is **active** and its `reasonReference` points to the hypertension
condition (`Condition/cond-htn`) — i.e., the medication is documented as treating
that hypertension. The prescription was authored **after** the date the
hypertension was recorded as resolved.

At the same visit her **blood pressure was 128/80 mmHg** (`Observation/obs-bp`)
and her **serum potassium was 4.3 mmol/L** (`Observation/obs-k`), both within
normal limits.
