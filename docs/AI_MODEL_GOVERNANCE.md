# AI Model Governance and AI Act Readiness

## Purpose

This document describes how AI models are managed within the Legal Anonymizer.

---

## Model Types

- Classical NLP models (spaCy)
- Transformer based models (Candle)
- Rule based recognizers (Presidio)

---

## Model Lifecycle

- Models are never auto updated
- Downloads are user initiated
- Model identifiers and hashes are recorded
- Past runs are never affected by model changes

---

## Transparency

For every run:
- Model name
- Model provider
- Model hash
- Detection source per finding

---

## Determinism

- No random seeds by default
- Deterministic pseudonym mapping
- Repeatable results with identical inputs

---

## AI Act Considerations

The tool is designed to support:
- Risk based use
- Human oversight
- Documentation and traceability
- Avoidance of opaque automated decisions

The tool does not make legal decisions.
It supports human decision making.

---

## Future Extensions

This document must be updated when:
- OCR is introduced
- Cloud based inference is added
- Automated decision making is enabled
