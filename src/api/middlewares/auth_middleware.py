"""
Auth Middleware

Bu middleware authentication işlemlerini yönetir.
"""

import jwt
from typing import Optional, Dict, Any
from aiohttp import web
from aiohttp.web import Request, Response, middleware

from ...core.settings import settings
from ...core.constants import API_PREFIX
from ...utils.logger import Logger
from ...db.models import User, Session, ApiKey


class AuthMiddleware:
    """Auth middleware sınıfı"""
    
    def __init__(self):
        """AuthMiddleware'ı başlat"""
        self.logger = Logger(__name__)
        self.jwt_secret = settings.security.jwt_secret_key
        self.jwt_algorithm = settings.security.jwt_algorithm
    
    @middleware
    async def middleware(self, request: Request, handler):
        """Auth middleware"""
        # Public endpoint'leri kontrol et
        if self._is_public_endpoint(request.path):
            return await handler(request)
        
        # Authentication token'ını al
        token = self._get_auth_token(request)
        
        if not token:
            return self._create_unauthorized_response("Token bulunamadı")
        
        # Token'ı doğrula
        user = await self._validate_token(token, request)
        
        if not user:
            return self._create_unauthorized_response("Geçersiz token")
        
        # User'ı request'e ekle
        request.user = user
        request.user_id = user.id
        
        # Request'i işle
        response = await handler(request)
        
        return response
    
    def _is_public_endpoint(self, path: str) -> bool:
        """
        Endpoint'in public olup olmadığını kontrol et
        
        Args:
            path: Request path
            
        Returns:
            Public endpoint mi
        """
        public_endpoints = [
            f"{API_PREFIX}/auth/login",
            f"{API_PREFIX}/auth/refresh",
            f"{API_PREFIX}/health",
            f"{API_PREFIX}/status"
        ]
        
        # Tam eşleşme kontrolü
        if path in public_endpoints:
            return True
        
        # OPTIONS request'leri her zaman public
        return False
    
    def _get_auth_token(self, request: Request) -> Optional[str]:
        """
        Request'ten auth token'ını al
        
        Args:
            request: Request objesi
            
        Returns:
            Auth token
        """
        # Authorization header'ından al
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]  # "Bearer " kısmını çıkar
        
        # Query parameter'ından al
        token = request.query.get('token')
        if token:
            return token
        
        # Cookie'den al
        token = request.cookies.get('auth_token')
        if token:
            return token
        
        return None
    
    async def _validate_token(self, token: str, request: Request) -> Optional[User]:
        """
        Token'ı doğrula ve user'ı döndür
        
        Args:
            token: Auth token
            request: Request objesi
            
        Returns:
            User objesi veya None
        """
        try:
            # JWT token'ı decode et
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            # Payload'dan user_id'yi al
            user_id = payload.get('user_id')
            if not user_id:
                return None
            
            # User'ı veritabanından al
            user = User.get_or_none(User.id == user_id, User.is_active == True)
            if not user:
                return None
            
            # Session'ı kontrol et
            session = Session.get_or_none(
                Session.user == user,
                Session.token == token,
                Session.is_active == True
            )
            
            if not session:
                return None
            
            # Session süresi kontrolü
            if session.is_expired():
                # Session'ı deaktif et
                session.is_active = False
                session.save()
                return None
            
            # Session aktivitesini güncelle
            session.update_activity()
            
            # User'ı request'e ekle
            request.session = session
            
            return user
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token süresi dolmuş")
            return None
        except jwt.InvalidTokenError:
            self.logger.warning("Geçersiz token")
            return None
        except Exception as e:
            self.logger.error(f"Token doğrulama hatası: {e}")
            return None
    
    def _create_unauthorized_response(self, message: str) -> Response:
        """
        Unauthorized response oluştur
        
        Args:
            message: Hata mesajı
            
        Returns:
            Unauthorized response
        """
        return web.json_response(
            data={
                "error": {
                    "code": 401,
                    "message": message
                }
            },
            status=401,
            headers={
                'WWW-Authenticate': 'Bearer'
            }
        )
    
    async def validate_api_key(self, api_key: str) -> Optional[User]:
        """
        API key'i doğrula
        
        Args:
            api_key: API key
            
        Returns:
            User objesi veya None
        """
        try:
            # API key'i hashle
            import hashlib
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # API key'i veritabanından al
            api_key_obj = ApiKey.get_or_none(
                ApiKey.key_hash == key_hash,
                ApiKey.is_active == True
            )
            
            if not api_key_obj:
                return None
            
            # API key süresi kontrolü
            if api_key_obj.is_expired():
                # API key'i deaktif et
                api_key_obj.is_active = False
                api_key_obj.save()
                return None
            
            # Son kullanım zamanını güncelle
            api_key_obj.update_last_used()
            
            # User'ı döndür
            return api_key_obj.user
            
        except Exception as e:
            self.logger.error(f"API key doğrulama hatası: {e}")
            return None
    
    def create_token(self, user: User, expires_in_minutes: int = None) -> str:
        """
        JWT token oluştur
        
        Args:
            user: User objesi
            expires_in_minutes: Token süresi (dakika)
            
        Returns:
            JWT token
        """
        if expires_in_minutes is None:
            expires_in_minutes = settings.security.jwt_access_token_expire_minutes
        
        import time
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': int(time.time()) + (expires_in_minutes * 60),
            'iat': int(time.time())
        }
        
        return jwt.encode(
            payload,
            self.jwt_secret,
            algorithm=self.jwt_algorithm
        )
    
    def create_refresh_token(self, user: User) -> str:
        """
        Refresh token oluştur
        
        Args:
            user: User objesi
            
        Returns:
            Refresh token
        """
        expires_in_days = settings.security.jwt_refresh_token_expire_days
        
        import time
        payload = {
            'user_id': user.id,
            'type': 'refresh',
            'exp': int(time.time()) + (expires_in_days * 24 * 60 * 60),
            'iat': int(time.time())
        }
        
        return jwt.encode(
            payload,
            self.jwt_secret,
            algorithm=self.jwt_algorithm
        )
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Token'ı decode et
        
        Args:
            token: JWT token
            
        Returns:
            Token payload veya None
        """
        try:
            return jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None


# Global auth middleware instance
auth_handler = AuthMiddleware()

# Export the middleware function
auth_middleware = auth_handler.middleware
