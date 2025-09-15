# 🔒 API Server Management System - Güvenlik Dokümantasyonu

## 📋 Genel Bakış

Bu dokümantasyon, API Server Management System'in güvenlik mimarisini, politikalarını, best practice'leri ve güvenlik önlemlerini detaylandırır. Sistem, modern güvenlik standartlarına uygun olarak tasarlanmış ve çoklu güvenlik katmanları ile korunmaktadır.

---

## 🛡️ Güvenlik Mimarisi

### Çok Katmanlı Güvenlik Modeli

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  • Input Validation        • XSS Protection                 │
│  • CSRF Protection         • SQL Injection Prevention       │
│  • Output Encoding         • File Upload Security           │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION LAYER                     │
├─────────────────────────────────────────────────────────────┤
│  • JWT Token Authentication • Multi-Factor Authentication   │
│  • Session Management       • Password Policies             │
│  • Account Lockout          • Token Blacklisting            │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    AUTHORIZATION LAYER                      │
├─────────────────────────────────────────────────────────────┤
│  • Role-Based Access Control • Permission Checking          │
│  • Resource-Level Security   • Dynamic Authorization        │
│  • Principle of Least Privilege                             │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    TRANSPORT LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  • HTTPS/TLS Encryption     • Certificate Management        │
│  • Secure Headers           • CORS Configuration            │
│  • Rate Limiting             • IP Whitelisting              │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                               │
├─────────────────────────────────────────────────────────────┤
│  • Data Encryption at Rest  • Database Security             │
│  • Secure Backup Storage    • Audit Logging                 │
│  • Data Anonymization       • Secure Key Management         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication (Kimlik Doğrulama)

### 1. JWT Token Authentication

#### Token Yapısı
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": 123,
    "username": "admin",
    "roles": ["admin", "operator"],
    "exp": 1640995200,
    "iat": 1640991600,
    "jti": "unique-token-id"
  },
  "signature": "HMACSHA256(...)"
}
```

#### Token Güvenlik Önlemleri
- **Short-lived Access Tokens**: 1 saat (varsayılan)
- **Long-lived Refresh Tokens**: 30 gün (varsayılan)
- **Token Rotation**: Her refresh'te yeni token
- **Token Blacklisting**: Çıkış yapılan token'lar
- **Secure Secret Key**: Minimum 256-bit entropy

#### Implementation
```python
class TokenService:
    def generate_access_token(self, user: User) -> str:
        """Access token oluştur"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'roles': [role.name for role in user.roles],
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'jti': str(uuid.uuid4())
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm='HS256')
    
    def verify_token(self, token: str) -> dict:
        """Token doğrula"""
        try:
            # Blacklist kontrolü
            if self.is_token_blacklisted(token):
                raise InvalidTokenError("Token is blacklisted")
            
            # Token decode
            payload = jwt.decode(token, settings.jwt_secret, algorithms=['HS256'])
            
            # Kullanıcı aktiflik kontrolü
            user = User.get_by_id(payload['user_id'])
            if not user.is_active:
                raise InvalidTokenError("User account is disabled")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")
```

### 2. Multi-Factor Authentication (MFA)

#### TOTP (Time-based One-Time Password)
```python
class TOTPService:
    def generate_secret(self) -> str:
        """TOTP secret oluştur"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user: User, secret: str) -> str:
        """QR kod oluştur"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="API Server Manager"
        )
        return qrcode.make(totp_uri)
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """TOTP token doğrula"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
```

#### SMS Verification
```python
class SMSService:
    def send_verification_code(self, phone: str) -> str:
        """SMS doğrulama kodu gönder"""
        code = self.generate_random_code(6)
        
        # Rate limiting
        if self.is_rate_limited(phone):
            raise RateLimitError("Too many SMS requests")
        
        # SMS gönder
        self.sms_provider.send_sms(phone, f"Verification code: {code}")
        
        # Cache'de sakla (5 dakika)
        self.cache.set(f"sms_code:{phone}", code, timeout=300)
        
        return code
