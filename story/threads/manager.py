from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from .thread import StoryThread, ThreadStatus
from ai.generator import AIGenerator

class StoryManager:
    def __init__(self, ai_generator: AIGenerator):
        self.ai_generator = ai_generator
        self.active_threads: Dict[str, StoryThread] = {}
        self.completed_threads: List[StoryThread] = []
        self.thread_dependencies: Dict[str, List[str]] = {}

    def get_state(self) -> Dict[str, Any]:
        """Get current story system state"""
        return {
            'active_threads': {
                thread_id: {
                    'title': thread.title,
                    'description': thread.description,
                    'status': thread.status.value if hasattr(thread, 'status') else 'unknown',
                    'priority': thread.priority.value if hasattr(thread, 'priority') else 'medium',
                    'current_branch': thread.current_branch,
                    'participants': thread.participants,
                    'locations': thread.locations
                } for thread_id, thread in self.active_threads.items()
            },
            'completed_threads': [
                {
                    'title': thread.title,
                    'description': thread.description,
                    'status': thread.status.value if hasattr(thread, 'status') else 'completed'
                } for thread in self.completed_threads
            ],
            'dependencies': self.thread_dependencies
        }

    async def process_action(self, action: Dict, world_state: Dict) -> Dict[str, Any]:
        """Process player action and update story state"""
        try:
            response = await self._generate_response(action, world_state)
            
            # Update thread states
            thread_updates = []
            for thread_id, thread in list(self.active_threads.items()):
                if self._check_progress_triggers(thread, action, world_state):
                    update = await self._advance_thread(thread, action, world_state)
                    thread_updates.append(update)
                
                if self._check_completion(thread, world_state):
                    completed_thread = self.active_threads.pop(thread_id)
                    self.completed_threads.append(completed_thread)
            
            return {
                'description': response.get('description', 'You proceed with your action.'),
                'location_changes': response.get('location_changes', {}),
                'player_changes': response.get('player_changes', {}),
                'thread_updates': thread_updates,
                'state': self.get_state()
            }
            
        except Exception as e:
            logging.error(f"Error processing story action: {e}")
            return {
                'description': 'You proceed with your action.',
                'location_changes': {},
                'player_changes': {},
                'thread_updates': [],
                'state': self.get_state()
            }
        
    async def _generate_response(self, action: Dict, world_state: Dict) -> Dict[str, Any]:
        """Generate AI response to player action"""
        try:
            params = {
                'action': action,
                'world_state': world_state,
                'active_threads': [
                    {
                        'title': thread.title,
                        'description': thread.description,
                        'status': thread.status.value
                    } for thread in self.active_threads.values()
                ]
            }
            
            response = await self.ai_generator.generate_content(
                'story_response',
                params
            )
            
            return response
            
        except Exception as e:
            logging.error(f"Error generating story response: {e}")
            return {
                'description': 'You proceed with your action.',
                'location_changes': {},
                'player_changes': {}
            }

    def _check_progress_triggers(self, thread: StoryThread, 
                               action: Dict, world_state: Dict) -> bool:
        """Check if action triggers thread progress"""
        # Basic implementation - can be expanded
        return True

    def _check_completion(self, thread: StoryThread, world_state: Dict) -> bool:
        """Check if thread is completed"""
        # Basic implementation - can be expanded
        return False

    async def _advance_thread(self, thread: StoryThread, 
                            action: Dict, world_state: Dict) -> Dict:
        """Advance thread state"""
        return {
            'thread_id': thread.id,
            'status': 'advanced',
            'changes': {}
        }