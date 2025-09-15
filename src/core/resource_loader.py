"""
Resource Loader module - Kaynak yükleyici

Bu modül uygulamanın kaynaklarını (icon, image, style vb.) yönetir.
Kaynak yükleme, cache yönetimi ve kaynak erişimi işlemleri.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import threading
from PIL import Image
import base64
from io import BytesIO

from .constants import LogLevel
from ..utils.logger import logger


class ResourceType:
    """Kaynak türleri."""
    ICON = "icon"
    IMAGE = "image"
    STYLE = "style"
    LOCALE = "locale"
    CONFIG = "config"
    FONT = "font"


class ResourceLoader:
    """
    Kaynak yükleme ve yönetme sınıfı.
    
    Bu sınıf uygulamanın tüm kaynaklarını (icon, image, style vb.) yönetir.
    """
    
    def __init__(self, resource_dir: str = "data/resources"):
        """
        ResourceLoader'ı başlatır.
        
        Args:
            resource_dir: Kaynak dosyalarının bulunduğu ana dizin
        """
        self.logger = logger
        self.resource_dir = Path(resource_dir)
        
        # Kaynak cache'i
        self.cache: Dict[str, Any] = {}
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Desteklenen dosya formatları
        self.supported_formats = {
            ResourceType.ICON: ['.png', '.svg', '.ico', '.jpg', '.jpeg'],
            ResourceType.IMAGE: ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.svg'],
            ResourceType.STYLE: ['.qss', '.css'],
            ResourceType.LOCALE: ['.json'],
            ResourceType.CONFIG: ['.json', '.yaml', '.yml'],
            ResourceType.FONT: ['.ttf', '.otf', '.woff', '.woff2']
        }
        
        # Kaynak dizin yapısı
        self.resource_paths = {
            ResourceType.ICON: self.resource_dir / "icons",
            ResourceType.IMAGE: self.resource_dir / "images",
            ResourceType.STYLE: self.resource_dir / "styles",
            ResourceType.LOCALE: Path("data/locale"),
            ResourceType.CONFIG: Path("data"),
            ResourceType.FONT: self.resource_dir / "fonts"
        }
        
        # Cache istatistikleri
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "loaded_resources": 0,
            "failed_loads": 0
        }
        
        # Kaynak dizinlerini oluştur
        self._create_resource_directories()
        
        # Varsayılan kaynakları yükle
        self._load_default_resources()
    
    def load_icon(self, icon_name: str, size: tuple = None, category: str = None) -> Optional[Any]:
        """
        Icon yükler.
        
        Args:
            icon_name: Icon adı
            size: İstenilen boyut (width, height)
            category: Icon kategorisi (tabs, actions, status)
            
        Returns:
            Yüklenen icon verisi
        """
        try:
            # Cache anahtarı oluştur
            cache_key = f"icon_{category}_{icon_name}_{size}"
            
            # Cache'den kontrol et
            cached_icon = self._get_from_cache(cache_key)
            if cached_icon is not None:
                return cached_icon
            
            # Icon dosyasını bul
            icon_path = self._find_icon_file(icon_name, category)
            if not icon_path:
                self.logger.warning(f"Icon not found: {icon_name} (category: {category})")
                return None
            
            # Icon'u yükle
            icon_data = self._load_image_file(icon_path, size)
            
            # Cache'e ekle
            self._add_to_cache(cache_key, icon_data)
            
            return icon_data
            
        except Exception as e:
            self.logger.error(f"Failed to load icon '{icon_name}': {e}")
            self.stats["failed_loads"] += 1
            return None
    
    def load_image(self, image_name: str, size: tuple = None) -> Optional[Any]:
        """
        Image yükler.
        
        Args:
            image_name: Image adı
            size: İstenilen boyut (width, height)
            
        Returns:
            Yüklenen image verisi
        """
        try:
            # Cache anahtarı oluştur
            cache_key = f"image_{image_name}_{size}"
            
            # Cache'den kontrol et
            cached_image = self._get_from_cache(cache_key)
            if cached_image is not None:
                return cached_image
            
            # Image dosyasını bul
            image_path = self._find_resource_file(image_name, ResourceType.IMAGE)
            if not image_path:
                self.logger.warning(f"Image not found: {image_name}")
                return None
            
            # Image'ı yükle
            image_data = self._load_image_file(image_path, size)
            
            # Cache'e ekle
            self._add_to_cache(cache_key, image_data)
            
            return image_data
            
        except Exception as e:
            self.logger.error(f"Failed to load image '{image_name}': {e}")
            self.stats["failed_loads"] += 1
            return None
    
    def load_style(self, style_name: str, theme: str = None) -> Optional[str]:
        """
        Style dosyası yükler.
        
        Args:
            style_name: Style dosyası adı
            theme: Tema adı (dark, light, custom)
            
        Returns:
            Style içeriği
        """
        try:
            # Cache anahtarı oluştur
            cache_key = f"style_{theme}_{style_name}"
            
            # Cache'den kontrol et
            cached_style = self._get_from_cache(cache_key)
            if cached_style is not None:
                return cached_style
            
            # Style dosyasını bul
            style_path = self._find_style_file(style_name, theme)
            if not style_path:
                self.logger.warning(f"Style not found: {style_name} (theme: {theme})")
                return None
            
            # Style dosyasını oku
            with open(style_path, 'r', encoding='utf-8') as f:
                style_content = f.read()
            
            # Cache'e ekle
            self._add_to_cache(cache_key, style_content)
            
            return style_content
            
        except Exception as e:
            self.logger.error(f"Failed to load style '{style_name}': {e}")
            self.stats["failed_loads"] += 1
            return None
    
    def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Config dosyası yükler.
        
        Args:
            config_name: Config dosyası adı
            
        Returns:
            Config verisi
        """
        try:
            # Cache anahtarı oluştur
            cache_key = f"config_{config_name}"
            
            # Cache'den kontrol et
            cached_config = self._get_from_cache(cache_key)
            if cached_config is not None:
                return cached_config
            
            # Config dosyasını bul
            config_path = self._find_resource_file(config_name, ResourceType.CONFIG)
            if not config_path:
                self.logger.warning(f"Config not found: {config_name}")
                return None
            
            # Config dosyasını yükle
            config_data = self._load_json_file(config_path)
            
            # Cache'e ekle
            self._add_to_cache(cache_key, config_data)
            
            return config_data
            
        except Exception as e:
            self.logger.error(f"Failed to load config '{config_name}': {e}")
            self.stats["failed_loads"] += 1
            return None
    
    def get_resource_path(self, resource_name: str, resource_type: str) -> Optional[Path]:
        """
        Kaynak dosyasının yolunu döndürür.
        
        Args:
            resource_name: Kaynak adı
            resource_type: Kaynak türü
            
        Returns:
            Kaynak dosyasının yolu
        """
        try:
            return self._find_resource_file(resource_name, resource_type)
            
        except Exception as e:
            self.logger.error(f"Failed to get resource path for '{resource_name}': {e}")
            return None
    
    def list_resources(self, resource_type: str, category: str = None) -> List[str]:
        """
        Belirtilen türdeki kaynakları listeler.
        
        Args:
            resource_type: Kaynak türü
            category: Kategori (icon için)
            
        Returns:
            Kaynak listesi
        """
        try:
            resources = []
            
            if resource_type == ResourceType.ICON and category:
                # Icon kategorisi
                icon_dir = self.resource_paths[ResourceType.ICON] / category
                if icon_dir.exists():
                    for file_path in icon_dir.iterdir():
                        if file_path.suffix.lower() in self.supported_formats[ResourceType.ICON]:
                            resources.append(file_path.stem)
            else:
                # Diğer kaynak türleri
                resource_dir = self.resource_paths.get(resource_type)
                if resource_dir and resource_dir.exists():
                    for file_path in resource_dir.iterdir():
                        if file_path.suffix.lower() in self.supported_formats.get(resource_type, []):
                            resources.append(file_path.stem)
            
            return sorted(resources)
            
        except Exception as e:
            self.logger.error(f"Failed to list resources for type '{resource_type}': {e}")
            return []
    
    def clear_cache(self, resource_type: str = None) -> bool:
        """
        Cache'i temizler.
        
        Args:
            resource_type: Temizlenecek kaynak türü (None ise tümü)
            
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            with self.lock:
                if resource_type:
                    # Belirli türdeki kaynakları temizle
                    keys_to_remove = [
                        key for key in self.cache.keys()
                        if key.startswith(f"{resource_type}_")
                    ]
                    for key in keys_to_remove:
                        del self.cache[key]
                else:
                    # Tüm cache'i temizle
                    self.cache.clear()
                
                self.logger.info(f"Cache cleared for type: {resource_type or 'all'}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Cache istatistiklerini döndürür.
        
        Returns:
            Cache istatistikleri
        """
        try:
            with self.lock:
                total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
                hit_rate = (self.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    "cache_size": len(self.cache),
                    "cache_hits": self.stats["cache_hits"],
                    "cache_misses": self.stats["cache_misses"],
                    "hit_rate_percent": round(hit_rate, 2),
                    "loaded_resources": self.stats["loaded_resources"],
                    "failed_loads": self.stats["failed_loads"],
                    "total_requests": total_requests
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get cache statistics: {e}")
            return {}
    
    def _find_icon_file(self, icon_name: str, category: str = None) -> Optional[Path]:
        """
        Icon dosyasını bulur.
        
        Args:
            icon_name: Icon adı
            category: Icon kategorisi
            
        Returns:
            Icon dosyasının yolu
        """
        try:
            icon_dir = self.resource_paths[ResourceType.ICON]
            
            if category:
                # Kategorili arama
                category_dir = icon_dir / category
                if category_dir.exists():
                    for ext in self.supported_formats[ResourceType.ICON]:
                        icon_path = category_dir / f"{icon_name}{ext}"
                        if icon_path.exists():
                            return icon_path
            
            # Ana dizinde arama
            for ext in self.supported_formats[ResourceType.ICON]:
                icon_path = icon_dir / f"{icon_name}{ext}"
                if icon_path.exists():
                    return icon_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find icon file '{icon_name}': {e}")
            return None
    
    def _find_style_file(self, style_name: str, theme: str = None) -> Optional[Path]:
        """
        Style dosyasını bulur.
        
        Args:
            style_name: Style adı
            theme: Tema adı
            
        Returns:
            Style dosyasının yolu
        """
        try:
            style_dir = self.resource_paths[ResourceType.STYLE]
            
            if theme:
                # Tema dizininde arama
                theme_dir = style_dir / "themes"
                for ext in self.supported_formats[ResourceType.STYLE]:
                    style_path = theme_dir / f"{theme}{ext}"
                    if style_path.exists():
                        return style_path
                
                # Component dizininde arama
                component_dir = style_dir / "components"
                for ext in self.supported_formats[ResourceType.STYLE]:
                    style_path = component_dir / f"{style_name}{ext}"
                    if style_path.exists():
                        return style_path
            
            # Ana dizinde arama
            for ext in self.supported_formats[ResourceType.STYLE]:
                style_path = style_dir / f"{style_name}{ext}"
                if style_path.exists():
                    return style_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find style file '{style_name}': {e}")
            return None
    
    def _find_resource_file(self, resource_name: str, resource_type: str) -> Optional[Path]:
        """
        Kaynak dosyasını bulur.
        
        Args:
            resource_name: Kaynak adı
            resource_type: Kaynak türü
            
        Returns:
            Kaynak dosyasının yolu
        """
        try:
            resource_dir = self.resource_paths.get(resource_type)
            if not resource_dir:
                return None
            
            supported_exts = self.supported_formats.get(resource_type, [])
            
            for ext in supported_exts:
                resource_path = resource_dir / f"{resource_name}{ext}"
                if resource_path.exists():
                    return resource_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find resource file '{resource_name}': {e}")
            return None
    
    def _load_image_file(self, image_path: Path, size: tuple = None) -> Optional[Any]:
        """
        Image dosyasını yükler.
        
        Args:
            image_path: Image dosyasının yolu
            size: İstenilen boyut
            
        Returns:
            Yüklenen image verisi
        """
        try:
            if image_path.suffix.lower() == '.svg':
                # SVG dosyası
                with open(image_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                return svg_content
            else:
                # Bitmap image
                with Image.open(image_path) as img:
                    if size:
                        img = img.resize(size, Image.Resampling.LANCZOS)
                    
                    # Image'ı bytes'a dönüştür
                    img_buffer = BytesIO()
                    img_format = 'PNG' if image_path.suffix.lower() in ['.png', '.ico'] else 'JPEG'
                    img.save(img_buffer, format=img_format)
                    img_bytes = img_buffer.getvalue()
                    
                    return img_bytes
                    
        except Exception as e:
            self.logger.error(f"Failed to load image file '{image_path}': {e}")
            return None
    
    def _load_json_file(self, json_path: Path) -> Optional[Dict[str, Any]]:
        """
        JSON dosyasını yükler.
        
        Args:
            json_path: JSON dosyasının yolu
            
        Returns:
            JSON verisi
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to load JSON file '{json_path}': {e}")
            return None
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Cache'den veri alır.
        
        Args:
            cache_key: Cache anahtarı
            
        Returns:
            Cache'deki veri
        """
        try:
            with self.lock:
                if cache_key in self.cache:
                    self.stats["cache_hits"] += 1
                    return self.cache[cache_key]
                else:
                    self.stats["cache_misses"] += 1
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to get from cache: {e}")
            return None
    
    def _add_to_cache(self, cache_key: str, data: Any):
        """
        Cache'e veri ekler.
        
        Args:
            cache_key: Cache anahtarı
            data: Eklenecek veri
        """
        try:
            with self.lock:
                self.cache[cache_key] = data
                self.stats["loaded_resources"] += 1
                
        except Exception as e:
            self.logger.error(f"Failed to add to cache: {e}")
    
    def _create_resource_directories(self):
        """Kaynak dizinlerini oluşturur."""
        try:
            # Ana kaynak dizinleri
            for resource_type, resource_path in self.resource_paths.items():
                resource_path.mkdir(parents=True, exist_ok=True)
            
            # Icon alt dizinleri
            icon_subdirs = ["tabs", "actions", "status"]
            for subdir in icon_subdirs:
                (self.resource_paths[ResourceType.ICON] / subdir).mkdir(exist_ok=True)
            
            # Style alt dizinleri
            style_subdirs = ["themes", "components"]
            for subdir in style_subdirs:
                (self.resource_paths[ResourceType.STYLE] / subdir).mkdir(exist_ok=True)
            
            self.logger.info("Resource directories created")
            
        except Exception as e:
            self.logger.error(f"Failed to create resource directories: {e}")
    
    def _load_default_resources(self):
        """Varsayılan kaynakları yükler."""
        try:
            # Varsayılan stil dosyalarını oluştur
            self._create_default_styles()
            
            # Varsayılan icon dosyalarını oluştur (placeholder)
            self._create_default_icons()
            
            self.logger.info("Default resources loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load default resources: {e}")
    
    def _create_default_styles(self):
        """Varsayılan stil dosyalarını oluşturur."""
        try:
            # Tema dosyaları zaten varsa, yeniden yazma
            themes_dir = self.resource_paths[ResourceType.STYLE] / "themes"
            dark_theme_file = themes_dir / "dark.qss"
            light_theme_file = themes_dir / "light.qss"
            
            if dark_theme_file.exists() and light_theme_file.exists():
                self.logger.info("Tema dosyaları zaten mevcut, atlanıyor")
                return
            # Dark theme
            dark_theme = """
/* Dark Theme - Complete */
QMainWindow {
    background-color: #1a1a1a;
    color: #ffffff;
}

QWidget {
    background-color: #1a1a1a;
    color: #ffffff;
}

QTabWidget::pane {
    border: 1px solid #333333;
    background-color: #2d2d2d;
}

QTabBar::tab {
    background-color: #333333;
    color: #ffffff;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #007acc;
    color: #ffffff;
}

QTabBar::tab:hover {
    background-color: #4a4a4a;
}

QPushButton {
    background-color: #007acc;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #005a9e;
}

QPushButton:pressed {
    background-color: #004578;
}

QPushButton:disabled {
    background-color: #3c3c3c;
    color: #666666;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 6px 8px;
    border-radius: 4px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #007acc;
    background-color: #404040;
}

QComboBox {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 6px 8px;
    border-radius: 4px;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #ffffff;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #555555;
    selection-background-color: #007acc;
    selection-color: #ffffff;
}

QProgressBar {
    background-color: #333333;
    border: 1px solid #555555;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    font-weight: 500;
}

QProgressBar::chunk {
    background-color: #007acc;
    border-radius: 3px;
}

QTableWidget, QTableView {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #333333;
    gridline-color: #333333;
    selection-background-color: #007acc;
    selection-color: #ffffff;
    alternate-background-color: #252526;
}

QTableWidget::item, QTableView::item {
    padding: 4px 8px;
    border: none;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #007acc;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #333333;
    color: #ffffff;
    padding: 8px;
    border: none;
    border-right: 1px solid #555555;
    border-bottom: 1px solid #555555;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #4a4a4a;
}

QHeaderView::section:pressed {
    background-color: #007acc;
}

QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QScrollBar:horizontal {
    background-color: #2d2d2d;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #555555;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #666666;
}

QGroupBox {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 8px 0 8px;
    color: #007acc;
    font-weight: bold;
}

QLabel {
    color: #ffffff;
    background-color: transparent;
}

QLabel[class="title"] {
    font-size: 14pt;
    font-weight: bold;
    color: #ffffff;
}

QLabel[class="subtitle"] {
    font-size: 11pt;
    font-weight: normal;
    color: #cccccc;
}

QLabel[class="success"] {
    color: #4caf50;
}

QLabel[class="warning"] {
    color: #ff9800;
}

QLabel[class="error"] {
    color: #f44336;
}

QLabel[class="info"] {
    color: #2196f3;
}

QLabel[class="status-online"] {
    color: #4caf50;
    font-weight: bold;
}

QLabel[class="status-offline"] {
    color: #f44336;
    font-weight: bold;
}

QLabel[class="status-warning"] {
    color: #ff9800;
    font-weight: bold;
}

QFrame {
    background-color: #2d2d2d;
    border: 1px solid #333333;
    border-radius: 4px;
}

QSplitter::handle {
    background-color: #333333;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:pressed {
    background-color: #007acc;
}

QMenuBar {
    background-color: #2d2d2d;
    color: #ffffff;
    border-bottom: 1px solid #333333;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 8px;
}

QMenuBar::item:selected {
    background-color: #333333;
}

QMenuBar::item:pressed {
    background-color: #007acc;
}

QMenu {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #555555;
}

QMenu::item {
    background-color: transparent;
    padding: 6px 20px;
}

QMenu::item:selected {
    background-color: #007acc;
}

QMenu::separator {
    height: 1px;
    background-color: #555555;
    margin: 4px 8px;
}

QToolTip {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
}

QStatusBar {
    background-color: #2d2d2d;
    color: #cccccc;
    border-top: 1px solid #333333;
}

QStatusBar::item {
    border: none;
}

QTextEdit[class="console"] {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 4px;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 9pt;
    line-height: 1.4;
}

QTextEdit[class="console"] QScrollBar:vertical {
    background-color: #1a1a1a;
}

QCheckBox {
    color: #ffffff;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    background-color: #333333;
    border: 1px solid #555555;
    border-radius: 2px;
}

QCheckBox::indicator:checked {
    background-color: #007acc;
    border: 1px solid #007acc;
    border-radius: 2px;
}

QCheckBox::indicator:checked:after {
    content: "✓";
    color: #ffffff;
    font-weight: bold;
}

QSpinBox {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 4px;
    border-radius: 4px;
}

QSpinBox:focus {
    border: 2px solid #007acc;
}

QSpinBox::up-button {
    background-color: #333333;
    border: 1px solid #555555;
    border-radius: 2px;
}

QSpinBox::down-button {
    background-color: #333333;
    border: 1px solid #555555;
    border-radius: 2px;
}

QSpinBox::up-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid #ffffff;
}

QSpinBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #ffffff;
}
"""
            
            # Light theme
            light_theme = """
/* Light Theme - Complete */
QMainWindow {
    background-color: #ffffff;
    color: #333333;
}

QWidget {
    background-color: #ffffff;
    color: #333333;
}

QTabWidget::pane {
    border: 1px solid #cccccc;
    background-color: #f5f5f5;
}

QTabBar::tab {
    background-color: #e0e0e0;
    color: #333333;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #0066cc;
    color: #ffffff;
}

QTabBar::tab:hover {
    background-color: #d0d0d0;
}

QPushButton {
    background-color: #0066cc;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #0052a3;
}

QPushButton:pressed {
    background-color: #004080;
}

QPushButton:disabled {
    background-color: #e1e1e1;
    color: #999999;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    padding: 6px 8px;
    border-radius: 4px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #0066cc;
    background-color: #fafafa;
}

QComboBox {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    padding: 6px 8px;
    border-radius: 4px;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #333333;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    selection-background-color: #0066cc;
    selection-color: #ffffff;
}

QProgressBar {
    background-color: #f5f5f5;
    border: 1px solid #cccccc;
    border-radius: 4px;
    text-align: center;
    color: #333333;
    font-weight: 500;
}

QProgressBar::chunk {
    background-color: #0066cc;
    border-radius: 3px;
}

QTableWidget, QTableView {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    gridline-color: #f0f0f0;
    selection-background-color: #0066cc;
    selection-color: #ffffff;
    alternate-background-color: #fafafa;
}

QTableWidget::item, QTableView::item {
    padding: 4px 8px;
    border: none;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #0066cc;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #f5f5f5;
    color: #333333;
    padding: 8px;
    border: none;
    border-right: 1px solid #cccccc;
    border-bottom: 1px solid #cccccc;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #e0e0e0;
}

QHeaderView::section:pressed {
    background-color: #0066cc;
    color: #ffffff;
}

QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #cccccc;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #999999;
}

QScrollBar:horizontal {
    background-color: #f5f5f5;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #cccccc;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #999999;
}

QGroupBox {
    background-color: #f5f5f5;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 8px 0 8px;
    color: #0066cc;
    font-weight: bold;
}

QLabel {
    color: #333333;
    background-color: transparent;
}

QLabel[class="title"] {
    font-size: 14pt;
    font-weight: bold;
    color: #333333;
}

QLabel[class="subtitle"] {
    font-size: 11pt;
    font-weight: normal;
    color: #666666;
}

QLabel[class="success"] {
    color: #4caf50;
}

QLabel[class="warning"] {
    color: #ff9800;
}

QLabel[class="error"] {
    color: #f44336;
}

QLabel[class="info"] {
    color: #2196f3;
}

QLabel[class="status-online"] {
    color: #4caf50;
    font-weight: bold;
}

QLabel[class="status-offline"] {
    color: #f44336;
    font-weight: bold;
}

QLabel[class="status-warning"] {
    color: #ff9800;
    font-weight: bold;
}

QFrame {
    background-color: #f5f5f5;
    border: 1px solid #cccccc;
    border-radius: 4px;
}

QSplitter::handle {
    background-color: #cccccc;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:pressed {
    background-color: #0066cc;
}

QMenuBar {
    background-color: #f5f5f5;
    color: #333333;
    border-bottom: 1px solid #cccccc;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 8px;
}

QMenuBar::item:selected {
    background-color: #e0e0e0;
}

QMenuBar::item:pressed {
    background-color: #0066cc;
    color: #ffffff;
}

QMenu {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
}

QMenu::item {
    background-color: transparent;
    padding: 6px 20px;
}

QMenu::item:selected {
    background-color: #0066cc;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #cccccc;
    margin: 4px 8px;
}

QToolTip {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 4px 8px;
}

QStatusBar {
    background-color: #f5f5f5;
    color: #666666;
    border-top: 1px solid #cccccc;
}

QStatusBar::item {
    border: none;
}

QTextEdit[class="console"] {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 4px;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 9pt;
    line-height: 1.4;
}

QTextEdit[class="console"] QScrollBar:vertical {
    background-color: #f5f5f5;
}

QCheckBox {
    color: #333333;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 2px;
}

QCheckBox::indicator:checked {
    background-color: #0066cc;
    border: 1px solid #0066cc;
    border-radius: 2px;
}

QCheckBox::indicator:checked:after {
    content: "✓";
    color: #ffffff;
    font-weight: bold;
}

QSpinBox {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    padding: 4px;
    border-radius: 4px;
}

QSpinBox:focus {
    border: 2px solid #0066cc;
}

QSpinBox::up-button {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 2px;
}

QSpinBox::down-button {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 2px;
}

QSpinBox::up-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid #333333;
}

QSpinBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #333333;
}
"""
            
            # Stil dosyalarını yaz
            themes_dir = self.resource_paths[ResourceType.STYLE] / "themes"
            
            with open(themes_dir / "dark.qss", 'w', encoding='utf-8') as f:
                f.write(dark_theme)
            
            with open(themes_dir / "light.qss", 'w', encoding='utf-8') as f:
                f.write(light_theme)
            
        except Exception as e:
            self.logger.error(f"Failed to create default styles: {e}")
    
    def _create_default_icons(self):
        """Varsayılan placeholder icon'ları oluşturur."""
        try:
            # Bu fonksiyon gelecekte gerçek icon'ları oluşturmak için kullanılabilir
            # Şimdilik boş bırakıyoruz
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to create default icons: {e}")


# Global instance
resource_loader = ResourceLoader()
