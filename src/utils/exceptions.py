"""
Custom Exceptions module - Özel exception sınıfları

Bu modül uygulamada kullanılan özel exception sınıflarını içerir.
Hata türlerine göre kategorize edilmiş exception'lar.
"""

from typing import Optional, Dict, Any


class APIServerManagerError(Exception):
    """
    Uygulama ana exception sınıfı.
    
    Tüm özel exception'lar bu sınıftan türer.
    """
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        """
        APIServerManagerError'ı başlatır.
        
        Args:
            message: Hata mesajı
            error_code: Hata kodu
            details: Ek hata detayları
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "GENERAL_ERROR"
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Exception'ı dictionary'ye çevirir."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


# Authentication ve Authorization Exception'ları

class AuthenticationError(APIServerManagerError):
    """Kimlik doğrulama hatası."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTH_FAILED", **kwargs)


class AuthorizationError(APIServerManagerError):
    """Yetkilendirme hatası."""
    
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(message, error_code="ACCESS_DENIED", **kwargs)


class InvalidTokenError(AuthenticationError):
    """Geçersiz token hatası."""
    
    def __init__(self, message: str = "Invalid or expired token", **kwargs):
        super().__init__(message, error_code="INVALID_TOKEN", **kwargs)


class TokenExpiredError(AuthenticationError):
    """Token süresi dolmuş hatası."""
    
    def __init__(self, message: str = "Token has expired", **kwargs):
        super().__init__(message, error_code="TOKEN_EXPIRED", **kwargs)


class InsufficientPrivilegesError(AuthorizationError):
    """Yetersiz yetki hatası."""
    
    def __init__(self, message: str = "Insufficient privileges", **kwargs):
        super().__init__(message, error_code="INSUFFICIENT_PRIVILEGES", **kwargs)


class UserNotFoundError(AuthenticationError):
    """Kullanıcı bulunamadı hatası."""
    
    def __init__(self, message: str = "User not found", **kwargs):
        super().__init__(message, error_code="USER_NOT_FOUND", **kwargs)


class InvalidCredentialsError(AuthenticationError):
    """Geçersiz kimlik bilgileri hatası."""
    
    def __init__(self, message: str = "Invalid credentials", **kwargs):
        super().__init__(message, error_code="INVALID_CREDENTIALS", **kwargs)


class AccountLockedError(AuthenticationError):
    """Hesap kilitli hatası."""
    
    def __init__(self, message: str = "Account is locked", **kwargs):
        super().__init__(message, error_code="ACCOUNT_LOCKED", **kwargs)


# Database Exception'ları

class DatabaseError(APIServerManagerError):
    """Veritabanı hatası."""
    
    def __init__(self, message: str = "Database error", **kwargs):
        super().__init__(message, error_code="DATABASE_ERROR", **kwargs)


class ConnectionError(DatabaseError):
    """Veritabanı bağlantı hatası."""
    
    def __init__(self, message: str = "Database connection failed", **kwargs):
        super().__init__(message, error_code="DB_CONNECTION_FAILED", **kwargs)


class RecordNotFoundError(DatabaseError):
    """Kayıt bulunamadı hatası."""
    
    def __init__(self, message: str = "Record not found", **kwargs):
        super().__init__(message, error_code="RECORD_NOT_FOUND", **kwargs)


class DuplicateRecordError(DatabaseError):
    """Duplicate kayıt hatası."""
    
    def __init__(self, message: str = "Duplicate record", **kwargs):
        super().__init__(message, error_code="DUPLICATE_RECORD", **kwargs)


class ConstraintViolationError(DatabaseError):
    """Constraint ihlali hatası."""
    
    def __init__(self, message: str = "Database constraint violation", **kwargs):
        super().__init__(message, error_code="CONSTRAINT_VIOLATION", **kwargs)


class MigrationError(DatabaseError):
    """Migration hatası."""
    
    def __init__(self, message: str = "Database migration failed", **kwargs):
        super().__init__(message, error_code="MIGRATION_FAILED", **kwargs)


