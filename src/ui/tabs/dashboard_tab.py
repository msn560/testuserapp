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
        """Create the system overview section with modern cards."""
        # Title
        title_label = QLabel(language_manager.translate("ui.dashboard.system_overview"))
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Cards container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        # Server Status Card
        server_card = self._create_status_card(
            "🖥️", 
            language_manager.translate("ui.dashboard.server_status"),
            "offline"
        )
        cards_layout.addWidget(server_card)
        
        # System Uptime Card
        uptime_card = self._create_info_card(
            "⏱️",
            language_manager.translate("ui.dashboard.system_uptime"),
            "N/A"
        )
        cards_layout.addWidget(uptime_card)
        
        # Boot Time Card
        boot_card = self._create_info_card(
            "🚀",
            language_manager.translate("ui.dashboard.boot_time"),
            "N/A"
        )
        cards_layout.addWidget(boot_card)
        
        layout.addLayout(cards_layout)
    
    def _create_status_card(self, icon: str, title: str, status: str) -> QFrame:
        """Create a modern status card."""
        card = QFrame()
        card.setProperty("class", "card")
        card.setFixedHeight(120)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Icon and title
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setProperty("class", "card-title")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Status
        self.server_status_label = QLabel(language_manager.translate("server.offline"))
        self.server_status_label.setProperty("class", "status-offline")
        self.server_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.server_status_label)
        
        return card
    
    def _create_info_card(self, icon: str, title: str, value: str) -> QFrame:
        """Create a modern info card."""
        card = QFrame()
        card.setProperty("class", "card")
        card.setFixedHeight(120)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Icon and title
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setProperty("class", "card-title")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(value)
        value_label.setProperty("class", "metric-value")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("font-family: 'JetBrains Mono', monospace;")
        layout.addWidget(value_label)
        
        # Store reference for updates
        if title == language_manager.translate("ui.dashboard.system_uptime"):
            self.system_uptime_label = value_label
        elif title == language_manager.translate("ui.dashboard.boot_time"):
            self.boot_time_label = value_label
        
        return card
    
    def _create_stats_section(self, layout: QVBoxLayout):
        """Create the statistics section with modern metric cards."""
        # Title
        title_label = QLabel(language_manager.translate("ui.dashboard.statistics"))
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # User Statistics Row
        user_stats_layout = QHBoxLayout()
        user_stats_layout.setSpacing(16)
        
        # User metric cards
        user_cards = [
            ("👥", language_manager.translate("ui.dashboard.total_users"), "0", "info"),
            ("✅", language_manager.translate("ui.dashboard.active_users"), "0", "success"),
            ("🟢", language_manager.translate("ui.dashboard.online_users"), "0", "warning"),
            ("🔐", language_manager.translate("ui.dashboard.verified_users"), "0", "info")
        ]
        
        for icon, title, value, variant in user_cards:
            card = self._create_metric_card(icon, title, value, variant)
            user_stats_layout.addWidget(card)
            
            # Store references
            if "total_users" in title:
                self.total_users_label = card.findChild(QLabel, "value")
            elif "active_users" in title:
                self.active_users_label = card.findChild(QLabel, "value")
            elif "online_users" in title:
                self.online_users_label = card.findChild(QLabel, "value")
            elif "verified_users" in title:
                self.verified_users_label = card.findChild(QLabel, "value")
        
        layout.addLayout(user_stats_layout)
        
        # Server Statistics Row
        server_stats_layout = QHBoxLayout()
        server_stats_layout.setSpacing(16)
        
        # Server metric cards
        server_cards = [
            ("📊", language_manager.translate("ui.dashboard.total_requests"), "0", "info"),
            ("❌", language_manager.translate("ui.dashboard.error_count"), "0", "error"),
            ("⏰", language_manager.translate("ui.dashboard.server_uptime"), "N/A", "success")
        ]
        
        for icon, title, value, variant in server_cards:
            card = self._create_metric_card(icon, title, value, variant)
            server_stats_layout.addWidget(card)
            
            # Store references
            if "total_requests" in title:
                self.total_requests_label = card.findChild(QLabel, "value")
            elif "error_count" in title:
                self.error_count_label = card.findChild(QLabel, "value")
            elif "server_uptime" in title:
                self.server_uptime_label = card.findChild(QLabel, "value")
        
        layout.addLayout(server_stats_layout)
    
    def _create_metric_card(self, icon: str, title: str, value: str, variant: str = "info") -> QFrame:
        """Create a modern metric card."""
        card = QFrame()
        card.setProperty("class", "metric-card")
        card.setFixedSize(150, 100)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setProperty("class", "metric-value")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace;")
        layout.addWidget(value_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setProperty("class", "metric-label")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Apply variant styling
        if variant == "success":
            value_label.setStyleSheet("color: #3fb950; font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace;")
        elif variant == "warning":
            value_label.setStyleSheet("color: #d29922; font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace;")
        elif variant == "error":
            value_label.setStyleSheet("color: #f85149; font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace;")
        else:  # info
            value_label.setStyleSheet("color: #58a6ff; font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace;")
        
        return card
    
    def _create_metrics_section(self, layout: QVBoxLayout):
        """Create the metrics section with modern progress cards."""
        # Title
        title_label = QLabel(language_manager.translate("ui.dashboard.system_metrics"))
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Metrics container
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)
        
        # CPU Metrics Card
        cpu_card = self._create_progress_card(
            "💻",
            language_manager.translate("ui.dashboard.cpu_usage"),
            0,
            "info"
        )
        metrics_layout.addWidget(cpu_card)
        
        # Memory Metrics Card
        memory_card = self._create_progress_card(
            "🧠",
            language_manager.translate("ui.dashboard.memory_usage"),
            0,
            "warning"
        )
        metrics_layout.addWidget(memory_card)
        
        # Disk Metrics Card
        disk_card = self._create_progress_card(
            "💾",
            language_manager.translate("ui.dashboard.disk_usage"),
            0,
            "success"
        )
        metrics_layout.addWidget(disk_card)
        
        layout.addLayout(metrics_layout)
        
        # Details row
        details_layout = QHBoxLayout()
        details_layout.setSpacing(16)
        
        # Memory details
        memory_details_card = self._create_details_card(
            "📊",
            language_manager.translate("ui.dashboard.memory_details"),
            "N/A"
        )
        details_layout.addWidget(memory_details_card)
        
        # Disk details
        disk_details_card = self._create_details_card(
            "📈",
            language_manager.translate("ui.dashboard.disk_details"),
            "N/A"
        )
        details_layout.addWidget(disk_details_card)
        
        layout.addLayout(details_layout)
    
    def _create_progress_card(self, icon: str, title: str, value: int, variant: str = "info") -> QFrame:
        """Create a modern progress card."""
        card = QFrame()
        card.setProperty("class", "metric-card")
        card.setFixedSize(200, 120)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setProperty("class", "card-title")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(value)
        progress_bar.setProperty("class", variant)
        progress_bar.setFormat(f"{title}: %p%")
        layout.addWidget(progress_bar)
        
        # Store reference
        if "cpu_usage" in title:
            self.cpu_progress = progress_bar
        elif "memory_usage" in title:
            self.memory_progress = progress_bar
        elif "disk_usage" in title:
            self.disk_progress = progress_bar
        
        return card
    
    def _create_details_card(self, icon: str, title: str, value: str) -> QFrame:
        """Create a details card."""
        card = QFrame()
        card.setProperty("class", "card")
        card.setFixedHeight(80)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        
        # Header
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setProperty("class", "card-subtitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(value)
        value_label.setProperty("class", "metric-value")
        value_label.setStyleSheet("font-size: 14px; font-family: 'JetBrains Mono', monospace;")
        layout.addWidget(value_label)
        
        # Store reference
        if "memory_details" in title:
            self.memory_details_label = value_label
        elif "disk_details" in title:
            self.disk_details_label = value_label
        
        return card
    
    def _create_activities_section(self, layout: QVBoxLayout):
        """Create the recent activities section with modern styling."""
        # Title
        title_label = QLabel(language_manager.translate("ui.dashboard.recent_activities"))
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Activities container
        activities_container = QFrame()
        activities_container.setProperty("class", "card")
        activities_layout = QVBoxLayout(activities_container)
        activities_layout.setContentsMargins(16, 16, 16, 16)
        
        # Activities table
        self.activities_table = QTableWidget()
        self.activities_table.setColumnCount(4)
        self.activities_table.setHorizontalHeaderLabels([
            "⏰ " + language_manager.translate("ui.dashboard.time"), 
            "🏷️ " + language_manager.translate("ui.dashboard.type"), 
            "👤 " + language_manager.translate("ui.dashboard.user"), 
            "📝 " + language_manager.translate("ui.dashboard.description")
        ])
        
        # Configure table with modern styling
        self.activities_table.setAlternatingRowColors(True)
        self.activities_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.activities_table.horizontalHeader().setStretchLastSection(True)
        self.activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.activities_table.setMaximumHeight(250)
        self.activities_table.setShowGrid(False)
        self.activities_table.verticalHeader().setVisible(False)
        
        # Style the table
        self.activities_table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                selection-background-color: #1f6feb;
                selection-color: #ffffff;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border: none;
                border-bottom: 1px solid #21262d;
            }
            QTableWidget::item:selected {
                background-color: #1f6feb;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #21262d;
                color: #f0f6fc;
                padding: 12px 16px;
                border: none;
                border-bottom: 2px solid #30363d;
                font-weight: 600;
                font-size: 12px;
            }
        """)
        
        activities_layout.addWidget(self.activities_table)
        layout.addWidget(activities_container)
    
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