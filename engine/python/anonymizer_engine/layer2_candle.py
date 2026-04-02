"""
Layer 2 - Accurate Legal Review using transformer-based NER.

This layer uses HuggingFace transformers for higher accuracy NER detection.
Models are downloaded once and run locally (offline-first).

Supported models:
- dslim/bert-base-NER (default, multilingual-capable)
- Any compatible token-classification model

The model runs entirely locally after initial download.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any

from .preset import Preset
from .findings import Finding
from .pseudonym import PseudonymMapper
from .patterns import detect_with_validation, PatternMatch
from .shared import PRIORITY, get_context, mask_value, log_detection_warning, log_detection_error

# Model cache
_MODEL_CACHE: Dict[str, Any] = {}
_TOKENIZER_CACHE: Dict[str, Any] = {}


@dataclass(frozen=True)
class Layer2ModelConfig:
    model_id: str
    task: str = "ner"
    aggregation_strategy: str = "simple"


DEFAULT_MODEL = Layer2ModelConfig(
    model_id="dslim/bert-base-NER",
    task="ner",
    aggregation_strategy="simple"
)


def _load_model(model_path: str):
    """Load transformer model and tokenizer from local path or HuggingFace."""
    if model_path in _MODEL_CACHE:
        return _MODEL_CACHE[model_path], _TOKENIZER_CACHE[model_path]

    try:
        from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

        tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        model = AutoModelForTokenClassification.from_pretrained(model_path, local_files_only=True)

        ner_pipeline = pipeline(
            "ner",
            model=model,
            tokenizer=tokenizer,
            aggregation_strategy="simple"
        )

        _MODEL_CACHE[model_path] = ner_pipeline
        _TOKENIZER_CACHE[model_path] = tokenizer

        return ner_pipeline, tokenizer
    except ImportError as e:
        log_detection_warning(
            "Layer 2",
            "Transformers library not installed. Layer 2 will use pattern matching only. "
            "For AI-powered detection, install: pip install transformers torch",
            e
        )
        return None, None
    except OSError as e:
        log_detection_error(
            "Layer 2",
            f"Could not download model '{model_path}'. Check your internet connection or use offline mode.",
            e
        )
        return None, None
    except Exception as e:
        log_detection_error(
            "Layer 2",
            f"Error loading transformer model '{model_path}'",
            e
        )
        return None, None


def _map_ner_label(label: str) -> Optional[str]:
    """Map NER model labels to our entity taxonomy."""
    label = label.upper().replace("B-", "").replace("I-", "")

    mapping = {
        "PER": "PERSON",
        "PERSON": "PERSON",
        "ORG": "ORGANIZATION",
        "ORGANIZATION": "ORGANIZATION",
        "LOC": "LOCATION",
        "LOCATION": "LOCATION",
        "GPE": "LOCATION",
        "MISC": None,  # Too generic, skip
        "DATE": "DATE",
        "TIME": None,
        "MONEY": None,
        "PERCENT": None,
        "QUANTITY": None,
    }

    return mapping.get(label)


def _detect_patterns(text: str) -> List[Tuple[int, int, str, str, int]]:
    """Detect structured patterns using comprehensive patterns module."""
    pattern_matches = detect_with_validation(text)
    return [
        (m.start, m.end, m.entity_type, m.value, m.confidence)
        for m in pattern_matches
    ]


def analyze_layer2_text(
    text: str,
    preset: Preset,
    language: str,
    model_path: str = "",
) -> Tuple[str, List[Finding], Dict[str, int]]:
    """
    Layer 2 NER using transformer models.

    Combines:
    - Structured pattern detection (high confidence)
    - Transformer-based NER (contextual understanding)

    Returns:
        Tuple of (redacted_text, findings, summary)
    """
    if not model_path:
        model_path = DEFAULT_MODEL.model_id

    candidates: List[Tuple[int, int, str, str, int]] = []

    # Pattern detection first (high confidence)
    candidates.extend(_detect_patterns(text))

    # Transformer NER
    ner_pipeline, _ = _load_model(model_path)

    if ner_pipeline is not None:
        try:
            ner_results = ner_pipeline(text)

            for entity in ner_results:
                entity_type = _map_ner_label(entity.get("entity_group", entity.get("entity", "")))

                if entity_type is None:
                    continue

                start = entity["start"]
                end = entity["end"]
                value = entity.get("word", text[start:end])
                confidence = int(entity.get("score", 0.85) * 100)

                # Clean up tokenizer artifacts
                value = value.replace("##", "").strip()
                if not value:
                    continue

                candidates.append((start, end, entity_type, text[start:end], confidence))
        except MemoryError as e:
            log_detection_error(
                "Layer 2",
                "Document too large for transformer processing. Consider using Layer 1 for large documents.",
                e
            )
        except Exception as e:
            log_detection_warning(
                "Layer 2",
                "Transformer detection failed, continuing with pattern matching only",
                e
            )

    # Apply actions to candidates
    return apply_layer2_actions(
        text=text,
        candidates=candidates,
        preset=preset,
        language=language,
        file_id="TEXT_0001",
        original_filename="",
        model_id=model_path if ner_pipeline else "pattern_only",
    )


def apply_layer2_actions(
    text: str,
    candidates: List[Tuple[int, int, str, str, int]],
    preset: Preset,
    language: str,
    file_id: str,
    original_filename: str,
    model_id: str = "transformer",
) -> Tuple[str, List[Finding], Dict[str, int]]:
    """
    Apply redaction actions to detected entities.

    Layer 2 defaults:
    - Priority 90+: redact
    - Priority 80: pseudonymise
    - Priority 70: redact
    - Priority 60+: configurable
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

    # Sort by position for replacement
    filtered.sort(key=lambda x: x[0])

    # Build whitelist / blacklist lookup sets (case-insensitive)
    global_whitelist = {w.lower() for w in (preset.whitelist or [])}
    lang_whitelist = {w.lower() for w in preset.language_whitelists.get(language, [])}
    all_whitelist = global_whitelist | lang_whitelist

    global_blacklist = {w.lower() for w in (preset.blacklist or [])}
    lang_blacklist = {w.lower() for w in preset.language_blacklists.get(language, [])}
    all_blacklist = global_blacklist | lang_blacklist

    # Build output with replacements (reverse order to preserve positions)
    out = text
    offset = 0

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
                detection_source="transformer" if "bert" in model_id.lower() or "transformer" in model_id.lower() else "pattern",
                model_id=model_id,
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
    for finding in reversed(findings):
        loc = finding.page_or_location
        # Parse "chars X-Y"
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
