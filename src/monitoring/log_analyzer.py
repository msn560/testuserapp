"""
Log analyzer for analyzing and processing system logs.

This module provides comprehensive log analysis including log parsing,
pattern detection, error analysis, and log statistics.
"""

import re
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Pattern
from dataclasses import dataclass
from collections import defaultdict, Counter
from enum import Enum

from ..db.models import SystemLog
from ..core.constants import LogLevel
from ..utils.logger import logger


class LogPattern(Enum):
    """Log pattern types."""
    ERROR_PATTERN = "error_pattern"
    WARNING_PATTERN = "warning_pattern"
    AUTHENTICATION_PATTERN = "auth_pattern"
    API_REQUEST_PATTERN = "api_request_pattern"
    DATABASE_PATTERN = "database_pattern"
    SECURITY_PATTERN = "security_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"


@dataclass
class LogEntry:
    """Log entry data structure."""
    timestamp: datetime
    level: LogLevel
    module: str
    message: str
    extra_data: Optional[str] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = None


@dataclass
class LogAnalysis:
    """Log analysis data structure."""
    timestamp: datetime
    total_logs: int
    error_count: int
    warning_count: int
    info_count: int
    debug_count: int
    critical_count: int
    top_modules: List[Dict[str, Any]]
    top_errors: List[Dict[str, Any]]
    error_rate: float
    log_volume_per_hour: List[Dict[str, Any]]
    pattern_matches: Dict[str, int]


