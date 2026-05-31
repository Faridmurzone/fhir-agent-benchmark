# FHIR Agent Benchmark — Conceptual Design and Research Background

Part of **Prometheus Frontier**.

## Purpose

FHIR Agent Benchmark is an open benchmark for evaluating AI agents operating over healthcare data represented with HL7 FHIR resources.

The goal is not to create another generic medical QA benchmark.

The goal is to evaluate whether AI systems can safely and correctly operate in the type of structured, interoperable, API-driven environment used by real healthcare systems.

## Core Thesis

Future healthcare AI systems will not only answer clinical questions in natural language.

They will need to:

- Read structured patient records
- Navigate longitudinal clinical histories
- Generate valid FHIR resources
- Detect inconsistencies
- Trace conclusions back to source resources
- Interact with healthcare APIs
- Execute clinical and administrative workflows safely

Current benchmark families do not fully capture this combination of structured reasoning, interoperability, safety, traceability, and agentic execution.

## Relevant Background and Prior Work

### 1. MedAgentBench: A Realistic Virtual EHR Environment to Benchmark Medical LLM Agents

Link: https://arxiv.org/abs/2501.14654  
Code: https://github.com/stanfordmlgroup/MedAgentBench

MedAgentBench is one of the closest antecedents. It introduces a benchmark for medical LLM agents inside a virtual EHR environment. It includes 300 patient-specific tasks, 100 patient profiles, more than 700,000 data elements, and a FHIR-compliant interactive environment.

Relevance:

- Validates that agent-based evaluation in medical records is an important research direction.
- Shows that current frontier models still have substantial room for improvement.
- Establishes the importance of realistic EHR-style environments.

Difference from FHIR Agent Benchmark:

- FHIR Agent Benchmark should focus more narrowly and deeply on FHIR-native reasoning, resource validity, serialization robustness, traceability, and lightweight reproducibility.
- The first version should be simpler than MedAgentBench but more precise as a FHIR evaluation harness.

### 2. MedCase-Structured: A Text-to-FHIR Dataset for Benchmarking Diagnostic Reasoning in Clinically Realistic EHR Settings

Link: https://arxiv.org/abs/2605.30295

MedCase-Structured generates clinically realistic HL7 FHIR R4 bundles from unstructured clinical cases. It reports valid FHIR generation for 82.5% of cases and finds that models perform worse on structured FHIR inputs than on plain text.

Relevance:

- Strongly supports the need for deployment-aligned evaluation.
- Shows that structured FHIR input is harder for LLMs than unstructured text.
- Provides a useful precedent for synthetic FHIR bundle generation.

Difference from FHIR Agent Benchmark:

- MedCase-Structured focuses on diagnostic reasoning over FHIR-derived cases.
- FHIR Agent Benchmark should focus on broader agentic workflows: medication reconciliation, patient snapshot understanding, timeline reasoning, FHIR generation, data quality, and safety detection.

### 3. Serialisation Strategy Matters: How FHIR Data Format Affects LLM Medication Reconciliation

Link: https://arxiv.org/abs/2604.21076

This paper compares four FHIR serialization strategies for medication reconciliation:

- Raw JSON
- Markdown Table
- Clinical Narrative
- Chronological Timeline

It evaluates five open-weight models over 200 synthetic patients and finds that input serialization strategy has a major impact on model performance, especially for smaller models.

Relevance:

- Serialization format must be a first-class dimension in the benchmark.
- The same clinical scenario should be rendered in multiple formats.
- Robustness across formats is itself a meaningful metric.

Design implication:

FHIR Agent Benchmark should include a **Serialization Robustness Score** that measures how stable a model's answer is across different input representations of the same underlying case.

### 4. Large Language Models for Automating Clinical Data Standardization: HL7 FHIR Use Case

Link: https://arxiv.org/abs/2507.03067

This work uses GPT-4o and Llama 3.2 405B to convert structured clinical datasets into HL7 FHIR format, using MIMIC-IV as a source. It focuses on mapping tabular clinical data to FHIR resources.

Relevance:

- Supports the feasibility of LLM-assisted FHIR mapping.
- Provides ideas for evaluating field mapping, resource selection, and schema-aware prompting.
- Highlights typical failure modes such as hallucinated attributes and granularity mismatches.

Design implication:

FHIR Agent Benchmark should include tasks where the model must generate valid FHIR resources from clinical descriptions or structured non-FHIR inputs.

### 5. Enhancing Health Data Interoperability with Large Language Models: A FHIR Study

Link: https://arxiv.org/abs/2310.12989

This earlier study evaluates the use of LLMs to convert clinical text snippets into corresponding FHIR resources, reporting over 90% exact match accuracy against human annotations.

Relevance:

- Establishes text-to-FHIR conversion as a valid evaluation area.
- Provides historical context for LLMs in healthcare interoperability.
- Shows that resource generation can be evaluated with exact or structured matching.

Design implication:

FHIR generation tasks should be part of the benchmark, but not the entire benchmark.

### 6. MedHELM: Holistic Evaluation of Large Language Models for Medical Tasks

Link: https://arxiv.org/abs/2505.23802

