"""
Models module - Peewee modelleri

Bu modül veritabanı modellerini içerir.
Tüm tablolar ve ilişkiler burada tanımlanır.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

from peewee import *
from playhouse.sqlite_ext import *

from .database import get_database
from ..core.constants import *
from ..utils.logger import Logger


# Veritabanı instance'ı
database = get_database()
logger = Logger(__name__)


class BaseModel(Model):
    """Temel model sınıfı"""
    
    class Meta:
        database = database
    
    def to_dict(self) -> Dict[str, Any]:
        """Model'i sözlüğe dönüştür"""
        data = {}
        for field_name in self._meta.fields:
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, (list, dict)):
                value = json.dumps(value, ensure_ascii=False)
            data[field_name] = value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Sözlükten model oluştur"""
        # JSON string'leri parse et
        for field_name, field in cls._meta.fields.items():
            if field_name in data and isinstance(data[field_name], str):
                if isinstance(field, (JSONField, TextField)):
                    try:
                        data[field_name] = json.loads(data[field_name])
                    except (json.JSONDecodeError, TypeError):
                        pass
        
        return cls(**data)


# ============================================================================
# KULLANICI YÖNETİMİ MODELLERİ
# ============================================================================

class User(BaseModel):
    """Kullanıcı modeli"""
    
    id = AutoField(primary_key=True)
    username = CharField(max_length=50, unique=True, index=True)
    email = CharField(max_length=100, unique=True, index=True)
    password_hash = CharField(max_length=255)
    full_name = CharField(max_length=100)
    avatar_path = CharField(max_length=255, null=True)
    
    # Durum alanları
    is_active = BooleanField(default=True, index=True)
    is_verified = BooleanField(default=False)
    is_superuser = BooleanField(default=False)
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now, index=True)
    updated_at = DateTimeField(default=datetime.now)
    last_login = DateTimeField(null=True, index=True)
    
    # Ekstra alanlar
    preferences = JSONField(default=dict)
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'users'
        indexes = (
            (('username', 'is_active'), False),
            (('email', 'is_active'), False),
        )
    
    def __str__(self):
        return f"User({self.username})"
    
    def is_online(self) -> bool:
        """Kullanıcı online mı?"""
        if not self.last_login:
            return False
        
        # Son 5 dakika içinde giriş yapmışsa online sayılır
        return datetime.now() - self.last_login < timedelta(minutes=5)
    
    def get_roles(self) -> List['Role']:
        """Kullanıcının rollerini al"""
        return [ur.role for ur in self.user_roles.select().join(Role)]
    
    def has_permission(self, permission: str) -> bool:
        """Kullanıcının belirli bir izni var mı?"""
        if self.is_superuser:
            return True
        
        for user_role in self.user_roles.select().join(Role):
            if user_role.role.has_permission(permission):
                return True
        
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Kullanıcının belirli bir rolü var mı?"""
        return any(ur.role.name == role_name for ur in self.user_roles.select().join(Role))


class Role(BaseModel):
    """Rol modeli"""
    
    id = AutoField(primary_key=True)
    name = CharField(max_length=50, unique=True, index=True)
    description = TextField(null=True)
    permissions = JSONField(default=list)  # İzin listesi
    color = CharField(max_length=7, default="#0066cc")  # Hex renk kodu
    icon = CharField(max_length=50, default="user")
    
    # Sistem rolü mü?
    is_system_role = BooleanField(default=False)
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    # Ekstra alanlar
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'roles'
        indexes = (
            (('name', 'is_system_role'), False),
        )
    
    def __str__(self):
        return f"Role({self.name})"
    
    def has_permission(self, permission: str) -> bool:
        """Rolün belirli bir izni var mı?"""
        if "*" in self.permissions:
            return True
        
        return permission in self.permissions
    
    def add_permission(self, permission: str) -> None:
        """Role izin ekle"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.save()
    
    def remove_permission(self, permission: str) -> None:
        """Rolden izin kaldır"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.save()


