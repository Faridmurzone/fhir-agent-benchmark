# Contributing

Thanks for your interest in FHIR Agent Benchmark. The project is in early design
(`v0.1`); the highest-value contributions right now are **benchmark cases** and
**review of the taxonomy and scoring methodology**.

## Principles

- **Open** — definitions, data, tasks, and methodology are public.
- **Reproducible** — a third party must be able to re-run and get the same numbers.
- **Realistic** — cases reflect real healthcare workflows.
- **Safe** — scoring rewards safe behavior and penalizes unsafe outputs.
- **Synthetic only** — no PHI, no real patient data, ever.

## Adding a benchmark case

A case is a folder `cases/pf-fhir-agent-NNNN/` containing:

| File | Purpose |
|------|---------|
| `bundle.json` | FHIR R4 Bundle (the clinical data) |
| `narrative.md` · `timeline.md` · `table.md` | alternative renderings of the *same* data |
| `task.json` | capability id, instruction, output contract, renderings |
| `ground_truth.json` | gold answer + evidence + declared safety events |
| `scoring.json` | applicable dimensions + comparison options |

Rules:

1. Each case targets **exactly one capability** from
   [`docs/TASK_TAXONOMY.md`](docs/TASK_TAXONOMY.md). The `output_contract` and
   scoring `dimensions` must match that capability in `taxonomy/taxonomy.json`.
2. Every `evidence` reference must resolve to a resource present in `bundle.json`.
3. All four renderings must describe the **same** underlying facts (this is what
   the Serialization Robustness dimension measures).
4. Data is synthetic and clinically plausible. Use realistic codes (SNOMED,
   LOINC, RxNorm) where applicable.

Then validate before opening a PR:

```bash
python -m benchmark_runner.cli validate cases/pf-fhir-agent-NNNN
python -m benchmark_runner.cli validate-all
pytest -q
```

A PR is mergeable only if `validate-all` and `pytest` pass.

## Changing the taxonomy or scoring

- Capability **IDs are immutable** — append, never renumber or reuse.
- Any change to output contracts, applicable dimensions, scoring weights,
  penalties, or the safety gate requires a new version and a `CHANGELOG.md` entry.
- Open an issue to discuss taxonomy/scoring changes before a PR.

## Code style

- Python, standard library first; keep dependencies minimal (`jsonschema`, `pytest`).
- Deterministic, reproducible behavior is a hard requirement for the runner.
