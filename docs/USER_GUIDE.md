# 📖 API Server Management System - Kullanıcı Kılavuzu

## 🚀 Hoş Geldiniz

API Server Management System, server'ınızı kolayca yönetmenizi, kullanıcıları kontrol etmenizi ve sistem performansını izlemenizi sağlayan kapsamlı bir yönetim aracıdır. Bu kılavuz, uygulamayı etkili bir şekilde kullanmanız için gereken tüm bilgileri içerir.

---

## 📥 Kurulum ve İlk Başlatma

### Sistem Gereksinimleri

- **İşletim Sistemi**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **RAM**: Minimum 4GB (8GB önerilir)
- **Disk Alanı**: 1GB boş alan
- **İnternet Bağlantısı**: Güncellemeler ve lisans doğrulaması için

### İlk Kurulum

1. **İndirme**: Resmi web sitesinden uygulamayı indirin
2. **Kurulum**: Setup dosyasını çalıştırın ve kurulum sihirbazını takip edin
3. **İlk Başlatma**: Uygulamayı başlattığınızda otomatik kurulum tamamlanacak

### İlk Yapılandırma

Uygulama ilk kez başlatıldığında:

1. **Varsayılan Admin Hesabı** otomatik oluşturulur:
   - **Kullanıcı Adı**: `admin`
   - **Parola**: `admin123` (hemen değiştirin!)

2. **Güvenlik Uyarısı**: İlk giriş sonrası parolanızı değiştirmeniz zorunludur

3. **Temel Ayarlar**: Server host/port ve diğer temel ayarlar yapılır

---

## 🔐 Giriş ve Kimlik Doğrulama

### Giriş Yapma

1. Uygulama başladığında **Login** penceresi açılır
2. **Kullanıcı adı** ve **parola**nızı girin
3. **Login** butonuna tıklayın

![Login Screen](images/login_screen.png)

### İlk Giriş Sonrası

- Parolanızı hemen değiştirin
- İki faktörlü kimlik doğrulamayı etkinleştirin (önerilir)
- Profil bilgilerinizi güncelleyin

### Güvenlik Özellikleri

- **Otomatik Oturum Kapatma**: 30 dakika hareketsizlik sonrası
- **Çoklu Oturum Koruması**: Aynı anda sadece bir oturum
- **Güvenli Parola Politikası**: Minimum 8 karakter, büyük/küçük harf, rakam

---

## 🏠 Ana Arayüz

### Ana Pencere Düzeni

Ana pencere şu bölümlerden oluşur:

```
┌─────────────────────────────────────────────────────────────┐
│  Menü Çubuğu                                                │
├─────────────────────────────────────────────────────────────┤
│  Araç Çubuğu                    │  Durum Göstergesi         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    Sekme Alanı                              │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐         │
│  │Dash │Serv │User │ API │Moni │Logs │Sett │Abou │         │
│  │board│er   │s    │     │tor  │     │ings │t    │         │
│  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘         │
│                                                             │
│                    İçerik Alanı                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Durum Çubuğu                                               │
└─────────────────────────────────────────────────────────────┘
```

### Menü Çubuğu

- **File**: Yeni, Aç, Kaydet, Çıkış
- **Edit**: Kopyala, Yapıştır, Ayarlar
- **View**: Tema, Dil, Tam Ekran
- **Tools**: Backup, Export, Import
- **Help**: Yardım, Hakkında, Güncellemeler

### Durum Göstergeleri

- 🟢 **Server Online**: API server çalışıyor
- 🔴 **Server Offline**: API server durmuş
- 🟡 **Server Starting**: API server başlatılıyor
- ⚠️ **Uyarılar**: Sistem uyarıları mevcut

---

## 📊 Dashboard Sekmesi

Dashboard, sistemin genel durumunu görmenizi sağlar.

### Ana Metrikler

#### Server Durumu Kartı
```
┌─────────────────────────────────┐
│  🖥️ Server Status               │
├─────────────────────────────────┤
│  Status: 🟢 Online              │
│  URL: http://127.0.0.1:8080     │
│  Uptime: 2h 15m                 │
│  Requests: 1,247                │
└─────────────────────────────────┘
```

