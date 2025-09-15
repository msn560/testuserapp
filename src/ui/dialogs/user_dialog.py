"""
User Dialog module - Kullanıcı ekleme/düzenleme dialog'u

Bu modül kullanıcı ekleme ve düzenleme işlemleri için dialog sağlar.
"""

import re
from typing import Dict, Any, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QPushButton,
    QLabel, QGroupBox, QListWidget, QListWidgetItem, QTabWidget,
    QFileDialog, QMessageBox, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QPixmap, QIcon

from .base_dialog import BaseDialog
from ...utils.logger import logger
from ...core.language import language_manager


class UserValidationWorker(QObject):
    """
    User validation worker - Background'da validation yapar
    """
    
    validation_complete = pyqtSignal(bool, list)  # success, errors
    
    def __init__(self):
        super().__init__()
    
    def validate_user_data(self, data: dict, is_new_user: bool = True):
        """
        Kullanıcı verilerini validate et
        
        Args:
            data: Kullanıcı verisi
            is_new_user: Yeni kullanıcı mı
        """
        errors = []
        
        try:
            # Username validation
            username = data.get('username', '').strip()
            if not username:
                errors.append({'field': 'username', 'message': 'Username is required'})
            elif len(username) < 3:
                errors.append({'field': 'username', 'message': 'Username must be at least 3 characters'})
            elif not re.match(r'^[a-zA-Z0-9_-]+$', username):
                errors.append({'field': 'username', 'message': 'Username can only contain letters, numbers, underscore and dash'})
            
            # Email validation
            email = data.get('email', '').strip()
            if not email:
                errors.append({'field': 'email', 'message': 'Email is required'})
            elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                errors.append({'field': 'email', 'message': 'Please enter a valid email address'})
            
            # Full name validation
            full_name = data.get('full_name', '').strip()
            if not full_name:
                errors.append({'field': 'full_name', 'message': 'Full name is required'})
            elif len(full_name) < 2:
                errors.append({'field': 'full_name', 'message': 'Full name must be at least 2 characters'})
            
            # Password validation (for new users)
            if is_new_user:
                password = data.get('password', '')
                if not password:
                    errors.append({'field': 'password', 'message': 'Password is required'})
                elif len(password) < 6:
                    errors.append({'field': 'password', 'message': 'Password must be at least 6 characters'})
                
                # Confirm password
                confirm_password = data.get('confirm_password', '')
                if password != confirm_password:
                    errors.append({'field': 'confirm_password', 'message': 'Passwords do not match'})
            
            # Roles validation
            roles = data.get('roles', [])
            if not roles:
                errors.append({'field': 'roles', 'message': 'At least one role must be assigned'})
            
            self.validation_complete.emit(len(errors) == 0, errors)
            
        except Exception as e:
            logger.error(f"Error validating user data: {e}")
            errors.append({'field': 'general', 'message': f'Validation error: {str(e)}'})
            self.validation_complete.emit(False, errors)


