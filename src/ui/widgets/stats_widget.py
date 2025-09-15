"""
Stats Widget module - İstatistik kartları

Bu modül sistem istatistiklerini gösteren kart widget'larını sağlar.
Real-time metrikler, grafikler ve trend göstergeleri.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QProgressBar, QFrame, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPainter, QColor, QLinearGradient, QPen
from typing import Dict, Any, List, Optional, Tuple
import math
from datetime import datetime, timedelta

from .base_widget import BaseWidget
from ...core.constants import LogLevel
from ...utils.logger import logger
from ...core.language import language_manager


class StatCard(QFrame):
    """
    İstatistik kartı widget'ı.
    
    Bu widget tek bir metrik için kart görünümü sağlar.
    """
    
    # Signals
    clicked = pyqtSignal()
    
    def __init__(self, title: str = "", value: str = "", unit: str = "", 
                 trend: float = 0.0, parent=None):
        """
        StatCard'ı başlatır.
        
        Args:
            title: Kart başlığı
            value: Değer
            unit: Birim
            trend: Trend değeri (yüzde)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self.value = value
        self.unit = unit
        self.trend = trend
        self.color = QColor(100, 200, 255)  # Varsayılan mavi
        self.animated_value = 0.0
        
        # UI ayarları
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(120)
        self.setMaximumHeight(150)
        
        # Layout
        self.setup_ui()
        self.setup_style()
        
        # Animasyon
        self.animation = QPropertyAnimation(self, b"animatedValue")
        self.animation.setDuration(1000)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def setup_ui(self):
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        # Başlık
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Segoe UI", 9))
        self.title_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.title_label)
        
        # Değer ve birim
        value_layout = QHBoxLayout()
        value_layout.setContentsMargins(0, 0, 0, 0)
        value_layout.setSpacing(5)
        
        self.value_label = QLabel(self.value)
        self.value_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.value_label.setStyleSheet("color: white;")
        value_layout.addWidget(self.value_label)
        
        if self.unit:
            self.unit_label = QLabel(self.unit)
            self.unit_label.setFont(QFont("Segoe UI", 10))
            self.unit_label.setStyleSheet("color: #888888;")
            value_layout.addWidget(self.unit_label)
        
        value_layout.addStretch()
        layout.addLayout(value_layout)
        
        # Trend
        if self.trend != 0:
            self.trend_label = QLabel()
            self.update_trend_display()
            self.trend_label.setFont(QFont("Segoe UI", 8))
            layout.addWidget(self.trend_label)
        
        layout.addStretch()
    
    def setup_style(self):
        """Stili ayarlar."""
        self.setStyleSheet(f"""
            StatCard {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }}
            StatCard:hover {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        """)
    
    def update_trend_display(self):
        """Trend görünümünü günceller."""
        if not hasattr(self, 'trend_label'):
            return
        
        if self.trend > 0:
            self.trend_label.setText(f"↗ +{self.trend:.1f}%")
            self.trend_label.setStyleSheet("color: #4CAF50;")
        elif self.trend < 0:
            self.trend_label.setText(f"↘ {self.trend:.1f}%")
            self.trend_label.setStyleSheet("color: #F44336;")
        else:
            self.trend_label.setText("→ 0.0%")
            self.trend_label.setStyleSheet("color: #888888;")
    
    def set_value(self, value: str, animate: bool = True):
        """
        Değeri günceller.
        
        Args:
            value: Yeni değer
            animate: Animasyon kullan
        """
        self.value = value
        self.value_label.setText(value)
        
        if animate and value.replace('.', '').replace(',', '').isdigit():
            try:
                new_value = float(value.replace(',', '.'))
                self.animation.setStartValue(self.animated_value)
                self.animation.setEndValue(new_value)
                self.animation.start()
            except ValueError:
                pass
    
    def set_trend(self, trend: float):
        """
        Trend değerini günceller.
        
        Args:
            trend: Trend değeri
        """
        self.trend = trend
        self.update_trend_display()
    
    def set_color(self, color: QColor):
        """
        Kart rengini ayarlar.
        
        Args:
            color: Renk
        """
        self.color = color
        self.update()
    
    def get_animated_value(self) -> float:
        """Animasyonlu değeri döndürür."""
        return self.animated_value
    
    def set_animated_value(self, value: float):
        """Animasyonlu değeri ayarlar."""
        self.animated_value = value
        self.update()
    
    def mousePressEvent(self, event):
        """Mouse tıklamasını handle eder."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def paintEvent(self, event):
        """Özel çizim yapar."""
        super().paintEvent(event)
        
        # Sol kenarda renkli çizgi çiz
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Gradient çizgi
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, self.color)
        gradient.setColorAt(1, self.color.lighter(150))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 4, self.height(), 2, 2)


class ProgressStatCard(StatCard):
    """
    Progress bar'lı istatistik kartı.
    
    Bu kart progress bar ile değer gösterir.
    """
    
    def __init__(self, title: str = "", value: float = 0.0, max_value: float = 100.0,
                 unit: str = "%", parent=None):
        """
        ProgressStatCard'ı başlatır.
        
        Args:
            title: Kart başlığı
            value: Değer
            max_value: Maksimum değer
            unit: Birim
            parent: Parent widget
        """
        self.max_value = max_value
        super().__init__(title, f"{value:.1f}", unit, parent=parent)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, int(max_value))
        self.progress_bar.setValue(int(value))
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 0.1);
                text-align: center;
                color: white;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #8BC34A);
                border-radius: 4px;
            }
        """)
        
        # Layout'a progress bar ekle
        self.layout().insertWidget(-1, self.progress_bar)
    
    def set_value(self, value: float, animate: bool = True):
        """
        Değeri günceller.
        
        Args:
            value: Yeni değer
            animate: Animasyon kullan
        """
        super().set_value(f"{value:.1f}", animate)
        self.progress_bar.setValue(int(value))
        
        # Renk değiştir (kırmızı > sarı > yeşil)
        if value > 80:
            color = "#F44336"  # Kırmızı
        elif value > 60:
            color = "#FF9800"  # Turuncu
        else:
            color = "#4CAF50"  # Yeşil
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 0.1);
                text-align: center;
                color: white;
                font-size: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)


