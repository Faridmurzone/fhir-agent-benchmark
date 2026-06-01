# Changelog

All notable changes to the benchmark, its taxonomy, and its scoring are recorded
here. Benchmark results always cite a `taxonomy_version` and a `scoring_version`.

The format follows [Keep a Changelog](https://keepachangelog.com/). Capability
IDs are immutable across versions.

## [Unreleased]

### Added
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
