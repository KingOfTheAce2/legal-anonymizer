#!/usr/bin/env python3
"""
Sidecar Entrypoint - Main interface between Tauri desktop app and Python engine.

Commands:
- analyze_text: Analyze text with specified layer
- analyze_file: Analyze a single file (DOCX, PDF, TXT)
- analyze_batch: Analyze a folder of files
- get_supported_extensions: List supported file types

Input: JSON via stdin
Output: JSON via stdout
"""

import json
import os
import sys
from dataclasses import asdict
from typing import Any, Dict

from langdetect import detect, DetectorFactory

from anonymizer_engine.preset import Preset
from anonymizer_engine.layer1 import analyze_layer1_text
from anonymizer_engine.layer2_candle import analyze_layer2_text
from anonymizer_engine.layer3_presidio import analyze_layer3_text
from anonymizer_engine.docx_scrubber import scrub_docx, hash_file
from anonymizer_engine.pdf_scrubber import scrub_pdf
from anonymizer_engine.file_dispatcher import default_dispatcher, safe_basename
from anonymizer_engine.report import (
    build_model_inventory,
    build_run_report,
    make_run_folder,
    new_run_id,
    preset_to_json,
    sha256_text,
    sha256_file,
    write_findings_csv,
    write_json,
)

# Ensure reproducible language detection
DetectorFactory.seed = 0

# Base folder for run artifacts
RUNS_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "runs"))


def parse_preset(d: Dict[str, Any]) -> Preset:
    """Parse a preset dictionary into a Preset object."""
    return Preset(**d)


def detect_language(text: str) -> str:
    """Detect language of text, defaulting to English."""
    try:
        return detect(text)
    except Exception:
        return "en"


def analyze_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze text using the specified layer.

    Input payload:
        - text: The text to analyze
        - preset: Preset configuration
        - model_path: (optional) Path to model for Layer 2

    Returns:
        - run_id: Unique run identifier
        - run_folder: Path to run artifacts
        - redacted_text: Anonymized text
        - summary: Entity counts
        - findings_count: Total findings
    """
    preset = parse_preset(payload["preset"])
    text = payload["text"]
    model_path = payload.get("model_path", "")

    # Determine language
    if preset.language_mode == "fixed" and preset.language:
        language = preset.language
    else:
        language = detect_language(text)

    # Create run folder
    run_id = new_run_id()
    run_folder = make_run_folder(RUNS_BASE, run_id)

    # Select layer-specific analyzer
    if preset.layer == 1:
        redacted, findings, summary = analyze_layer1_text(text, preset, language)
    elif preset.layer == 2:
        redacted, findings, summary = analyze_layer2_text(text, preset, language, model_path)
    elif preset.layer == 3:
        redacted, findings, summary = analyze_layer3_text(text, preset, language)
    else:
        # Default to Layer 1
        redacted, findings, summary = analyze_layer1_text(text, preset, language)

    # Write artifacts
    write_json(os.path.join(run_folder, "preset_used.json"), preset_to_json(preset))
    write_json(os.path.join(run_folder, "model_inventory.json"), build_model_inventory())
    write_json(os.path.join(run_folder, "run_report.json"),
               build_run_report(run_id, preset, summary, 1))

    write_findings_csv(
        os.path.join(run_folder, "findings.csv"),
        run_id,
        sha256_text(text),
        findings,
    )

    # Write redacted output
    with open(os.path.join(run_folder, "output", "TEXT_0001_redacted.txt"), "w", encoding="utf-8") as f:
        f.write(redacted)

    return {
        "run_id": run_id,
        "run_folder": run_folder,
        "redacted_text": redacted,
        "summary": summary,
        "findings_count": len(findings),
        "language": language,
    }


def analyze_file(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single file.

    Input payload:
        - input_path: Path to input file
        - preset: Preset configuration

    Returns:
        - run_id: Unique run identifier
        - run_folder: Path to run artifacts
        - output_path: Path to redacted file
        - summary: Entity counts
    """
    preset = parse_preset(payload["preset"])
    input_path = payload["input_path"]

    # Determine language
    if preset.language_mode == "fixed" and preset.language:
        language = preset.language
    else:
        language = "en"

    # Create run folder
    run_id = new_run_id()
    run_folder = make_run_folder(RUNS_BASE, run_id)
    output_folder = os.path.join(run_folder, "output")

    # Determine file type and process
    ext = os.path.splitext(input_path)[1].lower()
    filename = safe_basename(input_path)
    file_id = "FILE_00001"

    if ext == ".docx":
        out_name = filename[:-5] + "_redacted.docx" if filename.lower().endswith(".docx") else filename + "_redacted.docx"
        output_path = os.path.join(output_folder, out_name)
        findings, summary = scrub_docx(input_path, output_path, preset, language, file_id)
    elif ext == ".pdf":
        out_name = filename[:-4] + "_redacted.pdf" if filename.lower().endswith(".pdf") else filename + "_redacted.pdf"
        output_path = os.path.join(output_folder, out_name)
        findings, summary = scrub_pdf(input_path, output_path, preset, language, file_id)
    elif ext == ".txt":
        out_name = filename[:-4] + "_redacted.txt" if filename.lower().endswith(".txt") else filename + "_redacted.txt"
        output_path = os.path.join(output_folder, out_name)

        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()

        redacted, findings, summary = analyze_layer1_text(text, preset, language)

        for fd in findings:
            fd.file_id = file_id
            fd.original_filename = filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(redacted)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Write artifacts
    write_json(os.path.join(run_folder, "preset_used.json"), preset_to_json(preset))
    write_json(os.path.join(run_folder, "model_inventory.json"), build_model_inventory())
    write_json(os.path.join(run_folder, "run_report.json"),
               build_run_report(run_id, preset, summary, 1))

    write_findings_csv(
        os.path.join(run_folder, "findings.csv"),
        run_id,
        sha256_file(input_path),
        findings,
    )

    return {
        "run_id": run_id,
        "run_folder": run_folder,
        "output_path": output_path,
        "summary": summary,
        "findings_count": len(findings),
    }


def analyze_docx(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy command for DOCX analysis. Delegates to analyze_file."""
    return analyze_file(payload)


def get_supported_extensions(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return list of supported file extensions."""
    return {
        "extensions": default_dispatcher.supported_extensions(),
    }


def main() -> None:
    """Main entry point - parse command and execute."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command specified"}))
        sys.exit(1)

    cmd = sys.argv[1]
    payload = json.loads(sys.stdin.read())

    handlers = {
        "analyze_text": analyze_text,
        "analyze_file": analyze_file,
        "analyze_docx": analyze_docx,
        "get_supported_extensions": get_supported_extensions,
    }

    if cmd not in handlers:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

    try:
        result = handlers[cmd](payload)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
