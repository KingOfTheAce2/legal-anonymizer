"""
Layer 1 - Fast Legal Scrub

Detection: Regex patterns + spaCy NER
Speed: Fast and predictable
Use case: First-pass review, large batches
Languages: All 24 EU official languages + Russian, Chinese, Japanese, Korean.
           23 languages have native spaCy models; et/hu/ga/lv/mt/ar fall back to English.

Performance optimizations:
- Automatic chunking for documents >50KB
- Pattern validation caching
- Progress reporting for large documents
"""

import threading
from typing import Dict, List, Tuple, Any, Optional, Callable

from .preset import Preset
from .findings import Finding
from .pseudonym import PseudonymMapper
from .patterns import detect_with_validation
from .shared import PRIORITY, get_context, mask_value, log_detection_warning, log_detection_error
from .chunking import DocumentChunker

try:
    from .validators import EntityValidator
except ImportError:
    EntityValidator = None

# spaCy model cache — protected by a lock for thread-safe lazy loading
_SPACY_CACHE: Dict[str, Any] = {}
_SPACY_AVAILABLE: bool = True
_SPACY_LOCK: threading.Lock = threading.Lock()


def _load_spacy(language: str):
    """Load spaCy model for the given language (thread-safe)."""
    global _SPACY_AVAILABLE

    # Fast path: check availability and cache without acquiring lock
    if not _SPACY_AVAILABLE:
        return None
    if language in _SPACY_CACHE:
        return _SPACY_CACHE[language]

    with _SPACY_LOCK:
        # Re-check inside lock to avoid redundant loads (double-checked locking)
        if not _SPACY_AVAILABLE:
            return None
        if language in _SPACY_CACHE:
            return _SPACY_CACHE[language]

        try:
            import spacy

            model_map = {
                # EU official languages with native spaCy models
                "bg": "bg_core_news_sm",   # Bulgarian
                "hr": "hr_core_news_sm",   # Croatian
                "cs": "cs_core_news_sm",   # Czech
                "da": "da_core_news_sm",   # Danish
                "nl": "nl_core_news_sm",   # Dutch
                "en": "en_core_web_sm",    # English
                "fi": "fi_core_news_sm",   # Finnish
                "fr": "fr_core_news_sm",   # French
                "de": "de_core_news_sm",   # German
                "el": "el_core_news_sm",   # Greek
                "it": "it_core_news_sm",   # Italian
                "lt": "lt_core_news_sm",   # Lithuanian
                "pl": "pl_core_news_sm",   # Polish
                "pt": "pt_core_news_sm",   # Portuguese
                "ro": "ro_core_news_sm",   # Romanian
                "sk": "sk_core_news_sm",   # Slovak
                "sl": "sl_core_news_sm",   # Slovenian
                "es": "es_core_news_sm",   # Spanish
                "sv": "sv_core_news_sm",   # Swedish
                # Additional languages with native spaCy models
                "ru": "ru_core_news_sm",   # Russian
                "zh": "zh_core_web_sm",    # Chinese
                "ja": "ja_core_news_sm",   # Japanese
                "ko": "ko_core_news_sm",   # Korean
                # Languages without native spaCy models — fall back to English:
                # et (Estonian), hu (Hungarian), ga (Irish), lv (Latvian),
                # mt (Maltese), ar (Arabic)
            }

            model_name = model_map.get(language, "en_core_web_sm")

            try:
                nlp = spacy.load(model_name)
            except OSError:
                # Try English as fallback
                log_detection_warning(
                    "Layer 1",
                    f"Language model '{model_name}' not found, using English fallback. "
                    f"For better {language} detection, install: python -m spacy download {model_name}"
                )
                nlp = spacy.load("en_core_web_sm")

            _SPACY_CACHE[language] = nlp
            return nlp

        except ImportError as e:
            _SPACY_AVAILABLE = False
            log_detection_warning(
                "Layer 1",
                "spaCy library not installed. Name detection will use pattern matching only. "
                "For better accuracy, install spaCy: pip install spacy",
                e
            )
            return None
        except OSError as e:
            _SPACY_AVAILABLE = False
            log_detection_error(
                "Layer 1",
                "No spaCy language models found. Install one with: python -m spacy download en_core_web_sm",
                e
            )
            return None
        except Exception as e:
            log_detection_error(
                "Layer 1",
                f"Unexpected error loading spaCy model for language '{language}'",
                e
            )
            return None


