"""
Database module - Veritabanı bağlantısı

Bu modül veritabanı bağlantısını ve temel işlemleri yönetir.
Peewee ORM kullanarak SQLite veritabanı ile çalışır.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.migrate import SqliteMigrator, migrate

from ..core.constants import DATABASE_FILE, DATA_DIR
from ..core.settings import settings
from ..utils.logger import Logger


class DatabaseManager:
    """
    Veritabanı yöneticisi
    
    Veritabanı bağlantısını yönetir ve temel işlemleri sağlar.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        DatabaseManager'ı başlat
        
        Args:
            database_url: Veritabanı URL'i
        """
        self.logger = Logger(__name__)
        
        # Config'den database URL'ini yükle
        from ..core.config_manager import get_config_value
        self.database_url = database_url or get_config_value("database", "sqlite:///data/app.db")
        self.database: Optional[SqliteExtDatabase] = None
        self.migrator: Optional[SqliteMigrator] = None
        
        # Veritabanı dosya yolu
        self.db_path = self._parse_database_url()
        
        # Veritabanı bağlantısını başlat
        self._initialize_database()
    
    def _parse_database_url(self) -> Path:
        """
        Veritabanı URL'ini parse et
        
        Returns:
            Veritabanı dosya yolu
        """
        if self.database_url.startswith("sqlite:///"):
            # SQLite URL'ini parse et
            db_file = self.database_url.replace("sqlite:///", "")
            return Path(db_file)
        else:
            # Varsayılan dosya yolu
            return Path(DATABASE_FILE)
    
    def _initialize_database(self) -> None:
        """Veritabanı bağlantısını başlat"""
        try:
            # Veritabanı klasörünü oluştur
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Veritabanı bağlantısını oluştur
            self.database = SqliteExtDatabase(
                str(self.db_path),
                pragmas={
                    'journal_mode': 'wal',
                    'cache_size': -1024 * 64,  # 64MB cache
                    'foreign_keys': 1,
                    'ignore_check_constraints': 0,
                    'synchronous': 0
                }
            )
            
            # Migrator oluştur
            self.migrator = SqliteMigrator(self.database)
            
            self.logger.info(f"Veritabanı bağlantısı oluşturuldu: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Veritabanı bağlantısı oluşturulamadı: {e}")
            raise
    
    def connect(self) -> None:
        """Veritabanına bağlan"""
        try:
            if not self.database.is_connection_usable():
                self.database.connect()
                self.logger.info("Veritabanına bağlanıldı")
        except Exception as e:
            self.logger.error(f"Veritabanına bağlanılamadı: {e}")
            raise
    
    def disconnect(self) -> None:
        """Veritabanı bağlantısını kapat"""
        try:
            if self.database and not self.database.is_closed():
                self.database.close()
                self.logger.info("Veritabanı bağlantısı kapatıldı")
        except Exception as e:
            self.logger.error(f"Veritabanı bağlantısı kapatılamadı: {e}")
    
    def create_tables(self, models: List[Model]) -> None:
        """
        Tabloları oluştur
        
        Args:
            models: Oluşturulacak model listesi
        """
        try:
            self.database.create_tables(models, safe=True)
            self.logger.info(f"{len(models)} tablo oluşturuldu")
        except Exception as e:
            self.logger.error(f"Tablolar oluşturulamadı: {e}")
            raise
    
    def drop_tables(self, models: List[Model]) -> None:
        """
        Tabloları sil
        
        Args:
            models: Silinecek model listesi
        """
        try:
            self.database.drop_tables(models, safe=True)
            self.logger.info(f"{len(models)} tablo silindi")
        except Exception as e:
            self.logger.error(f"Tablolar silinemedi: {e}")
            raise
    
    def get_database(self) -> SqliteExtDatabase:
        """
        Veritabanı instance'ını al
        
        Returns:
            Veritabanı instance'ı
        """
        return self.database
    
    def get_migrator(self) -> SqliteMigrator:
        """
        Migrator instance'ını al
        
        Returns:
            Migrator instance'ı
        """
        return self.migrator
    
    @contextmanager
    def transaction(self):
        """
        Transaction context manager
        
        Yields:
            Transaction instance
        """
        with self.database.atomic() as transaction:
            try:
                yield transaction
            except Exception as e:
                self.logger.error(f"Transaction hatası: {e}")
                raise
    
    def execute_sql(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        SQL sorgusu çalıştır
        
        Args:
            sql: SQL sorgusu
            params: Sorgu parametreleri
            
        Returns:
            Sorgu sonuçları
        """
        try:
            cursor = self.database.execute_sql(sql, params)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        except Exception as e:
            self.logger.error(f"SQL sorgusu çalıştırılamadı: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Tablo bilgilerini al
        
        Args:
            table_name: Tablo adı
            
        Returns:
            Tablo bilgileri
        """
        try:
            sql = f"PRAGMA table_info({table_name})"
            return self.execute_sql(sql)
        except Exception as e:
            self.logger.error(f"Tablo bilgileri alınamadı: {e}")
            return []
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Veritabanı bilgilerini al
        
        Returns:
            Veritabanı bilgileri
        """
        try:
            # Veritabanı dosya boyutu
            file_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            # Tablo sayısı
            tables = self.execute_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            
            # Toplam kayıt sayısı
            total_records = 0
            for table in tables:
                table_name = table['name']
                count_result = self.execute_sql(f"SELECT COUNT(*) as count FROM {table_name}")
                if count_result:
                    total_records += count_result[0]['count']
            
            return {
                "file_path": str(self.db_path),
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "table_count": len(tables),
                "total_records": total_records,
                "tables": [table['name'] for table in tables],
                "is_connected": not self.database.is_closed()
            }
            
        except Exception as e:
            self.logger.error(f"Veritabanı bilgileri alınamadı: {e}")
            return {
                "file_path": str(self.db_path),
                "file_size": 0,
                "file_size_mb": 0,
                "table_count": 0,
                "total_records": 0,
                "tables": [],
                "is_connected": False,
                "error": str(e)
            }
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Veritabanını yedekle
        
        Args:
            backup_path: Yedek dosya yolu
            
        Returns:
            Yedekleme başarılı mı
        """
        try:
            import shutil
            
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Veritabanı dosyasını kopyala
            shutil.copy2(self.db_path, backup_file)
            
            self.logger.info(f"Veritabanı yedeklendi: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Veritabanı yedeklenemedi: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """
        Veritabanını geri yükle
        
        Args:
            backup_path: Yedek dosya yolu
            
        Returns:
            Geri yükleme başarılı mı
        """
        try:
            import shutil
            
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                self.logger.error(f"Yedek dosyası bulunamadı: {backup_path}")
                return False
            
            # Mevcut veritabanını yedekle
            current_backup = self.db_path.with_suffix('.backup')
            if self.db_path.exists():
                shutil.copy2(self.db_path, current_backup)
            
            # Yedek dosyasını geri yükle
            shutil.copy2(backup_file, self.db_path)
            
            # Veritabanı bağlantısını yenile
            self.disconnect()
            self._initialize_database()
            self.connect()
            
            self.logger.info(f"Veritabanı geri yüklendi: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Veritabanı geri yüklenemedi: {e}")
            return False
    
    def vacuum_database(self) -> bool:
        """
        Veritabanını optimize et (VACUUM)
        
        Returns:
            Optimizasyon başarılı mı
        """
        try:
            self.database.execute_sql("VACUUM")
            self.logger.info("Veritabanı optimize edildi")
            return True
            
        except Exception as e:
            self.logger.error(f"Veritabanı optimize edilemedi: {e}")
            return False
    
    def analyze_database(self) -> bool:
        """
        Veritabanını analiz et (ANALYZE)
        
        Returns:
            Analiz başarılı mı
        """
        try:
            self.database.execute_sql("ANALYZE")
            self.logger.info("Veritabanı analiz edildi")
            return True
            
        except Exception as e:
            self.logger.error(f"Veritabanı analiz edilemedi: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Bağlantı bilgilerini al
        
        Returns:
            Bağlantı bilgileri
        """
        return {
            "database_url": self.database_url,
            "db_path": str(self.db_path),
            "is_connected": not self.database.is_closed() if self.database else False,
            "connection_usable": self.database.is_connection_usable() if self.database else False
        }


# Global database manager instance
db_manager = DatabaseManager()


def get_database() -> SqliteExtDatabase:
    """
    Veritabanı instance'ını al
    
    Returns:
        Veritabanı instance'ı
    """
    return db_manager.get_database()


def get_migrator() -> SqliteMigrator:
    """
    Migrator instance'ını al
    
    Returns:
        Migrator instance'ı
    """
    return db_manager.get_migrator()


def init_database() -> None:
    """Veritabanını başlat"""
    db_manager.connect()


def close_database() -> None:
    """Veritabanı bağlantısını kapat"""
    db_manager.disconnect()


# Export database instance for direct access
database = db_manager.get_database()