class StatsWidget(BaseWidget):
    """
    İstatistik widget'ı.
    
    Bu widget birden fazla istatistik kartını gösterir.
    """
    
    # Signals
    card_clicked = pyqtSignal(str, dict)  # card_id, data
    
    def __init__(self, parent=None, widget_id: str = "stats_widget"):
        """
        StatsWidget'ı başlatır.
        
        Args:
            parent: Parent widget
            widget_id: Widget ID'si
        """
        super().__init__(parent, widget_id)
        
        # Kartlar
        self.cards: Dict[str, StatCard] = {}
        self.card_layout = None
        
        # UI
        self.setup_ui()
        
        self.logger.debug(f"StatsWidget initialized: {self.widget_id}")
    
    def setup_ui(self):
        """UI bileşenlerini oluşturur."""
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Başlık
        self.title_label = QLabel("System Statistics")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.title_label.setStyleSheet("color: white; margin-bottom: 10px;")
        main_layout.addWidget(self.title_label)
        
        # Kartlar için scroll area (gerekirse)
        self.cards_widget = QWidget()
        self.card_layout = QGridLayout(self.cards_widget)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(10)
        main_layout.addWidget(self.cards_widget)
        
        main_layout.addStretch()
    
    def add_card(self, card_id: str, title: str, value: str = "", 
                 unit: str = "", trend: float = 0.0, 
                 card_type: str = "normal", **kwargs) -> StatCard:
        """
        İstatistik kartı ekler.
        
        Args:
            card_id: Kart ID'si
            title: Kart başlığı
            value: Değer
            unit: Birim
            trend: Trend değeri
            card_type: Kart tipi (normal, progress)
            **kwargs: Ek parametreler
            
        Returns:
            Oluşturulan kart
        """
        try:
            # Kart tipine göre oluştur
            if card_type == "progress":
                max_value = kwargs.get("max_value", 100.0)
                card = ProgressStatCard(title, float(value or 0), max_value, unit)
            else:
                card = StatCard(title, value, unit, trend)
            
            # Kart'ı kaydet
            self.cards[card_id] = card
            
            # Layout'a ekle
            self.add_card_to_layout(card)
            
            # Click signal'ını bağla
            card.clicked.connect(lambda: self.on_card_clicked(card_id))
            
            self.logger.debug(f"Card added: {card_id}")
            return card
            
        except Exception as e:
            self.logger.error(f"Error adding card {card_id}: {e}")
            return None
    
    def add_card_to_layout(self, card: StatCard):
        """Kart'ı layout'a ekler."""
        try:
            # Mevcut kart sayısını al
            current_count = len(self.cards)
            
            # Grid pozisyonu hesapla (3 sütun)
            row = current_count // 3
            col = current_count % 3
            
            self.card_layout.addWidget(card, row, col)
            
        except Exception as e:
            self.logger.error(f"Error adding card to layout: {e}")
    
    def remove_card(self, card_id: str) -> bool:
        """
        İstatistik kartını kaldırır.
        
        Args:
            card_id: Kart ID'si
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if card_id in self.cards:
                card = self.cards[card_id]
                self.card_layout.removeWidget(card)
                card.deleteLater()
                del self.cards[card_id]
                
                # Layout'u yeniden düzenle
                self.rearrange_cards()
                
                self.logger.debug(f"Card removed: {card_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing card {card_id}: {e}")
            return False
    
    def rearrange_cards(self):
        """Kartları yeniden düzenler."""
        try:
            # Tüm kartları kaldır
            for card in self.cards.values():
                self.card_layout.removeWidget(card)
            
            # Yeniden ekle
            for i, card in enumerate(self.cards.values()):
                row = i // 3
                col = i % 3
                self.card_layout.addWidget(card, row, col)
                
        except Exception as e:
            self.logger.error(f"Error rearranging cards: {e}")
    
    def update_card(self, card_id: str, **kwargs) -> bool:
        """
        Kart'ı günceller.
        
        Args:
            card_id: Kart ID'si
            **kwargs: Güncellenecek özellikler
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if card_id not in self.cards:
                return False
            
            card = self.cards[card_id]
            
            # Değerleri güncelle
            if "value" in kwargs:
                card.set_value(kwargs["value"])
            
            if "trend" in kwargs:
                card.set_trend(kwargs["trend"])
            
            if "title" in kwargs:
                card.title = kwargs["title"]
                card.title_label.setText(kwargs["title"])
            
            if "color" in kwargs:
                if isinstance(kwargs["color"], str):
                    color = QColor(kwargs["color"])
                else:
                    color = kwargs["color"]
                card.set_color(color)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating card {card_id}: {e}")
            return False
    
    def get_card(self, card_id: str) -> Optional[StatCard]:
        """
        Kart'ı döndürür.
        
        Args:
            card_id: Kart ID'si
            
        Returns:
            Kart veya None
        """
        return self.cards.get(card_id)
    
    def clear_cards(self):
        """Tüm kartları temizler."""
        try:
            for card_id in list(self.cards.keys()):
                self.remove_card(card_id)
                
        except Exception as e:
            self.logger.error(f"Error clearing cards: {e}")
    
    def on_card_clicked(self, card_id: str):
        """Kart tıklandığında çağrılır."""
        try:
            card = self.cards.get(card_id)
            if card:
                data = {
                    "title": card.title,
                    "value": card.value,
                    "unit": card.unit,
                    "trend": card.trend
                }
                self.card_clicked.emit(card_id, data)
                
        except Exception as e:
            self.logger.error(f"Error handling card click {card_id}: {e}")
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """Widget verisini ayarlar."""
        super().set_data(data)
        
        # Kartları güncelle
        if "cards" in data:
            for card_data in data["cards"]:
                card_id = card_data.get("id")
                if card_id:
                    if card_id in self.cards:
                        self.update_card(card_id, **card_data)
                    else:
                        self.add_card(card_id, **card_data)
    
    def get_card_statistics(self) -> Dict[str, Any]:
        """Kart istatistiklerini döndürür."""
        try:
            return {
                "total_cards": len(self.cards),
                "card_ids": list(self.cards.keys()),
                "card_data": {
                    card_id: {
                        "title": card.title,
                        "value": card.value,
                        "unit": card.unit,
                        "trend": card.trend
                    }
                    for card_id, card in self.cards.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting card statistics: {e}")
            return {}
    
    def apply_style(self, style_dict: Dict[str, Any]) -> None:
        """Widget'a stil uygular."""
        super().apply_style(style_dict)
        
        # Başlık stilini güncelle
        if "title" in style_dict:
            title_style = self._dict_to_stylesheet({"QLabel": style_dict["title"]})
            self.title_label.setStyleSheet(title_style)
        
        # Kart stillerini güncelle
        if "cards" in style_dict:
            for card in self.cards.values():
                card.apply_style(style_dict["cards"])
