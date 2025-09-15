"""
Splash Screen module - Uygulama başlangıç ekranı

Bu modül uygulamanın başlangıç ekranını yönetir.
"""

from PyQt5.QtWidgets import QSplashScreen, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor

from ..core.settings import settings
from ..utils.logger import logger


class SplashWorker(QObject):
    """
    Splash screen worker that runs in a separate thread.
    """
    
    # Signals for GUI communication
    progress_updated = pyqtSignal(int, str)  # progress, status
    loading_completed = pyqtSignal()         # loading completed
    
    def __init__(self):
        super().__init__()
        self.logger = logger
        self.running = False
    
    def start_loading(self):
        """Start loading process in background thread."""
        try:
            self.running = True
            self.logger.info("Splash loading started")
            
            # Simulate loading steps
            steps = [
                (10, "Initializing..."),
                (25, "Loading configuration..."),
                (40, "Connecting to database..."),
                (60, "Loading modules..."),
                (80, "Preparing interface..."),
                (95, "Finalizing..."),
                (100, "Ready!")
            ]
            
            for progress, status in steps:
                if not self.running:
                    break
                
                self.progress_updated.emit(progress, status)
                
                # Simulate work (non-blocking)
                import time
                time.sleep(0.1)  # Short delay
            
            if self.running:
                self.loading_completed.emit()
                
        except Exception as e:
            self.logger.error(f"Splash loading error: {e}")
    
    def stop_loading(self):
        """Stop loading process."""
        self.running = False
        self.logger.info("Splash loading stopped")


