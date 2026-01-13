import json
import os
import sys
from typing import Any, Dict
from langdetect import detect, DetectorFactory

from anonymizer_engine.preset import Preset
from anonymizer_engine.layer1 import analyze_layer1_text
from anonymizer_engine.docx_scrubber import scrub_docx, hash_file
from anonymizer_engine.report import (
    build_model_inventory,
    build_run_report,
    make_run_folder,
    new_run_id,
    preset_to_json,
    sha256_text,
    write_findings_csv,
    write_json,
)

DetectorFactory.seed = 0
RUNS_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "runs"))


def parse_preset(d: Dict[str, Any]) -> Preset:
    return Preset(**d)


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "en"


def analyze_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    preset = parse_preset(payload["preset"])
    text = payload["text"]

    language = preset.language if preset.language_mode == "fixed" else detect_language(text)

    run_id = new_run_id()
    run_folder = make_run_folder(RUNS_BASE, run_id)

    redacted, findings, summary = analyze_layer1_text(text, preset, language)

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

    with open(os.path.join(run_folder, "output", "TEXT_0001_redacted.txt"), "w", encoding="utf-8") as f:
        f.write(redacted)

    return {"run_id": run_id, "run_folder": run_folder}


def analyze_docx(payload: Dict[str, Any]) -> Dict[str, Any]:
    preset = parse_preset(payload["preset"])
    path = payload["input_path"]

    language = preset.language if preset.language_mode == "fixed" else "en"

    run_id = new_run_id()
    run_folder = make_run_folder(RUNS_BASE, run_id)

    out = os.path.join(run_folder, "output", "redacted.docx")
    findings, summary = scrub_docx(path, out, preset, language, "FILE_0001")

    write_json(os.path.join(run_folder, "preset_used.json"), preset_to_json(preset))
    write_json(os.path.join(run_folder, "model_inventory.json"), build_model_inventory())
    write_json(os.path.join(run_folder, "run_report.json"),
               build_run_report(run_id, preset, summary, 1))

    write_findings_csv(
        os.path.join(run_folder, "findings.csv"),
        run_id,
        hash_file(path),
        findings,
    )

    return {"run_id": run_id, "run_folder": run_folder, "output_path": out}


def main() -> None:
    cmd = sys.argv[1]
    payload = json.loads(sys.stdin.read())

    if cmd == "analyze_text":
        print(json.dumps(analyze_text(payload)))
    elif cmd == "analyze_docx":
        print(json.dumps(analyze_docx(payload)))
    else:
        raise RuntimeError("Unknown command")


if __name__ == "__main__":
    main()
