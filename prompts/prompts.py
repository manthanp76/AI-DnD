# prompts.py
from typing import Dict, List, Any, Optional
import json
import logging

class PromptManager:
    def __init__(self):
        self.templates = {
            'location_description': {
                'base': '''Create an immersive D&D location description.

Parameters:
- Location Type: {type}
- Theme: {theme}
- Purpose: {purpose}
- Player Level: {player_level}
- Current State: {game_state}

Required elements:
1. Vivid sensory details (sights, sounds, smells)
2. Notable features and landmarks
3. Atmospheric elements
4. Hints of potential interactions
5. Clear navigation options

Return the response as a JSON object with these EXACT fields:
{{
    "name": "Evocative location name",
    "description": "3-4 sentences of rich, sensory description",
    "theme": "Primary thematic element",
    "features": ["3-5 distinct features or landmarks"],
    "atmosphere": "One sentence mood/feeling description",
    "exits": ["available directions"],
    "secrets": ["optional hidden elements"]
}}'''
            },
            'location_population': {
                'base': '''Generate inhabitants and items for a D&D location.

Parameters:
- Location Theme: {theme}
- Player Level: {player_level}
- Location Type: {type}

Create appropriate elements that:
1. Match the location theme
2. Suit the player level
3. Provide interesting interactions
4. Balance rewards/challenges

Return the response as a JSON object with these EXACT fields:
{{
    "items": [
        {{
            "name": "Item name",
            "type": "weapon/armor/potion/key/treasure/scroll",
            "description": "Item description",
            "effect_value": 0
        }}
    ],
    "npcs": [
        {{
            "name": "NPC name",
            "type": "friendly/neutral/hostile",
            "description": "NPC description",
            "behavior": "passive/aggressive/helpful"
        }}
    ]
}}'''
            },
            'search_response': {
                'base': '''Generate detailed search results for a D&D location.

Parameters:
- Area: {area}
- Location Details: {location}
- Player State: {player}
- Previous Discoveries: {discovered_secrets}

Create engaging discoveries that:
1. Match the location theme
2. Reward thorough exploration
3. Provide meaningful finds
4. Add to the atmosphere

Return the response as a JSON object with these EXACT fields:
{{
    "description": "Detailed description of what is found",
    "discoveries": [
        {{
            "type": "item/secret/clue",
            "name": "Name of discovery",
            "description": "Detailed description",
            "item_type": "treasure/weapon/potion/etc",
            "effect_value": 0
        }}
    ]
}}'''
            },
            'examine_response': {
                'base': '''Generate examination details for a specific target.

Parameters:
- Target: {target}
- Location: {location}
- Player State: {player}
- Known Secrets: {discovered_secrets}

Create detailed observations that:
1. Provide rich details
2. Reveal interesting aspects
3. Hint at interactions
4. Maintain atmosphere

Return the response as a JSON object with these EXACT fields:
{{
    "description": "Detailed examination results",
    "features": ["Notable aspects discovered"],
    "interactions": ["Possible interactions"],
    "secrets": ["Any secrets noticed"]
}}'''
            },
            'action_response': {
                'base': '''Generate a response to a player's action.

Parameters:
- Action: {command}
- Location: {location}
- Player State: {player}
- Game State: {game_state}

Create a response that:
1. Describes the outcome clearly
2. Maintains game atmosphere
3. Provides clear feedback
4. Suggests further possibilities

Return the response as a JSON object with these EXACT fields:
{{
    "description": "What happens as a result",
    "success": true,
    "effect": {{
        "player": {{"hp_change": 0, "status_effect": null}},
        "location": {{"state_changes": {{}}}}
    }},
    "next_situation": "exploration/combat/dialog"
}}'''
            }
        }

    def format_prompt(self, prompt_type: str, parameters: Dict[str, Any]) -> str:
        """Format a prompt template with parameters"""
        if prompt_type not in self.templates:
            logging.warning(f"Unknown prompt type: {prompt_type}")
            return self._get_fallback_template()

        try:
            template = self.templates[prompt_type]['base']
            formatted_params = self._prepare_parameters(prompt_type, parameters)
            return template.format(**formatted_params)
            
        except Exception as e:
            logging.error(f"Error formatting prompt: {e}")
            return self._get_fallback_template()

    def _prepare_parameters(self, prompt_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters with defaults"""
        defaults = {
            'type': 'area',
            'theme': 'general',
            'purpose': 'exploration',
            'player_level': 1,
            'command': 'look',
            'action': 'examine',
            'location': {
                'name': 'Unknown Area',
                'description': 'A mysterious place',
                'features': []
            },
            'player': {
                'level': 1,
                'state': 'exploring',
                'skills': []
            },
            'game_state': {
                'time_of_day': 'day',
                'weather': 'clear',
                'combat_active': False
            },
            'area': 'the surroundings',
            'target': 'the object',
            'discovered_secrets': []
        }
        
        return {**defaults, **params}

    def get_system_prompt(self) -> str:
        """Get the system prompt for AI context"""
        return """You are an expert D&D Dungeon Master AI assistant.

Key responsibilities:
1. Create rich, atmospheric descriptions
2. Generate balanced encounters
3. Provide meaningful discoveries
4. Maintain narrative consistency
5. Balance challenge and reward

IMPORTANT: You must ALWAYS return responses as properly formatted JSON objects exactly matching the specified format for each prompt type. Double-check your JSON structure before responding."""

    def _get_fallback_template(self) -> str:
        """Get fallback template for errors"""
        return '''Return the response as a JSON object with these EXACT fields:
{
    "description": "The situation unfolds naturally.",
    "success": true,
    "next_situation": "exploration"
}'''

    async def cleanup(self):
        """Cleanup resources"""
        self.templates.clear()
