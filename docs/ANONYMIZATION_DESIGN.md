# Legal Anonymization Tool – Design and Policy Specification

## Purpose

This document defines the design, policy choices, and legal reasoning behind a desktop anonymization tool intended for lawyers and legal professionals.  
The goal is to support GDPR compliant anonymization with strong auditability, explainability, and reproducibility.

This document is normative. Implementation must follow it.

---

## Design Principles

- Offline first desktop application
- No automatic external API calls
- Explicit user controlled model downloads
- Protection by design and by default (GDPR Article 25)
- Transparency, accountability, and reproducibility (GDPR Article 5)
- Same behavior across text and files
- Scalable from single document to large batches

---

## Anonymization Layers

### Layer 1 – Fast Legal Scrub
- Goal: speed and predictability
- Detection:
  - Structured pattern detection
  - spaCy NER
- Offline only
- Intended for first pass review and large batches

### Layer 2 – Accurate Legal Review
- Goal: higher contextual accuracy
- Detection:
  - Structured pattern detection
  - Candle based LLM NER
- User selects model
- Offline after model download
- Intended for substantive legal work

### Layer 3 – Regulatory and Market Standard
- Goal: conservative and enterprise grade
- Detection:
  - Structured pattern detection
  - Microsoft Presidio
- Offline only
- Intended for disclosure and regulatory contexts

---

## Entity Taxonomy

Entities represent legal meaning, not detection techniques.

### Priority 100 – Always Redact
- NATIONAL_ID
- PASSPORT_NUMBER
- MEDICAL_ID

### Priority 90 – Always Redact
- BANK_ACCOUNT
- CREDIT_CARD

### Priority 80 – Default Pseudonymise
- PERSON
- DATE_OF_BIRTH
- EMAIL
- PHONE_NUMBER
- VEHICLE_ID

### Priority 70 – Default Redact
- ADDRESS
- IP_ADDRESS

### Priority 60 – Contextual
- ORGANIZATION
- LOCATION
- ACCOUNT_USERNAME

### Priority 40 – Optional
- DATE

### Priority 20 – Internal Only
- NUMBER

---

## Entity Priority Rules

- Higher priority always overrides lower priority
- Examples:
  - NATIONAL_ID overrides NUMBER
  - BANK_ACCOUNT overrides NUMBER
  - DATE_OF_BIRTH overrides DATE
  - ADDRESS overrides LOCATION
- Partial redaction is forbidden for priority 80 and above

---

## Detection Methods

### Structured Pattern Detection
Used only for identifiers with strict structure:
- Email addresses
- IBAN and bank accounts
- Credit cards with Luhn validation
- Phone numbers
- IP addresses
- National IDs with checksum rules

### spaCy
- Contextual NER
- Fast and predictable
- Used in Layer 1

### Candle
- Transformer based LLM inference
- Higher accuracy and robustness
- Used in Layer 2

### Microsoft Presidio
- Enterprise and market standard recognizers
- Used in Layer 3

Detection methods never perform redaction themselves.

---

## Redaction Methods

### Redact
- Completely removes original value
- Irreversible
- Closest to anonymisation

### Pseudonymise
- Replaces with consistent placeholder
- Preserves structure and meaning
- Deterministic per run

### Mask
- Partially hides value
- Keeps format visible
- Used for uncertainty handling

---

## Redaction Escalation Rules

- Users may only increase protection
- Allowed:
  - mask → pseudonymise → redact
- Forbidden:
  - redact → anything weaker
  - pseudonymise → mask

Priority 90 and 100 entities only allow redact.

---

## Default Redaction by Priority

- Priority 100 and 90: redact only
- Priority 80: pseudonymise by default
- Priority 70: redact by default
- Priority 60: pseudonymise or leave intact
- Priority 40: disabled unless enabled

---

## Uncertainty Handling

- Default behavior: mask
- Uncertain detections are flagged in reports
- Users may choose stricter handling per preset

---

## Language Handling

- Automatic language detection by default
- User may explicitly set language
- User choice overrides detection
- Language choice is logged

---

## OCR Policy

- OCR is disabled by default
- OCR must be explicitly enabled by user
- OCR usage is logged
- OCR considered experimental and optional

---

## Pseudonym Style

- Default: neutral tokens
  - PERSON_001
  - ORG_002
- Optional: realistic placeholders
  - John Doe
  - Jane Roe
- Style is part of the preset
- Mapping is deterministic per run

---

## Model Management

- No automatic model updates
- All downloads are user initiated
- Model ID, version, and hash are logged
- Updating models does not affect past runs

---

## Batch Processing

- Supports large batches including 10k files
- Streaming processing
- Constant memory usage
- Resumable jobs
- Per file progress tracking

---

## Anonymization Run Record

Each run produces an audit folder containing:
- input_manifest.json
- preset_used.json
- model_inventory.json
- run_report.json
- findings.csv
- redacted output files
- logs

This enables full reproducibility and auditability.

---

## GDPR Alignment

### Article 5
- Transparency through logging and reports
- Data minimisation via entity priorities
- Accuracy via layered detection
- Accountability through reproducible runs

### Article 25
- Protection by default via safe presets
- Protection by design via escalation rules
- Explicit user actions required to weaken nothing

---

## Scope

Supported inputs include:
- Contracts
- Client memos
- Wills
- Statutes
- Bylaws
- Medical files
- Identification documents
- Structured and unstructured files

---

## Status

All policy and design decisions in this document are final and must be treated as authoritative.
