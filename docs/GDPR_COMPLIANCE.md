# GDPR Compliance Mapping

## Purpose

This document explains how the Legal Anonymizer supports compliance with the GDPR.
It does not constitute legal advice, but documents technical measures.

---

## Article 5 – Principles

### Lawfulness, Fairness, Transparency
- Findings reports explain every redaction
- Presets document decision logic
- Models and versions are logged

### Purpose Limitation
- The tool processes only user provided input
- No secondary use of data
- No telemetry or analytics by default

### Data Minimisation
- Entity priorities limit unnecessary processing
- File paths and metadata are excluded by default

### Accuracy
- Multiple detection layers
- Confidence thresholds
- Human review supported

### Integrity and Confidentiality
- Offline first operation
- No automatic external communication
- User controlled storage

### Accountability
- Reproducible runs
- Immutable run artifacts
- Explicit presets

---

## Article 25 – Data Protection by Design and by Default

- Strong defaults per entity priority
- Escalation only protection model
- OCR disabled by default
- Conservative handling of uncertainty

---

## Article 32 – Security of Processing

- Local processing
- Explicit user control over outputs
- Separation of source data and redacted outputs

---

## Pseudonymisation vs Anonymisation

- Redaction supports anonymisation
- Pseudonymisation reduces risk but remains personal data
- Masking is treated as a weaker protection

---

## Audit Support

Each run produces:
- Preset snapshot
- Model inventory
- Findings report
- Run report

These artifacts support audits and accountability.
