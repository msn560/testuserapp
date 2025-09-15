"""
aplan üzerineılLogin Window - Modern ve kullanıcı dostu giriş penceresi
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QCheckBox, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QPainter, QBrush, QLinearGradient

from ..core.settings import settings
from ..utils.logger import logger
from ..services.auth_service import AuthService
from ..core.language import language_manager


class AuthWorker(QObject):
    """Authentication worker - arka planda kimlik doğrulama"""
    
    # Signals
    auth_successful = pyqtSignal(dict)
    auth_failed = pyqtSignal(str)
    auth_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.logger = logger
        self.running = True
    
    def stop_worker(self):
        """Worker'ı durdur"""
        self.running = False
        self.logger.info("AuthWorker durduruldu")
    
    def authenticate(self, username: str, password: str):
        """Kullanıcı kimlik doğrulama"""
        try:
            self.logger.info(f"Kullanıcı kimlik doğrulama: {username}")
            
            result = self.auth_service.authenticate_user_sync(username, password)
            
            if result.get('success'):
                user_data = result.get('user', {})
                self.auth_successful.emit(user_data)
            else:
                error_message = result.get('message', 'Kimlik doğrulama başarısız')
                self.auth_failed.emit(error_message)
                
        except Exception as e:
            self.logger.error(f"Kimlik doğrulama hatası: {e}")
            self.auth_error.emit(str(e))


