from typing import Dict, List
import json
from pathlib import Path

class PromptTemplates:
    def __init__(self):
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, Dict]:
        """Load all prompt templates"""
        template_dir = Path(__file__).parent / 'templates'
        templates = {}
        
        # Load each template category
        for template_file in template_dir.glob('*.json'):
            category = template_file.stem
            with open(template_file, 'r') as f:
                templates[category] = json.load(f)
                
        return templates
    
    def get_template(self, category: str, template_name: str) -> str:
        """Get a specific template"""
        return self.templates.get(category, {}).get(template_name)

# Example template files:

# templates/location_templates.json
{
    "dungeon_room": {
        "base": """Create a detailed description for a dungeon room with the following elements:
        Theme: {theme}
        Purpose: {purpose}
        Size: {size}
        
        Include:
        - Visual details
        - Atmosphere
        - Notable features
        - Potential secrets
        
        Format:
        Description: (2-3 sentences)
        Features: (comma-separated list)
        Atmosphere: (1 sentence)
        Secrets: (optional hints)""",
        
        "variants": {
            "combat": "Add combat-relevant features and tactical elements",
            "puzzle": "Focus on mysterious elements and puzzle mechanics",
            "treasure": "Emphasize valuable items and hidden riches"
        }
    }
}

# templates/npc_templates.json
{
    "npc_interaction": {
        "base": """Generate NPC dialogue and behavior for:
        Name: {name}
        Type: {npc_type}
        Current mood: {mood}
        Player actions: {player_actions}
        
        Include:
        - Appropriate dialogue
        - Body language
        - Hidden motivations
        - Potential hooks
        
        Format:
        Dialogue: (what they say)
        Action: (how they act)
        Motivation: (their true intent)""",
        
        "variants": {
            "friendly": "Emphasize helpful and welcoming behavior",
            "hostile": "Focus on threatening or aggressive elements",
            "mysterious": "Add cryptic hints and unclear motivations"
        }
    }
}

# templates/combat_templates.json
{
    "combat_narration": {
        "base": """Narrate this combat action:
        Actor: {actor}
        Action: {action}
        Target: {target}
        Result: {result}
        
        Create an exciting description that includes:
        - Visual details
        - Action dynamics
        - Impact effects
        - Character reactions
        
        Format:
        Narration: (2 sentences max)
        Effect: (mechanical result)
        Reaction: (character response)""",
        
        "variants": {
            "critical_hit": "Emphasize spectacular success",
            "critical_miss": "Describe amusing or dramatic failure",
            "finishing_blow": "Detail the climactic final strike"
        }
    }
}

# config/difficulty_settings.json
{
    "easy": {
        "combat": {
            "enemy_hp_multiplier": 0.8,
            "enemy_damage_multiplier": 0.8,
            "healing_multiplier": 1.2,
            "xp_multiplier": 0.9
        },
        "challenges": {
            "dc_modifier": -2,
            "time_pressure_multiplier": 0.8,
            "hint_frequency": "high"
        }
    },
    "medium": {
        "combat": {
            "enemy_hp_multiplier": 1.0,
            "enemy_damage_multiplier": 1.0,
            "healing_multiplier": 1.0,
            "xp_multiplier": 1.0
        },
        "challenges": {
            "dc_modifier": 0,
            "time_pressure_multiplier": 1.0,
            "hint_frequency": "medium"
        }
    },
    "hard": {
        "combat": {
            "enemy_hp_multiplier": 1.2,
            "enemy_damage_multiplier": 1.2,
            "healing_multiplier": 0.8,
            "xp_multiplier": 1.2
        },
        "challenges": {
            "dc_modifier": 2,
            "time_pressure_multiplier": 1.2,
            "hint_frequency": "low"
        }
    }
}
