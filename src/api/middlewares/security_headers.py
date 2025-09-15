"""
Security Headers Middleware

Bu middleware güvenlik header'larını ekler.
"""

from aiohttp import web
from aiohttp.web import Request, Response, middleware

from ...core.settings import settings
from ...utils.logger import Logger


class SecurityHeadersMiddleware:
    """Security headers middleware sınıfı"""
    
    def __init__(self):
        """SecurityHeadersMiddleware'ı başlat"""
        self.logger = Logger(__name__)
    
    @middleware
    async def middleware(self, request: Request, handler):
        """Security headers middleware"""
        # Request'i işle
        response = await handler(request)
        
        # Güvenlik header'larını ekle
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response: Response) -> None:
        """
        Güvenlik header'larını ekle
        
        Args:
            response: Response objesi
        """
        # X-Content-Type-Options
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options
        response.headers['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content-Security-Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # Strict-Transport-Security (sadece HTTPS'de)
        if settings.server.ssl:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # X-Permitted-Cross-Domain-Policies
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        
        # Cross-Origin-Embedder-Policy
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        
        # Cross-Origin-Opener-Policy
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        
        # Cross-Origin-Resource-Policy
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'


# Global security middleware instance
security_handler = SecurityHeadersMiddleware()

# Export the middleware function
security_middleware = security_handler.middleware