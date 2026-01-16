"""
Layer 1 - Fast Legal Scrub

Detection: Regex patterns + spaCy NER
Speed: Fast and predictable
Use case: First-pass review, large batches
Languages: English, Dutch, German (via spaCy models)
"""

import re
from typing import Dict, List, Tuple, Any

from .preset import Preset
from .findings import Finding
from .pseudonym import PseudonymMapper
from .patterns import detect_with_validation, PatternMatch

# Entity priority mapping
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
    "MONEY": 30,
    "URL": 20,
}

# spaCy model cache
_SPACY_CACHE: Dict[str, Any] = {}
_SPACY_AVAILABLE: bool = True


def _load_spacy(language: str):
    """Load spaCy model for the given language."""
    global _SPACY_AVAILABLE

    if not _SPACY_AVAILABLE:
        return None

    if language in _SPACY_CACHE:
        return _SPACY_CACHE[language]

    try:
        import spacy

        model_map = {
            "en": "en_core_web_sm",
            "nl": "nl_core_news_sm",
            "de": "de_core_news_sm",
            "es": "es_core_news_sm",
            "fr": "fr_core_news_sm",
            "it": "it_core_news_sm",
            "pt": "pt_core_news_sm",
        }

        model_name = model_map.get(language, "en_core_web_sm")

        try:
            nlp = spacy.load(model_name)
        except OSError:
            # Try English as fallback
            nlp = spacy.load("en_core_web_sm")

        _SPACY_CACHE[language] = nlp
        return nlp

    except ImportError:
        _SPACY_AVAILABLE = False
        return None
    except Exception:
        return None


def _context(text: str, start: int, end: int, span: int = 30) -> str:
    """Extract context snippet around a match."""
    a = max(0, start - span)
    b = min(len(text), end + span)
    return text[a:b]


def _mask(value: str) -> str:
    """Mask a value, showing only first and last 2 characters."""
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + ("*" * (len(value) - 4)) + value[-2:]


def analyze_layer1_text(
    text: str,
    preset: Preset,
    language: str,
) -> Tuple[str, List[Finding], Dict[str, int]]:
    """
    Layer 1 text analysis using patterns + spaCy.

    Combines:
    - Comprehensive regex pattern detection
    - spaCy NER for contextual entities (PERSON, ORG, LOCATION)

    Args:
        text: Input text to analyze
        preset: Anonymization preset configuration
        language: Language code (en, nl, de, etc.)

    Returns:
        Tuple of (redacted_text, findings, summary)
    """
    pseudonyms = PseudonymMapper()
    findings: List[Finding] = []
    summary: Dict[str, int] = {}

    # Collect all candidates: (start, end, entity_type, value, source, confidence)
    candidates: List[Tuple[int, int, str, str, str, int]] = []

    # 1. Pattern-based detection (comprehensive)
    pattern_matches = detect_with_validation(text)
    for match in pattern_matches:
        candidates.append((
            match.start,
            match.end,
            match.entity_type,
            match.value,
            f"pattern:{match.pattern_name}",
            match.confidence,
        ))

    # 2. spaCy NER detection
    nlp = _load_spacy(language)
    if nlp is not None:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                entity_type = None
                confidence = 85

                if ent.label_ == "PERSON":
                    entity_type = "PERSON"
                    confidence = 90
                elif ent.label_ == "ORG":
                    entity_type = "ORGANIZATION"
                    confidence = 85
                elif ent.label_ in ("GPE", "LOC"):
                    entity_type = "LOCATION"
                    confidence = 85
                elif ent.label_ == "DATE":
                    entity_type = "DATE"
                    confidence = 80
                elif ent.label_ == "MONEY":
                    entity_type = "MONEY"
                    confidence = 85

                if entity_type:
                    candidates.append((
                        ent.start_char,
                        ent.end_char,
                        entity_type,
                        ent.text,
                        "spacy",
                        confidence,
                    ))
        except Exception:
            # spaCy failed, continue with pattern-only results
            pass

    # 3. Remove overlapping candidates
    # Sort by confidence (descending), then by position, then by length (longer first)
    candidates.sort(key=lambda x: (-x[5], x[0], -(x[1] - x[0])))

    used_ranges: List[Tuple[int, int]] = []
    filtered: List[Tuple[int, int, str, str, str, int]] = []

    for start, end, et, val, src, conf in candidates:
        # Check for overlap with already selected ranges
        overlaps = any(
            not (end <= us or start >= ue) for us, ue in used_ranges
        )
        if not overlaps:
            filtered.append((start, end, et, val, src, conf))
            used_ranges.append((start, end))

    # Sort by position for processing
    filtered.sort(key=lambda x: x[0])

    # 4. Apply actions and build output
    for start, end, et, val, src, confidence in filtered:
        # Check if entity type is enabled
        if not preset.entities_enabled.get(et, True):
            continue

        priority = PRIORITY.get(et, 0)
        threshold = preset.minimum_confidence
        uncertain = confidence < threshold

        # Determine action based on priority
        if priority >= 90:
            action = "redact"
        elif priority >= 80:
            action = "pseudonymise"
        elif priority >= 70:
            action = "redact"
        elif priority >= 60:
            action = "pseudonymise"
        else:
            action = "none"

        # Handle uncertainty
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
        elif action == "pseudonymise":
            replacement = pseudonyms.pseudonymise(et, val)
            pseudonym_value = replacement
        elif action == "mask":
            replacement = _mask(val)

        findings.append(Finding(
            file_id="TEXT_0001",
            original_filename="",
            page_or_location=f"chars {start}-{end}",
            entity_type=et,
            entity_priority=priority,
            detected_text=val,
            context_snippet=_context(text, start, end),
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

    # 5. Build redacted output (apply replacements in reverse order)
    output = text
    for finding in reversed(findings):
        loc = finding.page_or_location
        parts = loc.replace("chars ", "").split("-")
        start, end = int(parts[0]), int(parts[1])

        if finding.redaction_action == "redact":
            replacement = "█" * (end - start)
        elif finding.redaction_action == "mask":
            replacement = _mask(output[start:end])
        elif finding.redaction_action == "pseudonymise":
            replacement = finding.pseudonym_value
        else:
            continue

        output = output[:start] + replacement + output[end:]

    return output, findings, summary
