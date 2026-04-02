from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Preset:
    name: str
    minimum_confidence: int = 75  # 0..100
    preset_id: str = "default"
    layer: int = 1
    uncertainty_policy: str = "redact"   # mask, redact, leave_intact, flag_only
    pseudonym_style: str = "neutral"     # neutral, realistic
    language_mode: str = "auto"          # auto, fixed
    language: Optional[str] = None
    entities_enabled: Dict[str, bool] = field(default_factory=dict)
    whitelist: List[str] = field(default_factory=list)
    blacklist: List[str] = field(default_factory=list)
    language_whitelists: Dict[str, List[str]] = field(default_factory=dict)
    language_blacklists: Dict[str, List[str]] = field(default_factory=dict)
