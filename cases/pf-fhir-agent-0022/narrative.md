# Clinical Note

For patient `Patient/pat-001`, at `Encounter/enc-001` on 2026-05-20, the clinician
prescribed **lisinopril 10 mg orally once daily** for hypertension.

Task: produce the FHIR R4 `MedicationRequest` resource representing this new order.
Use RxNorm **314076** (Lisinopril 10 MG Oral Tablet), status active, intent order,
authoredOn 2026-05-20, subject the patient, and include the dosage instruction.
