"""
Status Widget module - Durum göstergesi

Bu modül sistem durumunu gösteren widget'ı sağlar.
Online/offline durumu, bağlantı bilgileri ve durum geçişleri.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFrame, QProgressBar, QToolButton)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QFont, QPainter, QColor, QPixmap, QIcon, QLinearGradient
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import math

from .base_widget import BaseWidget
from ...core.constants import LogLevel
from ...utils.logger import logger
from ...core.language import language_manager


class StatusIndicator(QWidget):
    """
    Durum göstergesi widget'ı.
    
    Bu widget LED benzeri durum göstergesi sağlar.
    """
    
    def __init__(self, parent=None, size: int = 20):
        """
        StatusIndicator'ı başlatır.
        
        Args:
            parent: Parent widget
            size: Gösterge boyutu
        """
        super().__init__(parent)
        
        self.size = size
        self.status = "offline"  # offline, online, warning, error
        self.blink_enabled = False
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.toggle_blink)
        self.blink_state = False
        
        # Boyut ayarla
        self.setFixedSize(size, size)
        
        # Renkler
        self.colors = {
            "offline": QColor(150, 150, 150),
            "online": QColor(76, 175, 80),
            "warning": QColor(255, 152, 0),
            "error": QColor(244, 67, 54)
        }
    
    def set_status(self, status: str, blink: bool = False):
        """
        Durumu ayarlar.
        
        Args:
            status: Durum (offline, online, warning, error)
            blink: Yanıp sönme aktif mi
        """
        self.status = status
        self.blink_enabled = blink
        
        if blink:
            self.blink_timer.start(500)  # 500ms interval
        else:
            self.blink_timer.stop()
            self.blink_state = False
        
        self.update()
    
    def toggle_blink(self):
        """Yanıp sönme durumunu değiştirir."""
        self.blink_state = not self.blink_state
        self.update()
    
    def paintEvent(self, event):
        """Göstergeyi çizer."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Merkez noktası
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(center_x, center_y) - 2
        
        # Renk belirle
        color = self.colors.get(self.status, self.colors["offline"])
        
        # Yanıp sönme efekti
        if self.blink_enabled and self.blink_state:
            color = color.lighter(200)
        
        # Gradient
        gradient = QLinearGradient(center_x - radius, center_y - radius,
                                 center_x + radius, center_y + radius)
        gradient.setColorAt(0, color.lighter(150))
        gradient.setColorAt(1, color.darker(150))
        
        # Dış halka (gölge efekti)
        painter.setBrush(QColor(0, 0, 0, 50))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - radius - 1, center_y - radius - 1,
                          radius * 2 + 2, radius * 2 + 2)
        
        # Ana daire
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - radius, center_y - radius,
                          radius * 2, radius * 2)
        
        # İç parlaklık
        inner_radius = radius * 0.6
        inner_gradient = QLinearGradient(center_x - inner_radius, center_y - inner_radius,
                                       center_x + inner_radius, center_y + inner_radius)
        inner_gradient.setColorAt(0, QColor(255, 255, 255, 100))
        inner_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(inner_gradient)
        painter.drawEllipse(center_x - inner_radius, center_y - inner_radius,
                          inner_radius * 2, inner_radius * 2)


class ConnectionInfo(QFrame):
    """
    Bağlantı bilgileri widget'ı.
    
    Bu widget server bağlantı bilgilerini gösterir.
    """
    
    def __init__(self, parent=None):
        """
        ConnectionInfo'yu başlatır.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setStyleSheet("""
            ConnectionInfo {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)
        
        # Başlık
        self.title_label = QLabel("Connection Info")
        self.title_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        layout.addWidget(self.title_label)
        
        # Bilgi etiketleri
        self.host_label = QLabel("Host: -")
        self.host_label.setFont(QFont("Segoe UI", 8))
        self.host_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.host_label)
        
        self.port_label = QLabel("Port: -")
        self.port_label.setFont(QFont("Segoe UI", 8))
        self.port_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.port_label)
        
        self.protocol_label = QLabel("Protocol: -")
        self.protocol_label.setFont(QFont("Segoe UI", 8))
        self.protocol_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.protocol_label)
        
        self.ssl_label = QLabel("SSL: -")
        self.ssl_label.setFont(QFont("Segoe UI", 8))
        self.ssl_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.ssl_label)
    
    def update_info(self, host: str = "", port: int = 0, protocol: str = "HTTP", ssl: bool = False):
        """
        Bağlantı bilgilerini günceller.
        
        Args:
            host: Host adresi
            port: Port numarası
            protocol: Protokol
            ssl: SSL aktif mi
        """
        self.host_label.setText(f"Host: {host or '-'}")
        self.port_label.setText(f"Port: {port or '-'}")
        self.protocol_label.setText(f"Protocol: {protocol}")
        self.ssl_label.setText(f"SSL: {'Yes' if ssl else 'No'}")


