# FHIR Agent Benchmark

An open benchmark for evaluating AI agents on **FHIR-native healthcare
workflows** — structured clinical reasoning, medication reconciliation, resource
generation, data-quality detection, safety evaluation, and serialization
robustness.

> **Status:** early design phase (`v0.1`). The taxonomy, scoring methodology,
> JSON schemas, and a first runnable seed case are in place. Contributions and
> discussion are welcome.

Part of [**Prometheus Frontier**](https://github.com/) — building open,
reproducible, vendor-neutral evaluation for healthcare AI.

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

```bash
git clone <repo-url> && cd fhir-agent-benchmark
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Validate every benchmark case (schemas + FHIR reference integrity + taxonomy)
python -m benchmark_runner.cli validate-all

# Validate a single case
python -m benchmark_runner.cli validate cases/pf-fhir-agent-0001

# Run the test suite
pytest -q
```

A case validates only if its `task.json` / `ground_truth.json` / `scoring.json`
pass their JSON Schemas **and** every evidence reference resolves to a resource
in the FHIR bundle **and** the capability/contract/dimensions match the
taxonomy.

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
├── cases/
│   └── pf-fhir-agent-0001/              # seed case: bundle + 4 renderings + task/gt/scoring
└── benchmark_runner/                    # load + validate (scoring engine: next)
```

## Documents

- [`VISION.md`](VISION.md) — problem, opportunity, principles, north star.
- [`ROADMAP.md`](ROADMAP.md) — phases 0–5 and the v0.1 milestone.
- [`docs/CONCEPTUAL_DESIGN.md`](docs/CONCEPTUAL_DESIGN.md) — design and prior work.
- [`docs/TASK_TAXONOMY.md`](docs/TASK_TAXONOMY.md) — what the benchmark measures.
- [`docs/SCORING.md`](docs/SCORING.md) — how it is scored.

---

## First milestone — v0.1

- 100 synthetic cases · 5 task families · 7 core FHIR resources · 4 input renderings
- 3 baseline models · a reproducible results report · a public Hugging Face dataset
- **Success criterion:** a third party can reproduce the results from scratch.

All cases are **synthetic** — no PHI, no real patient data.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The fastest way to help right now is to
propose or review benchmark cases: each one is a folder under `cases/` that must
pass `validate-all`.

## Citation

If you use this benchmark, please cite it — see [`CITATION.cff`](CITATION.cff).

## License

[MIT](LICENSE). All benchmark cases are synthetic and freely reusable under the
same terms.
