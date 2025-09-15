"""
Authentication schemas - Kimlik doğrulama şemaları

Bu modül kimlik doğrulama API'leri için veri şemalarını tanımlar.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime


class LoginRequest(BaseModel):
    """Giriş isteği şeması."""
    username: str = Field(..., min_length=3, max_length=50, description="Kullanıcı adı veya e-posta")
    password: str = Field(..., min_length=6, max_length=128, description="Parola")
    remember_me: bool = Field(False, description="Beni hatırla")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "admin",
                "password": "password123",
                "remember_me": False
            }
        }


class LoginResponse(BaseModel):
    """Giriş yanıtı şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    user: Optional[Dict[str, Any]] = Field(None, description="Kullanıcı bilgileri")
    token: Optional[str] = Field(None, description="Erişim token'ı")
    refresh_token: Optional[str] = Field(None, description="Yenileme token'ı")
    expires_at: Optional[datetime] = Field(None, description="Token geçerlilik süresi")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Giriş başarılı",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "full_name": "Administrator",
                    "roles": ["admin"]
                },
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "refresh_token_here",
                "expires_at": "2023-12-31T23:59:59"
            }
        }


class LogoutRequest(BaseModel):
    """Çıkış isteği şeması."""
    token: str = Field(..., description="Çıkış yapılacak token")
    all_sessions: bool = Field(False, description="Tüm oturumlardan çık")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "all_sessions": False
            }
        }


class LogoutResponse(BaseModel):
    """Çıkış yanıtı şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Çıkış başarılı"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Token yenileme isteği şeması."""
    refresh_token: str = Field(..., description="Yenileme token'ı")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "refresh_token_here"
            }
        }


class RefreshTokenResponse(BaseModel):
    """Token yenileme yanıtı şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    token: Optional[str] = Field(None, description="Yeni erişim token'ı")
    refresh_token: Optional[str] = Field(None, description="Yeni yenileme token'ı")
    expires_at: Optional[datetime] = Field(None, description="Token geçerlilik süresi")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Token yenilendi",
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "new_refresh_token_here",
                "expires_at": "2023-12-31T23:59:59"
            }
        }


class VerifyTokenRequest(BaseModel):
    """Token doğrulama isteği şeması."""
    token: str = Field(..., description="Doğrulanacak token")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class VerifyTokenResponse(BaseModel):
    """Token doğrulama yanıtı şeması."""
    success: bool = Field(..., description="Token geçerli mi")
    message: str = Field(..., description="İşlem mesajı")
    user: Optional[Dict[str, Any]] = Field(None, description="Kullanıcı bilgileri")
    expires_at: Optional[datetime] = Field(None, description="Token geçerlilik süresi")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Token geçerli",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "roles": ["admin"]
                },
                "expires_at": "2023-12-31T23:59:59"
            }
        }


class ForgotPasswordRequest(BaseModel):
    """Parola sıfırlama isteği şeması."""
    email: EmailStr = Field(..., description="E-posta adresi")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ForgotPasswordResponse(BaseModel):
    """Parola sıfırlama yanıtı şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Parola sıfırlama e-postası gönderildi"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Parola yenileme isteği şeması."""
    reset_token: str = Field(..., description="Sıfırlama token'ı")
    new_password: str = Field(..., min_length=6, max_length=128, description="Yeni parola")
    confirm_password: str = Field(..., min_length=6, max_length=128, description="Parola onayı")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Parolalar eşleşmiyor')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "reset_token": "reset_token_here",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        }


class ResetPasswordResponse(BaseModel):
    """Parola yenileme yanıtı şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Parola başarıyla yenilendi"
            }
        }


class ChangePasswordRequest(BaseModel):
    """Parola değiştirme isteği şeması."""
    current_password: str = Field(..., min_length=6, max_length=128, description="Mevcut parola")
    new_password: str = Field(..., min_length=6, max_length=128, description="Yeni parola")
    confirm_password: str = Field(..., min_length=6, max_length=128, description="Parola onayı")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Parolalar eşleşmiyor')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        }


class AuthResponse(BaseModel):
    """Genel kimlik doğrulama yanıtı şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    data: Optional[Dict[str, Any]] = Field(None, description="Ek veri")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "İşlem başarılı",
                "data": {}
            }
        }
