from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from .preset import Preset
from .findings import Finding
from .pseudonym import PseudonymMapper

"""
Layer 2 implementation placeholder with a clean interface.

This file intentionally does not yet run a real Candle model.
Reason:
- Candle integration depends on your final model choice and file formats
- This skeleton lets you build the rest of the product correctly now

You can run it today via scripts/layer2_entrypoint.py
It will:
- accept text input
- produce run artifacts and findings
- behave deterministically
- mark results as coming from "candle_stub"

Then later we replace only this file with real Candle inference,
without touching UI, reports, or batch flow.
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


@dataclass(frozen=True)
class CandleModelConfig:
    model_id: str
    filename: str
    sha256: Optional[str] = None


def _context(text: str, start: int, end: int, span: int = 30) -> str:
    a = max(0, start - span)
    b = min(len(text), end + span)
    return text[a:b]


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + ("*" * (len(value) - 4)) + value[-2:]


def analyze_layer2_text(
    text: str,
    preset: Preset,
    language: str,
    model_path: str,
) -> Tuple[str, List[Finding], Dict[str, int]]:
    """
    Candle stub NER.

    Current behavior:
    - does NOT do real NER
    - returns the input unchanged
    - produces an empty findings list

    Replace this function later with real Candle inference that outputs:
    candidates = [(start, end, entity_type, value, confidence)]
    """
    _ = model_path
    redacted = text
    return redacted, [], {}


def apply_layer2_actions(
    text: str,
    candidates: List[Tuple[int, int, str, str, int]],
    preset: Preset,
    language: str,
    file_id: str,
    original_filename: str,
) -> Tuple[str, List[Finding], Dict[str, int]]:
    """
    Shared action application logic for Layer 2 and later file types.
    """
    pseudonyms = PseudonymMapper()
    findings: List[Finding] = []
    summary: Dict[str, int] = {}
    out = list(text)

    # sort by start, longer first
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
            action = "pseudonymise"
        elif priority >= 70:
            action = "redact"
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
                detection_source="candle_stub",
                model_id="candle_stub",
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
