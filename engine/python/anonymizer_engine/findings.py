from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class Finding:
    file_id: str
    original_filename: str
    page_or_location: str
    entity_type: str
    entity_priority: int
    detected_text: str
    context_snippet: str
    detection_source: str
    model_id: str
    confidence_score: int
    confidence_threshold: int
    uncertainty_flag: bool
    redaction_action: str     # redact, pseudonymise, mask, none
    pseudonym_value: str
    escalation_applied: bool
    whitelist_match: bool
    blacklist_match: bool
    language: str
    notes: str = ""


FINDINGS_CSV_HEADER: List[str] = [
    "run_id",
    "file_id",
    "original_filename",
    "file_hash",
    "page_or_location",
    "entity_type",
    "entity_priority",
    "detected_text",
    "context_snippet",
    "detection_source",
    "model_id",
    "confidence_score",
    "confidence_threshold",
    "uncertainty_flag",
    "redaction_action",
    "pseudonym_value",
    "escalation_applied",
    "whitelist_match",
    "blacklist_match",
    "language",
    "notes",
]
