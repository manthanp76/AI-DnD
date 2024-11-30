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
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from PIL import Image, ImageTk

from config.settings import Settings
from core.game_world import GameWorld
from core.player import Player
from image_system.image_manager import GameImageManager

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
    def __init__(self, root):
        self.root = root
        self.root.title("D&D AI Dungeon Master")
        self.root.geometry("1200x800")  # Wider window to accommodate image

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

        # Initialize image manager
        self.image_manager = GameImageManager(root, api_key)

        # Create GUI elements
        self.create_enhanced_gui()
        
        # Start game setup
        self.setup_game()

    def create_enhanced_gui(self):
        # Main container with dark theme
        self.root.configure(bg='#1a1a1a')
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=3)  # Game area
        main_container.columnconfigure(1, weight=1)  # Image/stats area
        main_container.rowconfigure(0, weight=1)

        # Create left panel (game area)
        self.create_game_panel(main_container)
        
        # Create right panel (image and stats)
        self.create_image_panel(main_container)

    def create_game_panel(self, parent):
        game_frame = ttk.Frame(parent)
        game_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        game_frame.columnconfigure(0, weight=1)
        game_frame.rowconfigure(1, weight=1)  # Output area should expand

        # Text size controls
        controls_frame = ttk.Frame(game_frame)
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(controls_frame, text="Text Size:").pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="-", width=3,
                  command=self.decrease_font_size).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="+", width=3,
                  command=self.increase_font_size).pack(side=tk.LEFT, padx=2)

        # Game output area with custom styling
        self.output_area = scrolledtext.ScrolledText(
            game_frame,
            wrap=tk.WORD,
            font=("Consolas", self.current_font_size),
            bg='#2b2b2b',
            fg='#e0e0e0',
            insertbackground='white'
        )
        self.output_area.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.output_area.config(state='disabled')

        # Input area
        input_frame = ttk.Frame(game_frame)
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        input_frame.columnconfigure(1, weight=1)

        prompt_label = ttk.Label(
            input_frame,
            text=">",
            font=("Consolas", self.current_font_size, "bold")
        )
        prompt_label.grid(row=0, column=0, padx=(0, 5))

        self.input_entry = tk.Entry(
            input_frame,
            font=("Consolas", self.current_font_size),
            bg='#2b2b2b',
            fg='#e0e0e0',
            insertbackground='#e0e0e0'
        )
        self.input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), ipady=5)
        self.input_entry.bind('<Return>', self.handle_input)
        self.input_entry.focus_set()

    def create_image_panel(self, parent):
        image_frame = ttk.Frame(parent)
        image_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        image_frame.columnconfigure(0, weight=1)
        
        # Image display area with border and background
        image_container = ttk.Frame(image_frame, style='Dark.TFrame')
        image_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.image_label = ttk.Label(image_container)
        self.image_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status frame with style
        status_frame = ttk.LabelFrame(image_frame, text="Character Status", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Health bar
        hp_frame = ttk.Frame(status_frame)
        hp_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(hp_frame, text="Health:").grid(row=0, column=0, sticky=tk.W)
        self.health_bar = ttk.Progressbar(hp_frame, length=200, mode='determinate')
        self.health_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # XP bar
        xp_frame = ttk.Frame(status_frame)
        xp_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(xp_frame, text="Experience:").grid(row=0, column=0, sticky=tk.W)
        self.xp_bar = ttk.Progressbar(xp_frame, length=200, mode='determinate')
        self.xp_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Level display
        self.level_label = ttk.Label(status_frame, text="Level: 1")
        self.level_label.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # Combat frame
        self.combat_frame = ttk.LabelFrame(image_frame, text="Combat", padding="10")
        self.combat_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        self.combat_frame.grid_remove()  # Hidden by default
        
        self.combat_label = ttk.Label(
            self.combat_frame,
            text="",
            font=("Consolas", self.current_font_size)
        )
        self.combat_label.grid(row=0, column=0)

    def increase_font_size(self):
        if self.current_font_size < self.max_font_size:
            self.current_font_size += 1
            self.update_font_sizes()

    def decrease_font_size(self):
        if self.current_font_size > self.min_font_size:
            self.current_font_size -= 1
            self.update_font_sizes()

    def update_font_sizes(self):
        self.output_area.configure(font=("Consolas", self.current_font_size))
        self.input_entry.configure(font=("Consolas", self.current_font_size))
        self.combat_label.configure(font=("Consolas", self.current_font_size))

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
            # Run initialization asynchronously
            self.async_tk.run_coroutine(
                self.initialize_game_world(),
                self.handle_initialization_complete
            )
            return

        # Add command echo
        self.write_to_output(f"\n> {command}\n")

        # Process command asynchronously
        self.async_tk.run_coroutine(
            self.process_command(command),
            self.handle_command_complete
        )

    def handle_initialization_complete(self, result):
        """Handle completion of game initialization"""
        if isinstance(result, Exception):
            self.write_to_output(f"\nError during initialization: {str(result)}\n")
            self.write_to_output("\nAvailable commands: look, help\n")
        self.update_status()

    def handle_command_complete(self, result):
        """Handle completion of command processing"""
        if result:
            if 'message' in result:
                self.write_to_output(result['message'])
            if result.get('next_situation') == 'game_over':
                self.write_to_output("\nGame Over!\n")
            self.update_status()
            if self.combat_state:
                self.update_combat_status()

    async def initialize_game_world(self):
        """Initialize the game world"""
        try:
            self.write_to_output("\nInitializing game world...\n")
            
            # Generate starting location
            starting_location = await self.game_world.generate_starting_location()
            
            if not starting_location:
                raise Exception("Failed to generate starting location")
                
            self.player.current_location_id = starting_location.id
            
            # Display initial location
            current_location = self.game_world.locations.get(self.player.current_location_id)
            if current_location:
                # Generate and show location image
                await self.show_location_image(current_location)
                
                self.write_to_output("\n" + "═"*80 + "\n")
                self.write_to_output(current_location.get_current_description())
                self.write_to_output("\n" + "═"*80 + "\n")
                self.write_to_output("\nAvailable commands: look, move [direction], take [item], use [item], inventory, attack [target]\n")
            
            self.update_status()
            
        except Exception as e:
            self.write_to_output(f"\nError during initialization: {str(e)}\n")
            self.write_to_output("\nAvailable commands: look, help\n")

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
            
            # Show the action result
            self.write_to_output(f"{result.get('message', 'You proceed with your action.')}\n")
            
            # Update status displays
            self.update_status()
            if self.combat_state:
                self.update_combat_status()
            
            return result
            
        except Exception as e:
            self.write_to_output(f"\nError processing command: {str(e)}\n")
            self.write_to_output("\nAvailable commands: look, help\n")
            return None

    def write_to_output(self, text: str):
        """Thread-safe write to output"""
        self.root.after(0, self._write_to_output, text)

    def _write_to_output(self, text: str):
        """Write to output with formatting"""
        self.output_area.config(state='normal')
        
        # Add decorative lines for section breaks
        if len(text.strip()) > 0 and not text.startswith('>'):
            if not text.startswith('\n'):
                self.output_area.insert(tk.END, '\n')
            if not text.startswith('═') and not text.startswith('╔'): 
                self.output_area.insert(tk.END, '─' * 80 + '\n')
        
        self.output_area.insert(tk.END, text)
        
        # Add bottom line for command lists
        if "Available commands" in text or "Combat Commands" in text:
            self.output_area.insert(tk.END, '\n' + '─' * 80 + '\n')
        
        self.output_area.see(tk.END)
        self.output_area.config(state='disabled')

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

    def cleanup(self):
        """Cleanup resources when closing"""
        self.async_tk.stop()
        self.root.destroy()

    def configure_styles(self):
        """Configure custom styles for the GUI"""
        style = ttk.Style()
        
        # Configure dark theme colors
        style.configure("Dark.TFrame", background='#1e1e1e')
        style.configure("Dark.TLabel", background='#1e1e1e', foreground='#e0e0e0')
        style.configure("Dark.TLabelframe", background='#1e1e1e', foreground='#e0e0e0')
        style.configure("Dark.TLabelframe.Label", background='#1e1e1e', foreground='#e0e0e0')
        
        # Configure progress bars
        style.configure(
            "Health.Horizontal.TProgressbar",
            background='#ff4444',
            troughcolor='#2b2b2b'
        )
        style.configure(
            "XP.Horizontal.TProgressbar",
            background='#4444ff',
            troughcolor='#2b2b2b'
        )

def main():
    root = tk.Tk()
    root.minsize(1200, 800)
    
    # Configure window style
    if tk.TkVersion >= 8.5:
        try:
            root.tk.call('tk', 'scaling', 1.0)
        except:
            pass
        
    app = GameGUI(root)
    app.configure_styles()
    
    # Set up cleanup on window close
    root.protocol("WM_DELETE_WINDOW", app.cleanup)
    
    root.mainloop()

if __name__ == "__main__":
    main()