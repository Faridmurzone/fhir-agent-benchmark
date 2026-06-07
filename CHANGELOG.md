# Changelog

All notable changes to the benchmark, its taxonomy, and its scoring are recorded
here. Benchmark results always cite a `taxonomy_version` and a `scoring_version`.

The format follows [Keep a Changelog](https://keepachangelog.com/). Capability
IDs are immutable across versions.

## [Unreleased]

### Added
- **Family TX — Transformation & Mapping** (5 capabilities, TX-01..05): the
  benchmark now measures the dominant real-world integration task — turning
  **non-FHIR input** into correct FHIR — which FG deliberately did not (FG
  instructions dictate resource type, codes and values; TX withholds them).
  Cases `0030`–`0034`: `0030` (TX-01, proprietary LIS JSON → Observation,
  un-guided: resource-type identification, LOINC from memory forced by units,
  vendor vocab mapping F→final, date format conversion), `0031` (TX-02,
  plain-text note → Condition, SNOMED from memory), `0032` (TX-03, EHR chart
  extract → multi-resource Bundle with internal referential consistency),
  `0033` (TX-04, US Core conformance **without** being given the profile URL,
  category system or bindings — tests IG knowledge from memory), `0034` (TX-05,
  R4→R5 MedicationRequest migration: `medication[x]` → CodeableReference).
- **FV per-version validation**: `scoring.json` option `fhir_version: R4|R5`;
  `fhir_validate.validate(resource, version=...)` validates against the official
  R4B or R5 models. Verified discriminative: an un-migrated R4 shape fails R5
  validation and vice versa.
- **`equals_any` assertions** in generation ground truth: for un-guided coding
  tasks where more than one code is defensible (e.g. essential hypertension
  59621000 vs hypertensive disorder 38341003), asserting a single `equals`
  would fabricate failures (METHODOLOGY_LESSONS §3).
- New rendering `source_json` (non-FHIR vendor input) in `task.schema.json`.
- 17 new tests (`tests/test_transformation.py`): case validity, oracle ceiling,
  equals_any semantics, vendor-status leak detection, R4/R5 discrimination,
  un-guided US Core profile declaration, multi-wildcard bundle assertions.
- **Multi-sample runs** (`run_model(n_samples=N)`, `run_case_sampled`): each case
  is run N times and the scorecard reports overall mean / std / min / max. Needed
  because models (especially fast tiers) are non-deterministic — a single run is
  not a reliable score. A cross-vendor sanity run showed Gemini 2.5 Flash dropping
  to 41–61 on cases it scored 100 on re-runs, i.e. temporal variance, not a real
  capability gap; multi-sampling distinguishes the two.
- `docs/METHODOLOGY_LESSONS.md`: the scorer/data/validator — not the model — is
  the main bias risk; three documented instances (wrong RxNorm codes, lenient
  home-grown validator, substring scorer fabricating failures) and the
  independent-oracle defense for each. `STATUS.md`: working done/pending log.
- Foundation docs: README, VISION, ROADMAP, CONCEPTUAL_DESIGN.
- Task taxonomy v0.1: 6 families, 36 capabilities (28 core + 8 ext), with stable IDs.
- Scoring methodology v0.1: 6 dimensions, safety as a multiplicative gate,
  serialization robustness, traceability; `scoring/defaults.json`.
- JSON Schemas for `task.json`, `ground_truth.json`, `scoring.json`.
- Machine-readable taxonomy (`taxonomy/taxonomy.json`).
- First seed case `pf-fhir-agent-0001` (MR-01) with 4 input renderings.
- 6 hard cases targeting specific failure modes: `0010` (MR-01 status traps:
  on-hold/completed/entered-in-error are not active), `0011` (MR-03 therapeutic
  duplication across two different ACE inhibitors), `0012` (TR-04 recurrent
  condition — current state, not stale status), `0013` (DQ-03 cross-resource
  contradiction), `0014` (DQ-04 implausible value among normal distractors),
  `0015` (MR-04 false-alarm trap: entered-in-error allergy must NOT be flagged).
- `benchmark_runner`: case loading, schema validation, and consistency checks.
- Scoring engine: `metrics.py` (set F1, scalar, ordered, structured primitives)
  and `score_case.py` (CC, TRC, SF, SR, lightweight FV; per-rendering →
  per-case → per-model aggregation; safety gate + hard cap).
- 3 more seed cases: `pf-fhir-agent-0002` (PU-01), `0004` (MR-04, exercises the
  safety gate with a critical allergy–medication conflict), `0008` (DQ-01).
- Deterministic synthetic case generator (`generator/`) for MR-01, plus one
  generated example case `pf-fhir-agent-0900`.
- Adversarial generator (`generator/adversarial.py`) with **gold by
  construction**: hard MR-01 at scale (many medications, mixed statuses) and hard
  MR-03 (find all same-class therapeutic duplications among distractors).
  Difficulty knobs; fully deterministic. Empirical note: single-shot, single-
  capability tasks (even at scale) do not break a frontier model (Claude Opus 4.8
  scored 100); these cases discriminate weaker/open models, while frontier-vs-
  frontier discrimination will require the agentic/multi-step regime (Phase 4).
- CLI `score` and `generate` subcommands.
- Baseline run harness: prompt rendering per input format, model adapters
  (`oracle`, `empty` — credential-free; `anthropic` — gated by API key), a
  runner (render → answer → parse → score → aggregate), and a markdown results
  report. CLI `run` subcommand; results written to `results/` (gitignored).
- Vendor-neutral model adapters: `anthropic` (Claude), `openai` (GPT), `gemini`
  (Google) — all gated by their API key. Selectable as `--model <vendor>:<model>`.
  Defaults updated to current models (`claude-opus-4-8`, `gpt-5.5`,
  `gemini-3.5-flash`); the OpenAI adapter uses `max_completion_tokens` for
  GPT-5.x/o-series with a fallback to `max_tokens` for GPT-4.x.
- Cross-vendor bias check (n=3, current models): Gemini 3.5 Flash 100 / Opus 4.8
  99 / GPT-5.5 97 — the benchmark's author model (Opus) does **not** top the
  ranking, evidence against self-authoring bias. Single-run variance is large
  (GPT models swing 61–100 on some MR-01/PU-01 cases), which is why multi-sampling
  is required; results not published (pre-`v0.1.0`).
- Stability & versioning policy documented in the README (pre-release; results
  only against tagged versions).

- Agentic regime foundation (Phase 4): in-memory read-only FHIR environment
  (`fhir_env.py`) the agent must query via tools (`list_resource_types`/`search`/
  `read`/`finish`); a model-agnostic tool-use loop with a step budget; the **AE**
  (Agentic Execution) dimension scoring evidence recall, efficiency, decision
  correctness, and a safety gate (concluding "safe" when unsafe, or deciding
  without inspecting required evidence, is penalized). CLI `agentic`; task format
  under `agentic_tasks/`; design in `docs/AGENTIC.md`. Empirical note: a single-
  hop agentic safety check does not yet challenge a frontier model (Opus 4.8
  gathered evidence and decided correctly, AE/CC/SF = 100) — multi-hop tasks are
  the next step.
- Agentic tasks can carry an inline `bundle` (self-contained, no case folder),
  enabling FHIR resources the single-shot renderers don't cover (e.g.
  MedicationStatement). 3 multi-hop FHIR-native tasks: `agt-0002` (pick the most
  recent eGFR by effectiveDateTime → renal contraindication), `agt-0003`
  (reconcile MedicationRequest order vs MedicationStatement actual use), `agt-0004`
  (follow MedicationRequest.reasonReference to the Condition and read its
  clinicalStatus). Empirical note: Opus 4.8 solved all three (100) — frontier
  FHIR-native read/navigation is at ceiling; discrimination will require
  generation (FHIR validity) and large-context / missing-data regimes.

