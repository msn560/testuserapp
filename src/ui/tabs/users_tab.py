"""
Users tab for user management and administration.

This tab provides user CRUD operations, role management, and user statistics.
"""

from typing import Dict, Any, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QLineEdit, QComboBox, QCheckBox, QMessageBox,
    QHeaderView, QAbstractItemView, QDialog, QFormLayout,
    QDialogButtonBox, QTextEdit, QDateEdit, QSpinBox
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QIcon, QFont

from .base_tab import BaseTab, BaseTabWorker
from ...utils.logger import logger
from ...core.language import language_manager


class UsersWorker(BaseTabWorker):
    """Users tab worker for background data operations."""
    
    def __init__(self):
        super().__init__("users")
        self.user_service = None
        self.role_service = None
    
    def _do_refresh_data(self):
        """Refresh users data in background thread."""
        try:
            if not self.running:
                return
            
            # Get services from main app
            from ...app import App
            app = App.instance()
            if app:
                self.user_service = getattr(app, 'user_service', None)
                self.role_service = getattr(app, 'role_service', None)
            
            # Collect users data
            users_data = {
                'users': self._get_users_data(),
                'roles': self._get_roles_data(),
                'statistics': self._get_user_statistics(),
                'permissions': self._get_permissions_data()
            }
            
            self.data_ready.emit(users_data)
            
        except Exception as e:
            self.logger.error(f"Error refreshing users data: {e}")
            self.error_occurred.emit(str(e))
    
    def _get_users_data(self):
        """Get users data from database."""
        try:
            users = []
            
            # Try to get real data from database
            if self.user_service:
                try:
                    from ...db.models import User, UserRole, Role
                    
                    # Get all users with their roles
                    for user in User.select():
                        # Get user roles
                        user_roles = []
                        for user_role in UserRole.select().where(UserRole.user == user, UserRole.is_active == True):
                            user_roles.append(user_role.role.name)
                        
                        users.append({
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'full_name': user.full_name or '',
                            'roles': user_roles,
                            'is_active': user.is_active,
                            'is_verified': user.is_verified,
                            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                            'avatar_path': user.avatar_path or ''
                        })
                        
                except Exception as e:
                    self.logger.warning(f"Could not get real users data: {e}")
            
            # If no real data, return sample data
            if not users:
                users = [
                    {
                        'id': 1,
                        'username': 'admin',
                        'email': 'admin@example.com',
                        'full_name': 'System Administrator',
                        'roles': ['superadmin'],
                        'is_active': True,
                        'is_verified': True,
                        'last_login': '2024-01-15 10:30:00',
                        'created_at': '2024-01-01 00:00:00',
                        'avatar_path': ''
                    },
                    {
                        'id': 2,
                        'username': 'user1',
                        'email': 'user1@example.com',
                        'full_name': 'John Doe',
                        'roles': ['user'],
                        'is_active': True,
                        'is_verified': True,
                        'last_login': '2024-01-15 09:15:00',
                        'created_at': '2024-01-02 00:00:00',
                        'avatar_path': ''
                    }
                ]
            
            return users
            
        except Exception as e:
            self.logger.error(f"Error getting users data: {e}")
            return []
    
    def _get_roles_data(self):
        """Get roles data from database."""
        try:
            roles = []
            
            # Try to get real data from database
            if self.role_service:
                try:
                    from ...db.models import Role
                    
                    for role in Role.select():
                        roles.append({
                            'id': role.id,
                            'name': role.name,
                            'description': role.description or '',
                            'permissions': role.permissions or [],
                            'color': role.color or '#007acc',
                            'icon': role.icon or '',
                            'is_system_role': role.is_system_role,
                            'created_at': role.created_at.strftime('%Y-%m-%d %H:%M:%S') if role.created_at else ''
                        })
                        
                except Exception as e:
                    self.logger.warning(f"Could not get real roles data: {e}")
            
            # If no real data, return default roles
            if not roles:
                roles = [
                    {
                        'id': 1,
                        'name': 'superadmin',
                        'description': 'Full system access',
                        'permissions': ['*'],
                        'color': '#dc3545',
                        'icon': 'crown',
                        'is_system_role': True,
                        'created_at': '2024-01-01 00:00:00'
                    },
                    {
                        'id': 2,
                        'name': 'admin',
                        'description': 'Administrative access',
                        'permissions': ['user.manage', 'server.control', 'config.read'],
                        'color': '#fd7e14',
                        'icon': 'shield',
                        'is_system_role': True,
                        'created_at': '2024-01-01 00:00:00'
                    },
                    {
                        'id': 3,
                        'name': 'user',
                        'description': 'Standard user access',
                        'permissions': ['profile.read', 'profile.update'],
                        'color': '#28a745',
                        'icon': 'user',
                        'is_system_role': True,
                        'created_at': '2024-01-01 00:00:00'
                    }
                ]
            
            return roles
            
        except Exception as e:
            self.logger.error(f"Error getting roles data: {e}")
            return []
    
    def _get_user_statistics(self):
        """Get user statistics."""
        try:
            stats = {
                'total_users': 0,
                'active_users': 0,
                'verified_users': 0,
                'users_by_role': {},
                'recent_logins': 0,
                'new_users_today': 0
            }
            
            # Try to get real statistics
            if self.user_service:
                try:
                    from ...db.models import User, UserRole, Role
                    from datetime import datetime, timedelta
                    
                    # Total users
                    stats['total_users'] = User.select().count()
                    
                    # Active users
                    stats['active_users'] = User.select().where(User.is_active == True).count()
                    
                    # Verified users
                    stats['verified_users'] = User.select().where(User.is_verified == True).count()
                    
                    # Users by role
                    for role in Role.select():
                        count = UserRole.select().where(UserRole.role == role, UserRole.is_active == True).count()
                        stats['users_by_role'][role.name] = count
                    
                    # Recent logins (last 24 hours)
                    yesterday = datetime.now() - timedelta(days=1)
                    stats['recent_logins'] = User.select().where(User.last_login >= yesterday).count()
                    
                    # New users today
                    today = datetime.now().date()
                    stats['new_users_today'] = User.select().where(User.created_at.date() == today).count()
                    
                except Exception as e:
                    self.logger.warning(f"Could not get real user statistics: {e}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting user statistics: {e}")
            return {}
    
    def _get_permissions_data(self):
        """Get permissions data."""
        try:
            permissions = [
                {
                    'name': 'user.create',
                    'description': 'Create new users',
                    'resource': 'user',
                    'action': 'create'
                },
                {
                    'name': 'user.read',
                    'description': 'View user information',
                    'resource': 'user',
                    'action': 'read'
                },
                {
                    'name': 'user.update',
                    'description': 'Update user information',
                    'resource': 'user',
                    'action': 'update'
                },
                {
                    'name': 'user.delete',
                    'description': 'Delete users',
                    'resource': 'user',
                    'action': 'delete'
                },
                {
                    'name': 'server.control',
                    'description': 'Control server operations',
                    'resource': 'server',
                    'action': 'control'
                },
                {
                    'name': 'config.read',
                    'description': 'Read configuration',
                    'resource': 'config',
                    'action': 'read'
                },
                {
                    'name': 'config.update',
                    'description': 'Update configuration',
                    'resource': 'config',
                    'action': 'update'
                }
            ]
            
            return permissions
            
        except Exception as e:
            self.logger.error(f"Error getting permissions data: {e}")
            return []


