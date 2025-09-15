"""
Console Widget module - Kayan konsol ekranı

Bu modül server log'larını ve konsol çıktılarını gösteren widget'ı sağlar.
Real-time log streaming, filtreleme ve renk kodlaması.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QLineEdit, QPushButton, QComboBox, QLabel, 
                            QCheckBox, QSpinBox, QScrollBar)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, QMutex, QMutexLocker
from PyQt5.QtGui import QTextCharFormat, QColor, QFont, QSyntaxHighlighter, QTextDocument
from PyQt5.QtCore import QTextCursor
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

from .base_widget import BaseWidget
from ...core.constants import LogLevel
from ...utils.logger import logger
from ...core.language import language_manager


class LogHighlighter(QSyntaxHighlighter):
    """Log syntax highlighter."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        self.setup_highlighting_rules()
    
    def setup_highlighting_rules(self):
        """Highlighting kurallarını ayarlar."""
        # Log level renkleri
        level_colors = {
            'ERROR': QColor(255, 100, 100),
            'WARNING': QColor(255, 200, 100),
            'INFO': QColor(100, 200, 255),
            'DEBUG': QColor(150, 150, 150),
            'CRITICAL': QColor(255, 50, 50)
        }
        
        for level, color in level_colors.items():
            format = QTextCharFormat()
            format.setForeground(color)
            format.setFontWeight(QFont.Bold)
            self.highlighting_rules.append((re.compile(f'\\b{level}\\b'), format))
        
        # IP adresleri
        ip_format = QTextCharFormat()
        ip_format.setForeground(QColor(100, 255, 100))
        self.highlighting_rules.append((re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), ip_format))
        
        # HTTP status kodları
        status_format = QTextCharFormat()
        status_format.setForeground(QColor(255, 255, 100))
        status_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((re.compile(r'\b(200|201|204|400|401|403|404|500|502|503)\b'), status_format))
        
        # Timestamp
        timestamp_format = QTextCharFormat()
        timestamp_format.setForeground(QColor(200, 200, 200))
        self.highlighting_rules.append((re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'), timestamp_format))
    
    def highlightBlock(self, text):
        """Text bloğunu highlight eder."""
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format)


class LogEntry:
    """Log entry sınıfı."""
    
    def __init__(self, timestamp: datetime, level: str, message: str, 
                 source: str = "", metadata: Dict[str, Any] = None):
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.source = source
        self.metadata = metadata or {}
        self.formatted_message = self._format_message()
    
    def _format_message(self) -> str:
        """Log mesajını formatlar."""
        timestamp_str = self.timestamp.strftime("%H:%M:%S.%f")[:-3]  # Milisaniye
        return f"[{timestamp_str}] {self.level:8} | {self.source:15} | {self.message}"
    
    def matches_filter(self, level_filter: str, text_filter: str, source_filter: str) -> bool:
        """Filtre kriterlerine uygun mu kontrol eder."""
        # Level filtresi
        if level_filter and level_filter != "ALL" and self.level != level_filter:
            return False
        
        # Text filtresi
        if text_filter and text_filter.lower() not in self.message.lower():
            return False
        
        # Source filtresi
        if source_filter and source_filter.lower() not in self.source.lower():
            return False
        
        return True


class ConsoleWidget(BaseWidget):
    """
    Kayan konsol ekranı widget'ı.
    
    Bu widget server log'larını ve konsol çıktılarını gösterir.
    """
    
    # Signals
    log_selected = pyqtSignal(LogEntry)
    filter_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, widget_id: str = "console_widget"):
        """
        ConsoleWidget'ı başlatır.
        
        Args:
            parent: Parent widget
            widget_id: Widget ID'si
        """
        super().__init__(parent, widget_id)
        
        # Log verileri
        self.log_entries: List[LogEntry] = []
        self.max_entries = 10000
        self.auto_scroll = True
        self.word_wrap = True
        
        # Filtreler
        self.current_filters = {
            "level": "ALL",
            "text": "",
            "source": ""
        }
        
        # UI bileşenleri
        self.setup_ui()
        self.setup_connections()
        
        # Highlighter
        self.highlighter = LogHighlighter(self.console_text.document())
        
        # Timer'lar
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(100)  # 100ms güncelleme
        
        self.logger.debug(f"ConsoleWidget initialized: {self.widget_id}")
    
    def setup_ui(self):
        """UI bileşenlerini oluşturur."""
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Kontrol paneli
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Konsol metin alanı
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setFont(QFont("Consolas", 9))
        self.console_text.setLineWrapMode(QTextEdit.NoWrap if not self.word_wrap else QTextEdit.WidgetWidth)
        self.console_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.console_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_layout.addWidget(self.console_text)
        
        # Durum çubuğu
        status_panel = self.create_status_panel()
        main_layout.addWidget(status_panel)
    
    def create_control_panel(self) -> QWidget:
        """Kontrol panelini oluşturur."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Level filtresi
        layout.addWidget(QLabel(f"{language_manager.translate('ui.console.level')}:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.setCurrentText("ALL")
        layout.addWidget(self.level_filter)
        
        # Text filtresi
        layout.addWidget(QLabel(f"{language_manager.translate('ui.console.filter')}:"))
        self.text_filter = QLineEdit()
        self.text_filter.setPlaceholderText(language_manager.translate("ui.console.search_logs"))
        layout.addWidget(self.text_filter)
        
        # Source filtresi
        layout.addWidget(QLabel(f"{language_manager.translate('ui.console.source')}:"))
        self.source_filter = QLineEdit()
        self.source_filter.setPlaceholderText(language_manager.translate("ui.console.filter_by_source"))
        layout.addWidget(self.source_filter)
        
        # Kontrol butonları
        self.clear_button = QPushButton(language_manager.translate("ui.console.clear"))
        self.clear_button.setMaximumWidth(60)
        layout.addWidget(self.clear_button)
        
        self.export_button = QPushButton(language_manager.translate("ui.console.export"))
        self.export_button.setMaximumWidth(60)
        layout.addWidget(self.export_button)
        
        # Auto scroll checkbox
        self.auto_scroll_cb = QCheckBox(language_manager.translate("ui.console.auto_scroll"))
        self.auto_scroll_cb.setChecked(self.auto_scroll)
        layout.addWidget(self.auto_scroll_cb)
        
        # Word wrap checkbox
        self.word_wrap_cb = QCheckBox(language_manager.translate("ui.console.word_wrap"))
        self.word_wrap_cb.setChecked(self.word_wrap)
        layout.addWidget(self.word_wrap_cb)
        
        # Max entries
        layout.addWidget(QLabel(f"{language_manager.translate('ui.console.max_entries')}:"))
        self.max_entries_spin = QSpinBox()
        self.max_entries_spin.setRange(100, 100000)
        self.max_entries_spin.setValue(self.max_entries)
        self.max_entries_spin.setMaximumWidth(80)
        layout.addWidget(self.max_entries_spin)
        
        layout.addStretch()
        return panel
    
    def create_status_panel(self) -> QWidget:
        """Durum panelini oluşturur."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Durum etiketleri
        self.status_label = QLabel(language_manager.translate("ui.console.ready"))
        layout.addWidget(self.status_label)
        
        self.entries_label = QLabel(f"{language_manager.translate('ui.console.entries')}: 0")
        layout.addWidget(self.entries_label)
        
        self.filtered_label = QLabel(f"{language_manager.translate('ui.console.filtered')}: 0")
        layout.addWidget(self.filtered_label)
        
        layout.addStretch()
        
        # Scroll durumu
        self.scroll_label = QLabel("")
        layout.addWidget(self.scroll_label)
        
        return panel
    
    def setup_connections(self):
        """Bağlantıları kurar."""
        # Filtre değişiklikleri
        self.level_filter.currentTextChanged.connect(self.on_filter_changed)
        self.text_filter.textChanged.connect(self.on_filter_changed)
        self.source_filter.textChanged.connect(self.on_filter_changed)
        
        # Kontrol butonları
        self.clear_button.clicked.connect(self.clear_logs)
        self.export_button.clicked.connect(self.export_logs)
        
        # Checkbox'lar
        self.auto_scroll_cb.toggled.connect(self.on_auto_scroll_changed)
        self.word_wrap_cb.toggled.connect(self.on_word_wrap_changed)
        
        # Max entries
        self.max_entries_spin.valueChanged.connect(self.on_max_entries_changed)
        
        # Log seçimi
        self.console_text.selectionChanged.connect(self.on_log_selection_changed)
    
    def add_log_entry(self, level: str, message: str, source: str = "", 
                     metadata: Dict[str, Any] = None) -> None:
        """
        Log entry ekler.
        
        Args:
            level: Log seviyesi
            message: Log mesajı
            source: Log kaynağı
            metadata: Ek metadata
        """
        try:
            # Yeni log entry oluştur
            entry = LogEntry(
                timestamp=datetime.now(),
                level=level,
                message=message,
                source=source,
                metadata=metadata or {}
            )
            
            # Log entry'yi ekle
            self.log_entries.append(entry)
            
            # Maksimum entry sayısını kontrol et
            if len(self.log_entries) > self.max_entries:
                self.log_entries = self.log_entries[-self.max_entries:]
            
            # Display'i güncelle
            self.update_display()
            
        except Exception as e:
            self.logger.error(f"Error adding log entry: {e}")
    
    def clear_logs(self) -> None:
        """Log'ları temizler."""
        try:
            self.log_entries.clear()
            self.console_text.clear()
            self.update_status()
            
        except Exception as e:
            self.logger.error(f"Error clearing logs: {e}")
    
    def export_logs(self) -> None:
        """Log'ları dosyaya aktarır."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self, language_manager.translate("ui.console.export_logs"), f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    for entry in self.log_entries:
                        f.write(entry.formatted_message + "\n")
                
                self.logger.info(f"Logs exported to: {filename}")
                
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
    
    def update_display(self) -> None:
        """Display'i günceller."""
        try:
            # Filtrelenmiş entry'leri al
            filtered_entries = [
                entry for entry in self.log_entries
                if entry.matches_filter(
                    self.current_filters["level"],
                    self.current_filters["text"],
                    self.current_filters["source"]
                )
            ]
            
            # Mevcut text'i al
            current_text = self.console_text.toPlainText()
            
            # Yeni text oluştur
            new_text = "\n".join(entry.formatted_message for entry in filtered_entries)
            
            # Text değiştiyse güncelle
            if current_text != new_text:
                # Scroll pozisyonunu kaydet
                scrollbar = self.console_text.verticalScrollBar()
                was_at_bottom = scrollbar.value() == scrollbar.maximum()
                
                # Text'i güncelle
                self.console_text.setPlainText(new_text)
                
                # Auto scroll aktifse en alta git
                if self.auto_scroll and was_at_bottom:
                    self.console_text.moveCursor(QTextCursor.End)
                
                # Status'u güncelle
                self.update_status()
                
        except Exception as e:
            self.logger.error(f"Error updating display: {e}")
    
    def update_status(self) -> None:
        """Durum bilgilerini günceller."""
        try:
            total_entries = len(self.log_entries)
            
            # Filtrelenmiş entry sayısını hesapla
            filtered_count = len([
                entry for entry in self.log_entries
                if entry.matches_filter(
                    self.current_filters["level"],
                    self.current_filters["text"],
                    self.current_filters["source"]
                )
            ])
            
            # Etiketleri güncelle
            self.entries_label.setText(f"{language_manager.translate('ui.console.entries')}: {total_entries}")
            self.filtered_label.setText(f"{language_manager.translate('ui.console.filtered')}: {filtered_count}")
            
            # Scroll durumu
            scrollbar = self.console_text.verticalScrollBar()
            if scrollbar.maximum() > 0:
                scroll_percent = int((scrollbar.value() / scrollbar.maximum()) * 100)
                self.scroll_label.setText(f"{language_manager.translate('ui.console.scroll')}: {scroll_percent}%")
            else:
                self.scroll_label.setText(f"{language_manager.translate('ui.console.scroll')}: 0%")
                
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")
    
    def on_filter_changed(self) -> None:
        """Filtre değiştiğinde çağrılır."""
        try:
            self.current_filters = {
                "level": self.level_filter.currentText(),
                "text": self.text_filter.text(),
                "source": self.source_filter.text()
            }
            
            self.update_display()
            self.filter_changed.emit(self.current_filters)
            
        except Exception as e:
            self.logger.error(f"Error handling filter change: {e}")
    
    def on_auto_scroll_changed(self, checked: bool) -> None:
        """Auto scroll değiştiğinde çağrılır."""
        self.auto_scroll = checked
    
    def on_word_wrap_changed(self, checked: bool) -> None:
        """Word wrap değiştiğinde çağrılır."""
        self.word_wrap = checked
        self.console_text.setLineWrapMode(QTextEdit.NoWrap if not checked else QTextEdit.WidgetWidth)
    
    def on_max_entries_changed(self, value: int) -> None:
        """Max entries değiştiğinde çağrılır."""
        self.max_entries = value
        
        # Gerekirse entry'leri kırp
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries:]
            self.update_display()
    
    def on_log_selection_changed(self) -> None:
        """Log seçimi değiştiğinde çağrılır."""
        try:
            cursor = self.console_text.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
                
                # Seçilen text'ten log entry'yi bul
                for entry in self.log_entries:
                    if selected_text in entry.formatted_message:
                        self.log_selected.emit(entry)
                        break
                        
        except Exception as e:
            self.logger.error(f"Error handling log selection: {e}")
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """Widget verisini ayarlar."""
        super().set_data(data)
        
        # Log entry'leri ekle
        if "logs" in data:
            for log_data in data["logs"]:
                self.add_log_entry(
                    level=log_data.get("level", "INFO"),
                    message=log_data.get("message", ""),
                    source=log_data.get("source", ""),
                    metadata=log_data.get("metadata", {})
                )
    
    def get_filtered_logs(self) -> List[LogEntry]:
        """Filtrelenmiş log'ları döndürür."""
        return [
            entry for entry in self.log_entries
            if entry.matches_filter(
                self.current_filters["level"],
                self.current_filters["text"],
                self.current_filters["source"]
            )
        ]
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Log istatistiklerini döndürür."""
        try:
            stats = {
                "total_entries": len(self.log_entries),
                "filtered_entries": len(self.get_filtered_logs()),
                "level_counts": {},
                "source_counts": {},
                "oldest_entry": None,
                "newest_entry": None
            }
            
            if self.log_entries:
                # Level sayıları
                for entry in self.log_entries:
                    stats["level_counts"][entry.level] = stats["level_counts"].get(entry.level, 0) + 1
                    stats["source_counts"][entry.source] = stats["source_counts"].get(entry.source, 0) + 1
                
                # En eski ve en yeni entry
                stats["oldest_entry"] = self.log_entries[0].timestamp.isoformat()
                stats["newest_entry"] = self.log_entries[-1].timestamp.isoformat()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting log statistics: {e}")
            return {}
    
    def apply_style(self, style_dict: Dict[str, Any]) -> None:
        """Widget'a stil uygular."""
        super().apply_style(style_dict)
        
        # Console text'e özel stil uygula
        if "console_text" in style_dict:
            console_style = self._dict_to_stylesheet({"QTextEdit": style_dict["console_text"]})
            self.console_text.setStyleSheet(console_style)
