"""
Token Service module - Token yönetimi

Bu modül JWT token'larının oluşturulması, doğrulanması ve yönetimini sağlar.
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import secrets
import threading

from ..core.constants import LogLevel
from ..core.security import security_manager
from ..db.models import User, Session
from ..utils.logger import logger


class TokenService:
    """
    Token yönetimi servisi.
    
    Bu sınıf JWT token'larının oluşturulması, doğrulanması ve yönetimini sağlar.
    """
    
    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        """
        TokenService'i başlatır.
        
        Args:
            secret_key: JWT secret key
            algorithm: JWT algoritması
        """
        self.logger = logger
        self.secret_key = secret_key or security_manager.secret_key
        self.algorithm = algorithm
        
        # Token ayarları
        self.access_token_expiry = timedelta(hours=24)
        self.refresh_token_expiry = timedelta(days=7)
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Token blacklist (logout edilen token'lar)
        self.token_blacklist: set = set()
        
        # Token istatistikleri
        self.stats = {
            "tokens_created": 0,
            "tokens_validated": 0,
            "tokens_refreshed": 0,
            "tokens_blacklisted": 0,
            "validation_failures": 0
        }
    
    def create_access_token(self, user_id: int, user_data: Dict[str, Any] = None) -> str:
        """
        Access token oluşturur.
        
        Args:
            user_id: Kullanıcı ID'si
            user_data: Ek kullanıcı verileri
            
        Returns:
            Access token
        """
        try:
            payload = {
                "user_id": user_id,
                "token_type": "access",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + self.access_token_expiry,
                "jti": self._generate_jti()  # JWT ID
            }
            
            if user_data:
                payload.update(user_data)
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            with self.lock:
                self.stats["tokens_created"] += 1
            
            self.logger.debug(f"Access token created for user {user_id}")
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to create access token for user {user_id}: {e}")
            return None
    
    def create_refresh_token(self, user_id: int) -> str:
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
                "token_type": "refresh",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + self.refresh_token_expiry,
                "jti": self._generate_jti()
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            with self.lock:
                self.stats["tokens_created"] += 1
            
            self.logger.debug(f"Refresh token created for user {user_id}")
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to create refresh token for user {user_id}: {e}")
            return None
    
    def create_token_pair(self, user_id: int, user_data: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Access ve refresh token çifti oluşturur.
        
        Args:
            user_id: Kullanıcı ID'si
            user_data: Ek kullanıcı verileri
            
        Returns:
            Token çifti dictionary'si
        """
        try:
            access_token = self.create_access_token(user_id, user_data)
            refresh_token = self.create_refresh_token(user_id)
            
            if not access_token or not refresh_token:
                return None
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": int(self.access_token_expiry.total_seconds())
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create token pair for user {user_id}: {e}")
            return None
    
    def validate_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Token'ı doğrular.
        
        Args:
            token: Doğrulanacak token
            token_type: Token türü (access, refresh)
            
        Returns:
            Token payload veya None
        """
        try:
            # Token blacklist kontrolü
            if self.is_token_blacklisted(token):
                self.logger.warning("Token is blacklisted")
                with self.lock:
                    self.stats["validation_failures"] += 1
                return None
            
            # Token'ı decode et
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Token türü kontrolü
            if payload.get("token_type") != token_type:
                self.logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('token_type')}")
                with self.lock:
                    self.stats["validation_failures"] += 1
                return None
            
            # Kullanıcı var mı kontrol et
            user_id = payload.get("user_id")
            if not user_id:
                self.logger.warning("Token missing user_id")
                with self.lock:
                    self.stats["validation_failures"] += 1
                return None
            
            # Kullanıcı aktif mi kontrol et
            try:
                user = User.get_by_id(user_id)
                if not user or not user.is_active:
                    self.logger.warning(f"User {user_id} is inactive or not found")
                    with self.lock:
                        self.stats["validation_failures"] += 1
                    return None
            except Exception as e:
                self.logger.error(f"Error checking user {user_id}: {e}")
                with self.lock:
                    self.stats["validation_failures"] += 1
                return None
            
            with self.lock:
                self.stats["tokens_validated"] += 1
            
            self.logger.debug(f"Token validated for user {user_id}")
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token has expired")
            with self.lock:
                self.stats["validation_failures"] += 1
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid token: {e}")
            with self.lock:
                self.stats["validation_failures"] += 1
            return None
        except Exception as e:
            self.logger.error(f"Error validating token: {e}")
            with self.lock:
                self.stats["validation_failures"] += 1
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Access token'ı yeniler.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Yeni token çifti veya None
        """
        try:
            # Refresh token'ı doğrula
            payload = self.validate_token(refresh_token, "refresh")
            if not payload:
                return None
            
            user_id = payload.get("user_id")
            
            # Yeni token çifti oluştur
            new_tokens = self.create_token_pair(user_id)
            if not new_tokens:
                return None
            
            # Eski refresh token'ı blacklist'e ekle
            self.blacklist_token(refresh_token)
            
            with self.lock:
                self.stats["tokens_refreshed"] += 1
            
            self.logger.info(f"Access token refreshed for user {user_id}")
            return new_tokens
            
        except Exception as e:
            self.logger.error(f"Failed to refresh access token: {e}")
            return None
    
    def blacklist_token(self, token: str) -> bool:
        """
        Token'ı blacklist'e ekler.
        
        Args:
            token: Blacklist'e eklenecek token
            
        Returns:
            True if blacklisted successfully, False otherwise
        """
        try:
            with self.lock:
                self.token_blacklist.add(token)
                self.stats["tokens_blacklisted"] += 1
            
            self.logger.debug("Token blacklisted")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to blacklist token: {e}")
            return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Token blacklist'te mi kontrol eder.
        
        Args:
            token: Kontrol edilecek token
            
        Returns:
            True if blacklisted, False otherwise
        """
        try:
            with self.lock:
                return token in self.token_blacklist
                
        except Exception as e:
            self.logger.error(f"Error checking token blacklist: {e}")
            return False
    
    def revoke_user_tokens(self, user_id: int) -> int:
        """
        Kullanıcının tüm token'larını iptal eder.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            İptal edilen token sayısı
        """
        try:
            # Kullanıcının aktif session'larını bul
            sessions = Session.select().where(
                (Session.user_id == user_id) & (Session.is_active == True)
            )
            
            revoked_count = 0
            for session in sessions:
                # Session token'ını blacklist'e ekle
                if self.blacklist_token(session.token):
                    revoked_count += 1
                
                # Refresh token'ı da blacklist'e ekle
                if session.refresh_token:
                    self.blacklist_token(session.refresh_token)
            
            # Session'ları deaktif et
            Session.update(is_active=False).where(
                (Session.user_id == user_id) & (Session.is_active == True)
            ).execute()
            
            self.logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
            return revoked_count
            
        except Exception as e:
            self.logger.error(f"Failed to revoke tokens for user {user_id}: {e}")
            return 0
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Token bilgilerini döndürür (decode etmeden).
        
        Args:
            token: Token
            
        Returns:
            Token bilgileri veya None
        """
        try:
            # Token'ı decode et (doğrulama yapmadan)
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            
            return {
                "user_id": payload.get("user_id"),
                "token_type": payload.get("token_type"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
                "jti": payload.get("jti"),
                "is_expired": datetime.utcnow().timestamp() > payload.get("exp", 0),
                "is_blacklisted": self.is_token_blacklisted(token)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get token info: {e}")
            return None
    
    def cleanup_expired_tokens(self) -> int:
        """
        Süresi dolmuş token'ları temizler.
        
        Returns:
            Temizlenen token sayısı
        """
        try:
            current_time = datetime.utcnow().timestamp()
            cleaned_count = 0
            
            with self.lock:
                # Blacklist'teki süresi dolmuş token'ları temizle
                expired_tokens = []
                for token in self.token_blacklist:
                    try:
                        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
                        if payload.get("exp", 0) < current_time:
                            expired_tokens.append(token)
                    except:
                        # Geçersiz token'ları da temizle
                        expired_tokens.append(token)
                
                for token in expired_tokens:
                    self.token_blacklist.discard(token)
                    cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} expired tokens")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired tokens: {e}")
            return 0
    
    def get_token_statistics(self) -> Dict[str, Any]:
        """
        Token istatistiklerini döndürür.
        
        Returns:
            Token istatistikleri
        """
        try:
            with self.lock:
                total_validations = self.stats["tokens_validated"] + self.stats["validation_failures"]
                success_rate = (self.stats["tokens_validated"] / total_validations * 100) if total_validations > 0 else 0
                
                return {
                    "tokens_created": self.stats["tokens_created"],
                    "tokens_validated": self.stats["tokens_validated"],
                    "tokens_refreshed": self.stats["tokens_refreshed"],
                    "tokens_blacklisted": self.stats["tokens_blacklisted"],
                    "validation_failures": self.stats["validation_failures"],
                    "validation_success_rate": round(success_rate, 2),
                    "blacklist_size": len(self.token_blacklist),
                    "access_token_expiry_hours": self.access_token_expiry.total_seconds() / 3600,
                    "refresh_token_expiry_days": self.refresh_token_expiry.days
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get token statistics: {e}")
            return {}
    
    def _generate_jti(self) -> str:
        """
        JWT ID oluşturur.
        
        Returns:
            JWT ID
        """
        return secrets.token_urlsafe(32)


# Global instance
token_service = TokenService()
