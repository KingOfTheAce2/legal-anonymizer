import json
import os
import sys

from anonymizer_engine.model_manager import ModelManager, ModelRef
from anonymizer_engine.layer2_candle import analyze_layer2_text
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
from common import read_stdin_json, parse_preset


def main() -> None:
    payload = read_stdin_json()
    preset = parse_preset(payload)
    text = payload["text"]

    runs_base = payload.get("runs_base")
    if not runs_base:
        runs_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "runs"))

    models_dir = payload.get("models_dir")
    if not models_dir:
        models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

    language = payload.get("language") or (preset.language if preset.language_mode == "fixed" else "en")

    candle_cfg = payload.get("candle_model") or {}
    model_id = candle_cfg.get("model_id")
    if not model_id:
        raise ValueError("candle_model.model_id is required but was not provided")
    filename = candle_cfg.get("filename", "model.safetensors")
    expected_sha = candle_cfg.get("sha256")

    mm = ModelManager(models_dir)
    ref = ModelRef(provider="candle", model_id=model_id, filename=filename, sha256=expected_sha)

    verify = mm.verify(ref)
    if not verify.get("ok"):
        # Explicit download is allowed only if the user asks for it
        if payload.get("download_model") is True:
            token = payload.get("hf_token")
            dl = mm.download_from_huggingface(ref, token=token)
            if not dl.get("ok"):
                sys.stdout.write(json.dumps({"ok": False, "error": dl}, ensure_ascii=False))
                return
            verify = mm.verify(ref)
        else:
            sys.stdout.write(json.dumps({"ok": False, "error": verify}, ensure_ascii=False))
            return

    model_path = verify["path"]

    run_id = new_run_id()
    run_folder = make_run_folder(runs_base, run_id)

    redacted_text, findings, summary = analyze_layer2_text(text, preset, language, model_path)

    write_json(os.path.join(run_folder, "preset_used.json"), preset_to_json(preset))
    inv = build_model_inventory()
    inv["candle"] = {"model_id": model_id, "filename": filename, "sha256": verify.get("sha256")}
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
        "language": language,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