def analyze_layer1_text_chunk(
    chunk_text: str,
    preset: Preset,
    language: str,
) -> Tuple[str, List[Finding], Dict[str, int]]:
    """
    Analyze a single chunk of text (internal use for chunked processing).

    Args:
        chunk_text: Chunk text to analyze
        preset: Anonymization preset configuration
        language: Language code

    Returns:
        Tuple of (redacted_text, findings, summary)
    """
    # This function contains the core analysis logic
    # (extracted from analyze_layer1_text for reusability)
    pseudonyms = PseudonymMapper(style=getattr(preset, "pseudonym_style", "neutral"))
    findings: List[Finding] = []
    summary: Dict[str, int] = {}

    candidates: List[Tuple[int, int, str, str, str, int]] = []

    # Pattern-based detection with entity validation
    pattern_matches = detect_with_validation(chunk_text)
    for match in pattern_matches:
        # Apply entity validation to adjust confidence.
        # EntityValidator may be None if the validators module failed to import.
        if EntityValidator is not None:
            if match.entity_type == "SSN":
                is_valid, adjusted_confidence = EntityValidator.validate_ssn(match.value)
            elif match.entity_type == "EMAIL":
                is_valid, adjusted_confidence = EntityValidator.validate_email(match.value)
            elif match.entity_type == "PHONE_NUMBER":
                is_valid, adjusted_confidence = EntityValidator.validate_phone(match.value, match.pattern_name)
            elif match.entity_type == "CREDIT_CARD":
                is_valid, adjusted_confidence = EntityValidator.validate_credit_card(match.value)
            elif match.entity_type == "IBAN":
                is_valid, adjusted_confidence = EntityValidator.validate_iban(match.value)
            else:
                is_valid, adjusted_confidence = True, match.confidence
        else:
            is_valid, adjusted_confidence = True, match.confidence

        # Skip invalid entities (e.g., test SSNs, fake email addresses)
        if not is_valid:
            continue

        candidates.append((
            match.start,
            match.end,
            match.entity_type,
            match.value,
            f"pattern:{match.pattern_name}",
            adjusted_confidence,
        ))

    # spaCy NER detection
    nlp = _load_spacy(language)
    if nlp is not None:
        try:
            # Sanitize: lone surrogates (from malformed PDF/DOCX bytes) cause
            # UnicodeEncodeError inside spaCy's Cython layer.  Replace them.
            _text_safe = chunk_text.encode("utf-8", errors="replace").decode("utf-8")
            doc = nlp(_text_safe)
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
        except MemoryError as e:
            log_detection_error(
                "Layer 1",
                "Document too large for spaCy processing. Consider splitting into smaller sections.",
                e
            )
        except Exception as e:
            log_detection_warning(
                "Layer 1",
                "spaCy name detection failed, continuing with pattern matching only",
                e
            )

    # Remove overlapping candidates
    candidates.sort(key=lambda x: (-x[5], x[0], -(x[1] - x[0])))

    used_ranges: List[Tuple[int, int]] = []
    filtered: List[Tuple[int, int, str, str, str, int]] = []

    for start, end, et, val, src, conf in candidates:
        overlaps = any(
            not (end <= us or start >= ue) for us, ue in used_ranges
        )
        if not overlaps:
            filtered.append((start, end, et, val, src, conf))
            used_ranges.append((start, end))

    filtered.sort(key=lambda x: x[0])

    # Build whitelist / blacklist lookup sets (case-insensitive)
    global_whitelist = {w.lower() for w in (preset.whitelist or [])}
    lang_whitelist = {w.lower() for w in preset.language_whitelists.get(language, [])}
    all_whitelist = global_whitelist | lang_whitelist

    global_blacklist = {w.lower() for w in (preset.blacklist or [])}
    lang_blacklist = {w.lower() for w in preset.language_blacklists.get(language, [])}
    all_blacklist = global_blacklist | lang_blacklist

    # Apply actions
    for start, end, et, val, src, confidence in filtered:
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
        elif action == "pseudonymise":
            replacement = pseudonyms.pseudonymise(et, val)
            pseudonym_value = replacement
        elif action == "mask":
            replacement = mask_value(val)

        findings.append(Finding(
            file_id="TEXT_0001",
            original_filename="",
            page_or_location=f"chars {start}-{end}",
            entity_type=et,
            entity_priority=priority,
            detected_text=val,
            context_snippet=get_context(chunk_text, start, end),
            detection_source=src,
            model_id="spacy" if src == "spacy" else "",
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
        ))

        summary[et] = summary.get(et, 0) + 1

    # Build output
    output = chunk_text
    for finding in reversed(findings):
        loc = finding.page_or_location
        parts = loc.replace("chars ", "").split("-")
        start, end = int(parts[0]), int(parts[1])

        if finding.redaction_action == "redact":
            replacement = f"[{finding.entity_type}]"
        elif finding.redaction_action == "mask":
            replacement = mask_value(output[start:end])
        elif finding.redaction_action == "pseudonymise":
            replacement = finding.pseudonym_value
        else:
            continue

        output = output[:start] + replacement + output[end:]

    return output, findings, summary


