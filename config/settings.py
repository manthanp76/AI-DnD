# settings.py
from pathlib import Path
from typing import Dict, Any, Optional
import json
from enum import Enum
import logging

class DifficultyLevel(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    NIGHTMARE = "nightmare"

class GameMode(Enum):
    STORY = "story"
    SANDBOX = "sandbox"
    HARDCORE = "hardcore"
    ADVENTURE = "adventure"

class Settings:
    DEFAULT_CONFIG = {
        "game": {
            "mode": GameMode.STORY.value,
            "difficulty": DifficultyLevel.NORMAL.value,
            "starting_level": 1,
            "enable_permadeath": False,
            "enable_critical_failures": True,
            "auto_save": True,
            "save_interval": 300  # seconds
        },
        "world": {
            "enable_dynamic_weather": True,
            "enable_time_progression": True,
            "random_encounter_chance": 0.9,
            "max_active_quests": 10,
            "loot_quality_multiplier": 1.0,
            "enemy_scaling": True,
            "discovery_rewards": True
        },
        "ai": {
            "creativity_level": 0.7,
            "response_detail_level": "high",
            "memory_limit": 100,
            "context_window_size": 10,
            "enable_dynamic_difficulty": True,
            "narrative_consistency": True,
            "character_persistence": True
        },
        "combat": {
            "initiative_type": "individual",
            "critical_hit_multiplier": 2,
            "flanking_bonus": 2,
            "death_save_dc": 10,
            "healing_surge_value": 0.25,
            "enable_status_effects": True,
            "status_effect_duration": 3
        },
        "exploration": {
            "search_success_chance": 0.7,
            "hidden_item_chance": 0.4,
            "secret_discovery_bonus": 0.1,
            "feature_detail_level": "high",
            "enable_environmental_effects": True
        },
        "rewards": {
            "xp_multiplier": 1.0,
            "loot_frequency": "normal",
            "treasure_quality": "balanced",
            "discovery_bonus": True,
            "milestone_rewards": True
        }
    }

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/game_settings.json")
        self.settings = self._load_settings()
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('game.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Settings')
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file or use defaults"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    user_settings = json.load(f)
                    return self._merge_settings(self.DEFAULT_CONFIG, user_settings)
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
        return self.DEFAULT_CONFIG.copy()
    
    def _merge_settings(self, default: Dict, user: Dict) -> Dict:
        """Merge user settings with defaults"""
        merged = default.copy()
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict):
                if isinstance(value, dict):
                    merged[key] = self._merge_settings(merged[key], value)
            else:
                merged[key] = value
        return merged
    
    def save_settings(self) -> None:
        """Save current settings to file"""
        try:
            self.config_path.parent.mkdir(exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
    
    def get(self, *keys: str) -> Any:
        """Get a setting value by key path"""
        value = self.settings
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value
    
    def set(self, value: Any, *keys: str) -> None:
        """Set a setting value by key path"""
        settings = self.settings
        for key in keys[:-1]:
            settings = settings.setdefault(key, {})
        settings[keys[-1]] = value
        self.save_settings()

    def get_difficulty_settings(self) -> Dict[str, Any]:
        """Get current difficulty settings"""
        difficulty = self.get('game', 'difficulty')
        return {
            'easy': {
                'enemy_hp_multiplier': 0.8,
                'enemy_damage_multiplier': 0.8,
                'loot_quality': 1.2,
                'xp_multiplier': 1.2
            },
            'normal': {
                'enemy_hp_multiplier': 1.0,
                'enemy_damage_multiplier': 1.0,
                'loot_quality': 1.0,
                'xp_multiplier': 1.0
            },
            'hard': {
                'enemy_hp_multiplier': 1.2,
                'enemy_damage_multiplier': 1.2,
                'loot_quality': 0.8,
                'xp_multiplier': 0.8
            },
            'nightmare': {
                'enemy_hp_multiplier': 1.5,
                'enemy_damage_multiplier': 1.5,
                'loot_quality': 0.6,
                'xp_multiplier': 0.6
            }
        }.get(difficulty, 'normal')
