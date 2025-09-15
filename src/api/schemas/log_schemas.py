"""
Log schemas - Log yönetimi şemaları

Bu modül log yönetimi API'leri için veri şemalarını tanımlar.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    """Log seviyeleri."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry(BaseModel):
    """Log girişi şeması."""
    id: int = Field(..., description="Log ID'si")
    level: LogLevel = Field(..., description="Log seviyesi")
    module: str = Field(..., description="Modül adı")
    message: str = Field(..., description="Log mesajı")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Ek veriler")
    user_id: Optional[int] = Field(None, description="Kullanıcı ID'si")
    ip_address: Optional[str] = Field(None, description="IP adresi")
    created_at: datetime = Field(..., description="Oluşturulma tarihi")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "level": "INFO",
                "module": "auth_service",
                "message": "User login successful",
                "extra_data": {
                    "user_id": 1,
                    "ip_address": "127.0.0.1",
                    "user_agent": "Mozilla/5.0..."
                },
                "user_id": 1,
                "ip_address": "127.0.0.1",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class LogListResponse(BaseModel):
    """Log listesi yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    logs: List[LogEntry] = Field(..., description="Log listesi")
    total: int = Field(..., description="Toplam log sayısı")
    limit: int = Field(..., description="Sayfa başına kayıt sayısı")
    page: int = Field(..., description="Sayfa numarası")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "logs": [
                    {
                        "id": 1,
                        "level": "INFO",
                        "module": "auth_service",
                        "message": "User login successful",
                        "extra_data": {
                            "user_id": 1,
                            "ip_address": "127.0.0.1"
                        },
                        "user_id": 1,
                        "ip_address": "127.0.0.1",
                        "created_at": "2024-01-01T12:00:00Z"
                    }
                ],
                "total": 1000,
                "limit": 100,
                "page": 1
            }
        }


class LogExportRequest(BaseModel):
    """Log dışa aktarma isteği şeması."""
    format: str = Field("json", description="Export formatı")
    start_date: Optional[datetime] = Field(None, description="Başlangıç tarihi")
    end_date: Optional[datetime] = Field(None, description="Bitiş tarihi")
    level: Optional[LogLevel] = Field(None, description="Log seviyesi filtresi")
    module: Optional[str] = Field(None, description="Modül filtresi")
    user_id: Optional[int] = Field(None, description="Kullanıcı ID filtresi")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'csv', 'txt']
        if v not in allowed_formats:
            raise ValueError(f'Format {v} desteklenmiyor. Desteklenen formatlar: {allowed_formats}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "format": "json",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-01T23:59:59Z",
                "level": "ERROR",
                "module": "auth_service"
            }
        }


class LogExportResponse(BaseModel):
    """Log dışa aktarma yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    download_url: str = Field(..., description="İndirme URL'si")
    expires_at: datetime = Field(..., description="URL geçerlilik süresi")
    file_size: Optional[int] = Field(None, description="Dosya boyutu (byte)")
    record_count: Optional[int] = Field(None, description="Kayıt sayısı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "download_url": "/api/v1/logs/download/export_20240101_120000.json",
                "expires_at": "2024-01-01T13:00:00Z",
                "file_size": 1048576,
                "record_count": 1000
            }
        }


class LogStatsResponse(BaseModel):
    """Log istatistikleri yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    stats: Dict[str, Any] = Field(..., description="Log istatistikleri")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "stats": {
                    "total_logs": 10000,
                    "logs_by_level": {
                        "DEBUG": 2000,
                        "INFO": 6000,
                        "WARNING": 1500,
                        "ERROR": 400,
                        "CRITICAL": 100
                    },
                    "logs_by_module": {
                        "auth_service": 3000,
                        "api_server": 2500,
                        "database": 2000,
                        "user_service": 1500,
                        "monitor": 1000
                    },
                    "logs_by_hour": {
                        "00": 100,
                        "01": 80,
                        "02": 60,
                        "12": 500,
                        "13": 600,
                        "14": 550
                    },
                    "error_rate": 0.05,
                    "most_active_users": [
                        {"user_id": 1, "username": "admin", "log_count": 500},
                        {"user_id": 2, "username": "user1", "log_count": 300}
                    ],
                    "period": {
                        "start_date": "2024-01-01T00:00:00Z",
                        "end_date": "2024-01-01T23:59:59Z"
                    }
                }
            }
        }


class LogSearchRequest(BaseModel):
    """Log arama isteği şeması."""
    query: str = Field(..., min_length=1, max_length=200, description="Arama sorgusu")
    level: Optional[LogLevel] = Field(None, description="Log seviyesi filtresi")
    module: Optional[str] = Field(None, description="Modül filtresi")
    start_date: Optional[datetime] = Field(None, description="Başlangıç tarihi")
    end_date: Optional[datetime] = Field(None, description="Bitiş tarihi")
    user_id: Optional[int] = Field(None, description="Kullanıcı ID filtresi")
    ip_address: Optional[str] = Field(None, description="IP adresi filtresi")
    limit: int = Field(100, ge=1, le=1000, description="Maksimum sonuç sayısı")
    offset: int = Field(0, ge=0, description="Başlangıç offset'i")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "login failed",
                "level": "ERROR",
                "module": "auth_service",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-01T23:59:59Z",
                "limit": 50,
                "offset": 0
            }
        }


class LogSearchResponse(BaseModel):
    """Log arama yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    logs: List[LogEntry] = Field(..., description="Arama sonuçları")
    total: int = Field(..., description="Toplam sonuç sayısı")
    query: str = Field(..., description="Arama sorgusu")
    execution_time: float = Field(..., description="Arama süresi (saniye)")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "logs": [
                    {
                        "id": 1,
                        "level": "ERROR",
                        "module": "auth_service",
                        "message": "User login failed",
                        "extra_data": {
                            "username": "invalid_user",
                            "ip_address": "127.0.0.1"
                        },
                        "user_id": None,
                        "ip_address": "127.0.0.1",
                        "created_at": "2024-01-01T12:00:00Z"
                    }
                ],
                "total": 1,
                "query": "login failed",
                "execution_time": 0.15
            }
        }


class LogCleanupRequest(BaseModel):
    """Log temizleme isteği şeması."""
    older_than_days: int = Field(..., ge=1, le=365, description="Kaç günden eski loglar silinsin")
    level: Optional[LogLevel] = Field(None, description="Sadece belirli seviyedeki logları sil")
    module: Optional[str] = Field(None, description="Sadece belirli modüldeki logları sil")
    dry_run: bool = Field(True, description="Sadece simülasyon yap (gerçekten silme)")
    
    class Config:
        schema_extra = {
            "example": {
                "older_than_days": 30,
                "level": "DEBUG",
                "module": "auth_service",
                "dry_run": True
            }
        }


class LogCleanupResponse(BaseModel):
    """Log temizleme yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    deleted_count: int = Field(..., description="Silinen log sayısı")
    freed_space: Optional[int] = Field(None, description="Boşaltılan alan (byte)")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Log temizleme işlemi tamamlandı",
                "deleted_count": 1000,
                "freed_space": 10485760
            }
        }