class Permission(BaseModel):
    """İzin modeli"""
    
    id = AutoField(primary_key=True)
    name = CharField(max_length=100, unique=True, index=True)
    description = TextField(null=True)
    resource = CharField(max_length=50, index=True)  # Hangi kaynak
    action = CharField(max_length=50, index=True)    # Hangi aksiyon
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'permissions'
        indexes = (
            (('resource', 'action'), True),
        )
    
    def __str__(self):
        return f"Permission({self.resource}.{self.action})"


class UserRole(BaseModel):
    """Kullanıcı-Rol ilişki modeli"""
    
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User, backref='user_roles', on_delete='CASCADE')
    role = ForeignKeyField(Role, backref='user_roles', on_delete='CASCADE')
    
    # Atama bilgileri
    assigned_by = ForeignKeyField(User, backref='assigned_roles', null=True)
    assigned_at = DateTimeField(default=datetime.now)
    expires_at = DateTimeField(null=True)  # Rol süresi
    
    # Durum
    is_active = BooleanField(default=True)
    
    class Meta:
        table_name = 'user_roles'
        indexes = (
            (('user', 'role'), True),
            (('user', 'is_active'), False),
        )
    
    def __str__(self):
        return f"UserRole({self.user.username} -> {self.role.name})"
    
    def is_expired(self) -> bool:
        """Rol süresi dolmuş mu?"""
        if not self.expires_at:
            return False
        
        return datetime.now() > self.expires_at


# ============================================================================
# AUTHENTICATION & SESSIONS MODELLERİ
# ============================================================================

class Session(BaseModel):
    """Oturum modeli"""
    
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User, backref='sessions', on_delete='CASCADE')
    
    # Token bilgileri
    token = CharField(max_length=500, unique=True, index=True)
    refresh_token = CharField(max_length=500, unique=True, index=True)
    
    # Bağlantı bilgileri
    ip_address = CharField(max_length=45, index=True)  # IPv6 desteği
    user_agent = TextField(null=True)
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now, index=True)
    expires_at = DateTimeField(index=True)
    last_activity = DateTimeField(default=datetime.now, index=True)
    
    # Durum
    is_active = BooleanField(default=True, index=True)
    
    # Ekstra alanlar
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'sessions'
        indexes = (
            (('user', 'is_active'), False),
            (('ip_address', 'created_at'), False),
        )
    
    def __str__(self):
        return f"Session({self.user.username})"
    
    def is_expired(self) -> bool:
        """Oturum süresi dolmuş mu?"""
        return datetime.now() > self.expires_at
    
    def update_activity(self) -> None:
        """Son aktivite zamanını güncelle"""
        self.last_activity = datetime.now()
        self.save()
    
    def extend_expiry(self, minutes: int = 30) -> None:
        """Oturum süresini uzat"""
        self.expires_at = datetime.now() + timedelta(minutes=minutes)
        self.save()


class ApiKey(BaseModel):
    """API Key modeli"""
    
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User, backref='api_keys', on_delete='CASCADE')
    
    # Key bilgileri
    key_hash = CharField(max_length=255, unique=True, index=True)
    name = CharField(max_length=100)
    description = TextField(null=True)
    
    # İzinler
    permissions = JSONField(default=list)
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now)
    expires_at = DateTimeField(null=True, index=True)
    last_used = DateTimeField(null=True, index=True)
    
    # Durum
    is_active = BooleanField(default=True, index=True)
    
    # Ekstra alanlar
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'api_keys'
        indexes = (
            (('user', 'is_active'), False),
            (('key_hash', 'is_active'), False),
        )
    
    def __str__(self):
        return f"ApiKey({self.name})"
    
    def is_expired(self) -> bool:
        """API Key süresi dolmuş mu?"""
        if not self.expires_at:
            return False
        
        return datetime.now() > self.expires_at
    
    def update_last_used(self) -> None:
        """Son kullanım zamanını güncelle"""
        self.last_used = datetime.now()
        self.save()
    
    def has_permission(self, permission: str) -> bool:
        """API Key'in belirli bir izni var mı?"""
        if "*" in self.permissions:
            return True
        
        return permission in self.permissions


