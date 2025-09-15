"""
Event System module - Event dispatcher

Bu modül uygulamanın event sistemini yönetir.
Event gönderme, dinleme ve yönetme işlemleri.
"""

import asyncio
import threading
from typing import Dict, Any, List, Callable, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import weakref
import inspect

from .constants import LogLevel
from ..utils.logger import logger


class EventPriority(Enum):
    """Event öncelik seviyeleri."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Event veri yapısı."""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    priority: EventPriority = EventPriority.NORMAL
    is_async: bool = False
    is_cancelled: bool = False


@dataclass
class EventListener:
    """Event listener veri yapısı."""
    callback: Callable
    priority: EventPriority = EventPriority.NORMAL
    is_async: bool = False
    is_weak: bool = True
    once: bool = False


class EventSystem:
    """
    Event sistemi yöneticisi.
    
    Bu sınıf event gönderme, dinleme ve yönetme işlemlerini sağlar.
    """
    
    def __init__(self):
        """
        EventSystem'i başlatır.
        """
        self.logger = logger
        
        # Event listener'ları
        self.listeners: Dict[str, List[EventListener]] = {}
        
        # Event geçmişi
        self.event_history: List[Event] = []
        self.max_history_size = 1000
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Event istatistikleri
        self.stats = {
            "total_events": 0,
            "events_by_name": {},
            "listeners_by_event": {},
            "async_events": 0,
            "sync_events": 0
        }
        
        # Event loop (async events için)
        self.event_loop = None
        self.is_running = False
    
    def start(self) -> bool:
        """
        Event sistemini başlatır.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                self.logger.warning("Event system is already running")
                return True
            
            self.is_running = True
            
            # Event loop'u başlat
            try:
                self.event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.event_loop)
            except RuntimeError:
                # Zaten bir event loop varsa onu kullan
                self.event_loop = asyncio.get_event_loop()
            
            self.logger.info("Event system started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start event system: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Event sistemini durdurur.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if not self.is_running:
                self.logger.warning("Event system is not running")
                return True
            
            self.is_running = False
            
            # Event loop'u kapat
            if self.event_loop and not self.event_loop.is_closed():
                self.event_loop.close()
            
            self.logger.info("Event system stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop event system: {e}")
            return False
    
    def emit(self, event_name: str, data: Dict[str, Any] = None, 
             source: str = "", priority: EventPriority = EventPriority.NORMAL,
             is_async: bool = False) -> bool:
        """
        Event gönderir.
        
        Args:
            event_name: Event adı
            data: Event verisi
            source: Event kaynağı
            priority: Event önceliği
            is_async: Async event mi
            
        Returns:
            True if event emitted successfully, False otherwise
        """
        try:
            # Event oluştur
            event = Event(
                name=event_name,
                data=data or {},
                source=source,
                priority=priority,
                is_async=is_async
            )
            
            # Event geçmişine ekle
            self._add_to_history(event)
            
            # İstatistikleri güncelle
            self._update_stats(event)
            
            # Listener'ları bul
            listeners = self.listeners.get(event_name, [])
            if not listeners:
                self.logger.debug(f"No listeners for event: {event_name}")
                return True
            
            # Listener'ları önceliğe göre sırala
            sorted_listeners = sorted(listeners, key=lambda x: x.priority.value, reverse=True)
            
            # Event'i listener'lara gönder
            if is_async:
                return self._emit_async(event, sorted_listeners)
            else:
                return self._emit_sync(event, sorted_listeners)
                
        except Exception as e:
            self.logger.error(f"Failed to emit event '{event_name}': {e}")
            return False
    
    def on(self, event_name: str, callback: Callable, priority: EventPriority = EventPriority.NORMAL,
           is_async: bool = False, once: bool = False) -> bool:
        """
        Event listener ekler.
        
        Args:
            event_name: Dinlenecek event adı
            callback: Callback fonksiyonu
            priority: Listener önceliği
            is_async: Async callback mi
            once: Sadece bir kez mi dinle
            
        Returns:
            True if listener added successfully, False otherwise
        """
        try:
            with self.lock:
                # Event listener oluştur
                listener = EventListener(
                    callback=callback,
                    priority=priority,
                    is_async=is_async,
                    once=once
                )
                
                # Listener'ı ekle
                if event_name not in self.listeners:
                    self.listeners[event_name] = []
                
                self.listeners[event_name].append(listener)
                
                # İstatistikleri güncelle
                self.stats["listeners_by_event"][event_name] = len(self.listeners[event_name])
                
                self.logger.debug(f"Added listener for event: {event_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add listener for event '{event_name}': {e}")
            return False
    
    def subscribe(self, event_name: str, callback: Callable, 
                 priority: EventPriority = EventPriority.NORMAL,
                 is_async: bool = False, once: bool = False) -> bool:
        """
        Subscribe to an event (alias for on method).
        
        Args:
            event_name: Event name to subscribe to
            callback: Callback function
            priority: Event priority
            is_async: Whether callback is async
            once: Whether to listen only once
            
        Returns:
            True if subscription successful, False otherwise
        """
        return self.on(event_name, callback, priority, is_async, once)
    
    def off(self, event_name: str, callback: Callable = None) -> bool:
        """
        Event listener kaldırır.
        
        Args:
            event_name: Event adı
            callback: Kaldırılacak callback (None ise tüm listener'lar kaldırılır)
            
        Returns:
            True if listener removed successfully, False otherwise
        """
        try:
            with self.lock:
                if event_name not in self.listeners:
                    return True
                
                if callback is None:
                    # Tüm listener'ları kaldır
                    del self.listeners[event_name]
                    if event_name in self.stats["listeners_by_event"]:
                        del self.stats["listeners_by_event"][event_name]
                else:
                    # Belirli callback'i kaldır
                    listeners = self.listeners[event_name]
                    self.listeners[event_name] = [
                        listener for listener in listeners 
                        if listener.callback != callback
                    ]
                    
                    # Boş liste ise event'i kaldır
                    if not self.listeners[event_name]:
                        del self.listeners[event_name]
                        if event_name in self.stats["listeners_by_event"]:
                            del self.stats["listeners_by_event"][event_name]
                    else:
                        self.stats["listeners_by_event"][event_name] = len(self.listeners[event_name])
                
                self.logger.debug(f"Removed listener for event: {event_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to remove listener for event '{event_name}': {e}")
            return False
    
    def once(self, event_name: str, callback: Callable, priority: EventPriority = EventPriority.NORMAL,
             is_async: bool = False) -> bool:
        """
        Event'i sadece bir kez dinler.
        
        Args:
            event_name: Dinlenecek event adı
            callback: Callback fonksiyonu
            priority: Listener önceliği
            is_async: Async callback mi
            
        Returns:
            True if listener added successfully, False otherwise
        """
        return self.on(event_name, callback, priority, is_async, once=True)
    
    def emit_async(self, event_name: str, data: Dict[str, Any] = None, 
                   source: str = "", priority: EventPriority = EventPriority.NORMAL) -> bool:
        """
        Async event gönderir.
        
        Args:
            event_name: Event adı
            data: Event verisi
            source: Event kaynağı
            priority: Event önceliği
            
        Returns:
            True if event emitted successfully, False otherwise
        """
        return self.emit(event_name, data, source, priority, is_async=True)
    
    def get_event_history(self, event_name: str = None, limit: int = 100) -> List[Event]:
        """
        Event geçmişini döndürür.
        
        Args:
            event_name: Belirli event adı (None ise tüm event'ler)
            limit: Maksimum event sayısı
            
        Returns:
            Event geçmişi
        """
        try:
            with self.lock:
                if event_name:
                    filtered_events = [
                        event for event in self.event_history 
                        if event.name == event_name
                    ]
                else:
                    filtered_events = self.event_history
                
                return filtered_events[-limit:] if filtered_events else []
                
        except Exception as e:
            self.logger.error(f"Failed to get event history: {e}")
            return []
    
    def get_listeners(self, event_name: str = None) -> Dict[str, List[EventListener]]:
        """
        Event listener'ları döndürür.
        
        Args:
            event_name: Belirli event adı (None ise tüm listener'lar)
            
        Returns:
            Event listener'ları
        """
        try:
            with self.lock:
                if event_name:
                    return {event_name: self.listeners.get(event_name, [])}
                else:
                    return self.listeners.copy()
                    
        except Exception as e:
            self.logger.error(f"Failed to get listeners: {e}")
            return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Event sistemi istatistiklerini döndürür.
        
        Returns:
            Event sistemi istatistikleri
        """
        try:
            with self.lock:
                return {
                    "is_running": self.is_running,
                    "total_events": self.stats["total_events"],
                    "events_by_name": self.stats["events_by_name"].copy(),
                    "listeners_by_event": self.stats["listeners_by_event"].copy(),
                    "async_events": self.stats["async_events"],
                    "sync_events": self.stats["sync_events"],
                    "total_listeners": sum(len(listeners) for listeners in self.listeners.values()),
                    "event_history_size": len(self.event_history),
                    "max_history_size": self.max_history_size
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get event system statistics: {e}")
            return {}
    
    def clear_history(self) -> bool:
        """
        Event geçmişini temizler.
        
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            with self.lock:
                self.event_history.clear()
                self.logger.info("Event history cleared")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to clear event history: {e}")
            return False
    
    def _emit_sync(self, event: Event, listeners: List[EventListener]) -> bool:
        """
        Sync event gönderir.
        
        Args:
            event: Gönderilecek event
            listeners: Event listener'ları
            
        Returns:
            True if event sent successfully, False otherwise
        """
        try:
            for listener in listeners:
                try:
                    # Event iptal edildi mi kontrol et
                    if event.is_cancelled:
                        break
                    
                    # Callback'i çağır
                    if listener.is_async:
                        # Async callback'i sync context'te çalıştır
                        if self.event_loop and not self.event_loop.is_closed():
                            future = asyncio.run_coroutine_threadsafe(
                                self._call_async_callback(listener.callback, event),
                                self.event_loop
                            )
                            future.result(timeout=30)  # 30 saniye timeout
                    else:
                        # Sync callback
                        listener.callback(event)
                    
                    # Once listener ise kaldır
                    if listener.once:
                        self.off(event.name, listener.callback)
                        
                except Exception as e:
                    self.logger.error(f"Error in event listener for '{event.name}': {e}")
                    continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to emit sync event '{event.name}': {e}")
            return False
    
    def _emit_async(self, event: Event, listeners: List[EventListener]) -> bool:
        """
        Async event gönderir.
        
        Args:
            event: Gönderilecek event
            listeners: Event listener'ları
            
        Returns:
            True if event sent successfully, False otherwise
        """
        try:
            if not self.event_loop or self.event_loop.is_closed():
                self.logger.error("Event loop not available for async event")
                return False
            
            # Async event'i event loop'da çalıştır
            future = asyncio.run_coroutine_threadsafe(
                self._emit_async_coroutine(event, listeners),
                self.event_loop
            )
            
            # Timeout ile bekle
            try:
                future.result(timeout=60)  # 60 saniye timeout
                return True
            except asyncio.TimeoutError:
                self.logger.error(f"Async event '{event.name}' timed out")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to emit async event '{event.name}': {e}")
            return False
    
    async def _emit_async_coroutine(self, event: Event, listeners: List[EventListener]):
        """
        Async event coroutine'i.
        
        Args:
            event: Gönderilecek event
            listeners: Event listener'ları
        """
        try:
            for listener in listeners:
                try:
                    # Event iptal edildi mi kontrol et
                    if event.is_cancelled:
                        break
                    
                    # Callback'i çağır
                    if listener.is_async:
                        # Async callback
                        await self._call_async_callback(listener.callback, event)
                    else:
                        # Sync callback'i async context'te çalıştır
                        await asyncio.get_event_loop().run_in_executor(
                            None, listener.callback, event
                        )
                    
                    # Once listener ise kaldır
                    if listener.once:
                        self.off(event.name, listener.callback)
                        
                except Exception as e:
                    self.logger.error(f"Error in async event listener for '{event.name}': {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to emit async event coroutine '{event.name}': {e}")
    
    async def _call_async_callback(self, callback: Callable, event: Event):
        """
        Async callback'i çağırır.
        
        Args:
            callback: Async callback fonksiyonu
            event: Event
        """
        try:
            # Callback'in async olup olmadığını kontrol et
            if inspect.iscoroutinefunction(callback):
                await callback(event)
            else:
                # Sync callback'i async olarak çalıştır
                await asyncio.get_event_loop().run_in_executor(None, callback, event)
                
        except Exception as e:
            self.logger.error(f"Error calling async callback: {e}")
            raise
    
    def _add_to_history(self, event: Event):
        """
        Event'i geçmişe ekler.
        
        Args:
            event: Eklenecek event
        """
        try:
            with self.lock:
                self.event_history.append(event)
                
                # Maksimum boyutu kontrol et
                if len(self.event_history) > self.max_history_size:
                    self.event_history.pop(0)
                    
        except Exception as e:
            self.logger.error(f"Failed to add event to history: {e}")
    
    def _update_stats(self, event: Event):
        """
        İstatistikleri günceller.
        
        Args:
            event: Event
        """
        try:
            self.stats["total_events"] += 1
            
            # Event adına göre say
            if event.name not in self.stats["events_by_name"]:
                self.stats["events_by_name"][event.name] = 0
            self.stats["events_by_name"][event.name] += 1
            
            # Async/Sync say
            if event.is_async:
                self.stats["async_events"] += 1
            else:
                self.stats["sync_events"] += 1
                
        except Exception as e:
            self.logger.error(f"Failed to update event statistics: {e}")


# Global instance
event_system = EventSystem()
