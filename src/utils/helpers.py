"""
Helpers module - Yardımcı fonksiyonlar

Bu modül uygulama genelinde kullanılan yardımcı fonksiyonları içerir.
String, dict, list işlemleri ve genel utility fonksiyonları.
"""

import os
import re
import uuid
import hashlib
import secrets
import base64
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from pathlib import Path
import json
from urllib.parse import urlparse, parse_qs
import subprocess
import platform

from .logger import logger


def generate_id(prefix: str = "", length: int = 16) -> str:
    """
    Rastgele ID oluşturur.
    
    Args:
        prefix: ID ön eki
        length: ID uzunluğu
        
    Returns:
        Oluşturulan ID
    """
    random_part = secrets.token_urlsafe(length)[:length]
    return f"{prefix}{random_part}" if prefix else random_part


def generate_uuid() -> str:
    """
    UUID oluşturur.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """
    String'i hashler.
    
    Args:
        text: Hashlenecek text
        algorithm: Hash algoritması
        
    Returns:
        Hash değeri
    """
    try:
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(text.encode('utf-8'))
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing string: {e}")
        return ""


def encode_base64(data: Union[str, bytes]) -> str:
    """
    Base64 encoding yapar.
    
    Args:
        data: Encode edilecek veri
        
    Returns:
        Base64 encoded string
    """
    try:
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.b64encode(data).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding base64: {e}")
        return ""


def decode_base64(data: str) -> bytes:
    """
    Base64 decoding yapar.
    
    Args:
        data: Decode edilecek string
        
    Returns:
        Decoded bytes
    """
    try:
        return base64.b64decode(data)
    except Exception as e:
        logger.error(f"Error decoding base64: {e}")
        return b""


def safe_cast(value: Any, target_type: type, default: Any = None) -> Any:
    """
    Güvenli tip dönüşümü yapar.
    
    Args:
        value: Dönüştürülecek değer
        target_type: Hedef tip
        default: Varsayılan değer
        
    Returns:
        Dönüştürülmüş değer veya varsayılan
    """
    try:
        if target_type == bool and isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return target_type(value)
    except (ValueError, TypeError):
        return default


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Nested dictionary'yi flatten eder.
    
    Args:
        d: Flatten edilecek dictionary
        parent_key: Ana anahtar
        sep: Ayırıcı karakter
        
    Returns:
        Flatten edilmiş dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """
    Flatten edilmiş dictionary'yi unflatten eder.
    
    Args:
        d: Unflatten edilecek dictionary
        sep: Ayırıcı karakter
        
    Returns:
        Unflatten edilmiş dictionary
    """
    result = {}
    for key, value in d.items():
        keys = key.split(sep)
        current = result
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    return result


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    İki dictionary'yi deep merge yapar.
    
    Args:
        dict1: İlk dictionary
        dict2: İkinci dictionary
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_nested_value(data: Dict[str, Any], path: str, default: Any = None, sep: str = ".") -> Any:
    """
    Nested dictionary'den path ile değer alır.
    
    Args:
        data: Veri dictionary'si
        path: Noktalı path (örn: "user.profile.name")
        default: Varsayılan değer
        sep: Ayırıcı karakter
        
    Returns:
        Bulunan değer veya varsayılan
    """
    try:
        keys = path.split(sep)
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    except Exception:
        return default


def set_nested_value(data: Dict[str, Any], path: str, value: Any, sep: str = ".") -> None:
    """
    Nested dictionary'ye path ile değer atar.
    
    Args:
        data: Veri dictionary'si
        path: Noktalı path
        value: Atanacak değer
        sep: Ayırıcı karakter
    """
    try:
        keys = path.split(sep)
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    except Exception as e:
        logger.error(f"Error setting nested value: {e}")


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Listeyi chunk'lara böler.
    
    Args:
        lst: Bölünecek liste
        chunk_size: Chunk boyutu
        
    Returns:
        Chunk'lar listesi
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates(lst: List[Any], key: Callable = None) -> List[Any]:
    """
    Listeden duplikate'leri kaldırır.
    
    Args:
        lst: Liste
        key: Karşılaştırma fonksiyonu
        
    Returns:
        Duplikate'siz liste
    """
    if key is None:
        return list(dict.fromkeys(lst))
    
    seen = set()
    result = []
    for item in lst:
        item_key = key(item)
        if item_key not in seen:
            seen.add(item_key)
            result.append(item)
    return result


def filter_dict(d: Dict[str, Any], keys: List[str], include: bool = True) -> Dict[str, Any]:
    """
    Dictionary'yi anahtar listesine göre filtreler.
    
    Args:
        d: Filtrelenecek dictionary
        keys: Anahtar listesi
        include: True ise sadece bu anahtarları içer, False ise hariç tutar
        
    Returns:
        Filtrelenmiş dictionary
    """
    if include:
        return {k: v for k, v in d.items() if k in keys}
    else:
        return {k: v for k, v in d.items() if k not in keys}


def clean_string(text: str, remove_extra_spaces: bool = True, 
                 remove_special_chars: bool = False, 
                 allowed_chars: str = None) -> str:
    """
    String'i temizler.
    
    Args:
        text: Temizlenecek string
        remove_extra_spaces: Fazla boşlukları kaldır
        remove_special_chars: Özel karakterleri kaldır
        allowed_chars: İzin verilen özel karakterler
        
    Returns:
        Temizlenmiş string
    """
    if not text:
        return ""
    
    # Trim
    text = text.strip()
    
    # Fazla boşlukları kaldır
    if remove_extra_spaces:
        text = re.sub(r'\s+', ' ', text)
    
    # Özel karakterleri kaldır
    if remove_special_chars:
        if allowed_chars:
            pattern = f'[^a-zA-Z0-9\\s{re.escape(allowed_chars)}]'
        else:
            pattern = r'[^a-zA-Z0-9\s]'
        text = re.sub(pattern, '', text)
    
    return text


def slugify(text: str, max_length: int = 50) -> str:
    """
    String'i URL-friendly slug'a çevirir.
    
    Args:
        text: Slug yapılacak string
        max_length: Maksimum uzunluk
        
    Returns:
        Slug string
    """
    if not text:
        return ""
    
    # Küçük harfe çevir
    text = text.lower()
    
    # Türkçe karakterleri değiştir
    tr_chars = {
        'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'Ç': 'c', 'Ğ': 'g', 'I': 'i', 'İ': 'i', 'Ö': 'o', 'Ş': 's', 'Ü': 'u'
    }
    for tr_char, en_char in tr_chars.items():
        text = text.replace(tr_char, en_char)
    
    # Özel karakterleri kaldır ve boşlukları tire ile değiştir
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = text.strip('-')
    
    # Uzunluk sınırla
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text


def format_bytes(bytes_value: int, decimal_places: int = 2) -> str:
    """
    Byte değerini human-readable formata çevirir.
    
    Args:
        bytes_value: Byte değeri
        decimal_places: Ondalık basamak sayısı
        
    Returns:
        Formatlanmış string
    """
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    
    while bytes_value >= 1024 and unit_index < len(units) - 1:
        bytes_value /= 1024
        unit_index += 1
    
    return f"{bytes_value:.{decimal_places}f} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """
    Saniye değerini human-readable formata çevirir.
    
    Args:
        seconds: Saniye değeri
        
    Returns:
        Formatlanmış string
    """
    if seconds < 0:
        return "0s"
    
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def parse_url(url: str) -> Dict[str, Any]:
    """
    URL'yi parse eder.
    
    Args:
        url: Parse edilecek URL
        
    Returns:
        URL bileşenleri
    """
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        return {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "hostname": parsed.hostname,
            "port": parsed.port,
            "path": parsed.path,
            "query": parsed.query,
            "query_params": query_params,
            "fragment": parsed.fragment
        }
    except Exception as e:
        logger.error(f"Error parsing URL {url}: {e}")
        return {}


def is_valid_json(json_str: str) -> bool:
    """
    String'in geçerli JSON olup olmadığını kontrol eder.
    
    Args:
        json_str: Kontrol edilecek string
        
    Returns:
        True if valid JSON, False otherwise
    """
    try:
        json.loads(json_str)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    String'i belirtilen uzunlukta keser.
    
    Args:
        text: Kesilecek string
        max_length: Maksimum uzunluk
        suffix: Kesim sonrası eklenen suffix
        
    Returns:
        Kesilmiş string
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def mask_sensitive_data(text: str, mask_char: str = "*", 
                       start_chars: int = 2, end_chars: int = 2) -> str:
    """
    Hassas veriyi maskeler.
    
    Args:
        text: Maskelenecek text
        mask_char: Maskeleme karakteri
        start_chars: Başlangıçta gösterilecek karakter sayısı
        end_chars: Sonda gösterilecek karakter sayısı
        
    Returns:
        Maskelenmiş string
    """
    if not text or len(text) <= start_chars + end_chars:
        return mask_char * len(text) if text else ""
    
    start = text[:start_chars]
    end = text[-end_chars:] if end_chars > 0 else ""
    middle_length = len(text) - start_chars - end_chars
    middle = mask_char * middle_length
    
    return start + middle + end


def get_system_info() -> Dict[str, Any]:
    """
    Sistem bilgilerini alır.
    
    Returns:
        Sistem bilgileri
    """
    try:
        return {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {}


def run_command(command: str, cwd: str = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Sistem komutu çalıştırır.
    
    Args:
        command: Çalıştırılacak komut
        cwd: Çalışma dizini
        timeout: Timeout (saniye)
        
    Returns:
        Komut sonucu
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out"
        }
    except Exception as e:
        logger.error(f"Error running command {command}: {e}")
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e)
        }


def ensure_directory(directory: Union[str, Path]) -> bool:
    """
    Dizinin var olduğundan emin olur, yoksa oluşturur.
    
    Args:
        directory: Dizin yolu
        
    Returns:
        True if successful, False otherwise
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        return False


