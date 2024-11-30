import os
import base64
import requests
from typing import Optional
from PIL import Image
from io import BytesIO
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from openai import OpenAI

class DalleImageGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.cache_dir = Path("image_cache")
        self.cache_dir.mkdir(exist_ok=True)

    async def generate_location_image(self, location_name: str, description: str) -> Optional[str]:
        """Generate an image for a location using DALL-E"""
        try:
            # Create a focused prompt for the location
            prompt = f"Fantasy RPG scene of {location_name}: {description}. Digital art style, detailed, atmospheric lighting."
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            # Get the image URL from the response
            image_url = response.data[0].url
            
            # Download and cache the image
            if image_url:
                return self._cache_image(image_url, f"location_{location_name}")
                
            return None

        except Exception as e:
            print(f"Error generating location image: {e}")
            return None

    async def generate_npc_image(self, npc_name: str, description: str) -> Optional[str]:
        """Generate an image for an NPC using DALL-E"""
        try:
            # Create a focused prompt for the NPC
            prompt = f"Fantasy RPG character portrait of {npc_name}: {description}. Digital art style, detailed, fantasy lighting."
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            # Get the image URL from the response
            image_url = response.data[0].url
            
            # Download and cache the image
            if image_url:
                return self._cache_image(image_url, f"npc_{npc_name}")
                
            return None

        except Exception as e:
            print(f"Error generating NPC image: {e}")
            return None

    def _cache_image(self, image_url: str, prefix: str) -> Optional[str]:
        """Download and cache an image, return the local path"""
        try:
            # Download the image
            response = requests.get(image_url)
            if response.status_code == 200:
                # Create a unique filename
                filename = f"{prefix}_{hash(image_url)}.png"
                filepath = self.cache_dir / filename
                
                # Save the image
                with open(filepath, "wb") as f:
                    f.write(response.content)
                    
                return str(filepath)
            
            return None

        except Exception as e:
            print(f"Error caching image: {e}")
            return None

class ImageDisplay:
    def __init__(self, root):
        """Initialize the image display window"""
        self.window = tk.Toplevel(root)
        self.window.title("Scene View")
        self.window.geometry("1024x1024")
        
        # Create a label for the image
        self.image_label = ttk.Label(self.window)
        self.image_label.pack(expand=True, fill='both')
        
        # Hide the window initially
        self.window.withdraw()

    def show_image(self, image_path: str):
        """Display an image from a file path"""
        try:
            # Open and resize the image
            image = Image.open(image_path)
            image = image.resize((1024, 1024), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = tk.PhotoImage(file=image_path)
            
            # Update the label
            self.image_label.configure(image=photo)
            self.image_label.image = photo  # Keep a reference
            
            # Show the window
            self.window.deiconify()
            self.window.lift()

        except Exception as e:
            print(f"Error displaying image: {e}")

    def hide(self):
        """Hide the image window"""
        self.window.withdraw()