#### Kullanıcı İstatistikleri
```
┌─────────────────────────────────┐
│  👥 User Statistics             │
├─────────────────────────────────┤
│  Total Users: 25                │
│  Active Users: 18               │
│  Online Now: 5                  │
│  New Today: 2                   │
└─────────────────────────────────┘
```

#### Sistem Kaynakları
```
┌─────────────────────────────────┐
│  💻 System Resources            │
├─────────────────────────────────┤
│  CPU: [████████░░] 80%          │
│  RAM: [██████░░░░] 60%          │
│  Disk: [███░░░░░░░] 30%         │
│  Network: ↑15MB/s ↓8MB/s        │
└─────────────────────────────────┘
```

### Real-time Grafikler

- **CPU Kullanımı**: Son 1 saatlik CPU yüzdesi
- **Bellek Kullanımı**: RAM kullanım trendi
- **API İstekleri**: Dakikalık istek sayısı
- **Hata Oranı**: Başarısız istek yüzdesi

### Son Aktiviteler

Dashboard'da son sistem aktivitelerini görebilirsiniz:

- 🔐 Kullanıcı giriş/çıkışları
- 🖥️ Server durumu değişiklikleri
- ⚠️ Sistem uyarıları
- 📊 Önemli metrik değişimleri

---

## 🖥️ Server Sekmesi

Server sekmesi, API server'ınızı yönetmenizi sağlar.

### Server Kontrol Paneli

#### Temel Kontroller
```
┌─────────────────────────────────────────┐
│  🎮 Server Controls                     │
├─────────────────────────────────────────┤
│  [🟢 Start]  [🔴 Stop]  [🔄 Restart]   │
│                                         │
│  Status: Online                         │
│  PID: 1234                              │
│  Uptime: 2h 15m 30s                     │
└─────────────────────────────────────────┘
```

#### Server Yapılandırması
```
┌─────────────────────────────────────────┐
│  ⚙️ Server Configuration                │
├─────────────────────────────────────────┤
│  Host: [127.0.0.1          ]            │
│  Port: [8080    ]                       │
│  SSL:  [☐] Enable HTTPS                 │
│  Auto Start: [☑] Start on boot          │
│                                         │
│  [Apply Changes]  [Reset to Default]    │
└─────────────────────────────────────────┘
```

**⚠️ Önemli**: Server ayarları değiştirildiğinde, değişikliklerin etkili olması için server'ın yeniden başlatılması gerekir.

### Canlı Konsol Ekranı

Server sekmesinin alt kısmında **Canlı Konsol** bulunur:

```
┌─────────────────────────────────────────────────────────────┐
│  💻 Live Console                                            │
├─────────────────────────────────────────────────────────────┤
│  2025-01-01 12:00:01 [INFO] Server started on port 8080    │
│  2025-01-01 12:00:15 [INFO] User 'admin' logged in         │
│  2025-01-01 12:01:30 [WARN] Rate limit exceeded for IP ... │
│  2025-01-01 12:02:45 [ERROR] Database connection timeout   │
│                                                             │
│  [Clear Console]  [Export Logs]  [Auto Scroll ☑]          │
└─────────────────────────────────────────────────────────────┘
```

#### Konsol Özellikleri

- **Renk Kodlaması**:
  - 🔵 INFO: Mavi
  - 🟡 WARNING: Sarı
  - 🔴 ERROR: Kırmızı
  - 🟣 DEBUG: Mor

- **Filtreleme**: Log seviyesine göre filtreleme
- **Arama**: Konsol içinde arama yapma
- **Export**: Log'ları dosyaya aktarma
- **Auto Scroll**: Otomatik en alta kaydırma

---

## 👥 Users Sekmesi

Kullanıcı yönetimi sekmesi, sistem kullanıcılarını yönetmenizi sağlar.

### Kullanıcı Listesi

