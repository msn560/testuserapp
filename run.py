#!/usr/bin/env python3
"""
API Server Management System - Ana başlatıcı

Bu dosya uygulamanın ana giriş noktasıdır.
Uygulamayı başlatır ve gerekli kontrolleri yapar.
"""

import sys
import os
from pathlib import Path

# Proje kök dizinini Python path'ine ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# src dizinini Python path'ine ekle
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Gerekli dizinleri oluştur
def create_required_directories():
    """Gerekli dizinleri oluştur"""
    directories = [
        "data",
        "data/backup",
        "data/cache", 
        "data/logs",
        "data/certificates",
        "data/locale",
        "data/resources",
        "data/resources/icons",
        "data/resources/icons/tabs",
        "data/resources/icons/actions", 
        "data/resources/icons/status",
        "data/resources/images",
        "data/resources/styles",
        "data/resources/styles/themes",
        "data/resources/styles/components"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)

def check_dependencies():
    """Gerekli bağımlılıkları kontrol et"""
    required_packages = [
        "PyQt5",
        "aiohttp", 
        "peewee",
        "jwt",      # <-- PyJWT için doğru import adı
        "bcrypt",
        "psutil"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Eksik bağımlılıklar:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Bağımlılıkları yüklemek için:")
        print("   pip install -r requirements.txt")
        return False
    
    return True


def check_python_version():
    """Python sürümünü kontrol et"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 veya üzeri gerekli")
        print(f"   Mevcut sürüm: {sys.version}")
        return False
    
    return True

def main():
    """Ana fonksiyon"""
    print("🚀 API Server Management System")
    print("=" * 50)
    
    # Python sürümünü kontrol et
    if not check_python_version():
        return 1
    
    # Gerekli dizinleri oluştur
    print("📁 Dizinler kontrol ediliyor...")
    create_required_directories()
    
    # Bağımlılıkları kontrol et
    print("📦 Bağımlılıklar kontrol ediliyor...")
    if not check_dependencies():
        return 1
    
    print("✅ Tüm kontroller başarılı")
    print("🎯 Uygulama başlatılıyor...\n")
    
    try:
        # Uygulamayı başlat
        from src.app import main as app_main
        return app_main()
        
    except ImportError as e:
        print(f"❌ Import hatası: {e}")
        print("   Lütfen tüm bağımlılıkların yüklü olduğundan emin olun")
        return 1
    except Exception as e:
        print(f"❌ Uygulama hatası: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
