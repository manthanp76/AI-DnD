# base.py
from typing import Dict, Any
from abc import ABC, abstractmethod

class Entity(ABC):
    """Base class for all game entities"""
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get current entity state"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get current entity description"""
        pass

class GameObject:
    """Base class for game objects with common functionality"""
    def __init__(self, id: str, name: str, description: str):
        self.id = id
        self.name = name
        self.description = description

    def get_state(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

    def get_description(self) -> str:
        return self.description