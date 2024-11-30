from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class ThreadStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ON_HOLD = "on_hold"

class ThreadPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class StoryBranch:
    id: str
    description: str
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]
    probability: float
    chosen: bool = False

@dataclass
class StoryThread:
    id: str
    title: str
    description: str
    status: ThreadStatus
    priority: ThreadPriority
    branches: List[StoryBranch]
    current_branch: Optional[str] = None
    participants: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    prerequisites: List[Dict] = field(default_factory=list)
    progress_triggers: List[Dict] = field(default_factory=list)
    completion_conditions: List[Dict] = field(default_factory=list)
    failure_conditions: List[Dict] = field(default_factory=list)
    rewards: Dict[str, Any] = field(default_factory=dict)
