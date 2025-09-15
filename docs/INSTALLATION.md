# 📦 API Server Management System - Kurulum Kılavuzu

## 📋 Genel Bakış

Bu dokümantasyon, API Server Management System'in farklı ortamlarda kurulumu, yapılandırılması ve devreye alınması için kapsamlı bir rehber sağlar.

---

## 💻 Sistem Gereksinimleri

### Minimum Gereksinimler

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| **İşletim Sistemi** | Windows 10, macOS 10.14, Ubuntu 18.04 | Windows 11, macOS 12+, Ubuntu 20.04+ |
| **İşlemci** | Dual-core 2.0 GHz | Quad-core 2.5 GHz+ |
| **RAM** | 4 GB | 8 GB+ |
| **Disk Alanı** | 1 GB boş alan | 5 GB+ boş alan |
| **Ekran Çözünürlüğü** | 1024x768 | 1920x1080+ |
| **İnternet Bağlantısı** | Kurulum ve güncellemeler için | Sürekli bağlantı önerilir |

### Desteklenen Platformlar

#### Windows
- ✅ Windows 11 (22H2 ve üzeri)
- ✅ Windows 10 (1909 ve üzeri)
- ✅ Windows Server 2019/2022
- ❌ Windows 8.1 ve öncesi (desteklenmez)

#### macOS
- ✅ macOS Ventura (13.0+)
- ✅ macOS Monterey (12.0+)
- ✅ macOS Big Sur (11.0+)
- ✅ macOS Catalina (10.15+)
- ❌ macOS Mojave ve öncesi (desteklenmez)

#### Linux
- ✅ Ubuntu 20.04 LTS / 22.04 LTS
- ✅ CentOS 8 / Rocky Linux 8+
- ✅ Debian 10+ (Buster ve üzeri)
- ✅ Fedora 35+
- ✅ openSUSE Leap 15.3+

---

## 📥 Kurulum Yöntemleri

### 1. Hazır Executable Kurulumu (Önerilen)

En kolay kurulum yöntemi, önceden derlenmiş executable dosyaları kullanmaktır.

#### Windows Kurulumu

1. **İndirme**
   ```
   https://releases.yourcompany.com/api-server-manager/latest/windows/
   api-server-manager-setup-1.0.0.exe
   ```

