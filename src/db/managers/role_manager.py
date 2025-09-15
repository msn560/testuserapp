"""
Role Manager module - Rol yönetimi

Bu modül rol ve izin veritabanı işlemlerini yönetir.
Rol CRUD işlemleri, izin yönetimi ve rol istatistikleri.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_manager import BaseManager
from ..models import Role, Permission, UserRole
from ...core.constants import LogLevel
from ...utils.logger import logger


class RoleManager(BaseManager):
    """
    Rol yönetimi sınıfı.
    
    Bu sınıf rol ve izin veritabanı işlemlerini yönetir.
    """
    
    def __init__(self):
        """RoleManager'ı başlatır."""
        super().__init__(Role)
        self.logger = logger
    
    def create_role(self, name: str, description: str = None, 
                   permissions: List[str] = None, color: str = None, 
                   icon: str = None, is_system_role: bool = False) -> Optional[Role]:
        """
        Yeni rol oluşturur.
        
        Args:
            name: Rol adı
            description: Rol açıklaması
            permissions: İzin listesi (JSON string olarak saklanır)
            color: Rol rengi
            icon: Rol ikonu
            is_system_role: Sistem rolü mü
            
        Returns:
            Oluşturulan rol veya None
        """
        try:
            # Rol adı kontrolü
            if self.exists(name=name):
                self.logger.error(f"Role already exists: {name}")
                return None
            
            # Rol oluştur
            role_data = {
                'name': name,
                'description': description or f"Role: {name}",
                'permissions': str(permissions or []),  # JSON string olarak sakla
                'color': color,
                'icon': icon,
                'is_system_role': is_system_role,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            role = self.create(**role_data)
            
            if role:
                self.logger.info(f"Role created: {name} (ID: {role.id})")
            
            return role
            
        except Exception as e:
            self.logger.error(f"Failed to create role: {e}")
            return None
    
    def update_role_permissions(self, role_id: int, permissions: List[str]) -> bool:
        """
        Rol izinlerini günceller.
        
        Args:
            role_id: Rol ID'si
            permissions: Yeni izin listesi
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            return self.update(role_id, permissions=str(permissions))
            
        except Exception as e:
            self.logger.error(f"Failed to update role permissions for role {role_id}: {e}")
            return False
    
    def get_role_permissions(self, role_id: int) -> List[str]:
        """
        Rol izinlerini döndürür.
        
        Args:
            role_id: Rol ID'si
            
        Returns:
            İzin listesi
        """
        try:
            role = self.get_by_id(role_id)
            if not role:
                return []
            
            # Permissions string'ini parse et
            import ast
            permissions = ast.literal_eval(role.permissions) if role.permissions else []
            return permissions if isinstance(permissions, list) else []
            
        except Exception as e:
            self.logger.error(f"Failed to get role permissions for role {role_id}: {e}")
            return []
    
    def get_user_count_by_role(self, role_id: int) -> int:
        """
        Role sahip kullanıcı sayısını döndürür.
        
        Args:
            role_id: Rol ID'si
            
        Returns:
            Kullanıcı sayısı
        """
        try:
            return UserRole.select().where(UserRole.role_id == role_id).count()
            
        except Exception as e:
            self.logger.error(f"Failed to get user count for role {role_id}: {e}")
            return 0
    
    def get_system_roles(self) -> List[Role]:
        """
        Sistem rollerini döndürür.
        
        Returns:
            Sistem rolleri listesi
        """
        return self.get_by_filters({'is_system_role': True})
    
    def get_custom_roles(self) -> List[Role]:
        """
        Özel rolleri döndürür.
        
        Returns:
            Özel roller listesi
        """
        return self.get_by_filters({'is_system_role': False})
    
    def delete_role(self, role_id: int, force: bool = False) -> bool:
        """
        Rol siler.
        
        Args:
            role_id: Silinecek rol ID'si
            force: Kullanıcıları olan rolü zorla sil
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            role = self.get_by_id(role_id)
            if not role:
                return False
            
            # Sistem rolü kontrolü
            if role.is_system_role:
                self.logger.error(f"Cannot delete system role: {role.name}")
                return False
            
            # Kullanıcı kontrolü
            user_count = self.get_user_count_by_role(role_id)
            if user_count > 0 and not force:
                self.logger.error(f"Cannot delete role with {user_count} users: {role.name}")
                return False
            
            # Kullanıcı rol atamalarını sil
            if user_count > 0:
                UserRole.delete().where(UserRole.role_id == role_id).execute()
                self.logger.warning(f"Removed {user_count} user assignments for role: {role.name}")
            
            # Rolü sil
            success = self.delete(role_id)
            
            if success:
                self.logger.info(f"Role deleted: {role.name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete role {role_id}: {e}")
            return False
    
    def get_role_statistics(self) -> Dict[str, Any]:
        """
        Rol istatistiklerini döndürür.
        
        Returns:
            Rol istatistikleri
        """
        try:
            total_roles = self.count()
            system_roles = self.count({'is_system_role': True})
            custom_roles = total_roles - system_roles
            
            # Her rol için kullanıcı sayısı
            role_usage = {}
            for role in self.get_all():
                user_count = self.get_user_count_by_role(role.id)
                role_usage[role.name] = {
                    'id': role.id,
                    'user_count': user_count,
                    'is_system_role': role.is_system_role,
                    'description': role.description
                }
            
            return {
                'total_roles': total_roles,
                'system_roles': system_roles,
                'custom_roles': custom_roles,
                'role_usage': role_usage
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get role statistics: {e}")
            return {}


class PermissionManager(BaseManager):
    """
    İzin yönetimi sınıfı.
    
    Bu sınıf izin veritabanı işlemlerini yönetir.
    """
    
    def __init__(self):
        """PermissionManager'ı başlatır."""
        super().__init__(Permission)
        self.logger = logger
    
    def create_permission(self, name: str, description: str = None,
                         resource: str = None, action: str = None) -> Optional[Permission]:
        """
        Yeni izin oluşturur.
        
        Args:
            name: İzin adı
            description: İzin açıklaması
            resource: Kaynak adı
            action: Eylem adı
            
        Returns:
            Oluşturulan izin veya None
        """
        try:
            # İzin adı kontrolü
            if self.exists(name=name):
                self.logger.error(f"Permission already exists: {name}")
                return None
            
            # İzin oluştur
            permission_data = {
                'name': name,
                'description': description or f"Permission: {name}",
                'resource': resource,
                'action': action,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            permission = self.create(**permission_data)
            
            if permission:
                self.logger.info(f"Permission created: {name} (ID: {permission.id})")
            
            return permission
            
        except Exception as e:
            self.logger.error(f"Failed to create permission: {e}")
            return None
    
    def get_permissions_by_resource(self, resource: str) -> List[Permission]:
        """
        Kaynağa göre izinleri döndürür.
        
        Args:
            resource: Kaynak adı
            
        Returns:
            İzin listesi
        """
        return self.get_by_filters({'resource': resource})
    
    def get_permissions_by_action(self, action: str) -> List[Permission]:
        """
        Eyleme göre izinleri döndürür.
        
        Args:
            action: Eylem adı
            
        Returns:
            İzin listesi
        """
        return self.get_by_filters({'action': action})


# Global instances
role_manager = RoleManager()
permission_manager = PermissionManager()
