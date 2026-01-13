import json
import os
import sys
from typing import Any, Dict

from langdetect import detect, DetectorFactory

from anonymizer_engine.layer1 import analyze_layer1_text
from anonymizer_engine.preset import Preset
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

# Make language detection deterministic
DetectorFactory.seed = 0

RUNS_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "runs")
)


def parse_preset(d: Dict[str, Any]) -> Preset:
    return Preset(
        preset_id=d["preset_id"],
        name=d["name"],
        layer=int(d["layer"]),
        minimum_confidence=int(d["minimum_confidence"]),
        uncertainty_policy=d["uncertainty_policy"],
        pseudonym_style=d["pseudonym_style"],
        language_mode=d["language_mode"],
        language=d.get("language"),
        entities_enabled=d["entities_enabled"],
    )


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "en"


def analyze_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    preset = parse_preset(payload["preset"])
    text = payload["text"]

    # Language resolution logic
    if preset.language_mode == "fixed" and preset.language:
        language = preset.language
        language_source = "user"
    else:
        language = detect_language(text)
        language_source = "auto"

    run_id = new_run_id()
    run_folder = make_run_folder(RUNS_BASE, run_id)

    redacted_text, findings, summary = analyze_layer1_text(
        text,
        preset,
        language,
    )

    file_hash = sha256_text(text)

    # Write artifacts
    write_json(
        os.path.join(run_folder, "preset_used.json"),
        preset_to_json(preset),
    )

    write_json(
        os.path.join(run_folder, "model_inventory.json"),
        build_model_inventory(),
    )

    write_json(
        os.path.join(run_folder, "run_report.json"),
        {
            **build_run_report(run_id, preset, summary, file_count=1),
            "language": language,
            "language_source": language_source,
        },
    )

    write_findings_csv(
        os.path.join(run_folder, "findings.csv"),
        run_id,
        file_hash,
        findings,
    )

    # Write redacted output
    out_path = os.path.join(
        run_folder, "output", "TEXT_0001_redacted.txt"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(redacted_text)

    return {
        "run_id": run_id,
        "redacted_text": redacted_text,
        "run_folder": run_folder,
        "summary": summary,
        "language": language,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("missing command", file=sys.stderr)
        sys.exit(2)

    cmd = sys.argv[1].strip()
    raw = sys.stdin.buffer.read()
    payload = json.loads(raw.decode("utf-8")) if raw else {}

    if cmd == "analyze_text":
        res = analyze_text(payload)
        sys.stdout.write(json.dumps(res, ensure_ascii=False))
        return

    print(f"unknown command: {cmd}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
