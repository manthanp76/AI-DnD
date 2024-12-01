from openai import OpenAI
import pygame
import pygame.mixer
import asyncio
from pathlib import Path
import hashlib
import logging
from typing import Dict, Any, Optional
import os
import tempfile

class AudioManager:
    def __init__(self, api_key: str):
        """Initialize audio manager with OpenAI client"""
        self.client = OpenAI(api_key=api_key)
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        
        # Create cache directory
        self.cache_dir = Path("cache/audio")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up audio channels
        self.description_channel = pygame.mixer.Channel(0)
        self.effect_channel = pygame.mixer.Channel(1)
        
        self.current_audio = None
        self._volume = 1.0

    def speak(self, text: str, voice: str = "alloy") -> None:
        """Generate and play speech using OpenAI TTS"""
        try:
            # Create cache key from text and voice
            cache_key = hashlib.md5(f"{text}{voice}".encode()).hexdigest()
            cache_file = self.cache_dir / f"{cache_key}.mp3"

            # Check cache first
            if not cache_file.exists():
                # Use OpenAI's TTS API synchronously
                response = self.client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text
                )
                
                # Save the binary content
                with open(cache_file, "wb") as f:
                    f.write(response.content)

            # Play the audio using pygame
            sound = pygame.mixer.Sound(str(cache_file))
            self.description_channel.set_volume(self._volume)
            self.description_channel.play(sound)
            self.current_audio = sound

        except Exception as e:
            logging.error(f"Error generating/playing speech: {e}")

    def play_effect(self, effect_name: str) -> None:
        """Play a sound effect"""
        try:
            effect_path = Path("assets/audio/effects") / effect_name
            if effect_path.exists():
                sound = pygame.mixer.Sound(str(effect_path))
                self.effect_channel.set_volume(self._volume)
                self.effect_channel.play(sound)
        except Exception as e:
            logging.error(f"Error playing effect {effect_name}: {e}")

    def stop_audio(self):
        """Stop current audio playback"""
        self.description_channel.stop()
        self.effect_channel.stop()
        self.current_audio = None

    def set_volume(self, volume: float):
        """Set volume level (0.0 to 1.0)"""
        self._volume = max(0.0, min(1.0, volume))
        self.description_channel.set_volume(self._volume)
        self.effect_channel.set_volume(self._volume)

    def cleanup(self):
        """Clean up resources"""
        self.stop_audio()
        pygame.mixer.quit()