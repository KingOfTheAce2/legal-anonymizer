from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class Preset:
    preset_id: str
    name: str
    layer: int
    minimum_confidence: int  # 0..100
    uncertainty_policy: str  # mask, redact, leave_intact, flag_only
    pseudonym_style: str     # neutral, realistic
    language_mode: str       # auto, fixed
    language: Optional[str]
    entities_enabled: Dict[str, bool]
