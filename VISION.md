# Vision

## The Problem

Healthcare AI is entering a new era.

Large language models are becoming capable of interacting with structured healthcare information rather than simply generating text.

However, the industry lacks a common framework for answering questions such as:

- Which model performs best on clinical workflows?
- Which model understands FHIR data most accurately?
- Which agent is safest?
- Which architecture generalizes best?

Today, there is no equivalent of SWE-Bench, MMLU, or HumanEval for healthcare interoperability and FHIR-native agents.

## The Opportunity

FHIR has emerged as the dominant interoperability standard across healthcare ecosystems.

At the same time, agentic AI systems are rapidly becoming capable of:

- Reading records
- Querying APIs
- Generating structured outputs
- Executing workflows

The intersection between these trends creates a need for standardized evaluation.

## Our Hypothesis

Future healthcare AI systems will operate primarily through structured representations.

They will reason over:

- Patients
- Encounters
- Conditions
- Observations
- Care Plans
- Medication Requests

The ability to understand and manipulate these resources safely will become a critical capability.

## Strategic Goal

Build the open benchmark used by researchers, startups, hospitals, payers, and AI labs to evaluate healthcare AI systems.

## Principles

### Open

Benchmark definitions, datasets, tasks, and evaluation methodology should be openly accessible whenever possible.

### Reproducible

Results should be independently reproducible.

### Realistic

Tasks should reflect real-world healthcare workflows.

### Safe

Evaluation should explicitly reward safe behavior and penalize unsafe outputs.

### Vendor Neutral

The benchmark should evaluate capabilities, not vendors.

## Success Criteria

A successful benchmark would:

- Be used by the community
- Be cited by healthcare AI projects
- Be adopted by research teams
- Enable fair comparison across models
- Advance the state of healthcare AI evaluation

## North Star

Create the world's most trusted benchmark for FHIR-native AI agents.
