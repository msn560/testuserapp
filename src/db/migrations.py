"""
Migrations module - Database migrations

Bu modül veritabanı migration işlemlerini yönetir.
Tabloların oluşturulması, güncellenmesi ve veri migrasyonu işlemlerini sağlar.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from peewee import *
from playhouse.migrate import *

from .database import db_manager, get_migrator
from .models import ALL_MODELS, SYSTEM_ROLES, DEFAULT_PERMISSIONS
from ..core.constants import *
from ..core.settings import settings
from ..utils.logger import Logger


class MigrationManager:
    """
    Migration yöneticisi
    
    Veritabanı migration işlemlerini yönetir.
    """
    
    def __init__(self):
        """MigrationManager'ı başlat"""
        self.logger = Logger(__name__)
        self.migrator = get_migrator()
        self.migrations_dir = Path("data/migrations")
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
    
    def create_tables(self) -> bool:
        """
        Tüm tabloları oluştur
        
        Returns:
            Oluşturma başarılı mı
        """
        try:
            self.logger.info("Tablolar oluşturuluyor...")
            
            # Veritabanına bağlan
            db_manager.connect()
            
            # Tabloları oluştur
            db_manager.create_tables(ALL_MODELS)
            
            # Varsayılan verileri ekle
            self._create_default_data()
            
            self.logger.info("Tablolar başarıyla oluşturuldu")
            return True
            
        except Exception as e:
            self.logger.error(f"Tablolar oluşturulamadı: {e}")
            return False
    
    def drop_tables(self) -> bool:
        """
        Tüm tabloları sil
        
        Returns:
            Silme başarılı mı
        """
        try:
            self.logger.info("Tablolar siliniyor...")
            
            # Veritabanına bağlan
            db_manager.connect()
            
            # Tabloları sil (ters sırada)
            db_manager.drop_tables(reversed(ALL_MODELS))
            
            self.logger.info("Tablolar başarıyla silindi")
            return True
            
        except Exception as e:
            self.logger.error(f"Tablolar silinemedi: {e}")
            return False
    
    def reset_database(self) -> bool:
        """
        Veritabanını sıfırla
        
        Returns:
            Sıfırlama başarılı mı
        """
        try:
            self.logger.info("Veritabanı sıfırlanıyor...")
            
            # Tabloları sil
            if not self.drop_tables():
                return False
            
            # Tabloları oluştur
            if not self.create_tables():
                return False
            
            self.logger.info("Veritabanı başarıyla sıfırlandı")
            return True
            
        except Exception as e:
            self.logger.error(f"Veritabanı sıfırlanamadı: {e}")
            return False
    
    def _create_default_data(self) -> None:
        """Varsayılan verileri oluştur"""
        try:
            self.logger.info("Varsayılan veriler oluşturuluyor...")
            
            # Rolleri oluştur
            self._create_default_roles()
            
            # İzinleri oluştur
            self._create_default_permissions()
            
            # Varsayılan kullanıcıyı oluştur
            self._create_default_user()
            
            # Sistem ayarlarını oluştur
            self._create_system_settings()
            
            # Varsayılan server'ı oluştur
            self._create_default_server()
            
            # API endpoint'lerini oluştur
            self._create_default_api_endpoints()
            
            self.logger.info("Varsayılan veriler oluşturuldu")
            
        except Exception as e:
            self.logger.error(f"Varsayılan veriler oluşturulamadı: {e}")
            raise
    
    def _create_default_roles(self) -> None:
        """Varsayılan rolleri oluştur"""
        from .models import Role
        
        for role_name, role_data in SYSTEM_ROLES.items():
            if not Role.select().where(Role.name == role_name).exists():
                Role.create(
                    name=role_name,
                    description=role_data['description'],
                    permissions=role_data['permissions'],
                    color=role_data['color'],
                    icon=role_data['icon'],
                    is_system_role=role_data.get('is_system_role', True)
                )
                self.logger.info(f"Rol oluşturuldu: {role_name}")
    
    def _create_default_permissions(self) -> None:
        """Varsayılan izinleri oluştur"""
        from .models import Permission
        
        for permission in DEFAULT_PERMISSIONS:
            if not Permission.select().where(Permission.name == permission).exists():
                # İzni parse et (resource.action formatında)
                parts = permission.split('.')
                if len(parts) >= 2:
                    resource = parts[0]
                    action = '.'.join(parts[1:])
                    
                    Permission.create(
                        name=permission,
                        description=f"{resource} kaynağı için {action} işlemi",
                        resource=resource,
                        action=action
                    )
                    self.logger.info(f"İzin oluşturuldu: {permission}")
    
    def _create_default_user(self) -> None:
        """Varsayılan kullanıcıyı oluştur"""
        from .models import User, UserRole, Role
        import bcrypt
        
        # Admin kullanıcısı var mı kontrol et
        if User.select().where(User.username == 'admin').exists():
            return
        
        # Parolayı hashle
        password = 'admin123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Admin kullanıcısını oluştur
        admin_user = User.create(
            username='admin',
            email='admin@localhost',
            password_hash=password_hash,
            full_name='System Administrator',
            is_active=True,
            is_verified=True,
            is_superuser=True
        )
        
        # Superadmin rolünü ata
        superadmin_role = Role.get(Role.name == 'superadmin')
        UserRole.create(
            user=admin_user,
            role=superadmin_role,
            assigned_at=datetime.now(),
            is_active=True
        )
        
        self.logger.info("Varsayılan admin kullanıcısı oluşturuldu (admin/admin123)")
    
    def _create_system_settings(self) -> None:
        """Sistem ayarlarını oluştur"""
        from .models import SystemSettings
        
        default_settings = {
            'app_name': {
                'value': APP_NAME,
                'default_value': APP_NAME,
                'data_type': 'string',
                'description': 'Uygulama adı',
                'is_readonly': True
            },
            'app_version': {
                'value': APP_VERSION,
                'default_value': APP_VERSION,
                'data_type': 'string',
                'description': 'Uygulama sürümü',
                'is_readonly': True
            },
            'max_login_attempts': {
                'value': str(DEFAULT_MAX_LOGIN_ATTEMPTS),
                'default_value': str(DEFAULT_MAX_LOGIN_ATTEMPTS),
                'data_type': 'int',
                'description': 'Maksimum giriş denemesi sayısı',
                'is_readonly': False
            },
            'session_timeout_minutes': {
                'value': str(DEFAULT_SESSION_TIMEOUT_MINUTES),
                'default_value': str(DEFAULT_SESSION_TIMEOUT_MINUTES),
                'data_type': 'int',
                'description': 'Oturum zaman aşımı (dakika)',
                'is_readonly': False
            },
            'backup_enabled': {
                'value': 'true',
                'default_value': 'true',
                'data_type': 'bool',
                'description': 'Otomatik yedekleme etkin',
                'is_readonly': False
            },
            'monitoring_enabled': {
                'value': 'true',
                'default_value': 'true',
                'data_type': 'bool',
                'description': 'Sistem izleme etkin',
                'is_readonly': False
            }
        }
        
        for key, setting_data in default_settings.items():
            if not SystemSettings.select().where(SystemSettings.key == key).exists():
                SystemSettings.create(
                    key=key,
                    value=setting_data['value'],
                    default_value=setting_data['default_value'],
                    data_type=setting_data['data_type'],
                    description=setting_data['description'],
                    is_readonly=setting_data['is_readonly']
                )
                self.logger.info(f"Sistem ayarı oluşturuldu: {key}")
    
    def _create_default_server(self) -> None:
        """Varsayılan server'ı oluştur"""
        from .models import Server
        
        if not Server.select().where(Server.name == 'default').exists():
            Server.create(
                name='default',
                host=settings.server.host,
                port=settings.server.port,
                protocol='https' if settings.server.ssl else 'http',
                status='stopped',
                config={
                    'auto_start': settings.server.auto_start,
                    'ssl_enabled': settings.server.ssl,
                    'cors_enabled': True
                }
            )
            self.logger.info("Varsayılan server oluşturuldu")
    
    def _create_default_api_endpoints(self) -> None:
        """Varsayılan API endpoint'lerini oluştur"""
        from .models import ApiEndpoint
        
        default_endpoints = [
            {
                'method': 'POST',
                'path': '/api/v1/auth/login',
                'description': 'Kullanıcı girişi',
                'required_roles': [],
                'rate_limit': 10
            },
            {
                'method': 'POST',
                'path': '/api/v1/auth/logout',
                'description': 'Kullanıcı çıkışı',
                'required_roles': ['authenticated'],
                'rate_limit': 100
            },
            {
                'method': 'GET',
                'path': '/api/v1/users',
                'description': 'Kullanıcı listesi',
                'required_roles': ['admin', 'superadmin'],
                'rate_limit': 100
            },
            {
                'method': 'POST',
                'path': '/api/v1/users',
                'description': 'Yeni kullanıcı oluştur',
                'required_roles': ['admin', 'superadmin'],
                'rate_limit': 50
            },
            {
                'method': 'GET',
                'path': '/api/v1/server/status',
                'description': 'Server durumu',
                'required_roles': ['operator', 'admin', 'superadmin'],
                'rate_limit': 200
            },
            {
                'method': 'POST',
                'path': '/api/v1/server/start',
                'description': 'Server başlat',
                'required_roles': ['operator', 'admin', 'superadmin'],
                'rate_limit': 10
            },
            {
                'method': 'POST',
                'path': '/api/v1/server/stop',
                'description': 'Server durdur',
                'required_roles': ['operator', 'admin', 'superadmin'],
                'rate_limit': 10
            },
            {
                'method': 'GET',
                'path': '/api/v1/monitor/system',
                'description': 'Sistem metrikleri',
                'required_roles': ['viewer', 'operator', 'admin', 'superadmin'],
                'rate_limit': 100
            }
        ]
        
        for endpoint_data in default_endpoints:
            if not ApiEndpoint.select().where(
                ApiEndpoint.method == endpoint_data['method'],
                ApiEndpoint.path == endpoint_data['path']
            ).exists():
                ApiEndpoint.create(**endpoint_data)
                self.logger.info(f"API endpoint oluşturuldu: {endpoint_data['method']} {endpoint_data['path']}")
    
    def check_database_integrity(self) -> Dict[str, Any]:
        """
        Veritabanı bütünlüğünü kontrol et
        
        Returns:
            Kontrol sonuçları
        """
        try:
            results = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'table_counts': {},
                'missing_tables': [],
                'missing_data': []
            }
            
            # Tabloları kontrol et
            for model in ALL_MODELS:
                table_name = model._meta.table_name
                try:
                    count = model.select().count()
                    results['table_counts'][table_name] = count
                except Exception as e:
                    results['missing_tables'].append(table_name)
                    results['errors'].append(f"Tablo eksik: {table_name} - {e}")
                    results['is_valid'] = False
            
            # Gerekli verileri kontrol et
            from .models import User, Role, SystemSettings
            
            # Admin kullanıcısı var mı?
            if not User.select().where(User.username == 'admin').exists():
                results['missing_data'].append('Admin kullanıcısı eksik')
                results['warnings'].append('Varsayılan admin kullanıcısı bulunamadı')
            
            # Roller var mı?
            role_count = Role.select().count()
            if role_count == 0:
                results['missing_data'].append('Sistem rolleri eksik')
                results['errors'].append('Hiç rol bulunamadı')
                results['is_valid'] = False
            
            # Sistem ayarları var mı?
            settings_count = SystemSettings.select().count()
            if settings_count == 0:
                results['missing_data'].append('Sistem ayarları eksik')
                results['warnings'].append('Sistem ayarları bulunamadı')
            
            return results
            
        except Exception as e:
            self.logger.error(f"Veritabanı bütünlük kontrolü yapılamadı: {e}")
            return {
                'is_valid': False,
                'errors': [str(e)],
                'warnings': [],
                'table_counts': {},
                'missing_tables': [],
                'missing_data': []
            }
    
    def backup_before_migration(self, backup_name: str = None) -> str:
        """
        Migration öncesi yedek oluştur
        
        Args:
            backup_name: Yedek dosya adı
            
        Returns:
            Yedek dosya yolu
        """
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"pre_migration_backup_{timestamp}.db"
            
            backup_path = f"data/backup/{backup_name}"
            
            if db_manager.backup_database(backup_path):
                self.logger.info(f"Migration öncesi yedek oluşturuldu: {backup_path}")
                return backup_path
            else:
                raise Exception("Yedek oluşturulamadı")
                
        except Exception as e:
            self.logger.error(f"Migration öncesi yedek oluşturulamadı: {e}")
            raise
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Migration durumunu al
        
        Returns:
            Migration durumu
        """
        try:
            # Veritabanı bilgilerini al
            db_info = db_manager.get_database_info()
            
            # Bütünlük kontrolü yap
            integrity_check = self.check_database_integrity()
            
            return {
                'database_info': db_info,
                'integrity_check': integrity_check,
                'migration_needed': not integrity_check['is_valid'],
                'last_migration': self._get_last_migration_time()
            }
            
        except Exception as e:
            self.logger.error(f"Migration durumu alınamadı: {e}")
            return {
                'database_info': {},
                'integrity_check': {'is_valid': False, 'errors': [str(e)]},
                'migration_needed': True,
                'last_migration': None
            }
    
    def _get_last_migration_time(self) -> Optional[str]:
        """Son migration zamanını al"""
        try:
            # Veritabanı dosyasının son değiştirilme zamanını al
            db_path = Path(db_manager.db_path)
            if db_path.exists():
                return datetime.fromtimestamp(db_path.stat().st_mtime).isoformat()
            return None
        except Exception:
            return None


# Global migration manager instance
migration_manager = MigrationManager()


def init_database() -> bool:
    """
    Veritabanını başlat
    
    Returns:
        Başlatma başarılı mı
    """
    try:
        # Migration durumunu kontrol et
        status = migration_manager.get_migration_status()
        
        if status['migration_needed']:
            logger.info("Veritabanı migration'ı gerekli")
            
            # Yedek oluştur
            backup_path = migration_manager.backup_before_migration()
            logger.info(f"Yedek oluşturuldu: {backup_path}")
            
            # Tabloları oluştur
            if migration_manager.create_tables():
                logger.info("Veritabanı başarıyla başlatıldı")
                return True
            else:
                logger.error("Veritabanı başlatılamadı")
                return False
        else:
            logger.info("Veritabanı zaten güncel")
            return True
            
    except Exception as e:
        logger.error(f"Veritabanı başlatılamadı: {e}")
        return False


def reset_database() -> bool:
    """
    Veritabanını sıfırla
    
    Returns:
        Sıfırlama başarılı mı
    """
    return migration_manager.reset_database()


def check_database() -> Dict[str, Any]:
    """
    Veritabanı durumunu kontrol et
    
    Returns:
        Veritabanı durumu
    """
    return migration_manager.get_migration_status()
