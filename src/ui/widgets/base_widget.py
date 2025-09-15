"""
Base Widget module - Temel widget sınıfı

Bu modül tüm özel widget'lar için temel sınıfı sağlar.
Ortak özellikler, event handling ve styling.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QThread, QObject
from PyQt5.QtGui import QFont, QPalette, QColor
from typing import Any, Dict, Optional, List
import json

from ...core.constants import LogLevel
from ...utils.logger import logger
from ...core.language import language_manager


class BaseWidgetWorker(QObject):
    """
    Base widget worker that runs in a separate thread.
    """
    
    # Signals for GUI communication
    data_ready = pyqtSignal(dict)      # Data ready for display
    error_occurred = pyqtSignal(str)   # Error occurred
    status_updated = pyqtSignal(str)   # Status update
    
    def __init__(self, widget_id: str):
        super().__init__()
        self.widget_id = widget_id
        self.logger = logger
        self.running = False
    
    def start_worker(self):
        """Start the worker."""
        self.running = True
        self.logger.info(f"BaseWidgetWorker started for {self.widget_id}")
    
    def stop_worker(self):
        """Stop the worker."""
        self.running = False
        self.logger.info(f"BaseWidgetWorker stopped for {self.widget_id}")
    
    def refresh_data(self):
        """Refresh data in background thread."""
        try:
            if not self.running:
                return
            
            # This method should be overridden by subclasses
            self._do_refresh_data()
            
        except Exception as e:
            self.logger.error(f"Error refreshing data for {self.widget_id}: {e}")
            self.error_occurred.emit(str(e))
    
    def _do_refresh_data(self):
        """Override this method in subclasses to implement data refresh."""
        # Default implementation - emit empty data
        self.data_ready.emit({})


class BaseWidget(QWidget):
    """
    Tüm özel widget'lar için temel sınıf.
    
    Bu sınıf ortak özellikler, event handling ve styling sağlar.
    """
    
    # Signals
    data_changed = pyqtSignal(dict)  # Veri değiştiğinde
    action_triggered = pyqtSignal(str, dict)  # Aksiyon tetiklendiğinde
    error_occurred = pyqtSignal(str)  # Hata oluştuğunda
    
    def __init__(self, parent=None, widget_id: str = None):
        """
        BaseWidget'ı başlatır.
        
        Args:
            parent: Parent widget
            widget_id: Widget ID'si
        """
        super().__init__(parent)
        
        self.logger = logger
        self.widget_id = widget_id or self.__class__.__name__
        self.data = {}
        self.settings = {}
        self.animations = {}
        
        # Widget özellikleri
        self.setObjectName(self.widget_id)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Thread and worker for data operations
        self.worker_thread = None
        self.worker = None
        
        # Reduced timer usage - only for UI updates
        self.refresh_timer = None
        
        # Styling
        self.apply_default_style()
        
        # Event handling
        self.setup_connections()
        
        # Initialize worker thread
        self._init_worker_thread()
        
        self.logger.debug(f"BaseWidget initialized: {self.widget_id}")
    
    def _init_worker_thread(self):
        """Initialize the worker thread."""
        try:
            # Create thread and worker
            self.worker_thread = QThread()
            self.worker = self._create_worker()
            
            # Move worker to thread
            self.worker.moveToThread(self.worker_thread)
            
            # Connect signals
            self.worker.data_ready.connect(self._on_data_ready)
            self.worker.error_occurred.connect(self._on_worker_error)
            self.worker.status_updated.connect(self._on_status_updated)
            
            # Connect thread finished signal
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            
            # Start thread
            self.worker_thread.start()
            
            # Start worker
            self.worker.start_worker()
            
            self.logger.debug(f"Worker thread initialized for {self.widget_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize worker thread for {self.widget_id}: {e}")
    
    def _create_worker(self) -> BaseWidgetWorker:
        """Create worker instance. Override in subclasses."""
        return BaseWidgetWorker(self.widget_id)
    
    def _on_data_ready(self, data: dict):
        """Handle data ready from worker thread."""
        try:
            self._process_data(data)
            self.data_changed.emit(data)
        except Exception as e:
            self.logger.error(f"Error processing data for {self.widget_id}: {e}")
    
    def _on_worker_error(self, error_message: str):
        """Handle error from worker thread."""
        try:
            self.show_error(error_message)
        except Exception as e:
            self.logger.error(f"Error handling worker error for {self.widget_id}: {e}")
    
    def _on_status_updated(self, status_message: str):
        """Handle status update from worker thread."""
        try:
            self.logger.debug(f"Status update for {self.widget_id}: {status_message}")
        except Exception as e:
            self.logger.error(f"Error handling status update for {self.widget_id}: {e}")
    
    def _process_data(self, data: dict):
        """Process data from worker thread. Override in subclasses."""
        pass
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """
        Widget verisini ayarlar.
        
        Args:
            data: Widget verisi
        """
        try:
            old_data = self.data.copy()
            self.data.update(data)
            
            # Veri değişikliğini işle
            self.on_data_changed(old_data, self.data)
            
            # Signal gönder
            self.data_changed.emit(self.data)
            
        except Exception as e:
            self.logger.error(f"Error setting data for {self.widget_id}: {e}")
            self.error_occurred.emit(str(e))
    
    def get_data(self) -> Dict[str, Any]:
        """
        Widget verisini döndürür.
        
        Returns:
            Widget verisi
        """
        return self.data.copy()
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        Widget ayarını ayarlar.
        
        Args:
            key: Ayar anahtarı
            value: Ayar değeri
        """
        try:
            self.settings[key] = value
            self.on_setting_changed(key, value)
            
        except Exception as e:
            self.logger.error(f"Error setting {key} for {self.widget_id}: {e}")
            self.error_occurred.emit(str(e))
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Widget ayarını döndürür.
        
        Args:
            key: Ayar anahtarı
            default: Varsayılan değer
            
        Returns:
            Ayar değeri
        """
        return self.settings.get(key, default)
    
    def start_auto_refresh(self, interval_ms: int = 5000) -> None:
        """
        Otomatik yenileme başlatır (reduced usage).
        
        Args:
            interval_ms: Yenileme aralığı (milisaniye)
        """
        try:
            if not self.refresh_timer:
                self.refresh_timer = QTimer()
                self.refresh_timer.timeout.connect(self._request_data_refresh)
            
            self.refresh_timer.setInterval(interval_ms)
            self.refresh_timer.start()
            self.logger.debug(f"Auto refresh started for {self.widget_id}: {interval_ms}ms")
            
        except Exception as e:
            self.logger.error(f"Error starting auto refresh for {self.widget_id}: {e}")
    
    def stop_auto_refresh(self) -> None:
        """Otomatik yenilemeyi durdurur."""
        try:
            self.refresh_timer.stop()
            self.logger.debug(f"Auto refresh stopped for {self.widget_id}")
            
        except Exception as e:
            self.logger.error(f"Error stopping auto refresh for {self.widget_id}: {e}")
    
    def _request_data_refresh(self):
        """Request data refresh from worker thread (non-blocking)."""
        try:
            if self.worker:
                self.worker.refresh_data()
            else:
                self.logger.warning(f"No worker available for {self.widget_id}")
        except Exception as e:
            self.logger.error(f"Error requesting data refresh for {self.widget_id}: {e}")
    
    def refresh_data(self) -> None:
        """Veriyi yeniler (non-blocking)."""
        try:
            self._request_data_refresh()
            
        except Exception as e:
            self.logger.error(f"Error refreshing data for {self.widget_id}: {e}")
            self.error_occurred.emit(str(e))
    
    def show_loading(self, message: str = "Yükleniyor...") -> None:
        """
        Loading durumunu gösterir.
        
        Args:
            message: Loading mesajı
        """
        try:
            self.on_show_loading(message)
            
        except Exception as e:
            self.logger.error(f"Error showing loading for {self.widget_id}: {e}")
    
    def hide_loading(self) -> None:
        """Loading durumunu gizler."""
        try:
            self.on_hide_loading()
            
        except Exception as e:
            self.logger.error(f"Error hiding loading for {self.widget_id}: {e}")
    
    def show_error(self, message: str) -> None:
        """
        Hata mesajını gösterir.
        
        Args:
            message: Hata mesajı
        """
        try:
            self.on_show_error(message)
            self.error_occurred.emit(message)
            
        except Exception as e:
            self.logger.error(f"Error showing error for {self.widget_id}: {e}")
    
    def clear_error(self) -> None:
        """Hata mesajını temizler."""
        try:
            self.on_clear_error()
            
        except Exception as e:
            self.logger.error(f"Error clearing error for {self.widget_id}: {e}")
    
    def animate_property(self, property_name: str, start_value: Any, 
                        end_value: Any, duration: int = 300) -> None:
        """
        Widget özelliğini animasyonla değiştirir.
        
        Args:
            property_name: Animasyon yapılacak özellik
            start_value: Başlangıç değeri
            end_value: Bitiş değeri
            duration: Animasyon süresi (ms)
        """
        try:
            # Mevcut animasyonu durdur
            if property_name in self.animations:
                self.animations[property_name].stop()
            
            # Yeni animasyon oluştur
            animation = QPropertyAnimation(self, property_name.encode())
            animation.setDuration(duration)
            animation.setStartValue(start_value)
            animation.setEndValue(end_value)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            
            # Animasyonu kaydet ve başlat
            self.animations[property_name] = animation
            animation.start()
            
        except Exception as e:
            self.logger.error(f"Error animating property {property_name} for {self.widget_id}: {e}")
    
    def apply_style(self, style_dict: Dict[str, Any]) -> None:
        """
        Widget'a stil uygular.
        
        Args:
            style_dict: Stil dictionary'si
        """
        try:
            style_sheet = self._dict_to_stylesheet(style_dict)
            self.setStyleSheet(style_sheet)
            
        except Exception as e:
            self.logger.error(f"Error applying style to {self.widget_id}: {e}")
    
    def export_config(self) -> Dict[str, Any]:
        """
        Widget konfigürasyonunu dışa aktarır.
        
        Returns:
            Konfigürasyon dictionary'si
        """
        try:
            return {
                "widget_id": self.widget_id,
                "class_name": self.__class__.__name__,
                "data": self.data.copy(),
                "settings": self.settings.copy(),
                "geometry": {
                    "x": self.x(),
                    "y": self.y(),
                    "width": self.width(),
                    "height": self.height()
                },
                "visible": self.isVisible(),
                "enabled": self.isEnabled()
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting config for {self.widget_id}: {e}")
            return {}
    
    def import_config(self, config: Dict[str, Any]) -> bool:
        """
        Widget konfigürasyonunu içe aktarır.
        
        Args:
            config: Konfigürasyon dictionary'si
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Veri ve ayarları yükle
            if "data" in config:
                self.set_data(config["data"])
            
            if "settings" in config:
                for key, value in config["settings"].items():
                    self.set_setting(key, value)
            
            # Geometri ayarla
            if "geometry" in config:
                geom = config["geometry"]
                self.setGeometry(geom.get("x", 0), geom.get("y", 0),
                               geom.get("width", 100), geom.get("height", 100))
            
            # Görünürlük ve etkinlik
            if "visible" in config:
                self.setVisible(config["visible"])
            
            if "enabled" in config:
                self.setEnabled(config["enabled"])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing config for {self.widget_id}: {e}")
            return False
    
    def setup_connections(self) -> None:
        """Widget bağlantılarını kurar."""
        pass
    
    def apply_default_style(self) -> None:
        """Varsayılan stili uygular."""
        default_style = {
            "QWidget": {
                "background-color": "transparent",
                "color": "white",
                "font-family": "Segoe UI, Arial, sans-serif",
                "font-size": "9pt"
            }
        }
        self.apply_style(default_style)
    
    def on_data_changed(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> None:
        """
        Veri değiştiğinde çağrılır.
        
        Args:
            old_data: Eski veri
            new_data: Yeni veri
        """
        pass
    
    def on_setting_changed(self, key: str, value: Any) -> None:
        """
        Ayar değiştiğinde çağrılır.
        
        Args:
            key: Ayar anahtarı
            value: Yeni değer
        """
        pass
    
    def on_refresh(self) -> None:
        """Veri yenilendiğinde çağrılır."""
        pass
    
    def on_show_loading(self, message: str) -> None:
        """
        Loading gösterildiğinde çağrılır.
        
        Args:
            message: Loading mesajı
        """
        pass
    
    def on_hide_loading(self) -> None:
        """Loading gizlendiğinde çağrılır."""
        pass
    
    def on_show_error(self, message: str) -> None:
        """
        Hata gösterildiğinde çağrılır.
        
        Args:
            message: Hata mesajı
        """
        pass
    
    def on_clear_error(self) -> None:
        """Hata temizlendiğinde çağrılır."""
        pass
    
    def _dict_to_stylesheet(self, style_dict: Dict[str, Any]) -> str:
        """
        Dictionary'yi CSS stylesheet'e çevirir.
        
        Args:
            style_dict: Stil dictionary'si
            
        Returns:
            CSS stylesheet string
        """
        try:
            stylesheet_parts = []
            
            for selector, properties in style_dict.items():
                if isinstance(properties, dict):
                    property_parts = []
                    for prop, value in properties.items():
                        # CSS property'lerini formatla
                        css_prop = prop.replace('_', '-')
                        property_parts.append(f"    {css_prop}: {value};")
                    
                    if property_parts:
                        stylesheet_parts.append(f"{selector} {{\n" + "\n".join(property_parts) + "\n}")
            
            return "\n\n".join(stylesheet_parts)
            
        except Exception as e:
            self.logger.error(f"Error converting style dict to stylesheet: {e}")
            return ""
    
    def closeEvent(self, event) -> None:
        """Widget kapatılırken çağrılır."""
        try:
            # Stop worker
            if self.worker:
                self.worker.stop_worker()
            
            # Stop thread
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.quit()
                self.worker_thread.wait(3000)  # Wait up to 3 seconds
            
            # Timer'ları durdur
            self.stop_auto_refresh()
            
            # Animasyonları durdur
            for animation in self.animations.values():
                animation.stop()
            
            self.logger.debug(f"BaseWidget closed: {self.widget_id}")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Error in closeEvent for {self.widget_id}: {e}")
            event.accept()


class BaseContainerWidget(BaseWidget):
    """
    Container widget'lar için temel sınıf.
    
    Bu sınıf child widget'ları yöneten container'lar için kullanılır.
    """
    
    def __init__(self, parent=None, widget_id: str = None):
        """
        BaseContainerWidget'ı başlatır.
        
        Args:
            parent: Parent widget
            widget_id: Widget ID'si
        """
        super().__init__(parent, widget_id)
        
        self.child_widgets = {}
        self.layout_type = "vertical"  # vertical, horizontal, grid
        
        # Layout'u ayarla
        self.setup_layout()
    
    def add_widget(self, widget: QWidget, widget_id: str = None, 
                   position: int = None) -> str:
        """
        Child widget ekler.
        
        Args:
            widget: Eklenecek widget
            widget_id: Widget ID'si
            position: Pozisyon (None ise sona ekler)
            
        Returns:
            Widget ID'si
        """
        try:
            if not widget_id:
                widget_id = f"widget_{len(self.child_widgets)}"
            
            # Widget'ı kaydet
            self.child_widgets[widget_id] = widget
            
            # Layout'a ekle
            if position is not None:
                self.main_layout.insertWidget(position, widget)
            else:
                self.main_layout.addWidget(widget)
            
            self.logger.debug(f"Widget added to {self.widget_id}: {widget_id}")
            return widget_id
            
        except Exception as e:
            self.logger.error(f"Error adding widget to {self.widget_id}: {e}")
            return None
    
    def remove_widget(self, widget_id: str) -> bool:
        """
        Child widget kaldırır.
        
        Args:
            widget_id: Kaldırılacak widget ID'si
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if widget_id in self.child_widgets:
                widget = self.child_widgets[widget_id]
                self.main_layout.removeWidget(widget)
                widget.deleteLater()
                del self.child_widgets[widget_id]
                
                self.logger.debug(f"Widget removed from {self.widget_id}: {widget_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing widget from {self.widget_id}: {e}")
            return False
    
    def get_widget(self, widget_id: str) -> Optional[QWidget]:
        """
        Child widget döndürür.
        
        Args:
            widget_id: Widget ID'si
            
        Returns:
            Widget veya None
        """
        return self.child_widgets.get(widget_id)
    
    def clear_widgets(self) -> None:
        """Tüm child widget'ları temizler."""
        try:
            for widget_id in list(self.child_widgets.keys()):
                self.remove_widget(widget_id)
                
        except Exception as e:
            self.logger.error(f"Error clearing widgets from {self.widget_id}: {e}")
    
    def setup_layout(self) -> None:
        """Layout'u ayarlar."""
        if self.layout_type == "horizontal":
            self.main_layout = QHBoxLayout(self)
        elif self.layout_type == "grid":
            self.main_layout = QGridLayout(self)
        else:  # vertical
            self.main_layout = QVBoxLayout(self)
        
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
    
    def export_config(self) -> Dict[str, Any]:
        """Container konfigürasyonunu dışa aktarır."""
        config = super().export_config()
        config["child_widgets"] = {}
        
        for widget_id, widget in self.child_widgets.items():
            if hasattr(widget, 'export_config'):
                config["child_widgets"][widget_id] = widget.export_config()
        
        return config
    
    def import_config(self, config: Dict[str, Any]) -> bool:
        """Container konfigürasyonunu içe aktarır."""
        success = super().import_config(config)
        
        if success and "child_widgets" in config:
            for widget_id, widget_config in config["child_widgets"].items():
                # Child widget'ı yeniden oluştur (bu implementasyon child class'larda yapılmalı)
                pass
        
        return success
