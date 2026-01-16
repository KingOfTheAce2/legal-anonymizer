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

        tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=False)
        model = AutoModelForTokenClassification.from_pretrained(model_path, local_files_only=False)

        ner_pipeline = pipeline(
            "ner",
            model=model,
            tokenizer=tokenizer,
            aggregation_strategy="simple"
        )

        _MODEL_CACHE[model_path] = ner_pipeline
        _TOKENIZER_CACHE[model_path] = tokenizer

        return ner_pipeline, tokenizer
    except ImportError:
        return None, None
    except Exception:
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


def _context(text: str, start: int, end: int, span: int = 30) -> str:
    a = max(0, start - span)
    b = min(len(text), end + span)
    return text[a:b]


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + ("*" * (len(value) - 4)) + value[-2:]


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
        except Exception:
            # Fallback: transformer failed, continue with patterns only
            pass

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

    # Sort by position for replacement
    filtered.sort(key=lambda x: x[0])

    # Build output with replacements (reverse order to preserve positions)
    out = text
    offset = 0

    for start, end, et, val, confidence in filtered:
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
                detection_source="transformer" if "bert" in model_id.lower() or "transformer" in model_id.lower() else "pattern",
                model_id=model_id,
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
    for finding in reversed(findings):
        loc = finding.page_or_location
        # Parse "chars X-Y"
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