2. **Kurulum**
   - Setup dosyasını yönetici olarak çalıştırın
   - Kurulum sihirbazını takip edin
   - Lisans sözleşmesini kabul edin
   - Kurulum dizinini seçin (varsayılan: `C:\Program Files\API Server Manager\`)

3. **İlk Başlatma**
   - Başlat menüsünden "API Server Manager" çalıştırın
   - Firewall izni verin
   - İlk yapılandırmayı tamamlayın

#### macOS Kurulumu

1. **İndirme**
   ```
   https://releases.yourcompany.com/api-server-manager/latest/macos/
   api-server-manager-1.0.0.dmg
   ```

2. **Kurulum**
   ```bash
   # DMG dosyasını mount edin
   hdiutil attach api-server-manager-1.0.0.dmg
   
   # Uygulamayı Applications klasörüne kopyalayın
   cp -R "/Volumes/API Server Manager/API Server Manager.app" /Applications/
   
   # DMG'yi unmount edin
   hdiutil detach "/Volumes/API Server Manager"
   ```

3. **Gatekeeper Ayarları**
   ```bash
   # İmzasız uygulamaya izin verin (gerekirse)
   sudo xattr -rd com.apple.quarantine "/Applications/API Server Manager.app"
   ```

#### Linux Kurulumu

1. **İndirme**
   ```bash
   # Ubuntu/Debian için DEB paketi
   wget https://releases.yourcompany.com/api-server-manager/latest/linux/api-server-manager_1.0.0_amd64.deb
   
   # CentOS/RHEL için RPM paketi
   wget https://releases.yourcompany.com/api-server-manager/latest/linux/api-server-manager-1.0.0-1.x86_64.rpm
   
   # Generic binary
   wget https://releases.yourcompany.com/api-server-manager/latest/linux/api-server-manager-1.0.0-linux.tar.gz
   ```

2. **Paket Kurulumu**
   ```bash
   # Ubuntu/Debian
   sudo dpkg -i api-server-manager_1.0.0_amd64.deb
   sudo apt-get install -f  # Bağımlılıkları çöz
   
   # CentOS/RHEL
   sudo rpm -i api-server-manager-1.0.0-1.x86_64.rpm
   
   # Generic binary
   tar -xzf api-server-manager-1.0.0-linux.tar.gz
   sudo mv api-server-manager /opt/
   sudo ln -s /opt/api-server-manager/api-server-manager /usr/local/bin/
   ```

3. **Desktop Entry Oluşturma**
   ```bash
   cat > ~/.local/share/applications/api-server-manager.desktop << EOF
   [Desktop Entry]
   Version=1.0
   Type=Application
   Name=API Server Manager
   Comment=Manage API servers and users
   Exec=/usr/local/bin/api-server-manager
   Icon=/opt/api-server-manager/resources/icon.png
   Terminal=false
   Categories=Development;Network;
   EOF
   ```

### 2. Kaynak Koddan Kurulum

Geliştiriciler ve ileri düzey kullanıcılar için kaynak koddan kurulum.

#### Gereksinimler

- Python 3.8+ 
- pip (Python package manager)
- Git
- C++ derleyici (PyQt5 için)

#### Kurulum Adımları

1. **Kaynak Kodunu İndirme**
   ```bash
   git clone https://github.com/yourcompany/api-server-manager.git
   cd api-server-manager
   ```

2. **Sanal Ortam Oluşturma**
   ```bash
   # Python virtual environment oluştur
   python -m venv venv
   
   # Aktifleştir
   # Windows
   venv\Scripts\activate
   # macOS/Linux  
   source venv/bin/activate
   ```

3. **Bağımlılıkları Yükleme**
   ```bash
   # Production bağımlılıkları
   pip install -r requirements.txt
   
   # Development bağımlılıkları (opsiyonel)
   pip install -r requirements-dev.txt
   ```

4. **Veritabanını Başlatma**
   ```bash
   python scripts/migrate.py
   ```

5. **Uygulamayı Çalıştırma**
   ```bash
   python run.py
   ```

### 3. Docker Kurulumu

Konteyner tabanlı kurulum için Docker kullanabilirsiniz.

#### Docker Compose (Önerilen)

1. **docker-compose.yml Oluşturma**
   ```yaml
   version: '3.8'
   
   services:
     api-server-manager:
       image: yourcompany/api-server-manager:latest
       container_name: api-server-manager
       ports:
         - "8080:8080"
         - "5900:5900"  # VNC için
       volumes:
         - ./data:/app/data
         - ./config:/app/config
       environment:
         - DISPLAY=:1
         - VNC_PASSWORD=password123
       restart: unless-stopped
   
     vnc-server:
       image: consol/ubuntu-xfce-vnc:latest
       container_name: vnc-server
       ports:
         - "6901:6901"
       environment:
         - VNC_PW=password123
       volumes:
         - ./vnc-data:/headless
   ```

2. **Çalıştırma**
   ```bash
   docker-compose up -d
   ```

3. **Erişim**
   - VNC: http://localhost:6901 (password: password123)
   - API: http://localhost:8080

#### Standalone Docker

```bash
# Image çekme
docker pull yourcompany/api-server-manager:latest

# Konteyner çalıştırma
docker run -d \
  --name api-server-manager \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  yourcompany/api-server-manager:latest
```

---

## ⚙️ İlk Yapılandırma

### 1. Otomatik Kurulum Sihirbazı

Uygulama ilk kez başlatıldığında kurulum sihirbazı çalışır:

```
┌─────────────────────────────────────────────────────────────┐
│  🚀 Welcome to API Server Manager Setup Wizard             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: Database Setup                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Database Type: [SQLite ▼]                              │ │
│  │ Database Path: [data/app.db        ]                   │ │
│  │                                                        │ │
│  │ ☑ Create sample data                                   │ │
│  │ ☑ Enable automatic backups                             │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  [Back] [Next] [Cancel]                                     │
└─────────────────────────────────────────────────────────────┘
```

### 2. Admin Hesabı Oluşturma

```
┌─────────────────────────────────────────────────────────────┐
│  👤 Create Administrator Account                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Username: [admin          ]                                │
│  Email:    [admin@company.com]                              │
│  Password: [••••••••••••••]                                │
│  Confirm:  [••••••••••••••]                                │
│                                                             │
│  Full Name: [System Administrator]                          │
│                                                             │
│  ⚠️ Please use a strong password!                           │
│                                                             │
│  [Back] [Create Account] [Cancel]                           │
└─────────────────────────────────────────────────────────────┘
```

### 3. Server Ayarları

```
┌─────────────────────────────────────────────────────────────┐
│  🖥️ Server Configuration                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Network Settings:                                          │
│  Host: [127.0.0.1     ]                                     │
│  Port: [8080    ]                                           │
│                                                             │
│  Security:                                                  │
│  ☐ Enable HTTPS/SSL                                         │
│  ☑ Enable authentication                                    │
│  ☑ Enable rate limiting                                     │
│                                                             │
│  Performance:                                               │
│  Max connections: [100 ]                                    │
│  Request timeout: [30  ] seconds                            │
│                                                             │
│  [Back] [Finish Setup] [Cancel]                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Kurulum Tamamlama

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Setup Complete!                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎉 API Server Manager has been successfully configured!    │
│                                                             │
│  Summary:                                                   │
│  • Database: SQLite (data/app.db)                          │
│  • Admin user: admin                                        │
│  • Server: http://127.0.0.1:8080                           │
│  • Auto-start: Enabled                                      │
│                                                             │
│  Next Steps:                                                │
│  1. Change the default admin password                       │
│  2. Configure additional users                              │
│  3. Set up SSL certificate (recommended)                    │
│  4. Configure backup settings                               │
│                                                             │
│  [Start Application] [View Documentation]                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Manuel Yapılandırma

### 1. Yapılandırma Dosyası

Ana yapılandırma dosyası: `data/config.json`

```json
{
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
    "ssl_cert_path": null,
    "ssl_key_path": null,
    "auto_start": true,
    "max_connections": 100,
    "request_timeout": 30
  },
  "database": {
    "type": "sqlite",
    "path": "data/app.db",
    "backup_enabled": true,
    "backup_interval": 24,
    "backup_keep_days": 7
  },
  "security": {
    "jwt_secret_key": "your-secret-key-here",
    "jwt_expiry": 3600,
    "password_min_length": 8,
    "max_login_attempts": 5,
    "lockout_duration": 900
  },
  "ui": {
    "theme": "dark",
    "language": "en",
    "window_width": 1200,
    "window_height": 800,
    "show_splash_screen": true,
    "splash_screen_duration": 3000
  },
  "logging": {
    "level": "INFO",
    "file_enabled": true,
    "console_enabled": true,
    "max_file_size": 10485760,
    "backup_count": 5
  },
  "monitoring": {
    "enabled": true,
    "interval": 60,
    "metrics_retention": 30
  },
  "notifications": {
    "email_enabled": false,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "",
    "smtp_password": "",
    "desktop_notifications": true
  }
}
```

### 2. Environment Variables

Hassas bilgiler için ortam değişkenleri kullanın:

```bash
# Windows
set API_SECRET_KEY=your-secret-key-here
set API_DATABASE_URL=sqlite:///data/app.db
set API_SMTP_PASSWORD=your-smtp-password

# Linux/macOS
export API_SECRET_KEY=your-secret-key-here
export API_DATABASE_URL=sqlite:///data/app.db
export API_SMTP_PASSWORD=your-smtp-password
```

### 3. SSL/HTTPS Yapılandırması

#### Self-Signed Sertifika Oluşturma

```bash
# Private key oluştur
openssl genrsa -out data/certificates/server.key 2048

# Certificate signing request oluştur
openssl req -new -key data/certificates/server.key -out data/certificates/server.csr

# Self-signed sertifika oluştur
openssl x509 -req -days 365 -in data/certificates/server.csr -signkey data/certificates/server.key -out data/certificates/server.crt
```

#### Config'de SSL Etkinleştirme

```json
{
  "server": {
    "ssl_enabled": true,
    "ssl_cert_path": "data/certificates/server.crt",
    "ssl_key_path": "data/certificates/server.key"
  }
}
```

---

## 🗄️ Veritabanı Kurulumu

### SQLite (Varsayılan)

SQLite otomatik olarak kurulur, ek yapılandırma gerekmez.

```json
{
  "database": {
    "type": "sqlite",
    "path": "data/app.db"
  }
}
```

### PostgreSQL

1. **PostgreSQL Kurulumu**
   ```bash
   # Ubuntu/Debian
   sudo apt install postgresql postgresql-contrib
   
   # CentOS/RHEL
   sudo yum install postgresql-server postgresql-contrib
   ```

2. **Veritabanı Oluşturma**
   ```sql
   CREATE DATABASE api_server_manager;
   CREATE USER api_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE api_server_manager TO api_user;
   ```

3. **Config Güncelleme**
   ```json
   {
     "database": {
       "type": "postgresql",
       "host": "localhost",
       "port": 5432,
       "name": "api_server_manager",
       "user": "api_user",
       "password": "secure_password"
     }
   }
   ```

### MySQL

1. **MySQL Kurulumu**
   ```bash
   # Ubuntu/Debian
   sudo apt install mysql-server
   
   # CentOS/RHEL
   sudo yum install mysql-server
   ```

2. **Veritabanı Oluşturma**
   ```sql
   CREATE DATABASE api_server_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'api_user'@'localhost' IDENTIFIED BY 'secure_password';
   GRANT ALL PRIVILEGES ON api_server_manager.* TO 'api_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Config Güncelleme**
   ```json
   {
     "database": {
       "type": "mysql",
       "host": "localhost",
       "port": 3306,
       "name": "api_server_manager",
       "user": "api_user",
       "password": "secure_password"
     }
   }
   ```

---

## 🚀 Servis Olarak Kurulum

### Windows Service

1. **Service Script Oluşturma**
   ```python
   # service.py
   import win32serviceutil
   import win32service
   import win32event
   import servicemanager
   import socket
   import sys
   import os
   
   class APIServerManagerService(win32serviceutil.ServiceFramework):
       _svc_name_ = "APIServerManager"
       _svc_display_name_ = "API Server Manager Service"
       _svc_description_ = "API Server Management System Service"
       
       def __init__(self, args):
           win32serviceutil.ServiceFramework.__init__(self, args)
           self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
           socket.setdefaulttimeout(60)
       
       def SvcStop(self):
           self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
           win32event.SetEvent(self.hWaitStop)
       
       def SvcDoRun(self):
           servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                               servicemanager.PYS_SERVICE_STARTED,
                               (self._svc_name_, ''))
           self.main()
       
       def main(self):
           # Ana uygulama kodunu çalıştır
           from run import main
           main()
   
   if __name__ == '__main__':
       win32serviceutil.HandleCommandLine(APIServerManagerService)
   ```

2. **Service Kurulumu**
   ```cmd
   python service.py install
   python service.py start
   ```

### Linux Systemd Service

1. **Service Dosyası Oluşturma**
   ```bash
   sudo nano /etc/systemd/system/api-server-manager.service
   ```

2. **Service İçeriği**
   ```ini
   [Unit]
   Description=API Server Manager Service
   After=network.target
   
   [Service]
   Type=simple
   User=apiuser
   Group=apiuser
   WorkingDirectory=/opt/api-server-manager
   Environment=PATH=/opt/api-server-manager/venv/bin
   ExecStart=/opt/api-server-manager/venv/bin/python run.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Service Etkinleştirme**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable api-server-manager
   sudo systemctl start api-server-manager
   ```

### macOS LaunchDaemon

1. **Plist Dosyası Oluşturma**
   ```bash
   sudo nano /Library/LaunchDaemons/com.yourcompany.api-server-manager.plist
   ```

2. **Plist İçeriği**
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
             "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.yourcompany.api-server-manager</string>
       <key>ProgramArguments</key>
       <array>
           <string>/Applications/API Server Manager.app/Contents/MacOS/api-server-manager</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <true/>
       <key>StandardErrorPath</key>
       <string>/var/log/api-server-manager.log</string>
       <key>StandardOutPath</key>
       <string>/var/log/api-server-manager.log</string>
   </dict>
   </plist>
   ```

