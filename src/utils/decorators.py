"""
Decorators module - Özel decorator'lar

Bu modül uygulamada kullanılan özel decorator'ları içerir.
Authentication, caching, logging, rate limiting ve diğer decorator'lar.
"""

import functools
import time
import asyncio
from typing import Any, Callable, Dict, Optional, Union
from datetime import datetime, timedelta
import threading
import hashlib
import json

from .logger import logger


def timing(func: Callable) -> Callable:
    """
    Fonksiyon çalışma süresini ölçen decorator.
    
    Args:
        func: Ölçülecek fonksiyon
        
    Returns:
        Wrapped fonksiyon
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            duration = end_time - start_time
            logger.debug(f"Function {func.__name__} took {duration:.4f} seconds")
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            duration = end_time - start_time
            logger.debug(f"Async function {func.__name__} took {duration:.4f} seconds")
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0,
          exceptions: tuple = (Exception,)) -> Callable:
    """
    Fonksiyonu tekrar deneme decorator'u.
    
    Args:
        max_attempts: Maksimum deneme sayısı
        delay: İlk deneme arasındaki gecikme (saniye)
        backoff: Her denemede gecikme çarpanı
        exceptions: Tekrar denenecek exception türleri
        
    Returns:
        Decorator fonksiyonu
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}): {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Async function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"Async function {func.__name__} failed (attempt {attempt}/{max_attempts}): {e}")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


def cache(ttl: int = 300, maxsize: int = 128) -> Callable:
    """
    Basit cache decorator'u.
    
    Args:
        ttl: Cache yaşam süresi (saniye)
        maxsize: Maksimum cache boyutu
        
    Returns:
        Decorator fonksiyonu
    """
    def decorator(func: Callable) -> Callable:
        cache_data = {}
        cache_times = {}
        cache_lock = threading.Lock()
        
        def _make_key(*args, **kwargs):
            """Cache anahtarı oluşturur."""
            key_data = (args, tuple(sorted(kwargs.items())))
            key_string = json.dumps(key_data, sort_keys=True, default=str)
            return hashlib.md5(key_string.encode()).hexdigest()
        
        def _cleanup_cache():
            """Eski cache girişlerini temizler."""
            current_time = time.time()
            expired_keys = [
                key for key, cache_time in cache_times.items()
                if current_time - cache_time > ttl
            ]
            for key in expired_keys:
                cache_data.pop(key, None)
                cache_times.pop(key, None)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _make_key(*args, **kwargs)
            current_time = time.time()
            
            with cache_lock:
                # Cache kontrolü
                if cache_key in cache_data:
                    cache_time = cache_times.get(cache_key, 0)
                    if current_time - cache_time <= ttl:
                        logger.debug(f"Cache hit for {func.__name__}")
                        return cache_data[cache_key]
                
                # Cache boyut kontrolü
                if len(cache_data) >= maxsize:
                    _cleanup_cache()
                    # Hala doluysa en eskiyi sil
                    if len(cache_data) >= maxsize:
                        oldest_key = min(cache_times.keys(), key=lambda k: cache_times[k])
                        cache_data.pop(oldest_key, None)
                        cache_times.pop(oldest_key, None)
            
            # Fonksiyonu çalıştır ve cache'e kaydet
            result = func(*args, **kwargs)
            
            with cache_lock:
                cache_data[cache_key] = result
                cache_times[cache_key] = current_time
            
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result
        
        # Cache temizleme metodu ekle
        def clear_cache():
            with cache_lock:
                cache_data.clear()
                cache_times.clear()
                logger.debug(f"Cache cleared for {func.__name__}")
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator


def rate_limit(calls: int = 10, period: int = 60) -> Callable:
    """
    Rate limiting decorator'u.
    
    Args:
        calls: İzin verilen çağrı sayısı
        period: Zaman periyodu (saniye)
        
    Returns:
        Decorator fonksiyonu
    """
    def decorator(func: Callable) -> Callable:
        call_history = []
        lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            
            with lock:
                # Eski çağrıları temizle
                call_history[:] = [
                    call_time for call_time in call_history
                    if current_time - call_time < period
                ]
                
                # Rate limit kontrolü
                if len(call_history) >= calls:
                    raise Exception(f"Rate limit exceeded: {calls} calls per {period} seconds")
                
                # Yeni çağrıyı kaydet
                call_history.append(current_time)
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def deprecated(reason: str = None) -> Callable:
    """
    Deprecated fonksiyon decorator'u.
    
    Args:
        reason: Deprecated olma sebebi
        
    Returns:
        Decorator fonksiyonu
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warning_msg = f"Function {func.__name__} is deprecated"
            if reason:
                warning_msg += f": {reason}"
            logger.warning(warning_msg)
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def validate_input(**validators) -> Callable:
    """
    Input validasyon decorator'u.
    
    Args:
        **validators: Parametre adı -> validasyon fonksiyonu mapping'i
        
    Returns:
        Decorator fonksiyonu
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Fonksiyon signature'ını al
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validasyon yap
            for param_name, validator_func in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    try:
                        is_valid = validator_func(value)
                        if not is_valid:
                            raise ValueError(f"Invalid value for parameter {param_name}: {value}")
                    except Exception as e:
                        raise ValueError(f"Validation failed for parameter {param_name}: {e}")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def singleton(cls: type) -> type:
    """
    Singleton pattern decorator'u.
    
    Args:
        cls: Singleton olacak sınıf
        
    Returns:
        Singleton sınıfı
    """
    instances = {}
    lock = threading.Lock()
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