class StatusWidget(BaseWidget):
    """
    Durum widget'ı.
    
    Bu widget sistem durumunu ve bağlantı bilgilerini gösterir.
    """
    
    # Signals
    status_changed = pyqtSignal(str)  # Durum değiştiğinde
    action_requested = pyqtSignal(str)  # Aksiyon istendiğinde
    
    def __init__(self, parent=None, widget_id: str = "status_widget"):
        """
        StatusWidget'ı başlatır.
        
        Args:
            parent: Parent widget
            widget_id: Widget ID'si
        """
        super().__init__(parent, widget_id)
        
        # Durum bilgileri
        self.current_status = "offline"
        self.connection_info = {}
        self.uptime = None
        self.last_check = None
        
        # UI bileşenleri
        self.setup_ui()
        self.setup_connections()
        
        # Timer'lar
        self.uptime_timer = QTimer()
        self.uptime_timer.timeout.connect(self.update_uptime)
        
        self.logger.debug(f"StatusWidget initialized: {self.widget_id}")
    
    def setup_ui(self):
        """UI bileşenlerini oluşturur."""
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Başlık
        self.title_label = QLabel("Server Status")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        main_layout.addWidget(self.title_label)
        
        # Durum göstergesi ve bilgiler
        status_layout = QHBoxLayout()
        status_layout.setSpacing(15)
        
        # Sol taraf - Durum göstergesi ve metin
        left_layout = QVBoxLayout()
        left_layout.setSpacing(5)
        
        # Durum göstergesi
        indicator_layout = QHBoxLayout()
        indicator_layout.setSpacing(10)
        
        self.status_indicator = StatusIndicator(size=30)
        indicator_layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel("Offline")
        self.status_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.status_label.setStyleSheet("color: #888888;")
        indicator_layout.addWidget(self.status_label)
        
        indicator_layout.addStretch()
        left_layout.addLayout(indicator_layout)
        
        # Uptime
        self.uptime_label = QLabel("Uptime: -")
        self.uptime_label.setFont(QFont("Segoe UI", 9))
        self.uptime_label.setStyleSheet("color: #cccccc;")
        left_layout.addWidget(self.uptime_label)
        
        # Son kontrol
        self.last_check_label = QLabel("Last Check: -")
        self.last_check_label.setFont(QFont("Segoe UI", 9))
        self.last_check_label.setStyleSheet("color: #cccccc;")
        left_layout.addWidget(self.last_check_label)
        
        status_layout.addLayout(left_layout)
        
        # Sağ taraf - Bağlantı bilgileri
        self.connection_info = ConnectionInfo()
        status_layout.addWidget(self.connection_info)
        
        main_layout.addLayout(status_layout)
        
        # Kontrol butonları
        self.setup_control_buttons(main_layout)
        
        # Progress bar (bağlantı durumu için)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 0.1);
                text-align: center;
                color: white;
                font-size: 9px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #8BC34A);
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        main_layout.addStretch()
    
    def setup_control_buttons(self, parent_layout):
        """Kontrol butonlarını oluşturur."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Start butonu
        self.start_button = QPushButton("Start Server")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        button_layout.addWidget(self.start_button)
        
        # Stop butonu
        self.stop_button = QPushButton("Stop Server")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c1170a;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        button_layout.addWidget(self.stop_button)
        
        # Restart butonu
        self.restart_button = QPushButton("Restart")
        self.restart_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:pressed {
                background-color: #cc7700;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        button_layout.addWidget(self.restart_button)
        
        # Refresh butonu
        self.refresh_button = QToolButton()
        self.refresh_button.setText("↻")
        self.refresh_button.setToolTip("Refresh Status")
        self.refresh_button.setStyleSheet("""
            QToolButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #1976D2;
            }
            QToolButton:pressed {
                background-color: #1565C0;
            }
        """)
        button_layout.addWidget(self.refresh_button)
        
        button_layout.addStretch()
        parent_layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Bağlantıları kurar."""
        self.start_button.clicked.connect(lambda: self.action_requested.emit("start"))
        self.stop_button.clicked.connect(lambda: self.action_requested.emit("stop"))
        self.restart_button.clicked.connect(lambda: self.action_requested.emit("restart"))
        self.refresh_button.clicked.connect(lambda: self.action_requested.emit("refresh"))
    
    def set_status(self, status: str, message: str = None, blink: bool = False):
        """
        Durumu ayarlar.
        
        Args:
            status: Durum (offline, online, warning, error)
            message: Durum mesajı
            blink: Yanıp sönme aktif mi
        """
        try:
            old_status = self.current_status
            self.current_status = status
            
            # Durum göstergesini güncelle
            self.status_indicator.set_status(status, blink)
            
            # Durum metnini güncelle
            status_texts = {
                "offline": "Offline",
                "online": "Online",
                "warning": "Warning",
                "error": "Error"
            }
            
            self.status_label.setText(status_texts.get(status, status.title()))
            
            # Renk güncelle
            colors = {
                "offline": "#888888",
                "online": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336"
            }
            
            self.status_label.setStyleSheet(f"color: {colors.get(status, '#888888')};")
            
            # Buton durumlarını güncelle
            self.update_button_states(status)
            
            # Durum değiştiyse signal gönder
            if old_status != status:
                self.status_changed.emit(status)
                self.logger.info(f"Status changed: {old_status} -> {status}")
            
        except Exception as e:
            self.logger.error(f"Error setting status: {e}")
    
    def update_button_states(self, status: str):
        """Buton durumlarını günceller."""
        try:
            if status == "online":
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.restart_button.setEnabled(True)
            elif status == "offline":
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.restart_button.setEnabled(False)
            else:  # warning, error
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(True)
                self.restart_button.setEnabled(True)
                
        except Exception as e:
            self.logger.error(f"Error updating button states: {e}")
    
    def set_connection_info(self, host: str = "", port: int = 0, 
                           protocol: str = "HTTP", ssl: bool = False):
        """
        Bağlantı bilgilerini ayarlar.
        
        Args:
            host: Host adresi
            port: Port numarası
            protocol: Protokol
            ssl: SSL aktif mi
        """
        try:
            self.connection_info.update_info(host, port, protocol, ssl)
            self.connection_info_data = {
                "host": host,
                "port": port,
                "protocol": protocol,
                "ssl": ssl
            }
            
        except Exception as e:
            self.logger.error(f"Error setting connection info: {e}")
    
    def set_uptime(self, uptime_seconds: int):
        """
        Uptime'ı ayarlar.
        
        Args:
            uptime_seconds: Uptime saniye cinsinden
        """
        try:
            self.uptime = uptime_seconds
            self.uptime_timer.start(1000)  # Her saniye güncelle
            self.update_uptime()
            
        except Exception as e:
            self.logger.error(f"Error setting uptime: {e}")
    
    def update_uptime(self):
        """Uptime'ı günceller."""
        try:
            if self.uptime is not None:
                self.uptime += 1
                
                # Uptime'ı formatla
                hours = self.uptime // 3600
                minutes = (self.uptime % 3600) // 60
                seconds = self.uptime % 60
                
                if hours > 0:
                    uptime_text = f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    uptime_text = f"Uptime: {minutes:02d}:{seconds:02d}"
                
                self.uptime_label.setText(uptime_text)
                
        except Exception as e:
            self.logger.error(f"Error updating uptime: {e}")
    
    def set_last_check(self, timestamp: datetime = None):
        """
        Son kontrol zamanını ayarlar.
        
        Args:
            timestamp: Zaman damgası
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            self.last_check = timestamp
            time_str = timestamp.strftime("%H:%M:%S")
            self.last_check_label.setText(f"Last Check: {time_str}")
            
        except Exception as e:
            self.logger.error(f"Error setting last check: {e}")
    
    def show_progress(self, message: str = "Processing..."):
        """
        Progress bar gösterir.
        
        Args:
            message: Progress mesajı
        """
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.progress_bar.setFormat(message)
            
        except Exception as e:
            self.logger.error(f"Error showing progress: {e}")
    
    def hide_progress(self):
        """Progress bar'ı gizler."""
        try:
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.logger.error(f"Error hiding progress: {e}")
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """Widget verisini ayarlar."""
        super().set_data(data)
        
        # Durum bilgilerini güncelle
        if "status" in data:
            self.set_status(
                data["status"],
                data.get("message"),
                data.get("blink", False)
            )
        
        if "connection" in data:
            conn = data["connection"]
            self.set_connection_info(
                conn.get("host", ""),
                conn.get("port", 0),
                conn.get("protocol", "HTTP"),
                conn.get("ssl", False)
            )
        
        if "uptime" in data:
            self.set_uptime(data["uptime"])
        
        if "last_check" in data:
            self.set_last_check(data["last_check"])
    
    def get_status_info(self) -> Dict[str, Any]:
        """Durum bilgilerini döndürür."""
        try:
            return {
                "status": self.current_status,
                "uptime": self.uptime,
                "last_check": self.last_check.isoformat() if self.last_check else None,
                "connection": getattr(self, 'connection_info_data', {}),
                "button_states": {
                    "start_enabled": self.start_button.isEnabled(),
                    "stop_enabled": self.stop_button.isEnabled(),
                    "restart_enabled": self.restart_button.isEnabled()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting status info: {e}")
            return {}
