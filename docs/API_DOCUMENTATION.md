# 🌐 API Server Management System - API Dokümantasyonu

## 📋 Genel Bakış

Bu dokümantasyon, API Server Management System'in RESTful API endpoint'lerini, request/response formatlarını, authentication yöntemlerini ve güvenlik politikalarını detaylandırır.

**Base URL**: `http://localhost:8080/api/v1`  
**API Version**: v1  
**Content-Type**: `application/json`  
**Authentication**: JWT Bearer Token

---

## 🔐 Authentication

### JWT Token Authentication

API'ye erişim için JWT (JSON Web Token) authentication kullanılır.

#### Token Alma
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "password123"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "Bearer",
        "expires_in": 3600,
        "user": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "roles": ["superadmin"]
        }
    }
}
```

#### Token Kullanımı
Tüm protected endpoint'lerde Authorization header'ı gereklidir:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

---

## 🔑 Authentication Endpoints

### POST /auth/login
Kullanıcı girişi yapar ve JWT token alır.

**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Response (200):**
```json
{
    "success": true,
    "data": {
        "access_token": "string",
        "refresh_token": "string", 
        "token_type": "Bearer",
        "expires_in": 3600,
        "user": {
            "id": 1,
            "username": "string",
            "email": "string",
            "roles": ["string"]
        }
    }
}
```

**Errors:**
- `400`: Invalid credentials
- `401`: Account disabled
- `429`: Too many login attempts

### POST /auth/logout
Kullanıcı çıkışı yapar ve token'ı geçersiz kılar.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
    "success": true,
    "message": "Logged out successfully"
}
```

### POST /auth/refresh
Access token'ı yeniler.

**Request Body:**
```json
{
    "refresh_token": "string"
}
```

**Response (200):**
```json
{
    "success": true,
    "data": {
        "access_token": "string",
        "expires_in": 3600
    }
}
```

