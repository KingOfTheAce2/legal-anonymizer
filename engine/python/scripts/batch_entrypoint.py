import json
import os
import sys
from typing import Any, Dict

from anonymizer_engine.preset import Preset
from anonymizer_engine.batch import run_batch_folder


def _read_stdin_json() -> Dict[str, Any]:
    raw = sys.stdin.buffer.read()
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


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
    payload = _read_stdin_json()

    preset = _parse_preset(payload["preset"])
    input_folder = payload["input_folder"]

    # Where runs are stored (same convention as your other entrypoint)
    runs_base = payload.get("runs_base")
    if not runs_base:
        runs_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "runs"))

    language = payload.get("language", "en")
    recursive = bool(payload.get("recursive", True))
    max_files = payload.get("max_files")

    result = run_batch_folder(
        input_folder=input_folder,
        output_base_folder=runs_base,
        preset=preset,
        language=language,
        recursive=recursive,
        max_files=max_files,
    )

    sys.stdout.write(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
