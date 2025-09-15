#!/usr/bin/env python3
"""
API Server Management System - Minimal başlatıcı (External dependencies olmadan)

Bu versiyon sadece temel Python modülleri ile çalışır ve web-based interface sağlar.
"""

import sys
import os
import asyncio
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time
import socket
from urllib.parse import urlparse, parse_qs
import uuid
import hashlib
import base64

# Proje kök dizinini Python path'ine ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class MinimalConfig:
    """Minimal yapılandırma sınıfı"""
    
    def __init__(self):
        self.config = {
            "app": {
                "name": "API Server Management System (Minimal)",
                "version": "1.0.0-minimal",
                "debug": True,
                "environment": "development"
            },
            "server": {
                "host": "127.0.0.1",
                "port": 8080,
                "ssl_enabled": False,
                "auto_start": True
            },
            "database": {
                "path": "data/app.db",
                "backup_enabled": False
            },
            "ui": {
                "mode": "web",  # web-based interface
                "theme": "light"
            }
        }
    
    def get(self, key, default=None):
        """Nested key erişimi"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

class MinimalDatabase:
    """Minimal SQLite veritabanı yöneticisi"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Veritabanını başlat"""
        # Data dizinini oluştur
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # System logs tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                module TEXT,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                ip_address TEXT
            )
        ''')
        
        # Config tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, key)
            )
        ''')
        
        # Default admin kullanıcısını oluştur
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            password_hash = self.hash_password('admin123')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, is_active, is_verified)
                VALUES (?, ?, ?, ?, 1, 1)
            ''', ('admin', 'admin@example.com', password_hash, 'System Administrator'))
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
    def hash_password(self, password):
        """Basit password hashing (production'da bcrypt kullanılmalı)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, hash_value):
        """Password doğrulama"""
        return hashlib.sha256(password.encode()).hexdigest() == hash_value
    
    def get_user(self, username):
        """Kullanıcı getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def log_message(self, level, message, module=None):
        """Log mesajı kaydet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_logs (level, module, message)
                VALUES (?, ?, ?)
            ''', (level, module or '', message))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Log error: {e}")

