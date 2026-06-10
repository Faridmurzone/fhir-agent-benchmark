# FHIR Agent Benchmark

An open benchmark for evaluating AI agents on **FHIR-native healthcare
workflows** — structured clinical reasoning, medication reconciliation, resource
generation, data-quality detection, safety evaluation, and serialization
robustness.

## 📊 Preliminary results

> ⚠️ **Preliminary, pre-`v0.1.0`.** The spec is not frozen yet, so these numbers
> are exploratory and **not official**. Official results will only be published
> against a tagged release — see
> [Stability & versioning](#stability--versioning).

Sweep of **2026-06-07** · 20 cases (including the new **TX** transformation
family) · **3 samples per case** · scoring `v0.1`.

| Model | Mean | Pass % | Worst | σ | CC | FV | SF | TRC | SR | TX |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **Anthropic (Claude)** | | | | | | | | | | |
| Claude Opus 4.8 | 99 | 93 | 71 | 1 | 100 | 100 | 100 | 100 | 100 | 98 |
| Claude Opus 4.6 | 99 | 93 | 79 | 0 | 100 | 100 | 100 | 100 | 97 | 100 |
| Claude Opus 4.1 | 100 | 95 | 90 | 0 | 100 | 100 | 100 | 100 | 100 | 100 |
| Claude Sonnet 4.6 | 99 | 90 | 80 | 0 | 100 | 100 | 99 | 99 | 100 | 100 |
| Claude Haiku 4.5 | 96 | 82 | 51 | 1 | 98 | 91 | 99 | 90 | 97 | 88 |
| **Google (Gemini)** | | | | | | | | | | |
| Gemini 3.5 Flash | 97 | 93 | 0 | 4 | 95 | 88 | 100 | 90 | 100 | 87 |
| Gemini 3.1 Pro (preview) | 100 | 100 | 100 | 0 | 100 | 100 | 100 | 100 | 100 | 100 |
| Gemini 2.5 Pro | 99 | 95 | 69 | 1 | 100 | 91 | 100 | 100 | 100 | 99 |
| Gemini 2.5 Flash | 95 | 82 | 61 | 5 | 96 | 100 | 100 | 82 | 82 | 92 |
| **OpenAI (GPT)** | | | | | | | | | | |
| GPT-5.5 | 99 | 92 | 61 | 1 | 100 | 100 | 100 | 100 | 100 | 100 |
| GPT-5 | 99 | 92 | 90 | 0 | 100 | 100 | 100 | 100 | 100 | 100 |
| GPT-4.1 | 99 | 97 | 72 | 1 | 100 | 100 | 100 | 100 | 100 | 98 |
| GPT-4o | 97 | 92 | 43 | 1 | 98 | 91 | 100 | 90 | 100 | 87 |

**How to read it.** **Mean** = mean overall score across cases and samples ·
**Pass %** = share of cases at or above the pass threshold · **Worst** = worst
single case across samples · **σ** = standard deviation of the overall score ·
**CC** clinical correctness · **FV** FHIR validity · **SF** safety · **TRC**
traceability · **SR** serialization robustness · **TX** = overall score on the
transformation family (non-FHIR input → FHIR).

Three takeaways:

- **Atomic capabilities are saturated.** On the classic families nearly every
  frontier model scores ~100 — the signal is no longer there.
- **The TX (transformation) family discriminates.** TX-05 (R4→R5 migration) is
  the strongest discriminator: GPT-4o fails it consistently (it doesn't migrate
  `medication[x]` → `CodeableReference`), while current frontier models pass.
  TX-04 (US Core without being given the profile) hits the flash-tier models.
- **Variance matters.** Flash-tier models are noisy (Gemini 3.5 Flash has a
  worst case of 0); Pro/Opus/GPT-5-class models are stable (σ≈0). That's why we
  report the mean of 3 samples plus a pass rate — never a single run.

> **Status:** early design phase (`v0.1`). In place and runnable: the taxonomy,
> scoring methodology, JSON schemas, a multi-dimensional **scoring engine**, a
> deterministic **synthetic case generator**, **5 validated seed cases** across
> Patient Understanding, Medication Reconciliation, and Data Quality (including a
> safety-gate case), and a **baseline run harness** (oracle / empty baselines run
> without credentials; real model adapters gated by API key). Contributions and
> discussion are welcome.
>
> ⚠️ **Pre-release.** The spec (taxonomy, scoring, schemas, cases) may change
> until the first tagged release `v0.1.0`. The results above are preliminary —
> no official results are published until the spec is frozen at a tag; see
> [Stability & versioning](#stability--versioning).

Part of **Prometheus Frontier** — building open, reproducible, vendor-neutral
evaluation for healthcare AI.

---

## Why

Most existing LLM benchmarks focus on general reasoning, coding, mathematics, or
question answering. Healthcare introduces a different class of challenges:
structured clinical data, longitudinal patient histories, temporal reasoning,
medical safety constraints, and interoperability standards.

There is no equivalent of SWE-Bench, MMLU, or HumanEval for **healthcare
interoperability and FHIR-native agents**. This project aims to fill that gap.

FHIR Agent Benchmark is **not** a medical QA benchmark, a diagnosis benchmark, a
text-to-FHIR-only benchmark, or a generic agent benchmark. It is FHIR-native,
agent-oriented, safety-aware, traceability-focused, and serialization-aware.

## What it measures

Six task families, ~30 concrete capabilities (see [`docs/TASK_TAXONOMY.md`](docs/TASK_TAXONOMY.md)):

| Family | Examples |
|--------|----------|
| **Patient Understanding** | active conditions, active medications, allergies, latest encounter |
| **Medication Reconciliation** | active list, duplicate therapy, allergy–medication conflict |
| **Timeline Reasoning** | event ordering, state changes, active vs resolved |
| **FHIR Generation** | Observation, Condition, Encounter, MedicationRequest |
| **Data Quality** | broken references, missing fields, contradictions, implausible values |
| **Safety** | allergy violations, medication errors, safe abstention on missing data |

Models are scored on a **multi-dimensional scorecard** — never a single accuracy
number — where **Safety acts as a gate** on the overall score (see
[`docs/SCORING.md`](docs/SCORING.md)):

```
Clinical Correctness ........  91
FHIR Validity ...............  98
Safety ......................  72   ⚠ gate
Traceability ................  89
Serialization Robustness ....  65
────────────────────────────────
Overall Score ...............  83
```

---

## Quickstart

Requires **Python 3.10+**.

```bash
git clone https://github.com/Faridmurzone/fhir-agent-benchmark.git
cd fhir-agent-benchmark
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Validate every benchmark case (schemas + FHIR reference integrity + taxonomy)
python -m benchmark_runner.cli validate-all

# Validate a single case
python -m benchmark_runner.cli validate cases/pf-fhir-agent-0001

# Score a model submission against a case (multi-dimensional scorecard)
python -m benchmark_runner.cli score cases/pf-fhir-agent-0001 submission.json

# Generate a synthetic case (deterministic; same seed => identical case)
python -m benchmark_runner.cli generate --out cases/pf-fhir-agent-0901 --seed 7

# Run a baseline against all cases -> results/<model>.{json,md}
python -m benchmark_runner.cli run --model oracle    # upper bound (copies ground truth)
python -m benchmark_runner.cli run --model empty     # lower bound (answers nothing)
python -m benchmark_runner.cli run --model anthropic:claude-opus-4-8  # needs ANTHROPIC_API_KEY
python -m benchmark_runner.cli run --model openai:gpt-4o              # needs OPENAI_API_KEY
python -m benchmark_runner.cli run --model gemini:gemini-2.5-flash    # needs GOOGLE_API_KEY

# Run an AGENTIC task (Phase 4): the model must query a FHIR env via tools
python -m benchmark_runner.cli agentic agentic_tasks/agt-0001.json --model anthropic:claude-opus-4-8

# Run the test suite
pytest -q
```

The `oracle` and `empty` baselines run with **no credentials** and prove the
full loop (render → answer → parse → score → report). Real model adapters
(`anthropic`) are gated by an API key. Results land in `results/` (gitignored,
reproducible).

A case validates only if its `task.json` / `ground_truth.json` / `scoring.json`
pass their JSON Schemas **and** every evidence reference resolves to a resource
in the FHIR bundle **and** the capability/contract/dimensions match the
taxonomy.

---

## Evaluate your own model

Two ways:

**1. Plug in an adapter** (run end-to-end). Implement the small `Adapter`
protocol in [`benchmark_runner/adapters.py`](benchmark_runner/adapters.py) — a
single method `answer(case, rendering, prompt) -> dict` — register it in
`get_adapter`, then `run --model <name>`. The included `anthropic` adapter is a
worked example.

**2. Score offline outputs** (bring a JSON file). Produce your model's answers
and score them:

```bash
python -m benchmark_runner.cli score cases/pf-fhir-agent-0001 my_output.json
```

The submission JSON matches the case's **output contract**. For an `entity_list`
case (e.g. an active-medication list):

```json
{"items": [
  {"label": "Metformin 500 mg",
   "code": {"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "860975"},
   "status": "active",
   "evidence": ["MedicationRequest/mr-metformin"]}
]}
```

Other contracts: `flag_list` → `{"flags": [...]}`, `scalar` →
`{"value": ..., "evidence": [...]}`, `abstention` →
`{"abstained": true, "reason": "...", "missing": [...]}`. To score per input
rendering (and get a Serialization Robustness score), pass an object keyed by
rendering name: `{"fhir_json": {...}, "narrative": {...}}`. See
[`docs/SCORING.md`](docs/SCORING.md) for how each dimension is computed.

---

## Repository layout

```text
fhir-agent-benchmark/
├── README.md · VISION.md · ROADMAP.md   # what & why
├── docs/
│   ├── CONCEPTUAL_DESIGN.md             # design + research background / prior work
│   ├── TASK_TAXONOMY.md                 # the 6 families and ~30 capabilities (IDs)
│   ├── SCORING.md                       # multi-dimensional scoring + safety gate
│   └── PUBLISHING.md                    # how this repo is split out & published
├── taxonomy/taxonomy.json               # machine-readable taxonomy (tooling)
├── schemas/                             # JSON Schemas for task / ground_truth / scoring
├── scoring/defaults.json                # weights, safety penalties, gate params
├── cases/                               # seed cases (0001/0002/0004/0008) + generated (0900)
│   └── pf-fhir-agent-0001/              # bundle + 4 renderings + task/gt/scoring
├── generator/                           # deterministic synthetic case generator
└── benchmark_runner/                    # load, validate, score (metrics + score_case)
```

## Documents

- [`VISION.md`](VISION.md) — problem, opportunity, principles, north star.
- [`ROADMAP.md`](ROADMAP.md) — phases 0–5 and the v0.1 milestone.
- [`docs/CONCEPTUAL_DESIGN.md`](docs/CONCEPTUAL_DESIGN.md) — design and prior work.
- [`docs/TASK_TAXONOMY.md`](docs/TASK_TAXONOMY.md) — what the benchmark measures.
- [`docs/SCORING.md`](docs/SCORING.md) — how it is scored.
- [`docs/AGENTIC.md`](docs/AGENTIC.md) — the agentic regime (Phase 4): tools, loop, AE dimension.
- [`docs/DATA_INTEGRITY.md`](docs/DATA_INTEGRITY.md) — independent validation of FHIR validity and terminology codes against official sources.
- [`docs/METHODOLOGY_LESSONS.md`](docs/METHODOLOGY_LESSONS.md) — why the scorer, not the model, is the main bias risk (3 documented instances).

---

## First milestone — v0.1

- 100 synthetic cases · 5 task families · 7 core FHIR resources · 4 input renderings
- 3 baseline models · a reproducible results report · a public Hugging Face dataset
- **Success criterion:** a third party can reproduce the results from scratch.

All cases are **synthetic** — no PHI, no real patient data.

## Limitations (v0.1)

Honest scope so results aren't over-read:

- **Single-turn only.** Live API / tool-use agents (multi-step execution) are
  out of scope for v0.1 — the agentic-execution dimension is specified but unused.
- **Structural FHIR validity.** The validity check is structural (resource type,
  required fields, reference shape); full profile validation (e.g. US Core) is a
  later layer.
- **English only**, and the seed set is small — coverage grows toward the 100-case
  v0.1 milestone.
- **LLM-as-judge** is bounded to free-text rationale and never overrides a
  deterministic verdict (see `docs/SCORING.md`).

## Stability & versioning

A benchmark is only useful if results are comparable over time, so evolution is
explicit and disciplined:

- **Pre-release status.** Until the first tagged release `v0.1.0`, the spec
  (taxonomy, scoring, schemas, seed cases) is a **draft and may change**. Treat
  contracts as unstable and pin to a commit if you build on them now.
- **Capability IDs are immutable.** `PU-01` always means the same capability;
  IDs are appended, never renumbered or reused — so historical results stay
  interpretable.
- **Every result is versioned.** Results carry a `taxonomy_version` and a
  `scoring_version` (see [`CHANGELOG.md`](CHANGELOG.md)); cross-version
  comparisons always state both.
- **Official results only against tags.** No leaderboard or official model
  results are published until the spec is frozen at a tagged release. Clearly
  labeled **preliminary** numbers (like the table at the top of this README) may
  be shared for discussion, but official results are always tied to a specific
  tag — never to a moving `main`.

In short: the **design** is public (and evolving with community feedback); the
**numbers** wait until the spec is frozen.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The fastest way to help right now is to
propose or review benchmark cases: each one is a folder under `cases/` that must
pass `validate-all`.

## Citation

If you use this benchmark, please cite it — see [`CITATION.cff`](CITATION.cff).

## License

[MIT](LICENSE). All benchmark cases are synthetic and freely reusable under the
same terms.
