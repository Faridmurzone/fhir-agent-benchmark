# Clinical Narrative

**Patient:** Diane Synthetic — female, born 1955-12-03 (`Patient/pat-011`).

Diane is a 70-year-old woman with **essential hypertension** (diagnosed 2014,
`Condition/cond-htn`) and **type 2 diabetes mellitus** (diagnosed 2018,
`Condition/cond-dm`). Both conditions are currently active.

At an initial outpatient evaluation on **2025-10-05** (`Encounter/enc-001`) she
was started on **lisinopril 10 mg once daily** (`MedicationRequest/mr-lisinopril`)
for blood pressure, **metformin 500 mg twice daily**
(`MedicationRequest/mr-metformin`) for glycemic control, and **atorvastatin 20 mg
at night** (`MedicationRequest/mr-atorvastatin`).

At a hypertension follow-up on **2026-03-18** (`Encounter/enc-002`), seen by a
covering clinician, she was additionally started on **enalapril 10 mg once daily**
(`MedicationRequest/mr-enalapril`). The covering clinician did not reconcile the
existing list, and the prior lisinopril order was never discontinued.

Both lisinopril and enalapril are **ACE inhibitors** (angiotensin-converting
enzyme inhibitors). Having two active ACE inhibitor orders at the same time is a
**therapeutic duplication** within the same pharmacologic class and should be
flagged. Metformin (a biguanide antidiabetic) and atorvastatin (a statin) belong
to unrelated classes and are not duplicative.

All four medication orders are currently **active**. No drug allergies are
documented in this record.
