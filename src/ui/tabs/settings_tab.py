"""
Settings tab for application configuration.

This tab provides settings management for the application including
server configuration, UI preferences, and system settings.
"""

from typing import Dict, Any, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QGroupBox, QLineEdit, QSpinBox,
    QCheckBox, QComboBox, QSlider, QTextEdit, QFileDialog,
    QMessageBox, QTabWidget, QFormLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont

from .base_tab import BaseTab
from ...utils.logger import logger
from ...core.language import language_manager


class SettingsTab(BaseTab):
    """
    Settings tab for application configuration.
    
    This tab provides settings management for server configuration,
    UI preferences, security settings, and system preferences.
    """
    
    def __init__(self):
        """Initialize the settings tab."""
        super().__init__("settings", language_manager.translate("settings.title"))
        
        # Data storage
        self.current_settings = {}
        self.original_settings = {}
        
        # Create settings components
        self._create_settings_components()
        
        # Load current settings
        self._load_settings()
        
        self.logger.info("Settings tab initialized")
    
    def _create_settings_components(self) -> None:
        """Create settings management components."""
        try:
            # Initialize settings components
            self.settings_widgets = {}
            self.config_widgets = {}
            self.ui_widgets = {}
            
            # Create settings widgets
            self._create_settings_widgets()
            
            # Create config widgets
            self._create_config_widgets()
            
            # Create UI widgets
            self._create_ui_widgets()
            
            self.logger.info("Settings components created")
            
        except Exception as e:
            self.logger.error(f"Failed to create settings components: {e}")
    
    def _create_settings_widgets(self) -> None:
        """Create settings widgets."""
        try:
            # General settings
            self.settings_widgets['general'] = {
                'language': 'tr',
                'theme': 'dark',
                'auto_start': False,
                'minimize_to_tray': True,
                'check_updates': True
            }
            
            # Server settings
            self.settings_widgets['server'] = {
                'host': '127.0.0.1',
                'port': 8080,
                'ssl_enabled': False,
                'ssl_cert': '',
                'ssl_key': '',
                'cors_enabled': True,
                'rate_limiting': True
            }
            
            # Security settings
            self.settings_widgets['security'] = {
                'jwt_secret': '',
                'jwt_expiry': 3600,
                'password_min_length': 8,
                'require_uppercase': True,
                'require_numbers': True,
                'require_symbols': False,
                'session_timeout': 1800
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create settings widgets: {e}")
    
    def _create_config_widgets(self) -> None:
        """Create config widgets."""
        try:
            # Config'den ayarları al
            from ...core.config_manager import config_manager
            config = config_manager.load_config()
            
            # Database settings
            self.config_widgets['database'] = {
                'type': 'sqlite',
                'host': config.get('server', {}).get('host', 'localhost'),
                'port': config.get('server', {}).get('port', 8080),
                'name': 'app.db',
                'username': '',
                'password': '',
                'pool_size': 10,
                'timeout': config.get('server', {}).get('timeout', 30)
            }
            
            # Logging settings
            logging_config = config.get('logging', {})
            self.config_widgets['logging'] = {
                'level': logging_config.get('level', 20),
                'max_size': logging_config.get('file_max_size', 10485760),
                'backup_count': logging_config.get('file_backup_count', 5),
                'format': logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                'file_enabled': logging_config.get('file_output', True),
                'console_enabled': logging_config.get('console_output', True)
            }
            
            # Monitoring settings
            monitoring_config = config.get('monitoring', {})
            self.config_widgets['monitoring'] = {
                'enabled': monitoring_config.get('enabled', True),
                'interval': monitoring_config.get('interval', 5),
                'cpu_threshold': monitoring_config.get('alert_thresholds', {}).get('cpu', 80),
                'memory_threshold': monitoring_config.get('alert_thresholds', {}).get('memory', 85),
                'disk_threshold': monitoring_config.get('alert_thresholds', {}).get('disk', 90),
                'alert_email': monitoring_config.get('email_alerts', {}).get('email', ''),
                'alert_sms': ''
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create config widgets: {e}")
    
    def _create_ui_widgets(self) -> None:
        """Create UI widgets."""
        try:
            # Theme settings
            self.ui_widgets['theme'] = {
                'current': 'dark',
                'available': ['dark', 'light', 'blue', 'custom'],
                'custom_colors': {
                    'primary': '#007acc',
                    'secondary': '#2d2d2d',
                    'accent': '#ff6b35',
                    'background': '#1a1a1a',
                    'text': '#ffffff'
                }
            }
            
            # Layout settings
            self.ui_widgets['layout'] = {
                'window_size': [1200, 800],
                'window_position': [100, 100],
                'splitter_sizes': [300, 900],
                'tab_order': ['dashboard', 'server', 'users', 'api', 'monitor', 'logs', 'settings', 'about']
            }
            
            # Display settings
            self.ui_widgets['display'] = {
                'font_family': 'Segoe UI',
                'font_size': 9,
                'icon_size': 24,
                'animation_enabled': True,
                'tooltips_enabled': True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create UI widgets: {e}")
    
    def _create_content_widget(self) -> QWidget:
        """Create the settings content widget."""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Create settings tabs
        settings_tabs = QTabWidget()
        layout.addWidget(settings_tabs)
        
        # Server settings tab
        server_tab = self._create_server_settings_tab()
        settings_tabs.addTab(server_tab, language_manager.translate("settings.server_config"))
        
        # UI settings tab
        ui_tab = self._create_ui_settings_tab()
        settings_tabs.addTab(ui_tab, language_manager.translate("settings.ui_settings"))
        
        # Security settings tab
        security_tab = self._create_security_settings_tab()
        settings_tabs.addTab(security_tab, language_manager.translate("settings.security_settings"))
        
        # System settings tab
        system_tab = self._create_system_settings_tab()
        settings_tabs.addTab(system_tab, language_manager.translate("settings.system_settings"))
        
        # Settings controls
        controls_layout = QHBoxLayout()
        
        self.save_btn = QPushButton(language_manager.translate("settings.save_settings"))
        self.save_btn.setIcon(QIcon("data/resources/icons/actions/save.png"))
        self.save_btn.clicked.connect(self._save_settings)
        controls_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton(language_manager.translate("settings.reset_defaults"))
        self.reset_btn.clicked.connect(self._reset_settings)
        controls_layout.addWidget(self.reset_btn)
        
        self.reload_btn = QPushButton(language_manager.translate("settings.reload_settings"))
        self.reload_btn.clicked.connect(self._reload_settings)
        controls_layout.addWidget(self.reload_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        return content_widget
    
    def _create_server_settings_tab(self) -> QWidget:
        """Create the server settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Server configuration group
        server_group = QGroupBox(language_manager.translate("settings.server_config"))
        server_layout = QFormLayout(server_group)
        
        # Host
        self.host_input = QLineEdit()
        # Config'den default host'u al
        from ...core.config_manager import config_manager
        config = config_manager.load_config()
        default_host = config.get('server', {}).get('host', '127.0.0.1')
        self.host_input.setPlaceholderText(default_host)
        server_layout.addRow(f"{language_manager.translate('settings.host')}:", self.host_input)
        
        # Port
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        # Config'den default port'u al
        default_port = config.get('server', {}).get('port', 8080)
        self.port_input.setValue(default_port)
        server_layout.addRow(f"{language_manager.translate('settings.port')}:", self.port_input)
        
        # SSL settings
        self.ssl_enabled_cb = QCheckBox(language_manager.translate("settings.ssl_enabled"))
        self.ssl_enabled_cb.stateChanged.connect(self._toggle_ssl_settings)
        server_layout.addRow("SSL:", self.ssl_enabled_cb)
        
        # SSL certificate path
        ssl_cert_layout = QHBoxLayout()
        self.ssl_cert_input = QLineEdit()
        self.ssl_cert_input.setPlaceholderText("Path to SSL certificate")
        self.ssl_cert_input.setEnabled(False)
        ssl_cert_layout.addWidget(self.ssl_cert_input)
        
        self.ssl_cert_btn = QPushButton(language_manager.translate("settings.browse"))
        self.ssl_cert_btn.setEnabled(False)
        self.ssl_cert_btn.clicked.connect(self._browse_ssl_cert)
        ssl_cert_layout.addWidget(self.ssl_cert_btn)
        
        server_layout.addRow(f"{language_manager.translate('settings.ssl_cert')}:", ssl_cert_layout)
        
        # SSL key path
        ssl_key_layout = QHBoxLayout()
        self.ssl_key_input = QLineEdit()
        self.ssl_key_input.setPlaceholderText(language_manager.translate("settings.ssl_key"))
        self.ssl_key_input.setEnabled(False)
        ssl_key_layout.addWidget(self.ssl_key_input)
        
        self.ssl_key_btn = QPushButton(language_manager.translate("settings.browse"))
        self.ssl_key_btn.setEnabled(False)
        self.ssl_key_btn.clicked.connect(self._browse_ssl_key)
        ssl_key_layout.addWidget(self.ssl_key_btn)
        
        server_layout.addRow(f"{language_manager.translate('settings.ssl_key')}:", ssl_key_layout)
        
        # Auto-start
        self.auto_start_cb = QCheckBox("Auto-start server on application launch")
        server_layout.addRow("Auto-start:", self.auto_start_cb)
        
        # Max connections
        self.max_connections_input = QSpinBox()
        self.max_connections_input.setRange(1, 10000)
        self.max_connections_input.setValue(1000)
        server_layout.addRow("Max Connections:", self.max_connections_input)
        
        # Timeout
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(1, 300)
        self.timeout_input.setValue(30)
        self.timeout_input.setSuffix(" seconds")
        server_layout.addRow("Timeout:", self.timeout_input)
        
        scroll_layout.addWidget(server_group)
        
        # CORS settings group
        cors_group = QGroupBox("CORS Settings")
        cors_layout = QFormLayout(cors_group)
        
        # Allowed origins
        self.cors_origins_input = QLineEdit()
        # Config'den default CORS origins'i al
        default_origins = ", ".join(config.get('server', {}).get('cors_origins', ["*"]))
        self.cors_origins_input.setPlaceholderText(default_origins)
        cors_layout.addRow("Allowed Origins:", self.cors_origins_input)
        
        # Allowed methods
        self.cors_methods_input = QLineEdit()
        self.cors_methods_input.setPlaceholderText("GET, POST, PUT, DELETE, OPTIONS")
        cors_layout.addRow("Allowed Methods:", self.cors_methods_input)
        
        # Allowed headers
        self.cors_headers_input = QLineEdit()
        self.cors_headers_input.setPlaceholderText("Content-Type, Authorization")
        cors_layout.addRow("Allowed Headers:", self.cors_headers_input)
        
        scroll_layout.addWidget(cors_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        return tab
    
    def _create_ui_settings_tab(self) -> QWidget:
        """Create the UI settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Theme settings group
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QFormLayout(theme_group)
        
        # Theme selection
        self.theme_combo = QComboBox()
        # Config'den mevcut temaları al
        available_themes = ["dark", "light", "blue", "custom"]
        self.theme_combo.addItems(available_themes)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_layout.addRow("Theme:", self.theme_combo)
        
        # Show splash screen
        self.show_splash_cb = QCheckBox("Show splash screen on startup")
        self.show_splash_cb.setChecked(True)
        theme_layout.addRow("Splash Screen:", self.show_splash_cb)
        
        # Splash screen duration
        self.splash_duration_input = QSpinBox()
        self.splash_duration_input.setRange(1, 10)
        self.splash_duration_input.setValue(3)
        self.splash_duration_input.setSuffix(" seconds")
        theme_layout.addRow("Splash Duration:", self.splash_duration_input)
        
        scroll_layout.addWidget(theme_group)
        
        # Window settings group
        window_group = QGroupBox("Window Settings")
        window_layout = QFormLayout(window_group)
        
        # Window size
        size_layout = QHBoxLayout()
        self.window_width_input = QSpinBox()
        self.window_width_input.setRange(800, 2560)
        self.window_width_input.setValue(1400)
        size_layout.addWidget(self.window_width_input)
        size_layout.addWidget(QLabel("x"))
        self.window_height_input = QSpinBox()
        self.window_height_input.setRange(600, 1440)
        self.window_height_input.setValue(900)
        size_layout.addWidget(self.window_height_input)
        window_layout.addRow("Default Size:", size_layout)
        
        # Remember window position
        self.remember_position_cb = QCheckBox("Remember window position")
        self.remember_position_cb.setChecked(True)
        window_layout.addRow("Remember Position:", self.remember_position_cb)
        
        # Always on top
        self.always_on_top_cb = QCheckBox("Always keep window on top")
        window_layout.addRow("Always on Top:", self.always_on_top_cb)
        
        scroll_layout.addWidget(window_group)
        
        # Refresh settings group
        refresh_group = QGroupBox("Refresh Settings")
        refresh_layout = QFormLayout(refresh_group)
        
        # Dashboard refresh rate
        self.dashboard_refresh_input = QSpinBox()
        self.dashboard_refresh_input.setRange(1, 60)
        self.dashboard_refresh_input.setValue(5)
        self.dashboard_refresh_input.setSuffix(" seconds")
        refresh_layout.addRow("Dashboard Refresh:", self.dashboard_refresh_input)
        
        # Monitor refresh rate
        self.monitor_refresh_input = QSpinBox()
        self.monitor_refresh_input.setRange(1, 30)
        self.monitor_refresh_input.setValue(2)
        self.monitor_refresh_input.setSuffix(" seconds")
        refresh_layout.addRow("Monitor Refresh:", self.monitor_refresh_input)
        
        # Logs refresh rate
        self.logs_refresh_input = QSpinBox()
        self.logs_refresh_input.setRange(1, 30)
        self.logs_refresh_input.setValue(3)
        self.logs_refresh_input.setSuffix(" seconds")
        refresh_layout.addRow("Logs Refresh:", self.logs_refresh_input)
        
        scroll_layout.addWidget(refresh_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        return tab
    
    def _create_security_settings_tab(self) -> QWidget:
        """Create the security settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Authentication settings group
        auth_group = QGroupBox("Authentication Settings")
        auth_layout = QFormLayout(auth_group)
        
        # JWT secret
        self.jwt_secret_input = QLineEdit()
        self.jwt_secret_input.setEchoMode(QLineEdit.Password)
        self.jwt_secret_input.setPlaceholderText("Enter JWT secret key")
        auth_layout.addRow("JWT Secret:", self.jwt_secret_input)
        
        # JWT algorithm
        self.jwt_algorithm_combo = QComboBox()
        self.jwt_algorithm_combo.addItems(["HS256", "HS384", "HS512"])
        auth_layout.addRow("JWT Algorithm:", self.jwt_algorithm_combo)
        
        # Access token expiry
        self.access_token_expire_input = QSpinBox()
        self.access_token_expire_input.setRange(1, 1440)
        self.access_token_expire_input.setValue(30)
        self.access_token_expire_input.setSuffix(" minutes")
        auth_layout.addRow("Access Token Expiry:", self.access_token_expire_input)
        
        # Refresh token expiry
        self.refresh_token_expire_input = QSpinBox()
        self.refresh_token_expire_input.setRange(1, 365)
        self.refresh_token_expire_input.setValue(7)
        self.refresh_token_expire_input.setSuffix(" days")
        auth_layout.addRow("Refresh Token Expiry:", self.refresh_token_expire_input)
        
        scroll_layout.addWidget(auth_group)
        
        # Password settings group
        password_group = QGroupBox("Password Settings")
        password_layout = QFormLayout(password_group)
        
        # Password hash rounds
        self.password_hash_rounds_input = QSpinBox()
        self.password_hash_rounds_input.setRange(4, 20)
        self.password_hash_rounds_input.setValue(12)
        password_layout.addRow("Hash Rounds:", self.password_hash_rounds_input)
        
        # Minimum password length
        self.min_password_length_input = QSpinBox()
        self.min_password_length_input.setRange(6, 32)
        self.min_password_length_input.setValue(8)
        password_layout.addRow("Min Length:", self.min_password_length_input)
        
        # Require special characters
        self.require_special_chars_cb = QCheckBox("Require special characters")
        password_layout.addRow("Special Chars:", self.require_special_chars_cb)
        
        scroll_layout.addWidget(password_group)
        
        # Rate limiting group
        rate_limit_group = QGroupBox("Rate Limiting")
        rate_limit_layout = QFormLayout(rate_limit_group)
        
        # Rate limit per minute
        self.rate_limit_input = QSpinBox()
        self.rate_limit_input.setRange(0, 10000)
        self.rate_limit_input.setValue(100)
        self.rate_limit_input.setSuffix(" requests/minute")
        rate_limit_layout.addRow("Rate Limit:", self.rate_limit_input)
        
        # Enable rate limiting
        self.rate_limit_enabled_cb = QCheckBox("Enable rate limiting")
        self.rate_limit_enabled_cb.setChecked(True)
        rate_limit_layout.addRow("Enabled:", self.rate_limit_enabled_cb)
        
        scroll_layout.addWidget(rate_limit_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        return tab
    
    def _create_system_settings_tab(self) -> QWidget:
        """Create the system settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Database settings group
        db_group = QGroupBox("Database Settings")
        db_layout = QFormLayout(db_group)
        
        # Database path
        db_path_layout = QHBoxLayout()
        self.db_path_input = QLineEdit()
        self.db_path_input.setPlaceholderText("data/app.db")
        db_path_layout.addWidget(self.db_path_input)
        
        self.db_path_btn = QPushButton("Browse")
        self.db_path_btn.clicked.connect(self._browse_db_path)
        db_path_layout.addWidget(self.db_path_btn)
        
        db_layout.addRow("Database Path:", db_path_layout)
        
        # Auto-backup
        self.auto_backup_cb = QCheckBox("Enable automatic database backup")
        self.auto_backup_cb.setChecked(True)
        db_layout.addRow("Auto-backup:", self.auto_backup_cb)
        
        # Backup interval
        self.backup_interval_input = QSpinBox()
        self.backup_interval_input.setRange(1, 168)
        self.backup_interval_input.setValue(24)
        self.backup_interval_input.setSuffix(" hours")
        db_layout.addRow("Backup Interval:", self.backup_interval_input)
        
        scroll_layout.addWidget(db_group)
        
        # Logging settings group
        logging_group = QGroupBox("Logging Settings")
        logging_layout = QFormLayout(logging_group)
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")
        logging_layout.addRow("Log Level:", self.log_level_combo)
        
        # Log directory
        log_dir_layout = QHBoxLayout()
        self.log_dir_input = QLineEdit()
        self.log_dir_input.setPlaceholderText("data/logs")
        log_dir_layout.addWidget(self.log_dir_input)
        
        self.log_dir_btn = QPushButton("Browse")
        self.log_dir_btn.clicked.connect(self._browse_log_dir)
        log_dir_layout.addWidget(self.log_dir_btn)
        
        logging_layout.addRow("Log Directory:", log_dir_layout)
        
        # Max log file size
        self.max_log_size_input = QSpinBox()
        self.max_log_size_input.setRange(1, 1000)
        self.max_log_size_input.setValue(10)
        self.max_log_size_input.setSuffix(" MB")
        logging_layout.addRow("Max Log Size:", self.max_log_size_input)
        
        # Log backup count
        self.log_backup_count_input = QSpinBox()
        self.log_backup_count_input.setRange(1, 50)
        self.log_backup_count_input.setValue(5)
        logging_layout.addRow("Log Backup Count:", self.log_backup_count_input)
        
        scroll_layout.addWidget(logging_group)
        
        # System settings group
        system_group = QGroupBox("System Settings")
        system_layout = QFormLayout(system_group)
        
        # Language
        self.language_combo = QComboBox()
        # Config'den mevcut dilleri al
        available_languages = ["en", "tr", "de", "fr"]
        self.language_combo.addItems(available_languages)
        system_layout.addRow("Language:", self.language_combo)
        
        # Debug mode
        self.debug_mode_cb = QCheckBox("Enable debug mode")
        system_layout.addRow("Debug Mode:", self.debug_mode_cb)
        
        # Auto-update
        self.auto_update_cb = QCheckBox("Check for updates automatically")
        self.auto_update_cb.setChecked(True)
        system_layout.addRow("Auto-update:", self.auto_update_cb)
        
        scroll_layout.addWidget(system_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        return tab
    
    def _load_settings(self):
        """Load current settings from configuration."""
        try:
            # Load settings from config manager
            from ...core.config_manager import config_manager
            from ...core.settings import settings
            
            # Config dosyasından ayarları yükle
            config = config_manager.load_config()
            
            # Server settings
            server_config = config.get("server", {})
            self.host_input.setText(server_config.get("host", "127.0.0.1"))
            self.port_input.setValue(server_config.get("port", 8080))
            self.ssl_enabled_cb.setChecked(server_config.get("ssl", False))
            self.auto_start_cb.setChecked(server_config.get("auto_start", False))
            self.max_connections_input.setValue(server_config.get("max_connections", 1000))
            self.timeout_input.setValue(server_config.get("timeout", 30))
            
            # CORS settings
            self.cors_origins_input.setText(", ".join(server_config.get("cors_origins", ["*"])))
            self.cors_methods_input.setText(", ".join(server_config.get("cors_methods", ["GET", "POST", "PUT", "DELETE", "OPTIONS"])))
            self.cors_headers_input.setText(", ".join(server_config.get("cors_headers", ["Content-Type", "Authorization"])))
            
            # UI settings
            ui_config = config.get("ui", {})
            current_theme = ui_config.get("theme", "dark")
            # Theme enum'u string'e çevir
            if hasattr(current_theme, 'value'):
                current_theme = current_theme.value
            else:
                current_theme = str(current_theme)
            self.theme_combo.setCurrentText(current_theme)
            self.show_splash_cb.setChecked(ui_config.get("show_splash_screen", True))
            self.splash_duration_input.setValue(ui_config.get("splash_screen_duration", 3000) // 1000)
            self.window_width_input.setValue(ui_config.get("window_width", 1200))
            self.window_height_input.setValue(ui_config.get("window_height", 800))
            self.remember_position_cb.setChecked(ui_config.get("remember_window_state", True))
            self.always_on_top_cb.setChecked(ui_config.get("always_on_top", False))
            
            # Refresh settings
            self.dashboard_refresh_input.setValue(ui_config.get("auto_refresh_interval", 5000) // 1000)
            self.monitor_refresh_input.setValue(2)
            self.logs_refresh_input.setValue(3)
            
            # Security settings
            security_config = config.get("security", {})
            self.jwt_secret_input.setText(security_config.get("jwt_secret_key", "supersecretkey"))
            self.jwt_algorithm_combo.setCurrentText(security_config.get("jwt_algorithm", "HS256"))
            self.access_token_expire_input.setValue(security_config.get("jwt_access_token_expire_minutes", 30))
            self.refresh_token_expire_input.setValue(security_config.get("jwt_refresh_token_expire_days", 7))
            self.password_hash_rounds_input.setValue(security_config.get("bcrypt_rounds", 12))
            self.min_password_length_input.setValue(security_config.get("password_min_length", 8))
            self.require_special_chars_cb.setChecked(security_config.get("password_require_special_chars", True))
            
            # Rate limiting settings
            rate_limit_config = config.get("rate_limiting", {})
            self.rate_limit_input.setValue(rate_limit_config.get("requests_per_minute", 100))
            self.rate_limit_enabled_cb.setChecked(rate_limit_config.get("enabled", True))
            
            # System settings
            self.db_path_input.setText(config.get("database", "data/app.db"))
            backup_config = config.get("backup", {})
            self.auto_backup_cb.setChecked(backup_config.get("enabled", True))
            self.backup_interval_input.setValue(backup_config.get("interval_hours", 24))
            
            logging_config = config.get("logging", {})
            log_level = logging_config.get("level", 20)  # INFO level
            log_level_names = {10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR", 50: "CRITICAL"}
            self.log_level_combo.setCurrentText(log_level_names.get(log_level, "INFO"))
            self.log_dir_input.setText("data/logs")
            self.max_log_size_input.setValue(logging_config.get("file_max_size", 10485760) // 1048576)  # MB
            self.log_backup_count_input.setValue(logging_config.get("file_backup_count", 5))
            
            self.language_combo.setCurrentText(ui_config.get("language", "tr"))
            app_config = config.get("app", {})
            self.debug_mode_cb.setChecked(app_config.get("debug", False))
            self.auto_update_cb.setChecked(True)
            
            # Store original settings for reset functionality
            self._store_current_settings()
            self.original_settings = self.current_settings.copy()
            
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
    
    def _store_current_settings(self):
        """Store current settings in memory."""
        try:
            self.current_settings = {
                # Server settings
                "server": {
                    "host": self.host_input.text(),
                    "port": self.port_input.value(),
                    "ssl": self.ssl_enabled_cb.isChecked(),
                    "ssl_cert_path": self.ssl_cert_input.text(),
                    "ssl_key_path": self.ssl_key_input.text(),
                    "auto_start": self.auto_start_cb.isChecked(),
                    "max_connections": self.max_connections_input.value(),
                    "timeout": self.timeout_input.value(),
                    "cors_origins": [x.strip() for x in self.cors_origins_input.text().split(",") if x.strip()],
                    "cors_methods": [x.strip() for x in self.cors_methods_input.text().split(",") if x.strip()],
                    "cors_headers": [x.strip() for x in self.cors_headers_input.text().split(",") if x.strip()]
                },
                
                # UI settings
                "ui": {
                    "theme": self.theme_combo.currentText(),
                    "language": self.language_combo.currentText(),
                    "show_splash_screen": self.show_splash_cb.isChecked(),
                    "splash_screen_duration": self.splash_duration_input.value() * 1000,  # Convert to ms
                    "window_width": self.window_width_input.value(),
                    "window_height": self.window_height_input.value(),
                    "remember_window_state": self.remember_position_cb.isChecked(),
                    "always_on_top": self.always_on_top_cb.isChecked(),
                    "auto_refresh_interval": self.dashboard_refresh_input.value() * 1000  # Convert to ms
                },
                
                # Security settings
                "security": {
                    "jwt_secret_key": self.jwt_secret_input.text(),
                    "jwt_algorithm": self.jwt_algorithm_combo.currentText(),
                    "jwt_access_token_expire_minutes": self.access_token_expire_input.value(),
                    "jwt_refresh_token_expire_days": self.refresh_token_expire_input.value(),
                    "bcrypt_rounds": self.password_hash_rounds_input.value(),
                    "password_min_length": self.min_password_length_input.value(),
                    "password_require_special_chars": self.require_special_chars_cb.isChecked()
                },
                
                # Rate limiting settings
                "rate_limiting": {
                    "enabled": self.rate_limit_enabled_cb.isChecked(),
                    "requests_per_minute": self.rate_limit_input.value()
                },
                
                # Database settings
                "database": self.db_path_input.text(),
                
                # Backup settings
                "backup": {
                    "enabled": self.auto_backup_cb.isChecked(),
                    "interval_hours": self.backup_interval_input.value()
                },
                
                # Logging settings
                "logging": {
                    "level": {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}.get(self.log_level_combo.currentText(), 20),
                    "file_max_size": self.max_log_size_input.value() * 1048576,  # Convert MB to bytes
                    "file_backup_count": self.log_backup_count_input.value()
                },
                
                # App settings
                "app": {
                    "debug": self.debug_mode_cb.isChecked()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to store current settings: {e}")
    
    def _on_theme_changed(self, theme_name: str):
        """Handle theme change."""
        try:
            from ...core.settings import settings
            from ...core.config_manager import config_manager
            
            # Update settings
            from ...core.constants import ThemeType
            try:
                settings.ui.theme = ThemeType(theme_name)
            except ValueError:
                settings.ui.theme = ThemeType.DARK  # Fallback to dark theme
            
            # Save to config file
            config = config_manager.load_config()
            config['ui']['theme'] = theme_name
            config_manager.save_config(config)
            
            # Apply theme immediately to main window
            self._apply_theme()
            
            # Notify main window to reload configuration
            try:
                from PyQt5.QtWidgets import QApplication
                main_window = QApplication.activeWindow()
                if hasattr(main_window, 'reload_configuration'):
                    main_window.reload_configuration()
            except Exception as e:
                self.logger.warning(f"Could not notify main window: {e}")
            
            self.show_success(f"Theme changed to: {theme_name}")
            
        except Exception as e:
            self.show_error(f"Failed to change theme: {e}")
            self.logger.error(f"Theme change error: {e}")
    
    def _apply_theme(self):
        """Apply the current theme."""
        try:
            from ...core.settings import settings
            from PyQt5.QtWidgets import QApplication
            from pathlib import Path
            
            # Tema değerini string olarak al
            theme = settings.ui.theme.value if hasattr(settings.ui.theme, 'value') else str(settings.ui.theme)
            theme_file = Path(f"data/resources/styles/themes/{theme}.qss")
            
            if theme_file.exists():
                with open(theme_file, 'r', encoding='utf-8') as f:
                    style = f.read()
                
                # Apply to entire application
                QApplication.instance().setStyleSheet(style)
                self.logger.info(f"Theme applied: {theme}")
            else:
                self.logger.warning(f"Theme file not found: {theme_file}")
                
        except Exception as e:
            self.logger.error(f"Failed to apply theme: {e}")
    
    def _save_settings(self):
        """Save current settings."""
        try:
            # Store current settings
            self._store_current_settings()
            
            # Save to configuration file via ConfigManager
            from ...core.config_manager import config_manager
            from ...core.settings import settings
            
            # Settings'i güncelle
            settings.update_from_dict(self.current_settings)
            
            # Config dosyasına kaydet
            config_manager.save_config(self.current_settings)
            
            self.show_success("Settings saved successfully")
            self.logger.info("Settings saved to config file")
            
        except Exception as e:
            self.show_error(f"Failed to save settings: {e}")
            self.logger.error(f"Settings save error: {e}")
    
    def _reset_settings(self):
        """Reset settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Reset to original settings
                self._load_settings()
                self.show_success("Settings reset to defaults")
                
            except Exception as e:
                self.show_error(f"Failed to reset settings: {e}")
    
    def _reload_settings(self):
        """Reload settings from configuration file."""
        try:
            self._load_settings()
            self.show_success("Settings reloaded from file")
            
        except Exception as e:
            self.show_error(f"Failed to reload settings: {e}")
    
    def _toggle_ssl_settings(self, state):
        """Toggle SSL settings inputs."""
        ssl_enabled = state == Qt.Checked
        self.ssl_cert_input.setEnabled(ssl_enabled)
        self.ssl_cert_btn.setEnabled(ssl_enabled)
        self.ssl_key_input.setEnabled(ssl_enabled)
        self.ssl_key_btn.setEnabled(ssl_enabled)
    
    def _browse_ssl_cert(self):
        """Browse for SSL certificate file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select SSL Certificate",
            "",
            "Certificate Files (*.crt *.pem);;All Files (*)"
        )
        
        if filename:
            self.ssl_cert_input.setText(filename)
    
    def _browse_ssl_key(self):
        """Browse for SSL key file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select SSL Private Key",
            "",
            "Key Files (*.key *.pem);;All Files (*)"
        )
        
        if filename:
            self.ssl_key_input.setText(filename)
    
    def _browse_db_path(self):
        """Browse for database file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Select Database File",
            "data/app.db",
            "Database Files (*.db *.sqlite);;All Files (*)"
        )
        
        if filename:
            self.db_path_input.setText(filename)
    
    def _browse_log_dir(self):
        """Browse for log directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Log Directory",
            "data/logs"
        )
        
        if directory:
            self.log_dir_input.setText(directory)
    
    def get_tab_data(self) -> Dict[str, Any]:
        """Get settings tab data."""
        return {
            **super().get_tab_data(),
            "current_settings": self.current_settings,
            "settings_changed": self.current_settings != self.original_settings
        }
