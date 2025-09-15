"""
User schemas - Kullanıcı şemaları

Bu modül kullanıcı API'leri için veri şemalarını tanımlar.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime


class UserBase(BaseModel):
    """Temel kullanıcı şeması."""
    username: str = Field(..., min_length=3, max_length=50, description="Kullanıcı adı")
    email: EmailStr = Field(..., description="E-posta adresi")
    full_name: Optional[str] = Field(None, max_length=100, description="Tam ad")
    is_active: bool = Field(True, description="Aktif mi")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": True
            }
        }


class UserCreate(UserBase):
    """Kullanıcı oluşturma şeması."""
    password: str = Field(..., min_length=6, max_length=128, description="Parola")
    confirm_password: str = Field(..., min_length=6, max_length=128, description="Parola onayı")
    role: Optional[str] = Field("viewer", description="Kullanıcı rolü")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Parolalar eşleşmiyor')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "password": "password123",
                "confirm_password": "password123",
                "role": "viewer",
                "is_active": True
            }
        }


class UserUpdate(BaseModel):
    """Kullanıcı güncelleme şeması."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Kullanıcı adı")
    email: Optional[EmailStr] = Field(None, description="E-posta adresi")
    full_name: Optional[str] = Field(None, max_length=100, description="Tam ad")
    is_active: Optional[bool] = Field(None, description="Aktif mi")
    avatar_path: Optional[str] = Field(None, description="Avatar yolu")
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "John Smith",
                "is_active": True
            }
        }


class UserResponse(UserBase):
    """Kullanıcı yanıtı şeması."""
    id: int = Field(..., description="Kullanıcı ID'si")
    avatar_path: Optional[str] = Field(None, description="Avatar yolu")
    roles: List[str] = Field([], description="Kullanıcı rolleri")
    created_at: datetime = Field(..., description="Oluşturulma tarihi")
    updated_at: datetime = Field(..., description="Güncellenme tarihi")
    last_login: Optional[datetime] = Field(None, description="Son giriş tarihi")
    is_verified: bool = Field(False, description="Doğrulanmış mı")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "avatar_path": "/path/to/avatar.jpg",
                "roles": ["viewer"],
                "is_active": True,
                "is_verified": True,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "last_login": "2023-12-01T10:30:00"
            }
        }


class UserListResponse(BaseModel):
    """Kullanıcı listesi yanıtı şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    users: List[UserResponse] = Field([], description="Kullanıcı listesi")
    total: int = Field(0, description="Toplam kullanıcı sayısı")
    page: int = Field(1, description="Sayfa numarası")
    limit: int = Field(50, description="Sayfa başına kayıt sayısı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Kullanıcılar getirildi",
                "users": [
                    {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@example.com",
                        "full_name": "Administrator",
                        "roles": ["admin"],
                        "is_active": True,
                        "is_verified": True,
                        "created_at": "2023-01-01T00:00:00",
                        "updated_at": "2023-01-01T00:00:00",
                        "last_login": "2023-12-01T10:30:00"
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 50
            }
        }


class UserProfile(BaseModel):
    """Kullanıcı profil şeması."""
    id: int = Field(..., description="Kullanıcı ID'si")
    username: str = Field(..., description="Kullanıcı adı")
    email: EmailStr = Field(..., description="E-posta adresi")
    full_name: Optional[str] = Field(None, description="Tam ad")
    avatar_path: Optional[str] = Field(None, description="Avatar yolu")
    roles: List[str] = Field([], description="Kullanıcı rolleri")
    is_active: bool = Field(True, description="Aktif mi")
    is_verified: bool = Field(False, description="Doğrulanmış mı")
    created_at: datetime = Field(..., description="Oluşturulma tarihi")
    updated_at: datetime = Field(..., description="Güncellenme tarihi")
    last_login: Optional[datetime] = Field(None, description="Son giriş tarihi")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "avatar_path": "/path/to/avatar.jpg",
                "roles": ["viewer"],
                "is_active": True,
                "is_verified": True,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "last_login": "2023-12-01T10:30:00"
            }
        }


class UserProfileUpdate(BaseModel):
    """Kullanıcı profil güncelleme şeması."""
    full_name: Optional[str] = Field(None, max_length=100, description="Tam ad")
    email: Optional[EmailStr] = Field(None, description="E-posta adresi")
    current_password: Optional[str] = Field(None, min_length=6, description="Mevcut parola")
    new_password: Optional[str] = Field(None, min_length=6, description="Yeni parola")
    confirm_password: Optional[str] = Field(None, min_length=6, description="Parola onayı")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and values['new_password'] and v != values['new_password']:
            raise ValueError('Parolalar eşleşmiyor')
        return v
    
    @validator('new_password')
    def password_requires_current(cls, v, values, **kwargs):
        if v and not values.get('current_password'):
            raise ValueError('Yeni parola için mevcut parola gerekli')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "John Smith",
                "email": "johnsmith@example.com",
                "current_password": "oldpassword",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        }


class UserPasswordChange(BaseModel):
    """Kullanıcı parola değiştirme şeması."""
    current_password: str = Field(..., min_length=6, description="Mevcut parola")
    new_password: str = Field(..., min_length=6, description="Yeni parola")
    confirm_password: str = Field(..., min_length=6, description="Parola onayı")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Parolalar eşleşmiyor')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        }


class UserRoleAssignment(BaseModel):
    """Kullanıcı rol atama şeması."""
    role_name: str = Field(..., description="Atanacak rol adı")
    
    class Config:
        schema_extra = {
            "example": {
                "role_name": "admin"
            }
        }


class UserRoleAssign(BaseModel):
    """Kullanıcı rol atama şeması (alternatif isim)."""
    role_name: str = Field(..., description="Atanacak rol adı")
    
    class Config:
        schema_extra = {
            "example": {
                "role_name": "admin"
            }
        }


class UserRoleResponse(BaseModel):
    """Kullanıcı rol yanıtı şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    user_id: int = Field(..., description="Kullanıcı ID'si")
    role_name: str = Field(..., description="Rol adı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Rol başarıyla atandı",
                "user_id": 1,
                "role_name": "admin"
            }
        }