### GET /auth/verify
Token'ın geçerliliğini kontrol eder.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
    "success": true,
    "data": {
        "valid": true,
        "user": {
            "id": 1,
            "username": "string",
            "roles": ["string"]
        }
    }
}
```

### POST /auth/forgot-password
Parola sıfırlama isteği gönderir.

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Response (200):**
```json
{
    "success": true,
    "message": "Password reset email sent"
}
```

### POST /auth/reset-password
Parola sıfırlar.

**Request Body:**
```json
{
    "reset_token": "string",
    "new_password": "string"
}
```

**Response (200):**
```json
{
    "success": true,
    "message": "Password reset successfully"
}
```

---

## 👥 User Management Endpoints

### GET /users
Kullanıcı listesini getirir.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `admin`, `superadmin`

**Query Parameters:**
- `page`: Sayfa numarası (default: 1)
- `limit`: Sayfa başına kayıt (default: 20, max: 100)
- `search`: Arama terimi
- `role`: Rol filtresi
- `active`: Aktif kullanıcı filtresi (true/false)

**Example:**
```http
GET /api/v1/users?page=1&limit=10&search=admin&active=true
```

**Response (200):**
```json
{
    "success": true,
    "data": {
        "users": [
            {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "System Administrator",
                "is_active": true,
                "is_verified": true,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "last_login": "2025-01-01T12:00:00Z",
                "roles": ["superadmin"]
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 10,
            "total": 1,
            "pages": 1
        }
    }
}
```

### POST /users
Yeni kullanıcı oluşturur.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `admin`, `superadmin`

**Request Body:**
```json
{
    "username": "newuser",
    "email": "newuser@example.com",
    "full_name": "New User",
    "password": "password123",
    "roles": ["viewer"],
    "is_active": true,
    "is_verified": false
}
```

**Response (201):**
```json
{
    "success": true,
    "data": {
        "id": 2,
        "username": "newuser",
        "email": "newuser@example.com",
        "full_name": "New User",
        "is_active": true,
        "is_verified": false,
        "created_at": "2025-01-01T00:00:00Z",
        "roles": ["viewer"]
    }
}
```

**Validation Errors (400):**
```json
{
    "success": false,
    "error": "Validation failed",
    "details": [
        {
            "field": "username",
            "message": "Username already exists"
        },
        {
            "field": "email",
            "message": "Invalid email format"
        }
    ]
}
```

### GET /users/{user_id}
Belirli bir kullanıcının detaylarını getirir.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `admin`, `superadmin` (veya kendi profili)

**Response (200):**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "System Administrator",
        "is_active": true,
        "is_verified": true,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "last_login": "2025-01-01T12:00:00Z",
        "roles": ["superadmin"],
        "profile": {
            "avatar_url": "https://example.com/avatars/admin.jpg",
            "timezone": "UTC",
            "language": "en"
        }
    }
}
```

### PUT /users/{user_id}
Kullanıcı bilgilerini günceller.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `admin`, `superadmin` (veya kendi profili)

**Request Body:**
```json
{
    "email": "newemail@example.com",
    "full_name": "Updated Name",
    "is_active": true,
    "roles": ["admin", "operator"]
}
```

**Response (200):**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "username": "admin",
        "email": "newemail@example.com",
        "full_name": "Updated Name",
        "is_active": true,
        "updated_at": "2025-01-01T12:00:00Z",
        "roles": ["admin", "operator"]
    }
}
```

### DELETE /users/{user_id}
Kullanıcıyı siler.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `superadmin`

**Response (200):**
```json
{
    "success": true,
    "message": "User deleted successfully"
}
```

**Errors:**
- `403`: Cannot delete superadmin users
- `404`: User not found

---

## 🖥️ Server Management Endpoints

### GET /server/status
Server durumunu getirir.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `operator`, `admin`, `superadmin`

**Response (200):**
```json
{
    "success": true,
    "data": {
        "status": "running",
        "host": "127.0.0.1",
        "port": 8080,
        "ssl_enabled": false,
        "url": "http://127.0.0.1:8080",
        "uptime_seconds": 3600,
        "start_time": "2025-01-01T11:00:00Z",
        "pid": 1234,
        "version": "1.0.0",
        "environment": "development"
    }
}
```

### POST /server/start
Server'ı başlatır.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `operator`, `admin`, `superadmin`

**Request Body (Optional):**
```json
{
    "host": "127.0.0.1",
    "port": 8080,
    "ssl_enabled": false
}
```

**Response (200):**
```json
{
    "success": true,
    "message": "Server started successfully",
    "data": {
        "status": "starting",
        "pid": 1234,
        "start_time": "2025-01-01T12:00:00Z"
    }
}
```

### POST /server/stop
Server'ı durdurur.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `operator`, `admin`, `superadmin`

**Response (200):**
```json
{
    "success": true,
    "message": "Server stopped successfully"
}
```

### POST /server/restart
Server'ı yeniden başlatır.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `operator`, `admin`, `superadmin`

**Response (200):**
```json
{
    "success": true,
    "message": "Server restart initiated"
}
```

### GET /server/config
Server yapılandırmasını getirir.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `admin`, `superadmin`

**Response (200):**
```json
{
    "success": true,
    "data": {
        "host": "127.0.0.1",
        "port": 8080,
        "ssl_enabled": false,
        "ssl_cert_path": null,
        "ssl_key_path": null,
        "cors_enabled": true,
        "cors_origins": ["*"],
        "rate_limit_enabled": true,
        "rate_limit_requests": 100,
        "rate_limit_window": 60,
        "debug": false,
        "log_level": "INFO"
    }
}
```

### PUT /server/config
Server yapılandırmasını günceller.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `admin`, `superadmin`

**Request Body:**
```json
{
    "host": "0.0.0.0",
    "port": 8443,
    "ssl_enabled": true,
    "ssl_cert_path": "/path/to/cert.pem",
    "ssl_key_path": "/path/to/key.pem",
    "cors_origins": ["https://example.com"],
    "rate_limit_requests": 200,
    "log_level": "DEBUG"
}
```

**Response (200):**
```json
{
    "success": true,
    "message": "Configuration updated successfully",
    "data": {
        "restart_required": true
    }
}
```

---

## 📊 Monitoring Endpoints

### GET /monitor/system
Sistem metriklerini getirir.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `operator`, `admin`, `superadmin`

**Response (200):**
```json
{
    "success": true,
    "data": {
        "timestamp": "2025-01-01T12:00:00Z",
        "cpu": {
            "percent": 45.2,
            "cores": 8,
            "load_average": [1.2, 1.5, 1.8]
        },
        "memory": {
            "total": 16777216000,
            "available": 8388608000,
            "used": 8388608000,
            "percent": 50.0
        },
        "disk": {
            "total": 1000000000000,
            "used": 500000000000,
            "free": 500000000000,
            "percent": 50.0
        },
        "network": {
            "bytes_sent": 1000000,
            "bytes_recv": 2000000,
            "packets_sent": 1000,
            "packets_recv": 2000
        }
    }
}
```

### GET /monitor/database
Veritabanı metriklerini getirir.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `admin`, `superadmin`

**Response (200):**
```json
{
    "success": true,
    "data": {
        "status": "connected",
        "database_size": 10485760,
        "tables": [
            {
                "name": "users",
                "rows": 100,
                "size": 1048576
            },
            {
                "name": "sessions",
                "rows": 50,
                "size": 524288
            }
        ],
        "connections": {
            "active": 5,
            "idle": 10,
            "max": 20
        },
        "query_stats": {
            "total_queries": 1000,
            "slow_queries": 5,
            "avg_query_time": 0.05
        }
    }
}
```

### GET /monitor/api
API metriklerini getirir.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `operator`, `admin`, `superadmin`

**Query Parameters:**
- `period`: Zaman aralığı (1h, 24h, 7d, 30d)

**Response (200):**
```json
{
    "success": true,
    "data": {
        "period": "24h",
        "total_requests": 10000,
        "successful_requests": 9500,
        "failed_requests": 500,
        "avg_response_time": 0.15,
        "endpoints": [
            {
                "path": "/api/v1/users",
                "method": "GET",
                "requests": 2000,
                "avg_response_time": 0.12,
                "error_rate": 0.02
            }
        ],
        "status_codes": {
            "200": 8000,
            "400": 300,
            "401": 100,
            "404": 50,
            "500": 50
        }
    }
}
```

---

## 📝 Logging Endpoints

### GET /logs
Log kayıtlarını getirir.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `operator`, `admin`, `superadmin`

**Query Parameters:**
- `level`: Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `start_date`: Başlangıç tarihi (ISO format)
- `end_date`: Bitiş tarihi (ISO format)
- `module`: Modül filtresi
- `search`: Arama terimi
- `page`: Sayfa numarası
- `limit`: Sayfa başına kayıt

**Response (200):**
```json
{
    "success": true,
    "data": {
        "logs": [
            {
                "id": 1,
                "timestamp": "2025-01-01T12:00:00Z",
                "level": "INFO",
                "module": "api.server",
                "logger_name": "server_manager",
                "message": "Server started successfully",
                "user_id": null,
                "ip_address": null,
                "extra_data": {}
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 50,
            "total": 1000,
            "pages": 20
        }
    }
}
```

### GET /logs/export
Log'ları export eder.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `admin`, `superadmin`

**Query Parameters:**
- `format`: Export formatı (json, csv, txt)
- Diğer filtre parametreleri

**Response (200):**
```json
{
    "success": true,
    "data": {
        "download_url": "/api/v1/files/exports/logs_20250101_120000.json",
        "expires_at": "2025-01-01T13:00:00Z"
    }
}
```

---

## ⚙️ Configuration Endpoints

### GET /config
Sistem yapılandırmasını getirir.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `superadmin`

**Query Parameters:**
- `category`: Kategori filtresi

**Response (200):**
```json
{
    "success": true,
    "data": {
        "app": {
            "name": "API Server Management System",
            "version": "1.0.0",
            "debug": false,
            "environment": "production"
        },
        "server": {
            "host": "127.0.0.1",
            "port": 8080,
            "ssl_enabled": false,
            "auto_start": true
        },
        "security": {
            "jwt_secret_key": "***",
            "jwt_expiry": 3600,
            "password_min_length": 6,
            "max_login_attempts": 5
        },
        "database": {
            "path": "data/app.db",
            "backup_enabled": true,
            "backup_interval": 24
        }
    }
}
```

### PUT /config
Sistem yapılandırmasını günceller.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `superadmin`

**Request Body:**
```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 8443,
        "ssl_enabled": true
    },
    "security": {
        "jwt_expiry": 7200,
        "max_login_attempts": 3
    }
}
```

**Response (200):**
```json
{
    "success": true,
    "message": "Configuration updated successfully",
    "data": {
        "restart_required": true,
        "updated_keys": ["server.host", "server.port", "server.ssl_enabled", "security.jwt_expiry"]
    }
}
```

---

## 📁 File Management Endpoints

### GET /files
Dosya listesini getirir.

**Headers:** `Authorization: Bearer <token>`  
**Required Roles:** `admin`, `superadmin`

**Response (200):**
```json
{
    "success": true,
    "data": {
        "files": [
            {
                "id": 1,
                "filename": "backup_20250101.db",
                "path": "data/backup/backup_20250101.db",
                "size": 1048576,
                "created_at": "2025-01-01T00:00:00Z",
                "type": "backup"
            }
        ]
    }
}
```

### POST /files/upload
Dosya yükler.

**Headers:** 
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Required Roles:** `admin`, `superadmin`

**Form Data:**
- `file`: Yüklenecek dosya
- `type`: Dosya tipi (avatar, config, backup)

**Response (201):**
```json
{
    "success": true,
    "data": {
        "id": 2,
        "filename": "avatar.jpg",
        "path": "data/uploads/avatar.jpg",
        "size": 524288,
        "url": "/api/v1/files/2"
    }
}
```

---

## 🔌 WebSocket Endpoints

### WS /ws/system/status
Real-time sistem durumu.

**Headers:** `Authorization: Bearer <token>`

**Message Types:**
```json
{
    "type": "system_metrics",
    "data": {
        "cpu_percent": 45.2,
        "memory_percent": 60.1,
        "timestamp": "2025-01-01T12:00:00Z"
    }
}
```

### WS /ws/logs/stream
Canlı log akışı.

**Headers:** `Authorization: Bearer <token>`

**Message Types:**
```json
{
    "type": "log_entry",
    "data": {
        "timestamp": "2025-01-01T12:00:00Z",
        "level": "INFO",
        "module": "api.server",
        "message": "New user logged in"
    }
}
```

---

## ❌ Error Handling

### Standard Error Format

Tüm API hatalar aşağıdaki formatta döner:

```json
{
    "success": false,
    "error": "Error message",
    "error_code": "ERROR_CODE",
    "details": {},
    "timestamp": "2025-01-01T12:00:00Z",
    "request_id": "uuid"
}
```

### HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **409**: Conflict
- **422**: Validation Error
- **429**: Too Many Requests
- **500**: Internal Server Error

### Common Error Codes

- `INVALID_CREDENTIALS`: Geçersiz kullanıcı bilgileri
- `TOKEN_EXPIRED`: Token süresi dolmuş
- `INSUFFICIENT_PERMISSIONS`: Yetersiz yetki
- `VALIDATION_FAILED`: Veri doğrulama hatası
- `RESOURCE_NOT_FOUND`: Kaynak bulunamadı
- `RATE_LIMIT_EXCEEDED`: Rate limit aşıldı
- `SERVER_ERROR`: Sunucu hatası

---

## 🔒 Güvenlik

### Rate Limiting
- Varsayılan: 100 request/dakika per IP
- Authentication endpoint'leri: 5 request/dakika per IP
- Superadmin kullanıcıları için rate limit yok

### CORS Policy
- Varsayılan: Tüm origin'lere izin
- Production'da specific domain'ler için yapılandırılmalı

### Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (HTTPS için)

### Input Validation
- Tüm input'lar Pydantic schemas ile validate edilir
- SQL injection koruması
- XSS koruması
- CSRF token validation (form submission'lar için)

---

## 📈 API Versioning

- Current Version: v1
- Version header: `API-Version: v1`
- URL versioning: `/api/v1/`
- Backward compatibility: Minimum 6 ay

---

## 🧪 Testing

### Test Endpoints

```bash
# Health check
curl -X GET http://localhost:8080/api/v1/health

# Login
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Get users (with token)
curl -X GET http://localhost:8080/api/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Postman Collection
Postman collection dosyası: `docs/postman/API_Server_Management.json`

---

## 📞 Support

- **Email**: support@example.com
- **Documentation**: https://docs.example.com
- **GitHub Issues**: https://github.com/example/api-server-manager/issues