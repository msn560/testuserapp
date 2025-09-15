"""
Base tab class for all main window tabs.

This module provides the foundation for all tab classes in the application.
It includes common functionality like data refresh, error handling, and UI updates.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QIcon

from ...utils.logger import logger
from ...core.language import language_manager


class BaseTabWorker(QObject):
    """
    Base tab worker that runs in a separate thread.
    """
    
    # Signals for GUI communication
    data_ready = pyqtSignal(dict)      # Data ready for display
    error_occurred = pyqtSignal(str)   # Error occurred
    status_updated = pyqtSignal(str)   # Status update
    
    def __init__(self, tab_name: str):
        super().__init__()
        self.tab_name = tab_name
        self.logger = logger
        self.running = False
    
    def start_worker(self):
        """Start the worker."""
        self.running = True
        self.logger.debug(f"BaseTabWorker started for {self.tab_name}")
    
    def stop_worker(self):
        """Stop the worker."""
        self.running = False
        self.logger.debug(f"BaseTabWorker stopped for {self.tab_name}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.running = False
        except:
            pass
    
    def refresh_data(self):
        """Refresh data in background thread."""
        try:
            if not self.running:
                return
            
            # This method should be overridden by subclasses
            self._do_refresh_data()
            
        except Exception as e:
            self.logger.error(f"Error refreshing data for {self.tab_name}: {e}")
            self.error_occurred.emit(str(e))
    
    def _do_refresh_data(self):
        """Override this method in subclasses to implement data refresh."""
        # Default implementation - emit empty data
        self.data_ready.emit({})


class BaseTab(QWidget):
    """
    Base class for all tab widgets.
    
    This class provides common functionality for all tabs including
    data refresh, error handling, and UI update patterns.
    """
    
    # Signals
    data_updated = pyqtSignal(str, object)  # tab_name, data
    error_occurred = pyqtSignal(str)  # error_message
    status_changed = pyqtSignal(str)  # status_message
    
    def __init__(self, tab_name: str, title: str = None):
        """
        Initialize the base tab.
        
        Args:
            tab_name: Unique name for the tab
            title: Display title for the tab
        """
        super().__init__()
        
        self.tab_name = tab_name
        self.title = title or tab_name.title()
        self.logger = logger
        self.is_initialized = False
        
        # Thread and worker for data operations
        self.worker_thread = None
        self.worker = None
        
        # Reduced timer usage - only for UI updates
        self.refresh_timer = None
        
        # Initialize UI
        self._init_ui()
        self._setup_refresh_timer()
        
        # Register for language change callbacks
        language_manager.add_language_change_callback(self._on_language_changed)
        
        # Don't start thread immediately - start on first use
        self.worker_thread = None
        self.worker = None
        self.thread_started = False
        
        # Base tab initialized
    
    def _ensure_worker_thread(self):
        """Ensure worker thread is started (lazy loading)."""
        if not self.thread_started and not self.worker_thread:
            self._init_worker_thread()
            self.thread_started = True
    
    def _init_worker_thread(self):
        """Initialize the worker thread."""
        try:
            # Create thread and worker
            self.worker_thread = QThread()
            self.worker = self._create_worker()
            
            # Move worker to thread
            self.worker.moveToThread(self.worker_thread)
            
            # Connect signals
            self.worker.data_ready.connect(self._on_data_ready)
            self.worker.error_occurred.connect(self._on_worker_error)
            self.worker.status_updated.connect(self._on_status_updated)
            
            # Connect thread finished signal
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            
            # Start thread
            self.worker_thread.start()
            
            # Start worker
            self.worker.start_worker()
            
            # Worker thread initialized successfully
            
        except Exception as e:
            self.logger.error(f"Failed to initialize worker thread for {self.tab_name}: {e}")
    
    def cleanup_thread(self):
        """Clean up worker thread properly."""
        try:
            if self.worker_thread and self.worker_thread.isRunning():
                # Stop worker first
                if self.worker:
                    self.worker.stop_worker()
                
                # Disconnect all signals to prevent further communication
                if self.worker:
                    try:
                        self.worker.data_ready.disconnect()
                        self.worker.error_occurred.disconnect()
                        self.worker.status_updated.disconnect()
                    except:
                        pass  # Signals might already be disconnected
                
                # Quit thread
                self.worker_thread.quit()
                
                # Wait for thread to finish (with timeout)
                if not self.worker_thread.wait(5000):  # 5 second timeout
                    self.logger.warning(f"Thread {self.tab_name} did not finish in time, terminating")
                    self.worker_thread.terminate()
                    if not self.worker_thread.wait(2000):  # Wait 2 more seconds
                        self.logger.error(f"Thread {self.tab_name} could not be terminated")
                
                # Clear references
                self.worker = None
                self.worker_thread = None
                
        except Exception as e:
            self.logger.error(f"Error cleaning up thread {self.tab_name}: {e}")
            # Force cleanup even if there's an error
            try:
                if self.worker_thread:
                    self.worker_thread.terminate()
                    self.worker_thread.wait(1000)
                self.worker = None
                self.worker_thread = None
            except:
                pass
    
    def closeEvent(self, event):
        """Handle close event - cleanup thread."""
        self.cleanup_thread()
        super().closeEvent(event)
    
    def _create_worker(self) -> BaseTabWorker:
        """Create worker instance. Override in subclasses."""
        return BaseTabWorker(self.tab_name)
    
    def _on_data_ready(self, data: dict):
        """Handle data ready from worker thread."""
        try:
            self._process_data(data)
            self.data_updated.emit(self.tab_name, data)
        except Exception as e:
            self.logger.error(f"Error processing data for {self.tab_name}: {e}")
    
    def _on_worker_error(self, error_message: str):
        """Handle error from worker thread."""
        try:
            self.show_error(error_message)
        except Exception as e:
            self.logger.error(f"Error handling worker error for {self.tab_name}: {e}")
    
    def _on_status_updated(self, status_message: str):
        """Handle status update from worker thread."""
        try:
            self.update_status(status_message)
        except Exception as e:
            self.logger.error(f"Error handling status update for {self.tab_name}: {e}")
    
    def _process_data(self, data: dict):
        """Process data from worker thread. Override in subclasses."""
        pass
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Create header layout
        self.header_layout = QHBoxLayout()
        self.main_layout.addLayout(self.header_layout)
        
        # Create title label
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        self.header_layout.addWidget(self.title_label)
        
        # Add stretch to push refresh button to the right
        self.header_layout.addStretch()
        
        # Create refresh button
        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(QIcon("data/resources/icons/actions/refresh.png"))
        self.refresh_button.setToolTip("Refresh data")
        self.refresh_button.clicked.connect(self.refresh_data)
        self.header_layout.addWidget(self.refresh_button)
        
        # Create content area
        self.content_widget = self._create_content_widget()
        if self.content_widget:
            self.main_layout.addWidget(self.content_widget)
        
        # Create status area
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-size: 12px;")
        self.main_layout.addWidget(self.status_label)
    
    def _create_content_widget(self) -> Optional[QWidget]:
        """
        Create the main content widget for the tab.
        This method should be overridden by subclasses.
        
        Returns:
            The content widget or None
        """
        return None
    
    def _setup_refresh_timer(self):
        """Setup the automatic refresh timer (disabled by default)."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._request_data_refresh)
        # Timer'ı varsayılan olarak başlatma - sadece gerektiğinde başlat
        # self.refresh_timer.start(30000)
    
    def _request_data_refresh(self):
        """Request data refresh from worker thread (non-blocking)."""
        try:
            if self.worker:
                self.worker.refresh_data()
            # Worker yoksa sessizce geç - bu normal bir durum
        except Exception as e:
            self.logger.error(f"Error requesting data refresh for {self.tab_name}: {e}")
    
    @abstractmethod
    def refresh_data(self):
        """
        Refresh the data displayed in the tab.
        This method must be implemented by subclasses.
        """
        try:
            # Worker varsa refresh yap, yoksa sessizce geç
            if self.worker and hasattr(self.worker, 'refresh_data'):
                self.worker.refresh_data()
            # Worker yoksa sessizce geç - bu normal bir durum
        except Exception as e:
            self.logger.error(f"Error refreshing data for {self.tab_name}: {e}")
    
    def update_status(self, message: str, is_error: bool = False):
        """
        Update the status message.
        
        Args:
            message: Status message
            is_error: Whether this is an error message
        """
        if is_error:
            self.status_label.setProperty("class", "error")
            self.logger.error(f"Tab '{self.tab_name}': {message}")
        else:
            self.status_label.setProperty("class", "subtitle")
            self.logger.debug(f"Tab '{self.tab_name}': {message}")
        
        self.status_label.setText(message)
        self.status_changed.emit(message)
    
    def set_refresh_interval(self, interval_ms: int):
        """
        Set the refresh interval for the tab.
        
        Args:
            interval_ms: Refresh interval in milliseconds
        """
        if self.refresh_timer:
            self.refresh_timer.setInterval(interval_ms)
            self.logger.debug(f"Tab '{self.tab_name}' refresh interval set to {interval_ms}ms")
    
    def start_auto_refresh(self):
        """Start automatic data refresh."""
        if self.refresh_timer:
            self.refresh_timer.start()
            self.logger.debug(f"Tab '{self.tab_name}' auto-refresh started")
    
    def stop_auto_refresh(self):
        """Stop automatic data refresh."""
        if self.refresh_timer:
            self.refresh_timer.stop()
            self.logger.debug(f"Tab '{self.tab_name}' auto-refresh stopped")
    
    def show_error(self, error_message: str):
        """
        Show an error message to the user.
        
        Args:
            error_message: The error message to display
        """
        self.update_status(f"Error: {error_message}", is_error=True)
        self.error_occurred.emit(error_message)
    
    def show_success(self, message: str):
        """
        Show a success message to the user.
        
        Args:
            message: The success message to display
        """
        self.update_status(f"Success: {message}")
    
    def show_info(self, message: str):
        """
        Show an info message to the user.
        
        Args:
            message: The info message to display
        """
        self.update_status(f"Info: {message}")
    
    def is_tab_active(self) -> bool:
        """
        Check if this tab is currently active.
        
        Returns:
            True if tab is active, False otherwise
        """
        # This would need to be implemented by the main window
        # For now, return True as a placeholder
        return True
    
    def on_tab_activated(self):
        """
        Called when the tab becomes active.
        This method can be overridden by subclasses.
        """
        # Tab activated
        if not self.is_initialized:
            self._initialize_tab()
            self.is_initialized = True
    
    def on_tab_deactivated(self):
        """
        Called when the tab becomes inactive.
        This method can be overridden by subclasses.
        """
        # Tab deactivated
    
    def _initialize_tab(self):
        """
        Initialize tab-specific data and components.
        This method can be overridden by subclasses.
        """
        # Tab initialized
    
    def get_tab_data(self) -> Dict[str, Any]:
        """
        Get current tab data.
        This method can be overridden by subclasses.
        
        Returns:
            Dictionary containing tab data
        """
        return {
            "tab_name": self.tab_name,
            "title": self.title,
            "is_initialized": self.is_initialized,
            "auto_refresh_enabled": self.refresh_timer.isActive() if self.refresh_timer else False
        }
    
    def set_tab_data(self, data: Dict[str, Any]):
        """
        Set tab data.
        This method can be overridden by subclasses.
        
        Args:
            data: Dictionary containing tab data
        """
        self.logger.debug(f"Tab '{self.tab_name}' data updated")
    
    def _on_language_changed(self, old_lang: str, new_lang: str):
        """
        Called when language changes.
        This method can be overridden by subclasses to update UI text.
        
        Args:
            old_lang: Previous language code
            new_lang: New language code
        """
        # Update tab title if it's a navigation key
        if hasattr(self, 'title') and self.title:
            # Try to update title using navigation translation
            try:
                nav_key = f"navigation.{self.tab_name}"
                new_title = language_manager.translate(nav_key)
                if new_title != nav_key:  # Translation found
                    self.title = new_title
                    self.logger.debug(f"Tab '{self.tab_name}' title updated to '{new_title}'")
            except Exception as e:
                self.logger.warning(f"Failed to update tab title: {e}")
    
    def cleanup(self):
        """Cleanup tab resources."""
        try:
            # Unregister language change callback
            language_manager.remove_language_change_callback(self._on_language_changed)
            
            # Stop worker
            if self.worker:
                self.worker.stop_worker()
            
            # Stop thread
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.quit()
                self.worker_thread.wait(3000)  # Wait up to 3 seconds
            
            # Stop timer
            if self.refresh_timer:
                self.refresh_timer.stop()
            
            self.logger.debug(f"Tab '{self.tab_name}' cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up tab '{self.tab_name}': {e}")
    
    def closeEvent(self, event):
        """Handle tab close event."""
        self.cleanup()
        event.accept()