def get_file_extension(filename: str) -> str:
    """
    Dosya uzantısını alır.
    
    Args:
        filename: Dosya adı
        
    Returns:
        Dosya uzantısı (nokta ile)
    """
    return Path(filename).suffix.lower()


def is_file_older_than(file_path: Union[str, Path], days: int) -> bool:
    """
    Dosyanın belirtilen günden eski olup olmadığını kontrol eder.
    
    Args:
        file_path: Dosya yolu
        days: Gün sayısı
        
    Returns:
        True if file is older, False otherwise
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            return False
        
        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        threshold_time = datetime.now() - timedelta(days=days)
        
        return file_time < threshold_time
    except Exception as e:
        logger.error(f"Error checking file age {file_path}: {e}")
        return False


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Dosya adını güvenli hale getirir.
    
    Args:
        filename: Dosya adı
        replacement: Geçersiz karakterlerin yerine konacak karakter
        
    Returns:
        Güvenli dosya adı
    """
    # Windows ve Unix'te geçersiz karakterler
    invalid_chars = r'<>:"/\|?*'
    
    # Geçersiz karakterleri değiştir
    for char in invalid_chars:
        filename = filename.replace(char, replacement)
    
    # Rezerve dosya adları (Windows)
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_without_ext = Path(filename).stem
    if name_without_ext.upper() in reserved_names:
        filename = f"{replacement}{filename}"
    
    # Boşlukları temizle
    filename = filename.strip()
    
    # Nokta ile bitmesin
    filename = filename.rstrip('.')
    
    return filename or "untitled"


def retry_on_failure(func: Callable, max_retries: int = 3, delay: float = 1.0) -> Any:
    """
    Fonksiyonu hata durumunda tekrar dener.
    
    Args:
        func: Çalıştırılacak fonksiyon
        max_retries: Maksimum deneme sayısı
        delay: Denemeler arası gecikme
        
    Returns:
        Fonksiyon sonucu
    """
    import time
    
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed")
    
    raise last_exception