def analyze_layer1_text(
    text: str,
    preset: Preset,
    language: str,
    progress_callback: Optional[Callable[[int], None]] = None,
    enable_chunking: bool = True,
    chunk_size: int = 50 * 1024,  # 50KB default
) -> Tuple[str, List[Finding], Dict[str, int]]:
    """
    Layer 1 text analysis using patterns + spaCy.

    Combines:
    - Comprehensive regex pattern detection
    - spaCy NER for contextual entities (PERSON, ORG, LOCATION)

    Features:
    - Automatic chunking for documents >50KB
    - Progress reporting
    - Pattern validation caching

    Args:
        text: Input text to analyze
        preset: Anonymization preset configuration
        language: Language code (en, nl, de, etc.)
        progress_callback: Optional callback for progress (takes percent 0-100)
        enable_chunking: Enable automatic chunking for large documents
        chunk_size: Chunk size in bytes (default 50KB)

    Returns:
        Tuple of (redacted_text, findings, summary)
    """
    # Determine if chunking is needed
    should_chunk = enable_chunking and len(text) > chunk_size

    if not should_chunk:
        # Process as single chunk
        if progress_callback:
            progress_callback(0)
        output, findings, summary = analyze_layer1_text_chunk(text, preset, language)
        if progress_callback:
            progress_callback(100)
        return output, findings, summary

    # Process with chunking for large documents
    chunker = DocumentChunker(chunk_size=chunk_size)
    chunks = chunker.chunk_document(text, progress_callback)

    all_findings: List[Finding] = []
    summary: Dict[str, int] = {}
    chunk_outputs: List[str] = []

    for chunk in chunks:
        chunk_output, chunk_findings, chunk_summary = analyze_layer1_text_chunk(
            chunk.text, preset, language
        )

        chunk_outputs.append(chunk_output)
        all_findings.extend(chunk_findings)

        # Merge summary counts
        for entity_type, count in chunk_summary.items():
            summary[entity_type] = summary.get(entity_type, 0) + count

    # Reconstruct document from chunks (removing overlap)
    output = DocumentChunker.merge_chunks(chunks)

    # Update findings with correct offsets from chunks
    for finding in all_findings:
        # Find which chunk this finding belongs to
        for i, chunk in enumerate(chunks):
            if finding.start_pos >= chunk.start_offset and finding.end_pos <= chunk.end_offset:
                # Adjust offset if not first chunk
                if i > 0:
                    # Account for merged chunk offsets
                    finding.start_pos += (chunk.start_offset - i * (chunk.size - DocumentChunker.DEFAULT_OVERLAP))
                    finding.end_pos += (chunk.start_offset - i * (chunk.size - DocumentChunker.DEFAULT_OVERLAP))
                break

    if progress_callback:
        progress_callback(100)

    return output, all_findings, summary
