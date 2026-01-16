"""
Layer 3 - Regulatory and Market Standard using Microsoft Presidio.

This layer uses Microsoft Presidio for enterprise-grade PII detection.
Presidio is designed for regulatory compliance and offers:
- Extensive entity recognizers
- Multi-language support
- Configurable confidence thresholds

Layer 3 defaults are stricter than Layer 1 and 2:
- More entities default to redaction
- Higher priority given to conservative handling
"""

from typing import Dict, List, Tuple, Optional, Any

from .preset import Preset
from .findings import Finding
from .pseudonym import PseudonymMapper
from .patterns import detect_with_validation, PatternMatch

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

# Presidio entity to our taxonomy mapping
PRESIDIO_ENTITY_MAP: Dict[str, str] = {
    "PERSON": "PERSON",
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "PHONE_NUMBER",
    "IBAN_CODE": "BANK_ACCOUNT",
    "CREDIT_CARD": "CREDIT_CARD",
    "IP_ADDRESS": "IP_ADDRESS",
    "DATE_TIME": "DATE",
    "NRP": "NATIONAL_ID",  # National Registration Number
    "LOCATION": "LOCATION",
    "ORGANIZATION": "ORGANIZATION",
    "US_SSN": "NATIONAL_ID",
    "US_PASSPORT": "PASSPORT_NUMBER",
    "UK_NHS": "MEDICAL_ID",
    "US_DRIVER_LICENSE": "NATIONAL_ID",
    "US_BANK_NUMBER": "BANK_ACCOUNT",
    "SG_NRIC_FIN": "NATIONAL_ID",
    "AU_ABN": "ORGANIZATION",
    "AU_ACN": "ORGANIZATION",
    "AU_TFN": "NATIONAL_ID",
    "AU_MEDICARE": "MEDICAL_ID",
    "IN_PAN": "NATIONAL_ID",
    "IN_AADHAAR": "NATIONAL_ID",
    "IN_VEHICLE_REGISTRATION": "VEHICLE_ID",
    "MEDICAL_LICENSE": "MEDICAL_ID",
    "URL": None,  # Skip URLs
    "CRYPTO": None,  # Skip crypto addresses
}

# Analyzer and AnonymizerEngine cache
_ANALYZER_CACHE: Dict[str, Any] = {}


def _get_analyzer(language: str = "en"):
    """Get or create Presidio analyzer for the given language."""
    if language in _ANALYZER_CACHE:
        return _ANALYZER_CACHE[language]

    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        # Configure NLP engine based on language
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": language, "model_name": _get_spacy_model(language)}]
        }

        provider = NlpEngineProvider(nlp_configuration=nlp_config)
        nlp_engine = provider.create_engine()

        analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=[language])
        _ANALYZER_CACHE[language] = analyzer

        return analyzer
    except ImportError:
        return None
    except Exception:
        return None


def _get_spacy_model(language: str) -> str:
    """Get the appropriate spaCy model for the language."""
    models = {
        "en": "en_core_web_lg",
        "nl": "nl_core_news_lg",
        "de": "de_core_news_lg",
        "es": "es_core_news_lg",
        "fr": "fr_core_news_lg",
        "it": "it_core_news_lg",
        "pt": "pt_core_news_lg",
    }
    # Fallback to small models if large not available
    fallback = {
        "en": "en_core_web_sm",
        "nl": "nl_core_news_sm",
        "de": "de_core_news_sm",
        "es": "es_core_news_sm",
        "fr": "fr_core_news_sm",
        "it": "it_core_news_sm",
        "pt": "pt_core_news_sm",
    }
    return models.get(language, fallback.get(language, "en_core_web_sm"))


def _context(text: str, start: int, end: int, span: int = 30) -> str:
    a = max(0, start - span)
    b = min(len(text), end + span)
    return text[a:b]


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + ("*" * (len(value) - 4)) + value[-2:]


