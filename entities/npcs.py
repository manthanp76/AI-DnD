from enum import Enum
from typing import Dict, List, Optional, Any
import random
import uuid

class NPCType(Enum):
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    HOSTILE = "hostile"

class NPCBehavior(Enum):
    PASSIVE = "passive"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    COWARDLY = "cowardly"
    HELPFUL = "helpful"

class NPCDifficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    BOSS = "boss"

class NPC:
    def __init__(
        self,
        name: str,
        description: str,
        npc_type: NPCType,
        behavior: NPCBehavior,
        hp: int,
        max_hp: int,
        attack_power: int,
        difficulty: NPCDifficulty = NPCDifficulty.NORMAL,
        defense: int = 0,
        level: int = 1,
        faction_id: Optional[str] = None,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.npc_type = npc_type
        self.behavior = behavior
        self.hp = hp
        self.max_hp = max_hp
        self.attack_power = attack_power
        self.difficulty = difficulty
        self.defense = defense
        self.level = level
        self.faction_id = faction_id
        
        # Initialize default collections
        self.dialog = {}
        self.abilities = []
        self.weaknesses = []
        self.resistances = []
        self.loot_table = {}
        self.is_defeated = False

    def attack(self) -> tuple[int, bool]:
        """Perform an attack with damage variation"""
        base_damage = self.attack_power
        variation = random.uniform(0.8, 1.2)  # ±20% damage variation
        
        # Critical hit chance (10%)
        if random.random() < 0.1:
            damage = int(base_damage * 2 * variation)
            return damage, True  # Return damage and crit flag
            
        damage = int(base_damage * variation)
        return damage, False
        
    def take_damage(self, amount: int) -> int:
        """Take damage with defense calculation"""
        reduced_damage = max(1, amount - self.defense)
        self.hp = max(0, self.hp - reduced_damage)
        if self.hp == 0:
            self.is_defeated = True
        return reduced_damage

    def heal(self, amount: int) -> int:
        """Heal the NPC"""
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp
        
    def get_state(self) -> Dict[str, Any]:
        """Get complete NPC state"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'attack_power': self.attack_power,
            'defense': self.defense,
            'type': self.npc_type.value,
            'behavior': self.behavior.value,
            'difficulty': self.difficulty.value,
            'level': self.level,
            'is_defeated': self.is_defeated,
            'faction_id': self.faction_id,
            'abilities': self.abilities,
            'weaknesses': self.weaknesses,
            'resistances': self.resistances
        }

class NPCFactory:
    """Factory for creating different types of NPCs"""
    
    @staticmethod
    def create_combat_npc(name: str, description: str, player_level: int, location_theme: str = "normal") -> NPC:
        """Create a combat-oriented NPC scaled to player level"""
        # Determine difficulty based on location theme
        if "dangerous" in location_theme.lower():
            difficulty = NPCDifficulty.HARD
            level_modifier = 1.2
        else:
            difficulty = NPCDifficulty.NORMAL
            level_modifier = 1.0
            
        # Calculate stats based on player level
        level = max(1, int(player_level * level_modifier))
        hp = 10 + (level * 5)
        attack_power = 3 + (level * 2)
        defense = 1 + (level // 2)
        
        return NPC(
            name=name,
            description=description,
            npc_type=NPCType.HOSTILE,
            behavior=NPCBehavior.AGGRESSIVE,
            hp=hp,
            max_hp=hp,
            attack_power=attack_power,
            difficulty=difficulty,
            defense=defense,
            level=level
        )

    @staticmethod
    def create_friendly_npc(name: str, description: str) -> NPC:
        """Create a non-combat friendly NPC"""
        return NPC(
            name=name,
            description=description,
            npc_type=NPCType.FRIENDLY,
            behavior=NPCBehavior.HELPFUL,
            hp=10,
            max_hp=10,
            attack_power=1,
            difficulty=NPCDifficulty.EASY
        )

    @staticmethod
    def calculate_xp_reward(npc: NPC) -> int:
        """Calculate XP reward for defeating an NPC"""
        base_xp = 10
        
        # Scale by difficulty
        difficulty_multipliers = {
            NPCDifficulty.EASY: 0.8,
            NPCDifficulty.NORMAL: 1.0,
            NPCDifficulty.HARD: 1.5,
            NPCDifficulty.BOSS: 3.0
        }
        
        multiplier = difficulty_multipliers.get(npc.difficulty, 1.0)
        
        # Scale by level
        level_bonus = npc.level * 5
        
        return int((base_xp + level_bonus) * multiplier)