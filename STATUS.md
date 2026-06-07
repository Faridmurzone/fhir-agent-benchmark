# Project Status — FHIR Agent Benchmark

> Working status to resume later. Updated 2026-06-07. Not part of the published
> spec; a scratchpad of what's done and what's next.

## TL;DR

Pre-release (`v0.1`, no tag yet). The harness is fully runnable: 20 cases, a
multi-dimensional scorer with an **independent** FHIR validator (R4B **and R5**),
terminology verified against official sources, three vendor adapters (current
models), agentic regime, multi-sample / pass-rate metrics, and a transformation
axis (family TX: non-FHIR input → FHIR). 78 tests green. Public repo:
https://github.com/Faridmurzone/fhir-agent-benchmark (subtree split from the
private `prometheus` monorepo). **No official results published** until the spec
is frozen at `v0.1.0`.

## Key finding (the through-line)

The frontier models of 2026 (Opus 4.8, GPT-5.5, Gemini 3.5 Flash) are genuinely
strong on atomic FHIR tasks (read, navigate, temporal reasoning, generation,
US Core conformance) — even at moderate scale and with dirty data. Validated
cross-vendor, so it's not author bias. Every apparent "failure" we chased was an
artifact of the measuring instrument (data, validator, or scorer), documented in
`docs/METHODOLOGY_LESSONS.md`. The production gap is in **specification,
integration, scale, and the variance tail** — not atomic capability. Hence the
shift to measuring **pass-rate / worst-case**, not the mean.

## Done

- **Docs:** README, VISION, ROADMAP, CONCEPTUAL_DESIGN, TASK_TAXONOMY, SCORING,
  AGENTIC, DATA_INTEGRITY, METHODOLOGY_LESSONS, PUBLISHING.
- **Taxonomy:** 7 families, 41 capabilities (32 core), machine-readable
  `taxonomy/taxonomy.json`. Stable immutable IDs.
- **Scoring:** CC, FV, SF (multiplicative safety gate + hard cap), TRC, SR, AE.
  - FV structural validity delegated to **official HL7 models** (`fhir.resources`),
    R4B default y **R5 opcional** (`options.fhir_version`, para migración TX-05);
    heuristic fallback. Layer 7 = US Core conformance (conditional, opt-in).
  - CC entity/flag matching by code OR evidence OR label; generation CC by path
    assertions (`equals` / `equals_any` para coding un-guided); TRC by evidence recall.
  - `scoring/defaults.json` (weights, gate γ, penalties).
- **Cases (20):** seed 0001; hard 0010–0015 (status traps, dup therapy, recurrence,
  contradiction, implausible value, false-alarm allergy); FG 0020–0023 (Observation,
  Condition, MedicationRequest, US Core Condition); **TX 0030–0034** (LIS JSON→
  Observation un-guided, texto→Condition un-guided, export EHR→Bundle, US Core
  sin perfil dado, migración R4→R5); generated 0900.
- **Familia TX (Transformation & Mapping):** mide lo que FG no medía — input
  NO-FHIR (JSON propietario / texto plano) → FHIR correcto, donde el modelo
  decide resourceType, mapeo de campos, códigos de memoria (LOINC/SNOMED),
  vocabulario del vendor (F→final, M→male) y conformidad de IG sin guía.
  Rendering nuevo `source_json`.
- **Agentic regime (Phase 4):** `fhir_env.py` (read-only FHIR env + access log),
  `agentic.py` (tools list/search/read/finish, model-agnostic loop, AE scoring with
  safety gate), tasks `agt-0001..0004` (single + multi-hop: eGFR recency,
  MedicationRequest-vs-MedicationStatement, reasonReference→clinicalStatus).
- **Generators:** `patient_generator.py` (MR-01), `adversarial.py` (scale + dup
  therapy, gold by construction). Deterministic.
- **Runner:** load/validate/score/run/agentic/generate CLI. Multi-sample
  (`--samples N`) → pass_rate, worst_case, variance. Markdown + JSON reports
  (gitignored under `results/`).
