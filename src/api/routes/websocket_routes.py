"""
WebSocket Routes module - WebSocket endpoint'leri

Bu modül WebSocket bağlantıları ile ilgili endpoint'leri içerir.
"""

from aiohttp import web
from aiohttp.web import Request, Response

from .base_routes import BaseRoutes
from ...core.constants import API_PREFIX
from ...api.websocket_manager import websocket_manager


class WebSocketRoutes(BaseRoutes):
    """WebSocket routes sınıfı"""
    
    def __init__(self):
        """WebSocketRoutes'ı başlat"""
        super().__init__()
    
    def get_routes(self) -> list[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.get(f"/ws/system/status", self.system_status_websocket),
            web.get(f"/ws/system/metrics", self.system_metrics_websocket),
            web.get(f"/ws/logs", self.logs_websocket),
            web.get(f"/ws/notifications", self.notifications_websocket),
            web.get(f"/ws/server/status", self.server_status_websocket),
            web.get(f"/ws/monitor/alerts", self.monitor_alerts_websocket),
        ]
    
    async def system_status_websocket(self, request: Request) -> Response:
        """Sistem durumu WebSocket endpoint'i"""
        return await websocket_manager.websocket_handler(request)
    
    async def system_metrics_websocket(self, request: Request) -> Response:
        """Sistem metrikleri WebSocket endpoint'i"""
        return await websocket_manager.websocket_handler(request)
    
    async def logs_websocket(self, request: Request) -> Response:
        """Log WebSocket endpoint'i"""
        return await websocket_manager.websocket_handler(request)
    
    async def notifications_websocket(self, request: Request) -> Response:
        """Bildirimler WebSocket endpoint'i"""
        return await websocket_manager.websocket_handler(request)
    
    async def server_status_websocket(self, request: Request) -> Response:
        """Server durumu WebSocket endpoint'i"""
        return await websocket_manager.websocket_handler(request)
    
    async def monitor_alerts_websocket(self, request: Request) -> Response:
        """Monitor alert'leri WebSocket endpoint'i"""
        return await websocket_manager.websocket_handler(request)
