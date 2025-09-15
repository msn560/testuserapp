"""
API Server Management System

Modern, güvenli ve ölçeklenebilir API Server Management System.
Kullanıcıların hem masaüstü GUI üzerinden hem de REST API aracılığıyla
server yönetimi, kullanıcı yönetimi, sistem izleme ve yapılandırma
işlemlerini gerçekleştirebileceği profesyonel bir uygulama.

Author: API Server Manager Team
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "API Server Manager Team"
__email__ = "support@apiservermanager.com"
__license__ = "MIT"

# Core imports
from .app import APIServerManagerApp

__all__ = [
    "APIServerManagerApp",
    "__version__",
    "__author__",
    "__email__",
    "__license__"
]
