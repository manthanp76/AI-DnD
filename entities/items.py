# items.py
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
import random

class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    KEY = "key"
    TREASURE = "treasure"
    SCROLL = "scroll"
    TOOL = "tool"
    QUEST = "quest"
    MAGICAL = "magical"

class ItemRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"

@dataclass
class ItemEffect:
    type: str  # heal, damage, buff, debuff, etc.
    value: int
    duration: Optional[int] = None  # in rounds, None for permanent
    description: str = ""

@dataclass
class Item:
    id: str
    name: str
    description: str
    item_type: ItemType
    rarity: ItemRarity = ItemRarity.COMMON
    effect_value: int = 0
    uses_remaining: Optional[int] = None
    is_taken: bool = False
    is_used: bool = False
    requirements: Dict[str, Any] = field(default_factory=dict)
    effects: List[ItemEffect] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    @staticmethod
    def create_id() -> str:
        """Create a unique item ID"""
        return str(uuid.uuid4())

    def use(self, player: Any, location: Any) -> Dict[str, Any]:
        """Use item and apply effects"""
        if self.is_used and self.uses_remaining == 0:
            return {
                'success': False,
                'message': f"The {self.name} has already been used up."
            }

        # Check requirements
        if not self._check_requirements(player):
            return {
                'success': False,
                'message': f"You cannot use the {self.name} yet."
            }

        # Apply effects based on item type
        success = False
        messages = []

        for effect in self.effects:
            if effect.type == "heal":
                healing = player.heal(effect.value)
                if healing > 0:
                    messages.append(f"restore {healing} HP")
                    success = True
            elif effect.type == "buff":
                if effect.duration:
                    player.add_status_effect(effect.description, effect.duration)
                    messages.append(effect.description)
                    success = True
            elif effect.type == "damage_boost":
                player.attack_power += effect.value
                messages.append(f"increase attack power by {effect.value}")
                success = True
            elif effect.type == "defense_boost":
                player.defense += effect.value
                messages.append(f"increase defense by {effect.value}")
                success = True

        if success:
            self._consume_use()
            return {
                'success': True,
                'message': f"You use the {self.name} and {' and '.join(messages)}."
            }
        return {
            'success': False,
            'message': f"The {self.name} seems to have no effect."
        }

    def _check_requirements(self, player: Any) -> bool:
        """Check if all requirements are met"""
        if not self.requirements:
            return True
            
        for req, value in self.requirements.items():
            if req == 'min_level' and player.level < value:
                return False
            elif req == 'item_required' and not player.has_item(value):
                return False
            elif req == 'skill_required' and not hasattr(player, f"has_{value}"):
                return False
        return True

    def _check_magical_requirements(self, player: Any) -> bool:
        """Check magical requirements"""
        return player.level >= self.requirements.get('min_level', 1)

    def _consume_use(self) -> None:
        """Track item usage"""
        if self.uses_remaining is not None:
            self.uses_remaining -= 1
            if self.uses_remaining <= 0:
                self.is_used = True

    def get_state(self) -> Dict:
        """Get complete item state"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.item_type.value,
            'rarity': self.rarity.value,
            'effect_value': self.effect_value,
            'uses_remaining': self.uses_remaining,
            'is_taken': self.is_taken,
            'is_used': self.is_used,
            'effects': [{'type': e.type, 'description': e.description} for e in self.effects]
        }

class ItemFactory:
    """Factory for creating different types of items"""
    
    @staticmethod
    def create_item(name: str, item_type: str, effect_value: int = 0) -> Item:
        """Create a generic item"""
        try:
            item_type_enum = ItemType(item_type.lower())
        except ValueError:
            item_type_enum = ItemType.TREASURE

        rarity = ItemFactory._calculate_rarity(effect_value)

        # Create appropriate effects based on item type
        effects = []
        if item_type == "potion":
            effects.append(ItemEffect(
                type="heal",
                value=effect_value,
                description=f"restore {effect_value} health"
            ))
        elif item_type == "weapon":
            effects.append(ItemEffect(
                type="damage_boost",
                value=effect_value,
                description=f"increase attack power by {effect_value}"
            ))
        elif item_type == "armor":
            effects.append(ItemEffect(
                type="defense_boost",
                value=effect_value,
                description=f"increase defense by {effect_value}"
            ))
            
        return Item(
            id=Item.create_id(),
            name=name,
            description=ItemFactory._generate_description(item_type_enum, effect_value),
            item_type=item_type_enum,
            effect_value=effect_value,
            rarity=rarity,
            effects=effects
        )

    @staticmethod
    def create_healing_potion(name: str, heal_amount: int) -> Item:
        """Create a healing potion"""
        effects = [ItemEffect(
            type="heal",
            value=heal_amount,
            description=f"restore {heal_amount} health"
        )]
        
        return Item(
            id=Item.create_id(),
            name=name,
            description=f"A magical potion that restores {heal_amount} HP",
            item_type=ItemType.POTION,
            effect_value=heal_amount,
            uses_remaining=1,
            effects=effects,
            rarity=ItemFactory._calculate_rarity(heal_amount)
        )

    @staticmethod
    def create_weapon(name: str, damage_bonus: int) -> Item:
        """Create a weapon"""
        effects = [ItemEffect(
            type="damage_boost",
            value=damage_bonus,
            description=f"increase attack power by {damage_bonus}",
            duration=None  # Permanent until unequipped
        )]
        
        return Item(
            id=Item.create_id(),
            name=name,
            description=ItemFactory._generate_weapon_description(damage_bonus),
            item_type=ItemType.WEAPON,
            effect_value=damage_bonus,
            effects=effects,
            rarity=ItemFactory._calculate_rarity(damage_bonus)
        )

    @staticmethod
    def create_armor(name: str, defense_bonus: int) -> Item:
        """Create armor"""
        effects = [ItemEffect(
            type="defense_boost",
            value=defense_bonus,
            description=f"increase defense by {defense_bonus}",
            duration=None  # Permanent until unequipped
        )]
        
        return Item(
            id=Item.create_id(),
            name=name,
            description=f"Protective armor that increases your defense by {defense_bonus}",
            item_type=ItemType.ARMOR,
            effect_value=defense_bonus,
            effects=effects,
            rarity=ItemFactory._calculate_rarity(defense_bonus)
        )

    @staticmethod
    def create_magical_item(name: str, effects: List[ItemEffect], description: str = None) -> Item:
        """Create a magical item with custom effects"""
        return Item(
            id=Item.create_id(),
            name=name,
            description=description or f"A magical item with special powers",
            item_type=ItemType.MAGICAL,
            effects=effects,
            rarity=ItemRarity.RARE
        )

    @staticmethod
    def _calculate_rarity(value: int) -> ItemRarity:
        """Calculate item rarity based on effect value"""
        if value <= 5:
            return ItemRarity.COMMON
        elif value <= 10:
            return ItemRarity.UNCOMMON
        elif value <= 20:
            return ItemRarity.RARE
        else:
            return ItemRarity.LEGENDARY

    @staticmethod
    def _generate_description(item_type: ItemType, value: int) -> str:
        """Generate appropriate description based on item type"""
        if item_type == ItemType.WEAPON:
            return ItemFactory._generate_weapon_description(value)
        elif item_type == ItemType.ARMOR:
            return f"Protective armor that increases your defense by {value}"
        elif item_type == ItemType.POTION:
            return f"A magical potion that restores {value} HP"
        elif item_type == ItemType.TREASURE:
            return "A valuable treasure that might be worth something"
        elif item_type == ItemType.MAGICAL:
            return "A mysterious magical item radiating with power"
        return "An interesting item that might be useful"

    @staticmethod
    def _generate_weapon_description(damage: int) -> str:
        """Generate detailed weapon description"""
        quality = "crude" if damage <= 3 else \
                 "decent" if damage <= 6 else \
                 "fine" if damage <= 10 else \
                 "masterwork"
        return f"A {quality} weapon that adds {damage} to your attack power"
