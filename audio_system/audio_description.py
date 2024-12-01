from typing import Dict, Any, Optional
import asyncio
import logging
from gtts import gTTS
import os
import tempfile
import pygame
from pathlib import Path
import hashlib

from .audio_manager import AudioManager

class AudioDescription: 
    def __init__(self, audio_manager: AudioManager):
        self.audio_manager = audio_manager
        self.last_description = None

    # Rest of the class implementation remains the same

    async def describe_scene(self, scene_data: Dict[str, Any], voice: str = "alloy"):
        """Generate and speak scene description"""
        description = self._generate_description(scene_data)
        
        # Only speak if description has changed
        if description != self.last_description:
            await self.audio_manager.speak(description, voice)
            self.last_description = description

    def _generate_description(self, scene_data: Dict[str, Any]) -> str:
        """Generate descriptive text from scene data"""
        lines = []
        
        if 'location' in scene_data:
            loc = scene_data['location']
            lines.append(loc.get('description', ''))
            
            features = loc.get('features', [])
            if features:
                lines.append(f"You notice {', '.join(features)}.")
            
            items = loc.get('items', [])
            if items:
                item_names = [item.get('name') for item in items 
                            if not item.get('is_taken')]
                if item_names:
                    lines.append(f"There are items here: {', '.join(item_names)}.")
            
            npcs = loc.get('npcs', [])
            if npcs:
                npc_names = [npc.get('name') for npc in npcs 
                           if not npc.get('is_defeated')]
                if npc_names:
                    lines.append(f"You see: {', '.join(npc_names)}.")
            
            exits = loc.get('exits', [])
            if exits:
                lines.append(f"You can go: {', '.join(exits)}.")

        if scene_data.get('in_combat'):
            enemy = scene_data.get('enemy', {})
            lines.append(f"You are in combat with {enemy.get('name')}.")
            lines.append(f"Your health is {scene_data.get('player_hp')} "
                        f"out of {scene_data.get('player_max_hp')}.")
            lines.append(f"The enemy's health is {enemy.get('hp')} "
                        f"out of {enemy.get('max_hp')}.")

        return " ".join(lines)

    def toggle_descriptions(self, enabled: bool):
        """Toggle audio descriptions on/off"""
        self.tts_enabled = enabled
        if not enabled:
            self._description_channel.stop()

    def set_language(self, language_code: str):
        """Set the description language"""
        self.language = language_code

    def cleanup(self):
        """Clean up resources"""
        self._description_channel.stop()