# ============================================================================
# SİSTEM YAPILANDIRMASI MODELLERİ
# ============================================================================

class Config(BaseModel):
    """Konfigürasyon modeli"""
    
    id = AutoField(primary_key=True)
    category = CharField(max_length=50, index=True)
    key = CharField(max_length=100, index=True)
    value = TextField()
    data_type = CharField(max_length=20, default='string')  # string, int, bool, json
    
    # Açıklama ve güvenlik
    description = TextField(null=True)
    is_encrypted = BooleanField(default=False)
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    updated_by = ForeignKeyField(User, backref='config_updates', null=True)
    
    class Meta:
        table_name = 'config'
        indexes = (
            (('category', 'key'), True),
        )
    
    def __str__(self):
        return f"Config({self.category}.{self.key})"
    
    def get_value(self):
        """Değeri uygun tipte döndür"""
        if self.data_type == 'int':
            return int(self.value)
        elif self.data_type == 'bool':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.data_type == 'json':
            return json.loads(self.value)
        else:
            return self.value
    
    def set_value(self, value):
        """Değeri uygun formatta kaydet"""
        if self.data_type == 'json':
            self.value = json.dumps(value, ensure_ascii=False)
        else:
            self.value = str(value)
        
        self.updated_at = datetime.now()
        self.save()


class SystemSettings(BaseModel):
    """Sistem ayarları modeli"""
    
    id = AutoField(primary_key=True)
    key = CharField(max_length=100, unique=True, index=True)
    value = TextField()
    default_value = TextField()
    data_type = CharField(max_length=20, default='string')
    
    # Açıklama ve durum
    description = TextField(null=True)
    is_readonly = BooleanField(default=False)
    
    # Tarih alanları
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'system_settings'
    
    def __str__(self):
        return f"SystemSettings({self.key})"
    
    def get_value(self):
        """Değeri uygun tipte döndür"""
        if self.data_type == 'int':
            return int(self.value)
        elif self.data_type == 'bool':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.data_type == 'json':
            return json.loads(self.value)
        else:
            return self.value


# ============================================================================
# SERVER & API MANAGEMENT MODELLERİ
# ============================================================================

class Server(BaseModel):
    """Server modeli"""
    
    id = AutoField(primary_key=True)
    name = CharField(max_length=100, unique=True, index=True)
    host = CharField(max_length=255, default='localhost')
    port = IntegerField(default=8080)
    protocol = CharField(max_length=10, default='http')  # http, https
    
    # Durum bilgileri
    status = CharField(max_length=20, default='stopped', index=True)
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    last_ping = DateTimeField(null=True, index=True)
    
    # Ekstra alanlar
    config = JSONField(default=dict)
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'servers'
        indexes = (
            (('host', 'port'), False),
            (('status', 'last_ping'), False),
        )
    
    def __str__(self):
        return f"Server({self.name})"
    
    def get_url(self) -> str:
        """Server URL'ini al"""
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def is_online(self) -> bool:
        """Server online mı?"""
        if not self.last_ping:
            return False
        
        # Son 1 dakika içinde ping alınmışsa online sayılır
        return datetime.now() - self.last_ping < timedelta(minutes=1)
    
    def update_ping(self) -> None:
        """Ping zamanını güncelle"""
        self.last_ping = datetime.now()
        self.save()


