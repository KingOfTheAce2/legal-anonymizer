import os
import json
from dataclasses import asdict
from typing import Dict, List, Tuple, Optional

from .preset import Preset
from .findings import Finding
from .report import (
    make_run_folder,
    new_run_id,
    write_json,
    write_findings_csv,
    build_model_inventory,
    build_run_report,
    sha256_file,
)
from .docx_scrubber import scrub_docx


SUPPORTED_EXTENSIONS = {
    ".docx": "docx",
}


def _safe_basename(path: str) -> str:
    # Only filename, never directories, to avoid leaking PII from paths
    return path.replace("\\", "/").split("/")[-1]


def _iter_files(root: str, recursive: bool) -> List[str]:
    files: List[str] = []
    if recursive:
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                files.append(os.path.join(dirpath, fn))
    else:
        for fn in os.listdir(root):
            p = os.path.join(root, fn)
            if os.path.isfile(p):
                files.append(p)
    return files


def _next_file_id(n: int) -> str:
    return f"FILE_{n:05d}"


def run_batch_folder(
    input_folder: str,
    output_base_folder: str,
    preset: Preset,
    language: str,
    recursive: bool = True,
    max_files: Optional[int] = None,
) -> Dict:
    """
    Batch scrub all supported files in a folder.

    - Writes a run folder containing artifacts and redacted outputs.
    - Does NOT write any full file paths into findings.csv.
    - Uses FILE_00001 style ids.
    - Currently supports DOCX only. Other file types will be recorded as skipped.
    """

    if not os.path.isdir(input_folder):
        raise NotADirectoryError(input_folder)

    run_id = new_run_id()
    run_folder = make_run_folder(output_base_folder, run_id)
    output_folder = os.path.join(run_folder, "output")
    os.makedirs(output_folder, exist_ok=True)

    all_files = _iter_files(input_folder, recursive=recursive)
    all_files.sort()

    if max_files is not None:
        all_files = all_files[: max(0, int(max_files))]

    findings_all: List[Finding] = []
    summary: Dict[str, int] = {}
    processed = 0
    skipped: List[Dict] = []

    # Process each file
    for idx, in_path in enumerate(all_files, start=1):
        ext = os.path.splitext(in_path)[1].lower()
        kind = SUPPORTED_EXTENSIONS.get(ext)

        if not kind:
            skipped.append(
                {
                    "file_id": _next_file_id(idx),
                    "original_filename": _safe_basename(in_path),
                    "reason": f"unsupported_extension:{ext}",
                }
            )
            continue

        file_id = _next_file_id(idx)
        original_filename = _safe_basename(in_path)

        out_name = original_filename
        if out_name.lower().endswith(".docx"):
            out_name = out_name[:-5] + "_redacted.docx"
        else:
            out_name = out_name + "_redacted"

        out_path = os.path.join(output_folder, out_name)

        if kind == "docx":
            file_findings, file_summary = scrub_docx(
                input_path=in_path,
                output_path=out_path,
                preset=preset,
                language=language,
                file_id=file_id,
            )

            # Ensure no path leakage
            for f in file_findings:
                f.file_id = file_id
                f.original_filename = original_filename

            findings_all.extend(file_findings)

            for k, v in file_summary.items():
                summary[k] = summary.get(k, 0) + int(v)

            processed += 1

    # Artifacts
    write_json(os.path.join(run_folder, "preset_used.json"), asdict(preset))
    write_json(os.path.join(run_folder, "model_inventory.json"), build_model_inventory())

    run_report = build_run_report(run_id, preset, summary, file_count=processed)
    run_report["batch"] = {
        "input_folder_basename": _safe_basename(input_folder),
        "recursive": bool(recursive),
        "total_files_seen": len(all_files),
        "processed_files": processed,
        "skipped_files": len(skipped),
        "skipped": skipped,
        "language": language,
    }
    write_json(os.path.join(run_folder, "run_report.json"), run_report)

    # Findings CSV per-file hashing is required by your spec.
    # We do not include paths, so we write one findings.csv for the run with file_hash empty,
    # and also per-file findings hashes in a side json for audit completeness.
    # This avoids leaking file paths while preserving traceability.
    per_file_hashes: Dict[str, str] = {}
    for idx, in_path in enumerate(all_files, start=1):
        ext = os.path.splitext(in_path)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            per_file_hashes[_next_file_id(idx)] = sha256_file(in_path)

    write_json(os.path.join(run_folder, "input_manifest.json"), {
        "input_folder_basename": _safe_basename(input_folder),
        "recursive": bool(recursive),
        "files_seen": len(all_files),
        "file_hashes": per_file_hashes,
    })

    # For findings.csv we must still fill file_hash column.
    # We populate it by looking up the file_id hash.
    # This keeps the CSV format stable and audit-friendly.
    # We write the CSV ourselves with correct file_hash per row.
    findings_csv_path = os.path.join(run_folder, "findings.csv")
    _write_findings_csv_with_lookup(findings_csv_path, run_id, findings_all, per_file_hashes)

    return {
        "run_id": run_id,
        "run_folder": run_folder,
        "processed_files": processed,
        "skipped_files": len(skipped),
        "total_files_seen": len(all_files),
        "summary": summary,
        "output_folder": output_folder,
    }


def _write_findings_csv_with_lookup(
    path: str,
    run_id: str,
    findings: List[Finding],
    file_hash_lookup: Dict[str, str],
) -> None:
    # Import header from findings module to avoid duplication
    from .findings import FINDINGS_CSV_HEADER
    import csv

    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(FINDINGS_CSV_HEADER)
        for fd in findings:
            file_hash = file_hash_lookup.get(fd.file_id, "")
            w.writerow([
                run_id,
                fd.file_id,
                fd.original_filename,
                file_hash,
                fd.page_or_location,
                fd.entity_type,
                fd.entity_priority,
                fd.detected_text,
                fd.context_snippet,
                fd.detection_source,
                fd.model_id,
                fd.confidence_score,
                fd.confidence_threshold,
                str(fd.uncertainty_flag).lower(),
                fd.redaction_action,
                fd.pseudonym_value,
                str(fd.escalation_applied).lower(),
                str(fd.whitelist_match).lower(),
                str(fd.blacklist_match).lower(),
                fd.language,
                fd.notes,
            ])
