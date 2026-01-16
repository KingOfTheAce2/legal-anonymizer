"""
PDF Scrubber - Anonymize PDF documents.

Uses PyMuPDF (fitz) for PDF handling:
- Extracts text from each page
- Applies anonymization to text
- Creates redacted PDF with text replaced

Limitations:
- Text-based redaction only (no image OCR by default)
- Some complex PDF layouts may not be perfectly preserved
- Scanned PDFs require OCR (disabled by default)
"""

from hashlib import sha256
from typing import Dict, List, Tuple

from .preset import Preset
from .layer1 import analyze_layer1_text
from .findings import Finding


def hash_file(path: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def scrub_pdf(
    input_path: str,
    output_path: str,
    preset: Preset,
    language: str,
    file_id: str,
) -> Tuple[List[Finding], Dict[str, int]]:
    """
    Scrub PII from a PDF document.

    Process:
    1. Open PDF with PyMuPDF
    2. Extract text from each page
    3. Detect and redact PII entities
    4. Apply redactions as PDF annotations
    5. Save redacted PDF

    Args:
        input_path: Path to input PDF
        output_path: Path for output PDF
        preset: Anonymization preset
        language: Language code
        file_id: Unique file identifier

    Returns:
        Tuple of (findings, summary)
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDF (fitz) is required for PDF support. "
            "Install with: pip install PyMuPDF"
        )

    all_findings: List[Finding] = []
    summary: Dict[str, int] = {}
    filename = input_path.replace("\\", "/").split("/")[-1]

    # Open the PDF
    doc = fitz.open(input_path)

    for page_num, page in enumerate(doc, start=1):
        # Extract text from page
        text = page.get_text()

        if not text.strip():
            continue

        # Analyze text
        redacted_text, findings, local_summary = analyze_layer1_text(text, preset, language)

        # Update findings with page info
        for f in findings:
            f.file_id = file_id
            f.original_filename = filename
            f.page_or_location = f"page {page_num}, {f.page_or_location}"
            all_findings.append(f)

        # Accumulate summary
        for k, v in local_summary.items():
            summary[k] = summary.get(k, 0) + v

        # Apply redactions to the PDF
        # Find text instances and add redaction annotations
        for finding in findings:
            if finding.redaction_action in ("redact", "pseudonymise", "mask"):
                original_text = finding.detected_text

                # Search for the text on the page
                text_instances = page.search_for(original_text)

                for inst in text_instances:
                    # Add redaction annotation
                    annot = page.add_redact_annot(inst)

                    # Set fill color to black for full redaction
                    if finding.redaction_action == "redact":
                        annot.set_colors(fill=(0, 0, 0))
                    else:
                        # For pseudonymise/mask, we'll add replacement text
                        annot.set_colors(fill=(0.9, 0.9, 0.9))

        # Apply all redactions on this page
        page.apply_redactions()

        # For pseudonymise/mask, we need to add replacement text
        # This is done after applying redactions
        for finding in findings:
            if finding.redaction_action == "pseudonymise" and finding.pseudonym_value:
                original_text = finding.detected_text
                replacement = finding.pseudonym_value

                # This is a simplified approach - in production you'd want
                # more sophisticated text positioning
                # For now, redaction boxes are left black

    # Save the redacted PDF
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    return all_findings, summary


def extract_text_from_pdf(path: str) -> str:
    """
    Extract all text from a PDF file.

    Useful for preview or text-only analysis.
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("PyMuPDF required for PDF support")

    doc = fitz.open(path)
    text_parts = []

    for page in doc:
        text_parts.append(page.get_text())

    doc.close()

    return "\n\n".join(text_parts)
