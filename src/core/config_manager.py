"""
Config Manager module - JSON config yönetimi

Bu modül JSON tabanlı konfigürasyon dosyası yönetimini sağlar.
Config dosyasını okur, yazar ve günceller.
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import shutil

from .settings import Settings, settings
from .constants import CONFIG_FILE, BACKUP_DIR
from ..utils.logger import Logger


class ConfigManager:
    """
    Konfigürasyon yöneticisi
    
    JSON tabanlı konfigürasyon dosyasını yönetir.
    Config dosyasını okur, yazar, günceller ve yedekler.
    """
    
    def __init__(self, config_file: str = CONFIG_FILE):
        """
        ConfigManager'ı başlat
        
        Args:
            config_file: Konfigürasyon dosyası yolu
        """
        self.config_file = Path(config_file)
        self.logger = Logger(__name__)
        self.settings = settings
        
        # Config dosyası yoksa oluştur
        if not self.config_file.exists():
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Varsayılan konfigürasyon dosyasını oluştur"""
        try:
            # Klasörü oluştur
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Varsayılan ayarları al
            default_config = self.settings.get_all_settings()
            
            # Dosyayı yaz
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Varsayılan konfigürasyon dosyası oluşturuldu: {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Varsayılan konfigürasyon dosyası oluşturulamadı: {e}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Varsayılan konfigürasyonu döndür
        
        Returns:
            Varsayılan konfigürasyon sözlüğü
        """
        try:
            return self.settings.get_all_settings()
        except Exception as e:
            self.logger.error(f"Varsayılan konfigürasyon alınamadı: {e}")
            # Fallback varsayılan config
            return {
                "app": {
                    "name": "API Server Management System",
                    "version": "1.0.0",
                    "description": "Modern API Server Management System with GUI and REST API",
                    "author": "API Server Manager Team",
                    "debug": False,
                    "development_mode": False
                },
                "database": "sqlite:///data/app.db",
                "server": {
                    "host": "localhost",
                    "port": 8080,
                    "ssl": False,
                    "ssl_cert_path": "",
                    "ssl_key_path": "",
                    "auto_start": False,
                    "max_connections": 1000,
                    "timeout": 30,
                    "cors_origins": ["*"],
                    "cors_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "cors_headers": ["Content-Type", "Authorization"]
                },
                "security": {
                    "jwt_secret_key": "your-super-secret-jwt-key-change-this-in-production",
                    "jwt_algorithm": "HS256",
                    "jwt_access_token_expire_minutes": 30,
                    "jwt_refresh_token_expire_days": 7,
                    "bcrypt_rounds": 12,
                    "password_min_length": 8,
                    "password_require_uppercase": True,
                    "password_require_lowercase": True,
                    "password_require_numbers": True,
                    "password_require_special_chars": True,
                    "session_timeout_minutes": 30,
                    "max_login_attempts": 5,
                    "lockout_duration_minutes": 15
                },
                "ui": {
                    "theme": "dark",
                    "language": "tr",
                    "show_splash_screen": True,
                    "splash_screen_duration": 3000,
                    "window_width": 1200,
                    "window_height": 800,
                    "window_min_width": 800,
                    "window_min_height": 600,
                    "window_x": 100,
                    "window_y": 100,
                    "remember_window_state": True,
                    "always_on_top": False,
                    "auto_refresh_interval": 5000
                },
                "rate_limiting": {
                    "enabled": True,
                    "requests_per_minute": 100,
                    "burst_size": 10,
                    "per_ip_limit": True,
                    "per_user_limit": True
                },
                "backup": {
                    "enabled": True,
                    "interval_hours": 24,
                    "retention_days": 7,
                    "backup_path": "data/backup",
                    "compress": True,
                    "include_logs": True,
                    "include_config": True,
                    "auto_cleanup": True
                },
                "logging": {
                    "level": 20,
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "file_max_size": 10485760,
                    "file_backup_count": 5,
                    "console_output": True,
                    "file_output": True,
                    "log_file_path": "data/logs/app_{date}.log",
                    "error_file_path": "data/logs/error_{date}.log",
                    "security_file_path": "data/logs/security_{date}.log",
                    "api_file_path": "data/logs/api_{date}.log"
                }
            }
    
    def load_config(self) -> Dict[str, Any]:
        """
        Konfigürasyon dosyasını yükle
        
        Returns:
            Konfigürasyon sözlüğü
            
        Raises:
            FileNotFoundError: Config dosyası bulunamadı
            json.JSONDecodeError: JSON format hatası
        """
        try:
            if not self.config_file.exists():
                self.logger.warning(f"Konfigürasyon dosyası bulunamadı: {self.config_file}")
                # Varsayılan config'i oluştur
                default_config = self._get_default_config()
                self.save_config(default_config)
                return default_config
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Config'in dict olduğunu kontrol et
            if not isinstance(config, dict):
                self.logger.error("Config dosyası geçersiz format, varsayılan ayarlar kullanılıyor")
                return self._get_default_config()
            
            # Eksik ayarları otomatik ekle
            config = self._merge_missing_settings(config)
            
            self.logger.info(f"Konfigürasyon dosyası yüklendi: {self.config_file}")
            return config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON format hatası: {e}")
            return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Konfigürasyon yüklenemedi: {e}")
            return self._get_default_config()
    
    def _merge_missing_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Eksik ayarları varsayılan ayarlarla birleştir
        
        Args:
            config: Mevcut konfigürasyon
            
        Returns:
            Birleştirilmiş konfigürasyon
        """
        try:
            default_config = self._get_default_config()
            merged_config = self._deep_merge(default_config, config)
            
            # Eğer değişiklik varsa config'i kaydet
            if merged_config != config:
                self.logger.info("Eksik ayarlar varsayılan değerlerle eklendi")
                self.save_config(merged_config)
            
            return merged_config
            
        except Exception as e:
            self.logger.error(f"Ayar birleştirme hatası: {e}")
            return config
    
    def _deep_merge(self, default: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        """
        İki sözlüğü derinlemesine birleştir
        
        Args:
            default: Varsayılan değerler
            current: Mevcut değerler
            
        Returns:
            Birleştirilmiş sözlük
        """
        result = default.copy()
        
        for key, value in current.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """
        Konfigürasyon dosyasını kaydet
        
        Args:
            config: Kaydedilecek konfigürasyon
            
        Raises:
            PermissionError: Dosya yazma izni yok
        """
        try:
            # Yedek oluştur
            self._backup_config()
            
            # Geçici dosya ile yaz
            temp_file = self.config_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Geçici dosyayı asıl dosya ile değiştir
            temp_file.replace(self.config_file)
            
            self.logger.info(f"Konfigürasyon dosyası kaydedildi: {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon kaydedilemedi: {e}")
            raise
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Konfigürasyonu güncelle
        
        Args:
            updates: Güncellenecek ayarlar
        """
        try:
            # Mevcut konfigürasyonu yükle
            config = self.load_config()
            
            # Güncellemeleri uygula
            self._deep_update(config, updates)
            
            # Konfigürasyonu kaydet
            self.save_config(config)
            
            # Settings'i güncelle
            self.settings.update_from_dict(updates)
            
            self.logger.info("Konfigürasyon güncellendi")
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon güncellenemedi: {e}")
            raise
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        Konfigürasyon değerini al
        
        Args:
            key_path: Nokta ile ayrılmış anahtar yolu (örn: "server.port")
            default: Varsayılan değer
            
        Returns:
            Konfigürasyon değeri
        """
        try:
            config = self.load_config()
            keys = key_path.split('.')
            value = config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon değeri alınamadı ({key_path}): {e}")
            return default
    
    def set_config_value(self, key_path: str, value: Any) -> None:
        """
        Konfigürasyon değerini ayarla
        
        Args:
            key_path: Nokta ile ayrılmış anahtar yolu
            value: Ayarlanacak değer
        """
        try:
            config = self.load_config()
            keys = key_path.split('.')
            current = config
            
            # Son anahtara kadar git
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Değeri ayarla
            current[keys[-1]] = value
            
            # Konfigürasyonu kaydet
            self.save_config(config)
            
            self.logger.info(f"Konfigürasyon değeri ayarlandı: {key_path} = {value}")
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon değeri ayarlanamadı ({key_path}): {e}")
            raise
    
    def reset_to_default(self) -> None:
        """Konfigürasyonu varsayılan değerlere sıfırla"""
        try:
            # Yedek oluştur
            self._backup_config()
            
            # Varsayılan ayarları al
            default_config = self.settings.get_all_settings()
            
            # Konfigürasyonu kaydet
            self.save_config(default_config)
            
            # Settings'i güncelle
            self.settings.update_from_dict(default_config)
            
            self.logger.info("Konfigürasyon varsayılan değerlere sıfırlandı")
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon sıfırlanamadı: {e}")
            raise
    
    def validate_config(self) -> List[str]:
        """
        Konfigürasyonu doğrula
        
        Returns:
            Hata listesi
        """
        try:
            config = self.load_config()
            
            # Config'in dict olup olmadığını kontrol et
            if not isinstance(config, dict):
                self.logger.error(f"Config validation error: Config is not a dictionary")
                return ["Config validation failed"]
            
            errors = []
            
            # Gerekli bölümleri kontrol et
            required_sections = ['app', 'server', 'database', 'security', 'logging']
            for section in required_sections:
                if section not in config:
                    errors.append(f"Gerekli bölüm eksik: {section}")
            
            # Server port kontrolü
            if 'server' in config and isinstance(config['server'], dict) and 'port' in config['server']:
                port = config['server']['port']
                if not isinstance(port, int) or not (1 <= port <= 65535):
                    errors.append("Server port 1-65535 arasında olmalıdır")
            
            # JWT secret key kontrolü
            if 'security' in config and isinstance(config['security'], dict) and 'jwt_secret_key' in config['security']:
                secret_key = config['security']['jwt_secret_key']
                if not isinstance(secret_key, str) or len(secret_key) < 32:
                    errors.append("JWT secret key en az 32 karakter olmalıdır")
            
            # Log level kontrolü
            if 'logging' in config and isinstance(config['logging'], dict) and 'level' in config['logging']:
                level = config['logging']['level']
                # Log level sayısal değer olabilir (10, 20, 30, 40, 50)
                valid_levels = [10, 20, 30, 40, 50, 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
                if level not in valid_levels:
                    errors.append(f"Geçersiz log seviyesi: {level}")
            
            return errors
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon doğrulanamadı: {e}")
            return [f"Konfigürasyon doğrulama hatası: {e}"]
    
    def export_config(self, export_path: str) -> None:
        """
        Konfigürasyonu dışa aktar
        
        Args:
            export_path: Dışa aktarım yolu
        """
        try:
            config = self.load_config()
            export_file = Path(export_path)
            
            # Klasörü oluştur
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Dosyayı yaz
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Konfigürasyon dışa aktarıldı: {export_path}")
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon dışa aktarılamadı: {e}")
            raise
    
    def import_config(self, import_path: str) -> None:
        """
        Konfigürasyonu içe aktar
        
        Args:
            import_path: İçe aktarım yolu
        """
        try:
            import_file = Path(import_path)
            
            if not import_file.exists():
                raise FileNotFoundError(f"İçe aktarım dosyası bulunamadı: {import_path}")
            
            # Dosyayı oku
            with open(import_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Konfigürasyonu doğrula
            errors = self._validate_imported_config(config)
            if errors:
                raise ValueError(f"İçe aktarılan konfigürasyon geçersiz: {', '.join(errors)}")
            
            # Yedek oluştur
            self._backup_config()
            
            # Konfigürasyonu kaydet
            self.save_config(config)
            
            # Settings'i güncelle
            self.settings.update_from_dict(config)
            
            self.logger.info(f"Konfigürasyon içe aktarıldı: {import_path}")
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon içe aktarılamadı: {e}")
            raise
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """
        Derinlemesine sözlük güncelleme
        
        Args:
            base_dict: Güncellenecek temel sözlük
            update_dict: Güncelleme sözlüğü
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _backup_config(self) -> None:
        """Konfigürasyon yedeği oluştur"""
        try:
            if not self.config_file.exists():
                return
            
            # Yedek klasörünü oluştur
            backup_dir = Path(BACKUP_DIR)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Yedek dosya adı
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"config_backup_{timestamp}.json"
            
            # Yedek oluştur
            shutil.copy2(self.config_file, backup_file)
            
            self.logger.info(f"Konfigürasyon yedeği oluşturuldu: {backup_file}")
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon yedeği oluşturulamadı: {e}")
    
    def _validate_imported_config(self, config: Dict[str, Any]) -> List[str]:
        """
        İçe aktarılan konfigürasyonu doğrula
        
        Args:
            config: Doğrulanacak konfigürasyon
            
        Returns:
            Hata listesi
        """
        errors = []
        
        # Gerekli bölümleri kontrol et
        required_sections = ['app', 'server', 'database', 'security']
        for section in required_sections:
            if section not in config:
                errors.append(f"Gerekli bölüm eksik: {section}")
        
        # Server port kontrolü
        if 'server' in config and 'port' in config['server']:
            port = config['server']['port']
            if not isinstance(port, int) or not (1 <= port <= 65535):
                errors.append("Server port 1-65535 arasında olmalıdır")
        
        return errors
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        Konfigürasyon bilgilerini al
        
        Returns:
            Konfigürasyon bilgileri
        """
        try:
            config = self.load_config()
            
            return {
                "file_path": str(self.config_file),
                "file_size": self.config_file.stat().st_size if self.config_file.exists() else 0,
                "last_modified": datetime.fromtimestamp(
                    self.config_file.stat().st_mtime
                ).isoformat() if self.config_file.exists() else None,
                "sections": list(config.keys()),
                "is_valid": len(self.validate_config()) == 0,
                "errors": self.validate_config()
            }
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon bilgileri alınamadı: {e}")
            return {
                "file_path": str(self.config_file),
                "file_size": 0,
                "last_modified": None,
                "sections": [],
                "is_valid": False,
                "errors": [str(e)]
            }


# Global config manager instance
config_manager = ConfigManager()
