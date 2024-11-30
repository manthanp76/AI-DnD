# ai/generator.py
from typing import Dict, Any, Optional
import json
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from prompts.prompts import PromptManager
from utils.dice import DiceRoller

from openai import OpenAI
from config.api_config import setup_api

class AIGenerator:
    def __init__(self):
        # Setup API configuration
        api_key = setup_api()
        self.client = OpenAI(api_key=api_key)
        self.prompt_manager = PromptManager()
        self.context_history: List[Dict] = []
        self.max_context_length = 10
        self._lock = asyncio.Lock()
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('AIGenerator')

    async def generate_content(self, prompt_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content using AI with proper error handling"""
        try:
            # Get formatted prompts
            formatted_prompt = self.prompt_manager.format_prompt(prompt_type, parameters)
            system_prompt = self.prompt_manager.get_system_prompt()

            async with self._lock:
                # Generate response
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )

                response_text = response.choices[0].message.content
                
                # Add to context history
                self.context_history.append({
                    'timestamp': datetime.now(),
                    'prompt_type': prompt_type,
                    'response': response_text
                })
                
                # Maintain history length
                if len(self.context_history) > self.max_context_length:
                    self.context_history.pop(0)

                # Parse and validate response
                try:
                    result = json.loads(response_text)
                    return self._validate_response(result, prompt_type, parameters)
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse JSON response for {prompt_type}")
                    return self._format_non_json_response(response_text, prompt_type)

        except Exception as e:
            self.logger.error(f"AI generation failed: {e}")
            return self._get_fallback_response(prompt_type)

    def _validate_response(self, response: Dict, prompt_type: str, parameters: Dict) -> Dict:
        """Validate and format the AI response"""
        validators = {
            'location_description': {
                'required': ['name', 'description', 'theme', 'features'],
                'defaults': {
                    'name': 'Unknown Area',
                    'description': 'A nondescript area stretches before you.',
                    'theme': 'generic',
                    'features': [],
                    'atmosphere': 'The air is still and quiet.',
                    'exits': ['north', 'south']
                }
            },
            'search_response': {
                'required': ['description'],
                'defaults': {
                    'description': 'You search but find nothing unusual.',
                    'discoveries': []
                }
            },
            'examine_response': {
                'required': ['description'],
                'defaults': {
                    'description': 'You see nothing special.',
                    'features': [],
                    'interactions': []
                }
            },
            'action_response': {
                'required': ['description'],
                'defaults': {
                    'description': 'You proceed with your action.',
                    'success': True,
                    'next_situation': 'exploration'
                }
            }
        }

        if prompt_type in validators:
            validator = validators[prompt_type]
            
            # Check required fields
            for field in validator['required']:
                if field not in response:
                    response[field] = validator['defaults'][field]
                    
            # Add optional defaults
            for field, value in validator['defaults'].items():
                if field not in response:
                    response[field] = value

        return response

    def _format_non_json_response(self, text: str, prompt_type: str) -> Dict:
        """Format plaintext response into proper structure"""
        if prompt_type == 'location_description':
            return {
                'name': 'Unknown Area',
                'description': text,
                'theme': 'generic',
                'features': ['path'],
                'atmosphere': 'The area has a mysterious quality.',
                'exits': ['north', 'south']
            }
        elif prompt_type == 'search_response':
            return {
                'description': text,
                'discoveries': []
            }
        elif prompt_type == 'examine_response':
            return {
                'description': text,
                'features': [],
                'interactions': []
            }
        else:
            return {
                'description': text,
                'success': True,
                'next_situation': 'exploration'
            }

    def _get_fallback_response(self, prompt_type: str) -> Dict:
        """Get appropriate fallback response"""
        fallbacks = {
            'location_description': {
                'name': 'Mysterious Area',
                'description': 'A mysterious area shrouded in uncertainty.',
                'theme': 'mysterious',
                'features': ['shadows', 'mist'],
                'atmosphere': 'The air is thick with anticipation.',
                'exits': ['north', 'south']
            },
            'search_response': {
                'description': 'Your search reveals nothing unusual.',
                'discoveries': []
            },
            'examine_response': {
                'description': 'You see nothing special about it.',
                'features': [],
                'interactions': []
            },
            'action_response': {
                'description': 'You proceed with your action.',
                'success': True,
                'next_situation': 'exploration'
            }
        }
        return fallbacks.get(prompt_type, {
            'description': 'The situation continues normally.',
            'success': True,
            'next_situation': 'exploration'
        })

    async def cleanup(self):
        """Cleanup resources"""
        self.context_history.clear()
