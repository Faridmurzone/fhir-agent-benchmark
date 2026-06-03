# Methodology Lessons: The Scorer Is the Bias

Part of **Prometheus Frontier** · FHIR Agent Benchmark.

> The hardest problem in building a healthcare-AI benchmark is **not** getting
> models to fail. It is making sure that when the benchmark says "pass" or "fail,"
> it is telling the truth. Across this project, every apparent finding that looked
> like a model result turned out, on inspection, to be an artifact of the
> measuring instrument. This document records those instances so others don't
> repeat them — and so our own results are read with the right skepticism.

The benchmark was bootstrapped with help from a frontier LLM (Claude Opus 4.8),
the same class of model it evaluates. That raises a legitimate fear of bias. The
investigation below found bias **three times** — and in all three the culprit was
the instrument (data, validator, scorer), not the model. The defense, every time,
was an **independent oracle**: a source of truth that is not the benchmark author.

---

## Instance 1 — Correlated errors in the ground-truth data

**Symptom:** medication-reconciliation cases scored 100 across models.

**Reality:** ~10 of 17 RxNorm codes in the hand-authored data were *plausible but
wrong* — the code existed but pointed at a different drug/strength/form than its
`display` (e.g. `199351` labeled "Enalapril" is actually **trandolapril**;
`617312` labeled "Atorvastatin 20 mg" is **10 mg**). Because the scorer matched on
code, a model that read the (wrong) code from the bundle and echoed it "passed"
against a wrong gold. **Both wrong, reported as correct.**

**Why it happens:** an LLM-authored benchmark encodes the author model's own
errors. If the evaluated model shares them (likely — same training distribution),
the error is invisible to a self-referential check.

**Defense:** verify every code against an external authority (RxNav, LOINC,
`tx.fhir.org`). See `scripts/verify_terminology.py`, `docs/DATA_INTEGRITY.md`.

## Instance 2 — A lenient home-grown validator

**Symptom:** generated FHIR resources scored FV 90–100.

**Reality:** the hand-written structural validator didn't require
`MedicationRequest.medication[x]` and didn't catch a non-numeric
`valueQuantity.value` — both invalid under R4, both passed. The benchmark was the
judge of what counts as valid FHIR, and it judged leniently in exactly the way its
author model tends to emit.

**Defense:** delegate structural validity to the official HL7 R4B models
(`fhir.resources`), not a checker we wrote. See `benchmark_runner/fhir_validate.py`.

## Instance 3 — A scorer that fabricates failures (the dangerous one)

**Symptom:** under a deliberately vague, production-style prompt ("what medications
is this patient currently on?"), a substring-presence scorer reported that **all
three** frontier models *failed* — they "included" discontinued / on-hold /
entered-in-error medications.

**Reality:** reading the raw output showed the models answered **better than the
binary gold**. Opus returned a table of the 2 active meds, a separate table of the
4 non-active ones *with their status and reason*, and a clinical note that the
on-hold prednisone might be resumed and is worth flagging. The substring scorer
counted the mere presence of "amoxicillin" anywhere in the text as inclusion in
the active list — a **false positive of the scorer**.

**Why this is the most dangerous instance:** the author *wanted* to find a failure
(the whole exercise was "find where the frontier model drops below 100"). Wanting
a result makes it easy to build a scorer that produces it. A naive scorer + a
motivated author = a fabricated finding, in whichever direction the author leans.

**Defense:** never score open-ended output by string matching; always inspect raw
output before declaring a failure; for free-form answers, scoring needs a verified
structural/judge approach (and even then, adversarially checked).

---

## Principles that fell out of this

1. **An independent oracle for every dimension.** Terminology → official services.
   FHIR validity → official models. Open-ended correctness → verified extraction,
   never substring presence. If the benchmark is the only authority for a claim,
   distrust the claim.
2. **Inspect raw output before believing a verdict.** Three times the aggregate
   number lied; three times the raw artifact told the truth.
3. **The author's expectation is a bias source.** Selection of difficulty and
   design of the scorer both bend toward what the author expects. Cross-vendor
   runs (does the author's model top the ranking? it did not) and external oracles
   are the antidotes.
4. **Report failure rate, not the mean.** A model that is right 95% of the time
   scores ~99 on average but produces the 1-in-20 error a practitioner actually
   sees. `pass_rate` / `worst_case` over multiple samples capture this; the mean
   hides it.
5. **"The model failed" is the least likely explanation.** For 2026 frontier
   models on atomic FHIR tasks with clean data, near-100 is genuine (validated
   cross-vendor). Apparent failures were instrument artifacts or sampling noise.
   The production gap lives in specification, integration, scale, and the variance
   tail — not in atomic capability.

---

## What this means for reading our results

Any score this benchmark reports should be read as: *"under an independent oracle,
with verified data, over multiple samples, here is the pass rate."* A single mean
of 100 from a self-authored, single-run, substring-scored benchmark would have
been — and briefly was — wrong on all three counts. The value of this project is
less the leaderboard and more the discipline that makes the leaderboard
trustworthy.