3. **Service Yükleme**
   ```bash
   sudo launchctl load /Library/LaunchDaemons/com.yourcompany.api-server-manager.plist
   sudo launchctl start com.yourcompany.api-server-manager
   ```

---

## 🔒 Güvenlik Yapılandırması

### Firewall Ayarları

#### Windows Firewall

```powershell
# PowerShell (Yönetici olarak çalıştırın)
New-NetFirewallRule -DisplayName "API Server Manager" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```

#### Linux iptables

```bash
# HTTP portu için
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# HTTPS portu için
sudo iptables -A INPUT -p tcp --dport 8443 -j ACCEPT

# Kuralları kaydet
sudo iptables-save > /etc/iptables/rules.v4
```

#### Linux UFW

```bash
sudo ufw allow 8080/tcp
sudo ufw allow 8443/tcp
sudo ufw enable
```

### Reverse Proxy (Nginx)

1. **Nginx Kurulumu**
   ```bash
   sudo apt install nginx
   ```

2. **Nginx Yapılandırması**
   ```nginx
   # /etc/nginx/sites-available/api-server-manager
   server {
       listen 80;
       server_name your-domain.com;
       
       # HTTPS'e yönlendir
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl http2;
       server_name your-domain.com;
       
       ssl_certificate /path/to/certificate.crt;
       ssl_certificate_key /path/to/private.key;
       
       # SSL ayarları
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
       ssl_prefer_server_ciphers off;
       
       location / {
           proxy_pass http://127.0.0.1:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       # WebSocket desteği
       location /ws/ {
           proxy_pass http://127.0.0.1:8080;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
   }
   ```