class SplashScreen(QSplashScreen):
    """Uygulama başlangıç ekranı"""
    
    def __init__(self, parent=None):
        """
        SplashScreen'i başlat
        
        Args:
            parent: Parent widget
        """
        # Splash screen için pixmap oluştur
        pixmap = self._create_splash_pixmap()
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Progress tracking
        self.progress = 0
        self.max_progress = 100
        self.status_text = "Başlatılıyor..."
        
        # Thread and worker for loading
        self.loading_thread = None
        self.loading_worker = None
        
        # Show splash screen
        self.show()
        QApplication.processEvents()
        
        # Initialize loading thread
        self._init_loading_thread()
    
    def _init_loading_thread(self):
        """Initialize the loading thread."""
        try:
            # Create thread and worker
            self.loading_thread = QThread()
            self.loading_worker = SplashWorker()
            
            # Move worker to thread
            self.loading_worker.moveToThread(self.loading_thread)
            
            # Connect signals
            self.loading_worker.progress_updated.connect(self._on_progress_updated)
            self.loading_worker.loading_completed.connect(self._on_loading_completed)
            
            # Connect thread finished signal
            self.loading_thread.finished.connect(self.loading_thread.deleteLater)
            
            # Start thread
            self.loading_thread.start()
            
            # Start loading process
            self.loading_worker.start_loading()
            
            logger.info("Loading thread initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize loading thread: {e}")
    
    def _on_progress_updated(self, progress: int, status: str):
        """Handle progress update from worker thread."""
        try:
            self.progress = progress
            self.status_text = status
            self._update_progress_bar()
            QApplication.processEvents()
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
    
    def _on_loading_completed(self):
        """Handle loading completion from worker thread."""
        try:
            self.progress = 100
            self.status_text = "Ready!"
            self._update_progress_bar()
            QApplication.processEvents()
            
            # Auto-close after a short delay
            QTimer.singleShot(500, self.close)
            
        except Exception as e:
            logger.error(f"Error handling loading completion: {e}")
        
    def _create_splash_pixmap(self) -> QPixmap:
        """
        Splash screen için pixmap oluştur
        
        Returns:
            QPixmap objesi
        """
        # 400x300 boyutunda pixmap oluştur
        pixmap = QPixmap(400, 300)
        pixmap.fill(QColor(30, 30, 30))  # Koyu gri arka plan
        
        # Painter ile çizim yap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Arka plan gradient
        from PyQt5.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, 0, 300)
        gradient.setColorAt(0, QColor(45, 45, 45))
        gradient.setColorAt(1, QColor(20, 20, 20))
        painter.fillRect(0, 0, 400, 300, gradient)
        
        # Başlık
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        painter.drawText(50, 80, "API Server Manager")
        
        # Alt başlık
        painter.setFont(QFont("Arial", 12))
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(50, 110, "Sistem başlatılıyor...")
        
        # Progress bar arka planı
        painter.setPen(QColor(100, 100, 100))
        painter.setBrush(QColor(60, 60, 60))
        painter.drawRoundedRect(50, 200, 300, 20, 10, 10)
        
        # Progress bar dolgu
        painter.setBrush(QColor(0, 150, 255))
        painter.drawRoundedRect(50, 200, 0, 20, 10, 10)
        
        # Status text
        painter.setPen(QColor(180, 180, 180))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(50, 240, "Başlatılıyor...")
        
        # Version info
        painter.setPen(QColor(120, 120, 120))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(50, 270, "v1.0.0")
        
        painter.end()
        return pixmap
    
    
    def _update_progress_bar(self):
        """Progress bar'ı güncelle"""
        # Yeni pixmap oluştur
        pixmap = QPixmap(400, 300)
        pixmap.fill(QColor(30, 30, 30))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Arka plan gradient
        from PyQt5.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, 0, 300)
        gradient.setColorAt(0, QColor(45, 45, 45))
        gradient.setColorAt(1, QColor(20, 20, 20))
        painter.fillRect(0, 0, 400, 300, gradient)
        
        # Başlık
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        painter.drawText(50, 80, "API Server Manager")
        
        # Alt başlık
        painter.setFont(QFont("Arial", 12))
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(50, 110, "Sistem başlatılıyor...")
        
        # Progress bar arka planı
        painter.setPen(QColor(100, 100, 100))
        painter.setBrush(QColor(60, 60, 60))
        painter.drawRoundedRect(50, 200, 300, 20, 10, 10)
        
        # Progress bar dolgu (güncellenmiş)
        progress_width = int((self.progress / self.max_progress) * 300)
        painter.setBrush(QColor(0, 150, 255))
        painter.drawRoundedRect(50, 200, progress_width, 20, 10, 10)
        
        # Progress yüzdesi
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(50, 200, 300, 20, Qt.AlignCenter, f"{self.progress}%")
        
        # Status text
        painter.setPen(QColor(180, 180, 180))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(50, 240, self.status_text)
        
        # Version info
        painter.setPen(QColor(120, 120, 120))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(50, 270, "v1.0.0")
        
        painter.end()
        self.setPixmap(pixmap)
    
    
    def set_status(self, status: str):
        """
        Status metnini ayarla
        
        Args:
            status: Status metni
        """
        self.status_text = status
        self._update_progress_bar()
    
    def set_progress(self, progress: int):
        """
        Progress değerini ayarla
        
        Args:
            progress: Progress değeri (0-100)
        """
        self.progress = min(progress, self.max_progress)
        self._update_progress_bar()
    
    def show_message(self, message: str):
        """
        Mesaj göster
        
        Args:
            message: Gösterilecek mesaj
        """
        self.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255))
    
    def finish(self):
        """Splash screen'i tamamla"""
        self.progress = self.max_progress
        self._update_progress_bar()
        QTimer.singleShot(500, self.splash_finished.emit)
    
    def cleanup(self):
        """Cleanup loading thread when splash screen is closed."""
        try:
            if self.loading_worker:
                self.loading_worker.stop_loading()
            
            if self.loading_thread and self.loading_thread.isRunning():
                self.loading_thread.quit()
                self.loading_thread.wait(3000)  # Wait up to 3 seconds
            
            logger.info("Splash screen cleanup completed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup splash screen: {e}")
    
    def closeEvent(self, event):
        """Pencere kapatma olayını yönet"""
        self.cleanup()
        event.accept()
