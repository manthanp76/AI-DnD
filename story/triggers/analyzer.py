from typing import Dict, Any, List, Optional
from .types import Trigger, TriggerType, TriggerCategory
from ai.generator import AIGenerator

class TriggerAnalyzer:
    def __init__(self, ai_generator: AIGenerator):
        self.ai_generator = ai_generator
        self.trigger_history: List[Dict] = []
        self.pattern_cache: Dict[str, Dict] = {}

    def get_state(self) -> Dict[str, Any]:
        return {
            'trigger_history': self.trigger_history,
            'pattern_cache': self.pattern_cache
        }
        
    def analyze_trigger(self, event: Dict, world_state: Dict) -> Optional[Trigger]:
        """Analyze an event for potential triggers"""
        # Get AI analysis of the event
        params = {
            'event': event,
            'world_state': world_state,
            'recent_triggers': self.trigger_history[-5:]  # Last 5 triggers
        }
        
        response = self.ai_generator.generate_content('trigger_analysis', params)
        
        if response.get('is_trigger', False):
            trigger = self._create_trigger(response, event)
            self.trigger_history.append({
                'trigger': trigger,
                'event': event,
                'timestamp': world_state['time']
            })
            return trigger
        return None
    
    def find_patterns(self) -> Dict[str, Any]:
        """Analyze trigger history for patterns"""
        if len(self.trigger_history) < 5:
            return {}
            
        params = {
            'history': self.trigger_history,
            'patterns': self.pattern_cache
        }
        
        response = self.ai_generator.generate_content('pattern_analysis', params)
        
        # Update pattern cache
        self.pattern_cache.update(response.get('patterns', {}))
        
        return response.get('patterns', {})
