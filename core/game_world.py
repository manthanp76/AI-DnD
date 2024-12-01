# game_world.py
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import asyncio
import random

from ai.generator import AIGenerator
from core.location import Location
from core.player import Player
from entities.npcs import NPC, NPCFactory, NPCType, NPCBehavior
from entities.items import Item, ItemFactory, ItemType, ItemRarity
from utils.dice import DiceRoller
from audio_system.audio_manager import AudioManager
from audio_system.audio_description import AudioDescription

class GameWorld:
    def __init__(self, audio_manager: Optional[AudioManager] = None):
        self.locations: Dict[str, Location] = {}
        self.player: Optional[Player] = None
        self.game_time = datetime.now()
        self.audio_manager = audio_manager
        
        # Initialize AI Generator
        self.ai_generator = AIGenerator()
        
        self.current_state = {
            'combat_active': False,
            'current_enemy': None,
            'active_events': [],
            'last_action': None,
            'discovered_secrets': set(),
            'time_of_day': 'day',
            'weather': 'clear',
            'atmosphere': 'peaceful'
        }
        
        # Expanded command mappings
        self.command_aliases = {
            # Movement
            'n': 'move north',
            's': 'move south',
            'e': 'move east',
            'w': 'move west',
            'go': 'move',
            'walk': 'move',
            'run': 'move',
            'travel': 'move',
            
            # Combat
            'fight': 'attack',
            'hit': 'attack',
            'strike': 'attack',
            'block': 'defend',
            'parry': 'defend',
            'dodge': 'defend',
            'flee': 'retreat',
            'escape': 'retreat',
            
            # Items
            'get': 'take',
            'grab': 'take',
            'pickup': 'take',
            'collect': 'take',
            'drink': 'use',
            'consume': 'use',
            'equip': 'use',
            'wear': 'use',
            'wield': 'use',
            
            # Exploration
            'l': 'look',
            'x': 'examine',
            'search': 'search',
            'investigate': 'search',
            'inspect': 'examine',
            'study': 'examine',
            'check': 'examine',
            'explore': 'search',
            'probe': 'search',
            
            # Information
            'i': 'inventory',
            'inv': 'inventory',
            'bag': 'inventory',
            'stats': 'status',
            'health': 'status',
            'condition': 'status',
            
            # Interaction
            'talk': 'speak',
            'chat': 'speak',
            'greet': 'speak',
            'push': 'interact',
            'pull': 'interact',
            'touch': 'interact',
            'open': 'interact',
            'close': 'interact'
        }

    def _add_starter_items(self, location: Location) -> None:
        """Add initial items to starting location"""
        # Create health potion with proper healing effect
        health_potion = ItemFactory.create_healing_potion(
            name="Health Potion",
            heal_amount=20
        )
        
        # Create wooden sword with proper damage boost
        wooden_sword = ItemFactory.create_weapon(
            name="Wooden Sword",
            damage_bonus=2
        )
        
        # Add items to location
        location.add_item(health_potion)
        location.add_item(wooden_sword)

    async def generate_starting_location(self) -> Optional[Location]:
        """Generate the starting area"""
        try:
            # Rich parameters for the AI generator
            params = {
                'type': 'starting_area',
                'theme': 'welcoming',
                'purpose': 'introduction',
                'player_level': 1,
                'game_state': {
                    'time_of_day': self.current_state['time_of_day'],
                    'weather': self.current_state['weather'],
                    'atmosphere': self.current_state['atmosphere']
                }
            }
            
            location_data = await self.ai_generator.generate_content(
                'location_description',
                params
            )
            
            # Create the location with rich detail
            starting_location = Location(
                id="starting_area",
                name=location_data.get('name', 'The Tranquil Grove'),
                description="""You find yourself in a serene clearing called Tranquil Haven. 
                The air is filled with the gentle rustle of leaves as golden sunlight filters through 
                the emerald canopy above. A crystal-clear stream meanders through the area, its waters 
                catching the light like scattered diamonds. Ancient stone markers hint at long-forgotten 
                paths, while the sweet scent of wildflowers fills the air.""",
                theme=location_data.get('theme', 'peaceful sanctuary'),
                features=[
                    'Ancient guardian trees',
                    'Crystal-clear stream',
                    'Blooming wildflowers',
                    'Mysterious stone markers',
                    'Dappled sunlight patterns'
                ],
                atmosphere="A sense of peace and possibility fills this tranquil sanctuary."
            )
            
            # Add starter items using the updated method
            self._add_starter_items(starting_location)
            
            # Add searchable features
            self._add_searchable_features(starting_location)
            
            # Add initial exits
            starting_location.add_exit('north', 'forest_path')
            starting_location.add_exit('east', 'river_crossing')
            
            # Add some secrets
            starting_location.add_secret(
                'ancient_runes',
                'The stone markers bear faint magical runes that seem to pulse with energy.'
            )
            
            self.locations["starting_area"] = starting_location
            return starting_location
                
        except Exception as e:
            logging.error(f"Error generating starting location: {e}")
            return self._create_fallback_location()  # Remove parameters here
        
    def _add_searchable_features(self, location: Location) -> None:
        """Add searchable elements to features"""
        location.add_searchable_feature(
            "Ancient guardian trees",
            [
                "The bark bears strange symbols that seem to shift when you're not looking directly at them.",
                "There's a small hollow near the base that might hide something."
            ]
        )
        
        location.add_searchable_feature(
            "Crystal-clear stream",
            [
                "Sunlight reflects off something shiny beneath the water's surface.",
                "The water seems to whisper ancient secrets as it flows past."
            ]
        )
        
        location.add_searchable_feature(
            "Mysterious stone markers",
            [
                "The stones are covered in ancient runes that pulse with a faint blue light.",
                "Some of the markings seem to form a map or diagram."
            ]
        )

    def _create_fallback_location(self, location_id: str = "starting_area", direction: str = "north") -> Location:
        """Create a basic location if generation fails"""
        location = Location(
            id=location_id,
            name="Tranquil Haven",
            description="""A peaceful clearing surrounded by ancient trees. A gentle breeze carries 
            the scent of wildflowers, and sunlight filters through the canopy above.""",
            theme="peaceful",
            features=["Ancient trees", "Wildflowers", "Stone path"],
            atmosphere="A sense of tranquility fills this place."
        )
        
        # Add basic exits
        location.add_exit('north', 'forest_path')
        location.add_exit('east', 'river_crossing')
        
        # Add starter items
        self._add_starter_items(location)
        
        return location

    async def create_location(self, id: str, name: str, description: str, 
                            theme: str, features: List[str], 
                            atmosphere: str) -> Location:
        """Create a new location with the given parameters"""
        location = Location(
            id=id,
            name=name,
            description=description,
            theme=theme,
            features=features,
            atmosphere=atmosphere
        )
        
        # Store the location
        self.locations[id] = location
        return location
        
    # Add this method to the GameWorld class

    async def _initiate_combat(self, target_name: str, location: Location) -> Dict:
        """Start combat with an NPC"""
        try:
            if not target_name:
                return {
                    'message': "What do you want to attack?",
                    'next_situation': 'exploration'
                }

            # Find target NPC
            npc = location.get_npc(target_name)
            if not npc:
                return {
                    'message': f"You don't see {target_name} here to attack.",
                    'next_situation': 'exploration'
                }

            if npc.is_defeated:
                return {
                    'message': f"{npc.name} has already been defeated.",
                    'next_situation': 'exploration'
                }

            # Initialize combat state
            self.current_state['combat_active'] = True
            self.current_state['current_enemy'] = npc

            # Initial combat description
            combat_text = [
                f"\nCombat begins with {npc.name}!",
                f"Your HP: {self.player.hp}/{self.player.max_hp}",
                f"{npc.name}'s HP: {npc.hp}/{npc.max_hp}"
            ]

            # Player's attack
            damage = self.player.attack()
            npc.take_damage(damage)
            combat_text.append(f"You strike {npc.name} for {damage} damage!")

            if npc.is_defeated:
                # Calculate XP reward
                xp_gained = NPCFactory.calculate_xp_reward(npc)
                level_up = self.player.add_xp(xp_gained)
                
                combat_text.extend([
                    f"{npc.name} has been defeated!",
                    f"You gain {xp_gained} XP!"
                ])
                
                if level_up:
                    combat_text.append(f"Level Up! You are now level {self.player.level}!")

                self.current_state['combat_active'] = False
                self.current_state['current_enemy'] = None
                return {
                    'message': "\n".join(combat_text),
                    'next_situation': 'exploration'
                }

            # Enemy counter-attack
            damage, was_critical = npc.attack()
            if was_critical:
                combat_text.append(f"CRITICAL HIT! {npc.name} strikes you for {damage} damage!")
            else:
                combat_text.append(f"{npc.name} counter-attacks for {damage} damage!")
            
            self.player.take_damage(damage)

            if self.player.hp <= 0:
                combat_text.append("You have been defeated!")
                return {
                    'message': "\n".join(combat_text),
                    'next_situation': 'game_over'
                }

            # Show combat status
            combat_text.extend([
                f"\nYour HP: {self.player.hp}/{self.player.max_hp}",
                f"{npc.name}'s HP: {npc.hp}/{npc.max_hp}",
                "\nAvailable combat commands:",
                "- attack: Strike your opponent",
                "- defend: Take a defensive stance (reduces damage)",
                "- use [item]: Use an item from your inventory",
                "- retreat: Try to flee from combat"
            ])

            return {
                'message': "\n".join(combat_text),
                'next_situation': 'combat'
            }

        except Exception as e:
            logging.error(f"Error initiating combat: {e}")
            return {
                'message': "Something went wrong trying to start combat.",
                'next_situation': 'exploration'
            }

    async def _handle_combat_action(self, command: str) -> Dict:
        """Handle combat actions with sound effects"""
        try:
            enemy = self.current_state.get('current_enemy')
            if not enemy:
                self.current_state['combat_active'] = False
                return {
                    'message': "No enemy to fight.",
                    'next_situation': 'exploration'
                }

            combat_text = []
            result = {
                'message': '',
                'next_situation': 'combat',
                'combat_effect': None
            }

            # Handle equipment and item use during combat
            if command.startswith('use'):
                item_name = command[4:].strip()
                for item in self.player.inventory:
                    if item.name.lower() == item_name.lower():
                        # Handle equipment items
                        if item.item_type in [ItemType.WEAPON, ItemType.ARMOR]:
                            equip_result = self.player.equip_item(item)
                            combat_text.append(equip_result['message'])
                            result['combat_effect'] = 'equip_weapon' if item.item_type == ItemType.WEAPON else 'equip_armor'
                            result['message'] = '\n'.join(combat_text)
                            return result
                        # Handle consumable items
                        else:
                            use_result = item.use(self.player, None)
                            if use_result['success']:
                                self.player.remove_item(item.id)
                                combat_text.append(use_result['message'])
                                result['combat_effect'] = 'potion_use' if 'potion' in item.name.lower() else 'item_use'
                                enemy_attack = True

            elif command == "attack":
                # Player attack
                damage = self.player.attack()
                enemy.take_damage(damage)
                combat_text.append(f"You strike {enemy.name} for {damage} damage!")
                
                # Add appropriate combat sound effect
                if damage > 0:
                    result['combat_effect'] = 'sword_hit'
                    if damage >= self.player.attack_power * 1.5:  # Critical hit
                        result['combat_effect'] = 'critical_hit'
                else:
                    result['combat_effect'] = 'sword_miss'

                if enemy.is_defeated:
                    xp_gained = NPCFactory.calculate_xp_reward(enemy)
                    level_up = self.player.add_xp(xp_gained)
                    
                    combat_text.extend([
                        f"{enemy.name} has been defeated!",
                        f"You gain {xp_gained} XP!"
                    ])
                    
                    if level_up:
                        combat_text.append(f"Level Up! You are now level {self.player.level}!")
                        result['combat_effect'] = 'level_up'
                    else:
                        result['combat_effect'] = 'monster_die'

                    self.current_state['combat_active'] = False
                    self.current_state['current_enemy'] = None
                    result['message'] = "\n".join(combat_text)
                    result['next_situation'] = 'exploration'
                    return result

            elif command == "defend":
                self.player.add_status_effect('defending', 1)
                combat_text.append("You take a defensive stance!")
                result['combat_effect'] = 'shield_block'
                enemy_attack = True

            elif command == "retreat":
                # 50% chance to retreat successfully
                if random.random() < 0.5:
                    combat_text.append("You successfully retreat from combat!")
                    result['combat_effect'] = 'retreat_success'
                    self.current_state['combat_active'] = False
                    self.current_state['current_enemy'] = None
                    result['message'] = "\n".join(combat_text)
                    result['next_situation'] = 'exploration'
                    return result
                else:
                    combat_text.append("You fail to retreat!")
                    result['combat_effect'] = 'retreat_fail'
                    enemy_attack = True

            else:
                combat_text.append("Invalid combat command!")
                enemy_attack = True

            # Enemy turn
            if enemy_attack:
                damage, was_critical = enemy.attack()
                
                # Apply defensive stance reduction
                if 'defending' in self.player.status_effects:
                    damage = max(1, damage // 2)
                    combat_text.append("Your defensive stance reduces the damage!")
                
                if was_critical:
                    combat_text.append(f"CRITICAL HIT! {enemy.name} strikes you for {damage} damage!")
                    result['combat_effect'] = 'player_hit_critical'
                else:
                    combat_text.append(f"{enemy.name} attacks for {damage} damage!")
                    result['combat_effect'] = 'player_hit'
                    
                self.player.take_damage(damage)

                if self.player.hp <= 0:
                    combat_text.extend([
                        "You have been defeated!",
                        "Your journey ends here..."
                    ])
                    result['combat_effect'] = 'player_die'
                    result['message'] = "\n".join(combat_text)
                    result['next_situation'] = 'game_over'
                    return result

            # Update status
            combat_text.extend([
                f"\nYour HP: {self.player.hp}/{self.player.max_hp}",
                f"{enemy.name}'s HP: {enemy.hp}/{enemy.max_hp}",
                "\nAvailable combat commands:",
                "- attack: Strike your opponent",
                "- defend: Take a defensive stance (reduces damage)",
                "- use [item]: Use an item from your inventory",
                "- retreat: Try to flee from combat"
            ])

            result['message'] = "\n".join(combat_text)
            return result

        except Exception as e:
            logging.error(f"Error in combat: {e}")
            return {
                'message': "Something went wrong during combat.",
                'next_situation': 'exploration'
            }

    async def _populate_location(self, location: Location, params: Dict) -> None:
        """Add NPCs, items, and other content to a location"""
        try:
            # Get population data from AI
            population_data = await self.ai_generator.generate_content(
                'location_population',
                params
            )
            
            if not population_data:
                return
                
            # Add NPCs
            if 'npcs' in population_data:
                for npc_data in population_data['npcs']:
                    # Create appropriate NPC based on location theme and player level
                    location_difficulty = 'dangerous' if any(
                        word in location.theme.lower() 
                        for word in ['dark', 'evil', 'shadow', 'danger']
                    ) else 'normal'
                    
                    npc = NPCFactory.create_combat_npc(
                        name=npc_data.get('name', 'Unknown Entity'),
                        description=npc_data.get('description', 'A mysterious figure.'),
                        player_level=self.player.level if self.player else 1,
                        location_theme=location_difficulty
                    )
                    location.add_npc(npc)
            
            # Add items
            if 'items' in population_data:
                for item_data in population_data['items']:
                    item_type = item_data.get('type', 'treasure')
                    effect_value = item_data.get('effect_value', 0)
                    
                    # Scale effect value based on player level
                    if self.player:
                        effect_value = max(effect_value, self.player.level * 2)
                    
                    item = ItemFactory.create_item(
                        name=item_data.get('name', 'Mysterious Item'),
                        item_type=item_type,
                        effect_value=effect_value
                    )
                    
                    # 30% chance for items to be hidden
                    if random.random() < 0.3:
                        location.add_hidden_item(item)
                    else:
                        location.add_item(item)
            
            # Add searchable features
            for feature in location.features:
                if random.random() < 0.4:  # 40% chance for each feature
                    discoveries = [
                        f"You notice something interesting about the {feature.lower()}.",
                        f"There might be more to discover about the {feature.lower()}."
                    ]
                    location.add_searchable_feature(feature, discoveries)
                    
            # Add a guaranteed potion in dangerous areas
            if any(word in location.theme.lower() for word in ['dark', 'evil', 'shadow', 'danger']):
                health_potion = ItemFactory.create_healing_potion(
                    name="Health Potion",
                    heal_amount=20 * (self.player.level if self.player else 1)
                )
                if random.random() < 0.3:  # 30% chance to be hidden
                    location.add_hidden_item(health_potion)
                else:
                    location.add_item(health_potion)

        except Exception as e:
            logging.error(f"Error populating location: {e}")
            
    async def handle_player_action(self, action: Dict) -> Dict:
        """Handle player actions with sound effects"""
        try:
            command = action['command'].lower()
            current_location = self.locations.get(self.player.current_location_id)
            
            if not current_location:
                return {
                    'message': "Error: Location not found",
                    'next_situation': 'exploration'
                }

            result = {
                'message': '',
                'next_situation': 'exploration',
                'sound_effect': None,
                'new_location': False
            }

            # Handle combat initiation
            if command.startswith('attack'):
                target_name = command[7:].strip()
                combat_result = await self._initiate_combat(target_name, current_location)
                combat_result['sound_effect'] = 'combat_start'
                return combat_result

            # Parse command parts
            parts = command.split(' ', 1)
            base_command = parts[0]
            argument = parts[1] if len(parts) > 1 else ''

            # Handle movement
            if command.startswith('move'):
                move_result = await self._handle_movement(argument, current_location)
                if move_result.get('next_situation') == 'exploration':
                    move_result['sound_effect'] = 'footsteps'
                    if argument.lower() in current_location.exits:
                        move_result['new_location'] = True
                return move_result

            # Handle item taking
            elif command.startswith('take'):
                take_result = await self._handle_item_take(argument, current_location)
                if take_result.get('message', '').startswith('You pick up'):
                    take_result['sound_effect'] = 'item_pickup'
                return take_result

            # Handle item usage
            elif command.startswith('use'):
                use_result = await self._handle_item_use(argument, current_location)
                if use_result.get('success', False):
                    if 'potion' in argument.lower():
                        use_result['sound_effect'] = 'potion_use'
                    elif 'weapon' in argument.lower():
                        use_result['sound_effect'] = 'equip_weapon'
                    elif 'armor' in argument.lower():
                        use_result['sound_effect'] = 'equip_armor'
                    else:
                        use_result['sound_effect'] = 'item_use'
                return use_result

            # Handle inventory
            elif command == 'inventory':
                inv_result = await self._handle_inventory(argument, current_location)
                inv_result['sound_effect'] = 'menu_open'
                return inv_result

            # Handle examination
            elif command.startswith(('examine', 'look')):
                examine_result = await self._handle_examine(argument, current_location)
                examine_result['sound_effect'] = 'examine'
                return examine_result

            # Handle searching
            elif command.startswith('search'):
                search_result = await self._handle_search(argument, current_location)
                search_result['sound_effect'] = 'search'
                if 'find' in search_result.get('message', '').lower():
                    search_result['sound_effect'] = 'item_discover'
                return search_result

            # Handle special interactions
            elif command.startswith(('talk', 'speak')):
                interaction_result = await self._handle_dialog(argument, current_location)
                interaction_result['sound_effect'] = 'dialog'
                return interaction_result

            # Generate response for other actions
            result = await self._generate_action_response(command, current_location)
            result['sound_effect'] = 'action_generic'
            return result

        except Exception as e:
            logging.error(f"Error handling action: {e}")
            return {
                'message': "Something went wrong with that action.",
                'next_situation': 'exploration'
            }
                
    def _end_combat(self) -> None:
        """Clean up combat state"""
        self.current_state['combat_active'] = False
        self.current_state['current_enemy'] = None
    
    async def _generate_location(self, location_id: str, direction: str) -> Optional[Location]:
        """Generate a new location based on the direction of travel"""
        try:
            # Determine location type and theme based on direction/existing locations
            location_types = {
                'north': ['forest', 'mountains', 'hills'],
                'south': ['valley', 'plains', 'swamp'],
                'east': ['river', 'lake', 'cliffs'],
                'west': ['caves', 'ruins', 'canyon']
            }
            
            # Get potential types for this direction
            potential_types = location_types.get(direction, ['wilderness'])
            location_type = random.choice(potential_types)
            
            # Generate rich parameters for the AI generator
            params = {
                'type': location_type,
                'theme': self._get_location_theme(direction, location_type),
                'purpose': 'exploration',
                'player_level': self.player.level if self.player else 1,
                'game_state': {
                    'time_of_day': self.current_state['time_of_day'],
                    'weather': self.current_state['weather'],
                    'atmosphere': self.current_state['atmosphere']
                }
            }
            
            # Generate base location description
            location_data = await self.ai_generator.generate_content(
                'location_description',
                params
            )
            
            if not location_data:
                raise ValueError("Failed to generate location data")
            
            # Create new location with generated data
            new_location = Location(
                id=location_id,
                name=location_data.get('name', f"New {location_type.title()} Area"),
                description=location_data.get('description', "You enter a new area."),
                theme=location_data.get('theme', 'wilderness'),
                features=location_data.get('features', ['path']),
                atmosphere=location_data.get('atmosphere', 'The area feels mysterious.')
            )
            
            # Add appropriate exits
            opposite_directions = {
                'north': 'south',
                'south': 'north',
                'east': 'west',
                'west': 'east'
            }
            
            # Always add return path
            if direction in opposite_directions:
                new_location.add_exit(
                    opposite_directions[direction],
                    self.player.current_location_id if self.player else "starting_area"
                )
            
            # Add some random additional exits
            possible_exits = [d for d in ['north', 'south', 'east', 'west']
                            if d != opposite_directions.get(direction)]
            for _ in range(random.randint(1, 2)):  # 1-2 additional exits
                if possible_exits:
                    exit_dir = random.choice(possible_exits)
                    possible_exits.remove(exit_dir)
                    new_location.add_exit(exit_dir, f"{location_type}_{exit_dir}")
            
            # Generate and add content
            await self._populate_location(new_location, params)
            
            # Store the new location
            self.locations[location_id] = new_location
            return new_location
            
        except Exception as e:
            logging.error(f"Error generating location: {e}")
            return self._create_fallback_location(location_id, direction)

    def _get_location_theme(self, direction: str, location_type: str) -> str:
        """Determine appropriate theme for new location"""
        themes = {
            'forest': ['mystical', 'dark', 'enchanted', 'ancient'],
            'mountains': ['rugged', 'snowy', 'treacherous', 'majestic'],
            'valley': ['peaceful', 'fertile', 'sheltered', 'wild'],
            'river': ['flowing', 'dangerous', 'life-giving', 'mysterious'],
            'caves': ['dark', 'echoing', 'crystal-filled', 'abandoned'],
            'ruins': ['crumbling', 'haunted', 'overgrown', 'ancient'],
            'plains': ['windswept', 'vast', 'rolling', 'untamed'],
            'swamp': ['murky', 'dangerous', 'primordial', 'mysterious'],
        }
        
        return random.choice(
            themes.get(location_type, ['mysterious', 'untamed', 'wild', 'ancient'])
        )

    def _create_fallback_location(self, location_id: str, direction: str) -> Location:
        """Create a basic location if generation fails"""
        opposite_directions = {
            'north': 'south',
            'south': 'north',
            'east': 'west',
            'west': 'east'
        }
        
        location = Location(
            id=location_id,
            name="Mysterious Area",
            description="You enter a mysterious area shrouded in uncertainty.",
            theme="mysterious",
            features=["path", "strange markings"],
            atmosphere="The air is thick with anticipation."
        )
        
        # Add return path
        if direction in opposite_directions:
            location.add_exit(
                opposite_directions[direction],
                self.player.current_location_id if self.player else "starting_area"
            )
        
        self.locations[location_id] = location
        return location
        
    async def _handle_inventory(self, argument: str, location: Location) -> Dict:
        """Handle inventory display and management"""
        try:
            if not self.player:
                return {
                    'message': "Error: No player found.",
                    'next_situation': 'exploration'
                }

            # Get basic inventory list
            inventory_lines = ["Your inventory:"]
            
            if not self.player.inventory:
                inventory_lines.append("You aren't carrying anything.")
            else:
                # Group items by type
                items_by_type = {}
                for item in self.player.inventory:
                    item_type = item.item_type.value
                    if item_type not in items_by_type:
                        items_by_type[item_type] = []
                    items_by_type[item_type].append(item)

                # Display items by type
                for item_type, items in items_by_type.items():
                    inventory_lines.append(f"\n{item_type.title()}:")
                    for item in items:
                        # Show item details
                        details = []
                        if hasattr(item, 'effect_value') and item.effect_value:
                            details.append(f"Power: {item.effect_value}")
                        if hasattr(item, 'uses_remaining') and item.uses_remaining is not None:
                            details.append(f"Uses: {item.uses_remaining}")
                        
                        item_line = f"  - {item.name}"
                        if details:
                            item_line += f" ({', '.join(details)})"
                        if hasattr(item, 'is_used') and item.is_used:
                            item_line += " [used]"
                        inventory_lines.append(item_line)

            # Add equipped items section if relevant
            equipped_items = []
            if 'equipped_weapon' in self.player.attributes:
                weapon = self.player.attributes['equipped_weapon']
                equipped_items.append(f"Weapon: {weapon.name}")
            if 'equipped_armor' in self.player.attributes:
                armor = self.player.attributes['equipped_armor']
                equipped_items.append(f"Armor: {armor.name}")

            if equipped_items:
                inventory_lines.append("\nEquipped:")
                inventory_lines.extend([f"  - {item}" for item in equipped_items])

            # Add basic stats
            inventory_lines.append("\nCarrying Capacity:")
            inventory_lines.append(f"  Items: {len(self.player.inventory)}")

            return {
                'message': "\n".join(inventory_lines),
                'next_situation': 'exploration'
            }

        except Exception as e:
            logging.error(f"Error handling inventory: {e}")
            return {
                'message': "There was a problem checking your inventory.",
                'next_situation': 'exploration'
            }

    async def _handle_examine(self, target: str, location: Location) -> Dict:
        """Handle examine/look actions with rich detail"""
        try:
            # If no target, describe the whole location
            if not target or target.lower() == "around":
                return {
                    'message': location.get_current_description(),
                    'next_situation': 'exploration'
                }

            # Clean up target text
            target = target.lower().strip()
            
            # Remove common prefixes that might be in the command
            for prefix in ['at ', 'the ', 'around ', 'about ']:
                if target.startswith(prefix):
                    target = target[len(prefix):]

            # Check for items first
            item = location.get_item(target)
            if item:
                return {
                    'message': self._generate_item_examination(item),
                    'next_situation': 'exploration'
                }

            # Check for NPCs
            npc = location.get_npc(target)
            if npc:
                return {
                    'message': self._generate_npc_examination(npc),
                    'next_situation': 'exploration'
                }

            # Check for features (now with better partial matching)
            feature_found = None
            for feature in location.features:
                # Try to match feature names more flexibly
                if (target in feature.lower() or 
                    feature.lower() in target or 
                    any(word in feature.lower() for word in target.split())):
                    feature_found = feature
                    break

            if feature_found:
                feature_desc = location.get_feature_description(feature_found)
                if feature_desc:
                    params = {
                        'target': feature_found,
                        'location': location.get_state(),
                        'player': self.player.get_state(),
                        'discovered_secrets': list(self.current_state['discovered_secrets'])
                    }
                    
                    examine_result = await self.ai_generator.generate_content(
                        'examine_response',
                        params
                    )
                    
                    if isinstance(examine_result, dict):
                        # Handle any new secrets discovered
                        if 'secrets' in examine_result:
                            for secret in examine_result['secrets']:
                                self.current_state['discovered_secrets'].add(secret)
                                
                        return {
                            'message': examine_result.get('description', feature_desc),
                            'next_situation': 'exploration'
                        }
                    
                    return {
                        'message': feature_desc,
                        'next_situation': 'exploration'
                    }

            # If we get here, nothing was found to examine
            return {
                'message': f"You don't see {target} here to examine.",
                'next_situation': 'exploration'
            }

        except Exception as e:
            logging.error(f"Error during examination: {e}")
            return {
                'message': f"You try to examine {target if target else 'the area'} but something distracts you.",
                'next_situation': 'exploration'
            }

    async def _handle_search(self, area: str, location: Location) -> Dict:
        """Handle search actions with detailed results"""
        try:
            # Clean up area text
            if area:
                area = area.lower().strip()
                for prefix in ['in ', 'at ', 'the ', 'around ', 'about ']:
                    if area.startswith(prefix):
                        area = area[len(prefix):]

            # If searching specific area/feature
            if area:
                # More flexible feature matching
                feature_matches = []
                for feature in location.features:
                    if (area in feature.lower() or 
                        feature.lower() in area or 
                        any(word in feature.lower() for word in area.split())):
                        feature_matches.append(feature)
                    
                if not feature_matches:
                    return {
                        'message': f"You don't see {area} here to search.",
                        'next_situation': 'exploration'
                    }

                feature = feature_matches[0]
                search_result = location.search_feature(feature)
                
                if search_result:
                    messages = []
                    if search_result['found_items']:
                        for item in search_result['found_items']:
                            messages.append(f"You find {item.name}!")
                    
                    messages.extend(search_result['discoveries'])
                    
                    return {
                        'message': f"You carefully search the {feature}.\n" + 
                                "\n".join(messages),
                        'next_situation': 'exploration'
                    }

            # Generate thorough search results for the general area
            params = {
                'location': location.get_state(),
                'player': self.player.get_state(),
                'area': area if area else 'the area',
                'discovered_secrets': list(self.current_state['discovered_secrets'])
            }

            search_result = await self.ai_generator.generate_content(
                'search_response',
                params
            )
            
            if isinstance(search_result, dict):
                # Handle any discoveries
                if 'discoveries' in search_result:
                    for discovery in search_result['discoveries']:
                        if discovery['type'] == 'item':
                            new_item = ItemFactory.create_item(
                                discovery['name'],
                                discovery.get('item_type', 'treasure'),
                                discovery.get('effect_value', 0)
                            )
                            location.add_item(new_item)
                        elif discovery['type'] == 'secret':
                            self.current_state['discovered_secrets'].add(
                                discovery['description']
                            )

                return {
                    'message': search_result.get('description',
                        """As you search carefully, you notice:
                        - The way the light creates interesting patterns
                        - Subtle sounds that weren't apparent before
                        - Various small details about your surroundings"""),
                    'next_situation': 'exploration'
                }

            return {
                'message': "You search but find nothing unusual.",
                'next_situation': 'exploration'
            }

        except Exception as e:
            logging.error(f"Error during search: {e}")
            return {
                'message': "You search but find nothing unusual.",
                'next_situation': 'exploration'
            }

    async def _handle_special_location_interaction(self, command: str, location: Location) -> Dict:
        """Handle interactions with special locations like ruins, caves, etc."""
        # Extract the target location from command
        target = ' '.join(command.split()[1:])  # Remove the action word
        
        # Check if this is a special feature of the current location
        feature_match = None
        for feature in location.features:
            if any(word.lower() in feature.lower() for word in target.split()):
                feature_match = feature
                break
                
        if not feature_match:
            return {
                'message': f"You don't see {target} here to explore.",
                'next_situation': 'exploration'
            }
            
        # Generate specific interaction based on feature type
        if 'ruins' in feature_match.lower():
            params = {
                'feature': feature_match,
                'location': location.get_state(),
                'player': self.player.get_state(),
                'interaction_type': 'explore'
            }
            
            response = await self.ai_generator.generate_content(
                'feature_interaction',
                params
            )
            
            # Check if this should generate a new sub-location
            if response.get('create_sublocation', False):
                new_location = await self._generate_sublocation(
                    feature_match,
                    response.get('sublocation_type', 'ruins'),
                    location.id
                )
                
                if new_location:
                    self.player.current_location_id = new_location.id
                    return {
                        'message': f"You carefully make your way into {feature_match}.\n\n" + 
                                 new_location.get_current_description(),
                        'next_situation': 'exploration'
                    }
            
            return {
                'message': response.get('description', f"You explore {feature_match} but find nothing unusual."),
                'next_situation': 'exploration'
            }
            
        # Handle other special features (caves, towers, etc.)
        return {
            'message': f"You carefully approach {feature_match}, studying its ancient secrets.",
            'next_situation': 'exploration'
        }
    
    def _parse_command(self, raw_command: str) -> str:
        """Enhanced command parser with better natural language understanding"""
        command = raw_command.lower().strip()
        words = command.split()
        
        if not words:
            return ""

        # Handle movement variations
        movement_words = ['go', 'move', 'walk', 'travel', 'head', 'proceed']
        direction_words = ['north', 'south', 'east', 'west', 'n', 's', 'e', 'w']
        location_markers = ['to', 'towards', 'into', 'inside']
        
        if any(word in words for word in movement_words):
            # Extract direction or location
            for i, word in enumerate(words):
                if word in direction_words:
                    return f"move {word}"
                if word in location_markers and i + 1 < len(words):
                    target = ' '.join(words[i+1:])
                    return f"explore {target}"
            
        # Handle exploration and interaction
        if words[0] in ['explore', 'enter', 'investigate', 'approach']:
            return f"explore {' '.join(words[1:])}"
            
        if words[0] in ['search', 'examine', 'inspect', 'study']:
            return f"examine {' '.join(words[1:])}"
            
        if words[0] in ['talk', 'speak', 'ask']:
            return f"talk {' '.join(words[1:])}"

        # Return original if no special handling needed
        return command

    async def _handle_location_interaction(self, command: str, location: Location) -> Dict:
        """Handle natural movement and location exploration"""
        words = command.split()
        target = ' '.join(words[1:]) if len(words) > 1 else ''
        
        # Check if target is a known location feature
        feature_match = None
        for feature in location.features:
            if any(word.lower() in feature.lower() for word in target.split()):
                feature_match = feature
                break
                
        if feature_match:
            # Generate interaction for the feature
            params = {
                'feature': feature_match,
                'location': location.get_state(),
                'player_state': self.player.get_state()
            }
            
            response = await self.ai_generator.generate_content(
                'feature_interaction',
                params
            )
            
            # Handle possible sublocation creation
            if 'enter' in command.lower() or 'explore' in command.lower():
                sublocation = await self._create_sublocation(feature_match, location)
                if sublocation:
                    self.player.current_location_id = sublocation.id
                    return {
                        'message': f"You enter {feature_match}.\n\n{sublocation.get_current_description()}",
                        'next_situation': 'exploration'
                    }
            
            return {
                'message': response.get('description', f"You examine {feature_match} more closely."),
                'next_situation': 'exploration'
            }
            
        # Check if target is a location name or direction
        directions = ['north', 'south', 'east', 'west']
        for direction in directions:
            if direction in target.lower():
                if direction in location.exits:
                    return await self._handle_movement(direction, location)
                else:
                    return {
                        'message': f"You cannot go {direction} from here.",
                        'next_situation': 'exploration'
                    }

        return {
            'message': f"You don't see {target} here to explore.",
            'next_situation': 'exploration'
        }

    async def _create_sublocation(self, feature: str, parent_location: Location) -> Optional[Location]:
        """Create a sub-location for explorable features"""
        sublocation_id = f"{parent_location.id}_{feature.lower().replace(' ', '_')}"
        
        params = {
            'parent_location': parent_location.get_state(),
            'feature': feature,
            'player_level': self.player.level
        }
        
        generation = await self.ai_generator.generate_content(
            'sublocation_generation',
            params
        )
        
        if not generation:
            return None
            
        sublocation = Location(
            id=sublocation_id,
            name=generation.get('name', f"Inside {feature}"),
            description=generation.get('description', "You enter a mysterious area."),
            theme=generation.get('theme', 'mysterious'),
            features=generation.get('features', []),
            atmosphere=generation.get('atmosphere', "The air feels different here.")
        )
        
        # Add exit back to parent location
        sublocation.add_exit('back', parent_location.id)
        
        self.locations[sublocation_id] = sublocation
        return sublocation

    async def _generate_sublocation(self, feature_name: str, 
                                  location_type: str, 
                                  parent_id: str) -> Optional[Location]:
        """Generate a new sublocation when exploring special features"""
        try:
            params = {
                'parent_location': self.locations[parent_id].get_state(),
                'feature_name': feature_name,
                'location_type': location_type,
                'player_level': self.player.level if self.player else 1
            }
            
            location_data = await self.ai_generator.generate_content(
                'sublocation_generation',
                params
            )
            
            if not location_data:
                return None
                
            sublocation_id = f"{parent_id}_{location_type}_{len(self.locations)}"
            
            new_location = Location(
                id=sublocation_id,
                name=location_data.get('name', f"Inside {feature_name}"),
                description=location_data.get('description', "You enter a mysterious area."),
                theme=location_data.get('theme', 'ancient'),
                features=location_data.get('features', ['crumbling walls', 'ancient symbols']),
                atmosphere=location_data.get('atmosphere', 'The air is thick with history.')
            )
            
            # Add return path to parent location
            new_location.add_exit('back', parent_id)
            
            # Add to world locations
            self.locations[sublocation_id] = new_location
            return new_location
            
        except Exception as e:
            logging.error(f"Error generating sublocation: {e}")
            return None

    def _generate_item_examination(self, item: Item) -> str:
        """Generate detailed item examination description"""
        lines = [f"You examine the {item.name}:"]
        lines.append(item.description)
        
        if item.rarity != ItemRarity.COMMON:
            lines.append(f"This appears to be a {item.rarity.value} item.")
            
        if item.effects:
            effect_descs = [effect.description for effect in item.effects]
            lines.append("Effects: " + ", ".join(effect_descs))
            
        if item.uses_remaining is not None:
            lines.append(f"Uses remaining: {item.uses_remaining}")
            
        return "\n".join(lines)

    async def _handle_item_take(self, item_name: str, location: Location) -> Dict:
        """Handle picking up items"""
        try:
            if not item_name:
                return {
                    'message': "What do you want to take?",
                    'next_situation': 'exploration'
                }

            # Normalize and clean up item name
            item_name = item_name.lower().strip()
            # Remove common prefixes
            for prefix in ['the ', 'a ', 'an ']:
                if item_name.startswith(prefix):
                    item_name = item_name[len(prefix):]

            # Check for visible items with flexible matching
            for item in location.items:
                # Try exact match first
                if item.name.lower() == item_name and not item.is_taken:
                    return self._pick_up_item(item, location)
                    
                # Try partial matches
                if (not item.is_taken and 
                    (item_name in item.name.lower() or 
                    all(word in item.name.lower() for word in item_name.split()))):
                    return self._pick_up_item(item, location)

            return {
                'message': f"You don't see {item_name} here.",
                'next_situation': 'exploration'
            }

        except Exception as e:
            logging.error(f"Error in item take: {e}")
            return {
                'message': "Something went wrong trying to take that item.",
                'next_situation': 'exploration'
            }

    def _pick_up_item(self, item: Item, location: Location) -> Dict:
        """Handle the actual item pickup"""
        item.is_taken = True
        self.player.add_item(item)
        location.items.remove(item)
        
        return {
            'message': f"You pick up the {item.name}.",
            'next_situation': 'exploration'
        }

    # core/game_world.py

    async def _handle_item_use(self, item_name: str, location: Location) -> Dict:
            """Handle using items"""
            try:
                if not item_name:
                    return {
                        'message': "What do you want to use?",
                        'next_situation': 'exploration'
                    }

                # Normalize and clean up item name
                item_name = item_name.lower().strip()
                # Remove common prefixes
                for prefix in ['the ', 'a ', 'an ']:
                    if item_name.startswith(prefix):
                        item_name = item_name[len(prefix):]

                # Check player inventory with flexible matching
                for item in self.player.inventory:
                    # Try exact match first
                    if item.name.lower() == item_name:
                        result = item.use(self.player, location)
                        if result.get('success', False):
                            self.player.remove_item(item.id)
                        return {
                            'message': result.get('message', "You use the item."),
                            'next_situation': 'exploration'
                        }
                        
                    # Try partial matches
                    if (item_name in item.name.lower() or 
                        all(word in item.name.lower() for word in item_name.split())):
                        result = item.use(self.player, location)
                        if result.get('success', False):
                            self.player.remove_item(item.id)
                        return {
                            'message': result.get('message', "You use the item."),
                            'next_situation': 'exploration'
                        }

                return {
                    'message': f"You don't have {item_name} to use.",
                    'next_situation': 'exploration'
                }

            except Exception as e:
                logging.error(f"Error in item use: {e}")
                return {
                    'message': "Something went wrong trying to use that item.",
                    'next_situation': 'exploration'
                }

    async def _use_item(self, item: Item, location: Location) -> Dict:
        """Handle specific item usage with special cases"""
        # Special case for Whispering Waterskin
        if item.name == "Whispering Waterskin":
            result = {
                'success': True,
                'message': """You uncork the Whispering Waterskin and take a sip. 
                The water inside tastes crisp and refreshing, with a hint of magic. 
                You feel a surge of energy and your mind becomes clearer. 
                (Restored 15 HP and gained Water Breathing for 10 minutes)"""
            }
            self.player.heal(15)
            self.player.add_status_effect("water_breathing", 10)  # 10 rounds
            self.player.remove_item(item.id)
            return {
                'message': result['message'],
                'next_situation': 'exploration'
            }

        # Handle standard item use
        result = item.use(self.player, location)
        if result.get('success', False):
            self.player.remove_item(item.id)
        return {
            'message': result.get('message', "You use the item."),
            'next_situation': 'exploration'
        }

    def _generate_npc_examination(self, npc: NPC) -> str:
        """Generate detailed NPC examination description"""
        lines = [f"You observe {npc.name}:"]
        lines.append(npc.description)
        
        if npc.is_defeated:
            lines.append("They have been defeated.")
        else:
            health_status = "healthy" if npc.hp > npc.max_hp * 0.7 else \
                        "injured" if npc.hp > npc.max_hp * 0.3 else \
                        "badly wounded"
            lines.append(f"They appear to be {health_status}.")
            
        if npc.behavior != NPCBehavior.PASSIVE:
            lines.append(f"Their behavior seems {npc.behavior.value}.")
            
        return "\n".join(lines)

    def _generate_item_examination(self, item: Item) -> str:
        """Generate detailed item examination description"""
        lines = [f"You examine the {item.name}:"]
        lines.append(item.description)
        
        if item.rarity != ItemRarity.COMMON:
            lines.append(f"This appears to be a {item.rarity.value} item.")
            
        if item.effects:
            effect_descs = [effect.description for effect in item.effects]
            lines.append("Effects: " + ", ".join(effect_descs))
            
        if item.uses_remaining is not None:
            lines.append(f"Uses remaining: {item.uses_remaining}")
            
        return "\n".join(lines)

    def _generate_npc_examination(self, npc: NPC) -> str:
        """Generate detailed NPC examination description"""
        lines = [f"You observe {npc.name}:"]
        lines.append(npc.description)
        
        if npc.is_defeated:
            lines.append("They have been defeated.")
        else:
            health_status = "healthy" if npc.hp > npc.max_hp * 0.7 else \
                          "injured" if npc.hp > npc.max_hp * 0.3 else \
                          "badly wounded"
            lines.append(f"They appear to be {health_status}.")
            
        if npc.behavior != NPCBehavior.PASSIVE:
            lines.append(f"Their behavior seems {npc.behavior.value}.")
            
        return "\n".join(lines)

    async def _handle_movement(self, direction: str, location: Location) -> Dict:
        """Handle player movement between locations"""
        direction = direction.lower()
        if direction not in location.exits:
            return {
                'message': f"You cannot go {direction} from here.",
                'next_situation': 'exploration'
            }

        # Check for any movement restrictions
        if not self._can_move(location, direction):
            return {
                'message': self._get_movement_restriction_message(location, direction),
                'next_situation': 'exploration'
            }
            
        new_location_id = location.exits[direction]
        
        # Generate new location if needed
        if new_location_id not in self.locations:
            new_location = await self._generate_location(new_location_id, direction)
            if not new_location:
                return {
                    'message': "Something blocks your path in that direction.",
                    'next_situation': 'exploration'
                }
            
        self.player.current_location_id = new_location_id
        new_location = self.locations[new_location_id]
        
        # Mark as visited and handle any first-time visit events
        was_visited = new_location.visited
        new_location.visited = True
        
        # Get description and any additional messages
        messages = [new_location.get_current_description()]
        
        if not was_visited:
            discovery_message = self._handle_location_discovery(new_location)
            if discovery_message:
                messages.append(discovery_message)
        
        return {
            'message': "\n\n".join(messages),
            'next_situation': 'exploration'
        }

    def _can_move(self, location: Location, direction: str) -> bool:
        """Check if movement is possible"""
        # Check for locks or barriers
        if location.state_changes.get(f'{direction}_locked', False):
            return False
            
        # Check for status effects that prevent movement
        if 'paralyzed' in self.player.status_effects or \
           'stunned' in self.player.status_effects:
            return False
            
        return True

    def _get_movement_restriction_message(self, location: Location, direction: str) -> str:
        """Get appropriate message for movement restriction"""
        if location.state_changes.get(f'{direction}_locked', False):
            return f"The way {direction} is locked or blocked."
            
        if 'paralyzed' in self.player.status_effects:
            return "You are paralyzed and cannot move!"
            
        if 'stunned' in self.player.status_effects:
            return "You are too stunned to move right now."
            
        return f"Something prevents you from going {direction}."

    def _handle_location_discovery(self, location: Location) -> Optional[str]:
        """Handle first-time visit to a location"""
        messages = []
        
        # Check for any obvious items
        visible_items = [item for item in location.items if not item.is_taken]
        if visible_items:
            item_names = [item.name for item in visible_items]
            messages.append(f"You notice: {', '.join(item_names)}")
            
        # Check for any obvious features
        if location.features:
            interesting_features = random.sample(
                location.features,
                min(2, len(location.features))
            )
            messages.append(
                f"What catches your eye: {', '.join(interesting_features)}"
            )
            
        return "\n".join(messages) if messages else None

    async def _handle_dialog(self, target: str, location: Location) -> Dict:
        """Handle conversation with NPCs"""
        if not target:
            return {
                'message': "Who do you want to talk to?",
                'next_situation': 'exploration'
            }

        npc = location.get_npc(target)
        if not npc:
            return {
                'message': f"You don't see {target} here to talk to.",
                'next_situation': 'exploration'
            }

        if npc.is_defeated:
            return {
                'message': f"{npc.name} is in no condition to talk.",
                'next_situation': 'exploration'
            }

        params = {
            'npc': npc.get_state(),
            'player': self.player.get_state(),
            'location': location.get_state(),
            'history': []  # Could track conversation history
        }

        dialog_result = await self.ai_generator.generate_content(
            'dialog_response',
            params
        )

        return {
            'message': dialog_result.get('dialog', f"{npc.name} acknowledges your presence."),
            'next_situation': 'dialog'
        }

    async def _handle_interaction(self, target: str, location: Location) -> Dict:
        """Handle interaction with environment"""
        if not target:
            return {
                'message': "What do you want to interact with?",
                'next_situation': 'exploration'
            }

        # Check for feature interactions first
        feature_matches = [f for f in location.features 
                         if target.lower() in f.lower()]
        
        if feature_matches:
            params = {
                'target': feature_matches[0],
                'action': 'interact',
                'location': location.get_state(),
                'player': self.player.get_state()
            }
            
            result = await self.ai_generator.generate_content(
                'action_response',
                params
            )
            
            return {
                'message': result.get('description', f"You interact with {feature_matches[0]} but nothing obvious happens."),
                'next_situation': 'exploration'
            }

        return {
            'message': f"You don't see {target} here to interact with.",
            'next_situation': 'exploration'
        }

    def _handle_status(self, _: str, __: Location) -> Dict:
        """Handle status display"""
        lines = [f"Status of {self.player.name}:"]
        lines.append(f"Health: {self.player.hp}/{self.player.max_hp} HP")
        lines.append(f"Level: {self.player.level} ({self.player.xp} XP)")
        lines.append(f"Attack Power: {self.player.attack_power}")
        lines.append(f"Defense: {self.player.defense}")
        
        if self.player.status_effects:
            lines.append("\nActive Effects:")
            for effect, duration in self.player.status_effects.items():
                lines.append(f"- {effect.title()}: {duration} rounds remaining")
        
        equipped = []
        if 'equipped_weapon' in self.player.attributes:
            equipped.append(f"Weapon: {self.player.attributes['equipped_weapon'].name}")
        if 'equipped_armor' in self.player.attributes:
            equipped.append(f"Armor: {self.player.attributes['equipped_armor'].name}")
            
        if equipped:
            lines.append("\nEquipped Items:")
            lines.extend(equipped)
        
        return {
            'message': "\n".join(lines),
            'next_situation': 'exploration'
        }

    def _format_effect_expiration(self, effects: List[str]) -> str:
        """Format status effect expiration messages"""
        if not effects:
            return ""
            
        if len(effects) == 1:
            return f"The {effects[0]} effect wears off."
            
        effect_list = ", ".join(effects[:-1]) + f" and {effects[-1]}"
        return f"The following effects wear off: {effect_list}."

    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.ai_generator.cleanup()
            self.locations.clear()
            self.current_state = {
                'combat_active': False,
                'current_enemy': None,
                'active_events': [],
                'last_action': None,
                'discovered_secrets': set(),
                'time_of_day': 'day',
                'weather': 'clear',
                'atmosphere': 'peaceful'
            }
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    async def _generate_action_response(self, command: str, location: Location) -> Dict:
        """Generate AI response for unknown or general actions"""
        try:
            # Build action context
            params = {
                'command': command,
                'location': location.get_state(),
                'player': self.player.get_state() if self.player else {},
                'game_state': {
                    'time_of_day': self.current_state['time_of_day'],
                    'weather': self.current_state['weather'],
                    'atmosphere': self.current_state['atmosphere'],
                    'combat_active': self.current_state['combat_active']
                }
            }

            # Generate response from AI
            response = await self.ai_generator.generate_content(
                'action_response',
                params
            )

            # Process AI response
            if isinstance(response, dict):
                # Update game state if needed
                if 'location_changes' in response:
                    for change, value in response['location_changes'].items():
                        location.set_state(change, value)

                return {
                    'message': response.get('description', 'You proceed with your action.'),
                    'next_situation': response.get('next_situation', 'exploration')
                }

            return {
                'message': str(response) if response else 'You proceed with your action.',
                'next_situation': 'exploration'
            }

        except Exception as e:
            logging.error(f"Error generating action response: {e}")
            return {
                'message': f"You try to {command} but nothing obvious happens.",
                'next_situation': 'exploration'
            }

    def _check_for_enemies(self, location: Location) -> Optional[NPC]:
        """Check for hostile NPCs in the area"""
        for npc in location.npcs:
            if npc.npc_type == NPCType.HOSTILE and not npc.is_defeated:
                return npc
        return None

    def _describe_combat_state(self, enemy: NPC) -> str:
        """Get combat status description"""
        if not enemy:
            return ""
            
        enemy_status = "healthy" if enemy.hp > enemy.max_hp * 0.7 else \
                      "injured" if enemy.hp > enemy.max_hp * 0.3 else \
                      "badly wounded"
                      
        player_status = "healthy" if self.player.hp > self.player.max_hp * 0.7 else \
                       "injured" if self.player.hp > self.player.max_hp * 0.3 else \
                       "badly wounded"
                       
        return f"\n{enemy.name} looks {enemy_status}. You are {player_status}."

    def _handle_unknown_command(self, command: str) -> Dict:
        """Handle unknown commands gracefully"""
        suggestions = []
        
        # Try to find similar valid commands
        for base_command in ['move', 'take', 'use', 'attack', 'look', 'search']:
            if base_command in command.lower():
                suggestions.append(f"Did you mean to '{base_command} [target]'?")
                
        if suggestions:
            return {
                'message': f"Not sure what '{command}' means.\n" + "\n".join(suggestions),
                'next_situation': 'exploration'
            }
            
        return {
            'message': f"You can't '{command}' right now.",
            'next_situation': 'exploration'
        }
