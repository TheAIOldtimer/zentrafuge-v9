#!/usr/bin/env python3
"""
Zentrafuge v9 - Cryptographic Handler
Secure encryption/decryption for sensitive memory storage
"""

import os
import base64
import secrets
import logging
from typing import Optional  # ✅ FIXED THIS LINE
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ... rest of the file stays the same

logger = logging.getLogger(__name__)

class MemoryEncryption:
    """
    Handles encryption and decryption of sensitive memory data
    Uses Fernet (AES 128 in CBC mode) for symmetric encryption
    """
    
    def __init__(self, master_key: str = None):
        """
        Initialize encryption handler
        
        Args:
            master_key: Optional master key, otherwise derived from environment
        """
        self.master_key = master_key or self._get_or_create_master_key()
        self.fernet = self._create_fernet_instance()
    
    def _get_or_create_master_key(self) -> str:
        """
        Get master key from environment or create new one
        In production, this should be stored securely (e.g., Azure Key Vault)
        """
        master_key = os.getenv('ZENTRAFUGE_MASTER_KEY')
        
        if not master_key:
            # Generate new master key
            master_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
            logger.warning("Generated new master key - store this securely!")
            logger.warning(f"ZENTRAFUGE_MASTER_KEY={master_key}")
        
        return master_key
    
    def _create_fernet_instance(self) -> Fernet:
        """
        Create Fernet encryption instance from master key
        
        Returns:
            Configured Fernet instance for encryption/decryption
        """
        try:
            # Derive key from master key using PBKDF2
            master_key_bytes = self.master_key.encode()
            salt = b'zentrafuge_v9_salt'  # Static salt for consistency
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(master_key_bytes))
            return Fernet(key)
            
        except Exception as e:
            logger.error(f"Failed to create Fernet instance: {e}")
            raise
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt string data
        
        Args:
            data: Plain text string to encrypt
            
        Returns:
            Base64 encoded encrypted data
        """
        try:
            if not isinstance(data, str):
                raise ValueError("Data must be a string")
            
            # Convert to bytes and encrypt
            data_bytes = data.encode('utf-8')
            encrypted_bytes = self.fernet.encrypt(data_bytes)
            
            # Return base64 encoded string for storage
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted string data
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted plain text string
        """
        try:
            if not isinstance(encrypted_data, str):
                raise ValueError("Encrypted data must be a string")
            
            # Decode from base64 and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            
            # Return decoded string
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data_dict: dict) -> str:
        """
        Encrypt dictionary data (converts to JSON first)
        
        Args:
            data_dict: Dictionary to encrypt
            
        Returns:
            Base64 encoded encrypted JSON string
        """
        import json
        try:
            json_string = json.dumps(data_dict, ensure_ascii=False)
            return self.encrypt_data(json_string)
        except Exception as e:
            logger.error(f"Dictionary encryption failed: {e}")
            raise
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """
        Decrypt data back to dictionary
        
        Args:
            encrypted_data: Base64 encoded encrypted JSON
            
        Returns:
            Decrypted dictionary
        """
        import json
        try:
            json_string = self.decrypt_data(encrypted_data)
            return json.loads(json_string)
        except Exception as e:
            logger.error(f"Dictionary decryption failed: {e}")
            raise
    
    def rotate_key(self, new_master_key: str = None) -> str:
        """
        Rotate encryption key (creates new Fernet instance)
        WARNING: This will invalidate all existing encrypted data!
        
        Args:
            new_master_key: Optional new master key, otherwise generates one
            
        Returns:
            New master key that was set
        """
        try:
            if new_master_key:
                self.master_key = new_master_key
            else:
                self.master_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
            
            # Create new Fernet instance
            self.fernet = self._create_fernet_instance()
            
            logger.info("Encryption key rotated successfully")
            logger.warning("All existing encrypted data is now invalid!")
            
            return self.master_key
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise
    
    def test_encryption(self) -> bool:
        """
        Test encryption/decryption functionality
        
        Returns:
            True if encryption is working correctly
        """
        try:
            test_data = "Hello, Zentrafuge v9! 🧠💙"
            
            # Encrypt and decrypt
            encrypted = self.encrypt_data(test_data)
            decrypted = self.decrypt_data(encrypted)
            
            # Test dictionary encryption
            test_dict = {"message": "test", "number": 42, "active": True}
            encrypted_dict = self.encrypt_dict(test_dict)
            decrypted_dict = self.decrypt_dict(encrypted_dict)
            
            # Verify results
            if decrypted == test_data and decrypted_dict == test_dict:
                logger.info("Encryption test passed")
                return True
            else:
                logger.error("Encryption test failed - data mismatch")
                return False
                
        except Exception as e:
            logger.error(f"Encryption test failed: {e}")
            return False
    
    def get_key_info(self) -> dict:
        """
        Get information about current encryption setup
        
        Returns:
            Dictionary with key information (no sensitive data)
        """
        return {
            'key_set': bool(self.master_key),
            'key_length': len(self.master_key) if self.master_key else 0,
            'fernet_initialized': self.fernet is not None,
            'algorithm': 'Fernet (AES 128 CBC + HMAC SHA256)',
            'key_derivation': 'PBKDF2-HMAC-SHA256 (100k iterations)'
        }