class UserDialog(BaseDialog):
    """
    Kullanıcı dialog'u - Kullanıcı ekleme/düzenleme
    """
    
    def __init__(self, user_data: dict = None, parent=None):
        """
        User dialog'ını başlat
        
        Args:
            user_data: Düzenlenecek kullanıcı verisi (None ise yeni kullanıcı)
            parent: Parent widget
        """
        self.user_data = user_data or {}
        self.is_new_user = not bool(user_data.get('id'))
        
        title = "Add New User" if self.is_new_user else f"Edit User: {user_data.get('username', '')}"
        super().__init__(title, parent)
        
        # Available roles
        self.available_roles = [
            {'name': 'superadmin', 'description': 'Super Administrator - Full system access'},
            {'name': 'admin', 'description': 'Administrator - User and system management'},
            {'name': 'operator', 'description': 'Operator - Server and monitoring management'},
            {'name': 'viewer', 'description': 'Viewer - Read-only access'},
            {'name': 'api_user', 'description': 'API User - API access only'}
        ]
        
        # Validation worker
        self.validation_thread = QThread()
        self.validation_worker = UserValidationWorker()
        self.validation_worker.moveToThread(self.validation_thread)
        
        self.validation_worker.validation_complete.connect(self._on_validation_complete)
        self.validation_thread.start()
        
        # Load data
        self.load_data(self.user_data)
    
    def setup_content(self):
        """İçerik alanını kur"""
        # Tab widget
        self.tab_widget = QTabWidget()
        self.content_layout.addWidget(self.tab_widget)
        
        # Basic info tab
        self._setup_basic_tab()
        
        # Roles tab
        self._setup_roles_tab()
        
        # Advanced tab
        self._setup_advanced_tab()
        
        # Avatar tab (if editing existing user)
        if not self.is_new_user:
            self._setup_avatar_tab()
    
    def _setup_basic_tab(self):
        """Temel bilgiler sekmesi"""
        basic_widget = QWidget()
        layout = QFormLayout(basic_widget)
        
        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setMaxLength(50)
        self.username_edit.textChanged.connect(self.trigger_validation)
        layout.addRow("Username*:", self.username_edit)
        
        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setMaxLength(100)
        self.email_edit.textChanged.connect(self.trigger_validation)
        layout.addRow("Email*:", self.email_edit)
        
        # Full name
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setMaxLength(100)
        self.full_name_edit.textChanged.connect(self.trigger_validation)
        layout.addRow("Full Name*:", self.full_name_edit)
        
        # Password (only for new users)
        if self.is_new_user:
            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.password_edit.setMaxLength(100)
            self.password_edit.textChanged.connect(self.trigger_validation)
            layout.addRow("Password*:", self.password_edit)
            
            self.confirm_password_edit = QLineEdit()
            self.confirm_password_edit.setEchoMode(QLineEdit.Password)
            self.confirm_password_edit.setMaxLength(100)
            self.confirm_password_edit.textChanged.connect(self.trigger_validation)
            layout.addRow("Confirm Password*:", self.confirm_password_edit)
        
        self.tab_widget.addTab(basic_widget, "Basic Info")
    
    def _setup_roles_tab(self):
        """Roller sekmesi"""
        roles_widget = QWidget()
        layout = QVBoxLayout(roles_widget)
        
        # Info label
        info_label = QLabel("Select roles for this user:")
        layout.addWidget(info_label)
        
        # Roles list
        self.roles_list = QListWidget()
        self.roles_list.setMaximumHeight(200)
        
        for role in self.available_roles:
            item = QListWidgetItem(f"{role['name']} - {role['description']}")
            item.setData(Qt.UserRole, role['name'])
            item.setCheckState(Qt.Unchecked)
            self.roles_list.addItem(item)
        
        self.roles_list.itemChanged.connect(self.trigger_validation)
        layout.addWidget(self.roles_list)
        
        # Role permissions info
        permissions_group = QGroupBox("Role Permissions")
        permissions_layout = QVBoxLayout(permissions_group)
        
        self.permissions_text = QTextEdit()
        self.permissions_text.setReadOnly(True)
        self.permissions_text.setMaximumHeight(100)
        permissions_layout.addWidget(self.permissions_text)
        
        layout.addWidget(permissions_group)
        
        self.tab_widget.addTab(roles_widget, "Roles")
    
    def _setup_advanced_tab(self):
        """Gelişmiş ayarlar sekmesi"""
        advanced_widget = QWidget()
        layout = QFormLayout(advanced_widget)
        
        # Status
        self.is_active_cb = QCheckBox("User is active")
        self.is_active_cb.setChecked(True)
        layout.addRow("Status:", self.is_active_cb)
        
        # Verified
        self.is_verified_cb = QCheckBox("Email is verified")
        self.is_verified_cb.setChecked(False)
        layout.addRow("Verification:", self.is_verified_cb)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Optional notes about this user...")
        layout.addRow("Notes:", self.notes_edit)
        
        self.tab_widget.addTab(advanced_widget, "Advanced")
    
    def _setup_avatar_tab(self):
        """Avatar sekmesi"""
        avatar_widget = QWidget()
        layout = QVBoxLayout(avatar_widget)
        
        # Current avatar
        avatar_group = QGroupBox("User Avatar")
        avatar_layout = QVBoxLayout(avatar_group)
        
        self.avatar_label = QLabel()
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setMinimumSize(150, 150)
        self.avatar_label.setStyleSheet("border: 1px solid gray;")
        avatar_layout.addWidget(self.avatar_label)
        
        # Avatar buttons
        button_layout = QHBoxLayout()
        
        self.upload_avatar_btn = QPushButton("Upload New Avatar")
        self.upload_avatar_btn.clicked.connect(self._on_upload_avatar)
        button_layout.addWidget(self.upload_avatar_btn)
        
        self.remove_avatar_btn = QPushButton("Remove Avatar")
        self.remove_avatar_btn.clicked.connect(self._on_remove_avatar)
        button_layout.addWidget(self.remove_avatar_btn)
        
        avatar_layout.addLayout(button_layout)
        layout.addWidget(avatar_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(avatar_widget, "Avatar")
    
    def _populate_fields(self):
        """Alanları data ile doldur"""
        if not self.user_data:
            return
        
        # Basic info
        self.username_edit.setText(self.user_data.get('username', ''))
        self.email_edit.setText(self.user_data.get('email', ''))
        self.full_name_edit.setText(self.user_data.get('full_name', ''))
        
        # Advanced
        self.is_active_cb.setChecked(self.user_data.get('is_active', True))
        self.is_verified_cb.setChecked(self.user_data.get('is_verified', False))
        self.notes_edit.setPlainText(self.user_data.get('notes', ''))
        
        # Roles
        user_roles = self.user_data.get('roles', [])
        for i in range(self.roles_list.count()):
            item = self.roles_list.item(i)
            role_name = item.data(Qt.UserRole)
            if role_name in user_roles:
                item.setCheckState(Qt.Checked)
        
        # Avatar
        if hasattr(self, 'avatar_label'):
            avatar_path = self.user_data.get('avatar_path')
            if avatar_path:
                pixmap = QPixmap(avatar_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.avatar_label.setPixmap(scaled_pixmap)
                else:
                    self.avatar_label.setText("No Avatar")
            else:
                self.avatar_label.setText("No Avatar")
    
    def _collect_field_data(self):
        """Alanlardan data topla"""
        self.data = {
            'username': self.username_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'full_name': self.full_name_edit.text().strip(),
            'is_active': self.is_active_cb.isChecked(),
            'is_verified': self.is_verified_cb.isChecked(),
            'notes': self.notes_edit.toPlainText().strip()
        }
        
        # Password (only for new users)
        if self.is_new_user:
            self.data['password'] = self.password_edit.text()
            self.data['confirm_password'] = self.confirm_password_edit.text()
        
        # Roles
        roles = []
        for i in range(self.roles_list.count()):
            item = self.roles_list.item(i)
            if item.checkState() == Qt.Checked:
                roles.append(item.data(Qt.UserRole))
        self.data['roles'] = roles
        
        # Keep original ID if editing
        if not self.is_new_user:
            self.data['id'] = self.user_data.get('id')
    
    def _perform_validation(self) -> bool:
        """Validation işlemi"""
        # Async validation başlat
        if hasattr(self, 'validation_worker'):
            self.validation_worker.validate_user_data(self.data, self.is_new_user)
            return False  # Async validation, sonucu bekle
        
        return True
    
    def _on_validation_complete(self, success: bool, errors: list):
        """Validation tamamlandığında"""
        self.validation_errors = errors
        
        # OK butonunu aktif/pasif yap
        self.set_ok_enabled(success)
        
        # Hataları göster (opsiyonel)
        if not success and hasattr(self, '_show_validation_errors'):
            self.show_validation_errors()
    
    def _on_upload_avatar(self):
        """Avatar upload"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Avatar Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.avatar_label.setPixmap(scaled_pixmap)
                self.data['avatar_path'] = file_path
                logger.info(f"Avatar uploaded: {file_path}")
            else:
                QMessageBox.warning(self, "Invalid Image", "The selected file is not a valid image.")
    
    def _on_remove_avatar(self):
        """Avatar kaldır"""
        self.avatar_label.clear()
        self.avatar_label.setText("No Avatar")
        self.data['avatar_path'] = None
        logger.info("Avatar removed")
    
    def showEvent(self, event):
        """Dialog gösterildiğinde"""
        super().showEvent(event)
        
        # Focus'u ilk alana ver
        if self.username_edit:
            self.username_edit.setFocus()
    
    def cleanup(self):
        """Dialog'ı temizle"""
        if hasattr(self, 'validation_thread') and self.validation_thread.isRunning():
            self.validation_thread.quit()
            self.validation_thread.wait(3000)