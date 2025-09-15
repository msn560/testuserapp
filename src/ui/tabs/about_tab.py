"""
About tab for application information and system details.

This tab provides information about the application, system details,
and license information.
"""

from typing import Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QGroupBox, QTextEdit, QTabWidget,
    QScrollArea, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont, QPixmap

from .base_tab import BaseTab
from ...core.constants import APP_NAME, APP_VERSION
from ...utils.logger import logger
from ...core.language import language_manager


class AboutTab(BaseTab):
    """
    About tab for application information and system details.
    
    This tab provides information about the application, system details,
    license information, and update checking.
    """
    
    def __init__(self):
        """Initialize the about tab."""
        super().__init__("about", "About")
        
        # Data storage
        self.system_info = {}
        self.package_info = {}
        
        # Create about components
        self._create_about_components()
        
        # Load system information
        self._load_system_info()
        
        self.logger.info("About tab initialized")
    
    def _create_about_components(self) -> None:
        """Create about tab components."""
        try:
            # Initialize about components
            self.about_widgets = {}
            self.info_widgets = {}
            self.license_widgets = {}
            
            # Create about widgets
            self._create_about_widgets()
            
            # Create info widgets
            self._create_info_widgets()
            
            # Create license widgets
            self._create_license_widgets()
            
            self.logger.info("About components created")
            
        except Exception as e:
            self.logger.error(f"Failed to create about components: {e}")
    
    def _create_about_widgets(self) -> None:
        """Create about widgets."""
        try:
            # Application info
            self.about_widgets['app'] = {
                'name': 'API Server Management System',
                'version': '1.0.0',
                'description': 'Python tabanlı API Server Management System',
                'author': 'Development Team',
                'website': 'https://github.com/your-repo',
                'email': 'support@example.com'
            }
            
            # Build info
            self.about_widgets['build'] = {
                'build_date': '2025-09-14',
                'build_time': '15:17:00',
                'python_version': '3.8+',
                'qt_version': '5.15+',
                'platform': 'Windows/Linux/macOS'
            }
            
            # Features
            self.about_widgets['features'] = [
                'PyQt5 Desktop GUI',
                'AioHTTP REST API',
                'SQLite Database',
                'Real-time Monitoring',
                'User Management',
                'Log Analysis',
                'Configuration Management',
                'Security & Authentication'
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to create about widgets: {e}")
    
    def _create_info_widgets(self) -> None:
        """Create info widgets."""
        try:
            # System information
            self.info_widgets['system'] = {
                'os': 'Windows 10',
                'architecture': 'x64',
                'python_version': '3.11.0',
                'qt_version': '5.15.2',
                'memory': '8GB',
                'cpu': 'Intel Core i7'
            }
            
            # Package information
            self.info_widgets['packages'] = {
                'PyQt5': '5.15.9',
                'aiohttp': '3.8.5',
                'peewee': '3.15.4',
                'PyJWT': '2.6.0',
                'bcrypt': '4.0.1',
                'psutil': '5.9.5'
            }
            
            # Environment variables
            self.info_widgets['environment'] = {
                'PATH': '...',
                'PYTHONPATH': '...',
                'QT_QPA_PLATFORM': 'windows'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create info widgets: {e}")
    
    def _create_license_widgets(self) -> None:
        """Create license widgets."""
        try:
            # License information
            self.license_widgets['license'] = {
                'type': 'MIT License',
                'year': '2025',
                'holder': 'Development Team',
                'text': 'MIT License text here...'
            }
            
            # Third-party licenses
            self.license_widgets['third_party'] = {
                'PyQt5': 'GPL v3',
                'aiohttp': 'Apache 2.0',
                'peewee': 'MIT',
                'PyJWT': 'MIT',
                'bcrypt': 'Apache 2.0',
                'psutil': 'BSD'
            }
            
            # Credits
            self.license_widgets['credits'] = [
                'Python Software Foundation',
                'Qt Company',
                'aiohttp Contributors',
                'Peewee ORM Team',
                'PyJWT Contributors'
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to create license widgets: {e}")
    
    def _create_content_widget(self) -> QWidget:
        """Create the about content widget."""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Create about tabs
        about_tabs = QTabWidget()
        layout.addWidget(about_tabs)
        
        # Application info tab
        app_tab = self._create_application_tab()
        about_tabs.addTab(app_tab, "Application")
        
        # System info tab
        system_tab = self._create_system_tab()
        about_tabs.addTab(system_tab, "System")
        
        # Packages tab
        packages_tab = self._create_packages_tab()
        about_tabs.addTab(packages_tab, "Packages")
        
        # License tab
        license_tab = self._create_license_tab()
        about_tabs.addTab(license_tab, "License")
        
        return content_widget
    
    def _create_application_tab(self) -> QWidget:
        """Create the application information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Application header
        header_layout = QHBoxLayout()
        
        # Application icon (placeholder)
        icon_label = QLabel()
        try:
            icon_path = "data/resources/icons/app.ico"
            if os.path.exists(icon_path):
                icon_label.setPixmap(QPixmap(icon_path).scaled(64, 64))
            else:
                # Create a simple text-based icon if file doesn't exist
                icon_label.setText("🚀")
                icon_label.setStyleSheet("font-size: 48px; color: #007acc;")
        except Exception as e:
            # Fallback to text if icon loading fails
            icon_label.setText("🚀")
            icon_label.setStyleSheet("font-size: 48px; color: #007acc;")
        
        icon_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # Application info
        app_info_layout = QVBoxLayout()
        
        app_name_label = QLabel(APP_NAME)
        app_name_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        app_info_layout.addWidget(app_name_label)
        
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setStyleSheet("font-size: 16px; color: #666666;")
        app_info_layout.addWidget(version_label)
        
        build_label = QLabel("Build: 2024.01.15")
        build_label.setStyleSheet("font-size: 12px; color: #888888;")
        app_info_layout.addWidget(build_label)
        
        header_layout.addLayout(app_info_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Application description
        description_group = QGroupBox("Description")
        description_layout = QVBoxLayout(description_group)
        
        description_text = QTextEdit()
        description_text.setReadOnly(True)
        description_text.setMaximumHeight(120)
        description_text.setPlainText("""
API Server Management System is a comprehensive solution for managing API servers, 
users, and system monitoring. It provides both a desktop GUI and REST API for 
complete server management capabilities.

Features:
• Server Management (Start, Stop, Restart)
• User Management with Role-based Access Control
• Real-time System Monitoring
• Comprehensive Logging and Analysis
• Configuration Management
• Security and Authentication
• Modern PyQt5 Desktop Interface
        """.strip())
        
        description_layout.addWidget(description_text)
        layout.addWidget(description_group)
        
        # Developer information
        developer_group = QGroupBox("Developer Information")
        developer_layout = QGridLayout(developer_group)
        
        developer_layout.addWidget(QLabel("Developer:"), 0, 0)
        developer_layout.addWidget(QLabel("API Server Manager Team"), 0, 1)
        
        developer_layout.addWidget(QLabel("Company:"), 1, 0)
        developer_layout.addWidget(QLabel("API Server Manager"), 1, 1)
        
        developer_layout.addWidget(QLabel("Website:"), 2, 0)
        website_label = QLabel('<a href="https://github.com/api-server-manager">https://github.com/api-server-manager</a>')
        website_label.setOpenExternalLinks(True)
        developer_layout.addWidget(website_label, 2, 1)
        
        developer_layout.addWidget(QLabel("Email:"), 3, 0)
        developer_layout.addWidget(QLabel("support@api-server-manager.com"), 3, 1)
        
        layout.addWidget(developer_group)
        
        # Update information
        update_group = QGroupBox("Updates")
        update_layout = QVBoxLayout(update_group)
        
        update_info_layout = QHBoxLayout()
        
        self.update_status_label = QLabel("Checking for updates...")
        update_info_layout.addWidget(self.update_status_label)
        
        update_info_layout.addStretch()
        
        self.check_update_btn = QPushButton("Check for Updates")
        self.check_update_btn.clicked.connect(self._check_for_updates)
        update_info_layout.addWidget(self.check_update_btn)
        
        update_layout.addLayout(update_info_layout)
        
        self.update_info_text = QTextEdit()
        self.update_info_text.setReadOnly(True)
        self.update_info_text.setMaximumHeight(80)
        self.update_info_text.setPlainText("No updates available.")
        update_layout.addWidget(self.update_info_text)
        
        layout.addWidget(update_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return tab
    
    def _create_system_tab(self) -> QWidget:
        """Create the system information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Operating system information
        os_group = QGroupBox("Operating System")
        os_layout = QGridLayout(os_group)
        
        self.os_name_label = QLabel("Unknown")
        self.os_name_label.setStyleSheet("font-weight: bold;")
        os_layout.addWidget(QLabel("OS:"), 0, 0)
        os_layout.addWidget(self.os_name_label, 0, 1)
        
        self.os_version_label = QLabel("Unknown")
        os_layout.addWidget(QLabel("Version:"), 1, 0)
        os_layout.addWidget(self.os_version_label, 1, 1)
        
        self.os_arch_label = QLabel("Unknown")
        os_layout.addWidget(QLabel("Architecture:"), 2, 0)
        os_layout.addWidget(self.os_arch_label, 2, 1)
        
        self.os_platform_label = QLabel("Unknown")
        os_layout.addWidget(QLabel("Platform:"), 3, 0)
        os_layout.addWidget(self.os_platform_label, 3, 1)
        
        scroll_layout.addWidget(os_group)
        
        # Python information
        python_group = QGroupBox("Python Environment")
        python_layout = QGridLayout(python_group)
        
        self.python_version_label = QLabel("Unknown")
        self.python_version_label.setStyleSheet("font-weight: bold;")
        python_layout.addWidget(QLabel("Python Version:"), 0, 0)
        python_layout.addWidget(self.python_version_label, 0, 1)
        
        self.python_executable_label = QLabel("Unknown")
        python_layout.addWidget(QLabel("Executable:"), 1, 0)
        python_layout.addWidget(self.python_executable_label, 1, 1)
        
        self.python_path_label = QLabel("Unknown")
        python_layout.addWidget(QLabel("Path:"), 2, 0)
        python_layout.addWidget(self.python_path_label, 2, 1)
        
        scroll_layout.addWidget(python_group)
        
        # Hardware information
        hardware_group = QGroupBox("Hardware Information")
        hardware_layout = QGridLayout(hardware_group)
        
        self.cpu_count_label = QLabel("Unknown")
        hardware_layout.addWidget(QLabel("CPU Cores:"), 0, 0)
        hardware_layout.addWidget(self.cpu_count_label, 0, 1)
        
        self.memory_total_label = QLabel("Unknown")
        hardware_layout.addWidget(QLabel("Total Memory:"), 1, 0)
        hardware_layout.addWidget(self.memory_total_label, 1, 1)
        
        self.memory_available_label = QLabel("Unknown")
        hardware_layout.addWidget(QLabel("Available Memory:"), 2, 0)
        hardware_layout.addWidget(self.memory_available_label, 2, 1)
        
        scroll_layout.addWidget(hardware_group)
        
        # Environment variables
        env_group = QGroupBox("Environment Variables")
        env_layout = QVBoxLayout(env_group)
        
        self.env_text = QTextEdit()
        self.env_text.setReadOnly(True)
        self.env_text.setMaximumHeight(150)
        self.env_text.setFont(QFont("Consolas", 9))
        env_layout.addWidget(self.env_text)
        
        scroll_layout.addWidget(env_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        return tab
    
    def _create_packages_tab(self) -> QWidget:
        """Create the packages information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Package information
        packages_group = QGroupBox("Installed Packages")
        packages_layout = QVBoxLayout(packages_group)
        
        self.packages_text = QTextEdit()
        self.packages_text.setReadOnly(True)
        self.packages_text.setFont(QFont("Consolas", 9))
        packages_layout.addWidget(self.packages_text)
        
        layout.addWidget(packages_group)
        
        # Package controls
        controls_layout = QHBoxLayout()
        
        self.refresh_packages_btn = QPushButton("Refresh Package List")
        self.refresh_packages_btn.clicked.connect(self._refresh_packages)
        controls_layout.addWidget(self.refresh_packages_btn)
        
        self.export_packages_btn = QPushButton("Export Package List")
        self.export_packages_btn.clicked.connect(self._export_packages)
        controls_layout.addWidget(self.export_packages_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        return tab
    
    def _create_license_tab(self) -> QWidget:
        """Create the license information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # License information
        license_group = QGroupBox("License Information")
        license_layout = QVBoxLayout(license_group)
        
        self.license_text = QTextEdit()
        self.license_text.setReadOnly(True)
        self.license_text.setFont(QFont("Consolas", 9))
        self.license_text.setPlainText("""
MIT License

Copyright (c) 2024 API Server Manager

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
        """.strip())
        
        license_layout.addWidget(self.license_text)
        layout.addWidget(license_group)
        
        # Third-party licenses
        third_party_group = QGroupBox("Third-Party Licenses")
        third_party_layout = QVBoxLayout(third_party_group)
        
        self.third_party_text = QTextEdit()
        self.third_party_text.setReadOnly(True)
        self.third_party_text.setMaximumHeight(200)
        self.third_party_text.setFont(QFont("Consolas", 9))
        self.third_party_text.setPlainText("""
This software uses the following third-party libraries:

• PyQt5 - GPL v3 License
• AioHTTP - Apache License 2.0
• Peewee - MIT License
• PyJWT - MIT License
• bcrypt - Apache License 2.0
• psutil - BSD License
• python-dotenv - BSD License

For detailed license information, please refer to the individual
package documentation and license files.
        """.strip())
        
        third_party_layout.addWidget(self.third_party_text)
        layout.addWidget(third_party_group)
        
        return tab
    
    def refresh_data(self):
        """Refresh about data."""
        try:
            # Load system information
            self._load_system_info()
            
            # Load package information
            self._load_package_info()
            
            self.update_status("About data refreshed")
            
        except Exception as e:
            self.show_error(f"Failed to refresh about data: {e}")
    
    def _load_system_info(self):
        """Load system information."""
        try:
            import platform
            import sys
            import psutil
            import os
            
            # Operating system information
            self.os_name_label.setText(f"{platform.system()} {platform.release()}")
            self.os_version_label.setText(platform.version())
            self.os_arch_label.setText(platform.machine())
            self.os_platform_label.setText(platform.platform())
            
            # Python information
            self.python_version_label.setText(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
            self.python_executable_label.setText(sys.executable)
            self.python_path_label.setText("; ".join(sys.path[:3]) + "...")
            
            # Hardware information
            self.cpu_count_label.setText(str(psutil.cpu_count()))
            
            memory = psutil.virtual_memory()
            self.memory_total_label.setText(f"{memory.total // (1024**3)} GB")
            self.memory_available_label.setText(f"{memory.available // (1024**3)} GB")
            
            # Environment variables
            env_vars = []
            for key, value in os.environ.items():
                if key in ['PATH', 'PYTHONPATH', 'PYTHONHOME', 'HOME', 'USER', 'SHELL']:
                    env_vars.append(f"{key}={value}")
            
            self.env_text.setPlainText("\n".join(env_vars))
            
            # Store system info
            self.system_info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "cpu_count": psutil.cpu_count(),
                "memory_total": memory.total,
                "memory_available": memory.available
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load system info: {e}")
    
    def _load_package_info(self):
        """Load package information."""
        try:
            import pkg_resources
            
            packages = []
            for package in pkg_resources.working_set:
                packages.append(f"{package.project_name}=={package.version}")
            
            # Sort packages alphabetically
            packages.sort()
            
            self.packages_text.setPlainText("\n".join(packages))
            
            # Store package info
            self.package_info = {pkg.project_name: pkg.version for pkg in pkg_resources.working_set}
            
        except Exception as e:
            self.logger.error(f"Failed to load package info: {e}")
            self.packages_text.setPlainText("Failed to load package information.")
    
    def _check_for_updates(self):
        """Check for application updates."""
        try:
            self.update_status_label.setText("Checking for updates...")
            self.check_update_btn.setEnabled(False)
            
            # Simulate update check (placeholder)
            QTimer.singleShot(2000, self._update_check_complete)
            
        except Exception as e:
            self.logger.error(f"Failed to check for updates: {e}")
            self.update_status_label.setText("Update check failed")
            self.check_update_btn.setEnabled(True)
    
    def _update_check_complete(self):
        """Complete the update check."""
        try:
            # Placeholder - in real implementation, this would check for actual updates
            self.update_status_label.setText("No updates available")
            self.update_info_text.setPlainText("You are running the latest version of the application.")
            self.check_update_btn.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Failed to complete update check: {e}")
    
    def _refresh_packages(self):
        """Refresh package list."""
        self._load_package_info()
        self.show_success("Package list refreshed")
    
    def _export_packages(self):
        """Export package list to file."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            from datetime import datetime
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Package List",
                f"packages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.packages_text.toPlainText())
                
                self.show_success(f"Package list exported to {filename}")
            
        except Exception as e:
            self.show_error(f"Failed to export package list: {e}")
    
    def get_tab_data(self) -> Dict[str, Any]:
        """Get about tab data."""
        return {
            **super().get_tab_data(),
            "system_info": self.system_info,
            "package_count": len(self.package_info),
            "app_name": APP_NAME,
            "app_version": APP_VERSION
        }