3. **Site Etkinleştirme**
   ```bash
   sudo ln -s /etc/nginx/sites-available/api-server-manager /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

---

## 📊 Monitoring ve Logging

### Log Yapılandırması

```json
{
  "logging": {
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
      "detailed": {
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
      },
      "simple": {
        "format": "%(levelname)s - %(message)s"
      }
    },
    "handlers": {
      "console": {
        "class": "logging.StreamHandler",
        "level": "INFO",
        "formatter": "simple",
        "stream": "ext://sys.stdout"
      },
      "file": {
        "class": "logging.handlers.RotatingFileHandler",
        "level": "DEBUG",
        "formatter": "detailed",
        "filename": "data/logs/app.log",
        "maxBytes": 10485760,
        "backupCount": 5
      }
    },
    "loggers": {
      "": {
        "level": "INFO",
        "handlers": ["console", "file"]
      }
    }
  }
}
```

### Monitoring Entegrasyonu

#### Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'api-server-manager'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/api/v1/metrics'
    scrape_interval: 30s
```

#### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "API Server Manager",
    "panels": [
      {
        "title": "System CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "cpu_usage_percent",
            "legendFormat": "CPU %"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "memory_usage_percent",
            "legendFormat": "Memory %"
          }
        ]
      }
    ]
  }
}
```

---

## 🧪 Kurulum Doğrulama

### 1. Sistem Kontrolü

```bash
# Servis durumu
systemctl status api-server-manager

