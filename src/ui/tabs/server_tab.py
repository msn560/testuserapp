"""
Server tab for server control and console output.

This tab provides server management controls and real-time console output
for monitoring server operations and logs.
"""

from typing import Dict, Any, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QGroupBox, QLineEdit,
    QSpinBox, QCheckBox, QComboBox, QSplitter, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QTextCursor
from PyQt5.QtGui import QFont, QTextCharFormat, QColor

from .base_tab import BaseTab, BaseTabWorker
from ...utils.logger import logger
from ...core.language import language_manager


class ServerWorker(BaseTabWorker):
    """
    Server worker that runs in a separate thread.
    """
    
    # Additional signals for server-specific data
    server_status_updated = pyqtSignal(dict)  # Server status
    console_log_updated = pyqtSignal(dict)    # Console log entry
    config_updated = pyqtSignal(dict)         # Server configuration
    
    def __init__(self):
        super().__init__("server")
        self.console_logs = []
        self.max_log_lines = 1000
        self.server_manager = None
    
    def _do_refresh_data(self):
        """Refresh server data in background thread."""
        try:
            if not self.running:
                return
            
            # Get server status (real-time)
            self._get_server_status()
            
            # Get console logs (real-time)
            self._get_console_logs()
            
            # Config is only loaded once when tab is activated, not on every refresh
            # This prevents UI inputs from being overwritten constantly
            
            # Emit general data ready signal
            self.data_ready.emit({
                "timestamp": self._get_timestamp(),
                "status": "ready"
            })
            
        except Exception as e:
            self.logger.error(f"Error refreshing server data: {e}")
            self.error_occurred.emit(str(e))
    
    def _get_server_status(self):
        """Get server status (non-blocking)."""
        try:
            # Try to get real server status from server manager
            if self.server_manager:
                server_status = self.server_manager.get_status()
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
                    "pid": None
                }
                self.server_status_updated.emit(server_status)
            
        except Exception as e:
            self.logger.error(f"Error getting server status: {e}")
    
    def _get_main_window(self):
        """Get main window instance safely."""
        try:
            # This is a worker thread, so we need to access main window differently
            # We'll use a signal to request data from the main thread
            return None  # Workers shouldn't directly access GUI
        except Exception as e:
            self.logger.error(f"Error getting main window from worker: {e}")
            return None
    
    def _get_console_logs(self):
        """Get console logs (non-blocking)."""
        try:
            # Get real-time server logs from server manager
            if self.server_manager:
                # Get server metrics and status
                status = self.server_manager.get_status()
                metrics = self.server_manager.get_metrics()
                
                # Only add logs if server is running and we have new data
                if status.get('is_running', False):
                    # Add server status log (only once when server starts)
                    if not hasattr(self, '_server_start_logged'):
                        self.console_log_updated.emit({
                            "timestamp": self._get_timestamp(),
                            "level": "INFO",
                            "message": f"🚀 Server started on {status.get('url', 'N/A')}"
                        })
                        self._server_start_logged = True
                    
                    # Add detailed metrics log (every few refreshes)
                    if not hasattr(self, '_metrics_counter'):
                        self._metrics_counter = 0
                    
                    self._metrics_counter += 1
                    if self._metrics_counter % 20 == 0:  # Every 20th refresh
                        # Detaylı istatistikleri al
                        detailed_stats = self.server_manager.get_detailed_stats()
                        
                        if detailed_stats:
                            uptime = status.get('uptime_seconds', 0)
                            if uptime:
                                hours = int(uptime // 3600)
                                minutes = int((uptime % 3600) // 60)
                                seconds = int(uptime % 60)
                                uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                                
                                # Server yoğunluk bilgileri
                                server_stats = detailed_stats.get('server', {})
                                traffic_stats = detailed_stats.get('traffic', {})
                                
                                # Ana istatistikler
                                self.console_log_updated.emit({
                                    "timestamp": self._get_timestamp(),
                                    "level": "INFO",
                                    "message": f"📊 Server Stats - Uptime: {uptime_str} | Active: {server_stats.get('active_connections', 0)} | Peak: {server_stats.get('peak_connections', 0)} | RPM: {server_stats.get('requests_per_minute', 0)}"
                                })
                                
                                # Traffic bilgileri
                                if traffic_stats.get('total_bytes', 0) > 0:
                                    total_mb = traffic_stats['total_bytes'] / (1024 * 1024)
                                    self.console_log_updated.emit({
                                        "timestamp": self._get_timestamp(),
                                        "level": "INFO",
                                        "message": f"🌐 Traffic - Total: {total_mb:.2f}MB | Sent: {traffic_stats.get('total_bytes_sent', 0)}B | Received: {traffic_stats.get('total_bytes_received', 0)}B"
                                    })
                                
                                # En popüler endpoint'ler
                                top_endpoints = detailed_stats.get('top_endpoints', [])
                                if top_endpoints:
                                    top_endpoint = top_endpoints[0]
                                    self.console_log_updated.emit({
                                        "timestamp": self._get_timestamp(),
                                        "level": "INFO",
                                        "message": f"🔥 Top Endpoint - {top_endpoint['endpoint']} ({top_endpoint['count']} requests, {top_endpoint['avg_time']}s avg)"
                                    })
                                
                                # Kullanıcı bilgileri
                                unique_users = server_stats.get('unique_users', 0)
                                if unique_users > 0:
                                    self.console_log_updated.emit({
                                        "timestamp": self._get_timestamp(),
                                        "level": "INFO",
                                        "message": f"👥 Users - {unique_users} unique users active"
                                    })
                                
                                # Son hatalar
                                recent_errors = detailed_stats.get('recent_errors', [])
                                if recent_errors:
                                    error = recent_errors[-1]  # En son hata
                                    self.console_log_updated.emit({
                                        "timestamp": self._get_timestamp(),
                                        "level": "WARNING",
                                        "message": f"⚠️ Recent Error - {error['method']} {error['path']} - {error['status_code']} from {error['ip']}"
                                    })
                    
                    # Get recent API logs
                    api_logs = self.server_manager.get_api_logs()
                    if api_logs and not hasattr(self, '_last_log_count'):
                        self._last_log_count = 0
                    
                    if api_logs and len(api_logs) > getattr(self, '_last_log_count', 0):
                        # Yeni log'lar var, bunları ekle
                        new_logs = api_logs[getattr(self, '_last_log_count', 0):]
                        for log in new_logs:
                            # Log'u console'a ekle
                            level = "INFO" if log['status_code'] < 400 else "ERROR"
                            icon = "✅" if log['status_code'] < 400 else "❌"
                            
                            self.console_log_updated.emit({
                                "timestamp": time.strftime("%H:%M:%S", time.localtime(log['timestamp'])),
                                "level": level,
                                "message": f"{icon} {log['method']} {log['path']} - {log['status_code']} ({log['response_time']:.3f}s) from {log['ip_address']}"
                            })
                        
                        self._last_log_count = len(api_logs)
                else:
                    # Server is stopped
                    if hasattr(self, '_server_start_logged'):
                        self.console_log_updated.emit({
                            "timestamp": self._get_timestamp(),
                            "level": "WARNING",
                            "message": "⏹️ Server stopped"
                        })
                        delattr(self, '_server_start_logged')
                        # Reset log counter
                        if hasattr(self, '_last_log_count'):
                            delattr(self, '_last_log_count')
            
        except Exception as e:
            self.logger.error(f"Error getting console logs: {e}")
    
    def _get_server_config(self):
        """Get server configuration (non-blocking)."""
        try:
            # This would normally get config from server manager
            # For now, emit placeholder data
            config = {
                "host": "127.0.0.1",
                "port": 8080,
                "ssl_enabled": False,
                "ssl_cert": "",
                "ssl_key": ""
            }
            self.config_updated.emit(config)
            
        except Exception as e:
            self.logger.error(f"Error getting server config: {e}")
    
    def add_console_log(self, log_data: dict):
        """Add a console log entry."""
        try:
            self.console_logs.append(log_data)
            
            # Keep only last max_log_lines
            if len(self.console_logs) > self.max_log_lines:
                self.console_logs = self.console_logs[-self.max_log_lines:]
            
            # Emit log update
            self.console_log_updated.emit(log_data)
            
        except Exception as e:
            self.logger.error(f"Error adding console log: {e}")
    
    def set_server_manager(self, server_manager):
        """Set server manager reference."""
        self.server_manager = server_manager
    
    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")


class ServerTab(BaseTab):
    """
    Server tab for server control and console monitoring.
    
    This tab provides controls for starting/stopping the server,
    configuration management, and real-time console output.
    """
    
    def __init__(self):
        """Initialize the server tab."""
        super().__init__("server", language_manager.translate("ui.server.server_control"))
        
        # Data storage
        self.server_config = {}
        self.console_logs = []
        self.max_log_lines = 1000
        self.server_manager = None
        
        # Create server components
        self._create_server_components()
        
        # Set longer refresh interval for server monitoring (config won't be reloaded constantly)
        self.set_refresh_interval(5000)  # 5 seconds
        
        # Connect server-specific signals
        self._connect_server_signals()
        
        self.logger.info("Server tab initialized")
    
    def showEvent(self, event):
        """Tab gösterildiğinde çağrılır."""
        super().showEvent(event)
        # Tab aktif olduğunda config'i bir kez yükle
        self._load_initial_config()
    
    def _create_worker(self) -> BaseTabWorker:
        """Create server worker instance."""
        return ServerWorker()
    
    def _connect_server_signals(self):
        """Connect server-specific signals."""
        try:
            if self.worker and isinstance(self.worker, ServerWorker):
                # Connect server-specific signals
                self.worker.server_status_updated.connect(self._on_server_status_updated)
                self.worker.console_log_updated.connect(self._on_console_log_updated)
                self.worker.config_updated.connect(self._on_config_updated)
                
        except Exception as e:
            self.logger.error(f"Failed to connect server signals: {e}")
    
    def _on_server_status_updated(self, status: dict):
        """Handle server status update from worker thread."""
        try:
            self._update_server_status(status)
        except Exception as e:
            self.logger.error(f"Error updating server status: {e}")
    
    def _on_console_log_updated(self, log_data: dict):
        """Handle console log update from worker thread."""
        try:
            self._add_console_log(log_data)
        except Exception as e:
            self.logger.error(f"Error updating console log: {e}")
    
    def _on_config_updated(self, config: dict):
        """Handle config update from worker thread."""
        try:
            # Only load config if tab is currently active
            # This prevents UI inputs from being overwritten when user is editing
            if self.isVisible():
                self._load_config(config)
        except Exception as e:
            self.logger.error(f"Error updating config: {e}")
    
    def _create_server_components(self) -> None:
        """Create server components."""
        try:
            # Initialize server components
            self.server_controls = {}
            self.console_widgets = {}
            self.status_indicators = {}
            
            # Create server control components
            self._create_server_controls()
            
            # Create console components
            self._create_console_components()
            
            # Create status indicators
            self._create_status_indicators()
            
            self.logger.info("Server components created")
            
        except Exception as e:
            self.logger.error(f"Failed to create server components: {e}")
    
    def _create_server_controls(self) -> None:
        """Create server control components."""
        try:
            # Start button
            self.server_controls['start'] = {
                'enabled': True,
                'text': 'Başlat',
                'action': 'start_server'
            }
            
            # Stop button
            self.server_controls['stop'] = {
                'enabled': False,
                'text': 'Durdur',
                'action': 'stop_server'
            }
            
            # Restart button
            self.server_controls['restart'] = {
                'enabled': False,
                'text': 'Yeniden Başlat',
                'action': 'restart_server'
            }
            
            # Server configuration
            self.server_controls['config'] = {
                'host': '127.0.0.1',
                'port': 8080,
                'ssl_enabled': False
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create server controls: {e}")
    
    def _create_console_components(self) -> None:
        """Create console components."""
        try:
            # Console output widget
            self.console_widgets['output'] = {
                'max_lines': 1000,
                'auto_scroll': True,
                'color_coding': True
            }
            
            # Console input widget
            self.console_widgets['input'] = {
                'enabled': False,
                'placeholder': 'Komut girin...'
            }
            
            # Console filters
            self.console_widgets['filters'] = {
                'level': 'all',
                'module': 'all',
                'search': ''
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create console components: {e}")
    
    def _create_status_indicators(self) -> None:
        """Create status indicators."""
        try:
            # Server status
            self.status_indicators['server'] = {
                'status': 'offline',
                'color': '#e74c3c',
                'text': 'Offline'
            }
            
            # Port status
            self.status_indicators['port'] = {
                'status': 'closed',
                'color': '#e74c3c',
                'text': 'Port Kapalı'
            }
            
            # SSL status
            self.status_indicators['ssl'] = {
                'status': 'disabled',
                'color': '#f39c12',
                'text': 'SSL Devre Dışı'
            }
            
            # Connection count
            self.status_indicators['connections'] = {
                'count': 0,
                'color': '#27ae60',
                'text': '0 Bağlantı'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create status indicators: {e}")
    
    def _create_content_widget(self) -> QWidget:
        """Create the server content widget."""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Server controls
        left_panel = self._create_control_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Console output
        right_panel = self._create_console_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions (40% controls, 60% console)
        splitter.setSizes([400, 600])
        
        return content_widget
    
    def _create_control_panel(self) -> QWidget:
        """Create the server control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Server status section
        status_group = self._create_status_section()
        layout.addWidget(status_group)
        
        # Server controls section
        controls_group = self._create_controls_section()
        layout.addWidget(controls_group)
        
        # Configuration section
        config_group = self._create_config_section()
        layout.addWidget(config_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return panel
    
    def _create_status_section(self) -> QGroupBox:
        """Create the server status section."""
        group = QGroupBox(language_manager.translate("ui.server.server_status"))
        layout = QGridLayout(group)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("font-size: 24px; color: red;")
        layout.addWidget(QLabel(f"{language_manager.translate('ui.common.status')}:"), 0, 0)
        layout.addWidget(self.status_indicator, 0, 1)
        
        # Server URL
        self.server_url_display = QLabel(language_manager.translate("ui.common.na"))
        self.server_url_display.setStyleSheet("font-family: monospace;")
        layout.addWidget(QLabel(f"{language_manager.translate('ui.common.url')}:"), 1, 0)
        layout.addWidget(self.server_url_display, 1, 1)
        
        # Uptime
        self.uptime_display = QLabel(language_manager.translate("ui.common.na"))
        layout.addWidget(QLabel(f"{language_manager.translate('ui.server.uptime')}:"), 2, 0)
        layout.addWidget(self.uptime_display, 2, 1)
        
        # Process info
        self.process_info = QLabel(language_manager.translate("ui.common.na"))
        layout.addWidget(QLabel(f"{language_manager.translate('ui.server.process')}:"), 3, 0)
        layout.addWidget(self.process_info, 3, 1)
        
        return group
    
    def _create_controls_section(self) -> QGroupBox:
        """Create the server controls section."""
        group = QGroupBox(language_manager.translate("ui.server.server_controls"))
        layout = QVBoxLayout(group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton(f"▶ {language_manager.translate('ui.server.start_server')}")
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        self.start_btn.clicked.connect(self._start_server)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton(f"⏹ {language_manager.translate('ui.server.stop_server')}")
        self.stop_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; font-weight: bold; padding: 8px; }")
        self.stop_btn.clicked.connect(self._stop_server)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)  # Initially hidden
        button_layout.addWidget(self.stop_btn)
        
        self.restart_btn = QPushButton(f"🔄 {language_manager.translate('ui.server.restart_server')}")
        self.restart_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 8px; }")
        self.restart_btn.clicked.connect(self._restart_server)
        self.restart_btn.setEnabled(False)
        self.restart_btn.setVisible(False)  # Initially hidden
        button_layout.addWidget(self.restart_btn)
        
        layout.addLayout(button_layout)
        
        # Auto-start option
        self.auto_start_cb = QCheckBox(language_manager.translate("ui.server.auto_start_launch"))
        self.auto_start_cb.stateChanged.connect(self._toggle_auto_start)
        layout.addWidget(self.auto_start_cb)
        
        return group
    
    def _create_config_section(self) -> QGroupBox:
        """Create the configuration section."""
        group = QGroupBox(language_manager.translate("ui.server.server_configuration"))
        layout = QGridLayout(group)
        
        # Host configuration
        layout.addWidget(QLabel(f"{language_manager.translate('settings.host')}:"), 0, 0)
        self.host_input = QLineEdit("127.0.0.1")
        self.host_input.setPlaceholderText(language_manager.translate("ui.server.enter_host"))
        layout.addWidget(self.host_input, 0, 1)
        
        # Port configuration
        layout.addWidget(QLabel(f"{language_manager.translate('settings.port')}:"), 1, 0)
        self.port_input = QLineEdit()
        self.port_input.setText("8080")
        self.port_input.setPlaceholderText(language_manager.translate("ui.server.port_placeholder"))
        self.port_input.textChanged.connect(self._validate_port)
        layout.addWidget(self.port_input, 1, 1)
        
        # SSL configuration
        self.ssl_enabled_cb = QCheckBox(language_manager.translate("ui.server.enable_ssl"))
        self.ssl_enabled_cb.stateChanged.connect(self._toggle_ssl_config)
        layout.addWidget(self.ssl_enabled_cb, 2, 0, 1, 2)
        
        # SSL certificate path
        layout.addWidget(QLabel(f"{language_manager.translate('ui.server.ssl_certificate')}:"), 3, 0)
        self.ssl_cert_input = QLineEdit()
        self.ssl_cert_input.setPlaceholderText(language_manager.translate("ui.server.ssl_cert_path"))
        self.ssl_cert_input.setEnabled(False)
        layout.addWidget(self.ssl_cert_input, 3, 1)
        
        # SSL key path
        layout.addWidget(QLabel(f"{language_manager.translate('ui.server.ssl_key')}:"), 4, 0)
        self.ssl_key_input = QLineEdit()
        self.ssl_key_input.setPlaceholderText(language_manager.translate("ui.server.ssl_key_path"))
        self.ssl_key_input.setEnabled(False)
        layout.addWidget(self.ssl_key_input, 4, 1)
        
        # Configuration buttons
        config_button_layout = QHBoxLayout()
        
        self.save_config_btn = QPushButton(language_manager.translate("ui.server.save_config"))
        self.save_config_btn.clicked.connect(self._save_config)
        config_button_layout.addWidget(self.save_config_btn)
        
        self.reload_config_btn = QPushButton(language_manager.translate("ui.server.reload_config"))
        self.reload_config_btn.clicked.connect(self._reload_config)
        config_button_layout.addWidget(self.reload_config_btn)
        
        layout.addLayout(config_button_layout, 5, 0, 1, 2)
        
        return group
    
    def _create_console_panel(self) -> QWidget:
        """Create the console output panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Console header
        console_header = QHBoxLayout()
        
        console_title = QLabel(language_manager.translate("ui.server.server_console"))
        console_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        console_header.addWidget(console_title)
        
        console_header.addStretch()
        
        # Console controls
        self.clear_console_btn = QPushButton(language_manager.translate("ui.server.clear"))
        self.clear_console_btn.clicked.connect(self._clear_console)
        console_header.addWidget(self.clear_console_btn)
        
        self.pause_console_btn = QPushButton(language_manager.translate("ui.server.pause"))
        self.pause_console_btn.setCheckable(True)
        self.pause_console_btn.clicked.connect(self._toggle_console_pause)
        console_header.addWidget(self.pause_console_btn)
        
        layout.addLayout(console_header)
        
        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 10))
        self.console_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
            }
        """)
        layout.addWidget(self.console_output)
        
        # Console status
        self.console_status = QLabel(language_manager.translate("ui.server.console_ready"))
        self.console_status.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(self.console_status)
        
        return panel
    
    def refresh_data(self):
        """Refresh server data (non-blocking)."""
        try:
            # Request data refresh from worker thread
            self._request_data_refresh()
            self.update_status("Server data refresh requested")
            
        except Exception as e:
            self.show_error(f"Failed to refresh server data: {e}")
    
    def _update_server_status(self, status: Dict[str, Any]):
        """Update server status display."""
        try:
            is_running = status.get('is_running', False)
            
            if is_running:
                # Server is running - show green status
                self.status_indicator.setText("●")
                self.status_indicator.setStyleSheet("font-size: 24px; color: green;")
                self.server_url_display.setText(status.get('url', 'N/A'))
                
                # Update uptime
                uptime = status.get('uptime_seconds', 0)
                if uptime:
                    hours = int(uptime // 3600)
                    minutes = int((uptime % 3600) // 60)
                    seconds = int(uptime % 60)
                    self.uptime_display.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                else:
                    self.uptime_display.setText("N/A")
                
                # Update process info
                self.process_info.setText(f"PID: {status.get('pid', 'N/A')}")
                
                # Update button states - server running
                self.start_btn.setEnabled(False)
                self.start_btn.setVisible(False)  # Hide start button
                self.stop_btn.setEnabled(True)
                self.stop_btn.setVisible(True)    # Show stop button
                self.restart_btn.setEnabled(True)
                self.restart_btn.setVisible(True) # Show restart button
                
                # Update button text and styles
                self.stop_btn.setText("⏹ Stop Server")
                self.restart_btn.setText("🔄 Restart Server")
                
            else:
                # Server is stopped - show red status
                self.status_indicator.setText("●")
                self.status_indicator.setStyleSheet("font-size: 24px; color: red;")
                self.server_url_display.setText("N/A")
                self.uptime_display.setText("N/A")
                self.process_info.setText("N/A")
                
                # Update button states - server stopped
                self.start_btn.setEnabled(True)
                self.start_btn.setVisible(True)   # Show start button
                self.stop_btn.setEnabled(False)
                self.stop_btn.setVisible(False)   # Hide stop button
                self.restart_btn.setEnabled(False)
                self.restart_btn.setVisible(False) # Hide restart button
                
                # Update button text and styles
                self.start_btn.setText("▶ Start Server")
            
            self.logger.debug(f"Server status updated: running={is_running}")
            
        except Exception as e:
            self.logger.error(f"Failed to update server status: {e}")
    
    def _update_console_output(self):
        """Update console output with new logs."""
        try:
            # Console output is now updated via server manager signals
            # This method is kept for compatibility but logs are handled
            # through _on_server_manager_log signal handler
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to update console output: {e}")
    
    def _add_console_log(self, log_data: Dict[str, Any]):
        """Add a log entry to the console."""
        try:
            timestamp = log_data.get('timestamp', '')
            level = log_data.get('level', 'INFO')
            message = log_data.get('message', '')
            
            # Format log entry
            log_entry = f"[{timestamp}] {level}: {message}"
            
            # Add to console
            self.console_output.append(log_entry)
            
            # Apply color formatting based on log level
            cursor = self.console_output.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
            
            format = QTextCharFormat()
            if level == 'ERROR':
                format.setForeground(QColor('#f44336'))  # Red
            elif level == 'WARNING':
                format.setForeground(QColor('#ff9800'))  # Orange
            elif level == 'INFO':
                format.setForeground(QColor('#2196f3'))  # Blue
            else:
                format.setForeground(QColor('#ffffff'))  # White
            
            cursor.setCharFormat(format)
            
            # Scroll to bottom
            self.console_output.moveCursor(QTextCursor.End)
            
            # Limit console lines
            if self.console_output.document().blockCount() > self.max_log_lines:
                cursor = self.console_output.textCursor()
                cursor.movePosition(QTextCursor.Start)
                cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
            
        except Exception as e:
            self.logger.error(f"Failed to add console log: {e}")
    
    def _load_config(self, config: Dict[str, Any] = None):
        """Load server configuration."""
        try:
            if config is None:
                # Default config
                config = {
                    "host": "127.0.0.1",
                    "port": 8080,
                    "ssl_enabled": False,
                    "ssl_cert": "",
                    "ssl_key": ""
                }
            
            # Only update UI if values are different to prevent overwriting user input
            current_host = getattr(self, 'host_input', None) and self.host_input.text() or "127.0.0.1"
            current_port_text = getattr(self, 'port_input', None) and self.port_input.text() or "8080"
            try:
                current_port = int(current_port_text) if current_port_text.isdigit() else 8080
            except ValueError:
                current_port = 8080
            current_ssl = getattr(self, 'ssl_enabled_cb', None) and self.ssl_enabled_cb.isChecked() or False
            
            new_host = config.get("host", "127.0.0.1")
            new_port = config.get("port", 8080)
            new_ssl = config.get("ssl_enabled", False)
            
            # Only update if values are different
            if current_host != new_host and hasattr(self, 'host_input'):
                self.host_input.setText(new_host)
            if current_port != new_port and hasattr(self, 'port_input'):
                self.port_input.setText(str(new_port))
            if current_ssl != new_ssl and hasattr(self, 'ssl_enabled_cb'):
                self.ssl_enabled_cb.setChecked(new_ssl)
            
            # Always update SSL cert and key (these are less likely to be edited by user)
            if hasattr(self, 'ssl_cert_input'):
                self.ssl_cert_input.setText(config.get("ssl_cert", ""))
            if hasattr(self, 'ssl_key_input'):
                self.ssl_key_input.setText(config.get("ssl_key", ""))
            
            self.server_config = config
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
    
    def _start_server(self):
        """Start server button handler."""
        try:
            # Get main window and server manager
            main_window = self._get_main_window()
            if not main_window:
                self.show_error(language_manager.translate("ui.common.main_window_not_found"))
                return
            
            # Get current configuration from UI
            config = self._get_current_config()
            
            # Validate port before starting server
            if not self._validate_port_config(config['port']):
                self.show_error(language_manager.translate("ui.server.invalid_port", port=config['port']))
                return
            
            if hasattr(main_window, 'start_server'):
                # Start server with current configuration
                main_window.start_server(config)
                self._add_console_log({
                    'timestamp': self._get_timestamp(),
                    'level': 'INFO',
                    'message': 'Server start requested...'
                })
            else:
                self.show_error(language_manager.translate("ui.common.start_server_method_not_found"))
        except Exception as e:
            self.show_error(f"Error starting server: {e}")
            self.logger.error(f"Error starting server: {e}")
    
    def _stop_server(self):
        """Stop server button handler."""
        try:
            main_window = self._get_main_window()
            if not main_window:
                self.show_error(language_manager.translate("ui.common.main_window_not_found"))
                return
            
            if hasattr(main_window, 'stop_server'):
                main_window.stop_server()
                self._add_console_log({
                    'timestamp': self._get_timestamp(),
                    'level': 'INFO',
                    'message': 'Server stop requested...'
                })
            else:
                self.show_error(language_manager.translate("ui.common.stop_server_method_not_found"))
        except Exception as e:
            self.show_error(f"Error stopping server: {e}")
            self.logger.error(f"Error stopping server: {e}")
    
    def _restart_server(self):
        """Restart server button handler."""
        try:
            main_window = self._get_main_window()
            if not main_window:
                self.show_error(language_manager.translate("ui.common.main_window_not_found"))
                return
            
            if hasattr(main_window, 'restart_server'):
                main_window.restart_server()
                self._add_console_log({
                    'timestamp': self._get_timestamp(),
                    'level': 'INFO',
                    'message': 'Server restart requested...'
                })
            else:
                self.show_error(language_manager.translate("ui.common.restart_server_method_not_found"))
        except Exception as e:
            self.show_error(f"Error restarting server: {e}")
            self.logger.error(f"Error restarting server: {e}")
    
    def _get_main_window(self):
        """Get main window instance safely."""
        try:
            # Try to find main window through parent hierarchy
            widget = self
            while widget:
                if hasattr(widget, 'start_server') and hasattr(widget, 'server_manager'):
                    return widget
                widget = widget.parent()
            return None
        except Exception as e:
            self.logger.error(f"Error getting main window: {e}")
            return None
    
    def _get_current_config(self):
        """Get current server configuration from UI."""
        try:
            # Get port as integer from text input
            port_text = getattr(self, 'port_input', None) and self.port_input.text() or '8080'
            try:
                port = int(port_text) if port_text.isdigit() else 8080
            except ValueError:
                port = 8080
            
            config = {
                'host': getattr(self, 'host_input', None) and self.host_input.text() or '127.0.0.1',
                'port': port,
                'ssl_enabled': getattr(self, 'ssl_enabled_cb', None) and self.ssl_enabled_cb.isChecked() or False,
                'ssl_cert': getattr(self, 'ssl_cert_input', None) and self.ssl_cert_input.text() or '',
                'ssl_key': getattr(self, 'ssl_key_input', None) and self.ssl_key_input.text() or ''
            }
            return config
        except Exception as e:
            self.logger.error(f"Error getting current config: {e}")
            return {
                'host': '127.0.0.1',
                'port': 8080,
                'ssl_enabled': False,
                'ssl_cert': '',
                'ssl_key': ''
            }
    
    def _load_initial_config(self):
        """Load initial server configuration when tab is activated."""
        try:
            # Load config from settings or server manager
            if self.server_manager:
                config = self.server_manager.get_config()
            else:
                # Default config
                config = {
                    "host": "127.0.0.1",
                    "port": 8080,
                    "ssl_enabled": False,
                    "ssl_cert": "",
                    "ssl_key": ""
                }
            
            self._load_config(config)
            self.logger.info("Initial server config loaded")
            
        except Exception as e:
            self.logger.error(f"Error loading initial config: {e}")
    
    def _validate_port(self, text: str):
        """Validate port number input."""
        try:
            # Remove any non-numeric characters
            clean_text = ''.join(filter(str.isdigit, text))
            
            if clean_text != text:
                # If text was modified, update the input
                self.port_input.setText(clean_text)
                return
            
            if clean_text:
                port = int(clean_text)
                if port < 1 or port > 65535:
                    # Invalid port range
                    self.port_input.setStyleSheet("QLineEdit { border: 2px solid red; background-color: #ffe6e6; }")
                    self.port_input.setToolTip(language_manager.translate("ui.server.port_validation_msg"))
                else:
                    # Valid port
                    self.port_input.setStyleSheet("QLineEdit { border: 2px solid green; background-color: #e6ffe6; }")
                    self.port_input.setToolTip(language_manager.translate("ui.server.valid_port_msg"))
            else:
                # Empty input
                self.port_input.setStyleSheet("")
                self.port_input.setToolTip(language_manager.translate("ui.server.enter_port_msg"))
                
        except Exception as e:
            self.logger.error(f"Port validation error: {e}")
            self.port_input.setStyleSheet("QLineEdit { border: 2px solid red; background-color: #ffe6e6; }")
    
    def _validate_port_config(self, port: int) -> bool:
        """Validate port configuration value."""
        try:
            return 1 <= port <= 65535
        except (TypeError, ValueError):
            return False
    
    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def set_server_manager(self, server_manager):
        """Set server manager instance."""
        try:
            self.server_manager = server_manager
            if server_manager:
                # Connect server manager signals
                server_manager.server_status_changed.connect(self._on_server_manager_status_changed)
                server_manager.server_error.connect(self._on_server_manager_error)
                server_manager.log_message.connect(self._on_server_manager_log)
                
                # Set server manager to worker
                if self.worker and hasattr(self.worker, 'set_server_manager'):
                    self.worker.set_server_manager(server_manager)
                
                self.logger.info("Server manager connected to server tab")
            else:
                self.logger.warning("Server manager is None")
        except Exception as e:
            self.logger.error(f"Failed to set server manager: {e}")
    
    def _on_server_manager_status_changed(self, is_running: bool):
        """Handle server manager status change."""
        try:
            if self.server_manager:
                status = self.server_manager.get_status()
                self._update_server_status(status)
                
                # Add console log for status change
                status_text = "started" if is_running else "stopped"
                self._add_console_log({
                    'timestamp': self._get_timestamp(),
                    'level': 'INFO',
                    'message': f"Server {status_text} successfully"
                })
                
                self.logger.info(f"Server status changed: running={is_running}")
        except Exception as e:
            self.logger.error(f"Error handling server status change: {e}")
    
    def _on_server_manager_error(self, error_message: str):
        """Handle server manager error."""
        try:
            self.show_error(f"Server error: {error_message}")
            self._add_console_log({
                'timestamp': self._get_timestamp(),
                'level': 'ERROR',
                'message': f"Server error: {error_message}"
            })
        except Exception as e:
            self.logger.error(f"Error handling server error: {e}")
    
    def _on_server_manager_log(self, log_data: dict):
        """Handle server manager log message."""
        try:
            self._add_console_log(log_data)
        except Exception as e:
            self.logger.error(f"Error handling server log: {e}")
    
    def _toggle_auto_start(self, state):
        """Toggle auto-start option."""
        auto_start = state == Qt.Checked
        self.logger.info(f"Auto-start set to: {auto_start}")
    
    def _toggle_ssl_config(self, state):
        """Toggle SSL configuration inputs."""
        ssl_enabled = state == Qt.Checked
        self.ssl_cert_input.setEnabled(ssl_enabled)
        self.ssl_key_input.setEnabled(ssl_enabled)
    
    def _save_config(self):
        """Save server configuration."""
        try:
            config = {
                'host': self.host_input.text(),
                'port': self.port_input.value(),
                'ssl_enabled': self.ssl_enabled_cb.isChecked(),
                'ssl_cert': self.ssl_cert_input.text(),
                'ssl_key': self.ssl_key_input.text()
            }
            
            # Save configuration (placeholder)
            self.server_config = config
            self.show_success(language_manager.translate("ui.common.configuration_saved"))
            
        except Exception as e:
            self.show_error(f"Failed to save configuration: {e}")
    
    def _reload_config(self):
        """Reload server configuration."""
        try:
            self._load_config()
            self.show_success(language_manager.translate("ui.common.configuration_reloaded"))
        except Exception as e:
            self.show_error(f"Failed to reload configuration: {e}")
    
    def _clear_console(self):
        """Clear console output."""
        self.console_output.clear()
        self.console_status.setText(language_manager.translate("ui.server.console_cleared"))
    
    def _toggle_console_pause(self, checked):
        """Toggle console pause state."""
        if checked:
            self.pause_console_btn.setText(language_manager.translate("ui.server.resume"))
            self.console_status.setText(language_manager.translate("ui.server.console_paused"))
        else:
            self.pause_console_btn.setText(language_manager.translate("ui.server.pause"))
            self.console_status.setText(language_manager.translate("ui.server.console_active"))
    
    def get_tab_data(self) -> Dict[str, Any]:
        """Get server tab data."""
        return {
            **super().get_tab_data(),
            "server_config": self.server_config,
            "console_logs_count": len(self.console_logs),
            "console_paused": self.pause_console_btn.isChecked()
        }
