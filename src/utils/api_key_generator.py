"""
API Key Generator Utility for IntenseRP API
Generates secure API keys with the format: intense-<random_string>
"""

import secrets
import string
from typing import List, Set


class APIKeyGenerator:
    """Generates secure API keys for IntenseRP API authentication"""
    
    # Characters for key generation (alphanumeric)
    KEY_CHARS = string.ascii_letters + string.digits
    
    # Key format configuration
    PREFIX = "intense-"
    RANDOM_LENGTH = 32  # Length of random part
    TOTAL_MIN_LENGTH = 16  # Minimum total length for validation
    
    @classmethod
    def generate_key(cls) -> str:
        """
        Generate a new secure API key
        
        Returns:
            str: API key in format 'intense-<32_random_chars>'
        
        Example:
            'intense-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'
        """
        # Generate cryptographically secure random string
        random_part = ''.join(secrets.choice(cls.KEY_CHARS) for _ in range(cls.RANDOM_LENGTH))
        
        return f"{cls.PREFIX}{random_part}"
    
    @classmethod
    def generate_multiple_keys(cls, count: int) -> List[str]:
        """
        Generate multiple unique API keys
        
        Args:
            count: Number of keys to generate
            
        Returns:
            List[str]: List of unique API keys
        """
        if count <= 0:
            return []
        
        keys = set()
        while len(keys) < count:
            keys.add(cls.generate_key())
        
        return list(keys)
    
    @classmethod
    def is_valid_format(cls, key: str) -> bool:
        """
        Check if a key matches the expected format
        
        Args:
            key: API key to validate
            
        Returns:
            bool: True if key matches format, False otherwise
        """
        if not key or not isinstance(key, str):
            return False
        
        # Check prefix
        if not key.startswith(cls.PREFIX):
            return False
        
        # Check total length
        if len(key) < cls.TOTAL_MIN_LENGTH:
            return False
        
        # Check random part contains only valid characters
        random_part = key[len(cls.PREFIX):]
        if not all(c in cls.KEY_CHARS for c in random_part):
            return False
        
        return True
    
    @classmethod
    def extract_existing_keys(cls, keys_text: str) -> Set[str]:
        """
        Extract existing keys from textarea content
        
        Args:
            keys_text: Content from API keys textarea
            
        Returns:
            Set[str]: Set of existing valid keys
        """
        if not keys_text:
            return set()
        
        existing_keys = set()
        for line in keys_text.strip().split('\n'):
            key = line.strip()
            if key and len(key) >= cls.TOTAL_MIN_LENGTH:
                existing_keys.add(key)
        
        return existing_keys
    
    @classmethod
    def add_key_to_textarea(cls, current_content: str, new_key: str) -> str:
        """
        Add a new key to existing textarea content
        
        Args:
            current_content: Current content of the textarea
            new_key: New key to add
            
        Returns:
            str: Updated textarea content
        """
        if not current_content or not current_content.strip():
            return new_key
        
        # Check if key already exists
        existing_keys = cls.extract_existing_keys(current_content)
        if new_key in existing_keys:
            return current_content  # Don't add duplicates
        
        # Add new key on a new line
        content = current_content.rstrip()
        return f"{content}\n{new_key}"


# Convenience functions for direct use
def generate_api_key() -> str:
    """Generate a single API key"""
    return APIKeyGenerator.generate_key()

def generate_multiple_api_keys(count: int) -> List[str]:
    """Generate multiple API keys"""
    return APIKeyGenerator.generate_multiple_keys(count)

def is_intense_api_key(key: str) -> bool:
    """Check if key matches IntenseRP format"""
    return APIKeyGenerator.is_valid_format(key)