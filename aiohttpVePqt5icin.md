# AioHTTP + PyQt5 Paralel Geliştirme Rehberi

## 🎯 Genel Mimari ve Yaklaşım

Bu rehber, AioHTTP tabanlı async HTTP server ile PyQt5 GUI'yi paralel olarak çalıştırmak için thread-safe bir yaklaşım sunar. Ana amaç, UI donmaları önlemek ve performanslı bir sistem oluşturmaktır.

## 🧵 Thread Mimarisi

### Ana Thread Yapısı
```
Main Thread (GUI)
├── UI Components (PyQt5)
├── Event Loop (Qt)
└── Signal/Slot Communication

Worker Thread (API Server)  
├── AioHTTP Server
├── Async Event Loop
└── Background Tasks
```

## 🔄 Thread-Safe İletişim Modeli

### 1. QThread + QObject Pattern
```python
class ServerWorker(QObject):
    """AioHTTP server'ını ayrı thread'de çalıştıran worker"""
    
    # Signals - Thread-safe communication
    server_started = pyqtSignal(dict)
    server_stopped = pyqtSignal()
    server_error = pyqtSignal(str)
    log_message = pyqtSignal(dict)
    status_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self._running = False
        
    def start_server(self, config: dict):
        """Server'ı başlat - async olarak"""
        try:
            # Event loop oluştur
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Server'ı başlat
            loop.run_until_complete(self._start_server_async(config))
            
        except Exception as e:
            self.server_error.emit(str(e))
    
    async def _start_server_async(self, config: dict):
        """Async server başlatma"""
        self.app = web.Application()
        
        # Middleware'leri ekle
        self._setup_middlewares()
        
        # Route'ları ekle
        self._setup_routes()
        
        # Runner oluştur
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        # Site oluştur ve başlat
        self.site = web.TCPSite(
            self.runner, 
            config['host'], 
            config['port']
        )
        await self.site.start()
        
        self._running = True
        
        # Signal gönder
        self.server_started.emit({
            'host': config['host'],
            'port': config['port'],
            'status': 'running'
        })
```

### 2. Manager Class Pattern
```python
class APIServerManager(QObject):
    """Server manager - UI ile worker arasında köprü"""
    
    # UI için signals
    status_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Worker thread oluştur
        self.worker_thread = QThread()
        self.worker = ServerWorker()
        
        # Worker'ı thread'e taşı
        self.worker.moveToThread(self.worker_thread)
        
        # Signal bağlantıları
        self._setup_connections()
        
        # Thread'i başlat
        self.worker_thread.start()
    
    def _setup_connections(self):
        """Signal-slot bağlantılarını kur"""
        # Worker signals -> Manager slots
        self.worker.server_started.connect(self._on_server_started)
        self.worker.server_stopped.connect(self._on_server_stopped)
        self.worker.server_error.connect(self._on_server_error)
        
        # Thread lifecycle
        self.worker_thread.started.connect(self.worker.initialize)
        self.worker_thread.finished.connect(self.worker.cleanup)
    
    def start_server(self, config: dict):
        """Server'ı başlat - thread-safe"""
        # Worker thread'e signal gönder
        QMetaObject.invokeMethod(
            self.worker,
            "start_server",
            Qt.QueuedConnection,
            Q_ARG(dict, config)
        )
```

## 🎛️ UI Integration Patterns

### 1. Main Window Integration
```python
class MainWindow(QMainWindow):
    """Ana pencere - server manager ile entegre"""
    
    def __init__(self):
        super().__init__()
        
        # Server manager oluştur
        self.server_manager = APIServerManager()
        
        # Signal bağlantıları
        self.server_manager.status_updated.connect(self._on_server_status_updated)
        self.server_manager.error_occurred.connect(self._on_server_error)
        
        # UI timer'lar
        self._setup_timers()
    
    def _setup_timers(self):
        """Periyodik güncellemeler için timer'lar"""
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._request_status_update)
        self.status_timer.start(5000)  # 5 saniyede bir
        
        # Log update timer
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self._request_log_update)
        self.log_timer.start(1000)  # 1 saniyede bir
    
    @pyqtSlot(dict)
    def _on_server_status_updated(self, status: dict):
        """Server status güncellendiğinde - UI thread'de çalışır"""
        # Status widget'ını güncelle
        self.status_widget.update_status(status)
        
        # Server tab'ını güncelle
        if hasattr(self, 'server_tab'):
            self.server_tab.update_server_status(status)
```

