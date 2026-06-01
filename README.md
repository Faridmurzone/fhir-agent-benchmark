# FHIR Agent Benchmark

An open benchmark for evaluating AI agents on **FHIR-native healthcare
workflows** — structured clinical reasoning, medication reconciliation, resource
generation, data-quality detection, safety evaluation, and serialization
robustness.

> **Status:** early design phase (`v0.1`). In place and runnable: the taxonomy,
> scoring methodology, JSON schemas, a multi-dimensional **scoring engine**, a
> deterministic **synthetic case generator**, **5 validated seed cases** across
> Patient Understanding, Medication Reconciliation, and Data Quality (including a
> safety-gate case), and a **baseline run harness** (oracle / empty baselines run
> without credentials; real model adapters gated by API key). Contributions and
> discussion are welcome.
>
> ⚠️ **Pre-release.** The spec (taxonomy, scoring, schemas, cases) may change
> until the first tagged release `v0.1.0`. No official results are published yet
> — see [Stability & versioning](#stability--versioning).

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
  results are published until the spec is frozen at a tagged release. Results are
  always tied to a specific tag — never to a moving `main`.

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