# Port kontrolü
netstat -tlnp | grep 8080

# Log kontrolü
tail -f /var/log/api-server-manager.log
```

### 2. API Testi

```bash
# Health check
curl -X GET http://localhost:8080/api/v1/health

# Authentication test
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'
```

### 3. UI Testi

- Tarayıcıda `http://localhost:8080` adresini açın
- Login sayfasının yüklendiğini kontrol edin
- Admin hesabıyla giriş yapın
- Dashboard'ın düzgün görüntülendiğini kontrol edin

### 4. Performance Testi

```bash
# Apache Bench ile basit load test
ab -n 1000 -c 10 http://localhost:8080/api/v1/health

# Curl ile response time testi
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/api/v1/health
```

---

## 🔄 Güncelleme ve Bakım

### Otomatik Güncelleme

Uygulama otomatik güncelleme desteği içerir:

1. **Settings > Updates > Check for Updates**
2. Güncelleme mevcut ise indir
3. Backup oluştur
4. Güncellemeyi uygula
5. Yeniden başlat

### Manuel Güncelleme

1. **Mevcut Sürümü Yedekle**
   ```bash
   cp -r /opt/api-server-manager /opt/api-server-manager.backup
   ```

2. **Yeni Sürümü İndir**
   ```bash
   wget https://releases.yourcompany.com/api-server-manager/latest/api-server-manager-1.1.0.tar.gz
   ```

