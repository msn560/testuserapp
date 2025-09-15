"""
Monitor tab for real-time system monitoring.

This tab provides real-time system monitoring, performance metrics,
and system health indicators.
"""

from typing import Dict, Any, List
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QProgressBar, QTextEdit, QSplitter,
    QHeaderView, QAbstractItemView, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QColor

from .base_tab import BaseTab, BaseTabWorker
from ...utils.logger import logger
from ...core.language import language_manager


class SystemMonitorWorker(BaseTabWorker):
    """
    System monitoring worker that runs in a separate thread.
    """
    
    # Signals for GUI communication
    metrics_updated = pyqtSignal(dict)  # System metrics
    processes_updated = pyqtSignal(list)  # Process list
    alert_detected = pyqtSignal(str)  # Alert message
    
    def __init__(self):
        super().__init__("monitor")
    
    def _do_refresh_data(self):
        """Refresh monitoring data in background thread."""
        try:
            if not self.running:
                return
            
            # Get system metrics
            self.get_system_metrics()
            
            # Get process list
            self.get_process_list()
            
        except Exception as e:
            self.logger.error(f"Error refreshing monitoring data: {e}")
            self.error_occurred.emit(str(e))
    
    def start_monitoring(self):
        """Start system monitoring."""
        self.running = True
        self.logger.debug("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.running = False
        self.logger.debug("System monitoring stopped")
    
    def get_system_metrics(self):
        """Get system metrics (non-blocking)."""
        try:
            import psutil
            import platform
            from datetime import datetime, timedelta
            
            # System information
            system_info = f"System: {platform.system()} {platform.release()}"
            
            # Boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            # Uptime
            uptime = datetime.now() - boot_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
                load_avg_str = f"Load Average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
            except AttributeError:
                load_avg_str = "Load Average: N/A (Windows)"
            
            # CPU usage (non-blocking)
            cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O (placeholder)
            network_io = "0 KB/s"
            
            # Prepare metrics
            metrics = {
                "system_info": system_info,
                "boot_time": boot_time.strftime('%Y-%m-%d %H:%M:%S'),
                "uptime": uptime_str,
                "load_avg": load_avg_str,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk_percent,
                "network_io": network_io,
                "boot_time_obj": boot_time,
                "uptime_obj": uptime
            }
            
            # Emit metrics
            self.metrics_updated.emit(metrics)
            
            # Check for alerts
            self._check_alerts(metrics)
            
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
    
    def get_processes(self):
        """Get process list (non-blocking)."""
        try:
            import psutil
            
            # Get process list
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            # Take top 20 processes
            top_processes = processes[:20]
            
            # Emit processes
            self.processes_updated.emit(top_processes)
            
        except Exception as e:
            self.logger.error(f"Failed to get processes: {e}")
    
    def _check_alerts(self, metrics: dict):
        """Check for system alerts."""
        try:
            # Check CPU usage
            if metrics.get('cpu_percent', 0) > 80:
                self.alert_detected.emit(f"WARNING: High CPU usage ({metrics['cpu_percent']:.1f}%)")
            
            # Check memory usage
            if metrics.get('memory_percent', 0) > 90:
                self.alert_detected.emit(f"CRITICAL: High memory usage ({metrics['memory_percent']:.1f}%)")
            
            # Check disk usage
            if metrics.get('disk_percent', 0) > 85:
                self.alert_detected.emit(f"WARNING: High disk usage ({metrics['disk_percent']:.1f}%)")
            
        except Exception as e:
            self.logger.error(f"Failed to check alerts: {e}")


class MonitorTab(BaseTab):
    """
    Monitor tab for real-time system monitoring.
    
    This tab provides real-time monitoring of system performance,
    resource usage, and system health indicators.
    """
    
    def __init__(self):
        """Initialize the monitor tab."""
        super().__init__("monitor", "System Monitor")
        
        # Data storage
        self.system_metrics = {}
        self.process_list = []
        self.alert_list = []
        
        # Create monitoring components
        self._create_monitor_components()
        
        # Set shorter refresh interval for real-time monitoring
        self.set_refresh_interval(2000)  # 2 seconds
        
        # Initialize monitoring worker
        self._init_monitor_worker()
        
        self.logger.info("Monitor tab initialized")
    
    def _init_monitor_worker(self):
        """Initialize monitor-specific worker."""
        try:
            # Use base class lazy loading
            self._ensure_worker_thread()
            
            # Create new monitor worker if not exists
            if not self.worker:
                self.worker = SystemMonitorWorker()
                
                # Connect signals
                self.worker.data_ready.connect(self._on_data_ready)
                self.worker.error_occurred.connect(self._on_error_occurred)
                self.worker.metrics_updated.connect(self._on_metrics_updated)
                self.worker.processes_updated.connect(self._on_processes_updated)
                self.worker.alert_detected.connect(self._on_alert_detected)
                
                # Move worker to thread
                self.worker.moveToThread(self.worker_thread)
            
            # Start worker
            self.worker_thread.started.connect(self.worker.start_worker)
            self.worker_thread.start()
            
            self.logger.info("Monitor worker initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize monitor worker: {e}")
    
    def _on_metrics_updated(self, metrics: dict):
        """Handle metrics updated signal."""
        try:
            # Update system info
            self.system_info_label.setText(metrics.get("system_info", "Unknown"))
            self.boot_time_label.setText(f"Boot Time: {metrics.get('boot_time', 'Unknown')}")
            self.uptime_label.setText(f"Uptime: {metrics.get('uptime', 'Unknown')}")
            self.load_avg_label.setText(metrics.get("load_avg", "Unknown"))
            
            # Update progress bars
            self.cpu_progress.setValue(int(metrics.get('cpu_percent', 0)))
            self.memory_progress.setValue(int(metrics.get('memory_percent', 0)))
            self.disk_progress.setValue(int(metrics.get('disk_percent', 0)))
            self.network_io_label.setText(metrics.get("network_io", "0 KB/s"))
            
            # Store metrics
            self.system_metrics = {
                "cpu_percent": metrics.get('cpu_percent', 0),
                "memory_percent": metrics.get('memory_percent', 0),
                "disk_percent": metrics.get('disk_percent', 0),
                "boot_time": metrics.get('boot_time_obj'),
                "uptime": metrics.get('uptime_obj')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {e}")
    
    def _on_processes_updated(self, processes: list):
        """Handle processes updated signal."""
        try:
            self.process_list = processes
            self._populate_processes_table()
        except Exception as e:
            self.logger.error(f"Failed to update processes: {e}")
    
    def _on_alert_detected(self, alert_message: str):
        """Handle alert detected signal."""
        try:
            alert_text = f"[{datetime.now().strftime('%H:%M:%S')}] {alert_message}"
            self.alerts_list.append(alert_text)
            
            # Keep only last 50 lines
            lines = self.alerts_list.toPlainText().split('\n')
            if len(lines) > 50:
                self.alerts_list.setPlainText('\n'.join(lines[-50:]))
                
        except Exception as e:
            self.logger.error(f"Failed to handle alert: {e}")
    
    def _create_monitor_components(self) -> None:
        """Create monitoring components."""
        try:
            # Initialize monitoring components
            self.monitor_widgets = {}
            self.metric_widgets = {}
            self.alert_widgets = {}
            
            # Create system monitoring widgets
            self._create_system_widgets()
            
            # Create metric widgets
            self._create_metric_widgets()
            
            # Create alert widgets
            self._create_alert_widgets()
            
            self.logger.info("Monitor components created")
            
        except Exception as e:
            self.logger.error(f"Failed to create monitor components: {e}")
    
    def _create_system_widgets(self) -> None:
        """Create system monitoring widgets."""
        try:
            # CPU monitoring
            self.monitor_widgets['cpu'] = {
                'usage': 0,
                'cores': [],
                'temperature': 0,
                'frequency': 0
            }
            
            # Memory monitoring
            self.monitor_widgets['memory'] = {
                'total': 0,
                'used': 0,
                'available': 0,
                'percentage': 0
            }
            
            # Disk monitoring
            self.monitor_widgets['disk'] = {
                'total': 0,
                'used': 0,
                'free': 0,
                'percentage': 0
            }
            
            # Network monitoring
            self.monitor_widgets['network'] = {
                'bytes_sent': 0,
                'bytes_recv': 0,
                'packets_sent': 0,
                'packets_recv': 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create system widgets: {e}")
    
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
    
    def _create_alert_widgets(self) -> None:
        """Create alert widgets."""
        try:
            # Alert types
            self.alert_widgets['types'] = {
                'cpu_high': {'threshold': 80, 'enabled': True},
                'memory_high': {'threshold': 85, 'enabled': True},
                'disk_full': {'threshold': 90, 'enabled': True},
                'api_error': {'threshold': 5, 'enabled': True}
            }
            
            # Alert notifications
            self.alert_widgets['notifications'] = {
                'email': {'enabled': False, 'recipients': []},
                'sms': {'enabled': False, 'recipients': []},
                'webhook': {'enabled': False, 'url': ''}
            }
            
            # Alert history
            self.alert_widgets['history'] = []
            
        except Exception as e:
            self.logger.error(f"Failed to create alert widgets: {e}")
    
    def _create_content_widget(self) -> QWidget:
        """Create the monitor content widget."""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Top panel - System metrics
        top_panel = self._create_metrics_panel()
        splitter.addWidget(top_panel)
        
        # Bottom panel - Processes and alerts
        bottom_panel = self._create_processes_panel()
        splitter.addWidget(bottom_panel)
        
        # Set splitter proportions (60% metrics, 40% processes)
        splitter.setSizes([400, 300])
        
        return content_widget
    
    def _create_metrics_panel(self) -> QWidget:
        """Create the system metrics panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # System overview section
        overview_group = self._create_overview_section()
        layout.addWidget(overview_group)
        
        # Performance metrics section
        performance_group = self._create_performance_section()
        layout.addWidget(performance_group)
        
        return panel
    
    def _create_overview_section(self) -> QGroupBox:
        """Create the system overview section."""
        group = QGroupBox("System Overview")
        layout = QGridLayout(group)
        
        # System info
        self.system_info_label = QLabel("System: Unknown")
        layout.addWidget(self.system_info_label, 0, 0, 1, 2)
        
        self.boot_time_label = QLabel("Boot Time: Unknown")
        layout.addWidget(self.boot_time_label, 1, 0, 1, 2)
        
        self.uptime_label = QLabel("Uptime: Unknown")
        layout.addWidget(self.uptime_label, 2, 0, 1, 2)
        
        # System load
        self.load_avg_label = QLabel("Load Average: Unknown")
        layout.addWidget(self.load_avg_label, 3, 0, 1, 2)
        
        return group
    
    def _create_performance_section(self) -> QGroupBox:
        """Create the performance metrics section."""
        group = QGroupBox("Performance Metrics")
        layout = QGridLayout(group)
        
        # CPU usage
        layout.addWidget(QLabel("CPU Usage:"), 0, 0)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setValue(0)
        self.cpu_progress.setFormat("CPU: %p%")
        layout.addWidget(self.cpu_progress, 0, 1)
        
        # Memory usage
        layout.addWidget(QLabel("Memory Usage:"), 1, 0)
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_progress.setValue(0)
        self.memory_progress.setFormat("Memory: %p%")
        layout.addWidget(self.memory_progress, 1, 1)
        
        # Disk usage
        layout.addWidget(QLabel("Disk Usage:"), 2, 0)
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        self.disk_progress.setValue(0)
        self.disk_progress.setFormat("Disk: %p%")
        layout.addWidget(self.disk_progress, 2, 1)
        
        # Network I/O
        layout.addWidget(QLabel("Network I/O:"), 3, 0)
        self.network_io_label = QLabel("0 KB/s")
        self.network_io_label.setStyleSheet("font-family: monospace;")
        layout.addWidget(self.network_io_label, 3, 1)
        
        return group
    
    def _create_processes_panel(self) -> QWidget:
        """Create the processes and alerts panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create horizontal splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Processes section
        processes_group = self._create_processes_section()
        splitter.addWidget(processes_group)
        
        # Alerts section
        alerts_group = self._create_alerts_section()
        splitter.addWidget(alerts_group)
        
        # Set splitter proportions (70% processes, 30% alerts)
        splitter.setSizes([500, 200])
        
        return panel
    
    def _create_processes_section(self) -> QGroupBox:
        """Create the processes section."""
        group = QGroupBox("Top Processes")
        layout = QVBoxLayout(group)
        
        # Process controls
        controls_layout = QHBoxLayout()
        
        self.refresh_processes_btn = QPushButton("Refresh")
        self.refresh_processes_btn.setIcon(QIcon("data/resources/icons/actions/refresh.png"))
        self.refresh_processes_btn.clicked.connect(self._refresh_processes)
        controls_layout.addWidget(self.refresh_processes_btn)
        
        self.auto_refresh_cb = QCheckBox("Auto-refresh")
        self.auto_refresh_cb.setChecked(True)
        self.auto_refresh_cb.stateChanged.connect(self._toggle_auto_refresh)
        controls_layout.addWidget(self.auto_refresh_cb)
        
        controls_layout.addStretch()
        
        # Sort options
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["CPU", "Memory", "Name"])
        self.sort_combo.currentTextChanged.connect(self._sort_processes)
        controls_layout.addWidget(QLabel("Sort by:"))
        controls_layout.addWidget(self.sort_combo)
        
        layout.addLayout(controls_layout)
        
        # Processes table
        self.processes_table = QTableWidget()
        self.processes_table.setColumnCount(5)
        self.processes_table.setHorizontalHeaderLabels([
            "PID", "Name", "CPU%", "Memory%", "Status"
        ])
        
        # Configure table
        self.processes_table.setAlternatingRowColors(True)
        self.processes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.processes_table.horizontalHeader().setStretchLastSection(True)
        self.processes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.processes_table.setMaximumHeight(200)
        
        layout.addWidget(self.processes_table)
        
        return group
    
    def _create_alerts_section(self) -> QGroupBox:
        """Create the alerts section."""
        group = QGroupBox("System Alerts")
        layout = QVBoxLayout(group)
        
        # Alert controls
        alert_controls_layout = QHBoxLayout()
        
        self.clear_alerts_btn = QPushButton("Clear")
        self.clear_alerts_btn.clicked.connect(self._clear_alerts)
        alert_controls_layout.addWidget(self.clear_alerts_btn)
        
        alert_controls_layout.addStretch()
        
        layout.addLayout(alert_controls_layout)
        
        # Alerts list
        self.alerts_list = QTextEdit()
        self.alerts_list.setReadOnly(True)
        self.alerts_list.setMaximumHeight(150)
        self.alerts_list.setProperty("class", "console")
        layout.addWidget(self.alerts_list)
        
        return group
    
    def refresh_data(self):
        """Refresh monitoring data (non-blocking)."""
        try:
            if self.monitor_worker:
                # Request system metrics from worker thread
                self.monitor_worker.get_system_metrics()
                
                # Request processes if auto-refresh is enabled
                if self.auto_refresh_cb.isChecked():
                    self.monitor_worker.get_processes()
                
                self.update_status("Monitoring data refresh requested")
            else:
                self.show_error("Monitoring worker not available")
            
        except Exception as e:
            self.show_error(f"Failed to refresh monitoring data: {e}")
    
    
    def _populate_processes_table(self):
        """Populate the processes table (optimized for performance)."""
        try:
            # Disable table updates during population to prevent UI freezing
            self.processes_table.setUpdatesEnabled(False)
            
            # Limit the number of processes to display for better performance
            max_processes = 100
            processes_to_show = self.process_list[:max_processes]
            
            self.processes_table.setRowCount(len(processes_to_show))
            
            for row, process in enumerate(processes_to_show):
                # PID
                self.processes_table.setItem(row, 0, QTableWidgetItem(str(process.get('pid', ''))))
                
                # Name
                name = process.get('name', 'Unknown')
                if len(name) > 20:
                    name = name[:17] + "..."
                self.processes_table.setItem(row, 1, QTableWidgetItem(name))
                
                # CPU%
                cpu_percent = process.get('cpu_percent', 0)
                cpu_item = QTableWidgetItem(f"{cpu_percent:.1f}%")
                if cpu_percent > 50:
                    cpu_item.setBackground(QColor('#ffebee'))  # Light red
                elif cpu_percent > 20:
                    cpu_item.setBackground(QColor('#fff3e0'))  # Light orange
                self.processes_table.setItem(row, 2, cpu_item)
                
                # Memory%
                memory_percent = process.get('memory_percent', 0)
                memory_item = QTableWidgetItem(f"{memory_percent:.1f}%")
                if memory_percent > 10:
                    memory_item.setBackground(QColor('#ffebee'))  # Light red
                elif memory_percent > 5:
                    memory_item.setBackground(QColor('#fff3e0'))  # Light orange
                self.processes_table.setItem(row, 3, memory_item)
                
                # Status
                status = process.get('status', 'Unknown')
                self.processes_table.setItem(row, 4, QTableWidgetItem(status))
            
            # Re-enable table updates after population
            self.processes_table.setUpdatesEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Failed to populate processes table: {e}")
            # Make sure to re-enable updates even if there's an error
            self.processes_table.setUpdatesEnabled(True)
    
    def _refresh_processes(self):
        """Refresh processes list (non-blocking)."""
        try:
            if self.monitor_worker:
                self.monitor_worker.get_processes()
                self.show_success("Processes refresh requested")
            else:
                self.show_error("Monitoring worker not available")
        except Exception as e:
            self.show_error(f"Failed to refresh processes: {e}")
    
    def _toggle_auto_refresh(self, state):
        """Toggle auto-refresh for processes."""
        auto_refresh = state == Qt.Checked
        if auto_refresh:
            self.show_info("Process auto-refresh enabled")
        else:
            self.show_info("Process auto-refresh disabled")
    
    def _sort_processes(self, sort_by: str):
        """Sort processes by specified criteria."""
        try:
            if sort_by == "CPU":
                self.process_list.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            elif sort_by == "Memory":
                self.process_list.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
            elif sort_by == "Name":
                self.process_list.sort(key=lambda x: x.get('name', '').lower())
            
            self._populate_processes_table()
            
        except Exception as e:
            self.logger.error(f"Failed to sort processes: {e}")
    
    def _clear_alerts(self):
        """Clear all alerts."""
        self.alerts_list.clear()
        self.show_success("Alerts cleared")
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """Update metrics from external source."""
        try:
            # Update CPU usage
            if 'cpu_percent' in metrics:
                self.cpu_progress.setValue(int(metrics['cpu_percent']))
            
            # Update memory usage
            if 'memory_percent' in metrics:
                self.memory_progress.setValue(int(metrics['memory_percent']))
            
            # Update disk usage
            if 'disk_percent' in metrics:
                self.disk_progress.setValue(int(metrics['disk_percent']))
            
            # Update system metrics
            self.system_metrics.update(metrics)
            
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {e}")
    
    def cleanup(self):
        """Cleanup monitoring thread when tab is closed."""
        try:
            if self.monitor_worker:
                self.monitor_worker.stop_monitoring()
            
            if self.monitor_thread and self.monitor_thread.isRunning():
                self.monitor_thread.quit()
                self.monitor_thread.wait(3000)  # Wait up to 3 seconds
            
            self.logger.info("Monitor tab cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup monitor tab: {e}")
    
    def get_tab_data(self) -> Dict[str, Any]:
        """Get monitor tab data."""
        return {
            **super().get_tab_data(),
            "system_metrics": self.system_metrics,
            "processes_count": len(self.process_list),
            "alerts_count": len(self.alert_list),
            "auto_refresh_enabled": self.auto_refresh_cb.isChecked()
        }
