# Task Taxonomy

Part of **Prometheus Frontier** · FHIR Agent Benchmark.

> This document defines **what the benchmark measures**, independent of any
> particular case, model, or prompt. It is the conceptual backbone: every
> benchmark case targets exactly one **capability** defined here, and every
> capability maps to a fixed set of **scoring dimensions** (see `SCORING.md`).

Status: **v0.1 draft** — the taxonomy is versioned and governed (see
[Versioning & governance](#versioning--governance)). Capability IDs are stable
once published; they are never reused or renumbered.

---

## How to read this document

The taxonomy has three levels:

```
Family            (7)    e.g. Patient Understanding
  └─ Capability   (~30)  e.g. PU-01 Active Conditions
       └─ Case    (many) e.g. pf-fhir-agent-0001
```

- A **family** is a coarse competence area.
- A **capability** is a single, concretely testable skill with a stable ID, a
  fixed input contract, and a fixed output contract.
- A **case** is one instance: synthetic FHIR data + an instruction targeting
  one capability + ground truth + scoring config.

Each capability is tagged with:

| Tag | Meaning |
|-----|---------|
| **Tier** | `core` = in v0.1; `ext` = planned for a later release |
| **Difficulty** | `L1` (extraction) · `L2` (reasoning) · `L3` (multi-step / safety-critical) |
| **Output** | The output contract family the agent must return (see [Output contracts](#output-contracts)) |
| **Dimensions** | Which scoring dimensions apply (CC, FV, SF, TRC, SR — defined in `SCORING.md`) |

---

## Capability ID scheme

```
<FAMILY>-<NN>      e.g.  MR-04
```

- `FAMILY` is a two-letter family code (below).
- `NN` is a zero-padded sequence within the family.
- IDs are **append-only and immutable**. Deprecated capabilities are marked
  `deprecated` but keep their ID forever, so historical leaderboard results
  remain interpretable.

| Code | Family |
|------|--------|
| `PU` | Patient Understanding |
| `MR` | Medication Reconciliation |
| `TR` | Timeline Reasoning |
| `FG` | FHIR Generation |
| `DQ` | Data Quality |
| `SA` | Safety |
| `TX` | Transformation & Mapping |

Every capability also has a machine slug used in `task.json` (e.g.
`patient_understanding.active_conditions`).

---

## Family 1 — Patient Understanding (`PU`)

*Can the agent read a FHIR Bundle and state the patient's current clinical
state?* This is the floor: nothing else is safe if this fails.

| ID | Capability | Slug | Tier | Diff | Output | Dimensions |
|----|------------|------|------|------|--------|------------|
| PU-01 | Active Conditions | `active_conditions` | core | L1 | `entity_list` | CC, TRC, SR |
| PU-02 | Active Medications | `active_medications` | core | L1 | `entity_list` | CC, TRC, SR |
| PU-03 | Allergies & Intolerances | `allergies` | core | L1 | `entity_list` | CC, TRC, SR |
| PU-04 | Latest Encounter | `latest_encounter` | core | L1 | `scalar` | CC, TRC, SR |
| PU-05 | Recent Key Observations | `recent_observations` | core | L2 | `entity_list` | CC, TRC, SR |
| PU-06 | Demographics & Administrative | `demographics` | core | L1 | `structured` | CC, TRC, SR |
| PU-07 | Care Plan Status | `careplan_status` | ext | L2 | `structured` | CC, TRC, SR |

**Why it matters:** every downstream task assumes the agent can locate and
classify the current-state resources. PU isolates that assumption so failures
elsewhere can be attributed correctly.

---

## Family 2 — Medication Reconciliation (`MR`)

*Can the agent produce a correct, safe active medication picture?* High clinical
risk, well suited to structured evaluation.

| ID | Capability | Slug | Tier | Diff | Output | Dimensions |
|----|------------|------|------|------|--------|------------|
| MR-01 | Active Medication List | `active_medication_list` | core | L2 | `entity_list` | CC, TRC, SR |
| MR-02 | Discontinued Medications | `discontinued_medications` | core | L2 | `entity_list` | CC, TRC, SR |
| MR-03 | Duplicate Therapy Detection | `duplicate_therapy` | core | L2 | `flag_list` | CC, SF, TRC, SR |
| MR-04 | Allergy–Medication Conflict | `allergy_med_conflict` | core | L3 | `flag_list` | CC, SF, TRC, SR |
| MR-05 | Dose / Frequency Consistency | `dose_consistency` | ext | L2 | `flag_list` | CC, SF, TRC, SR |
| MR-06 | Drug–Drug Interaction (flagging) | `ddi_flagging` | ext | L3 | `flag_list` | CC, SF, TRC, SR |

> **Decision:** MR-06 (drug–drug interactions) is `ext`, not `core`. It requires
> an external interaction knowledge base, which would couple benchmark results
> to that KB's coverage and version. v0.1 stays self-contained: every correct
> answer must be derivable from the case's own resources.

---

## Family 3 — Timeline Reasoning (`TR`)

*Can the agent reason across time instead of flattening history?* Many model
failures hide here.

| ID | Capability | Slug | Tier | Diff | Output | Dimensions |
|----|------------|------|------|------|--------|------------|
| TR-01 | Event Ordering | `event_ordering` | core | L2 | `ordered_list` | CC, TRC, SR |
| TR-02 | State Changes | `state_changes` | core | L2 | `entity_list` | CC, TRC, SR |
| TR-03 | Disease Progression | `disease_progression` | core | L2 | `structured` | CC, TRC, SR |
| TR-04 | Active vs Resolved vs Historical | `state_resolution` | core | L3 | `entity_list` | CC, SF, TRC, SR |
| TR-05 | Medication Change Tracking | `medication_changes` | core | L2 | `ordered_list` | CC, TRC, SR |
| TR-06 | Temporal Anchoring | `temporal_anchoring` | ext | L2 | `scalar` | CC, TRC, SR |

**Why it matters:** TR-04 ("is this condition active, resolved, or just
historical?") is the single most consequential timeline skill — misclassifying a
resolved condition as active drives downstream safety errors, so it carries the
`SF` dimension.

---

## Family 4 — FHIR Generation (`FG`)

*Can the agent emit valid, interoperable FHIR — not prose?*

| ID | Capability | Slug | Tier | Diff | Output | Dimensions |
|----|------------|------|------|------|--------|------------|
| FG-01 | Observation generation | `gen_observation` | core | L2 | `fhir_resource` | FV, CC, TRC |
| FG-02 | Condition generation | `gen_condition` | core | L2 | `fhir_resource` | FV, CC, TRC |
| FG-03 | Encounter generation | `gen_encounter` | core | L2 | `fhir_resource` | FV, CC, TRC |
| FG-04 | MedicationRequest generation | `gen_medicationrequest` | core | L2 | `fhir_resource` | FV, CC, SF, TRC |
| FG-05 | AllergyIntolerance generation | `gen_allergyintolerance` | ext | L2 | `fhir_resource` | FV, CC, SF, TRC |
| FG-06 | CarePlan generation | `gen_careplan` | ext | L3 | `fhir_resource` | FV, CC, TRC |
| FG-07 | Bundle assembly w/ references | `gen_bundle` | ext | L3 | `fhir_bundle` | FV, CC, TRC |

> **Decision:** generation tasks are evaluated against **structural validity +
> semantic correctness of populated fields**, never against byte-equality with a
> single "correct" resource. There are many valid serializations of the same
> clinical fact; scoring must not punish legitimate variation (see `SCORING.md` →
> FHIR Validity and Clinical Correctness).

---

## Family 5 — Data Quality (`DQ`)

*Can the agent detect that the underlying data is broken?* A clinical agent that
trusts bad data is dangerous.

| ID | Capability | Slug | Tier | Diff | Output | Dimensions |
|----|------------|------|------|------|--------|------------|
| DQ-01 | Broken References | `broken_references` | core | L1 | `flag_list` | CC, TRC, SR |
| DQ-02 | Missing Required Fields | `missing_fields` | core | L1 | `flag_list` | CC, FV, TRC, SR |
| DQ-03 | Contradictions | `contradictions` | core | L2 | `flag_list` | CC, SF, TRC, SR |
| DQ-04 | Implausible Values | `implausible_values` | core | L2 | `flag_list` | CC, SF, TRC, SR |
| DQ-05 | Orphan / Unlinked Resources | `orphan_resources` | ext | L2 | `flag_list` | CC, TRC, SR |

**Why it matters:** DQ tasks are the bridge to Safety. Detecting a contradiction
(DQ-03) or an implausible lab (DQ-04) is often the difference between a safe and
an unsafe downstream decision, hence the shared `SF` dimension.

---

## Family 6 — Safety (`SA`)

*Does the agent behave safely — flagging hazards, refusing on insufficient data,
and never inventing clinical facts?* Safety is both a **family** (dedicated
tasks) and a **cross-cutting dimension** (`SF`) applied to many other
capabilities.

| ID | Capability | Slug | Tier | Diff | Output | Dimensions |
|----|------------|------|------|------|--------|------------|
| SA-01 | Allergy Violation Detection | `allergy_violation` | core | L3 | `flag_list` | SF, CC, TRC, SR |
| SA-02 | Medication Error Detection | `medication_error` | core | L3 | `flag_list` | SF, CC, TRC, SR |
| SA-03 | Missing Critical Data → Abstain | `missing_critical_data` | core | L3 | `abstention` | SF, CC, SR |
| SA-04 | Unsupported Recommendation Avoidance | `no_unsupported_reco` | core | L3 | `abstention` | SF, CC |
| SA-05 | Hallucinated Fact Avoidance | `no_hallucinated_facts` | core | L3 | `flag_list` | SF, CC, TRC |

> **Decision:** safe **abstention** is a first-class, *rewarded* behavior. When a
> case lacks the data required to answer safely (SA-03/SA-04), the correct output
> is an explicit, justified refusal — not a guess. The output contract
> `abstention` and the Safety dimension encode this (see `SCORING.md`).

---

## Family 7 — Transformation & Mapping (`TX`)

*Can the agent turn **non-FHIR input** — a proprietary vendor JSON export or a
plain-text clinical note — into correct, valid FHIR?* This is the dominant
real-world integration task: the input does not tell you which resource to
produce, which fields map where, or which codes to use. The agent must decide
all of that itself.

The contrast with `FG` is deliberate: FG instructions **dictate** the target
resource type, codes, and field values (they measure assembly); TX instructions
**withhold** them (they measure resource-type identification, field mapping,
terminology selection from memory, vocabulary mapping — e.g. a vendor status
`"F"` → `final`, `sex: "M"` → `male` — and conformance decisions).

| ID | Capability | Slug | Tier | Diff | Output | Dimensions |
|----|------------|------|------|------|--------|------------|
| TX-01 | Non-standard JSON → FHIR Resource | `json_to_fhir_resource` | core | L2 | `fhir_resource` | CC, FV, TRC |
| TX-02 | Plain Text → FHIR Resource (un-guided) | `text_to_fhir_unguided` | core | L2 | `fhir_resource` | CC, FV, TRC |
| TX-03 | Non-standard Export → FHIR Bundle | `json_to_fhir_bundle` | core | L3 | `fhir_bundle` | CC, FV, TRC |
| TX-04 | IG-conformant Transformation (un-guided US Core) | `ig_conformance_unguided` | core | L3 | `fhir_resource` | CC, FV, TRC |
| TX-05 | R4 → R5 Version Migration | `r4_to_r5_migration` | ext | L3 | `fhir_resource` | CC, FV, TRC |

**Why it matters:** in production, "generate FHIR" almost never means "fill in
the fields I dictate" — it means "here is a LIS/EHR export or a note; produce
the right resources." TX-04 additionally tests whether the model knows an
implementation guide (US Core) *from memory* — the case asks for conformance
without providing the profile URL or required bindings. TX-05 tests version
migration (e.g. R4 `medication[x]` → R5 `medication` CodeableReference), scored
against the official R5 models.

> **Scoring note (anti-bias):** un-guided coding can have more than one
> defensible answer. Where legitimate alternatives exist, ground truth uses
> `equals_any` assertions instead of a single `equals` — a deliberate guard
> against the false-failure mode documented in `METHODOLOGY_LESSONS.md` §3.

---

## Output contracts

Every capability returns one of a small, fixed set of output shapes. Fixing
these now lets `task.json` / `ground_truth.json` schemas stay small and lets the
scorer be largely deterministic. All outputs are JSON.

### `entity_list`
A set of clinical entities, each coded and traceable.
```json
{
  "items": [
    {
      "label": "Type 2 diabetes mellitus",
      "code": {"system": "http://snomed.info/sct", "code": "44054006"},
      "status": "active",
      "evidence": ["Condition/cond-001"]
    }
  ]
}
```

### `scalar`
A single value (date, code, id, enum).
```json
{ "value": "Encounter/enc-007", "evidence": ["Encounter/enc-007"] }
```

### `structured`
A fixed-shape object defined per capability (e.g. demographics).
```json
{ "fields": { "age": 67, "sex": "female" }, "evidence": ["Patient/pat-001"] }
```

### `ordered_list`
A sequence whose **order** is scored (chronology, change sequence).
```json
{ "sequence": ["Encounter/enc-001", "Encounter/enc-004", "Encounter/enc-007"] }
```

### `flag_list`
Zero or more issues found. Empty list is a valid (and sometimes correct) answer.
```json
{
  "flags": [
    {
      "type": "allergy_med_conflict",
      "severity": "critical",
      "description": "Amoxicillin ordered despite documented penicillin allergy.",
      "evidence": ["MedicationRequest/mr-003", "AllergyIntolerance/allergy-001"]
    }
  ]
}
```

### `abstention`
An explicit refusal with justification and what is missing.
```json
{
  "answer": null,
  "abstained": true,
  "reason": "No recent renal function results; dosing cannot be assessed safely.",
  "missing": ["Observation: eGFR within 90 days"]
}
```

### `fhir_resource` / `fhir_bundle`
A generated FHIR R4 resource or Bundle (validated structurally + semantically).

> **Decision:** **every** non-generation output carries an `evidence` array of
> FHIR references. Traceability is not an optional extra task — it is required on
> most answers and scored via the `TRC` dimension. This is a core
> differentiator: the benchmark rewards agents that can *show their work* against
> source resources.

---

## Summary

| Family | Core caps | Ext caps | Total |
|--------|:---------:|:--------:|:-----:|
| Patient Understanding (PU) | 6 | 1 | 7 |
| Medication Reconciliation (MR) | 4 | 2 | 6 |
| Timeline Reasoning (TR) | 5 | 1 | 6 |
| FHIR Generation (FG) | 4 | 3 | 7 |
| Data Quality (DQ) | 4 | 1 | 5 |
| Safety (SA) | 5 | 0 | 5 |
| **Total** | **28** | **8** | **36** |

**v0.1 scope = 28 `core` capabilities across 6 families.** The 8 `ext`
capabilities are specified now (so the schema and IDs are stable) but are not
required for the first release.

### v0.1 seed focus

The first 10 seed cases (see `ROADMAP.md`) deliberately cover only **three**
families — PU, MR, DQ/SA — to validate the format end-to-end before scaling:

- Patient Snapshot Understanding (PU-01..PU-04)
- Medication Reconciliation (MR-01..MR-04)
- Data Quality & Safety (DQ-01..DQ-04, SA-01..SA-03)

---

## Out of scope for v0.1

To keep results interpretable and reproducible, v0.1 explicitly excludes:

- **Live API / tool-use agents** (multi-step execution) — deferred to Phase 4;
  the `AE` Agentic Execution dimension is defined in `SCORING.md` but unused in v0.1.
- **External knowledge bases** (drug interaction DBs, guideline engines).
- **Diagnosis / treatment recommendation** — this is not a diagnostic benchmark.
- **PHI / real patient data** — all cases are synthetic.
- **Non-English renderings** — `language` is in the schema but fixed to `en` for v0.1.

---

## Versioning & governance

- The taxonomy is versioned with the benchmark (`v0.1`, `v0.2`, …).
- **Capability IDs are immutable.** New capabilities append; obsolete ones are
  marked `deprecated` but never removed or renumbered.
- A capability's **output contract and applicable dimensions** are part of its
  contract; changing them requires a new minor version and is recorded in a
  `CHANGELOG`.
- Leaderboard results are always reported against a specific taxonomy version so
  cross-version comparisons are explicit, never silent.

---

## Next

With the taxonomy fixed, the next deliverable is `SCORING.md` (how each
dimension is computed and aggregated). After that, the JSON schemas
(`task.json`, `ground_truth.json`, `scoring.json`) can be derived directly from
the output contracts above — at which point the benchmark stops being a document
and becomes runnable.
