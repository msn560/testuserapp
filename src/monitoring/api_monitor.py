"""
API monitor for monitoring API performance and usage statistics.

This module provides comprehensive API monitoring including request tracking,
response time monitoring, error rate tracking, and endpoint usage statistics.
"""

import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum

from ..db.models import ApiLog, SystemLog
from ..core.constants import LogLevel
from ..utils.logger import logger


class RequestStatus(Enum):
    """Request status enumeration."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


@dataclass
class ApiRequest:
    """API request data structure."""
    timestamp: datetime
    method: str
    path: str
    status_code: int
    response_time: float
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_size: int = 0
    response_size: int = 0


@dataclass
class EndpointStats:
    """Endpoint statistics data structure."""
    path: str
    method: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    last_request: Optional[datetime] = None
    unique_users: set = field(default_factory=set)
    unique_ips: set = field(default_factory=set)


@dataclass
class ApiMetrics:
    """API metrics data structure."""
    timestamp: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    requests_per_minute: float
    error_rate: float
    top_endpoints: List[Dict[str, Any]]
    response_time_distribution: Dict[str, int]
    status_code_distribution: Dict[int, int]


class ApiMonitor:
    """
    API monitor for monitoring API performance and usage statistics.
    
    This class provides comprehensive API monitoring including request tracking,
    response time monitoring, error rate tracking, and endpoint usage statistics.
    """
    
    def __init__(self, history_size: int = 10000, aggregation_interval: int = 60):
        """
        Initialize the API monitor.
        
        Args:
            history_size: Maximum number of requests to keep in memory
            aggregation_interval: Metrics aggregation interval in seconds
        """
        self.history_size = history_size
        self.aggregation_interval = aggregation_interval
        self.is_running = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        self.logger = logger
        
        # Request storage
        self.request_history: deque = deque(maxlen=history_size)
        self.endpoint_stats: Dict[str, EndpointStats] = {}
        
        # Metrics storage
        self.current_metrics: Optional[ApiMetrics] = None
        self.metrics_history: List[ApiMetrics] = []
        self.max_history_size = 1000
        
        # Callbacks
        self.metrics_callbacks: List[Callable[[ApiMetrics], None]] = []
        self.alert_callbacks: List[Callable[[str, str], None]] = []
        
        # Alert thresholds
        self.thresholds = {
            "error_rate": 5.0,  # 5% error rate
            "response_time": 1000.0,  # 1 second
            "requests_per_minute": 1000.0  # 1000 requests per minute
        }
        
        # Rate limiting tracking
        self.rate_limit_violations: Dict[str, int] = defaultdict(int)
        
        # Thread safety
        self.lock = threading.Lock()
    
    def start(self) -> bool:
        """
        Start the API monitor.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                self.logger.warning("API monitor is already running")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Start monitor thread
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="ApiMonitor"
            )
            self.monitor_thread.start()
            
            self.logger.info("API monitor started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start API monitor: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the API monitor.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if not self.is_running:
                self.logger.warning("API monitor is not running")
                return True
            
            self.is_running = False
            self.stop_event.set()
            
            # Wait for monitor thread to finish
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=10)
            
            self.logger.info("API monitor stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop API monitor: {e}")
            return False
    
    def log_request(self, request: ApiRequest):
        """
        Log an API request.
        
        Args:
            request: API request to log
        """
        try:
            with self.lock:
                # Add to history
                self.request_history.append(request)
                
                # Update endpoint stats
                endpoint_key = f"{request.method}:{request.path}"
                if endpoint_key not in self.endpoint_stats:
                    self.endpoint_stats[endpoint_key] = EndpointStats(
                        path=request.path,
                        method=request.method
                    )
                
                stats = self.endpoint_stats[endpoint_key]
                stats.total_requests += 1
                stats.total_response_time += request.response_time
                stats.min_response_time = min(stats.min_response_time, request.response_time)
                stats.max_response_time = max(stats.max_response_time, request.response_time)
                stats.last_request = request.timestamp
                
                if 200 <= request.status_code < 400:
                    stats.successful_requests += 1
                else:
                    stats.failed_requests += 1
                
                if request.user_id:
                    stats.unique_users.add(request.user_id)
                
                if request.ip_address:
                    stats.unique_ips.add(request.ip_address)
                
                # Store in database
                self._store_request(request)
                
        except Exception as e:
            self.logger.error(f"Failed to log request: {e}")
    
    def get_current_metrics(self) -> Optional[ApiMetrics]:
        """
        Get current API metrics.
        
        Returns:
            Current API metrics or None if not available
        """
        return self.current_metrics
    
    def get_endpoint_stats(self, endpoint: str = None) -> Dict[str, EndpointStats]:
        """
        Get endpoint statistics.
        
        Args:
            endpoint: Specific endpoint to get stats for, or None for all
            
        Returns:
            Dictionary of endpoint statistics
        """
        with self.lock:
            if endpoint:
                return {endpoint: self.endpoint_stats.get(endpoint)}
            return self.endpoint_stats.copy()
    
    def get_top_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top endpoints by request count.
        
        Args:
            limit: Maximum number of endpoints to return
            
        Returns:
            List of top endpoints with statistics
        """
        try:
            with self.lock:
                sorted_endpoints = sorted(
                    self.endpoint_stats.values(),
                    key=lambda x: x.total_requests,
                    reverse=True
                )
                
                top_endpoints = []
                for stats in sorted_endpoints[:limit]:
                    avg_response_time = (
                        stats.total_response_time / stats.total_requests
                        if stats.total_requests > 0 else 0
                    )
                    
                    top_endpoints.append({
                        "endpoint": f"{stats.method} {stats.path}",
                        "total_requests": stats.total_requests,
                        "successful_requests": stats.successful_requests,
                        "failed_requests": stats.failed_requests,
                        "success_rate": (
                            stats.successful_requests / stats.total_requests * 100
                            if stats.total_requests > 0 else 0
                        ),
                        "average_response_time": avg_response_time,
                        "min_response_time": stats.min_response_time if stats.min_response_time != float('inf') else 0,
                        "max_response_time": stats.max_response_time,
                        "unique_users": len(stats.unique_users),
                        "unique_ips": len(stats.unique_ips),
                        "last_request": stats.last_request.isoformat() if stats.last_request else None
                    })
                
                return top_endpoints
                
        except Exception as e:
            self.logger.error(f"Failed to get top endpoints: {e}")
            return []
    
    def get_response_time_distribution(self) -> Dict[str, int]:
        """
        Get response time distribution.
        
        Returns:
            Dictionary with response time ranges and counts
        """
        try:
            with self.lock:
                distribution = {
                    "0-100ms": 0,
                    "100-500ms": 0,
                    "500ms-1s": 0,
                    "1s-5s": 0,
                    "5s+": 0
                }
                
                for request in self.request_history:
                    response_time = request.response_time
                    if response_time < 0.1:
                        distribution["0-100ms"] += 1
                    elif response_time < 0.5:
                        distribution["100-500ms"] += 1
                    elif response_time < 1.0:
                        distribution["500ms-1s"] += 1
                    elif response_time < 5.0:
                        distribution["1s-5s"] += 1
                    else:
                        distribution["5s+"] += 1
                
                return distribution
                
        except Exception as e:
            self.logger.error(f"Failed to get response time distribution: {e}")
            return {}
    
    def get_status_code_distribution(self) -> Dict[int, int]:
        """
        Get status code distribution.
        
        Returns:
            Dictionary with status codes and counts
        """
        try:
            with self.lock:
                distribution = defaultdict(int)
                
                for request in self.request_history:
                    distribution[request.status_code] += 1
                
                return dict(distribution)
                
        except Exception as e:
            self.logger.error(f"Failed to get status code distribution: {e}")
            return {}
    
    def get_requests_per_minute(self) -> float:
        """
        Get current requests per minute.
        
        Returns:
            Requests per minute
        """
        try:
            with self.lock:
                now = datetime.now()
                one_minute_ago = now - timedelta(minutes=1)
                
                recent_requests = [
                    req for req in self.request_history
                    if req.timestamp >= one_minute_ago
                ]
                
                return len(recent_requests)
                
        except Exception as e:
            self.logger.error(f"Failed to get requests per minute: {e}")
            return 0.0
    
    def get_error_rate(self) -> float:
        """
        Get current error rate percentage.
        
        Returns:
            Error rate percentage
        """
        try:
            with self.lock:
                if not self.request_history:
                    return 0.0
                
                total_requests = len(self.request_history)
                failed_requests = sum(
                    1 for req in self.request_history
                    if req.status_code >= 400
                )
                
                return (failed_requests / total_requests) * 100
                
        except Exception as e:
            self.logger.error(f"Failed to get error rate: {e}")
            return 0.0
    
    def get_average_response_time(self) -> float:
        """
        Get average response time.
        
        Returns:
            Average response time in milliseconds
        """
        try:
            with self.lock:
                if not self.request_history:
                    return 0.0
                
                total_time = sum(req.response_time for req in self.request_history)
                return total_time / len(self.request_history)
                
        except Exception as e:
            self.logger.error(f"Failed to get average response time: {e}")
            return 0.0
    
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
    
    def add_metrics_callback(self, callback: Callable[[ApiMetrics], None]):
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
            self.logger.info("API monitor loop started")
            
            while self.is_running and not self.stop_event.is_set():
                try:
                    # Calculate metrics
                    metrics = self._calculate_metrics()
                    
                    if metrics:
                        # Update current metrics
                        self.current_metrics = metrics
                        
                        # Add to history
                        self.metrics_history.append(metrics)
                        
                        # Limit history size
                        if len(self.metrics_history) > self.max_history_size:
                            self.metrics_history.pop(0)
                        
                        # Check for alerts
                        self._check_alerts(metrics)
                        
                        # Notify callbacks
                        for callback in self.metrics_callbacks:
                            try:
                                callback(metrics)
                            except Exception as e:
                                self.logger.error(f"Error in metrics callback: {e}")
                    
                    # Wait for next aggregation
                    self.stop_event.wait(self.aggregation_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in monitor loop: {e}")
                    self.stop_event.wait(5)  # Wait longer on error
            
            self.logger.info("API monitor loop stopped")
            
        except Exception as e:
            self.logger.error(f"Fatal error in monitor loop: {e}")
    
    def _calculate_metrics(self) -> Optional[ApiMetrics]:
        """
        Calculate current API metrics.
        
        Returns:
            API metrics or None if calculation failed
        """
        try:
            with self.lock:
                if not self.request_history:
                    return None
                
                # Basic metrics
                total_requests = len(self.request_history)
                successful_requests = sum(
                    1 for req in self.request_history
                    if 200 <= req.status_code < 400
                )
                failed_requests = total_requests - successful_requests
                
                # Response time metrics
                response_times = [req.response_time for req in self.request_history]
                average_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                # Rate metrics
                requests_per_minute = self.get_requests_per_minute()
                error_rate = self.get_error_rate()
                
                # Top endpoints
                top_endpoints = self.get_top_endpoints(5)
                
                # Distributions
                response_time_distribution = self.get_response_time_distribution()
                status_code_distribution = self.get_status_code_distribution()
                
                return ApiMetrics(
                    timestamp=datetime.now(),
                    total_requests=total_requests,
                    successful_requests=successful_requests,
                    failed_requests=failed_requests,
                    average_response_time=average_response_time,
                    requests_per_minute=requests_per_minute,
                    error_rate=error_rate,
                    top_endpoints=top_endpoints,
                    response_time_distribution=response_time_distribution,
                    status_code_distribution=status_code_distribution
                )
                
        except Exception as e:
            self.logger.error(f"Failed to calculate metrics: {e}")
            return None
    
    def _store_request(self, request: ApiRequest):
        """
        Store request in the database.
        
        Args:
            request: API request to store
        """
        try:
            ApiLog.create(
                endpoint_id=None,  # Would need endpoint mapping
                user_id=request.user_id,
                method=request.method,
                path=request.path,
                status_code=request.status_code,
                response_time=request.response_time,
                ip_address=request.ip_address,
                user_agent=request.user_agent,
                created_at=request.timestamp
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store request: {e}")
    
    def _check_alerts(self, metrics: ApiMetrics):
        """
        Check for alert conditions.
        
        Args:
            metrics: Current API metrics
        """
        try:
            # Check error rate
            if metrics.error_rate > self.thresholds["error_rate"]:
                self._trigger_alert("Error Rate", f"High error rate: {metrics.error_rate:.1f}%")
            
            # Check response time
            if metrics.average_response_time > self.thresholds["response_time"]:
                self._trigger_alert("Response Time", f"High response time: {metrics.average_response_time:.1f}ms")
            
            # Check requests per minute
            if metrics.requests_per_minute > self.thresholds["requests_per_minute"]:
                self._trigger_alert("Request Rate", f"High request rate: {metrics.requests_per_minute:.1f} req/min")
                
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
                module="api_monitor",
                message=f"ALERT [{alert_type}]: {message}",
                created_at=datetime.now()
            )
            
            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert_type, message)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")
            
            self.logger.warning(f"API alert: {alert_type} - {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger alert: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get API monitor status.
        
        Returns:
            Dictionary with monitor status information
        """
        try:
            with self.lock:
                return {
                    "is_running": self.is_running,
                    "aggregation_interval": self.aggregation_interval,
                    "request_history_size": len(self.request_history),
                    "endpoint_stats_count": len(self.endpoint_stats),
                    "metrics_history_size": len(self.metrics_history),
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


# Global API monitor instance
api_monitor = ApiMonitor()
