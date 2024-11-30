from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
from datetime import datetime, timedelta

class DiplomaticStatus(Enum):
    ALLIED = "allied"
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    UNFRIENDLY = "unfriendly"
    HOSTILE = "hostile"
    WAR = "war"

class ResourceType(Enum):
    GOLD = "gold"
    MILITARY = "military"
    INFLUENCE = "influence"
    KNOWLEDGE = "knowledge"
    MAGIC = "magic"
    TERRITORY = "territory"

@dataclass
class FactionResource:
    type: ResourceType
    amount: float
    max_amount: float
    growth_rate: float
    last_update: datetime

@dataclass
class DiplomaticRelation:
    status: DiplomaticStatus
    trust: float  # -1.0 to 1.0
    influence: float  # 0.0 to 1.0
    trade_relations: bool
    military_pact: bool
    shared_interests: List[str]
    conflicts: List[str]
    last_interaction: datetime
    interaction_history: List[Dict] = field(default_factory=list)

@dataclass
class Faction:
    id: str
    name: str
    description: str
    leader: Optional[str]
    headquarters: str
    power_level: float  # 0.0 to 1.0
    ideology: Dict[str, float]  # belief -> strength
    resources: Dict[ResourceType, FactionResource]
    relations: Dict[str, DiplomaticRelation]
    goals: List[Dict]
    territory: Set[str]
    agents: List[str]
    active_plots: List[Dict]
    
    def update_resources(self, current_time: datetime) -> Dict[str, float]:
        """Update faction resources based on time passed"""
        updates = {}
        for res_type, resource in self.resources.items():
            time_passed = (current_time - resource.last_update).total_seconds()
            growth = resource.growth_rate * (time_passed / 86400)  # per day
            
            old_amount = resource.amount
            resource.amount = min(
                resource.max_amount,
                resource.amount + growth
            )
            resource.last_update = current_time
            
            updates[res_type.value] = resource.amount - old_amount
            
        return updates
    
    def modify_relation(self, faction_id: str, 
                       changes: Dict[str, float]) -> DiplomaticStatus:
        """Modify relationship with another faction"""
        if faction_id not in self.relations:
            return None
            
        relation = self.relations[faction_id]
        
        # Update trust and influence
        relation.trust = max(-1.0, min(1.0, 
            relation.trust + changes.get('trust', 0.0)))
        relation.influence = max(0.0, min(1.0, 
            relation.influence + changes.get('influence', 0.0)))
        
        # Determine new status based on trust
        old_status = relation.status
        relation.status = self._calculate_status(relation.trust)
        
        # Record interaction
        relation.interaction_history.append({
            'timestamp': datetime.now(),
            'changes': changes,
            'old_status': old_status,
            'new_status': relation.status
        })
        
        return relation.status
    
    def can_ally_with(self, other_faction: 'Faction') -> bool:
        """Check if alliance is possible with another faction"""
        if other_faction.id not in self.relations:
            return False
            
        relation = self.relations[other_faction.id]
        
        # Check trust threshold
        if relation.trust < 0.7:
            return False
            
        # Check ideology compatibility
        ideology_compatibility = self._calculate_ideology_compatibility(
            other_faction.ideology)
        if ideology_compatibility < 0.5:
            return False
            
        # Check for blocking conflicts
        if any(self._is_blocking_conflict(conflict) 
               for conflict in relation.conflicts):
            return False
            
        return True
    
    def _calculate_status(self, trust: float) -> DiplomaticStatus:
        """Calculate diplomatic status based on trust level"""
        if trust >= 0.8:
            return DiplomaticStatus.ALLIED
        elif trust >= 0.4:
            return DiplomaticStatus.FRIENDLY
        elif trust >= -0.2:
            return DiplomaticStatus.NEUTRAL
        elif trust >= -0.6:
            return DiplomaticStatus.UNFRIENDLY
        elif trust >= -0.9:
            return DiplomaticStatus.HOSTILE
        else:
            return DiplomaticStatus.WAR
