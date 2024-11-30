Certainly, here's a more detailed README file that includes the usage of the project's functions:

# D&D AI Dungeon Master

## Introduction
The D&D AI Dungeon Master is a text-based adventure game where an AI assistant acts as the Dungeon Master, creating an immersive and responsive D&D-style experience for the player. The game features NPC interactions, combat, skill checks, item management, and a persistent game world.

## File Structure
The project is organized into the following files and directories:

### Main Files
- `main.py`: The entry point of the application, which creates the game GUI and initializes the game components.
  - `GameGUI` class: Responsible for creating the graphical user interface and handling user input.
  - `setup_game()` function: Initializes the game by displaying a welcome message and prompting the player to enter their character's name.
- `game_gui.py`: Defines the `GameGUI` class, which handles the graphical user interface and interactions with the player.
  - `create_gui()` method: Creates the GUI elements, including the output area, status frame, and input field.
  - `handle_input()` method: Processes the player's input and delegates the action to the `GameWorld` class.
  - `write_to_output()` method: Writes text to the output area with improved formatting.
  - `update_status()` method: Updates the player's status information displayed in the GUI.

### Core Components
- `game_world.py`: Defines the `GameWorld` class, which manages the game world, player actions, and AI responses.
  - `handle_player_action()` method: Processes the player's action and generates a response.
  - `_handle_movement()` method: Handles the player's movement between locations.
  - `_handle_item_take()` method: Handles the player's attempt to pick up an item.
  - `_handle_item_use()` method: Handles the player's attempt to use an item.
  - `_initiate_combat()` method: Initiates combat between the player and an NPC.
  - `_generate_action_response()` method: Generates an AI response for miscellaneous actions.
- `location.py`: Defines the `Location` class, which represents a location in the game world and handles its state and descriptions.
  - `get_current_description()` method: Returns the current description of the location, reflecting its state and the entities present.
  - `add_npc()`, `remove_npc()`, `get_npc()` methods: Manage the NPCs in the location.
  - `add_item()`, `remove_item()`, `get_item()` methods: Manage the items in the location.
  - `set_state()`, `add_exit()`, `remove_exit()`, `get_exit()`, `is_exit_locked()`, `lock_exit()`, `unlock_exit()` methods: Manage the location's state and exits.
- `player.py`: Defines the `Player` class, which represents the player character and their attributes, inventory, and actions.
  - `attack()` method: Performs an attack roll for the player.
  - `take_damage()` method: Applies damage to the player and checks if they are defeated.
  - `heal()` method: Heals the player.
  - `add_xp()` method: Adds experience points to the player and checks for level-up.
  - `level_up()` method: Increases the player's stats on level-up.
  - `add_item()`, `remove_item()`, `has_item()` methods: Manage the player's inventory.
  - `get_inventory_description()` method: Returns a formatted description of the player's inventory.
  - `perform_skill_check()` method: Performs a skill check using the `DiceRoller` utility.
- `npcs.py`: Defines the `NPC` and `NPCFactory` classes, which represent non-player characters and handle their behavior, dialog, and interactions.
  - `interact()` method: Handles the player's interaction with an NPC and generates a response.
  - `add_memory()` method: Adds a new memory to the NPC.
  - `get_relevant_memories()` method: Retrieves memories relevant to the current context.
  - `_select_response()` method: Selects an appropriate response based on the context and the NPC's memories.
  - `NPCFactory` class: Provides static methods for creating different types of NPCs.

### AI Components
- `generator.py`: Defines the `AIGenerator` class, which handles the generation of content using the OpenAI API.
  - `generate_content()` method: Generates content based on the provided prompt type and parameters.
  - `_validate_response()` method: Validates and formats the AI-generated response.
  - `_format_non_json_response()` method: Formats a plaintext response into the expected structure.
  - `_get_fallback_response()` method: Provides a fallback response in case of errors.
- `prompts.py`: Defines the `PromptManager` class, which manages the prompt templates used by the AI generator.
  - `get_system_prompt()` method: Returns the system prompt for the AI context.
  - `format_prompt()` method: Formats a prompt template with the provided parameters.
  - `_get_formatting_instructions()` method: Retrieves the formatting instructions for a specific prompt type.
  - `_get_fallback_template()` method: Provides a fallback prompt template in case of errors.
  - `get_template()` method: Retrieves a specific prompt template.
  - `_load_templates()` method: Loads the prompt templates from a JSON file.
  - `_load_prompt_relationships()` method: Loads the prompt relationship mappings from a JSON file.

### Utility Components
- `dice.py`: Defines the `DiceRoller` class, which handles dice rolling and skill checks.
  - `roll()` method: Rolls dice based on the provided dice string (e.g., "1d6+2").
  - `skill_check()` method: Performs a skill check and returns the success state and the roll value.
  - `get_roll_description()` method: Returns a description of the dice roll results.
- `time.py`: Defines the `TimeManager` class, which handles the passage of time and time-based events in the game.
  - `advance_time()` method: Advances the game time by the specified amount and scale, processing any time triggers.
  - `get_state()` method: Returns the current state of the time management system.
  - `add_time_trigger()` method: Adds a new time trigger with a unique identifier.
  - `remove_time_trigger()` method: Removes a specific time trigger by its identifier.
  - `_process_time_triggers()` method: Processes any triggered events in a thread-safe manner.
- `settings.py`: Defines the `Settings` class, which manages the game's configuration settings.
  - `_load_settings()` method: Loads the settings from a JSON file or uses default values.
  - `_merge_settings()` method: Merges user settings with default settings.
  - `save_settings()` method: Saves the current settings to a JSON file.
  - `get()` and `set()` methods: Retrieve and modify individual settings.

## Usage
To run the D&D AI Dungeon Master, follow these steps:

1. Install the required dependencies (e.g., `tkinter`, `openai`, `numpy`, `pandas`).
2. Run the `main.py` script to start the game.
3. Follow the on-screen instructions to create your character and explore the game world.

When playing the game, you can use the following commands:

- `look`: Examine the current location.
- `move [direction]`: Move to a new location in the specified direction.
- `take [item]`: Pick up an item from the current location.
- `use [item]`: Use an item from your inventory.
- `attack [target]`: Initiate combat with an NPC.
- `inventory` or `i`: View your current inventory.

## Customization
The D&D AI Dungeon Master is designed to be customizable. You can modify the following aspects of the game:

- **Prompt Templates**: The `PromptManager` class in `prompts.py` manages the prompt templates used by the AI generator. You can customize these templates to suit your preferences.
  - `get_system_prompt()` method: Modify the system prompt for the AI context.
  - `format_prompt()` method: Update the formatting of the prompt templates.
- **Item and NPC Definitions**: The `Item` and `NPC` classes in `items.py` and `npcs.py`, respectively, define the items and NPCs in the game world. You can add, modify, or remove these entities to expand the game world.
  - `ItemFactory` class: Create new item types or modify the existing ones.
  - `NPCFactory` class: Create new NPC types or modify the existing ones.
- **Game Settings**: The `Settings` class in `settings.py` allows you to configure various game settings, such as difficulty, game mode, and more.
  - `get()` and `set()` methods: Retrieve and modify individual settings.

## Contribution
If you'd like to contribute to the D&D AI Dungeon Master project, feel free to submit a pull request with your improvements or additions. We welcome any feedback or suggestions to make the game more engaging and immersive.

## License
This project is licensed under the [MIT License](LICENSE)."# AI-DnD" 
