# Findings Report Specification

## Purpose

The findings report documents every detected and processed piece of potentially personal data during an anonymization run.

It exists to support:
- legal review
- explainability
- quality control
- audit and compliance
- reproducibility

The findings report is authoritative and immutable once generated.

---

## Relationship to Other Artifacts

The findings report is generated per anonymization run and must be interpreted together with:
- preset_used.json
- model_inventory.json
- run_report.json
- redacted output files

The findings report explains *why* redactions occurred.

---

## Format

The primary findings report format is **CSV**.

Reasons:
- universally readable
- importable into Excel and legal review tools
- stable over time
- auditable

An optional JSON version may exist for programmatic use, but CSV is normative.

---

## One Row per Finding

Each row represents **one detected entity instance**, regardless of whether it was ultimately redacted, masked, pseudonymised, or left intact.

Nothing is hidden.

---

## Required Columns

### 1. run_id
Unique identifier of the anonymization run.

---

### 2. file_path
Relative path of the file in which the entity was found.

For text input, a synthetic identifier is used.

---

### 3. file_hash
SHA-256 hash of the original file.

Ensures traceability.

---

### 4. page_or_location
Location within the file:
- page number for PDFs
- sheet and cell for spreadsheets
- paragraph index for documents
- character range for plain text

Human readable, not byte offsets.

---

### 5. entity_type
One of the supported legal entity types:
- PERSON
- ADDRESS
- BANK_ACCOUNT
- etc.

This reflects legal meaning, not detection method.

---

### 6. entity_priority
Numeric priority assigned to the entity.

Used to explain conflict resolution.

---

### 7. detected_text
The exact text as found in the input.

If redaction occurred, this field still shows the original value.

Access to this report must be controlled.

---

### 8. context_snippet
A short snippet of surrounding text for human interpretation.

Must not exceed a configurable length.

---

### 9. detection_source
How the entity was detected:
- pattern
- spacy
- candle
- presidio

Multiple sources may be listed if applicable.

---

### 10. model_id
Identifier of the model used, if applicable.

Empty for pure pattern detections.

---

### 11. confidence_score
Confidence expressed as a value from 0 to 100.

Explained in the UI as certainty.

---

### 12. confidence_threshold
The minimum confidence required by the preset.

Allows reviewers to understand why action was taken.

---

### 13. uncertainty_flag
Boolean value indicating whether the detection fell below threshold and uncertainty handling was applied.

---

### 14. redaction_action
One of:
- redact
- pseudonymise
- mask
- none

Reflects the final applied action.

---

### 15. pseudonym_value
If pseudonymisation was applied, the replacement value.

Empty otherwise.

---

### 16. escalation_applied
Indicates whether the user escalated protection beyond defaults.

Values:
- true
- false

---

### 17. whitelist_match
Indicates whether a whitelist rule influenced this finding.

Values:
- true
- false

---

### 18. blacklist_match
Indicates whether a blacklist rule influenced this finding.

Values:
- true
- false

---

### 19. language
Language context used for detection.

---

### 20. notes
Free text field reserved for:
- reviewer comments
- manual decisions
- downstream workflows

Initially empty.

---

## Mandatory Inclusion Rules

- All detections must appear, even if no redaction occurred
- Suppressed detections must still be logged
- Whitelisted and blacklisted cases must be visible
- Failed detections or fallbacks must be flagged

This supports transparency and accountability.

---

## Privacy and Access Considerations

The findings report contains original personal data.

Recommended safeguards:
- restricted access
- encryption at rest
- separate handling from redacted outputs

This should be documented for users.

---

## Example Row (Illustrative)

| run_id | file_path | entity_type | detected_text | detection_source | confidence_score | redaction_action |
|------|----------|-------------|---------------|------------------|------------------|------------------|
| R-123 | contract.docx | PERSON | John Smith | candle | 87 | pseudonymise |

This is illustrative only.

### File Identification and Privacy

File system paths may contain personal or sensitive data.

For this reason:
- Full file paths must never appear in the findings report
- Each file is assigned a generated file_id (for example FILE_0001)
- The original filename may be included optionally
- Any mapping between file_id and original path is stored separately and access restricted

This ensures data minimisation and prevents accidental disclosure of personal data through metadata.

---

## Relationship to GDPR

### Article 5
- Transparency through explicit logging
- Accuracy via confidence and source reporting
- Accountability through traceability

### Article 25
- Protection by design through mandatory reporting
- No silent or implicit processing

---

## Status

This findings report format is final and normative.

All implementations must conform to this specification.
