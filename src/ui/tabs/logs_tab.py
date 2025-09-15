"""
Logs tab for log viewing and analysis.

This tab provides log viewing, filtering, and analysis capabilities.
"""

from typing import Dict, Any, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QGroupBox, QLineEdit,
    QComboBox, QCheckBox, QDateEdit, QSpinBox, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QTextCursor, QIcon
from PyQt5.QtGui import QFont, QTextCharFormat, QColor

from .base_tab import BaseTab, BaseTabWorker
from ...utils.logger import logger
from ...core.language import language_manager


class LogsWorker(BaseTabWorker):
    """
    Logs worker that runs in a separate thread.
    """
    
    def __init__(self):
        super().__init__("logs")
    
    def _do_refresh_data(self):
        """Refresh logs data in background thread."""
        try:
            if not self.running:
                return
            
            # Get recent log entries
            self._get_recent_logs()
            
        except Exception as e:
            self.logger.error(f"Error refreshing logs data: {e}")
            self.error_occurred.emit(str(e))
    
    def _get_recent_logs(self):
        """Get recent log entries."""
        try:
            # Simulate getting recent logs
            log_data = {
                "recent_logs": [],
                "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "total_entries": 0
            }
            
            self.data_ready.emit(log_data)
            
        except Exception as e:
            self.logger.error(f"Error getting recent logs: {e}")
            self.error_occurred.emit(str(e))


