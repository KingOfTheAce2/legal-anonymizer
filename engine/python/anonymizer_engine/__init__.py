"""
Legal Anonymizer Engine

Offline-first legal anonymization for GDPR-compliant text and document processing.

Layers:
- Layer 1: Fast Legal Scrub (spaCy + patterns)
- Layer 2: Accurate Legal Review (transformers + patterns)
- Layer 3: Regulatory Standard (Presidio + patterns)
"""

__version__ = "0.1.0"

from .preset import Preset
from .findings import Finding, FINDINGS_CSV_HEADER
from .layer1 import analyze_layer1_text
from .layer2_candle import analyze_layer2_text
from .layer3_presidio import analyze_layer3_text
from .docx_scrubber import scrub_docx
from .pdf_scrubber import scrub_pdf
from .file_dispatcher import FileDispatcher, default_dispatcher
from .patterns import detect_patterns, detect_with_validation, PatternMatch

__all__ = [
    "Preset",
    "Finding",
    "FINDINGS_CSV_HEADER",
    "analyze_layer1_text",
    "analyze_layer2_text",
    "analyze_layer3_text",
    "scrub_docx",
    "scrub_pdf",
    "FileDispatcher",
    "default_dispatcher",
    "detect_patterns",
    "detect_with_validation",
    "PatternMatch",
]
