# Security Considerations

## Purpose

This document outlines security related design decisions and considerations for the Legal Anonymizer.

It documents what the system protects against, what it does not protect against, and why.

---

## Security Goals

The Legal Anonymizer is designed to:

- Prevent accidental disclosure of personal data
- Avoid silent weakening of anonymization behavior
- Ensure reproducibility and traceability
- Minimize metadata leakage
- Support secure, offline operation

It is not designed to be a security boundary.

---

## Offline First Operation

By default:
- No network connections are made
- No telemetry is collected
- No analytics are sent
- No model updates occur automatically

Any network access must be explicitly initiated by the user.

---

## File Handling

- Original input files are never overwritten
- Redacted outputs are written to a separate location
- File paths are not written to findings reports
- Only safe file identifiers are exposed in reports

---

## Findings Reports

Findings reports contain original detected values.

Security implications:
- Findings reports are sensitive
- Access must be restricted
- They should not be shared externally

This is documented explicitly to users.

---

## Model Security

- Models are treated as data, not code
- Model hashes are recorded
- Model provenance is documented
- No dynamic model execution from remote sources

---

## Memory and Disk Usage

- Large batch jobs use streaming processing
- No unnecessary caching of full documents
- Intermediate data is not persisted unless required

---

## Known Risks

The following risks are acknowledged:

- A compromised host system can access data
- Users may mis-handle findings reports
- OCR may introduce unintended data exposure
- Adversarial inputs are not mitigated

---

## Non-Goals

The system does not attempt to:

- Protect against malicious insiders
- Encrypt outputs automatically
- Prevent deliberate re-identification
- Act as a secure enclave

---

## Review and Updates

This document should be reviewed when:
- Cloud features are added
- Multi-user access is introduced
- OCR is enabled by default
- Regulatory requirements change
