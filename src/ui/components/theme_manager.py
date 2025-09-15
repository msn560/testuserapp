"""
Theme Manager module - Tema yöneticisi

Bu modül uygulamanın tema sistemini yönetir.
Dark, light ve custom tema desteği.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPalette, QColor

from ...utils.logger import logger
from ...core.constants import THEMES_DIR


class ThemeManager(QObject):
    """
    Tema yöneticisi sınıfı
    
    Uygulamanın tema sistemini yönetir.
    """
    
    # Signals
    theme_changed = pyqtSignal(str)  # Tema değişti
    theme_loaded = pyqtSignal(dict)  # Tema yüklendi
    
    def __init__(self):
        """Theme manager'ı başlat"""
        super().__init__()
        
        self.current_theme = "dark"
        self.available_themes = {}
        self.theme_colors = {}
        self.custom_styles = {}
        
        # Default themes
        self._setup_default_themes()
        
        # Load available themes
        self._load_available_themes()
    
    def _setup_default_themes(self):
        """Varsayılan temaları kur"""
        # Dark theme
        self.available_themes['dark'] = {
            'name': 'Dark Theme',
            'description': 'Dark theme with blue accents',
            'file': 'dark.qss',
            'colors': {
                'primary_bg': '#2b2b2b',
                'secondary_bg': '#3c3c3c',
                'accent_color': '#0078d4',
                'text_primary': '#ffffff',
                'text_secondary': '#cccccc',
                'border_color': '#555555',
                'success_color': '#28a745',
                'warning_color': '#ffc107',
                'error_color': '#dc3545',
                'info_color': '#17a2b8'
            }
        }
        
        # Light theme
        self.available_themes['light'] = {
            'name': 'Light Theme',
            'description': 'Light theme with blue accents',
            'file': 'light.qss',
            'colors': {
                'primary_bg': '#ffffff',
                'secondary_bg': '#f8f9fa',
                'accent_color': '#0066cc',
                'text_primary': '#212529',
                'text_secondary': '#6c757d',
                'border_color': '#dee2e6',
                'success_color': '#28a745',
                'warning_color': '#ffc107',
                'error_color': '#dc3545',
                'info_color': '#17a2b8'
            }
        }
        
        # Blue theme
        self.available_themes['blue'] = {
            'name': 'Blue Theme',
            'description': 'Blue-based professional theme',
            'file': 'blue.qss',
            'colors': {
                'primary_bg': '#1e3a5f',
                'secondary_bg': '#2c5282',
                'accent_color': '#4299e1',
                'text_primary': '#ffffff',
                'text_secondary': '#e2e8f0',
                'border_color': '#4a5568',
                'success_color': '#38a169',
                'warning_color': '#d69e2e',
                'error_color': '#e53e3e',
                'info_color': '#3182ce'
            }
        }
    
    def _load_available_themes(self):
        """Mevcut temaları yükle"""
        try:
            themes_dir = Path(THEMES_DIR)
            if not themes_dir.exists():
                logger.warning(f"Themes directory not found: {themes_dir}")
                return
            
            # QSS dosyalarını tara
            for qss_file in themes_dir.glob("*.qss"):
                theme_name = qss_file.stem
                
                # Eğer default theme'lerden biri değilse ekle
                if theme_name not in self.available_themes:
                    self.available_themes[theme_name] = {
                        'name': theme_name.title(),
                        'description': f'Custom {theme_name} theme',
                        'file': qss_file.name,
                        'colors': self._extract_colors_from_qss(qss_file)
                    }
            
            logger.info(f"Loaded {len(self.available_themes)} themes")
            
        except Exception as e:
            logger.error(f"Error loading themes: {e}")
    
    def _extract_colors_from_qss(self, qss_file: Path) -> Dict[str, str]:
        """QSS dosyasından renkleri çıkar"""
        colors = {}
        
        try:
            with open(qss_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basit renk çıkarma (comment'lerde tanımlanmış renkler)
            import re
            color_pattern = r'/\*\s*(\w+):\s*(#[0-9a-fA-F]{6})\s*\*/'
            matches = re.findall(color_pattern, content)
            
            for color_name, color_value in matches:
                colors[color_name] = color_value
            
            # Eğer hiç renk bulunamazsa varsayılan renkleri kullan
            if not colors:
                colors = self.available_themes['dark']['colors'].copy()
                
        except Exception as e:
            logger.error(f"Error extracting colors from {qss_file}: {e}")
            colors = self.available_themes['dark']['colors'].copy()
        
        return colors
    
    def get_available_themes(self) -> Dict[str, Dict[str, Any]]:
        """Mevcut temaları al"""
        return self.available_themes.copy()
    
    def get_current_theme(self) -> str:
        """Mevcut temayı al"""
        return self.current_theme
    
    def set_theme(self, theme_name: str) -> bool:
        """
        Tema ayarla
        
        Args:
            theme_name: Tema adı
            
        Returns:
            Tema değiştirme başarılı mı
        """
        try:
            if theme_name not in self.available_themes:
                logger.error(f"Theme not found: {theme_name}")
                return False
            
            theme_info = self.available_themes[theme_name]
            
            # QSS dosyasını yükle
            if not self._load_theme_file(theme_info['file']):
                return False
            
            # Tema renklerini güncelle
            self.theme_colors = theme_info['colors'].copy()
            
            # Mevcut temayı güncelle
            old_theme = self.current_theme
            self.current_theme = theme_name
            
            # Signal gönder
            self.theme_changed.emit(theme_name)
            self.theme_loaded.emit(theme_info)
            
            logger.info(f"Theme changed from '{old_theme}' to '{theme_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error setting theme '{theme_name}': {e}")
            return False
    
    def _load_theme_file(self, theme_file: str) -> bool:
        """
        Tema dosyasını yükle
        
        Args:
            theme_file: Tema dosyası adı
            
        Returns:
            Yükleme başarılı mı
        """
        try:
            theme_path = Path(THEMES_DIR) / theme_file
            
            if not theme_path.exists():
                logger.error(f"Theme file not found: {theme_path}")
                return False
            
            # QSS içeriğini oku
            with open(theme_path, 'r', encoding='utf-8') as f:
                qss_content = f.read()
            
            # Uygulamaya uygula
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss_content)
                logger.debug(f"Applied theme file: {theme_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading theme file '{theme_file}': {e}")
            return False
    
    def get_theme_color(self, color_name: str, default: str = "#000000") -> str:
        """
        Tema rengini al
        
        Args:
            color_name: Renk adı
            default: Varsayılan renk
            
        Returns:
            Renk değeri
        """
        return self.theme_colors.get(color_name, default)
    
    def get_theme_colors(self) -> Dict[str, str]:
        """Tema renklerini al"""
        return self.theme_colors.copy()
    
    def create_custom_theme(self, theme_name: str, colors: Dict[str, str], 
                           base_theme: str = "dark") -> bool:
        """
        Özel tema oluştur
        
        Args:
            theme_name: Tema adı
            colors: Tema renkleri
            base_theme: Temel tema
            
        Returns:
            Oluşturma başarılı mı
        """
        try:
            if theme_name in self.available_themes:
                logger.warning(f"Theme '{theme_name}' already exists")
            
            # Base theme'i al
            if base_theme not in self.available_themes:
                base_theme = "dark"
            
            base_colors = self.available_themes[base_theme]['colors'].copy()
            
            # Renkleri güncelle
            base_colors.update(colors)
            
            # Custom theme oluştur
            custom_theme = {
                'name': theme_name.title(),
                'description': f'Custom {theme_name} theme',
                'file': f'{theme_name}.qss',
                'colors': base_colors,
                'is_custom': True
            }
            
            # QSS dosyası oluştur
            if self._generate_theme_file(theme_name, base_colors, base_theme):
                self.available_themes[theme_name] = custom_theme
                logger.info(f"Created custom theme: {theme_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error creating custom theme '{theme_name}': {e}")
            return False
    
    def _generate_theme_file(self, theme_name: str, colors: Dict[str, str], 
                           base_theme: str) -> bool:
        """
        Tema dosyası oluştur
        
        Args:
            theme_name: Tema adı
            colors: Renk değerleri
            base_theme: Temel tema
            
        Returns:
            Oluşturma başarılı mı
        """
        try:
            themes_dir = Path(THEMES_DIR)
            themes_dir.mkdir(parents=True, exist_ok=True)
            
            # Base theme dosyasını oku
            base_file = themes_dir / self.available_themes[base_theme]['file']
            if base_file.exists():
                with open(base_file, 'r', encoding='utf-8') as f:
                    base_content = f.read()
            else:
                # Fallback template
                base_content = self._get_default_qss_template()
            
            # Renkleri değiştir
            custom_content = self._replace_colors_in_qss(base_content, colors)
            
            # Custom theme dosyasını yaz
            custom_file = themes_dir / f'{theme_name}.qss'
            with open(custom_file, 'w', encoding='utf-8') as f:
                f.write(custom_content)
            
            logger.info(f"Generated theme file: {custom_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating theme file for '{theme_name}': {e}")
            return False
    
    def _replace_colors_in_qss(self, qss_content: str, colors: Dict[str, str]) -> str:
        """
        QSS içeriğindeki renkleri değiştir
        
        Args:
            qss_content: QSS içeriği
            colors: Yeni renkler
            
        Returns:
            Güncellenmiş QSS içeriği
        """
        import re
        
        # Color comment mapping
        color_mappings = {
            'primary_bg': r'#[0-9a-fA-F]{6}(?=.*background)',
            'secondary_bg': r'#[0-9a-fA-F]{6}(?=.*alternate)',
            'accent_color': r'#[0-9a-fA-F]{6}(?=.*selection)',
            'text_primary': r'#[0-9a-fA-F]{6}(?=.*color)',
            'border_color': r'#[0-9a-fA-F]{6}(?=.*border)'
        }
        
        updated_content = qss_content
        
        for color_name, color_value in colors.items():
            if color_name in color_mappings:
                pattern = color_mappings[color_name]
                updated_content = re.sub(pattern, color_value, updated_content)
        
        return updated_content
    
    def _get_default_qss_template(self) -> str:
        """Varsayılan QSS template'i al"""
        return """
/* Default Theme Template */
/* primary_bg: #2b2b2b */
/* secondary_bg: #3c3c3c */
/* accent_color: #0078d4 */
/* text_primary: #ffffff */
/* text_secondary: #cccccc */
/* border_color: #555555 */

QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #3c3c3c;
}

QTabBar::tab {
    background-color: #2b2b2b;
    color: #ffffff;
    padding: 8px 16px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #0078d4;
}

QPushButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #106ebe;
}

QLineEdit, QTextEdit {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 4px;
}

QTableWidget {
    background-color: #3c3c3c;
    alternate-background-color: #2b2b2b;
    color: #ffffff;
    gridline-color: #555555;
}

QHeaderView::section {
    background-color: #2b2b2b;
    color: #ffffff;
    padding: 4px;
    border: 1px solid #555555;
}
"""
    
    def delete_custom_theme(self, theme_name: str) -> bool:
        """
        Özel temayı sil
        
        Args:
            theme_name: Tema adı
            
        Returns:
            Silme başarılı mı
        """
        try:
            if theme_name not in self.available_themes:
                logger.error(f"Theme not found: {theme_name}")
                return False
            
            theme_info = self.available_themes[theme_name]
            
            # Sadece custom theme'leri sil
            if not theme_info.get('is_custom', False):
                logger.error(f"Cannot delete built-in theme: {theme_name}")
                return False
            
            # Dosyayı sil
            theme_file = Path(THEMES_DIR) / theme_info['file']
            if theme_file.exists():
                theme_file.unlink()
            
            # Available themes'den kaldır
            del self.available_themes[theme_name]
            
            # Eğer silinen tema aktifse, dark tema'ya geç
            if self.current_theme == theme_name:
                self.set_theme("dark")
            
            logger.info(f"Deleted custom theme: {theme_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting custom theme '{theme_name}': {e}")
            return False
    
    def export_theme(self, theme_name: str, export_path: str) -> bool:
        """
        Temayı export et
        
        Args:
            theme_name: Tema adı
            export_path: Export yolu
            
        Returns:
            Export başarılı mı
        """
        try:
            if theme_name not in self.available_themes:
                logger.error(f"Theme not found: {theme_name}")
                return False
            
            theme_info = self.available_themes[theme_name].copy()
            
            # Theme dosyasını oku
            theme_file = Path(THEMES_DIR) / theme_info['file']
            if theme_file.exists():
                with open(theme_file, 'r', encoding='utf-8') as f:
                    qss_content = f.read()
                theme_info['qss_content'] = qss_content
            
            # JSON olarak export et
            export_file = Path(export_path)
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(theme_info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported theme '{theme_name}' to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting theme '{theme_name}': {e}")
            return False
    
    def import_theme(self, import_path: str) -> bool:
        """
        Temayı import et
        
        Args:
            import_path: Import yolu
            
        Returns:
            Import başarılı mı
        """
        try:
            # JSON dosyasını oku
            with open(import_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            theme_name = Path(import_path).stem
            
            # QSS içeriğini dosyaya yaz
            if 'qss_content' in theme_data:
                themes_dir = Path(THEMES_DIR)
                themes_dir.mkdir(parents=True, exist_ok=True)
                
                theme_file = themes_dir / f'{theme_name}.qss'
                with open(theme_file, 'w', encoding='utf-8') as f:
                    f.write(theme_data['qss_content'])
                
                # Theme info'yu güncelle
                theme_data['file'] = f'{theme_name}.qss'
                theme_data['is_custom'] = True
                del theme_data['qss_content']
                
                # Available themes'e ekle
                self.available_themes[theme_name] = theme_data
                
                logger.info(f"Imported theme: {theme_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error importing theme from '{import_path}': {e}")
            return False
    
    def apply_system_palette(self):
        """Sistem paletini uygula"""
        try:
            app = QApplication.instance()
            if not app:
                return
            
            # Current theme colors'ı al
            colors = self.get_theme_colors()
            
            # QPalette oluştur
            palette = QPalette()
            
            # Ana renkler
            palette.setColor(QPalette.Window, QColor(colors.get('primary_bg', '#2b2b2b')))
            palette.setColor(QPalette.WindowText, QColor(colors.get('text_primary', '#ffffff')))
            palette.setColor(QPalette.Base, QColor(colors.get('secondary_bg', '#3c3c3c')))
            palette.setColor(QPalette.AlternateBase, QColor(colors.get('primary_bg', '#2b2b2b')))
            palette.setColor(QPalette.Text, QColor(colors.get('text_primary', '#ffffff')))
            palette.setColor(QPalette.Button, QColor(colors.get('secondary_bg', '#3c3c3c')))
            palette.setColor(QPalette.ButtonText, QColor(colors.get('text_primary', '#ffffff')))
            palette.setColor(QPalette.Highlight, QColor(colors.get('accent_color', '#0078d4')))
            palette.setColor(QPalette.HighlightedText, QColor(colors.get('text_primary', '#ffffff')))
            
            # Palette'i uygula
            app.setPalette(palette)
            
            logger.debug("Applied system palette")
            
        except Exception as e:
            logger.error(f"Error applying system palette: {e}")


# Global theme manager instance
theme_manager = ThemeManager()