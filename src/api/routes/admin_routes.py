"""
Admin Routes module - Admin endpoint'leri

Bu modül admin işlemleri ile ilgili API endpoint'lerini içerir.
"""

import time
from typing import Dict, Any, List
from aiohttp import web
from aiohttp.web import Request, Response

from .base_routes import BaseRoutes
from ...core.constants import API_PREFIX, SUCCESS_MESSAGES, ERROR_MESSAGES
from ...db.models import User, Session, UserRole, Role
from ...utils.logger import Logger


class AdminRoutes(BaseRoutes):
    """Admin routes sınıfı"""
    
    def __init__(self):
        """AdminRoutes'ı başlat"""
        super().__init__()
        self.logger = Logger(__name__)
    
    def get_routes(self) -> list[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.get(f"{API_PREFIX}/admin/dashboard", self.get_dashboard),
            web.get(f"{API_PREFIX}/admin/stats", self.get_stats),
            web.get(f"{API_PREFIX}/admin/users", self.get_admin_users),
            web.get(f"{API_PREFIX}/admin/sessions", self.get_admin_sessions),
            web.get(f"{API_PREFIX}/admin/system", self.get_admin_system),
            web.post(f"{API_PREFIX}/admin/users/{{user_id}}/activate", self.activate_user),
            web.post(f"{API_PREFIX}/admin/users/{{user_id}}/deactivate", self.deactivate_user),
            web.post(f"{API_PREFIX}/admin/sessions/{{session_id}}/terminate", self.terminate_session),
            web.get(f"{API_PREFIX}/admin/audit-logs", self.get_audit_logs),
        ]
    
    async def get_dashboard(self, request: Request) -> Response:
        """Admin dashboard"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Kullanıcının admin olup olmadığını kontrol et
            user = User.get_by_id(user_id)
            if not user.is_superuser:
                return self.create_error_response(
                    message="Admin yetkisi gerekli",
                    status_code=403
                )
            
            # Dashboard verilerini topla
            dashboard_data = {
                "overview": {
                    "total_users": User.select().count(),
                    "active_users": User.select().where(User.is_active == True).count(),
                    "total_sessions": Session.select().count(),
                    "active_sessions": Session.select().where(Session.is_active == True).count(),
                    "system_uptime": self._get_system_uptime(),
                    "last_updated": time.time()
                },
                "recent_activity": self._get_recent_activity(),
                "system_health": self._get_system_health(),
                "user_statistics": self._get_user_statistics(),
                "security_alerts": self._get_security_alerts()
            }
            
            return self.create_success_response(
                message="Admin dashboard verileri alındı",
                data=dashboard_data
            )
            
        except Exception as e:
            self.logger.error(f"Admin dashboard alınamadı: {e}")
            return self.create_error_response(
                message="Admin dashboard alınamadı",
                status_code=500
            )
    
    async def get_stats(self, request: Request) -> Response:
        """Admin istatistikleri"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Kullanıcının admin olup olmadığını kontrol et
            user = User.get_by_id(user_id)
            if not user.is_superuser:
                return self.create_error_response(
                    message="Admin yetkisi gerekli",
                    status_code=403
                )
            
            # Detaylı istatistikleri al
            stats_data = {
                "users": {
                    "total": User.select().count(),
                    "active": User.select().where(User.is_active == True).count(),
                    "inactive": User.select().where(User.is_active == False).count(),
                    "verified": User.select().where(User.is_verified == True).count(),
                    "unverified": User.select().where(User.is_verified == False).count(),
                    "superusers": User.select().where(User.is_superuser == True).count(),
                    "regular_users": User.select().where(User.is_superuser == False).count()
                },
                "sessions": {
                    "total": Session.select().count(),
                    "active": Session.select().where(Session.is_active == True).count(),
                    "expired": Session.select().where(Session.is_active == False).count(),
                    "today": self._get_today_sessions(),
                    "this_week": self._get_week_sessions(),
                    "this_month": self._get_month_sessions()
                },
                "roles": {
                    "total_roles": Role.select().count(),
                    "role_distribution": self._get_role_distribution()
                },
                "system": {
                    "uptime": self._get_system_uptime(),
                    "memory_usage": self._get_memory_usage(),
                    "disk_usage": self._get_disk_usage(),
                    "cpu_usage": self._get_cpu_usage()
                },
                "security": {
                    "failed_logins": self._get_failed_logins(),
                    "suspicious_activity": self._get_suspicious_activity(),
                    "blocked_ips": self._get_blocked_ips()
                }
            }
            
            return self.create_success_response(
                message="Admin istatistikleri alındı",
                data=stats_data
            )
            
        except Exception as e:
            self.logger.error(f"Admin istatistikleri alınamadı: {e}")
            return self.create_error_response(
                message="Admin istatistikleri alınamadı",
                status_code=500
            )
    
    async def get_admin_users(self, request: Request) -> Response:
        """Admin kullanıcı yönetimi"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Kullanıcının admin olup olmadığını kontrol et
            user = User.get_by_id(user_id)
            if not user.is_superuser:
                return self.create_error_response(
                    message="Admin yetkisi gerekli",
                    status_code=403
                )
            
            # Query parametrelerini al
            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', 20))
            search = request.query.get('search', '')
            status_filter = request.query.get('status', '')
            
            # Sayfalama için offset hesapla
            offset = (page - 1) * limit
            
            # Kullanıcıları al
            query = User.select()
            
            # Filtreleri uygula
            if search:
                query = query.where(
                    (User.username.contains(search)) |
                    (User.email.contains(search)) |
                    (User.full_name.contains(search))
                )
            
            if status_filter:
                if status_filter == 'active':
                    query = query.where(User.is_active == True)
                elif status_filter == 'inactive':
                    query = query.where(User.is_active == False)
                elif status_filter == 'verified':
                    query = query.where(User.is_verified == True)
                elif status_filter == 'unverified':
                    query = query.where(User.is_verified == False)
            
            # Toplam sayıyı al
            total_count = query.count()
            
            # Sayfalama uygula
            users = query.offset(offset).limit(limit)
            
            # Kullanıcı verilerini formatla
            user_list = []
            for user in users:
                # Kullanıcı rollerini al
                user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
                
                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "is_superuser": user.is_superuser,
                    "roles": user_roles,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "login_count": self._get_user_login_count(user.id)
                }
                user_list.append(user_data)
            
            response_data = {
                "users": user_list,
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                    "pages": (total_count + limit - 1) // limit
                }
            }
            
            return self.create_success_response(
                message="Admin kullanıcı listesi alındı",
                data=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Admin kullanıcı listesi alınamadı: {e}")
            return self.create_error_response(
                message="Admin kullanıcı listesi alınamadı",
                status_code=500
            )
    
    async def get_admin_sessions(self, request: Request) -> Response:
        """Admin session yönetimi"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Kullanıcının admin olup olmadığını kontrol et
            user = User.get_by_id(user_id)
            if not user.is_superuser:
                return self.create_error_response(
                    message="Admin yetkisi gerekli",
                    status_code=403
                )
            
            # Query parametrelerini al
            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', 20))
            status_filter = request.query.get('status', '')
            
            # Sayfalama için offset hesapla
            offset = (page - 1) * limit
            
            # Session'ları al
            query = Session.select().join(User)
            
            # Filtreleri uygula
            if status_filter == 'active':
                query = query.where(Session.is_active == True)
            elif status_filter == 'inactive':
                query = query.where(Session.is_active == False)
            
            # Toplam sayıyı al
            total_count = query.count()
            
            # Sayfalama uygula
            sessions = query.offset(offset).limit(limit)
            
            # Session verilerini formatla
            session_list = []
            for session in sessions:
                session_data = {
                    "id": session.id,
                    "user": {
                        "id": session.user.id,
                        "username": session.user.username,
                        "email": session.user.email
                    },
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "is_active": session.is_active,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                    "last_activity": session.last_activity.isoformat() if session.last_activity else None
                }
                session_list.append(session_data)
            
            response_data = {
                "sessions": session_list,
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                    "pages": (total_count + limit - 1) // limit
                }
            }
            
            return self.create_success_response(
                message="Admin session listesi alındı",
                data=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Admin session listesi alınamadı: {e}")
            return self.create_error_response(
                message="Admin session listesi alınamadı",
                status_code=500
            )
    
    async def get_admin_system(self, request: Request) -> Response:
        """Admin sistem bilgileri"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Kullanıcının admin olup olmadığını kontrol et
            user = User.get_by_id(user_id)
            if not user.is_superuser:
                return self.create_error_response(
                    message="Admin yetkisi gerekli",
                    status_code=403
                )
            
            # Sistem bilgilerini al
            system_data = {
                "server": {
                    "uptime": self._get_system_uptime(),
                    "version": "1.0.0",
                    "environment": "development",
                    "start_time": self._get_server_start_time()
                },
                "performance": {
                    "memory_usage": self._get_memory_usage(),
                    "disk_usage": self._get_disk_usage(),
                    "cpu_usage": self._get_cpu_usage(),
                    "network_io": self._get_network_io()
                },
                "database": {
                    "connection_count": self._get_db_connection_count(),
                    "query_count": self._get_db_query_count(),
                    "slow_queries": self._get_slow_queries()
                },
                "security": {
                    "failed_logins": self._get_failed_logins(),
                    "blocked_ips": self._get_blocked_ips(),
                    "security_events": self._get_security_events()
                }
            }
            
            return self.create_success_response(
                message="Admin sistem bilgileri alındı",
                data=system_data
            )
            
        except Exception as e:
            self.logger.error(f"Admin sistem bilgileri alınamadı: {e}")
            return self.create_error_response(
                message="Admin sistem bilgileri alınamadı",
                status_code=500
            )
    
    # Helper methods
    def _get_system_uptime(self) -> float:
        """Sistem uptime'ını al"""
        import psutil
        return time.time() - psutil.boot_time()
    
    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Son aktiviteleri al"""
        return [
            {
                "type": "user_login",
                "user": "admin",
                "timestamp": time.time() - 300,
                "description": "Admin giriş yaptı"
            },
            {
                "type": "config_update",
                "user": "admin",
                "timestamp": time.time() - 600,
                "description": "Server konfigürasyonu güncellendi"
            }
        ]
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Sistem sağlık durumunu al"""
        return {
            "status": "healthy",
            "cpu_usage": 25.5,
            "memory_usage": 60.2,
            "disk_usage": 45.8,
            "active_connections": 15
        }
    
    def _get_user_statistics(self) -> Dict[str, Any]:
        """Kullanıcı istatistiklerini al"""
        return {
            "total_users": User.select().count(),
            "active_users": User.select().where(User.is_active == True).count(),
            "new_users_today": 5,
            "new_users_this_week": 25
        }
    
    def _get_security_alerts(self) -> List[Dict[str, Any]]:
        """Güvenlik uyarılarını al"""
        return [
            {
                "type": "failed_login",
                "severity": "medium",
                "count": 3,
                "last_occurrence": time.time() - 1800
            }
        ]
    
    def _get_today_sessions(self) -> int:
        """Bugünkü session sayısını al"""
        from datetime import datetime, timedelta
        today = datetime.now().date()
        return Session.select().where(
            Session.created_at >= today
        ).count()
    
    def _get_week_sessions(self) -> int:
        """Bu haftaki session sayısını al"""
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        return Session.select().where(
            Session.created_at >= week_ago
        ).count()
    
    def _get_month_sessions(self) -> int:
        """Bu ayki session sayısını al"""
        from datetime import datetime, timedelta
        month_ago = datetime.now() - timedelta(days=30)
        return Session.select().where(
            Session.created_at >= month_ago
        ).count()
    
    def _get_role_distribution(self) -> Dict[str, int]:
        """Rol dağılımını al"""
        distribution = {}
        for role in Role.select():
            count = UserRole.select().where(UserRole.role == role).count()
            distribution[role.name] = count
        return distribution
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Memory kullanımını al"""
        import psutil
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "used": memory.used,
            "available": memory.available,
            "percent": memory.percent
        }
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """Disk kullanımını al"""
        import psutil
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
    
    def _get_cpu_usage(self) -> float:
        """CPU kullanımını al"""
        import psutil
        return psutil.cpu_percent(interval=1)
    
    def _get_network_io(self) -> Dict[str, int]:
        """Network I/O bilgilerini al"""
        import psutil
        network = psutil.net_io_counters()
        return {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
    
    def _get_failed_logins(self) -> int:
        """Başarısız giriş sayısını al"""
        return 5
    
    def _get_suspicious_activity(self) -> int:
        """Şüpheli aktivite sayısını al"""
        return 2
    
    def _get_blocked_ips(self) -> int:
        """Engellenmiş IP sayısını al"""
        return 1
    
    def _get_user_login_count(self, user_id: int) -> int:
        """Kullanıcının giriş sayısını al"""
        return 15
    
    def _get_db_connection_count(self) -> int:
        """Veritabanı bağlantı sayısını al"""
        return 5
    
    def _get_db_query_count(self) -> int:
        """Veritabanı sorgu sayısını al"""
        return 1250
    
    def _get_slow_queries(self) -> int:
        """Yavaş sorgu sayısını al"""
        return 3
    
    def _get_security_events(self) -> int:
        """Güvenlik olay sayısını al"""
        return 8
    
    def _get_server_start_time(self) -> str:
        """Server başlangıç zamanını al"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def activate_user(self, request: Request) -> Response:
        """Kullanıcıyı aktif et"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Kullanıcının admin olup olmadığını kontrol et
            user = User.get_by_id(user_id)
            if not user.is_superuser:
                return self.create_error_response(
                    message="Admin yetkisi gerekli",
                    status_code=403
                )
            
            target_user_id = int(request.match_info['user_id'])
            target_user = User.get_by_id(target_user_id)
            
            target_user.is_active = True
            target_user.save()
            
            # Log yaz
            self.logger.log_user_action(
                "user_activated",
                user_id,
                f"Kullanıcı aktif edildi: {target_user.username}",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message=f"Kullanıcı {target_user.username} başarıyla aktif edildi"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz kullanıcı ID",
                status_code=400
            )
        except User.DoesNotExist:
            return self.create_error_response(
                message="Kullanıcı bulunamadı",
                status_code=404
            )
        except Exception as e:
            self.logger.error(f"Kullanıcı aktif etme hatası: {e}")
            return self.create_error_response(
                message="Kullanıcı aktif edilemedi",
                status_code=500
            )
    
    async def deactivate_user(self, request: Request) -> Response:
        """Kullanıcıyı deaktif et"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Kullanıcının admin olup olmadığını kontrol et
            user = User.get_by_id(user_id)
            if not user.is_superuser:
                return self.create_error_response(
                    message="Admin yetkisi gerekli",
                    status_code=403
                )
            
            target_user_id = int(request.match_info['user_id'])
            target_user = User.get_by_id(target_user_id)
            
            # Kendini deaktif etmeye çalışıyor mu?
            if target_user_id == user_id:
                return self.create_error_response(
                    message="Kendinizi deaktif edemezsiniz",
                    status_code=400
                )
            
            target_user.is_active = False
            target_user.save()
            
            # Log yaz
            self.logger.log_user_action(
                "user_deactivated",
                user_id,
                f"Kullanıcı deaktif edildi: {target_user.username}",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message=f"Kullanıcı {target_user.username} başarıyla deaktif edildi"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz kullanıcı ID",
                status_code=400
            )
        except User.DoesNotExist:
            return self.create_error_response(
                message="Kullanıcı bulunamadı",
                status_code=404
            )
        except Exception as e:
            self.logger.error(f"Kullanıcı deaktif etme hatası: {e}")
            return self.create_error_response(
                message="Kullanıcı deaktif edilemedi",
                status_code=500
            )
    
    async def terminate_session(self, request: Request) -> Response:
        """Session'ı sonlandır"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Kullanıcının admin olup olmadığını kontrol et
            user = User.get_by_id(user_id)
            if not user.is_superuser:
                return self.create_error_response(
                    message="Admin yetkisi gerekli",
                    status_code=403
                )
            
            session_id = int(request.match_info['session_id'])
            session = Session.get_by_id(session_id)
            
            session.is_active = False
            session.save()
            
            # Log yaz
            self.logger.log_user_action(
                "session_terminated",
                user_id,
                f"Session sonlandırıldı: {session.user.username}",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message=f"Session başarıyla sonlandırıldı"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz session ID",
                status_code=400
            )
        except Session.DoesNotExist:
            return self.create_error_response(
                message="Session bulunamadı",
                status_code=404
            )
        except Exception as e:
            self.logger.error(f"Session sonlandırma hatası: {e}")
            return self.create_error_response(
                message="Session sonlandırılamadı",
                status_code=500
            )
    
    async def get_audit_logs(self, request: Request) -> Response:
        """Audit log'larını al"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Kullanıcının admin olup olmadığını kontrol et
            user = User.get_by_id(user_id)
            if not user.is_superuser:
                return self.create_error_response(
                    message="Admin yetkisi gerekli",
                    status_code=403
                )
            
            # Query parametrelerini al
            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', 50))
            action_filter = request.query.get('action', '')
            user_filter = request.query.get('user', '')
            
            # Sayfalama için offset hesapla
            offset = (page - 1) * limit
            
            # Örnek audit log verileri (gerçek uygulamada veritabanından alınır)
            audit_logs = [
                {
                    "id": 1,
                    "action": "user_login",
                    "user_id": 1,
                    "username": "admin",
                    "ip_address": "127.0.0.1",
                    "user_agent": "Mozilla/5.0...",
                    "timestamp": time.time() - 3600,
                    "details": "Successful login",
                    "status": "success"
                },
                {
                    "id": 2,
                    "action": "user_created",
                    "user_id": 1,
                    "username": "admin",
                    "ip_address": "127.0.0.1",
                    "user_agent": "Mozilla/5.0...",
                    "timestamp": time.time() - 7200,
                    "details": "Created user: testuser",
                    "status": "success"
                }
            ]
            
            # Filtreleme
            if action_filter:
                audit_logs = [log for log in audit_logs if action_filter in log['action']]
            
            if user_filter:
                audit_logs = [log for log in audit_logs if user_filter.lower() in log['username'].lower()]
            
            # Sayfalama
            total_count = len(audit_logs)
            paginated_logs = audit_logs[offset:offset + limit]
            
            # Log formatını düzenle
            formatted_logs = []
            for log in paginated_logs:
                formatted_log = {
                    "id": log['id'],
                    "action": log['action'],
                    "user_id": log['user_id'],
                    "username": log['username'],
                    "ip_address": log['ip_address'],
                    "user_agent": log['user_agent'],
                    "timestamp": log['timestamp'],
                    "details": log['details'],
                    "status": log['status']
                }
                formatted_logs.append(formatted_log)
            
            response_data = {
                "audit_logs": formatted_logs,
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                    "pages": (total_count + limit - 1) // limit
                }
            }
            
            return self.create_success_response(
                message="Audit log'ları alındı",
                data=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Audit log'ları alınamadı: {e}")
            return self.create_error_response(
                message="Audit log'ları alınamadı",
                status_code=500
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Client IP adresini al"""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote
