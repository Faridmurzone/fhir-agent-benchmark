# Clinical Note

Patient `Patient/pat-001` has a new, confirmed, active diagnosis of **essential
hypertension**.

Task: produce a FHIR R4 `Condition` resource that is **conformant to the US Core
Condition (Problems and Health Concerns) profile**. This means, beyond a valid
R4 Condition:

- declare the profile in `meta.profile`
  (`http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition-problems-health-concerns`)
- include `category` (problem-list-item) with the correct US Core / HL7 category system
- include `clinicalStatus` (active) and `verificationStatus` (confirmed)
- code the problem with SNOMED CT **59621000** (essential hypertension)
- reference the patient as `subject`
