"""
Configuration schemas - Yapılandırma şemaları

Bu modül yapılandırma API'leri için veri şemalarını tanımlar.
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ConfigDataType(str, Enum):
    """Yapılandırma veri türleri."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY = "array"


class ConfigBase(BaseModel):
    """Temel yapılandırma şeması."""
    category: str = Field(..., min_length=1, max_length=50, description="Kategori")
    key: str = Field(..., min_length=1, max_length=100, description="Anahtar")
    value: Union[str, int, float, bool, Dict, List] = Field(..., description="Değer")
    data_type: ConfigDataType = Field(ConfigDataType.STRING, description="Veri türü")
    description: Optional[str] = Field(None, max_length=500, description="Açıklama")
    is_encrypted: bool = Field(False, description="Şifrelenmiş mi")
    
    class Config:
        schema_extra = {
            "example": {
                "category": "server",
                "key": "port",
                "value": 8080,
                "data_type": "integer",
                "description": "Server port numarası",
                "is_encrypted": False
            }
        }


class ConfigCreate(ConfigBase):
    """Yapılandırma oluşturma şeması."""
    pass


class ConfigUpdate(BaseModel):
    """Yapılandırma güncelleme şeması."""
    value: Union[str, int, float, bool, Dict, List] = Field(..., description="Yeni değer")
    description: Optional[str] = Field(None, max_length=500, description="Açıklama")
    
    class Config:
        schema_extra = {
            "example": {
                "value": 8081,
                "description": "Güncellenmiş port numarası"
            }
        }


class ConfigResponse(ConfigBase):
    """Yapılandırma yanıt şeması."""
    id: int = Field(..., description="Yapılandırma ID'si")
    created_at: datetime = Field(..., description="Oluşturulma tarihi")
    updated_at: datetime = Field(..., description="Güncellenme tarihi")
    updated_by: Optional[int] = Field(None, description="Güncelleyen kullanıcı ID'si")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "category": "server",
                "key": "port",
                "value": 8080,
                "data_type": "integer",
                "description": "Server port numarası",
                "is_encrypted": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "updated_by": 1
            }
        }


class ConfigListResponse(BaseModel):
    """Yapılandırma listesi yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    configs: List[ConfigResponse] = Field(..., description="Yapılandırma listesi")
    total: int = Field(..., description="Toplam kayıt sayısı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "configs": [
                    {
                        "id": 1,
                        "category": "server",
                        "key": "port",
                        "value": 8080,
                        "data_type": "integer",
                        "description": "Server port numarası",
                        "is_encrypted": False,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                        "updated_by": 1
                    }
                ],
                "total": 1
            }
        }


class ConfigCategoryResponse(BaseModel):
    """Kategori bazlı yapılandırma yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    category: str = Field(..., description="Kategori adı")
    configs: Dict[str, Any] = Field(..., description="Kategori yapılandırmaları")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "category": "server",
                "configs": {
                    "host": "127.0.0.1",
                    "port": 8080,
                    "ssl_enabled": False,
                    "cors_enabled": True,
                    "rate_limit_enabled": True,
                    "rate_limit_requests": 100,
                    "rate_limit_window": 60
                }
            }
        }


class ConfigBulkUpdateRequest(BaseModel):
    """Toplu yapılandırma güncelleme şeması."""
    configs: Dict[str, Dict[str, Any]] = Field(..., description="Kategori bazlı yapılandırmalar")
    
    class Config:
        schema_extra = {
            "example": {
                "configs": {
                    "server": {
                        "port": 8081,
                        "ssl_enabled": True
                    },
                    "security": {
                        "jwt_expiration": 7200,
                        "password_min_length": 12
                    }
                }
            }
        }


class ConfigBulkUpdateResponse(BaseModel):
    """Toplu yapılandırma güncelleme yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    updated_count: int = Field(..., description="Güncellenen kayıt sayısı")
    failed_updates: List[Dict[str, Any]] = Field(default_factory=list, description="Başarısız güncellemeler")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Yapılandırmalar başarıyla güncellendi",
                "updated_count": 5,
                "failed_updates": []
            }
        }
