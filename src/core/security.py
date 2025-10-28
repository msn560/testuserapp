"""
Security module - Güvenlik işlemleri

Bu modül uygulamanın güvenlik işlemlerini yönetir.
Şifreleme, hashleme, token doğrulama ve güvenlik kontrolleri.
"""

import hashlib
import secrets
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from .constants import LogLevel
from ..utils.logger import logger


class SecurityManager:
    """
    Güvenlik işlemlerini yöneten ana sınıf.
    
    Bu sınıf şifreleme, hashleme, token yönetimi ve güvenlik kontrollerini sağlar.
    """
    
    def __init__(self, secret_key: str = None):
        """
        SecurityManager'ı başlatır.
        
        Args:
            secret_key: Şifreleme için kullanılacak gizli anahtar
        """
        from ..core.config_manager import get_config_value
        
        self.logger = logger
        
        # Config'den güvenlik ayarlarını yükle
        self.secret_key = secret_key or get_config_value("security.jwt_secret_key") or self._generate_secret_key()
        self.encryption_key = self._derive_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        # JWT ayarları - config'den yükle
        self.jwt_algorithm = get_config_value("security.jwt_algorithm", "HS256")
        self.jwt_expiration = timedelta(minutes=get_config_value("security.jwt_access_token_expire_minutes", 30))
        self.jwt_refresh_expiration = timedelta(days=get_config_value("security.jwt_refresh_token_expire_days", 7))
        
        # Güvenlik ayarları - config'den yükle
        self.max_login_attempts = get_config_value("security.max_login_attempts", 5)
        self.lockout_duration = timedelta(minutes=get_config_value("security.lockout_duration_minutes", 15))
        self.password_min_length = get_config_value("security.password_min_length", 8)
        self.bcrypt_rounds = get_config_value("security.bcrypt_rounds", 12)
        
        # Parola gereksinimleri - config'den yükle
        self.password_requirements = {
            "min_length": self.password_min_length,
            "require_uppercase": get_config_value("security.password_require_uppercase", True),
            "require_lowercase": get_config_value("security.password_require_lowercase", True),
            "require_numbers": get_config_value("security.password_require_numbers", True),
            "require_special": get_config_value("security.password_require_special_chars", True)
        }
    
    def hash_password(self, password: str) -> str:
        """
        Parolayı güvenli şekilde hashler.
        
        Args:
            password: Hashlenecek parola
            
        Returns:
            Hashlenmiş parola
        """
        try:
            # bcrypt ile hashleme - config'den rounds değerini kullan
            salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Parola hashleme hatası: {e}")
            raise
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Parolanın doğruluğunu kontrol eder.
        
        Args:
            password: Kontrol edilecek parola
            hashed_password: Hashlenmiş parola
            
        Returns:
            True if password is correct, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Parola doğrulama hatası: {e}")
            return False
    
    def generate_token(self, user_id: int, user_data: Dict[str, Any] = None) -> str:
        """
        JWT token oluşturur.
        
        Args:
            user_id: Kullanıcı ID'si
            user_data: Token'a eklenecek ek kullanıcı verileri
            
        Returns:
            JWT token
        """
        try:
            payload = {
                "user_id": user_id,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + self.jwt_expiration,
                "type": "access"
            }
            
            if user_data:
                payload.update(user_data)
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.jwt_algorithm)
            return token
            
        except Exception as e:
            self.logger.error(f"Token oluşturma hatası: {e}")
            raise
    
    def generate_refresh_token(self, user_id: int) -> str:
        """
        Refresh token oluşturur.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Refresh token
        """
        try:
            payload = {
                "user_id": user_id,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + self.jwt_refresh_expiration,
                "type": "refresh"
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.jwt_algorithm)
            return token
            
        except Exception as e:
            self.logger.error(f"Refresh token oluşturma hatası: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        JWT token'ı doğrular.
        
        Args:
            token: Doğrulanacak token
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token süresi dolmuş")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Geçersiz token: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Token doğrulama hatası: {e}")
            return None
    
    def encrypt_data(self, data: str) -> str:
        """
        Veriyi şifreler.
        
        Args:
            data: Şifrelenecek veri
            
        Returns:
            Şifrelenmiş veri
        """
        try:
            encrypted_data = self.fernet.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Veri şifreleme hatası: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Şifrelenmiş veriyi çözer.
        
        Args:
            encrypted_data: Çözülecek şifrelenmiş veri
            
        Returns:
            Çözülmüş veri
        """
        try:
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Veri çözme hatası: {e}")
            raise
    
    def generate_api_key(self) -> str:
        """
        API anahtarı oluşturur.
        
        Returns:
            API anahtarı
        """
        try:
            # Güvenli rastgele API anahtarı oluştur
            api_key = secrets.token_urlsafe(32)
            return f"api_{api_key}"
            
        except Exception as e:
            self.logger.error(f"API anahtarı oluşturma hatası: {e}")
            raise
    
    def hash_api_key(self, api_key: str) -> str:
        """
        API anahtarını hashler.
        
        Args:
            api_key: Hashlenecek API anahtarı
            
        Returns:
            Hashlenmiş API anahtarı
        """
        try:
            return hashlib.sha256(api_key.encode('utf-8')).hexdigest()
            
        except Exception as e:
            self.logger.error(f"API anahtarı hashleme hatası: {e}")
            raise
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Parola gücünü kontrol eder.
        
        Args:
            password: Kontrol edilecek parola
            
        Returns:
            Validation sonucu
        """
        try:
            result = {
                "is_valid": True,
                "errors": [],
                "strength": "weak"
            }
            
            # Minimum uzunluk kontrolü
            if len(password) < self.password_requirements["min_length"]:
                result["is_valid"] = False
                result["errors"].append(f"Parola en az {self.password_requirements['min_length']} karakter olmalı")
            
            # Büyük harf kontrolü
            if self.password_requirements["require_uppercase"] and not any(c.isupper() for c in password):
                result["is_valid"] = False
                result["errors"].append("Parola en az bir büyük harf içermeli")
            
            # Küçük harf kontrolü
            if self.password_requirements["require_lowercase"] and not any(c.islower() for c in password):
                result["is_valid"] = False
                result["errors"].append("Parola en az bir küçük harf içermeli")
            
            # Sayı kontrolü
            if self.password_requirements["require_numbers"] and not any(c.isdigit() for c in password):
                result["is_valid"] = False
                result["errors"].append("Parola en az bir sayı içermeli")
            
            # Özel karakter kontrolü
            if self.password_requirements["require_special"] and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                result["is_valid"] = False
                result["errors"].append("Parola en az bir özel karakter içermeli")
            
            # Güç hesaplama
            if result["is_valid"]:
                strength_score = 0
                if len(password) >= 12:
                    strength_score += 2
                elif len(password) >= 8:
                    strength_score += 1
                
                if any(c.isupper() for c in password):
                    strength_score += 1
                if any(c.islower() for c in password):
                    strength_score += 1
                if any(c.isdigit() for c in password):
                    strength_score += 1
                if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                    strength_score += 1
                
                if strength_score >= 5:
                    result["strength"] = "strong"
                elif strength_score >= 3:
                    result["strength"] = "medium"
                else:
                    result["strength"] = "weak"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Parola gücü kontrolü hatası: {e}")
            return {"is_valid": False, "errors": ["Parola kontrolü sırasında hata oluştu"], "strength": "unknown"}
    
    def sanitize_input(self, input_data: str) -> str:
        """
        Kullanıcı girişini temizler.
        
        Args:
            input_data: Temizlenecek veri
            
        Returns:
            Temizlenmiş veri
        """
        try:
            # HTML etiketlerini kaldır
            import re
            clean_data = re.sub(r'<[^>]+>', '', input_data)
            
            # SQL injection karakterlerini escape et
            clean_data = clean_data.replace("'", "''")
            clean_data = clean_data.replace(";", "")
            clean_data = clean_data.replace("--", "")
            clean_data = clean_data.replace("/*", "")
            clean_data = clean_data.replace("*/", "")
            
            # XSS karakterlerini escape et
            clean_data = clean_data.replace("<", "&lt;")
            clean_data = clean_data.replace(">", "&gt;")
            clean_data = clean_data.replace('"', "&quot;")
            clean_data = clean_data.replace("'", "&#x27;")
            clean_data = clean_data.replace("/", "&#x2F;")
            
            return clean_data.strip()
            
        except Exception as e:
            self.logger.error(f"Input temizleme hatası: {e}")
            return input_data
    
    def check_ip_whitelist(self, ip_address: str, whitelist: List[str]) -> bool:
        """
        IP adresinin whitelist'te olup olmadığını kontrol eder.
        
        Args:
            ip_address: Kontrol edilecek IP adresi
            whitelist: IP whitelist'i
            
        Returns:
            True if IP is whitelisted, False otherwise
        """
        try:
            return ip_address in whitelist
            
        except Exception as e:
            self.logger.error(f"IP whitelist kontrolü hatası: {e}")
            return False
    
    def check_ip_blacklist(self, ip_address: str, blacklist: List[str]) -> bool:
        """
        IP adresinin blacklist'te olup olmadığını kontrol eder.
        
        Args:
            ip_address: Kontrol edilecek IP adresi
            blacklist: IP blacklist'i
            
        Returns:
            True if IP is blacklisted, False otherwise
        """
        try:
            return ip_address in blacklist
            
        except Exception as e:
            self.logger.error(f"IP blacklist kontrolü hatası: {e}")
            return False
    
    def generate_csrf_token(self) -> str:
        """
        CSRF token oluşturur.
        
        Returns:
            CSRF token
        """
        try:
            return secrets.token_urlsafe(32)
            
        except Exception as e:
            self.logger.error(f"CSRF token oluşturma hatası: {e}")
            raise
    
    def verify_csrf_token(self, token: str, session_token: str) -> bool:
        """
        CSRF token'ı doğrular.
        
        Args:
            token: Doğrulanacak token
            session_token: Session'daki token
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            return token == session_token
            
        except Exception as e:
            self.logger.error(f"CSRF token doğrulama hatası: {e}")
            return False
    
    def _generate_secret_key(self) -> str:
        """
        Gizli anahtar oluşturur.
        
        Returns:
            Gizli anahtar
        """
        try:
            return secrets.token_urlsafe(32)
            
        except Exception as e:
            self.logger.error(f"Gizli anahtar oluşturma hatası: {e}")
            raise
    
    def _derive_encryption_key(self) -> bytes:
        """
        Şifreleme anahtarı türetir.
        
        Returns:
            Şifreleme anahtarı
        """
        try:
            # PBKDF2 ile anahtar türetme
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'api_server_manager_salt',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
            return key
            
        except Exception as e:
            self.logger.error(f"Şifreleme anahtarı türetme hatası: {e}")
            raise
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Güvenlik durumunu döndürür.
        
        Returns:
            Güvenlik durumu bilgileri
        """
        try:
            return {
                "password_requirements": self.password_requirements,
                "jwt_expiration_hours": self.jwt_expiration.total_seconds() / 3600,
                "jwt_refresh_expiration_days": self.jwt_refresh_expiration.days,
                "max_login_attempts": self.max_login_attempts,
                "lockout_duration_minutes": self.lockout_duration.total_seconds() / 60,
                "encryption_enabled": True,
                "csrf_protection_enabled": True
            }
            
        except Exception as e:
            self.logger.error(f"Güvenlik durumu alınamadı: {e}")
            return {}


# Global instance
security_manager = SecurityManager()
