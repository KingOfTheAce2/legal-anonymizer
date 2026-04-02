"""
Shared utilities for entrypoint scripts.

Functions here are duplicated across batch_entrypoint.py, layer2_entrypoint.py,
and layer3_entrypoint.py. Import from this module instead of copying.
"""

import json
import sys
from typing import Any, Dict

from anonymizer_engine.preset import Preset


def read_stdin_json() -> Dict[str, Any]:
    """Read and decode a JSON payload from stdin."""
    raw = sys.stdin.buffer.read()
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def parse_preset(data: Dict[str, Any]) -> Preset:
    """Build a Preset from the 'preset' key of an entrypoint payload."""
    p = data["preset"]
    return Preset(
        preset_id=p["preset_id"],
        name=p["name"],
        layer=int(p["layer"]),
        minimum_confidence=int(p["minimum_confidence"]),
        uncertainty_policy=p["uncertainty_policy"],
        pseudonym_style=p["pseudonym_style"],
        language_mode=p["language_mode"],
        language=p.get("language"),
        entities_enabled=p["entities_enabled"],
    )