```
┌─────────────────────────────────────────────────────────────┐
│  👥 User Management                                         │
├─────────────────────────────────────────────────────────────┤
│  Search: [admin        ] Status: [All ▼] Role: [All ▼]     │
│                                                             │
│  ┌─────┬──────────┬────────────────┬─────────┬─────────────┐ │
│  │ ID  │ Username │ Email          │ Status  │ Last Login  │ │
│  ├─────┼──────────┼────────────────┼─────────┼─────────────┤ │
│  │ 1   │ admin    │ admin@test.com │ 🟢Active│ 2h ago      │ │
│  │ 2   │ operator │ op@test.com    │ 🟢Active│ 1d ago      │ │
│  │ 3   │ viewer   │ view@test.com  │ 🔴Inactive│ Never     │ │
│  └─────┴──────────┴────────────────┴─────────┴─────────────┘ │
│                                                             │
│  [➕ Add User]  [✏️ Edit]  [🗑️ Delete]  [🔄 Refresh]        │
└─────────────────────────────────────────────────────────────┘
```

### Yeni Kullanıcı Ekleme

**Add User** butonuna tıkladığınızda açılan dialog:

```
┌─────────────────────────────────────────┐
│  ➕ Add New User                        │
├─────────────────────────────────────────┤
│  Basic Information:                     │
│  Username: [newuser    ]                │
│  Email:    [user@example.com]           │
│  Full Name:[John Doe   ]                │
│  Password: [••••••••••]                 │
│  Confirm:  [••••••••••]                 │
│                                         │
│  Roles:                                 │
│  ☐ superadmin - Full system access      │
│  ☐ admin - User and system management   │
│  ☑ operator - Server and monitoring     │
│  ☐ viewer - Read-only access            │
│                                         │
│  Options:                               │
│  ☑ Account is active                    │
│  ☐ Email is verified                    │
│                                         │
│  [Cancel]  [Create User]                │
└─────────────────────────────────────────┘
```

### Kullanıcı Düzenleme

Mevcut kullanıcıya çift tıklayarak veya **Edit** butonuyla düzenleme yapabilirsiniz:

- **Temel Bilgiler**: Ad, email, tam ad
- **Roller**: Kullanıcı rollerini değiştirme
- **Durum**: Aktif/pasif yapma
- **Parola**: Parola sıfırlama
- **Avatar**: Profil resmi yükleme

### Toplu İşlemler

Birden fazla kullanıcı seçerek toplu işlemler yapabilirsiniz:

- **Toplu Aktivasyon**: Seçili kullanıcıları aktif yapma
- **Toplu Deaktivasyon**: Seçili kullanıcıları pasif yapma
- **Rol Atama**: Seçili kullanıcılara rol atama
- **Export**: Seçili kullanıcıları CSV/Excel'e aktarma

---

## 🌐 API Sekmesi

API yönetimi sekmesi, REST API endpoint'lerini kontrol etmenizi sağlar.

### Endpoint Listesi

```
┌─────────────────────────────────────────────────────────────┐
│  🌐 API Endpoint Management                                 │
├─────────────────────────────────────────────────────────────┤
│  Filter: [All ▼] Status: [All ▼] Method: [All ▼]           │
│                                                             │
│  ┌────────┬─────────────────┬────────┬─────────┬───────────┐ │
│  │ Method │ Endpoint        │ Status │ Requests│ Avg Time  │ │
│  ├────────┼─────────────────┼────────┼─────────┼───────────┤ │
│  │ GET    │ /api/v1/users   │ 🟢 On  │ 1,247   │ 45ms      │ │
│  │ POST   │ /api/v1/auth    │ 🟢 On  │ 89      │ 120ms     │ │
│  │ GET    │ /api/v1/server  │ 🔴 Off │ 0       │ -         │ │
│  └────────┴─────────────────┴────────┴─────────┴───────────┘ │
│                                                             │
│  [🔄 Refresh]  [📊 Analytics]  [⚙️ Configure]              │
└─────────────────────────────────────────────────────────────┘
```

### Endpoint Detayları

Bir endpoint'e tıkladığınızda detay bilgiler görüntülenir:

- **İstek İstatistikleri**: Son 24 saatlik istek sayısı
- **Yanıt Süreleri**: Ortalama, minimum, maksimum süreler
- **Hata Oranları**: HTTP status kodlarına göre dağılım
- **Kullanım Trendleri**: Saatlik/günlük kullanım grafikleri

### API Güvenlik Ayarları

```
┌─────────────────────────────────────────┐
│  🔒 Security Settings                   │
├─────────────────────────────────────────┤
│  Rate Limiting:                         │
│  ☑ Enable rate limiting                 │
│  Max requests: [100] per minute         │
│                                         │
│  Authentication:                        │
│  ☑ Require authentication               │
│  ☐ Allow anonymous access               │
│                                         │
│  IP Restrictions:                       │
│  Whitelist: [192.168.1.0/24]           │
│  Blacklist: [                 ]         │
│                                         │
│  [Save Changes]                         │
└─────────────────────────────────────────┘
```

