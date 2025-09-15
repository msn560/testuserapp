"""
Crypto utilities for encryption, decryption, and hashing operations.

This module provides cryptographic utilities for secure data handling,
password hashing, and encryption/decryption operations.
"""

import hashlib
import secrets
import base64
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt


class CryptoUtils:
    """Cryptographic utilities for secure operations."""
    
    @staticmethod
    def generate_salt(length: int = 32) -> str:
        """
        Generate a cryptographically secure random salt.
        
        Args:
            length: Length of the salt in bytes
            
        Returns:
            Base64 encoded salt string
        """
        salt = secrets.token_bytes(length)
        return base64.b64encode(salt).decode('utf-8')
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            salt: Optional salt (if None, generates new salt)
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            # Generate new salt using bcrypt
            salt_bytes = bcrypt.gensalt()
            salt = salt_bytes.decode('utf-8')
        else:
            salt_bytes = salt.encode('utf-8')
        
        # Hash the password
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, salt_bytes)
        
        return hashed.decode('utf-8'), salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    
    @staticmethod
    def generate_key_from_password(password: str, salt: bytes) -> bytes:
        """
        Generate encryption key from password using PBKDF2.
        
        Args:
            password: Password string
            salt: Salt bytes
            
        Returns:
            Encryption key bytes
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @staticmethod
    def encrypt_data(data: str, key: bytes) -> str:
        """
        Encrypt data using Fernet encryption.
        
        Args:
            data: Data to encrypt
            key: Encryption key
            
        Returns:
            Encrypted data as base64 string
        """
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode('utf-8'))
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: bytes) -> str:
        """
        Decrypt data using Fernet decryption.
        
        Args:
            encrypted_data: Encrypted data as base64 string
            key: Decryption key
            
        Returns:
            Decrypted data string
            
        Raises:
            ValueError: If decryption fails
        """
        try:
            f = Fernet(key)
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = f.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """
        Generate a secure API key.
        
        Args:
            length: Length of the API key in bytes
            
        Returns:
            Base64 encoded API key
        """
        key = secrets.token_bytes(length)
        return base64.urlsafe_b64encode(key).decode('utf-8')
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """
        Hash an API key for storage.
        
        Args:
            api_key: Plain API key
            
        Returns:
            SHA-256 hash of the API key
        """
        return hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate a secure random token.
        
        Args:
            length: Length of the token in bytes
            
        Returns:
            URL-safe base64 encoded token
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_string(data: str, algorithm: str = 'sha256') -> str:
        """
        Hash a string using specified algorithm.
        
        Args:
            data: String to hash
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256', 'sha512')
            
        Returns:
            Hexadecimal hash string
        """
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(data.encode('utf-8'))
        return hash_obj.hexdigest()
    
    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """
        Compare two strings in constant time to prevent timing attacks.
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            True if strings are equal, False otherwise
        """
        return secrets.compare_digest(a, b)
    
    @staticmethod
    def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
        """
        Mask sensitive data for logging purposes.
        
        Args:
            data: Sensitive data to mask
            visible_chars: Number of characters to show at the end
            
        Returns:
            Masked data string
        """
        if len(data) <= visible_chars:
            return '*' * len(data)
        
        return '*' * (len(data) - visible_chars) + data[-visible_chars:]
    
    @staticmethod
    def generate_secure_filename(original_filename: str) -> str:
        """
        Generate a secure filename from original filename.
        
        Args:
            original_filename: Original filename
            
        Returns:
            Secure filename with random prefix
        """
        # Get file extension
        if '.' in original_filename:
            name, ext = original_filename.rsplit('.', 1)
            ext = f'.{ext}'
        else:
            name = original_filename
            ext = ''
        
        # Generate secure name
        secure_name = secrets.token_urlsafe(16)
        return f"{secure_name}{ext}"
    
    @staticmethod
    def validate_password_strength(password: str) -> dict:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'is_valid': True,
            'score': 0,
            'issues': []
        }
        
        # Length check
        if len(password) < 8:
            result['issues'].append('Password must be at least 8 characters long')
            result['is_valid'] = False
        else:
            result['score'] += 1
        
        # Uppercase check
        if not any(c.isupper() for c in password):
            result['issues'].append('Password must contain at least one uppercase letter')
        else:
            result['score'] += 1
        
        # Lowercase check
        if not any(c.islower() for c in password):
            result['issues'].append('Password must contain at least one lowercase letter')
        else:
            result['score'] += 1
        
        # Digit check
        if not any(c.isdigit() for c in password):
            result['issues'].append('Password must contain at least one digit')
        else:
            result['score'] += 1
        
        # Special character check
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            result['issues'].append('Password must contain at least one special character')
        else:
            result['score'] += 1
        
        # Common password check
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        if password.lower() in common_passwords:
            result['issues'].append('Password is too common')
            result['is_valid'] = False
        
        return result
