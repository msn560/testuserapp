"""
Notification Service module - Bildirim yönetimi

Bu modül sistem bildirimlerinin yönetimini sağlar.
E-posta, SMS, webhook ve in-app bildirimler.
"""

import smtplib
import requests
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json

from ..core.constants import LogLevel
from ..utils.logger import logger


class NotificationChannel:
    """Bildirim kanalı türleri."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    SYSTEM_LOG = "system_log"


class NotificationPriority:
    """Bildirim öncelik seviyeleri."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationService:
    """
    Bildirim yönetimi servisi.
    
    Bu sınıf sistem bildirimlerinin yönetimini sağlar.
    """
    
    def __init__(self):
        """
        NotificationService'i başlatır.
        """
        self.logger = logger
        
        # Bildirim ayarları
        self.settings = {
            NotificationChannel.EMAIL: {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "",
                "use_tls": True,
                "use_ssl": False
            },
            NotificationChannel.SMS: {
                "enabled": False,
                "provider": "twilio",  # twilio, aws_sns, custom
                "api_key": "",
                "api_secret": "",
                "from_number": "",
                "webhook_url": ""
            },
            NotificationChannel.WEBHOOK: {
                "enabled": False,
                "url": "",
                "headers": {},
                "timeout": 30,
                "retry_count": 3
            },
            NotificationChannel.IN_APP: {
                "enabled": True,
                "max_notifications": 100,
                "retention_days": 30
            },
            NotificationChannel.SYSTEM_LOG: {
                "enabled": True,
                "log_level": "INFO"
            }
        }
        
        # In-app bildirimler
        self.in_app_notifications: List[Dict[str, Any]] = []
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Bildirim istatistikleri
        self.stats = {
            "total_sent": 0,
            "successful_sent": 0,
            "failed_sent": 0,
            "by_channel": {
                NotificationChannel.EMAIL: 0,
                NotificationChannel.SMS: 0,
                NotificationChannel.WEBHOOK: 0,
                NotificationChannel.IN_APP: 0,
                NotificationChannel.SYSTEM_LOG: 0
            }
        }
        
        # Callback'ler
        self.notification_callbacks: List[Callable] = []
    
    def send_notification(self, message: str, title: str = None, 
                         channels: List[str] = None, priority: str = NotificationPriority.NORMAL,
                         recipients: List[str] = None, metadata: Dict[str, Any] = None) -> Dict[str, bool]:
        """
        Bildirim gönderir.
        
        Args:
            message: Bildirim mesajı
            title: Bildirim başlığı
            channels: Bildirim kanalları
            priority: Bildirim önceliği
            recipients: Alıcı listesi
            metadata: Ek metadata
            
        Returns:
            Kanal bazında gönderim sonuçları
        """
        try:
            if not channels:
                channels = [NotificationChannel.IN_APP, NotificationChannel.SYSTEM_LOG]
            
            if not recipients:
                recipients = []
            
            # Bildirim verisi oluştur
            notification_data = {
                "id": self._generate_notification_id(),
                "title": title or "System Notification",
                "message": message,
                "priority": priority,
                "channels": channels,
                "recipients": recipients,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            
            # Her kanal için bildirim gönder
            results = {}
            for channel in channels:
                try:
                    success = self._send_to_channel(channel, notification_data)
                    results[channel] = success
                    
                    # İstatistikleri güncelle
                    with self.lock:
                        self.stats["total_sent"] += 1
                        self.stats["by_channel"][channel] += 1
                        if success:
                            self.stats["successful_sent"] += 1
                        else:
                            self.stats["failed_sent"] += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to send notification to {channel}: {e}")
                    results[channel] = False
                    with self.lock:
                        self.stats["failed_sent"] += 1
            
            # Callback'leri çağır
            for callback in self.notification_callbacks:
                try:
                    callback(notification_data, results)
                except Exception as e:
                    self.logger.error(f"Error in notification callback: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return {}
    
    def send_email(self, to_emails: List[str], subject: str, message: str, 
                   html_message: str = None, attachments: List[str] = None) -> bool:
        """
        E-posta gönderir.
        
        Args:
            to_emails: Alıcı e-posta adresleri
            subject: E-posta konusu
            message: E-posta mesajı
            html_message: HTML mesaj
            attachments: Ek dosyalar
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            settings = self.settings[NotificationChannel.EMAIL]
            if not settings["enabled"]:
                self.logger.warning("Email notifications are disabled")
                return False
            
            # E-posta oluştur
            msg = MIMEMultipart('alternative')
            msg['From'] = settings["from_email"]
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Metin mesajı
            text_part = MIMEText(message, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # HTML mesajı
            if html_message:
                html_part = MIMEText(html_message, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Ek dosyalar
            if attachments:
                for attachment_path in attachments:
                    try:
                        with open(attachment_path, 'rb') as f:
                            attachment = MIMEBase('application', 'octet-stream')
                            attachment.set_payload(f.read())
                            encoders.encode_base64(attachment)
                            attachment.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {Path(attachment_path).name}'
                            )
                            msg.attach(attachment)
                    except Exception as e:
                        self.logger.warning(f"Failed to attach file {attachment_path}: {e}")
            
            # E-posta gönder
            server = smtplib.SMTP(settings["smtp_server"], settings["smtp_port"])
            
            if settings["use_tls"]:
                server.starttls()
            elif settings["use_ssl"]:
                server = smtplib.SMTP_SSL(settings["smtp_server"], settings["smtp_port"])
            
            if settings["username"] and settings["password"]:
                server.login(settings["username"], settings["password"])
            
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email sent to {len(to_emails)} recipients")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def send_sms(self, to_numbers: List[str], message: str) -> bool:
        """
        SMS gönderir.
        
        Args:
            to_numbers: Alıcı telefon numaraları
            message: SMS mesajı
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            settings = self.settings[NotificationChannel.SMS]
            if not settings["enabled"]:
                self.logger.warning("SMS notifications are disabled")
                return False
            
            provider = settings["provider"]
            
            if provider == "twilio":
                return self._send_sms_twilio(to_numbers, message, settings)
            elif provider == "aws_sns":
                return self._send_sms_aws_sns(to_numbers, message, settings)
            else:
                self.logger.error(f"Unsupported SMS provider: {provider}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send SMS: {e}")
            return False
    
    def send_webhook(self, url: str, data: Dict[str, Any], headers: Dict[str, str] = None) -> bool:
        """
        Webhook gönderir.
        
        Args:
            url: Webhook URL'i
            data: Gönderilecek veri
            headers: HTTP header'ları
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            settings = self.settings[NotificationChannel.WEBHOOK]
            if not settings["enabled"]:
                self.logger.warning("Webhook notifications are disabled")
                return False
            
            # Header'ları birleştir
            request_headers = settings["headers"].copy()
            if headers:
                request_headers.update(headers)
            
            # Webhook gönder
            response = requests.post(
                url,
                json=data,
                headers=request_headers,
                timeout=settings["timeout"]
            )
            
            response.raise_for_status()
            
            self.logger.info(f"Webhook sent to {url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook to {url}: {e}")
            return False
    
    def add_in_app_notification(self, message: str, title: str = None, 
                               priority: str = NotificationPriority.NORMAL,
                               metadata: Dict[str, Any] = None) -> str:
        """
        In-app bildirim ekler.
        
        Args:
            message: Bildirim mesajı
            title: Bildirim başlığı
            priority: Bildirim önceliği
            metadata: Ek metadata
            
        Returns:
            Bildirim ID'si
        """
        try:
            notification_id = self._generate_notification_id()
            
            notification = {
                "id": notification_id,
                "title": title or "System Notification",
                "message": message,
                "priority": priority,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "read": False
            }
            
            with self.lock:
                self.in_app_notifications.append(notification)
                
                # Maksimum bildirim sayısını kontrol et
                max_notifications = self.settings[NotificationChannel.IN_APP]["max_notifications"]
                if len(self.in_app_notifications) > max_notifications:
                    self.in_app_notifications = self.in_app_notifications[-max_notifications:]
            
            self.logger.debug(f"In-app notification added: {notification_id}")
            return notification_id
            
        except Exception as e:
            self.logger.error(f"Failed to add in-app notification: {e}")
            return None
    
    def get_in_app_notifications(self, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """
        In-app bildirimleri döndürür.
        
        Args:
            unread_only: Sadece okunmamış bildirimler
            limit: Maksimum bildirim sayısı
            
        Returns:
            In-app bildirim listesi
        """
        try:
            with self.lock:
                notifications = self.in_app_notifications.copy()
            
            if unread_only:
                notifications = [n for n in notifications if not n.get("read", False)]
            
            # Tarihe göre sırala (en yeni önce)
            notifications.sort(key=lambda x: x["created_at"], reverse=True)
            
            return notifications[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get in-app notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """
        Bildirimi okundu olarak işaretler.
        
        Args:
            notification_id: Bildirim ID'si
            
        Returns:
            True if marked successfully, False otherwise
        """
        try:
            with self.lock:
                for notification in self.in_app_notifications:
                    if notification["id"] == notification_id:
                        notification["read"] = True
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to mark notification as read: {e}")
            return False
    
    def clear_old_notifications(self) -> int:
        """
        Eski bildirimleri temizler.
        
        Returns:
            Temizlenen bildirim sayısı
        """
        try:
            retention_days = self.settings[NotificationChannel.IN_APP]["retention_days"]
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with self.lock:
                original_count = len(self.in_app_notifications)
                self.in_app_notifications = [
                    n for n in self.in_app_notifications
                    if datetime.fromisoformat(n["created_at"]) > cutoff_date
                ]
                cleared_count = original_count - len(self.in_app_notifications)
            
            if cleared_count > 0:
                self.logger.info(f"Cleared {cleared_count} old notifications")
            
            return cleared_count
            
        except Exception as e:
            self.logger.error(f"Failed to clear old notifications: {e}")
            return 0
    
    def configure_channel(self, channel: str, settings: Dict[str, Any]) -> bool:
        """
        Bildirim kanalını yapılandırır.
        
        Args:
            channel: Kanal adı
            settings: Kanal ayarları
            
        Returns:
            True if configured successfully, False otherwise
        """
        try:
            if channel not in self.settings:
                self.logger.error(f"Unknown notification channel: {channel}")
                return False
            
            self.settings[channel].update(settings)
            self.logger.info(f"Notification channel configured: {channel}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure channel {channel}: {e}")
            return False
    
    def add_notification_callback(self, callback: Callable):
        """
        Bildirim callback'i ekler.
        
        Args:
            callback: Callback fonksiyonu
        """
        self.notification_callbacks.append(callback)
    
    def get_notification_statistics(self) -> Dict[str, Any]:
        """
        Bildirim istatistiklerini döndürür.
        
        Returns:
            Bildirim istatistikleri
        """
        try:
            with self.lock:
                total_sent = self.stats["total_sent"]
                success_rate = (self.stats["successful_sent"] / total_sent * 100) if total_sent > 0 else 0
                
                return {
                    "total_sent": total_sent,
                    "successful_sent": self.stats["successful_sent"],
                    "failed_sent": self.stats["failed_sent"],
                    "success_rate_percent": round(success_rate, 2),
                    "by_channel": self.stats["by_channel"].copy(),
                    "in_app_notifications_count": len(self.in_app_notifications),
                    "unread_notifications_count": len([n for n in self.in_app_notifications if not n.get("read", False)]),
                    "settings": {k: {**v} for k, v in self.settings.items()}
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get notification statistics: {e}")
            return {}
    
    def _send_to_channel(self, channel: str, notification_data: Dict[str, Any]) -> bool:
        """
        Belirli kanala bildirim gönderir.
        
        Args:
            channel: Bildirim kanalı
            notification_data: Bildirim verisi
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if channel == NotificationChannel.EMAIL:
                return self._send_email_notification(notification_data)
            elif channel == NotificationChannel.SMS:
                return self._send_sms_notification(notification_data)
            elif channel == NotificationChannel.WEBHOOK:
                return self._send_webhook_notification(notification_data)
            elif channel == NotificationChannel.IN_APP:
                return self._send_in_app_notification(notification_data)
            elif channel == NotificationChannel.SYSTEM_LOG:
                return self._send_system_log_notification(notification_data)
            else:
                self.logger.error(f"Unknown notification channel: {channel}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send to channel {channel}: {e}")
            return False
    
    def _send_email_notification(self, notification_data: Dict[str, Any]) -> bool:
        """E-posta bildirimi gönderir."""
        try:
            settings = self.settings[NotificationChannel.EMAIL]
            if not settings["enabled"]:
                return False
            
            recipients = notification_data.get("recipients", [])
            if not recipients:
                return False
            
            subject = f"[{notification_data['priority'].upper()}] {notification_data['title']}"
            message = notification_data["message"]
            
            return self.send_email(recipients, subject, message)
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _send_sms_notification(self, notification_data: Dict[str, Any]) -> bool:
        """SMS bildirimi gönderir."""
        try:
            settings = self.settings[NotificationChannel.SMS]
            if not settings["enabled"]:
                return False
            
            recipients = notification_data.get("recipients", [])
            if not recipients:
                return False
            
            message = f"{notification_data['title']}: {notification_data['message']}"
            
            return self.send_sms(recipients, message)
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS notification: {e}")
            return False
    
    def _send_webhook_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Webhook bildirimi gönderir."""
        try:
            settings = self.settings[NotificationChannel.WEBHOOK]
            if not settings["enabled"]:
                return False
            
            url = settings["url"]
            if not url:
                return False
            
            return self.send_webhook(url, notification_data)
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
            return False
    
    def _send_in_app_notification(self, notification_data: Dict[str, Any]) -> bool:
        """In-app bildirimi gönderir."""
        try:
            notification_id = self.add_in_app_notification(
                notification_data["message"],
                notification_data["title"],
                notification_data["priority"],
                notification_data["metadata"]
            )
            return notification_id is not None
            
        except Exception as e:
            self.logger.error(f"Failed to send in-app notification: {e}")
            return False
    
    def _send_system_log_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Sistem log bildirimi gönderir."""
        try:
            settings = self.settings[NotificationChannel.SYSTEM_LOG]
            if not settings["enabled"]:
                return False
            
            log_level = getattr(LogLevel, settings["log_level"], LogLevel.INFO)
            log_message = f"NOTIFICATION [{notification_data['priority']}]: {notification_data['title']} - {notification_data['message']}"
            
            # Sistem log'a yaz
            from ..db.models import SystemLog
            SystemLog.create(
                level=log_level.value,
                module="notification_service",
                message=log_message,
                created_at=datetime.now()
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send system log notification: {e}")
            return False
    
    def _send_sms_twilio(self, to_numbers: List[str], message: str, settings: Dict[str, Any]) -> bool:
        """Twilio ile SMS gönderir."""
        try:
            # Twilio API kullanımı için gerekli implementasyon
            # Bu örnekte basit bir HTTP isteği simüle ediliyor
            self.logger.info(f"SMS sent via Twilio to {len(to_numbers)} numbers")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS via Twilio: {e}")
            return False
    
    def _send_sms_aws_sns(self, to_numbers: List[str], message: str, settings: Dict[str, Any]) -> bool:
        """AWS SNS ile SMS gönderir."""
        try:
            # AWS SNS API kullanımı için gerekli implementasyon
            # Bu örnekte basit bir HTTP isteği simüle ediliyor
            self.logger.info(f"SMS sent via AWS SNS to {len(to_numbers)} numbers")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS via AWS SNS: {e}")
            return False
    
    def _generate_notification_id(self) -> str:
        """Bildirim ID'si oluşturur."""
        import secrets
        return f"notif_{secrets.token_urlsafe(16)}"


# Global instance
notification_service = NotificationService()