---

## 📈 Monitor Sekmesi

Sistem izleme sekmesi, real-time performans verilerini görüntüler.

### Sistem Metrikleri

```
┌─────────────────────────────────────────────────────────────┐
│  📊 System Monitoring                                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┬──────────────────┬──────────────────┐ │
│  │   CPU Usage      │   Memory Usage   │   Disk Usage     │ │
│  │                  │                  │                  │ │
│  │      75%         │      60%         │      30%         │ │
│  │  ████████░░      │  ██████░░░░      │  ███░░░░░░░      │ │
│  │                  │                  │                  │ │
│  │  8 cores         │  16GB total      │  1TB total       │ │
│  │  6 active        │  9.6GB used      │  300GB used      │ │
│  └──────────────────┴──────────────────┴──────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  📈 Performance Graphs                                  │ │
│  │                                                         │ │
│  │  CPU %  ┌─────────────────────────────────────────────┐ │ │
│  │  100 ─  │                                    ▲        │ │ │
│  │   75 ─  │              ▲        ▲          ▲▲▲        │ │ │
│  │   50 ─  │        ▲   ▲▲▲▲  ▲  ▲▲▲▲      ▲▲▲▲▲        │ │ │
│  │   25 ─  │  ▲  ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲        │ │ │
│  │    0 ─  │▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲        │ │ │
│  │         └─────────────────────────────────────────────┘ │ │
│  │           12:00  12:15  12:30  12:45  13:00            │ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Network Trafiği

```
┌─────────────────────────────────────────┐
│  🌐 Network Traffic                     │
├─────────────────────────────────────────┤
│  Download: ↓ 15.2 MB/s                  │
│  Upload:   ↑ 8.7 MB/s                   │
│                                         │
│  Total today:                           │
│  Downloaded: 2.1 GB                     │
│  Uploaded:   850 MB                     │
│                                         │
│  Active Connections: 127                │
│  Listening Ports: 3                     │
└─────────────────────────────────────────┘
```

### Process Monitor

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 Process Monitor                                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────┬──────────────────┬─────────┬─────────┬───────────┐ │
│  │ PID │ Process Name     │ CPU %   │ Memory  │ Status    │ │
│  ├─────┼──────────────────┼─────────┼─────────┼───────────┤ │
│  │1234 │ api_server.exe   │ 15.2%   │ 45 MB   │ Running   │ │
│  │5678 │ database.exe     │ 8.7%    │ 128 MB  │ Running   │ │
│  │9012 │ monitor.exe      │ 2.1%    │ 12 MB   │ Running   │ │
│  └─────┴──────────────────┴─────────┴─────────┴───────────┘ │
│                                                             │
│  [🔄 Refresh]  [⏹️ Kill Process]  [📊 Details]             │
└─────────────────────────────────────────────────────────────┘
```

### Alert Sistemi

Monitor sekmesinde sistem uyarılarını da görebilirsiniz:

- **🔴 Critical**: CPU %90 üzerinde
- **🟡 Warning**: Bellek %80 üzerinde
- **🔵 Info**: Disk %70 üzerinde
- **🟢 OK**: Tüm sistem normal

---

## 📝 Logs Sekmesi

Log yönetimi sekmesi, sistem log'larını görüntülemenizi ve analiz etmenizi sağlar.

### Log Görüntüleyici

```
┌─────────────────────────────────────────────────────────────┐
│  📝 Log Viewer                                              │
├─────────────────────────────────────────────────────────────┤
│  Filters:                                                   │
│  Level: [All ▼] Module: [All ▼] Date: [Today ▼]            │
│  Search: [                    ] [🔍]                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Time     │Level│Module    │Message                      │ │
│  ├──────────┼─────┼──────────┼─────────────────────────────┤ │
│  │12:00:01  │INFO │server    │Server started successfully  │ │
│  │12:00:15  │WARN │auth      │Failed login: admin          │ │
│  │12:01:30  │ERROR│database  │Connection timeout           │ │
│  │12:02:45  │DEBUG│api       │Processing request /users    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  [📥 Export] [🗑️ Clear] [⚙️ Settings] [🔄 Auto-refresh ☑]  │
└─────────────────────────────────────────────────────────────┘
```

