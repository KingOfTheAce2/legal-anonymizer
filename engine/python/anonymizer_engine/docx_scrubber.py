from hashlib import sha256
from typing import Dict, List, Tuple
from docx import Document

from .preset import Preset
from .layer1 import analyze_layer1_text
from .findings import Finding


def hash_file(path: str) -> str:
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def scrub_docx(
    input_path: str,
    output_path: str,
    preset: Preset,
    language: str,
    file_id: str,
) -> Tuple[List[Finding], Dict[str, int]]:

    doc = Document(input_path)
    all_findings: List[Finding] = []
    summary: Dict[str, int] = {}
    filename = input_path.split("/")[-1]

    def process(text: str, location: str) -> str:
        redacted, findings, local = analyze_layer1_text(text, preset, language)
        for f in findings:
            f.file_id = file_id
            f.original_filename = filename
            f.page_or_location = location
        all_findings.extend(findings)
        for k, v in local.items():
            summary[k] = summary.get(k, 0) + v
        return redacted

    for i, p in enumerate(doc.paragraphs):
        if p.text.strip():
            p.text = process(p.text, f"paragraph {i+1}")

    for ti, table in enumerate(doc.tables):
        for ri, row in enumerate(table.rows):
            for ci, cell in enumerate(row.cells):
                if cell.text.strip():
                    cell.text = process(cell.text, f"table {ti+1}, row {ri+1}, cell {ci+1}")

    doc.save(output_path)
    return all_findings, summary
