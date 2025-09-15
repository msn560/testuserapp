"""
Config Service module - Yapılandırma yönetimi

Bu modül uygulama yapılandırmasının yönetimini sağlar.
Config dosyası okuma/yazma, ayar güncelleme ve yapılandırma doğrulama.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import threading
import shutil

from ..core.constants import LogLevel
from ..core.config_manager import config_manager
from ..db.models import Config, SystemSettings
from ..utils.logger import logger


class ConfigService:
    """
    Yapılandırma yönetimi servisi.
    
    Bu sınıf uygulama yapılandırmasının yönetimini sağlar.
    """
    
    def __init__(self, config_file: str = "data/config.json"):
        """
        ConfigService'i başlatır.
        
        Args:
            config_file: Yapılandırma dosyası yolu
        """
        self.logger = logger
        self.config_file = Path(config_file)
        self.config_data: Dict[str, Any] = {}
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Backup dizini
        self.backup_dir = Path("data/backup")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Varsayılan yapılandırma
        self.default_config = self._get_default_config()
        
        # Yapılandırmayı yükle
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Yapılandırma dosyasını yükler.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if not self.config_file.exists():
                self.logger.warning(f"Config file not found: {self.config_file}")
                self._create_default_config()
                return True
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            
            # Varsayılan değerleri ekle
            self._merge_defaults()
            
            # Yapılandırmayı doğrula
            if not self._validate_config():
                self.logger.error("Config validation failed")
                return False
            
            self.logger.info(f"Config loaded from {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return False
    
    def save_config(self, backup: bool = True) -> bool:
        """
        Yapılandırmayı dosyaya kaydeder.
        
        Args:
            backup: Yedek oluştur
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with self.lock:
                # Yedek oluştur
                if backup and self.config_file.exists():
                    self._create_backup()
                
                # Yapılandırmayı doğrula
                if not self._validate_config():
                    self.logger.error("Config validation failed before save")
                    return False
                
                # Dosyaya yaz
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config_data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Config saved to {self.config_file}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
    
    def get_config(self, key: str = None, default: Any = None) -> Any:
        """
        Yapılandırma değeri alır.
        
        Args:
            key: Yapılandırma anahtarı (noktalı notasyon desteklenir)
            default: Varsayılan değer
            
        Returns:
            Yapılandırma değeri
        """
        try:
            if key is None:
                return self.config_data.copy()
            
            # Noktalı notasyon desteği
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"Failed to get config value for key '{key}': {e}")
            return default
    
    def set_config(self, key: str, value: Any, save: bool = True) -> bool:
        """
        Yapılandırma değeri ayarlar.
        
        Args:
            key: Yapılandırma anahtarı (noktalı notasyon desteklenir)
            value: Yeni değer
            save: Dosyaya kaydet
            
        Returns:
            True if set successfully, False otherwise
        """
        try:
            with self.lock:
                # Noktalı notasyon desteği
                keys = key.split('.')
                config = self.config_data
                
                # Son anahtar hariç tüm anahtarları oluştur
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                
                # Son anahtarı ayarla
                config[keys[-1]] = value
                
                # Yapılandırmayı doğrula
                if not self._validate_config():
                    self.logger.error(f"Config validation failed for key '{key}'")
                    return False
                
                # Dosyaya kaydet
                if save:
                    return self.save_config()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to set config value for key '{key}': {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any], save: bool = True) -> bool:
        """
        Birden fazla yapılandırma değerini günceller.
        
        Args:
            updates: Güncellenecek değerler
            save: Dosyaya kaydet
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            with self.lock:
                # Değerleri güncelle
                for key, value in updates.items():
                    keys = key.split('.')
                    config = self.config_data
                    
                    for k in keys[:-1]:
                        if k not in config:
                            config[k] = {}
                        config = config[k]
                    
                    config[keys[-1]] = value
                
                # Yapılandırmayı doğrula
                if not self._validate_config():
                    self.logger.error("Config validation failed after update")
                    return False
                
                # Dosyaya kaydet
                if save:
                    return self.save_config()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False
    
    def reset_config(self, category: str = None) -> bool:
        """
        Yapılandırmayı varsayılan değerlere sıfırlar.
        
        Args:
            category: Sıfırlanacak kategori (None ise tümü)
            
        Returns:
            True if reset successfully, False otherwise
        """
        try:
            with self.lock:
                if category:
                    # Belirli kategoriyi sıfırla
                    if category in self.default_config:
                        self.config_data[category] = self.default_config[category].copy()
                else:
                    # Tüm yapılandırmayı sıfırla
                    self.config_data = self.default_config.copy()
                
                return self.save_config()
                
        except Exception as e:
            self.logger.error(f"Failed to reset config: {e}")
            return False
    
    def get_config_categories(self) -> List[str]:
        """
        Yapılandırma kategorilerini döndürür.
        
        Returns:
            Kategori listesi
        """
        try:
            return list(self.config_data.keys())
            
        except Exception as e:
            self.logger.error(f"Failed to get config categories: {e}")
            return []
    
    def get_config_by_category(self, category: str) -> Dict[str, Any]:
        """
        Kategoriye göre yapılandırmayı döndürür.
        
        Args:
            category: Kategori adı
            
        Returns:
            Kategori yapılandırması
        """
        try:
            return self.config_data.get(category, {}).copy()
            
        except Exception as e:
            self.logger.error(f"Failed to get config for category '{category}': {e}")
            return {}
    
    def validate_config_value(self, key: str, value: Any) -> bool:
        """
        Yapılandırma değerini doğrular.
        
        Args:
            key: Yapılandırma anahtarı
            value: Doğrulanacak değer
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Temel doğrulama kuralları
            validation_rules = {
                "app.name": lambda v: isinstance(v, str) and len(v) > 0,
                "app.version": lambda v: isinstance(v, str) and len(v) > 0,
                "server.host": lambda v: isinstance(v, str) and len(v) > 0,
                "server.port": lambda v: isinstance(v, int) and 1 <= v <= 65535,
                "server.ssl_enabled": lambda v: isinstance(v, bool),
                "database.path": lambda v: isinstance(v, str) and len(v) > 0,
                "security.jwt_secret": lambda v: isinstance(v, str) and len(v) >= 32,
                "security.password_min_length": lambda v: isinstance(v, int) and v >= 6,
                "logging.level": lambda v: v in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "ui.theme": lambda v: v in ["dark", "light", "blue", "custom"],
                "ui.language": lambda v: v in ["tr", "en", "de", "fr"]
            }
            
            if key in validation_rules:
                return validation_rules[key](value)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate config value for key '{key}': {e}")
            return False
    
    def export_config(self, file_path: str) -> bool:
        """
        Yapılandırmayı dosyaya dışa aktarır.
        
        Args:
            file_path: Dışa aktarım dosyası yolu
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            export_path = Path(file_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Config exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export config to {file_path}: {e}")
            return False
    
    def import_config(self, file_path: str, backup: bool = True) -> bool:
        """
        Yapılandırmayı dosyadan içe aktarır.
        
        Args:
            file_path: İçe aktarım dosyası yolu
            backup: Mevcut yapılandırmayı yedekle
            
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            import_path = Path(file_path)
            if not import_path.exists():
                self.logger.error(f"Import file not found: {import_path}")
                return False
            
            # Mevcut yapılandırmayı yedekle
            if backup:
                self._create_backup()
            
            # Yeni yapılandırmayı yükle
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Yapılandırmayı doğrula
            temp_config = self.config_data.copy()
            self.config_data = imported_config
            
            if not self._validate_config():
                self.logger.error("Imported config validation failed")
                self.config_data = temp_config
                return False
            
            # Yapılandırmayı kaydet
            return self.save_config(backup=False)
            
        except Exception as e:
            self.logger.error(f"Failed to import config from {file_path}: {e}")
            return False
    
    def get_config_history(self) -> List[Dict[str, Any]]:
        """
        Yapılandırma geçmişini döndürür.
        
        Returns:
            Yapılandırma geçmişi
        """
        try:
            history = []
            backup_files = list(self.backup_dir.glob("config_backup_*.json"))
            
            for backup_file in sorted(backup_files, reverse=True):
                try:
                    # Dosya adından tarih bilgisini çıkar
                    timestamp_str = backup_file.stem.replace("config_backup_", "")
                    timestamp = datetime.fromisoformat(timestamp_str)
                    
                    # Dosya boyutunu al
                    file_size = backup_file.stat().st_size
                    
                    history.append({
                        "file_path": str(backup_file),
                        "timestamp": timestamp,
                        "size_bytes": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Failed to process backup file {backup_file}: {e}")
                    continue
            
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get config history: {e}")
            return []
    
    def restore_config(self, backup_file: str) -> bool:
        """
        Yapılandırmayı yedekten geri yükler.
        
        Args:
            backup_file: Yedek dosya yolu
            
        Returns:
            True if restored successfully, False otherwise
        """
        try:
            return self.import_config(backup_file, backup=True)
            
        except Exception as e:
            self.logger.error(f"Failed to restore config from {backup_file}: {e}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Varsayılan yapılandırmayı döndürür.
        
        Returns:
            Varsayılan yapılandırma
        """
        return {
            "app": {
                "name": "API Server Manager",
                "version": "1.0.0",
                "description": "API Server Management System",
                "debug": False
            },
            "server": {
                "host": "127.0.0.1",
                "port": 8080,
                "ssl_enabled": False,
                "ssl_cert_path": "",
                "ssl_key_path": "",
                "cors_enabled": True,
                "cors_origins": ["*"],
                "rate_limit_enabled": True,
                "rate_limit_requests": 100,
                "rate_limit_window": 60
            },
            "database": {
                "path": "data/app.db",
                "backup_enabled": True,
                "backup_interval_hours": 24,
                "max_backups": 7
            },
            "security": {
                "jwt_secret": "",
                "jwt_expiry_hours": 24,
                "refresh_token_expiry_days": 7,
                "password_min_length": 8,
                "password_require_uppercase": True,
                "password_require_lowercase": True,
                "password_require_numbers": True,
                "password_require_special": True,
                "max_login_attempts": 5,
                "lockout_duration_minutes": 15
            },
            "logging": {
                "level": "INFO",
                "file_enabled": True,
                "console_enabled": True,
                "max_file_size_mb": 10,
                "backup_count": 5
            },
            "ui": {
                "theme": "dark",
                "language": "tr",
                "auto_refresh_interval": 5,
                "show_splash": True,
                "minimize_to_tray": True
            },
            "monitoring": {
                "enabled": True,
                "metrics_retention_days": 30,
                "alert_enabled": True,
                "alert_email": "",
                "alert_thresholds": {
                    "cpu_percent": 80,
                    "memory_percent": 85,
                    "disk_percent": 90
                }
            }
        }
    
    def _merge_defaults(self):
        """Varsayılan değerleri mevcut yapılandırmaya ekler."""
        try:
            def merge_dict(default: dict, current: dict) -> dict:
                result = default.copy()
                for key, value in current.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = merge_dict(result[key], value)
                    else:
                        result[key] = value
                return result
            
            self.config_data = merge_dict(self.default_config, self.config_data)
            
        except Exception as e:
            self.logger.error(f"Failed to merge defaults: {e}")
    
    def _validate_config(self) -> bool:
        """
        Yapılandırmayı doğrular.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Temel yapı kontrolü
            required_categories = ["app", "server", "database", "security", "logging", "ui"]
            for category in required_categories:
                if category not in self.config_data:
                    self.logger.error(f"Missing required config category: {category}")
                    return False
            
            # Kritik değerleri doğrula
            critical_checks = [
                ("server.port", self.config_data.get("server", {}).get("port")),
                ("server.host", self.config_data.get("server", {}).get("host")),
                ("database.path", self.config_data.get("database", ""))  # Database string olarak geliyor
            ]
            
            for key, value in critical_checks:
                if not self.validate_config_value(key, value):
                    self.logger.error(f"Invalid config value for {key}: {value}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Config validation error: {e}")
            return False
    
    def _create_backup(self):
        """Yapılandırma yedeği oluşturur."""
        try:
            if not self.config_file.exists():
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"config_backup_{timestamp}.json"
            
            shutil.copy2(self.config_file, backup_file)
            self.logger.info(f"Config backup created: {backup_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to create config backup: {e}")
    
    def _create_default_config(self):
        """Varsayılan yapılandırma dosyası oluşturur."""
        try:
            self.config_data = self.default_config.copy()
            self.save_config(backup=False)
            self.logger.info("Default config file created")
            
        except Exception as e:
            self.logger.error(f"Failed to create default config: {e}")


# Global instance
config_service = ConfigService()
