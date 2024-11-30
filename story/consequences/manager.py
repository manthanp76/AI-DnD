from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from .consequence import Consequence, ConsequenceEffect
from ai.generator import AIGenerator

class ConsequenceManager:
    def __init__(self, ai_generator: AIGenerator):
        self.ai_generator = ai_generator
        self.active_consequences: Dict[str, Consequence] = {}
        self.resolved_consequences: List[Consequence] = []
        self.consequence_relationships: Dict[str, List[str]] = {}

    async def process_action(self, action: Dict, world_state: Dict) -> Dict[str, Any]:
        try:
            consequences = []
            updates = {
                'description': '',
                'location_changes': {},
                'player_changes': {},
                'consequences': consequences
            }

            # Check for new consequences
            new_consequence = await self._check_for_new_consequences(action, world_state)
            if new_consequence:
                self.active_consequences[new_consequence.id] = new_consequence
                consequences.append(new_consequence.id)
                
            # Update existing consequences
            for cons_id, consequence in list(self.active_consequences.items()):
                cons_update = await self._update_consequence(consequence, action, world_state)
                if cons_update:
                    updates.update(cons_update)
                    
                if self._is_resolved(consequence, world_state):
                    self._resolve_consequence(cons_id)
                
            return updates
            
        except Exception as e:
            logging.error(f"Error processing consequences: {e}")
            return {
                'description': '',
                'location_changes': {},
                'player_changes': {},
                'consequences': []
            }

    async def _check_for_new_consequences(self, 
                                        action: Dict, 
                                        world_state: Dict) -> Optional[Consequence]:
        """Check if an action should trigger new consequences"""
        try:
            params = {
                'action': action,
                'world_state': world_state,
                'active_consequences': [c.title for c in self.active_consequences.values()]
            }
            
            response = await self.ai_generator.generate_content(
                'consequence_creation',
                params
            )
            
            if response.get('should_create', False):
                return self._create_consequence(response['consequence_data'])
            return None
            
        except Exception as e:
            logging.error(f"Error checking for consequences: {e}")
            return None

    async def _update_consequence(self, 
                                consequence: Consequence,
                                action: Dict,
                                world_state: Dict) -> Optional[Dict]:
        """Update a consequence based on current action and world state"""
        try:
            params = {
                'consequence': {
                    'id': consequence.id,
                    'title': consequence.title,
                    'description': consequence.description,
                    'current_stage': consequence.current_stage
                },
                'action': action,
                'world_state': world_state
            }
            
            response = await self.ai_generator.generate_content(
                'consequence_update',
                params
            )
            
            if response.get('has_updates', False):
                return {
                    'consequence_id': consequence.id,
                    'updates': response['updates']
                }
            return None
            
        except Exception as e:
            logging.error(f"Error updating consequence: {e}")
            return None

    def _is_resolved(self, consequence: Consequence, world_state: Dict) -> bool:
        """Check if a consequence should be resolved"""
        # Basic implementation
        return False

    def _resolve_consequence(self, consequence_id: str):
        """Move a consequence to resolved list"""
        if consequence_id in self.active_consequences:
            consequence = self.active_consequences.pop(consequence_id)
            self.resolved_consequences.append(consequence)
                    
    def get_state(self) -> Dict[str, Any]:
        """Get current state of consequences"""
        return {
            'active_consequences': {
                cons_id: {
                    'title': consequence.title,
                    'description': consequence.description,
                    'scope': consequence.scope.value,
                    'type': consequence.type.value,
                    'intensity': consequence.intensity,
                    'effects': [
                        {
                            'target_type': effect.target_type,
                            'target_id': effect.target_id,
                            'effect_type': effect.effect_type,
                            'value': effect.value,
                            'duration': str(effect.duration) if effect.duration else None
                        } for effect in consequence.effects
                    ],
                    'start_time': consequence.start_time.isoformat(),
                    'duration': str(consequence.duration) if consequence.duration else None,
                    'current_stage': consequence.current_stage
                } for cons_id, consequence in self.active_consequences.items()
            },
            'resolved_consequences': [cons.id for cons in self.resolved_consequences]
        }

    async def cleanup(self):
        """Cleanup resources"""
        self.active_consequences.clear()
        self.resolved_consequences.clear()
        self.consequence_relationships.clear()

    def create_consequence(self, trigger_event: Dict, world_state: Dict) -> Consequence:
        """Generate a new consequence from an event"""
        params = {
            'event': trigger_event,
            'world_state': world_state,
            'active_consequences': [c.title for c in self.active_consequences.values()]
        }
        
        response = self.ai_generator.generate_content('consequence_creation', params)
        consequence = self._build_consequence(response)
        self.active_consequences[consequence.id] = consequence
        return consequence
    
    def update_consequences(self, game_time: datetime, 
                          world_state: Dict) -> List[Dict]:
        """Update and evolve active consequences"""
        updates = []
        resolved = []
        
        for cons_id, consequence in self.active_consequences.items():
            if self._should_evolve(consequence, game_time, world_state):
                update = self._evolve_consequence(consequence, world_state)
                updates.append(update)
            
            if self._is_resolved(consequence, world_state):
                resolved.append(cons_id)
                
        # Remove resolved consequences
        for cons_id in resolved:
            consequence = self.active_consequences.pop(cons_id)
            self.resolved_consequences.append(consequence)
            
        return updates

