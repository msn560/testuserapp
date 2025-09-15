"""
Response schemas - Genel yanıt şemaları

Bu modül tüm API yanıtları için ortak şemaları tanımlar.
"""

from typing import Optional, Dict, Any, List, Union, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Yanıt durumları."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class BaseResponse(BaseModel, Generic[T]):
    """Temel yanıt şeması."""
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    status: ResponseStatus = Field(ResponseStatus.SUCCESS, description="Yanıt durumu")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Yanıt zamanı")
    data: Optional[T] = Field(None, description="Yanıt verisi")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "İşlem başarılı",
                "status": "success",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": None
            }
        }


class SuccessResponse(BaseResponse[T]):
    """Başarılı yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı")
    status: ResponseStatus = Field(ResponseStatus.SUCCESS, description="Başarılı durum")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "İşlem başarıyla tamamlandı",
                "status": "success",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": {
                    "id": 1,
                    "name": "example"
                }
            }
        }


class ErrorResponse(BaseResponse[None]):
    """Hata yanıt şeması."""
    success: bool = Field(False, description="İşlem başarısız")
    status: ResponseStatus = Field(ResponseStatus.ERROR, description="Hata durumu")
    error_code: Optional[str] = Field(None, description="Hata kodu")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Hata detayları")
    data: None = Field(None, description="Hata durumunda veri yok")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "İşlem başarısız",
                "status": "error",
                "timestamp": "2024-01-01T12:00:00Z",
                "error_code": "VALIDATION_ERROR",
                "error_details": {
                    "field": "email",
                    "reason": "Invalid email format"
                },
                "data": None
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """Doğrulama hatası yanıt şeması."""
    error_code: str = Field("VALIDATION_ERROR", description="Doğrulama hatası kodu")
    validation_errors: List[Dict[str, Any]] = Field(..., description="Doğrulama hataları")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Doğrulama hatası",
                "status": "error",
                "timestamp": "2024-01-01T12:00:00Z",
                "error_code": "VALIDATION_ERROR",
                "error_details": None,
                "validation_errors": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "value": "invalid-email"
                    },
                    {
                        "field": "password",
                        "message": "Password must be at least 8 characters",
                        "value": "123"
                    }
                ],
                "data": None
            }
        }


class PaginationResponse(BaseResponse[T]):
    """Sayfalama yanıt şeması."""
    pagination: Dict[str, Any] = Field(..., description="Sayfalama bilgileri")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Veriler başarıyla alındı",
                "status": "success",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"}
                ],
                "pagination": {
                    "page": 1,
                    "limit": 20,
                    "total": 100,
                    "pages": 5,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }


class ListResponse(BaseResponse[List[T]]):
    """Liste yanıt şeması."""
    total: int = Field(..., description="Toplam kayıt sayısı")
    count: int = Field(..., description="Dönen kayıt sayısı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Liste başarıyla alındı",
                "status": "success",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"}
                ],
                "total": 100,
                "count": 2
            }
        }


class CreatedResponse(SuccessResponse[T]):
    """Oluşturma yanıt şeması."""
    message: str = Field("Kaynak başarıyla oluşturuldu", description="Oluşturma mesajı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Kaynak başarıyla oluşturuldu",
                "status": "success",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": {
                    "id": 1,
                    "name": "New Item",
                    "created_at": "2024-01-01T12:00:00Z"
                }
            }
        }


class UpdatedResponse(SuccessResponse[T]):
    """Güncelleme yanıt şeması."""
    message: str = Field("Kaynak başarıyla güncellendi", description="Güncelleme mesajı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Kaynak başarıyla güncellendi",
                "status": "success",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": {
                    "id": 1,
                    "name": "Updated Item",
                    "updated_at": "2024-01-01T12:00:00Z"
                }
            }
        }


class DeletedResponse(SuccessResponse[None]):
    """Silme yanıt şeması."""
    message: str = Field("Kaynak başarıyla silindi", description="Silme mesajı")
    data: None = Field(None, description="Silme işleminde veri dönmez")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Kaynak başarıyla silindi",
                "status": "success",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": None
            }
        }


class NotFoundResponse(ErrorResponse):
    """Bulunamadı yanıt şeması."""
    message: str = Field("Kaynak bulunamadı", description="Bulunamadı mesajı")
    error_code: str = Field("NOT_FOUND", description="Bulunamadı hatası kodu")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Kaynak bulunamadı",
                "status": "error",
                "timestamp": "2024-01-01T12:00:00Z",
                "error_code": "NOT_FOUND",
                "error_details": {
                    "resource": "user",
                    "id": 999
                },
                "data": None
            }
        }


class UnauthorizedResponse(ErrorResponse):
    """Yetkisiz erişim yanıt şeması."""
    message: str = Field("Yetkisiz erişim", description="Yetkisiz erişim mesajı")
    error_code: str = Field("UNAUTHORIZED", description="Yetkisiz erişim hatası kodu")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Yetkisiz erişim",
                "status": "error",
                "timestamp": "2024-01-01T12:00:00Z",
                "error_code": "UNAUTHORIZED",
                "error_details": {
                    "reason": "Invalid or missing token"
                },
                "data": None
            }
        }


class ForbiddenResponse(ErrorResponse):
    """Yasaklı erişim yanıt şeması."""
    message: str = Field("Erişim yasak", description="Yasaklı erişim mesajı")
    error_code: str = Field("FORBIDDEN", description="Yasaklı erişim hatası kodu")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Erişim yasak",
                "status": "error",
                "timestamp": "2024-01-01T12:00:00Z",
                "error_code": "FORBIDDEN",
                "error_details": {
                    "required_permission": "admin",
                    "user_permissions": ["user"]
                },
                "data": None
            }
        }


class RateLimitResponse(ErrorResponse):
    """Rate limit yanıt şeması."""
    message: str = Field("Çok fazla istek", description="Rate limit mesajı")
    error_code: str = Field("RATE_LIMIT_EXCEEDED", description="Rate limit hatası kodu")
    retry_after: int = Field(..., description="Tekrar deneme süresi (saniye)")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Çok fazla istek",
                "status": "error",
                "timestamp": "2024-01-01T12:00:00Z",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "error_details": {
                    "limit": 100,
                    "window": 60,
                    "remaining": 0
                },
                "retry_after": 60,
                "data": None
            }
        }


class ServerErrorResponse(ErrorResponse):
    """Sunucu hatası yanıt şeması."""
    message: str = Field("Sunucu hatası", description="Sunucu hatası mesajı")
    error_code: str = Field("INTERNAL_SERVER_ERROR", description="Sunucu hatası kodu")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Sunucu hatası",
                "status": "error",
                "timestamp": "2024-01-01T12:00:00Z",
                "error_code": "INTERNAL_SERVER_ERROR",
                "error_details": {
                    "error_id": "err_123456789",
                    "support_contact": "support@example.com"
                },
                "data": None
            }
        }