```

### 3. Password Security

#### Password Policy
```python
class PasswordPolicy:
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True  
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    def validate_password(self, password: str) -> List[str]:
        """Parola politikasını kontrol et"""
        errors = []
        
        if len(password) < self.MIN_LENGTH:
            errors.append(f"Password must be at least {self.MIN_LENGTH} characters")
        
        if len(password) > self.MAX_LENGTH:
            errors.append(f"Password must be at most {self.MAX_LENGTH} characters")
        
        if self.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.REQUIRE_SPECIAL_CHARS and not re.search(f'[{re.escape(self.SPECIAL_CHARS)}]', password):
            errors.append("Password must contain at least one special character")
        
        return errors
```

#### Password Hashing
```python
class SecurityManager:
    def hash_password(self, password: str) -> str:
        """Parolayı hash'le"""
        # bcrypt kullan (cost factor: 12)
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Parolayı doğrula"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

---

## 🎭 Authorization (Yetkilendirme)

### 1. Role-Based Access Control (RBAC)

#### Rol Hiyerarşisi
```
superadmin (Tüm yetkiler)
    ├── admin (Kullanıcı ve sistem yönetimi)
    │   ├── operator (Server ve monitoring)
    │   └── viewer (Sadece okuma)
    └── api_user (Sadece API erişimi)
```

#### Rol Tanımları
```python
ROLES = {
    'superadmin': {
        'name': 'Super Administrator',
        'description': 'Full system access',
        'permissions': ['*'],  # Tüm yetkiler
        'inherits': []
    },
    'admin': {
        'name': 'Administrator', 
        'description': 'User and system management',
        'permissions': [
            'users.*', 'roles.*', 'config.*', 
            'server.read', 'monitor.read', 'logs.read'
        ],
        'inherits': ['operator']
    },
    'operator': {
        'name': 'Operator',
        'description': 'Server and monitoring management',
        'permissions': [
            'server.*', 'monitor.*', 'logs.read',
            'users.read', 'config.read'
        ],
        'inherits': ['viewer']
    },
    'viewer': {
        'name': 'Viewer',
        'description': 'Read-only access',
        'permissions': [
            '*.read'
        ],
        'inherits': []
    },
    'api_user': {
        'name': 'API User',
        'description': 'API access only',
        'permissions': [
            'api.*'
        ],
        'inherits': []
    }
}
```

#### Permission Checking
```python
class AuthorizationService:
    def has_permission(self, user: User, resource: str, action: str) -> bool:
        """Kullanıcının yetkisini kontrol et"""
        permission = f"{resource}.{action}"
        
        # Superadmin her şeyi yapabilir
        if 'superadmin' in [role.name for role in user.roles]:
            return True
        
        # Kullanıcı rollerini kontrol et
        user_permissions = set()
        for role in user.roles:
            user_permissions.update(self.get_role_permissions(role.name))
        
        # Wildcard permissions
        if '*' in user_permissions:
            return True
        
        if f"{resource}.*" in user_permissions:
            return True
        
        if f"*.{action}" in user_permissions:
            return True
        
        # Exact permission
        return permission in user_permissions
    
    def require_permission(self, resource: str, action: str):
        """Decorator: İzin gerektirir"""
        def decorator(func):
            @wraps(func)
            async def wrapper(request):
                user = await self.get_current_user(request)
                if not self.has_permission(user, resource, action):
                    raise HTTPForbidden()
                return await func(request)
            return wrapper
        return decorator
```

### 2. Resource-Level Security

#### Kullanıcı Kaynak Erişimi
```python
class UserResourceSecurity:
    def can_access_user(self, current_user: User, target_user: User) -> bool:
        """Kullanıcı kaynağına erişim kontrolü"""
        # Kendi profili
        if current_user.id == target_user.id:
            return True
        
        # Admin/Superadmin tüm kullanıcılara erişebilir
        if self.has_admin_role(current_user):
            return True
        
        return False
    
    def can_modify_user(self, current_user: User, target_user: User) -> bool:
        """Kullanıcı değiştirme yetkisi"""
        # Superadmin kendisi dahil herkesi değiştirebilir
        if 'superadmin' in [role.name for role in current_user.roles]:
            return True
        
        # Admin, superadmin olmayan kullanıcıları değiştirebilir
        if 'admin' in [role.name for role in current_user.roles]:
            if 'superadmin' not in [role.name for role in target_user.roles]:
                return True
        
        # Kullanıcı kendi profilini değiştirebilir (sınırlı)
        if current_user.id == target_user.id:
            return True
        
        return False
```

