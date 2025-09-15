# 🏗️ API Server Management System - Sistem Mimarisi

## 📋 Genel Bakış

API Server Management System, modern Python teknolojilerini kullanarak geliştirilmiş, modüler ve ölçeklenebilir bir server yönetim sistemidir. Bu dokümantasyon sistemin mimari yapısını, bileşenler arası ilişkileri ve tasarım kararlarını detaylandırır.

---

## 🎯 Mimari Prensipleri

### 1. Separation of Concerns (Endişelerin Ayrılması)
- **UI Layer**: PyQt5 tabanlı desktop interface
- **API Layer**: AioHTTP tabanlı RESTful API
- **Business Logic**: Service katmanında iş mantığı
- **Data Access**: Repository pattern ile veri erişimi

### 2. Dependency Injection
- Bileşenler arası gevşek bağlılık
- Test edilebilirlik
- Yapılandırılabilirlik

### 3. Event-Driven Architecture
- PyQt5 signal/slot sistemi
- Async event handling
- Real-time updates

### 4. Thread Safety
- UI thread ile worker thread'ler arasında güvenli iletişim
- QThread kullanımı
- Signal-based communication

---

## 🏗️ Katmanlı Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  PyQt5 GUI        │  REST API        │  WebSocket API       │
│  - Main Window    │  - Auth Routes   │  - Real-time Data    │
│  - Tab System     │  - User Routes   │  - Live Logs         │
│  - Dialogs        │  - Server Routes │  - System Metrics    │
│  - Widgets        │  - Monitor Routes│                      │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                     │
├─────────────────────────────────────────────────────────────┤
│  Services                                                   │
│  - AuthService     - UserService      - ServerService      │
│  - TokenService    - ConfigService    - MonitorService     │
│  - BackupService   - NotificationService                   │
│                                                             │
│  Core Components                                            │
│  - Settings        - Security         - Language           │
│  - EventSystem     - SessionManager   - ResourceLoader     │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  Database Managers                                          │
│  - UserManager     - RoleManager      - SessionManager     │
│  - ConfigManager   - LogManager       - APIManager         │
│                                                             │
│  ORM Models (Peewee)                                        │
│  - User           - Role              - Session             │
│  - Config         - SystemLog         - ApiLog             │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                     │
├─────────────────────────────────────────────────────────────┤
│  Database         │  File System     │  External Services   │
│  - SQLite         │  - Config Files  │  - Email Service     │
│  - Connection     │  - Log Files     │  - SMS Service       │
│    Pool           │  - Backups       │  - Monitoring        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 Bileşen Mimarisi

### 1. Core Components

#### Settings Manager
```python
class Settings:
    """Merkezi ayar yöneticisi"""
    - app: AppSettings
    - server: ServerSettings  
    - ui: UISettings
    - security: SecuritySettings
    - database: DatabaseSettings
    - features: FeatureFlags
```

#### Event System
```python
class EventSystem:
    """Event dispatcher sistemi"""
    - subscribe(event_type, callback)
    - emit(event_type, data)
    - unsubscribe(event_type, callback)
```

#### Security Manager
```python
class SecurityManager:
    """Güvenlik işlemleri"""
    - hash_password(password)
    - verify_password(password, hash)
    - generate_token(user_id, roles)
    - verify_token(token)
```

### 2. Database Layer

#### Model Relationships
```
User ──┐
       ├── UserRole ──── Role
       └── Session
       
Config ──── SystemSettings

ApiLog ──── User (optional)
SystemLog ──── User (optional)

Backup ──── User (created_by)
```

#### Database Manager Pattern
```python
class BaseManager:
    """Temel database manager"""
    def create(self, **kwargs)
    def get_by_id(self, id)
    def update(self, id, **kwargs)
    def delete(self, id)
    def list(self, filters=None, pagination=None)
```

### 3. Service Layer

#### Service Dependencies
```
AuthService ──┬── UserManager
              ├── TokenService
              └── SecurityManager

UserService ──┬── UserManager
              ├── RoleManager
              └── EventSystem

ServerService ──┬── ConfigManager
                ├── APIServerManager
                └── MonitorService
```

### 4. API Layer

#### Middleware Stack
```
Request
   │
   ├── SecurityHeadersMiddleware
   ├── CORSMiddleware
   ├── LoggingMiddleware
   ├── AuthMiddleware
   ├── RateLimitMiddleware
   └── ErrorHandlerMiddleware
   │
Route Handler
   │
Response
```

#### Route Organization
```
/api/v1/
├── auth/          # Authentication
├── users/         # User management
├── roles/         # Role management
├── server/        # Server control
├── monitor/       # System monitoring
├── config/        # Configuration
├── logs/          # Log management
└── files/         # File operations
```

