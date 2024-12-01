import asyncio
from PIL import Image, ImageTk
from typing import Optional
from .dalle_integration import DalleImageGenerator, ImageDisplay

class GameImageManager:
    def __init__(self, root, api_key: str):
        self.dalle_generator = DalleImageGenerator(api_key)
        self.image_display = ImageDisplay(root)
        self.location_cache = {}
        self.npc_cache = {}
        self._lock = asyncio.Lock()
        self.current_image = None  # Keep reference to prevent garbage collection

    async def show_location(self, location_id: str, name: str, description: str) -> Optional[str]:
        """Generate and return path to location image"""
        async with self._lock:
            # Check cache first
            if location_id in self.location_cache:
                return self.location_cache[location_id]

            # Generate new image
            image_path = await self.dalle_generator.generate_location_image(name, description)
            if image_path:
                self.location_cache[location_id] = image_path
                return image_path
            
            return None

    async def show_npc(self, npc_id: str, name: str, description: str):
        """Generate and display an NPC image"""
        async with self._lock:
            # Check cache first
            if npc_id in self.npc_cache:
                self.image_display.show_image(self.npc_cache[npc_id])
                return

            # Generate new image
            image_path = await self.dalle_generator.generate_npc_image(name, description)
            if image_path:
                self.npc_cache[npc_id] = image_path
                self.image_display.show_image(image_path)

    def hide_image(self):
        """Hide the image display"""
        self.image_display.hide()