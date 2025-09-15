"""
Log Viewer Widget module - Log görüntüleyici

Bu modül log kayıtlarını görüntülemek için widget sağlar.
Real-time log streaming, filtreleme, arama ve export özellikleri.
"""

import re
import json
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
    QPushButton, QComboBox, QLabel, QCheckBox, QSpinBox,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMenu, QAction, QFileDialog, QMessageBox,
    QProgressBar, QGroupBox, QFormLayout, QDateTimeEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, QObject, QDateTime
from PyQt5.QtGui import QTextCharFormat, QColor, QFont, QSyntaxHighlighter, QTextDocument, QTextCursor

from .base_widget import BaseWidget
from ...core.constants import LogLevel
from ...utils.logger import logger
from ...core.language import language_manager


class LogFilterWorker(QObject):
    """
    Log filter worker - Log'ları background'da filtreler
    """
    
    logs_filtered = pyqtSignal(list)  # Filtrelenmiş log'lar
    filter_progress = pyqtSignal(int, int)  # current, total
    filter_complete = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.cancel_requested = False
    
    def filter_logs(self, logs: List[Dict], filters: Dict[str, Any]):
        """
        Log'ları filtrele
        
        Args:
            logs: Tüm log kayıtları
            filters: Filtre kriterleri
        """
        try:
            self.running = True
            self.cancel_requested = False
            
            filtered_logs = []
            total_logs = len(logs)
            
            for i, log_entry in enumerate(logs):
                if self.cancel_requested:
                    break
                
                if self._matches_filters(log_entry, filters):
                    filtered_logs.append(log_entry)
                
                # Progress güncelle
                if i % 100 == 0:  # Her 100 log'da bir
                    self.filter_progress.emit(i + 1, total_logs)
            
            if not self.cancel_requested:
                self.logs_filtered.emit(filtered_logs)
                self.filter_complete.emit()
            
        except Exception as e:
            logger.error(f"Error filtering logs: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.running = False
    
    def _matches_filters(self, log_entry: Dict, filters: Dict[str, Any]) -> bool:
        """
        Log entry'nin filtrelere uyup uymadığını kontrol et
        
        Args:
            log_entry: Log kaydı
            filters: Filtre kriterleri
            
        Returns:
            Filtre eşleşmesi
        """
        # Level filter
        level_filter = filters.get('level')
        if level_filter and level_filter != 'ALL':
            if log_entry.get('level', '').upper() != level_filter.upper():
                return False
        
        # Search text
        search_text = filters.get('search_text', '').lower()
        if search_text:
            searchable_fields = [
                log_entry.get('message', ''),
                log_entry.get('module', ''),
                log_entry.get('logger_name', '')
            ]
            if not any(search_text in field.lower() for field in searchable_fields):
                return False
        
        # Date range
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        if start_date or end_date:
            log_time = log_entry.get('timestamp')
            if log_time:
                if isinstance(log_time, str):
                    try:
                        log_datetime = datetime.fromisoformat(log_time.replace('Z', '+00:00'))
                    except:
                        return False
                else:
                    log_datetime = log_time
                
                if start_date and log_datetime < start_date:
                    return False
                if end_date and log_datetime > end_date:
                    return False
        
        # Module filter
        module_filter = filters.get('module')
        if module_filter and log_entry.get('module', '') != module_filter:
            return False
        
        # Regex filter
        regex_pattern = filters.get('regex_pattern')
        if regex_pattern:
            try:
                if not re.search(regex_pattern, log_entry.get('message', ''), re.IGNORECASE):
                    return False
            except re.error:
                # Invalid regex, ignore filter
                pass
        
        return True
    
    def cancel_filtering(self):
        """Filtrelemeyi iptal et"""
        self.cancel_requested = True


class LogHighlighter(QSyntaxHighlighter):
    """Log syntax highlighter"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        self.setup_highlighting_rules()
    
    def setup_highlighting_rules(self):
        """Highlighting kurallarını ayarla"""
        # Log level colors
        level_colors = {
            'CRITICAL': QColor(255, 50, 50),
            'ERROR': QColor(255, 100, 100),
            'WARNING': QColor(255, 200, 100),
            'INFO': QColor(100, 200, 255),
            'DEBUG': QColor(150, 150, 150)
        }
        
        for level, color in level_colors.items():
            format = QTextCharFormat()
            format.setForeground(color)
            format.setFontWeight(QFont.Bold)
            self.highlighting_rules.append((re.compile(f'\\b{level}\\b'), format))
        
        # Timestamps
        timestamp_format = QTextCharFormat()
        timestamp_format.setForeground(QColor(100, 255, 100))
        self.highlighting_rules.append((
            re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'), 
            timestamp_format
        ))
        
        # IP addresses
        ip_format = QTextCharFormat()
        ip_format.setForeground(QColor(255, 255, 100))
        self.highlighting_rules.append((
            re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
            ip_format
        ))
        
        # URLs
        url_format = QTextCharFormat()
        url_format.setForeground(QColor(100, 255, 255))
        url_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        self.highlighting_rules.append((
            re.compile(r'https?://[^\s]+'),
            url_format
        ))
    
    def highlightBlock(self, text):
        """Text block'u highlight et"""
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format)