def analyze_layer3_text(
    text: str,
    preset: Preset,
    language: str,
) -> Tuple[str, List[Finding], Dict[str, int]]:
    """
    Layer 3 PII detection using Microsoft Presidio.

    Presidio provides enterprise-grade detection with:
    - Built-in recognizers for many entity types
    - Support for custom recognizers
    - Multi-language support

    Returns:
        Tuple of (redacted_text, findings, summary)
    """
    candidates: List[Tuple[int, int, str, str, int]] = []

    analyzer = _get_analyzer(language)

    if analyzer is not None:
        try:
            results = analyzer.analyze(
                text=text,
                language=language,
                return_decision_process=False,
            )

            for result in results:
                entity_type = PRESIDIO_ENTITY_MAP.get(result.entity_type)

                if entity_type is None:
                    continue

                start = result.start
                end = result.end
                value = text[start:end]
                confidence = int(result.score * 100)

                candidates.append((start, end, entity_type, value, confidence))
        except Exception:
            # Presidio failed, fall back to pattern detection
            pass

    # If Presidio not available or failed, use pattern fallback
    if not candidates:
        candidates = _pattern_fallback(text)

    return apply_layer3_actions(
        text=text,
        candidates=candidates,
        preset=preset,
        language=language,
        file_id="TEXT_0001",
        original_filename="",
    )


def _pattern_fallback(text: str) -> List[Tuple[int, int, str, str, int]]:
    """Fallback pattern detection using comprehensive patterns module."""
    pattern_matches = detect_with_validation(text)
    return [
        (m.start, m.end, m.entity_type, m.value, m.confidence)
        for m in pattern_matches
    ]


def apply_layer3_actions(
    text: str,
    candidates: List[Tuple[int, int, str, str, int]],
    preset: Preset,
    language: str,
    file_id: str,
    original_filename: str,
) -> Tuple[str, List[Finding], Dict[str, int]]:
    """
    Apply redaction actions to detected entities.

    Layer 3 defaults are STRICTER:
    - Priority 90+: redact (same as others)
    - Priority 80: redact (stricter than Layer 1/2 which pseudonymise)
    - Priority 70: redact
    - Priority 60: pseudonymise
    - Everything else: pseudonymise or flag
    """
    pseudonyms = PseudonymMapper()
    findings: List[Finding] = []
    summary: Dict[str, int] = {}

    # Remove overlapping candidates (prefer higher confidence, then longer match)
    candidates.sort(key=lambda x: (-x[4], x[0], -(x[1] - x[0])))

    used_ranges: List[Tuple[int, int]] = []
    filtered: List[Tuple[int, int, str, str, int]] = []

    for start, end, et, val, conf in candidates:
        overlaps = any(
            not (end <= us or start >= ue) for us, ue in used_ranges
        )
        if not overlaps:
            filtered.append((start, end, et, val, conf))
            used_ranges.append((start, end))

    filtered.sort(key=lambda x: x[0])

    for start, end, et, val, confidence in filtered:
        if not preset.entities_enabled.get(et, True):
            continue

        priority = PRIORITY.get(et, 0)
        threshold = preset.minimum_confidence
        uncertain = confidence < threshold

        # Layer 3 stricter defaults
        if priority >= 90:
            action = "redact"
        elif priority >= 80:
            action = "redact"  # STRICTER: Layer 1/2 would pseudonymise
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
        elif action == "mask":
            replacement = _mask(val)
        elif action == "pseudonymise":
            token = pseudonyms.pseudonymise(et, val)
            replacement = token
            pseudonym_value = token

        findings.append(
            Finding(
                file_id=file_id,
                original_filename=original_filename,
                page_or_location=f"chars {start}-{end}",
                entity_type=et,
                entity_priority=priority,
                detected_text=val,
                context_snippet=_context(text, start, end),
                detection_source="presidio",
                model_id="presidio_analyzer",
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

    # Apply replacements in reverse order
    out = text
    for finding in reversed(findings):
        loc = finding.page_or_location
        parts = loc.replace("chars ", "").split("-")
        start, end = int(parts[0]), int(parts[1])

        if finding.redaction_action == "redact":
            replacement = "█" * (end - start)
        elif finding.redaction_action == "mask":
            replacement = _mask(out[start:end])
        elif finding.redaction_action == "pseudonymise":
            replacement = finding.pseudonym_value
        else:
            continue

        out = out[:start] + replacement + out[end:]

    return out, findings, summary
