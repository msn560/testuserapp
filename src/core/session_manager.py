"""
Session Manager module - Oturum yönetimi

Bu modül kullanıcı oturumlarını yönetir.
Session oluşturma, doğrulama, yenileme ve sonlandırma işlemleri.
"""

import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from collections import defaultdict

from ..db.models import Session, User
from ..core.constants import LogLevel
from ..utils.logger import logger


@dataclass
class SessionData:
    """Session veri yapısı."""
    session_id: str
    user_id: int
    token: str
    refresh_token: str
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    is_active: bool
    metadata: Dict[str, Any] = None


class SessionManager:
    """
    Kullanıcı oturumlarını yöneten sınıf.
    
    Bu sınıf session oluşturma, doğrulama, yenileme ve sonlandırma işlemlerini sağlar.
    """
    
    def __init__(self, session_timeout: int = 3600, cleanup_interval: int = 300):
        """
        SessionManager'ı başlatır.
        
        Args:
            session_timeout: Session timeout süresi (saniye)
            cleanup_interval: Temizlik aralığı (saniye)
        """
        self.logger = logger
        self.session_timeout = session_timeout
        self.cleanup_interval = cleanup_interval
        
        # Memory cache for active sessions
        self.active_sessions: Dict[str, SessionData] = {}
        self.user_sessions: Dict[int, List[str]] = defaultdict(list)
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Cleanup thread
        self.cleanup_thread = None
        self.is_running = False
        
        # Session statistics
        self.stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "expired_sessions": 0,
            "invalidated_sessions": 0
        }
    
    def start(self) -> bool:
        """
        Session manager'ı başlatır.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                self.logger.warning("Session manager is already running")
                return True
            
            self.is_running = True
            
            # Start cleanup thread
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True,
                name="SessionCleanup"
            )
            self.cleanup_thread.start()
            
            # Load existing sessions from database
            self._load_existing_sessions()
            
            self.logger.info("Session manager started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start session manager: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Session manager'ı durdurur.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if not self.is_running:
                self.logger.warning("Session manager is not running")
                return True
            
            self.is_running = False
            
            # Wait for cleanup thread to finish
            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=10)
            
            # Save sessions to database
            self._save_sessions_to_db()
            
            self.logger.info("Session manager stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop session manager: {e}")
            return False
    
    def create_session(self, user_id: int, ip_address: str, user_agent: str, 
                      metadata: Dict[str, Any] = None) -> Optional[SessionData]:
        """
        Yeni session oluşturur.
        
        Args:
            user_id: Kullanıcı ID'si
            ip_address: IP adresi
            user_agent: User agent
            metadata: Ek metadata
            
        Returns:
            Oluşturulan session data
        """
        try:
            with self.lock:
                # Generate session tokens
                session_id = self._generate_session_id()
                token = self._generate_token()
                refresh_token = self._generate_refresh_token()
                
                # Calculate expiration times
                now = datetime.now()
                expires_at = now + timedelta(seconds=self.session_timeout)
                
                # Create session data
                session_data = SessionData(
                    session_id=session_id,
                    user_id=user_id,
                    token=token,
                    refresh_token=refresh_token,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_at=now,
                    expires_at=expires_at,
                    last_activity=now,
                    is_active=True,
                    metadata=metadata or {}
                )
                
                # Store in memory cache
                self.active_sessions[session_id] = session_data
                self.user_sessions[user_id].append(session_id)
                
                # Save to database
                self._save_session_to_db(session_data)
                
                # Update statistics
                self.stats["total_sessions"] += 1
                self.stats["active_sessions"] += 1
                
                self.logger.info(f"Session created for user {user_id}: {session_id}")
                return session_data
                
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return None
    
    def validate_session(self, session_id: str, token: str) -> Optional[SessionData]:
        """
        Session'ı doğrular.
        
        Args:
            session_id: Session ID
            token: Session token
            
        Returns:
            Session data if valid, None otherwise
        """
        try:
            with self.lock:
                session_data = self.active_sessions.get(session_id)
                
                if not session_data:
                    self.logger.warning(f"Session not found: {session_id}")
                    return None
                
                if not session_data.is_active:
                    self.logger.warning(f"Session is inactive: {session_id}")
                    return None
                
                if session_data.token != token:
                    self.logger.warning(f"Invalid token for session: {session_id}")
                    return None
                
                if datetime.now() > session_data.expires_at:
                    self.logger.warning(f"Session expired: {session_id}")
                    self._invalidate_session(session_id)
                    return None
                
                # Update last activity
                session_data.last_activity = datetime.now()
                
                return session_data
                
        except Exception as e:
            self.logger.error(f"Failed to validate session: {e}")
            return None
    
    def refresh_session(self, session_id: str, refresh_token: str) -> Optional[SessionData]:
        """
        Session'ı yeniler.
        
        Args:
            session_id: Session ID
            refresh_token: Refresh token
            
        Returns:
            Yenilenen session data
        """
        try:
            with self.lock:
                session_data = self.active_sessions.get(session_id)
                
                if not session_data:
                    self.logger.warning(f"Session not found for refresh: {session_id}")
                    return None
                
                if not session_data.is_active:
                    self.logger.warning(f"Session is inactive for refresh: {session_id}")
                    return None
                
                if session_data.refresh_token != refresh_token:
                    self.logger.warning(f"Invalid refresh token for session: {session_id}")
                    return None
                
                # Generate new tokens
                new_token = self._generate_token()
                new_refresh_token = self._generate_refresh_token()
                
                # Update session data
                session_data.token = new_token
                session_data.refresh_token = new_refresh_token
                session_data.last_activity = datetime.now()
                session_data.expires_at = datetime.now() + timedelta(seconds=self.session_timeout)
                
                # Update in database
                self._update_session_in_db(session_data)
                
                self.logger.info(f"Session refreshed: {session_id}")
                return session_data
                
        except Exception as e:
            self.logger.error(f"Failed to refresh session: {e}")
            return None
    
    def invalidate_session(self, session_id: str) -> bool:
        """
        Session'ı geçersiz kılar.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        try:
            with self.lock:
                return self._invalidate_session(session_id)
                
        except Exception as e:
            self.logger.error(f"Failed to invalidate session: {e}")
            return False
    
    def invalidate_user_sessions(self, user_id: int) -> int:
        """
        Kullanıcının tüm session'larını geçersiz kılar.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Geçersiz kılınan session sayısı
        """
        try:
            with self.lock:
                invalidated_count = 0
                user_session_ids = self.user_sessions.get(user_id, [])
                
                for session_id in user_session_ids[:]:  # Copy list to avoid modification during iteration
                    if self._invalidate_session(session_id):
                        invalidated_count += 1
                
                self.logger.info(f"Invalidated {invalidated_count} sessions for user {user_id}")
                return invalidated_count
                
        except Exception as e:
            self.logger.error(f"Failed to invalidate user sessions: {e}")
            return 0
    
    def get_user_sessions(self, user_id: int) -> List[SessionData]:
        """
        Kullanıcının aktif session'larını döndürür.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Kullanıcının aktif session'ları
        """
        try:
            with self.lock:
                sessions = []
                user_session_ids = self.user_sessions.get(user_id, [])
                
                for session_id in user_session_ids:
                    session_data = self.active_sessions.get(session_id)
                    if session_data and session_data.is_active:
                        sessions.append(session_data)
                
                return sessions
                
        except Exception as e:
            self.logger.error(f"Failed to get user sessions: {e}")
            return []
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Session istatistiklerini döndürür.
        
        Returns:
            Session istatistikleri
        """
        try:
            with self.lock:
                return {
                    "total_sessions": self.stats["total_sessions"],
                    "active_sessions": len(self.active_sessions),
                    "expired_sessions": self.stats["expired_sessions"],
                    "invalidated_sessions": self.stats["invalidated_sessions"],
                    "session_timeout": self.session_timeout,
                    "cleanup_interval": self.cleanup_interval,
                    "is_running": self.is_running
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get session statistics: {e}")
            return {}
    
    def cleanup_expired_sessions(self) -> int:
        """
        Süresi dolmuş session'ları temizler.
        
        Returns:
            Temizlenen session sayısı
        """
        try:
            with self.lock:
                cleaned_count = 0
                current_time = datetime.now()
                
                # Find expired sessions
                expired_sessions = []
                for session_id, session_data in self.active_sessions.items():
                    if current_time > session_data.expires_at:
                        expired_sessions.append(session_id)
                
                # Remove expired sessions
                for session_id in expired_sessions:
                    if self._invalidate_session(session_id):
                        cleaned_count += 1
                
                if cleaned_count > 0:
                    self.logger.info(f"Cleaned up {cleaned_count} expired sessions")
                
                return cleaned_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    def _invalidate_session(self, session_id: str) -> bool:
        """
        Session'ı geçersiz kılar (internal method).
        
        Args:
            session_id: Session ID
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        try:
            session_data = self.active_sessions.get(session_id)
            if not session_data:
                return False
            
            # Mark as inactive
            session_data.is_active = False
            
            # Remove from user sessions
            user_sessions = self.user_sessions.get(session_data.user_id, [])
            if session_id in user_sessions:
                user_sessions.remove(session_id)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Update in database
            self._update_session_in_db(session_data)
            
            # Update statistics
            self.stats["invalidated_sessions"] += 1
            self.stats["active_sessions"] -= 1
            
            self.logger.info(f"Session invalidated: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to invalidate session {session_id}: {e}")
            return False
    
    def _generate_session_id(self) -> str:
        """
        Session ID oluşturur.
        
        Returns:
            Session ID
        """
        import secrets
        return f"sess_{secrets.token_urlsafe(16)}"
    
    def _generate_token(self) -> str:
        """
        Session token oluşturur.
        
        Returns:
            Session token
        """
        import secrets
        return f"tok_{secrets.token_urlsafe(32)}"
    
    def _generate_refresh_token(self) -> str:
        """
        Refresh token oluşturur.
        
        Returns:
            Refresh token
        """
        import secrets
        return f"ref_{secrets.token_urlsafe(32)}"
    
    def _load_existing_sessions(self):
        """Veritabanından mevcut session'ları yükler."""
        try:
            # Load active sessions from database
            db_sessions = Session.select().where(
                (Session.is_active == True) &
                (Session.expires_at > datetime.now())
            )
            
            for db_session in db_sessions:
                session_data = SessionData(
                    session_id=db_session.token,  # Using token as session_id
                    user_id=db_session.user_id,
                    token=db_session.token,
                    refresh_token=db_session.refresh_token,
                    ip_address=db_session.ip_address,
                    user_agent=db_session.user_agent,
                    created_at=db_session.created_at,
                    expires_at=db_session.expires_at,
                    last_activity=db_session.last_activity,
                    is_active=db_session.is_active,
                    metadata={}
                )
                
                self.active_sessions[session_data.session_id] = session_data
                self.user_sessions[session_data.user_id].append(session_data.session_id)
            
            self.logger.info(f"Loaded {len(self.active_sessions)} existing sessions")
            
        except Exception as e:
            self.logger.error(f"Failed to load existing sessions: {e}")
    
    def _save_session_to_db(self, session_data: SessionData):
        """Session'ı veritabanına kaydeder."""
        try:
            Session.create(
                user_id=session_data.user_id,
                token=session_data.token,
                refresh_token=session_data.refresh_token,
                ip_address=session_data.ip_address,
                user_agent=session_data.user_agent,
                created_at=session_data.created_at,
                expires_at=session_data.expires_at,
                last_activity=session_data.last_activity,
                is_active=session_data.is_active
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save session to database: {e}")
    
    def _update_session_in_db(self, session_data: SessionData):
        """Session'ı veritabanında günceller."""
        try:
            db_session = Session.get(Session.token == session_data.token)
            db_session.refresh_token = session_data.refresh_token
            db_session.expires_at = session_data.expires_at
            db_session.last_activity = session_data.last_activity
            db_session.is_active = session_data.is_active
            db_session.save()
            
        except Exception as e:
            self.logger.error(f"Failed to update session in database: {e}")
    
    def _save_sessions_to_db(self):
        """Tüm session'ları veritabanına kaydeder."""
        try:
            for session_data in self.active_sessions.values():
                self._update_session_in_db(session_data)
                
        except Exception as e:
            self.logger.error(f"Failed to save sessions to database: {e}")
    
    def _cleanup_loop(self):
        """Session temizlik döngüsü."""
        try:
            self.logger.info("Session cleanup loop started")
            
            while self.is_running:
                try:
                    # Cleanup expired sessions
                    self.cleanup_expired_sessions()
                    
                    # Wait for next cleanup
                    import time
                    time.sleep(self.cleanup_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in cleanup loop: {e}")
                    import time
                    time.sleep(60)  # Wait longer on error
            
            self.logger.info("Session cleanup loop stopped")
            
        except Exception as e:
            self.logger.error(f"Fatal error in cleanup loop: {e}")


# Global instance
session_manager = SessionManager()
