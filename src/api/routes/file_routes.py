"""
File Routes module - File operations endpoint'leri

Bu modül dosya işlemleri ile ilgili API endpoint'lerini içerir.
"""

import os
import uuid
import time
from typing import Dict, Any, List
from aiohttp import web
from aiohttp.web import Request, Response
from aiohttp.web_request import FileField

from .base_routes import BaseRoutes
from ...core.constants import API_PREFIX, SUCCESS_MESSAGES, ERROR_MESSAGES
from ...utils.logger import Logger


class FileRoutes(BaseRoutes):
    """File routes sınıfı"""
    
    def __init__(self):
        """FileRoutes'ı başlat"""
        super().__init__()
        self.logger = Logger(__name__)
        self.upload_dir = "uploads"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {'.txt', '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif'}
        
        # Upload dizinini oluştur
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
    
    def get_routes(self) -> list[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.get(f"{API_PREFIX}/files", self.get_files),
            web.post(f"{API_PREFIX}/files/upload", self.upload_file),
            web.get(f"{API_PREFIX}/files/{{file_id}}", self.get_file),
            web.delete(f"{API_PREFIX}/files/{{file_id}}", self.delete_file),
            web.get(f"{API_PREFIX}/files/{{file_id}}/download", self.download_file),
            web.get(f"{API_PREFIX}/files/stats", self.get_file_stats),
            web.post(f"{API_PREFIX}/files/{{file_id}}/share", self.share_file),
            web.get(f"{API_PREFIX}/files/shared/{{share_token}}", self.get_shared_file),
        ]
    
    async def get_files(self, request: Request) -> Response:
        """Dosya listesi"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Query parametrelerini al
            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', 20))
            search = request.query.get('search', '')
            file_type = request.query.get('type', '')
            
            # Sayfalama için offset hesapla
            offset = (page - 1) * limit
            
            # Dosya listesini al
            files = self._get_file_list()
            
            # Filtreleri uygula
            if search:
                files = [f for f in files if search.lower() in f['name'].lower()]
            
            if file_type:
                files = [f for f in files if f['type'] == file_type]
            
            # Toplam sayıyı al
            total_count = len(files)
            
            # Sayfalama uygula
            paginated_files = files[offset:offset + limit]
            
            response_data = {
                "files": paginated_files,
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                    "pages": (total_count + limit - 1) // limit
                }
            }
            
            return self.create_success_response(
                message="Dosya listesi alındı",
                data=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Dosya listesi alınamadı: {e}")
            return self.create_error_response(
                message="Dosya listesi alınamadı",
                status_code=500
            )
    
    async def upload_file(self, request: Request) -> Response:
        """Dosya upload"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Multipart form data'yı parse et
            reader = await request.multipart()
            
            file_field = None
            while True:
                part = await reader.next()
                if part is None:
                    break
                
                if part.name == 'file':
                    file_field = part
                    break
            
            if not file_field:
                return self.create_error_response(
                    message="Dosya bulunamadı",
                    status_code=400
                )
            
            # Dosya bilgilerini al
            filename = file_field.filename
            if not filename:
                return self.create_error_response(
                    message="Dosya adı bulunamadı",
                    status_code=400
                )
            
            # Dosya uzantısını kontrol et
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in self.allowed_extensions:
                return self.create_error_response(
                    message=f"Desteklenmeyen dosya türü: {file_ext}",
                    status_code=400
                )
            
            # Dosya boyutunu kontrol et
            file_size = 0
            content = b''
            while True:
                chunk = await file_field.read_chunk()
                if not chunk:
                    break
                content += chunk
                file_size += len(chunk)
                
                if file_size > self.max_file_size:
                    return self.create_error_response(
                        message=f"Dosya boyutu çok büyük. Maksimum: {self.max_file_size // (1024*1024)}MB",
                        status_code=400
                    )
            
            # Benzersiz dosya adı oluştur
            file_id = str(uuid.uuid4())
            safe_filename = f"{file_id}_{filename}"
            file_path = os.path.join(self.upload_dir, safe_filename)
            
            # Dosyayı kaydet
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Dosya bilgilerini kaydet
            file_info = {
                "id": file_id,
                "name": filename,
                "size": file_size,
                "type": file_ext,
                "path": file_path,
                "uploaded_by": user_id,
                "uploaded_at": time.time(),
                "download_count": 0
            }
            
            # Log yaz
            self.logger.log_user_action(
                "file_upload",
                user_id,
                f"Dosya yüklendi: {filename}",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message="Dosya başarıyla yüklendi",
                data=file_info
            )
            
        except Exception as e:
            self.logger.error(f"Dosya yükleme hatası: {e}")
            return self.create_error_response(
                message="Dosya yüklenemedi",
                status_code=500
            )
    
    async def get_file(self, request: Request) -> Response:
        """Dosya bilgilerini al"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            file_id = request.match_info['file_id']
            
            # Dosya bilgilerini al
            file_info = self._get_file_info(file_id)
            
            if not file_info:
                return self.create_error_response(
                    message="Dosya bulunamadı",
                    status_code=404
                )
            
            return self.create_success_response(
                message="Dosya bilgileri alındı",
                data=file_info
            )
            
        except Exception as e:
            self.logger.error(f"Dosya bilgileri alınamadı: {e}")
            return self.create_error_response(
                message="Dosya bilgileri alınamadı",
                status_code=500
            )
    
    async def delete_file(self, request: Request) -> Response:
        """Dosya sil"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            file_id = request.match_info['file_id']
            
            # Dosya bilgilerini al
            file_info = self._get_file_info(file_id)
            
            if not file_info:
                return self.create_error_response(
                    message="Dosya bulunamadı",
                    status_code=404
                )
            
            # Dosyayı sil
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])
            
            # Log yaz
            self.logger.log_user_action(
                "file_delete",
                user_id,
                f"Dosya silindi: {file_info['name']}",
                ip_address=self._get_client_ip(request)
            )
            
            return self.create_success_response(
                message="Dosya başarıyla silindi"
            )
            
        except Exception as e:
            self.logger.error(f"Dosya silme hatası: {e}")
            return self.create_error_response(
                message="Dosya silinemedi",
                status_code=500
            )
    
    async def download_file(self, request: Request) -> Response:
        """Dosya indir"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            file_id = request.match_info['file_id']
            
            # Dosya bilgilerini al
            file_info = self._get_file_info(file_id)
            
            if not file_info:
                return self.create_error_response(
                    message="Dosya bulunamadı",
                    status_code=404
                )
            
            # Dosya var mı kontrol et
            if not os.path.exists(file_info['path']):
                return self.create_error_response(
                    message="Dosya bulunamadı",
                    status_code=404
                )
            
            # Download sayısını artır
            self._increment_download_count(file_id)
            
            # Log yaz
            self.logger.log_user_action(
                "file_download",
                user_id,
                f"Dosya indirildi: {file_info['name']}",
                ip_address=self._get_client_ip(request)
            )
            
            # Dosyayı döndür
            return web.FileResponse(
                path=file_info['path'],
                headers={
                    'Content-Disposition': f'attachment; filename="{file_info["name"]}"'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Dosya indirme hatası: {e}")
            return self.create_error_response(
                message="Dosya indirilemedi",
                status_code=500
            )
    
    def _get_file_list(self) -> List[Dict[str, Any]]:
        """Dosya listesini al"""
        files = []
        
        if os.path.exists(self.upload_dir):
            for filename in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, filename)
                if os.path.isfile(file_path):
                    # Dosya bilgilerini al
                    stat = os.stat(file_path)
                    file_id = filename.split('_')[0]
                    
                    file_info = {
                        "id": file_id,
                        "name": '_'.join(filename.split('_')[1:]) if '_' in filename else filename,
                        "size": stat.st_size,
                        "type": os.path.splitext(filename)[1].lower(),
                        "uploaded_at": stat.st_ctime,
                        "modified_at": stat.st_mtime,
                        "download_count": 0  # Bu bilgi ayrı bir dosyada saklanabilir
                    }
                    files.append(file_info)
        
        return files
    
    def _get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Dosya bilgilerini al"""
        files = self._get_file_list()
        for file_info in files:
            if file_info['id'] == file_id:
                file_info['path'] = os.path.join(self.upload_dir, f"{file_id}_{file_info['name']}")
                return file_info
        return None
    
    def _increment_download_count(self, file_id: str):
        """Download sayısını artır"""
        # Bu bilgi ayrı bir dosyada saklanabilir
        pass
    
    def _get_client_ip(self, request: Request) -> str:
        """Client IP adresini al"""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote
    
    async def get_file_stats(self, request: Request) -> Response:
        """Dosya istatistikleri"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            # Dosya listesini al
            files = self._get_file_list()
            
            # İstatistikleri hesapla
            total_files = len(files)
            total_size = sum(f['size'] for f in files)
            
            # Dosya türü dağılımı
            file_types = {}
            for file_info in files:
                file_type = file_info['type']
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # En büyük dosyalar
            largest_files = sorted(files, key=lambda x: x['size'], reverse=True)[:5]
            
            # Son yüklenen dosyalar
            recent_files = sorted(files, key=lambda x: x['uploaded_at'], reverse=True)[:5]
            
            stats = {
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "largest_files": [
                    {
                        "name": f['name'],
                        "size": f['size'],
                        "size_mb": round(f['size'] / (1024 * 1024), 2),
                        "type": f['type']
                    } for f in largest_files
                ],
                "recent_files": [
                    {
                        "name": f['name'],
                        "uploaded_at": f['uploaded_at'],
                        "size": f['size'],
                        "type": f['type']
                    } for f in recent_files
                ]
            }
            
            return self.create_success_response(
                message="Dosya istatistikleri alındı",
                data=stats
            )
            
        except Exception as e:
            self.logger.error(f"Dosya istatistikleri alınamadı: {e}")
            return self.create_error_response(
                message="Dosya istatistikleri alınamadı",
                status_code=500
            )
    
    async def share_file(self, request: Request) -> Response:
        """Dosyayı paylaş"""
        try:
            # Kullanıcıyı kontrol et
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return self.create_error_response(
                    message="Authentication gerekli",
                    status_code=401
                )
            
            file_id = request.match_info['file_id']
            
            # Dosya bilgilerini al
            file_info = self._get_file_info(file_id)
            
            if not file_info:
                return self.create_error_response(
                    message="Dosya bulunamadı",
                    status_code=404
                )
            
            # Paylaşım token'ı oluştur
            import hashlib
            share_token = hashlib.md5(f"{file_id}_{user_id}_{time.time()}".encode()).hexdigest()
            
            # Paylaşım bilgilerini kaydet (gerçek uygulamada veritabanında saklanır)
            share_info = {
                "file_id": file_id,
                "shared_by": user_id,
                "share_token": share_token,
                "created_at": time.time(),
                "expires_at": time.time() + (7 * 24 * 3600),  # 7 gün
                "download_count": 0,
                "max_downloads": 100
            }
            
            # Paylaşım URL'ini oluştur
            share_url = f"/api/v1/files/shared/{share_token}"
            
            return self.create_success_response(
                message="Dosya başarıyla paylaşıldı",
                data={
                    "share_token": share_token,
                    "share_url": share_url,
                    "expires_at": share_info['expires_at'],
                    "max_downloads": share_info['max_downloads']
                }
            )
            
        except Exception as e:
            self.logger.error(f"Dosya paylaşma hatası: {e}")
            return self.create_error_response(
                message="Dosya paylaşılamadı",
                status_code=500
            )
    
    async def get_shared_file(self, request: Request) -> Response:
        """Paylaşılan dosyayı al"""
        try:
            share_token = request.match_info['share_token']
            
            # Paylaşım bilgilerini al (gerçek uygulamada veritabanından alınır)
            # Şimdilik basit bir kontrol yapıyoruz
            if not share_token or len(share_token) != 32:
                return self.create_error_response(
                    message="Geçersiz paylaşım token'ı",
                    status_code=400
                )
            
            # Token'dan dosya ID'sini çıkar (basit implementasyon)
            # Gerçek uygulamada veritabanından alınır
            file_id = share_token[:8]  # Basit örnek
            
            # Dosya bilgilerini al
            file_info = self._get_file_info(file_id)
            
            if not file_info:
                return self.create_error_response(
                    message="Paylaşılan dosya bulunamadı",
                    status_code=404
                )
            
            # Dosya var mı kontrol et
            if not os.path.exists(file_info['path']):
                return self.create_error_response(
                    message="Dosya bulunamadı",
                    status_code=404
                )
            
            # Download sayısını artır
            self._increment_download_count(file_id)
            
            # Dosyayı döndür
            return web.FileResponse(
                path=file_info['path'],
                headers={
                    'Content-Disposition': f'attachment; filename="{file_info["name"]}"'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Paylaşılan dosya alınamadı: {e}")
            return self.create_error_response(
                message="Paylaşılan dosya alınamadı",
                status_code=500
            )
