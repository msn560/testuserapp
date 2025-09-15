"""
Alert system for monitoring and managing system alerts.

This module provides comprehensive alert management including alert creation,
notification, escalation, and management.
"""

import threading
import smtplib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..db.models import Alert, SystemLog, User
from ..core.constants import LogLevel
from ..utils.logger import logger


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(Enum):
    """Notification channels."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    SYSTEM_LOG = "system_log"


@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    description: str
    condition: str  # JSON string with condition logic
    severity: AlertSeverity
    channels: List[NotificationChannel]
    escalation_time: int  # Minutes before escalation
    suppression_time: int  # Minutes to suppress after resolution
    enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class AlertNotification:
    """Alert notification data structure."""
    alert_id: int
    channel: NotificationChannel
    recipient: str
    subject: str
    message: str
    sent_at: datetime
    status: str  # sent, failed, pending
    error_message: Optional[str] = None


class AlertSystem:
    """
    Alert system for monitoring and managing system alerts.
    
    This class provides comprehensive alert management including alert creation,
    notification, escalation, and management.
    """
    
    def __init__(self, check_interval: int = 60):  # 1 minute
        """
        Initialize the alert system.
        
        Args:
            check_interval: Alert check interval in seconds
        """
        self.check_interval = check_interval
        self.is_running = False
        self.alert_thread = None
        self.stop_event = threading.Event()
        self.logger = logger
        
        # Alert rules storage
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.max_history_size = 1000
        
        # Notification settings
        self.notification_settings = {
            NotificationChannel.EMAIL: {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "",
                "use_tls": True
            },
            NotificationChannel.SMS: {
                "enabled": False,
                "provider": "",
                "api_key": "",
                "from_number": ""
            },
            NotificationChannel.WEBHOOK: {
                "enabled": False,
                "url": "",
                "headers": {},
                "timeout": 30
            },
            NotificationChannel.IN_APP: {
                "enabled": True
            },
            NotificationChannel.SYSTEM_LOG: {
                "enabled": True
            }
        }
        
        # Callbacks
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        self.notification_callbacks: List[Callable[[AlertNotification], None]] = []
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Load default alert rules
        self._load_default_rules()
    
    def start(self) -> bool:
        """
        Start the alert system.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                self.logger.warning("Alert system is already running")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Start alert thread
            self.alert_thread = threading.Thread(
                target=self._alert_loop,
                daemon=True,
                name="AlertSystem"
            )
            self.alert_thread.start()
            
            self.logger.info("Alert system started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start alert system: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the alert system.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if not self.is_running:
                self.logger.warning("Alert system is not running")
                return True
            
            self.is_running = False
            self.stop_event.set()
            
            # Wait for alert thread to finish
            if self.alert_thread and self.alert_thread.is_alive():
                self.alert_thread.join(timeout=10)
            
            self.logger.info("Alert system stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop alert system: {e}")
            return False
    
    def create_alert(self, rule_name: str, message: str, severity: AlertSeverity = None, 
                    metadata: Dict[str, Any] = None) -> Optional[Alert]:
        """
        Create a new alert.
        
        Args:
            rule_name: Name of the alert rule
            message: Alert message
            severity: Alert severity (default: from rule)
            metadata: Additional metadata
            
        Returns:
            Created alert or None if failed
        """
        try:
            # Get alert rule
            rule = self.alert_rules.get(rule_name)
            if not rule or not rule.enabled:
                self.logger.warning(f"Alert rule not found or disabled: {rule_name}")
                return None
            
            # Use rule severity if not specified
            if severity is None:
                severity = rule.severity
            
            # Create alert in database
            alert = Alert.create(
                title=f"{rule.name}: {message}",
                message=message,
                severity=severity.value,
                status=AlertStatus.ACTIVE.value,
                rule_name=rule_name,
                metadata=json.dumps(metadata) if metadata else None,
                created_at=datetime.now()
            )
            
            # Store in active alerts
            self.active_alerts[rule_name] = alert
            
            # Add to history
            self.alert_history.append(alert)
            if len(self.alert_history) > self.max_history_size:
                self.alert_history.pop(0)
            
            # Send notifications
            self._send_notifications(alert, rule)
            
            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")
            
            self.logger.info(f"Alert created: {rule_name} - {message}")
            return alert
            
        except Exception as e:
            self.logger.error(f"Failed to create alert: {e}")
            return None
    
    def acknowledge_alert(self, alert_id: int, user_id: int, note: str = None) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID
            user_id: User ID who acknowledged
            note: Optional note
            
        Returns:
            True if acknowledged successfully, False otherwise
        """
        try:
            # Update alert in database
            alert = Alert.get_by_id(alert_id)
            alert.status = AlertStatus.ACKNOWLEDGED.value
            alert.acknowledged_by = user_id
            alert.acknowledged_at = datetime.now()
            alert.notes = note
            alert.save()
            
            # Remove from active alerts
            for rule_name, active_alert in list(self.active_alerts.items()):
                if active_alert.id == alert_id:
                    del self.active_alerts[rule_name]
                    break
            
            self.logger.info(f"Alert acknowledged: {alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert: {e}")
            return False
    
    def resolve_alert(self, alert_id: int, user_id: int, resolution: str = None) -> bool:
        """
        Resolve an alert.
        
        Args:
            alert_id: Alert ID
            user_id: User ID who resolved
            resolution: Resolution description
            
        Returns:
            True if resolved successfully, False otherwise
        """
        try:
            # Update alert in database
            alert = Alert.get_by_id(alert_id)
            alert.status = AlertStatus.RESOLVED.value
            alert.resolved_by = user_id
            alert.resolved_at = datetime.now()
            alert.resolution = resolution
            alert.save()
            
            # Remove from active alerts
            for rule_name, active_alert in list(self.active_alerts.items()):
                if active_alert.id == alert_id:
                    del self.active_alerts[rule_name]
                    break
            
            self.logger.info(f"Alert resolved: {alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to resolve alert: {e}")
            return False
    
    def suppress_alert(self, alert_id: int, user_id: int, duration_minutes: int = 60, reason: str = None) -> bool:
        """
        Suppress an alert.
        
        Args:
            alert_id: Alert ID
            user_id: User ID who suppressed
            duration_minutes: Suppression duration in minutes
            reason: Suppression reason
            
        Returns:
            True if suppressed successfully, False otherwise
        """
        try:
            # Update alert in database
            alert = Alert.get_by_id(alert_id)
            alert.status = AlertStatus.SUPPRESSED.value
            alert.suppressed_by = user_id
            alert.suppressed_at = datetime.now()
            alert.suppression_duration = duration_minutes
            alert.suppression_reason = reason
            alert.save()
            
            # Remove from active alerts
            for rule_name, active_alert in list(self.active_alerts.items()):
                if active_alert.id == alert_id:
                    del self.active_alerts[rule_name]
                    break
            
            self.logger.info(f"Alert suppressed: {alert_id} for {duration_minutes} minutes")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to suppress alert: {e}")
            return False
    
    def get_active_alerts(self) -> List[Alert]:
        """
        Get all active alerts.
        
        Returns:
            List of active alerts
        """
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of historical alerts
        """
        return self.alert_history[-limit:] if self.alert_history else []
    
    def get_alert_statistics(self, start_time: datetime = None, end_time: datetime = None) -> Dict[str, Any]:
        """
        Get alert statistics for a time period.
        
        Args:
            start_time: Start time for statistics
            end_time: End time for statistics
            
        Returns:
            Dictionary with alert statistics
        """
        try:
            # Set default time range
            if not end_time:
                end_time = datetime.now()
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            # Query alerts from database
            alerts = Alert.select().where(
                (Alert.created_at >= start_time) &
                (Alert.created_at <= end_time)
            )
            
            # Calculate statistics
            total_alerts = alerts.count()
            severity_counts = {}
            status_counts = {}
            rule_counts = {}
            
            for alert in alerts:
                # Count by severity
                severity = alert.severity
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                # Count by status
                status = alert.status
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count by rule
                rule = alert.rule_name
                rule_counts[rule] = rule_counts.get(rule, 0) + 1
            
            return {
                "total_alerts": total_alerts,
                "severity_distribution": severity_counts,
                "status_distribution": status_counts,
                "rule_distribution": rule_counts,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get alert statistics: {e}")
            return {}
    
    def add_alert_rule(self, rule: AlertRule) -> bool:
        """
        Add a new alert rule.
        
        Args:
            rule: Alert rule to add
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            self.alert_rules[rule.name] = rule
            self.logger.info(f"Alert rule added: {rule.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add alert rule: {e}")
            return False
    
    def remove_alert_rule(self, rule_name: str) -> bool:
        """
        Remove an alert rule.
        
        Args:
            rule_name: Name of the rule to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            if rule_name in self.alert_rules:
                del self.alert_rules[rule_name]
                self.logger.info(f"Alert rule removed: {rule_name}")
                return True
            else:
                self.logger.warning(f"Alert rule not found: {rule_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove alert rule: {e}")
            return False
    
    def update_alert_rule(self, rule_name: str, updates: Dict[str, Any]) -> bool:
        """
        Update an alert rule.
        
        Args:
            rule_name: Name of the rule to update
            updates: Dictionary with updates
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if rule_name not in self.alert_rules:
                self.logger.warning(f"Alert rule not found: {rule_name}")
                return False
            
            rule = self.alert_rules[rule_name]
            
            # Update rule attributes
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            rule.updated_at = datetime.now()
            self.alert_rules[rule_name] = rule
            
            self.logger.info(f"Alert rule updated: {rule_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update alert rule: {e}")
            return False
    
    def configure_notification_channel(self, channel: NotificationChannel, settings: Dict[str, Any]) -> bool:
        """
        Configure a notification channel.
        
        Args:
            channel: Notification channel
            settings: Channel settings
            
        Returns:
            True if configured successfully, False otherwise
        """
        try:
            if channel in self.notification_settings:
                self.notification_settings[channel].update(settings)
                self.logger.info(f"Notification channel configured: {channel.value}")
                return True
            else:
                self.logger.warning(f"Unknown notification channel: {channel}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to configure notification channel: {e}")
            return False
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """
        Add a callback for alert events.
        
        Args:
            callback: Function to call when alerts are created
        """
        self.alert_callbacks.append(callback)
    
    def add_notification_callback(self, callback: Callable[[AlertNotification], None]):
        """
        Add a callback for notification events.
        
        Args:
            callback: Function to call when notifications are sent
        """
        self.notification_callbacks.append(callback)
    
    def _load_default_rules(self):
        """Load default alert rules."""
        try:
            # High CPU usage rule
            cpu_rule = AlertRule(
                name="high_cpu_usage",
                description="High CPU usage detected",
                condition='{"metric": "cpu_percent", "operator": ">", "value": 80}',
                severity=AlertSeverity.HIGH,
                channels=[NotificationChannel.IN_APP, NotificationChannel.SYSTEM_LOG],
                escalation_time=15,
                suppression_time=30
            )
            self.alert_rules["high_cpu_usage"] = cpu_rule
            
            # High memory usage rule
            memory_rule = AlertRule(
                name="high_memory_usage",
                description="High memory usage detected",
                condition='{"metric": "memory_percent", "operator": ">", "value": 85}',
                severity=AlertSeverity.HIGH,
                channels=[NotificationChannel.IN_APP, NotificationChannel.SYSTEM_LOG],
                escalation_time=15,
                suppression_time=30
            )
            self.alert_rules["high_memory_usage"] = memory_rule
            
            # Disk space rule
            disk_rule = AlertRule(
                name="low_disk_space",
                description="Low disk space detected",
                condition='{"metric": "disk_percent", "operator": ">", "value": 90}',
                severity=AlertSeverity.CRITICAL,
                channels=[NotificationChannel.IN_APP, NotificationChannel.SYSTEM_LOG],
                escalation_time=5,
                suppression_time=60
            )
            self.alert_rules["low_disk_space"] = disk_rule
            
            # API error rate rule
            api_error_rule = AlertRule(
                name="high_api_error_rate",
                description="High API error rate detected",
                condition='{"metric": "api_error_rate", "operator": ">", "value": 10}',
                severity=AlertSeverity.MEDIUM,
                channels=[NotificationChannel.IN_APP, NotificationChannel.SYSTEM_LOG],
                escalation_time=30,
                suppression_time=60
            )
            self.alert_rules["high_api_error_rate"] = api_error_rule
            
            # Database connection rule
            db_rule = AlertRule(
                name="database_connection_error",
                description="Database connection error detected",
                condition='{"metric": "db_connection", "operator": "==", "value": false}',
                severity=AlertSeverity.CRITICAL,
                channels=[NotificationChannel.IN_APP, NotificationChannel.SYSTEM_LOG],
                escalation_time=5,
                suppression_time=120
            )
            self.alert_rules["database_connection_error"] = db_rule
            
            self.logger.info("Default alert rules loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load default alert rules: {e}")
    
    def _alert_loop(self):
        """Main alert loop that runs in a separate thread."""
        try:
            self.logger.info("Alert system loop started")
            
            while self.is_running and not self.stop_event.is_set():
                try:
                    # Check for alert conditions
                    self._check_alert_conditions()
                    
                    # Process escalations
                    self._process_escalations()
                    
                    # Process suppressions
                    self._process_suppressions()
                    
                    # Wait for next check
                    self.stop_event.wait(self.check_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in alert loop: {e}")
                    self.stop_event.wait(60)  # Wait longer on error
            
            self.logger.info("Alert system loop stopped")
            
        except Exception as e:
            self.logger.error(f"Fatal error in alert loop: {e}")
    
    def _check_alert_conditions(self):
        """Check alert conditions and create alerts if needed."""
        try:
            # This would typically check system metrics, logs, etc.
            # For now, we'll implement a simple example
            
            # Check if we have any active alerts that need to be re-evaluated
            for rule_name, alert in list(self.active_alerts.items()):
                rule = self.alert_rules.get(rule_name)
                if rule and rule.enabled:
                    # Check if condition is still met
                    if not self._evaluate_condition(rule.condition):
                        # Condition no longer met, resolve alert
                        self.resolve_alert(alert.id, 1, "Condition no longer met")
            
        except Exception as e:
            self.logger.error(f"Failed to check alert conditions: {e}")
    
    def _evaluate_condition(self, condition: str) -> bool:
        """
        Evaluate an alert condition.
        
        Args:
            condition: JSON string with condition logic
            
        Returns:
            True if condition is met, False otherwise
        """
        try:
            # Parse condition
            condition_data = json.loads(condition)
            
            # This is a simplified example
            # In a real implementation, you would check actual metrics
            metric = condition_data.get("metric")
            operator = condition_data.get("operator")
            value = condition_data.get("value")
            
            # Mock evaluation - in reality, you would check actual system metrics
            if metric == "cpu_percent":
                # Check actual CPU usage
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                if operator == ">":
                    return cpu_percent > value
                elif operator == "<":
                    return cpu_percent < value
                elif operator == "==":
                    return cpu_percent == value
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate condition: {e}")
            return False
    
    def _process_escalations(self):
        """Process alert escalations."""
        try:
            current_time = datetime.now()
            
            for rule_name, alert in list(self.active_alerts.items()):
                rule = self.alert_rules.get(rule_name)
                if rule and rule.escalation_time > 0:
                    # Check if alert needs escalation
                    time_since_creation = (current_time - alert.created_at).total_seconds() / 60
                    
                    if time_since_creation >= rule.escalation_time:
                        # Escalate alert
                        self._escalate_alert(alert, rule)
            
        except Exception as e:
            self.logger.error(f"Failed to process escalations: {e}")
    
    def _escalate_alert(self, alert: Alert, rule: AlertRule):
        """
        Escalate an alert.
        
        Args:
            alert: Alert to escalate
            rule: Alert rule
        """
        try:
            # Update alert severity
            if alert.severity == AlertSeverity.LOW.value:
                alert.severity = AlertSeverity.MEDIUM.value
            elif alert.severity == AlertSeverity.MEDIUM.value:
                alert.severity = AlertSeverity.HIGH.value
            elif alert.severity == AlertSeverity.HIGH.value:
                alert.severity = AlertSeverity.CRITICAL.value
            
            alert.save()
            
            # Send escalation notifications
            self._send_notifications(alert, rule, is_escalation=True)
            
            self.logger.warning(f"Alert escalated: {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to escalate alert: {e}")
    
    def _process_suppressions(self):
        """Process alert suppressions."""
        try:
            current_time = datetime.now()
            
            # Check for suppressed alerts that should be reactivated
            suppressed_alerts = Alert.select().where(
                Alert.status == AlertStatus.SUPPRESSED.value
            )
            
            for alert in suppressed_alerts:
                if alert.suppressed_at and alert.suppression_duration:
                    time_since_suppression = (current_time - alert.suppressed_at).total_seconds() / 60
                    
                    if time_since_suppression >= alert.suppression_duration:
                        # Reactivate alert
                        alert.status = AlertStatus.ACTIVE.value
                        alert.suppressed_at = None
                        alert.suppression_duration = None
                        alert.suppression_reason = None
                        alert.save()
                        
                        # Add back to active alerts
                        self.active_alerts[alert.rule_name] = alert
                        
                        self.logger.info(f"Alert reactivated: {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to process suppressions: {e}")
    
    def _send_notifications(self, alert: Alert, rule: AlertRule, is_escalation: bool = False):
        """
        Send notifications for an alert.
        
        Args:
            alert: Alert to send notifications for
            rule: Alert rule
            is_escalation: Whether this is an escalation notification
        """
        try:
            for channel in rule.channels:
                if channel in self.notification_settings:
                    settings = self.notification_settings[channel]
                    
                    if settings.get("enabled", False):
                        # Send notification
                        notification = self._create_notification(alert, rule, channel, is_escalation)
                        if notification:
                            self._send_notification(notification, settings)
                            
                            # Notify callbacks
                            for callback in self.notification_callbacks:
                                try:
                                    callback(notification)
                                except Exception as e:
                                    self.logger.error(f"Error in notification callback: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to send notifications: {e}")
    
    def _create_notification(self, alert: Alert, rule: AlertRule, channel: NotificationChannel, 
                           is_escalation: bool = False) -> Optional[AlertNotification]:
        """
        Create a notification for an alert.
        
        Args:
            alert: Alert to create notification for
            rule: Alert rule
            channel: Notification channel
            is_escalation: Whether this is an escalation notification
            
        Returns:
            Created notification or None if failed
        """
        try:
            # Determine subject and message
            if is_escalation:
                subject = f"ESCALATED: {alert.title}"
                message = f"Alert has been escalated:\n\n{alert.message}\n\nSeverity: {alert.severity}\nCreated: {alert.created_at}"
            else:
                subject = f"ALERT: {alert.title}"
                message = f"New alert:\n\n{alert.message}\n\nSeverity: {alert.severity}\nCreated: {alert.created_at}"
            
            # Determine recipient
            recipient = self._get_notification_recipient(channel)
            
            notification = AlertNotification(
                alert_id=alert.id,
                channel=channel,
                recipient=recipient,
                subject=subject,
                message=message,
                sent_at=datetime.now(),
                status="pending"
            )
            
            return notification
            
        except Exception as e:
            self.logger.error(f"Failed to create notification: {e}")
            return None
    
    def _get_notification_recipient(self, channel: NotificationChannel) -> str:
        """
        Get notification recipient for a channel.
        
        Args:
            channel: Notification channel
            
        Returns:
            Recipient identifier
        """
        try:
            if channel == NotificationChannel.EMAIL:
                # Get admin users' emails
                admin_users = User.select().where(User.role == "admin")
                return ",".join([user.email for user in admin_users if user.email])
            elif channel == NotificationChannel.SMS:
                # Get admin users' phone numbers
                admin_users = User.select().where(User.role == "admin")
                return ",".join([user.phone for user in admin_users if user.phone])
            elif channel == NotificationChannel.WEBHOOK:
                return "webhook"
            elif channel == NotificationChannel.IN_APP:
                return "in_app"
            elif channel == NotificationChannel.SYSTEM_LOG:
                return "system_log"
            
            return "unknown"
            
        except Exception as e:
            self.logger.error(f"Failed to get notification recipient: {e}")
            return "unknown"
    
    def _send_notification(self, notification: AlertNotification, settings: Dict[str, Any]):
        """
        Send a notification.
        
        Args:
            notification: Notification to send
            settings: Channel settings
        """
        try:
            if notification.channel == NotificationChannel.EMAIL:
                self._send_email_notification(notification, settings)
            elif notification.channel == NotificationChannel.SMS:
                self._send_sms_notification(notification, settings)
            elif notification.channel == NotificationChannel.WEBHOOK:
                self._send_webhook_notification(notification, settings)
            elif notification.channel == NotificationChannel.IN_APP:
                self._send_in_app_notification(notification, settings)
            elif notification.channel == NotificationChannel.SYSTEM_LOG:
                self._send_system_log_notification(notification, settings)
            
            # Update notification status
            notification.status = "sent"
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            notification.status = "failed"
            notification.error_message = str(e)
    
    def _send_email_notification(self, notification: AlertNotification, settings: Dict[str, Any]):
        """Send email notification."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = settings.get("from_email", "")
            msg['To'] = notification.recipient
            msg['Subject'] = notification.subject
            
            # Add body
            msg.attach(MIMEText(notification.message, 'plain'))
            
            # Send email
            server = smtplib.SMTP(settings.get("smtp_server", ""), settings.get("smtp_port", 587))
            
            if settings.get("use_tls", True):
                server.starttls()
            
            if settings.get("username") and settings.get("password"):
                server.login(settings.get("username"), settings.get("password"))
            
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email notification sent: {notification.alert_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            raise
    
    def _send_sms_notification(self, notification: AlertNotification, settings: Dict[str, Any]):
        """Send SMS notification."""
        try:
            # This would integrate with an SMS provider
            # For now, just log the notification
            self.logger.info(f"SMS notification would be sent: {notification.alert_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS notification: {e}")
            raise
    
    def _send_webhook_notification(self, notification: AlertNotification, settings: Dict[str, Any]):
        """Send webhook notification."""
        try:
            import requests
            
            # Prepare payload
            payload = {
                "alert_id": notification.alert_id,
                "subject": notification.subject,
                "message": notification.message,
                "timestamp": notification.sent_at.isoformat()
            }
            
            # Send webhook
            response = requests.post(
                settings.get("url", ""),
                json=payload,
                headers=settings.get("headers", {}),
                timeout=settings.get("timeout", 30)
            )
            
            response.raise_for_status()
            
            self.logger.info(f"Webhook notification sent: {notification.alert_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
            raise
    
    def _send_in_app_notification(self, notification: AlertNotification, settings: Dict[str, Any]):
        """Send in-app notification."""
        try:
            # This would integrate with the UI system
            # For now, just log the notification
            self.logger.info(f"In-app notification would be sent: {notification.alert_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send in-app notification: {e}")
            raise
    
    def _send_system_log_notification(self, notification: AlertNotification, settings: Dict[str, Any]):
        """Send system log notification."""
        try:
            # Log to system log
            SystemLog.create(
                level=LogLevel.WARNING.value,
                module="alert_system",
                message=f"ALERT NOTIFICATION: {notification.subject} - {notification.message}",
                created_at=datetime.now()
            )
            
            self.logger.info(f"System log notification sent: {notification.alert_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send system log notification: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get alert system status.
        
        Returns:
            Dictionary with system status information
        """
        try:
            with self.lock:
                return {
                    "is_running": self.is_running,
                    "check_interval": self.check_interval,
                    "active_alerts_count": len(self.active_alerts),
                    "alert_rules_count": len(self.alert_rules),
                    "alert_history_size": len(self.alert_history),
                    "notification_channels": {
                        channel.value: settings.get("enabled", False)
                        for channel, settings in self.notification_settings.items()
                    },
                    "callbacks_count": {
                        "alerts": len(self.alert_callbacks),
                        "notifications": len(self.notification_callbacks)
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get alert system status: {e}")
            return {"is_running": False, "error": str(e)}


# Global alert system instance
alert_system = AlertSystem()