---

## 🔄 Data Flow

### 1. User Authentication Flow
```
UI Login Form
     │
     ├── AuthService.login()
     │       │
     │       ├── UserManager.get_by_username()
     │       ├── SecurityManager.verify_password()
     │       └── TokenService.generate_token()
     │
     └── Session Storage
             │
             └── UI State Update
```

### 2. API Request Flow
```
HTTP Request
     │
     ├── Middleware Chain
     │       │
     │       ├── Authentication
     │       ├── Authorization  
     │       └── Validation
     │
     ├── Route Handler
     │       │
     │       ├── Service Layer
     │       ├── Database Layer
     │       └── Response Generation
     │
     └── HTTP Response
```

### 3. Real-time Update Flow
```
System Event
     │
     ├── EventSystem.emit()
     │       │
     │       ├── Service Listeners
     │       ├── UI Signal Emission
     │       └── WebSocket Broadcast
     │
     └── UI Update (via Qt Signals)
```

---

## 🧵 Threading Model

### 1. Main Thread (UI)
- PyQt5 event loop
- UI rendering
- User interaction handling
- Signal/slot connections

### 2. Worker Threads
```python
# API Server Thread
APIServerWorker
├── AioHTTP Server
├── Async Request Handling
└── Background Tasks

# Database Worker Thread  
DatabaseWorker
├── Database Operations
├── Backup Tasks
└── Cleanup Operations

# Monitoring Worker Thread
MonitoringWorker
├── System Metrics Collection
├── Performance Monitoring
└── Alert Generation
```

### 3. Thread Communication
```python
# UI → Worker
QMetaObject.invokeMethod(worker, "method_name", 
                        Qt.QueuedConnection, 
                        Q_ARG(type, value))

# Worker → UI
worker_signal.emit(data)  # Automatically thread-safe
```

---

## 📊 State Management

### 1. Application State
```python
class AppState:
    """Uygulama durumu"""
    - current_user: User
    - server_status: ServerStatus
    - ui_state: UIState
    - system_metrics: SystemMetrics
```

### 2. Session Management
```python
class SessionManager:
    """Oturum yöneticisi"""
    - create_session(user_id) → Session
    - validate_session(token) → bool
    - refresh_session(token) → new_token
    - invalidate_session(token)
```

### 3. Configuration State
```python
class ConfigManager:
    """Yapılandırma yöneticisi"""
    - load_config() → dict
    - save_config(config)
    - validate_config(config) → errors
    - reload_config()
```

---

## 🔒 Security Architecture

### 1. Authentication Layer
```
┌─────────────────────────────────────────┐
│            Authentication               │
├─────────────────────────────────────────┤
│  JWT Token Based                        │
│  ├── Access Token (short-lived)        │
│  ├── Refresh Token (long-lived)        │
│  └── Token Blacklisting                │
│                                         │
│  Multi-Factor Authentication           │
│  ├── TOTP Support                      │
│  ├── SMS Verification                  │
│  └── Email Verification                │
└─────────────────────────────────────────┘
```

### 2. Authorization Layer
```
┌─────────────────────────────────────────┐
│            Authorization                │
├─────────────────────────────────────────┤
│  Role-Based Access Control (RBAC)      │
│  ├── Roles: superadmin, admin,         │
│  │          operator, viewer           │
│  ├── Permissions: endpoint-based       │
│  └── Dynamic Permission Checking       │
│                                         │
│  Resource-Level Security               │
│  ├── User can only edit own profile    │
│  ├── Admin can manage users            │
│  └── Superadmin can access all         │
└─────────────────────────────────────────┘
```

### 3. Security Measures
- **Input Validation**: Pydantic schemas
- **SQL Injection**: Peewee ORM protection
- **XSS Protection**: Input sanitization
- **CSRF Protection**: Token-based
- **Rate Limiting**: Per-IP and per-user
- **Audit Logging**: All security events

---

## 🚀 Performance Architecture

### 1. Caching Strategy
```python
# Memory Cache
class MemoryCache:
    - user_sessions: dict
    - config_cache: dict
    - system_metrics: dict

# File Cache  
class FileCache:
    - log_files: rotating
    - backup_files: compressed
    - temp_files: auto-cleanup
```

### 2. Database Optimization
- **Connection Pooling**: Peewee connection pool
- **Query Optimization**: Indexed columns
- **Batch Operations**: Bulk inserts/updates
- **Pagination**: Large dataset handling

### 3. UI Performance
- **Lazy Loading**: Tab content loading
- **Virtual Scrolling**: Large lists
- **Background Processing**: Worker threads
- **Update Batching**: UI refresh optimization

---

