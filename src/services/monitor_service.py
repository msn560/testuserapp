"""
Monitor Service module - Sistem izleme

Bu modül sistem performansı, API metrikleri ve veritabanı durumunu izler.
Real-time monitoring, alerting ve istatistik toplama.
"""

import asyncio
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import time

from ..monitoring.system_monitor import system_monitor
from ..monitoring.api_monitor import api_monitor
from ..monitoring.database_monitor import database_monitor
from ..monitoring.alert_system import alert_system
from ..core.constants import LogLevel
from ..utils.logger import logger


class MonitorService:
    """
    Sistem izleme servisi.
    
    Bu sınıf sistem performansı, API metrikleri ve veritabanı durumunu izler.
    """
    
    def __init__(self, monitoring_interval: int = 30):
        """
        MonitorService'i başlatır.
        
        Args:
            monitoring_interval: İzleme aralığı (saniye)
        """
        self.logger = logger
        self.monitoring_interval = monitoring_interval
        self.is_running = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # İzleme bileşenleri
        self.system_monitor = system_monitor
        self.api_monitor = api_monitor
        self.database_monitor = database_monitor
        self.alert_system = alert_system
        
        # Callback'ler
        self.metrics_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        # İstatistikler
        self.stats = {
            "monitoring_cycles": 0,
            "alerts_triggered": 0,
            "last_monitoring_time": None,
            "monitoring_errors": 0
        }
        
        # Thread safety
        self.lock = threading.Lock()
    
    def start(self) -> bool:
        """
        İzleme servisini başlatır.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                self.logger.warning("Monitor service is already running")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Alert sistemini başlat
            if not self.alert_system.start():
                self.logger.error("Failed to start alert system")
                return False
            
            # İzleme thread'ini başlat
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="MonitorService"
            )
            self.monitor_thread.start()
            
            self.logger.info("Monitor service started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitor service: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        İzleme servisini durdurur.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if not self.is_running:
                self.logger.warning("Monitor service is not running")
                return True
            
            self.is_running = False
            self.stop_event.set()
            
            # İzleme thread'ini bekle
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=10)
            
            # Alert sistemini durdur
            self.alert_system.stop()
            
            self.logger.info("Monitor service stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop monitor service: {e}")
            return False
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Sistem metriklerini döndürür.
        
        Returns:
            Sistem metrikleri
        """
        try:
            # Asenkron metrikleri senkron olarak al
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                cpu_usage = loop.run_until_complete(self.system_monitor.get_cpu_usage())
                memory_usage = loop.run_until_complete(self.system_monitor.get_memory_usage())
                disk_usage = loop.run_until_complete(self.system_monitor.get_disk_usage())
                network_io = loop.run_until_complete(self.system_monitor.get_network_io())
                system_info = loop.run_until_complete(self.system_monitor.get_system_info())
                process_list = loop.run_until_complete(self.system_monitor.get_process_list(limit=10))
                
                return {
                    "cpu": cpu_usage,
                    "memory": memory_usage,
                    "disk": disk_usage,
                    "network": network_io,
                    "system": system_info,
                    "processes": process_list,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """
        API metriklerini döndürür.
        
        Returns:
            API metrikleri
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                general_metrics = loop.run_until_complete(self.api_monitor.get_api_metrics())
                endpoint_metrics = loop.run_until_complete(self.api_monitor.get_endpoint_metrics())
                
                return {
                    "general": general_metrics,
                    "endpoints": endpoint_metrics,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Failed to get API metrics: {e}")
            return {}
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """
        Veritabanı metriklerini döndürür.
        
        Returns:
            Veritabanı metrikleri
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                connection_status = loop.run_until_complete(self.database_monitor.get_db_connection_status())
                table_sizes = loop.run_until_complete(self.database_monitor.get_table_sizes())
                query_performance = loop.run_until_complete(self.database_monitor.get_query_performance())
                
                return {
                    "connection": connection_status,
                    "table_sizes": table_sizes,
                    "query_performance": query_performance,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Failed to get database metrics: {e}")
            return {}
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Tüm metrikleri döndürür.
        
        Returns:
            Tüm metrikler
        """
        try:
            return {
                "system": self.get_system_metrics(),
                "api": self.get_api_metrics(),
                "database": self.get_database_metrics(),
                "alerts": self.get_active_alerts(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get all metrics: {e}")
            return {}
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Aktif alert'leri döndürür.
        
        Returns:
            Aktif alert listesi
        """
        try:
            alerts = self.alert_system.get_active_alerts()
            return [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity,
                    "status": alert.status,
                    "created_at": alert.created_at.isoformat(),
                    "rule_name": alert.rule_name
                }
                for alert in alerts
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get active alerts: {e}")
            return []
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        Alert istatistiklerini döndürür.
        
        Returns:
            Alert istatistikleri
        """
        try:
            return self.alert_system.get_alert_statistics()
            
        except Exception as e:
            self.logger.error(f"Failed to get alert statistics: {e}")
            return {}
    
    def acknowledge_alert(self, alert_id: int, user_id: int, note: str = None) -> bool:
        """
        Alert'i onaylar.
        
        Args:
            alert_id: Alert ID'si
            user_id: Kullanıcı ID'si
            note: Not
            
        Returns:
            True if acknowledged successfully, False otherwise
        """
        try:
            return self.alert_system.acknowledge_alert(alert_id, user_id, note)
            
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False
    
    def resolve_alert(self, alert_id: int, user_id: int, resolution: str = None) -> bool:
        """
        Alert'i çözer.
        
        Args:
            alert_id: Alert ID'si
            user_id: Kullanıcı ID'si
            resolution: Çözüm açıklaması
            
        Returns:
            True if resolved successfully, False otherwise
        """
        try:
            return self.alert_system.resolve_alert(alert_id, user_id, resolution)
            
        except Exception as e:
            self.logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False
    
    def add_metrics_callback(self, callback: Callable):
        """
        Metrik callback'i ekler.
        
        Args:
            callback: Callback fonksiyonu
        """
        self.metrics_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable):
        """
        Alert callback'i ekler.
        
        Args:
            callback: Callback fonksiyonu
        """
        self.alert_callbacks.append(callback)
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """
        İzleme durumunu döndürür.
        
        Returns:
            İzleme durumu
        """
        try:
            with self.lock:
                return {
                    "is_running": self.is_running,
                    "monitoring_interval": self.monitoring_interval,
                    "monitoring_cycles": self.stats["monitoring_cycles"],
                    "alerts_triggered": self.stats["alerts_triggered"],
                    "last_monitoring_time": self.stats["last_monitoring_time"],
                    "monitoring_errors": self.stats["monitoring_errors"],
                    "alert_system_status": self.alert_system.get_status(),
                    "callbacks_count": {
                        "metrics": len(self.metrics_callbacks),
                        "alerts": len(self.alert_callbacks)
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get monitoring status: {e}")
            return {}
    
    def _monitoring_loop(self):
        """İzleme döngüsü."""
        try:
            self.logger.info("Monitoring loop started")
            
            while self.is_running and not self.stop_event.is_set():
                try:
                    # Metrikleri topla
                    metrics = self.get_all_metrics()
                    
                    # Alert'leri kontrol et
                    self._check_alerts(metrics)
                    
                    # Callback'leri çağır
                    for callback in self.metrics_callbacks:
                        try:
                            callback(metrics)
                        except Exception as e:
                            self.logger.error(f"Error in metrics callback: {e}")
                    
                    # İstatistikleri güncelle
                    with self.lock:
                        self.stats["monitoring_cycles"] += 1
                        self.stats["last_monitoring_time"] = datetime.now().isoformat()
                    
                    # Bekle
                    self.stop_event.wait(self.monitoring_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    with self.lock:
                        self.stats["monitoring_errors"] += 1
                    self.stop_event.wait(60)  # Hata durumunda daha uzun bekle
            
            self.logger.info("Monitoring loop stopped")
            
        except Exception as e:
            self.logger.error(f"Fatal error in monitoring loop: {e}")
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """
        Alert'leri kontrol eder.
        
        Args:
            metrics: Toplanan metrikler
        """
        try:
            system_metrics = metrics.get("system", {})
            
            # CPU kullanımı kontrolü
            cpu_percent = system_metrics.get("cpu", {}).get("total_percent", 0)
            if cpu_percent > 80:
                self.alert_system.create_alert(
                    "high_cpu_usage",
                    f"High CPU usage detected: {cpu_percent}%",
                    metadata={"cpu_percent": cpu_percent}
                )
            
            # Bellek kullanımı kontrolü
            memory_percent = system_metrics.get("memory", {}).get("percent", 0)
            if memory_percent > 85:
                self.alert_system.create_alert(
                    "high_memory_usage",
                    f"High memory usage detected: {memory_percent}%",
                    metadata={"memory_percent": memory_percent}
                )
            
            # Disk kullanımı kontrolü
            disk_percent = system_metrics.get("disk", {}).get("percent", 0)
            if disk_percent > 90:
                self.alert_system.create_alert(
                    "low_disk_space",
                    f"Low disk space detected: {disk_percent}%",
                    metadata={"disk_percent": disk_percent}
                )
            
            # API hata oranı kontrolü
            api_metrics = metrics.get("api", {})
            error_rate = api_metrics.get("general", {}).get("error_rate_percent", 0)
            if error_rate > 10:
                self.alert_system.create_alert(
                    "high_api_error_rate",
                    f"High API error rate detected: {error_rate}%",
                    metadata={"error_rate": error_rate}
                )
            
            # Veritabanı bağlantı kontrolü
            db_metrics = metrics.get("database", {})
            is_connected = db_metrics.get("connection", {}).get("is_connected", True)
            if not is_connected:
                self.alert_system.create_alert(
                    "database_connection_error",
                    "Database connection error detected",
                    metadata={"connection_status": is_connected}
                )
            
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")


# Global instance
monitor_service = MonitorService()
