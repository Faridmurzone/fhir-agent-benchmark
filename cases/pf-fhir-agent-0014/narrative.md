# Clinical Narrative

**Patient:** David Synthetic — male, born 1972-11-04 (`Patient/pat-014`).

David is a 53-year-old man who attended a **primary care visit with routine
bloodwork** on **2026-05-20** (`Encounter/enc-040`). A basic metabolic panel was
drawn and resulted the same day.

The panel returned the following values:

- **Serum potassium 54 mmol/L** (`Observation/obs-potassium`), LOINC 2823-3,
  against a reference range of 3.5–5.1 mmol/L.
- **Serum sodium 140 mmol/L** (`Observation/obs-sodium`), LOINC 2951-2,
  reference range 135–145 mmol/L.
- **Fasting glucose 95 mg/dL** (`Observation/obs-glucose`), LOINC 1558-6,
  reference range 70–99 mg/dL.
- **Serum creatinine 0.9 mg/dL** (`Observation/obs-creatinine`), LOINC 2160-0,
  reference range 0.7–1.3 mg/dL.

The sodium, glucose, and creatinine results are all within their normal
reference ranges. The reported potassium of **54 mmol/L** is physiologically
impossible: human serum potassium is incompatible with life far below that
figure (severe hyperkalemia is already life-threatening around 7 mmol/L). A
value of 54 mmol/L is roughly ten times any survivable concentration and is
almost certainly a **data-entry / decimal error** — the intended value is most
plausibly **5.4 mmol/L**. The result should be flagged as an implausible value
rather than acted upon.
