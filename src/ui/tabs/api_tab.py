"""
API tab for API endpoint management and monitoring.

This tab provides API endpoint management, monitoring, and analytics.
"""

from typing import Dict, Any, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QLineEdit, QComboBox, QCheckBox, QMessageBox,
    QHeaderView, QAbstractItemView, QProgressBar, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont

from .base_tab import BaseTab, BaseTabWorker
from ...utils.logger import logger
from ...core.language import language_manager


class ApiWorker(BaseTabWorker):
    """API tab worker for background data operations."""
    
    def __init__(self):
        super().__init__("api")
        self.api_manager = None
    
    def _do_refresh_data(self):
        """Refresh API data in background thread."""
        try:
            if not self.running:
                return
            
            # Get API manager from main app
            from ...app import App
            app = App.instance()
            if app and hasattr(app, 'server_manager'):
                self.api_manager = app.server_manager
            
            # Collect API data
            api_data = {
                'endpoints': self._get_endpoints_data(),
                'metrics': self._get_api_metrics(),
                'recent_requests': self._get_recent_requests(),
                'server_status': self._get_server_status()
            }
            
            self.data_ready.emit(api_data)
            
        except Exception as e:
            self.logger.error(f"Error refreshing API data: {e}")
            self.error_occurred.emit(str(e))
    
    def _get_endpoints_data(self):
        """Get API endpoints data."""
        try:
            # Default API endpoints
            endpoints = [
                {
                    'method': 'GET',
                    'path': '/api/v1/health',
                    'is_active': True,
                    'request_count': 0,
                    'avg_response_time': 0,
                    'last_used': 'Never'
                },
                {
                    'method': 'POST',
                    'path': '/api/v1/auth/login',
                    'is_active': True,
                    'request_count': 0,
                    'avg_response_time': 0,
                    'last_used': 'Never'
                },
                {
                    'method': 'GET',
                    'path': '/api/v1/users',
                    'is_active': True,
                    'request_count': 0,
                    'avg_response_time': 0,
                    'last_used': 'Never'
                },
                {
                    'method': 'GET',
                    'path': '/api/v1/server/status',
                    'is_active': True,
                    'request_count': 0,
                    'avg_response_time': 0,
                    'last_used': 'Never'
                },
                {
                    'method': 'POST',
                    'path': '/api/v1/server/start',
                    'is_active': True,
                    'request_count': 0,
                    'avg_response_time': 0,
                    'last_used': 'Never'
                },
                {
                    'method': 'POST',
                    'path': '/api/v1/server/stop',
                    'is_active': True,
                    'request_count': 0,
                    'avg_response_time': 0,
                    'last_used': 'Never'
                }
            ]
            
            # If server manager is available, get real data
            if self.api_manager and hasattr(self.api_manager, 'get_detailed_stats'):
                try:
                    stats = self.api_manager.get_detailed_stats()
                    if stats and 'endpoint_stats' in stats:
                        for endpoint in endpoints:
                            path = endpoint['path']
                            if path in stats['endpoint_stats']:
                                endpoint_stats = stats['endpoint_stats'][path]
                                endpoint['request_count'] = endpoint_stats.get('count', 0)
                                endpoint['avg_response_time'] = endpoint_stats.get('avg_response_time', 0)
                                endpoint['last_used'] = endpoint_stats.get('last_used', 'Never')
                except Exception as e:
                    self.logger.warning(f"Could not get real API stats: {e}")
            
            return endpoints
            
        except Exception as e:
            self.logger.error(f"Error getting endpoints data: {e}")
            return []
    
    def _get_api_metrics(self):
        """Get API metrics data."""
        try:
            metrics = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0,
                'requests_per_minute': 0,
                'active_connections': 0
            }
            
            # If server manager is available, get real metrics
            if self.api_manager and hasattr(self.api_manager, 'get_detailed_stats'):
                try:
                    stats = self.api_manager.get_detailed_stats()
                    if stats:
                        metrics.update({
                            'total_requests': stats.get('total_requests', 0),
                            'successful_requests': stats.get('successful_requests', 0),
                            'failed_requests': stats.get('failed_requests', 0),
                            'avg_response_time': stats.get('avg_response_time', 0),
                            'requests_per_minute': stats.get('requests_per_minute', 0),
                            'active_connections': stats.get('active_connections', 0)
                        })
                except Exception as e:
                    self.logger.warning(f"Could not get real API metrics: {e}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting API metrics: {e}")
            return {}
    
    def _get_recent_requests(self):
        """Get recent API requests."""
        try:
            recent_requests = []
            
            # If server manager is available, get real data
            if self.api_manager and hasattr(self.api_manager, 'get_api_logs'):
                try:
                    api_logs = self.api_manager.get_api_logs()
                    if api_logs:
                        # Get last 10 requests
                        recent_requests = api_logs[-10:] if len(api_logs) > 10 else api_logs
                except Exception as e:
                    self.logger.warning(f"Could not get real API logs: {e}")
            
            return recent_requests
            
        except Exception as e:
            self.logger.error(f"Error getting recent requests: {e}")
            return []
    
    def _get_server_status(self):
        """Get server status."""
        try:
            status = {
                'is_running': False,
                'uptime': '0s',
                'host': '127.0.0.1',
                'port': 8080,
                'ssl_enabled': False
            }
            
            # If server manager is available, get real status
            if self.api_manager and hasattr(self.api_manager, 'is_running'):
                try:
                    status['is_running'] = self.api_manager.is_running()
                    if hasattr(self.api_manager, 'get_uptime'):
                        status['uptime'] = self.api_manager.get_uptime()
                except Exception as e:
                    self.logger.warning(f"Could not get real server status: {e}")
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting server status: {e}")
            return {}


