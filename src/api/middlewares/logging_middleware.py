"""
Logging Middleware

Bu middleware HTTP request'lerini loglar.
"""

import time
from typing import Dict, Any
from aiohttp import web
from aiohttp.web import Request, Response, middleware

from ...utils.logger import Logger


class LoggingMiddleware:
    """Logging middleware sınıfı"""
    
    def __init__(self):
        """LoggingMiddleware'ı başlat"""
        self.logger = Logger(__name__)
    
    @middleware
    async def middleware(self, request: Request, handler):
        """Logging middleware"""
        # Request başlangıç zamanı
        start_time = time.time()
        
        # Request bilgilerini al
        method = request.method
        path = request.path
        query_string = request.query_string
        user_agent = request.headers.get('User-Agent', '')
        ip_address = self._get_client_ip(request)
        
        # User ID'yi al (auth middleware'den)
        user_id = getattr(request, 'user_id', None)
        
        # Request'i işle
        try:
            response = await handler(request)
            
            # Response bilgilerini al
            status_code = response.status
            response_time = (time.time() - start_time) * 1000  # Milisaniye
            
            # API request log'u
            self.logger.log_api_request(
                method=method,
                path=path,
                status_code=status_code,
                response_time=response_time,
                user_id=user_id,
                ip_address=ip_address,
                query_string=query_string,
                user_agent=user_agent
            )
            
            # Server manager'a API log'u gönder
            try:
                # App context'ten server manager'ı al
                server_manager = request.app.get('server_manager')
                if server_manager and hasattr(server_manager, 'worker') and server_manager.worker:
                    # Response boyutunu hesapla
                    bytes_sent = 0
                    if hasattr(response, 'body') and response.body:
                        bytes_sent = len(response.body)
                    
                    # Request boyutunu hesapla
                    bytes_received = 0
                    if hasattr(request, 'content_length') and request.content_length:
                        bytes_received = request.content_length
                    
                    server_manager.worker.add_api_log(
                        method=method,
                        path=path,
                        status_code=status_code,
                        response_time=response_time / 1000,  # Saniyeye çevir
                        ip_address=ip_address,
                        user_agent=user_agent,
                        user_id=user_id,
                        bytes_sent=bytes_sent,
                        bytes_received=bytes_received
                    )
            except Exception as e:
                self.logger.error(f"Error sending API log to server manager: {e}")
            
            return response
            
        except Exception as e:
            # Hata durumunda log
            response_time = (time.time() - start_time) * 1000
            
            self.logger.log_api_request(
                method=method,
                path=path,
                status_code=500,
                response_time=response_time,
                user_id=user_id,
                ip_address=ip_address,
                query_string=query_string,
                user_agent=user_agent,
                error=str(e)
            )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Client IP adresini al
        
        Args:
            request: Request objesi
            
        Returns:
            Client IP adresi
        """
        # X-Forwarded-For header'ını kontrol et
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # İlk IP'yi al (proxy chain'de)
            return forwarded_for.split(',')[0].strip()
        
        # X-Real-IP header'ını kontrol et
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Remote IP'yi al
        return request.remote


# Global logging middleware instance
logging_handler = LoggingMiddleware()

# Export the middleware function
logging_middleware = logging_handler.middleware