class LogViewerWidget(BaseWidget):
    """
    Log viewer widget'ı - Gelişmiş log görüntüleme
    """
    
    # Signals
    log_selected = pyqtSignal(dict)  # Log seçildi
    filter_changed = pyqtSignal(dict)  # Filtre değişti
    export_requested = pyqtSignal(list, str)  # Export istendi
    
    def __init__(self, parent=None):
        """Log viewer widget'ını başlat"""
        super().__init__(parent)
        
        self.all_logs = []
        self.filtered_logs = []
        self.current_filters = {}
        self.auto_scroll = True
        self.max_logs = 10000
        
        # Worker thread
        self.filter_thread = QThread()
        self.filter_worker = LogFilterWorker()
        self.filter_worker.moveToThread(self.filter_thread)
        
        self._setup_ui()
        self._setup_connections()
        self._setup_worker()
        
        # Auto refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._load_logs)
        self.refresh_timer.start(5000)  # 5 saniyede bir
    
    def _setup_ui(self):
        """UI'yi kur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs...")
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(QLabel("Search:"))
        toolbar_layout.addWidget(self.search_input)
        
        # Level filter
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"])
        self.level_combo.currentTextChanged.connect(self._on_level_filter_changed)
        toolbar_layout.addWidget(QLabel("Level:"))
        toolbar_layout.addWidget(self.level_combo)
        
        # Module filter
        self.module_combo = QComboBox()
        self.module_combo.addItem("All Modules")
        self.module_combo.currentTextChanged.connect(self._on_module_filter_changed)
        toolbar_layout.addWidget(QLabel("Module:"))
        toolbar_layout.addWidget(self.module_combo)
        
        toolbar_layout.addStretch()
        
        # Buttons
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._load_logs)
        toolbar_layout.addWidget(self.refresh_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_logs)
        toolbar_layout.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self._on_export_logs)
        toolbar_layout.addWidget(self.export_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # Advanced filters (collapsible)
        self.advanced_group = QGroupBox("Advanced Filters")
        self.advanced_group.setCheckable(True)
        self.advanced_group.setChecked(False)
        
        advanced_layout = QFormLayout(self.advanced_group)
        
        # Date range
        date_layout = QHBoxLayout()
        
        self.start_date_edit = QDateTimeEdit()
        self.start_date_edit.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.start_date_edit.dateTimeChanged.connect(self._on_date_filter_changed)
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.start_date_edit)
        
        self.end_date_edit = QDateTimeEdit()
        self.end_date_edit.setDateTime(QDateTime.currentDateTime())
        self.end_date_edit.dateTimeChanged.connect(self._on_date_filter_changed)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.end_date_edit)
        
        advanced_layout.addRow("Date Range:", date_layout)
        
        # Regex filter
        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText("Regular expression pattern...")
        self.regex_input.textChanged.connect(self._on_regex_filter_changed)
        advanced_layout.addRow("Regex:", self.regex_input)
        
        # Max logs
        self.max_logs_spin = QSpinBox()
        self.max_logs_spin.setRange(100, 50000)
        self.max_logs_spin.setValue(self.max_logs)
        self.max_logs_spin.valueChanged.connect(self._on_max_logs_changed)
        advanced_layout.addRow("Max Logs:", self.max_logs_spin)
        
        main_layout.addWidget(self.advanced_group)
        
        # Splitter for log view modes
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Log table (structured view)
        self.log_table = QTableWidget()
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.log_table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Table columns
        self.columns = [
            {'key': 'timestamp', 'title': 'Time', 'width': 150},
            {'key': 'level', 'title': 'Level', 'width': 80},
            {'key': 'module', 'title': 'Module', 'width': 120},
            {'key': 'message', 'title': 'Message', 'width': 400}
        ]
        
        self.log_table.setColumnCount(len(self.columns))
        self.log_table.setHorizontalHeaderLabels([col['title'] for col in self.columns])
        
        # Column widths
        header = self.log_table.horizontalHeader()
        for i, col in enumerate(self.columns):
            if col['width']:
                self.log_table.setColumnWidth(i, col['width'])
        header.setStretchLastSection(True)
        
        self.log_table.itemSelectionChanged.connect(self._on_log_selected)
        self.splitter.addWidget(self.log_table)
        
        # Log text view (raw view)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        
        # Syntax highlighter
        self.highlighter = LogHighlighter(self.log_text.document())
        
        self.splitter.addWidget(self.log_text)
        
        # Equal sizes initially
        self.splitter.setSizes([400, 400])
        
        main_layout.addWidget(self.splitter)
        
        # Status bar
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        status_layout.addStretch()
        
        # Auto scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto Scroll")
        self.auto_scroll_cb.setChecked(self.auto_scroll)
        self.auto_scroll_cb.toggled.connect(self._on_auto_scroll_toggled)
        status_layout.addWidget(self.auto_scroll_cb)
        
        # Count label
        self.count_label = QLabel("0 logs")
        status_layout.addWidget(self.count_label)
        
        main_layout.addLayout(status_layout)
    
    def _setup_connections(self):
        """Signal bağlantılarını kur"""
        pass
    
    def _setup_worker(self):
        """Worker'ı kur"""
        self.filter_worker.logs_filtered.connect(self._on_logs_filtered)
        self.filter_worker.filter_progress.connect(self._on_filter_progress)
        self.filter_worker.filter_complete.connect(self._on_filter_complete)
        self.filter_worker.error_occurred.connect(self._on_filter_error)
        
        self.filter_thread.start()
    
    def add_log_entry(self, log_entry: Dict[str, Any]):
        """
        Yeni log entry ekle
        
        Args:
            log_entry: Log kaydı
        """
        # Timestamp ekle
        if 'timestamp' not in log_entry:
            log_entry['timestamp'] = datetime.now().isoformat()
        
        self.all_logs.append(log_entry)
        
        # Max logs kontrolü
        if len(self.all_logs) > self.max_logs:
            self.all_logs.pop(0)
        
        # Module combo'yu güncelle
        self._update_module_combo()
        
        # Filtreleri uygula
        self._apply_filters()
    
    def add_log_entries(self, log_entries: List[Dict[str, Any]]):
        """
        Çoklu log entry ekle
        
        Args:
            log_entries: Log kayıtları
        """
        for entry in log_entries:
            if 'timestamp' not in entry:
                entry['timestamp'] = datetime.now().isoformat()
        
        self.all_logs.extend(log_entries)
        
        # Max logs kontrolü
        if len(self.all_logs) > self.max_logs:
            self.all_logs = self.all_logs[-self.max_logs:]
        
        self._update_module_combo()
        self._apply_filters()
    
    def clear_logs(self):
        """Log'ları temizle"""
        self.all_logs.clear()
        self.filtered_logs.clear()
        self.log_table.setRowCount(0)
        self.log_text.clear()
        self.count_label.setText("0 logs")
        logger.info("Logs cleared")
    
    def _load_logs(self):
        """Log'ları yükle (mock data)"""
        # Mock log entries - gerçek implementasyonda log service'den gelecek
        mock_logs = [
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'module': 'api.server',
                'message': 'Server started successfully',
                'logger_name': 'server_manager'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'WARNING',
                'module': 'auth.service',
                'message': 'Failed login attempt from 192.168.1.100',
                'logger_name': 'auth_service'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'ERROR',
                'module': 'database',
                'message': 'Connection timeout to database',
                'logger_name': 'db_manager'
            }
        ]
        
        # Sadece test için - gerçek implementasyonda kaldırılacak
        if len(self.all_logs) < 100:  # İlk 100 log'u yükle
            self.add_log_entries(mock_logs)
    
    def _update_module_combo(self):
        """Module combo'yu güncelle"""
        modules = set()
        for log in self.all_logs:
            module = log.get('module', '')
            if module:
                modules.add(module)
        
        current_text = self.module_combo.currentText()
        self.module_combo.clear()
        self.module_combo.addItem("All Modules")
        
        for module in sorted(modules):
            self.module_combo.addItem(module)
        
        # Önceki seçimi geri yükle
        index = self.module_combo.findText(current_text)
        if index >= 0:
            self.module_combo.setCurrentIndex(index)
    
    def _apply_filters(self):
        """Filtreleri uygula"""
        if not self.all_logs:
            self.filtered_logs = []
            self._populate_table()
            return
        
        if not self.current_filters:
            self.filtered_logs = self.all_logs.copy()
            self._populate_table()
            return
        
        # Worker thread'de filtrele
        if not self.filter_worker.running:
            self.status_label.setText("Filtering logs...")
            self.progress_bar.setVisible(True)
            self.filter_worker.filter_logs(self.all_logs, self.current_filters)
    
    def _on_logs_filtered(self, filtered_logs: List[Dict]):
        """Log'lar filtrelendiğinde"""
        self.filtered_logs = filtered_logs
        self._populate_table()
    
    def _on_filter_progress(self, current: int, total: int):
        """Filtre progress güncellemesi"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
    
    def _on_filter_complete(self):
        """Filtreleme tamamlandığında"""
        self.status_label.setText("Ready")
        self.progress_bar.setVisible(False)
    
    def _on_filter_error(self, error: str):
        """Filtre hatası"""
        self.status_label.setText(f"Filter error: {error}")
        self.progress_bar.setVisible(False)
        logger.error(f"Log filter error: {error}")
    
    def _populate_table(self):
        """Tabloyu doldur"""
        self.log_table.setRowCount(len(self.filtered_logs))
        
        for row, log_entry in enumerate(self.filtered_logs):
            for col, column in enumerate(self.columns):
                item = self._create_table_item(log_entry, column)
                self.log_table.setItem(row, col, item)
        
        # Count güncelle
        self.count_label.setText(f"{len(self.filtered_logs)} logs")
        
        # Auto scroll
        if self.auto_scroll:
            self.log_table.scrollToBottom()
        
        # Text view'i güncelle
        self._update_text_view()
    
    def _create_table_item(self, log_entry: Dict, column: Dict) -> QTableWidgetItem:
        """Tablo item'ı oluştur"""
        key = column['key']
        value = log_entry.get(key, '')
        
        if key == 'timestamp':
            # Timestamp formatting
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    text = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    text = str(value)
            else:
                text = str(value)
        else:
            text = str(value)
        
        item = QTableWidgetItem(text)
        item.setData(Qt.UserRole, log_entry)
        
        # Level-based coloring
        if key == 'level':
            level = log_entry.get('level', '').upper()
            if level == 'ERROR':
                item.setForeground(QColor(255, 100, 100))
            elif level == 'WARNING':
                item.setForeground(QColor(255, 200, 100))
            elif level == 'INFO':
                item.setForeground(QColor(100, 200, 255))
            elif level == 'DEBUG':
                item.setForeground(QColor(150, 150, 150))
            elif level == 'CRITICAL':
                item.setForeground(QColor(255, 50, 50))
        
        return item
    
    def _update_text_view(self):
        """Text view'i güncelle"""
        text_lines = []
        for log_entry in self.filtered_logs:
            timestamp = log_entry.get('timestamp', '')
            level = log_entry.get('level', '')
            module = log_entry.get('module', '')
            message = log_entry.get('message', '')
            
            line = f"{timestamp} [{level}] {module}: {message}"
            text_lines.append(line)
        
        self.log_text.setPlainText('\n'.join(text_lines))
        
        # Auto scroll
        if self.auto_scroll:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text.setTextCursor(cursor)
    
    def _on_search_changed(self, text: str):
        """Search değiştiğinde"""
        self.current_filters['search_text'] = text
        self._apply_filters()
    
    def _on_level_filter_changed(self, level: str):
        """Level filtresi değiştiğinde"""
        if level == "ALL":
            self.current_filters.pop('level', None)
        else:
            self.current_filters['level'] = level
        self._apply_filters()
    
    def _on_module_filter_changed(self, module: str):
        """Module filtresi değiştiğinde"""
        if module == "All Modules":
            self.current_filters.pop('module', None)
        else:
            self.current_filters['module'] = module
        self._apply_filters()
    
    def _on_date_filter_changed(self):
        """Date filtresi değiştiğinde"""
        start_date = self.start_date_edit.dateTime().toPyDateTime()
        end_date = self.end_date_edit.dateTime().toPyDateTime()
        
        self.current_filters['start_date'] = start_date
        self.current_filters['end_date'] = end_date
        self._apply_filters()
    
    def _on_regex_filter_changed(self, pattern: str):
        """Regex filtresi değiştiğinde"""
        if pattern.strip():
            self.current_filters['regex_pattern'] = pattern
        else:
            self.current_filters.pop('regex_pattern', None)
        self._apply_filters()
    
    def _on_max_logs_changed(self, value: int):
        """Max logs değiştiğinde"""
        self.max_logs = value
        if len(self.all_logs) > self.max_logs:
            self.all_logs = self.all_logs[-self.max_logs:]
            self._apply_filters()
    
    def _on_auto_scroll_toggled(self, checked: bool):
        """Auto scroll toggle"""
        self.auto_scroll = checked
    
    def _on_log_selected(self):
        """Log seçildiğinde"""
        current_row = self.log_table.currentRow()
        if current_row >= 0:
            item = self.log_table.item(current_row, 0)
            if item:
                log_entry = item.data(Qt.UserRole)
                if log_entry:
                    self.log_selected.emit(log_entry)
    
    def _on_export_logs(self):
        """Log'ları export et"""
        if not self.filtered_logs:
            QMessageBox.information(self, "Export Logs", "No logs to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json);;Text Files (*.txt);;CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    self._export_json(file_path)
                elif file_path.endswith('.txt'):
                    self._export_text(file_path)
                elif file_path.endswith('.csv'):
                    self._export_csv(file_path)
                
                QMessageBox.information(self, "Export Complete", f"Logs exported to {file_path}")
                logger.info(f"Logs exported to {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export logs: {str(e)}")
                logger.error(f"Failed to export logs: {e}")
    
    def _export_json(self, file_path: str):
        """JSON formatında export"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.filtered_logs, f, indent=2, ensure_ascii=False, default=str)
    
    def _export_text(self, file_path: str):
        """Text formatında export"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for log_entry in self.filtered_logs:
                timestamp = log_entry.get('timestamp', '')
                level = log_entry.get('level', '')
                module = log_entry.get('module', '')
                message = log_entry.get('message', '')
                
                line = f"{timestamp} [{level}] {module}: {message}\n"
                f.write(line)
    
    def _export_csv(self, file_path: str):
        """CSV formatında export"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['Timestamp', 'Level', 'Module', 'Message'])
            
            # Data
            for log_entry in self.filtered_logs:
                writer.writerow([
                    log_entry.get('timestamp', ''),
                    log_entry.get('level', ''),
                    log_entry.get('module', ''),
                    log_entry.get('message', '')
                ])
    
    def get_widget_data(self) -> Dict[str, Any]:
        """Widget verilerini al"""
        return {
            'total_logs': len(self.all_logs),
            'filtered_logs': len(self.filtered_logs),
            'current_filters': self.current_filters.copy(),
            'auto_scroll': self.auto_scroll,
            'max_logs': self.max_logs
        }
    
    def cleanup(self):
        """Widget'ı temizle"""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
        
        if self.filter_thread.isRunning():
            self.filter_worker.cancel_filtering()
            self.filter_thread.quit()
            self.filter_thread.wait(3000)
        
        super().cleanup()