"""
Routes module - API endpoint'leri

Bu modül API route'larını içerir:
- Base routes
- Auth routes
- User routes
- Admin routes
- Config routes
- Server routes
- Monitor routes
- Log routes
- File routes
"""

from .base_routes import BaseRoutes
from .auth_routes import AuthRoutes
from .user_routes import UserRoutes
from .admin_routes import AdminRoutes
from .config_routes import ConfigRoutes
from .server_routes import ServerRoutes
from .monitor_routes import MonitorRoutes
from .log_routes import LogRoutes
from .file_routes import FileRoutes
from .websocket_routes import WebSocketRoutes
from .role_routes import RoleRoutes
from .backup_routes import BackupRoutes

__all__ = [
    "BaseRoutes",
    "AuthRoutes",
    "UserRoutes",
    "AdminRoutes",
    "ConfigRoutes",
    "ServerRoutes",
    "MonitorRoutes",
    "LogRoutes",
    "FileRoutes",
    "WebSocketRoutes",
    "RoleRoutes",
    "BackupRoutes"
]

# Route setup fonksiyonu
def setup_routes(app):
    """Tüm route'ları uygulamaya ekle"""
    from aiohttp import web
    
    # Base routes
    base_routes = BaseRoutes()
    app.router.add_routes(base_routes.get_routes())
    
    # Auth routes
    auth_routes = AuthRoutes()
    app.router.add_routes(auth_routes.get_routes())
    
    # User routes
    user_routes = UserRoutes()
    app.router.add_routes(user_routes.get_routes())
    
    # Admin routes
    admin_routes = AdminRoutes()
    app.router.add_routes(admin_routes.get_routes())
    
    # Config routes
    config_routes = ConfigRoutes()
    app.router.add_routes(config_routes.get_routes())
    
    # Server routes
    server_routes = ServerRoutes()
    app.router.add_routes(server_routes.get_routes())
    
    # Monitor routes
    monitor_routes = MonitorRoutes()
    app.router.add_routes(monitor_routes.get_routes())
    
    # Log routes
    log_routes = LogRoutes()
    app.router.add_routes(log_routes.get_routes())
    
    # File routes
    file_routes = FileRoutes()
    app.router.add_routes(file_routes.get_routes())
    
    # WebSocket routes
    websocket_routes = WebSocketRoutes()
    app.router.add_routes(websocket_routes.get_routes())
    
    # Role routes
    role_routes = RoleRoutes()
    app.router.add_routes(role_routes.get_routes())
    
    # Backup routes
    backup_routes = BackupRoutes()
    app.router.add_routes(backup_routes.get_routes())
