import re
from typing import Dict, List, Tuple
import spacy

from .preset import Preset
from .findings import Finding
from .pseudonym import PseudonymMapper

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", re.IGNORECASE)

PRIORITY: Dict[str, int] = {
    "BANK_ACCOUNT": 90,
    "EMAIL": 80,
    "PHONE_NUMBER": 80,
    "PERSON": 80,
    "ORGANIZATION": 60,
    "LOCATION": 60,
}

_SPACY_CACHE: Dict[str, object] = {}


def load_spacy(language: str):
    if language in _SPACY_CACHE:
        return _SPACY_CACHE[language]

    model = {
        "en": "en_core_web_sm",
        "nl": "nl_core_news_sm",
        "de": "de_core_news_sm",
    }.get(language, "en_core_web_sm")

    nlp = spacy.load(model)
    _SPACY_CACHE[language] = nlp
    return nlp


def analyze_layer1_text(
    text: str,
    preset: Preset,
    language: str,
) -> Tuple[str, List[Finding], Dict[str, int]]:

    nlp = load_spacy(language)
    pseudonyms = PseudonymMapper()
    findings: List[Finding] = []
    summary: Dict[str, int] = {}

    candidates: List[Tuple[int, int, str, str, str]] = []

    for m in EMAIL_RE.finditer(text):
        candidates.append((m.start(), m.end(), "EMAIL", m.group(), "pattern"))

    for m in PHONE_RE.finditer(text):
        candidates.append((m.start(), m.end(), "PHONE_NUMBER", m.group(), "pattern"))

    for m in IBAN_RE.finditer(text):
        candidates.append((m.start(), m.end(), "BANK_ACCOUNT", m.group(), "pattern"))

    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            candidates.append((ent.start_char, ent.end_char, "PERSON", ent.text, "spacy"))
        elif ent.label_ == "ORG":
            candidates.append((ent.start_char, ent.end_char, "ORGANIZATION", ent.text, "spacy"))
        elif ent.label_ in ("GPE", "LOC"):
            candidates.append((ent.start_char, ent.end_char, "LOCATION", ent.text, "spacy"))

    candidates.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    output = list(text)

    for start, end, et, val, src in candidates:
        if not preset.entities_enabled.get(et, True):
            continue

        priority = PRIORITY.get(et, 0)
        confidence = 95 if src == "pattern" else 90
        threshold = preset.minimum_confidence
        uncertain = confidence < threshold

        if priority >= 90:
            action = "redact"
        elif priority >= 80:
            action = "pseudonymise"
        else:
            action = "none"

        if uncertain and preset.uncertainty_policy == "mask":
            action = "mask"

        replacement = val
        pseudonym_value = ""

        if action == "redact":
            replacement = "█" * len(val)
        elif action == "pseudonymise":
            replacement = pseudonyms.pseudonymise(et, val)
            pseudonym_value = replacement
        elif action == "mask":
            replacement = val[:2] + "*" * (len(val) - 4) + val[-2:]

        output[start:end] = list(replacement)

        findings.append(Finding(
            file_id="TEXT_0001",
            original_filename="",
            page_or_location=f"chars {start}-{end}",
            entity_type=et,
            entity_priority=priority,
            detected_text=val,
            context_snippet=text[max(0, start-30):min(len(text), end+30)],
            detection_source=src,
            model_id="spacy" if src == "spacy" else "",
            confidence_score=confidence,
            confidence_threshold=threshold,
            uncertainty_flag=uncertain,
            redaction_action=action,
            pseudonym_value=pseudonym_value,
            escalation_applied=False,
            whitelist_match=False,
            blacklist_match=False,
            language=language,
        ))

        summary[et] = summary.get(et, 0) + 1

    return "".join(output), findings, summary