class UsersTab(BaseTab):
    """
    Users tab for user management and administration.
    
    This tab provides functionality for managing users, roles, and permissions.
    """
    
    def __init__(self):
        """Initialize the users tab."""
        super().__init__("users", "User Management")
        
        # Data storage
        self.users = []
        self.roles = []
        self.permissions = []
        self.statistics = {}
        self.selected_user = None
        
        # Create user management components
        self._create_user_components()
        
        # Set refresh interval
        self.set_refresh_interval(10000)  # 10 seconds
        
        # Override worker with Users-specific worker
        self._init_users_worker()
        
        self.logger.info("Users tab initialized")
    
    def _init_users_worker(self):
        """Initialize Users-specific worker."""
        try:
            # Use base class lazy loading
            self._ensure_worker_thread()
            
            # Create new Users worker if not exists
            if not self.worker:
                self.worker = UsersWorker()
                
                # Connect signals
                self.worker.data_ready.connect(self._on_data_ready)
                self.worker.error_occurred.connect(self._on_error_occurred)
                
                # Move worker to thread
            self.worker.moveToThread(self.worker_thread)
            
            # Start worker
            self.worker_thread.started.connect(self.worker.start_worker)
            self.worker_thread.start()
            
            self.logger.info("Users worker initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Users worker: {e}")
    
    def _on_data_ready(self, data: dict):
        """Handle data ready from worker."""
        try:
            # Update local data
            self.users = data.get('users', [])
            self.roles = data.get('roles', [])
            self.permissions = data.get('permissions', [])
            self.statistics = data.get('statistics', {})
            
            # Update UI
            self._update_users_ui()
            
        except Exception as e:
            self.logger.error(f"Error handling users data: {e}")
    
    def _on_error_occurred(self, error_message: str):
        """Handle error from worker."""
        self.logger.error(f"Users worker error: {error_message}")
        self.update_status(f"Users Error: {error_message}", "error")
    
    def _update_users_ui(self):
        """Update users UI with current data."""
        try:
            # Update users table
            if hasattr(self, 'users_table'):
                self._populate_users_table()
            
            # Update statistics
            self._update_statistics_display()
            
            # Update roles combo
            self._update_roles_combo()
            
        except Exception as e:
            self.logger.error(f"Error updating users UI: {e}")
    
    def _create_user_components(self) -> None:
        """Create user management components."""
        try:
            # Initialize user components
            self.user_widgets = {}
            self.role_widgets = {}
            self.permission_widgets = {}
            
            # Create user management widgets
            self._create_user_widgets()
            
            # Create role management widgets
            self._create_role_widgets()
            
            # Create permission widgets
            self._create_permission_widgets()
            
            self.logger.info("User components created")
            
        except Exception as e:
            self.logger.error(f"Failed to create user components: {e}")
    
    def _create_user_widgets(self) -> None:
        """Create user management widgets."""
        try:
            # User table widget
            self.user_widgets['table'] = {
                'columns': ['ID', 'Kullanıcı Adı', 'E-posta', 'Rol', 'Durum', 'Son Giriş'],
                'sortable': True,
                'filterable': True,
                'selectable': True
            }
            
            # User form widget
            self.user_widgets['form'] = {
                'fields': ['username', 'email', 'password', 'full_name', 'role'],
                'validation': True,
                'required': ['username', 'email', 'password']
            }
            
            # User actions
            self.user_widgets['actions'] = {
                'create': {'enabled': True, 'text': 'Yeni Kullanıcı'},
                'edit': {'enabled': False, 'text': 'Düzenle'},
                'delete': {'enabled': False, 'text': 'Sil'},
                'reset_password': {'enabled': False, 'text': 'Şifre Sıfırla'}
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create user widgets: {e}")
    
    def _create_role_widgets(self) -> None:
        """Create role management widgets."""
        try:
            # Role list widget
            self.role_widgets['list'] = {
                'roles': ['superadmin', 'admin', 'operator', 'viewer', 'api_user'],
                'descriptions': {
                    'superadmin': 'Tam sistem kontrolü',
                    'admin': 'Kullanıcı ve sistem yönetimi',
                    'operator': 'Server ve monitoring yönetimi',
                    'viewer': 'Salt okunur erişim',
                    'api_user': 'API erişim yetkisi'
                }
            }
            
            # Role permissions
            self.role_widgets['permissions'] = {
                'superadmin': ['all'],
                'admin': ['user_management', 'system_config', 'monitoring'],
                'operator': ['server_control', 'monitoring', 'logs'],
                'viewer': ['read_only'],
                'api_user': ['api_access']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create role widgets: {e}")
    
    def _create_permission_widgets(self) -> None:
        """Create permission widgets."""
        try:
            # Permission categories
            self.permission_widgets['categories'] = {
                'user_management': 'Kullanıcı Yönetimi',
                'system_config': 'Sistem Yapılandırması',
                'server_control': 'Server Kontrolü',
                'monitoring': 'İzleme',
                'logs': 'Log Yönetimi',
                'api_access': 'API Erişimi'
            }
            
            # Permission actions
            self.permission_widgets['actions'] = {
                'create': 'Oluştur',
                'read': 'Oku',
                'update': 'Güncelle',
                'delete': 'Sil',
                'execute': 'Çalıştır'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create permission widgets: {e}")
    
    def _create_content_widget(self) -> QWidget:
        """Create the users content widget."""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # User statistics section
        stats_group = self._create_statistics_section()
        layout.addWidget(stats_group)
        
        # User management section
        management_group = self._create_management_section()
        layout.addWidget(management_group)
        
        return content_widget
    
    def _create_statistics_section(self) -> QGroupBox:
        """Create the user statistics section."""
        group = QGroupBox("User Statistics")
        layout = QGridLayout(group)
        
        # Total users
        self.total_users_label = QLabel("0")
        self.total_users_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        layout.addWidget(QLabel("Total Users:"), 0, 0)
        layout.addWidget(self.total_users_label, 0, 1)
        
        # Active users
        self.active_users_label = QLabel("0")
        self.active_users_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(QLabel("Active Users:"), 1, 0)
        layout.addWidget(self.active_users_label, 1, 1)
        
        # Online users
        self.online_users_label = QLabel("0")
        self.online_users_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FF9800;")
        layout.addWidget(QLabel("Online Users:"), 2, 0)
        layout.addWidget(self.online_users_label, 2, 1)
        
        # Verified users
        self.verified_users_label = QLabel("0")
        self.verified_users_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #9C27B0;")
        layout.addWidget(QLabel("Verified Users:"), 3, 0)
        layout.addWidget(self.verified_users_label, 3, 1)
        
        return group
    
    def _create_management_section(self) -> QGroupBox:
        """Create the user management section."""
        group = QGroupBox("User Management")
        layout = QVBoxLayout(group)
        
        # User actions toolbar
        toolbar_layout = QHBoxLayout()
        
        self.add_user_btn = QPushButton("Add User")
        self.add_user_btn.setIcon(QIcon("data/resources/icons/actions/add.png"))
        self.add_user_btn.clicked.connect(self._add_user)
        toolbar_layout.addWidget(self.add_user_btn)
        
        self.edit_user_btn = QPushButton("Edit User")
        self.edit_user_btn.setIcon(QIcon("data/resources/icons/actions/edit.png"))
        self.edit_user_btn.clicked.connect(self._edit_user)
        self.edit_user_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_user_btn)
        
        self.delete_user_btn = QPushButton("Delete User")
        self.delete_user_btn.setIcon(QIcon("data/resources/icons/actions/delete.png"))
        self.delete_user_btn.clicked.connect(self._delete_user)
        self.delete_user_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_user_btn)
        
        toolbar_layout.addStretch()
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.textChanged.connect(self._search_users)
        toolbar_layout.addWidget(QLabel("Search:"))
        toolbar_layout.addWidget(self.search_input)
        
        layout.addLayout(toolbar_layout)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Username", "Email", "Full Name", "Roles", "Status", "Last Login"
        ])
        
        # Configure table
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Connect selection change
        self.users_table.selectionModel().selectionChanged.connect(self._on_user_selection_changed)
        
        layout.addWidget(self.users_table)
        
        return group
    
    def refresh_data(self):
        """Refresh user data."""
        try:
            # Load users from service (placeholder)
            self._load_users()
            self._load_user_statistics()
            
            self.update_status("User data refreshed")
            
        except Exception as e:
            self.show_error(f"Failed to refresh user data: {e}")
    
    def _load_users(self):
        """Load users from the user service."""
        try:
            # Placeholder data - in real implementation, this would come from UserService
            placeholder_users = [
                {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "full_name": "Administrator",
                    "roles": ["superadmin"],
                    "is_active": True,
                    "is_verified": True,
                    "last_login": "2024-01-15 10:30:00"
                },
                {
                    "id": 2,
                    "username": "user1",
                    "email": "user1@example.com",
                    "full_name": "John Doe",
                    "roles": ["user"],
                    "is_active": True,
                    "is_verified": True,
                    "last_login": "2024-01-15 09:15:00"
                },
                {
                    "id": 3,
                    "username": "user2",
                    "email": "user2@example.com",
                    "full_name": "Jane Smith",
                    "roles": ["user"],
                    "is_active": False,
                    "is_verified": False,
                    "last_login": None
                }
            ]
            
            self.users = placeholder_users
            self._populate_users_table()
            
        except Exception as e:
            self.logger.error(f"Failed to load users: {e}")
    
    def _load_user_statistics(self):
        """Load user statistics."""
        try:
            total_users = len(self.users)
            active_users = sum(1 for user in self.users if user.get('is_active', False))
            verified_users = sum(1 for user in self.users if user.get('is_verified', False))
            online_users = 0  # Placeholder - would come from session service
            
            self.total_users_label.setText(str(total_users))
            self.active_users_label.setText(str(active_users))
            self.verified_users_label.setText(str(verified_users))
            self.online_users_label.setText(str(online_users))
            
        except Exception as e:
            self.logger.error(f"Failed to load user statistics: {e}")
    
    def _populate_users_table(self):
        """Populate the users table with data (optimized for performance)."""
        try:
            # Disable table updates during population to prevent UI freezing
            self.users_table.setUpdatesEnabled(False)
            
            # Limit the number of users to display for better performance
            max_users = 200
            users_to_show = self.users[:max_users]
            
            self.users_table.setRowCount(len(users_to_show))
            
            for row, user in enumerate(users_to_show):
                # ID
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user.get('id', ''))))
                
                # Username
                self.users_table.setItem(row, 1, QTableWidgetItem(user.get('username', '')))
                
                # Email
                self.users_table.setItem(row, 2, QTableWidgetItem(user.get('email', '')))
                
                # Full Name
                self.users_table.setItem(row, 3, QTableWidgetItem(user.get('full_name', '')))
                
                # Roles
                roles = user.get('roles', [])
                roles_text = ', '.join(roles) if roles else 'No roles'
                self.users_table.setItem(row, 4, QTableWidgetItem(roles_text))
                
                # Status
                status = "Active" if user.get('is_active', False) else "Inactive"
                if not user.get('is_verified', False):
                    status += " (Unverified)"
                self.users_table.setItem(row, 5, QTableWidgetItem(status))
                
                # Last Login
                last_login = user.get('last_login', 'Never')
                self.users_table.setItem(row, 6, QTableWidgetItem(str(last_login)))
            
            # Re-enable table updates after population
            self.users_table.setUpdatesEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Failed to populate users table: {e}")
            # Make sure to re-enable updates even if there's an error
            self.users_table.setUpdatesEnabled(True)
    
    def _update_statistics_display(self):
        """Update statistics display with current data."""
        try:
            if not hasattr(self, 'stats_widgets'):
                return
            
            # Update total users
            if 'total_users' in self.stats_widgets:
                self.stats_widgets['total_users'].setText(
                    str(self.statistics.get('total_users', 0))
                )
            
            # Update active users
            if 'active_users' in self.stats_widgets:
                self.stats_widgets['active_users'].setText(
                    str(self.statistics.get('active_users', 0))
                )
            
            # Update verified users
            if 'verified_users' in self.stats_widgets:
                self.stats_widgets['verified_users'].setText(
                    str(self.statistics.get('verified_users', 0))
                )
            
            # Update recent logins
            if 'recent_logins' in self.stats_widgets:
                self.stats_widgets['recent_logins'].setText(
                    str(self.statistics.get('recent_logins', 0))
                )
            
            # Update new users today
            if 'new_users_today' in self.stats_widgets:
                self.stats_widgets['new_users_today'].setText(
                    str(self.statistics.get('new_users_today', 0))
                )
            
        except Exception as e:
            self.logger.error(f"Error updating statistics display: {e}")
    
    def _update_roles_combo(self):
        """Update roles combo box with current roles."""
        try:
            if not hasattr(self, 'roles_combo'):
                return
            
            # Clear existing items
            self.roles_combo.clear()
            
            # Add roles
            for role in self.roles:
                self.roles_combo.addItem(role['name'], role)
            
        except Exception as e:
            self.logger.error(f"Error updating roles combo: {e}")
    
    def _search_users(self, search_text: str):
        """Search and filter users."""
        try:
            if not search_text:
                self._populate_users_table()
                return
            
            # Filter users based on search text
            filtered_users = []
            search_lower = search_text.lower()
            
            for user in self.users:
                if (search_lower in user.get('username', '').lower() or
                    search_lower in user.get('email', '').lower() or
                    search_lower in user.get('full_name', '').lower()):
                    filtered_users.append(user)
            
            # Update table with filtered results
            self.users_table.setRowCount(len(filtered_users))
            
            for row, user in enumerate(filtered_users):
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user.get('id', ''))))
                self.users_table.setItem(row, 1, QTableWidgetItem(user.get('username', '')))
                self.users_table.setItem(row, 2, QTableWidgetItem(user.get('email', '')))
                self.users_table.setItem(row, 3, QTableWidgetItem(user.get('full_name', '')))
                
                roles = user.get('roles', [])
                roles_text = ', '.join(roles) if roles else 'No roles'
                self.users_table.setItem(row, 4, QTableWidgetItem(roles_text))
                
                status = "Active" if user.get('is_active', False) else "Inactive"
                if not user.get('is_verified', False):
                    status += " (Unverified)"
                self.users_table.setItem(row, 5, QTableWidgetItem(status))
                
                last_login = user.get('last_login', 'Never')
                self.users_table.setItem(row, 6, QTableWidgetItem(str(last_login)))
            
        except Exception as e:
            self.logger.error(f"Failed to search users: {e}")
    
    def _on_user_selection_changed(self):
        """Handle user selection change."""
        try:
            selected_rows = self.users_table.selectionModel().selectedRows()
            
            if selected_rows:
                row = selected_rows[0].row()
                user_id = int(self.users_table.item(row, 0).text())
                
                # Find selected user
                self.selected_user = next((user for user in self.users if user['id'] == user_id), None)
                
                # Enable edit and delete buttons
                self.edit_user_btn.setEnabled(True)
                self.delete_user_btn.setEnabled(True)
            else:
                self.selected_user = None
                self.edit_user_btn.setEnabled(False)
                self.delete_user_btn.setEnabled(False)
                
        except Exception as e:
            self.logger.error(f"Failed to handle user selection: {e}")
    
    def _add_user(self):
        """Add a new user."""
        try:
            dialog = UserDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                user_data = dialog.get_user_data()
                
                # Add user (placeholder)
                new_user = {
                    "id": len(self.users) + 1,
                    **user_data
                }
                self.users.append(new_user)
                
                # Refresh table
                self._populate_users_table()
                self._load_user_statistics()
                
                self.show_success(f"User '{user_data['username']}' added successfully")
                
        except Exception as e:
            self.show_error(f"Failed to add user: {e}")
    
    def _edit_user(self):
        """Edit selected user."""
        try:
            if not self.selected_user:
                return
            
            dialog = UserDialog(self, self.selected_user)
            if dialog.exec_() == QDialog.Accepted:
                user_data = dialog.get_user_data()
                
                # Update user (placeholder)
                for key, value in user_data.items():
                    self.selected_user[key] = value
                
                # Refresh table
                self._populate_users_table()
                self._load_user_statistics()
                
                self.show_success(f"User '{user_data['username']}' updated successfully")
                
        except Exception as e:
            self.show_error(f"Failed to edit user: {e}")
    
    def _delete_user(self):
        """Delete selected user."""
        try:
            if not self.selected_user:
                return
            
            username = self.selected_user.get('username', 'Unknown')
            
            reply = QMessageBox.question(
                self,
                "Delete User",
                f"Are you sure you want to delete user '{username}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Remove user (placeholder)
                self.users = [user for user in self.users if user['id'] != self.selected_user['id']]
                
                # Refresh table
                self._populate_users_table()
                self._load_user_statistics()
                
                self.show_success(f"User '{username}' deleted successfully")
                
        except Exception as e:
            self.show_error(f"Failed to delete user: {e}")
    
    def get_tab_data(self) -> Dict[str, Any]:
        """Get users tab data."""
        return {
            **super().get_tab_data(),
            "total_users": len(self.users),
            "selected_user": self.selected_user,
            "search_text": self.search_input.text()
        }


class UserDialog(QDialog):
    """Dialog for adding/editing users."""
    
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.user_data = user_data or {}
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Add User" if not self.user_data else "Edit User")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setText(self.user_data.get('username', ''))
        form_layout.addRow("Username:", self.username_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setText(self.user_data.get('email', ''))
        form_layout.addRow("Email:", self.email_input)
        
        # Full Name
        self.full_name_input = QLineEdit()
        self.full_name_input.setText(self.user_data.get('full_name', ''))
        form_layout.addRow("Full Name:", self.full_name_input)
        
        # Password (only for new users)
        if not self.user_data:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            form_layout.addRow("Password:", self.password_input)
        
        # Roles
        self.roles_combo = QComboBox()
        self.roles_combo.addItems(["user", "admin", "superadmin"])
        if self.user_data.get('roles'):
            self.roles_combo.setCurrentText(self.user_data['roles'][0])
        form_layout.addRow("Role:", self.roles_combo)
        
        # Active status
        self.active_checkbox = QCheckBox()
        self.active_checkbox.setChecked(self.user_data.get('is_active', True))
        form_layout.addRow("Active:", self.active_checkbox)
        
        # Verified status
        self.verified_checkbox = QCheckBox()
        self.verified_checkbox.setChecked(self.user_data.get('is_verified', False))
        form_layout.addRow("Verified:", self.verified_checkbox)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_user_data(self) -> Dict[str, Any]:
        """Get user data from the dialog."""
        data = {
            'username': self.username_input.text(),
            'email': self.email_input.text(),
            'full_name': self.full_name_input.text(),
            'roles': [self.roles_combo.currentText()],
            'is_active': self.active_checkbox.isChecked(),
            'is_verified': self.verified_checkbox.isChecked()
        }
        
        if not self.user_data and hasattr(self, 'password_input'):
            data['password'] = self.password_input.text()
        
        return data
