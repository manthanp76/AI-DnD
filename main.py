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

from config.settings import Settings
from core.game_world import GameWorld
from core.player import Player

class GameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("D&D AI Dungeon Master")
        self.root.geometry("800x800")

        # Initialize game components
        self.settings = Settings()
        self.game_world = GameWorld()
        self.player = None
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.game_state = "naming"
        self.combat_state = False

        # Create GUI elements
        self.create_gui()
        
        # Start game setup
        self.setup_game()

    def create_gui(self):
        # Main frame with padding and darker bg
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.configure(bg='#2b2b2b')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Game output area
        self.output_area = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=32,
            font=("Consolas", 11),
            bg='#1e1e1e',
            fg='#e0e0e0',
            insertbackground='white'
        )
        self.output_area.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.output_area.config(state='disabled')

        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Character Status", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(
            status_frame,
            text="",
            font=("Consolas", 10)
        )
        self.status_label.grid(row=0, column=0)

        # Combat status frame
        self.combat_frame = ttk.LabelFrame(main_frame, text="Combat Status", padding="10")
        self.combat_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        self.combat_frame.grid_remove()  # Hidden by default
        
        self.combat_label = ttk.Label(
            self.combat_frame,
            text="",
            font=("Consolas", 10)
        )
        self.combat_label.grid(row=0, column=0)

        # Input frame
        input_frame = ttk.Frame(main_frame, padding="5")
        input_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(1, weight=1)

        # Command prompt
        prompt_label = ttk.Label(
            input_frame,
            text=">",
            font=("Consolas", 11, "bold")
        )
        prompt_label.grid(row=0, column=0, padx=(0, 5))

        # Command input
        self.input_entry = tk.Entry(
            input_frame,
            font=("Consolas", 11),
            bg='#2b2b2b',
            fg='#e0e0e0',
            insertbackground='#e0e0e0',
            relief='flat',
            highlightthickness=1,
            highlightbackground='#404040',
            highlightcolor='#606060'
        )
        self.input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), ipady=5)
        self.input_entry.bind('<Return>', self.handle_input)
        self.input_entry.focus_set()

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

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
            self.game_world.root = self.root  # Pass root for potential combat window
            self.game_state = "playing"
            self.write_to_output(f"\nWelcome, {command}!\n")
            threading.Thread(target=self.initialize_game_world, daemon=True).start()
            return

        # Add command echo
        self.write_to_output(f"\n> {command}\n")

        # Process command in thread
        threading.Thread(target=self.process_command, args=(command,), daemon=True).start()

    def process_command(self, command: str):
        """Process game commands"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Handle special combat state
            if self.combat_state:
                result = loop.run_until_complete(
                    self.game_world._handle_combat_action(command)
                )
            else:
                result = loop.run_until_complete(
                    self.game_world.handle_player_action({"command": command.lower()})
                )
            
            # Update combat state based on result
            self.combat_state = (result.get('next_situation') == 'combat')
            
            # Show the action result
            self.write_to_output(f"{result.get('message', 'You proceed with your action.')}\n")
            
            # Update status displays
            self.update_status()
            if self.combat_state:
                self.update_combat_status()
            
            # Show appropriate command help
            if result.get('next_situation') == 'game_over':
                self.write_to_output("\n╔══════════════════════════════════════════════════╗")
                self.write_to_output("\n║                   GAME OVER                      ║")
                self.write_to_output("\n╚══════════════════════════════════════════════════╝\n")
            elif self.combat_state:
                self.write_to_output("\nCombat Commands: attack, defend, retreat, use [item]\n")
            else:
                self.write_to_output("\nAvailable commands: look, move [direction], take [item], use [item], inventory, attack [target]\n")
            
            loop.close()
            
        except Exception as e:
            self.write_to_output(f"\nError processing command: {str(e)}\n")
            self.write_to_output("\nAvailable commands: look, help\n")
            
    def initialize_game_world(self):
        """Initialize the game world"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.write_to_output("\nInitializing game world...\n")
            
            # Generate starting location
            starting_location = loop.run_until_complete(
                self.game_world.generate_starting_location()
            )
            
            if not starting_location:
                raise Exception("Failed to generate starting location")
                
            self.player.current_location_id = starting_location.id
            
            # Display initial location
            current_location = self.game_world.locations.get(self.player.current_location_id)
            if current_location:
                self.write_to_output("\n" + "═"*80 + "\n")
                self.write_to_output(current_location.get_current_description())
                self.write_to_output("\n" + "═"*80 + "\n")
                self.write_to_output("\nAvailable commands: look, move [direction], take [item], use [item], inventory, attack [target]\n")
            
            self.update_status()
            loop.close()
            
        except Exception as e:
            self.write_to_output(f"\nError during initialization: {str(e)}\n")
            self.write_to_output("\nAvailable commands: look, help\n")
            loop.close()

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
            status_text = f"⚔ {self.player.name} | "
            status_text += f"❤ HP: {self.player.hp}/{self.player.max_hp} | "
            status_text += f"⭐ Level: {self.player.level} | "
            status_text += f"✨ XP: {self.player.xp}"
            
            self.root.after(0, self.status_label.config, {"text": status_text})
            
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

def main():
    root = tk.Tk()
    root.minsize(800, 800)
    
    # Configure window style
    if tk.TkVersion >= 8.5:
        try:
            root.tk.call('tk', 'scaling', 1.0)
        except:
            pass
        
    app = GameGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()