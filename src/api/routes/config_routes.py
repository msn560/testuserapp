"""
Config Routes module - Configuration endpoint'leri

Bu modül konfigürasyon yönetimi ile ilgili API endpoint'lerini içerir.
"""

import json
from typing import Dict, Any, Optional
from aiohttp import web
from aiohttp.web import Request, Response

from .base_routes import BaseRoutes
from ...core.constants import API_PREFIX, SUCCESS_MESSAGES, ERROR_MESSAGES
from ...core.settings import settings
from ...utils.logger import Logger


class ConfigRoutes(BaseRoutes):
    """Config routes sınıfı"""
    
    def __init__(self):
        """ConfigRoutes'ı başlat"""
        super().__init__()
        self.logger = Logger(__name__)
    
    def get_routes(self) -> list[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.get(f"{API_PREFIX}/config", self.get_config),
            web.put(f"{API_PREFIX}/config", self.update_config),
            web.get(f"{API_PREFIX}/config/{{category}}", self.get_config_category),
            web.put(f"{API_PREFIX}/config/{{category}}", self.update_config_category),
            web.get(f"{API_PREFIX}/config/{{category}}/{{key}}", self.get_config_key),
            web.put(f"{API_PREFIX}/config/{{category}}/{{key}}", self.update_config_key),
            web.get(f"{API_PREFIX}/config/server", self.get_server_config),
            web.put(f"{API_PREFIX}/config/server", self.update_server_config),
            web.get(f"{API_PREFIX}/config/database", self.get_database_config),
            web.put(f"{API_PREFIX}/config/database", self.update_database_config),
        ]
    
    async def get_config(self, request: Request) -> Response:
        """Tüm konfigürasyonu al"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Konfigürasyonu al
            config_data = {
                "server": {
                    "host": getattr(settings.server, 'host', '127.0.0.1'),
                    "port": getattr(settings.server, 'port', 8080),
                    "debug": getattr(settings.server, 'debug', False),
                    "workers": getattr(settings.server, 'workers', 1)
                },
                "database": {
                    "host": getattr(settings.database, 'host', 'localhost'),
                    "port": getattr(settings.database, 'port', 5432),
                    "name": getattr(settings.database, 'name', 'raspos_db'),
                    "user": getattr(settings.database, 'user', 'postgres'),
                    "pool_size": getattr(settings.database, 'pool_size', 10),
                    "max_overflow": getattr(settings.database, 'max_overflow', 20)
                },
                "security": {
                    "jwt_secret_key": "***HIDDEN***",
                    "jwt_access_token_expire_minutes": getattr(settings.security, 'jwt_access_token_expire_minutes', 30),
                    "jwt_refresh_token_expire_days": getattr(settings.security, 'jwt_refresh_token_expire_days', 7),
                    "bcrypt_rounds": getattr(settings.security, 'bcrypt_rounds', 12)
                },
                "rate_limiting": {
                    "enabled": getattr(settings.rate_limiting, 'enabled', True),
                    "requests_per_minute": getattr(settings.rate_limiting, 'requests_per_minute', 60),
                    "burst_size": getattr(settings.rate_limiting, 'burst_size', 100)
                },
                "logging": {
                    "level": getattr(settings.logging, 'level', 'INFO'),
                    "format": getattr(settings.logging, 'format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                    "file_enabled": getattr(settings.logging, 'file_enabled', True),
                    "console_enabled": getattr(settings.logging, 'console_enabled', True)
                }
            }
            
            return self.create_success_response(
                message="Konfigürasyon alındı",
                data=config_data
            )
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon alınamadı: {e}")
            return self.create_error_response(
                message="Konfigürasyon alınamadı",
                status_code=500
            )
    
    async def update_config(self, request: Request) -> Response:
        """Konfigürasyonu güncelle"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Request body'yi al
            data = await request.json()
            
            # Güvenlik kontrolü - hassas ayarları koru
            protected_keys = ['jwt_secret_key', 'database_password']
            for key in protected_keys:
                if key in data:
                    return self.create_error_response(
                        message=f"{key} güvenlik nedeniyle değiştirilemez",
                        status_code=403
                    )
            
            # Konfigürasyonu güncelle (gerçek uygulamada dosyaya yazılır)
            updated_config = {
                "message": "Konfigürasyon güncellendi",
                "updated_fields": list(data.keys()),
                "timestamp": self._get_current_time().isoformat()
            }
            
            # Log yaz
            self.logger.log_user_action(
                "config_update",
                user_id,
                f"Konfigürasyon güncellendi: {list(data.keys())}",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message="Konfigürasyon başarıyla güncellendi",
                data=updated_config
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Konfigürasyon güncellenemedi: {e}")
            return self.create_error_response(
                message="Konfigürasyon güncellenemedi",
                status_code=500
            )
    
    async def get_config_category(self, request: Request) -> Response:
        """Kategori konfigürasyonunu al"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            category = request.match_info['category']
            
            # Kategori konfigürasyonunu al
            category_config = self._get_category_config(category)
            
            if category_config is None:
                return self.create_error_response(
                    message=f"Geçersiz kategori: {category}",
                    status_code=404
                )
            
            return self.create_success_response(
                message=f"{category} konfigürasyonu alındı",
                data=category_config
            )
            
        except Exception as e:
            self.logger.error(f"Kategori konfigürasyonu alınamadı: {e}")
            return self.create_error_response(
                message="Kategori konfigürasyonu alınamadı",
                status_code=500
            )
    
    async def update_config_category(self, request: Request) -> Response:
        """Kategori konfigürasyonunu güncelle"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            category = request.match_info['category']
            data = await request.json()
            
            # Kategori konfigürasyonunu güncelle
            updated_config = {
                "category": category,
                "updated_fields": list(data.keys()),
                "timestamp": self._get_current_time().isoformat()
            }
            
            # Log yaz
            self.logger.log_user_action(
                "config_category_update",
                user_id,
                f"{category} kategorisi güncellendi: {list(data.keys())}",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message=f"{category} kategorisi güncellendi",
                data=updated_config
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Kategori konfigürasyonu güncellenemedi: {e}")
            return self.create_error_response(
                message="Kategori konfigürasyonu güncellenemedi",
                status_code=500
            )
    
    async def get_config_key(self, request: Request) -> Response:
        """Spesifik konfigürasyon anahtarını al"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            category = request.match_info['category']
            key = request.match_info['key']
            
            # Anahtar değerini al
            key_value = self._get_config_key_value(category, key)
            
            if key_value is None:
                return self.create_error_response(
                    message=f"Geçersiz anahtar: {category}.{key}",
                    status_code=404
                )
            
            return self.create_success_response(
                message=f"{category}.{key} değeri alındı",
                data={key: key_value}
            )
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon anahtarı alınamadı: {e}")
            return self.create_error_response(
                message="Konfigürasyon anahtarı alınamadı",
                status_code=500
            )
    
    async def update_config_key(self, request: Request) -> Response:
        """Spesifik konfigürasyon anahtarını güncelle"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            category = request.match_info['category']
            key = request.match_info['key']
            data = await request.json()
            
            # Güvenlik kontrolü
            if key in ['jwt_secret_key', 'database_password']:
                return self.create_error_response(
                    message=f"{key} güvenlik nedeniyle değiştirilemez",
                    status_code=403
                )
            
            # Anahtar değerini güncelle
            updated_config = {
                "category": category,
                "key": key,
                "old_value": self._get_config_key_value(category, key),
                "new_value": data.get('value'),
                "timestamp": self._get_current_time().isoformat()
            }
            
            # Log yaz
            self.logger.log_user_action(
                "config_key_update",
                user_id,
                f"{category}.{key} güncellendi",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message=f"{category}.{key} güncellendi",
                data=updated_config
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Konfigürasyon anahtarı güncellenemedi: {e}")
            return self.create_error_response(
                message="Konfigürasyon anahtarı güncellenemedi",
                status_code=500
            )
    
    def _get_category_config(self, category: str) -> Optional[Dict[str, Any]]:
        """Kategori konfigürasyonunu al"""
        config_map = {
            "server": {
                "host": getattr(settings.server, 'host', '127.0.0.1'),
                "port": getattr(settings.server, 'port', 8080),
                "debug": getattr(settings.server, 'debug', False),
                "workers": getattr(settings.server, 'workers', 1)
            },
            "database": {
                "host": getattr(settings.database, 'host', 'localhost'),
                "port": getattr(settings.database, 'port', 5432),
                "name": getattr(settings.database, 'name', 'raspos_db'),
                "user": getattr(settings.database, 'user', 'postgres'),
                "pool_size": getattr(settings.database, 'pool_size', 10),
                "max_overflow": getattr(settings.database, 'max_overflow', 20)
            },
            "security": {
                "jwt_secret_key": "***HIDDEN***",
                "jwt_access_token_expire_minutes": getattr(settings.security, 'jwt_access_token_expire_minutes', 30),
                "jwt_refresh_token_expire_days": getattr(settings.security, 'jwt_refresh_token_expire_days', 7),
                "bcrypt_rounds": getattr(settings.security, 'bcrypt_rounds', 12)
            },
            "rate_limiting": {
                "enabled": getattr(settings.rate_limiting, 'enabled', True),
                "requests_per_minute": getattr(settings.rate_limiting, 'requests_per_minute', 60),
                "burst_size": getattr(settings.rate_limiting, 'burst_size', 100)
            },
            "logging": {
                "level": getattr(settings.logging, 'level', 'INFO'),
                "format": getattr(settings.logging, 'format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                "file_enabled": getattr(settings.logging, 'file_enabled', True),
                "console_enabled": getattr(settings.logging, 'console_enabled', True)
            }
        }
        
        return config_map.get(category)
    
    def _get_config_key_value(self, category: str, key: str) -> Optional[Any]:
        """Konfigürasyon anahtar değerini al"""
        category_config = self._get_category_config(category)
        if category_config:
            return category_config.get(key)
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Client IP adresini al"""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote
    
    def _get_current_time(self):
        """Mevcut zamanı al"""
        from datetime import datetime
        return datetime.now()
    
    async def get_server_config(self, request: Request) -> Response:
        """Server konfigürasyonu al"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Server konfigürasyonunu al
            server_config = {
                "host": getattr(settings.server, 'host', '127.0.0.1'),
                "port": getattr(settings.server, 'port', 8080),
                "ssl_enabled": getattr(settings.server, 'ssl', False),
                "ssl_cert_path": getattr(settings.server, 'ssl_cert_path', ''),
                "ssl_key_path": getattr(settings.server, 'ssl_key_path', ''),
                "cors_origins": getattr(settings.server, 'cors_origins', ['*']),
                "cors_methods": getattr(settings.server, 'cors_methods', ['GET', 'POST', 'PUT', 'DELETE']),
                "cors_headers": getattr(settings.server, 'cors_headers', ['Content-Type', 'Authorization']),
                "auto_start": getattr(settings.server, 'auto_start', False)
            }
            
            return self.create_success_response(
                message="Server konfigürasyonu alındı",
                data=server_config
            )
            
        except Exception as e:
            self.logger.error(f"Server konfigürasyonu alınamadı: {e}")
            return self.create_error_response(
                message="Server konfigürasyonu alınamadı",
                status_code=500
            )
    
    async def update_server_config(self, request: Request) -> Response:
        """Server konfigürasyonu güncelle"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Request body'yi al
            data = await request.json()
            
            # Güvenlik kontrolü
            protected_keys = ['ssl_cert_path', 'ssl_key_path']
            for key in protected_keys:
                if key in data:
                    return self.create_error_response(
                        message=f"{key} güvenlik nedeniyle değiştirilemez",
                        status_code=403
                    )
            
            # Konfigürasyonu güncelle (gerçek uygulamada dosyaya yazılır)
            updated_config = {
                "message": "Server konfigürasyonu güncellendi",
                "updated_fields": list(data.keys()),
                "timestamp": self._get_current_time().isoformat()
            }
            
            # Log yaz
            self.logger.log_user_action(
                "server_config_update",
                user_id,
                f"Server konfigürasyonu güncellendi: {list(data.keys())}",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message="Server konfigürasyonu başarıyla güncellendi",
                data=updated_config
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Server konfigürasyonu güncellenemedi: {e}")
            return self.create_error_response(
                message="Server konfigürasyonu güncellenemedi",
                status_code=500
            )
    
    async def get_database_config(self, request: Request) -> Response:
        """Database konfigürasyonu al"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Database konfigürasyonunu al
            database_config = {
                "url": getattr(settings.database, 'url', 'sqlite:///data/app.db'),
                "echo": getattr(settings.database, 'echo', False),
                "pool_size": getattr(settings.database, 'pool_size', 10),
                "max_overflow": getattr(settings.database, 'max_overflow', 20),
                "pool_timeout": getattr(settings.database, 'pool_timeout', 30),
                "pool_recycle": getattr(settings.database, 'pool_recycle', 3600)
            }
            
            return self.create_success_response(
                message="Database konfigürasyonu alındı",
                data=database_config
            )
            
        except Exception as e:
            self.logger.error(f"Database konfigürasyonu alınamadı: {e}")
            return self.create_error_response(
                message="Database konfigürasyonu alınamadı",
                status_code=500
            )
    
    async def update_database_config(self, request: Request) -> Response:
        """Database konfigürasyonu güncelle"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Request body'yi al
            data = await request.json()
            
            # Güvenlik kontrolü
            protected_keys = ['url', 'password']
            for key in protected_keys:
                if key in data:
                    return self.create_error_response(
                        message=f"{key} güvenlik nedeniyle değiştirilemez",
                        status_code=403
                    )
            
            # Konfigürasyonu güncelle (gerçek uygulamada dosyaya yazılır)
            updated_config = {
                "message": "Database konfigürasyonu güncellendi",
                "updated_fields": list(data.keys()),
                "timestamp": self._get_current_time().isoformat()
            }
            
            # Log yaz
            self.logger.log_user_action(
                "database_config_update",
                user_id,
                f"Database konfigürasyonu güncellendi: {list(data.keys())}",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message="Database konfigürasyonu başarıyla güncellendi",
                data=updated_config
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Database konfigürasyonu güncellenemedi: {e}")
            return self.create_error_response(
                message="Database konfigürasyonu güncellenemedi",
                status_code=500
            )