# Validation Exception'ları

class ValidationError(APIServerManagerError):
    """Validasyon hatası."""
    
    def __init__(self, message: str = "Validation failed", field: str = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_FAILED", **kwargs)
        self.field = field
        if field:
            self.details["field"] = field


class InvalidInputError(ValidationError):
    """Geçersiz input hatası."""
    
    def __init__(self, message: str = "Invalid input", **kwargs):
        super().__init__(message, error_code="INVALID_INPUT", **kwargs)


class RequiredFieldError(ValidationError):
    """Gerekli alan eksik hatası."""
    
    def __init__(self, field: str, message: str = None, **kwargs):
        message = message or f"Required field '{field}' is missing"
        super().__init__(message, field=field, error_code="REQUIRED_FIELD_MISSING", **kwargs)


class InvalidFormatError(ValidationError):
    """Geçersiz format hatası."""
    
    def __init__(self, field: str, expected_format: str = None, **kwargs):
        message = f"Invalid format for field '{field}'"
        if expected_format:
            message += f", expected: {expected_format}"
        super().__init__(message, field=field, error_code="INVALID_FORMAT", **kwargs)
        if expected_format:
            self.details["expected_format"] = expected_format


class ValueOutOfRangeError(ValidationError):
    """Değer aralık dışı hatası."""
    
    def __init__(self, field: str, min_value: Any = None, max_value: Any = None, **kwargs):
        message = f"Value out of range for field '{field}'"
        if min_value is not None and max_value is not None:
            message += f", allowed range: {min_value} - {max_value}"
        elif min_value is not None:
            message += f", minimum value: {min_value}"
        elif max_value is not None:
            message += f", maximum value: {max_value}"
        
        super().__init__(message, field=field, error_code="VALUE_OUT_OF_RANGE", **kwargs)
        if min_value is not None:
            self.details["min_value"] = min_value
        if max_value is not None:
            self.details["max_value"] = max_value


# Configuration Exception'ları

class ConfigurationError(APIServerManagerError):
    """Yapılandırma hatası."""
    
    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)


class InvalidConfigError(ConfigurationError):
    """Geçersiz yapılandırma hatası."""
    
    def __init__(self, setting: str, message: str = None, **kwargs):
        message = message or f"Invalid configuration for '{setting}'"
        super().__init__(message, error_code="INVALID_CONFIG", **kwargs)
        self.details["setting"] = setting


class MissingConfigError(ConfigurationError):
    """Eksik yapılandırma hatası."""
    
    def __init__(self, setting: str, **kwargs):
        message = f"Missing required configuration: '{setting}'"
        super().__init__(message, error_code="MISSING_CONFIG", **kwargs)
        self.details["setting"] = setting


class ConfigLoadError(ConfigurationError):
    """Yapılandırma yükleme hatası."""
    
    def __init__(self, file_path: str, **kwargs):
        message = f"Failed to load configuration from: {file_path}"
        super().__init__(message, error_code="CONFIG_LOAD_FAILED", **kwargs)
        self.details["file_path"] = file_path


# File ve Resource Exception'ları

class FileError(APIServerManagerError):
    """Dosya hatası."""
    
    def __init__(self, message: str = "File error", file_path: str = None, **kwargs):
        super().__init__(message, error_code="FILE_ERROR", **kwargs)
        if file_path:
            self.details["file_path"] = file_path


class FileNotFoundError(FileError):
    """Dosya bulunamadı hatası."""
    
    def __init__(self, file_path: str, **kwargs):
        message = f"File not found: {file_path}"
        super().__init__(message, file_path=file_path, error_code="FILE_NOT_FOUND", **kwargs)


class FilePermissionError(FileError):
    """Dosya izin hatası."""
    
    def __init__(self, file_path: str, operation: str = "access", **kwargs):
        message = f"Permission denied for {operation} operation on: {file_path}"
        super().__init__(message, file_path=file_path, error_code="FILE_PERMISSION_DENIED", **kwargs)
        self.details["operation"] = operation


