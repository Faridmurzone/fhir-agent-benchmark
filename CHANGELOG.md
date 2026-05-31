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
- `benchmark_runner`: case loading, schema validation, and consistency checks.
- Scoring engine: `metrics.py` (set F1, scalar, ordered, structured primitives)
  and `score_case.py` (CC, TRC, SF, SR, lightweight FV; per-rendering →
  per-case → per-model aggregation; safety gate + hard cap).
- 3 more seed cases: `pf-fhir-agent-0002` (PU-01), `0004` (MR-04, exercises the
  safety gate with a critical allergy–medication conflict), `0008` (DQ-01).
- Deterministic synthetic case generator (`generator/`) for MR-01, plus one
  generated example case `pf-fhir-agent-0900`.
- CLI `score` and `generate` subcommands.
- Baseline run harness: prompt rendering per input format, model adapters
  (`oracle`, `empty` — credential-free; `anthropic` — gated by API key), a
  runner (render → answer → parse → score → aggregate), and a markdown results
  report. CLI `run` subcommand; results written to `results/` (gitignored).
- Vendor-neutral model adapters: `anthropic` (Claude), `openai` (GPT), `gemini`
  (Google) — all gated by their API key. Selectable as `--model <vendor>:<model>`.
- Stability & versioning policy documented in the README (pre-release; results
  only against tagged versions).

### Decisions
- **License:** MIT (single license for code and synthetic cases). Revisit before
  v0.1 release if a dual code/data license (e.g. CC-BY-4.0 for cases) is preferred.
- **Distribution:** developed inside the `prometheus` monorepo; the benchmark
  will be split out to its own public repository via `git subtree split`
  (preserving history) when ready — see `docs/PUBLISHING.md`.
