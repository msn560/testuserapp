"""
Language module - Dil yönetimi

Bu modül uygulamanın çoklu dil desteğini yönetir.
Dil dosyalarını yükleme, çeviri alma ve dil değiştirme işlemleri.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
import threading

from .constants import LogLevel
from ..utils.logger import logger


class SupportedLanguage(Enum):
    """Desteklenen diller."""
    TURKISH = "tr"
    ENGLISH = "en"
    GERMAN = "de"
    FRENCH = "fr"


class LanguageManager:
    """
    Dil yönetimi sınıfı.
    
    Bu sınıf çoklu dil desteği, çeviri yönetimi ve dil değiştirme işlemlerini sağlar.
    """
    
    def __init__(self, locale_dir: str = "data/locale", default_language: SupportedLanguage = None):
        """
        LanguageManager'ı başlatır.
        
        Args:
            locale_dir: Dil dosyalarının bulunduğu dizin
            default_language: Varsayılan dil (None ise config'den alınır)
        """
        self.logger = logger
        self.locale_dir = Path(locale_dir)
        
        # Config'den dil ayarını al
        if default_language is None:
            try:
                from .config_manager import config_manager
                config = config_manager.load_config()
                ui_config = config.get('ui', {})
                lang_code = ui_config.get('language', 'tr')
                self.default_language = SupportedLanguage(lang_code)
            except Exception as e:
                self.logger.warning(f"Failed to load language from config: {e}")
                self.default_language = SupportedLanguage.TURKISH
        else:
            self.default_language = default_language
            
        self.current_language = self.default_language
        
        # Dil çevirileri cache
        self.translations: Dict[str, Dict[str, str]] = {}
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Dil değişikliği callback'leri
        self.language_change_callbacks: List[callable] = []
        
        # Mevcut dil dosyalarını yükle
        self._load_available_languages()
        
        # Varsayılan dili yükle
        self._load_language(self.current_language)
    
    def get_available_languages(self) -> List[Dict[str, Any]]:
        """
        Mevcut dilleri döndürür.
        
        Returns:
            Mevcut dil listesi
        """
        try:
            languages = []
            for lang in SupportedLanguage:
                languages.append({
                    "code": lang.value,
                    "name": self._get_language_name(lang),
                    "native_name": self._get_native_name(lang),
                    "is_loaded": lang.value in self.translations
                })
            return languages
            
        except Exception as e:
            self.logger.error(f"Failed to get available languages: {e}")
            return []
    
    def set_language(self, language_code: str) -> bool:
        """
        Aktif dili değiştirir.
        
        Args:
            language_code: Dil kodu (tr, en, de, fr)
            
        Returns:
            True if language changed successfully, False otherwise
        """
        try:
            # Dil kodunu enum'a dönüştür
            try:
                new_language = SupportedLanguage(language_code)
            except ValueError:
                self.logger.warning(f"Unsupported language code: {language_code}")
                return False
            
            with self.lock:
                # Dil dosyasını yükle
                if not self._load_language(new_language):
                    return False
                
                # Aktif dili güncelle
                old_language = self.current_language
                self.current_language = new_language
                
                # Config dosyasını güncelle
                self._update_config_language(language_code)
                
                # Callback'leri çağır
                for callback in self.language_change_callbacks:
                    try:
                        callback(old_language.value, new_language.value)
                    except Exception as e:
                        self.logger.error(f"Error in language change callback: {e}")
                
                self.logger.info(f"Language changed from {old_language.value} to {new_language.value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to set language: {e}")
            return False
    
    def _update_config_language(self, language_code: str):
        """
        Config dosyasındaki dil ayarını günceller.
        
        Args:
            language_code: Yeni dil kodu
        """
        try:
            from .config_manager import config_manager
            config = config_manager.load_config()
            config['ui']['language'] = language_code
            config_manager.save_config(config)
            self.logger.info(f"Config language updated to: {language_code}")
        except Exception as e:
            self.logger.error(f"Failed to update config language: {e}")
    
    def translate(self, key: str, **kwargs) -> str:
        """
        Çeviri anahtarından çeviri metnini döndürür.
        
        Args:
            key: Çeviri anahtarı (örn: "user.login.title")
            **kwargs: Çeviri metnindeki değişkenler
            
        Returns:
            Çevrilmiş metin
        """
        return self.get_translation(key, **kwargs)
    
    def get_translation(self, key: str, **kwargs) -> str:
        """
        Çeviri anahtarından çeviri metnini döndürür.
        
        Args:
            key: Çeviri anahtarı (örn: "user.login.title")
            **kwargs: Çeviri metnindeki değişkenler
            
        Returns:
            Çevrilmiş metin
        """
        try:
            with self.lock:
                # Önce mevcut dilden çevir
                translation = self._get_translation_from_language(self.current_language, key)
                
                # Mevcut dilde bulunamazsa varsayılan dilden çevir
                if not translation and self.current_language != self.default_language:
                    translation = self._get_translation_from_language(self.default_language, key)
                
                # Hala bulunamazsa anahtarı döndür
                if not translation:
                    self.logger.warning(f"Translation not found for key: {key}")
                    return key
                
                # Değişkenleri değiştir
                try:
                    return translation.format(**kwargs)
                except (KeyError, ValueError) as e:
                    self.logger.warning(f"Error formatting translation for key '{key}': {e}")
                    return translation
                
        except Exception as e:
            self.logger.error(f"Failed to get translation for key '{key}': {e}")
            return key
    
    def get_current_language(self) -> str:
        """
        Mevcut dili döndürür.
        
        Returns:
            Mevcut dil kodu
        """
        return self.current_language.value
    
    def get_current_language_info(self) -> Dict[str, str]:
        """
        Mevcut dil bilgilerini döndürür.
        
        Returns:
            Mevcut dil bilgileri
        """
        try:
            return {
                "code": self.current_language.value,
                "name": self._get_language_name(self.current_language),
                "native_name": self._get_native_name(self.current_language),
                "is_default": self.current_language == self.default_language
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get current language info: {e}")
            return {}
    
    def add_language_change_callback(self, callback: callable):
        """
        Dil değişikliği callback'i ekler.
        
        Args:
            callback: Dil değiştiğinde çağrılacak fonksiyon
        """
        self.language_change_callbacks.append(callback)
    
    def remove_language_change_callback(self, callback: callable):
        """
        Dil değişikliği callback'ini kaldırır.
        
        Args:
            callback: Kaldırılacak callback fonksiyonu
        """
        if callback in self.language_change_callbacks:
            self.language_change_callbacks.remove(callback)
    
    def reload_language(self, language_code: str) -> bool:
        """
        Dil dosyasını yeniden yükler.
        
        Args:
            language_code: Yeniden yüklenecek dil kodu
            
        Returns:
            True if reloaded successfully, False otherwise
        """
        try:
            language = SupportedLanguage(language_code)
            return self._load_language(language, force_reload=True)
            
        except ValueError:
            self.logger.warning(f"Unsupported language code for reload: {language_code}")
            return False
    
    def reload_all_languages(self) -> Dict[str, bool]:
        """
        Tüm dil dosyalarını yeniden yükler.
        
        Returns:
            Her dil için yükleme sonucu
        """
        try:
            results = {}
            for language in SupportedLanguage:
                results[language.value] = self._load_language(language, force_reload=True)
            
            self.logger.info(f"Reloaded {sum(results.values())} language files")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to reload all languages: {e}")
            return {}
    
    def get_translation_statistics(self) -> Dict[str, Any]:
        """
        Çeviri istatistiklerini döndürür.
        
        Returns:
            Çeviri istatistikleri
        """
        try:
            stats = {
                "current_language": self.current_language.value,
                "default_language": self.default_language.value,
                "available_languages": len(SupportedLanguage),
                "loaded_languages": len(self.translations),
                "total_translations": 0,
                "language_details": {}
            }
            
            for lang_code, translations in self.translations.items():
                stats["language_details"][lang_code] = {
                    "translation_count": len(translations),
                    "is_loaded": True
                }
                stats["total_translations"] += len(translations)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get translation statistics: {e}")
            return {}
    
    def _load_available_languages(self):
        """Mevcut dil dosyalarını kontrol eder."""
        try:
            if not self.locale_dir.exists():
                self.logger.warning(f"Locale directory not found: {self.locale_dir}")
                return
            
            # Dil dosyalarının varlığını kontrol et
            for language in SupportedLanguage:
                lang_file = self.locale_dir / f"{language.value}.json"
                if not lang_file.exists():
                    self.logger.warning(f"Language file not found: {lang_file}")
                    # Varsayılan dil dosyasını oluştur
                    self._create_default_language_file(language)
                    
        except Exception as e:
            self.logger.error(f"Failed to load available languages: {e}")
    
    def _load_language(self, language: SupportedLanguage, force_reload: bool = False) -> bool:
        """
        Dil dosyasını yükler.
        
        Args:
            language: Yüklenecek dil
            force_reload: Zorla yeniden yükleme
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            lang_file = self.locale_dir / f"{language.value}.json"
            
            if not lang_file.exists():
                self.logger.error(f"Language file not found: {lang_file}")
                return False
            
            # Zaten yüklü mü kontrol et
            if language.value in self.translations and not force_reload:
                return True
            
            # Dosyayı oku
            with open(lang_file, 'r', encoding='utf-8') as f:
                translations = json.load(f)
            
            # Cache'e ekle
            self.translations[language.value] = translations
            
            self.logger.info(f"Loaded language file: {language.value} ({len(translations)} translations)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load language file {language.value}: {e}")
            return False
    
    def _get_translation_from_language(self, language: SupportedLanguage, key: str) -> Optional[str]:
        """
        Belirli bir dilden çeviri alır.
        
        Args:
            language: Dil
            key: Çeviri anahtarı
            
        Returns:
            Çeviri metni veya None
        """
        try:
            translations = self.translations.get(language.value, {})
            
            # Noktalı anahtar desteği (örn: "user.login.title")
            keys = key.split('.')
            current = translations
            
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return None
            
            return current if isinstance(current, str) else None
            
        except Exception as e:
            self.logger.error(f"Failed to get translation from language {language.value} for key '{key}': {e}")
            return None
    
    def _get_language_name(self, language: SupportedLanguage) -> str:
        """
        Dil adını döndürür.
        
        Args:
            language: Dil enum'u
            
        Returns:
            Dil adı
        """
        language_names = {
            SupportedLanguage.TURKISH: "Turkish",
            SupportedLanguage.ENGLISH: "English", 
            SupportedLanguage.GERMAN: "German",
            SupportedLanguage.FRENCH: "French"
        }
        return language_names.get(language, language.value)
    
    def _get_native_name(self, language: SupportedLanguage) -> str:
        """
        Yerel dil adını döndürür.
        
        Args:
            language: Dil enum'u
            
        Returns:
            Yerel dil adı
        """
        native_names = {
            SupportedLanguage.TURKISH: "Türkçe",
            SupportedLanguage.ENGLISH: "English",
            SupportedLanguage.GERMAN: "Deutsch", 
            SupportedLanguage.FRENCH: "Français"
        }
        return native_names.get(language, language.value)
    
    def _create_default_language_file(self, language: SupportedLanguage):
        """
        Varsayılan dil dosyasını oluşturur.
        
        Args:
            language: Oluşturulacak dil
        """
        try:
            default_translations = {
                "app": {
                    "name": "API Server Manager",
                    "version": "1.0.0",
                    "description": "API Server Management System"
                },
                "common": {
                    "ok": "OK",
                    "cancel": "Cancel",
                    "save": "Save",
                    "delete": "Delete",
                    "edit": "Edit",
                    "add": "Add",
                    "search": "Search",
                    "filter": "Filter",
                    "refresh": "Refresh",
                    "loading": "Loading...",
                    "error": "Error",
                    "success": "Success",
                    "warning": "Warning",
                    "info": "Information"
                },
                "navigation": {
                    "dashboard": "Dashboard",
                    "server": "Server",
                    "users": "Users",
                    "api": "API",
                    "monitor": "Monitor",
                    "logs": "Logs",
                    "settings": "Settings",
                    "about": "About"
                },
                "auth": {
                    "login": "Login",
                    "logout": "Logout",
                    "username": "Username",
                    "password": "Password",
                    "remember_me": "Remember Me",
                    "forgot_password": "Forgot Password?",
                    "invalid_credentials": "Invalid username or password",
                    "login_success": "Login successful",
                    "logout_success": "Logout successful"
                },
                "server": {
                    "start": "Start Server",
                    "stop": "Stop Server", 
                    "restart": "Restart Server",
                    "status": "Server Status",
                    "online": "Online",
                    "offline": "Offline",
                    "port": "Port",
                    "host": "Host"
                }
            }
            
            lang_file = self.locale_dir / f"{language.value}.json"
            
            # Dil dosyasını oluştur
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump(default_translations, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Created default language file: {language.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to create default language file for {language.value}: {e}")


# Global instance
language_manager = LanguageManager()
