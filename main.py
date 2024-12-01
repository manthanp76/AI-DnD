import tkinter as tk
from tkinter import ttk, scrolledtext, Toplevel
from pathlib import Path
import asyncio
import logging
import queue
from typing import Optional, Any, List, Dict
import threading
from datetime import datetime
import random
import numpy
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from PIL import Image, ImageTk
import pygame
import pygame.mixer

from config.settings import Settings
from core.game_world import GameWorld
from core.player import Player
from image_system.image_manager import GameImageManager
from audio_system.audio_manager import AudioManager
from audio_system.audio_description import AudioDescription

from enum import Enum

class SoundCategory(Enum):
    MUSIC = "music"
    EFFECTS = "effects"
    AMBIENT = "ambient"
    SPEECH = "speech"
    MASTER = "master"

# Load environment variables
load_dotenv()

class AsyncTkinter:
    """Helper class to run async code with tkinter"""
    def __init__(self, root):
        self.root = root
        self.loop = asyncio.new_event_loop()
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        
    def start(self):
        """Start the async event loop in a separate thread"""
        def run_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
            
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the async event loop"""
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()
        self.thread_pool.shutdown()
        
    async def async_run(self, func, *args, **kwargs):
        """Run a coroutine in the event loop"""
        return await func(*args, **kwargs)
        
    def run_coroutine(self, coroutine, callback=None):
        """Run a coroutine and optionally call a callback with the result"""
        async def run():
            try:
                result = await coroutine
                if callback:
                    self.root.after(0, callback, result)
            except Exception as e:
                print(f"Error in coroutine: {e}")
                
        asyncio.run_coroutine_threadsafe(run(), self.loop)

class GameGUI:
    def __init__(self, root, audio_manager: Optional[AudioManager] = None):
        self.root = root
        self.root.title("D&D AI Dungeon Master")
        self.root.geometry("1200x800")

        # Font configuration
        self.current_font_size = 11
        self.min_font_size = 8
        self.max_font_size = 20

        # Initialize async support
        self.async_tk = AsyncTkinter(root)
        self.async_tk.start()

        # Initialize game components
        self.settings = Settings()
        self.game_world = GameWorld()
        self.player = None
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.game_state = "naming"
        self.combat_state = False

        # Get API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # Use provided audio manager or create a new one if none provided
        self.audio_manager = audio_manager if audio_manager else AudioManager(api_key)

        # Initialize audio systems
        self.audio_description = AudioDescription(self.audio_manager)
        
        # Create audio control panel
        self.create_audio_controls()

        # Initialize image manager
        self.image_manager = GameImageManager(root, api_key)

        # Create GUI elements
        self.create_enhanced_gui()
        
        # Start game setup
        self.setup_game()

    def create_enhanced_gui(self):
        """Create GUI elements with enhanced styling"""
        # Configure window style
        self.root.configure(bg='#1a1a1a')
        
        # Create custom styles
        style = ttk.Style()
        style.configure('Dark.TFrame', background='#1a1a1a')
        style.configure('Dark.TLabel', background='#1a1a1a', foreground='#e0e0e0')
        style.configure('Game.TFrame', background='#2b2b2b', borderwidth=2, relief='solid')
        
        main_container = ttk.Frame(self.root, padding="10", style='Dark.TFrame')
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=3)  # Game area
        main_container.columnconfigure(1, weight=1)  # Image/stats area
        main_container.rowconfigure(0, weight=1)

        # Create game panel (left side)
        game_frame = ttk.Frame(main_container, style='Game.TFrame')
        game_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        game_frame.columnconfigure(0, weight=1)
        game_frame.rowconfigure(1, weight=1)

        # Font size controls with improved styling
        controls_frame = ttk.Frame(game_frame, style='Dark.TFrame')
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(controls_frame, text="Text Size:", style='Dark.TLabel').pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="-", width=3, command=self.decrease_font_size).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="+", width=3, command=self.increase_font_size).pack(side=tk.LEFT, padx=2)

        # Game output with enhanced styling
        output_frame = ttk.Frame(game_frame, style='Game.TFrame')
        output_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        self.output_area = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=("Consolas", self.current_font_size),
            bg='#2b2b2b',
            fg='#e0e0e0',
            insertbackground='white',
            padx=10,
            pady=10
        )
        self.output_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)

        # Input area with improved styling
        input_frame = ttk.Frame(game_frame, style='Game.TFrame')
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(1, weight=1)

        prompt_label = ttk.Label(
            input_frame,
            text=">",
            font=("Consolas", self.current_font_size, "bold"),
            foreground="#90CAF9",  # Light blue
            style='Dark.TLabel'
        )
        prompt_label.grid(row=0, column=0, padx=(10, 5), pady=5)

        self.input_entry = tk.Entry(
            input_frame,
            font=("Consolas", self.current_font_size),
            bg='#2b2b2b',
            fg='#e0e0e0',
            insertbackground='#90CAF9',
            relief='flat',
            highlightthickness=1,
            highlightbackground='#404040',
            highlightcolor='#6200ee'
        )
        self.input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        self.input_entry.bind('<Return>', self.handle_input)
        self.input_entry.focus_set()

        # Create image panel (right side)
        image_frame = ttk.Frame(main_container, style='Game.TFrame')
        image_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        image_frame.columnconfigure(0, weight=1)
        
        # Image display with border
        self.image_label = ttk.Label(image_frame, borderwidth=0)
        self.image_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)

        # Status frame with improved styling
        status_frame = ttk.LabelFrame(image_frame, text="Character Status", padding="10", style='Dark.TFrame')
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        # Configure progress bars with enhanced style
        style.configure("health.Horizontal.TProgressbar", 
                    troughcolor='#2b2b2b', 
                    background='#4CAF50')
        style.configure("xp.Horizontal.TProgressbar", 
                    troughcolor='#2b2b2b', 
                    background='#2196F3')

        # Health bar
        ttk.Label(status_frame, text="Health:", style='Dark.TLabel').grid(row=0, column=0, sticky=tk.W)
        self.health_bar = ttk.Progressbar(status_frame, style="health.Horizontal.TProgressbar", length=200)
        self.health_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        # XP bar
        ttk.Label(status_frame, text="Experience:", style='Dark.TLabel').grid(row=2, column=0, sticky=tk.W)
        self.xp_bar = ttk.Progressbar(status_frame, style="xp.Horizontal.TProgressbar", length=200)
        self.xp_bar.grid(row=3, column=0, sticky=(tk.W, tk.E))

        # Level display
        self.level_label = ttk.Label(status_frame, text="Level: 1", style='Dark.TLabel')
        self.level_label.grid(row=4, column=0, sticky=tk.W, pady=(5, 0))

        # Create combat frame and label
        self.combat_frame = ttk.LabelFrame(image_frame, text="Combat", padding="10", style='Dark.TFrame')
        self.combat_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.combat_label = ttk.Label(
            self.combat_frame,
            text="",
            style='Dark.TLabel',
            font=("Consolas", self.current_font_size)
        )
        self.combat_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Hide combat frame initially
        self.combat_frame.grid_remove()

    def create_audio_controls(self):
        """Create simplified audio control panel"""
        audio_frame = ttk.LabelFrame(self.root, text="Audio", padding="10")
        audio_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(10, 0))

        # Volume control
        volume_frame = ttk.Frame(audio_frame)
        volume_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(volume_frame, text="Volume:").pack(side=tk.LEFT)
        
        volume_scale = ttk.Scale(
            volume_frame, 
            from_=0, to=100, 
            orient=tk.HORIZONTAL,
            command=lambda v: self.audio_manager.set_volume(float(v)/100)
        )
        volume_scale.set(100)
        volume_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Voice selection
        voice_frame = ttk.Frame(audio_frame)
        voice_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(voice_frame, text="Voice:").pack(side=tk.LEFT)
        
        self.voice_var = tk.StringVar(value="alloy")
        voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        voice_menu = ttk.OptionMenu(voice_frame, self.voice_var, "alloy", *voices)
        voice_menu.pack(side=tk.LEFT, padx=5)

        # Description toggle
        desc_frame = ttk.Frame(audio_frame)
        desc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.desc_var = tk.BooleanVar(value=True)
        desc_check = ttk.Checkbutton(
            desc_frame, 
            text="Audio Descriptions",
            variable=self.desc_var,
            command=self.toggle_descriptions
        )
        desc_check.pack(side=tk.LEFT)

    def update_volume(self, category: SoundCategory, volume: float):
        """Update volume for a sound category"""
        self.audio_manager.set_volume(category, volume)

    def toggle_descriptions(self):
        """Toggle audio descriptions"""
        if not self.desc_var.get():
            self.audio_manager.speech_generator.stop_description()

    def increase_font_size(self):
        """Increase font size with safety checks"""
        if self.current_font_size < self.max_font_size:
            self.current_font_size += 1
            try:
                self.update_font_sizes()
            except Exception as e:
                self.current_font_size -= 1
                print(f"Error updating font sizes: {e}")

    def decrease_font_size(self):
        """Decrease font size with safety checks"""
        if self.current_font_size > self.min_font_size:
            self.current_font_size -= 1
            try:
                self.update_font_sizes()
            except Exception as e:
                self.current_font_size += 1
                print(f"Error updating font sizes: {e}")

    def update_font_sizes(self):
        """Update font sizes with error handling"""
        try:
            if hasattr(self, 'output_area'):
                self.output_area.configure(font=("Consolas", self.current_font_size))
            if hasattr(self, 'input_entry'):
                self.input_entry.configure(font=("Consolas", self.current_font_size))
            if hasattr(self, 'combat_label') and self.combat_label.winfo_exists():
                self.combat_label.configure(font=("Consolas", self.current_font_size))
        except Exception as e:
            print(f"Error updating fonts: {e}")

    def setup_game(self):
        """Initialize the game"""
        welcome_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     Welcome to D&D AI Dungeon Master!                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

What is your character's name?
Type your character's name and press Enter.
"""
        self.write_to_output(welcome_text)
        self.game_state = "naming"

    def handle_input(self, event=None):
        """Handle player input"""
        command = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)

        if not command:
            return

        if self.game_state == "naming":
            self.player = Player(name=command)
            self.game_world.player = self.player
            self.game_world.root = self.root
            self.game_state = "playing"
            self.write_to_output(f"\nWelcome, {command}!\n")
            self.async_tk.run_coroutine(
                self.initialize_game_world(),
                self.handle_initialization_complete
            )
            return

        self.write_to_output(f"\n> {command}\n")
        self.async_tk.run_coroutine(
            self.process_command(command),
            self.handle_command_complete
        )

    async def handle_command(self, command: str):
        """Process game commands with audio"""
        try:
            # Handle special combat state
            if self.combat_state:
                result = await self.game_world._handle_combat_action(command)
                if result.get('combat_effect'):
                    self.audio_manager.play_effect(result['combat_effect'])
                    
                # Add voice response for combat
                if result.get('message'):
                    self.audio_manager.speak(result['message'], voice=self.voice_var.get())
                    
            else:
                result = await self.game_world.handle_player_action({"command": command.lower()})
                if result.get('sound_effect'):
                    self.audio_manager.play_effect(result['sound_effect'])
                    
                # Add voice response for general actions
                if result.get('message'):
                    self.audio_manager.speak(result['message'], voice=self.voice_var.get())
            
            # Update combat state based on result
            self.combat_state = (result.get('next_situation') == 'combat')
            
            # Update images based on command result
            current_location = self.game_world.locations.get(self.player.current_location_id)
            if current_location:
                await self.show_location_image(current_location)
                
                # Update ambient sound based on location
                await self.audio_manager.change_ambient(current_location.theme)
                
                # Generate audio description for new location
                if result.get('new_location', False):
                    await self.audio_description.describe_scene({
                        'location': current_location.get_state(),
                        'in_combat': self.combat_state,
                        'player_hp': self.player.hp,
                        'player_max_hp': self.player.max_hp,
                        'enemy': self.game_world.current_state.get('current_enemy', {})
                    })
            
            # Handle music changes
            if result.get('next_situation') == 'combat' and not self.combat_state:
                await self.audio_manager.change_music('combat')
            elif result.get('next_situation') == 'exploration' and self.combat_state:
                await self.audio_manager.change_music('exploration')
            
            # Show the action result - single output
            self.write_to_output(f"{result.get('message', 'You proceed with your action.')}\n")
            
            # Update status displays
            self.update_status()
            if self.combat_state:
                self.update_combat_status()
            
            return result
            
        except Exception as e:
            error_msg = f"\nError processing command: {str(e)}\n"
            self.write_to_output(error_msg)
            self.write_to_output("\nAvailable commands: look, help\n")
            self.audio_manager.speak("Sorry, there was an error processing your command.", voice=self.voice_var.get())
            return None

    def handle_command_complete(self, result):
        """Handle completion of command processing"""
        if result:
            # Only write game over message since regular messages are handled in process_command
            if result.get('next_situation') == 'game_over':
                self.write_to_output("\nGame Over!\n")
            self.update_status()
            if self.combat_state:
                self.update_combat_status()

    def write_to_output(self, text: str):
        """Write to output with better deduplication"""
        self.output_area.config(state='normal')
        
        # Clean and format the text
        formatted_text = self._clean_text_for_display(text)
        
        # Add a separator before most messages (but not after commands or special content)
        if formatted_text and not formatted_text.startswith(('>','╔','═')):
            self.output_area.insert(tk.END, '─' * 80 + '\n', 'separator')
        
        # Apply different tags based on content type
        if formatted_text.startswith('>'):
            self.output_area.insert(tk.END, formatted_text + '\n', 'command')
        elif '║' in formatted_text:
            self.output_area.insert(tk.END, formatted_text + '\n', 'title')
        elif formatted_text.startswith('Available commands:'):
            self.output_area.insert(tk.END, formatted_text + '\n', 'help')
        else:
            self.output_area.insert(tk.END, formatted_text + '\n', 'normal')
        
        # Configure text tags with colors
        self.output_area.tag_configure('command', foreground='#90CAF9')  # Light blue
        self.output_area.tag_configure('title', foreground='#FFD700')    # Gold
        self.output_area.tag_configure('help', foreground='#98FB98')     # Pale green
        self.output_area.tag_configure('separator', foreground='#404040') # Dark gray
        self.output_area.tag_configure('normal', foreground='#e0e0e0')   # Light gray
        
        # Ensure we're showing the latest text
        self.output_area.see(tk.END)
        self.output_area.config(state='disabled')

    def _clean_text_for_display(self, text: str) -> str:
        """Clean and format text for display with improved deduplication"""
        # Split into lines and remove empty ones
        lines = [line.strip() for line in text.split('\n')]
        
        cleaned_lines = []
        seen_content = set()  # Track unique content
        last_line = None
        
        for line in lines:
            # Skip empty lines if the last line was empty
            if not line and last_line == "":
                continue
                
            # Handle special formatting
            is_border = '╔' in line or '╚' in line or '║' in line
            is_separator = '═' * 4 in line or '─' * 4 in line
            is_command = line.startswith('>')
            
            # Always include borders, separators, and commands
            if is_border or is_command:
                cleaned_lines.append(line)
                last_line = line
                continue
                
            # Handle separators - only include if helpful for readability
            if is_separator and last_line and not last_line.startswith('─'):
                cleaned_lines.append(line)
                last_line = line
                continue
                
            # For normal content, check for duplicates
            content_key = line.strip().lower()
            if content_key and content_key not in seen_content:
                cleaned_lines.append(line)
                seen_content.add(content_key)
                last_line = line
            
        return '\n'.join(cleaned_lines)
    
    async def initialize_game_world(self):
        """Initialize the game world"""
        try:
            # Initial message
            init_message = "\nInitializing game world...\n"
            self.write_to_output(init_message)
            self.audio_manager.speak(init_message.strip(), voice=self.voice_var.get())
            
            # Generate starting location
            starting_location = await self.game_world.generate_starting_location()
            
            if not starting_location:
                raise Exception("Failed to generate starting location")
                    
            self.player.current_location_id = starting_location.id
            
            # Display initial location
            current_location = self.game_world.locations.get(self.player.current_location_id)
            if current_location:
                try:
                    # Generate and show location image
                    await self.show_location_image(current_location)
                    
                    # Display description
                    self.write_to_output("\n" + "═"*80 + "\n")
                    location_desc = current_location.get_current_description()
                    self.write_to_output(location_desc)
                    self.write_to_output("\n" + "═"*80 + "\n")
                    
                    # Narrate description
                    self.audio_manager.speak(location_desc, voice=self.voice_var.get())
                    
                    # Show available commands
                    cmd_text = "\nAvailable commands: look, move [direction], take [item], use [item], inventory, attack [target]\n"
                    self.write_to_output(cmd_text)
                    self.audio_manager.speak("Here are your available commands: look around, move in a direction, take items, use items, check inventory, or attack targets.", 
                                        voice=self.voice_var.get())
                
                except Exception as e:
                    print(f"Error setting up initial location: {e}")
            
            self.update_status()
            
        except Exception as e:
            error_msg = f"\nError during initialization: {str(e)}\n"
            self.write_to_output(error_msg)
            self.write_to_output("\nAvailable commands: look, help\n")
            self.audio_manager.speak("Sorry, there was an error initializing the game world.", 
                                voice=self.voice_var.get())

    async def process_command(self, command: str):
        """Process game commands"""
        try:
            # Handle special combat state
            if self.combat_state:
                result = await self.game_world._handle_combat_action(command)
            else:
                result = await self.game_world.handle_player_action({"command": command.lower()})
            
            # Update combat state based on result
            self.combat_state = (result.get('next_situation') == 'combat')
            
            # Update images based on command result
            current_location = self.game_world.locations.get(self.player.current_location_id)
            if current_location:
                await self.show_location_image(current_location)
            
            # Write the action result to the output
            if 'message' in result:
                self.write_to_output(result['message'])
            
            # Update status displays
            self.update_status()
            if self.combat_state:
                self.update_combat_status()
            
            return result
        
        except Exception as e:
            self.write_to_output(f"\nError processing command: {str(e)}\n")
            self.write_to_output("\nAvailable commands: look, help\n")
            return None

    def handle_initialization_complete(self, result):
        """Handle completion of game initialization"""
        if isinstance(result, Exception):
            self.write_to_output(f"\nError during initialization: {str(result)}\n")
            self.write_to_output("\nAvailable commands: look, help\n")
        self.update_status()

    def update_status(self):
        """Update player status display"""
        if self.player:
            # Update health bar
            health_percentage = (self.player.hp / self.player.max_hp) * 100
            self.health_bar['value'] = health_percentage
            
            # Update XP bar (assuming 100 XP per level)
            xp_percentage = (self.player.xp % 100)
            self.xp_bar['value'] = xp_percentage
            
            # Update level display
            self.level_label.config(text=f"Level: {self.player.level}")
            
            # Show/hide combat frame based on state
            if self.combat_state:
                self.combat_frame.grid()
            else:
                self.combat_frame.grid_remove()

    def update_combat_status(self):
        """Update combat status display"""
        if self.combat_state and self.game_world.current_state.get('current_enemy'):
            enemy = self.game_world.current_state['current_enemy']
            combat_text = f"Fighting: {enemy.name}\n"
            combat_text += f"Enemy HP: {enemy.hp}/{enemy.max_hp}"
            self.combat_label.config(text=combat_text)

    async def show_location_image(self, location):
        """Show location image in the GUI"""
        try:
            image_path = await self.image_manager.show_location(
                location.id,
                location.name,
                location.description
            )
            if image_path:
                # Load and resize image
                image = Image.open(image_path)
                image = image.resize((384, 384), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                # Update image label
                self.image_label.configure(image=photo)
                self.image_label.image = photo  # Keep a reference
                
        except Exception as e:
            print(f"Error displaying image: {e}")

    def check_audio_setup():
        """Setup audio system and verify files"""
        try:
            # Initialize pygame mixer
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            
            # Create required directories
            audio_dirs = {
                'effects': [
                    'sword_hit.wav', 'sword_miss.wav', 'critical_hit.wav',
                    'monster_hit.wav', 'monster_die.wav', 'player_hit.wav',
                    'player_hit_critical.wav', 'player_die.wav', 'shield_block.wav',
                    'combat_start.wav', 'retreat_success.wav', 'retreat_fail.wav',
                    'item_pickup.wav', 'item_use.wav', 'potion_use.wav',
                    'equip_weapon.wav', 'equip_armor.wav', 'item_discover.wav',
                    'footsteps.wav', 'examine.wav', 'search.wav', 'dialog.wav',
                    'menu_open.wav', 'action_generic.wav', 'level_up.wav'
                ],
                'ambient': [
                    'forest_ambient.wav', 'cave_ambient.wav', 'dungeon_ambient.wav',
                    'village_ambient.wav', 'combat_ambient.wav'
                ],
                'music': [
                    'main_theme.mp3', 'exploration.mp3', 'combat.mp3',
                    'victory.mp3', 'defeat.mp3'
                ]
            }

            base_path = Path('assets/audio')
            for category, files in audio_dirs.items():
                category_path = base_path / category
                category_path.mkdir(parents=True, exist_ok=True)
                
                # Check for missing files
                missing = []
                for filename in files:
                    if not (category_path / filename).exists():
                        missing.append(filename)
                
                if missing:
                    print(f"Missing {category} files: {', '.join(missing)}")
                    # Here you could add code to extract or download missing files

        except Exception as e:
            print(f"Error setting up audio: {e}")
            return False
        
        return True

    def cleanup(self):
        """Cleanup resources including audio"""
        if hasattr(self, 'audio_manager'):
            self.audio_manager.cleanup()
        if hasattr(self, 'async_tk'):
            self.async_tk.stop()
        self.root.destroy()

    def configure_styles(self):
        """Configure custom styles for the GUI"""
        style = ttk.Style()
        
        # Configure dark theme colors
        COLORS = {
            'bg_dark': '#1a1a1a',
            'bg_medium': '#2b2b2b',
            'text_primary': '#e0e0e0',
            'text_secondary': '#a0a0a0',
            'accent_primary': '#6200ee',
            'accent_secondary': '#03dac6',
            'warning': '#cf6679',
            'success': '#4CAF50'
        }
        
        # Configure styles
        style.configure("Dark.TFrame", background=COLORS['bg_dark'])
        style.configure("Dark.TLabel", 
                       background=COLORS['bg_dark'], 
                       foreground=COLORS['text_primary'])
        style.configure("Game.TFrame", 
                       background=COLORS['bg_medium'], 
                       borderwidth=2, 
                       relief='solid')
        style.configure("Custom.TButton",
                       background=COLORS['accent_primary'],
                       foreground=COLORS['text_primary'],
                       padding=(10, 5))
        style.configure("health.Horizontal.TProgressbar",
                       troughcolor=COLORS['bg_medium'],
                       background=COLORS['success'])
        style.configure("xp.Horizontal.TProgressbar",
                       troughcolor=COLORS['bg_medium'],
                       background=COLORS['accent_primary'])

async def test_audio_system(audio_manager):
    try:
        await audio_manager.speak("Testing audio system", voice="alloy")
        return True
    except Exception as e:
        print(f"Audio test failed: {e}")
        return False

def test_audio():
    """Test basic audio functionality"""
    try:
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Create a simple beep sound
        duration = 1  # seconds
        frequency = 440  # Hz
        sample_rate = 44100
        samples = duration * sample_rate
        
        # Generate a simple sine wave
        buffer = numpy.sin(2 * numpy.pi * numpy.arange(samples) * frequency / sample_rate)
        buffer = (buffer * 32767).astype(numpy.int16)
        
        # Play the sound
        sound = pygame.mixer.Sound(buffer)
        sound.play()
        
        # Wait for the sound to finish
        pygame.time.wait(int(duration * 1000))
        
        print("Audio test successful!")
        return True
    except Exception as e:
        print(f"Audio test failed: {e}")
        return False

def main():
    # Load OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    # Test basic audio first
    if not test_audio():
        print("Warning: Basic audio system not working properly")
        
    root = tk.Tk()
    root.minsize(1200, 800)
    
    # Initialize audio manager with OpenAI API key
    audio_manager = AudioManager(api_key)
    
    # Test speech
    audio_manager.speak("Testing audio system", voice="alloy")
    
    # Create game GUI
    app = GameGUI(root=root, audio_manager=audio_manager)
    app.configure_styles()
    
    root.protocol("WM_DELETE_WINDOW", app.cleanup)
    root.mainloop()

if __name__ == "__main__":
    main()