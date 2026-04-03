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

import re
from typing import Dict, List, Tuple, Optional, Any

from .preset import Preset
from .findings import Finding
from .pseudonym import PseudonymMapper
from .patterns import detect_with_validation
from .shared import PRIORITY, get_context, mask_value, log_detection_warning, log_detection_error

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



# Pattern for ALL-CAPS multi-word sequences that look like person names in legal documents.
# Requires 3+ uppercase letters per word, 2–4 words total, stops at commas/punctuation.
_ALLCAPS_NAME_RE = re.compile(r'\b[A-Z]{3,}(?:\s+[A-Z]{2,}){1,3}\b')


def _find_allcaps_names(text: str) -> List[Tuple[int, int, str, str, int]]:
    """Find ALL-CAPS multi-word name sequences not normally caught by spaCy NER.

    Legal documents write party names in ALL-CAPS (e.g. RAYMOND SCOTT DELACROIX).
    SpaCy models are trained on mixed-case text and frequently miss these.
    Returns candidates as (start, end, entity_type, value, confidence) tuples.
    """
    candidates = []
    for m in _ALLCAPS_NAME_RE.finditer(text):
        candidates.append((m.start(), m.end(), "PERSON", m.group(), 70))
    return candidates


def _resolve_spacy_model(language: str) -> Optional[str]:
    """Return the best loadable spaCy model for the given language.

    Tries the large model first, falls back to the small model, then falls
    back to en_core_web_sm.  Returns None only if nothing at all is loadable.
    """
    import spacy
    small_fallbacks = {
        "bg": "bg_core_news_sm", "hr": "hr_core_news_sm", "cs": "cs_core_news_sm",
        "da": "da_core_news_sm", "nl": "nl_core_news_sm", "en": "en_core_web_sm",
        "fi": "fi_core_news_sm", "fr": "fr_core_news_sm", "de": "de_core_news_sm",
        "el": "el_core_news_sm", "it": "it_core_news_sm", "lt": "lt_core_news_sm",
        "pl": "pl_core_news_sm", "pt": "pt_core_news_sm", "ro": "ro_core_news_sm",
        "sk": "sk_core_news_sm", "sl": "sl_core_news_sm", "es": "es_core_news_sm",
        "sv": "sv_core_news_sm", "ru": "ru_core_news_sm", "zh": "zh_core_web_sm",
        "ja": "ja_core_news_sm", "ko": "ko_core_news_sm",
    }
    candidates = [
        _get_spacy_model(language),
        small_fallbacks.get(language, "en_core_web_sm"),
        "en_core_web_sm",
    ]
    for name in candidates:
        if not name:
            continue
        try:
            spacy.load(name)
            return name
        except OSError:
            continue
    return None


def _get_analyzer(language: str = "en"):
    """Get or create Presidio analyzer for the given language."""
    if language in _ANALYZER_CACHE:
        return _ANALYZER_CACHE[language]

    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        # Resolve best available spaCy model without relying on Presidio's download path.
        model_name = _resolve_spacy_model(language)
        if model_name is None:
            log_detection_error(
                "Layer 3",
                f"No loadable spaCy model for '{language}'",
                None,
            )
            return None

        # Patch spacy.cli.download to a no-op while Presidio initialises.
        # Presidio's SpacyNlpEngine._try_load_spacy_model() calls spacy.cli.download()
        # when spacy.load() raises OSError, which triggers a hanging pip subprocess
        # inside a frozen PyInstaller binary.  Since we already verified the model
        # above, a download attempt here means the model name was wrong — we want
        # an immediate OSError, not a blocked process.
        import spacy.cli as _spacy_cli  # noqa: PLC0415
        _orig_download = getattr(_spacy_cli, "download", None)
        def _no_download(*a, **kw):
            raise OSError("spaCy model download disabled in frozen/bundled build")
        try:
            if _orig_download is not None:
                _spacy_cli.download = _no_download

            nlp_config = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": language, "model_name": model_name}],
            }
            provider = NlpEngineProvider(nlp_configuration=nlp_config)
            nlp_engine = provider.create_engine()
            analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=[language])
        finally:
            if _orig_download is not None:
                _spacy_cli.download = _orig_download

        _ANALYZER_CACHE[language] = analyzer
        return analyzer

    except ImportError as e:
        log_detection_warning(
            "Layer 3",
            "Microsoft Presidio not installed. Layer 3 will use pattern matching only. "
            "For enterprise-grade detection, install: pip install presidio-analyzer presidio-anonymizer",
            e
        )
        return None
    except OSError as e:
        log_detection_error(
            "Layer 3",
            f"spaCy language model not found for '{language}'. "
            f"Install with: python -m spacy download {_get_spacy_model(language)}",
            e
        )
        return None
    except Exception as e:
        log_detection_error(
            "Layer 3",
            f"Error initializing Presidio analyzer for language '{language}'",
            e
        )
        return None