### Log Seviyeleri

- **🔴 ERROR**: Sistem hataları
- **🟡 WARNING**: Uyarılar
- **🔵 INFO**: Bilgi mesajları
- **🟣 DEBUG**: Hata ayıklama mesajları
- **🔴 CRITICAL**: Kritik sistem hataları

### Log Analizi

```
┌─────────────────────────────────────────┐
│  📊 Log Analysis                        │
├─────────────────────────────────────────┤
│  Last 24 hours:                         │
│  Total logs: 15,247                     │
│  Errors: 23 (0.15%)                     │
│  Warnings: 156 (1.02%)                  │
│  Info: 14,890 (97.66%)                  │
│  Debug: 178 (1.17%)                     │
│                                         │
│  Top Error Sources:                     │
│  1. database (12 errors)                │
│  2. auth (8 errors)                     │
│  3. api (3 errors)                      │
│                                         │
│  [📈 Detailed Report]                   │
└─────────────────────────────────────────┘
```

### Log Export

Log'ları farklı formatlarda export edebilirsiniz:

- **JSON**: Programatik analiz için
- **CSV**: Excel'de analiz için
- **TXT**: Basit metin formatı
- **PDF**: Raporlama için

---

## ⚙️ Settings Sekmesi

Sistem ayarları sekmesi, uygulamanın tüm yapılandırma seçeneklerini içerir.

### Genel Ayarlar

```
┌─────────────────────────────────────────────────────────────┐
│  ⚙️ General Settings                                        │
├─────────────────────────────────────────────────────────────┤
│  Application:                                               │
│  Language: [English ▼]                                      │
│  Theme: [Dark ▼]                                            │
│  Auto-start: ☑ Start with system                           │
│  Updates: ☑ Check for updates automatically                 │
│                                                             │
│  UI Preferences:                                            │
│  Window size: [1200x800]                                    │
│  Font size: [12pt]                                          │
│  Show tooltips: ☑                                           │
│  Animation: ☑ Enable UI animations                          │
│                                                             │
│  [Save Changes] [Reset to Default]                          │
└─────────────────────────────────────────────────────────────┘
```

### Server Ayarları

```
┌─────────────────────────────────────────┐
│  🖥️ Server Settings                     │
├─────────────────────────────────────────┤
│  Network:                               │
│  Host: [127.0.0.1     ]                 │
│  Port: [8080    ]                       │
│  SSL: ☐ Enable HTTPS                    │
│                                         │
│  SSL Configuration:                     │
│  Certificate: [Browse...]               │
│  Private Key: [Browse...]               │
│                                         │
│  Performance:                           │
│  Max connections: [1000]                │
│  Request timeout: [30] seconds          │
│  Keep-alive: ☑ Enable                   │
│                                         │
│  [Test Connection] [Apply]              │
└─────────────────────────────────────────┘
```

### Güvenlik Ayarları

```
┌─────────────────────────────────────────┐
│  🔒 Security Settings                   │
├─────────────────────────────────────────┤
│  Authentication:                        │
│  Session timeout: [30] minutes          │
│  Max login attempts: [5]                │
│  Lockout duration: [15] minutes         │
│                                         │
│  Password Policy:                       │
│  Minimum length: [8] characters         │
│  ☑ Require uppercase letters            │
│  ☑ Require lowercase letters            │
│  ☑ Require numbers                      │
│  ☑ Require special characters           │
│                                         │
│  Two-Factor Authentication:             │
│  ☐ Enable 2FA for all users             │
│  ☑ Allow users to enable 2FA            │
│                                         │
│  [Save Security Settings]               │
└─────────────────────────────────────────┘
```

### Database Ayarları

