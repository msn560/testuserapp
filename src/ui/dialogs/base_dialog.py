"""
Base Dialog module - Temel dialog sınıfı

Bu modül tüm dialog'lar için temel sınıf sağlar.
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

from ...utils.logger import logger
from ...core.language import language_manager


class BaseDialog(QDialog):
    """
    Temel dialog sınıfı
    
    Tüm dialog'lar bu sınıftan türer.
    """
    
    # Signals
    dialog_accepted = pyqtSignal(dict)  # Dialog kabul edildi
    dialog_rejected = pyqtSignal()      # Dialog reddedildi
    data_changed = pyqtSignal(dict)     # Data değişti
    
    def __init__(self, title: str = "", parent=None):
        """
        Dialog'ı başlat
        
        Args:
            title: Dialog başlığı
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self.data = {}
        self.validation_errors = []
        
        self._setup_ui()
        self._setup_connections()
        self._setup_validation()
    
    def _setup_ui(self):
        """UI'yi kur"""
        self.setWindowTitle(self.title)
        self.setModal(True)
        self.setMinimumSize(400, 300)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Header
        if self.title:
            header_label = QLabel(self.title)
            header_label.setFont(QFont("Arial", 14, QFont.Bold))
            header_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(header_label)
            
            # Separator
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            main_layout.addWidget(separator)
        
        # Content area - subclass'lar burayı implement edecek
        self.content_layout = QVBoxLayout()
        main_layout.addLayout(self.content_layout)
        
        # Spacer
        main_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._on_ok_clicked)
        self.ok_btn.setDefault(True)
        button_layout.addWidget(self.ok_btn)
        
        main_layout.addLayout(button_layout)
    
    def _setup_connections(self):
        """Signal bağlantılarını kur"""
        self.accepted.connect(self._on_accepted)
        self.rejected.connect(self._on_rejected)
    
    def _setup_validation(self):
        """Validation'ı kur"""
        # Validation timer - gerçek zamanlı validation için
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._validate_data)
    
    def setup_content(self):
        """
        İçerik alanını kur
        
        Bu metod subclass'lar tarafından override edilmeli.
        """
        pass
    
    def load_data(self, data: dict):
        """
        Data yükle
        
        Args:
            data: Yüklenecek data
        """
        self.data = data.copy() if data else {}
        self._populate_fields()
    
    def get_data(self) -> dict:
        """
        Dialog'dan data al
        
        Returns:
            Dialog data'sı
        """
        self._collect_field_data()
        return self.data.copy()
    
    def _populate_fields(self):
        """
        Alanları data ile doldur
        
        Bu metod subclass'lar tarafından override edilmeli.
        """
        pass
    
    def _collect_field_data(self):
        """
        Alanlardan data topla
        
        Bu metod subclass'lar tarafından override edilmeli.
        """
        pass
    
    def _validate_data(self) -> bool:
        """
        Data'yı validate et
        
        Returns:
            Validation başarılı mı
        """
        self.validation_errors = []
        
        # Subclass'lar bu metodu override edebilir
        return self._perform_validation()
    
    def _perform_validation(self) -> bool:
        """
        Gerçek validation işlemi
        
        Bu metod subclass'lar tarafından override edilmeli.
        
        Returns:
            Validation başarılı mı
        """
        return True
    
    def add_validation_error(self, field: str, message: str):
        """
        Validation hatası ekle
        
        Args:
            field: Hata olan alan
            message: Hata mesajı
        """
        self.validation_errors.append({
            'field': field,
            'message': message
        })
    
    def show_validation_errors(self):
        """Validation hatalarını göster"""
        if not self.validation_errors:
            return
        
        error_messages = []
        for error in self.validation_errors:
            error_messages.append(f"• {error['message']}")
        
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(
            self,
            "Validation Errors",
            "Please fix the following errors:\n\n" + "\n".join(error_messages)
        )
    
    def _on_ok_clicked(self):
        """OK butonu tıklandığında"""
        # Data'yı topla
        self._collect_field_data()
        
        # Validate et
        if not self._validate_data():
            self.show_validation_errors()
            return
        
        # Dialog'ı kabul et
        self.accept()
    
    def _on_accepted(self):
        """Dialog kabul edildiğinde"""
        self.dialog_accepted.emit(self.get_data())
    
    def _on_rejected(self):
        """Dialog reddedildiğinde"""
        self.dialog_rejected.emit()
    
    def trigger_validation(self):
        """Validation'ı tetikle (delayed)"""
        self.validation_timer.start(500)  # 500ms delay
    
    def set_ok_enabled(self, enabled: bool):
        """OK butonunu aktif/pasif yap"""
        self.ok_btn.setEnabled(enabled)
    
    def set_title(self, title: str):
        """Dialog başlığını değiştir"""
        self.title = title
        self.setWindowTitle(title)
    
    def center_on_parent(self):
        """Dialog'ı parent'ın ortasına yerleştir"""
        if self.parent():
            parent_rect = self.parent().geometry()
            dialog_rect = self.geometry()
            
            x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            
            self.move(x, y)
        else:
            # Screen center
            screen = QApplication.desktop().screenGeometry()
            dialog_rect = self.geometry()
            
            x = (screen.width() - dialog_rect.width()) // 2
            y = (screen.height() - dialog_rect.height()) // 2
            
            self.move(x, y)
    
    def showEvent(self, event):
        """Dialog gösterildiğinde"""
        super().showEvent(event)
        
        # Setup content (if not already done)
        if not hasattr(self, '_content_setup'):
            self.setup_content()
            self._content_setup = True
        
        # Center dialog
        self.center_on_parent()
    
    def keyPressEvent(self, event):
        """Key press event"""
        # Escape key ile dialog'ı kapat
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)