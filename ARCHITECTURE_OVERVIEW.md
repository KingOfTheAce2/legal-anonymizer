# Architecture Overview

## Purpose

This document provides a high level architectural overview of the Legal Anonymizer.
It explains how the system is structured, how components interact, and why certain design choices were made.

This document is intended for:
- technical reviewers
- auditors
- security teams
- future contributors

---

## High Level Architecture

The Legal Anonymizer is structured as a **layered, offline first system** with clear separation of concerns.

At a high level:

- User Interface (desktop application)
- Command and orchestration layer
- Anonymization engine
- Detection providers
- Reporting and audit artifacts

Each layer is replaceable without affecting others.

---

## Core Architectural Principles

- Offline by default
- Explicit user control
- Deterministic behavior
- Explainability over opacity
- No hidden side effects
- No automatic external communication

These principles apply across all components.

---

## Component Overview

### User Interface

Responsibilities:
- Collect input from the user
- Allow selection of presets and layers
- Trigger anonymization runs
- Display results and summaries

The UI does not perform anonymization logic.

---

### Orchestration Layer

Responsibilities:
- Receive user commands
- Select the appropriate anonymization layer
- Invoke the correct engine entrypoint
- Track progress and errors

This layer does not inspect or modify content.

---

### Anonymization Engine

Responsibilities:
- Execute anonymization logic
- Apply presets and policies
- Produce redacted outputs
- Generate audit artifacts

The engine is designed to run:
- on text input
- on individual files
- on large batches

---

### Detection Providers

Detection is separated from redaction.

Supported detection approaches:
- Structured pattern matching
- Classical NLP models
- Transformer based models
- Enterprise recognizers

Each provider produces normalized findings with:
- offsets
- entity types
- confidence scores
- source attribution

---

### Redaction and Policy Layer

Responsibilities:
- Apply entity priorities
- Resolve overlaps
- Enforce escalation only rules
- Handle uncertainty consistently

This layer ensures GDPR compliant behavior regardless of detection method.

---

### Reporting and Audit Layer

Responsibilities:
- Generate findings reports
- Record presets and model versions
- Create run summaries
- Preserve reproducibility

This layer is mandatory and cannot be disabled silently.

---

## Layered Anonymization Model

### Layer 1
- Fast
- Predictable
- Pattern detection plus classical NLP

### Layer 2
- Higher accuracy
- Transformer based NER
- User selected models

### Layer 3
- Conservative
- Market standard
- Enterprise recognizers

All layers share:
- the same preset schema
- the same reporting format
- the same audit requirements

---

## Data Flow Overview

1. User selects input and preset
2. Orchestration layer starts a run
3. Engine processes input
4. Detection providers emit findings
5. Policy layer applies actions
6. Outputs and reports are written
7. User reviews results

At no point is data transmitted externally unless explicitly configured.

---

## Extensibility

The architecture supports:
- adding new file types
- adding new detection models
- adding OCR as an optional module
- adding batch scaling

Extending the system does not require redesigning core concepts.

---

## Trust Boundaries

- User environment is trusted
- File system access is explicit
- Outputs are never overwritten
- Findings reports are treated as sensitive artifacts

---

## Summary

The Legal Anonymizer architecture prioritizes:
- correctness
- transparency
- auditability
- legal defensibility

These qualities are enforced structurally, not through convention.