```
┌─────────────────────────────────────────┐
│  🗄️ Database Settings                   │
├─────────────────────────────────────────┤
│  Database File:                         │
│  Path: [data/app.db] [Browse...]        │
│  Size: 15.2 MB                          │
│  Tables: 12                             │
│                                         │
│  Backup Settings:                       │
│  ☑ Enable automatic backups             │
│  Frequency: [Daily ▼]                   │
│  Keep backups: [7] days                 │
│  Backup location: [data/backup/]        │
│                                         │
│  Maintenance:                           │
│  [🗜️ Compress Database]                 │
│  [🧹 Clean Old Logs]                    │
│  [📊 Analyze Performance]               │
│                                         │
│  [💾 Backup Now] [🔄 Restore]           │
└─────────────────────────────────────────┘
```

### Bildirim Ayarları

```
┌─────────────────────────────────────────┐
│  🔔 Notification Settings               │
├─────────────────────────────────────────┤
│  Desktop Notifications:                 │
│  ☑ Show system notifications            │
│  ☑ Show error notifications             │
│  ☐ Show info notifications              │
│                                         │
│  Email Notifications:                   │
│  ☑ Enable email alerts                  │
│  SMTP Server: [smtp.gmail.com]          │
│  Port: [587]                            │
│  Username: [admin@company.com]          │
│  Password: [••••••••••]                 │
│                                         │
│  Alert Conditions:                      │
│  ☑ Server down                          │
│  ☑ High CPU usage (>90%)                │
│  ☑ High memory usage (>90%)             │
│  ☑ Disk space low (<10%)                │
│  ☑ Failed login attempts (>5)           │
│                                         │
│  [Test Email] [Save Settings]           │
└─────────────────────────────────────────┘
```

---

## ℹ️ About Sekmesi

Hakkında sekmesi, uygulama bilgilerini ve sistem detaylarını gösterir.

### Uygulama Bilgileri

```
┌─────────────────────────────────────────────────────────────┐
│  ℹ️ Application Information                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│      🖥️ API Server Management System                       │
│                                                             │
│  Version: 1.0.0                                             │
│  Build: 20250101-1200                                       │
│  Release Date: January 1, 2025                              │
│                                                             │
│  Developer: Your Company Name                               │
│  Website: https://www.yourcompany.com                       │
│  Support: support@yourcompany.com                           │
│                                                             │
│  License: Commercial License                                │
│  Licensed to: Your Organization                             │
│  Expires: December 31, 2025                                 │
│                                                             │
│  [📋 Copy Info] [🌐 Visit Website] [📧 Contact Support]    │
└─────────────────────────────────────────────────────────────┘
```

### Sistem Bilgileri

```
┌─────────────────────────────────────────┐
│  💻 System Information                  │
├─────────────────────────────────────────┤
│  Operating System:                      │
│  Windows 11 Pro (Build 22000.1)        │
│                                         │
│  Hardware:                              │
│  CPU: Intel Core i7-10700K @ 3.8GHz    │
│  RAM: 32 GB DDR4                        │
│  Disk: 1TB NVMe SSD                     │
│                                         │
│  Python Environment:                    │
│  Python: 3.11.5                        │
│  PyQt5: 5.15.9                         │
│  aiohttp: 3.8.5                        │
│  peewee: 3.16.2                         │
│                                         │
│  Network:                               │
│  IP Address: 192.168.1.100              │
│  Hostname: DESKTOP-ABC123               │
│  Domain: WORKGROUP                      │
└─────────────────────────────────────────┘
```

### Güncellemeler

```
┌─────────────────────────────────────────┐
│  🔄 Updates                             │
├─────────────────────────────────────────┤
│  Current Version: 1.0.0                 │
│  Latest Version: 1.0.1                  │
│                                         │
│  🆕 Update Available!                   │
│                                         │
│  Version 1.0.1 (Released: Jan 15, 2025)│
│  • Bug fixes and improvements           │
│  • New monitoring features              │
│  • Enhanced security                    │
│  • Performance optimizations            │
│                                         │
│  [📥 Download Update] [📋 Release Notes]│
│                                         │
│  ☑ Automatically check for updates      │
│  ☐ Install updates automatically        │
└─────────────────────────────────────────┘
```

---

## 🔧 Gelişmiş Özellikler

### Tema Özelleştirme

Uygulamada 4 farklı tema mevcuttur:

1. **Dark Theme** (Varsayılan): Koyu renkli, göz dostu
2. **Light Theme**: Açık renkli, klasik görünüm
3. **Blue Theme**: Mavi tonlarda profesyonel
4. **Custom Theme**: Kendi renk şemanızı oluşturun

