"""
Server schemas - Server yönetimi şemaları

Bu modül server yönetimi API'leri için veri şemalarını tanımlar.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ServerStatus(str, Enum):
    """Server durumları."""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


class ServerProtocol(str, Enum):
    """Server protokolleri."""
    HTTP = "http"
    HTTPS = "https"
    WS = "ws"
    WSS = "wss"


class ServerStatusResponse(BaseModel):
    """Server durumu yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    status: Dict[str, Any] = Field(..., description="Server durumu")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "status": {
                    "is_running": True,
                    "host": "127.0.0.1",
                    "port": 8080,
                    "protocol": "HTTP",
                    "ssl_enabled": False,
                    "uptime": 3600,
                    "connections": 5,
                    "last_check": "2024-01-01T12:00:00Z",
                    "status": "running",
                    "pid": 12345,
                    "memory_usage": 52428800,
                    "cpu_usage": 15.5
                }
            }
        }


class ServerConfigRequest(BaseModel):
    """Server yapılandırma isteği şeması."""
    host: Optional[str] = Field(None, description="Host adresi")
    port: Optional[int] = Field(None, ge=1, le=65535, description="Port numarası")
    ssl_enabled: Optional[bool] = Field(None, description="SSL etkin mi")
    ssl_cert_path: Optional[str] = Field(None, description="SSL sertifika yolu")
    ssl_key_path: Optional[str] = Field(None, description="SSL anahtar yolu")
    cors_enabled: Optional[bool] = Field(None, description="CORS etkin mi")
    cors_origins: Optional[List[str]] = Field(None, description="CORS origin'leri")
    rate_limit_enabled: Optional[bool] = Field(None, description="Rate limiting etkin mi")
    rate_limit_requests: Optional[int] = Field(None, ge=1, description="Rate limit istek sayısı")
    rate_limit_window: Optional[int] = Field(None, ge=1, description="Rate limit pencere süresi (saniye)")
    max_request_size: Optional[int] = Field(None, ge=1024, description="Maksimum istek boyutu (byte)")
    keepalive_timeout: Optional[int] = Field(None, ge=1, description="Keep-alive timeout (saniye)")
    
    @validator('port')
    def validate_port(cls, v):
        if v is not None and (v < 1 or v > 65535):
            raise ValueError('Port numarası 1-65535 arasında olmalıdır')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "host": "0.0.0.0",
                "port": 8080,
                "ssl_enabled": False,
                "cors_enabled": True,
                "cors_origins": ["http://localhost:3000"],
                "rate_limit_enabled": True,
                "rate_limit_requests": 100,
                "rate_limit_window": 60,
                "max_request_size": 10485760,
                "keepalive_timeout": 65
            }
        }


class ServerConfigResponse(BaseModel):
    """Server yapılandırma yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    config: Dict[str, Any] = Field(..., description="Server yapılandırması")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "config": {
                    "host": "127.0.0.1",
                    "port": 8080,
                    "ssl_enabled": False,
                    "ssl_cert_path": None,
                    "ssl_key_path": None,
                    "cors_enabled": True,
                    "cors_origins": ["*"],
                    "rate_limit_enabled": True,
                    "rate_limit_requests": 100,
                    "rate_limit_window": 60,
                    "max_request_size": 10485760,
                    "keepalive_timeout": 65,
                    "worker_processes": 1,
                    "worker_connections": 1000
                }
            }
        }


class ServerStartResponse(BaseModel):
    """Server başlatma yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    server_info: Optional[Dict[str, Any]] = Field(None, description="Server bilgileri")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Server başarıyla başlatıldı",
                "server_info": {
                    "host": "127.0.0.1",
                    "port": 8080,
                    "protocol": "HTTP",
                    "pid": 12345,
                    "started_at": "2024-01-01T12:00:00Z"
                }
            }
        }


class ServerStopResponse(BaseModel):
    """Server durdurma yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    stopped_at: Optional[datetime] = Field(None, description="Durdurulma zamanı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Server başarıyla durduruldu",
                "stopped_at": "2024-01-01T12:00:00Z"
            }
        }


class ServerRestartResponse(BaseModel):
    """Server yeniden başlatma yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    restart_info: Optional[Dict[str, Any]] = Field(None, description="Yeniden başlatma bilgileri")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Server başarıyla yeniden başlatıldı",
                "restart_info": {
                    "stopped_at": "2024-01-01T12:00:00Z",
                    "started_at": "2024-01-01T12:00:05Z",
                    "restart_duration": 5.2,
                    "new_pid": 12346
                }
            }
        }


class ServerMetricsResponse(BaseModel):
    """Server metrikleri yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    metrics: Dict[str, Any] = Field(..., description="Server metrikleri")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "metrics": {
                    "uptime": 3600,
                    "total_requests": 1000,
                    "active_connections": 5,
                    "memory_usage": 52428800,
                    "cpu_usage": 15.5,
                    "request_rate": 2.5,
                    "response_time_avg": 150.5,
                    "error_rate": 0.02,
                    "ssl_connections": 0,
                    "last_request": "2024-01-01T12:00:00Z"
                }
            }
        }


class ServerHealthResponse(BaseModel):
    """Server sağlık durumu yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    health: Dict[str, Any] = Field(..., description="Sağlık durumu")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "health": {
                    "status": "healthy",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "version": "1.0.0",
                    "uptime": 3600,
                    "checks": {
                        "database": "healthy",
                        "memory": "healthy",
                        "disk": "healthy",
                        "network": "healthy"
                    }
                }
            }
        }