class UserSearchRequest(BaseModel):
    """Kullanıcı arama isteği şeması."""
    search_term: str = Field(..., min_length=2, max_length=100, description="Arama terimi")
    filters: Optional[Dict[str, Any]] = Field(None, description="Ek filtreler")
    page: int = Field(1, ge=1, description="Sayfa numarası")
    limit: int = Field(50, ge=1, le=100, description="Sayfa başına kayıt sayısı")
    
    class Config:
        schema_extra = {
            "example": {
                "search_term": "john",
                "filters": {
                    "is_active": True,
                    "role": "admin"
                },
                "page": 1,
                "limit": 20
            }
        }


class UserStatsResponse(BaseModel):
    """Kullanıcı istatistikleri yanıtı şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    total_users: int = Field(0, description="Toplam kullanıcı sayısı")
    active_users: int = Field(0, description="Aktif kullanıcı sayısı")
    inactive_users: int = Field(0, description="Pasif kullanıcı sayısı")
    recent_logins_30d: int = Field(0, description="Son 30 günde giriş yapan kullanıcı sayısı")
    role_distribution: Dict[str, int] = Field({}, description="Rollere göre kullanıcı dağılımı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "İstatistikler getirildi",
                "total_users": 100,
                "active_users": 85,
                "inactive_users": 15,
                "recent_logins_30d": 50,
                "role_distribution": {
                    "admin": 5,
                    "operator": 20,
                    "viewer": 75
                }
            }
        }


class UserLoginHistory(BaseModel):
    """Kullanıcı giriş geçmişi şeması."""
    login_time: datetime = Field(..., description="Giriş zamanı")
    ip_address: str = Field(..., description="IP adresi")
    user_agent: str = Field(..., description="User agent")
    is_active: bool = Field(..., description="Oturum aktif mi")
    last_activity: Optional[datetime] = Field(None, description="Son aktivite zamanı")
    
    class Config:
        schema_extra = {
            "example": {
                "login_time": "2023-12-01T10:30:00",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "is_active": True,
                "last_activity": "2023-12-01T11:15:00"
            }
        }


class UserLoginHistoryResponse(BaseModel):
    """Kullanıcı giriş geçmişi yanıtı şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    login_history: List[UserLoginHistory] = Field([], description="Giriş geçmişi")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Giriş geçmişi getirildi",
                "login_history": [
                    {
                        "login_time": "2023-12-01T10:30:00",
                        "ip_address": "192.168.1.100",
                        "user_agent": "Mozilla/5.0...",
                        "is_active": True,
                        "last_activity": "2023-12-01T11:15:00"
                    }
                ]
            }
        }


class UserResponse(BaseModel):
    """Genel kullanıcı işlem yanıtı şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    user: Optional[UserResponse] = Field(None, description="Kullanıcı verisi")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "İşlem başarılı",
                "user": {
                    "id": 1,
                    "username": "johndoe",
                    "email": "john@example.com",
                    "full_name": "John Doe",
                    "roles": ["viewer"],
                    "is_active": True
                }
            }
        }
