"""
Monitor Routes module - Monitoring endpoint'leri

Bu modül sistem izleme ile ilgili API endpoint'lerini içerir.
"""

import psutil
import time
from typing import Dict, Any, List, Optional
from aiohttp import web
from aiohttp.web import Request, Response

from .base_routes import BaseRoutes
from ...core.constants import API_PREFIX, SUCCESS_MESSAGES, ERROR_MESSAGES
from ...api.schemas.monitor_schemas import (
    SystemMetricsResponse, DatabaseMetricsResponse, ApiMetricsResponse,
    AlertResponse, AlertListResponse, AlertResolveRequest, AlertResolveResponse,
    SystemHealthResponse
)


class MonitorRoutes(BaseRoutes):
    """Monitor routes sınıfı"""
    
    def __init__(self):
        """MonitorRoutes'ı başlat"""
        super().__init__()
    
    def get_routes(self) -> list[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.get(f"{API_PREFIX}/monitor/system", self.get_system_metrics),
            web.get(f"{API_PREFIX}/monitor/database", self.get_database_metrics),
            web.get(f"{API_PREFIX}/monitor/api", self.get_api_metrics),
            web.get(f"{API_PREFIX}/monitor/health", self.get_system_health),
            web.get(f"{API_PREFIX}/monitor/alerts", self.get_alerts),
            web.post(f"{API_PREFIX}/monitor/alerts/{{alert_id}}/resolve", self.resolve_alert),
            web.get(f"{API_PREFIX}/monitor/performance", self.get_performance_metrics),
            web.get(f"{API_PREFIX}/monitor/uptime", self.get_uptime_metrics),
        ]
    
    async def get_system_metrics(self, request: Request) -> Response:
        """Sistem metrikleri"""
        try:
            # CPU metrikleri
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Memory metrikleri
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
                "cached": getattr(memory, 'cached', 0),
                "buffers": getattr(memory, 'buffers', 0)
            }
            
            # Disk metrikleri
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            disk_info = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100,
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0
            }
            
            # Network metrikleri
            network_io = psutil.net_io_counters()
            network_info = {
                "bytes_sent": network_io.bytes_sent if network_io else 0,
                "bytes_recv": network_io.bytes_recv if network_io else 0,
                "packets_sent": network_io.packets_sent if network_io else 0,
                "packets_recv": network_io.packets_recv if network_io else 0,
                "errors_in": network_io.errin if network_io else 0,
                "errors_out": network_io.errout if network_io else 0
            }
            
            metrics = {
                "cpu": {
                    "total_percent": cpu_percent,
                    "cores": cpu_per_core,
                    "load_average": list(load_avg)
                },
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info,
                "timestamp": time.time()
            }
            
            return self.create_success_response(
                message="Sistem metrikleri alındı",
                data=metrics
            )
            
        except Exception as e:
            self.logger.error(f"Sistem metrikleri alınamadı: {e}")
            return self.create_error_response(
                message="Sistem metrikleri alınamadı",
                status_code=500
            )
    
    async def get_database_metrics(self, request: Request) -> Response:
        """Veritabanı metrikleri"""
        try:
            # Veritabanı bağlantısını kontrol et
            from ...db.database import db_manager
            
            # Temel veritabanı bilgileri
            is_connected = db_manager.is_connected()
            connection_count = 1 if is_connected else 0
            
            # Tablo boyutları (örnek)
            table_sizes = {
                "users": 0,
                "sessions": 0,
                "logs": 0,
                "config": 0
            }
            
            # Query performance (örnek)
            query_performance = {
                "average_time": 15.5,
                "slow_queries": 0,
                "total_queries": 0,
                "cache_hit_ratio": 0.95
            }
            
            # Storage bilgileri
            storage = {
                "database_size": 0,
                "index_size": 0,
                "free_space": 0
            }
            
            database_info = {
                "is_connected": is_connected,
                "connection_count": connection_count,
                "active_queries": 0,
                "table_sizes": table_sizes,
                "query_performance": query_performance,
                "storage": storage,
                "timestamp": time.time()
            }
            
            return self.create_success_response(
                message="Veritabanı metrikleri alındı",
                data=database_info
            )
            
        except Exception as e:
            self.logger.error(f"Veritabanı metrikleri alınamadı: {e}")
            return self.create_error_response(
                message="Veritabanı metrikleri alınamadı",
                status_code=500
            )
    
    async def get_api_metrics(self, request: Request) -> Response:
        """API metrikleri"""
        try:
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # API istatistiklerini al
            detailed_stats = server_manager.get_detailed_stats()
            endpoint_stats = server_manager.get_endpoint_stats()
            
            # Toplam istek sayısı
            total_requests = detailed_stats.get("server", {}).get("total_requests", 0)
            error_count = detailed_stats.get("server", {}).get("error_count", 0)
            successful_requests = total_requests - error_count
            
            # Response time
            avg_response_time = detailed_stats.get("server", {}).get("avg_response_time", 0)
            requests_per_minute = detailed_stats.get("server", {}).get("requests_per_minute", 0)
            
            # Endpoint istatistikleri
            endpoints = {}
            if endpoint_stats and "endpoints" in endpoint_stats:
                for endpoint in endpoint_stats["endpoints"]:
                    endpoints[endpoint["path"]] = {
                        "requests": endpoint["count"],
                        "average_time": endpoint["avg_time"],
                        "error_rate": endpoint["error_rate"]
                    }
            
            # Status code dağılımı (örnek)
            status_codes = {
                "200": successful_requests,
                "400": error_count // 2,
                "401": error_count // 4,
                "500": error_count // 4
            }
            
            api_metrics = {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": error_count,
                "average_response_time": avg_response_time,
                "requests_per_minute": requests_per_minute,
                "endpoints": endpoints,
                "status_codes": status_codes,
                "timestamp": time.time()
            }
            
            return self.create_success_response(
                message="API metrikleri alındı",
                data=api_metrics
            )
            
        except Exception as e:
            self.logger.error(f"API metrikleri alınamadı: {e}")
            return self.create_error_response(
                message="API metrikleri alınamadı",
                status_code=500
            )
    
    async def get_system_health(self, request: Request) -> Response:
        """Sistem sağlık durumu"""
        try:
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # Server sağlık durumunu al
            health = server_manager.get_server_health()
            
            return self.create_success_response(
                message="Sistem sağlık durumu alındı",
                data=health
            )
            
        except Exception as e:
            self.logger.error(f"Sistem sağlık durumu alınamadı: {e}")
            return self.create_error_response(
                message="Sistem sağlık durumu alınamadı",
                status_code=500
            )
    
    async def get_alerts(self, request: Request) -> Response:
        """Aktif alert'leri getir"""
        try:
            # Query parametrelerini al
            severity = request.query.get('severity')
            type_filter = request.query.get('type')
            resolved = request.query.get('resolved', 'false').lower() == 'true'
            
            # Örnek alert verileri (gerçek uygulamada veritabanından alınır)
            alerts = [
                {
                    "id": 1,
                    "type": "system",
                    "severity": "high",
                    "title": "High CPU Usage",
                    "message": "CPU usage is above 80%",
                    "is_resolved": False,
                    "created_at": time.time() - 3600,
                    "resolved_at": None,
                    "resolved_by": None,
                    "metadata": {
                        "cpu_percent": 85.2,
                        "threshold": 80.0
                    }
                }
            ]
            
            # Filtreleme
            if severity:
                alerts = [a for a in alerts if a["severity"] == severity]
            if type_filter:
                alerts = [a for a in alerts if a["type"] == type_filter]
            if resolved is not None:
                alerts = [a for a in alerts if a["is_resolved"] == resolved]
            
            # Çözülmemiş alert sayısı
            unresolved_count = len([a for a in alerts if not a["is_resolved"]])
            
            response_data = {
                "alerts": alerts,
                "total": len(alerts),
                "unresolved_count": unresolved_count
            }
            
            return self.create_success_response(
                message="Alert'ler alındı",
                data=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Alert'ler alınamadı: {e}")
            return self.create_error_response(
                message="Alert'ler alınamadı",
                status_code=500
            )
    
    async def resolve_alert(self, request: Request) -> Response:
        """Alert'i çöz"""
        try:
            # Alert ID'yi al
            alert_id = int(request.match_info['alert_id'])
            
            # Request body'yi al
            data = await request.json()
            resolution = data.get('resolution', '')
            
            if not resolution:
                return self.create_error_response(
                    message="Çözüm açıklaması gerekli",
                    status_code=400
                )
            
            # Kullanıcı ID'sini al
            user_id = getattr(request, 'user_id', None)
            
            # Alert'i çöz (gerçek uygulamada veritabanında güncellenir)
            resolved_at = time.time()
            
            response_data = {
                "resolved_at": resolved_at,
                "resolved_by": user_id,
                "resolution": resolution
            }
            
            return self.create_success_response(
                message="Alert başarıyla çözüldü",
                data=response_data
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz alert ID",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Alert çözülemedi: {e}")
            return self.create_error_response(
                message="Alert çözülemedi",
                status_code=500
            )
    
    async def get_performance_metrics(self, request: Request) -> Response:
        """Performance metrikleri"""
        try:
            import psutil
            
            # CPU performance
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_times = psutil.cpu_times()
            
            # Memory performance
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk performance
            disk_io = psutil.disk_io_counters()
            disk_usage = psutil.disk_usage('/')
            
            # Network performance
            network_io = psutil.net_io_counters()
            
            # Process performance
            process_count = len(psutil.pids())
            
            performance_data = {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "frequency": {
                        "current": cpu_freq.current if cpu_freq else 0,
                        "min": cpu_freq.min if cpu_freq else 0,
                        "max": cpu_freq.max if cpu_freq else 0
                    },
                    "times": {
                        "user": cpu_times.user,
                        "system": cpu_times.system,
                        "idle": cpu_times.idle
                    }
                },
                "memory": {
                    "virtual": {
                        "total": memory.total,
                        "available": memory.available,
                        "used": memory.used,
                        "percent": memory.percent
                    },
                    "swap": {
                        "total": swap.total,
                        "used": swap.used,
                        "free": swap.free,
                        "percent": swap.percent
                    }
                },
                "disk": {
                    "io": {
                        "read_count": disk_io.read_count if disk_io else 0,
                        "write_count": disk_io.write_count if disk_io else 0,
                        "read_bytes": disk_io.read_bytes if disk_io else 0,
                        "write_bytes": disk_io.write_bytes if disk_io else 0
                    },
                    "usage": {
                        "total": disk_usage.total,
                        "used": disk_usage.used,
                        "free": disk_usage.free,
                        "percent": (disk_usage.used / disk_usage.total) * 100
                    }
                },
                "network": {
                    "bytes_sent": network_io.bytes_sent if network_io else 0,
                    "bytes_recv": network_io.bytes_recv if network_io else 0,
                    "packets_sent": network_io.packets_sent if network_io else 0,
                    "packets_recv": network_io.packets_recv if network_io else 0
                },
                "processes": {
                    "total": process_count,
                    "running": len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running'])
                },
                "timestamp": time.time()
            }
            
            return self.create_success_response(
                message="Performance metrikleri alındı",
                data=performance_data
            )
            
        except Exception as e:
            self.logger.error(f"Performance metrikleri alınamadı: {e}")
            return self.create_error_response(
                message="Performance metrikleri alınamadı",
                status_code=500
            )
    
    async def get_uptime_metrics(self, request: Request) -> Response:
        """Uptime metrikleri"""
        try:
            import psutil
            
            # Sistem uptime
            boot_time = psutil.boot_time()
            current_time = time.time()
            system_uptime = current_time - boot_time
            
            # Uygulama uptime (basit implementasyon)
            app_start_time = getattr(self, '_app_start_time', current_time)
            app_uptime = current_time - app_start_time
            
            # Uptime formatları
            def format_uptime(seconds):
                days = int(seconds // 86400)
                hours = int((seconds % 86400) // 3600)
                minutes = int((seconds % 3600) // 60)
                return f"{days}d {hours}h {minutes}m"
            
            uptime_data = {
                "system": {
                    "uptime_seconds": system_uptime,
                    "uptime_formatted": format_uptime(system_uptime),
                    "boot_time": boot_time,
                    "boot_time_formatted": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(boot_time))
                },
                "application": {
                    "uptime_seconds": app_uptime,
                    "uptime_formatted": format_uptime(app_uptime),
                    "start_time": app_start_time,
                    "start_time_formatted": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(app_start_time))
                },
                "current_time": current_time,
                "current_time_formatted": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
            }
            
            return self.create_success_response(
                message="Uptime metrikleri alındı",
                data=uptime_data
            )
            
        except Exception as e:
            self.logger.error(f"Uptime metrikleri alınamadı: {e}")
            return self.create_error_response(
                message="Uptime metrikleri alınamadı",
                status_code=500
            )