class InvalidFileTypeError(FileError):
    """Geçersiz dosya türü hatası."""
    
    def __init__(self, file_path: str, expected_types: list = None, **kwargs):
        message = f"Invalid file type: {file_path}"
        if expected_types:
            message += f", expected: {', '.join(expected_types)}"
        super().__init__(message, file_path=file_path, error_code="INVALID_FILE_TYPE", **kwargs)
        if expected_types:
            self.details["expected_types"] = expected_types


class FileSizeExceededError(FileError):
    """Dosya boyutu aşıldı hatası."""
    
    def __init__(self, file_path: str, max_size: int, actual_size: int = None, **kwargs):
        message = f"File size exceeded for: {file_path}, maximum allowed: {max_size} bytes"
        if actual_size:
            message += f", actual size: {actual_size} bytes"
        super().__init__(message, file_path=file_path, error_code="FILE_SIZE_EXCEEDED", **kwargs)
        self.details["max_size"] = max_size
        if actual_size:
            self.details["actual_size"] = actual_size


# Server ve Network Exception'ları

class ServerError(APIServerManagerError):
    """Server hatası."""
    
    def __init__(self, message: str = "Server error", **kwargs):
        super().__init__(message, error_code="SERVER_ERROR", **kwargs)


class ServerStartupError(ServerError):
    """Server başlatma hatası."""
    
    def __init__(self, message: str = "Failed to start server", port: int = None, **kwargs):
        super().__init__(message, error_code="SERVER_STARTUP_FAILED", **kwargs)
        if port:
            self.details["port"] = port


class ServerShutdownError(ServerError):
    """Server kapatma hatası."""
    
    def __init__(self, message: str = "Failed to shutdown server", **kwargs):
        super().__init__(message, error_code="SERVER_SHUTDOWN_FAILED", **kwargs)


class PortAlreadyInUseError(ServerStartupError):
    """Port zaten kullanımda hatası."""
    
    def __init__(self, port: int, **kwargs):
        message = f"Port {port} is already in use"
        super().__init__(message, port=port, error_code="PORT_IN_USE", **kwargs)


class NetworkError(ServerError):
    """Ağ hatası."""
    
    def __init__(self, message: str = "Network error", **kwargs):
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)


class TimeoutError(NetworkError):
    """Timeout hatası."""
    
    def __init__(self, message: str = "Operation timed out", timeout: float = None, **kwargs):
        super().__init__(message, error_code="TIMEOUT", **kwargs)
        if timeout:
            self.details["timeout"] = timeout


# API Exception'ları

class APIError(APIServerManagerError):
    """API hatası."""
    
    def __init__(self, message: str = "API error", status_code: int = 500, **kwargs):
        super().__init__(message, error_code="API_ERROR", **kwargs)
        self.status_code = status_code
        self.details["status_code"] = status_code


class InvalidRequestError(APIError):
    """Geçersiz istek hatası."""
    
    def __init__(self, message: str = "Invalid request", **kwargs):
        super().__init__(message, status_code=400, error_code="INVALID_REQUEST", **kwargs)


class ResourceNotFoundError(APIError):
    """Kaynak bulunamadı hatası."""
    
    def __init__(self, resource: str = "Resource", **kwargs):
        message = f"{resource} not found"
        super().__init__(message, status_code=404, error_code="RESOURCE_NOT_FOUND", **kwargs)
        self.details["resource"] = resource


class MethodNotAllowedError(APIError):
    """İzin verilmeyen metod hatası."""
    
    def __init__(self, method: str, allowed_methods: list = None, **kwargs):
        message = f"Method '{method}' not allowed"
        if allowed_methods:
            message += f", allowed methods: {', '.join(allowed_methods)}"
        super().__init__(message, status_code=405, error_code="METHOD_NOT_ALLOWED", **kwargs)
        self.details["method"] = method
        if allowed_methods:
            self.details["allowed_methods"] = allowed_methods


