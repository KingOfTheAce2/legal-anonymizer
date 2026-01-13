import re
from typing import Dict, List, Tuple

from .findings import Finding
from .preset import Preset

# ---------------------------
# Regex patterns (Layer 1)
# ---------------------------

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", re.IGNORECASE)
IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
)
CREDITCARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

# ---------------------------
# Entity priorities
# ---------------------------

PRIORITY: Dict[str, int] = {
    "EMAIL": 80,
    "PHONE_NUMBER": 80,
    "BANK_ACCOUNT": 90,
    "CREDIT_CARD": 90,
    "IP_ADDRESS": 70,
}

# ---------------------------
# Utility functions
# ---------------------------

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
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + ("*" * (len(value) - 4)) + value[-2:]


# ---------------------------
# Pseudonym mapping (per run)
# ---------------------------

class PseudonymMapper:
    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}
        self._mapping: Dict[str, str] = {}

    def pseudonymise(self, entity_type: str, original: str) -> str:
        key = f"{entity_type}:{original}"

        if key in self._mapping:
            return self._mapping[key]

        count = self._counters.get(entity_type, 0) + 1
        self._counters[entity_type] = count

        token = f"{entity_type}_{count:03d}"
        self._mapping[key] = token
        return token


# ---------------------------
# Layer 1 text analysis
# ---------------------------

def analyze_layer1_text(
    text: str,
    preset: Preset,
    language: str,
) -> Tuple[str, List[Finding], Dict[str, int]]:

    findings: List[Finding] = []
    summary: Dict[str, int] = {}
    pseudonym_mapper = PseudonymMapper()

    # Collect candidate detections
    candidates: List[Tuple[int, int, str, str]] = []

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

    # Sort candidates by start position and length
    candidates.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    # Resolve overlaps using priority
    kept: List[Tuple[int, int, str, str]] = []

    for cand in candidates:
        s, e, et, val = cand
        pr = PRIORITY.get(et, 0)

        replaced = False
        for i, k in enumerate(kept):
            ks, ke, ket, _ = k
            if not (e <= ks or s >= ke):
                kpr = PRIORITY.get(ket, 0)
                if pr > kpr or (pr == kpr and (e - s) > (ke - ks)):
                    kept[i] = cand
                replaced = True
                break

        if not replaced:
            kept.append(cand)

    redacted_chars = list(text)
    file_id = "TEXT_0001"
    original_filename = ""

    for s, e, et, val in kept:
        if not preset.entities_enabled.get(et, True):
            continue

        priority = PRIORITY.get(et, 0)
        confidence = 95
        threshold = preset.minimum_confidence
        uncertain = confidence < threshold

        # Determine action
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

        replacement = val
        pseudonym_value = ""

        if action == "redact":
            replacement = "█" * len(val)
        elif action == "mask":
            replacement = apply_mask(val)
        elif action == "pseudonymise":
            token = pseudonym_mapper.pseudonymise(et, val)
            replacement = token
            pseudonym_value = token

        redacted_chars[s:e] = list(replacement)

        findings.append(
            Finding(
                file_id=file_id,
                original_filename=original_filename,
                page_or_location=f"chars {s}-{e}",
                entity_type=et,
                entity_priority=priority,
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
        )

        summary[et] = summary.get(et, 0) + 1

    return "".join(redacted_chars), findings, summary