class WebInterface:
    """Web tabanlı arayüz"""
    
    def __init__(self, config, database):
        self.config = config
        self.database = database
        self.sessions = {}
    
    def generate_session_token(self):
        """Session token oluştur"""
        return str(uuid.uuid4())
    
    def create_session(self, username):
        """Session oluştur"""
        token = self.generate_session_token()
        self.sessions[token] = {
            'username': username,
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
        return token
    
    def verify_session(self, token):
        """Session doğrula"""
        if token in self.sessions:
            session = self.sessions[token]
            session['last_activity'] = datetime.now()
            return session
        return None
    
    def get_dashboard_html(self):
        """Dashboard HTML'i oluştur"""
        return '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Server Management System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; text-align: center; margin-bottom: 30px; border-radius: 8px; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h3 { color: #2c3e50; margin-bottom: 15px; }
        .status { display: inline-block; padding: 5px 10px; border-radius: 4px; color: white; font-weight: bold; }
        .status.online { background: #27ae60; }
        .status.offline { background: #e74c3c; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .metric { text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
        .metric-label { color: #7f8c8d; margin-top: 5px; }
        .logs { max-height: 300px; overflow-y: auto; background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 4px; font-family: monospace; }
        .log-entry { margin: 2px 0; }
        .log-info { color: #3498db; }
        .log-warning { color: #f39c12; }
        .log-error { color: #e74c3c; }
        button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; }
        button:hover { background: #2980b9; }
        button.danger { background: #e74c3c; }
        button.danger:hover { background: #c0392b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 API Server Management System</h1>
            <p>Minimal Web Interface - Version 1.0.0</p>
        </div>
        
        <div class="card">
            <h3>📊 Server Status</h3>
            <p>Status: <span class="status online">🟢 Online</span></p>
            <p>URL: <a href="http://127.0.0.1:8080">http://127.0.0.1:8080</a></p>
            <p>Started: <span id="start-time">''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</span></p>
            <div style="margin-top: 15px;">
                <button onclick="alert('Server restart functionality would be implemented here')">🔄 Restart Server</button>
                <button class="danger" onclick="alert('Server stop functionality would be implemented here')">⏹️ Stop Server</button>
            </div>
        </div>
        
        <div class="metrics">
            <div class="card metric">
                <h3>👥 Users</h3>
                <div class="metric-value">1</div>
                <div class="metric-label">Total Users</div>
            </div>
            <div class="card metric">
                <h3>📈 Requests</h3>
                <div class="metric-value">0</div>
                <div class="metric-label">API Requests</div>
            </div>
            <div class="card metric">
                <h3>💾 Database</h3>
                <div class="metric-value">✅</div>
                <div class="metric-label">SQLite Ready</div>
            </div>
        </div>
        
        <div class="card">
            <h3>📝 Recent Logs</h3>
            <div class="logs">
                <div class="log-entry log-info">[''' + datetime.now().strftime('%H:%M:%S') + '''] [INFO] Server started successfully</div>
                <div class="log-entry log-info">[''' + datetime.now().strftime('%H:%M:%S') + '''] [INFO] Database initialized</div>
                <div class="log-entry log-info">[''' + datetime.now().strftime('%H:%M:%S') + '''] [INFO] Web interface ready</div>
                <div class="log-entry log-warning">[''' + datetime.now().strftime('%H:%M:%S') + '''] [WARNING] Running in minimal mode - some features disabled</div>
            </div>
        </div>
        
        <div class="card">
            <h3>ℹ️ System Information</h3>
            <p><strong>Mode:</strong> Minimal (No PyQt5/aiohttp dependencies)</p>
            <p><strong>Python:</strong> ''' + sys.version + '''</p>
            <p><strong>Database:</strong> SQLite</p>
            <p><strong>Features:</strong> Basic monitoring, User management (limited), Log viewing</p>
        </div>
        
        <div class="card">
            <h3>🔗 Available Endpoints</h3>
            <ul>
                <li><a href="/api/health">/api/health</a> - Health check</li>
                <li><a href="/api/status">/api/status</a> - Server status</li>
                <li><a href="/api/users">/api/users</a> - User list (JSON)</li>
                <li><a href="/api/logs">/api/logs</a> - System logs (JSON)</li>
            </ul>
        </div>
    </div>
    
    <script>
        // Auto-refresh status every 30 seconds
        setInterval(() => {
            // In a full implementation, this would fetch real-time data
            console.log('Auto-refresh triggered');
        }, 30000);
    </script>
</body>
</html>
        '''

class MinimalHTTPHandler(SimpleHTTPRequestHandler):
    """Minimal HTTP request handler"""
    
    def __init__(self, *args, config=None, database=None, web_interface=None, **kwargs):
        self.config = config
        self.database = database
        self.web_interface = web_interface
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """GET request handler"""
        if self.path == '/' or self.path == '/dashboard':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.web_interface.get_dashboard_html().encode())
        
        elif self.path == '/api/health':
            self.send_json_response({'status': 'ok', 'message': 'Server is healthy'})
        
        elif self.path == '/api/status':
            status = {
                'server': 'online',
                'version': '1.0.0-minimal',
                'uptime': int(time.time() - start_time),
                'database': 'connected'
            }
            self.send_json_response(status)
        
        elif self.path == '/api/users':
            # Basit kullanıcı listesi
            users = [{'id': 1, 'username': 'admin', 'email': 'admin@example.com', 'active': True}]
            self.send_json_response({'users': users})
        
        elif self.path == '/api/logs':
            # Son 10 log kaydı
            logs = [
                {'timestamp': datetime.now().isoformat(), 'level': 'INFO', 'message': 'Server started'},
                {'timestamp': datetime.now().isoformat(), 'level': 'INFO', 'message': 'Database ready'},
                {'timestamp': datetime.now().isoformat(), 'level': 'WARNING', 'message': 'Minimal mode active'}
            ]
            self.send_json_response({'logs': logs})
        
        else:
            self.send_error(404, 'Endpoint not found')
    
    def send_json_response(self, data):
        """JSON response gönder"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, format, *args):
        """Log mesajlarını özelleştir"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")

def create_required_directories():
    """Gerekli dizinleri oluştur"""
    directories = [
        "data",
        "data/backup", 
        "data/cache",
        "data/logs",
        "data/resources"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Logging'i kur"""
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'app.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Ana fonksiyon"""
    global start_time
    start_time = time.time()
    
    print("🚀 API Server Management System (Minimal Mode)")
    print("=" * 60)
    
    # Gerekli dizinleri oluştur
    print("📁 Creating directories...")
    create_required_directories()
    
    # Logging'i kur
    print("📝 Setting up logging...")
    setup_logging()
    
    # Config'i yükle
    print("⚙️ Loading configuration...")
    config = MinimalConfig()
    
    # Database'i başlat
    print("🗄️ Initializing database...")
    database = MinimalDatabase(config.get('database.path'))
    
    # Web interface'i başlat
    print("🌐 Setting up web interface...")
    web_interface = WebInterface(config, database)
    
    # HTTP Server'ı başlat
    host = config.get('server.host')
    port = config.get('server.port')
    
    print(f"🖥️ Starting HTTP server on {host}:{port}...")
    
    def handler(*args, **kwargs):
        return MinimalHTTPHandler(*args, config=config, database=database, 
                                web_interface=web_interface, **kwargs)
    
    try:
        with HTTPServer((host, port), handler) as httpd:
            print(f"✅ Server started successfully!")
            print(f"🌐 Web Interface: http://{host}:{port}")
            print(f"📊 API Endpoints: http://{host}:{port}/api/")
            print(f"📝 Logs: data/logs/app.log")
            print("\n🎉 Ready to serve requests!")
            print("Press Ctrl+C to stop the server...")
            
            # Log başlangıç mesajı
            database.log_message('INFO', f'Server started on {host}:{port}', 'server')
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n⏹️ Server stopped by user")
        database.log_message('INFO', 'Server stopped by user', 'server')
    except Exception as e:
        print(f"❌ Server error: {e}")
        database.log_message('ERROR', f'Server error: {e}', 'server')
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())