class LogsTab(BaseTab):
    """
    Logs tab for log viewing and analysis.
    
    This tab provides functionality for viewing, filtering, and analyzing
    system logs and API logs.
    """
    
    def __init__(self):
        """Initialize the logs tab."""
        super().__init__("logs", "Log Viewer")
        
        # Data storage
        self.log_entries = []
        self.filtered_entries = []
        self.log_filters = {}
        
        # Create log components
        self._create_log_components()
        
        # Set refresh interval
        self.set_refresh_interval(3000)  # 3 seconds
        
        # Initialize worker
        self._init_logs_worker()
        
        self.logger.info("Logs tab initialized")
    
    def _init_logs_worker(self):
        """Initialize logs-specific worker."""
        try:
            # Use base class lazy loading
            self._ensure_worker_thread()
            
            # Create new logs worker if not exists
            if not self.worker:
                self.worker = LogsWorker()
                
                # Connect signals
                self.worker.data_ready.connect(self._on_data_ready)
                self.worker.error_occurred.connect(self._on_error_occurred)
                
                # Move worker to thread
                self.worker.moveToThread(self.worker_thread)
            
            # Start worker
            self.worker_thread.started.connect(self.worker.start_worker)
            self.worker_thread.start()
            
            self.logger.info("Logs worker initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize logs worker: {e}")
    
    def _create_log_components(self) -> None:
        """Create log management components."""
        try:
            # Initialize log components
            self.log_widgets = {}
            self.filter_widgets = {}
            self.viewer_widgets = {}
            
            # Create log widgets
            self._create_log_widgets()
            
            # Create filter widgets
            self._create_filter_widgets()
            
            # Create viewer widgets
            self._create_viewer_widgets()
            
            self.logger.info("Log components created")
            
        except Exception as e:
            self.logger.error(f"Failed to create log components: {e}")
    
    def _create_log_widgets(self) -> None:
        """Create log widgets."""
        try:
            # Log types
            self.log_widgets['types'] = {
                'app': 'Uygulama Logları',
                'api': 'API Logları',
                'error': 'Hata Logları',
                'security': 'Güvenlik Logları',
                'system': 'Sistem Logları'
            }
            
            # Log levels
            self.log_widgets['levels'] = {
                'DEBUG': {'color': '#6c757d', 'priority': 0},
                'INFO': {'color': '#17a2b8', 'priority': 1},
                'WARNING': {'color': '#ffc107', 'priority': 2},
                'ERROR': {'color': '#dc3545', 'priority': 3},
                'CRITICAL': {'color': '#6f42c1', 'priority': 4}
            }
            
            # Log actions
            self.log_widgets['actions'] = {
                'refresh': {'enabled': True, 'text': 'Yenile'},
                'clear': {'enabled': True, 'text': 'Temizle'},
                'export': {'enabled': True, 'text': 'Dışa Aktar'},
                'search': {'enabled': True, 'text': 'Ara'}
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create log widgets: {e}")
    
    def _create_filter_widgets(self) -> None:
        """Create filter widgets."""
        try:
            # Date filters
            self.filter_widgets['date'] = {
                'start_date': None,
                'end_date': None,
                'date_range': 'today'
            }
            
            # Level filters
            self.filter_widgets['level'] = {
                'selected_levels': ['INFO', 'WARNING', 'ERROR'],
                'min_level': 'INFO'
            }
            
            # Module filters
            self.filter_widgets['module'] = {
                'selected_modules': [],
                'exclude_modules': []
            }
            
            # Text filters
            self.filter_widgets['text'] = {
                'search_text': '',
                'case_sensitive': False,
                'regex_enabled': False
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create filter widgets: {e}")
    
    def _create_viewer_widgets(self) -> None:
        """Create viewer widgets."""
        try:
            # Log viewer settings
            self.viewer_widgets['settings'] = {
                'auto_scroll': True,
                'word_wrap': True,
                'show_timestamps': True,
                'show_levels': True,
                'max_lines': 10000
            }
            
            # Display options
            self.viewer_widgets['display'] = {
                'font_family': 'Consolas',
                'font_size': 10,
                'line_height': 1.2,
                'color_scheme': 'dark'
            }
            
            # Export options
            self.viewer_widgets['export'] = {
                'format': 'txt',
                'include_metadata': True,
                'filtered_only': True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create viewer widgets: {e}")
    
    def _create_content_widget(self) -> QWidget:
        """Create the logs content widget."""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Filters and controls
        left_panel = self._create_filters_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Log viewer
        right_panel = self._create_log_viewer_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions (30% filters, 70% logs)
        splitter.setSizes([300, 700])
        
        return content_widget
    
    def _create_filters_panel(self) -> QWidget:
        """Create the filters and controls panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Log type selection
        type_group = self._create_type_selection()
        layout.addWidget(type_group)
        
        # Time filters
        time_group = self._create_time_filters()
        layout.addWidget(time_group)
        
        # Level filters
        level_group = self._create_level_filters()
        layout.addWidget(level_group)
        
        # Text filters
        text_group = self._create_text_filters()
        layout.addWidget(text_group)
        
        # Control buttons
        controls_group = self._create_controls()
        layout.addWidget(controls_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return panel
    
    def _create_type_selection(self) -> QGroupBox:
        """Create the log type selection group."""
        group = QGroupBox("Log Type")
        layout = QVBoxLayout(group)
        
        self.log_type_combo = QComboBox()
        self.log_type_combo.addItems(["All Logs", "System Logs", "API Logs", "Error Logs", "Security Logs"])
        self.log_type_combo.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.log_type_combo)
        
        return group
    
    def _create_time_filters(self) -> QGroupBox:
        """Create the time filters group."""
        group = QGroupBox("Time Range")
        layout = QGridLayout(group)
        
        # From date
        layout.addWidget(QLabel("From:"), 0, 0)
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate())
        self.from_date.setCalendarPopup(True)
        self.from_date.dateChanged.connect(self._apply_filters)
        layout.addWidget(self.from_date, 0, 1)
        
        # To date
        layout.addWidget(QLabel("To:"), 1, 0)
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.dateChanged.connect(self._apply_filters)
        layout.addWidget(self.to_date, 1, 1)
        
        # Quick time ranges
        quick_layout = QHBoxLayout()
        
        self.last_hour_btn = QPushButton("Last Hour")
        self.last_hour_btn.clicked.connect(self._set_last_hour)
        quick_layout.addWidget(self.last_hour_btn)
        
        self.last_day_btn = QPushButton("Last Day")
        self.last_day_btn.clicked.connect(self._set_last_day)
        quick_layout.addWidget(self.last_day_btn)
        
        layout.addLayout(quick_layout, 2, 0, 1, 2)
        
        return group
    
    def _create_level_filters(self) -> QGroupBox:
        """Create the log level filters group."""
        group = QGroupBox("Log Levels")
        layout = QVBoxLayout(group)
        
        self.debug_cb = QCheckBox("DEBUG")
        self.debug_cb.setChecked(True)
        self.debug_cb.stateChanged.connect(self._apply_filters)
        layout.addWidget(self.debug_cb)
        
        self.info_cb = QCheckBox("INFO")
        self.info_cb.setChecked(True)
        self.info_cb.stateChanged.connect(self._apply_filters)
        layout.addWidget(self.info_cb)
        
        self.warning_cb = QCheckBox("WARNING")
        self.warning_cb.setChecked(True)
        self.warning_cb.stateChanged.connect(self._apply_filters)
        layout.addWidget(self.warning_cb)
        
        self.error_cb = QCheckBox("ERROR")
        self.error_cb.setChecked(True)
        self.error_cb.stateChanged.connect(self._apply_filters)
        layout.addWidget(self.error_cb)
        
        self.critical_cb = QCheckBox("CRITICAL")
        self.critical_cb.setChecked(True)
        self.critical_cb.stateChanged.connect(self._apply_filters)
        layout.addWidget(self.critical_cb)
        
        return group
    
    def _create_text_filters(self) -> QGroupBox:
        """Create the text filters group."""
        group = QGroupBox("Text Filters")
        layout = QVBoxLayout(group)
        
        # Search text
        layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search text...")
        self.search_input.textChanged.connect(self._apply_filters)
        layout.addWidget(self.search_input)
        
        # Module filter
        layout.addWidget(QLabel("Module:"))
        self.module_combo = QComboBox()
        self.module_combo.addItems(["All Modules", "server", "auth", "api", "database", "ui"])
        self.module_combo.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.module_combo)
        
        # User filter
        layout.addWidget(QLabel("User:"))
        self.user_combo = QComboBox()
        self.user_combo.addItems(["All Users", "admin", "user1", "user2"])
        self.user_combo.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.user_combo)
        
        return group
    
    def _create_controls(self) -> QGroupBox:
        """Create the control buttons group."""
        group = QGroupBox("Controls")
        layout = QVBoxLayout(group)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setIcon(QIcon("data/resources/icons/actions/refresh.png"))
        self.refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(self.refresh_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear Logs")
        self.clear_btn.clicked.connect(self._clear_logs)
        layout.addWidget(self.clear_btn)
        
        # Export button
        self.export_btn = QPushButton("Export Logs")
        self.export_btn.clicked.connect(self._export_logs)
        layout.addWidget(self.export_btn)
        
        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        layout.addWidget(self.auto_scroll_cb)
        
        return group
    
    def _create_log_viewer_panel(self) -> QWidget:
        """Create the log viewer panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Log viewer header
        header_layout = QHBoxLayout()
        
        self.log_count_label = QLabel("0 entries")
        self.log_count_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.log_count_label)
        
        header_layout.addStretch()
        
        # Log level indicators
        self.level_indicators = {}
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            indicator = QLabel("●")
            indicator.setProperty("class", level.lower())
            indicator.setStyleSheet(f"font-size: 16px;")
            indicator.setToolTip(f"{level} logs")
            header_layout.addWidget(indicator)
            self.level_indicators[level] = indicator
        
        layout.addLayout(header_layout)
        
        # Log viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setFont(QFont("Consolas", 9))
        self.log_viewer.setProperty("class", "console")
        layout.addWidget(self.log_viewer)
        
        return panel
    
    def refresh_data(self):
        """Refresh log data."""
        try:
            # Load logs from service (placeholder)
            self._load_logs()
            
            # Apply current filters
            self._apply_filters()
            
            self.update_status("Log data refreshed")
            
        except Exception as e:
            self.show_error(f"Failed to refresh log data: {e}")
    
    def _load_logs(self):
        """Load logs from the log service."""
        try:
            # Placeholder data - in real implementation, this would come from LogService
            placeholder_logs = [
                {
                    "timestamp": "2024-01-15 10:30:15",
                    "level": "INFO",
                    "module": "server",
                    "message": "Server started successfully on port 8080",
                    "user": "admin"
                },
                {
                    "timestamp": "2024-01-15 10:30:20",
                    "level": "DEBUG",
                    "module": "auth",
                    "message": "User authentication successful",
                    "user": "user1"
                },
                {
                    "timestamp": "2024-01-15 10:30:25",
                    "level": "WARNING",
                    "module": "api",
                    "message": "Rate limit exceeded for IP 192.168.1.100",
                    "user": None
                },
                {
                    "timestamp": "2024-01-15 10:30:30",
                    "level": "ERROR",
                    "module": "database",
                    "message": "Database connection timeout",
                    "user": "admin"
                },
                {
                    "timestamp": "2024-01-15 10:30:35",
                    "level": "INFO",
                    "module": "api",
                    "message": "API request processed successfully",
                    "user": "user2"
                }
            ]
            
            self.log_entries = placeholder_logs
            
        except Exception as e:
            self.logger.error(f"Failed to load logs: {e}")
    
    def _apply_filters(self):
        """Apply current filters to log entries."""
        try:
            filtered_entries = []
            
            for entry in self.log_entries:
                # Check log type
                log_type = self.log_type_combo.currentText()
                if log_type != "All Logs":
                    if log_type == "System Logs" and entry.get("module") not in ["server", "database"]:
                        continue
                    elif log_type == "API Logs" and entry.get("module") != "api":
                        continue
                    elif log_type == "Error Logs" and entry.get("level") not in ["ERROR", "CRITICAL"]:
                        continue
                    elif log_type == "Security Logs" and entry.get("module") != "auth":
                        continue
                
                # Check log level
                level = entry.get("level", "")
                if level == "DEBUG" and not self.debug_cb.isChecked():
                    continue
                elif level == "INFO" and not self.info_cb.isChecked():
                    continue
                elif level == "WARNING" and not self.warning_cb.isChecked():
                    continue
                elif level == "ERROR" and not self.error_cb.isChecked():
                    continue
                elif level == "CRITICAL" and not self.critical_cb.isChecked():
                    continue
                
                # Check text search
                search_text = self.search_input.text().lower()
                if search_text:
                    if (search_text not in entry.get("message", "").lower() and
                        search_text not in entry.get("module", "").lower()):
                        continue
                
                # Check module filter
                module_filter = self.module_combo.currentText()
                if module_filter != "All Modules" and entry.get("module") != module_filter:
                    continue
                
                # Check user filter
                user_filter = self.user_combo.currentText()
                if user_filter != "All Users" and entry.get("user") != user_filter:
                    continue
                
                filtered_entries.append(entry)
            
            self.filtered_entries = filtered_entries
            self._display_logs()
            
        except Exception as e:
            self.logger.error(f"Failed to apply filters: {e}")
    
    def _display_logs(self):
        """Display filtered logs in the log viewer."""
        try:
            self.log_viewer.clear()
            
            for entry in self.filtered_entries:
                timestamp = entry.get("timestamp", "")
                level = entry.get("level", "")
                module = entry.get("module", "")
                message = entry.get("message", "")
                user = entry.get("user", "")
                
                # Format log entry
                log_line = f"[{timestamp}] {level:8} {module:10} {message}"
                if user:
                    log_line += f" (User: {user})"
                
                # Add to viewer
                self.log_viewer.append(log_line)
                
                # Apply color formatting
                cursor = self.log_viewer.textCursor()
                cursor.movePosition(QTextCursor.End)
                cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
                
                format = QTextCharFormat()
                format.setForeground(QColor(self._get_level_color(level)))
                cursor.setCharFormat(format)
            
            # Update log count
            self.log_count_label.setText(f"{len(self.filtered_entries)} entries")
            
            # Auto-scroll to bottom if enabled
            if self.auto_scroll_cb.isChecked():
                self.log_viewer.moveCursor(QTextCursor.End)
            
        except Exception as e:
            self.logger.error(f"Failed to display logs: {e}")
    
    def _get_level_color(self, level: str) -> str:
        """Get color for log level."""
        colors = {
            "DEBUG": "#888888",
            "INFO": "#6bcf7f",
            "WARNING": "#ffd93d",
            "ERROR": "#ff6b6b",
            "CRITICAL": "#ff4757"
        }
        return colors.get(level, "#ffffff")
    
    def _set_last_hour(self):
        """Set time filter to last hour."""
        from datetime import datetime, timedelta
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        self.from_date.setDate(QDate(one_hour_ago.year, one_hour_ago.month, one_hour_ago.day))
        self.to_date.setDate(QDate(now.year, now.month, now.day))
    
    def _set_last_day(self):
        """Set time filter to last day."""
        from datetime import datetime, timedelta
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        self.from_date.setDate(QDate(one_day_ago.year, one_day_ago.month, one_day_ago.day))
        self.to_date.setDate(QDate(now.year, now.month, now.day))
    
    def _clear_logs(self):
        """Clear all logs."""
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Are you sure you want to clear all logs?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.log_viewer.clear()
            self.log_entries = []
            self.filtered_entries = []
            self.log_count_label.setText("0 entries")
            self.show_success("Logs cleared")
    
    def _export_logs(self):
        """Export logs to file."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Logs",
                f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_viewer.toPlainText())
                
                self.show_success(f"Logs exported to {filename}")
            
        except Exception as e:
            self.show_error(f"Failed to export logs: {e}")
    
    def add_log_entry(self, log_data: Dict[str, Any]):
        """Add a new log entry."""
        try:
            self.log_entries.append(log_data)
            
            # Apply filters and refresh display
            self._apply_filters()
            
        except Exception as e:
            self.logger.error(f"Failed to add log entry: {e}")
    
    def get_tab_data(self) -> Dict[str, Any]:
        """Get logs tab data."""
        return {
            **super().get_tab_data(),
            "total_logs": len(self.log_entries),
            "filtered_logs": len(self.filtered_entries),
            "log_type": self.log_type_combo.currentText(),
            "search_text": self.search_input.text(),
            "auto_scroll": self.auto_scroll_cb.isChecked()
        }