---

## 🛡️ Input Validation ve Sanitization

### 1. Pydantic Schema Validation

#### User Schema
```python
class UserCreateSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    roles: List[str] = Field(..., min_items=1)
    
    @validator('username')
    def validate_username(cls, v):
        if v.lower() in ['admin', 'root', 'system']:
            raise ValueError('Reserved username')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        policy = PasswordPolicy()
        errors = policy.validate_password(v)
        if errors:
            raise ValueError('; '.join(errors))
        return v
```

### 2. SQL Injection Prevention

#### Peewee ORM Protection
```python
# ✅ Güvenli - Peewee ORM kullanımı
def get_users_by_role(role_name: str):
    return User.select().join(UserRole).join(Role).where(Role.name == role_name)

# ❌ Güvensiz - Raw SQL
def get_users_by_role_unsafe(role_name: str):
    query = f"SELECT * FROM users WHERE role = '{role_name}'"  # SQL Injection riski
    return database.execute_sql(query)

# ✅ Güvenli - Parametrized query
def get_users_by_role_safe(role_name: str):
    query = "SELECT * FROM users WHERE role = ?"
    return database.execute_sql(query, (role_name,))
```

### 3. XSS Protection

#### Output Encoding
```python
class XSSProtection:
    @staticmethod
    def escape_html(text: str) -> str:
        """HTML karakterleri escape et"""
        return html.escape(text, quote=True)
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Input'u temizle"""
        # HTML tag'lerini kaldır
        text = re.sub(r'<[^>]*>', '', text)
        
        # Script tag'lerini kaldır
        text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.IGNORECASE)
        
        # Tehlikeli karakterleri encode et
        dangerous_chars = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;'
        }
        
        for char, encoded in dangerous_chars.items():
            text = text.replace(char, encoded)
        
        return text
```

### 4. File Upload Security

#### Secure File Upload
```python
class FileUploadSecurity:
    ALLOWED_EXTENSIONS = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
        'document': ['.pdf', '.txt', '.doc', '.docx'],
        'config': ['.json', '.yaml', '.yml', '.ini']
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def validate_file(self, file_data: bytes, filename: str, file_type: str) -> bool:
        """Dosyayı doğrula"""
        # Boyut kontrolü
        if len(file_data) > self.MAX_FILE_SIZE:
            raise ValidationError("File too large")
        
        # Extension kontrolü
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS.get(file_type, []):
            raise ValidationError("File type not allowed")
        
        # Magic number kontrolü (dosya içeriği)
        if not self.validate_file_content(file_data, file_ext):
            raise ValidationError("File content doesn't match extension")
        
        # Virus scan (opsiyonel)
        if self.scan_for_virus(file_data):
            raise ValidationError("File contains malware")
        
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """Dosya adını temizle"""
        # Tehlikeli karakterleri kaldır
        filename = re.sub(r'[^\w\-_\.]', '', filename)
        
        # Path traversal koruması
        filename = os.path.basename(filename)
        
        # Maksimum uzunluk
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
```

---

## 🔒 Data Security

### 1. Encryption at Rest

#### Database Encryption
```python
class DatabaseEncryption:
    def __init__(self, key: bytes):
        self.cipher_suite = Fernet(key)
    
    def encrypt_sensitive_field(self, data: str) -> str:
        """Hassas veriyi şifrele"""
        if not data:
            return data
        
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_sensitive_field(self, encrypted_data: str) -> str:
        """Şifreli veriyi çöz"""
        if not encrypted_data:
            return encrypted_data
        
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            raise DecryptionError("Failed to decrypt data")

# Model'de kullanım
class User(BaseModel):
    username = CharField()
    email = CharField()
    password_hash = CharField()
    phone = CharField()  # Şifrelenecek
    
    def set_phone(self, phone: str):
        """Telefonu şifrele ve kaydet"""
        if phone:
            self.phone = encryption.encrypt_sensitive_field(phone)
        else:
            self.phone = None
    
    def get_phone(self) -> str:
        """Telefonu çöz ve döndür"""
        if self.phone:
            return encryption.decrypt_sensitive_field(self.phone)
        return None
```

