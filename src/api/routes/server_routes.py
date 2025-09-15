"""
Server Routes module - Server management endpoint'leri

Bu modül server yönetimi ile ilgili API endpoint'lerini içerir.
"""

import json
from typing import Dict, Any
from aiohttp import web
from aiohttp.web import Request, Response

from .base_routes import BaseRoutes
from ...core.constants import API_PREFIX, SUCCESS_MESSAGES, ERROR_MESSAGES
from ...api.schemas.server_schemas import (
    ServerStatusResponse, ServerConfigRequest, ServerConfigResponse,
    ServerStartResponse, ServerStopResponse, ServerRestartResponse,
    ServerMetricsResponse, ServerHealthResponse
)


class ServerRoutes(BaseRoutes):
    """Server routes sınıfı"""
    
    def __init__(self):
        """ServerRoutes'ı başlat"""
        super().__init__()
    
    def get_routes(self) -> list[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.get(f"{API_PREFIX}/server/status", self.get_server_status),
            web.post(f"{API_PREFIX}/server/start", self.start_server),
            web.post(f"{API_PREFIX}/server/stop", self.stop_server),
            web.post(f"{API_PREFIX}/server/restart", self.restart_server),
            web.get(f"{API_PREFIX}/server/config", self.get_server_config),
            web.put(f"{API_PREFIX}/server/config", self.update_server_config),
            web.get(f"{API_PREFIX}/server/metrics", self.get_server_metrics),
            web.get(f"{API_PREFIX}/server/health", self.get_server_health),
            web.get(f"{API_PREFIX}/server/logs", self.get_server_logs),
            web.get(f"{API_PREFIX}/server/processes", self.get_server_processes),
        ]
    
    async def get_server_status(self, request: Request) -> Response:
        """Server durumu"""
        try:
            # Server manager'ı al
            from ...api.server_manager import api_server_manager
            status = api_server_manager.get_status()
            
            return self.create_success_response(
                message="Server durumu alındı",
                data=status
            )
            
        except Exception as e:
            self.logger.error(f"Server status alınamadı: {e}")
            return self.create_error_response(
                message="Server durumu alınamadı",
                status_code=500
            )
    
    async def start_server(self, request: Request) -> Response:
        """Server başlat"""
        try:
            # Server manager'ı al
            from ...api.server_manager import api_server_manager
            
            # Server zaten çalışıyor mu kontrol et
            if api_server_manager.is_running:
                return self.create_error_response(
                    message="Server zaten çalışıyor",
                    status_code=400
                )
            
            # Server'ı başlat
            api_server_manager.start_server()
            
            # Başlatma işleminin tamamlanmasını bekle
            import time
            time.sleep(0.5)
            
            status = api_server_manager.get_status()
            return self.create_success_response(
                message="Server başarıyla başlatıldı",
                data=status
            )
                
        except Exception as e:
            self.logger.error(f"Server başlatılamadı: {e}")
            return self.create_error_response(
                message="Server başlatılamadı",
                status_code=500
            )
    
    async def stop_server(self, request: Request) -> Response:
        """Server durdur"""
        try:
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # Server çalışmıyor mu kontrol et
            if not server_manager.is_server_running():
                return self.create_error_response(
                    message="Server zaten durdurulmuş",
                    status_code=400
                )
            
            # Server'ı durdur
            success = server_manager.stop_server()
            
            if success:
                return self.create_success_response(
                    message="Server başarıyla durduruldu"
                )
            else:
                return self.create_error_response(
                    message="Server durdurulamadı",
                    status_code=500
                )
                
        except Exception as e:
            self.logger.error(f"Server durdurulamadı: {e}")
            return self.create_error_response(
                message="Server durdurulamadı",
                status_code=500
            )
    
    async def restart_server(self, request: Request) -> Response:
        """Server yeniden başlat"""
        try:
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # Server'ı yeniden başlat
            success = server_manager.restart_server()
            
            if success:
                status = server_manager.get_status()
                return self.create_success_response(
                    message="Server başarıyla yeniden başlatıldı",
                    data=status
                )
            else:
                return self.create_error_response(
                    message="Server yeniden başlatılamadı",
                    status_code=500
                )
                
        except Exception as e:
            self.logger.error(f"Server yeniden başlatılamadı: {e}")
            return self.create_error_response(
                message="Server yeniden başlatılamadı",
                status_code=500
            )
    
    async def get_server_config(self, request: Request) -> Response:
        """Server yapılandırması"""
        try:
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # Server yapılandırmasını al
            config = server_manager.get_server_config()
            
            return self.create_success_response(
                message="Server yapılandırması alındı",
                data=config
            )
            
        except Exception as e:
            self.logger.error(f"Server config alınamadı: {e}")
            return self.create_error_response(
                message="Server yapılandırması alınamadı",
                status_code=500
            )
    
    async def update_server_config(self, request: Request) -> Response:
        """Server yapılandırmasını güncelle"""
        try:
            # Request body'yi al
            data = await request.json()
            
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # Server çalışıyor mu kontrol et
            if server_manager.is_server_running():
                return self.create_error_response(
                    message="Server çalışırken yapılandırma değiştirilemez",
                    status_code=400
                )
            
            # Yapılandırmayı güncelle
            success = server_manager.update_server_config(data)
            
            if success:
                config = server_manager.get_server_config()
                return self.create_success_response(
                    message="Server yapılandırması güncellendi",
                    data=config
                )
            else:
                return self.create_error_response(
                    message="Server yapılandırması güncellenemedi",
                    status_code=500
                )
                
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Server config güncellenemedi: {e}")
            return self.create_error_response(
                message="Server yapılandırması güncellenemedi",
                status_code=500
            )
    
    async def get_server_metrics(self, request: Request) -> Response:
        """Server metrikleri"""
        try:
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # Detaylı istatistikleri al
            metrics = server_manager.get_detailed_stats()
            
            return self.create_success_response(
                message="Server metrikleri alındı",
                data=metrics
            )
            
        except Exception as e:
            self.logger.error(f"Server metrics alınamadı: {e}")
            return self.create_error_response(
                message="Server metrikleri alınamadı",
                status_code=500
            )
    
    async def get_server_health(self, request: Request) -> Response:
        """Server sağlık durumu"""
        try:
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # Sağlık durumunu al
            health = server_manager.get_server_health()
            
            return self.create_success_response(
                message="Server sağlık durumu alındı",
                data=health
            )
            
        except Exception as e:
            self.logger.error(f"Server health alınamadı: {e}")
            return self.create_error_response(
                message="Server sağlık durumu alınamadı",
                status_code=500
            )
    
    async def get_server_logs(self, request: Request) -> Response:
        """Server log'ları"""
        try:
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # Query parametrelerini al
            limit = int(request.query.get('limit', 100))
            level = request.query.get('level', '')
            
            # Server log'larını al
            server_logs = server_manager.get_api_logs()
            
            # Filtreleme
            if level:
                server_logs = [log for log in server_logs if log.get('level') == level]
            
            # Limit uygula
            server_logs = server_logs[-limit:] if limit > 0 else server_logs
            
            # Log formatını düzenle
            formatted_logs = []
            for log in server_logs:
                formatted_log = {
                    "id": log.get('id', 0),
                    "level": log.get('level', 'INFO'),
                    "message": log.get('message', ''),
                    "timestamp": log.get('timestamp', 0),
                    "module": log.get('module', 'unknown')
                }
                formatted_logs.append(formatted_log)
            
            return self.create_success_response(
                message="Server log'ları alındı",
                data={
                    "logs": formatted_logs,
                    "total": len(formatted_logs),
                    "limit": limit
                }
            )
            
        except Exception as e:
            self.logger.error(f"Server log'ları alınamadı: {e}")
            return self.create_error_response(
                message="Server log'ları alınamadı",
                status_code=500
            )
    
    async def get_server_processes(self, request: Request) -> Response:
        """Server process'leri"""
        try:
            import psutil
            
            # Mevcut process'leri al
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    processes.append({
                        "pid": proc_info['pid'],
                        "name": proc_info['name'],
                        "cpu_percent": proc_info['cpu_percent'],
                        "memory_percent": proc_info['memory_percent'],
                        "status": proc_info['status']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Python process'lerini filtrele
            python_processes = [p for p in processes if 'python' in p['name'].lower()]
            
            # En çok kaynak kullanan process'leri sırala
            top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10]
            
            return self.create_success_response(
                message="Server process'leri alındı",
                data={
                    "total_processes": len(processes),
                    "python_processes": len(python_processes),
                    "top_processes": top_processes,
                    "python_processes_detail": python_processes
                }
            )
            
        except Exception as e:
            self.logger.error(f"Server process'leri alınamadı: {e}")
            return self.create_error_response(
                message="Server process'leri alınamadı",
                status_code=500
            )