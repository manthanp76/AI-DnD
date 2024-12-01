from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from entities.items import Item
from utils.dice import DiceRoller

@dataclass
class Player:
    name: str
    hp: int = 50
    max_hp: int = 50
    attack_power: int = 5
    defense: int = 2
    xp: int = 0
    level: int = 1
    inventory: List[Item] = field(default_factory=list)
    current_location_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status_effects: Dict[str, int] = field(default_factory=dict)  # effect -> duration

    def __post_init__(self):
        """Initialize additional attributes after creation"""
        if not hasattr(self, 'attributes'):
            self.attributes = {
                'equipped_weapon': None,
                'equipped_armor': None,
                'active_buffs': [],
                'skills': [],
                'resistances': []
            }
        if not hasattr(self, 'status_effects'):
            self.status_effects = {}

    def attack(self) -> int:
        """Perform an attack roll"""
        base_roll = DiceRoller.roll("1d8").total
        damage = base_roll + self.attack_power
        
        # Critical hit (natural 8)
        if base_roll == 8:
            damage *= 2
            
        return damage

    def take_damage(self, amount: int) -> bool:
        """Take damage and return if defeated"""
        actual_damage = max(1, amount - self.defense)
        self.hp = max(0, self.hp - actual_damage)
        return self.hp <= 0

    def heal(self, amount: int) -> int:
        """Heal and return amount healed"""
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

    def add_xp(self, amount: int) -> bool:
        """Add XP and return whether leveled up"""
        self.xp += amount
        if self.xp >= self.level * 100:  # Simple XP curve
            self.level_up()
            return True
        return False

    def level_up(self) -> None:
        """Level up and improve stats"""
        self.level += 1
        self.max_hp += 10
        self.hp = self.max_hp  # Full heal on level up
        self.attack_power += 2
        self.defense += 1

    def add_item(self, item: Item) -> None:
        """Add item to inventory"""
        self.inventory.append(item)

    def remove_item(self, item_id: str) -> Optional[Item]:
        """Remove and return item from inventory"""
        for i, item in enumerate(self.inventory):
            if item.id == item_id:
                return self.inventory.pop(i)
        return None

    def has_item(self, item_id: str) -> bool:
        """Check if player has specific item"""
        return any(item.id == item_id for item in self.inventory)

    def get_inventory_description(self) -> str:
        """Get formatted inventory description"""
        if not self.inventory:
            return "Your inventory is empty."
            
        desc = "Inventory:\n"
        for item in self.inventory:
            desc += f"- {item.name}: {item.description}\n"
        return desc

    def add_status_effect(self, effect: str, duration: int) -> None:
        """Add a status effect with duration"""
        self.status_effects[effect] = duration

    def remove_status_effect(self, effect: str) -> None:
        """Remove a status effect"""
        if effect in self.status_effects:
            del self.status_effects[effect]

    def update_status_effects(self) -> List[str]:
        """Update status effect durations, return expired effects"""
        expired = []
        for effect, duration in list(self.status_effects.items()):
            self.status_effects[effect] = duration - 1
            if self.status_effects[effect] <= 0:
                del self.status_effects[effect]
                expired.append(effect)
        return expired

    def equip_item(self, item: Item) -> Dict[str, Any]:
        """Equip an item and return result"""
        if item.item_type.value == 'weapon':
            # Check if item is already equipped
            if self.attributes.get('equipped_weapon') == item:
                return {'success': False, 'message': f"The {item.name} is already equipped."}

            # Remove old weapon's effect
            old_weapon = self.attributes.get('equipped_weapon')
            if old_weapon:
                self.attack_power -= old_weapon.effect_value

            # Apply new weapon
            self.attributes['equipped_weapon'] = item
            self.attack_power += item.effect_value
            return {'success': True, 'message': f"You equip the {item.name}."}
        
        elif item.item_type.value == 'armor':
            # Check if item is already equipped
            if self.attributes.get('equipped_armor') == item:
                return {'success': False, 'message': f"The {item.name} is already equipped."}

            # Remove old armor's effect
            old_armor = self.attributes.get('equipped_armor')
            if old_armor:
                self.defense -= old_armor.effect_value

            # Apply new armor
            self.attributes['equipped_armor'] = item
            self.defense += item.effect_value
            return {'success': True, 'message': f"You equip the {item.name}."}
            
        return {'success': False, 'message': f"You can't equip the {item.name}."}

    def get_state(self) -> Dict:
        """Get current player state"""
        return {
            'name': self.name,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'attack_power': self.attack_power,
            'defense': self.defense,
            'xp': self.xp,
            'level': self.level,
            'inventory': [item.get_state() for item in self.inventory],
            'current_location_id': self.current_location_id,
            'attributes': self.attributes,
            'status_effects': dict(self.status_effects)
        }

    def perform_skill_check(self, difficulty: str = "normal") -> Tuple[bool, int]:
        """Perform a skill check"""
        return DiceRoller.skill_check(difficulty)