### 2. Secure Key Management

#### Key Rotation
```python
class KeyManager:
    def __init__(self):
        self.current_key_id = self.get_current_key_id()
        self.keys = self.load_keys()
    
    def generate_new_key(self) -> str:
        """Yeni şifreleme anahtarı oluştur"""
        key = Fernet.generate_key()
        key_id = str(uuid.uuid4())
        
        # Güvenli şekilde sakla
        self.store_key(key_id, key)
        
        return key_id
    
    def rotate_keys(self):
        """Anahtarları rotasyona al"""
        new_key_id = self.generate_new_key()
        
        # Eski anahtarla şifrelenmiş verileri yeni anahtarla yeniden şifrele
        self.reencrypt_data(self.current_key_id, new_key_id)
        
        # Mevcut anahtar ID'sini güncelle
        self.current_key_id = new_key_id
        
        # Eski anahtarı arşivle (hemen silme, geri dönüş için)
        self.archive_key(self.current_key_id)
```

### 3. Backup Security

#### Encrypted Backups
```python
class SecureBackupService:
    def create_backup(self, backup_path: str, encryption_key: bytes):
        """Şifrelenmiş backup oluştur"""
        # Database dump
        dump_data = self.create_database_dump()
        
        # Compress
        compressed_data = gzip.compress(dump_data.encode())
        
        # Encrypt
        cipher_suite = Fernet(encryption_key)
        encrypted_data = cipher_suite.encrypt(compressed_data)
        
        # Save with integrity check
        backup_data = {
            'data': base64.b64encode(encrypted_data).decode(),
            'checksum': hashlib.sha256(encrypted_data).hexdigest(),
            'created_at': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f)
    
    def restore_backup(self, backup_path: str, encryption_key: bytes):
        """Şifrelenmiş backup'ı geri yükle"""
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        # Integrity check
        encrypted_data = base64.b64decode(backup_data['data'])
        if hashlib.sha256(encrypted_data).hexdigest() != backup_data['checksum']:
            raise BackupCorruptedError("Backup integrity check failed")
        
        # Decrypt
        cipher_suite = Fernet(encryption_key)
        compressed_data = cipher_suite.decrypt(encrypted_data)
        
        # Decompress
        dump_data = gzip.decompress(compressed_data).decode()
        
        # Restore database
        self.restore_database_dump(dump_data)
```

---

## 🚦 Rate Limiting ve DDoS Protection

### 1. Rate Limiting Implementation

#### Token Bucket Algorithm
```python
class RateLimiter:
    def __init__(self, capacity: int, refill_rate: int):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.buckets = {}  # {identifier: {'tokens': int, 'last_refill': float}}
    
    def is_allowed(self, identifier: str) -> bool:
        """Rate limit kontrolü"""
        now = time.time()
        
        if identifier not in self.buckets:
            self.buckets[identifier] = {
                'tokens': self.capacity,
                'last_refill': now
            }
        
        bucket = self.buckets[identifier]
        
        # Token'ları yenile
        elapsed = now - bucket['last_refill']
        tokens_to_add = elapsed * self.refill_rate
        bucket['tokens'] = min(self.capacity, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = now
        
        # Token tüket
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True
        
        return False

# Middleware olarak kullanım
class RateLimitMiddleware:
    def __init__(self):
        self.general_limiter = RateLimiter(100, 1)  # 100 req/min
        self.auth_limiter = RateLimiter(5, 0.1)     # 5 req/min
    
    async def __call__(self, request, handler):
        client_ip = self.get_client_ip(request)
        
        # Authentication endpoint'leri için özel limit
        if request.path.startswith('/api/v1/auth'):
            if not self.auth_limiter.is_allowed(client_ip):
                raise HTTPTooManyRequests()
        else:
            if not self.general_limiter.is_allowed(client_ip):
                raise HTTPTooManyRequests()
        
        return await handler(request)
```

### 2. IP Whitelisting/Blacklisting