## 📈 Monitoring Architecture

### 1. System Monitoring
```python
class SystemMonitor:
    """Sistem izleme"""
    - cpu_usage: float
    - memory_usage: float
    - disk_usage: float
    - network_io: dict
    - process_list: list
```

### 2. Application Monitoring
```python
class AppMonitor:
    """Uygulama izleme"""
    - api_requests: counter
    - response_times: histogram
    - error_rates: gauge
    - active_sessions: gauge
```

### 3. Alert System
```python
class AlertSystem:
    """Uyarı sistemi"""
    - threshold_alerts: list
    - custom_alerts: list
    - notification_channels: list
    - escalation_rules: list
```

---

## 🔧 Configuration Architecture

### 1. Configuration Hierarchy
```
Environment Variables (highest priority)
    ↓
Command Line Arguments
    ↓
Configuration File (config.json)
    ↓
Default Settings (lowest priority)
```

### 2. Configuration Categories
```python
{
    "app": {
        "name": "API Server Management System",
        "version": "1.0.0",
        "debug": false
    },
    "server": {
        "host": "127.0.0.1",
        "port": 8080,
        "ssl_enabled": false
    },
    "database": {
        "path": "data/app.db",
        "backup_enabled": true
    },
    "security": {
        "jwt_secret": "secret",
        "jwt_expiry": 3600
    },
    "ui": {
        "theme": "dark",
        "language": "en"
    }
}
```

---

## 🧪 Testing Architecture

### 1. Test Categories
- **Unit Tests**: Individual components
- **Integration Tests**: Component interactions
- **API Tests**: Endpoint testing
- **UI Tests**: User interface testing
- **Performance Tests**: Load and stress testing

### 2. Test Infrastructure
```python
# Test Database
test_db = SqliteDatabase(':memory:')

# Mock Services
class MockUserService:
    def get_user(self, user_id): ...

# Test Fixtures
@pytest.fixture
def test_user():
    return User.create(username='test', email='test@example.com')
```

---

## 📦 Deployment Architecture

### 1. Packaging
- **PyInstaller**: Single executable
- **Virtual Environment**: Dependencies isolation
- **Configuration**: External config files
- **Assets**: Bundled resources

### 2. Installation
```
api_server_manager/
├── api_server_manager.exe    # Main executable
├── config.json              # Configuration
├── data/                    # Data directory
│   ├── app.db              # Database
│   ├── logs/               # Log files
│   └── backups/            # Backup files
└── resources/              # UI resources
    ├── icons/
    ├── themes/
    └── translations/
```

### 3. Update Mechanism
- **Auto-update**: Built-in updater
- **Version Check**: Remote version checking
- **Backup**: Automatic backup before update
- **Rollback**: Previous version restoration

---

## 🔄 Development Workflow

### 1. Code Organization
```
src/
├── core/           # Core components
├── db/            # Database layer
├── api/           # API layer
├── services/      # Business logic
├── ui/            # User interface
├── monitoring/    # Monitoring system
└── utils/         # Utilities
```

### 2. Development Principles
- **DRY**: Don't Repeat Yourself
- **SOLID**: Object-oriented design principles
- **Clean Code**: Readable and maintainable
- **Documentation**: Comprehensive docs

### 3. Quality Assurance
- **Code Review**: Peer review process
- **Static Analysis**: Flake8, MyPy
- **Testing**: Automated test suite
- **CI/CD**: Continuous integration

---

## 📚 Extension Points

### 1. Plugin System
```python
class PluginInterface:
    """Plugin arayüzü"""
    def initialize(self, app_context)
    def get_routes(self) → list
    def get_ui_components(self) → list
    def cleanup(self)
```

### 2. Custom Themes
```python
class ThemeInterface:
    """Tema arayüzü"""
    def get_stylesheet(self) → str
    def get_colors(self) → dict
    def get_fonts(self) → dict
```

### 3. Custom Monitors
```python
class MonitorInterface:
    """Monitor arayüzü"""
    def collect_metrics(self) → dict
    def get_alerts(self) → list
    def get_dashboard_widgets(self) → list
```

---

## 🎯 Future Enhancements

### 1. Microservices Migration
- Service decomposition
- API Gateway
- Service discovery
- Load balancing

### 2. Cloud Integration
- Docker containerization
- Kubernetes orchestration
- Cloud storage
- Managed databases

### 3. Advanced Features
- Machine learning analytics
- Predictive monitoring
- Advanced reporting
- Multi-tenant support

---

Bu mimari dokümantasyonu, sistemin mevcut durumunu ve gelecekteki genişleme planlarını kapsamaktadır. Sistem modüler yapısı sayesinde kolayca genişletilebilir ve sürdürülebilir.