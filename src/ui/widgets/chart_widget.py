"""
Chart Widget module - Grafik bileşeni

Bu modül real-time grafikler için widget sağlar.
CPU, RAM, Network gibi sistem metriklerini görselleştirir.
"""

import sys
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QCheckBox, QSlider,
    QGroupBox, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

from .base_widget import BaseWidget
from ...utils.logger import logger
from ...core.language import language_manager


class ChartWidget(BaseWidget):
    """
    Grafik widget'ı - Real-time data visualization
    """
    
    # Signals
    chart_clicked = pyqtSignal(dict)  # Chart tıklandığında
    data_point_hovered = pyqtSignal(dict)  # Data point hover
    
    def __init__(self, title: str = "", chart_type: str = "line", parent=None):
        """
        Chart widget'ını başlat
        
        Args:
            title: Grafik başlığı
            chart_type: Grafik tipi (line, bar, area)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self.chart_type = chart_type
        self.data_points = []
        self.max_points = 100
        self.colors = [
            QColor(52, 152, 219),   # Blue
            QColor(231, 76, 60),    # Red  
            QColor(46, 204, 113),   # Green
            QColor(241, 196, 15),   # Yellow
            QColor(155, 89, 182),   # Purple
            QColor(230, 126, 34),   # Orange
        ]
        self.series = {}
        self.y_range = [0, 100]
        self.auto_scale = True
        self.grid_enabled = True
        self.legend_enabled = True
        
        self._setup_ui()
        self._setup_timer()
    
    def _setup_ui(self):
        """UI'yi kur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Controls
        self.auto_scale_cb = QCheckBox("Auto Scale")
        self.auto_scale_cb.setChecked(self.auto_scale)
        self.auto_scale_cb.toggled.connect(self._on_auto_scale_toggled)
        header_layout.addWidget(self.auto_scale_cb)
        
        self.grid_cb = QCheckBox("Grid")
        self.grid_cb.setChecked(self.grid_enabled)
        self.grid_cb.toggled.connect(self._on_grid_toggled)
        header_layout.addWidget(self.grid_cb)
        
        layout.addLayout(header_layout)
        
        # Chart area - Bu widget'ın kendisi chart area olarak kullanılacak
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(300, 200)
    
    def _setup_timer(self):
        """Update timer'ını kur"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(1000)  # 1 saniyede bir güncelle
    
    def add_series(self, name: str, color: QColor = None) -> None:
        """
        Yeni seri ekle
        
        Args:
            name: Seri adı
            color: Seri rengi
        """
        if color is None:
            color = self.colors[len(self.series) % len(self.colors)]
        
        self.series[name] = {
            'data': [],
            'color': color,
            'visible': True
        }
    
    def add_data_point(self, series_name: str, value: float, timestamp: datetime = None):
        """
        Data point ekle
        
        Args:
            series_name: Seri adı
            value: Değer
            timestamp: Zaman damgası
        """
        if series_name not in self.series:
            self.add_series(series_name)
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Data point ekle
        self.series[series_name]['data'].append({
            'value': value,
            'timestamp': timestamp
        })
        
        # Maksimum point sayısını kontrol et
        if len(self.series[series_name]['data']) > self.max_points:
            self.series[series_name]['data'].pop(0)
        
        # Auto scale
        if self.auto_scale:
            self._update_y_range()
        
        # Widget'ı yeniden çiz
        self.update()
    
    def clear_series(self, series_name: str = None):
        """
        Seri(leri) temizle
        
        Args:
            series_name: Temizlenecek seri adı (None ise hepsini temizle)
        """
        if series_name:
            if series_name in self.series:
                self.series[series_name]['data'].clear()
        else:
            for series in self.series.values():
                series['data'].clear()
        
        self.update()
    
    def set_y_range(self, min_val: float, max_val: float):
        """
        Y ekseni aralığını ayarla
        
        Args:
            min_val: Minimum değer
            max_val: Maksimum değer
        """
        self.y_range = [min_val, max_val]
        self.auto_scale = False
        self.auto_scale_cb.setChecked(False)
        self.update()
    
    def _update_y_range(self):
        """Y ekseni aralığını otomatik güncelle"""
        if not self.series:
            return
        
        all_values = []
        for series in self.series.values():
            if series['visible'] and series['data']:
                all_values.extend([point['value'] for point in series['data']])
        
        if all_values:
            min_val = min(all_values)
            max_val = max(all_values)
            
            # Biraz padding ekle
            padding = (max_val - min_val) * 0.1
            if padding == 0:
                padding = 1
            
            self.y_range = [min_val - padding, max_val + padding]
    
    def paintEvent(self, event):
        """Widget'ı çiz"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        # Chart area hesapla
        margin = 50
        chart_rect = self.rect().adjusted(margin, margin, -margin, -margin)
        
        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return
        
        # Grid çiz
        if self.grid_enabled:
            self._draw_grid(painter, chart_rect)
        
        # Axes çiz
        self._draw_axes(painter, chart_rect)
        
        # Data çiz
        self._draw_data(painter, chart_rect)
        
        # Legend çiz
        if self.legend_enabled:
            self._draw_legend(painter)
    
    def _draw_grid(self, painter: QPainter, chart_rect):
        """Grid çiz"""
        painter.setPen(QPen(QColor(60, 60, 60), 1, Qt.DotLine))
        
        # Vertical grid lines
        for i in range(1, 10):
            x = chart_rect.left() + (chart_rect.width() * i / 10)
            painter.drawLine(x, chart_rect.top(), x, chart_rect.bottom())
        
        # Horizontal grid lines
        for i in range(1, 10):
            y = chart_rect.top() + (chart_rect.height() * i / 10)
            painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)
    
    def _draw_axes(self, painter: QPainter, chart_rect):
        """Eksenleri çiz"""
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        
        # Y axis
        painter.drawLine(chart_rect.left(), chart_rect.top(), 
                        chart_rect.left(), chart_rect.bottom())
        
        # X axis
        painter.drawLine(chart_rect.left(), chart_rect.bottom(),
                        chart_rect.right(), chart_rect.bottom())
        
        # Y axis labels
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setFont(QFont("Arial", 8))
        
        for i in range(6):
            y = chart_rect.bottom() - (chart_rect.height() * i / 5)
            value = self.y_range[0] + (self.y_range[1] - self.y_range[0]) * i / 5
            painter.drawText(5, y + 3, f"{value:.1f}")
    
    def _draw_data(self, painter: QPainter, chart_rect):
        """Data çiz"""
        if not self.series:
            return
        
        for series_name, series in self.series.items():
            if not series['visible'] or not series['data']:
                continue
            
            points = []
            data = series['data']
            
            # Points hesapla
            for i, point in enumerate(data):
                x = chart_rect.left() + (chart_rect.width() * i / max(1, len(data) - 1))
                
                # Y değerini normalize et
                if self.y_range[1] != self.y_range[0]:
                    normalized_y = (point['value'] - self.y_range[0]) / (self.y_range[1] - self.y_range[0])
                else:
                    normalized_y = 0.5
                
                y = chart_rect.bottom() - (chart_rect.height() * normalized_y)
                points.append(QPointF(x, y))
            
            if len(points) < 2:
                continue
            
            # Çizim tipi
            if self.chart_type == "line":
                self._draw_line_series(painter, points, series['color'])
            elif self.chart_type == "area":
                self._draw_area_series(painter, points, series['color'], chart_rect)
            elif self.chart_type == "bar":
                self._draw_bar_series(painter, points, series['color'], chart_rect)
    
    def _draw_line_series(self, painter: QPainter, points: List[QPointF], color: QColor):
        """Line series çiz"""
        painter.setPen(QPen(color, 2))
        
        path = QPainterPath()
        path.moveTo(points[0])
        
        for point in points[1:]:
            path.lineTo(point)
        
        painter.drawPath(path)
        
        # Data points
        painter.setBrush(QBrush(color))
        for point in points:
            painter.drawEllipse(point, 3, 3)
    
    def _draw_area_series(self, painter: QPainter, points: List[QPointF], color: QColor, chart_rect):
        """Area series çiz"""
        if not points:
            return
        
        # Area path oluştur
        path = QPainterPath()
        path.moveTo(points[0].x(), chart_rect.bottom())
        path.lineTo(points[0])
        
        for point in points[1:]:
            path.lineTo(point)
        
        path.lineTo(points[-1].x(), chart_rect.bottom())
        path.closeSubpath()
        
        # Area fill
        area_color = QColor(color)
        area_color.setAlpha(100)
        painter.setBrush(QBrush(area_color))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawPath(path)
        
        # Line
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(Qt.NoBrush))
        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for point in points[1:]:
            line_path.lineTo(point)
        painter.drawPath(line_path)
    
    def _draw_bar_series(self, painter: QPainter, points: List[QPointF], color: QColor, chart_rect):
        """Bar series çiz"""
        if not points:
            return
        
        bar_width = chart_rect.width() / max(1, len(points)) * 0.8
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(120), 1))
        
        for point in points:
            bar_height = chart_rect.bottom() - point.y()
            bar_rect = chart_rect.__class__(
                point.x() - bar_width / 2,
                point.y(),
                bar_width,
                bar_height
            )
            painter.drawRect(bar_rect)
    
    def _draw_legend(self, painter: QPainter):
        """Legend çiz"""
        if not self.series:
            return
        
        painter.setFont(QFont("Arial", 9))
        
        legend_x = self.width() - 150
        legend_y = 30
        
        for i, (name, series) in enumerate(self.series.items()):
            if not series['visible']:
                continue
            
            y = legend_y + (i * 20)
            
            # Color box
            painter.setBrush(QBrush(series['color']))
            painter.setPen(QPen(series['color']))
            painter.drawRect(legend_x, y, 10, 10)
            
            # Text
            painter.setPen(QPen(QColor(200, 200, 200)))
            painter.drawText(legend_x + 15, y + 8, name)
    
    def _on_auto_scale_toggled(self, checked: bool):
        """Auto scale toggle"""
        self.auto_scale = checked
        if checked:
            self._update_y_range()
            self.update()
    
    def _on_grid_toggled(self, checked: bool):
        """Grid toggle"""
        self.grid_enabled = checked
        self.update()
    
    def mousePressEvent(self, event):
        """Mouse click event"""
        if event.button() == Qt.LeftButton:
            self.chart_clicked.emit({
                'x': event.x(),
                'y': event.y(),
                'widget': self
            })
        super().mousePressEvent(event)
    
    def get_widget_data(self) -> Dict[str, Any]:
        """Widget verilerini al"""
        return {
            'title': self.title,
            'chart_type': self.chart_type,
            'series_count': len(self.series),
            'total_points': sum(len(s['data']) for s in self.series.values()),
            'y_range': self.y_range,
            'auto_scale': self.auto_scale
        }