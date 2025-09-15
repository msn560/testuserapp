"""
Auth Routes module - Authentication endpoint'leri

Bu modül authentication ile ilgili API endpoint'lerini içerir.
"""

import bcrypt
import json
from typing import Dict, Any, Optional
from aiohttp import web
from aiohttp.web import Request, Response

from .base_routes import BaseRoutes
from ...core.constants import API_PREFIX, SUCCESS_MESSAGES, ERROR_MESSAGES
from ...core.settings import settings
from ...db.models import User, Session, UserRole, Role
from ...utils.logger import Logger


class AuthRoutes(BaseRoutes):
    """Auth routes sınıfı"""
    
    def __init__(self):
        """AuthRoutes'ı başlat"""
        super().__init__()
        self.logger = Logger(__name__)
    
    def get_routes(self) -> list[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.post(f"{API_PREFIX}/auth/login", self.login),
            web.post(f"{API_PREFIX}/auth/logout", self.logout),
            web.post(f"{API_PREFIX}/auth/refresh", self.refresh_token),
            web.get(f"{API_PREFIX}/auth/verify", self.verify_token),
            web.post(f"{API_PREFIX}/auth/forgot-password", self.forgot_password),
            web.post(f"{API_PREFIX}/auth/reset-password", self.reset_password),
            web.post(f"{API_PREFIX}/auth/change-password", self.change_password),
            web.get(f"{API_PREFIX}/auth/me", self.get_current_user),
        ]
    
    async def login(self, request: Request) -> Response:
        """
        Kullanıcı girişi
        
        Args:
            request: Request objesi
            
        Returns:
            Login response
        """
        try:
            # Request verisini al
            data = await request.json()
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return self.create_error_response(
                    "Kullanıcı adı ve parola gerekli",
                    status_code=400
                )
            
            # Kullanıcıyı bul
            user = User.get_or_none(
                (User.username == username) | (User.email == username),
                User.is_active == True
            )
            
            if not user:
                self.logger.log_security_event(
                    "login_failed",
                    f"Kullanıcı bulunamadı: {username}",
                    ip_address=self._get_client_ip(request)
                )
                return self.create_error_response(
                    ERROR_MESSAGES["INVALID_CREDENTIALS"],
                    status_code=401
                )
            
            # Parolayı kontrol et
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                self.logger.log_security_event(
                    "login_failed",
                    f"Yanlış parola: {username}",
                    user_id=user.id,
                    ip_address=self._get_client_ip(request)
                )
                return self.create_error_response(
                    ERROR_MESSAGES["INVALID_CREDENTIALS"],
                    status_code=401
                )
            
            # Token oluştur
            from ...api.middlewares.auth_middleware import AuthMiddleware
            auth_middleware = AuthMiddleware()
            
            access_token = auth_middleware.create_token(user)
            refresh_token = auth_middleware.create_refresh_token(user)
            
            # Session oluştur
            session = Session.create(
                user=user,
                token=access_token,
                refresh_token=refresh_token,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get('User-Agent', ''),
                expires_at=self._get_token_expiry()
            )
            
            # Son giriş zamanını güncelle
            user.last_login = self._get_current_time()
            user.save()
            
            # Kullanıcı rollerini al
            user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
            
            # Başarılı giriş log'u
            self.logger.log_user_action(
                "login",
                user.id,
                f"Başarılı giriş: {username}",
                ip_address=self._get_client_ip(request)
            )
            
            # Response oluştur
            response_data = {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "roles": user_roles,
                    "is_superuser": user.is_superuser
                },
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": settings.security.jwt_access_token_expire_minutes * 60
                }
            }
            
            return self.create_success_response(
                data=response_data,
                message=SUCCESS_MESSAGES["LOGIN_SUCCESS"]
            )
            
        except Exception as e:
            self.logger.error(f"Login hatası: {e}")
            return self.create_error_response(
                ERROR_MESSAGES["SERVER_ERROR"],
                status_code=500
            )
    
    async def logout(self, request: Request) -> Response:
        """
        Kullanıcı çıkışı
        
        Args:
            request: Request objesi
            
        Returns:
            Logout response
        """
        try:
            # Token'ı al
            token = self._get_auth_token(request)
            if not token:
                return self.create_error_response(
                    "Token bulunamadı",
                    status_code=401
                )
            
            # Session'ı bul ve deaktif et
            session = Session.get_or_none(
                Session.token == token,
                Session.is_active == True
            )
            
            if session:
                session.is_active = False
                session.save()
                
                # Çıkış log'u
                self.logger.log_user_action(
                    "logout",
                    session.user.id,
                    f"Kullanıcı çıkışı: {session.user.username}",
                    ip_address=self._get_client_ip(request)
                )
            
            return self.create_success_response(
                message=SUCCESS_MESSAGES["LOGOUT_SUCCESS"]
            )
            
        except Exception as e:
            self.logger.error(f"Logout hatası: {e}")
            return self.create_error_response(
                ERROR_MESSAGES["SERVER_ERROR"],
                status_code=500
            )
    
    async def refresh_token(self, request: Request) -> Response:
        """
        Token yenileme
        
        Args:
            request: Request objesi
            
        Returns:
            Refresh token response
        """
        try:
            # Request verisini al
            try:
                data = await request.json()
            except Exception as json_error:
                self.logger.error(f"JSON parse hatası: {json_error}")
                return self.create_error_response(
                    "Geçersiz JSON formatı",
                    status_code=400
                )
            
            if not data:
                return self.create_error_response(
                    "Request body boş olamaz",
                    status_code=400
                )
            
            refresh_token = data.get('refresh_token')
            
            if not refresh_token:
                return self.create_error_response(
                    "Refresh token gerekli",
                    status_code=400
                )
            
            # Refresh token'ı doğrula
            from ...api.middlewares.auth_middleware import AuthMiddleware
            auth_middleware = AuthMiddleware()
            
            payload = auth_middleware.decode_token(refresh_token)
            if not payload or payload.get('type') != 'refresh':
                return self.create_error_response(
                    ERROR_MESSAGES["INVALID_TOKEN"],
                    status_code=401
                )
            
            # Kullanıcıyı bul
            user_id = payload.get('user_id')
            user = User.get_or_none(User.id == user_id, User.is_active == True)
            
            if not user:
                return self.create_error_response(
                    ERROR_MESSAGES["USER_NOT_FOUND"],
                    status_code=401
                )
            
            # Yeni token'lar oluştur
            new_access_token = auth_middleware.create_token(user)
            new_refresh_token = auth_middleware.create_refresh_token(user)
            
            # Eski session'ı deaktif et
            old_session = Session.get_or_none(
                Session.refresh_token == refresh_token,
                Session.is_active == True
            )
            
            if old_session:
                old_session.is_active = False
                old_session.save()
            
            # Yeni session oluştur
            new_session = Session.create(
                user=user,
                token=new_access_token,
                refresh_token=new_refresh_token,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get('User-Agent', ''),
                expires_at=self._get_token_expiry()
            )
            
            # Response oluştur
            response_data = {
                "tokens": {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                    "expires_in": settings.security.jwt_access_token_expire_minutes * 60
                }
            }
            
            return self.create_success_response(data=response_data)
            
        except Exception as e:
            self.logger.error(f"Token yenileme hatası: {e}")
            return self.create_error_response(
                ERROR_MESSAGES["SERVER_ERROR"],
                status_code=500
            )
    
    async def verify_token(self, request: Request) -> Response:
        """
        Token doğrulama
        
        Args:
            request: Request objesi
            
        Returns:
            Token verification response
        """
        try:
            # Token'ı al
            token = self._get_auth_token(request)
            if not token:
                return self.create_error_response(
                    "Token bulunamadı",
                    status_code=401
                )
            
            # Token'ı doğrula
            from ...api.middlewares.auth_middleware import AuthMiddleware
            auth_middleware = AuthMiddleware()
            
            payload = auth_middleware.decode_token(token)
            if not payload:
                return self.create_error_response(
                    ERROR_MESSAGES["INVALID_TOKEN"],
                    status_code=401
                )
            
            # Kullanıcıyı bul
            user_id = payload.get('user_id')
            user = User.get_or_none(User.id == user_id, User.is_active == True)
            
            if not user:
                return self.create_error_response(
                    ERROR_MESSAGES["USER_NOT_FOUND"],
                    status_code=401
                )
            
            # Kullanıcı rollerini al
            user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
            
            # Response oluştur
            response_data = {
                "valid": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "roles": user_roles,
                    "is_superuser": user.is_superuser
                },
                "expires_at": payload.get('exp')
            }
            
            return self.create_success_response(data=response_data)
            
        except Exception as e:
            self.logger.error(f"Token doğrulama hatası: {e}")
            return self.create_error_response(
                ERROR_MESSAGES["SERVER_ERROR"],
                status_code=500
            )
    
    async def forgot_password(self, request: Request) -> Response:
        """
        Parola sıfırlama isteği
        
        Args:
            request: Request objesi
            
        Returns:
            Forgot password response
        """
        try:
            # Request verisini al
            data = await request.json()
            email = data.get('email')
            
            if not email:
                return self.create_error_response(
                    "Email adresi gerekli",
                    status_code=400
                )
            
            # Kullanıcıyı bul
            user = User.get_or_none(User.email == email, User.is_active == True)
            
            if not user:
                # Güvenlik için aynı response döndür
                return self.create_success_response(
                    message="Eğer email adresiniz sistemde kayıtlıysa, parola sıfırlama linki gönderilecektir."
                )
            
            # TODO: Email gönderme işlemi implement edilecek
            # Şimdilik sadece log yazıyoruz
            
            self.logger.log_user_action(
                "forgot_password_request",
                user.id,
                f"Parola sıfırlama isteği: {email}",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message="Eğer email adresiniz sistemde kayıtlıysa, parola sıfırlama linki gönderilecektir."
            )
            
        except Exception as e:
            self.logger.error(f"Parola sıfırlama isteği hatası: {e}")
            return self.create_error_response(
                ERROR_MESSAGES["SERVER_ERROR"],
                status_code=500
            )
    
    async def reset_password(self, request: Request) -> Response:
        """
        Parola sıfırlama
        
        Args:
            request: Request objesi
            
        Returns:
            Reset password response
        """
        try:
            # Request verisini al
            data = await request.json()
            token = data.get('token')
            new_password = data.get('new_password')
            
            if not token or not new_password:
                return self.create_error_response(
                    "Token ve yeni parola gerekli",
                    status_code=400
                )
            
            # TODO: Token doğrulama ve parola sıfırlama implement edilecek
            # Şimdilik sadece log yazıyoruz
            
            self.logger.log_user_action(
                "password_reset",
                None,
                f"Parola sıfırlama işlemi: {token[:10]}...",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message="Parola başarıyla sıfırlandı"
            )
            
        except Exception as e:
            self.logger.error(f"Parola sıfırlama hatası: {e}")
            return self.create_error_response(
                ERROR_MESSAGES["SERVER_ERROR"],
                status_code=500
            )
    
    async def change_password(self, request: Request) -> Response:
        """
        Parola değiştirme
        
        Args:
            request: Request objesi
            
        Returns:
            Change password response
        """
        try:
            # Token'ı al
            token = self._get_auth_token(request)
            if not token:
                return self.create_error_response(
                    "Token bulunamadı",
                    status_code=401
                )
            
            # Token'ı doğrula
            from ...api.middlewares.auth_middleware import AuthMiddleware
            auth_middleware = AuthMiddleware()
            
            payload = auth_middleware.decode_token(token)
            if not payload:
                return self.create_error_response(
                    ERROR_MESSAGES["INVALID_TOKEN"],
                    status_code=401
                )
            
            # Kullanıcıyı bul
            user_id = payload.get('user_id')
            user = User.get_or_none(User.id == user_id, User.is_active == True)
            
            if not user:
                return self.create_error_response(
                    ERROR_MESSAGES["USER_NOT_FOUND"],
                    status_code=401
                )
            
            # Request verisini al
            data = await request.json()
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            
            if not current_password or not new_password:
                return self.create_error_response(
                    "Mevcut parola ve yeni parola gerekli",
                    status_code=400
                )
            
            # Mevcut parolayı kontrol et
            if not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
                return self.create_error_response(
                    "Mevcut parola yanlış",
                    status_code=400
                )
            
            # Yeni parolayı hash'le ve kaydet
            new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            user.password_hash = new_hashed_password.decode('utf-8')
            user.save()
            
            # Parola değişikliği log'u
            self.logger.log_user_action(
                "password_change",
                user.id,
                f"Parola değiştirildi: {user.username}",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message="Parola başarıyla değiştirildi"
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                "Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Parola değiştirme hatası: {e}")
            return self.create_error_response(
                ERROR_MESSAGES["SERVER_ERROR"],
                status_code=500
            )
    
    async def get_current_user(self, request: Request) -> Response:
        """
        Mevcut kullanıcı bilgilerini al
        
        Args:
            request: Request objesi
            
        Returns:
            Current user response
        """
        try:
            # Token'ı al
            token = self._get_auth_token(request)
            if not token:
                return self.create_error_response(
                    "Token bulunamadı",
                    status_code=401
                )
            
            # Token'ı doğrula
            from ...api.middlewares.auth_middleware import AuthMiddleware
            auth_middleware = AuthMiddleware()
            
            payload = auth_middleware.decode_token(token)
            if not payload:
                return self.create_error_response(
                    ERROR_MESSAGES["INVALID_TOKEN"],
                    status_code=401
                )
            
            # Kullanıcıyı bul
            user_id = payload.get('user_id')
            user = User.get_or_none(User.id == user_id, User.is_active == True)
            
            if not user:
                return self.create_error_response(
                    ERROR_MESSAGES["USER_NOT_FOUND"],
                    status_code=401
                )
            
            # Kullanıcı rollerini al
            user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
            
            # Response oluştur
            response_data = {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "roles": user_roles,
                    "is_superuser": user.is_superuser,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                },
                "token_info": {
                    "expires_at": payload.get('exp'),
                    "issued_at": payload.get('iat')
                }
            }
            
            return self.create_success_response(
                data=response_data,
                message="Kullanıcı bilgileri alındı"
            )
            
        except Exception as e:
            self.logger.error(f"Mevcut kullanıcı bilgileri alınamadı: {e}")
            return self.create_error_response(
                ERROR_MESSAGES["SERVER_ERROR"],
                status_code=500
            )
    
    def _get_auth_token(self, request: Request) -> Optional[str]:
        """Request'ten auth token'ını al"""
        # Authorization header'ından al
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]
        
        # Query parameter'ından al
        return request.query.get('token')
    
    def _get_client_ip(self, request: Request) -> str:
        """Client IP adresini al"""
        # X-Forwarded-For header'ını kontrol et
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        # X-Real-IP header'ını kontrol et
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Remote IP'yi al
        return request.remote
    
    def _get_current_time(self):
        """Mevcut zamanı al"""
        from datetime import datetime
        return datetime.now()
    
    def _get_token_expiry(self):
        """Token süresini al"""
        from datetime import datetime, timedelta
        return datetime.now() + timedelta(minutes=settings.security.jwt_access_token_expire_minutes)