class LogAnalyzer:
    """
    Log analyzer for analyzing and processing system logs.
    
    This class provides comprehensive log analysis including log parsing,
    pattern detection, error analysis, and log statistics.
    """
    
    def __init__(self, analysis_interval: int = 300):  # 5 minutes
        """
        Initialize the log analyzer.
        
        Args:
            analysis_interval: Analysis interval in seconds
        """
        self.analysis_interval = analysis_interval
        self.is_running = False
        self.analyzer_thread = None
        self.stop_event = threading.Event()
        self.logger = logger
        
        # Analysis storage
        self.current_analysis: Optional[LogAnalysis] = None
        self.analysis_history: List[LogAnalysis] = []
        self.max_history_size = 100
        
        # Pattern definitions
        self.patterns = self._define_patterns()
        
        # Callbacks
        self.analysis_callbacks: List[Callable[[LogAnalysis], None]] = []
        self.alert_callbacks: List[Callable[[str, str], None]] = []
        
        # Alert thresholds
        self.thresholds = {
            "error_rate": 10.0,  # 10% error rate
            "critical_count": 5,  # 5 critical logs
            "log_volume": 1000,  # 1000 logs per hour
            "pattern_matches": 50  # 50 pattern matches
        }
        
        # Thread safety
        self.lock = threading.Lock()
    
    def start(self) -> bool:
        """
        Start the log analyzer.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                self.logger.warning("Log analyzer is already running")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Start analyzer thread
            self.analyzer_thread = threading.Thread(
                target=self._analyzer_loop,
                daemon=True,
                name="LogAnalyzer"
            )
            self.analyzer_thread.start()
            
            self.logger.info("Log analyzer started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start log analyzer: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the log analyzer.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if not self.is_running:
                self.logger.warning("Log analyzer is not running")
                return True
            
            self.is_running = False
            self.stop_event.set()
            
            # Wait for analyzer thread to finish
            if self.analyzer_thread and self.analyzer_thread.is_alive():
                self.analyzer_thread.join(timeout=10)
            
            self.logger.info("Log analyzer stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop log analyzer: {e}")
            return False
    
    def analyze_logs(self, start_time: datetime = None, end_time: datetime = None) -> LogAnalysis:
        """
        Analyze logs for a specific time period.
        
        Args:
            start_time: Start time for analysis (default: last hour)
            end_time: End time for analysis (default: now)
            
        Returns:
            Log analysis results
        """
        try:
            # Set default time range
            if not end_time:
                end_time = datetime.now()
            if not start_time:
                start_time = end_time - timedelta(hours=1)
            
            # Query logs from database
            logs = self._get_logs(start_time, end_time)
            
            # Perform analysis
            analysis = self._perform_analysis(logs, start_time, end_time)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze logs: {e}")
            return None
    
    def get_current_analysis(self) -> Optional[LogAnalysis]:
        """
        Get current log analysis.
        
        Returns:
            Current log analysis or None if not available
        """
        return self.current_analysis
    
    def get_analysis_history(self, limit: int = 10) -> List[LogAnalysis]:
        """
        Get analysis history.
        
        Args:
            limit: Maximum number of analyses to return
            
        Returns:
            List of historical analyses
        """
        return self.analysis_history[-limit:] if self.analysis_history else []
    
    def search_logs(self, query: str, start_time: datetime = None, end_time: datetime = None) -> List[LogEntry]:
        """
        Search logs with a query.
        
        Args:
            query: Search query
            start_time: Start time for search
            end_time: End time for search
            
        Returns:
            List of matching log entries
        """
        try:
            # Set default time range
            if not end_time:
                end_time = datetime.now()
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            # Query logs from database
            logs = self._get_logs(start_time, end_time)
            
            # Filter logs based on query
            matching_logs = []
            query_lower = query.lower()
            
            for log in logs:
                if (query_lower in log.message.lower() or
                    query_lower in log.module.lower() or
                    query_lower in log.level.value.lower()):
                    matching_logs.append(log)
            
            return matching_logs
            
        except Exception as e:
            self.logger.error(f"Failed to search logs: {e}")
            return []
    
    def get_log_statistics(self, start_time: datetime = None, end_time: datetime = None) -> Dict[str, Any]:
        """
        Get log statistics for a time period.
        
        Args:
            start_time: Start time for statistics
            end_time: End time for statistics
            
        Returns:
            Dictionary with log statistics
        """
        try:
            # Set default time range
            if not end_time:
                end_time = datetime.now()
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            # Query logs from database
            logs = self._get_logs(start_time, end_time)
            
            # Calculate statistics
            total_logs = len(logs)
            level_counts = Counter(log.level.value for log in logs)
            module_counts = Counter(log.module for log in logs)
            
            # Calculate hourly distribution
            hourly_distribution = defaultdict(int)
            for log in logs:
                hour = log.timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_distribution[hour] += 1
            
            return {
                "total_logs": total_logs,
                "level_distribution": dict(level_counts),
                "module_distribution": dict(module_counts),
                "hourly_distribution": dict(hourly_distribution),
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get log statistics: {e}")
            return {}
    
    def detect_anomalies(self, start_time: datetime = None, end_time: datetime = None) -> List[Dict[str, Any]]:
        """
        Detect anomalies in logs.
        
        Args:
            start_time: Start time for anomaly detection
            end_time: End time for anomaly detection
            
        Returns:
            List of detected anomalies
        """
        try:
            # Set default time range
            if not end_time:
                end_time = datetime.now()
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            # Query logs from database
            logs = self._get_logs(start_time, end_time)
            
            anomalies = []
            
            # Detect error spikes
            error_spikes = self._detect_error_spikes(logs)
            anomalies.extend(error_spikes)
            
            # Detect unusual patterns
            unusual_patterns = self._detect_unusual_patterns(logs)
            anomalies.extend(unusual_patterns)
            
            # Detect high volume periods
            volume_anomalies = self._detect_volume_anomalies(logs)
            anomalies.extend(volume_anomalies)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Failed to detect anomalies: {e}")
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
    
    def add_analysis_callback(self, callback: Callable[[LogAnalysis], None]):
        """
        Add a callback for analysis updates.
        
        Args:
            callback: Function to call when analysis is updated
        """
        self.analysis_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable[[str, str], None]):
        """
        Add a callback for alerts.
        
        Args:
            callback: Function to call when alerts are triggered
        """
        self.alert_callbacks.append(callback)
    
    def _define_patterns(self) -> Dict[LogPattern, Pattern]:
        """
        Define log patterns for analysis.
        
        Returns:
            Dictionary of compiled regex patterns
        """
        patterns = {
            LogPattern.ERROR_PATTERN: re.compile(r'(?i)(error|exception|failed|failure)'),
            LogPattern.WARNING_PATTERN: re.compile(r'(?i)(warning|warn|caution)'),
            LogPattern.AUTHENTICATION_PATTERN: re.compile(r'(?i)(auth|login|logout|token|session)'),
            LogPattern.API_REQUEST_PATTERN: re.compile(r'(?i)(api|request|response|endpoint)'),
            LogPattern.DATABASE_PATTERN: re.compile(r'(?i)(database|db|query|sql|connection)'),
            LogPattern.SECURITY_PATTERN: re.compile(r'(?i)(security|attack|intrusion|breach|unauthorized)'),
            LogPattern.PERFORMANCE_PATTERN: re.compile(r'(?i)(slow|timeout|performance|latency|response time)')
        }
        return patterns
    
    def _analyzer_loop(self):
        """Main analyzer loop that runs in a separate thread."""
        try:
            self.logger.info("Log analyzer loop started")
            
            while self.is_running and not self.stop_event.is_set():
                try:
                    # Perform analysis
                    analysis = self.analyze_logs()
                    
                    if analysis:
                        # Update current analysis
                        self.current_analysis = analysis
                        
                        # Add to history
                        self.analysis_history.append(analysis)
                        
                        # Limit history size
                        if len(self.analysis_history) > self.max_history_size:
                            self.analysis_history.pop(0)
                        
                        # Check for alerts
                        self._check_alerts(analysis)
                        
                        # Notify callbacks
                        for callback in self.analysis_callbacks:
                            try:
                                callback(analysis)
                            except Exception as e:
                                self.logger.error(f"Error in analysis callback: {e}")
                    
                    # Wait for next analysis
                    self.stop_event.wait(self.analysis_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in analyzer loop: {e}")
                    self.stop_event.wait(60)  # Wait longer on error
            
            self.logger.info("Log analyzer loop stopped")
            
        except Exception as e:
            self.logger.error(f"Fatal error in analyzer loop: {e}")
    
    def _get_logs(self, start_time: datetime, end_time: datetime) -> List[LogEntry]:
        """
        Get logs from database for a time period.
        
        Args:
            start_time: Start time
            end_time: End time
            
        Returns:
            List of log entries
        """
        try:
            # Query logs from database
            db_logs = SystemLog.select().where(
                (SystemLog.created_at >= start_time) &
                (SystemLog.created_at <= end_time)
            ).order_by(SystemLog.created_at.desc())
            
            # Convert to LogEntry objects
            logs = []
            for db_log in db_logs:
                log_entry = LogEntry(
                    timestamp=db_log.created_at,
                    level=LogLevel(db_log.level),
                    module=db_log.module,
                    message=db_log.message,
                    extra_data=db_log.extra_data,
                    user_id=db_log.user_id,
                    ip_address=db_log.ip_address
                )
                logs.append(log_entry)
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Failed to get logs: {e}")
            return []
    
    def _perform_analysis(self, logs: List[LogEntry], start_time: datetime, end_time: datetime) -> LogAnalysis:
        """
        Perform log analysis.
        
        Args:
            logs: List of log entries
            start_time: Analysis start time
            end_time: Analysis end time
            
        Returns:
            Log analysis results
        """
        try:
            # Count logs by level
            level_counts = Counter(log.level.value for log in logs)
            
            # Get top modules
            module_counts = Counter(log.module for log in logs)
            top_modules = [
                {"module": module, "count": count}
                for module, count in module_counts.most_common(10)
            ]
            
            # Get top errors
            error_logs = [log for log in logs if log.level == LogLevel.ERROR]
            error_messages = Counter(log.message for log in error_logs)
            top_errors = [
                {"message": message, "count": count}
                for message, count in error_messages.most_common(10)
            ]
            
            # Calculate error rate
            total_logs = len(logs)
            error_count = level_counts.get(LogLevel.ERROR.value, 0)
            error_rate = (error_count / total_logs * 100) if total_logs > 0 else 0
            
            # Calculate hourly log volume
            hourly_volume = defaultdict(int)
            for log in logs:
                hour = log.timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_volume[hour] += 1
            
            log_volume_per_hour = [
                {"hour": hour.isoformat(), "count": count}
                for hour, count in sorted(hourly_volume.items())
            ]
            
            # Pattern matching
            pattern_matches = defaultdict(int)
            for log in logs:
                for pattern_type, pattern in self.patterns.items():
                    if pattern.search(log.message):
                        pattern_matches[pattern_type.value] += 1
            
            return LogAnalysis(
                timestamp=datetime.now(),
                total_logs=total_logs,
                error_count=level_counts.get(LogLevel.ERROR.value, 0),
                warning_count=level_counts.get(LogLevel.WARNING.value, 0),
                info_count=level_counts.get(LogLevel.INFO.value, 0),
                debug_count=level_counts.get(LogLevel.DEBUG.value, 0),
                critical_count=level_counts.get(LogLevel.CRITICAL.value, 0),
                top_modules=top_modules,
                top_errors=top_errors,
                error_rate=error_rate,
                log_volume_per_hour=log_volume_per_hour,
                pattern_matches=dict(pattern_matches)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to perform analysis: {e}")
            return None
    
    def _detect_error_spikes(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """
        Detect error spikes in logs.
        
        Args:
            logs: List of log entries
            
        Returns:
            List of detected error spikes
        """
        try:
            # Group logs by hour
            hourly_errors = defaultdict(int)
            for log in logs:
                if log.level == LogLevel.ERROR:
                    hour = log.timestamp.replace(minute=0, second=0, microsecond=0)
                    hourly_errors[hour] += 1
            
            # Detect spikes (more than 2 standard deviations above mean)
            if not hourly_errors:
                return []
            
            error_counts = list(hourly_errors.values())
            mean_errors = sum(error_counts) / len(error_counts)
            variance = sum((x - mean_errors) ** 2 for x in error_counts) / len(error_counts)
            std_dev = variance ** 0.5
            
            threshold = mean_errors + (2 * std_dev)
            
            spikes = []
            for hour, count in hourly_errors.items():
                if count > threshold:
                    spikes.append({
                        "type": "error_spike",
                        "timestamp": hour.isoformat(),
                        "count": count,
                        "threshold": threshold,
                        "severity": "high" if count > mean_errors + (3 * std_dev) else "medium"
                    })
            
            return spikes
            
        except Exception as e:
            self.logger.error(f"Failed to detect error spikes: {e}")
            return []
    
    def _detect_unusual_patterns(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """
        Detect unusual patterns in logs.
        
        Args:
            logs: List of log entries
            
        Returns:
            List of detected unusual patterns
        """
        try:
            unusual_patterns = []
            
            # Detect repeated error messages
            error_messages = [log.message for log in logs if log.level == LogLevel.ERROR]
            message_counts = Counter(error_messages)
            
            for message, count in message_counts.items():
                if count > 10:  # Threshold for repeated errors
                    unusual_patterns.append({
                        "type": "repeated_errors",
                        "message": message,
                        "count": count,
                        "severity": "high" if count > 50 else "medium"
                    })
            
            # Detect security-related patterns
            security_logs = [log for log in logs if "security" in log.message.lower()]
            if len(security_logs) > 5:
                unusual_patterns.append({
                    "type": "security_events",
                    "count": len(security_logs),
                    "severity": "high"
                })
            
            return unusual_patterns
            
        except Exception as e:
            self.logger.error(f"Failed to detect unusual patterns: {e}")
            return []
    
    def _detect_volume_anomalies(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """
        Detect volume anomalies in logs.
        
        Args:
            logs: List of log entries
            
        Returns:
            List of detected volume anomalies
        """
        try:
            # Group logs by hour
            hourly_volume = defaultdict(int)
            for log in logs:
                hour = log.timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_volume[hour] += 1
            
            if not hourly_volume:
                return []
            
            # Calculate average volume
            volumes = list(hourly_volume.values())
            avg_volume = sum(volumes) / len(volumes)
            
            # Detect high volume periods
            anomalies = []
            for hour, volume in hourly_volume.items():
                if volume > avg_volume * 2:  # 2x average volume
                    anomalies.append({
                        "type": "high_volume",
                        "timestamp": hour.isoformat(),
                        "volume": volume,
                        "average": avg_volume,
                        "severity": "high" if volume > avg_volume * 3 else "medium"
                    })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Failed to detect volume anomalies: {e}")
            return []
    
    def _check_alerts(self, analysis: LogAnalysis):
        """
        Check for alert conditions.
        
        Args:
            analysis: Current log analysis
        """
        try:
            # Check error rate
            if analysis.error_rate > self.thresholds["error_rate"]:
                self._trigger_alert("Error Rate", f"High error rate: {analysis.error_rate:.1f}%")
            
            # Check critical count
            if analysis.critical_count > self.thresholds["critical_count"]:
                self._trigger_alert("Critical Logs", f"High critical log count: {analysis.critical_count}")
            
            # Check log volume
            if analysis.total_logs > self.thresholds["log_volume"]:
                self._trigger_alert("Log Volume", f"High log volume: {analysis.total_logs}")
            
            # Check pattern matches
            total_pattern_matches = sum(analysis.pattern_matches.values())
            if total_pattern_matches > self.thresholds["pattern_matches"]:
                self._trigger_alert("Pattern Matches", f"High pattern matches: {total_pattern_matches}")
                
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
                module="log_analyzer",
                message=f"ALERT [{alert_type}]: {message}",
                created_at=datetime.now()
            )
            
            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert_type, message)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")
            
            self.logger.warning(f"Log analysis alert: {alert_type} - {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger alert: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get log analyzer status.
        
        Returns:
            Dictionary with analyzer status information
        """
        try:
            with self.lock:
                return {
                    "is_running": self.is_running,
                    "analysis_interval": self.analysis_interval,
                    "analysis_history_size": len(self.analysis_history),
                    "current_analysis": self.current_analysis.__dict__ if self.current_analysis else None,
                    "thresholds": self.thresholds,
                    "patterns_count": len(self.patterns),
                    "callbacks_count": {
                        "analysis": len(self.analysis_callbacks),
                        "alerts": len(self.alert_callbacks)
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get analyzer status: {e}")
            return {"is_running": False, "error": str(e)}
