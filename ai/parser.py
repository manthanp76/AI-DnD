from typing import Dict, Any, List, Optional
import re
import json

class ResponseParser:
    def _parse_story_response(self, response: str) -> Dict[str, Any]:
        try:
            # Try to parse as JSON first
            data = json.loads(response)
            return {
                'description': data.get('description', ''),
                'location_changes': data.get('location_changes', {}),
                'player_changes': data.get('player_changes', {})
            }
        except:
            # Fallback to text parsing
            return {
                'description': response,
                'location_changes': {},
                'player_changes': {}
            }

    def _parse_consequence_creation(self, response: str) -> Dict[str, Any]:
        try:
            data = json.loads(response)
            return {
                'description': data.get('description', ''),
                'changes': data.get('changes', {})
            }
        except:
            return {
                'description': '',
                'changes': {}
            }
        
    def parse_response(self, response: str, prompt_type: str) -> Dict[str, Any]:
        """Parse AI response based on prompt type"""
        parser_method = getattr(self, f"_parse_{prompt_type}", None)
        if parser_method:
            return parser_method(response)
            
        # Default parsing for simple responses
        return self._parse_default(response)
    
    def _parse_location_description(self, response: str) -> Dict[str, Any]:
        """Parse location description response"""
        sections = self._split_sections(response)
        
        return {
            'description': sections.get('Description', ''),
            'features': [f.strip() for f in sections.get('Features', '').split(',')],
            'atmosphere': sections.get('Atmosphere', ''),
            'secrets': sections.get('Secrets', '')
        }
    
    def _parse_npc_dialog(self, response: str) -> Dict[str, Any]:
        """Parse NPC dialog response"""
        sections = self._split_sections(response)
        
        return {
            'dialog': sections.get('Dialog', ''),
            'action': sections.get('Action', ''),
            'intent': sections.get('Intent', '')
        }
    
    def _parse_combat_narration(self, response: str) -> Dict[str, Any]:
        """Parse combat narration response"""
        sections = self._split_sections(response)
        
        return {
            'action': sections.get('Action', ''),
            'effect': sections.get('Effect', ''),
            'reaction': sections.get('Reaction', '')
        }
    
    def _parse_default(self, response: str) -> Dict[str, Any]:
        """Default parsing for unstructured responses"""
        return {'content': response.strip()}
    
    def _split_sections(self, text: str) -> Dict[str, str]:
        """Split response into sections based on formatting"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check for section header
            if ':' in line and not current_content:
                parts = line.split(':', 1)
                current_section = parts[0].strip()
                content = parts[1].strip()
                if content:
                    current_content.append(content)
            elif current_section:
                current_content.append(line)
                
            # Save completed section
            if current_section and (not line or ':' in line):
                sections[current_section] = '\n'.join(current_content)
                current_section = None
                current_content = []
                
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
            
        return sections
    
class ResponseParser:
    def parse_response(self, response: str, prompt_type: str) -> Dict[str, Any]:
        try:
            # Try to parse as JSON first
            data = json.loads(response)
            return self._format_response(data, prompt_type)
        except json.JSONDecodeError:
            # Handle plain text response
            return self._format_text_response(response, prompt_type)
    
    def _format_response(self, data: Dict, prompt_type: str) -> Dict:
        if prompt_type == 'story_response':
            return {
                'description': data.get('description', 'You proceed with your action.'),
                'location_changes': data.get('location_changes', {}),
                'player_changes': data.get('player_changes', {})
            }
        elif prompt_type == 'location_description':
            return {
                'name': data.get('name', 'New Area'),
                'description': data.get('description', 'You enter a new area.'),
                'features': data.get('features', []),
                'atmosphere': data.get('atmosphere', ''),
                'theme': data.get('theme', 'wilderness')
            }
        return data

    def _format_text_response(self, text: str, prompt_type: str) -> Dict:
        """Handle plain text responses"""
        if prompt_type == 'story_response':
            return {
                'description': text,
                'location_changes': {},
                'player_changes': {}
            }
        elif prompt_type == 'location_description':
            return {
                'name': 'New Area',
                'description': text,
                'features': ['path'],
                'atmosphere': 'mysterious',
                'theme': 'wilderness'
            }
        return {'content': text}