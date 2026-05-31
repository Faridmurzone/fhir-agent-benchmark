# FHIR Agent Benchmark

A benchmark for evaluating AI agents on real-world healthcare interoperability and clinical reasoning tasks using FHIR resources.

## Why

Most existing LLM benchmarks focus on:

- General reasoning
- Coding
- Mathematics
- Question answering

Healthcare systems introduce a different class of challenges:

- Structured clinical data
- Longitudinal patient histories
- Temporal reasoning
- Medical safety constraints
- Interoperability standards

FHIR Agent Benchmark aims to evaluate how well AI agents can operate on healthcare data represented using the HL7 FHIR standard.

## Vision

We believe future healthcare AI systems will not simply answer questions.

They will:

- Navigate patient histories
- Interpret clinical records
- Generate structured resources
- Detect inconsistencies
- Coordinate workflows
- Interact with healthcare systems through APIs

Current benchmarks do not adequately measure these capabilities.

FHIR Agent Benchmark aims to fill that gap.

## Evaluation Domains

### Patient Understanding

Can an agent correctly understand a patient record?

Examples:

- Demographics
- Allergies
- Conditions
- Medications

### Longitudinal Reasoning

Can an agent reason across multiple encounters?

Examples:

- Disease progression
- Medication history
- Timeline reconstruction

### Clinical Safety

Can an agent avoid unsafe conclusions?

Examples:

- Allergy conflicts
- Medication contradictions
- Missing information

### FHIR Generation

Can an agent generate valid FHIR resources?

Examples:

- Observation
- Condition
- Encounter
- CarePlan

### Data Quality

Can an agent detect inconsistencies?

Examples:

- Missing references
- Invalid relationships
- Conflicting information

## Benchmark Structure

Each task contains:

- Clinical scenario
- FHIR resources
- Ground truth
- Evaluation criteria

## Initial Target Models

- GPT
- Claude
- Gemini
- DeepSeek
- Open-weight models

## Long-Term Goal

Become the reference benchmark for evaluating AI agents operating on healthcare data and FHIR ecosystems.

## Status

Early design phase.

Contributions and discussion are welcome.
