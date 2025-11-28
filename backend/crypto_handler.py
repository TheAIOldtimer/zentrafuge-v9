"""
crypto_handler.py - Encryption and data validation utilities for Zentrafuge v9

Provides:
- DataValidator: Input sanitization and validation
- encrypt_text / decrypt_text: AES encryption at rest using Fernet
- Master key management from environment variable
"""

import os
import re
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# ============================================================================
# ENCRYPTION KEY MANAGEMENT
# ============================================================================

_FERNET_INSTANCE = None


def get_fernet() -> Fernet:
    """
    Get or create the Fernet encryption instance.
    Uses ZENTRAFUGE_MASTER_KEY from environment, or generates temporary key.
    """
    global _FERNET_INSTANCE
    if _FERNET_INSTANCE is not None:
        return _FERNET_INSTANCE

    key = os.getenv("ZENTRAFUGE_MASTER_KEY")
    if not key:
        # Generate a temporary key for development
        key = Fernet.generate_key().decode("utf-8")
        logger.warning(
            "⚠️ ZENTRAFUGE_MASTER_KEY not set; using temporary in-memory key. "
            "All encrypted data will be unreadable after restart. "
            "Set ZENTRAFUGE_MASTER_KEY in production!"
        )
    else:
        # Key from env may be plain string; ensure bytes
        if not isinstance(key, bytes):
            key = key.encode("utf-8")

    _FERNET_INSTANCE = Fernet(key)
    logger.info("🔐 Encryption key initialized successfully")
    return _FERNET_INSTANCE


def encrypt_text(plain: str | None) -> str:
    """
    Encrypt plaintext string using Fernet (AES-128).
    
    Args:
        plain: Plaintext string to encrypt
        
    Returns:
        Base64-encoded ciphertext as string, or empty string if input is None
        
    Note:
        Never raises exceptions - returns original value on failure
    """
    if plain is None:
        return ""
    
    # Ensure string type
    if not isinstance(plain, str):
        plain = str(plain)
    
    if not plain:
        return ""
    
    try:
        fernet = get_fernet()
        encrypted_bytes = fernet.encrypt(plain.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"❌ Encryption failed: {e}")
        # Return original to avoid breaking write paths
        return plain


def decrypt_text(cipher: str | None) -> str:
    """
    Decrypt Fernet-encrypted ciphertext.
    
    Args:
        cipher: Base64-encoded ciphertext string
        
    Returns:
        Decrypted plaintext string
        
    Note:
        If decryption fails (legacy plaintext, wrong key, corrupted), 
        returns the original value unchanged. Never raises exceptions.
    """
    if cipher is None or cipher == "":
        return cipher if cipher is not None else ""
    
    if not isinstance(cipher, str):
        return str(cipher)
    
    try:
        fernet = get_fernet()
        decrypted_bytes = fernet.decrypt(cipher.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken:
        # Likely legacy plaintext or encrypted with different key
        logger.debug("Decrypt failed (InvalidToken) - returning original value")
        return cipher
    except Exception as e:
        # Any other error - assume plaintext
        logger.debug(f"Decrypt failed ({type(e).__name__}) - returning original value")
        return cipher


# ============================================================================
# DATA VALIDATION
# ============================================================================

class DataValidator:
    """
    Validates and sanitizes user input for security.
    
    Provides basic protection against:
    - XSS attempts
    - SQL injection patterns
    - Excessive whitespace
    - Control characters
    """
    
    # Dangerous patterns to remove
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'onclick\s*=',
        r'<iframe[^>]*>',
        r'<embed[^>]*>',
        r'<object[^>]*>',
    ]
    
    SQL_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
        r'(--|;|\/\*|\*\/)',
        r'(\bUNION\b.*\bSELECT\b)',
    ]
    
    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """
        Sanitize user input by removing dangerous patterns.
        
        Args:
            text: Raw user input string
            
        Returns:
            Cleaned string safe for processing
        """
        if not text or not isinstance(text, str):
            return ""
        
        cleaned = text
        
        # Remove XSS patterns
        for pattern in DataValidator.XSS_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove SQL injection patterns (but allow normal conversation)
        for pattern in DataValidator.SQL_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove control characters except newlines and tabs
        cleaned = ''.join(
            char for char in cleaned 
            if char.isprintable() or char in '\n\t'
        )
        
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Limit length (prevent memory exhaustion)
        max_length = 10000
        if len(cleaned) > max_length:
            logger.warning(f"Input truncated from {len(cleaned)} to {max_length} chars")
            cleaned = cleaned[:max_length]
        
        return cleaned.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Basic email validation.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email format is valid
        """
        if not email or not isinstance(email, str):
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """
        Validate Firebase user ID format.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if format is valid
        """
        if not user_id or not isinstance(user_id, str):
            return False
        
        # Firebase UIDs are typically 28 characters, alphanumeric
        return len(user_id) >= 10 and user_id.isalnum()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "DataValidator",
    "encrypt_text",
    "decrypt_text",
    "get_fernet",
]
