"""
Constants module - Sabitler ve enum'lar

Bu modül uygulama genelinde kullanılan sabitleri ve enum'ları içerir.
"""

from enum import Enum, IntEnum
from typing import Dict, List, Any


class LogLevel(IntEnum):
    """Log seviyeleri"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class UserStatus(Enum):
    """Kullanıcı durumları"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class ServerStatus(Enum):
    """Server durumları"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert önem seviyeleri"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Alert türleri"""
    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR = "error"
    WARNING = "warning"


class BackupType(Enum):
    """Backup türleri"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    CONFIG = "config"
    DATABASE = "database"
    LOGS = "logs"


class TaskStatus(Enum):
    """Görev durumları"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HTTPMethod(Enum):
    """HTTP metodları"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class ThemeType(Enum):
    """Tema türleri"""
    DARK = "dark"
    LIGHT = "light"
    BLUE = "blue"
    CUSTOM = "custom"


class LanguageCode(Enum):
    """Dil kodları"""
    TR = "tr"
    EN = "en"
    DE = "de"
    FR = "fr"


# Uygulama sabitleri
APP_NAME = "API Server Management System"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Modern API Server Management System with GUI and REST API"
APP_AUTHOR = "API Server Manager Team"

# Dosya yolları
DATA_DIR = "data"
CONFIG_FILE = "data/config.json"
DATABASE_FILE = "data/app.db"
LOGS_DIR = "data/logs"
BACKUP_DIR = "data/backup"
CACHE_DIR = "data/cache"
CERTIFICATES_DIR = "data/certificates"
LOCALE_DIR = "data/locale"
RESOURCES_DIR = "data/resources"
DEFAULT_BACKUP_DIR = "data/backup"

# API sabitleri
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Güvenlik sabitleri
DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
DEFAULT_JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
DEFAULT_BCRYPT_ROUNDS = 12
DEFAULT_SESSION_TIMEOUT_MINUTES = 60
DEFAULT_MAX_LOGIN_ATTEMPTS = 5
DEFAULT_LOCKOUT_DURATION_MINUTES = 15

# Parola gereksinimleri
DEFAULT_PASSWORD_MIN_LENGTH = 8
DEFAULT_PASSWORD_REQUIRE_UPPERCASE = True
DEFAULT_PASSWORD_REQUIRE_LOWERCASE = True
DEFAULT_PASSWORD_REQUIRE_NUMBERS = True
DEFAULT_PASSWORD_REQUIRE_SPECIAL_CHARS = True

# Rate limiting sabitleri
DEFAULT_RATE_LIMIT_REQUESTS_PER_MINUTE = 100
DEFAULT_RATE_LIMIT_BURST_SIZE = 20

# Logging sabitleri
DEFAULT_LOG_LEVEL = LogLevel.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_LOG_FILE_BACKUP_COUNT = 5

# UI sabitleri
DEFAULT_UI_THEME = ThemeType.DARK
DEFAULT_UI_LANGUAGE = LanguageCode.TR
DEFAULT_UI_AUTO_REFRESH_INTERVAL = 5000  # milliseconds
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_WINDOW_MIN_WIDTH = 800
DEFAULT_WINDOW_MIN_HEIGHT = 600
DEFAULT_SPLASH_SCREEN_DURATION = 3000  # milliseconds

# Monitoring sabitleri
DEFAULT_MONITORING_INTERVAL = 30  # seconds
DEFAULT_METRICS_RETENTION_DAYS = 30
DEFAULT_CPU_USAGE_THRESHOLD = 80
DEFAULT_MEMORY_USAGE_THRESHOLD = 85
DEFAULT_DISK_USAGE_THRESHOLD = 90
DEFAULT_RESPONSE_TIME_THRESHOLD = 1000  # milliseconds
DEFAULT_ERROR_RATE_THRESHOLD = 5  # percent

# Backup sabitleri
DEFAULT_BACKUP_INTERVAL_HOURS = 24
DEFAULT_BACKUP_RETENTION_DAYS = 30
DEFAULT_BACKUP_COMPRESS = True

# Cache sabitleri
DEFAULT_CACHE_TTL = 300  # seconds
DEFAULT_CACHE_MAX_SIZE = 1000
DEFAULT_CACHE_CLEANUP_INTERVAL = 600  # seconds

# Sistem rolleri ve izinleri
SYSTEM_ROLES = {
    "superadmin": {
        "name": "Super Admin",
        "description": "Tam sistem kontrolü",
        "permissions": ["*"],
        "color": "#ff0000",
        "icon": "crown",
        "is_system_role": True
    },
    "admin": {
        "name": "Admin",
        "description": "Kullanıcı ve sistem yönetimi",
        "permissions": [
            "user.*", "role.*", "config.read", 
            "monitor.*", "log.*", "backup.*"
        ],
        "color": "#ff6600",
        "icon": "shield",
        "is_system_role": True
    },
    "operator": {
        "name": "Operator",
        "description": "Server ve monitoring yönetimi",
        "permissions": [
            "server.*", "monitor.*", "log.read", 
            "backup.read"
        ],
        "color": "#0066ff",
        "icon": "settings",
        "is_system_role": True
    },
    "viewer": {
        "name": "Viewer",
        "description": "Salt okunur erişim",
        "permissions": [
            "user.read", "monitor.read", "log.read", 
            "config.read"
        ],
        "color": "#00aa00",
        "icon": "eye",
        "is_system_role": True
    },
    "api_user": {
        "name": "API User",
        "description": "API erişim yetkisi",
        "permissions": ["api.*"],
        "color": "#aa00aa",
        "icon": "api",
        "is_system_role": True
    }
}

# Varsayılan izinler
DEFAULT_PERMISSIONS = [
    # User permissions
    "user.create", "user.read", "user.update", "user.delete",
    "user.list", "user.profile", "user.avatar",
    
    # Role permissions
    "role.create", "role.read", "role.update", "role.delete",
    "role.list", "role.assign",
    
    # Config permissions
    "config.read", "config.update", "config.backup", "config.restore",
    
    # Server permissions
    "server.start", "server.stop", "server.restart", "server.status",
    "server.config", "server.metrics",
    
    # Monitor permissions
    "monitor.system", "monitor.database", "monitor.api", "monitor.logs",
    "monitor.alerts", "monitor.metrics",
    
    # Log permissions
    "log.read", "log.export", "log.delete", "log.stats",
    
    # Backup permissions
    "backup.create", "backup.read", "backup.restore", "backup.delete",
    "backup.list", "backup.schedule",
    
    # API permissions
    "api.read", "api.create", "api.update", "api.delete",
    "api.test", "api.documentation",
    
    # File permissions
    "file.upload", "file.download", "file.delete", "file.list",
    
    # System permissions
    "system.info", "system.restart", "system.shutdown",
    "system.update", "system.maintenance"
]

# HTTP status kodları
HTTP_STATUS_CODES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable"
}

# Hata mesajları
ERROR_MESSAGES = {
    "INVALID_CREDENTIALS": "Geçersiz kullanıcı adı veya parola",
    "USER_NOT_FOUND": "Kullanıcı bulunamadı",
    "USER_ALREADY_EXISTS": "Kullanıcı zaten mevcut",
    "INVALID_TOKEN": "Geçersiz token",
    "TOKEN_EXPIRED": "Token süresi dolmuş",
    "INSUFFICIENT_PERMISSIONS": "Yetersiz yetki",
    "SERVER_ERROR": "Sunucu hatası",
    "VALIDATION_ERROR": "Doğrulama hatası",
    "RATE_LIMIT_EXCEEDED": "Rate limit aşıldı",
    "RESOURCE_NOT_FOUND": "Kaynak bulunamadı",
    "CONFLICT": "Çakışma hatası",
    "UNAUTHORIZED": "Yetkisiz erişim",
    "FORBIDDEN": "Erişim engellendi"
}

# Başarı mesajları
SUCCESS_MESSAGES = {
    "LOGIN_SUCCESS": "Giriş başarılı",
    "LOGOUT_SUCCESS": "Çıkış başarılı",
    "USER_CREATED": "Kullanıcı oluşturuldu",
    "USER_UPDATED": "Kullanıcı güncellendi",
    "USER_DELETED": "Kullanıcı silindi",
    "ROLE_CREATED": "Rol oluşturuldu",
    "ROLE_UPDATED": "Rol güncellendi",
    "ROLE_DELETED": "Rol silindi",
    "CONFIG_UPDATED": "Konfigürasyon güncellendi",
    "SERVER_STARTED": "Sunucu başlatıldı",
    "SERVER_STOPPED": "Sunucu durduruldu",
    "SERVER_RESTARTED": "Sunucu yeniden başlatıldı",
    "BACKUP_CREATED": "Yedek oluşturuldu",
    "BACKUP_RESTORED": "Yedek geri yüklendi"
}

# Regex patterns
REGEX_PATTERNS = {
    "EMAIL": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "USERNAME": r"^[a-zA-Z0-9_-]{3,20}$",
    "PASSWORD": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
    "IP_ADDRESS": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
    "URL": r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"
}

# MIME types
MIME_TYPES = {
    ".json": "application/json",
    ".xml": "application/xml",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".pdf": "application/pdf",
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip"
}

# Dosya boyut limitleri (bytes)
FILE_SIZE_LIMITS = {
    "AVATAR": 5 * 1024 * 1024,  # 5MB
    "CONFIG": 1 * 1024 * 1024,  # 1MB
    "LOG": 50 * 1024 * 1024,    # 50MB
    "BACKUP": 500 * 1024 * 1024, # 500MB
    "UPLOAD": 100 * 1024 * 1024  # 100MB
}

# Kullanıcı rolleri
class UserRole(Enum):
    """Kullanıcı rolleri"""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    API_USER = "api_user"
