# Clinical Note

Patient `Patient/pat-001` was seen at encounter `Encounter/enc-001` on 2026-05-20.

A hemoglobin A1c (HbA1c) laboratory test was performed. The result was **7.2 %**.

Task: produce the FHIR R4 `Observation` resource representing this lab result.
Use LOINC **4548-4** for HbA1c. The observation is final, belongs to the
laboratory category, was effective on 2026-05-20, and is for this patient at
this encounter. Express the value as a UCUM quantity in percent.
