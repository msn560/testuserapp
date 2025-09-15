"""
Database monitor for monitoring database performance and health.

This module provides comprehensive database monitoring including connection
monitoring, query performance tracking, and database health metrics.
"""

import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from collections import defaultdict, deque
from enum import Enum

from ..db.database import database
from ..db.models import SystemLog, SystemMetric
from ..core.constants import LogLevel
from ..utils.logger import logger


class QueryType(Enum):
    """Query type enumeration."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"
    OTHER = "OTHER"


@dataclass
class QueryMetrics:
    """Query metrics data structure."""
    timestamp: datetime
    query_type: QueryType
    query_text: str
    execution_time: float
    rows_affected: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class DatabaseMetrics:
    """Database metrics data structure."""
    timestamp: datetime
    connection_count: int
    active_connections: int
    total_queries: int
    slow_queries: int
    failed_queries: int
    average_query_time: float
    database_size: int
    table_count: int
    index_count: int
    cache_hit_ratio: float


class DatabaseMonitor:
    """
    Database monitor for monitoring database performance and health.
    
    This class provides comprehensive database monitoring including connection
    monitoring, query performance tracking, and database health metrics.
    """
    
    def __init__(self, collection_interval: int = 30, slow_query_threshold: float = 1.0):
        """
        Initialize the database monitor.
        
        Args:
            collection_interval: Metrics collection interval in seconds
            slow_query_threshold: Threshold for slow queries in seconds
        """
        self.collection_interval = collection_interval
        self.slow_query_threshold = slow_query_threshold
        self.is_running = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        self.logger = logger
        
        # Metrics storage
        self.query_history: deque = deque(maxlen=10000)
        self.current_metrics: Optional[DatabaseMetrics] = None
        self.metrics_history: List[DatabaseMetrics] = []
        self.max_history_size = 1000
        
        # Query tracking
        self.query_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "errors": 0
        })
        
        # Callbacks
        self.metrics_callbacks: List[Callable[[DatabaseMetrics], None]] = []
        self.alert_callbacks: List[Callable[[str, str], None]] = []
        
        # Alert thresholds
        self.thresholds = {
            "connection_count": 100,
            "slow_query_rate": 10.0,  # 10% slow queries
            "error_rate": 5.0,  # 5% error rate
            "average_query_time": 0.5,  # 500ms
            "cache_hit_ratio": 80.0  # 80% cache hit ratio
        }
        
        # Thread safety
        self.lock = threading.Lock()
    
    def start(self) -> bool:
        """
        Start the database monitor.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                self.logger.warning("Database monitor is already running")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Start monitor thread
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="DatabaseMonitor"
            )
            self.monitor_thread.start()
            
            self.logger.info("Database monitor started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start database monitor: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the database monitor.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if not self.is_running:
                self.logger.warning("Database monitor is not running")
                return True
            
            self.is_running = False
            self.stop_event.set()
            
            # Wait for monitor thread to finish
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=10)
            
            self.logger.info("Database monitor stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop database monitor: {e}")
            return False
    
    def log_query(self, query_metrics: QueryMetrics):
        """
        Log a database query.
        
        Args:
            query_metrics: Query metrics to log
        """
        try:
            with self.lock:
                # Add to history
                self.query_history.append(query_metrics)
                
                # Update query stats
                query_key = f"{query_metrics.query_type.value}:{query_metrics.query_text[:50]}"
                stats = self.query_stats[query_key]
                
                stats["count"] += 1
                stats["total_time"] += query_metrics.execution_time
                stats["min_time"] = min(stats["min_time"], query_metrics.execution_time)
                stats["max_time"] = max(stats["max_time"], query_metrics.execution_time)
                
                if not query_metrics.success:
                    stats["errors"] += 1
                
                # Check for slow queries
                if query_metrics.execution_time > self.slow_query_threshold:
                    self._log_slow_query(query_metrics)
                
                # Check for errors
                if not query_metrics.success:
                    self._log_query_error(query_metrics)
                
        except Exception as e:
            self.logger.error(f"Failed to log query: {e}")
    
    def get_current_metrics(self) -> Optional[DatabaseMetrics]:
        """
        Get current database metrics.
        
        Returns:
            Current database metrics or None if not available
        """
        return self.current_metrics
    
    def get_query_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get query statistics.
        
        Returns:
            Dictionary of query statistics
        """
        with self.lock:
            return dict(self.query_stats)
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get slow queries.
        
        Args:
            limit: Maximum number of slow queries to return
            
        Returns:
            List of slow queries with details
        """
        try:
            with self.lock:
                slow_queries = [
                    query for query in self.query_history
                    if query.execution_time > self.slow_query_threshold
                ]
                
                # Sort by execution time (descending)
                slow_queries.sort(key=lambda x: x.execution_time, reverse=True)
                
                return [
                    {
                        "timestamp": query.timestamp.isoformat(),
                        "query_type": query.query_type.value,
                        "query_text": query.query_text,
                        "execution_time": query.execution_time,
                        "rows_affected": query.rows_affected,
                        "success": query.success,
                        "error_message": query.error_message
                    }
                    for query in slow_queries[:limit]
                ]
                
        except Exception as e:
            self.logger.error(f"Failed to get slow queries: {e}")
            return []
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information.
        
        Returns:
            Dictionary with database information
        """
        try:
            # This would need to be implemented based on the specific database
            # For SQLite, we can get some basic information
            return {
                "database_type": "SQLite",
                "database_path": "data/app.db",
                "version": "3.x",
                "encoding": "UTF-8"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}")
            return {}
    
    def get_table_info(self) -> List[Dict[str, Any]]:
        """
        Get table information.
        
        Returns:
            List of table information
        """
        try:
            # This would need to be implemented based on the specific database
            # For SQLite, we can query the sqlite_master table
            tables = []
            
            # Placeholder implementation
            table_names = [
                "users", "roles", "permissions", "sessions", "api_keys",
                "config", "system_settings", "servers", "api_endpoints",
                "api_logs", "system_logs", "system_metrics", "alerts",
                "backups", "maintenance_tasks"
            ]
            
            for table_name in table_names:
                tables.append({
                    "name": table_name,
                    "row_count": 0,  # Would need to query actual count
                    "size_bytes": 0,  # Would need to calculate actual size
                    "index_count": 0,  # Would need to query actual index count
                    "last_modified": datetime.now().isoformat()
                })
            
            return tables
            
        except Exception as e:
            self.logger.error(f"Failed to get table info: {e}")
            return []
    
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
    
    def add_metrics_callback(self, callback: Callable[[DatabaseMetrics], None]):
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
            self.logger.info("Database monitor loop started")
            
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
            
            self.logger.info("Database monitor loop stopped")
            
        except Exception as e:
            self.logger.error(f"Fatal error in monitor loop: {e}")
    
    def _collect_metrics(self) -> Optional[DatabaseMetrics]:
        """
        Collect current database metrics.
        
        Returns:
            Database metrics or None if collection failed
        """
        try:
            with self.lock:
                # Basic metrics
                total_queries = len(self.query_history)
                slow_queries = sum(
                    1 for query in self.query_history
                    if query.execution_time > self.slow_query_threshold
                )
                failed_queries = sum(
                    1 for query in self.query_history
                    if not query.success
                )
                
                # Calculate average query time
                if total_queries > 0:
                    total_time = sum(query.execution_time for query in self.query_history)
                    average_query_time = total_time / total_queries
                else:
                    average_query_time = 0.0
                
                # Connection metrics (placeholder)
                connection_count = 1  # SQLite typically has one connection
                active_connections = 1
                
                # Database size (placeholder)
                database_size = 0  # Would need to get actual file size
                
                # Table and index counts (placeholder)
                table_count = len(self.get_table_info())
                index_count = 0  # Would need to query actual index count
                
                # Cache hit ratio (placeholder)
                cache_hit_ratio = 95.0  # SQLite doesn't expose this directly
                
                return DatabaseMetrics(
                    timestamp=datetime.now(),
                    connection_count=connection_count,
                    active_connections=active_connections,
                    total_queries=total_queries,
                    slow_queries=slow_queries,
                    failed_queries=failed_queries,
                    average_query_time=average_query_time,
                    database_size=database_size,
                    table_count=table_count,
                    index_count=index_count,
                    cache_hit_ratio=cache_hit_ratio
                )
                
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
            return None
    
    def _store_metrics(self, metrics: DatabaseMetrics):
        """
        Store metrics in the database.
        
        Args:
            metrics: Database metrics to store
        """
        try:
            # Store connection count
            SystemMetric.create(
                metric_name="database_connections",
                value=metrics.connection_count,
                unit="count",
                tags=f'{{"timestamp": "{metrics.timestamp.isoformat()}"}}',
                recorded_at=metrics.timestamp
            )
            
            # Store query count
            SystemMetric.create(
                metric_name="database_queries",
                value=metrics.total_queries,
                unit="count",
                tags=f'{{"timestamp": "{metrics.timestamp.isoformat()}"}}',
                recorded_at=metrics.timestamp
            )
            
            # Store average query time
            SystemMetric.create(
                metric_name="database_avg_query_time",
                value=metrics.average_query_time,
                unit="seconds",
                tags=f'{{"timestamp": "{metrics.timestamp.isoformat()}"}}',
                recorded_at=metrics.timestamp
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {e}")
    
    def _check_alerts(self, metrics: DatabaseMetrics):
        """
        Check for alert conditions.
        
        Args:
            metrics: Current database metrics
        """
        try:
            # Check connection count
            if metrics.connection_count > self.thresholds["connection_count"]:
                self._trigger_alert("Connections", f"High connection count: {metrics.connection_count}")
            
            # Check slow query rate
            if metrics.total_queries > 0:
                slow_query_rate = (metrics.slow_queries / metrics.total_queries) * 100
                if slow_query_rate > self.thresholds["slow_query_rate"]:
                    self._trigger_alert("Slow Queries", f"High slow query rate: {slow_query_rate:.1f}%")
            
            # Check error rate
            if metrics.total_queries > 0:
                error_rate = (metrics.failed_queries / metrics.total_queries) * 100
                if error_rate > self.thresholds["error_rate"]:
                    self._trigger_alert("Query Errors", f"High error rate: {error_rate:.1f}%")
            
            # Check average query time
            if metrics.average_query_time > self.thresholds["average_query_time"]:
                self._trigger_alert("Query Time", f"High average query time: {metrics.average_query_time:.3f}s")
            
            # Check cache hit ratio
            if metrics.cache_hit_ratio < self.thresholds["cache_hit_ratio"]:
                self._trigger_alert("Cache", f"Low cache hit ratio: {metrics.cache_hit_ratio:.1f}%")
                
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
                module="database_monitor",
                message=f"ALERT [{alert_type}]: {message}",
                created_at=datetime.now()
            )
            
            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert_type, message)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")
            
            self.logger.warning(f"Database alert: {alert_type} - {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger alert: {e}")
    
    def _log_slow_query(self, query_metrics: QueryMetrics):
        """
        Log a slow query.
        
        Args:
            query_metrics: Query metrics for the slow query
        """
        try:
            SystemLog.create(
                level=LogLevel.WARNING.value,
                module="database_monitor",
                message=f"Slow query detected: {query_metrics.query_type.value} - {query_metrics.execution_time:.3f}s",
                extra_data=f'{{"query": "{query_metrics.query_text[:100]}", "execution_time": {query_metrics.execution_time}}}',
                created_at=query_metrics.timestamp
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log slow query: {e}")
    
    def _log_query_error(self, query_metrics: QueryMetrics):
        """
        Log a query error.
        
        Args:
            query_metrics: Query metrics for the failed query
        """
        try:
            SystemLog.create(
                level=LogLevel.ERROR.value,
                module="database_monitor",
                message=f"Query error: {query_metrics.query_type.value} - {query_metrics.error_message}",
                extra_data=f'{{"query": "{query_metrics.query_text[:100]}", "error": "{query_metrics.error_message}"}}',
                created_at=query_metrics.timestamp
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log query error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get database monitor status.
        
        Returns:
            Dictionary with monitor status information
        """
        try:
            with self.lock:
                return {
                    "is_running": self.is_running,
                    "collection_interval": self.collection_interval,
                    "slow_query_threshold": self.slow_query_threshold,
                    "query_history_size": len(self.query_history),
                    "query_stats_count": len(self.query_stats),
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


# Global database monitor instance
database_monitor = DatabaseMonitor()
