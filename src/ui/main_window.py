"""
Main window for the API Server Management System.

This module implements the main PyQt5 window with tabbed interface
and server management capabilities according to the AioHTTP + PyQt5
parallel development guide.
"""

import sys
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, 
    QWidget, QStatusBar, QMenuBar, QAction, QMessageBox,
    QSystemTrayIcon, QMenu, QApplication
)
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, Qt, QThread
from PyQt5.QtGui import QIcon, QKeySequence

from ..core.constants import APP_NAME, APP_VERSION
from ..utils.logger import logger
from ..api.server_manager import APIServerManager
from ..core.settings import settings
from ..core.language import language_manager
from .tabs.dashboard_tab import DashboardTab
from .tabs.server_tab import ServerTab
from .tabs.users_tab import UsersTab
from .tabs.api_tab import ApiTab
from .tabs.monitor_tab import MonitorTab
from .tabs.logs_tab import LogsTab
from .tabs.settings_tab import SettingsTab
from .tabs.about_tab import AboutTab


class MainWindow(QMainWindow):
    """
    Main window class for the API Server Management System.
    
    This class implements the main PyQt5 window with tabbed interface,
    server management, and thread-safe communication with the AioHTTP server.
    """
    
    # Signals for thread-safe communication
    server_status_changed = pyqtSignal(dict)
    notification_received = pyqtSignal(str)
    data_received = pyqtSignal(dict)
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        self.logger = logger
        self.server_manager: Optional[APIServerManager] = None
        self.tabs = {}
        self.tray_icon = None
        
        # Initialize UI
        self._init_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_system_tray()
        self._setup_timer()
        
        # Connect signals
        self._connect_signals()
        
        self.logger.info("Main window initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        
        # Config'den window boyutlarını al
        from src.core.settings import settings
        self.setMinimumSize(
            getattr(settings.ui, 'window_min_width', 800),
            getattr(settings.ui, 'window_min_height', 600)
        )
        self.resize(
            getattr(settings.ui, 'window_width', 1200),
            getattr(settings.ui, 'window_height', 800)
        )
        
        # Center window on screen
        self._center_window()
        
        # Create central widget with tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(False)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Add tabs immediately
        self._create_tabs()
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Apply theme
        self._apply_theme()
    
    def _apply_theme(self):
        """Apply theme to the main window."""
        try:
            from src.core.settings import settings
            from src.core.resource_loader import resource_loader
            
            # Get current theme
            current_theme = settings.ui.theme
            if hasattr(current_theme, 'value'):
                theme_name = current_theme.value
            else:
                theme_name = str(current_theme)
            
            # Load theme file
            theme_content = resource_loader.load_style("theme", theme_name)
            if theme_content:
                self.setStyleSheet(theme_content)
                self.logger.info(f"Theme applied: {theme_name}")
            else:
                self.logger.warning(f"Theme file not found: {theme_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to apply theme: {e}")
    
    def reload_configuration(self):
        """Reload configuration and apply changes."""
        try:
            from src.core.config_manager import config_manager
            from src.core.settings import settings
            
            # Reload config
            config = config_manager.load_config()
            settings.update_from_dict(config)
            
            # Apply theme
            self._apply_theme()
            
            self.logger.info("Configuration reloaded")
            
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
    
    def _on_tab_changed(self, index):
        """Handle tab change - log only for now."""
        try:
            # Get current tab name
            current_tab_name = self.tab_widget.tabText(index)
            self.logger.debug(f"Tab changed to: {current_tab_name}")
            
            # For now, just log the change - no cleanup to prevent crashes
            
        except Exception as e:
            self.logger.error(f"Error handling tab change: {e}")
    
    def _cleanup_all_tabs(self):
        """Cleanup all tab threads."""
        try:
            self.logger.info("Cleaning up all tab threads...")
            
            for tab_name, tab in self.tabs.items():
                try:
                    if hasattr(tab, 'cleanup_thread'):
                        tab.cleanup_thread()
                        self.logger.debug(f"Cleaned up thread for tab: {tab_name}")
                except Exception as e:
                    self.logger.error(f"Error cleaning up tab {tab_name}: {e}")
            
            self.logger.info("All tab threads cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error in _cleanup_all_tabs: {e}")
    
    def _create_tabs(self):
        """Create and add all tabs to the tab widget."""
        try:
            self.logger.info("Creating tabs...")
            
            # Dashboard tab
            try:
                self.tabs['dashboard'] = DashboardTab()
                self.tab_widget.addTab(
                    self.tabs['dashboard'], 
                    QIcon("data/resources/icons/tabs/dashboard.svg"),
                    language_manager.translate("navigation.dashboard")
                )
                self.logger.debug("Dashboard tab created")
            except Exception as e:
                self.logger.error(f"Failed to create Dashboard tab: {e}")
            
            # Server tab
            try:
                self.tabs['server'] = ServerTab()
                self.tab_widget.addTab(
                    self.tabs['server'],
                    QIcon("data/resources/icons/tabs/server.svg"),
                    language_manager.translate("navigation.server")
                )
                self.logger.debug("Server tab created")
            except Exception as e:
                self.logger.error(f"Failed to create Server tab: {e}")
            
            # Users tab
            try:
                self.tabs['users'] = UsersTab()
                self.tab_widget.addTab(
                    self.tabs['users'],
                    QIcon("data/resources/icons/tabs/users.svg"),
                    language_manager.translate("navigation.users")
                )
                self.logger.debug("Users tab created")
            except Exception as e:
                self.logger.error(f"Failed to create Users tab: {e}")
            
            # API tab
            try:
                self.tabs['api'] = ApiTab()
                self.tab_widget.addTab(
                    self.tabs['api'],
                    QIcon("data/resources/icons/tabs/api.svg"),
                    language_manager.translate("navigation.api")
                )
                self.logger.debug("API tab created")
            except Exception as e:
                self.logger.error(f"Failed to create API tab: {e}")
            
            # Monitor tab
            try:
                self.tabs['monitor'] = MonitorTab()
                self.tab_widget.addTab(
                    self.tabs['monitor'],
                    QIcon("data/resources/icons/tabs/monitor.svg"),
                    language_manager.translate("navigation.monitor")
                )
                self.logger.debug("Monitor tab created")
            except Exception as e:
                self.logger.error(f"Failed to create Monitor tab: {e}")
            
            # Logs tab
            try:
                self.tabs['logs'] = LogsTab()
                self.tab_widget.addTab(
                    self.tabs['logs'],
                    QIcon("data/resources/icons/tabs/logs.svg"),
                    language_manager.translate("navigation.logs")
                )
                self.logger.debug("Logs tab created")
            except Exception as e:
                self.logger.error(f"Failed to create Logs tab: {e}")
            
            # Settings tab
            try:
                self.tabs['settings'] = SettingsTab()
                self.tab_widget.addTab(
                    self.tabs['settings'],
                    QIcon("data/resources/icons/tabs/settings.svg"),
                    language_manager.translate("navigation.settings")
                )
                self.logger.debug("Settings tab created")
            except Exception as e:
                self.logger.error(f"Failed to create Settings tab: {e}")
            
            # About tab
            try:
                self.tabs['about'] = AboutTab()
                self.tab_widget.addTab(
                    self.tabs['about'],
                    QIcon("data/resources/icons/tabs/about.svg"),
                    language_manager.translate("navigation.about")
                )
                self.logger.debug("About tab created")
            except Exception as e:
                self.logger.error(f"Failed to create About tab: {e}")
            
            self.logger.info("All tabs created successfully")
            
            # Initialize server button states
            self._update_server_actions(False)  # Server starts as stopped
            
        except Exception as e:
            self.logger.error(f"Failed to create tabs: {e}")
            QMessageBox.critical(self, language_manager.translate("messages.error"), f"{language_manager.translate('messages.failed_create_tabs')}: {e}")
    
    def _setup_menu_bar(self):
        """Setup the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu(f"&{language_manager.translate('menu.file')}")
        
        # New action
        new_action = QAction(f"&{language_manager.translate('menu.new')}", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.setStatusTip(language_manager.translate("messages.new_config"))
        new_action.triggered.connect(self._new_configuration)
        file_menu.addAction(new_action)
        
        # Open action
        open_action = QAction(f"&{language_manager.translate('menu.open')}", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip(language_manager.translate("messages.open_config"))
        open_action.triggered.connect(self._open_configuration)
        file_menu.addAction(open_action)
        
        # Save action
        save_action = QAction(f"&{language_manager.translate('menu.save')}", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.setStatusTip(language_manager.translate("messages.save_config"))
        save_action.triggered.connect(self._save_configuration)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction(f"E&{language_manager.translate('menu.exit')}", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip(language_manager.translate("menu.exit"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Server menu
        server_menu = menubar.addMenu(f"&{language_manager.translate('menu.server')}")
        
        # Start server action
        self.start_server_action = QAction(f"&{language_manager.translate('menu.start_server')}", self)
        self.start_server_action.setStatusTip(language_manager.translate("server.start"))
        self.start_server_action.triggered.connect(self._start_server)
        server_menu.addAction(self.start_server_action)
        
        # Stop server action
        self.stop_server_action = QAction(f"&{language_manager.translate('menu.stop_server')}", self)
        self.stop_server_action.setStatusTip(language_manager.translate("server.stop"))
        self.stop_server_action.triggered.connect(self._stop_server)
        self.stop_server_action.setEnabled(False)
        server_menu.addAction(self.stop_server_action)
        
        # Restart server action
        self.restart_server_action = QAction(f"&{language_manager.translate('menu.restart_server')}", self)
        self.restart_server_action.setStatusTip(language_manager.translate("server.restart"))
        self.restart_server_action.triggered.connect(self._restart_server)
        self.restart_server_action.setEnabled(False)
        server_menu.addAction(self.restart_server_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Refresh action
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.setStatusTip("Refresh current view")
        refresh_action.triggered.connect(self._refresh_view)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = self.statusBar()
        
        # Server status label
        self.server_status_label = self.status_bar.addWidget(
            QWidget()
        )  # Placeholder for server status widget
        
        # Connection status label
        self.connection_status_label = self.status_bar.addPermanentWidget(
            QWidget()
        )  # Placeholder for connection status widget
        
        # Update status bar
        self._update_status_bar()
    
    def _setup_system_tray(self):
        """Setup the system tray icon."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon("data/resources/icons/app.ico"))
            
            # Create tray menu
            tray_menu = QMenu()
            
            # Show/Hide action
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            # Server actions
            tray_menu.addSeparator()
            tray_menu.addAction(self.start_server_action)
            tray_menu.addAction(self.stop_server_action)
            tray_menu.addAction(self.restart_server_action)
            
            # Exit action
            tray_menu.addSeparator()
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.close)
            tray_menu.addAction(exit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self._tray_icon_activated)
            self.tray_icon.show()
    
    def _setup_timer(self):
        """Setup the refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_data)
        # Auto refresh interval'i config'den al
        refresh_interval = getattr(settings.ui, 'auto_refresh_interval', 10000)
        self.refresh_timer.start(refresh_interval)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        # Connect server status signals
        self.server_status_changed.connect(self._on_server_status_changed)
        self.notification_received.connect(self._on_notification_received)
        self.data_received.connect(self._on_data_received)
        
        # Connect tab signals
        for tab in self.tabs.values():
            if hasattr(tab, 'data_updated'):
                tab.data_updated.connect(self._on_tab_data_updated)
    
    def _center_window(self):
        """Center the window on the screen."""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
        # Always on top ayarını uygula
        if getattr(settings.ui, 'always_on_top', False):
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
    
    
    def start_server(self, config: dict = None) -> bool:
        """
        Start the API server.
        
        Args:
            config: Server configuration dictionary (optional)
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            if self.server_manager and self.server_manager.is_server_running():
                self.logger.warning("Server is already running")
                return True
            
            # Use provided config or default settings
            if config:
                host = config.get('host', settings.server.host)
                port = config.get('port', settings.server.port)
                ssl_enabled = config.get('ssl_enabled', settings.server.ssl)
                ssl_cert = config.get('ssl_cert', getattr(settings.server, 'ssl_cert', None))
                ssl_key = config.get('ssl_key', getattr(settings.server, 'ssl_key', None))
            else:
                host = settings.server.host
                port = settings.server.port
                ssl_enabled = settings.server.ssl
                ssl_cert = getattr(settings.server, 'ssl_cert', None)
                ssl_key = getattr(settings.server, 'ssl_key', None)
            
            # Create server manager
            self.server_manager = APIServerManager(
                host=host,
                port=port,
                ssl_enabled=ssl_enabled,
                ssl_cert=ssl_cert,
                ssl_key=ssl_key
            )
            
            # Connect signals
            self.server_manager.server_status_changed.connect(self._on_server_status_changed)
            self.server_manager.server_error.connect(self._on_server_error)
            self.server_manager.log_message.connect(self._on_log_message)
            
            # Set server manager to server tab
            if 'server' in self.tabs and hasattr(self.tabs['server'], 'set_server_manager'):
                self.tabs['server'].set_server_manager(self.server_manager)
            
            # Start server
            self.server_manager.start_server()
            
            self.logger.info("Server starting...")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start server: {e}")
            return False
    
    def _on_server_status_changed(self, is_running: bool):
        """Handle server status change signal."""
        try:
            self._update_server_actions(is_running)
            if is_running:
                self.logger.info("Server started successfully")
            else:
                self.logger.info("Server stopped successfully")
        except Exception as e:
            self.logger.error(f"Error handling server status change: {e}")
    
    def _on_server_error(self, error_message: str):
        """Handle server error signal."""
        try:
            self._update_server_actions(False)
            self.logger.error(f"Server error: {error_message}")
            QMessageBox.critical(self, "Server Error", error_message)
        except Exception as e:
            self.logger.error(f"Error handling server error: {e}")
    
    def _on_log_message(self, log_data: dict):
        """Handle log message signal."""
        try:
            # Update console in server tab if available
            if 'server' in self.tabs and self.tabs['server']:
                server_tab = self.tabs['server']
                if hasattr(server_tab, '_add_console_log'):
                    server_tab._add_console_log(log_data)
        except Exception as e:
            self.logger.error(f"Error handling log message: {e}")
    
    def stop_server(self) -> bool:
        """
        Stop the API server.
        
        Returns:
            True if server stopped successfully, False otherwise
        """
        try:
            if not self.server_manager or not self.server_manager.is_server_running():
                self.logger.warning("Server is not running")
                return True
            
            # Stop server
            self.server_manager.stop_server()
            
            self.logger.info("Server stopping...")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to stop server: {e}")
            QMessageBox.critical(self, "Error", f"Failed to stop server: {e}")
            return False
    
    def restart_server(self) -> bool:
        """
        Restart the API server.
        
        Returns:
            True if server restarted successfully, False otherwise
        """
        try:
            if not self.server_manager:
                return self.start_server()
            
            # Restart server
            self.server_manager.restart_server()
            
            self.logger.info("Server restart initiated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restart server: {e}")
            QMessageBox.critical(self, "Error", f"Failed to restart server: {e}")
            return False
    
    def _update_server_actions(self, server_running: bool):
        """Update server action states."""
        try:
            # Update menu actions (if they exist)
            if hasattr(self, 'start_server_action'):
                self.start_server_action.setEnabled(not server_running)
            if hasattr(self, 'stop_server_action'):
                self.stop_server_action.setEnabled(server_running)
            if hasattr(self, 'restart_server_action'):
                self.restart_server_action.setEnabled(server_running)
            
            # Update tab buttons (thread-safe)
            self._update_tab_buttons(server_running)
        except Exception as e:
            self.logger.error(f"Failed to update server actions: {e}")
    
    def _update_tab_buttons(self, server_running: bool):
        """Update server control buttons in all tabs (thread-safe)."""
        try:
            # Update Server Tab buttons
            if 'server' in self.tabs and self.tabs['server']:
                server_tab = self.tabs['server']
                if hasattr(server_tab, 'start_btn'):
                    server_tab.start_btn.setEnabled(not server_running)
                if hasattr(server_tab, 'stop_btn'):
                    server_tab.stop_btn.setEnabled(server_running)
                if hasattr(server_tab, 'restart_btn'):
                    server_tab.restart_btn.setEnabled(server_running)
            
            # Update Dashboard Tab buttons
            if 'dashboard' in self.tabs and self.tabs['dashboard']:
                dashboard_tab = self.tabs['dashboard']
                if hasattr(dashboard_tab, 'start_button'):
                    dashboard_tab.start_button.setEnabled(not server_running)
                if hasattr(dashboard_tab, 'stop_button'):
                    dashboard_tab.stop_button.setEnabled(server_running)
                if hasattr(dashboard_tab, 'restart_button'):
                    dashboard_tab.restart_button.setEnabled(server_running)
                    
        except Exception as e:
            self.logger.error(f"Failed to update tab buttons: {e}")
    
    def _update_status_bar(self):
        """Update the status bar."""
        if self.server_manager and self.server_manager.is_server_running():
            status = self.server_manager.get_status()
            self.status_bar.showMessage(
                f"Server: {status['protocol']}://{status['host']}:{status['port']} - "
                f"Uptime: {status.get('uptime_seconds', 0):.0f}s"
            )
        else:
            self.status_bar.showMessage("Server: Stopped")
    
    def _refresh_data(self):
        """Refresh data from server (non-blocking)."""
        try:
            if self.server_manager and self.server_manager.is_server_running():
                # Get server data (non-blocking)
                server_data = self.server_manager.get_queue_data()
                for data in server_data:
                    self.data_received.emit(data)
                
                # Update status bar (non-blocking)
                self._update_status_bar()
                
                # Request data refresh from tabs (non-blocking)
                # Tabs will handle their own refresh in background threads
                for tab in self.tabs.values():
                    if hasattr(tab, '_request_data_refresh'):
                        tab._request_data_refresh()
                    elif hasattr(tab, 'refresh_data'):
                        # Fallback for tabs that don't use worker threads yet
                        QTimer.singleShot(0, tab.refresh_data)
                        
        except Exception as e:
            self.logger.error(f"Error refreshing data: {e}")
    
    def _on_server_status_changed(self, is_running: bool):
        """Handle server status changes."""
        self._update_server_actions(is_running)
        self._update_status_bar()
    
    def _on_notification_received(self, message: str):
        """Handle notifications from server."""
        self.logger.info(f"Notification: {message}")
        # Show notification in status bar
        from src.core.settings import settings
        timeout = getattr(settings.ui, 'auto_refresh_interval', 5000)
        self.status_bar.showMessage(message, timeout)
    
    def _on_data_received(self, data: Dict[str, Any]):
        """Handle data received from server."""
        # Process data and update relevant tabs
        data_type = data.get('type')
        if data_type == 'metrics':
            if 'monitor' in self.tabs:
                self.tabs['monitor'].update_metrics(data)
        elif data_type == 'log':
            if 'logs' in self.tabs:
                self.tabs['logs'].add_log_entry(data)
    
    def _on_tab_data_updated(self, tab_name: str, data: Any):
        """Handle data updates from tabs."""
        self.logger.debug(f"Tab {tab_name} data updated")
    
    def _tray_icon_activated(self, reason):
        """Handle system tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    # Menu action handlers
    def _new_configuration(self):
        """Create new configuration."""
        QMessageBox.information(self, language_manager.translate("menu.new"), language_manager.translate("messages.new_config"))
    
    def _open_configuration(self):
        """Open configuration file."""
        QMessageBox.information(self, language_manager.translate("menu.open"), language_manager.translate("messages.open_config"))
    
    def _save_configuration(self):
        """Save configuration."""
        QMessageBox.information(self, language_manager.translate("menu.save"), language_manager.translate("messages.save_config"))
    
    def _start_server(self):
        """Start server action handler."""
        self.start_server()
    
    def _stop_server(self):
        """Stop server action handler."""
        self.stop_server()
    
    def _restart_server(self):
        """Restart server action handler."""
        self.restart_server()
    
    def _refresh_view(self):
        """Refresh current view."""
        current_tab = self.tab_widget.currentWidget()
        if hasattr(current_tab, 'refresh_data'):
            current_tab.refresh_data()
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"""
            <h3>{APP_NAME} v{APP_VERSION}</h3>
            <p>A comprehensive API Server Management System with PyQt5 GUI and AioHTTP backend.</p>
            <p>Features:</p>
            <ul>
                <li>Server Management</li>
                <li>User Management</li>
                <li>Real-time Monitoring</li>
                <li>Log Analysis</li>
                <li>Configuration Management</li>
            </ul>
            <p>Built with Python, PyQt5, and AioHTTP.</p>
            """
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            # Stop server if running
            if self.server_manager and self.server_manager.is_server_running():
                reply = QMessageBox.question(
                    self,
                    "Exit Application",
                    "Server is running. Do you want to stop it and exit?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.stop_server()
                else:
                    event.ignore()
                    return
            
            # Hide to tray if available
            if self.tray_icon and self.tray_icon.isVisible():
                self.hide()
                event.ignore()
                return
            
            # Remember window state if enabled
            if getattr(settings.ui, 'remember_window_state', True):
                self._save_window_state()
            
            # Cleanup all tab threads before closing
            self._cleanup_all_tabs()
            
            # Accept close event
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Error in close event: {e}")
            event.accept()
    
    def _save_window_state(self):
        """Save window state to config."""
        try:
            from ...core.config_manager import config_manager
            
            # Mevcut config'i yükle
            config = config_manager.load_config()
            
            # Window state'i güncelle
            config['ui']['window_width'] = self.width()
            config['ui']['window_height'] = self.height()
            config['ui']['window_x'] = self.x()
            config['ui']['window_y'] = self.y()
            
            # Config'i kaydet
            config_manager.save_config(config)
            
        except Exception as e:
            self.logger.error(f"Failed to save window state: {e}")
    
    def _restore_window_state(self):
        """Restore window state from config."""
        try:
            from ...core.config_manager import config_manager
            
            # Config'i yükle
            config = config_manager.load_config()
            ui_config = config.get('ui', {})
            
            # Window state'i geri yükle
            if 'window_x' in ui_config and 'window_y' in ui_config:
                self.move(ui_config['window_x'], ui_config['window_y'])
            
        except Exception as e:
            self.logger.error(f"Failed to restore window state: {e}")
    
    def notify(self, message: str):
        """
        Thread-safe notification method for server callbacks.
        This method is called from the server thread.
        """
        self.notification_received.emit(message)
    
    def get_server_manager(self) -> Optional[APIServerManager]:
        """Get the server manager instance."""
        return self.server_manager
