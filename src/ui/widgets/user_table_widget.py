"""
User Table Widget module - Kullanıcı tablosu

Bu modül kullanıcıları listelemek ve yönetmek için tablo widget'ı sağlar.
Sortable, filterable, inline edit özellikleri.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QLabel, QHeaderView, QAbstractItemView,
    QMenu, QAction, QMessageBox, QCheckBox, QToolButton, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, QObject
from PyQt5.QtGui import QIcon, QPixmap, QColor, QFont

from .base_widget import BaseWidget
from ...utils.logger import logger
from ...core.language import language_manager
from ...db.models import User, Role, UserRole


class UserTableWorker(QObject):
    """
    User table worker - Kullanıcı verilerini background'da yükler
    """
    
    users_loaded = pyqtSignal(list)  # Kullanıcılar yüklendi
    error_occurred = pyqtSignal(str)  # Hata oluştu
    
    def __init__(self):
        super().__init__()
        self.running = False
    
    def load_users(self, filters: dict = None):
        """
        Kullanıcıları yükle
        
        Args:
            filters: Filtre kriterleri
        """
        try:
            self.running = True
            
            # Mock data - gerçek implementasyonda database'den gelecek
            users = [
                {
                    'id': 1,
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'full_name': 'System Administrator',
                    'is_active': True,
                    'is_verified': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'roles': ['superadmin', 'admin']
                },
                {
                    'id': 2,
                    'username': 'operator',
                    'email': 'operator@example.com',
                    'full_name': 'System Operator',
                    'is_active': True,
                    'is_verified': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'roles': ['operator']
                },
                {
                    'id': 3,
                    'username': 'viewer',
                    'email': 'viewer@example.com',
                    'full_name': 'System Viewer',
                    'is_active': True,
                    'is_verified': False,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'last_login': None,
                    'roles': ['viewer']
                }
            ]
            
            # Filtreleme uygula
            if filters:
                filtered_users = []
                for user in users:
                    if self._matches_filters(user, filters):
                        filtered_users.append(user)
                users = filtered_users
            
            self.users_loaded.emit(users)
            
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.running = False
    
    def _matches_filters(self, user: dict, filters: dict) -> bool:
        """
        Kullanıcının filtrelere uyup uymadığını kontrol et
        
        Args:
            user: Kullanıcı verisi
            filters: Filtre kriterleri
            
        Returns:
            Filtre eşleşmesi
        """
        # Search text
        search_text = filters.get('search_text', '').lower()
        if search_text:
            searchable_fields = [
                user.get('username', ''),
                user.get('email', ''),
                user.get('full_name', '')
            ]
            if not any(search_text in field.lower() for field in searchable_fields):
                return False
        
        # Status filter
        status_filter = filters.get('status_filter')
        if status_filter == 'active' and not user.get('is_active'):
            return False
        elif status_filter == 'inactive' and user.get('is_active'):
            return False
        
        # Role filter
        role_filter = filters.get('role_filter')
        if role_filter and role_filter not in user.get('roles', []):
            return False
        
        return True


class UserTableWidget(BaseWidget):
    """
    Kullanıcı tablosu widget'ı
    """
    
    # Signals
    user_selected = pyqtSignal(dict)  # Kullanıcı seçildi
    user_double_clicked = pyqtSignal(dict)  # Kullanıcı çift tıklandı
    user_context_menu = pyqtSignal(dict, object)  # Context menu
    users_changed = pyqtSignal()  # Kullanıcılar değişti
    
    def __init__(self, parent=None):
        """User table widget'ını başlat"""
        super().__init__(parent)
        
        self.users = []
        self.filtered_users = []
        self.current_filters = {}
        self.selected_users = []
        
        # Worker thread
        self.worker_thread = QThread()
        self.worker = UserTableWorker()
        self.worker.moveToThread(self.worker_thread)
        
        self._setup_ui()
        self._setup_connections()
        self._setup_worker()
        
        # İlk yükleme
        self.refresh_users()
    
    def _setup_ui(self):
        """UI'yi kur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(QLabel("Search:"))
        toolbar_layout.addWidget(self.search_input)
        
        # Status filter
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Active", "Inactive"])
        self.status_combo.currentTextChanged.connect(self._on_status_filter_changed)
        toolbar_layout.addWidget(QLabel("Status:"))
        toolbar_layout.addWidget(self.status_combo)
        
        # Role filter
        self.role_combo = QComboBox()
        self.role_combo.addItems(["All Roles", "superadmin", "admin", "operator", "viewer"])
        self.role_combo.currentTextChanged.connect(self._on_role_filter_changed)
        toolbar_layout.addWidget(QLabel("Role:"))
        toolbar_layout.addWidget(self.role_combo)
        
        toolbar_layout.addStretch()
        
        # Buttons
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_users)
        toolbar_layout.addWidget(self.refresh_btn)
        
        self.add_btn = QPushButton("Add User")
        self.add_btn.clicked.connect(self._on_add_user)
        toolbar_layout.addWidget(self.add_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Table signals
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        
        # Columns
        self.columns = [
            {'key': 'id', 'title': 'ID', 'width': 50},
            {'key': 'username', 'title': 'Username', 'width': 120},
            {'key': 'email', 'title': 'Email', 'width': 200},
            {'key': 'full_name', 'title': 'Full Name', 'width': 150},
            {'key': 'roles', 'title': 'Roles', 'width': 120},
            {'key': 'status', 'title': 'Status', 'width': 80},
            {'key': 'verified', 'title': 'Verified', 'width': 80},
            {'key': 'last_login', 'title': 'Last Login', 'width': 150},
            {'key': 'created_at', 'title': 'Created', 'width': 150}
        ]
        
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels([col['title'] for col in self.columns])
        
        # Column widths
        header = self.table.horizontalHeader()
        for i, col in enumerate(self.columns):
            if col['width']:
                self.table.setColumnWidth(i, col['width'])
        
        header.setStretchLastSection(True)
        
        layout.addWidget(self.table)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        self.count_label = QLabel("0 users")
        status_layout.addWidget(self.count_label)
        
        layout.addLayout(status_layout)
    
    def _setup_connections(self):
        """Signal bağlantılarını kur"""
        pass
    
    def _setup_worker(self):
        """Worker'ı kur"""
        self.worker.users_loaded.connect(self._on_users_loaded)
        self.worker.error_occurred.connect(self._on_worker_error)
        
        self.worker_thread.started.connect(lambda: logger.debug("User table worker started"))
        self.worker_thread.start()
    
    def refresh_users(self):
        """Kullanıcıları yenile"""
        self.status_label.setText("Loading users...")
        self.refresh_btn.setEnabled(False)
        
        # Worker'a yükleme sinyali gönder
        if not self.worker.running:
            self.worker.load_users(self.current_filters)
    
    def _on_users_loaded(self, users: list):
        """Kullanıcılar yüklendiğinde"""
        self.users = users
        self.filtered_users = users.copy()
        self._populate_table()
        
        self.status_label.setText("Ready")
        self.refresh_btn.setEnabled(True)
        self.count_label.setText(f"{len(users)} users")
        
        self.users_changed.emit()
    
    def _on_worker_error(self, error: str):
        """Worker hatası"""
        self.status_label.setText(f"Error: {error}")
        self.refresh_btn.setEnabled(True)
        logger.error(f"User table worker error: {error}")
    
    def _populate_table(self):
        """Tabloyu doldur"""
        self.table.setRowCount(len(self.filtered_users))
        
        for row, user in enumerate(self.filtered_users):
            for col, column in enumerate(self.columns):
                item = self._create_table_item(user, column)
                self.table.setItem(row, col, item)
        
        # Sort by username
        self.table.sortItems(1, Qt.AscendingOrder)
    
    def _create_table_item(self, user: dict, column: dict) -> QTableWidgetItem:
        """Tablo item'ı oluştur"""
        key = column['key']
        value = user.get(key, '')
        
        if key == 'roles':
            # Rolleri string olarak göster
            roles = user.get('roles', [])
            text = ', '.join(roles) if roles else 'No roles'
        elif key == 'status':
            # Status göstergesi
            text = 'Active' if user.get('is_active') else 'Inactive'
        elif key == 'verified':
            # Verified göstergesi
            text = 'Yes' if user.get('is_verified') else 'No'
        elif key == 'last_login':
            # Last login formatting
            last_login = user.get('last_login')
            text = last_login if last_login else 'Never'
        else:
            text = str(value) if value is not None else ''
        
        item = QTableWidgetItem(text)
        item.setData(Qt.UserRole, user)  # User data'sını sakla
        
        # Styling
        if key == 'status':
            if user.get('is_active'):
                item.setForeground(QColor(0, 150, 0))  # Green
            else:
                item.setForeground(QColor(150, 0, 0))  # Red
        elif key == 'verified':
            if user.get('is_verified'):
                item.setForeground(QColor(0, 150, 0))  # Green
            else:
                item.setForeground(QColor(200, 100, 0))  # Orange
        
        return item
    
    def _on_search_changed(self, text: str):
        """Search değiştiğinde"""
        self.current_filters['search_text'] = text
        self._apply_filters()
    
    def _on_status_filter_changed(self, status: str):
        """Status filtresi değiştiğinde"""
        if status == "All":
            self.current_filters.pop('status_filter', None)
        else:
            self.current_filters['status_filter'] = status.lower()
        self._apply_filters()
    
    def _on_role_filter_changed(self, role: str):
        """Role filtresi değiştiğinde"""
        if role == "All Roles":
            self.current_filters.pop('role_filter', None)
        else:
            self.current_filters['role_filter'] = role
        self._apply_filters()
    
    def _apply_filters(self):
        """Filtreleri uygula"""
        if not self.users:
            return
        
        self.filtered_users = []
        for user in self.users:
            if self._matches_filters(user, self.current_filters):
                self.filtered_users.append(user)
        
        self._populate_table()
        self.count_label.setText(f"{len(self.filtered_users)} users")
    
    def _matches_filters(self, user: dict, filters: dict) -> bool:
        """Filtre eşleşmesi kontrol et"""
        # Search text
        search_text = filters.get('search_text', '').lower()
        if search_text:
            searchable_fields = [
                user.get('username', ''),
                user.get('email', ''),
                user.get('full_name', '')
            ]
            if not any(search_text in field.lower() for field in searchable_fields):
                return False
        
        # Status filter
        status_filter = filters.get('status_filter')
        if status_filter == 'active' and not user.get('is_active'):
            return False
        elif status_filter == 'inactive' and user.get('is_active'):
            return False
        
        # Role filter
        role_filter = filters.get('role_filter')
        if role_filter and role_filter not in user.get('roles', []):
            return False
        
        return True
    
    def _on_selection_changed(self):
        """Seçim değiştiğinde"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.selected_users = []
            return
        
        # Seçili satırları al
        selected_rows = set()
        for item in selected_items:
            selected_rows.add(item.row())
        
        # Seçili kullanıcıları al
        self.selected_users = []
        for row in selected_rows:
            item = self.table.item(row, 0)  # First column
            if item:
                user = item.data(Qt.UserRole)
                if user:
                    self.selected_users.append(user)
        
        # Signal gönder
        if len(self.selected_users) == 1:
            self.user_selected.emit(self.selected_users[0])
    
    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """Item çift tıklandığında"""
        user = item.data(Qt.UserRole)
        if user:
            self.user_double_clicked.emit(user)
    
    def _on_context_menu(self, position):
        """Context menu"""
        item = self.table.itemAt(position)
        if not item:
            return
        
        user = item.data(Qt.UserRole)
        if not user:
            return
        
        menu = QMenu(self)
        
        # Actions
        edit_action = QAction("Edit User", self)
        edit_action.triggered.connect(lambda: self._edit_user(user))
        menu.addAction(edit_action)
        
        delete_action = QAction("Delete User", self)
        delete_action.triggered.connect(lambda: self._delete_user(user))
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        if user.get('is_active'):
            deactivate_action = QAction("Deactivate", self)
            deactivate_action.triggered.connect(lambda: self._toggle_user_status(user, False))
            menu.addAction(deactivate_action)
        else:
            activate_action = QAction("Activate", self)
            activate_action.triggered.connect(lambda: self._toggle_user_status(user, True))
            menu.addAction(activate_action)
        
        menu.addSeparator()
        
        reset_password_action = QAction("Reset Password", self)
        reset_password_action.triggered.connect(lambda: self._reset_password(user))
        menu.addAction(reset_password_action)
        
        # Show menu
        global_pos = self.table.mapToGlobal(position)
        menu.exec_(global_pos)
        
        self.user_context_menu.emit(user, menu)
    
    def _on_add_user(self):
        """Kullanıcı ekle"""
        # Bu signal UI'da yakalanacak ve dialog açılacak
        self.user_double_clicked.emit({})  # Empty user for new user
    
    def _edit_user(self, user: dict):
        """Kullanıcıyı düzenle"""
        self.user_double_clicked.emit(user)
    
    def _delete_user(self, user: dict):
        """Kullanıcıyı sil"""
        reply = QMessageBox.question(
            self, 
            "Delete User",
            f"Are you sure you want to delete user '{user.get('username')}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: Implement user deletion
            logger.info(f"Deleting user: {user.get('username')}")
            # Refresh table
            self.refresh_users()
    
    def _toggle_user_status(self, user: dict, active: bool):
        """Kullanıcı durumunu değiştir"""
        action = "activate" if active else "deactivate"
        logger.info(f"{action.title()} user: {user.get('username')}")
        # TODO: Implement status toggle
        # Refresh table
        self.refresh_users()
    
    def _reset_password(self, user: dict):
        """Parolayı sıfırla"""
        reply = QMessageBox.question(
            self,
            "Reset Password",
            f"Reset password for user '{user.get('username')}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info(f"Resetting password for user: {user.get('username')}")
            # TODO: Implement password reset
    
    def get_selected_users(self) -> List[dict]:
        """Seçili kullanıcıları al"""
        return self.selected_users.copy()
    
    def get_all_users(self) -> List[dict]:
        """Tüm kullanıcıları al"""
        return self.users.copy()
    
    def get_widget_data(self) -> Dict[str, Any]:
        """Widget verilerini al"""
        return {
            'total_users': len(self.users),
            'filtered_users': len(self.filtered_users),
            'selected_users': len(self.selected_users),
            'current_filters': self.current_filters.copy()
        }
    
    def cleanup(self):
        """Widget'ı temizle"""
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(3000)
        super().cleanup()