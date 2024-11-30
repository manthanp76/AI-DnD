from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

class ConsequenceScope(Enum):
    LOCAL = "local"
    REGIONAL = "regional"
    GLOBAL = "global"

class ConsequenceType(Enum):
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    POLITICAL = "political"
    ECONOMIC = "economic"
    MAGICAL = "magical"

@dataclass
class ConsequenceEffect:
    target_type: str  # location, faction, npc, etc.
    target_id: str
    effect_type: str
    value: Any
    duration: Optional[timedelta] = None

@dataclass
class Consequence:
    id: str
    title: str
    description: str
    scope: ConsequenceScope
    type: ConsequenceType
    intensity: int  # 1-5
    effects: List[ConsequenceEffect]
    start_time: datetime
    duration: Optional[timedelta] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    resolution_triggers: List[Dict] = field(default_factory=list)
    evolution_stages: List[Dict] = field(default_factory=list)
    current_stage: int = 0
