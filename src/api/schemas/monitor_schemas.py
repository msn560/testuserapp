"""
Monitoring schemas - İzleme şemaları

Bu modül sistem izleme API'leri için veri şemalarını tanımlar.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class AlertSeverity(str, Enum):
    """Alert önem seviyeleri."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Alert türleri."""
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"
    APPLICATION = "application"
    DATABASE = "database"
    NETWORK = "network"


class SystemMetricsResponse(BaseModel):
    """Sistem metrikleri yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    metrics: Dict[str, Any] = Field(..., description="Sistem metrikleri")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "metrics": {
                    "cpu": {
                        "total_percent": 45.2,
                        "cores": [30.1, 60.3, 45.2, 35.8],
                        "load_average": [1.2, 1.5, 1.8]
                    },
                    "memory": {
                        "total": 8589934592,
                        "available": 4294967296,
                        "used": 4294967296,
                        "percent": 50.0,
                        "cached": 1073741824,
                        "buffers": 536870912
                    },
                    "disk": {
                        "total": 100000000000,
                        "used": 50000000000,
                        "free": 50000000000,
                        "percent": 50.0,
                        "read_bytes": 1024000,
                        "write_bytes": 2048000
                    },
                    "network": {
                        "bytes_sent": 1024000,
                        "bytes_recv": 2048000,
                        "packets_sent": 1000,
                        "packets_recv": 1200,
                        "errors_in": 0,
                        "errors_out": 0
                    },
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }


class DatabaseMetricsResponse(BaseModel):
    """Veritabanı metrikleri yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    database: Dict[str, Any] = Field(..., description="Veritabanı durumu")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "database": {
                    "is_connected": True,
                    "connection_count": 5,
                    "active_queries": 2,
                    "table_sizes": {
                        "users": 1000,
                        "sessions": 50,
                        "logs": 10000,
                        "config": 25
                    },
                    "query_performance": {
                        "average_time": 15.5,
                        "slow_queries": 2,
                        "total_queries": 1000,
                        "cache_hit_ratio": 0.95
                    },
                    "storage": {
                        "database_size": 10485760,
                        "index_size": 2097152,
                        "free_space": 1073741824
                    },
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }


class ApiMetricsResponse(BaseModel):
    """API metrikleri yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    api_metrics: Dict[str, Any] = Field(..., description="API metrikleri")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "api_metrics": {
                    "total_requests": 1000,
                    "successful_requests": 950,
                    "failed_requests": 50,
                    "average_response_time": 150.5,
                    "requests_per_minute": 10.5,
                    "endpoints": {
                        "/api/v1/auth/login": {
                            "requests": 100,
                            "average_time": 200.0,
                            "error_rate": 5.0,
                            "last_request": "2024-01-01T12:00:00Z"
                        },
                        "/api/v1/users": {
                            "requests": 200,
                            "average_time": 120.0,
                            "error_rate": 2.0,
                            "last_request": "2024-01-01T12:00:00Z"
                        }
                    },
                    "status_codes": {
                        "200": 950,
                        "400": 30,
                        "401": 15,
                        "500": 5
                    },
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }


class AlertResponse(BaseModel):
    """Alert yanıt şeması."""
    id: int = Field(..., description="Alert ID'si")
    type: AlertType = Field(..., description="Alert türü")
    severity: AlertSeverity = Field(..., description="Önem seviyesi")
    title: str = Field(..., description="Alert başlığı")
    message: str = Field(..., description="Alert mesajı")
    is_resolved: bool = Field(False, description="Çözüldü mü")
    created_at: datetime = Field(..., description="Oluşturulma tarihi")
    resolved_at: Optional[datetime] = Field(None, description="Çözülme tarihi")
    resolved_by: Optional[int] = Field(None, description="Çözen kullanıcı ID'si")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Ek bilgiler")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "type": "system",
                "severity": "high",
                "title": "High CPU Usage",
                "message": "CPU usage is above 80%",
                "is_resolved": False,
                "created_at": "2024-01-01T12:00:00Z",
                "resolved_at": None,
                "resolved_by": None,
                "metadata": {
                    "cpu_percent": 85.2,
                    "threshold": 80.0,
                    "duration": 300
                }
            }
        }


class AlertListResponse(BaseModel):
    """Alert listesi yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    alerts: List[AlertResponse] = Field(..., description="Alert listesi")
    total: int = Field(..., description="Toplam alert sayısı")
    unresolved_count: int = Field(..., description="Çözülmemiş alert sayısı")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "alerts": [
                    {
                        "id": 1,
                        "type": "system",
                        "severity": "high",
                        "title": "High CPU Usage",
                        "message": "CPU usage is above 80%",
                        "is_resolved": False,
                        "created_at": "2024-01-01T12:00:00Z",
                        "resolved_at": None,
                        "resolved_by": None,
                        "metadata": {
                            "cpu_percent": 85.2,
                            "threshold": 80.0
                        }
                    }
                ],
                "total": 1,
                "unresolved_count": 1
            }
        }


class AlertResolveRequest(BaseModel):
    """Alert çözümleme isteği şeması."""
    resolution: str = Field(..., min_length=1, max_length=500, description="Çözüm açıklaması")
    
    class Config:
        schema_extra = {
            "example": {
                "resolution": "CPU usage normalized after system optimization"
            }
        }


class AlertResolveResponse(BaseModel):
    """Alert çözümleme yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    message: str = Field(..., description="İşlem mesajı")
    resolved_at: datetime = Field(..., description="Çözülme tarihi")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Alert başarıyla çözüldü",
                "resolved_at": "2024-01-01T12:00:00Z"
            }
        }


class SystemHealthResponse(BaseModel):
    """Sistem sağlık durumu yanıt şeması."""
    success: bool = Field(True, description="İşlem başarılı mı")
    health: Dict[str, Any] = Field(..., description="Sistem sağlık durumu")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "health": {
                    "overall_status": "healthy",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "components": {
                        "database": {
                            "status": "healthy",
                            "response_time": 15.5,
                            "last_check": "2024-01-01T12:00:00Z"
                        },
                        "api": {
                            "status": "healthy",
                            "response_time": 120.0,
                            "last_check": "2024-01-01T12:00:00Z"
                        },
                        "storage": {
                            "status": "healthy",
                            "free_space_percent": 50.0,
                            "last_check": "2024-01-01T12:00:00Z"
                        },
                        "network": {
                            "status": "healthy",
                            "latency": 5.2,
                            "last_check": "2024-01-01T12:00:00Z"
                        }
                    },
                    "active_alerts": 0,
                    "uptime": 3600
                }
            }
        }