class ApiTab(BaseTab):
    """
    API tab for API endpoint management and monitoring.
    
    This tab provides functionality for managing API endpoints,
    monitoring API performance, and viewing API analytics.
    """
    
    def __init__(self):
        """Initialize the API tab."""
        super().__init__("api", "API Management")
        
        # Data storage
        self.endpoints = []
        self.api_metrics = {}
        self.recent_requests = []
        
        # Create API management components
        self._create_api_components()
        
        # Set refresh interval
        self.set_refresh_interval(5000)  # 5 seconds
        
        # Override worker with API-specific worker
        self._init_api_worker()
        
        self.logger.info("API tab initialized")
    
    def _init_api_worker(self):
        """Initialize API-specific worker."""
        try:
            # Use base class lazy loading
            self._ensure_worker_thread()
            
            # Create new API worker if not exists
            if not self.worker:
                self.worker = ApiWorker()
                
                # Connect signals
                self.worker.data_ready.connect(self._on_data_ready)
                self.worker.error_occurred.connect(self._on_error_occurred)
                
                # Move worker to thread
            self.worker.moveToThread(self.worker_thread)
            
            # Start worker
            self.worker_thread.started.connect(self.worker.start_worker)
            self.worker_thread.start()
            
            self.logger.info("API worker initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize API worker: {e}")
    
    def _on_data_ready(self, data: dict):
        """Handle data ready from worker."""
        try:
            # Update local data
            self.endpoints = data.get('endpoints', [])
            self.api_metrics = data.get('metrics', {})
            self.recent_requests = data.get('recent_requests', [])
            
            # Update UI
            self._update_api_ui()
            
        except Exception as e:
            self.logger.error(f"Error handling API data: {e}")
    
    def _on_error_occurred(self, error_message: str):
        """Handle error from worker."""
        self.logger.error(f"API worker error: {error_message}")
        self.update_status(f"API Error: {error_message}", "error")
    
    def _update_api_ui(self):
        """Update API UI with current data."""
        try:
            # Update endpoints table
            if hasattr(self, 'endpoints_table'):
                self._populate_endpoints_table()
            
            # Update metrics
            self._update_metrics_display()
            
            # Update recent requests
            self._update_recent_requests()
            
        except Exception as e:
            self.logger.error(f"Error updating API UI: {e}")
    
    def _create_api_components(self) -> None:
        """Create API management components."""
        try:
            # Initialize API components
            self.api_widgets = {}
            self.endpoint_widgets = {}
            self.metrics_widgets = {}
            
            # Create API management widgets
            self._create_api_widgets()
            
            # Create endpoint widgets
            self._create_endpoint_widgets()
            
            # Create metrics widgets
            self._create_metrics_widgets()
            
            self.logger.info("API components created")
            
        except Exception as e:
            self.logger.error(f"Failed to create API components: {e}")
    
    def _create_api_widgets(self) -> None:
        """Create API management widgets."""
        try:
            # API status widget
            self.api_widgets['status'] = {
                'server_status': 'offline',
                'endpoints_count': 0,
                'active_connections': 0,
                'uptime': '0s'
            }
            
            # API configuration
            self.api_widgets['config'] = {
                'host': '127.0.0.1',
                'port': 8080,
                'ssl_enabled': False,
                'cors_enabled': True,
                'rate_limiting': True
            }
            
            # API actions
            self.api_widgets['actions'] = {
                'start': {'enabled': True, 'text': 'API Başlat'},
                'stop': {'enabled': False, 'text': 'API Durdur'},
                'restart': {'enabled': False, 'text': 'API Yeniden Başlat'},
                'test': {'enabled': False, 'text': 'API Test Et'}
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create API widgets: {e}")
    
    def _create_endpoint_widgets(self) -> None:
        """Create endpoint widgets."""
        try:
            # Endpoint list
            self.endpoint_widgets['list'] = {
                'endpoints': [
                    {'method': 'GET', 'path': '/api/v1/status', 'description': 'API durumu'},
                    {'method': 'POST', 'path': '/api/v1/auth/login', 'description': 'Kullanıcı girişi'},
                    {'method': 'GET', 'path': '/api/v1/users', 'description': 'Kullanıcı listesi'},
                    {'method': 'GET', 'path': '/api/v1/monitor/system', 'description': 'Sistem metrikleri'}
                ],
                'sortable': True,
                'filterable': True
            }
            
            # Endpoint details
            self.endpoint_widgets['details'] = {
                'method': 'GET',
                'path': '/api/v1/status',
                'description': 'API durumu',
                'parameters': [],
                'response': {'status': 'ok', 'message': 'API is running'},
                'rate_limit': 100,
                'auth_required': False
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create endpoint widgets: {e}")
    
    def _create_metrics_widgets(self) -> None:
        """Create metrics widgets."""
        try:
            # API metrics
            self.metrics_widgets['api'] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_response_time': 0,
                'requests_per_minute': 0
            }
            
            # Endpoint metrics
            self.metrics_widgets['endpoints'] = {
                'most_used': [],
                'slowest': [],
                'error_rate': {}
            }
            
            # Performance metrics
            self.metrics_widgets['performance'] = {
                'cpu_usage': 0,
                'memory_usage': 0,
                'active_connections': 0,
                'queue_size': 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create metrics widgets: {e}")
    
    def _create_content_widget(self) -> QWidget:
        """Create the API content widget."""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # API statistics section
        stats_group = self._create_statistics_section()
        layout.addWidget(stats_group)
        
        # Endpoints management section
        endpoints_group = self._create_endpoints_section()
        layout.addWidget(endpoints_group)
        
        # API analytics section
        analytics_group = self._create_analytics_section()
        layout.addWidget(analytics_group)
        
        return content_widget
    
    def _create_statistics_section(self) -> QGroupBox:
        """Create the API statistics section."""
        group = QGroupBox("API Statistics")
        layout = QGridLayout(group)
        
        # Total requests
        self.total_requests_label = QLabel("0")
        self.total_requests_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        layout.addWidget(QLabel("Total Requests:"), 0, 0)
        layout.addWidget(self.total_requests_label, 0, 1)
        
        # Successful requests
        self.successful_requests_label = QLabel("0")
        self.successful_requests_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(QLabel("Successful:"), 1, 0)
        layout.addWidget(self.successful_requests_label, 1, 1)
        
        # Failed requests
        self.failed_requests_label = QLabel("0")
        self.failed_requests_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #F44336;")
        layout.addWidget(QLabel("Failed:"), 2, 0)
        layout.addWidget(self.failed_requests_label, 2, 1)
        
        # Average response time
        self.avg_response_time_label = QLabel("0ms")
        self.avg_response_time_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FF9800;")
        layout.addWidget(QLabel("Avg Response Time:"), 3, 0)
        layout.addWidget(self.avg_response_time_label, 3, 1)
        
        return group
    
    def _create_endpoints_section(self) -> QGroupBox:
        """Create the endpoints management section."""
        group = QGroupBox("API Endpoints")
        layout = QVBoxLayout(group)
        
        # Endpoints toolbar
        toolbar_layout = QHBoxLayout()
        
        self.refresh_endpoints_btn = QPushButton("Refresh")
        self.refresh_endpoints_btn.setIcon(QIcon("data/resources/icons/actions/refresh.png"))
        self.refresh_endpoints_btn.clicked.connect(self._refresh_endpoints)
        toolbar_layout.addWidget(self.refresh_endpoints_btn)
        
        self.toggle_all_btn = QPushButton("Toggle All")
        self.toggle_all_btn.clicked.connect(self._toggle_all_endpoints)
        toolbar_layout.addWidget(self.toggle_all_btn)
        
        toolbar_layout.addStretch()
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search endpoints...")
        self.search_input.textChanged.connect(self._search_endpoints)
        toolbar_layout.addWidget(QLabel("Search:"))
        toolbar_layout.addWidget(self.search_input)
        
        layout.addLayout(toolbar_layout)
        
        # Endpoints table
        self.endpoints_table = QTableWidget()
        self.endpoints_table.setColumnCount(6)
        self.endpoints_table.setHorizontalHeaderLabels([
            "Method", "Path", "Status", "Requests", "Avg Time", "Last Used"
        ])
        
        # Configure table
        self.endpoints_table.setAlternatingRowColors(True)
        self.endpoints_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.endpoints_table.horizontalHeader().setStretchLastSection(True)
        self.endpoints_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        layout.addWidget(self.endpoints_table)
        
        return group
    
    def _create_analytics_section(self) -> QGroupBox:
        """Create the API analytics section."""
        group = QGroupBox("API Analytics")
        layout = QVBoxLayout(group)
        
        # Analytics tabs or sections
        analytics_layout = QHBoxLayout()
        
        # Top endpoints
        top_endpoints_group = QGroupBox("Top Endpoints")
        top_endpoints_layout = QVBoxLayout(top_endpoints_group)
        
        self.top_endpoints_list = QTextEdit()
        self.top_endpoints_list.setReadOnly(True)
        self.top_endpoints_list.setMaximumHeight(150)
        top_endpoints_layout.addWidget(self.top_endpoints_list)
        
        analytics_layout.addWidget(top_endpoints_group)
        
        # Response time distribution
        response_time_group = QGroupBox("Response Time Distribution")
        response_time_layout = QVBoxLayout(response_time_group)
        
        # Response time ranges
        self.response_time_0_100 = QProgressBar()
        self.response_time_0_100.setFormat("0-100ms: %p%")
        response_time_layout.addWidget(self.response_time_0_100)
        
        self.response_time_100_500 = QProgressBar()
        self.response_time_100_500.setFormat("100-500ms: %p%")
        response_time_layout.addWidget(self.response_time_100_500)
        
        self.response_time_500_1000 = QProgressBar()
        self.response_time_500_1000.setFormat("500ms-1s: %p%")
        response_time_layout.addWidget(self.response_time_500_1000)
        
        self.response_time_1000_plus = QProgressBar()
        self.response_time_1000_plus.setFormat("1s+: %p%")
        response_time_layout.addWidget(self.response_time_1000_plus)
        
        analytics_layout.addWidget(response_time_group)
        
        layout.addLayout(analytics_layout)
        
        return group
    
    def refresh_data(self):
        """Refresh API data."""
        try:
            # Load endpoints
            self._load_endpoints()
            
            # Load API metrics
            self._load_api_metrics()
            
            # Load analytics
            self._load_analytics()
            
            self.update_status("API data refreshed")
            
        except Exception as e:
            self.show_error(f"Failed to refresh API data: {e}")
    
    def _load_endpoints(self):
        """Load API endpoints."""
        try:
            # Placeholder data - in real implementation, this would come from API service
            placeholder_endpoints = [
                {
                    "method": "GET",
                    "path": "/api/v1/status",
                    "is_active": True,
                    "request_count": 1250,
                    "avg_response_time": 45,
                    "last_used": "2024-01-15 10:30:00"
                },
                {
                    "method": "POST",
                    "path": "/api/v1/auth/login",
                    "is_active": True,
                    "request_count": 890,
                    "avg_response_time": 120,
                    "last_used": "2024-01-15 10:29:45"
                },
                {
                    "method": "GET",
                    "path": "/api/v1/users",
                    "is_active": True,
                    "request_count": 650,
                    "avg_response_time": 85,
                    "last_used": "2024-01-15 10:28:30"
                },
                {
                    "method": "PUT",
                    "path": "/api/v1/users/{id}",
                    "is_active": False,
                    "request_count": 45,
                    "avg_response_time": 200,
                    "last_used": "2024-01-15 09:15:20"
                }
            ]
            
            self.endpoints = placeholder_endpoints
            self._populate_endpoints_table()
            
        except Exception as e:
            self.logger.error(f"Failed to load endpoints: {e}")
    
    def _load_api_metrics(self):
        """Load API metrics."""
        try:
            # Calculate metrics from endpoints
            total_requests = sum(endpoint.get('request_count', 0) for endpoint in self.endpoints)
            successful_requests = int(total_requests * 0.95)  # Placeholder: 95% success rate
            failed_requests = total_requests - successful_requests
            
            avg_response_time = 0
            if self.endpoints:
                total_time = sum(endpoint.get('avg_response_time', 0) for endpoint in self.endpoints)
                avg_response_time = total_time / len(self.endpoints)
            
            # Update labels
            self.total_requests_label.setText(str(total_requests))
            self.successful_requests_label.setText(str(successful_requests))
            self.failed_requests_label.setText(str(failed_requests))
            self.avg_response_time_label.setText(f"{avg_response_time:.0f}ms")
            
            self.api_metrics = {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "avg_response_time": avg_response_time
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load API metrics: {e}")
    
    def _load_analytics(self):
        """Load API analytics."""
        try:
            # Top endpoints
            sorted_endpoints = sorted(self.endpoints, key=lambda x: x.get('request_count', 0), reverse=True)
            top_endpoints_text = ""
            
            for i, endpoint in enumerate(sorted_endpoints[:5]):
                method = endpoint.get('method', '')
                path = endpoint.get('path', '')
                count = endpoint.get('request_count', 0)
                top_endpoints_text += f"{i+1}. {method} {path} - {count} requests\n"
            
            self.top_endpoints_list.setText(top_endpoints_text)
            
            # Response time distribution (placeholder)
            self.response_time_0_100.setValue(60)
            self.response_time_100_500.setValue(30)
            self.response_time_500_1000.setValue(8)
            self.response_time_1000_plus.setValue(2)
            
        except Exception as e:
            self.logger.error(f"Failed to load analytics: {e}")
    
    def _populate_endpoints_table(self):
        """Populate the endpoints table (optimized for performance)."""
        try:
            # Disable table updates during population to prevent UI freezing
            self.endpoints_table.setUpdatesEnabled(False)
            
            # Limit the number of endpoints to display for better performance
            max_endpoints = 100
            endpoints_to_show = self.endpoints[:max_endpoints]
            
            self.endpoints_table.setRowCount(len(endpoints_to_show))
            
            for row, endpoint in enumerate(endpoints_to_show):
                # Method
                method_item = QTableWidgetItem(endpoint.get('method', ''))
                method_item.setTextAlignment(Qt.AlignCenter)
                self.endpoints_table.setItem(row, 0, method_item)
                
                # Path
                self.endpoints_table.setItem(row, 1, QTableWidgetItem(endpoint.get('path', '')))
                
                # Status
                status = "Active" if endpoint.get('is_active', False) else "Inactive"
                status_item = QTableWidgetItem(status)
                if endpoint.get('is_active', False):
                    status_item.setBackground(Qt.green)
                else:
                    status_item.setBackground(Qt.red)
                self.endpoints_table.setItem(row, 2, status_item)
                
                # Request count
                self.endpoints_table.setItem(row, 3, QTableWidgetItem(str(endpoint.get('request_count', 0))))
                
                # Average response time
                avg_time = endpoint.get('avg_response_time', 0)
                self.endpoints_table.setItem(row, 4, QTableWidgetItem(f"{avg_time}ms"))
                
                # Last used
                self.endpoints_table.setItem(row, 5, QTableWidgetItem(endpoint.get('last_used', 'Never')))
            
            # Re-enable table updates after population
            self.endpoints_table.setUpdatesEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Failed to populate endpoints table: {e}")
            # Make sure to re-enable updates even if there's an error
            self.endpoints_table.setUpdatesEnabled(True)
    
    def _update_metrics_display(self):
        """Update metrics display with current data."""
        try:
            if not hasattr(self, 'metrics_widgets'):
                return
            
            # Update total requests
            if 'total_requests' in self.metrics_widgets:
                self.metrics_widgets['total_requests'].setText(
                    str(self.api_metrics.get('total_requests', 0))
                )
            
            # Update successful requests
            if 'successful_requests' in self.metrics_widgets:
                self.metrics_widgets['successful_requests'].setText(
                    str(self.api_metrics.get('successful_requests', 0))
                )
            
            # Update failed requests
            if 'failed_requests' in self.metrics_widgets:
                self.metrics_widgets['failed_requests'].setText(
                    str(self.api_metrics.get('failed_requests', 0))
                )
            
            # Update average response time
            if 'avg_response_time' in self.metrics_widgets:
                avg_time = self.api_metrics.get('avg_response_time', 0)
                self.metrics_widgets['avg_response_time'].setText(f"{avg_time}ms")
            
            # Update requests per minute
            if 'requests_per_minute' in self.metrics_widgets:
                self.metrics_widgets['requests_per_minute'].setText(
                    str(self.api_metrics.get('requests_per_minute', 0))
                )
            
            # Update active connections
            if 'active_connections' in self.metrics_widgets:
                self.metrics_widgets['active_connections'].setText(
                    str(self.api_metrics.get('active_connections', 0))
                )
            
        except Exception as e:
            self.logger.error(f"Error updating metrics display: {e}")
    
    def _update_recent_requests(self):
        """Update recent requests display."""
        try:
            if not hasattr(self, 'recent_requests_text'):
                return
            
            # Clear existing content
            self.recent_requests_text.clear()
            
            # Add recent requests
            if self.recent_requests:
                for request in self.recent_requests:
                    timestamp = request.get('timestamp', 'Unknown')
                    method = request.get('method', 'Unknown')
                    path = request.get('path', 'Unknown')
                    status = request.get('status_code', 'Unknown')
                    response_time = request.get('response_time', 0)
                    
                    request_text = f"[{timestamp}] {method} {path} - {status} ({response_time}ms)\n"
                    self.recent_requests_text.append(request_text)
            else:
                self.recent_requests_text.append("No recent requests")
            
        except Exception as e:
            self.logger.error(f"Error updating recent requests: {e}")
    
    def _search_endpoints(self, search_text: str):
        """Search and filter endpoints."""
        try:
            if not search_text:
                self._populate_endpoints_table()
                return
            
            # Filter endpoints based on search text
            filtered_endpoints = []
            search_lower = search_text.lower()
            
            for endpoint in self.endpoints:
                if (search_lower in endpoint.get('method', '').lower() or
                    search_lower in endpoint.get('path', '').lower()):
                    filtered_endpoints.append(endpoint)
            
            # Update table with filtered results
            self.endpoints_table.setRowCount(len(filtered_endpoints))
            
            for row, endpoint in enumerate(filtered_endpoints):
                self.endpoints_table.setItem(row, 0, QTableWidgetItem(endpoint.get('method', '')))
                self.endpoints_table.setItem(row, 1, QTableWidgetItem(endpoint.get('path', '')))
                
                status = "Active" if endpoint.get('is_active', False) else "Inactive"
                status_item = QTableWidgetItem(status)
                if endpoint.get('is_active', False):
                    status_item.setBackground(Qt.green)
                else:
                    status_item.setBackground(Qt.red)
                self.endpoints_table.setItem(row, 2, status_item)
                
                self.endpoints_table.setItem(row, 3, QTableWidgetItem(str(endpoint.get('request_count', 0))))
                self.endpoints_table.setItem(row, 4, QTableWidgetItem(f"{endpoint.get('avg_response_time', 0)}ms"))
                self.endpoints_table.setItem(row, 5, QTableWidgetItem(endpoint.get('last_used', 'Never')))
            
        except Exception as e:
            self.logger.error(f"Failed to search endpoints: {e}")
    
    def _refresh_endpoints(self):
        """Refresh endpoints data."""
        self._load_endpoints()
        self.show_success("Endpoints refreshed")
    
    def _toggle_all_endpoints(self):
        """Toggle all endpoints active/inactive."""
        try:
            # Check if all are active
            all_active = all(endpoint.get('is_active', False) for endpoint in self.endpoints)
            
            # Toggle all endpoints
            for endpoint in self.endpoints:
                endpoint['is_active'] = not all_active
            
            # Refresh table
            self._populate_endpoints_table()
            
            action = "activated" if not all_active else "deactivated"
            self.show_success(f"All endpoints {action}")
            
        except Exception as e:
            self.show_error(f"Failed to toggle endpoints: {e}")
    
    def get_tab_data(self) -> Dict[str, Any]:
        """Get API tab data."""
        return {
            **super().get_tab_data(),
            "endpoints_count": len(self.endpoints),
            "api_metrics": self.api_metrics,
            "search_text": self.search_input.text()
        }
