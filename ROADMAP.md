# Roadmap

## Phase 0 — Foundation

### Goal

Define benchmark scope and evaluation philosophy.

### Deliverables

- README
- Vision document
- Evaluation taxonomy
- Repository structure

**Status: In Progress**

---

## Phase 1 — MVP

### Goal

Create first benchmark release.

### Dataset

Synthetic clinical scenarios.

### Tasks

#### Patient Understanding

Examples:

- Extract allergies
- Identify active conditions
- Identify active medications

#### Timeline Reasoning

Examples:

- Reconstruct chronology
- Detect latest event
- Detect medication changes

#### FHIR Generation

Examples:

- Generate Observation
- Generate Condition
- Generate CarePlan

#### Consistency Detection

Examples:

- Broken references
- Contradictory data
- Missing required fields

### Deliverables

- 100 benchmark cases
- JSON task format
- Evaluation harness
- Baseline model results

---

## Phase 2 — Evaluation Engine

### Goal

Automated scoring.

### Features

- Exact match scoring
- Structured output validation
- FHIR schema validation
- LLM-as-judge experiments
- Human review workflows

### Deliverables

- Benchmark runner
- Scoring framework
- Metrics dashboard

---

## Phase 3 — Public Benchmark

### Goal

Enable community participation.

### Deliverables

- Hugging Face dataset
- Public leaderboard
- Submission workflow
- Documentation

---

## Phase 4 — Clinical Agents

### Goal

Move beyond single-turn evaluations.

### New Tasks

- Multi-step reasoning
- Tool use
- API interaction
- Care coordination
- Clinical workflow execution

### Deliverables

- Agent benchmark suite
- Agent leaderboard

---

## Phase 5 — Research Platform

### Goal

Become a standard benchmark for healthcare AI.

### Deliverables

- Community governance
- Research collaborations
- Benchmark versions
- Annual benchmark reports

---

## First Milestone

**FHIR Agent Benchmark v0.1**

Target:

- 100 synthetic cases
- 4 task families
- 3 evaluated models
- Public GitHub repository
- Public Hugging Face dataset

Success Criteria:

A third party can reproduce benchmark results from scratch.
