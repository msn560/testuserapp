"""
App module - Ana kontrol sınıfı

Bu modül uygulamanın ana kontrol sınıfını içerir.
Uygulama başlatma, durdurma ve genel yönetim işlemlerini yönetir.
"""

import asyncio
import sys
import signal
from typing import Optional, Dict, Any
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QObject, pyqtSignal

from .core.settings import settings
from .core.config_manager import config_manager
from .core.constants import APP_NAME, APP_VERSION
from .utils.logger import Logger, logger
from .ui.main_window import MainWindow
from .ui.splash_screen import SplashScreen
from .api.server_manager import APIServerManager
from .services.scheduler_service import SchedulerService


class APIServerManagerApp(QObject):
    """
    Ana uygulama sınıfı
    
    Uygulamanın ana kontrol sınıfı. GUI ve API server'ı yönetir.
    """
    
    # Signals
    app_started = pyqtSignal()
    app_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        """Uygulama sınıfını başlat"""
        super().__init__()
        
        self.logger = Logger(__name__)
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.splash_screen: Optional[SplashScreen] = None
        self.login_window: Optional['LoginWindow'] = None
        self.api_server: Optional[APIServerManager] = None
        self.scheduler: Optional[SchedulerService] = None
        
        self.is_running = False
        self.startup_errors = []
        
        # Signal bağlantıları
        self.app_started.connect(self._on_app_started)
        self.app_stopped.connect(self._on_app_stopped)
        self.error_occurred.connect(self._on_error_occurred)
    
    def initialize(self) -> bool:
        """
        Uygulamayı başlat
        
        Returns:
            Başlatma başarılı mı
        """
        try:
            self.logger.info(f"{APP_NAME} v{APP_VERSION} başlatılıyor...")
            
            # Konfigürasyonu yükle
            if not self._load_configuration():
                return False
            
            # QApplication oluştur
            if not self._create_application():
                return False
            
            # Config'den UI ayarlarını al ve splash screen göster
            from ..core.config_manager import get_config_value
            show_splash = get_config_value("ui.show_splash_screen", True)
            if show_splash:
                self._show_splash_screen()
            else:
                # Splash screen gösterilmiyorsa direkt login window'u göster
                self._show_login_window()
            
            # API server'ı başlat
            if not self._start_api_server():
                return False
            
            # Scheduler'ı başlat
            if not self._start_scheduler():
                return False
            
            # Signal handler'ları ayarla
            self._setup_signal_handlers()
            
            self.is_running = True
            self.app_started.emit()
            
            self.logger.info("Uygulama başarıyla başlatıldı")
            return True
            
        except Exception as e:
            self.logger.error(f"Uygulama başlatılamadı: {e}")
            self.startup_errors.append(str(e))
            return False
    
    def run(self) -> int:
        """
        Uygulamayı çalıştır
        
        Returns:
            Çıkış kodu
        """
        try:
            if not self.is_running:
                self.logger.error("Uygulama başlatılmamış")
                return 1
            
            # Splash screen'i gizle
            if self.splash_screen:
                self.splash_screen.close()
                self.splash_screen = None
            
            # Ana pencereyi göster (eğer henüz gösterilmemişse)
            if self.main_window and not self.main_window.isVisible():
                self.main_window.show()
                self.logger.info("Main window shown from run()")
            
            # Event loop'u başlat
            self.logger.info("Starting event loop...")
            return self.app.exec_()
            
        except Exception as e:
            self.logger.error(f"Uygulama çalıştırılamadı: {e}")
            return 1
    
    def shutdown(self) -> None:
        """Uygulamayı kapat"""
        try:
            self.logger.info("Uygulama kapatılıyor...")
            
            self.is_running = False
            
            # Önce tüm child widget'ları temizle
            if self.main_window:
                try:
                    # Main window'daki tüm tab'ları temizle
                    if hasattr(self.main_window, '_cleanup_all_tabs'):
                        self.main_window._cleanup_all_tabs()
                    
                    # Main window'u kapat
                    self.main_window.close()
                    self.main_window = None
                except Exception as e:
                    self.logger.warning(f"Main window kapatılırken hata: {e}")
            
            # Login window'u temizle
            if self.login_window:
                try:
                    self.login_window.close()
                    self.login_window = None
                except Exception as e:
                    self.logger.warning(f"Login window kapatılırken hata: {e}")
            
            # Splash screen'i temizle
            if self.splash_screen:
                try:
                    self.splash_screen.close()
                    self.splash_screen = None
                except Exception as e:
                    self.logger.warning(f"Splash screen kapatılırken hata: {e}")
            
            # Scheduler'ı durdur
            if self.scheduler:
                try:
                    self.scheduler.stop()
                    self.scheduler = None
                except Exception as e:
                    self.logger.warning(f"Scheduler durdurulurken hata: {e}")
            
            # API server'ı durdur
            if self.api_server:
                try:
                    self.api_server.stop_server()
                    self.api_server = None
                except Exception as e:
                    self.logger.warning(f"API server durdurulurken hata: {e}")
            
            # Signal'ları temizle
            try:
                self.app_started.disconnect()
                self.app_stopped.disconnect()
                self.error_occurred.disconnect()
            except:
                pass  # Signal'lar zaten kesilmiş olabilir
            
            # QApplication'ı kapat (en son)
            if self.app:
                try:
                    self.app.quit()
                    # QApplication'ı hemen None yapma, quit() işleminin tamamlanmasını bekle
                except Exception as e:
                    self.logger.warning(f"QApplication kapatılırken hata: {e}")
            
            self.logger.info("Uygulama kapatıldı")
            
        except Exception as e:
            self.logger.error(f"Uygulama kapatılamadı: {e}")
    
    def _load_configuration(self) -> bool:
        """
        Konfigürasyonu yükle
        
        Returns:
            Yükleme başarılı mı
        """
        try:
            # Config dosyasının varlığını kontrol et
            config_file_path = Path("data/config.json")
            
            if not config_file_path.exists():
                self.logger.info("Config dosyası bulunamadı, varsayılan ayarlarla oluşturuluyor...")
                # Varsayılan config'i oluştur ve kaydet
                default_config = settings.get_all_settings()
                config_manager.save_config(default_config)
                self.logger.info("Varsayılan config dosyası oluşturuldu")
            else:
                self.logger.info("Config dosyası bulundu, yükleniyor...")
            
            # Config dosyasını yükle
            config = config_manager.load_config()
            
            # Settings'i config'den güncelle
            settings.update_from_dict(config)
            
            # Konfigürasyonu doğrula
            errors = config_manager.validate_config()
            if errors:
                self.logger.warning(f"Konfigürasyon uyarıları: {', '.join(errors)}")
            
            self.logger.info("Konfigürasyon başarıyla yüklendi")
            
            # Veritabanını başlat
            self._initialize_database()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon yüklenemedi: {e}")
            return False
    
    def _initialize_database(self) -> None:
        """
        Veritabanını başlat ve tabloları oluştur
        
        Veritabanı dosyası yoksa otomatik oluşturur.
        """
        try:
            from src.db.migrations import MigrationManager
            
            # Migration manager'ı başlat
            migration_manager = MigrationManager()
            
            # Veritabanı dosyası var mı kontrol et
            from src.core.constants import DATABASE_FILE
            db_path = Path(DATABASE_FILE)
            
            if not db_path.exists():
                self.logger.info("Veritabanı dosyası bulunamadı, oluşturuluyor...")
                # Tabloları oluştur
                if migration_manager.create_tables():
                    self.logger.info("Veritabanı ve tablolar başarıyla oluşturuldu")
                else:
                    self.logger.error("Veritabanı oluşturulamadı")
            else:
                self.logger.info("Veritabanı dosyası mevcut")
                
        except Exception as e:
            self.logger.error(f"Veritabanı başlatılamadı: {e}")
    
    def _create_application(self) -> bool:
        """
        QApplication oluştur
        
        Returns:
            Oluşturma başarılı mı
        """
        try:
            # QApplication oluştur
            self.app = QApplication(sys.argv)
            self.app.setApplicationName(APP_NAME)
            self.app.setApplicationVersion(APP_VERSION)
            self.app.setOrganizationName("API Server Manager")
            
            # Debug mode'u config'den al
            from ..core.config_manager import get_config_value
            debug_mode = get_config_value("app.debug", False)
            if debug_mode:
                self.app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
                self.app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
                self.logger.info("Debug mode enabled")
            
            # Tema ayarla
            self._apply_theme()
            
            self.logger.info("QApplication oluşturuldu")
            return True
            
        except Exception as e:
            self.logger.error(f"QApplication oluşturulamadı: {e}")
            return False
    
    def _show_splash_screen(self) -> None:
        """Splash screen göster"""
        try:
            self.splash_screen = SplashScreen()
            self.splash_screen.show()
            
            # Splash screen artık QTimer.singleShot ile kapanıyor
            # Signal bağlantısı kaldırıldı
            
            # Fallback timer (in case signal doesn't work) - config'den süreyi al
            from ..core.config_manager import get_config_value
            splash_duration = get_config_value("ui.splash_screen_duration", 3000)
            QTimer.singleShot(
                splash_duration,
                self._on_splash_finished
            )
            
            self.logger.info("Splash screen gösterildi")
            
        except Exception as e:
            self.logger.error(f"Splash screen gösterilemedi: {e}")
    
    def _on_splash_finished(self) -> None:
        """Splash screen tamamlandığında çağrılır"""
        try:
            if self.splash_screen:
                self.splash_screen.close()
                self.splash_screen = None
                self.logger.info("Splash screen kapatıldı")
            
            # Login window'u göster
            self._show_login_window()
            
        except Exception as e:
            self.logger.error(f"Splash screen kapatılamadı: {e}")
    
    def _show_login_window(self) -> None:
        """Login window'u göster"""
        try:
            from .ui.login_window import LoginWindow
            
            self.login_window = LoginWindow()
            
            # Login başarılı olduğunda ana pencereyi göster
            self.login_window.login_successful.connect(self._on_login_successful)
            
            self.login_window.show()
            self.logger.info("Login window gösterildi")
            
        except Exception as e:
            self.logger.error(f"Login window gösterilemedi: {e}")
            # Login window gösterilemezse direkt ana pencereyi göster
            self._create_and_show_main_window()
    
    def _on_login_successful(self, user_data: dict) -> None:
        """Login başarılı olduğunda çağrılır"""
        try:
            self.logger.info(f"Login başarılı: {user_data.get('username', 'Unknown')}")
            
            # Login window'u kapat
            if self.login_window:
                self.login_window.close()
                self.login_window = None
            
            # Ana pencereyi göster
            self._create_and_show_main_window()
            
        except Exception as e:
            self.logger.error(f"Login başarılı işlemi hatası: {e}")
    
    def _create_and_show_main_window(self) -> None:
        """Ana pencereyi oluştur ve göster"""
        try:
            if self._create_main_window():
                self.main_window.show()
                self.logger.info("Ana pencere gösterildi")
            else:
                self.logger.error("Ana pencere oluşturulamadı")
                self.app.quit()
        except Exception as e:
            self.logger.error(f"Ana pencere gösterilemedi: {e}")
            self.app.quit()
    
    def _create_main_window(self) -> bool:
        """
        Ana pencereyi oluştur
        
        Returns:
            Oluşturma başarılı mı
        """
        try:
            self.main_window = MainWindow()
            
            # Config'den pencere boyutlarını ayarla
            from ..core.config_manager import get_config_value
            self.main_window.resize(
                get_config_value("ui.window_width", 1360),
                get_config_value("ui.window_height", 840)
            )
            
            # Minimum boyutları ayarla
            self.main_window.setMinimumSize(
                get_config_value("ui.window_min_width", 800),
                get_config_value("ui.window_min_height", 600)
            )
            
            self.logger.info("Ana pencere oluşturuldu")
            return True
            
        except Exception as e:
            self.logger.error(f"Ana pencere oluşturulamadı: {e}")
            return False
    
    def _start_api_server(self) -> bool:
        """
        API server'ı başlat
        
        Returns:
            Başlatma başarılı mı
        """
        try:
            if not settings.features.api_management:
                self.logger.info("API management devre dışı")
                return True
            
            self.api_server = APIServerManager()
            
            # Server'ı başlat
            if settings.server.auto_start:
                asyncio.create_task(self.api_server.start())
                self.logger.info("API server otomatik başlatıldı")
            else:
                self.logger.info("API server hazır (manuel başlatma)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"API server başlatılamadı: {e}")
            return False
    
    def _start_scheduler(self) -> bool:
        """
        Scheduler'ı başlat
        
        Returns:
            Başlatma başarılı mı
        """
        try:
            self.scheduler = SchedulerService()
            self.scheduler.start()
            
            self.logger.info("Scheduler başlatıldı")
            return True
            
        except Exception as e:
            self.logger.error(f"Scheduler başlatılamadı: {e}")
            return False
    
    def _setup_signal_handlers(self) -> None:
        """Signal handler'ları ayarla"""
        try:
            # SIGINT (Ctrl+C) handler
            signal.signal(signal.SIGINT, self._signal_handler)
            
            # SIGTERM handler
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.logger.info("Signal handler'lar ayarlandı")
            
        except Exception as e:
            self.logger.error(f"Signal handler'lar ayarlanamadı: {e}")
    
    def _signal_handler(self, signum, frame):
        """Signal handler"""
        self.logger.info(f"Signal alındı: {signum}")
        self.shutdown()
        sys.exit(0)
    
    def _apply_theme(self) -> None:
        """Tema uygula"""
        try:
            # Config'den tema değerini al
            from ..core.config_manager import get_config_value
            theme = get_config_value("ui.theme", "dark")
            
            # Tema dosyası yolu
            theme_file = Path(f"data/resources/styles/themes/{theme}.qss")
            
            if theme_file.exists():
                with open(theme_file, 'r', encoding='utf-8') as f:
                    style = f.read()
                
                self.app.setStyleSheet(style)
                self.logger.info(f"Tema uygulandı: {theme}")
            else:
                self.logger.warning(f"Tema dosyası bulunamadı: {theme_file}")
                
        except Exception as e:
            self.logger.error(f"Tema uygulanamadı: {e}")
    
    def _on_app_started(self) -> None:
        """Uygulama başlatıldığında çağrılır"""
        self.logger.info("Uygulama başlatıldı signal'i alındı")
    
    def _on_app_stopped(self) -> None:
        """Uygulama durdurulduğunda çağrılır"""
        self.logger.info("Uygulama durduruldu signal'i alındı")
    
    def _on_error_occurred(self, error_message: str) -> None:
        """Hata oluştuğunda çağrılır"""
        self.logger.error(f"Uygulama hatası: {error_message}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Uygulama durumunu al
        
        Returns:
            Uygulama durumu
        """
        return {
            "is_running": self.is_running,
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "api_server_running": self.api_server.is_running if self.api_server else False,
            "scheduler_running": self.scheduler.is_running if self.scheduler else False,
            "startup_errors": self.startup_errors,
            "config_valid": len(config_manager.validate_config()) == 0
        }
    
    def restart_api_server(self) -> bool:
        """
        API server'ı yeniden başlat
        
        Returns:
            Yeniden başlatma başarılı mı
        """
        try:
            if not self.api_server:
                return False
            
            # Server'ı durdur
            asyncio.create_task(self.api_server.stop())
            
            # Kısa bir bekleme
            asyncio.sleep(1)
            
            # Server'ı başlat
            asyncio.create_task(self.api_server.start())
            
            self.logger.info("API server yeniden başlatıldı")
            return True
            
        except Exception as e:
            self.logger.error(f"API server yeniden başlatılamadı: {e}")
            return False
    
    def reload_configuration(self) -> bool:
        """
        Konfigürasyonu yeniden yükle
        
        Returns:
            Yeniden yükleme başarılı mı
        """
        try:
            # Konfigürasyonu yükle
            if not self._load_configuration():
                return False
            
            # Tema uygula
            self._apply_theme()
            
            # Ana pencereyi güncelle
            if self.main_window:
                self.main_window.reload_configuration()
            
            self.logger.info("Konfigürasyon yeniden yüklendi")
            return True
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon yeniden yüklenemedi: {e}")
            return False


def main() -> int:
    """
    Ana fonksiyon
    
    Returns:
        Çıkış kodu
    """
    app = None
    try:
        # Global logging'i yapılandır
        Logger.configure_global_logging()
        
        # Uygulama instance'ı oluştur
        app = APIServerManagerApp()
        
        # Uygulamayı başlat
        if not app.initialize():
            logger.error("Uygulama başlatılamadı")
            return 1
        
        # Uygulamayı çalıştır
        exit_code = app.run()
        
        return exit_code
        
    except KeyboardInterrupt:
        logger.info("Kullanıcı tarafından durduruldu")
        return 0
    except Exception as e:
        logger.error(f"Uygulama hatası: {e}")
        return 1
    finally:
        # Uygulamayı güvenli şekilde kapat
        if app:
            try:
                app.shutdown()
            except Exception as e:
                logger.error(f"Shutdown hatası: {e}")


if __name__ == "__main__":
    sys.exit(main())
