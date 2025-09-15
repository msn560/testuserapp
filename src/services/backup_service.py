"""
Backup Service module - Yedekleme yönetimi

Bu modül veritabanı ve yapılandırma dosyalarının yedeklenmesini yönetir.
Otomatik yedekleme, geri yükleme ve yedek yönetimi.
"""

import os
import shutil
import zipfile
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import threading
import asyncio

from ..db.models import Backup
from ..core.constants import LogLevel
from ..utils.logger import logger


class BackupService:
    """
    Yedekleme yönetimi servisi.
    
    Bu sınıf veritabanı ve yapılandırma dosyalarının yedeklenmesini yönetir.
    """
    
    def __init__(self, backup_dir: str = "data/backup"):
        """
        BackupService'i başlatır.
        
        Args:
            backup_dir: Yedek dizini
        """
        self.logger = logger
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Yedekleme ayarlarını config'den yükle
        from ..core.config_manager import get_config_value
        self.settings = {
            "auto_backup_enabled": get_config_value("backup.enabled", True),
            "backup_interval_hours": get_config_value("backup.interval_hours", 24),
            "max_backups": get_config_value("backup.retention_days", 30),
            "compress_backups": get_config_value("backup.compress", True),
            "include_logs": get_config_value("backup.include_logs", True),
            "include_config": get_config_value("backup.include_config", True)
        }
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Yedekleme istatistikleri
        self.stats = {
            "total_backups": 0,
            "successful_backups": 0,
            "failed_backups": 0,
            "total_size_bytes": 0,
            "last_backup_time": None
        }
    
    def create_backup(self, backup_type: str = "full", description: str = None, 
                     created_by: int = None) -> Optional[Backup]:
        """
        Yedek oluşturur.
        
        Args:
            backup_type: Yedek türü (full, database, config, logs)
            description: Yedek açıklaması
            created_by: Oluşturan kullanıcı ID'si
            
        Returns:
            Oluşturulan yedek kaydı
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{backup_type}_backup_{timestamp}"
            
            if self.settings["compress_backups"]:
                backup_filename += ".zip"
            
            backup_path = self.backup_dir / backup_filename
            
            # Yedek türüne göre oluştur
            if backup_type == "full":
                success = self._create_full_backup(backup_path, timestamp)
            elif backup_type == "database":
                success = self._create_database_backup(backup_path, timestamp)
            elif backup_type == "config":
                success = self._create_config_backup(backup_path, timestamp)
            elif backup_type == "logs":
                success = self._create_logs_backup(backup_path, timestamp)
            else:
                self.logger.error(f"Unknown backup type: {backup_type}")
                return None
            
            if not success:
                return None
            
            # Dosya boyutunu hesapla
            file_size = backup_path.stat().st_size
            
            # Veritabanına kaydet
            backup_record = Backup.create(
                type=backup_type,
                filename=backup_filename,
                file_path=str(backup_path),
                size_bytes=file_size,
                created_at=datetime.now(),
                created_by=created_by,
                description=description or f"{backup_type.title()} backup created automatically"
            )
            
            # İstatistikleri güncelle
            with self.lock:
                self.stats["total_backups"] += 1
                self.stats["successful_backups"] += 1
                self.stats["total_size_bytes"] += file_size
                self.stats["last_backup_time"] = datetime.now().isoformat()
            
            self.logger.info(f"Backup created: {backup_filename} ({file_size} bytes)")
            return backup_record
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            with self.lock:
                self.stats["failed_backups"] += 1
            return None
    
    def restore_backup(self, backup_id: int, restore_path: str = None) -> bool:
        """
        Yedekten geri yükler.
        
        Args:
            backup_id: Yedek ID'si
            restore_path: Geri yükleme yolu (None ise orijinal konuma)
            
        Returns:
            True if restored successfully, False otherwise
        """
        try:
            # Yedek kaydını al
            backup = Backup.get_by_id(backup_id)
            if not backup:
                self.logger.error(f"Backup not found: {backup_id}")
                return False
            
            backup_path = Path(backup.file_path)
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Geri yükleme işlemini gerçekleştir
            if backup.type == "database":
                success = self._restore_database_backup(backup_path, restore_path)
            elif backup.type == "config":
                success = self._restore_config_backup(backup_path, restore_path)
            elif backup.type == "full":
                success = self._restore_full_backup(backup_path, restore_path)
            else:
                self.logger.error(f"Unknown restore type: {backup.type}")
                return False
            
            if success:
                self.logger.info(f"Backup restored: {backup.filename}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to restore backup {backup_id}: {e}")
            return False
    
    def list_backups(self, backup_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Yedekleri listeler.
        
        Args:
            backup_type: Yedek türü filtresi
            limit: Maksimum yedek sayısı
            
        Returns:
            Yedek listesi
        """
        try:
            query = Backup.select().order_by(Backup.created_at.desc())
            
            if backup_type:
                query = query.where(Backup.type == backup_type)
            
            if limit:
                query = query.limit(limit)
            
            backups = []
            for backup in query:
                backup_dict = {
                    "id": backup.id,
                    "type": backup.type,
                    "filename": backup.filename,
                    "file_path": backup.file_path,
                    "size_bytes": backup.size_bytes,
                    "size_mb": round(backup.size_bytes / (1024 * 1024), 2),
                    "created_at": backup.created_at.isoformat(),
                    "created_by": backup.created_by,
                    "description": backup.description,
                    "exists": Path(backup.file_path).exists()
                }
                backups.append(backup_dict)
            
            return backups
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
            return []
    
    def delete_backup(self, backup_id: int) -> bool:
        """
        Yedek siler.
        
        Args:
            backup_id: Silinecek yedek ID'si
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Yedek kaydını al
            backup = Backup.get_by_id(backup_id)
            if not backup:
                self.logger.error(f"Backup not found: {backup_id}")
                return False
            
            # Dosyayı sil
            backup_path = Path(backup.file_path)
            if backup_path.exists():
                backup_path.unlink()
            
            # Veritabanından sil
            backup.delete_instance()
            
            # İstatistikleri güncelle
            with self.lock:
                self.stats["total_size_bytes"] -= backup.size_bytes
            
            self.logger.info(f"Backup deleted: {backup.filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """
        Eski yedekleri temizler.
        
        Returns:
            Temizlenen yedek sayısı
        """
        try:
            max_backups = self.settings["max_backups"]
            
            # Tüm yedekleri al (sıralı)
            all_backups = list(Backup.select().order_by(Backup.created_at.desc()))
            
            # Fazla yedekleri sil
            deleted_count = 0
            for backup in all_backups[max_backups:]:
                if self.delete_backup(backup.id):
                    deleted_count += 1
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old backups")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
            return 0
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """
        Yedekleme istatistiklerini döndürür.
        
        Returns:
            Yedekleme istatistikleri
        """
        try:
            with self.lock:
                total_backups = Backup.select().count()
                total_size = sum(backup.size_bytes for backup in Backup.select())
                
                # Yedek türlerine göre dağılım
                type_distribution = {}
                for backup in Backup.select():
                    backup_type = backup.type
                    if backup_type not in type_distribution:
                        type_distribution[backup_type] = 0
                    type_distribution[backup_type] += 1
                
                return {
                    "total_backups": total_backups,
                    "successful_backups": self.stats["successful_backups"],
                    "failed_backups": self.stats["failed_backups"],
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "type_distribution": type_distribution,
                    "last_backup_time": self.stats["last_backup_time"],
                    "settings": self.settings.copy()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get backup statistics: {e}")
            return {}
    
    def _create_full_backup(self, backup_path: Path, timestamp: str) -> bool:
        """
        Tam yedek oluşturur.
        
        Args:
            backup_path: Yedek dosya yolu
            timestamp: Zaman damgası
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            if self.settings["compress_backups"]:
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Veritabanı dosyası
                    db_path = Path("data/app.db")
                    if db_path.exists():
                        zipf.write(db_path, "app.db")
                    
                    # Yapılandırma dosyası
                    config_path = Path("data/config.json")
                    if config_path.exists():
                        zipf.write(config_path, "config.json")
                    
                    # Log dosyaları
                    if self.settings["include_logs"]:
                        logs_dir = Path("data/logs")
                        if logs_dir.exists():
                            for log_file in logs_dir.glob("*.log"):
                                zipf.write(log_file, f"logs/{log_file.name}")
                    
                    # Yedek meta bilgisi
                    metadata = {
                        "backup_type": "full",
                        "timestamp": timestamp,
                        "created_at": datetime.now().isoformat(),
                        "settings": self.settings
                    }
                    zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
            else:
                # Yedek dizini oluştur
                backup_dir = backup_path.with_suffix('')
                backup_dir.mkdir(exist_ok=True)
                
                # Dosyaları kopyala
                db_path = Path("data/app.db")
                if db_path.exists():
                    shutil.copy2(db_path, backup_dir / "app.db")
                
                config_path = Path("data/config.json")
                if config_path.exists():
                    shutil.copy2(config_path, backup_dir / "config.json")
                
                # Meta bilgiyi kaydet
                metadata = {
                    "backup_type": "full",
                    "timestamp": timestamp,
                    "created_at": datetime.now().isoformat(),
                    "settings": self.settings
                }
                with open(backup_dir / "backup_metadata.json", 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create full backup: {e}")
            return False
    
    def _create_database_backup(self, backup_path: Path, timestamp: str) -> bool:
        """
        Veritabanı yedeği oluşturur.
        
        Args:
            backup_path: Yedek dosya yolu
            timestamp: Zaman damgası
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            db_path = Path("data/app.db")
            if not db_path.exists():
                self.logger.error("Database file not found")
                return False
            
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(db_path, "app.db")
                    
                    metadata = {
                        "backup_type": "database",
                        "timestamp": timestamp,
                        "created_at": datetime.now().isoformat()
                    }
                    zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
            else:
                shutil.copy2(db_path, backup_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create database backup: {e}")
            return False
    
    def _create_config_backup(self, backup_path: Path, timestamp: str) -> bool:
        """
        Yapılandırma yedeği oluşturur.
        
        Args:
            backup_path: Yedek dosya yolu
            timestamp: Zaman damgası
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            config_path = Path("data/config.json")
            if not config_path.exists():
                self.logger.error("Config file not found")
                return False
            
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(config_path, "config.json")
                    
                    metadata = {
                        "backup_type": "config",
                        "timestamp": timestamp,
                        "created_at": datetime.now().isoformat()
                    }
                    zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
            else:
                shutil.copy2(config_path, backup_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create config backup: {e}")
            return False
    
    def _create_logs_backup(self, backup_path: Path, timestamp: str) -> bool:
        """
        Log yedeği oluşturur.
        
        Args:
            backup_path: Yedek dosya yolu
            timestamp: Zaman damgası
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            logs_dir = Path("data/logs")
            if not logs_dir.exists():
                self.logger.error("Logs directory not found")
                return False
            
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for log_file in logs_dir.glob("*.log"):
                        zipf.write(log_file, f"logs/{log_file.name}")
                    
                    metadata = {
                        "backup_type": "logs",
                        "timestamp": timestamp,
                        "created_at": datetime.now().isoformat()
                    }
                    zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
            else:
                # Log dizinini kopyala
                backup_logs_dir = backup_path.with_suffix('')
                shutil.copytree(logs_dir, backup_logs_dir)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create logs backup: {e}")
            return False
    
    def _restore_database_backup(self, backup_path: Path, restore_path: str = None) -> bool:
        """
        Veritabanı yedeğini geri yükler.
        
        Args:
            backup_path: Yedek dosya yolu
            restore_path: Geri yükleme yolu
            
        Returns:
            True if restored successfully, False otherwise
        """
        try:
            target_path = Path(restore_path) if restore_path else Path("data/app.db")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extract("app.db", target_path.parent)
                    extracted_file = target_path.parent / "app.db"
                    if extracted_file.exists():
                        extracted_file.rename(target_path)
            else:
                shutil.copy2(backup_path, target_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore database backup: {e}")
            return False
    
    def _restore_config_backup(self, backup_path: Path, restore_path: str = None) -> bool:
        """
        Yapılandırma yedeğini geri yükler.
        
        Args:
            backup_path: Yedek dosya yolu
            restore_path: Geri yükleme yolu
            
        Returns:
            True if restored successfully, False otherwise
        """
        try:
            target_path = Path(restore_path) if restore_path else Path("data/config.json")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extract("config.json", target_path.parent)
                    extracted_file = target_path.parent / "config.json"
                    if extracted_file.exists():
                        extracted_file.rename(target_path)
            else:
                shutil.copy2(backup_path, target_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore config backup: {e}")
            return False
    
    def _restore_full_backup(self, backup_path: Path, restore_path: str = None) -> bool:
        """
        Tam yedeği geri yükler.
        
        Args:
            backup_path: Yedek dosya yolu
            restore_path: Geri yükleme yolu
            
        Returns:
            True if restored successfully, False otherwise
        """
        try:
            target_dir = Path(restore_path) if restore_path else Path("data")
            target_dir.mkdir(parents=True, exist_ok=True)
            
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(target_dir)
            else:
                # Dizin yedeği
                source_dir = backup_path.with_suffix('')
                if source_dir.exists():
                    for item in source_dir.iterdir():
                        target_item = target_dir / item.name
                        if item.is_file():
                            shutil.copy2(item, target_item)
                        elif item.is_dir():
                            shutil.copytree(item, target_item, dirs_exist_ok=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore full backup: {e}")
            return False


# Global instance
backup_service = BackupService()