- **Adapters (current models, gated by key):** `anthropic:claude-opus-4-8`,
  `openai:gpt-5.5` (uses `max_completion_tokens`), `gemini:gemini-3.5-flash`,
  plus `oracle`/`empty` baselines.
- **Independent verification:** `scripts/verify_terminology.py` (RxNav / LOINC /
  tx.fhir.org); corrected ~10 RxNorm + 1 SNOMED bad codes.
- **Tests:** 78 green. **Distribution:** subtree split → public repo, MIT, topics set.

## Experiments run (private, not committed — pre-v0.1.0)

- Cross-vendor n=3 (current models): Gemini 3.5 Flash 100 / Opus 4.8 99 / GPT-5.5 97.
  Author model (Opus) does not top → no self-authoring bias.
- Single-run variance is large (61–100 on some MR-01/PU-01) → multi-sampling needed.
- Safety case 0004 n=12: 0% failure for all three (robust where it matters most).
- Worst-case on 0900 is TRC noise (CC always 100), not clinical error.
- Ambiguous-prompt test: models answer *better* than a binary gold (separate active
  vs non-active with reasons) → naive substring scorer gave a FALSE failure.
- FHIRPath authoring: Opus/GPT 4/4, Gemini 3/4 — weak discriminator.
- Scale+dirty (193 resources, meds w/o codes): all three perfect.

## Pending / next steps

1. **Realistic ambiguous-prompt axis (chosen direction, not yet built).** Needs a
   *robust* open-ended scorer (NOT substring). Options: force a structured
   "active vs non-active" split and score that, or a verified/adversarial LLM-judge.
   The naive version fabricates failures (see METHODOLOGY_LESSONS §3) — do not ship
   it as-is.
2. **Multi-step compounding tasks** (agentic, 4–6 hops) where errors accumulate —
   most promising for genuine frontier discrimination. Infra exists (`agentic.py`).
3. **Tail characterization:** N=20–50 per case, report p5 / failure-rate by capability.
4. **Audit `generator/adversarial.py` full catalog** against RxNav (only reused
   codes verified so far; the rest is marked pending in the file).
5. ~~**US Core un-guided generation**~~ — **DONE** como TX-04 / caso 0033
   (US Core sin perfil dado, FV capa 7 activa).
6. **Validate against user's real stack** (model/prompt/context actually used in
   prod) — likely where the real errors live.
7. **Freeze + tag `v0.1.0`** once the spec is stable, then publish official results
   (only against the tag; results are gitignored until then).
8. **Correr los 3 vendors sobre la familia TX** (0030–0034, multi-sample): es el
   eje con más chances de discriminar frontier de verdad (la capacidad atómica
   está saturada; acá el modelo decide mapeos, códigos de memoria y conformidad
   de IG sin guía). Verificar los códigos nuevos (2345-7, 2951-2, 2823-3, 2160-0)
   con `scripts/verify_terminology.py` si el script levanta códigos de casos.
9. **Extender TX**: más vendors/formatos (CSV, HL7v2-ish), más tipos de recurso,
   migración R5→R4 (downgrade), otros IGs (IPS).

## How to resume (commands)

```bash
cd fhir-agent-benchmark
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# secrets live in .env (gitignored): ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY
set -a; . ./.env; set +a
.venv/bin/python -m benchmark_runner.cli validate-all          # 20/20
.venv/bin/python -m pytest -q                                  # 78 green
.venv/bin/python -m benchmark_runner.cli run --model anthropic:claude-opus-4-8 --samples 3
.venv/bin/python scripts/verify_terminology.py                 # 0 INVALID (needs network)
# publish update: git subtree split --prefix=fhir-agent-benchmark -b fhir-agent-benchmark-public
#                 git push public-benchmark fhir-agent-benchmark-public:main
```

## Open risk

API keys (Anthropic, OpenAI, Google) were shared in chat and live in `.env`.
**Rotate them.** `.env` is gitignored and was never committed (verified).