MedHELM introduces a broad medical evaluation framework with a clinician-validated taxonomy, 35 benchmarks, and LLM-jury evaluation compared with clinician ratings.

Relevance:

- Useful methodological reference for medical evaluation design.
- Shows the value of taxonomies, task families, human validation, and cost-performance analysis.
- Supports combining automated scoring with human/clinical review.

Design implication:

FHIR Agent Benchmark should define an explicit taxonomy of task families and avoid relying on a single aggregate score.

### 7. MedEval: A Multi-Level, Multi-Task, and Multi-Domain Medical Benchmark for Language Model Evaluation

Link: https://arxiv.org/abs/2310.14088

MedEval is a broad medical benchmark covering multiple tasks, domains, annotations, and language model evaluation settings.

Relevance:

- Useful as a general benchmark design reference.
- Shows the importance of multi-task and multi-domain evaluation in healthcare.
- Less directly tied to FHIR or agentic workflows.

Design implication:

FHIR Agent Benchmark should remain focused enough to be differentiated: FHIR-native agents, not general medical language understanding.

## Strategic Positioning

Existing work evaluates:

- Medical QA
- Clinical reasoning
- Text-to-FHIR conversion
- FHIR serialization strategies
- Medical agents in virtual EHR environments

FHIR Agent Benchmark should position itself as:

> An open benchmark for evaluating FHIR-native AI agents across structured clinical reasoning, resource generation, safety detection, reference tracing, serialization robustness, and workflow execution.

## Benchmark Unit: `BenchmarkCase`

Each case should represent:

- A synthetic but clinically plausible scenario
- A set of FHIR resources
- One task instruction
- Ground truth
- Evaluation criteria
- Optional alternative renderings of the same case

Proposed structure:

```json
{
  "case_id": "pf-fhir-agent-0001",
  "version": "0.1",
  "language": "en",
  "scenario": "A patient with diabetes and hypertension has multiple encounters and medication changes.",
  "input_format": "fhir_json",
  "resources": [
    "Patient",
    "Condition",
    "MedicationRequest",
    "Observation",
    "Encounter",
    "AllergyIntolerance"
  ],
  "task": {
    "type": "medication_reconciliation",
    "instruction": "Identify the currently active medications and flag any safety concerns."
  },
  "expected_output": {
    "active_medications": [],
    "safety_flags": [],
    "explanation_required": true
  },
  "scoring": {
    "schema_validity": true,
    "clinical_correctness": true,
    "safety_penalty": true,
    "fhir_reference_integrity": true
  }
}
```

## Recommended Repository Structure

```text
fhir-agent-benchmark/
  README.md
  VISION.md
  ROADMAP.md
  docs/
    CONCEPTUAL_DESIGN.md
    BACKGROUND.md
    TASK_TAXONOMY.md
    SCORING.md
  cases/
    pf-fhir-agent-0001/
      bundle.json
      narrative.md
      timeline.md
      table.md
      task.json
      ground_truth.json
      scoring.json
  benchmark_runner/
    load_case.py
    render_prompt.py
    run_model.py
    validate_output.py
    score_case.py
    aggregate_results.py
```

## Task Families v0.1

The v0.1 benchmark should start with a small number of task families.

### 1. Patient Snapshot Understanding

The agent receives a FHIR Bundle and must extract the current clinical state.

Examples:

- Active conditions
- Active medications
- Known allergies
- Most recent relevant observations
- Last encounter
- Care plan status

Why it matters:

This is the base capability required before any agent can safely operate on a patient record.

### 2. Medication Reconciliation

The agent must identify active medications and detect medication-related safety concerns.

Examples:

- Current medication list
- Recently discontinued medications
- Duplicate therapies
- Allergy conflicts
- Contraindications
- Conflicting medication status

Why it matters:

Medication reconciliation is clinically important, high-risk, and well suited for structured evaluation.

### 3. FHIR Resource Generation

The agent receives a clinical scenario and must generate valid FHIR resources.

Examples:

- Observation
- Condition
- Encounter
- MedicationRequest
- AllergyIntolerance
- CarePlan

Why it matters:

AI systems in healthcare will need to produce structured, interoperable outputs, not just prose.

### 4. Longitudinal Timeline Reasoning

The agent must reason across multiple events over time.

Examples:

- Reconstruct clinical chronology
- Identify latest state
- Detect changes across encounters
- Distinguish active vs resolved conditions
- Track medication changes

Why it matters:

Healthcare records are temporal. Many model failures happen when systems flatten history.

### 5. Data Quality and Safety Detection

The agent must detect data inconsistencies or safety issues.

Examples:

- Broken references
- Missing required fields
- Conflicting dates
- Contradictory medication status
- Allergy ignored by medication order
- Implausible lab values

Why it matters:

Clinical AI systems must not only answer questions; they must detect when the underlying data is unsafe or incomplete.

## Core FHIR Resources v0.1

Keep v0.1 intentionally narrow:

- Patient
- Encounter
- Condition
- Observation
- MedicationRequest
- AllergyIntolerance
- CarePlan

Optional later resources:

