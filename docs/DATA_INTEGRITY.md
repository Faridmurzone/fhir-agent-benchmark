# Data Integrity & Independent Verification

Part of **Prometheus Frontier** · FHIR Agent Benchmark.

> A benchmark whose data is authored (in part) with help from an LLM faces a real
> bias: **correlated errors**. If the author puts a plausible-but-wrong code in
> the gold, and the model under test repeats the same mistake, a code-based scorer
> calls it "correct" — both are wrong, but the benchmark reports a pass. The
> defense is to verify the data against **external authorities** that are
> independent of whoever wrote the cases.

This project applies that defense in two places.

## 1. FHIR structural validity → official validator, not a homegrown one

The FV dimension's structural check (required elements, cardinality, datatypes,
choice types like `value[x]`/`medication[x]`, references) is decided by
`fhir.resources` — Pydantic models generated from HL7's R4B StructureDefinitions
— **not** by a hand-written checker (see `SCORING.md`). Cross-checking the
homegrown heuristic against it surfaced genuine holes (it didn't require
`MedicationRequest.medication[x]`, didn't catch a non-numeric `valueQuantity`).

## 2. Terminology codes → official terminology services

Every `coding` in the benchmark is verified against the authoritative source for
its system:

| System | Authority | Endpoint |
|--------|-----------|----------|
| RxNorm | NLM RxNav | `rxnav.nlm.nih.gov/REST` |
| LOINC | NLM Clinical Tables | `clinicaltables.nlm.nih.gov` |
| SNOMED CT | HL7 FHIR tx server | `tx.fhir.org` (`$lookup`) |

Run it:

```bash
python scripts/verify_terminology.py          # exits non-zero if any code is INVALID
python scripts/verify_terminology.py --json report.json
```

Each coding is classified `OK` / `MISMATCH` (code exists but its official name
diverges from the `display` — likely the wrong code) / `INVALID` (code does not
exist) / `UNKNOWN` (source unreachable — never treated as a failure).

### What the first audit found (and why it matters)

The initial hand-authored data **failed this check on ~10 RxNorm codes** — the
single strongest confirmation of the correlated-error bias this benchmark guards
against. Examples of codes that existed but pointed at the *wrong* drug/strength/
form:

| Code (used) | Labeled as | Actually is (RxNav) |
|-------------|------------|---------------------|
| `199351` | Enalapril 10 mg | **trandolapril 2 mg** (different drug) |
| `866412` | Metoprolol tartrate 50 mg | metoprolol **succinate 100 mg ER** |
| `617312` | Atorvastatin 20 mg | atorvastatin **10 mg** |
| `308182` | Amoxicillin 500 mg | amoxicillin **250 mg** |
| `860975` | Metformin 500 mg (IR) | metformin 500 mg **ER** |
| `966222`/`966224` | Levothyroxine 0.05 mg | **0.075 / 0.125 mg** |

LOINC (11/11) and SNOMED (13/14; one CKD stage code) were largely correct —
consistent with RxNorm's far finer granularity (strength, salt, form, release)
being much easier to misremember. All flagged codes were corrected to the
RxNav/`$lookup`-verified values, and the verifier now passes with **0 INVALID**.

### Standing policy

- Terminology verification is part of the data contract; new cases must pass
  `verify_terminology.py` before a tagged release.
- The check uses **live external services**, so it is gated on network access; a
  source being unreachable is reported as `UNKNOWN`, never as a pass or a failure.
- Generator catalogs (`generator/`) feed cases too; codes reused in published
  cases are verified, and the catalogs carry a note to run the verifier before
  using their cases in published results.

This is deliberately public: the credibility of a healthcare benchmark rests on
its data being checkable by third parties, not taken on trust.
