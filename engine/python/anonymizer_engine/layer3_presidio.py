from typing import Dict, List, Tuple

from .preset import Preset
from .findings import Finding
from .pseudonym import PseudonymMapper

"""
Layer 3 Presidio placeholder.

This file defines the interface and output contract.
It is runnable today as a stub and produces correct artifacts.

Later, we will swap detection with the real Presidio AnalyzerEngine,
without changing UI, run artifacts, or CSV schema.
"""

PRIORITY: Dict[str, int] = {
    "NATIONAL_ID": 100,
    "PASSPORT_NUMBER": 100,
    "MEDICAL_ID": 100,
    "BANK_ACCOUNT": 90,
    "CREDIT_CARD": 90,
    "PERSON": 80,
    "DATE_OF_BIRTH": 80,
    "EMAIL": 80,
    "PHONE_NUMBER": 80,
    "VEHICLE_ID": 80,
    "ADDRESS": 70,
    "IP_ADDRESS": 70,
    "ORGANIZATION": 60,
    "LOCATION": 60,
    "ACCOUNT_USERNAME": 60,
    "DATE": 40,
}


def _context(text: str, start: int, end: int, span: int = 30) -> str:
    a = max(0, start - span)
    b = min(len(text), end + span)
    return text[a:b]


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + ("*" * (len(value) - 4)) + value[-2:]


def analyze_layer3_text_stub(text: str) -> List[Tuple[int, int, str, str, int]]:
    """
    Returns empty results in stub form.
    Replace later with Presidio detections.
    """
    _ = text
    return []


def apply_layer3_actions(
    text: str,
    candidates: List[Tuple[int, int, str, str, int]],
    preset: Preset,
    language: str,
    file_id: str,
    original_filename: str,
) -> Tuple[str, List[Finding], Dict[str, int]]:
    pseudonyms = PseudonymMapper()
    findings: List[Finding] = []
    summary: Dict[str, int] = {}
    out = list(text)

    candidates.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    for start, end, et, val, confidence in candidates:
        if not preset.entities_enabled.get(et, True):
            continue

        priority = PRIORITY.get(et, 0)
        threshold = preset.minimum_confidence
        uncertain = confidence < threshold

        if priority >= 90:
            action = "redact"
        elif priority >= 80:
            action = "redact"  # Layer 3 defaults are stricter
        elif priority >= 70:
            action = "redact"
        elif priority >= 60:
            action = "pseudonymise"
        else:
            action = "none"

        if uncertain:
            if preset.uncertainty_policy == "mask":
                action = "mask"
            elif preset.uncertainty_policy == "redact":
                action = "redact"
            elif preset.uncertainty_policy == "leave_intact":
                action = "none"
            elif preset.uncertainty_policy == "flag_only":
                action = "none"

        replacement = val
        pseudonym_value = ""

        if action == "redact":
            replacement = "█" * len(val)
        elif action == "mask":
            replacement = _mask(val)
        elif action == "pseudonymise":
            token = pseudonyms.pseudonymise(et, val)
            replacement = token
            pseudonym_value = token

        out[start:end] = list(replacement)

        findings.append(
            Finding(
                file_id=file_id,
                original_filename=original_filename,
                page_or_location=f"chars {start}-{end}",
                entity_type=et,
                entity_priority=priority,
                detected_text=val,
                context_snippet=_context(text, start, end),
                detection_source="presidio_stub",
                model_id="presidio_stub",
                confidence_score=confidence,
                confidence_threshold=threshold,
                uncertainty_flag=uncertain,
                redaction_action=action,
                pseudonym_value=pseudonym_value,
                escalation_applied=False,
                whitelist_match=False,
                blacklist_match=False,
                language=language,
            )
        )

        summary[et] = summary.get(et, 0) + 1

    return "".join(out), findings, summary
