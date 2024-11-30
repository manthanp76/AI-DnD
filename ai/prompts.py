from typing import Dict, List, Any, Optional
import json
from pathlib import Path
import logging

class PromptManager:
    def __init__(self):
        self.templates = self._load_templates()
        self.prompt_relationships = self._load_prompt_relationships()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for AI context"""
        return """You are an expert D&D Dungeon Master AI assistant.
        Generate creative and consistent content that:
        - Follows D&D themes and mechanics
        - Maintains narrative consistency
        - Creates engaging scenarios
        - Balances challenge and fun
        - Provides clear, actionable descriptions"""

    def format_prompt(self, prompt_type: str, parameters: Dict[str, Any], variant: Optional[str] = None) -> str:
        if prompt_type not in self.templates:
            logging.warning(f"Unknown prompt type: {prompt_type}, using fallback")
            return self._get_fallback_template()
        
        try:
            # Add default purpose if not provided
            if 'purpose' not in parameters:
                parameters['purpose'] = 'exploration'
                
            template = self.templates[prompt_type]['base'].format(**parameters)
            if variant and variant in self.templates[prompt_type].get('variants', {}):
                template += f"\n\n{self.templates[prompt_type]['variants'][variant]}"
                
            formatting = self._get_formatting_instructions(prompt_type)
            if formatting:
                template += f"\n\n{formatting}"
                
            return template
            
        except KeyError as e:
            logging.error(f"Missing required parameter: {e}")
            return self._get_fallback_template()
        except Exception as e:
            logging.error(f"Error formatting prompt with parameters: {e}")
            return self._get_fallback_template()

    # ... (rest of the previous methods remain the same)    
    def _get_formatting_instructions(self, prompt_type: str) -> str:
        formatting_instructions = {
            'location_description': """
            Format response as:
            Description: (2-3 sentences of vivid description)
            Name: (location name)
            Features: (comma-separated list of notable features)
            Theme: (primary theme)
            Atmosphere: (1 sentence about the mood/feeling)
            Secrets: (any hidden elements or hints)""",
            
            'npc_dialog': """
            Format response as:
            Dialog: (what the NPC says)
            Action: (how they say it)
            Intent: (their hidden motivation)"""
        }
        return formatting_instructions.get(prompt_type, "")
    
    def _get_fallback_template(self) -> str:
        return "Please describe what happens next in the game."

    def get_template(self, category: str, template_name: str) -> str:
        return self.templates.get(category, {}).get(template_name)

    def _load_templates(self) -> Dict:
        """Load prompt templates from file"""
        template_path = Path(__file__).parent / 'templates' / 'prompts.json'
        try:
            if template_path.exists():
                with open(template_path, 'r') as f:
                    return json.load(f)
            else:
                logging.warning(f"Template file not found: {template_path}")
                return self._get_default_templates()
        except Exception as e:
            logging.error(f"Error loading templates: {e}")
            return self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[str, Dict[str, str]]:
        return {
            'location_description': {
                'base': "Create a detailed description for a {type} location with theme: {theme}",
                'variants': {
                    'combat': "Add combat-relevant features",
                    'puzzle': "Focus on mysterious elements",
                    'treasure': "Emphasize valuable items"
                },
            'story_response': {
                'base': """Process this player action and generate a response:
                Action: {action}
                Current State: {world_state}
                Active Threads: {active_threads}
                
                Generate a response that includes:
                - Description of what happens
                - Any changes to the location
                - Any changes to the player
                """,
                'variants': {
                    'combat': "Focus on action and combat outcomes",
                    'exploration': "Emphasize discovery and environment",
                    'dialogue': "Focus on character interactions"
                }
            }
            }
        }

    def _load_prompt_relationships(self) -> Dict[str, List[str]]:
        """Load prompt relationship mappings"""
        relationship_path = Path(__file__).parent / 'templates' / 'relationships.json'
        try:
            if relationship_path.exists():
                with open(relationship_path, 'r') as f:
                    return json.load(f)
            else:
                logging.warning(f"Relationships file not found: {relationship_path}")
                return {}
        except Exception as e:
            logging.error(f"Error loading relationships: {e}")
            return {}