"""
Validators module - Veri doğrulama

Bu modül veri doğrulama fonksiyonlarını içerir.
E-posta, parola, IP adresi, dosya ve diğer veri tiplerinin doğrulanması.
"""

import re
import ipaddress
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
import mimetypes
import json

from .logger import logger


class ValidationResult:
    """Doğrulama sonucu sınıfı."""
    
    def __init__(self, is_valid: bool = True, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str):
        """Hata ekler."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Uyarı ekler."""
        self.warnings.append(warning)


class DataValidator:
    """
    Veri doğrulama sınıfı.
    
    Bu sınıf çeşitli veri tiplerinin doğrulanması için fonksiyonlar sağlar.
    """
    
    def __init__(self):
        """DataValidator'ı başlatır."""
        self.logger = logger
        
        # Regex pattern'ları
        self.patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'phone': re.compile(r'^(\+90|0)?[1-9][0-9]{9}$'),  # Türkiye telefon numarası
            'username': re.compile(r'^[a-zA-Z0-9_]{3,30}$'),
            'hostname': re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'),
            'url': re.compile(r'^https?://(?:[-\w.])+(?::[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'),
            'ipv4': re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'),
            'mac_address': re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'),
            'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE),
            'jwt': re.compile(r'^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$')
        }
        
        # Dosya boyut limitleri (bytes)
        self.file_size_limits = {
            'image': 10 * 1024 * 1024,  # 10MB
            'document': 50 * 1024 * 1024,  # 50MB
            'video': 500 * 1024 * 1024,  # 500MB
            'audio': 100 * 1024 * 1024,  # 100MB
            'default': 10 * 1024 * 1024  # 10MB
        }
        
        # İzin verilen MIME tipleri
        self.allowed_mime_types = {
            'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
            'document': ['application/pdf', 'text/plain', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'archive': ['application/zip', 'application/x-rar-compressed', 'application/x-tar'],
            'data': ['application/json', 'text/csv', 'application/xml']
        }
    
    def validate_email(self, email: str) -> ValidationResult:
        """
        E-posta adresini doğrular.
        
        Args:
            email: E-posta adresi
            
        Returns:
            Doğrulama sonucu
        """
        result = ValidationResult()
        
        try:
            if not email:
                result.add_error("E-posta adresi boş olamaz")
                return result
            
            if not isinstance(email, str):
                result.add_error("E-posta adresi string olmalı")
                return result
            
            email = email.strip().lower()
            
            # Uzunluk kontrolü
            if len(email) > 254:
                result.add_error("E-posta adresi çok uzun (maksimum 254 karakter)")
            
            # Format kontrolü
            if not self.patterns['email'].match(email):
                result.add_error("Geçersiz e-posta formatı")
            
            # Local part kontrolü (@ öncesi)
            local_part = email.split('@')[0]
            if len(local_part) > 64:
                result.add_error("E-posta yerel kısmı çok uzun (maksimum 64 karakter)")
            
            # Başlangıç ve bitiş nokta kontrolü
            if local_part.startswith('.') or local_part.endswith('.'):
                result.add_error("E-posta yerel kısmı nokta ile başlayamaz veya bitemez")
            
            # Ardışık nokta kontrolü
            if '..' in email:
                result.add_error("E-posta adresinde ardışık nokta bulunamaz")
                
        except Exception as e:
            self.logger.error(f"Email validation error: {e}")
            result.add_error("E-posta doğrulama sırasında hata oluştu")
        
        return result
    
    def validate_password(self, password: str, min_length: int = None, 
                         require_uppercase: bool = None, require_lowercase: bool = None,
                         require_numbers: bool = None, require_special: bool = None) -> ValidationResult:
        """
        Parola güvenliğini doğrular.
        
        Args:
            password: Parola
            min_length: Minimum uzunluk
            require_uppercase: Büyük harf gerekli mi
            require_lowercase: Küçük harf gerekli mi
            require_numbers: Sayı gerekli mi
            require_special: Özel karakter gerekli mi
            
        Returns:
            Doğrulama sonucu
        """
        result = ValidationResult()
        
        try:
            # Config'den varsayılan değerleri al
            from ..core.settings import settings
            if min_length is None:
                min_length = settings.security.password_min_length
            if require_uppercase is None:
                require_uppercase = getattr(settings.security, 'password_require_uppercase', True)
            if require_lowercase is None:
                require_lowercase = getattr(settings.security, 'password_require_lowercase', True)
            if require_numbers is None:
                require_numbers = getattr(settings.security, 'password_require_numbers', True)
            if require_special is None:
                require_special = settings.security.password_require_special_chars
            
            if not password:
                result.add_error("Parola boş olamaz")
                return result
            
            if not isinstance(password, str):
                result.add_error("Parola string olmalı")
                return result
            
            # Uzunluk kontrolü
            if len(password) < min_length:
                result.add_error(f"Parola en az {min_length} karakter olmalı")
            
            if len(password) > 128:
                result.add_error("Parola çok uzun (maksimum 128 karakter)")
            
            # Büyük harf kontrolü
            if require_uppercase and not any(c.isupper() for c in password):
                result.add_error("Parola en az bir büyük harf içermeli")
            
            # Küçük harf kontrolü
            if require_lowercase and not any(c.islower() for c in password):
                result.add_error("Parola en az bir küçük harf içermeli")
            
            # Sayı kontrolü
            if require_numbers and not any(c.isdigit() for c in password):
                result.add_error("Parola en az bir sayı içermeli")
            
            # Özel karakter kontrolü
            if require_special:
                special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
                if not any(c in special_chars for c in password):
                    result.add_error("Parola en az bir özel karakter içermeli")
            
            # Yaygın parolalar kontrolü
            common_passwords = [
                "password", "123456", "123456789", "qwerty", "abc123",
                "password123", "admin", "root", "user", "test"
            ]
            if password.lower() in common_passwords:
                result.add_error("Yaygın kullanılan parolalar güvenli değildir")
            
            # Tekrarlayan karakter kontrolü
            if len(set(password)) < len(password) / 2:
                result.add_warning("Parola çok fazla tekrarlayan karakter içeriyor")
                
        except Exception as e:
            self.logger.error(f"Password validation error: {e}")
            result.add_error("Parola doğrulama sırasında hata oluştu")
        
        return result
    
    def validate_username(self, username: str) -> ValidationResult:
        """
        Kullanıcı adını doğrular.
        
        Args:
            username: Kullanıcı adı
            
        Returns:
            Doğrulama sonucu
        """
        result = ValidationResult()
        
        try:
            if not username:
                result.add_error("Kullanıcı adı boş olamaz")
                return result
            
            if not isinstance(username, str):
                result.add_error("Kullanıcı adı string olmalı")
                return result
            
            username = username.strip()
            
            # Uzunluk kontrolü
            if len(username) < 3:
                result.add_error("Kullanıcı adı en az 3 karakter olmalı")
            
            if len(username) > 30:
                result.add_error("Kullanıcı adı en fazla 30 karakter olmalı")
            
            # Format kontrolü
            if not self.patterns['username'].match(username):
                result.add_error("Kullanıcı adı sadece harf, sayı ve alt çizgi içerebilir")
            
            # Başlangıç kontrolü
            if username.startswith('_') or username.endswith('_'):
                result.add_error("Kullanıcı adı alt çizgi ile başlayamaz veya bitemez")
            
            # Rezerve isimler
            reserved_names = [
                'admin', 'administrator', 'root', 'system', 'api', 'www',
                'mail', 'email', 'support', 'help', 'info', 'contact'
            ]
            if username.lower() in reserved_names:
                result.add_error("Bu kullanıcı adı rezerve edilmiştir")
                
        except Exception as e:
            self.logger.error(f"Username validation error: {e}")
            result.add_error("Kullanıcı adı doğrulama sırasında hata oluştu")
        
        return result
    
    def validate_ip_address(self, ip_address: str, allow_private: bool = True) -> ValidationResult:
        """
        IP adresini doğrular.
        
        Args:
            ip_address: IP adresi
            allow_private: Özel IP adreslerine izin ver
            
        Returns:
            Doğrulama sonucu
        """
        result = ValidationResult()
        
        try:
            if not ip_address:
                result.add_error("IP adresi boş olamaz")
                return result
            
            if not isinstance(ip_address, str):
                result.add_error("IP adresi string olmalı")
                return result
            
            ip_address = ip_address.strip()
            
            # IPv4 doğrulama
            try:
                ip_obj = ipaddress.IPv4Address(ip_address)
                
                # Özel IP kontrolü
                if not allow_private and ip_obj.is_private:
                    result.add_error("Özel IP adresleri izin verilmiyor")
                
                # Loopback kontrolü
                if ip_obj.is_loopback:
                    result.add_warning("Loopback IP adresi")
                
                # Multicast kontrolü
                if ip_obj.is_multicast:
                    result.add_warning("Multicast IP adresi")
                    
            except ipaddress.AddressValueError:
                # IPv6 deneme
                try:
                    ip_obj = ipaddress.IPv6Address(ip_address)
                    result.add_warning("IPv6 adresi tespit edildi")
                except ipaddress.AddressValueError:
                    result.add_error("Geçersiz IP adresi formatı")
                    
        except Exception as e:
            self.logger.error(f"IP address validation error: {e}")
            result.add_error("IP adresi doğrulama sırasında hata oluştu")
        
        return result
    
    def validate_port(self, port: Union[int, str]) -> ValidationResult:
        """
        Port numarasını doğrular.
        
        Args:
            port: Port numarası
            
        Returns:
            Doğrulama sonucu
        """
        result = ValidationResult()
        
        try:
            # String ise integer'a çevir
            if isinstance(port, str):
                try:
                    port = int(port)
                except ValueError:
                    result.add_error("Port numarası geçerli bir sayı olmalı")
                    return result
            
            if not isinstance(port, int):
                result.add_error("Port numarası integer olmalı")
                return result
            
            # Aralık kontrolü
            if port < 1 or port > 65535:
                result.add_error("Port numarası 1-65535 arasında olmalı")
            
            # Rezerve portlar
            if port < 1024:
                result.add_warning("Sistem rezerve port aralığı (1-1023)")
            
            # Yaygın portlar
            common_ports = {
                22: "SSH", 25: "SMTP", 53: "DNS", 80: "HTTP",
                110: "POP3", 143: "IMAP", 443: "HTTPS", 993: "IMAPS", 995: "POP3S"
            }
            if port in common_ports:
                result.add_warning(f"Yaygın kullanılan port: {common_ports[port]}")
                
        except Exception as e:
            self.logger.error(f"Port validation error: {e}")
            result.add_error("Port doğrulama sırasında hata oluştu")
        
        return result
    
    def validate_url(self, url: str, require_https: bool = False) -> ValidationResult:
        """
        URL'yi doğrular.
        
        Args:
            url: URL
            require_https: HTTPS zorunlu mu
            
        Returns:
            Doğrulama sonucu
        """
        result = ValidationResult()
        
        try:
            if not url:
                result.add_error("URL boş olamaz")
                return result
            
            if not isinstance(url, str):
                result.add_error("URL string olmalı")
                return result
            
            url = url.strip()
            
            # Uzunluk kontrolü
            if len(url) > 2048:
                result.add_error("URL çok uzun (maksimum 2048 karakter)")
            
            # Format kontrolü
            if not self.patterns['url'].match(url):
                result.add_error("Geçersiz URL formatı")
                return result
            
            # HTTPS kontrolü
            if require_https and not url.startswith('https://'):
                result.add_error("HTTPS gerekli")
            
            # HTTP kontrolü
            if url.startswith('http://') and not url.startswith('https://'):
                result.add_warning("Güvenli olmayan HTTP bağlantısı")
                
        except Exception as e:
            self.logger.error(f"URL validation error: {e}")
            result.add_error("URL doğrulama sırasında hata oluştu")
        
        return result
    
    def validate_file(self, file_path: str, allowed_extensions: List[str] = None,
                     max_size: int = None, file_type: str = None) -> ValidationResult:
        """
        Dosyayı doğrular.
        
        Args:
            file_path: Dosya yolu
            allowed_extensions: İzin verilen uzantılar
            max_size: Maksimum dosya boyutu (bytes)
            file_type: Dosya tipi (image, document, vb.)
            
        Returns:
            Doğrulama sonucu
        """
        result = ValidationResult()
        
        try:
            if not file_path:
                result.add_error("Dosya yolu boş olamaz")
                return result
            
            file_path_obj = Path(file_path)
            
            # Dosya varlığı kontrolü
            if not file_path_obj.exists():
                result.add_error("Dosya bulunamadı")
                return result
            
            # Dosya mı kontrolü
            if not file_path_obj.is_file():
                result.add_error("Belirtilen yol bir dosya değil")
                return result
            
            # Uzantı kontrolü
            if allowed_extensions:
                file_extension = file_path_obj.suffix.lower()
                if file_extension not in [ext.lower() for ext in allowed_extensions]:
                    result.add_error(f"İzin verilmeyen dosya uzantısı: {file_extension}")
            
            # Boyut kontrolü
            file_size = file_path_obj.stat().st_size
            max_allowed_size = max_size or self.file_size_limits.get(file_type, self.file_size_limits['default'])
            
            if file_size > max_allowed_size:
                result.add_error(f"Dosya çok büyük (maksimum: {max_allowed_size / (1024*1024):.1f} MB)")
            
            # MIME type kontrolü
            if file_type and file_type in self.allowed_mime_types:
                mime_type, _ = mimetypes.guess_type(str(file_path_obj))
                if mime_type and mime_type not in self.allowed_mime_types[file_type]:
                    result.add_error(f"İzin verilmeyen dosya tipi: {mime_type}")
            
            # Boş dosya kontrolü
            if file_size == 0:
                result.add_warning("Dosya boş")
                
        except Exception as e:
            self.logger.error(f"File validation error: {e}")
            result.add_error("Dosya doğrulama sırasında hata oluştu")
        
        return result
    
    def validate_json(self, json_data: Union[str, Dict]) -> ValidationResult:
        """
        JSON verisini doğrular.
        
        Args:
            json_data: JSON verisi (string veya dict)
            
        Returns:
            Doğrulama sonucu
        """
        result = ValidationResult()
        
        try:
            if isinstance(json_data, str):
                # String ise parse et
                try:
                    json.loads(json_data)
                except json.JSONDecodeError as e:
                    result.add_error(f"Geçersiz JSON formatı: {e}")
            elif isinstance(json_data, dict):
                # Dict ise serialize et
                try:
                    json.dumps(json_data)
                except TypeError as e:
                    result.add_error(f"JSON serialize edilemedi: {e}")
            else:
                result.add_error("JSON verisi string veya dict olmalı")
                
        except Exception as e:
            self.logger.error(f"JSON validation error: {e}")
            result.add_error("JSON doğrulama sırasında hata oluştu")
        
        return result
    
    def validate_date(self, date_string: str, date_format: str = "%Y-%m-%d") -> ValidationResult:
        """
        Tarih string'ini doğrular.
        
        Args:
            date_string: Tarih string'i
            date_format: Tarih formatı
            
        Returns:
            Doğrulama sonucu
        """
        result = ValidationResult()
        
        try:
            if not date_string:
                result.add_error("Tarih boş olamaz")
                return result
            
            # Tarih parse et
            try:
                parsed_date = datetime.strptime(date_string, date_format)
                
                # Gelecek tarih kontrolü
                if parsed_date > datetime.now():
                    result.add_warning("Gelecek tarih")
                
                # Çok eski tarih kontrolü
                if parsed_date.year < 1900:
                    result.add_warning("Çok eski tarih")
                    
            except ValueError as e:
                result.add_error(f"Geçersiz tarih formatı: {e}")
                
        except Exception as e:
            self.logger.error(f"Date validation error: {e}")
            result.add_error("Tarih doğrulama sırasında hata oluştu")
        
        return result
    
    def validate_phone(self, phone: str, country_code: str = "TR") -> ValidationResult:
        """
        Telefon numarasını doğrular.
        
        Args:
            phone: Telefon numarası
            country_code: Ülke kodu
            
        Returns:
            Doğrulama sonucu
        """
        result = ValidationResult()
        
        try:
            if not phone:
                result.add_error("Telefon numarası boş olamaz")
                return result
            
            # Sadece rakam, +, -, (, ), boşluk bırak
            cleaned_phone = re.sub(r'[^\d+\-\(\)\s]', '', phone)
            
            if country_code == "TR":
                # Türkiye telefon numarası kontrolü
                if not self.patterns['phone'].match(cleaned_phone):
                    result.add_error("Geçersiz Türkiye telefon numarası formatı")
            else:
                # Genel format kontrolü
                if len(cleaned_phone) < 7 or len(cleaned_phone) > 15:
                    result.add_error("Telefon numarası 7-15 karakter arasında olmalı")
                    
        except Exception as e:
            self.logger.error(f"Phone validation error: {e}")
            result.add_error("Telefon numarası doğrulama sırasında hata oluştu")
        
        return result


# Global instance
validator = DataValidator()
