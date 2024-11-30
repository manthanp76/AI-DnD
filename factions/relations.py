from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class DiplomaticEvent:
    type: str
    description: str
    source_faction: str
    target_faction: str
    timestamp: datetime
    changes: Dict[str, float]
    context: Dict

class DiplomaticRelationManager:
    def __init__(self):
        self.events: List[DiplomaticEvent] = []
    
    def add_event(self, event: DiplomaticEvent) -> None:
        """Record a diplomatic event"""
        self.events.append(event)
        
    def get_faction_history(self, faction_id: str) -> List[DiplomaticEvent]:
        """Get diplomatic history for a faction"""
        return [
            event for event in self.events
            if event.source_faction == faction_id 
            or event.target_faction == faction_id
        ]
    
    def get_relationship_trends(self, faction_id1: str, 
                              faction_id2: str,
                              timeframe: timedelta) -> Dict:
        """Analyze relationship trends between two factions"""
        relevant_events = [
            event for event in self.events
            if (event.source_faction in [faction_id1, faction_id2]
                and event.target_faction in [faction_id1, faction_id2]
                and event.timestamp >= datetime.now() - timeframe)
        ]
        
        trust_change = sum(
            event.changes.get('trust', 0.0) for event in relevant_events
        )
        influence_change = sum(
            event.changes.get('influence', 0.0) for event in relevant_events
        )
        
        return {
            'trust_trend': trust_change / len(relevant_events) if relevant_events else 0,
            'influence_trend': influence_change / len(relevant_events) if relevant_events else 0,
            'event_count': len(relevant_events),
            'major_events': [
                event for event in relevant_events
                if abs(event.changes.get('trust', 0.0)) > 0.2
                or abs(event.changes.get('influence', 0.0)) > 0.2
            ]
        }
