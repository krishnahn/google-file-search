"""
Configuration management for Google File Search RAG system.
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Settings:
    """Configuration settings for the RAG system."""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.default_model = os.getenv('DEFAULT_MODEL', 'gemini-2.5-flash')
        self.default_store_name = os.getenv('DEFAULT_STORE_NAME', 'rag-documents')
        
        # Chunking configuration
        self.max_tokens_per_chunk = int(os.getenv('MAX_TOKENS_PER_CHUNK', 500))
        self.max_overlap_tokens = int(os.getenv('MAX_OVERLAP_TOKENS', 50))
        
        # File limits
        self.max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', 100))
        
        # Validate required settings
        if not self.api_key or self.api_key == 'your_api_key_here':
            raise ValueError(
                "GEMINI_API_KEY is required. Get your API key from "
                "https://aistudio.google.com/apikey and set it in your .env file"
            )
    
    def get_chunking_config(self) -> dict:
        """Get chunking configuration for file uploads."""
        return {
            'chunking_config': {
                'white_space_config': {
                    'max_tokens_per_chunk': self.max_tokens_per_chunk,
                    'max_overlap_tokens': self.max_overlap_tokens
                }
            }
        }

# Global settings instance
settings = Settings()