### 2. Real-time Data Updates
```python
class MonitorTab(BaseTab):
    """Monitoring sekmesi - real-time data"""
    
    def __init__(self):
        super().__init__()
        
        # WebSocket bağlantısı için worker
        self.ws_worker = WebSocketWorker()
        self.ws_thread = QThread()
        
        self.ws_worker.moveToThread(self.ws_thread)
        
        # Signal bağlantıları
        self.ws_worker.data_received.connect(self._on_data_received)
        self.ws_worker.connection_status.connect(self._on_connection_status)
        
        self.ws_thread.start()
    
    @pyqtSlot(dict)
    def _on_data_received(self, data: dict):
        """Real-time data alındığında"""
        data_type = data.get('type')
        
        if data_type == 'system_metrics':
            self._update_system_charts(data['metrics'])
        elif data_type == 'api_metrics':
            self._update_api_charts(data['metrics'])
        elif data_type == 'logs':
            self._update_log_display(data['logs'])
    
    def _update_system_charts(self, metrics: dict):
        """Sistem grafiklerini güncelle - UI thread'de"""
        # CPU chart
        self.cpu_chart.add_data_point(metrics['cpu_percent'])
        
        # Memory chart
        self.memory_chart.add_data_point(metrics['memory_percent'])
        
        # Disk chart
        self.disk_chart.add_data_point(metrics['disk_percent'])
```

## 📡 WebSocket Real-time Communication

### WebSocket Worker Pattern
```python
class WebSocketWorker(QObject):
    """WebSocket client worker"""
    
    data_received = pyqtSignal(dict)
    connection_status = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.websocket = None
        self._running = False
    
    async def connect_and_listen(self, url: str):
        """WebSocket'e bağlan ve dinle"""
        try:
            import websockets
            
            self.websocket = await websockets.connect(url)
            self.connection_status.emit('connected')
            
            self._running = True
            
            while self._running:
                try:
                    message = await self.websocket.recv()
                    data = json.loads(message)
                    
                    # Signal gönder (thread-safe)
                    self.data_received.emit(data)
                    
                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    self.error_occurred.emit(str(e))
                    
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.connection_status.emit('disconnected')
    
    def start_connection(self, url: str):
        """Bağlantıyı başlat"""
        # Yeni event loop'ta çalıştır
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.connect_and_listen(url))
        finally:
            loop.close()
```

## 🔒 Thread-Safe Data Sharing

### 1. Shared State Manager
```python
class SharedStateManager(QObject):
    """Thread'ler arası güvenli veri paylaşımı"""
    
    state_changed = pyqtSignal(str, object)  # key, value
    
    def __init__(self):
        super().__init__()
        self._state = {}
        self._lock = QMutex()
    
    def set_state(self, key: str, value: Any):
        """State güncelle - thread-safe"""
        with QMutexLocker(self._lock):
            self._state[key] = value
            self.state_changed.emit(key, value)
    
    def get_state(self, key: str, default=None):
        """State oku - thread-safe"""
        with QMutexLocker(self._lock):
            return self._state.get(key, default)
    
    def get_all_state(self) -> dict:
        """Tüm state'i oku - thread-safe"""
        with QMutexLocker(self._lock):
            return self._state.copy()
```

### 2. Queue-based Communication
```python
from queue import Queue
from PyQt5.QtCore import QTimer

class AsyncTaskManager(QObject):
    """Async task'ları UI thread'den yönet"""
    
    task_completed = pyqtSignal(str, object)  # task_id, result
    task_failed = pyqtSignal(str, str)        # task_id, error
    
    def __init__(self):
        super().__init__()
        self.result_queue = Queue()
        
        # Sonuçları kontrol etmek için timer
        self.result_timer = QTimer()
        self.result_timer.timeout.connect(self._check_results)
        self.result_timer.start(100)  # 100ms'de bir kontrol et
    
    def _check_results(self):
        """Async task sonuçlarını kontrol et"""
        while not self.result_queue.empty():
            try:
                task_id, result, error = self.result_queue.get_nowait()
                
                if error:
                    self.task_failed.emit(task_id, error)
                else:
                    self.task_completed.emit(task_id, result)
                    
            except queue.Empty:
                break
    
    def submit_async_task(self, task_id: str, coro):
        """Async task submit et"""
        # Worker thread'e gönder
        self.worker.submit_task(task_id, coro, self.result_queue)
```

## ⚡ Performance Optimization

