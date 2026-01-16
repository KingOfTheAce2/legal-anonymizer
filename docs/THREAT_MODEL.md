# Threat Model and Risk Assumptions

## Purpose

This document describes the threat model assumed by the Legal Anonymizer.
It explicitly documents which risks are addressed and which are out of scope.

This document is part of the compliance and transparency posture of the product.

---

## In Scope Threats

The following threats are explicitly addressed by design:

- Accidental disclosure of personal data in documents
- Metadata leakage via filenames or file paths
- Silent weakening of anonymization rules
- Non reproducible anonymization results
- Unlogged AI model changes
- Overwriting original source documents
- Undocumented fallback behavior

---

## Out of Scope Threats

The following are explicitly out of scope:

- Malicious insiders with full system access
- Compromised operating systems
- Hardware keyloggers or memory inspection
- Deliberate re identification attacks using external datasets
- Adversarial inputs crafted to bypass anonymization

---

## Assumptions

- The user environment is trusted
- The filesystem permissions are correctly configured
- The user controls distribution of outputs
- The tool is used as a preprocessing step, not as a security boundary

---

## Design Consequences

Because of these assumptions:
- The tool focuses on correctness and auditability
- Outputs are not encrypted by default
- Original detected values appear in findings reports
- The tool prioritizes explainability over adversarial robustness

---

## Review

This threat model should be reviewed whenever:
- OCR is enabled
- Cloud connectivity is introduced
- Multi user collaboration is added
- The tool is used for public data release