- FHIR generation cases (FG) with a path-assertion CC scorer: `0020` (FG-01
  Observation/HbA1c), `0021` (FG-02 Condition), `0022` (FG-04 MedicationRequest).
  The model receives a clinical note + context bundle and must emit a valid FHIR
  R4 resource. CC scores path assertions (`code.coding[*].code`, `valueQuantity.value`,
  `subject.reference`, …) — robust to valid serialization variation; FV scores
  structural validity; TRC scores recall of required internal references. Each
  gold carries a `reference_resource` (oracle baseline + example solution).
  Empirical note: Opus 4.8 generated all three correctly (FV 90 / CC 100 /
  TRC 100; FV is capped at 90 because profile validation — layer 7 — is deferred).
  Seventh axis at ceiling for a frontier model; discrimination on generation will
  require profile conformance (US Core), transaction bundles, and spec edge cases
  (contained resources, choice types, identifier references).

- FV layer 7 — **US Core profile conformance** (`score_fv` + `US_CORE_PROFILES`
  for Patient/Condition/Observation/MedicationRequest/AllergyIntolerance/
  Encounter). Conditional: a case opts in via `scoring.json`
  `options.profile: "us-core"`; layer 7 then checks `meta.profile`, must-support
  elements, and required category bindings (up to 10 pts). When not requested,
  layers 1–6 renormalize to 100 (no penalty for an unrequested profile). New case
  `0023` (US Core Condition). The layer discriminates — a valid R4 resource that
  is not US Core-conformant drops to FV 93 / overall 60 — though Opus 4.8, given
  explicit instructions, produced a fully conformant resource (FV/CC/TRC 100).

