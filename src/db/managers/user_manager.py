"""
User Manager module - Kullanıcı yönetimi

Bu modül kullanıcı veritabanı işlemlerini yönetir.
Kullanıcı CRUD işlemleri, rol yönetimi ve kullanıcı istatistikleri.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import bcrypt

from .base_manager import BaseManager
from ..models import User, Role, UserRole, Session
from ...core.constants import LogLevel
from ...utils.logger import logger


class UserManager(BaseManager):
    """
    Kullanıcı yönetimi sınıfı.
    
    Bu sınıf kullanıcı veritabanı işlemlerini ve rol yönetimini sağlar.
    """
    
    def __init__(self):
        """UserManager'ı başlatır."""
        super().__init__(User)
        self.logger = logger
    
    def create_user(self, username: str, email: str, password: str, 
                   full_name: str = None, role_name: str = "viewer",
                   is_active: bool = True, **kwargs) -> Optional[User]:
        """
        Yeni kullanıcı oluşturur.
        
        Args:
            username: Kullanıcı adı
            email: E-posta adresi
            password: Parola (düz metin)
            full_name: Tam ad
            role_name: Rol adı
            is_active: Aktif mi
            **kwargs: Ek alanlar
            
        Returns:
            Oluşturulan kullanıcı veya None
        """
        try:
            # Kullanıcı adı ve e-posta kontrolü
            if self.exists(username=username):
                self.logger.error(f"Username already exists: {username}")
                return None
            
            if self.exists(email=email):
                self.logger.error(f"Email already exists: {email}")
                return None
            
            # Parolayı hashle
            password_hash = self._hash_password(password)
            
            # Kullanıcı oluştur
            user_data = {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'full_name': full_name or username,
                'is_active': is_active,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                **kwargs
            }
            
            user = self.create(**user_data)
            if not user:
                return None
            
            # Rol ata
            if not self.assign_role(user.id, role_name):
                self.logger.warning(f"Failed to assign role {role_name} to user {user.id}")
            
            self.logger.info(f"User created: {username} (ID: {user.id})")
            return user
            
        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Kullanıcı kimlik doğrulaması yapar.
        
        Args:
            username: Kullanıcı adı veya e-posta
            password: Parola
            
        Returns:
            Kimlik doğrulanmış kullanıcı veya None
        """
        try:
            # Kullanıcıyı bul (username veya email ile)
            user = self.get_by_field('username', username)
            if not user:
                user = self.get_by_field('email', username)
            
            if not user:
                self.logger.warning(f"User not found: {username}")
                return None
            
            # Kullanıcı aktif mi kontrol et
            if not user.is_active:
                self.logger.warning(f"User is inactive: {username}")
                return None
            
            # Parola kontrolü
            if not self._verify_password(password, user.password_hash):
                self.logger.warning(f"Invalid password for user: {username}")
                return None
            
            # Son giriş zamanını güncelle
            self.update(user.id, last_login=datetime.now())
            
            self.logger.info(f"User authenticated: {username}")
            return user
            
        except Exception as e:
            self.logger.error(f"Failed to authenticate user: {e}")
            return None
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Kullanıcı parolasını değiştirir.
        
        Args:
            user_id: Kullanıcı ID'si
            old_password: Eski parola
            new_password: Yeni parola
            
        Returns:
            True if password changed successfully, False otherwise
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                return False
            
            # Eski parola kontrolü
            if not self._verify_password(old_password, user.password_hash):
                self.logger.warning(f"Invalid old password for user: {user_id}")
                return False
            
            # Yeni parolayı hashle
            new_password_hash = self._hash_password(new_password)
            
            # Parolayı güncelle
            return self.update(user_id, password_hash=new_password_hash)
            
        except Exception as e:
            self.logger.error(f"Failed to change password for user {user_id}: {e}")
            return False
    
    def reset_password(self, user_id: int, new_password: str) -> bool:
        """
        Kullanıcı parolasını sıfırlar (admin yetkisi gerekir).
        
        Args:
            user_id: Kullanıcı ID'si
            new_password: Yeni parola
            
        Returns:
            True if password reset successfully, False otherwise
        """
        try:
            # Yeni parolayı hashle
            new_password_hash = self._hash_password(new_password)
            
            # Parolayı güncelle
            success = self.update(user_id, password_hash=new_password_hash)
            
            if success:
                self.logger.info(f"Password reset for user: {user_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to reset password for user {user_id}: {e}")
            return False
    
    def assign_role(self, user_id: int, role_name: str, assigned_by: int = None) -> bool:
        """
        Kullanıcıya rol atar.
        
        Args:
            user_id: Kullanıcı ID'si
            role_name: Rol adı
            assigned_by: Atayan kullanıcı ID'si
            
        Returns:
            True if role assigned successfully, False otherwise
        """
        try:
            # Rolü bul
            role = Role.get(Role.name == role_name)
            
            # Mevcut rol atamasını kontrol et
            existing_assignment = UserRole.select().where(
                (UserRole.user_id == user_id) & (UserRole.role_id == role.id)
            ).first()
            
            if existing_assignment:
                self.logger.warning(f"Role {role_name} already assigned to user {user_id}")
                return True
            
            # Rol ataması oluştur
            UserRole.create(
                user_id=user_id,
                role_id=role.id,
                assigned_by=assigned_by,
                assigned_at=datetime.now()
            )
            
            self.logger.info(f"Role {role_name} assigned to user {user_id}")
            return True
            
        except Role.DoesNotExist:
            self.logger.error(f"Role not found: {role_name}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to assign role {role_name} to user {user_id}: {e}")
            return False
    
    def remove_role(self, user_id: int, role_name: str) -> bool:
        """
        Kullanıcıdan rol kaldırır.
        
        Args:
            user_id: Kullanıcı ID'si
            role_name: Rol adı
            
        Returns:
            True if role removed successfully, False otherwise
        """
        try:
            # Rolü bul
            role = Role.get(Role.name == role_name)
            
            # Rol atamasını bul ve sil
            deleted_count = UserRole.delete().where(
                (UserRole.user_id == user_id) & (UserRole.role_id == role.id)
            ).execute()
            
            if deleted_count > 0:
                self.logger.info(f"Role {role_name} removed from user {user_id}")
                return True
            else:
                self.logger.warning(f"Role {role_name} not assigned to user {user_id}")
                return False
                
        except Role.DoesNotExist:
            self.logger.error(f"Role not found: {role_name}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove role {role_name} from user {user_id}: {e}")
            return False
    
    def get_user_roles(self, user_id: int) -> List[str]:
        """
        Kullanıcının rollerini döndürür.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Rol adları listesi
        """
        try:
            query = (UserRole
                    .select(Role.name)
                    .join(Role)
                    .where(UserRole.user_id == user_id))
            
            roles = [user_role.role.name for user_role in query]
            return roles
            
        except Exception as e:
            self.logger.error(f"Failed to get roles for user {user_id}: {e}")
            return []
    
    def has_role(self, user_id: int, role_name: str) -> bool:
        """
        Kullanıcının belirli rolü var mı kontrol eder.
        
        Args:
            user_id: Kullanıcı ID'si
            role_name: Rol adı
            
        Returns:
            True if user has role, False otherwise
        """
        try:
            user_roles = self.get_user_roles(user_id)
            return role_name in user_roles
            
        except Exception as e:
            self.logger.error(f"Failed to check role {role_name} for user {user_id}: {e}")
            return False
    
    def activate_user(self, user_id: int) -> bool:
        """
        Kullanıcıyı aktifleştirir.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            True if activated successfully, False otherwise
        """
        return self.update(user_id, is_active=True)
    
    def deactivate_user(self, user_id: int) -> bool:
        """
        Kullanıcıyı deaktifleştirir.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            True if deactivated successfully, False otherwise
        """
        success = self.update(user_id, is_active=False)
        
        if success:
            # Kullanıcının tüm session'larını geçersiz kıl
            Session.update(is_active=False).where(Session.user_id == user_id).execute()
            self.logger.info(f"User deactivated and sessions invalidated: {user_id}")
        
        return success
    
    def get_active_users(self, limit: int = None) -> List[User]:
        """
        Aktif kullanıcıları döndürür.
        
        Args:
            limit: Maksimum kullanıcı sayısı
            
        Returns:
            Aktif kullanıcı listesi
        """
        return self.get_by_filters({'is_active': True}, limit=limit, order_by='-last_login')
    
    def get_users_by_role(self, role_name: str, limit: int = None) -> List[User]:
        """
        Belirli role sahip kullanıcıları döndürür.
        
        Args:
            role_name: Rol adı
            limit: Maksimum kullanıcı sayısı
            
        Returns:
            Kullanıcı listesi
        """
        try:
            query = (User
                    .select()
                    .join(UserRole)
                    .join(Role)
                    .where(Role.name == role_name))
            
            if limit:
                query = query.limit(limit)
            
            return list(query)
            
        except Exception as e:
            self.logger.error(f"Failed to get users by role {role_name}: {e}")
            return []
    
    def search_users(self, search_term: str, limit: int = 50) -> List[User]:
        """
        Kullanıcı arar.
        
        Args:
            search_term: Arama terimi
            limit: Maksimum sonuç sayısı
            
        Returns:
            Arama sonuçları
        """
        try:
            query = (User
                    .select()
                    .where(
                        (User.username.contains(search_term)) |
                        (User.email.contains(search_term)) |
                        (User.full_name.contains(search_term))
                    )
                    .limit(limit))
            
            return list(query)
            
        except Exception as e:
            self.logger.error(f"Failed to search users with term '{search_term}': {e}")
            return []
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """
        Kullanıcı istatistiklerini döndürür.
        
        Returns:
            Kullanıcı istatistikleri
        """
        try:
            total_users = self.count()
            active_users = self.count({'is_active': True})
            inactive_users = total_users - active_users
            
            # Son 30 gün içinde giriş yapan kullanıcılar
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_logins = self.count({
                'last_login': {'operator': 'gte', 'value': thirty_days_ago}
            })
            
            # Rollere göre dağılım
            role_distribution = {}
            for role in Role.select():
                user_count = (UserRole
                             .select()
                             .where(UserRole.role_id == role.id)
                             .count())
                role_distribution[role.name] = user_count
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': inactive_users,
                'recent_logins_30d': recent_logins,
                'role_distribution': role_distribution,
                'admin_count': role_distribution.get('admin', 0),
                'viewer_count': role_distribution.get('viewer', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user statistics: {e}")
            return {}
    
    def get_login_history(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Kullanıcının giriş geçmişini döndürür.
        
        Args:
            user_id: Kullanıcı ID'si
            limit: Maksimum kayıt sayısı
            
        Returns:
            Giriş geçmişi
        """
        try:
            sessions = (Session
                       .select()
                       .where(Session.user_id == user_id)
                       .order_by(Session.created_at.desc())
                       .limit(limit))
            
            login_history = []
            for session in sessions:
                login_history.append({
                    'login_time': session.created_at,
                    'ip_address': session.ip_address,
                    'user_agent': session.user_agent,
                    'is_active': session.is_active,
                    'last_activity': session.last_activity
                })
            
            return login_history
            
        except Exception as e:
            self.logger.error(f"Failed to get login history for user {user_id}: {e}")
            return []
    
    def _hash_password(self, password: str) -> str:
        """
        Parolayı hashler.
        
        Args:
            password: Düz metin parola
            
        Returns:
            Hashlenmiş parola
        """
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Failed to hash password: {e}")
            raise
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Parolayı doğrular.
        
        Args:
            password: Düz metin parola
            hashed_password: Hashlenmiş parola
            
        Returns:
            True if password is correct, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Failed to verify password: {e}")
            return False


# Global instance
user_manager = UserManager()
