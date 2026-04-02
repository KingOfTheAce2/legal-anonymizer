import json
import os
import sys

from anonymizer_engine.batch import run_batch_folder
from common import read_stdin_json, parse_preset


def main() -> None:
    payload = read_stdin_json()

    preset = parse_preset(payload)
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
