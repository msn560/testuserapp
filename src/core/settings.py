"""
Settings module - Varsayılan ayarlar

Bu modül uygulamanın varsayılan ayarlarını içerir ve
konfigürasyon yönetimini sağlar.
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

from .constants import *


@dataclass
class DatabaseSettings:
    """Veritabanı ayarları"""
    url: str = "sqlite:///data/app.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class ServerSettings:
    """Server ayarları"""
    host: str = "localhost"
    port: int = 8080
    ssl: bool = False
    ssl_cert_path: str = "data/certificates/server.crt"
    ssl_key_path: str = "data/certificates/server.key"
    auto_start: bool = False
    max_connections: int = 1000
    timeout: int = 30
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_headers: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization"])


@dataclass
class SecuritySettings:
    """Güvenlik ayarları"""
    jwt_secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = DEFAULT_JWT_ALGORITHM
    jwt_access_token_expire_minutes: int = DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    jwt_refresh_token_expire_days: int = DEFAULT_JWT_REFRESH_TOKEN_EXPIRE_DAYS
    bcrypt_rounds: int = DEFAULT_BCRYPT_ROUNDS
    password_min_length: int = DEFAULT_PASSWORD_MIN_LENGTH
    password_require_uppercase: bool = DEFAULT_PASSWORD_REQUIRE_UPPERCASE
    password_require_lowercase: bool = DEFAULT_PASSWORD_REQUIRE_LOWERCASE
    password_require_numbers: bool = DEFAULT_PASSWORD_REQUIRE_NUMBERS
    password_require_special_chars: bool = DEFAULT_PASSWORD_REQUIRE_SPECIAL_CHARS
    session_timeout_minutes: int = DEFAULT_SESSION_TIMEOUT_MINUTES
    max_login_attempts: int = DEFAULT_MAX_LOGIN_ATTEMPTS
    lockout_duration_minutes: int = DEFAULT_LOCKOUT_DURATION_MINUTES


@dataclass
class RateLimitSettings:
    """Rate limiting ayarları"""
    enabled: bool = True
    requests_per_minute: int = DEFAULT_RATE_LIMIT_REQUESTS_PER_MINUTE
    burst_size: int = DEFAULT_RATE_LIMIT_BURST_SIZE
    per_ip_limit: bool = True
    per_user_limit: bool = True


@dataclass
class LoggingSettings:
    """Logging ayarları"""
    level: LogLevel = DEFAULT_LOG_LEVEL
    format: str = DEFAULT_LOG_FORMAT
    file_max_size: int = DEFAULT_LOG_FILE_MAX_SIZE
    file_backup_count: int = DEFAULT_LOG_FILE_BACKUP_COUNT
    console_output: bool = True
    file_output: bool = True
    log_file_path: str = "data/logs/app_{date}.log"
    error_file_path: str = "data/logs/error_{date}.log"
    security_file_path: str = "data/logs/security_{date}.log"
    api_file_path: str = "data/logs/api_{date}.log"


@dataclass
class UISettings:
    """UI ayarları"""
    theme: ThemeType = DEFAULT_UI_THEME
    language: LanguageCode = DEFAULT_UI_LANGUAGE
    auto_refresh_interval: int = DEFAULT_UI_AUTO_REFRESH_INTERVAL
    window_width: int = DEFAULT_WINDOW_WIDTH
    window_height: int = DEFAULT_WINDOW_HEIGHT
    window_min_width: int = DEFAULT_WINDOW_MIN_WIDTH
    window_min_height: int = DEFAULT_WINDOW_MIN_HEIGHT
    remember_window_state: bool = True
    show_splash_screen: bool = True
    splash_screen_duration: int = DEFAULT_SPLASH_SCREEN_DURATION


@dataclass
class MonitoringSettings:
    """Monitoring ayarları"""
    enabled: bool = True
    interval: int = DEFAULT_MONITORING_INTERVAL
    metrics_retention_days: int = DEFAULT_METRICS_RETENTION_DAYS
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "cpu_usage_percent": DEFAULT_CPU_USAGE_THRESHOLD,
        "memory_usage_percent": DEFAULT_MEMORY_USAGE_THRESHOLD,
        "disk_usage_percent": DEFAULT_DISK_USAGE_THRESHOLD,
        "response_time_ms": DEFAULT_RESPONSE_TIME_THRESHOLD,
        "error_rate_percent": DEFAULT_ERROR_RATE_THRESHOLD
    })
    email_alerts: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_username": "",
        "smtp_password": "",
        "from_email": "",
        "to_emails": []
    })


@dataclass
class BackupSettings:
    """Backup ayarları"""
    enabled: bool = True
    interval_hours: int = DEFAULT_BACKUP_INTERVAL_HOURS
    retention_days: int = DEFAULT_BACKUP_RETENTION_DAYS
    backup_path: str = DEFAULT_BACKUP_DIR
    compress: bool = DEFAULT_BACKUP_COMPRESS
    include_logs: bool = True
    include_config: bool = True
    auto_cleanup: bool = True


@dataclass
class CacheSettings:
    """Cache ayarları"""
    enabled: bool = True
    default_ttl: int = DEFAULT_CACHE_TTL
    max_size: int = DEFAULT_CACHE_MAX_SIZE
    cleanup_interval: int = DEFAULT_CACHE_CLEANUP_INTERVAL


@dataclass
class FeatureSettings:
    """Özellik ayarları"""
    user_management: bool = True
    role_management: bool = True
    api_management: bool = True
    monitoring: bool = True
    logging: bool = True
    backup_restore: bool = True
    real_time_updates: bool = True
    websocket_support: bool = True
    file_upload: bool = True
    export_import: bool = True


@dataclass
class AppSettings:
    """Uygulama ayarları"""
    name: str = APP_NAME
    version: str = APP_VERSION
    description: str = APP_DESCRIPTION
    author: str = APP_AUTHOR
    debug: bool = False
    development_mode: bool = False


class Settings:
    """
    Ana ayarlar sınıfı
    
    Uygulamanın tüm ayarlarını yönetir ve varsayılan değerleri sağlar.
    """
    
    def __init__(self):
        """Ayarları başlat"""
        self.app = AppSettings()
        self.database = DatabaseSettings()
        self.server = ServerSettings()
        self.security = SecuritySettings()
        self.rate_limiting = RateLimitSettings()
        self.logging = LoggingSettings()
        self.ui = UISettings()
        self.monitoring = MonitoringSettings()
        self.backup = BackupSettings()
        self.cache = CacheSettings()
        self.features = FeatureSettings()
        
        # Sistem rolleri
        self.system_roles = SYSTEM_ROLES.copy()
        
        # API endpoint'leri
        self.api_endpoints = {
            "auth": {
                "login": "/api/v1/auth/login",
                "logout": "/api/v1/auth/logout",
                "refresh": "/api/v1/auth/refresh",
                "verify": "/api/v1/auth/verify"
            },
            "users": {
                "list": "/api/v1/users",
                "create": "/api/v1/users",
                "get": "/api/v1/users/{id}",
                "update": "/api/v1/users/{id}",
                "delete": "/api/v1/users/{id}"
            },
            "server": {
                "status": "/api/v1/server/status",
                "start": "/api/v1/server/start",
                "stop": "/api/v1/server/stop",
                "restart": "/api/v1/server/restart",
                "config": "/api/v1/server/config"
            },
            "monitor": {
                "system": "/api/v1/monitor/system",
                "database": "/api/v1/monitor/database",
                "api": "/api/v1/monitor/api",
                "logs": "/api/v1/monitor/logs"
            }
        }
    
    def get_database_url(self) -> str:
        """Veritabanı URL'ini döndür"""
        return self.database.url
    
    def get_server_config(self) -> Dict[str, Any]:
        """Server konfigürasyonunu döndür"""
        return {
            "host": self.server.host,
            "port": self.server.port,
            "ssl": self.server.ssl,
            "ssl_cert_path": self.server.ssl_cert_path,
            "ssl_key_path": self.server.ssl_key_path,
            "auto_start": self.server.auto_start,
            "cors_origins": self.server.cors_origins,
            "cors_methods": self.server.cors_methods,
            "cors_headers": self.server.cors_headers
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Güvenlik konfigürasyonunu döndür"""
        return {
            "jwt_secret_key": self.security.jwt_secret_key,
            "jwt_algorithm": self.security.jwt_algorithm,
            "jwt_access_token_expire_minutes": self.security.jwt_access_token_expire_minutes,
            "jwt_refresh_token_expire_days": self.security.jwt_refresh_token_expire_days,
            "bcrypt_rounds": self.security.bcrypt_rounds,
            "password_min_length": self.security.password_min_length,
            "password_require_uppercase": self.security.password_require_uppercase,
            "password_require_lowercase": self.security.password_require_lowercase,
            "password_require_numbers": self.security.password_require_numbers,
            "password_require_special_chars": self.security.password_require_special_chars,
            "session_timeout_minutes": self.security.session_timeout_minutes,
            "max_login_attempts": self.security.max_login_attempts,
            "lockout_duration_minutes": self.security.lockout_duration_minutes
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Logging konfigürasyonunu döndür"""
        return {
            "level": self.logging.level.value if hasattr(self.logging.level, 'value') else int(self.logging.level),
            "format": self.logging.format,
            "file_max_size": self.logging.file_max_size,
            "file_backup_count": self.logging.file_backup_count,
            "console_output": self.logging.console_output,
            "file_output": self.logging.file_output,
            "log_file_path": self.logging.log_file_path,
            "error_file_path": self.logging.error_file_path,
            "security_file_path": self.logging.security_file_path,
            "api_file_path": self.logging.api_file_path
        }
    
    def get_ui_config(self) -> Dict[str, Any]:
        """UI konfigürasyonunu döndür"""
        return {
            "theme": self.ui.theme.value if hasattr(self.ui.theme, 'value') else str(self.ui.theme),
            "language": self.ui.language.value if hasattr(self.ui.language, 'value') else str(self.ui.language),
            "auto_refresh_interval": self.ui.auto_refresh_interval,
            "window_width": self.ui.window_width,
            "window_height": self.ui.window_height,
            "window_min_width": self.ui.window_min_width,
            "window_min_height": self.ui.window_min_height,
            "window_x": getattr(self.ui, 'window_x', 100),
            "window_y": getattr(self.ui, 'window_y', 100),
            "remember_window_state": self.ui.remember_window_state,
            "always_on_top": getattr(self.ui, 'always_on_top', False),
            "show_splash_screen": self.ui.show_splash_screen,
            "splash_screen_duration": self.ui.splash_screen_duration
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Monitoring konfigürasyonunu döndür"""
        return {
            "enabled": self.monitoring.enabled,
            "interval": self.monitoring.interval,
            "metrics_retention_days": self.monitoring.metrics_retention_days,
            "alert_thresholds": self.monitoring.alert_thresholds,
            "email_alerts": self.monitoring.email_alerts
        }
    
    def get_backup_config(self) -> Dict[str, Any]:
        """Backup konfigürasyonunu döndür"""
        return {
            "enabled": self.backup.enabled,
            "interval_hours": self.backup.interval_hours,
            "retention_days": self.backup.retention_days,
            "backup_path": self.backup.backup_path,
            "compress": self.backup.compress,
            "include_logs": self.backup.include_logs,
            "include_config": self.backup.include_config,
            "auto_cleanup": self.backup.auto_cleanup
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Cache konfigürasyonunu döndür"""
        return {
            "enabled": self.cache.enabled,
            "default_ttl": self.cache.default_ttl,
            "max_size": self.cache.max_size,
            "cleanup_interval": self.cache.cleanup_interval
        }
    
    def get_feature_config(self) -> Dict[str, bool]:
        """Özellik konfigürasyonunu döndür"""
        return {
            "user_management": self.features.user_management,
            "role_management": self.features.role_management,
            "api_management": self.features.api_management,
            "monitoring": self.features.monitoring,
            "logging": self.features.logging,
            "backup_restore": self.features.backup_restore,
            "real_time_updates": self.features.real_time_updates,
            "websocket_support": self.features.websocket_support,
            "file_upload": self.features.file_upload,
            "export_import": self.features.export_import
        }
    
    def get_system_roles(self) -> Dict[str, Dict[str, Any]]:
        """Sistem rollerini döndür"""
        return self.system_roles.copy()
    
    def get_api_endpoints(self) -> Dict[str, Dict[str, str]]:
        """API endpoint'lerini döndür"""
        return self.api_endpoints.copy()
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Özelliğin etkin olup olmadığını kontrol et"""
        return getattr(self.features, feature_name, False)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Tüm ayarları döndür"""
        return {
            "app": {
                "name": self.app.name,
                "version": self.app.version,
                "description": self.app.description,
                "author": self.app.author,
                "debug": self.app.debug,
                "development_mode": self.app.development_mode
            },
            "database": self.get_database_url(),
            "server": self.get_server_config(),
            "security": self.get_security_config(),
            "rate_limiting": {
                "enabled": self.rate_limiting.enabled,
                "requests_per_minute": self.rate_limiting.requests_per_minute,
                "burst_size": self.rate_limiting.burst_size,
                "per_ip_limit": self.rate_limiting.per_ip_limit,
                "per_user_limit": self.rate_limiting.per_user_limit
            },
            "logging": self.get_logging_config(),
            "ui": self.get_ui_config(),
            "monitoring": self.get_monitoring_config(),
            "backup": self.get_backup_config(),
            "cache": self.get_cache_config(),
            "features": self.get_feature_config(),
            "system_roles": self.get_system_roles(),
            "api_endpoints": self.get_api_endpoints()
        }
    
    def update_from_dict(self, settings_dict: Dict[str, Any]) -> None:
        """Sözlükten ayarları güncelle"""
        for section, values in settings_dict.items():
            if hasattr(self, section) and isinstance(values, dict):
                section_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        # Tema ve dil enum'larını doğru işle
                        if key == 'theme' and isinstance(value, str):
                            try:
                                from .constants import ThemeType
                                setattr(section_obj, key, ThemeType(value))
                            except ValueError:
                                # Geçersiz tema değeri, varsayılanı kullan
                                setattr(section_obj, key, DEFAULT_UI_THEME)
                        elif key == 'language' and isinstance(value, str):
                            try:
                                from .constants import LanguageCode
                                setattr(section_obj, key, LanguageCode(value))
                            except ValueError:
                                # Geçersiz dil değeri, varsayılanı kullan
                                setattr(section_obj, key, DEFAULT_UI_LANGUAGE)
                        else:
                            setattr(section_obj, key, value)
    
    def validate_settings(self) -> List[str]:
        """Ayarları doğrula ve hataları döndür"""
        errors = []
        
        # Veritabanı URL kontrolü
        if not self.database.url:
            errors.append("Database URL boş olamaz")
        
        # Server port kontrolü
        if not (1 <= self.server.port <= 65535):
            errors.append("Server port 1-65535 arasında olmalıdır")
        
        # JWT secret key kontrolü
        if not self.security.jwt_secret_key or len(self.security.jwt_secret_key) < 32:
            errors.append("JWT secret key en az 32 karakter olmalıdır")
        
        # Parola uzunluk kontrolü
        if self.security.password_min_length < 6:
            errors.append("Parola minimum uzunluğu en az 6 olmalıdır")
        
        # Logging seviye kontrolü
        if not isinstance(self.logging.level, LogLevel):
            errors.append("Geçersiz log seviyesi")
        
        # UI boyut kontrolü
        if self.ui.window_width < self.ui.window_min_width:
            errors.append("Pencere genişliği minimum genişlikten küçük olamaz")
        
        if self.ui.window_height < self.ui.window_min_height:
            errors.append("Pencere yüksekliği minimum yükseklikten küçük olamaz")
        
        return errors


# Global settings instance
settings = Settings()