class ApiEndpoint(BaseModel):
    """API Endpoint modeli"""
    
    id = AutoField(primary_key=True)
    method = CharField(max_length=10, index=True)  # GET, POST, PUT, DELETE
    path = CharField(max_length=255, index=True)
    description = TextField(null=True)
    
    # Durum ve güvenlik
    is_active = BooleanField(default=True, index=True)
    required_roles = JSONField(default=list)
    rate_limit = IntegerField(default=100)  # Dakikada istek sayısı
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    # Ekstra alanlar
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'api_endpoints'
        indexes = (
            (('method', 'path'), True),
            (('is_active', 'method'), False),
        )
    
    def __str__(self):
        return f"ApiEndpoint({self.method} {self.path})"
    
    def requires_role(self, role_name: str) -> bool:
        """Endpoint belirli bir rol gerektiriyor mu?"""
        return role_name in self.required_roles


class ApiLog(BaseModel):
    """API Log modeli"""
    
    id = AutoField(primary_key=True)
    endpoint = ForeignKeyField(ApiEndpoint, backref='logs', null=True)
    user = ForeignKeyField(User, backref='api_logs', null=True)
    
    # Request bilgileri
    method = CharField(max_length=10, index=True)
    path = CharField(max_length=255, index=True)
    status_code = IntegerField(index=True)
    response_time = FloatField()  # Milisaniye
    
    # Bağlantı bilgileri
    ip_address = CharField(max_length=45, index=True)
    user_agent = TextField(null=True)
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now, index=True)
    
    # Ekstra alanlar
    request_data = JSONField(default=dict)
    response_data = JSONField(default=dict)
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'api_logs'
        indexes = (
            (('user', 'created_at'), False),
            (('status_code', 'created_at'), False),
            (('ip_address', 'created_at'), False),
        )
    
    def __str__(self):
        return f"ApiLog({self.method} {self.path} - {self.status_code})"


# ============================================================================
# MONITORING & LOGS MODELLERİ
# ============================================================================

class SystemLog(BaseModel):
    """Sistem log modeli"""
    
    id = AutoField(primary_key=True)
    level = CharField(max_length=20, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    module = CharField(max_length=100, index=True)
    message = TextField()
    extra_data = JSONField(default=dict)
    
    # Kullanıcı ve bağlantı bilgileri
    user = ForeignKeyField(User, backref='system_logs', null=True)
    ip_address = CharField(max_length=45, null=True, index=True)
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now, index=True)
    
    class Meta:
        table_name = 'system_logs'
        indexes = (
            (('level', 'created_at'), False),
            (('module', 'created_at'), False),
            (('user', 'created_at'), False),
        )
    
    def __str__(self):
        return f"SystemLog({self.level} - {self.module})"


class SystemMetric(BaseModel):
    """Sistem metrik modeli"""
    
    id = AutoField(primary_key=True)
    metric_name = CharField(max_length=100, index=True)
    value = FloatField()
    unit = CharField(max_length=20, default='')
    tags = JSONField(default=dict)
    
    # Tarih alanları
    recorded_at = DateTimeField(default=datetime.now, index=True)
    
    class Meta:
        table_name = 'system_metrics'
        indexes = (
            (('metric_name', 'recorded_at'), False),
        )
    
    def __str__(self):
        return f"SystemMetric({self.metric_name}: {self.value}{self.unit})"


class Alert(BaseModel):
    """Alert modeli"""
    
    id = AutoField(primary_key=True)
    type = CharField(max_length=50, index=True)  # system, security, performance, error
    severity = CharField(max_length=20, index=True)  # low, medium, high, critical
    title = CharField(max_length=200)
    message = TextField()
    
    # Durum
    is_resolved = BooleanField(default=False, index=True)
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now, index=True)
    resolved_at = DateTimeField(null=True)
    resolved_by = ForeignKeyField(User, backref='resolved_alerts', null=True)
    
    # Ekstra alanlar
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'alerts'
        indexes = (
            (('type', 'severity'), False),
            (('is_resolved', 'created_at'), False),
        )
    
    def __str__(self):
        return f"Alert({self.type} - {self.severity})"
    
    def resolve(self, user: User) -> None:
        """Alert'i çöz"""
        self.is_resolved = True
        self.resolved_at = datetime.now()
        self.resolved_by = user
        self.save()


