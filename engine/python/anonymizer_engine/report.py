import csv
import hashlib
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, List

from .preset import Preset
from .findings import Finding, FINDINGS_CSV_HEADER


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"RUN_{ts}"


def make_run_folder(base: str, run_id: str) -> str:
    folder = os.path.join(base, run_id)
    os.makedirs(os.path.join(folder, "output"), exist_ok=True)
    os.makedirs(os.path.join(folder, "logs"), exist_ok=True)
    return folder


def write_json(path: str, obj: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def write_findings_csv(
    path: str,
    run_id: str,
    file_hash: str,
    findings: List[Finding],
) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FINDINGS_CSV_HEADER)
        for fd in findings:
            writer.writerow([
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


def preset_to_json(preset: Preset) -> Dict:
    return asdict(preset)


def build_model_inventory() -> Dict:
    return {
        "engine": {"name": "anonymizer-engine", "version": "0.1.0"},
        "spacy": {"used": True},
        "candle": None,
        "presidio": None,
    }


def build_run_report(
    run_id: str,
    preset: Preset,
    summary: Dict[str, int],
    file_count: int,
) -> Dict:
    return {
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "layer": preset.layer,
        "preset_id": preset.preset_id,
        "summary": summary,
        "file_count": file_count,
        "ocr_used": False,
    }