#### IP Access Control
```python
class IPAccessControl:
    def __init__(self):
        self.whitelist = set()
        self.blacklist = set()
        self.whitelist_networks = []
        self.blacklist_networks = []
    
    def add_to_whitelist(self, ip_or_network: str):
        """Whitelist'e ekle"""
        try:
            network = ipaddress.ip_network(ip_or_network, strict=False)
            if network.num_addresses == 1:
                self.whitelist.add(str(network.network_address))
            else:
                self.whitelist_networks.append(network)
        except ValueError:
            logger.error(f"Invalid IP or network: {ip_or_network}")
    
    def add_to_blacklist(self, ip_or_network: str):
        """Blacklist'e ekle"""
        try:
            network = ipaddress.ip_network(ip_or_network, strict=False)
            if network.num_addresses == 1:
                self.blacklist.add(str(network.network_address))
            else:
                self.blacklist_networks.append(network)
        except ValueError:
            logger.error(f"Invalid IP or network: {ip_or_network}")
    
    def is_allowed(self, ip: str) -> bool:
        """IP'nin erişim yetkisi var mı"""
        try:
            ip_addr = ipaddress.ip_address(ip)
            
            # Blacklist kontrolü
            if ip in self.blacklist:
                return False
            
            for network in self.blacklist_networks:
                if ip_addr in network:
                    return False
            
            # Whitelist boşsa, tüm IP'lere izin ver
            if not self.whitelist and not self.whitelist_networks:
                return True
            
            # Whitelist kontrolü
            if ip in self.whitelist:
                return True
            
            for network in self.whitelist_networks:
                if ip_addr in network:
                    return True
            
            return False
            
        except ValueError:
            return False
```

---

## 📊 Security Monitoring ve Logging

### 1. Security Event Logging

#### Security Logger
```python
class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('security')
        handler = logging.FileHandler('data/logs/security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_login_attempt(self, username: str, ip: str, success: bool, user_agent: str = None):
        """Login denemesini logla"""
        event = {
            'event_type': 'login_attempt',
            'username': username,
            'ip_address': ip,
            'success': success,
            'user_agent': user_agent,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if success:
            self.logger.info(f"Successful login: {json.dumps(event)}")
        else:
            self.logger.warning(f"Failed login attempt: {json.dumps(event)}")
    
    def log_permission_denied(self, user_id: int, resource: str, action: str, ip: str):
        """İzin reddedilmesini logla"""
        event = {
            'event_type': 'permission_denied',
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'ip_address': ip,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.warning(f"Permission denied: {json.dumps(event)}")
    
    def log_suspicious_activity(self, description: str, ip: str, user_id: int = None):
        """Şüpheli aktiviteyi logla"""
        event = {
            'event_type': 'suspicious_activity',
            'description': description,
            'ip_address': ip,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.error(f"Suspicious activity: {json.dumps(event)}")
```

### 2. Intrusion Detection

#### Anomaly Detection
```python
class IntrusionDetectionSystem:
    def __init__(self):
        self.failed_login_threshold = 5
        self.failed_login_window = 900  # 15 minutes
        self.suspicious_patterns = [
            r'(?i)(union|select|insert|delete|drop|create|alter)',  # SQL injection
            r'(?i)(<script|javascript:|vbscript:|onload|onerror)',   # XSS
            r'(?i)(\.\.\/|\.\.\\)',                                  # Path traversal
        ]
    
    def check_failed_logins(self, ip: str) -> bool:
        """Başarısız login denemelerini kontrol et"""
        recent_failures = self.get_recent_failed_logins(ip, self.failed_login_window)
        
        if len(recent_failures) >= self.failed_login_threshold:
            self.security_logger.log_suspicious_activity(
                f"Multiple failed login attempts from {ip}",
                ip
            )
            return True
        
        return False
    
    def check_suspicious_patterns(self, request_data: str, ip: str) -> bool:
        """Şüpheli pattern'leri kontrol et"""
        for pattern in self.suspicious_patterns:
            if re.search(pattern, request_data):
                self.security_logger.log_suspicious_activity(
                    f"Suspicious pattern detected: {pattern}",
                    ip
                )
                return True
        
        return False
    
    def analyze_request(self, request) -> bool:
        """Request'i analiz et"""
        ip = self.get_client_ip(request)
        
        # URL ve body'yi kontrol et
        request_data = f"{request.url} {await request.text()}"
        
        if self.check_suspicious_patterns(request_data, ip):
            return True
        
        if self.check_failed_logins(ip):
            return True
        
        return False
```