3. **Güncellemeyi Uygula**
   ```bash
   tar -xzf api-server-manager-1.1.0.tar.gz
   sudo cp -r api-server-manager-1.1.0/* /opt/api-server-manager/
   ```

4. **Servisi Yeniden Başlat**
   ```bash
   sudo systemctl restart api-server-manager
   ```

### Database Migration

```bash
# Migration scriptini çalıştır
python scripts/migrate.py --from-version 1.0.0 --to-version 1.1.0

# Backup oluştur
python scripts/backup.py --type full

# Yeni sürümü başlat
systemctl start api-server-manager
```

---

## ❌ Sorun Giderme

### Yaygın Kurulum Sorunları

#### Port Çakışması

```bash
# Port kullanımını kontrol et
netstat -tlnp | grep 8080
lsof -i :8080

# Çözüm: Config'de port değiştir
sed -i 's/"port": 8080/"port": 8081/g' data/config.json
```

#### İzin Sorunları

```bash
# Dosya izinlerini düzelt
sudo chown -R $USER:$USER /opt/api-server-manager
chmod +x /opt/api-server-manager/api-server-manager

# SELinux sorunları (CentOS/RHEL)
sudo setsebool -P httpd_can_network_connect 1
```

#### Bağımlılık Sorunları

```bash
# Python bağımlılıklarını yeniden yükle
pip install --upgrade --force-reinstall -r requirements.txt

# Sistem paketlerini güncelle
sudo apt update && sudo apt upgrade
```

### Log Analizi

```bash
# Hata mesajları
grep -i error data/logs/app.log

# Son 100 satır
tail -n 100 data/logs/app.log

# Real-time monitoring
tail -f data/logs/app.log | grep -i error
```

### Performance Sorunları

```bash
# Memory kullanımı
ps aux | grep api-server-manager

# CPU kullanımı
top -p $(pgrep api-server-manager)

# Disk I/O
iotop -p $(pgrep api-server-manager)
```

---

## 📞 Destek

### Kurulum Desteği

- **Email**: install-support@yourcompany.com
- **Telefon**: +90 XXX XXX XX XX
- **Dokümantasyon**: https://docs.yourcompany.com/installation
- **Video Rehberler**: https://videos.yourcompany.com/installation

### Topluluk Desteği

- **Forum**: https://community.yourcompany.com
- **Discord**: https://discord.gg/yourcompany
- **Stack Overflow**: Tag `api-server-manager`
- **GitHub Issues**: https://github.com/yourcompany/api-server-manager/issues

Bu kurulum kılavuzu, API Server Management System'i farklı ortamlarda başarıyla kurmanız için gereken tüm bilgileri içermektedir. Kurulum sırasında sorun yaşarsanız, destek kanallarımızdan yardım alabilirsiniz.