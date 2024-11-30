from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from .consequence import Consequence, ConsequenceEffect, ConsequenceScope, ConsequenceType
from ...ai.generator import AIGenerator

class EvolutionPattern(Enum):
    LINEAR = "linear"          # Steady progression
    EXPONENTIAL = "exponential"  # Accelerating change
    CYCLICAL = "cyclical"      # Repeating patterns
    CASCADING = "cascading"    # Triggering related changes
    THRESHOLD = "threshold"    # Sudden changes at specific points
    ADAPTIVE = "adaptive"      # Changes based on world response
    RANDOM = "random"          # Unpredictable changes

@dataclass
class EvolutionStage:
    description: str
    intensity_change: int
    effect_changes: List[Dict[str, Any]]
    conditions: List[Dict[str, Any]]
    duration: Optional[timedelta]
    next_stages: List[str]
    probability: float = 1.0

@dataclass
class EvolutionPath:
    id: str
    pattern: EvolutionPattern
    stages: List[EvolutionStage]
    current_stage_index: int = 0
    mutations: List[Dict] = None
    stability_factor: float = 1.0  # 1.0 is stable, lower values increase mutation chance

class ConsequenceEvolution:
    def __init__(self, ai_generator: AIGenerator):
        self.ai_generator = ai_generator
        self.active_evolutions: Dict[str, EvolutionPath] = {}
        
    def initialize_evolution(self, consequence: Consequence) -> EvolutionPath:
        """Initialize an evolution path for a consequence"""
        params = {
            'consequence': {
                'title': consequence.title,
                'description': consequence.description,
                'scope': consequence.scope.value,
                'type': consequence.type.value,
                'intensity': consequence.intensity
            },
            'world_state': self._gather_evolution_context(consequence)
        }
        
        response = self.ai_generator.generate_content('evolution_initialization', params)
        
        evolution_path = self._create_evolution_path(response)
        self.active_evolutions[consequence.id] = evolution_path
        return evolution_path

    def evolve_consequence(self, consequence: Consequence, 
                         world_state: Dict,
                         time_passed: timedelta) -> Dict[str, Any]:
        """Evolve a consequence based on its pattern and current state"""
        evolution_path = self.active_evolutions.get(consequence.id)
        if not evolution_path:
            evolution_path = self.initialize_evolution(consequence)
            
        # Check for potential mutations
        self._check_mutations(evolution_path, world_state)
        
        # Get current stage
        current_stage = evolution_path.stages[evolution_path.current_stage_index]
        
        # Check if stage conditions are met for progression
        if self._check_stage_progression(current_stage, consequence, world_state, time_passed):
            return self._progress_evolution(consequence, evolution_path, world_state)
        
        # Apply current stage effects
        return self._apply_stage_effects(consequence, current_stage, time_passed)

    def _check_mutations(self, evolution_path: EvolutionPath, 
                        world_state: Dict) -> None:
        """Check for and apply potential mutations to the evolution path"""
        mutation_chance = (1 - evolution_path.stability_factor) * \
                         self._calculate_mutation_pressure(world_state)
        
        if mutation_chance > 0 and random.random() < mutation_chance:
            params = {
                'evolution_path': {
                    'pattern': evolution_path.pattern.value,
                    'current_stage': evolution_path.stages[evolution_path.current_stage_index],
                    'mutations': evolution_path.mutations
                },
                'world_state': world_state
            }
            
            response = self.ai_generator.generate_content('evolution_mutation', params)
            self._apply_mutation(evolution_path, response['mutation'])

    def _progress_evolution(self, consequence: Consequence,
                          evolution_path: EvolutionPath,
                          world_state: Dict) -> Dict[str, Any]:
        """Progress to the next evolution stage"""
        current_stage = evolution_path.stages[evolution_path.current_stage_index]
        
        # Determine next stage based on conditions and probabilities
        possible_next_stages = self._get_possible_next_stages(
            current_stage, evolution_path, world_state
        )
        
        if not possible_next_stages:
            return {'status': 'completed', 'changes': None}
            
        # Use AI to select most appropriate next stage
        params = {
            'current_stage': current_stage,
            'possible_stages': possible_next_stages,
            'world_state': world_state,
            'consequence': consequence.__dict__
        }
        
        response = self.ai_generator.generate_content('stage_selection', params)
        next_stage_index = evolution_path.stages.index(
            self._find_stage_by_description(evolution_path, response['selected_stage'])
        )
        
        # Apply stage transition
        evolution_path.current_stage_index = next_stage_index
        new_stage = evolution_path.stages[next_stage_index]
        
        return {
            'status': 'progressed',
            'changes': {
                'intensity_change': new_stage.intensity_change,
                'effect_changes': new_stage.effect_changes,
                'description': new_stage.description
            }
        }

    def _apply_stage_effects(self, consequence: Consequence,
                           stage: EvolutionStage,
                           time_passed: timedelta) -> Dict[str, Any]:
        """Apply the effects of the current evolution stage"""
        # Calculate effect magnitude based on time passed
        if stage.duration:
            progress = min(1.0, time_passed / stage.duration)
        else:
            progress = 1.0
            
        applied_effects = []
        for effect_change in stage.effect_changes:
            applied_effect = self._apply_effect_change(
                effect_change, progress, consequence
            )
            applied_effects.append(applied_effect)
            
        return {
            'status': 'active',
            'changes': {
                'intensity_change': int(stage.intensity_change * progress),
                'applied_effects': applied_effects,
                'progress': progress
            }
        }

    def _calculate_mutation_pressure(self, world_state: Dict) -> float:
        """Calculate environmental pressure for mutations"""
        factors = {
            'magical_instability': self._get_magical_instability(world_state),
            'chaos_level': self._get_chaos_level(world_state),
            'player_influence': self._get_player_influence(world_state),
            'world_events': self._get_significant_events(world_state)
        }
        
        return sum(factors.values()) / len(factors)

    def _get_possible_next_stages(self, current_stage: EvolutionStage,
                                evolution_path: EvolutionPath,
                                world_state: Dict) -> List[EvolutionStage]:
        """Get all possible next stages based on conditions"""
        possible_stages = []
        
        for stage_id in current_stage.next_stages:
            stage = self._find_stage_by_id(evolution_path, stage_id)
            if stage and self._check_stage_conditions(stage, world_state):
                possible_stages.append(stage)
                
        return possible_stages

    def _create_evolution_path(self, ai_response: Dict) -> EvolutionPath:
        """Create an evolution path from AI response"""
        stages = []
        for stage_data in ai_response['stages']:
            stage = EvolutionStage(
                description=stage_data['description'],
                intensity_change=stage_data['intensity_change'],
                effect_changes=stage_data['effect_changes'],
                conditions=stage_data['conditions'],
                duration=timedelta(minutes=stage_data['duration_minutes']) 
                    if stage_data.get('duration_minutes') else None,
                next_stages=stage_data['next_stages'],
                probability=stage_data.get('probability', 1.0)
            )
            stages.append(stage)
            
        return EvolutionPath(
            id=ai_response['path_id'],
            pattern=EvolutionPattern(ai_response['pattern']),
            stages=stages,
            mutations=[],
            stability_factor=ai_response.get('stability_factor', 1.0)
        )

    def _apply_mutation(self, evolution_path: EvolutionPath,
                       mutation: Dict) -> None:
        """Apply a mutation to the evolution path"""
        if mutation['type'] == 'add_stage':
            new_stage = EvolutionStage(**mutation['stage_data'])
            evolution_path.stages.append(new_stage)
            # Update next_stages references
            for stage in evolution_path.stages:
                if mutation['after_stage'] in stage.next_stages:
                    stage.next_stages.append(new_stage.id)
                    
        elif mutation['type'] == 'modify_stage':
            stage = self._find_stage_by_id(evolution_path, mutation['stage_id'])
            if stage:
                for key, value in mutation['changes'].items():
                    setattr(stage, key, value)
                    
        elif mutation['type'] == 'remove_stage':
            stage = self._find_stage_by_id(evolution_path, mutation['stage_id'])
            if stage:
                evolution_path.stages.remove(stage)
                # Update next_stages references
                for s in evolution_path.stages:
                    if stage.id in s.next_stages:
                        s.next_stages.remove(stage.id)
                        s.next_stages.extend(stage.next_stages)
                        
        evolution_path.mutations.append(mutation)