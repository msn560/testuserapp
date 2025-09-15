"""
System monitor for real-time system performance monitoring.

This module provides comprehensive system monitoring including CPU, memory,
disk, network, and process monitoring with real-time metrics collection.
"""

import asyncio
import psutil
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..db.models import SystemMetric, SystemLog
from ..core.constants import LogLevel
from ..utils.logger import logger


class MetricType(Enum):
    """System metric types."""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"
    PROCESS_COUNT = "process_count"
    LOAD_AVERAGE = "load_average"
    TEMPERATURE = "temperature"
    UPTIME = "uptime"


@dataclass
class SystemMetrics:
    """System metrics data structure."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_percent: float
    disk_used: int
    disk_total: int
    network_sent: int
    network_recv: int
    process_count: int
    load_average: List[float]
    temperature: Optional[float]
    uptime: float


class SystemMonitor:
    """
    System monitor for real-time system performance monitoring.
    
    This class provides comprehensive system monitoring including CPU, memory,
    disk, network, and process monitoring with real-time metrics collection.
    """
    
    def __init__(self, collection_interval: int = 5):
        """
        Initialize the system monitor.
        
        Args:
            collection_interval: Metrics collection interval in seconds
        """
        self.collection_interval = collection_interval
        self.is_running = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        self.logger = logger
        
        # Metrics storage
        self.current_metrics: Optional[SystemMetrics] = None
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000
        
        # Callbacks for real-time updates
        self.metrics_callbacks: List[Callable[[SystemMetrics], None]] = []
        self.alert_callbacks: List[Callable[[str, str], None]] = []
        
        # Alert thresholds
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 90.0,
            "disk_percent": 85.0,
            "load_average": 2.0,
            "temperature": 80.0
        }
        
        # Network monitoring
        self.last_network_stats = None
        self.network_start_time = None
    
    def start(self) -> bool:
        """
        Start the system monitor.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                self.logger.warning("System monitor is already running")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Initialize network monitoring
            self._init_network_monitoring()
            
            # Start monitor thread
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="SystemMonitor"
            )
            self.monitor_thread.start()
            
            self.logger.info("System monitor started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start system monitor: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the system monitor.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if not self.is_running:
                self.logger.warning("System monitor is not running")
                return True
            
            self.is_running = False
            self.stop_event.set()
            
            # Wait for monitor thread to finish
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=10)
            
            self.logger.info("System monitor stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop system monitor: {e}")
            return False
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """
        Get current system metrics.
        
        Returns:
            Current system metrics or None if not available
        """
        return self.current_metrics
    
    def get_metrics_history(self, limit: int = 100) -> List[SystemMetrics]:
        """
        Get metrics history.
        
        Args:
            limit: Maximum number of metrics to return
            
        Returns:
            List of historical metrics
        """
        return self.metrics_history[-limit:] if self.metrics_history else []
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary with averages and peaks.
        
        Returns:
            Dictionary with metrics summary
        """
        try:
            if not self.metrics_history:
                return {}
            
            # Calculate averages
            cpu_values = [m.cpu_percent for m in self.metrics_history]
            memory_values = [m.memory_percent for m in self.metrics_history]
            disk_values = [m.disk_percent for m in self.metrics_history]
            
            return {
                "cpu": {
                    "current": self.current_metrics.cpu_percent if self.current_metrics else 0,
                    "average": sum(cpu_values) / len(cpu_values),
                    "peak": max(cpu_values),
                    "min": min(cpu_values)
                },
                "memory": {
                    "current": self.current_metrics.memory_percent if self.current_metrics else 0,
                    "average": sum(memory_values) / len(memory_values),
                    "peak": max(memory_values),
                    "min": min(memory_values),
                    "used_gb": (self.current_metrics.memory_used / (1024**3)) if self.current_metrics else 0,
                    "total_gb": (self.current_metrics.memory_total / (1024**3)) if self.current_metrics else 0
                },
                "disk": {
                    "current": self.current_metrics.disk_percent if self.current_metrics else 0,
                    "average": sum(disk_values) / len(disk_values),
                    "peak": max(disk_values),
                    "min": min(disk_values),
                    "used_gb": (self.current_metrics.disk_used / (1024**3)) if self.current_metrics else 0,
                    "total_gb": (self.current_metrics.disk_total / (1024**3)) if self.current_metrics else 0
                },
                "process_count": self.current_metrics.process_count if self.current_metrics else 0,
                "uptime_hours": (self.current_metrics.uptime / 3600) if self.current_metrics else 0,
                "sample_count": len(self.metrics_history)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics summary: {e}")
            return {}
    
    def set_threshold(self, metric: str, threshold: float) -> bool:
        """
        Set alert threshold for a metric.
        
        Args:
            metric: Metric name
            threshold: Threshold value
            
        Returns:
            True if set successfully, False otherwise
        """
        try:
            if metric in self.thresholds:
                self.thresholds[metric] = threshold
                self.logger.info(f"Threshold set for {metric}: {threshold}")
                return True
            else:
                self.logger.warning(f"Unknown metric: {metric}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set threshold for {metric}: {e}")
            return False
    
    def add_metrics_callback(self, callback: Callable[[SystemMetrics], None]):
        """
        Add a callback for metrics updates.
        
        Args:
            callback: Function to call when metrics are updated
        """
        self.metrics_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable[[str, str], None]):
        """
        Add a callback for alerts.
        
        Args:
            callback: Function to call when alerts are triggered
        """
        self.alert_callbacks.append(callback)
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        try:
            self.logger.info("System monitor loop started")
            
            while self.is_running and not self.stop_event.is_set():
                try:
                    # Collect metrics
                    metrics = self._collect_metrics()
                    
                    if metrics:
                        # Update current metrics
                        self.current_metrics = metrics
                        
                        # Add to history
                        self.metrics_history.append(metrics)
                        
                        # Limit history size
                        if len(self.metrics_history) > self.max_history_size:
                            self.metrics_history.pop(0)
                        
                        # Store in database
                        self._store_metrics(metrics)
                        
                        # Check for alerts
                        self._check_alerts(metrics)
                        
                        # Notify callbacks
                        for callback in self.metrics_callbacks:
                            try:
                                callback(metrics)
                            except Exception as e:
                                self.logger.error(f"Error in metrics callback: {e}")
                    
                    # Wait for next collection
                    self.stop_event.wait(self.collection_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in monitor loop: {e}")
                    self.stop_event.wait(5)  # Wait longer on error
            
            self.logger.info("System monitor loop stopped")
            
        except Exception as e:
            self.logger.error(f"Fatal error in monitor loop: {e}")
    
    def _collect_metrics(self) -> Optional[SystemMetrics]:
        """
        Collect current system metrics.
        
        Returns:
            System metrics or None if collection failed
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network_sent, network_recv = self._get_network_io()
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix-like systems)
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                load_average = [0.0, 0.0, 0.0]  # Windows doesn't support load average
            
            # Temperature (if available)
            temperature = self._get_temperature()
            
            # Uptime
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used=memory.used,
                memory_total=memory.total,
                disk_percent=(disk.used / disk.total) * 100,
                disk_used=disk.used,
                disk_total=disk.total,
                network_sent=network_sent,
                network_recv=network_recv,
                process_count=process_count,
                load_average=load_average,
                temperature=temperature,
                uptime=uptime
            )
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
            return None
    
    def _init_network_monitoring(self):
        """Initialize network monitoring."""
        try:
            self.last_network_stats = psutil.net_io_counters()
            self.network_start_time = time.time()
        except Exception as e:
            self.logger.error(f"Failed to initialize network monitoring: {e}")
    
    def _get_network_io(self) -> tuple:
        """
        Get network I/O statistics.
        
        Returns:
            Tuple of (bytes_sent, bytes_received)
        """
        try:
            current_stats = psutil.net_io_counters()
            
            if self.last_network_stats:
                sent = current_stats.bytes_sent - self.last_network_stats.bytes_sent
                recv = current_stats.bytes_recv - self.last_network_stats.bytes_recv
                
                # Update last stats
                self.last_network_stats = current_stats
                
                return sent, recv
            else:
                self.last_network_stats = current_stats
                return 0, 0
                
        except Exception as e:
            self.logger.error(f"Failed to get network I/O: {e}")
            return 0, 0
    
    def _get_temperature(self) -> Optional[float]:
        """
        Get system temperature if available.
        
        Returns:
            Temperature in Celsius or None if not available
        """
        try:
            # Try to get temperature from psutil (if available)
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get the first available temperature
                    for name, entries in temps.items():
                        if entries:
                            return entries[0].current
            return None
            
        except Exception as e:
            self.logger.debug(f"Temperature not available: {e}")
            return None
    
    def _store_metrics(self, metrics: SystemMetrics):
        """
        Store metrics in the database.
        
        Args:
            metrics: System metrics to store
        """
        try:
            # Store CPU usage
            SystemMetric.create(
                metric_name=MetricType.CPU_USAGE.value,
                value=metrics.cpu_percent,
                unit="percent",
                tags=f'{{"timestamp": "{metrics.timestamp.isoformat()}"}}',
                recorded_at=metrics.timestamp
            )
            
            # Store memory usage
            SystemMetric.create(
                metric_name=MetricType.MEMORY_USAGE.value,
                value=metrics.memory_percent,
                unit="percent",
                tags=f'{{"timestamp": "{metrics.timestamp.isoformat()}"}}',
                recorded_at=metrics.timestamp
            )
            
            # Store disk usage
            SystemMetric.create(
                metric_name=MetricType.DISK_USAGE.value,
                value=metrics.disk_percent,
                unit="percent",
                tags=f'{{"timestamp": "{metrics.timestamp.isoformat()}"}}',
                recorded_at=metrics.timestamp
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {e}")
    
    def _check_alerts(self, metrics: SystemMetrics):
        """
        Check for alert conditions.
        
        Args:
            metrics: Current system metrics
        """
        try:
            # Check CPU usage
            if metrics.cpu_percent > self.thresholds["cpu_percent"]:
                self._trigger_alert("CPU", f"High CPU usage: {metrics.cpu_percent:.1f}%")
            
            # Check memory usage
            if metrics.memory_percent > self.thresholds["memory_percent"]:
                self._trigger_alert("Memory", f"High memory usage: {metrics.memory_percent:.1f}%")
            
            # Check disk usage
            if metrics.disk_percent > self.thresholds["disk_percent"]:
                self._trigger_alert("Disk", f"High disk usage: {metrics.disk_percent:.1f}%")
            
            # Check load average
            if metrics.load_average and metrics.load_average[0] > self.thresholds["load_average"]:
                self._trigger_alert("Load", f"High load average: {metrics.load_average[0]:.2f}")
            
            # Check temperature
            if metrics.temperature and metrics.temperature > self.thresholds["temperature"]:
                self._trigger_alert("Temperature", f"High temperature: {metrics.temperature:.1f}°C")
                
        except Exception as e:
            self.logger.error(f"Failed to check alerts: {e}")
    
    def _trigger_alert(self, alert_type: str, message: str):
        """
        Trigger an alert.
        
        Args:
            alert_type: Type of alert
            message: Alert message
        """
        try:
            # Log alert
            SystemLog.create(
                level=LogLevel.WARNING.value,
                module="system_monitor",
                message=f"ALERT [{alert_type}]: {message}",
                created_at=datetime.now()
            )
            
            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert_type, message)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")
            
            self.logger.warning(f"System alert: {alert_type} - {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger alert: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get system monitor status.
        
        Returns:
            Dictionary with monitor status information
        """
        try:
            return {
                "is_running": self.is_running,
                "collection_interval": self.collection_interval,
                "metrics_count": len(self.metrics_history),
                "current_metrics": self.current_metrics.__dict__ if self.current_metrics else None,
                "thresholds": self.thresholds,
                "callbacks_count": {
                    "metrics": len(self.metrics_callbacks),
                    "alerts": len(self.alert_callbacks)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get monitor status: {e}")
            return {"is_running": False, "error": str(e)}


# Global system monitor instance
system_monitor = SystemMonitor()