#### Özel Tema Oluşturma

1. **Settings > Appearance > Custom Theme**
2. Renk paletini özelleştirin
3. **Preview** ile önizleme yapın
4. **Apply** ile uygulayın

### Dil Desteği

Uygulama 4 dilde kullanılabilir:

- 🇺🇸 **English** (İngilizce)
- 🇹🇷 **Türkçe** (Turkish)
- 🇩🇪 **Deutsch** (Almanca)
- 🇫🇷 **Français** (Fransızca)

Dil değiştirmek için: **Settings > General > Language**

### Keyboard Shortcuts

| Kısayol | İşlev |
|---------|-------|
| `Ctrl+N` | Yeni kullanıcı ekle |
| `Ctrl+S` | Ayarları kaydet |
| `Ctrl+R` | Sayfayı yenile |
| `F5` | Dashboard'u yenile |
| `F11` | Tam ekran |
| `Ctrl+Q` | Uygulamayı kapat |
| `Ctrl+,` | Ayarları aç |
| `Ctrl+Shift+L` | Log'ları temizle |

### Backup ve Restore

#### Otomatik Backup

- **Günlük**: Her gece 02:00'da
- **Haftalık**: Her Pazar 03:00'da
- **Aylık**: Her ayın ilk günü 04:00'da

#### Manuel Backup

1. **Settings > Database > Backup Now**
2. Backup konumunu seçin
3. **Create Backup** tıklayın

#### Restore İşlemi

1. **Settings > Database > Restore**
2. Backup dosyasını seçin
3. **Restore** onayını verin
4. Uygulama otomatik yeniden başlar

### Import/Export

#### Kullanıcı Listesi Export

1. **Users sekmesi > Export**
2. Format seçin (CSV, Excel, JSON)
3. Kayıt konumunu belirleyin

#### Ayarları Export/Import

1. **Settings > Advanced > Export Settings**
2. Ayar dosyasını kaydedin
3. Başka sistemde **Import Settings** ile yükleyin

---

## 🚨 Sorun Giderme

### Sık Karşılaşılan Sorunlar

#### Server Başlamıyor

**Belirtiler**: Server status "Offline" görünüyor

**Çözümler**:
1. Port çakışması kontrol edin
2. Firewall ayarlarını kontrol edin
3. Administrator yetkisiyle çalıştırın
4. Log'larda hata mesajlarını kontrol edin

#### Kullanıcı Giriş Yapamıyor

**Belirtiler**: "Invalid credentials" hatası

**Çözümler**:
1. Kullanıcı adı/parola doğruluğunu kontrol edin
2. Hesap aktif mi kontrol edin
3. Hesap kilitli mi kontrol edin
4. Database bağlantısını kontrol edin

#### UI Donuyor

**Belirtiler**: Arayüz yanıt vermiyor

**Çözümler**:
1. Uygulamayı yeniden başlatın
2. System resources kontrol edin
3. Debug mode'da çalıştırın
4. Log'larda hata mesajlarını kontrol edin

#### Database Hatası

**Belirtiler**: "Database connection failed"

**Çözümler**:
1. Database dosyası var mı kontrol edin
2. Dosya izinlerini kontrol edin
3. Disk alanını kontrol edin
4. Backup'tan restore edin

### Debug Mode

Sorun giderme için debug mode'u etkinleştirin:

1. **Settings > Advanced > Debug Mode**
2. Uygulamayı yeniden başlatın
3. Detaylı log'ları inceleyin

### Log Analizi

Sorun teşhisi için log dosyalarını inceleyin:

- **app.log**: Genel uygulama log'ları
- **api.log**: API istekleri ve yanıtları
- **error.log**: Hata mesajları
- **security.log**: Güvenlik olayları

### Performans Sorunları

#### Yavaş Çalışma

**Belirtiler**: Arayüz yavaş, gecikmeler

**Çözümler**:
1. RAM kullanımını kontrol edin
2. CPU kullanımını kontrol edin
3. Database'i optimize edin
4. Log dosyalarını temizleyin

#### Yüksek CPU Kullanımı

**Belirtiler**: CPU %100'e yakın

**Çözümler**:
1. Gereksiz process'leri kapatın
2. Monitoring frequency'sini azaltın
3. Log level'ını INFO'ya çevirin
4. Background task'ları optimize edin