### 3. Alert System

#### Security Alerts
```python
class SecurityAlertSystem:
    def __init__(self):
        self.alert_channels = []
        self.alert_thresholds = {
            'failed_login_threshold': 10,
            'suspicious_activity_threshold': 5,
            'rate_limit_violations': 20
        }
    
    def add_alert_channel(self, channel):
        """Alert kanalı ekle"""
        self.alert_channels.append(channel)
    
    def send_security_alert(self, alert_type: str, description: str, severity: str = 'medium'):
        """Güvenlik uyarısı gönder"""
        alert = {
            'type': alert_type,
            'description': description,
            'severity': severity,
            'timestamp': datetime.utcnow().isoformat(),
            'hostname': socket.gethostname()
        }
        
        for channel in self.alert_channels:
            try:
                channel.send_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")
    
    def check_alert_conditions(self):
        """Alert koşullarını kontrol et"""
        # Son 1 saatteki failed login'leri kontrol et
        failed_logins = self.get_recent_failed_logins_count(3600)
        if failed_logins > self.alert_thresholds['failed_login_threshold']:
            self.send_security_alert(
                'high_failed_login_rate',
                f"{failed_logins} failed login attempts in the last hour",
                'high'
            )
        
        # Şüpheli aktivite sayısını kontrol et
        suspicious_activities = self.get_recent_suspicious_activities_count(3600)
        if suspicious_activities > self.alert_thresholds['suspicious_activity_threshold']:
            self.send_security_alert(
                'high_suspicious_activity',
                f"{suspicious_activities} suspicious activities in the last hour",
                'high'
            )
```

---

## 🔧 Security Configuration

### 1. Security Headers

#### HTTP Security Headers
```python
class SecurityHeadersMiddleware:
    def __init__(self):
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': self.get_csp_policy(),
            'Permissions-Policy': self.get_permissions_policy()
        }
    
    def get_csp_policy(self) -> str:
        """Content Security Policy oluştur"""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
    
    def get_permissions_policy(self) -> str:
        """Permissions Policy oluştur"""
        return (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
    
    async def __call__(self, request, handler):
        response = await handler(request)
        
        # Security header'ları ekle
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # HTTPS için ek header'lar
        if request.scheme == 'https':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
```

### 2. CORS Configuration

#### CORS Security
```python
class CORSMiddleware:
    def __init__(self, allowed_origins=None, allowed_methods=None, allowed_headers=None):
        self.allowed_origins = allowed_origins or ['*']
        self.allowed_methods = allowed_methods or ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        self.allowed_headers = allowed_headers or ['Content-Type', 'Authorization']
        self.max_age = 86400  # 24 hours
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Origin'in izinli olup olmadığını kontrol et"""
        if '*' in self.allowed_origins:
            return True
        
        return origin in self.allowed_origins
    
    async def __call__(self, request, handler):
        origin = request.headers.get('Origin')
        
        # Preflight request
        if request.method == 'OPTIONS':
            if origin and self.is_origin_allowed(origin):
                response = web.Response()
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
                response.headers['Access-Control-Allow-Headers'] = ', '.join(self.allowed_headers)
                response.headers['Access-Control-Max-Age'] = str(self.max_age)
                return response
            else:
                raise web.HTTPForbidden()
        
        response = await handler(request)
        
        # CORS header'ları ekle
        if origin and self.is_origin_allowed(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response
```

---

## 🧪 Security Testing

### 1. Penetration Testing Checklist

#### Authentication Testing
- [ ] Brute force attack resistance
- [ ] Session fixation protection
- [ ] Token expiration handling
- [ ] Multi-factor authentication bypass
- [ ] Password reset vulnerabilities

#### Authorization Testing
- [ ] Privilege escalation attempts
- [ ] Role-based access control bypass
- [ ] Direct object reference vulnerabilities
- [ ] Admin panel access control

