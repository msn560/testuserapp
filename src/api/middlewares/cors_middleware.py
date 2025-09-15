"""
CORS Middleware

Bu middleware Cross-Origin Resource Sharing (CORS) işlemlerini yönetir.
"""

from typing import List, Set
from aiohttp import web
from aiohttp.web import Request, Response, middleware

from ...core.settings import settings
from ...utils.logger import Logger


class CORSMiddleware:
    """CORS middleware sınıfı"""
    
    def __init__(self):
        """CORSMiddleware'ı başlat"""
        self.logger = Logger(__name__)
        
        # Config'den CORS ayarlarını yükle
        from ...core.config_manager import get_config_value
        self.allowed_origins = set(get_config_value("server.cors_origins", ["*"]))
        self.allowed_methods = set(get_config_value("server.cors_methods", ["GET", "POST", "PUT", "DELETE", "OPTIONS"]))
        self.allowed_headers = set(get_config_value("server.cors_headers", ["Content-Type", "Authorization"]))
        
        # Varsayılan değerler
        if "*" in self.allowed_origins:
            self.allowed_origins = {"*"}
        
        if "*" in self.allowed_methods:
            self.allowed_methods = {"GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"}
        
        if "*" in self.allowed_headers:
            self.allowed_headers = {"*"}
    
    @middleware
    async def middleware(self, request: Request, handler):
        """CORS middleware"""
        # Origin header'ını al
        origin = request.headers.get('Origin')
        
        # Preflight request kontrolü
        if request.method == 'OPTIONS':
            return await self._handle_preflight_request(request, origin)
        
        # Normal request'i işle
        response = await handler(request)
        
        # CORS header'larını ekle
        self._add_cors_headers(response, origin)
        
        return response
    
    async def _handle_preflight_request(self, request: Request, origin: str) -> Response:
        """
        Preflight request'i işle
        
        Args:
            request: Request objesi
            origin: Origin header değeri
            
        Returns:
            Preflight response
        """
        # Origin kontrolü
        if not self._is_origin_allowed(origin):
            return web.Response(status=403, text="Origin not allowed")
        
        # Request method kontrolü
        request_method = request.headers.get('Access-Control-Request-Method')
        if request_method and request_method not in self.allowed_methods:
            return web.Response(status=403, text="Method not allowed")
        
        # Request headers kontrolü
        request_headers = request.headers.get('Access-Control-Request-Headers')
        if request_headers:
            headers = [h.strip() for h in request_headers.split(',')]
            if not self._are_headers_allowed(headers):
                return web.Response(status=403, text="Headers not allowed")
        
        # Preflight response oluştur
        response = web.Response(status=200)
        self._add_cors_headers(response, origin)
        
        return response
    
    def _add_cors_headers(self, response: Response, origin: str) -> None:
        """
        CORS header'larını ekle
        
        Args:
            response: Response objesi
            origin: Origin header değeri
        """
        # Origin header'ı
        if self._is_origin_allowed(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
        elif "*" in self.allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = "*"
        
        # Methods header'ı
        response.headers['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
        
        # Headers header'ı
        response.headers['Access-Control-Allow-Headers'] = ', '.join(self.allowed_headers)
        
        # Credentials header'ı
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Max age header'ı
        response.headers['Access-Control-Max-Age'] = '86400'  # 24 saat
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """
        Origin'in izinli olup olmadığını kontrol et
        
        Args:
            origin: Origin değeri
            
        Returns:
            Origin izinli mi
        """
        if not origin:
            return False
        
        if "*" in self.allowed_origins:
            return True
        
        return origin in self.allowed_origins
    
    def _are_headers_allowed(self, headers: List[str]) -> bool:
        """
        Header'ların izinli olup olmadığını kontrol et
        
        Args:
            headers: Header listesi
            
        Returns:
            Header'lar izinli mi
        """
        if "*" in self.allowed_headers:
            return True
        
        return all(header.lower() in [h.lower() for h in self.allowed_headers] for header in headers)


# Global CORS middleware instance
cors_handler = CORSMiddleware()

# Export the middleware function
cors_middleware = cors_handler.middleware
