"""
Base Routes module - Temel route sınıfı

Bu modül temel route sınıfını ve yardımcı fonksiyonları içerir.
"""

from typing import Dict, Any, List, Optional
from aiohttp import web
from aiohttp.web import Request, Response

from ...core.constants import API_PREFIX, SUCCESS_MESSAGES
from ...utils.logger import Logger


class BaseRoutes:
    """Temel route sınıfı"""
    
    def __init__(self):
        """BaseRoutes'ı başlat"""
        self.logger = Logger(__name__)
    
    def get_routes(self) -> List[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.get("/", self.root),
            web.get(f"{API_PREFIX}/health", self.health_check),
            web.get(f"{API_PREFIX}/status", self.status),
            web.get(f"{API_PREFIX}/info", self.info),
            web.get(f"{API_PREFIX}/version", self.version),
            web.get(f"{API_PREFIX}/ping", self.ping),
            web.get(f"{API_PREFIX}/metrics", self.get_metrics),
        ]
    
    async def root(self, request: Request) -> Response:
        """
        Root endpoint
        
        Args:
            request: Request objesi
            
        Returns:
            Root response
        """
        try:
            return self.create_success_response(
                message="API Server Management System",
                data={
                    "version": "1.0.0",
                    "status": "running",
                    "endpoints": {
                        "health": f"{API_PREFIX}/health",
                        "status": f"{API_PREFIX}/status",
                        "info": f"{API_PREFIX}/info",
                        "version": f"{API_PREFIX}/version"
                    }
                }
            )
        except Exception as e:
            self.logger.error(f"Root endpoint error: {e}")
            return self.create_error_response(f"Root endpoint error: {e}")
    
    async def health_check(self, request: Request) -> Response:
        """
        Health check endpoint
        
        Args:
            request: Request objesi
            
        Returns:
            Health check response
        """
        try:
            # Temel sağlık kontrolü
            health_data = {
                "status": "healthy",
                "timestamp": self._get_timestamp(),
                "uptime": self._get_uptime(),
                "version": self._get_version()
            }
            
            # Veritabanı bağlantısını kontrol et
            try:
                from ...db.database import db_manager
                health_data["database"] = {
                    "status": "connected" if not db_manager.database.is_closed() else "disconnected"
                }
            except Exception as e:
                health_data["database"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            return web.json_response(health_data)
            
        except Exception as e:
            self.logger.error(f"Health check hatası: {e}")
            return web.json_response(
                {"status": "unhealthy", "error": str(e)},
                status=500
            )
    
    async def status(self, request: Request) -> Response:
        """
        Status endpoint
        
        Args:
            request: Request objesi
            
        Returns:
            Status response
        """
        try:
            # API server durumunu al
            from ...api.server_manager import api_server_manager
            server_status = api_server_manager.get_status()
            
            # Veritabanı bilgilerini al
            try:
                from ...db.database import db_manager
                db_info = db_manager.get_database_info()
            except Exception as db_e:
                self.logger.warning(f"Database info alınamadı: {db_e}")
                db_info = {"status": "unknown", "error": str(db_e)}
            
            status_data = {
                "api_server": server_status,
                "database": db_info,
                "timestamp": self._get_timestamp()
            }
            
            return self.create_success_response(
                data=status_data,
                message="Sistem durumu alındı"
            )
            
        except Exception as e:
            self.logger.error(f"Status endpoint hatası: {e}")
            return self.create_error_response(
                message=f"Status endpoint hatası: {e}",
                status_code=500
            )
    
    async def info(self, request: Request) -> Response:
        """
        Info endpoint
        
        Args:
            request: Request objesi
            
        Returns:
            Info response
        """
        try:
            info_data = {
                "app_name": self._get_app_name(),
                "version": self._get_version(),
                "description": self._get_description(),
                "author": self._get_author(),
                "api_version": "v1",
                "endpoints": self._get_available_endpoints(),
                "features": self._get_enabled_features(),
                "timestamp": self._get_timestamp()
            }
            
            return self.create_success_response(
                data=info_data,
                message="Sistem bilgileri alındı"
            )
            
        except Exception as e:
            self.logger.error(f"Info endpoint hatası: {e}")
            return self.create_error_response(
                message=f"Info endpoint hatası: {e}",
                status_code=500
            )
    
    async def version(self, request: Request) -> Response:
        """
        Version endpoint
        
        Args:
            request: Request objesi
            
        Returns:
            Version response
        """
        try:
            version_data = {
                "version": self._get_version(),
                "api_version": "v1",
                "build_date": self._get_build_date(),
                "python_version": self._get_python_version(),
                "timestamp": self._get_timestamp()
            }
            
            return self.create_success_response(
                data=version_data,
                message="Versiyon bilgileri alındı"
            )
            
        except Exception as e:
            self.logger.error(f"Version endpoint hatası: {e}")
            return self.create_error_response(
                message=f"Version endpoint hatası: {e}",
                status_code=500
            )
    
    def _get_timestamp(self) -> str:
        """Timestamp al"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_uptime(self) -> float:
        """Uptime al"""
        import time
        # Uygulama başlangıç zamanını al (basit implementasyon)
        return time.time() - getattr(self, '_start_time', time.time())
    
    def _get_version(self) -> str:
        """Versiyon al"""
        from ...core.constants import APP_VERSION
        return APP_VERSION
    
    def _get_app_name(self) -> str:
        """Uygulama adını al"""
        from ...core.constants import APP_NAME
        return APP_NAME
    
    def _get_description(self) -> str:
        """Açıklama al"""
        from ...core.constants import APP_DESCRIPTION
        return APP_DESCRIPTION
    
    def _get_author(self) -> str:
        """Yazar al"""
        from ...core.constants import APP_AUTHOR
        return APP_AUTHOR
    
    def _get_build_date(self) -> str:
        """Build tarihi al"""
        import os
        from datetime import datetime
        
        # Basit build tarihi (dosya oluşturma tarihi)
        try:
            build_time = os.path.getctime(__file__)
            return datetime.fromtimestamp(build_time).isoformat()
        except:
            return datetime.now().isoformat()
    
    def _get_python_version(self) -> str:
        """Python versiyonu al"""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def _get_available_endpoints(self) -> List[Dict[str, str]]:
        """Mevcut endpoint'leri al"""
        return [
            {"method": "GET", "path": f"{API_PREFIX}/health", "description": "Health check"},
            {"method": "GET", "path": f"{API_PREFIX}/status", "description": "System status"},
            {"method": "GET", "path": f"{API_PREFIX}/info", "description": "System info"},
            {"method": "GET", "path": f"{API_PREFIX}/version", "description": "Version info"},
            {"method": "POST", "path": f"{API_PREFIX}/auth/login", "description": "User login"},
            {"method": "POST", "path": f"{API_PREFIX}/auth/logout", "description": "User logout"},
            {"method": "GET", "path": f"{API_PREFIX}/users", "description": "User list"},
            {"method": "GET", "path": f"{API_PREFIX}/server/status", "description": "Server status"},
            {"method": "GET", "path": f"{API_PREFIX}/monitor/system", "description": "System metrics"},
        ]
    
    def _get_enabled_features(self) -> Dict[str, bool]:
        """Etkin özellikleri al"""
        try:
            from ...core.settings import settings
            return settings.get_feature_config()
        except Exception as e:
            self.logger.warning(f"Feature config alınamadı: {e}")
            return {
                "authentication": True,
                "user_management": True,
                "server_control": True,
                "monitoring": True,
                "logging": True,
                "backup": True
            }
    
    def create_success_response(self, data: Any = None, message: str = None) -> Response:
        """
        Başarı response'u oluştur
        
        Args:
            data: Response verisi
            message: Başarı mesajı
            
        Returns:
            Success response
        """
        response_data = {
            "success": True,
            "timestamp": self._get_timestamp()
        }
        
        if message:
            response_data["message"] = message
        
        if data is not None:
            response_data["data"] = data
        
        return web.json_response(response_data)
    
    def create_error_response(self, message: str, status_code: int = 400, 
                            error_code: str = None, details: Any = None) -> Response:
        """
        Hata response'u oluştur
        
        Args:
            message: Hata mesajı
            status_code: HTTP status kodu
            error_code: Hata kodu
            details: Hata detayları
            
        Returns:
            Error response
        """
        response_data = {
            "success": False,
            "error": {
                "message": message,
                "timestamp": self._get_timestamp()
            }
        }
        
        if error_code:
            response_data["error"]["code"] = error_code
        
        if details:
            response_data["error"]["details"] = details
        
        return web.json_response(response_data, status=status_code)
    
    def create_paginated_response(self, data: List[Any], page: int, 
                                page_size: int, total: int) -> Response:
        """
        Sayfalanmış response oluştur
        
        Args:
            data: Veri listesi
            page: Sayfa numarası
            page_size: Sayfa boyutu
            total: Toplam kayıt sayısı
            
        Returns:
            Paginated response
        """
        total_pages = (total + page_size - 1) // page_size
        
        response_data = {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "timestamp": self._get_timestamp()
        }
        
        return web.json_response(response_data)
    
    def get_pagination_params(self, request: Request) -> tuple[int, int]:
        """
        Sayfalama parametrelerini al
        
        Args:
            request: Request objesi
            
        Returns:
            (page, page_size) tuple
        """
        try:
            page = int(request.query.get('page', 1))
            page_size = int(request.query.get('page_size', 20))
            
            # Sınırları kontrol et
            page = max(1, page)
            page_size = max(1, min(page_size, 100))  # Max 100
            
            return page, page_size
            
        except (ValueError, TypeError):
            return 1, 20
    
    def get_sort_params(self, request: Request) -> tuple[str, str]:
        """
        Sıralama parametrelerini al
        
        Args:
            request: Request objesi
            
        Returns:
            (sort_field, sort_order) tuple
        """
        sort_field = request.query.get('sort', 'id')
        sort_order = request.query.get('order', 'asc')
        
        # Sıralama yönünü kontrol et
        if sort_order.lower() not in ['asc', 'desc']:
            sort_order = 'asc'
        
        return sort_field, sort_order
    
    async def ping(self, request: Request) -> Response:
        """
        Ping endpoint - Basit bağlantı testi
        
        Args:
            request: Request objesi
            
        Returns:
            Ping response
        """
        try:
            ping_data = {
                "status": "pong",
                "timestamp": self._get_timestamp(),
                "server_time": self._get_timestamp(),
                "uptime": self._get_uptime()
            }
            
            return self.create_success_response(
                data=ping_data,
                message="Ping başarılı"
            )
            
        except Exception as e:
            self.logger.error(f"Ping endpoint hatası: {e}")
            return self.create_error_response(
                message=f"Ping endpoint hatası: {e}",
                status_code=500
            )
    
    async def get_metrics(self, request: Request) -> Response:
        """
        Metrics endpoint - Sistem metrikleri
        
        Args:
            request: Request objesi
            
        Returns:
            Metrics response
        """
        try:
            # Temel sistem metrikleri
            import psutil
            
            # CPU metrikleri
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrikleri
            memory = psutil.virtual_memory()
            
            # Disk metrikleri
            disk = psutil.disk_usage('/')
            
            # Network metrikleri
            network = psutil.net_io_counters()
            
            metrics_data = {
                "timestamp": self._get_timestamp(),
                "system": {
                    "cpu": {
                        "percent": cpu_percent,
                        "count": cpu_count,
                        "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
                    },
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "used": memory.used,
                        "percent": memory.percent
                    },
                    "disk": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "percent": (disk.used / disk.total) * 100
                    },
                    "network": {
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv
                    }
                },
                "application": {
                    "uptime": self._get_uptime(),
                    "version": self._get_version(),
                    "python_version": self._get_python_version()
                }
            }
            
            return self.create_success_response(
                data=metrics_data,
                message="Sistem metrikleri alındı"
            )
            
        except Exception as e:
            self.logger.error(f"Metrics endpoint hatası: {e}")
            return self.create_error_response(
                message=f"Metrics endpoint hatası: {e}",
                status_code=500
            )