---

## 🔒 Güvenlik Best Practices

### Parola Güvenliği

- **Güçlü Parolalar**: En az 12 karakter, karışık karakterler
- **Düzenli Değiştirme**: 90 günde bir parola değiştirin
- **Benzersiz Parolalar**: Her sistem için farklı parola
- **2FA Kullanımı**: İki faktörlü kimlik doğrulamayı etkinleştirin

### Kullanıcı Yönetimi

- **Minimum Yetki**: Sadece gerekli yetkileri verin
- **Düzenli İnceleme**: Kullanıcı yetkilerini periyodik kontrol edin
- **Deaktif Hesaplar**: Kullanılmayan hesapları deaktive edin
- **Guest Hesaplar**: Misafir hesapları sınırlı süreli yapın

### Sistem Güvenliği

- **Güncel Tutun**: Uygulamayı ve sistem güncel tutun
- **Firewall**: Ağ erişimini sınırlayın
- **Backup**: Düzenli backup alın
- **Monitoring**: Güvenlik log'larını takip edin

### Network Güvenliği

- **HTTPS**: SSL/TLS şifrelemesi kullanın
- **VPN**: Uzaktan erişim için VPN kullanın
- **IP Kısıtlaması**: Sadece güvenli IP'lere izin verin
- **Rate Limiting**: Brute force saldırılarını önleyin

---

## 📞 Destek ve Yardım

### Teknik Destek

- **Email**: support@yourcompany.com
- **Telefon**: +90 XXX XXX XX XX
- **Çalışma Saatleri**: 09:00-18:00 (Hafta içi)
- **Acil Destek**: 7/24 kritik sorunlar için

### Online Kaynaklar

- **Dokümantasyon**: https://docs.yourcompany.com
- **Video Eğitimler**: https://training.yourcompany.com
- **Forum**: https://community.yourcompany.com
- **FAQ**: https://faq.yourcompany.com

### Eğitim ve Sertifikasyon

- **Temel Kullanım Eğitimi**: 4 saatlik online eğitim
- **İleri Seviye Yönetim**: 8 saatlik uzman eğitimi
- **Sertifikasyon Programı**: Uzman sertifikası
- **Özel Eğitimler**: Kurumsal eğitim paketleri

### Geri Bildirim

Görüşlerinizi bizimle paylaşın:

- **Özellik İstekleri**: features@yourcompany.com
- **Bug Raporları**: bugs@yourcompany.com
- **Genel Geri Bildirim**: feedback@yourcompany.com

---

## 📋 Sık Sorulan Sorular (FAQ)

### Genel Sorular

**S: Uygulama ücretsiz mi?**
C: Uygulama ticari bir üründür. 30 günlük deneme sürümü mevcuttur.

**S: Kaç kullanıcı destekleniyor?**
C: Lisansa göre değişir. Standart lisans 50 kullanıcı destekler.

**S: Mobil uygulaması var mı?**
C: Şu anda sadece desktop versiyonu mevcuttur. Mobil uygulama geliştirilmektedir.

### Teknik Sorular

**S: Hangi veritabanları destekleniyor?**
C: SQLite (varsayılan), PostgreSQL, MySQL desteklenmektedir.

**S: API'yi nasıl entegre edebilirim?**
C: REST API dokümantasyonunu inceleyerek entegrasyon yapabilirsiniz.

**S: Backup dosyaları şifreli mi?**
C: Evet, tüm backup dosyaları AES-256 ile şifrelenmektedir.

### Lisans Sorularý

**S: Lisansım ne zaman bitiyor?**
C: About sekmesinde lisans bitiş tarihini görebilirsiniz.

**S: Lisansı nasıl yenileyebilirim?**
C: Satış ekibimizle iletişime geçerek yenileme yapabilirsiniz.

**S: Offline kullanılabiliyor mu?**
C: Evet, lisans doğrulaması sonrası offline kullanım mümkündür.

---

Bu kullanıcı kılavuzu, API Server Management System'i etkili bir şekilde kullanmanız için gereken tüm bilgileri içermektedir. Daha detaylı bilgi için online dokümantasyonumuzu ziyaret edebilir veya destek ekibimizle iletişime geçebilirsiniz.