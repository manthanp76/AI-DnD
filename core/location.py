# location.py
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from entities.npcs import NPC
from entities.items import Item

@dataclass
class Location:
    id: str
    name: str
    description: str
    theme: str
    features: List[str]
    atmosphere: str
    npcs: List[NPC] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> location_id
    state_changes: Dict[str, bool] = field(default_factory=dict)
    secrets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    visited: bool = False
    hidden_items: List[Item] = field(default_factory=list)
    searchable_features: Dict[str, List[str]] = field(default_factory=dict)
    
    def get_current_description(self) -> str:
        """Get the current description reflecting the location's state"""
        description_parts = []
        
        # Main description
        description_parts.append(self.description.strip())
        
        # Features if present
        if self.features:
            features_desc = "Notable features include: " + ", ".join(self.features)
            description_parts.append(features_desc)

        # Atmosphere
        if self.atmosphere:
            description_parts.append(self.atmosphere)

        # Visible NPCs
        visible_npcs = [npc for npc in self.npcs if not npc.is_defeated]
        if visible_npcs:
            for npc in visible_npcs:
                description_parts.append(f"You see {npc.name} here.")

        # Visible items (not hidden)
        visible_items = [item for item in self.items if not item.is_taken]
        if visible_items:
            for item in visible_items:
                description_parts.append(f"There is {item.name} here.")

        # Available exits
        if self.exits:
            exits_desc = "You can go: " + ", ".join(self.exits.keys())
            description_parts.append(exits_desc)

        return " ".join(description_parts)

    def get_item(self, item_name: str) -> Optional[Item]:
        """Get item by name - handle multi-word items"""
        if not item_name:
            return None
            
        item_name = item_name.lower()
        for item in self.items:
            if item.name.lower() == item_name and not item.is_taken:
                return item
        return None

    def get_searchable_features(self) -> List[str]:
        """Get list of features that can be searched"""
        searchable = []
        for feature in self.features:
            feature_lower = feature.lower()
            # Check if feature has hidden items or secrets
            if (feature_lower in self.searchable_features or 
                any(item.name.lower() in feature_lower for item in self.hidden_items)):
                searchable.append(feature)
        return searchable

    def add_searchable_feature(self, feature: str, discoveries: List[str]) -> None:
        """Add a feature that can be searched"""
        self.searchable_features[feature.lower()] = discoveries

    def search_feature(self, feature: str) -> Optional[Dict[str, Any]]:
        """Search a specific feature and return any discoveries"""
        feature_lower = feature.lower()
        
        # Check for hidden items
        found_items = []
        for item in self.hidden_items[:]:  # Create a copy to modify during iteration
            if item.name.lower() in feature_lower:
                found_items.append(item)
                self.hidden_items.remove(item)
                self.items.append(item)

        # Check for predefined discoveries
        discoveries = self.searchable_features.get(feature_lower, [])
        
        if found_items or discoveries:
            return {
                'found_items': found_items,
                'discoveries': discoveries
            }
        return None

    def add_hidden_item(self, item: Item) -> None:
        """Add an item that must be found through searching"""
        self.hidden_items.append(item)

    def add_npc(self, npc: NPC) -> None:
        """Add an NPC to the location"""
        self.npcs.append(npc)

    def remove_npc(self, npc_id: str) -> Optional[NPC]:
        """Remove and return an NPC"""
        for i, npc in enumerate(self.npcs):
            if npc.id == npc_id:
                return self.npcs.pop(i)
        return None

    def get_npc(self, npc_name: str) -> Optional[NPC]:
        """Get NPC by name"""
        if not npc_name:
            return None
        for npc in self.npcs:
            if npc.name.lower() == npc_name.lower() and not npc.is_defeated:
                return npc
        return None

    def add_item(self, item: Item) -> None:
        """Add an item to the location"""
        self.items.append(item)

    def remove_item(self, item_id: str) -> Optional[Item]:
        """Remove and return an item"""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                return self.items.pop(i)
        return None

    def get_feature_description(self, feature: str) -> Optional[str]:
        """Get detailed description of a specific feature"""
        feature_lower = feature.lower()
        for f in self.features:
            if feature_lower in f.lower():
                # Generate or return a detailed description of the feature
                return f"You examine the {f}. " + self._generate_feature_description(f)
        return None

    def _generate_feature_description(self, feature: str) -> str:
        """Generate a detailed description for a feature"""
        # Add detailed descriptions based on feature type
        if "tree" in feature.lower():
            return """Its ancient bark is weathered and worn, with intricate patterns 
            that seem almost like writing. The branches reach toward the sky, 
            swaying gently in the breeze."""
        elif "water" in feature.lower() or "stream" in feature.lower():
            return """The water is crystal clear, reflecting the light in 
            mesmerizing patterns. Small ripples dance across its surface."""
        elif "stone" in feature.lower() or "rock" in feature.lower():
            return """The stone surface is cool to the touch, bearing the marks 
            of countless years of weathering. Faint markings catch your eye."""
        else:
            return """It appears to be a natural part of the environment, 
            though something about it catches your attention."""

    def add_exit(self, direction: str, location_id: str) -> None:
        """Add an exit"""
        self.exits[direction.lower()] = location_id

    def remove_exit(self, direction: str) -> None:
        """Remove an exit"""
        direction = direction.lower()
        if direction in self.exits:
            del self.exits[direction]

    def get_exit(self, direction: str) -> Optional[str]:
        """Get destination for an exit"""
        return self.exits.get(direction.lower())

    def add_secret(self, secret_id: str, description: str, discovered: bool = False) -> None:
        """Add a secret to the location"""
        self.secrets[secret_id] = {
            'description': description,
            'discovered': discovered,
            'discovery_time': None
        }

    def discover_secret(self, secret_id: str) -> bool:
        """Mark a secret as discovered"""
        if secret_id in self.secrets and not self.secrets[secret_id]['discovered']:
            self.secrets[secret_id]['discovered'] = True
            self.secrets[secret_id]['discovery_time'] = datetime.now()
            return True
        return False

    def set_state(self, key: str, value: bool) -> None:
        """Set a state value"""
        self.state_changes[key] = value

    def get_state(self) -> Dict:
        """Get complete location state"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'theme': self.theme,
            'features': self.features,
            'atmosphere': self.atmosphere,
            'npcs': [npc.get_state() for npc in self.npcs],
            'items': [item.get_state() for item in self.items],
            'exits': self.exits,
            'state_changes': self.state_changes,
            'secrets': {k: v['discovered'] for k, v in self.secrets.items()},
            'visited': self.visited,
            'searchable_features': list(self.searchable_features.keys())
        }