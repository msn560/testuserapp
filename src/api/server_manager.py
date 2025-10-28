"""
Server Manager module - AioHTTP + PyQt5 uyumlu server yöneticisi

Bu modül HTTP API server'ını yönetir.
AioHTTP tabanlı async HTTP server'ı PyQt5 ile uyumlu şekilde başlatır, durdurur ve yönetir.
QThread ve Signal kullanarak thread-safe iletişim sağlar.
"""

import asyncio
import ssl
import time
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
import aiohttp
from aiohttp import web, web_middlewares
from aiohttp.web import Request, Response, Application
from aiohttp.web_middlewares import normalize_path_middleware

from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer

from ..core.settings import settings
from ..core.constants import *
from ..utils.logger import Logger
from .middlewares.auth_middleware import AuthMiddleware
from .middlewares.cors_middleware import CORSMiddleware
from .middlewares.rate_limit import RateLimitMiddleware
from .middlewares.error_handler import ErrorHandlerMiddleware
from .middlewares.logging_middleware import LoggingMiddleware
from .middlewares.security_headers import SecurityHeadersMiddleware
from .routes import setup_routes


class ServerWorker(QObject):
    """
    Server Worker sınıfı - AioHTTP server'ını ayrı thread'de çalıştırır.
    """
    
    # PyQt5 Signals
    server_started = pyqtSignal(dict)  # Server başlatıldığında
    server_stopped = pyqtSignal()      # Server durdurulduğunda
    server_error = pyqtSignal(str)     # Server hatası
    log_message = pyqtSignal(dict)     # Log mesajı
    
    def __init__(self, host: str = None, port: int = None, 
                 ssl_enabled: bool = None, ssl_cert: Optional[str] = None, 
                 ssl_key: Optional[str] = None):
        super().__init__()
        
        self.logger = Logger(__name__)
        
        # Config'den server ayarlarını yükle
        from ..core.config_manager import get_config_value
        self.host = host or get_config_value("server.host", "localhost")
        self.port = port or get_config_value("server.port", 8080)
        self.ssl_enabled = ssl_enabled if ssl_enabled is not None else get_config_value("server.ssl", False)
        self.ssl_cert = ssl_cert or get_config_value("server.ssl_cert_path", "")
        self.ssl_key = ssl_key or get_config_value("server.ssl_key_path", "")
        
        # Server bileşenleri
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.app: Optional[Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.is_running = False
        self.start_time: Optional[float] = None
        
        # Server istatistikleri
        self.request_count = 0
        self.error_count = 0
        self.last_request_time = None
        
        # API request log'ları
        self.api_logs = []
        self.max_logs = 100  # Maksimum log sayısı
        
        # Detaylı server istatistikleri
        self.active_connections = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0
        self.requests_per_minute = 0
        self.avg_response_time = 0.0
        self.peak_connections = 0
        self.unique_users = set()
        self.endpoint_stats = {}  # Endpoint bazlı istatistikler
        self.user_agents = {}  # User agent istatistikleri
        self.ip_addresses = {}  # IP adresi istatistikleri
        self.response_times = []  # Response time geçmişi
        self.error_logs = []  # Hata log'ları
        
        # Zaman bazlı istatistikler
        self.minute_start_time = time.time()
        self.requests_this_minute = 0
        
        self.logger.info(f"ServerWorker initialized for {host}:{port} (SSL: {ssl_enabled})")
    
    def start_server(self):
        """Server'ı başlat (QThread'den çağrılır)"""
        try:
            # Yeni event loop oluştur
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Async server başlatma
            self.loop.run_until_complete(self._start_server_async())
            
            # Server başlatıldıktan sonra event loop'u çalıştır
            self.loop.run_forever()
            
        except Exception as e:
            self.logger.error(f"Server başlatılamadı: {e}")
            self.server_error.emit(str(e))
        finally:
            if self.loop and not self.loop.is_closed():
                self.loop.close()
    
    def stop_server(self):
        """Server'ı durdur (QThread'den çağrılır)"""
        try:
            if self.loop and not self.loop.is_closed():
                # Stop işlemini schedule et
                future = asyncio.run_coroutine_threadsafe(
                    self._stop_server_async(), self.loop
                )
                # Timeout ile bekle
                try:
                    future.result(timeout=5)
                except Exception as e:
                    self.logger.warning(f"Stop timeout: {e}")
                
                # Event loop'u durdur
                if self.loop.is_running():
                    self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception as e:
            self.logger.error(f"Server durdurulamadı: {e}")
            self.server_error.emit(str(e))
    
    async def _start_server_async(self):
        """Async server başlatma implementasyonu"""
        try:
            # Web uygulaması oluştur
            self.app = await self._create_application()
            
            # Route'ları ayarla
            setup_routes(self.app)
            
            # Runner oluştur
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            # SSL ile site oluştur
            if self.ssl_enabled:
                if not self.ssl_cert or not self.ssl_key:
                    raise ValueError("SSL sertifika ve key dosyaları SSL aktifken gerekli.")
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(self.ssl_cert, self.ssl_key)
                self.site = web.TCPSite(self.runner, host=self.host, port=self.port, ssl_context=ssl_context)
                self.logger.info(f"SSL ile server başlatılıyor: https://{self.host}:{self.port}")
            else:
                self.site = web.TCPSite(self.runner, host=self.host, port=self.port)
                self.logger.info(f"Server başlatılıyor: http://{self.host}:{self.port}")
            
            # Site'ı başlat
            await self.site.start()
            
            self.is_running = True
            self.start_time = time.time()
            
            # Signal gönder
            status = self.get_status()
            self.server_started.emit(status)
            self.logger.info("AioHTTP server başarıyla başlatıldı")
            
        except Exception as e:
            self.logger.error(f"Server başlatılamadı: {e}")
            self.server_error.emit(str(e))
            raise
    
    async def _stop_server_async(self):
        """Async server durdurma implementasyonu"""
        try:
            self.logger.info("Server durduruluyor...")
            
            if self.site:
                await self.site.stop()
                self.logger.info("Site durduruldu")
            
            if self.runner:
                await self.runner.cleanup()
                self.logger.info("Runner temizlendi")
            
            self.is_running = False
            self.start_time = None
            
            # Signal gönder
            self.server_stopped.emit()
            self.logger.info("AioHTTP server başarıyla durduruldu")
            
        except Exception as e:
            self.logger.error(f"Server durdurulamadı: {e}")
            self.server_error.emit(str(e))
            # Hata olsa bile durumu güncelle
            self.is_running = False
            self.start_time = None
            self.server_stopped.emit()
    
    async def _create_application(self) -> Application:
        """AioHTTP uygulaması oluştur"""
        # Middleware'leri oluştur
        middlewares = [
            normalize_path_middleware(append_slash=False),
            CORSMiddleware().middleware,
            SecurityHeadersMiddleware().middleware,
            RateLimitMiddleware().middleware,
            LoggingMiddleware().middleware,
            ErrorHandlerMiddleware().middleware,
            AuthMiddleware().middleware,
        ]
        
        # Uygulama oluştur
        app = web.Application(
            middlewares=middlewares,
            client_max_size=16 * 1024 * 1024  # 16MB
        )
        
        # Server ayarlarını config'den uygula
        from ..core.config_manager import get_config_value
        app['max_connections'] = get_config_value("server.max_connections", 1000)
        app['timeout'] = get_config_value("server.timeout", 30)
        
        # Server manager'ı app context'e ekle
        app['server_manager'] = self
        
        # Startup ve cleanup event handler'ları
        app.on_startup.append(self._on_startup)
        app.on_cleanup.append(self._on_cleanup)
        
        return app
    
    async def _on_startup(self, app: Application) -> None:
        """Uygulama başlatıldığında çağrılır"""
        self.logger.info("API server startup event")
        
        # Veritabanı bağlantısını kontrol et
        try:
            from ..db.database import db_manager
            db_manager.connect()
            self.logger.info("Veritabanı bağlantısı kuruldu")
        except Exception as e:
            self.logger.error(f"Veritabanı bağlantısı kurulamadı: {e}")
    
    async def _on_cleanup(self, app: Application) -> None:
        """Uygulama kapatıldığında çağrılır"""
        self.logger.info("API server cleanup event")
        
        # Veritabanı bağlantısını kapat
        try:
            from ..db.database import db_manager
            db_manager.disconnect()
            self.logger.info("Veritabanı bağlantısı kapatıldı")
        except Exception as e:
            self.logger.error(f"Veritabanı bağlantısı kapatılamadı: {e}")
    
    def add_api_log(self, method: str, path: str, status_code: int, response_time: float, 
                   ip_address: str = None, user_agent: str = "", user_id: str = None, 
                   bytes_sent: int = 0, bytes_received: int = 0):
        """API request log'u ekle"""
        try:
            # Config'den default IP'yi al
            if ip_address is None:
                from ..core.settings import settings
                ip_address = settings.server.host
            
            current_time = time.time()
            
            log_entry = {
                "timestamp": current_time,
                "method": method,
                "path": path,
                "status_code": status_code,
                "response_time": response_time,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "user_id": user_id,
                "bytes_sent": bytes_sent,
                "bytes_received": bytes_received
            }
            
            # Log'u ekle
            self.api_logs.append(log_entry)
            
            # Maksimum log sayısını kontrol et
            if len(self.api_logs) > self.max_logs:
                self.api_logs.pop(0)  # En eski log'u kaldır
            
            # Temel istatistikleri güncelle
            self.request_count += 1
            self.last_request_time = current_time
            self.requests_this_minute += 1
            
            # Aktif bağlantı sayısını güncelle
            self.active_connections += 1
            if self.active_connections > self.peak_connections:
                self.peak_connections = self.active_connections
            
            # Byte istatistikleri
            self.total_bytes_sent += bytes_sent
            self.total_bytes_received += bytes_received
            
            # Response time istatistikleri
            self.response_times.append(response_time)
            if len(self.response_times) > 100:  # Son 100 request'in ortalaması
                self.response_times.pop(0)
            self.avg_response_time = sum(self.response_times) / len(self.response_times)
            
            # Endpoint istatistikleri
            endpoint_key = f"{method} {path}"
            if endpoint_key not in self.endpoint_stats:
                self.endpoint_stats[endpoint_key] = {
                    "count": 0,
                    "total_time": 0,
                    "errors": 0,
                    "avg_time": 0
                }
            
            self.endpoint_stats[endpoint_key]["count"] += 1
            self.endpoint_stats[endpoint_key]["total_time"] += response_time
            self.endpoint_stats[endpoint_key]["avg_time"] = (
                self.endpoint_stats[endpoint_key]["total_time"] / 
                self.endpoint_stats[endpoint_key]["count"]
            )
            
            # User agent istatistikleri
            if user_agent:
                if user_agent not in self.user_agents:
                    self.user_agents[user_agent] = 0
                self.user_agents[user_agent] += 1
            
            # IP adresi istatistikleri
            if ip_address not in self.ip_addresses:
                self.ip_addresses[ip_address] = 0
            self.ip_addresses[ip_address] += 1
            
            # Kullanıcı istatistikleri
            if user_id:
                self.unique_users.add(user_id)
            
            # Hata istatistikleri
            if status_code >= 400:
                self.error_count += 1
                self.endpoint_stats[endpoint_key]["errors"] += 1
                
                # Hata log'u ekle
                error_log = {
                    "timestamp": current_time,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
                self.error_logs.append(error_log)
                if len(self.error_logs) > 50:  # Son 50 hata
                    self.error_logs.pop(0)
            
            # Dakikalık istatistikleri güncelle
            if current_time - self.minute_start_time >= 60:
                self.requests_per_minute = self.requests_this_minute
                self.requests_this_minute = 0
                self.minute_start_time = current_time
            
            # Aktif bağlantı sayısını azalt (simüle et)
            QTimer.singleShot(1000, lambda: self._decrease_active_connections())
            
            # Signal gönder
            level = "INFO" if status_code < 400 else "ERROR"
            icon = "✅" if status_code < 400 else "❌"
            
            # Detaylı mesaj oluştur
            message = f"{icon} {method} {path} - {status_code} ({response_time:.3f}s)"
            if user_id:
                message += f" [User: {user_id}]"
            message += f" from {ip_address}"
            if bytes_sent > 0 or bytes_received > 0:
                message += f" [{bytes_received}B→{bytes_sent}B]"
            
            self.log_message.emit({
                "timestamp": time.strftime("%H:%M:%S", time.localtime()),
                "level": level,
                "message": message
            })
            
        except Exception as e:
            self.logger.error(f"Error adding API log: {e}")
    
    def _decrease_active_connections(self):
        """Aktif bağlantı sayısını azalt"""
        if self.active_connections > 0:
            self.active_connections -= 1
    
    def get_api_logs(self) -> List[Dict[str, Any]]:
        """API log'larını al"""
        return self.api_logs.copy()
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Detaylı server istatistiklerini al"""
        try:
            # En popüler endpoint'leri al
            top_endpoints = sorted(
                self.endpoint_stats.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:5]
            
            # En aktif IP adreslerini al
            top_ips = sorted(
                self.ip_addresses.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # En çok kullanılan user agent'ları al
            top_user_agents = sorted(
                self.user_agents.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            # Son hataları al
            recent_errors = self.error_logs[-5:] if self.error_logs else []
            
            return {
                "server": {
                    "active_connections": self.active_connections,
                    "peak_connections": self.peak_connections,
                    "total_requests": self.request_count,
                    "requests_per_minute": self.requests_per_minute,
                    "avg_response_time": round(self.avg_response_time, 3),
                    "error_count": self.error_count,
                    "unique_users": len(self.unique_users)
                },
                "traffic": {
                    "total_bytes_sent": self.total_bytes_sent,
                    "total_bytes_received": self.total_bytes_received,
                    "total_bytes": self.total_bytes_sent + self.total_bytes_received
                },
                "top_endpoints": [
                    {
                        "endpoint": endpoint,
                        "count": stats["count"],
                        "avg_time": round(stats["avg_time"], 3),
                        "errors": stats["errors"]
                    }
                    for endpoint, stats in top_endpoints
                ],
                "top_ips": [
                    {"ip": ip, "requests": count}
                    for ip, count in top_ips
                ],
                "top_user_agents": [
                    {"user_agent": ua[:50] + "..." if len(ua) > 50 else ua, "count": count}
                    for ua, count in top_user_agents
                ],
                "recent_errors": [
                    {
                        "timestamp": time.strftime("%H:%M:%S", time.localtime(error["timestamp"])),
                        "method": error["method"],
                        "path": error["path"],
                        "status_code": error["status_code"],
                        "ip": error["ip_address"]
                    }
                    for error in recent_errors
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting detailed stats: {e}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Mevcut server durumunu al"""
        uptime = None
        if self.start_time and self.is_running:
            uptime = time.time() - self.start_time
        
        return {
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "ssl_enabled": self.ssl_enabled,
            "protocol": "https" if self.ssl_enabled else "http",
            "url": f"{'https' if self.ssl_enabled else 'http'}://{self.host}:{self.port}",
            "uptime_seconds": uptime,
            "start_time": self.start_time,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "last_request_time": self.last_request_time
        }
    
    def get_server_health(self) -> Dict[str, Any]:
        """Server sağlık durumunu al"""
        try:
            current_time = time.time()
            
            # Temel sağlık kontrolleri
            server_healthy = self.is_running and self.app is not None
            database_healthy = True  # Veritabanı kontrolü burada yapılabilir
            api_healthy = self.request_count > 0 or self.is_running
            
            # Genel sağlık durumu
            overall_status = "healthy" if all([server_healthy, database_healthy, api_healthy]) else "unhealthy"
            
            return {
                "overall_status": overall_status,
                "timestamp": current_time,
                "components": {
                    "server": {
                        "status": "healthy" if server_healthy else "unhealthy",
                        "response_time": 0.0,  # Bu değer gerçek zamanlı olarak hesaplanabilir
                        "last_check": current_time
                    },
                    "database": {
                        "status": "healthy" if database_healthy else "unhealthy",
                        "response_time": 0.0,
                        "last_check": current_time
                    },
                    "api": {
                        "status": "healthy" if api_healthy else "unhealthy",
                        "response_time": self.avg_response_time,
                        "last_check": current_time
                    }
                },
                "active_alerts": 0,  # Bu değer alert sistemi ile entegre edilebilir
                "uptime": time.time() - self.start_time if self.start_time else 0
            }
        except Exception as e:
            self.logger.error(f"Error getting server health: {e}")
            return {
                "overall_status": "error",
                "timestamp": time.time(),
                "error": str(e)
            }
    
    def get_endpoint_stats(self) -> Dict[str, Any]:
        """Endpoint istatistiklerini al"""
        try:
            if not self.endpoint_stats:
                return {}
            
            # Endpoint'leri sırala
            sorted_endpoints = sorted(
                self.endpoint_stats.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )
            
            return {
                "total_endpoints": len(self.endpoint_stats),
                "endpoints": [
                    {
                        "path": endpoint,
                        "count": stats["count"],
                        "avg_time": round(stats["avg_time"], 3),
                        "errors": stats["errors"],
                        "error_rate": round(stats["errors"] / stats["count"] * 100, 2) if stats["count"] > 0 else 0
                    }
                    for endpoint, stats in sorted_endpoints
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting endpoint stats: {e}")
            return {}
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Kullanıcı istatistiklerini al"""
        try:
            return {
                "unique_users": len(self.unique_users),
                "users": list(self.unique_users),
                "top_ips": [
                    {"ip": ip, "requests": count}
                    for ip, count in sorted(
                        self.ip_addresses.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting user stats: {e}")
            return {}
    
    def clear_logs(self) -> bool:
        """API log'larını temizle"""
        try:
            self.api_logs.clear()
            self.error_logs.clear()
            self.response_times.clear()
            self.logger.info("API log'ları temizlendi")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing logs: {e}")
            return False
    
    def export_logs(self, format: str = "json") -> Optional[str]:
        """API log'larını dışa aktar"""
        try:
            import json
            import csv
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == "json":
                filename = f"api_logs_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.api_logs, f, indent=2, ensure_ascii=False, default=str)
            
            elif format.lower() == "csv":
                filename = f"api_logs_{timestamp}.csv"
                if self.api_logs:
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=self.api_logs[0].keys())
                        writer.writeheader()
                        writer.writerows(self.api_logs)
            
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return None
            
            self.logger.info(f"API log'ları {filename} dosyasına aktarıldı")
            return filename
            
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            return None


class APIServerManager(QObject):
    """
    API Server yöneticisi - PyQt5 uyumlu
    
    AioHTTP tabanlı HTTP API server'ını PyQt5 ile uyumlu şekilde yönetir.
    QThread ve Signal kullanarak thread-safe iletişim sağlar.
    """
    
    # PyQt5 Signals
    server_status_changed = pyqtSignal(bool)  # Server durumu değişti
    server_error = pyqtSignal(str)            # Server hatası
    log_message = pyqtSignal(dict)            # Log mesajı
    
    def __init__(self, host: str = None, port: int = None, 
                 ssl_enabled: bool = None, ssl_cert: Optional[str] = None, 
                 ssl_key: Optional[str] = None):
        super().__init__()
        
        self.logger = Logger(__name__)
        
        # Config'den server ayarlarını yükle
        from ..core.config_manager import get_config_value
        self.host = host or get_config_value("server.host", "localhost")
        self.port = port or get_config_value("server.port", 8080)
        self.ssl_enabled = ssl_enabled if ssl_enabled is not None else get_config_value("server.ssl", False)
        self.ssl_cert = ssl_cert or get_config_value("server.ssl_cert_path", "")
        self.ssl_key = ssl_key or get_config_value("server.ssl_key_path", "")
        
        # Thread ve worker
        self.thread: Optional[QThread] = None
        self.worker: Optional[ServerWorker] = None
        self.is_running = False
        
        self.logger.info(f"APIServerManager initialized for {host}:{port} (SSL: {ssl_enabled})")
    
    def start_server(self):
        """Server'ı ayrı thread'de başlat"""
        try:
            if self.is_running:
                self.logger.warning("Server zaten çalışıyor")
                return
            
            # Thread ve worker oluştur
            self.thread = QThread()
            self.worker = ServerWorker(
                host=self.host,
                port=self.port,
                ssl_enabled=self.ssl_enabled,
                ssl_cert=self.ssl_cert,
                ssl_key=self.ssl_key
            )
            
            # Worker'ı thread'e taşı
            self.worker.moveToThread(self.thread)
            
            # Signal'ları bağla
            self.thread.started.connect(self.worker.start_server)
            self.worker.server_started.connect(self._on_server_started)
            self.worker.server_stopped.connect(self._on_server_stopped)
            self.worker.server_error.connect(self._on_server_error)
            self.worker.log_message.connect(self.log_message.emit)
            
            # Thread finished signal'ını bağla
            self.thread.finished.connect(self.thread.deleteLater)
            
            # Thread'i başlat
            self.thread.start()
            
            self.logger.info("Server thread başlatıldı")
            
        except Exception as e:
            self.logger.error(f"Server thread başlatılamadı: {e}")
            self.server_error.emit(str(e))
    
    def stop_server(self):
        """Server'ı durdur"""
        try:
            if not self.is_running or not self.worker:
                self.logger.warning("Server çalışmıyor")
                return
            
            # Worker thread'de server'ı durdur
            self.worker.stop_server()
            
            # Thread'in bitmesini bekle
            if self.thread and self.thread.isRunning():
                self.thread.quit()
                # Config'den timeout değerini al
                from ..core.settings import settings
                timeout = getattr(settings.server, 'timeout', 30) * 1000  # ms'ye çevir
                self.thread.wait(timeout)
            
            self.logger.info("Server durdurma isteği gönderildi")
            
        except Exception as e:
            self.logger.error(f"Server durdurulamadı: {e}")
            self.server_error.emit(str(e))
    
    def stop(self):
        """Alias for stop_server - compatibility method"""
        self.stop_server()
    
    def restart_server(self):
        """Server'ı yeniden başlat"""
        try:
            if self.is_running:
                self.logger.info("Server yeniden başlatılıyor...")
                self.stop_server()
                # QTimer ile durdurma tamamlandıktan sonra başlat
                QTimer.singleShot(1000, self.start_server)  # 1 saniye sonra başlat
            else:
                self.start_server()
                
        except Exception as e:
            self.logger.error(f"Server yeniden başlatılamadı: {e}")
            self.server_error.emit(str(e))
    
    def _on_server_started(self, status: Dict[str, Any]):
        """Server başlatıldı signal handler'ı"""
        self.is_running = True
        self.server_status_changed.emit(True)
        self.logger.info(f"Server başlatıldı: {status['url']}")
    
    def _on_server_stopped(self):
        """Server durduruldu signal handler'ı"""
        self.is_running = False
        self.server_status_changed.emit(False)
        self.logger.info("Server durduruldu")
    
    def _on_server_error(self, error_message: str):
        """Server hatası signal handler'ı"""
        self.is_running = False
        self.server_status_changed.emit(False)
        self.server_error.emit(error_message)
        self.logger.error(f"Server hatası: {error_message}")
    
    def get_status(self) -> Dict[str, Any]:
        """Mevcut server durumunu al"""
        if self.worker:
            return self.worker.get_status()
        else:
            return {
                "is_running": False,
                "host": self.host,
                "port": self.port,
                "ssl_enabled": self.ssl_enabled,
                "protocol": "https" if self.ssl_enabled else "http",
                "url": f"{'https' if self.ssl_enabled else 'http'}://{self.host}:{self.port}",
                "uptime_seconds": None,
                "start_time": None,
                "request_count": 0,
                "error_count": 0,
                "last_request_time": None
            }
    
    def is_server_running(self) -> bool:
        """Server çalışıyor mu kontrol et"""
        return self.is_running
    
    def get_server_url(self) -> str:
        """Server URL'ini al"""
        protocol = "https" if self.ssl_enabled else "http"
        return f"{protocol}://{self.host}:{self.port}"
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """Server konfigürasyonunu güncelle"""
        try:
            # Sadece server durmuşken konfigürasyon güncellenebilir
            if self.is_running:
                self.logger.error("Server çalışırken konfigürasyon güncellenemez")
                return False
            
            # Konfigürasyonu güncelle
            if 'host' in config:
                self.host = config['host']
            if 'port' in config:
                self.port = config['port']
            if 'ssl_enabled' in config:
                self.ssl_enabled = config['ssl_enabled']
            if 'ssl_cert' in config:
                self.ssl_cert = config['ssl_cert']
            if 'ssl_key' in config:
                self.ssl_key = config['ssl_key']
            
            self.logger.info("Server konfigürasyonu güncellendi")
            return True
            
        except Exception as e:
            self.logger.error(f"Server konfigürasyonu güncellenemedi: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Server konfigürasyonunu al"""
        return {
            "host": self.host,
            "port": self.port,
            "ssl_enabled": self.ssl_enabled,
            "ssl_cert": self.ssl_cert,
            "ssl_key": self.ssl_key
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Server metriklerini al"""
        if self.worker:
            return {
                "server": {
                    "is_running": self.is_running,
                    "uptime_seconds": self.worker.get_status().get("uptime_seconds"),
                    "start_time": self.worker.get_status().get("start_time"),
                    "host": self.host,
                    "port": self.port,
                    "ssl_enabled": self.ssl_enabled
                },
                "requests": {
                    "total_requests": self.worker.request_count,
                    "error_count": self.worker.error_count,
                    "last_request_time": self.worker.last_request_time
                },
                "thread": {
                    "is_alive": self.thread.isRunning() if self.thread else False,
                    "thread_name": self.thread.objectName() if self.thread else None
                }
            }
        else:
            return {
                "server": {
                    "is_running": False,
                    "uptime_seconds": None,
                    "start_time": None,
                    "host": self.host,
                    "port": self.port,
                    "ssl_enabled": self.ssl_enabled
                },
                "requests": {
                    "total_requests": 0,
                    "error_count": 0,
                    "last_request_time": None
                },
                "thread": {
                    "is_alive": False,
                    "thread_name": None
                }
            }
    
    def get_api_logs(self) -> List[Dict[str, Any]]:
        """API log'larını al"""
        if self.worker:
            return self.worker.get_api_logs()
        return []
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Detaylı server istatistiklerini al"""
        if self.worker:
            return self.worker.get_detailed_stats()
        return {}
    
    def get_queue_data(self) -> List[Dict[str, Any]]:
        """Get queued data (for compatibility)."""
        # This method is kept for compatibility
        # Real-time data is now handled via signals
        return []
    
    def get_server_health(self) -> Dict[str, Any]:
        """Server sağlık durumunu al"""
        if self.worker:
            return self.worker.get_server_health()
        return {
            "status": "stopped",
            "timestamp": time.time(),
            "components": {
                "server": {"status": "stopped"},
                "database": {"status": "unknown"},
                "api": {"status": "stopped"}
            }
        }
    
    def get_server_config(self) -> Dict[str, Any]:
        """Server yapılandırmasını al"""
        return {
            "host": self.host,
            "port": self.port,
            "ssl_enabled": self.ssl_enabled,
            "ssl_cert": self.ssl_cert,
            "ssl_key": self.ssl_key,
            "max_request_size": 16 * 1024 * 1024,  # 16MB
            "cors_enabled": True,
            "rate_limit_enabled": True,
            "auth_enabled": True
        }
    
    def update_server_config(self, config: Dict[str, Any]) -> bool:
        """Server yapılandırmasını güncelle"""
        try:
            # Sadece server durdurulmuşken yapılandırma değişikliği yapılabilir
            if self.is_server_running():
                self.logger.warning("Server çalışırken yapılandırma değiştirilemez")
                return False
            
            # Yapılandırmayı güncelle
            if "host" in config:
                self.host = config["host"]
            if "port" in config:
                self.port = config["port"]
            if "ssl_enabled" in config:
                self.ssl_enabled = config["ssl_enabled"]
            if "ssl_cert" in config:
                self.ssl_cert = config["ssl_cert"]
            if "ssl_key" in config:
                self.ssl_key = config["ssl_key"]
            
            self.logger.info("Server yapılandırması güncellendi")
            return True
            
        except Exception as e:
            self.logger.error(f"Server yapılandırması güncellenemedi: {e}")
            return False
    
    def get_endpoint_stats(self) -> Dict[str, Any]:
        """Endpoint istatistiklerini al"""
        if self.worker:
            return self.worker.get_endpoint_stats()
        return {}
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Kullanıcı istatistiklerini al"""
        if self.worker:
            return self.worker.get_user_stats()
        return {}
    
    def clear_logs(self) -> bool:
        """API log'larını temizle"""
        try:
            if self.worker:
                self.worker.clear_logs()
            self.logger.info("API log'ları temizlendi")
            return True
        except Exception as e:
            self.logger.error(f"API log'ları temizlenemedi: {e}")
            return False
    
    def export_logs(self, format: str = "json") -> Optional[str]:
        """API log'larını dışa aktar"""
        try:
            if self.worker:
                return self.worker.export_logs(format)
            return None
        except Exception as e:
            self.logger.error(f"API log'ları dışa aktarılamadı: {e}")
            return None


# Global API server manager instance
api_server_manager = APIServerManager()
