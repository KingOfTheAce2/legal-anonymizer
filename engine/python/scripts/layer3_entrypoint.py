import json
import os
import sys
from typing import Any, Dict

from anonymizer_engine.preset import Preset
from anonymizer_engine.layer3_presidio import analyze_layer3_text_stub, apply_layer3_actions
from anonymizer_engine.report import (
    make_run_folder,
    new_run_id,
    write_json,
    write_findings_csv,
    build_model_inventory,
    build_run_report,
    sha256_text,
    preset_to_json,
)


def _read_json() -> Dict[str, Any]:
    raw = sys.stdin.buffer.read()
    return json.loads(raw.decode("utf-8")) if raw else {}


def _parse_preset(d: Dict[str, Any]) -> Preset:
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


def main() -> None:
    payload = _read_json()
    preset = _parse_preset(payload["preset"])
    text = payload["text"]

    runs_base = payload.get("runs_base")
    if not runs_base:
        runs_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "runs"))

    language = payload.get("language") or (preset.language if preset.language_mode == "fixed" else "en")

    run_id = new_run_id()
    run_folder = make_run_folder(runs_base, run_id)

    candidates = analyze_layer3_text_stub(text)
    redacted_text, findings, summary = apply_layer3_actions(
        text=text,
        candidates=candidates,
        preset=preset,
        language=language,
        file_id="TEXT_0001",
        original_filename="",
    )

    write_json(os.path.join(run_folder, "preset_used.json"), preset_to_json(preset))
    inv = build_model_inventory()
    inv["presidio"] = {"used": True, "mode": "stub"}
    write_json(os.path.join(run_folder, "model_inventory.json"), inv)
    write_json(os.path.join(run_folder, "run_report.json"), build_run_report(run_id, preset, summary, 1))
    write_findings_csv(os.path.join(run_folder, "findings.csv"), run_id, sha256_text(text), findings)

    with open(os.path.join(run_folder, "output", "TEXT_0001_redacted.txt"), "w", encoding="utf-8") as f:
        f.write(redacted_text)

    sys.stdout.write(json.dumps({
        "ok": True,
        "run_id": run_id,
        "run_folder": run_folder,
        "summary": summary,
        "language": language
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
