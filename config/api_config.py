# config/api_config.py
import os
from pathlib import Path
from dotenv import load_dotenv

def setup_api():
    """Setup API configuration"""
    # Try to load from .env file
    env_path = Path('.') / '.env'
    load_dotenv(env_path)
    
    # Get API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable "
            "or create a .env file with OPENAI_API_KEY=your-api-key"
        )
    
    # Set the API key for the OpenAI client
    os.environ['OPENAI_API_KEY'] = api_key

    return api_key
