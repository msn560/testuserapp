"""
Logger module - Logging sistemi

Bu modül uygulama genelinde kullanılan logging sistemini sağlar.
Farklı log seviyeleri, dosya rotasyonu ve formatlama özellikleri içerir.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

from ..core.constants import LogLevel, LOGS_DIR, DEFAULT_LOG_FORMAT


class ColoredFormatter(logging.Formatter):
    """Renkli log formatter"""
    
    # ANSI renk kodları
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        """Log kaydını formatla"""
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON log formatter"""
    
    def format(self, record):
        """Log kaydını JSON formatında formatla"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Ekstra alanlar varsa ekle
        if hasattr(record, 'extra_data'):
            log_entry['extra_data'] = record.extra_data
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class Logger:
    """
    Ana logger sınıfı
    
    Uygulama genelinde kullanılan logging sistemini yönetir.
    Farklı log seviyeleri, dosya rotasyonu ve formatlama özellikleri sağlar.
    """
    
    _instances: Dict[str, 'Logger'] = {}
    _initialized = False
    
    def __new__(cls, name: str = __name__):
        """Singleton pattern ile logger instance'ı döndür"""
        if name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[name] = instance
            instance._initialized = False  # Initialize flag'i ekle
        return cls._instances[name]
    
    def __init__(self, name: str = __name__):
        """
        Logger'ı başlat
        
        Args:
            name: Logger adı
        """
        if self._initialized:
            return
        
        self.name = name
        # Tüm logger'ları global logger'ı kullanacak şekilde ayarla
        self.logger = logging.getLogger("global")
        self.logger.setLevel(logging.DEBUG)
        
        # Handler'ları temizle - sadece bu logger'ın handler'larını temizle
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Handler'ları ekle - sadece handler yoksa ekle
        if not self.logger.handlers:
            self._setup_handlers()
        
        self._initialized = True
    
    def _setup_handlers(self):
        """Handler'ları ayarla"""
        # Console handler
        self._setup_console_handler()
        
        # File handlers
        self._setup_file_handlers()
        
        # Error file handler
        self._setup_error_handler()
    
    def _setup_console_handler(self):
        """Console handler'ı ayarla"""
        # Root logger'ın handler'larını kontrol et
        root_logger = logging.getLogger()
        if root_logger.handlers:
            # Root logger'da handler varsa, bu logger'ı root'a propagate etme
            self.logger.propagate = False
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Renkli formatter
        if sys.stdout.isatty():
            formatter = ColoredFormatter(DEFAULT_LOG_FORMAT)
        else:
            formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handlers(self):
        """Dosya handler'larını ayarla"""
        # Logs klasörünü oluştur
        logs_dir = Path(LOGS_DIR)
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Logging ayarlarını config'den al
        from ..core.settings import settings
        max_bytes = settings.logging.file_max_size
        backup_count = settings.logging.file_backup_count
        
        # Genel log dosyası
        general_log_file = logs_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        general_handler = logging.handlers.RotatingFileHandler(
            general_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        general_handler.setLevel(logging.DEBUG)
        general_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        self.logger.addHandler(general_handler)
        
        # API log dosyası
        api_log_file = logs_dir / f"api_{datetime.now().strftime('%Y%m%d')}.log"
        api_handler = logging.handlers.RotatingFileHandler(
            api_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        api_handler.setLevel(logging.INFO)
        api_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(api_handler)
        
        # Security log dosyası
        security_log_file = logs_dir / f"security_{datetime.now().strftime('%Y%m%d')}.log"
        security_handler = logging.handlers.RotatingFileHandler(
            security_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(security_handler)
    
    def _setup_error_handler(self):
        """Error handler'ı ayarla"""
        logs_dir = Path(LOGS_DIR)
        error_log_file = logs_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Logging ayarlarını config'den al
        from ..core.settings import settings
        max_bytes = settings.logging.file_max_size
        backup_count = settings.logging.file_backup_count
        
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Debug seviyesinde log"""
        self._log(logging.DEBUG, message, extra_data, **kwargs)
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Info seviyesinde log"""
        self._log(logging.INFO, message, extra_data, **kwargs)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Warning seviyesinde log"""
        self._log(logging.WARNING, message, extra_data, **kwargs)
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Error seviyesinde log"""
        self._log(logging.ERROR, message, extra_data, **kwargs)
    
    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Critical seviyesinde log"""
        self._log(logging.CRITICAL, message, extra_data, **kwargs)
    
    def _log(self, level: int, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Log kaydı oluştur
        
        Args:
            level: Log seviyesi
            message: Log mesajı
            extra_data: Ekstra veri
            **kwargs: Ekstra alanlar
        """
        extra = {}
        
        if extra_data:
            extra['extra_data'] = extra_data
        
        # Ekstra alanları ekle
        for key, value in kwargs.items():
            extra[key] = value
        
        self.logger.log(level, message, extra=extra)
    
    def log_api_request(self, method: str, path: str, status_code: int, 
                       response_time: float, user_id: Optional[int] = None,
                       ip_address: Optional[str] = None, **kwargs):
        """
        API request log'u
        
        Args:
            method: HTTP metodu
            path: Request path
            status_code: HTTP status kodu
            response_time: Response süresi
            user_id: Kullanıcı ID
            ip_address: IP adresi
            **kwargs: Ekstra alanlar
        """
        message = f"API Request: {method} {path} - {status_code} ({response_time:.3f}s)"
        
        extra = {
            'api_method': method,
            'api_path': path,
            'status_code': status_code,
            'response_time': response_time,
            **kwargs
        }
        
        if user_id:
            extra['user_id'] = user_id
        
        if ip_address:
            extra['ip_address'] = ip_address
        
        self.info(message, extra_data=extra)
    
    def log_security_event(self, event_type: str, message: str, 
                          user_id: Optional[int] = None,
                          ip_address: Optional[str] = None, **kwargs):
        """
        Güvenlik olayı log'u
        
        Args:
            event_type: Olay türü
            message: Log mesajı
            user_id: Kullanıcı ID
            ip_address: IP adresi
            **kwargs: Ekstra alanlar
        """
        log_message = f"Security Event [{event_type}]: {message}"
        
        extra = {
            'security_event_type': event_type,
            **kwargs
        }
        
        if user_id:
            extra['user_id'] = user_id
        
        if ip_address:
            extra['ip_address'] = ip_address
        
        self.warning(log_message, extra_data=extra)
    
    def log_user_action(self, action: str, user_id: int, 
                       details: Optional[str] = None,
                       ip_address: Optional[str] = None, **kwargs):
        """
        Kullanıcı aksiyonu log'u
        
        Args:
            action: Aksiyon türü
            user_id: Kullanıcı ID
            details: Detaylar
            ip_address: IP adresi
            **kwargs: Ekstra alanlar
        """
        message = f"User Action [{action}]: User {user_id}"
        if details:
            message += f" - {details}"
        
        extra = {
            'user_action': action,
            'user_id': user_id,
            **kwargs
        }
        
        if details:
            extra['details'] = details
        
        if ip_address:
            extra['ip_address'] = ip_address
        
        self.info(message, extra_data=extra)
    
    def log_system_event(self, event_type: str, message: str, **kwargs):
        """
        Sistem olayı log'u
        
        Args:
            event_type: Olay türü
            message: Log mesajı
            **kwargs: Ekstra alanlar
        """
        log_message = f"System Event [{event_type}]: {message}"
        
        extra = {
            'system_event_type': event_type,
            **kwargs
        }
        
        self.info(log_message, extra_data=extra)
    
    def set_level(self, level: LogLevel):
        """
        Log seviyesini ayarla
        
        Args:
            level: Log seviyesi
        """
        self.logger.setLevel(level.value)
    
    def get_level(self) -> LogLevel:
        """
        Mevcut log seviyesini al
        
        Returns:
            Log seviyesi
        """
        return LogLevel(self.logger.level)
    
    def add_handler(self, handler: logging.Handler):
        """
        Handler ekle
        
        Args:
            handler: Log handler
        """
        self.logger.addHandler(handler)
    
    def remove_handler(self, handler: logging.Handler):
        """
        Handler kaldır
        
        Args:
            handler: Log handler
        """
        self.logger.removeHandler(handler)
    
    def get_log_files(self) -> Dict[str, str]:
        """
        Log dosyalarını al
        
        Returns:
            Log dosya yolları
        """
        logs_dir = Path(LOGS_DIR)
        today = datetime.now().strftime('%Y%m%d')
        
        return {
            'general': str(logs_dir / f"app_{today}.log"),
            'api': str(logs_dir / f"api_{today}.log"),
            'security': str(logs_dir / f"security_{today}.log"),
            'error': str(logs_dir / f"error_{today}.log")
        }
    
    def clear_old_logs(self, days: int = 30):
        """
        Eski log dosyalarını temizle
        
        Args:
            days: Kaç gün önceki loglar silinecek
        """
        try:
            logs_dir = Path(LOGS_DIR)
            if not logs_dir.exists():
                return
            
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for log_file in logs_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    self.info(f"Eski log dosyası silindi: {log_file}")
        
        except Exception as e:
            self.error(f"Eski log dosyaları temizlenemedi: {e}")
    
    @classmethod
    def get_logger(cls, name: str) -> 'Logger':
        """
        Logger instance'ı al
        
        Args:
            name: Logger adı
            
        Returns:
            Logger instance
        """
        return cls(name)
    
    @classmethod
    def configure_global_logging(cls, level: LogLevel = LogLevel.INFO):
        """
        Global logging'i yapılandır
        
        Args:
            level: Log seviyesi
        """
        # Root logger'ı yapılandır
        root_logger = logging.getLogger()
        root_logger.setLevel(level.value)
        
        # Mevcut handler'ları temizle
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler ekle
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level.value)
        
        if sys.stdout.isatty():
            formatter = ColoredFormatter(DEFAULT_LOG_FORMAT)
        else:
            formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
        
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


# Global logger instance
logger = Logger("global")
