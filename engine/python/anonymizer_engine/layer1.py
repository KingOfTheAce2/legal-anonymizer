import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .findings import Finding
from .preset import Preset

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)

# Very permissive phone regex, we will refine later per country.
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")

# IBAN, basic structure check. We will add per-country checks later.
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", re.IGNORECASE)

IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")

CREDITCARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

PRIORITY = {
    "EMAIL": 80,
    "PHONE_NUMBER": 80,
    "BANK_ACCOUNT": 90,
    "IP_ADDRESS": 70,
    "CREDIT_CARD": 90,
}

ENTITY_MAP = {
    "EMAIL": "EMAIL",
    "PHONE_NUMBER": "PHONE_NUMBER",
    "BANK_ACCOUNT": "BANK_ACCOUNT",
    "IP_ADDRESS": "IP_ADDRESS",
    "CREDIT_CARD": "CREDIT_CARD",
}

def luhn_ok(num: str) -> bool:
    digits = [int(c) for c in num if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d2 = d * 2
            checksum += d2 - 9 if d2 > 9 else d2
        else:
            checksum += d
    return checksum % 10 == 0


def context(text: str, start: int, end: int, span: int = 30) -> str:
    a = max(0, start - span)
    b = min(len(text), end + span)
    return text[a:b]


def apply_mask(value: str) -> str:
    # Keep first 2 and last 2 characters if possible.
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + ("*" * (len(value) - 4)) + value[-2:]


def analyze_layer1_text(text: str, preset: Preset, language: str) -> Tuple[str, List[Finding], Dict[str, int]]:
    findings: List[Finding] = []
    summary: Dict[str, int] = {}

    # Collect candidate matches
    candidates: List[Tuple[int, int, str, str]] = []  # start, end, entity_type, detected_text

    for m in EMAIL_RE.finditer(text):
        candidates.append((m.start(), m.end(), "EMAIL", m.group(0)))

    for m in PHONE_RE.finditer(text):
        candidates.append((m.start(), m.end(), "PHONE_NUMBER", m.group(0)))

    for m in IBAN_RE.finditer(text):
        candidates.append((m.start(), m.end(), "BANK_ACCOUNT", m.group(0)))

    for m in IPV4_RE.finditer(text):
        candidates.append((m.start(), m.end(), "IP_ADDRESS", m.group(0)))

    for m in CREDITCARD_RE.finditer(text):
        raw = m.group(0)
        if luhn_ok(raw):
            candidates.append((m.start(), m.end(), "CREDIT_CARD", raw))

    # Sort by start then longer first
    candidates.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    # Simple overlap handling: keep higher priority, or longer if same priority
    kept: List[Tuple[int, int, str, str]] = []
    for c in candidates:
        s, e, et, val = c
        pr = PRIORITY.get(et, 0)

        overlap_idx = None
        for i, k in enumerate(kept):
            ks, ke, ket, kval = k
            if not (e <= ks or s >= ke):
                overlap_idx = i
                break

        if overlap_idx is None:
            kept.append(c)
            continue

        ks, ke, ket, kval = kept[overlap_idx]
        kpr = PRIORITY.get(ket, 0)

        if pr > kpr or (pr == kpr and (e - s) > (ke - ks)):
            kept[overlap_idx] = c

    # Apply actions
    redacted = list(text)
    file_id = "TEXT_0001"
    original_filename = ""

    for s, e, et, val in kept:
        if not preset.entities_enabled.get(et, True):
            continue

        pr = PRIORITY.get(et, 0)
        threshold = preset.minimum_confidence

        # For patterns we set a high confidence by default
        confidence = 95

        uncertain = confidence < threshold
        action = "none"
        pseudonym_value = ""

        if pr >= 90:
            action = "redact"
        elif pr >= 80:
            action = "pseudonymise"
        elif pr >= 70:
            action = "redact"
        else:
            action = "none"

        if uncertain:
            # Apply uncertainty policy
            up = preset.uncertainty_policy
            if up == "mask":
                action = "mask"
            elif up == "redact":
                action = "redact"
            elif up == "leave_intact":
                action = "none"
            elif up == "flag_only":
                action = "none"

        replacement = val
        if action == "redact":
            replacement = "█" * len(val)
        elif action == "mask":
            replacement = apply_mask(val)
        elif action == "pseudonymise":
            # Neutral tokens only for now.
            # Later we add consistent mapping and realistic placeholders.
            token = f"{et}_001"
            replacement = token
            pseudonym_value = token

        # Apply replacement to redacted list
        redacted[s:e] = list(replacement)

        fd = Finding(
            file_id=file_id,
            original_filename=original_filename,
            page_or_location=f"chars {s}-{e}",
            entity_type=et,
            entity_priority=pr,
            detected_text=val,
            context_snippet=context(text, s, e),
            detection_source="pattern",
            model_id="",
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
        findings.append(fd)
        summary[et] = summary.get(et, 0) + 1

    return "".join(redacted), findings, summary
