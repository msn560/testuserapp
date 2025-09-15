"""
Dashboard tab for system overview and statistics.

This tab provides a comprehensive overview of the system status,
including server status, user statistics, and real-time metrics.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QProgressBar, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QScrollArea, QSplitter, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

from .base_tab import BaseTab, BaseTabWorker
from ...utils.logger import logger
from ...core.language import language_manager


class DashboardWorker(BaseTabWorker):
    """
    Dashboard worker that runs in a separate thread.
    """
    
    # Additional signals for dashboard-specific data
    server_status_updated = pyqtSignal(dict)  # Server status
    user_stats_updated = pyqtSignal(dict)     # User statistics
    system_metrics_updated = pyqtSignal(dict) # System metrics
    activities_updated = pyqtSignal(list)     # Recent activities
    
    def __init__(self):
        super().__init__("dashboard")
    
    def _do_refresh_data(self):
        """Refresh dashboard data in background thread."""
        try:
            if not self.running:
                return
            
            # Get server status
            self._get_server_status()
            
            # Get user statistics
            self._get_user_statistics()
            
            # Get system metrics
            self._get_system_metrics()
            
            # Get recent activities
            self._get_recent_activities()
            
            # Emit general data ready signal
            self.data_ready.emit({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "ready"
            })
            
        except Exception as e:
            self.logger.error(f"Error refreshing dashboard data: {e}")
            self.error_occurred.emit(str(e))
    
    def _get_server_status(self):
        """Get server status (non-blocking)."""
        try:
            # Try to get real server status from main window
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'server_manager') and main_window.server_manager:
                server_status = main_window.server_manager.get_status()
                self.server_status_updated.emit(server_status)
            else:
                # Fallback to placeholder data
                server_status = {
                    "is_running": False,
                    "host": "127.0.0.1",
                    "port": 8080,
                    "ssl_enabled": False,
                    "url": "http://127.0.0.1:8080",
                    "uptime_seconds": None,
                    "start_time": None,
                    "request_count": 0,
                    "error_count": 0
                }
                self.server_status_updated.emit(server_status)
            
        except Exception as e:
            self.logger.error(f"Error getting server status: {e}")
    
    def _get_user_statistics(self):
        """Get user statistics (non-blocking)."""
        try:
            # Placeholder data - in real implementation, this would come from the user service
            user_stats = {
                "total_users": 25,
                "active_users": 18,
                "online_users": 5,
                "verified_users": 22,
                "admin_users": 3,
                "new_users_today": 2,
                "new_users_this_week": 8
            }
            self.user_stats_updated.emit(user_stats)
            
        except Exception as e:
            self.logger.error(f"Error getting user statistics: {e}")
    
    def _get_system_metrics(self):
        """Get system metrics (non-blocking)."""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get network stats
            network = psutil.net_io_counters()
            
            system_metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_used_gb": disk.used / (1024**3),
                "disk_total_gb": disk.total / (1024**3),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
                "uptime": str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())).split('.')[0]
            }
            
            self.system_metrics_updated.emit(system_metrics)
            
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
    
    def _get_recent_activities(self):
        """Get recent activities (non-blocking)."""
        try:
            # Placeholder data - in real implementation, this would come from the activity service
            activities = [
                {
                    "time": "17:15:30",
                    "type": "User Login",
                    "user": "admin",
                    "description": "User logged in successfully"
                },
                {
                    "time": "17:14:45",
                    "type": "API Request",
                    "user": "system",
                    "description": "GET /api/v1/health - 200 OK"
                },
                {
                    "time": "17:13:20",
                    "type": "User Registration",
                    "user": "newuser",
                    "description": "New user registered"
                },
                {
                    "time": "17:12:10",
                    "type": "Server Start",
                    "user": "admin",
                    "description": "HTTP server started on port 8080"
                },
                {
                    "time": "17:11:55",
                    "type": "Config Update",
                    "user": "admin",
                    "description": "Server configuration updated"
                }
            ]
            
            self.activities_updated.emit(activities)
            
        except Exception as e:
            self.logger.error(f"Error getting recent activities: {e}")
    
    def _get_main_window(self):
        """Get main window instance safely."""
        # Workers shouldn't directly access GUI components
        # This is a placeholder - in real implementation, data would come from services
        return None


class DashboardTab(BaseTab):
    """
    Dashboard tab for system overview and statistics.
    
    This tab provides a comprehensive overview of the system status,
    including server status, user statistics, and real-time metrics.
    """
    
    def __init__(self):
        """Initialize the dashboard tab."""
        super().__init__("dashboard", language_manager.translate("navigation.dashboard"))
        
        # Data storage
        self.server_status = {}
        self.user_stats = {}
        self.system_metrics = {}
        self.recent_activities = []
        
        # Create dashboard components
        self._create_dashboard_components()
        
        # Set refresh interval
        self.set_refresh_interval(5000)  # 5 seconds
        
        # Connect dashboard-specific signals
        self._connect_dashboard_signals()
        
        self.logger.info("Dashboard tab initialized")
    
    def _create_worker(self):
        """Create dashboard worker."""
        return DashboardWorker()
    
    def _connect_dashboard_signals(self):
        """Connect dashboard-specific signals."""
        try:
            if self.worker:
                self.worker.server_status_updated.connect(self._on_server_status_updated)
                self.worker.user_stats_updated.connect(self._on_user_stats_updated)
                self.worker.system_metrics_updated.connect(self._on_system_metrics_updated)
                self.worker.activities_updated.connect(self._on_activities_updated)
        except Exception as e:
            self.logger.error(f"Failed to connect dashboard signals: {e}")
    
    def _on_server_status_updated(self, status: dict):
        """Handle server status update from worker thread."""
        try:
            self.server_status = status
            self._update_server_status_display()
        except Exception as e:
            self.logger.error(f"Error updating server status: {e}")
    
    def _on_user_stats_updated(self, stats: dict):
        """Handle user statistics update from worker thread."""
        try:
            self.user_stats = stats
            self._update_user_statistics_display()
        except Exception as e:
            self.logger.error(f"Error updating user statistics: {e}")
    
    def _on_system_metrics_updated(self, metrics: dict):
        """Handle system metrics update from worker thread."""
        try:
            self.system_metrics = metrics
            self._update_system_metrics_display()
        except Exception as e:
            self.logger.error(f"Error updating system metrics: {e}")
    
    def _on_activities_updated(self, activities: list):
        """Handle activities update from worker thread."""
        try:
            self.recent_activities = activities
            self._update_activities_display()
        except Exception as e:
            self.logger.error(f"Error updating activities: {e}")
    
    def _create_dashboard_components(self) -> None:
        """Create dashboard components."""
        try:
            # Initialize dashboard components
            self.stats_widgets = {}
            self.metric_widgets = {}
            self.status_widgets = {}
            
            # Create stats widgets
            self._create_stats_widgets()
            
            # Create metric widgets
            self._create_metric_widgets()
            
            # Create status widgets
            self._create_status_widgets()
            
            self.logger.info("Dashboard components created")
            
        except Exception as e:
            self.logger.error(f"Failed to create dashboard components: {e}")
    
    def _create_stats_widgets(self) -> None:
        """Create statistics widgets."""
        try:
            # User stats widget
            self.stats_widgets['users'] = {
                'total': 0,
                'active': 0,
                'online': 0,
                'verified': 0
            }
            
            # Server stats widget
            self.stats_widgets['server'] = {
                'uptime': 0,
                'requests': 0,
                'errors': 0,
                'connections': 0
            }
            
            # System stats widget
            self.stats_widgets['system'] = {
                'cpu': 0,
                'memory': 0,
                'disk': 0,
                'network': 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create stats widgets: {e}")
    
    def _create_metric_widgets(self) -> None:
        """Create metric widgets."""
        try:
            # Performance metrics
            self.metric_widgets['performance'] = {
                'response_time': 0,
                'throughput': 0,
                'error_rate': 0,
                'uptime': 0
            }
            
            # API metrics
            self.metric_widgets['api'] = {
                'requests_per_second': 0,
                'average_response_time': 0,
                'active_connections': 0,
                'queue_size': 0
            }
            
            # Database metrics
            self.metric_widgets['database'] = {
                'connection_count': 0,
                'query_time': 0,
                'cache_hit_rate': 0,
                'table_size': 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create metric widgets: {e}")
    
    def _create_status_widgets(self) -> None:
        """Create status widgets."""
        try:
            # Server status
            self.status_widgets['server'] = {
                'status': 'offline',
                'url': 'N/A',
                'uptime': 'N/A'
            }
            
            # Database status
            self.status_widgets['database'] = {
                'status': 'connected',
                'connections': 0,
                'response_time': 0
            }
            
            # System status
            self.status_widgets['system'] = {
                'status': 'healthy',
                'cpu': 0,
                'memory': 0,
                'disk': 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create status widgets: {e}")
    
    def _create_content_widget(self) -> QWidget:
        """Create the dashboard content widget."""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Create scroll area for the dashboard
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create main dashboard widget
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        
        # Create dashboard sections
        self._create_overview_section(dashboard_layout)
        self._create_stats_section(dashboard_layout)
        self._create_metrics_section(dashboard_layout)
        self._create_activities_section(dashboard_layout)
        
        # Set the dashboard widget as the scroll area's widget
        scroll_area.setWidget(dashboard_widget)
        layout.addWidget(scroll_area)
        
        return content_widget
    
    def _create_overview_section(self, layout: QVBoxLayout):
        """Create the system overview section."""
        overview_group = QGroupBox(language_manager.translate("ui.dashboard.system_overview"))
        overview_layout = QGridLayout(overview_group)
        
        # Server status
        overview_layout.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.server_status')}:"), 0, 0)
        self.server_status_label = QLabel(language_manager.translate("server.offline"))
        self.server_status_label.setProperty("class", "status-offline")
        overview_layout.addWidget(self.server_status_label, 0, 1)
        
        # Server URL
        overview_layout.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.server_url')}:"), 0, 2)
        self.server_url_label = QLabel(language_manager.translate("ui.common.na"))
        self.server_url_label.setStyleSheet("font-family: 'Consolas', monospace;")
        overview_layout.addWidget(self.server_url_label, 0, 3)
        
        # System uptime
        overview_layout.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.system_uptime')}:"), 1, 0)
        self.system_uptime_label = QLabel(language_manager.translate("ui.common.na"))
        self.system_uptime_label.setStyleSheet("font-family: 'Consolas', monospace;")
        overview_layout.addWidget(self.system_uptime_label, 1, 1)
        
        # Boot time
        overview_layout.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.boot_time')}:"), 1, 2)
        self.boot_time_label = QLabel(language_manager.translate("ui.common.na"))
        self.boot_time_label.setStyleSheet("font-family: 'Consolas', monospace;")
        overview_layout.addWidget(self.boot_time_label, 1, 3)
        
        layout.addWidget(overview_group)
    
    def _create_stats_section(self, layout: QVBoxLayout):
        """Create the statistics section."""
        stats_group = QGroupBox(language_manager.translate("ui.dashboard.statistics"))
        stats_layout = QGridLayout(stats_group)
        
        # User statistics
        user_stats_frame = QFrame()
        user_stats_frame.setFrameStyle(QFrame.StyledPanel)
        user_stats_layout = QVBoxLayout(user_stats_frame)
        
        user_stats_title = QLabel(language_manager.translate("ui.dashboard.user_statistics"))
        user_stats_title.setProperty("class", "title")
        user_stats_layout.addWidget(user_stats_title)
        
        # User stats grid
        user_grid = QGridLayout()
        
        user_grid.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.total_users')}:"), 0, 0)
        self.total_users_label = QLabel("0")
        self.total_users_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        user_grid.addWidget(self.total_users_label, 0, 1)
        
        user_grid.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.active_users')}:"), 0, 2)
        self.active_users_label = QLabel("0")
        self.active_users_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        user_grid.addWidget(self.active_users_label, 0, 3)
        
        user_grid.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.online_users')}:"), 1, 0)
        self.online_users_label = QLabel("0")
        self.online_users_label.setStyleSheet("font-weight: bold; color: #FF9800;")
        user_grid.addWidget(self.online_users_label, 1, 1)
        
        user_grid.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.verified_users')}:"), 1, 2)
        self.verified_users_label = QLabel("0")
        self.verified_users_label.setStyleSheet("font-weight: bold; color: #9C27B0;")
        user_grid.addWidget(self.verified_users_label, 1, 3)
        
        user_stats_layout.addLayout(user_grid)
        stats_layout.addWidget(user_stats_frame, 0, 0)
        
        # Server statistics
        server_stats_frame = QFrame()
        server_stats_frame.setFrameStyle(QFrame.StyledPanel)
        server_stats_layout = QVBoxLayout(server_stats_frame)
        
        server_stats_layout.addWidget(QLabel(language_manager.translate("ui.dashboard.server_statistics"), styleSheet="font-weight: bold;"))
        
        # Server stats grid
        server_grid = QGridLayout()
        
        server_grid.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.total_requests')}:"), 0, 0)
        self.total_requests_label = QLabel("0")
        self.total_requests_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        server_grid.addWidget(self.total_requests_label, 0, 1)
        
        server_grid.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.error_count')}:"), 0, 2)
        self.error_count_label = QLabel("0")
        self.error_count_label.setStyleSheet("font-weight: bold; color: #F44336;")
        server_grid.addWidget(self.error_count_label, 0, 3)
        
        server_grid.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.server_uptime')}:"), 1, 0)
        self.server_uptime_label = QLabel(language_manager.translate("ui.common.na"))
        self.server_uptime_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        server_grid.addWidget(self.server_uptime_label, 1, 1)
        
        server_stats_layout.addLayout(server_grid)
        stats_layout.addWidget(server_stats_frame, 0, 1)
        
        layout.addWidget(stats_group)
    
    def _create_metrics_section(self, layout: QVBoxLayout):
        """Create the metrics section."""
        metrics_group = QGroupBox(language_manager.translate("ui.dashboard.system_metrics"))
        metrics_layout = QGridLayout(metrics_group)
        
        # CPU usage
        metrics_layout.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.cpu_usage')}:"), 0, 0)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setValue(0)
        self.cpu_progress.setFormat("CPU: %p%")
        metrics_layout.addWidget(self.cpu_progress, 0, 1)
        
        # Memory usage
        metrics_layout.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.memory_usage')}:"), 1, 0)
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_progress.setValue(0)
        self.memory_progress.setFormat("Memory: %p%")
        metrics_layout.addWidget(self.memory_progress, 1, 1)
        
        # Disk usage
        metrics_layout.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.disk_usage')}:"), 2, 0)
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        self.disk_progress.setValue(0)
        self.disk_progress.setFormat("Disk: %p%")
        metrics_layout.addWidget(self.disk_progress, 2, 1)
        
        # Memory details
        metrics_layout.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.memory_details')}:"), 0, 2)
        self.memory_details_label = QLabel(language_manager.translate("ui.common.na"))
        self.memory_details_label.setStyleSheet("font-family: monospace; font-size: 10px;")
        metrics_layout.addWidget(self.memory_details_label, 0, 3)
        
        # Disk details
        metrics_layout.addWidget(QLabel(f"{language_manager.translate('ui.dashboard.disk_details')}:"), 1, 2)
        self.disk_details_label = QLabel(language_manager.translate("ui.common.na"))
        self.disk_details_label.setStyleSheet("font-family: monospace; font-size: 10px;")
        metrics_layout.addWidget(self.disk_details_label, 1, 3)
        
        layout.addWidget(metrics_group)
    
    def _create_activities_section(self, layout: QVBoxLayout):
        """Create the recent activities section."""
        activities_group = QGroupBox(language_manager.translate("ui.dashboard.recent_activities"))
        activities_layout = QVBoxLayout(activities_group)
        
        # Activities table
        self.activities_table = QTableWidget()
        self.activities_table.setColumnCount(4)
        self.activities_table.setHorizontalHeaderLabels([
            language_manager.translate("ui.dashboard.time"), 
            language_manager.translate("ui.dashboard.type"), 
            language_manager.translate("ui.dashboard.user"), 
            language_manager.translate("ui.dashboard.description")
        ])
        
        # Configure table
        self.activities_table.setAlternatingRowColors(True)
        self.activities_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.activities_table.horizontalHeader().setStretchLastSection(True)
        self.activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.activities_table.setMaximumHeight(200)
        
        activities_layout.addWidget(self.activities_table)
        
        layout.addWidget(activities_group)
    
    def _update_server_status_display(self):
        """Update server status display."""
        try:
            if self.server_status:
                is_running = self.server_status.get('is_running', False)
                
                if is_running:
                    self.server_status_label.setText(language_manager.translate("server.online"))
                    self.server_status_label.setProperty("class", "status-online")
                    
                    # Update server URL
                    url = self.server_status.get('url', language_manager.translate("ui.common.na"))
                    self.server_url_label.setText(url)
                    
                    # Update server uptime
                    uptime_seconds = self.server_status.get('uptime_seconds')
                    if uptime_seconds:
                        hours = int(uptime_seconds // 3600)
                        minutes = int((uptime_seconds % 3600) // 60)
                        seconds = int(uptime_seconds % 60)
                        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        self.server_uptime_label.setText(uptime_str)
                    
                    # Update request count
                    request_count = self.server_status.get('request_count', 0)
                    self.total_requests_label.setText(str(request_count))
                    
                    # Update error count
                    error_count = self.server_status.get('error_count', 0)
                    self.error_count_label.setText(str(error_count))
                else:
                    self.server_status_label.setText(language_manager.translate("server.offline"))
                    self.server_status_label.setProperty("class", "status-offline")
                    self.server_url_label.setText(language_manager.translate("ui.common.na"))
                    self.server_uptime_label.setText(language_manager.translate("ui.common.na"))
                    self.total_requests_label.setText("0")
                    self.error_count_label.setText("0")
                    
        except Exception as e:
            self.logger.error(f"Error updating server status display: {e}")
    
    def _update_user_statistics_display(self):
        """Update user statistics display."""
        try:
            if self.user_stats:
                self.total_users_label.setText(str(self.user_stats.get('total_users', 0)))
                self.active_users_label.setText(str(self.user_stats.get('active_users', 0)))
                self.online_users_label.setText(str(self.user_stats.get('online_users', 0)))
                self.verified_users_label.setText(str(self.user_stats.get('verified_users', 0)))
                
        except Exception as e:
            self.logger.error(f"Error updating user statistics display: {e}")
    
    def _update_system_metrics_display(self):
        """Update system metrics display."""
        try:
            if self.system_metrics:
                # Update progress bars
                cpu_percent = self.system_metrics.get('cpu_percent', 0)
                self.cpu_progress.setValue(int(cpu_percent))
                
                memory_percent = self.system_metrics.get('memory_percent', 0)
                self.memory_progress.setValue(int(memory_percent))
                
                disk_percent = self.system_metrics.get('disk_percent', 0)
                self.disk_progress.setValue(int(disk_percent))
                
                # Update memory details
                memory_used = self.system_metrics.get('memory_used_gb', 0)
                memory_total = self.system_metrics.get('memory_total_gb', 0)
                self.memory_details_label.setText(f"{memory_used:.1f}GB / {memory_total:.1f}GB")
                
                # Update disk details
                disk_used = self.system_metrics.get('disk_used_gb', 0)
                disk_total = self.system_metrics.get('disk_total_gb', 0)
                self.disk_details_label.setText(f"{disk_used:.1f}GB / {disk_total:.1f}GB")
                
                # Update system uptime
                uptime = self.system_metrics.get('uptime', 'N/A')
                self.system_uptime_label.setText(uptime)
                
                # Update boot time
                boot_time = self.system_metrics.get('boot_time', 'N/A')
                self.boot_time_label.setText(boot_time)
                
        except Exception as e:
            self.logger.error(f"Error updating system metrics display: {e}")
    
    def _update_activities_display(self):
        """Update activities display (optimized for performance)."""
        try:
            if not self.recent_activities:
                return
            
            # Disable table updates during population to prevent UI freezing
            self.activities_table.setUpdatesEnabled(False)
            
            # Limit the number of activities to display for better performance
            max_activities = 50
            activities_to_show = self.recent_activities[:max_activities]
            
            self.activities_table.setRowCount(len(activities_to_show))
            
            for row, activity in enumerate(activities_to_show):
                self.activities_table.setItem(row, 0, QTableWidgetItem(activity.get('time', '')))
                self.activities_table.setItem(row, 1, QTableWidgetItem(activity.get('type', '')))
                self.activities_table.setItem(row, 2, QTableWidgetItem(activity.get('user', '')))
                self.activities_table.setItem(row, 3, QTableWidgetItem(activity.get('description', '')))
            
            # Re-enable table updates after population
            self.activities_table.setUpdatesEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Error updating activities display: {e}")
            # Make sure to re-enable updates even if there's an error
            self.activities_table.setUpdatesEnabled(True)
    
    def refresh_data(self):
        """Refresh dashboard data (non-blocking)."""
        try:
            self._request_data_refresh()
            self.update_status("Dashboard data refresh requested")
        except Exception as e:
            self.show_error(f"Failed to refresh dashboard data: {e}")
    
    def get_tab_data(self) -> Dict[str, Any]:
        """Get dashboard tab data."""
        return {
            **super().get_tab_data(),
            "server_status": self.server_status,
            "user_stats": self.user_stats,
            "system_metrics": self.system_metrics,
            "activities_count": len(self.recent_activities)
        }