- **Independent FHIR validation for FV** (`fhir_validate.py` using `fhir.resources`
  R4B official models). Structural R4 validity is now decided by a validator built
  from HL7's StructureDefinitions, not a hand-written checker — removing a
  "judge-and-jury" bias. Cross-checking surfaced real holes the heuristic missed
  (e.g. it did not require `MedicationRequest.medication[x]`, nor catch a non-
  numeric `valueQuantity.value`); the official validator now flags both. Optional
  dependency with a documented heuristic fallback; the result records which
  validator was used.

- **Independent terminology verification** (`scripts/verify_terminology.py`):
  checks every RxNorm/LOINC/SNOMED coding against official services (RxNav,
  NLM Clinical Tables, `tx.fhir.org` `$lookup`). Distinguishes INVALID from
  network-UNKNOWN. Documented in `docs/DATA_INTEGRITY.md`.

### Fixed
- **Corrected ~10 RxNorm codes + 1 SNOMED code** in the hand-authored data that
  were plausible but pointed at the wrong drug/strength/form (e.g. `199351` was
  trandolapril, not enalapril; `617312` was atorvastatin 10 mg, not 20 mg) — the
  textbook "correlated error" bias a self-authored benchmark is prone to. Caught
  by the external verifier; data now passes with 0 INVALID. Generator catalogs
  updated and case `0900` regenerated.

### Changed
- **Matching semantics (scoring).** Surfaced by a sanity run: code-only entity
  matching unfairly scored narrative/timeline renderings at 0 (they carry no
  codes), and exact flag-`type` string matching zeroed correct hazard flags.
  Now: entities match on **code OR evidence reference OR normalized label**
  (renderings comparable); flags match on **evidence overlap** (not the free-text
  type). `docs/SCORING.md` updated accordingly.

### Decisions
- **License:** MIT (single license for code and synthetic cases). Revisit before
  v0.1 release if a dual code/data license (e.g. CC-BY-4.0 for cases) is preferred.
- **Distribution:** developed inside the `prometheus` monorepo; the benchmark
  will be split out to its own public repository via `git subtree split`
  (preserving history) when ready — see `docs/PUBLISHING.md`.