# ============================================================================
# BACKUP & MAINTENANCE MODELLERİ
# ============================================================================

class Backup(BaseModel):
    """Backup modeli"""
    
    id = AutoField(primary_key=True)
    type = CharField(max_length=50, index=True)  # full, incremental, config, database
    filename = CharField(max_length=255)
    file_path = CharField(max_length=500)
    size_bytes = BigIntegerField()
    
    # Tarih alanları
    created_at = DateTimeField(default=datetime.now, index=True)
    created_by = ForeignKeyField(User, backref='created_backups', null=True)
    
    # Durum
    is_scheduled = BooleanField(default=False)
    
    # Ekstra alanlar
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'backups'
        indexes = (
            (('type', 'created_at'), False),
            (('is_scheduled', 'created_at'), False),
        )
    
    def __str__(self):
        return f"Backup({self.type} - {self.filename})"
    
    def get_size_mb(self) -> float:
        """Dosya boyutunu MB cinsinden al"""
        return round(self.size_bytes / (1024 * 1024), 2)


class MaintenanceTask(BaseModel):
    """Bakım görevi modeli"""
    
    id = AutoField(primary_key=True)
    name = CharField(max_length=100, index=True)
    description = TextField(null=True)
    status = CharField(max_length=20, default='pending', index=True)  # pending, running, completed, failed
    
    # Zamanlama
    scheduled_at = DateTimeField(index=True)
    started_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)
    
    # Sonuç
    result = TextField(null=True)
    
    # Ekstra alanlar
    metadata = JSONField(default=dict)
    
    class Meta:
        table_name = 'maintenance_tasks'
        indexes = (
            (('status', 'scheduled_at'), False),
        )
    
    def __str__(self):
        return f"MaintenanceTask({self.name})"
    
    def start(self) -> None:
        """Görevi başlat"""
        self.status = 'running'
        self.started_at = datetime.now()
        self.save()
    
    def complete(self, result: str = None) -> None:
        """Görevi tamamla"""
        self.status = 'completed'
        self.completed_at = datetime.now()
        if result:
            self.result = result
        self.save()
    
    def fail(self, error: str) -> None:
        """Görevi başarısız olarak işaretle"""
        self.status = 'failed'
        self.completed_at = datetime.now()
        self.result = error
        self.save()


# ============================================================================
# MODEL İLİŞKİLERİ
# ============================================================================

# User-Role ilişkileri
# User model'ine roles property'si ekle
def get_user_roles(self):
    """Kullanıcının rollerini getir"""
    return [ur.role for ur in self.user_roles.select().join(Role)]

User.roles = property(get_user_roles)

# Role model'ine users property'si ekle  
def get_role_users(self):
    """Rolün kullanıcılarını getir"""
    return [ur.user for ur in self.user_roles.select().join(User)]

Role.users = property(get_role_users)

# ============================================================================
# MODEL LİSTESİ
# ============================================================================

# Tüm modellerin listesi
ALL_MODELS = [
    # Kullanıcı yönetimi
    User, Role, Permission, UserRole,
    
    # Authentication & Sessions
    Session, ApiKey,
    
    # Sistem yapılandırması
    Config, SystemSettings,
    
    # Server & API Management
    Server, ApiEndpoint, ApiLog,
    
    # Monitoring & Logs
    SystemLog, SystemMetric, Alert,
    
    # Backup & Maintenance
    Backup, MaintenanceTask
]

# Model kategorileri
USER_MODELS = [User, Role, Permission, UserRole]
AUTH_MODELS = [Session, ApiKey]
CONFIG_MODELS = [Config, SystemSettings]
SERVER_MODELS = [Server, ApiEndpoint, ApiLog]
MONITORING_MODELS = [SystemLog, SystemMetric, Alert]
MAINTENANCE_MODELS = [Backup, MaintenanceTask]
