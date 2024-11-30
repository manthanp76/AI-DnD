import asyncio
from .dalle_integration import DalleImageGenerator, ImageDisplay

class GameImageManager:
    def __init__(self, root, api_key: str):
        self.dalle_generator = DalleImageGenerator(api_key)
        self.image_display = ImageDisplay(root)
        self.location_cache = {}
        self.npc_cache = {}
        self._lock = asyncio.Lock()

    async def show_location(self, location_id: str, name: str, description: str):
        """Generate and display a location image"""
        async with self._lock:
            # Check cache first
            if location_id in self.location_cache:
                self.image_display.show_image(self.location_cache[location_id])
                return

            # Generate new image
            image_path = await self.dalle_generator.generate_location_image(name, description)
            if image_path:
                self.location_cache[location_id] = image_path
                self.image_display.show_image(image_path)

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