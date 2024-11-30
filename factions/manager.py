from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from .faction import Faction, DiplomaticStatus, ResourceType
from ai.generator import AIGenerator

class FactionManager:
    def __init__(self, ai_generator: Optional[AIGenerator] = None):
        self.factions: Dict[str, Faction] = {}
        self.ai_generator = ai_generator
        self.last_update = datetime.now()
        self.event_history: List[Dict] = []
        
    async def process_action(self, action: Dict, world_state: Dict) -> Dict[str, Any]:
        try:
            affected_factions = self._identify_affected_factions(action)
            faction_reactions = []
            
            for faction_id in affected_factions:
                reaction = await self._generate_faction_reaction(
                    faction_id, action, world_state
                )
                self._apply_faction_reaction(faction_id, reaction)
                faction_reactions.append(reaction)
                
            return {
                'reactions': faction_reactions,
                'description': self._combine_reactions(faction_reactions)
            }
        except Exception as e:
            logging.error(f"Error processing faction action: {e}")
            return {
                'reactions': [],
                'description': ''
            }

    def _combine_reactions(self, reactions: List[Dict]) -> str:
        """Combine multiple faction reactions into a single description"""
        descriptions = [r['description'] for r in reactions if r.get('description')]
        return ' '.join(descriptions) if descriptions else ''


    def _identify_affected_factions(self, action: Dict) -> List[str]:
        """Identify factions affected by an action"""
        # Basic implementation - return all faction IDs for now
        return list(self.factions.keys())

    async def _generate_faction_reaction(self, faction_id: str,
                                     action: Dict,
                                     world_state: Dict) -> Dict:
        """Generate a faction's reaction to a player action"""
        faction = self.factions[faction_id]
        
        params = {
            'faction': {
                'name': faction.name,
                'ideology': faction.ideology,
                'current_goals': faction.goals
            },
            'action': action,
            'world_state': world_state
        }
        
        try:
            reaction = await self.ai_generator.generate_content(
                'faction_reaction',
                params
            )
            return {
                'faction_id': faction_id,
                'type': reaction.get('type', 'neutral'),
                'description': reaction.get('description', ''),
                'attitude_change': reaction.get('attitude_change', 0),
                'resource_changes': reaction.get('resource_changes', {}),
                'diplomatic_changes': reaction.get('diplomatic_changes', {})
            }
        except Exception as e:
            logging.error(f"Error generating faction reaction: {e}")
            return {
                'faction_id': faction_id,
                'type': 'neutral',
                'description': 'The faction shows no obvious reaction.',
                'attitude_change': 0,
                'resource_changes': {},
                'diplomatic_changes': {}
            }

    def _apply_faction_reaction(self, faction_id: str, reaction: Dict):
        """Apply reaction effects to faction"""
        if faction_id not in self.factions:
            return
            
        faction = self.factions[faction_id]
        
        # Record event
        self.event_history.append({
            'timestamp': datetime.now(),
            'faction_id': faction_id,
            'type': reaction['type'],
            'description': reaction['description']
        })
        
    def get_state(self) -> Dict[str, Any]:
        """Get current faction state"""
        return {
            'factions': {
                faction_id: {
                    'name': faction.name,
                    'description': faction.description,
                    'power_level': faction.power_level,
                    'ideology': faction.ideology,
                    'resources': {
                        res_type.value: {
                            'amount': resource.amount,
                            'max_amount': resource.max_amount,
                            'growth_rate': resource.growth_rate
                        } for res_type, resource in faction.resources.items()
                    },
                    'relations': {
                        other_id: {
                            'status': relation.status.value,
                            'trust': relation.trust,
                            'influence': relation.influence
                        } for other_id, relation in faction.relations.items()
                    }
                } for faction_id, faction in self.factions.items()
            },
            'events': self.event_history[-10:]  # Last 10 events
        }

    async def cleanup(self):
        """Cleanup resources"""
        self.factions.clear()
        self.event_history.clear()
        
    def process_player_action(self, action: Dict, 
                            world_state: Dict) -> List[Dict]:
        """Process player action's effect on factions"""
        affected_factions = self._identify_affected_factions(action)
        faction_reactions = []
        
        for faction_id in affected_factions:
            reaction = self._generate_faction_reaction(
                faction_id, action, world_state
            )
            self._apply_faction_reaction(faction_id, reaction)
            faction_reactions.append(reaction)
            
        return faction_reactions
    
    def update_factions(self, current_time: datetime) -> List[Dict]:
        """Update all faction states"""
        updates = []
        time_passed = current_time - self.last_update
        
        # Update basic resources
        resource_updates = self._update_all_resources(current_time)
        
        # Generate and process AI faction actions
        faction_actions = self._generate_faction_actions(time_passed)
        
        # Process faction interactions
        interaction_updates = self._process_faction_interactions(faction_actions)
        
        # Combine all updates
        updates.extend(resource_updates)
        updates.extend(interaction_updates)
        
        self.last_update = current_time
        return updates
    
    def _generate_faction_reaction(self, faction_id: str,
                                 action: Dict,
                                 world_state: Dict) -> Dict:
        """Generate a faction's reaction to a player action"""
        faction = self.factions[faction_id]
        
        # Use AI to generate appropriate reaction
        reaction_prompt = {
            'faction': {
                'name': faction.name,
                'ideology': faction.ideology,
                'current_goals': faction.goals
            },
            'action': action,
            'world_state': world_state
        }
        
        reaction = self.ai_generator.generate_content(
            'faction_reaction',
            reaction_prompt
        )
        
        return {
            'faction_id': faction_id,
            'type': reaction['type'],
            'description': reaction['description'],
            'attitude_change': reaction['attitude_change'],
            'resource_changes': reaction['resource_changes'],
            'diplomatic_changes': reaction['diplomatic_changes']
        }
    
    def _process_faction_interactions(self, 
                                   faction_actions: List[Dict]) -> List[Dict]:
        """Process interactions between factions"""
        updates = []
        
        for action in faction_actions:
            source_faction = self.factions[action['source']]
            target_faction = self.factions[action['target']]
            
            # Calculate interaction results
            interaction_result = self._calculate_interaction_result(
                source_faction, target_faction, action
            )
            
            # Apply changes
            self._apply_interaction_result(
                source_faction, target_faction, interaction_result
            )
            
            updates.append({
                'type': 'faction_interaction',
                'source': action['source'],
                'target': action['target'],
                'action': action['type'],
                'result': interaction_result
            })
            
        return updates