#### Input Validation Testing
- [ ] SQL injection vulnerabilities
- [ ] XSS vulnerabilities
- [ ] Command injection
- [ ] File upload vulnerabilities
- [ ] Path traversal attacks

#### Session Management Testing
- [ ] Session hijacking resistance
- [ ] Session timeout enforcement
- [ ] Concurrent session handling
- [ ] Session invalidation

### 2. Security Scan Integration

#### Automated Security Scanning
```python
class SecurityScanner:
    def __init__(self):
        self.scan_results = []
    
    def scan_sql_injection(self, endpoints: List[str]) -> List[dict]:
        """SQL injection taraması"""
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --"
        ]
        
        vulnerabilities = []
        
        for endpoint in endpoints:
            for payload in payloads:
                try:
                    # Test payload'ını gönder
                    response = self.send_test_request(endpoint, payload)
                    
                    # SQL hata mesajlarını kontrol et
                    if self.check_sql_error_patterns(response.text):
                        vulnerabilities.append({
                            'type': 'sql_injection',
                            'endpoint': endpoint,
                            'payload': payload,
                            'severity': 'high'
                        })
                except Exception as e:
                    logger.error(f"Error testing {endpoint}: {e}")
        
        return vulnerabilities
    
    def check_sql_error_patterns(self, response_text: str) -> bool:
        """SQL hata pattern'lerini kontrol et"""
        error_patterns = [
            r'SQL syntax.*MySQL',
            r'Warning.*mysql_.*',
            r'valid MySQL result',
            r'PostgreSQL.*ERROR',
            r'Warning.*pg_.*',
            r'valid PostgreSQL result',
            r'SQLite.*error',
            r'sqlite3.OperationalError'
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                return True
        
        return False
```

---

## 📋 Security Compliance

### 1. OWASP Top 10 Compliance

#### A01: Broken Access Control
- ✅ Role-based access control implemented
- ✅ Permission checking on all endpoints
- ✅ Resource-level security
- ✅ Principle of least privilege

#### A02: Cryptographic Failures
- ✅ Strong encryption algorithms (AES-256, bcrypt)
- ✅ Secure key management
- ✅ Data encryption at rest
- ✅ TLS/HTTPS enforcement

#### A03: Injection
- ✅ Parameterized queries (Peewee ORM)
- ✅ Input validation (Pydantic schemas)
- ✅ Output encoding
- ✅ NoSQL injection prevention

#### A04: Insecure Design
- ✅ Security by design principles
- ✅ Threat modeling
- ✅ Secure architecture patterns
- ✅ Defense in depth

#### A05: Security Misconfiguration
- ✅ Secure default configurations
- ✅ Security headers implementation
- ✅ Error handling (no sensitive info exposure)
- ✅ Regular security updates

#### A06: Vulnerable Components
- ✅ Dependency vulnerability scanning
- ✅ Regular updates
- ✅ Component inventory
- ✅ Security advisories monitoring

#### A07: Identification and Authentication Failures
- ✅ Strong password policies
- ✅ Multi-factor authentication
- ✅ Session management
- ✅ Account lockout mechanisms

#### A08: Software and Data Integrity Failures
- ✅ Code signing
- ✅ Integrity checks
- ✅ Secure CI/CD pipeline
- ✅ Digital signatures

#### A09: Security Logging and Monitoring Failures
- ✅ Comprehensive security logging
- ✅ Real-time monitoring
- ✅ Alert system
- ✅ Incident response procedures

#### A10: Server-Side Request Forgery (SSRF)
- ✅ URL validation
- ✅ Network segmentation
- ✅ Allowlist approach
- ✅ Response filtering

### 2. GDPR Compliance

#### Data Protection Measures
- **Data Minimization**: Sadece gerekli veriler toplanır
- **Purpose Limitation**: Veriler sadece belirtilen amaçlar için kullanılır
- **Storage Limitation**: Veriler gerekli süre kadar saklanır
- **Data Security**: Teknik ve organizasyonel güvenlik önlemleri
- **Privacy by Design**: Varsayılan olarak gizlilik koruması

