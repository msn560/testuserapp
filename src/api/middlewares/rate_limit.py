"""
Rate Limiting Middleware

Bu middleware rate limiting işlemlerini yönetir.
"""

import time
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from aiohttp import web
from aiohttp.web import Request, Response, middleware

from ...core.settings import settings
from ...utils.logger import Logger


class RateLimitMiddleware:
    """Rate limiting middleware sınıfı"""
    
    def __init__(self):
        """RateLimitMiddleware'ı başlat"""
        self.logger = Logger(__name__)
        
        # Config'den rate limiting ayarlarını yükle
        from ...core.config_manager import get_config_value
        self.enabled = get_config_value("rate_limiting.enabled", True)
        self.requests_per_minute = get_config_value("rate_limiting.requests_per_minute", 100)
        self.burst_size = get_config_value("rate_limiting.burst_size", 20)
        self.per_ip_limit = get_config_value("rate_limiting.per_ip_limit", True)
        self.per_user_limit = get_config_value("rate_limiting.per_user_limit", True)
        
        # Rate limit storage
        self.ip_requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.user_requests: Dict[int, deque] = defaultdict(lambda: deque())
        
        # Endpoint bazlı rate limitler
        self.endpoint_limits = {
            '/api/v1/auth/login': {'requests_per_minute': 10, 'burst_size': 3},
            '/api/v1/auth/refresh': {'requests_per_minute': 20, 'burst_size': 5},
            '/api/v1/server/start': {'requests_per_minute': 5, 'burst_size': 1},
            '/api/v1/server/stop': {'requests_per_minute': 5, 'burst_size': 1},
            '/api/v1/server/restart': {'requests_per_minute': 5, 'burst_size': 1},
        }
        
        # Cleanup için son temizlik zamanı
        self.last_cleanup = time.time()
        
        # Rate limit istatistikleri
        self.rate_limit_hits = 0
        self.total_requests = 0
    
    @middleware
    async def middleware(self, request: Request, handler):
        """Rate limiting middleware"""
        if not self.enabled:
            return await handler(request)
        
        # Client IP'yi al
        client_ip = self._get_client_ip(request)
        
        # User ID'yi al (auth middleware'den)
        user_id = getattr(request, 'user_id', None)
        
        # Endpoint bazlı rate limit kontrolü
        endpoint = request.path
        if self._is_endpoint_rate_limited(endpoint, client_ip, user_id):
            return self._create_rate_limit_response()
        
        # Genel rate limit kontrolü
        if self._is_rate_limited(client_ip, user_id):
            return self._create_rate_limit_response()
        
        # Request'i işle
        response = await handler(request)
        
        # Request'i kaydet
        self._record_request(client_ip, user_id)
        self.total_requests += 1
        
        # Periyodik temizlik
        self._cleanup_old_requests()
        
        return response
    
    def _is_rate_limited(self, client_ip: str, user_id: Optional[int]) -> bool:
        """
        Rate limit kontrolü yap
        
        Args:
            client_ip: Client IP adresi
            user_id: Kullanıcı ID
            
        Returns:
            Rate limit aşıldı mı
        """
        current_time = time.time()
        
        # IP bazlı kontrol
        if self.per_ip_limit:
            if self._check_rate_limit(self.ip_requests[client_ip], current_time):
                self.logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return True
        
        # User bazlı kontrol
        if self.per_user_limit and user_id:
            if self._check_rate_limit(self.user_requests[user_id], current_time):
                self.logger.warning(f"Rate limit exceeded for user: {user_id}")
                return True
        
        return False
    
    def _check_rate_limit(self, requests: deque, current_time: float) -> bool:
        """
        Rate limit kontrolü yap
        
        Args:
            requests: Request zamanları deque'si
            current_time: Mevcut zaman
            
        Returns:
            Rate limit aşıldı mı
        """
        # Son 1 dakikadaki request'leri temizle
        while requests and current_time - requests[0] > 60:
            requests.popleft()
        
        # Request sayısını kontrol et
        if len(requests) >= self.requests_per_minute:
            return True
        
        # Burst kontrolü
        if len(requests) >= self.burst_size:
            # Son 10 saniyedeki request'leri kontrol et
            recent_requests = [req for req in requests if current_time - req <= 10]
            if len(recent_requests) >= self.burst_size:
                return True
        
        return False
    
    def _is_endpoint_rate_limited(self, endpoint: str, client_ip: str, user_id: Optional[int]) -> bool:
        """
        Endpoint bazlı rate limit kontrolü yap
        
        Args:
            endpoint: Endpoint path
            client_ip: Client IP adresi
            user_id: Kullanıcı ID
            
        Returns:
            Rate limit aşıldı mı
        """
        # Endpoint için özel limit var mı kontrol et
        if endpoint not in self.endpoint_limits:
            return False
        
        endpoint_config = self.endpoint_limits[endpoint]
        current_time = time.time()
        
        # Endpoint bazlı IP kontrolü
        endpoint_key = f"{endpoint}:{client_ip}"
        if endpoint_key not in self.ip_requests:
            self.ip_requests[endpoint_key] = deque()
        
        # Endpoint bazlı user kontrolü
        if user_id:
            user_endpoint_key = f"{endpoint}:user:{user_id}"
            if user_endpoint_key not in self.user_requests:
                self.user_requests[user_endpoint_key] = deque()
        
        # Endpoint limitlerini kontrol et
        requests_per_minute = endpoint_config.get('requests_per_minute', self.requests_per_minute)
        burst_size = endpoint_config.get('burst_size', self.burst_size)
        
        # IP bazlı endpoint kontrolü
        if self._check_endpoint_rate_limit(self.ip_requests[endpoint_key], current_time, requests_per_minute, burst_size):
            self.logger.warning(f"Endpoint rate limit exceeded for IP {client_ip} on {endpoint}")
            self.rate_limit_hits += 1
            return True
        
        # User bazlı endpoint kontrolü
        if user_id:
            user_endpoint_key = f"{endpoint}:user:{user_id}"
            if self._check_endpoint_rate_limit(self.user_requests[user_endpoint_key], current_time, requests_per_minute, burst_size):
                self.logger.warning(f"Endpoint rate limit exceeded for user {user_id} on {endpoint}")
                self.rate_limit_hits += 1
                return True
        
        return False
    
    def _check_endpoint_rate_limit(self, requests: deque, current_time: float, requests_per_minute: int, burst_size: int) -> bool:
        """
        Endpoint bazlı rate limit kontrolü yap
        
        Args:
            requests: Request zamanları deque'si
            current_time: Mevcut zaman
            requests_per_minute: Dakika başına istek sayısı
            burst_size: Burst boyutu
            
        Returns:
            Rate limit aşıldı mı
        """
        # Son 1 dakikadaki request'leri temizle
        while requests and current_time - requests[0] > 60:
            requests.popleft()
        
        # Request sayısını kontrol et
        if len(requests) >= requests_per_minute:
            return True
        
        # Burst kontrolü
        if len(requests) >= burst_size:
            # Son 10 saniyedeki request'leri kontrol et
            recent_requests = [req for req in requests if current_time - req <= 10]
            if len(recent_requests) >= burst_size:
                return True
        
        return False
    
    def _record_request(self, client_ip: str, user_id: Optional[int]) -> None:
        """
        Request'i kaydet
        
        Args:
            client_ip: Client IP adresi
            user_id: Kullanıcı ID
        """
        current_time = time.time()
        
        # IP bazlı kayıt
        if self.per_ip_limit:
            self.ip_requests[client_ip].append(current_time)
        
        # User bazlı kayıt
        if self.per_user_limit and user_id:
            self.user_requests[user_id].append(current_time)
    
    def _cleanup_old_requests(self) -> None:
        """Eski request'leri temizle"""
        current_time = time.time()
        
        # 5 dakikada bir temizlik yap
        if current_time - self.last_cleanup < 300:
            return
        
        # IP request'lerini temizle
        for ip in list(self.ip_requests.keys()):
            requests = self.ip_requests[ip]
            while requests and current_time - requests[0] > 60:
                requests.popleft()
            
            # Boş deque'leri sil
            if not requests:
                del self.ip_requests[ip]
        
        # User request'lerini temizle
        for user_id in list(self.user_requests.keys()):
            requests = self.user_requests[user_id]
            while requests and current_time - requests[0] > 60:
                requests.popleft()
            
            # Boş deque'leri sil
            if not requests:
                del self.user_requests[user_id]
        
        self.last_cleanup = current_time
    
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
            return forwarded_for.split(',')[0].strip()
        
        # X-Real-IP header'ını kontrol et
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Remote IP'yi al
        return request.remote
    
    def _create_rate_limit_response(self) -> Response:
        """
        Rate limit response'u oluştur
        
        Returns:
            Rate limit response
        """
        return web.json_response(
            data={
                "error": {
                    "code": 429,
                    "message": "Rate limit exceeded",
                    "retry_after": 60
                }
            },
            status=429,
            headers={
                'Retry-After': '60'
            }
        )
    
    def get_rate_limit_status(self, client_ip: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Rate limit durumunu al
        
        Args:
            client_ip: Client IP adresi
            user_id: Kullanıcı ID
            
        Returns:
            Rate limit durumu
        """
        current_time = time.time()
        
        status = {
            "enabled": self.enabled,
            "requests_per_minute": self.requests_per_minute,
            "burst_size": self.burst_size,
            "per_ip_limit": self.per_ip_limit,
            "per_user_limit": self.per_user_limit
        }
        
        # IP bazlı durum
        if self.per_ip_limit:
            ip_requests = self.ip_requests.get(client_ip, deque())
            # Son 1 dakikadaki request'leri say
            recent_requests = [req for req in ip_requests if current_time - req <= 60]
            status["ip_requests"] = {
                "current": len(recent_requests),
                "limit": self.requests_per_minute,
                "remaining": max(0, self.requests_per_minute - len(recent_requests))
            }
        
        # User bazlı durum
        if self.per_user_limit and user_id:
            user_requests = self.user_requests.get(user_id, deque())
            # Son 1 dakikadaki request'leri say
            recent_requests = [req for req in user_requests if current_time - req <= 60]
            status["user_requests"] = {
                "current": len(recent_requests),
                "limit": self.requests_per_minute,
                "remaining": max(0, self.requests_per_minute - len(recent_requests))
            }
        
        return status
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """
        Rate limit istatistiklerini al
        
        Returns:
            Rate limit istatistikleri
        """
        current_time = time.time()
        
        # Aktif IP sayısı
        active_ips = len([ip for ip, requests in self.ip_requests.items() 
                         if requests and current_time - requests[-1] <= 60])
        
        # Aktif user sayısı
        active_users = len([user_id for user_id, requests in self.user_requests.items() 
                           if requests and current_time - requests[-1] <= 60])
        
        # Rate limit hit oranı
        hit_rate = (self.rate_limit_hits / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "enabled": self.enabled,
            "total_requests": self.total_requests,
            "rate_limit_hits": self.rate_limit_hits,
            "hit_rate_percent": round(hit_rate, 2),
            "active_ips": active_ips,
            "active_users": active_users,
            "requests_per_minute": self.requests_per_minute,
            "burst_size": self.burst_size,
            "per_ip_limit": self.per_ip_limit,
            "per_user_limit": self.per_user_limit,
            "endpoint_limits": self.endpoint_limits
        }
    
    def update_rate_limit_config(self, config: Dict[str, Any]) -> bool:
        """
        Rate limit yapılandırmasını güncelle
        
        Args:
            config: Yeni yapılandırma
            
        Returns:
            Güncelleme başarılı mı
        """
        try:
            if "enabled" in config:
                self.enabled = config["enabled"]
            if "requests_per_minute" in config:
                self.requests_per_minute = config["requests_per_minute"]
            if "burst_size" in config:
                self.burst_size = config["burst_size"]
            if "per_ip_limit" in config:
                self.per_ip_limit = config["per_ip_limit"]
            if "per_user_limit" in config:
                self.per_user_limit = config["per_user_limit"]
            if "endpoint_limits" in config:
                self.endpoint_limits.update(config["endpoint_limits"])
            
            self.logger.info("Rate limit yapılandırması güncellendi")
            return True
            
        except Exception as e:
            self.logger.error(f"Rate limit yapılandırması güncellenemedi: {e}")
            return False
    
    def reset_rate_limit_stats(self) -> None:
        """Rate limit istatistiklerini sıfırla"""
        self.rate_limit_hits = 0
        self.total_requests = 0
        self.ip_requests.clear()
        self.user_requests.clear()
        self.logger.info("Rate limit istatistikleri sıfırlandı")


# Global rate limit middleware instance
rate_limit_handler = RateLimitMiddleware()

# Export the middleware function
rate_limit_middleware = rate_limit_handler.middleware