class RateLimitExceededError(APIError):
    """Rate limit aşıldı hatası."""
    
    def __init__(self, limit: int, window: int, **kwargs):
        message = f"Rate limit exceeded: {limit} requests per {window} seconds"
        super().__init__(message, status_code=429, error_code="RATE_LIMIT_EXCEEDED", **kwargs)
        self.details.update({"limit": limit, "window": window})


class ConflictError(APIError):
    """Çakışma hatası."""
    
    def __init__(self, message: str = "Resource conflict", **kwargs):
        super().__init__(message, status_code=409, error_code="CONFLICT", **kwargs)


# Monitoring ve Alert Exception'ları

class MonitoringError(APIServerManagerError):
    """İzleme hatası."""
    
    def __init__(self, message: str = "Monitoring error", **kwargs):
        super().__init__(message, error_code="MONITORING_ERROR", **kwargs)


class MetricCollectionError(MonitoringError):
    """Metrik toplama hatası."""
    
    def __init__(self, metric_name: str, **kwargs):
        message = f"Failed to collect metric: {metric_name}"
        super().__init__(message, error_code="METRIC_COLLECTION_FAILED", **kwargs)
        self.details["metric_name"] = metric_name


class AlertError(MonitoringError):
    """Alert hatası."""
    
    def __init__(self, message: str = "Alert error", alert_id: str = None, **kwargs):
        super().__init__(message, error_code="ALERT_ERROR", **kwargs)
        if alert_id:
            self.details["alert_id"] = alert_id


class ThresholdExceededError(AlertError):
    """Eşik aşıldı hatası."""
    
    def __init__(self, metric: str, value: float, threshold: float, **kwargs):
        message = f"Threshold exceeded for {metric}: {value} > {threshold}"
        super().__init__(message, error_code="THRESHOLD_EXCEEDED", **kwargs)
        self.details.update({
            "metric": metric,
            "value": value,
            "threshold": threshold
        })


# Backup ve Maintenance Exception'ları

class BackupError(APIServerManagerError):
    """Yedekleme hatası."""
    
    def __init__(self, message: str = "Backup error", **kwargs):
        super().__init__(message, error_code="BACKUP_ERROR", **kwargs)


class BackupCreationError(BackupError):
    """Yedek oluşturma hatası."""
    
    def __init__(self, backup_type: str, **kwargs):
        message = f"Failed to create {backup_type} backup"
        super().__init__(message, error_code="BACKUP_CREATION_FAILED", **kwargs)
        self.details["backup_type"] = backup_type


class BackupRestoreError(BackupError):
    """Yedek geri yükleme hatası."""
    
    def __init__(self, backup_id: str = None, **kwargs):
        message = "Failed to restore backup"
        if backup_id:
            message += f" (ID: {backup_id})"
        super().__init__(message, error_code="BACKUP_RESTORE_FAILED", **kwargs)
        if backup_id:
            self.details["backup_id"] = backup_id


class MaintenanceError(APIServerManagerError):
    """Bakım hatası."""
    
    def __init__(self, message: str = "Maintenance error", **kwargs):
        super().__init__(message, error_code="MAINTENANCE_ERROR", **kwargs)


# Utility fonksiyonlar

def handle_exception(exc: Exception) -> Dict[str, Any]:
    """
    Exception'ı handle eder ve standart format döndürür.
    
    Args:
        exc: Handle edilecek exception
        
    Returns:
        Standart hata formatı
    """
    if isinstance(exc, APIServerManagerError):
        return exc.to_dict()
    else:
        return {
            "error": exc.__class__.__name__,
            "message": str(exc),
            "error_code": "INTERNAL_ERROR",
            "details": {}
        }


def create_error_response(exc: Exception, include_traceback: bool = False) -> Dict[str, Any]:
    """
    Exception'dan error response oluşturur.
    
    Args:
        exc: Exception
        include_traceback: Traceback dahil et
        
    Returns:
        Error response
    """
    import traceback
    
    error_data = handle_exception(exc)
    
    response = {
        "success": False,
        "error": error_data
    }
    
    if include_traceback and not isinstance(exc, APIServerManagerError):
        response["traceback"] = traceback.format_exc()
    
    return response
