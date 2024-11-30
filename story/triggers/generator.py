from typing import Dict, List, Optional
from datetime import datetime
from .types import Trigger, TriggerType, TriggerCategory
from .analyzer import TriggerAnalyzer
from ...ai.generator import AIGenerator

class TriggerGenerator:
    def __init__(self, ai_generator: AIGenerator):
        self.ai_generator = ai_generator
        self.analyzer = TriggerAnalyzer(ai_generator)
        
    def generate_triggers(self, world_state: Dict) -> List[Trigger]:
        """Generate potential triggers based on world state"""
        # Analyze current patterns
        patterns = self.analyzer.find_patterns()
        
        params = {
            'world_state': world_state,
            'patterns': patterns,
            'time': datetime.now()
        }
        
        response = self.ai_generator.generate_content('trigger_generation', params)
        return [self._create_trigger(t) for t in response.get('triggers', [])]
    
    def check_trigger_conditions(self, trigger: Trigger, 
                               world_state: Dict) -> bool:
        """Check if trigger conditions are met"""
        for condition in trigger.conditions:
            if condition.required and not self._check_condition(
                condition, world_state
            ):
                return False
        return True
