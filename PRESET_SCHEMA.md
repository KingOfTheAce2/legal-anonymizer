# Preset Schema Specification

## Purpose

A preset defines the exact anonymization policy used during a run.  
It is immutable once a run starts and is stored with the run record.

Presets exist to ensure:
- reproducibility
- explainability
- GDPR compliance
- consistent behavior across files and batches

Presets are policy, not implementation.

---

## Core Principles

- Every run uses exactly one preset
- Presets are copied into the run record
- Presets may be edited only before execution
- Users may only increase protection, never weaken defaults
- Presets apply equally to text input and file input

---

## Preset Structure Overview

A preset consists of the following sections:

1. Metadata
2. Layer selection
3. Entity configuration
4. Confidence policy
5. Redaction policy
6. Uncertainty handling
7. Language handling
8. OCR policy
9. Pseudonymisation policy
10. Logging and audit flags

---

## 1. Metadata

Descriptive information only.

Fields:
- preset_id
- name
- description
- version
- created_at
- author
- locked

Notes:
- `locked = true` means the preset cannot be modified
- versioning is mandatory

---

## 2. Layer Selection

Defines which anonymization layer is used.

Allowed values:
- 1 (Fast Legal Scrub)
- 2 (Accurate Legal Review)
- 3 (Regulatory and Market Standard)

Fields:
- layer
- allowed_detection_sources

Examples:
- Layer 1 allows pattern and spaCy
- Layer 2 allows pattern and Candle
- Layer 3 allows pattern and Presidio

---

## 3. Entity Configuration

Defines which legal entities are enabled.

Entities are legal concepts, not detection techniques.

Supported entities:
- NATIONAL_ID
- PASSPORT_NUMBER
- MEDICAL_ID
- BANK_ACCOUNT
- CREDIT_CARD
- PERSON
- DATE_OF_BIRTH
- EMAIL
- PHONE_NUMBER
- VEHICLE_ID
- ADDRESS
- IP_ADDRESS
- ORGANIZATION
- LOCATION
- ACCOUNT_USERNAME
- DATE

NUMBER is internal only and never user configurable.

For each entity:
- enabled (true or false)
- priority (numeric, immutable)
- minimum_redaction (redact, pseudonymise, mask)
- allowed_escalation (true or false)

Example logic:
- Priority 90 and 100 entities allow only redact
- Priority 80 entities default to pseudonymise
- Lower priority entities are configurable

---

## 4. Confidence Policy

Controls how certain the system must be before acting.

Fields:
- minimum_confidence (0 to 100):
- 0 means redact everything that looks even slightly like this
- 50 means redact if the system is reasonably sure
- 100 means redact only if the system is almost certain
- confidence_explanation (user facing text)

Rules:
- Applies uniformly across all enabled entities
- UI explains confidence as certainty, not probability
- Confidence values are logged per finding

---

## 5. Redaction Policy

Defines default redaction behavior by priority.

Rules:
- Priority 100 and 90: redact only
- Priority 80: pseudonymise by default
- Priority 70: redact by default
- Priority 60: pseudonymise or leave intact
- Priority 40: disabled unless enabled

Users may only escalate protection.

---

## 6. Uncertainty Handling

Defines what happens when confidence is below threshold.

Allowed values:
- mask
- redact
- leave_intact
- flag_only

Default:
- mask

Notes:
- Uncertain detections are always logged
- Findings report must mark uncertainty clearly

---

## 7. Language Handling

Controls language behavior.

Fields:
- language_mode (auto or fixed)
- language (if fixed)
- allow_user_override (true or false)

Rules:
- Auto detect by default
- User override always wins
- Language choice is logged

---

## 8. OCR Policy

Controls optical character recognition.

Fields:
- ocr_enabled (true or false)
- ocr_requires_confirmation (true or false)

Rules:
- OCR disabled by default
- OCR must be explicitly enabled
- OCR usage is logged and flagged

---

## 9. Pseudonymisation Policy

Defines how pseudonyms are generated.

Fields:
- style (neutral or realistic)
- deterministic (true or false)
- scope (per_file or per_run)

Defaults:
- neutral
- deterministic
- per_run

Notes:
- Deterministic mapping is required for legal review
- Style choice is part of the audit record

---

## 10. Logging and Audit Flags

Defines audit behavior.

Fields:
- generate_run_report
- generate_findings_report
- log_model_versions
- log_fallbacks
- log_uncertainty

Defaults:
- all enabled

These flags exist for transparency and audits.

---

## Preset Immutability Rules

- Once execution starts, the preset is frozen
- The exact preset is copied into the run folder
- Future edits do not affect past runs
- Preset version is included in all reports

---

## Relationship to GDPR

Presets implement:
- Article 5 principles through transparency and accountability
- Article 25 requirements through safe defaults and escalation only rules

Presets are the formal expression of data protection by design.

---

## Status

This schema is final.

Any implementation must conform to this specification.