def async_to_sync(func: Callable) -> Callable:
    """
    Async fonksiyonu sync fonksiyona çeviren decorator.
    
    Args:
        func: Async fonksiyon
        
    Returns:
        Sync fonksiyon
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(func(*args, **kwargs))
    
    return wrapper


def sync_to_async(func: Callable) -> Callable:
    """
    Sync fonksiyonu async fonksiyona çeviren decorator.
    
    Args:
        func: Sync fonksiyon
        
    Returns:
        Async fonksiyon
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    
    return wrapper


def log_calls(level: str = "DEBUG") -> Callable:
    """
    Fonksiyon çağrılarını loglayan decorator.
    
    Args:
        level: Log seviyesi
        
    Returns:
        Decorator fonksiyonu
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log_func = getattr(logger, level.lower(), logger.debug)
            log_func(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                log_func(f"{func.__name__} returned: {result}")
                return result
            except Exception as e:
                log_func(f"{func.__name__} raised exception: {e}")
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            log_func = getattr(logger, level.lower(), logger.debug)
            log_func(f"Calling async {func.__name__} with args={args}, kwargs={kwargs}")
            
            try:
                result = await func(*args, **kwargs)
                log_func(f"Async {func.__name__} returned: {result}")
                return result
            except Exception as e:
                log_func(f"Async {func.__name__} raised exception: {e}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


def require_auth(func: Callable) -> Callable:
    """
    Authentication gerektiren decorator.
    
    Args:
        func: Korunacak fonksiyon
        
    Returns:
        Protected fonksiyon
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # İlk argüman genellikle self veya request olur
        # Burada basit bir kontrol yapıyoruz
        if not hasattr(args[0], 'user') or not args[0].user:
            raise Exception("Authentication required")
        
        return func(*args, **kwargs)
    
    return wrapper


def require_role(required_role: str) -> Callable:
    """
    Belirli rol gerektiren decorator.
    
    Args:
        required_role: Gerekli rol
        
    Returns:
        Decorator fonksiyonu
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # İlk argüman genellikle self veya request olur
            if not hasattr(args[0], 'user') or not args[0].user:
                raise Exception("Authentication required")
            
            user_roles = getattr(args[0].user, 'roles', [])
            if required_role not in user_roles:
                raise Exception(f"Role '{required_role}' required")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def exception_handler(exceptions: tuple = (Exception,), 
                     default_return: Any = None,
                     log_exception: bool = True) -> Callable:
    """
    Exception handling decorator'u.
    
    Args:
        exceptions: Yakalanacak exception türleri
        default_return: Exception durumunda döndürülecek değer
        log_exception: Exception'ı logla
        
    Returns:
        Decorator fonksiyonu
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_exception:
                    logger.exception(f"Exception in {func.__name__}: {e}")
                return default_return
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                if log_exception:
                    logger.exception(f"Exception in async {func.__name__}: {e}")
                return default_return
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


class memoize:
    """
    Memoization decorator sınıfı.
    
    Fonksiyon sonuçlarını cache'ler ve aynı parametrelerle
    çağrıldığında cache'den döndürür.
    """
    
    def __init__(self, ttl: Optional[int] = None):
        """
        Memoize decorator'ını başlatır.
        
        Args:
            ttl: Cache yaşam süresi (saniye, None ise sınırsız)
        """
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}
        self.lock = threading.Lock()
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Cache anahtarı oluştur
            key = self._make_key(args, kwargs)
            current_time = time.time()
            
            with self.lock:
                # Cache kontrolü
                if key in self.cache:
                    if self.ttl is None or (current_time - self.timestamps[key]) < self.ttl:
                        return self.cache[key]
                
                # Fonksiyonu çalıştır ve cache'e kaydet
                result = func(*args, **kwargs)
                self.cache[key] = result
                self.timestamps[key] = current_time
                
                return result
        
        # Cache temizleme metodu ekle
        wrapper.clear_cache = self.clear_cache
        return wrapper
    
    def _make_key(self, args, kwargs):
        """Cache anahtarı oluşturur."""
        key_data = (args, tuple(sorted(kwargs.items())))
        return hash(str(key_data))
    
    def clear_cache(self):
        """Cache'i temizler."""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()


# Hazır decorator örnekleri
timer = timing
cached = cache()
limited = rate_limit()
safe = exception_handler()
authenticated = require_auth
admin_required = require_role("admin")