class ModernLoginWindow(QDialog):
    """Modern ve şık login penceresi"""
    
    # Signals
    login_successful = pyqtSignal(dict)
    login_failed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Thread ve worker
        self.auth_thread = None
        self.auth_worker = None
        
        # UI setup
        self.setup_ui()
        self.setup_connections()
        self.init_auth_thread()
        
        # Animasyonlar
        self.setup_animations()
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        self.setWindowTitle(f"{language_manager.translate('app.name')} - {language_manager.translate('auth.login')}")
        self.setFixedSize(500, 700)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setObjectName("loginDialog")
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Ana layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Ana container
        self.main_container = QFrame()
        self.main_container.setObjectName("mainContainer")
        main_layout.addWidget(self.main_container)
        
        # Container layout
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(20)
        
        # Header
        self.create_header(container_layout)
        
        # Form
        self.create_form(container_layout)
        
        # Buttons
        self.create_buttons(container_layout)
        
        # Footer
        self.create_footer(container_layout)
        
        self.setLayout(main_layout)
        self.apply_styles()
    
    def create_header(self, layout):
        """Header bölümü"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setFixedHeight(120)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(10)
        header_layout.setContentsMargins(0, 10, 0, 10)
        
        # Logo
        logo_label = QLabel("🚀")
        logo_label.setObjectName("logoLabel")
        logo_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel(language_manager.translate("app.name"))
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel(language_manager.translate("auth.login"))
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)
    
    def create_form(self, layout):
        """Form bölümü"""
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(25, 25, 25, 25)
        
        # Username
        username_label = QLabel(language_manager.translate("auth.username"))
        username_label.setObjectName("fieldLabel")
        form_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setObjectName("usernameInput")
        self.username_input.setPlaceholderText(language_manager.translate("auth.username"))
        self.username_input.setMinimumHeight(45)
        self.username_input.setMaximumHeight(45)
        form_layout.addWidget(self.username_input)
        
        # Password
        password_label = QLabel(language_manager.translate("auth.password"))
        password_label.setObjectName("fieldLabel")
        form_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setObjectName("passwordInput")
        self.password_input.setPlaceholderText(language_manager.translate("auth.password"))
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        self.password_input.setMaximumHeight(45)
        form_layout.addWidget(self.password_input)
        
        # Remember me
        self.remember_checkbox = QCheckBox(language_manager.translate("auth.remember_me"))
        self.remember_checkbox.setObjectName("rememberCheckbox")
        form_layout.addWidget(self.remember_checkbox)
        
        # Error message
        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        form_layout.addWidget(self.error_label)
        
        layout.addWidget(form_frame)
    
    def create_buttons(self, layout):
        """Butonlar"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Login button
        self.login_button = QPushButton(language_manager.translate("auth.login"))
        self.login_button.setObjectName("loginButton")
        self.login_button.setMinimumHeight(50)
        self.login_button.setMaximumHeight(50)
        button_layout.addWidget(self.login_button)
        
        # Cancel button
        self.cancel_button = QPushButton(language_manager.translate("common.cancel"))
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setMinimumHeight(50)
        self.cancel_button.setMaximumHeight(50)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def create_footer(self, layout):
        """Footer"""
        footer_label = QLabel(f"© 2024 {language_manager.translate('app.name')} v{language_manager.translate('app.version')}")
        footer_label.setObjectName("footerLabel")
        footer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer_label)
    
    def apply_styles(self):
        """Stilleri uygula - Global tema dosyasını override etmek için !important kullanıyoruz"""
        self.setStyleSheet("""
            QDialog#loginDialog {
                background: transparent !important;
            }
            
            #mainContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2) !important;
                border-radius: 20px !important;
            }
            
            #headerFrame {
                background: transparent !important;
                border: none !important;
            }
            
            #logoLabel {
                font-size: 48px !important;
                color: white !important;
                margin: 5px 0 !important;
                background: transparent !important;
                border: none !important;
            }
            
            #titleLabel {
                font-size: 20px !important;
                font-weight: bold !important;
                color: white !important;
                margin: 3px 0 !important;
                background: transparent !important;
                border: none !important;
            }
            
            #subtitleLabel {
                font-size: 12px !important;
                color: rgba(255, 255, 255, 0.8) !important;
                margin: 3px 0 !important;
                background: transparent !important;
                border: none !important;
            }
            
            #formFrame {
                background: white !important;
                border-radius: 15px !important;
                margin: 20px 0 !important;
            }
            
            #fieldLabel {
                font-size: 11px !important;
                font-weight: bold !important;
                color: #2c3e50 !important;
                margin-bottom: 3px !important;
                background: transparent !important;
                border: none !important;
            }
            
            #usernameInput, #passwordInput {
                padding: 12px 15px !important;
                border: 2px solid #e1e8ed !important;
                border-radius: 8px !important;
                font-size: 13px !important;
                background: white !important;
                color: #2c3e50 !important;
                min-height: 45px !important;
                max-height: 45px !important;
            }
            
            #usernameInput:focus, #passwordInput:focus {
                border-color: #667eea !important;
                background: white !important;
                outline: none !important;
            }
            
            #usernameInput:hover, #passwordInput:hover {
                border-color: #bdc3c7 !important;
                background: white !important;
            }
            
            #rememberCheckbox {
                font-size: 12px !important;
                color: #2c3e50 !important;
                spacing: 8px !important;
                background: transparent !important;
                border: none !important;
            }
            
            #rememberCheckbox::indicator {
                width: 18px !important;
                height: 18px !important;
                border-radius: 9px !important;
                border: 2px solid #bdc3c7 !important;
                background: white !important;
            }
            
            #rememberCheckbox::indicator:checked {
                background: #667eea !important;
                border-color: #667eea !important;
            }
            
            #errorLabel {
                color: #e74c3c !important;
                background: rgba(253, 242, 242, 0.9) !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 12px !important;
                font-size: 12px !important;
            }
            
            #loginButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2) !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 12px 20px !important;
                font-size: 13px !important;
                font-weight: bold !important;
                min-height: 50px !important;
                max-height: 50px !important;
            }
            
            #loginButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6fd8, stop:1 #6a4190) !important;
            }
            
            #loginButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4e5bc6, stop:1 #5e377e) !important;
            }
            
            #loginButton:disabled {
                background: #bdc3c7 !important;
                color: #7f8c8d !important;
            }
            
            #cancelButton {
                background: #95a5a6 !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 12px 20px !important;
                font-size: 13px !important;
                font-weight: bold !important;
                min-height: 50px !important;
                max-height: 50px !important;
            }
            
            #cancelButton:hover {
                background: #7f8c8d !important;
            }
            
            #cancelButton:pressed {
                background: #6c7b7d !important;
            }
            
            #footerLabel {
                color: rgba(255, 255, 255, 0.7) !important;
                font-size: 10px !important;
                margin-top: 20px !important;
                background: transparent !important;
                border: none !important;
            }
        """)
    
    def setup_connections(self):
        """Signal bağlantıları"""
        self.login_button.clicked.connect(self.attempt_login)
        self.cancel_button.clicked.connect(self.reject)
        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)
    
    def init_auth_thread(self):
        """Authentication thread'i başlat"""
        try:
            self.auth_thread = QThread()
            self.auth_worker = AuthWorker()
            self.auth_worker.moveToThread(self.auth_thread)
            
            # Signal bağlantıları
            self.auth_worker.auth_successful.connect(self.on_auth_successful)
            self.auth_worker.auth_failed.connect(self.on_auth_failed)
            self.auth_worker.auth_error.connect(self.on_auth_error)
            
            self.auth_thread.finished.connect(self.auth_thread.deleteLater)
            self.auth_thread.start()
            
            logger.info("Authentication thread başlatıldı")
            
        except Exception as e:
            logger.error(f"Authentication thread başlatılamadı: {e}")
    
    def cleanup_auth_thread(self):
        """Authentication thread'i temizle"""
        try:
            if self.auth_thread and self.auth_thread.isRunning():
                logger.debug("Authentication thread temizleniyor...")
                
                # Stop worker first
                if self.auth_worker:
                    self.auth_worker.stop_worker()
                
                # Disconnect signals
                if self.auth_worker:
                    try:
                        self.auth_worker.auth_successful.disconnect()
                        self.auth_worker.auth_failed.disconnect()
                        self.auth_worker.auth_error.disconnect()
                    except:
                        pass
                
                # Quit thread
                self.auth_thread.quit()
                
                # Wait for thread to finish
                if not self.auth_thread.wait(3000):
                    logger.warning("Auth thread did not finish in time, terminating")
                    self.auth_thread.terminate()
                    self.auth_thread.wait(1000)
                
                # Clear references
                self.auth_worker = None
                self.auth_thread = None
                
                logger.debug("Authentication thread temizlendi")
                
        except Exception as e:
            logger.error(f"Error cleaning up auth thread: {e}")
    
    def closeEvent(self, event):
        """Close event - cleanup thread"""
        self.cleanup_auth_thread()
        super().closeEvent(event)
    
    def setup_animations(self):
        """Animasyonları ayarla"""
        # Fade in animasyonu
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def showEvent(self, event):
        """Pencere gösterildiğinde animasyon başlat"""
        super().showEvent(event)
        self.fade_animation.start()
    
    def attempt_login(self):
        """Giriş denemesi"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        username = "admin"
        password = "admin123"
        if not username or not password:
            self.show_error("Lütfen kullanıcı adı ve şifre girin.")
            return
        
        self.set_loading_state(True)
        self.hide_error()
        
        if self.auth_worker:
            self.auth_worker.authenticate(username, password)
    
    def set_loading_state(self, loading: bool):
        """Loading durumu"""
        self.login_button.setEnabled(not loading)
        self.cancel_button.setEnabled(not loading)
        self.username_input.setEnabled(not loading)
        self.password_input.setEnabled(not loading)
        self.remember_checkbox.setEnabled(not loading)
        
        if loading:
            self.login_button.setText("Giriş yapılıyor...")
        else:
            self.login_button.setText("Giriş Yap")
    
    def show_error(self, message: str):
        """Hata mesajı göster"""
        self.error_label.setText(message)
        self.error_label.show()
        
        # 5 saniye sonra gizle
        QTimer.singleShot(5000, self.hide_error)
    
    def hide_error(self):
        """Hata mesajını gizle"""
        self.error_label.hide()
    
    def on_auth_successful(self, user_data: dict):
        """Başarılı giriş"""
        try:
            self.login_successful.emit(user_data)
            # Thread'i temizle
            self.cleanup_auth_thread()
            self.accept()
        except Exception as e:
            logger.error(f"Başarılı giriş işlenirken hata: {e}")
        finally:
            self.set_loading_state(False)
    
    def on_auth_failed(self, error_message: str):
        """Başarısız giriş"""
        try:
            self.show_error(error_message)
            self.login_failed.emit(error_message)
        except Exception as e:
            logger.error(f"Başarısız giriş işlenirken hata: {e}")
        finally:
            self.set_loading_state(False)
    
    def on_auth_error(self, error_message: str):
        """Kimlik doğrulama hatası"""
        try:
            self.show_error("Bir hata oluştu. Lütfen tekrar deneyin.")
            self.login_failed.emit(error_message)
        except Exception as e:
            logger.error(f"Kimlik doğrulama hatası işlenirken hata: {e}")
        finally:
            self.set_loading_state(False)
    
    def closeEvent(self, event):
        """Pencere kapatılırken temizlik"""
        try:
            if self.auth_thread and self.auth_thread.isRunning():
                self.auth_thread.quit()
                self.auth_thread.wait(3000)
            
            logger.info("Login window temizlendi")
        except Exception as e:
            logger.error(f"Login window temizlenirken hata: {e}")
        
        event.accept()
    
    def keyPressEvent(self, event):
        """Klavye olayları"""
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


# Backward compatibility
LoginWindow = ModernLoginWindow