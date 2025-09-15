#!/usr/bin/env python3
"""
Dependency checker - Mevcut modülleri kontrol eder
"""

import sys
import importlib
from pathlib import Path

def check_module(module_name, alternative_names=None):
    """Modül varlığını kontrol et"""
    names_to_try = [module_name] + (alternative_names or [])
    
    for name in names_to_try:
        try:
            importlib.import_module(name)
            return True, name
        except ImportError:
            continue
    
    return False, None

def main():
    """Ana fonksiyon"""
    print("🔍 Python Modül Kontrol Raporu")
    print("=" * 50)
    
    # Kontrol edilecek modüller
    modules_to_check = [
        ("asyncio", []),
        ("json", []),
        ("sqlite3", []),
        ("threading", []),
        ("logging", []),
        ("pathlib", []),
        ("datetime", []),
        ("uuid", []),
        ("hashlib", []),
        ("base64", []),
        ("re", []),
        ("os", []),
        ("sys", []),
        ("time", []),
        ("socket", []),
        ("http.server", ["http"]),
        ("urllib.parse", ["urllib"]),
        # Opsiyonel modüller
        ("tkinter", ["Tkinter"]),  # GUI alternatifi
        ("http.server", []),
    ]
    
    available_modules = []
    missing_modules = []
    
    for module_name, alternatives in modules_to_check:
        available, found_name = check_module(module_name, alternatives)
        if available:
            available_modules.append(found_name or module_name)
            print(f"✅ {found_name or module_name}")
        else:
            missing_modules.append(module_name)
            print(f"❌ {module_name}")
    
    print(f"\n📊 Özet:")
    print(f"✅ Mevcut modüller: {len(available_modules)}")
    print(f"❌ Eksik modüller: {len(missing_modules)}")
    
    if missing_modules:
        print(f"\n❌ Eksik modüller:")
        for module in missing_modules:
            print(f"   - {module}")
    
    # Minimal çalışabilirlik kontrolü
    critical_modules = ["asyncio", "json", "sqlite3", "threading", "logging"]
    critical_available = [m for m in critical_modules if m in available_modules]
    
    print(f"\n🎯 Kritik modüller: {len(critical_available)}/{len(critical_modules)}")
    
    if len(critical_available) >= 4:
        print("✅ Minimal çalışabilir durumda!")
        return True
    else:
        print("❌ Kritik modüller eksik, çalışmayabilir!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)