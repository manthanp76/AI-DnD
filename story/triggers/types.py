from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List

class TriggerType(Enum):
    DISCOVERY = "discovery"
    INTERACTION = "interaction"
    COMBAT = "combat"
    QUEST = "quest"
    STORY = "story"
    WORLD = "world"

class TriggerCategory(Enum):
    PLAYER = "player"
    WORLD = "world"
    NPC = "npc"
    FACTION = "faction"
    ENVIRONMENT = "environment"

@dataclass
class TriggerCondition:
    type: str
    parameters: Dict[str, Any]
    required: bool = True

@dataclass
class Trigger:
    id: str
    type: TriggerType
    category: TriggerCategory
    conditions: List[TriggerCondition]
    weight: float = 1.0
    cooldown: int = 0  # in minutes
    last_triggered: int = 0  # timestamp