#### User Rights Implementation
```python
class GDPRComplianceService:
    def export_user_data(self, user_id: int) -> dict:
        """Kullanıcı verilerini export et (Right to Data Portability)"""
        user = User.get_by_id(user_id)
        
        return {
            'personal_data': {
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            },
            'activity_data': self.get_user_activity_logs(user_id),
            'preferences': self.get_user_preferences(user_id)
        }
    
    def anonymize_user_data(self, user_id: int):
        """Kullanıcı verilerini anonimleştir (Right to be Forgotten)"""
        user = User.get_by_id(user_id)
        
        # Kişisel verileri anonimleştir
        user.username = f"deleted_user_{user_id}"
        user.email = f"deleted_{user_id}@anonymized.com"
        user.full_name = "Deleted User"
        user.phone = None
        user.is_active = False
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        user.save()
        
        # İlgili log kayıtlarını anonimleştir
        self.anonymize_user_logs(user_id)
```

---

## 🚨 Incident Response

### 1. Security Incident Response Plan

#### Incident Classification
- **P1 - Critical**: Sistem tamamen çökmüş, veri sızıntısı
- **P2 - High**: Önemli güvenlik açığı, kısmi sistem arızası
- **P3 - Medium**: Güvenlik uyarısı, performans sorunları
- **P4 - Low**: Minör güvenlik olayları

#### Response Procedures
```python
class IncidentResponseSystem:
    def __init__(self):
        self.incident_handlers = {
            'data_breach': self.handle_data_breach,
            'unauthorized_access': self.handle_unauthorized_access,
            'ddos_attack': self.handle_ddos_attack,
            'malware_detection': self.handle_malware_detection
        }
    
    def handle_security_incident(self, incident_type: str, details: dict):
        """Güvenlik olayını işle"""
        # Incident kaydı oluştur
        incident_id = self.create_incident_record(incident_type, details)
        
        # Otomatik response
        if incident_type in self.incident_handlers:
            self.incident_handlers[incident_type](incident_id, details)
        
        # Alert gönder
        self.send_incident_alert(incident_id, incident_type, details)
        
        # Forensic data topla
        self.collect_forensic_data(incident_id)
        
        return incident_id
    
    def handle_data_breach(self, incident_id: str, details: dict):
        """Veri sızıntısı işleme"""
        # Etkilenen kullanıcıları belirle
        affected_users = details.get('affected_users', [])
        
        # Kullanıcı oturumlarını sonlandır
        for user_id in affected_users:
            self.invalidate_user_sessions(user_id)
        
        # Şifre sıfırlama zorla
        for user_id in affected_users:
            self.force_password_reset(user_id)
        
        # Yasal bildirimleri başlat
        self.initiate_legal_notifications(incident_id, affected_users)
```

### 2. Forensic Data Collection

#### Digital Forensics
```python
class ForensicDataCollector:
    def collect_incident_data(self, incident_id: str) -> dict:
        """Olay verilerini topla"""
        return {
            'system_logs': self.collect_system_logs(),
            'security_logs': self.collect_security_logs(),
            'network_logs': self.collect_network_logs(),
            'database_logs': self.collect_database_logs(),
            'application_logs': self.collect_application_logs(),
            'system_state': self.capture_system_state(),
            'memory_dump': self.create_memory_dump(),
            'file_integrity': self.check_file_integrity()
        }
    
    def preserve_evidence(self, evidence_data: dict, incident_id: str):
        """Delilleri koru"""
        # Hash hesapla
        evidence_hash = self.calculate_evidence_hash(evidence_data)
        
        # Şifrele ve sakla
        encrypted_evidence = self.encrypt_evidence(evidence_data)
        
        # Chain of custody kayıt
        custody_record = {
            'incident_id': incident_id,
            'collected_at': datetime.utcnow().isoformat(),
            'collected_by': 'system',
            'evidence_hash': evidence_hash,
            'storage_location': f'forensic/{incident_id}/'
        }
        
        self.store_evidence(encrypted_evidence, custody_record)
```

---

Bu güvenlik dokümantasyonu, API Server Management System'in güvenlik mimarisini ve uygulanan güvenlik önlemlerini kapsamlı şekilde açıklamaktadır. Sistem, modern güvenlik standartlarına uygun olarak tasarlanmış ve çoklu güvenlik katmanları ile korunmaktadır.