- Procedure
- DiagnosticReport
- ServiceRequest
- Immunization
- Goal
- MedicationStatement
- Practitioner
- Organization
- Location

## Input Renderings

Each case should support multiple representations of the same underlying clinical data.

### Raw FHIR JSON

Direct representation of the FHIR Bundle.

### Clinical Narrative

Human-readable clinical summary generated from the resources.

### Chronological Timeline

Ordered list of clinical events.

### Markdown Table

Structured but compressed tabular representation.

## Evaluation Dimensions

### 1. FHIR Validity Score

Measures whether generated outputs are valid FHIR.

Checks:

- Valid JSON
- Valid `resourceType`
- Required fields
- CodeableConcept structure
- References
- Cardinality
- Profile validation where applicable

### 2. Clinical Correctness Score

Measures whether the answer matches the ground truth.

Examples:

- Correct active medication list
- Correct active problem list
- Correct latest lab values
- Correct identification of resolved vs active conditions

### 3. Safety Score

Penalizes clinically unsafe behavior.

Examples:

- Missing allergy conflict
- Inventing a medication
- Ignoring abnormal labs
- Confusing active and discontinued medications
- Making unsupported clinical recommendations

### 4. Traceability Score

Measures whether the agent can justify its answer using source resources.

Example:

```json
{
  "answer": "The patient is allergic to penicillin.",
  "evidence": ["AllergyIntolerance/allergy-001"]
}
```

### 5. Serialization Robustness Score

Measures whether performance remains stable across different renderings of the same case.

Example:

A model should ideally reach similar conclusions whether the input is:

- Raw FHIR JSON
- Timeline
- Clinical narrative
- Markdown table

### 6. Agentic Execution Score

For later phases, measures tool-use behavior.

Examples:

- Correct API call sequence
- Correct resource retrieval
- Minimal unnecessary calls
- Correct final answer
- Safe refusal when data is insufficient

## Scoring Strategy v0.1

Use hybrid scoring.

### Deterministic Scoring

Best for:

- JSON validity
- FHIR validation
- Exact field matching
- Reference integrity
- Resource count
- Required field checks

### Semantic Scoring

Best for:

- Clinical explanations
- Natural language answers
- Reasoning summaries
- Safety justification

### Human Review

Use for:

- Ambiguous cases
- Clinical correctness validation
- Safety-critical examples
- Calibration of LLM-as-judge

## MVP Target

FHIR Agent Benchmark v0.1 should include:

- 100 synthetic cases
- 5 task families
- 7 core FHIR resources
- 4 input renderings
- 3 baseline models
- A simple benchmark runner
- A reproducible results report
- A public Hugging Face dataset

## Baseline Models

Initial baseline candidates:

- GPT-4.1 or GPT-4o
- Claude Sonnet
- Gemini
- Llama open-weight model
- Qwen open-weight model
- Mistral open-weight model

The benchmark should not depend on one vendor.

## Suggested First Milestone

Create the first 10 cases manually or semi-manually.

Each case should include:

- `bundle.json`
- `narrative.md`
- `timeline.md`
- `table.md`
- `task.json`
- `ground_truth.json`
- `scoring.json`

The first cases should focus only on:

1. Patient Snapshot Understanding
2. Medication Reconciliation
3. Data Quality and Safety Detection

Do not start with all task families at once.

## Differentiation Statement

FHIR Agent Benchmark is not:

- A medical QA benchmark
- A diagnosis benchmark
- A text-to-FHIR-only benchmark
- A generic agent benchmark

FHIR Agent Benchmark is:

- FHIR-native
- Agent-oriented
- Safety-aware
- Traceability-focused
- Serialization-aware
- Designed for real healthcare interoperability workflows

## Open Research Questions

1. Which FHIR serialization strategy produces the most reliable agent behavior?
2. Can models reliably distinguish active, resolved, and historical clinical facts?
3. Can agents identify missing or contradictory clinical data?
4. Can LLMs generate valid FHIR resources without hallucinated fields?
5. Does traceability improve safety?
6. Do FHIR-native tasks reveal weaknesses hidden by plain-text medical benchmarks?
7. How do open-weight models compare with frontier models in structured healthcare workflows?
8. Can a lightweight benchmark approximate real EHR agent behavior without requiring a full virtual EHR environment?

## Initial Public Positioning

Suggested README sentence:

> FHIR Agent Benchmark is an open benchmark for evaluating AI agents on FHIR-native healthcare workflows, including structured clinical reasoning, medication reconciliation, resource generation, data quality detection, safety evaluation, and serialization robustness.

## Next Steps

1. Define exact JSON schemas for:
   - `task.json`
   - `ground_truth.json`
   - `scoring.json`

2. Create 10 seed cases.

3. Implement deterministic validators:
   - JSON validity
   - FHIR resourceType validation
   - Reference integrity
   - Required field checks

4. Run first baseline models.

5. Publish dataset preview on Hugging Face.

6. Write a technical post explaining:
   - why FHIR-native evaluation matters
   - what existing benchmarks miss
   - what FHIR Agent Benchmark adds

## Notes

This document is an initial conceptual design. It should evolve as the project receives feedback from the AI, healthcare, FHIR, and open-source communities.