### 1. Batch Updates
```python
class BatchUpdateManager(QObject):
    """UI güncellemelerini batch'le"""
    
    def __init__(self, update_interval: int = 100):
        super().__init__()
        self.pending_updates = {}
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._process_updates)
        self.update_timer.start(update_interval)
    
    def schedule_update(self, widget_id: str, update_data: dict):
        """Güncellemeyi planla"""
        self.pending_updates[widget_id] = update_data
    
    def _process_updates(self):
        """Bekleyen güncellemeleri işle"""
        if not self.pending_updates:
            return
        
        updates = self.pending_updates.copy()
        self.pending_updates.clear()
        
        for widget_id, data in updates.items():
            widget = self._get_widget_by_id(widget_id)
            if widget:
                widget.batch_update(data)
```

### 2. Lazy Loading
```python
class LazyLoadingTab(BaseTab):
    """Lazy loading ile tab"""
    
    def __init__(self):
        super().__init__()
        self._loaded = False
        self._load_timer = QTimer()
        self._load_timer.setSingleShot(True)
        self._load_timer.timeout.connect(self._delayed_load)
    
    def showEvent(self, event):
        """Tab gösterildiğinde"""
        super().showEvent(event)
        
        if not self._loaded:
            # Kısa bir delay ile yükle (UI responsive kalması için)
            self._load_timer.start(50)
    
    def _delayed_load(self):
        """Geciktirilmiş yükleme"""
        if not self._loaded:
            self._load_content()
            self._loaded = True
```

## 🚨 Error Handling ve Recovery

### 1. Graceful Error Handling
```python
class ErrorHandler(QObject):
    """Merkezi error handling"""
    
    error_occurred = pyqtSignal(str, str, dict)  # level, message, context
    
    def handle_thread_error(self, thread_name: str, error: Exception):
        """Thread hatalarını işle"""
        error_msg = f"Thread '{thread_name}' hatası: {str(error)}"
        
        # Log'la
        logger.error(error_msg, exc_info=error)
        
        # UI'ye bildir
        self.error_occurred.emit('error', error_msg, {
            'thread': thread_name,
            'error_type': type(error).__name__
        })
        
        # Recovery'yi dene
        self._attempt_recovery(thread_name, error)
    
    def _attempt_recovery(self, thread_name: str, error: Exception):
        """Hata recovery'si dene"""
        if thread_name == 'server_worker':
            # Server'ı yeniden başlatmayı dene
            QTimer.singleShot(5000, self._restart_server)
        elif thread_name == 'websocket_worker':
            # WebSocket'i yeniden bağlamayı dene
            QTimer.singleShot(2000, self._reconnect_websocket)
```

### 2. Resource Cleanup
```python
class ResourceManager(QObject):
    """Kaynak temizleme yöneticisi"""
    
    def __init__(self):
        super().__init__()
        self.active_threads = []
        self.active_timers = []
        self.active_connections = []
    
    def register_thread(self, thread: QThread):
        """Thread'i kaydet"""
        self.active_threads.append(thread)
        thread.finished.connect(lambda: self._unregister_thread(thread))
    
    def cleanup_all(self):
        """Tüm kaynakları temizle"""
        # Thread'leri temizle
        for thread in self.active_threads[:]:
            if thread.isRunning():
                thread.quit()
                thread.wait(5000)  # 5 saniye bekle
                if thread.isRunning():
                    thread.terminate()
        
        # Timer'ları durdur
        for timer in self.active_timers[:]:
            timer.stop()
        
        # Bağlantıları kapat
        for connection in self.active_connections[:]:
            try:
                connection.close()
            except:
                pass
```

## 📋 Best Practices Checklist

### ✅ Thread Safety
- [ ] Tüm UI güncellemeleri main thread'de yapılıyor
- [ ] Signal/slot kullanılarak thread'ler arası iletişim sağlanıyor
- [ ] Shared data için mutex kullanılıyor
- [ ] QMetaObject.invokeMethod ile cross-thread method çağrıları yapılıyor

### ✅ Performance
- [ ] Long-running işlemler worker thread'lerde yapılıyor
- [ ] UI güncellemeleri batch'leniyor
- [ ] Lazy loading uygulanıyor
- [ ] Memory leak'ler kontrol ediliyor

### ✅ Error Handling
- [ ] Tüm thread'ler için error handling mevcut
- [ ] Graceful shutdown implementasyonu var
- [ ] Resource cleanup yapılıyor
- [ ] Recovery mekanizmaları mevcut

### ✅ Code Quality
- [ ] Type hints kullanılıyor
- [ ] Docstring'ler mevcut
- [ ] Logging yapılıyor
- [ ] Unit test'ler yazılıyor

Bu rehber, AioHTTP + PyQt5 kombinasyonunda thread-safe, performanslı ve robust bir uygulama geliştirmek için gerekli tüm pattern'leri ve best practice'leri içermektedir.