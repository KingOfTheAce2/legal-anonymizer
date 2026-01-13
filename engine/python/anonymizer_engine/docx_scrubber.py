from typing import Dict, List, Tuple
from hashlib import sha256
from docx import Document

from .layer1 import analyze_layer1_text
from .preset import Preset
from .findings import Finding


def scrub_docx(
    input_path: str,
    output_path: str,
    preset: Preset,
    language: str,
    file_id: str,
) -> Tuple[List[Finding], Dict[str, int]]:
    """
    Scrub a DOCX file in place and write a redacted copy.
    Returns findings and summary.
    """

    doc = Document(input_path)
    all_findings: List[Finding] = []
    summary: Dict[str, int] = {}

    # Helper to process text blocks
    def process_text(text: str, location: str) -> str:
        redacted, findings, local_summary = analyze_layer1_text(
            text,
            preset,
            language,
        )

        for f in findings:
            f.file_id = file_id
            f.original_filename = input_path.split("/")[-1]
            f.page_or_location = location

        all_findings.extend(findings)

        for k, v in local_summary.items():
            summary[k] = summary.get(k, 0) + v

        return redacted

    # Paragraphs
    for idx, p in enumerate(doc.paragraphs):
        if not p.text.strip():
            continue
        redacted = process_text(
            p.text,
            f"paragraph {idx + 1}",
        )
        p.text = redacted

    # Tables
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                if not cell.text.strip():
                    continue
                redacted = process_text(
                    cell.text,
                    f"table {t_idx + 1}, row {r_idx + 1}, cell {c_idx + 1}",
                )
                cell.text = redacted

    doc.save(output_path)

    return all_findings, summary


def hash_file(path: str) -> str:
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