def _get_spacy_model(language: str) -> str:
    """Get the appropriate spaCy model for the language."""
    # Large models (preferred for Layer 3 accuracy)
    models = {
        "bg": "bg_core_news_lg",   "hr": "hr_core_news_sm",   # hr has no lg
        "cs": "cs_core_news_lg",   "da": "da_core_news_lg",
        "nl": "nl_core_news_lg",   "en": "en_core_web_lg",
        "fi": "fi_core_news_lg",   "fr": "fr_core_news_lg",
        "de": "de_core_news_lg",   "el": "el_core_news_lg",
        "it": "it_core_news_lg",   "lt": "lt_core_news_lg",
        "pl": "pl_core_news_lg",   "pt": "pt_core_news_lg",
        "ro": "ro_core_news_lg",   "sk": "sk_core_news_lg",
        "sl": "sl_core_news_lg",   "es": "es_core_news_lg",
        "sv": "sv_core_news_lg",   "ru": "ru_core_news_lg",
        "zh": "zh_core_web_lg",    "ja": "ja_core_news_lg",
        "ko": "ko_core_news_sm",   # ko has no lg
    }
    # Small model fallbacks (et/hu/ga/lv/mt/ar fall through to en_core_web_sm)
    fallback = {
        "bg": "bg_core_news_sm",   "hr": "hr_core_news_sm",
        "cs": "cs_core_news_sm",   "da": "da_core_news_sm",
        "nl": "nl_core_news_sm",   "en": "en_core_web_sm",
        "fi": "fi_core_news_sm",   "fr": "fr_core_news_sm",
        "de": "de_core_news_sm",   "el": "el_core_news_sm",
        "it": "it_core_news_sm",   "lt": "lt_core_news_sm",
        "pl": "pl_core_news_sm",   "pt": "pt_core_news_sm",
        "ro": "ro_core_news_sm",   "sk": "sk_core_news_sm",
        "sl": "sl_core_news_sm",   "es": "es_core_news_sm",
        "sv": "sv_core_news_sm",   "ru": "ru_core_news_sm",
        "zh": "zh_core_web_sm",    "ja": "ja_core_news_sm",
        "ko": "ko_core_news_sm",
    }
    return models.get(language, fallback.get(language, "en_core_web_sm"))


# Matches only multi-word ALL-CAPS sequences (at least 2 whitespace-separated words).
# Single-word abbreviations like SSN, DOB, LLC, INC are intentionally excluded so
# that Presidio can still see them as context labels (e.g. "SSN 078-05-1120").
_ALLCAPS_RE = re.compile(r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})+\b')


def _normalize_allcaps(text: str) -> str:
    """Convert all-caps name sequences to Title Case so spaCy NER recognises them.

    Only affects sequences of 3+ uppercase characters (words, commas, periods)
    so that acronyms like 'USA' or 'LLC' are left alone but full names like
    'RAYMOND SCOTT DELACROIX' become 'Raymond Scott Delacroix'.
    The replacement is the same byte-length, so Presidio span offsets are valid
    against both the normalised text and the original.
    """
    def _to_title(m: re.Match) -> str:
        # Title-case word by word, preserve length (title never changes length)
        return m.group(0).title()

    return _ALLCAPS_RE.sub(_to_title, text)


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
            # Normalize ALL-CAPS sequences to Title Case so spaCy NER catches names
            # like RAYMOND SCOTT DELACROIX. Title-casing never changes string length,
            # so Presidio's character offsets are valid against the original text.
            ner_text = _normalize_allcaps(text)

            results = analyzer.analyze(
                text=ner_text,
                language=language,
                return_decision_process=False,
            )

            for result in results:
                entity_type = PRESIDIO_ENTITY_MAP.get(result.entity_type)

                if entity_type is None:
                    continue

                start = result.start
                end = result.end
                value = text[start:end]  # use original text for the actual value
                confidence = int(result.score * 100)

                candidates.append((start, end, entity_type, value, confidence))
        except MemoryError as e:
            log_detection_error(
                "Layer 3",
                "Document too large for Presidio processing. Consider using Layer 1 for large documents.",
                e
            )
        except Exception as e:
            log_detection_warning(
                "Layer 3",
                "Presidio detection failed, falling back to pattern matching",
                e
            )

    # If Presidio not available or failed, use pattern fallback
    if not candidates:
        candidates = _pattern_fallback(text)

    # Supplement with ALL-CAPS multi-word name detection for legal document captions.
    # SpaCy NER (even large models) frequently misses ALL-CAPS person names because
    # the models are trained on mixed-case text. This pass runs directly on the
    # original text without depending on Presidio internals.
    candidates += _find_allcaps_names(text)

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
    pseudonyms = PseudonymMapper(style=getattr(preset, "pseudonym_style", "neutral"))
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

    # Build whitelist / blacklist lookup sets (case-insensitive)
    global_whitelist = {w.lower() for w in (preset.whitelist or [])}
    lang_whitelist = {w.lower() for w in preset.language_whitelists.get(language, [])}
    all_whitelist = global_whitelist | lang_whitelist

    global_blacklist = {w.lower() for w in (preset.blacklist or [])}
    lang_blacklist = {w.lower() for w in preset.language_blacklists.get(language, [])}
    all_blacklist = global_blacklist | lang_blacklist

    for start, end, et, val, confidence in filtered:
        val_lower = val.lower()

        # Whitelisted terms are false positives — skip entirely
        if val_lower in all_whitelist:
            continue

        # Blacklisted terms are always flagged at maximum confidence
        is_blacklisted = val_lower in all_blacklist
        if is_blacklisted:
            confidence = max(confidence, 95)

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
            replacement = f"[{et}]"
        elif action == "mask":
            replacement = mask_value(val)
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
                context_snippet=get_context(text, start, end),
                detection_source="presidio",
                model_id="presidio_analyzer",
                confidence_score=confidence,
                confidence_threshold=threshold,
                uncertainty_flag=uncertain,
                redaction_action=action,
                pseudonym_value=pseudonym_value,
                escalation_applied=False,
                whitelist_match=False,
                blacklist_match=is_blacklisted,
                language=language,
                start_pos=start,
                end_pos=end,
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
            replacement = f"[{finding.entity_type}]"
        elif finding.redaction_action == "mask":
            replacement = mask_value(out[start:end])
        elif finding.redaction_action == "pseudonymise":
            replacement = finding.pseudonym_value
        else:
            continue

        out = out[:start] + replacement + out[end:]

    return out, findings, summary
