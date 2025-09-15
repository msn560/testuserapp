"""
Error Handler Middleware

Bu middleware HTTP hatalarını yakalar ve uygun response'lar döndürür.
"""

import traceback
from typing import Dict, Any
from aiohttp import web
from aiohttp.web import Request, Response, middleware
from aiohttp.web_exceptions import HTTPException

from ...core.constants import HTTP_STATUS_CODES, ERROR_MESSAGES
from ...utils.logger import Logger


class ErrorHandlerMiddleware:
    """Error handler middleware sınıfı"""
    
    def __init__(self):
        """ErrorHandlerMiddleware'ı başlat"""
        self.logger = Logger(__name__)
    
    @middleware
    async def middleware(self, request: Request, handler):
        """Error handler middleware"""
        try:
            # Request'i işle
            response = await handler(request)
            return response
            
        except HTTPException as e:
            # HTTP exception'ları yakala
            return self._create_error_response(
                status_code=e.status,
                message=e.text or HTTP_STATUS_CODES.get(e.status, "Unknown error"),
                request=request
            )
            
        except Exception as e:
            # Diğer exception'ları yakala
            self.logger.error(f"Unhandled exception: {e}", extra_data={
                'path': request.path,
                'method': request.method,
                'traceback': traceback.format_exc()
            })
            
            return self._create_error_response(
                status_code=500,
                message=ERROR_MESSAGES.get("SERVER_ERROR", "Internal server error"),
                request=request,
                error_details=str(e) if request.app.get('debug', False) else None
            )
    
    def _create_error_response(self, status_code: int, message: str, 
                             request: Request, error_details: str = None) -> Response:
        """
        Error response oluştur
        
        Args:
            status_code: HTTP status kodu
            message: Hata mesajı
            request: Request objesi
            error_details: Hata detayları (debug modunda)
            
        Returns:
            Error response
        """
        error_data = {
            "error": {
                "code": status_code,
                "message": message,
                "path": request.path,
                "method": request.method,
                "timestamp": self._get_timestamp()
            }
        }
        
        # Debug modunda hata detaylarını ekle
        if error_details and request.app.get('debug', False):
            error_data["error"]["details"] = error_details
        
        # Headers (Content-Type otomatik ayarlanır)
        headers = {}
        
        return web.json_response(
            data=error_data,
            status=status_code,
            headers=headers
        )
    
    def _get_timestamp(self) -> str:
        """Timestamp al"""
        from datetime import datetime
        return datetime.now().isoformat()


# Global error middleware instance
error_handler = ErrorHandlerMiddleware()

# Export the middleware function
error_middleware = error_handler.middleware