class SecureTokenGenerator:
    """
    Generate secure tokens for session management and API keys
    """
    
    @staticmethod
    def generate_session_token(length: int = 32) -> str:
        """
        Generate cryptographically secure session token
        
        Args:
            length: Token length in bytes
            
        Returns:
            URL-safe base64 encoded token
        """
        token_bytes = secrets.token_bytes(length)
        return base64.urlsafe_b64encode(token_bytes).decode('utf-8')
    
    @staticmethod
    def generate_api_key(prefix: str = "zf", length: int = 24) -> str:
        """
        Generate API key with prefix
        
        Args:
            prefix: Key prefix for identification
            length: Random portion length in bytes
            
        Returns:
            API key in format: prefix_base64token
        """
        token_bytes = secrets.token_bytes(length)
        token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        return f"{prefix}_{token}"
    
    @staticmethod
    def generate_user_id(length: int = 16) -> str:
        """
        Generate unique user identifier
        
        Args:
            length: ID length in bytes
            
        Returns:
            URL-safe base64 encoded user ID
        """
        id_bytes = secrets.token_bytes(length)
        return base64.urlsafe_b64encode(id_bytes).decode('utf-8')


class DataValidator:
    """
    Validate and sanitize data before encryption
    """
    
    @staticmethod
    def validate_memory_content(content: dict) -> bool:
        """
        Validate memory content structure
        
        Args:
            content: Memory content dictionary
            
        Returns:
            True if content is valid for encryption
        """
        try:
            # Check if content is serializable
            import json
            json.dumps(content)
            
            # Check for reasonable size (< 1MB when serialized)
            content_size = len(json.dumps(content).encode('utf-8'))
            if content_size > 1024 * 1024:  # 1MB limit
                logger.warning(f"Memory content too large: {content_size} bytes")
                return False
            
            # Check for forbidden keys (if any)
            forbidden_keys = ['__proto__', 'constructor', 'prototype']
            if any(key in str(content) for key in forbidden_keys):
                logger.warning("Memory content contains forbidden keys")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Memory content validation failed: {e}")
            return False
    
    @staticmethod
    def sanitize_user_input(user_input: str, max_length: int = 10000) -> str:
        """
        Sanitize user input before storage
        
        Args:
            user_input: Raw user input string
            max_length: Maximum allowed length
            
        Returns:
            Sanitized input string
        """
        try:
            if not isinstance(user_input, str):
                user_input = str(user_input)
            
            # Truncate if too long
            if len(user_input) > max_length:
                user_input = user_input[:max_length]
                logger.warning(f"User input truncated to {max_length} characters")
            
            # Remove null bytes and other control characters
            user_input = ''.join(char for char in user_input if ord(char) >= 32 or char in '\n\r\t')
            
            # Strip excessive whitespace
            user_input = ' '.join(user_input.split())
            
            return user_input
            
        except Exception as e:
            logger.error(f"Input sanitization failed: {e}")
            return ""


# Utility functions for easy access
def create_encryption_handler(master_key: str = None) -> MemoryEncryption:
    """
    Factory function to create encryption handler
    
    Args:
        master_key: Optional master key
        
    Returns:
        Configured MemoryEncryption instance
    """
    return MemoryEncryption(master_key)


def test_crypto_system() -> bool:
    """
    Test the entire crypto system
    
    Returns:
        True if all tests pass
    """
    try:
        # Test encryption handler
        encryption = MemoryEncryption()
        if not encryption.test_encryption():
            return False
        
        # Test token generation
        session_token = SecureTokenGenerator.generate_session_token()
        api_key = SecureTokenGenerator.generate_api_key()
        user_id = SecureTokenGenerator.generate_user_id()
        
        if not all([session_token, api_key, user_id]):
            logger.error("Token generation failed")
            return False
        
        # Test data validation
        test_content = {"message": "test", "data": [1, 2, 3]}
        if not DataValidator.validate_memory_content(test_content):
            logger.error("Data validation failed")
            return False
        
        logger.info("All crypto system tests passed")
        return True
        
    except Exception as e:
        logger.error(f"Crypto system test failed: {e}")
        return False


if __name__ == "__main__":
    # Run tests if executed directly
    print("Testing Zentrafuge v9 Crypto System...")
    
    if test_crypto_system():
        print("✅ All crypto tests passed!")
    else:
        print("❌ Crypto tests failed!")
        exit(1)
