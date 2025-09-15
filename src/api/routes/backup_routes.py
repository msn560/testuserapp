"""
Backup Routes module - Backup management endpoint'leri

Bu modül yedekleme yönetimi ile ilgili API endpoint'lerini içerir.
"""

import json
import os
import time
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from aiohttp import web
from aiohttp.web import Request, Response

from .base_routes import BaseRoutes
from ...core.constants import API_PREFIX, SUCCESS_MESSAGES, ERROR_MESSAGES
from ...utils.logger import Logger


class BackupRoutes(BaseRoutes):
    """Backup routes sınıfı"""
    
    def __init__(self):
        """BackupRoutes'ı başlat"""
        super().__init__()
        self.logger = Logger(__name__)
        self.backup_dir = "backups"
        
        # Backup dizinini oluştur
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def get_routes(self) -> list[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.get(f"{API_PREFIX}/backups", self.get_backups),
            web.post(f"{API_PREFIX}/backups", self.create_backup),
            web.get(f"{API_PREFIX}/backups/{{backup_id}}", self.get_backup),
            web.delete(f"{API_PREFIX}/backups/{{backup_id}}", self.delete_backup),
            web.post(f"{API_PREFIX}/backups/{{backup_id}}/restore", self.restore_backup),
            web.get(f"{API_PREFIX}/backups/{{backup_id}}/download", self.download_backup),
        ]
    
    async def get_backups(self, request: Request) -> Response:
        """Yedek listesi"""
        try:
            # Query parametrelerini al
            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', 20))
            backup_type = request.query.get('type', '')
            
            # Sayfalama için offset hesapla
            offset = (page - 1) * limit
            
            # Yedek dosyalarını al
            backups = self._get_backup_list()
            
            # Filtreleme
            if backup_type:
                backups = [b for b in backups if b['type'] == backup_type]
            
            # Toplam sayıyı al
            total = len(backups)
            
            # Sayfalama uygula
            paginated_backups = backups[offset:offset + limit]
            
            # Sayfalama bilgisi
            pagination = {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
            
            return self.create_success_response(
                data={
                    "backups": paginated_backups,
                    "pagination": pagination
                },
                message="Yedek listesi başarıyla alındı"
            )
            
        except Exception as e:
            self.logger.error(f"Yedek listesi hatası: {e}")
            return self.create_error_response(
                message="Yedek listesi alınamadı",
                status_code=500
            )
    
    async def create_backup(self, request: Request) -> Response:
        """Yeni yedek oluştur"""
        try:
            # Request body'yi al
            data = await request.json()
            
            backup_type = data.get('type', 'full')
            description = data.get('description', '')
            
            # Geçerli yedek türlerini kontrol et
            valid_types = ['full', 'database', 'files', 'config']
            if backup_type not in valid_types:
                return self.create_error_response(
                    message=f"Geçersiz yedek türü. Geçerli türler: {', '.join(valid_types)}",
                    status_code=400
                )
            
            # Yedek ID oluştur
            backup_id = f"backup_{int(time.time())}"
            backup_filename = f"{backup_id}_{backup_type}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Yedek oluştur
            success = self._create_backup_file(backup_type, backup_path)
            
            if not success:
                return self.create_error_response(
                    message="Yedek oluşturulamadı",
                    status_code=500
                )
            
            # Yedek bilgilerini kaydet
            backup_info = {
                "id": backup_id,
                "type": backup_type,
                "description": description,
                "filename": backup_filename,
                "path": backup_path,
                "size": os.path.getsize(backup_path) if os.path.exists(backup_path) else 0,
                "created_at": time.time(),
                "created_by": getattr(request, 'user_id', None),
                "status": "completed"
            }
            
            # Yedek bilgilerini dosyaya kaydet
            self._save_backup_info(backup_info)
            
            return self.create_success_response(
                data=backup_info,
                message="Yedek başarıyla oluşturuldu"
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Yedek oluşturma hatası: {e}")
            return self.create_error_response(
                message="Yedek oluşturulamadı",
                status_code=500
            )
    
    async def get_backup(self, request: Request) -> Response:
        """Yedek detayı"""
        try:
            backup_id = request.match_info['backup_id']
            
            # Yedek bilgilerini al
            backup_info = self._get_backup_info(backup_id)
            
            if not backup_info:
                return self.create_error_response(
                    message="Yedek bulunamadı",
                    status_code=404
                )
            
            return self.create_success_response(
                data=backup_info,
                message="Yedek detayları başarıyla alındı"
            )
            
        except Exception as e:
            self.logger.error(f"Yedek detayı hatası: {e}")
            return self.create_error_response(
                message="Yedek detayları alınamadı",
                status_code=500
            )
    
    async def delete_backup(self, request: Request) -> Response:
        """Yedek sil"""
        try:
            backup_id = request.match_info['backup_id']
            
            # Yedek bilgilerini al
            backup_info = self._get_backup_info(backup_id)
            
            if not backup_info:
                return self.create_error_response(
                    message="Yedek bulunamadı",
                    status_code=404
                )
            
            # Yedek dosyasını sil
            if os.path.exists(backup_info['path']):
                os.remove(backup_info['path'])
            
            # Yedek bilgilerini sil
            self._delete_backup_info(backup_id)
            
            return self.create_success_response(
                data={"deleted_backup_id": backup_id},
                message="Yedek başarıyla silindi"
            )
            
        except Exception as e:
            self.logger.error(f"Yedek silme hatası: {e}")
            return self.create_error_response(
                message="Yedek silinemedi",
                status_code=500
            )
    
    async def restore_backup(self, request: Request) -> Response:
        """Yedek geri yükle"""
        try:
            backup_id = request.match_info['backup_id']
            data = await request.json()
            
            # Yedek bilgilerini al
            backup_info = self._get_backup_info(backup_id)
            
            if not backup_info:
                return self.create_error_response(
                    message="Yedek bulunamadı",
                    status_code=404
                )
            
            # Yedek dosyası var mı kontrol et
            if not os.path.exists(backup_info['path']):
                return self.create_error_response(
                    message="Yedek dosyası bulunamadı",
                    status_code=404
                )
            
            # Geri yükleme seçeneklerini al
            force_restore = data.get('force', False)
            restore_type = data.get('restore_type', backup_info['type'])
            
            # Geri yükleme işlemini başlat
            success = self._restore_backup_file(backup_info, restore_type, force_restore)
            
            if not success:
                return self.create_error_response(
                    message="Yedek geri yüklenemedi",
                    status_code=500
                )
            
            # Geri yükleme bilgilerini kaydet
            restore_info = {
                "backup_id": backup_id,
                "restore_type": restore_type,
                "restored_at": time.time(),
                "restored_by": getattr(request, 'user_id', None),
                "force_restore": force_restore
            }
            
            return self.create_success_response(
                data=restore_info,
                message="Yedek başarıyla geri yüklendi"
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Yedek geri yükleme hatası: {e}")
            return self.create_error_response(
                message="Yedek geri yüklenemedi",
                status_code=500
            )
    
    async def download_backup(self, request: Request) -> Response:
        """Yedek indir"""
        try:
            backup_id = request.match_info['backup_id']
            
            # Yedek bilgilerini al
            backup_info = self._get_backup_info(backup_id)
            
            if not backup_info:
                return self.create_error_response(
                    message="Yedek bulunamadı",
                    status_code=404
                )
            
            # Yedek dosyası var mı kontrol et
            if not os.path.exists(backup_info['path']):
                return self.create_error_response(
                    message="Yedek dosyası bulunamadı",
                    status_code=404
                )
            
            # Dosyayı döndür
            return web.FileResponse(
                path=backup_info['path'],
                headers={
                    'Content-Disposition': f'attachment; filename="{backup_info["filename"]}"'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Yedek indirme hatası: {e}")
            return self.create_error_response(
                message="Yedek indirilemedi",
                status_code=500
            )
    
    def _get_backup_list(self) -> List[Dict[str, Any]]:
        """Yedek listesini al"""
        backups = []
        
        if os.path.exists(self.backup_dir):
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, filename)
                    if os.path.isfile(file_path):
                        # Dosya bilgilerini al
                        stat = os.stat(file_path)
                        backup_id = filename.split('_')[1].split('.')[0]
                        
                        backup_info = {
                            "id": backup_id,
                            "type": filename.split('_')[2].split('.')[0],
                            "filename": filename,
                            "size": stat.st_size,
                            "created_at": stat.st_ctime,
                            "modified_at": stat.st_mtime,
                            "status": "completed"
                        }
                        backups.append(backup_info)
        
        # Tarihe göre sırala (en yeni önce)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return backups
    
    def _get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Yedek bilgilerini al"""
        backups = self._get_backup_list()
        for backup in backups:
            if backup['id'] == backup_id:
                backup['path'] = os.path.join(self.backup_dir, backup['filename'])
                return backup
        return None
    
    def _create_backup_file(self, backup_type: str, backup_path: str) -> bool:
        """Yedek dosyası oluştur"""
        try:
            import zipfile
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if backup_type in ['full', 'database']:
                    # Veritabanı yedekleme
                    self._backup_database(zipf)
                
                if backup_type in ['full', 'files']:
                    # Dosya yedekleme
                    self._backup_files(zipf)
                
                if backup_type in ['full', 'config']:
                    # Konfigürasyon yedekleme
                    self._backup_config(zipf)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Yedek dosyası oluşturulamadı: {e}")
            return False
    
    def _backup_database(self, zipf):
        """Veritabanını yedekle"""
        try:
            # Veritabanı dosyalarını yedekle
            db_files = ['data.db', 'users.db', 'sessions.db']
            for db_file in db_files:
                if os.path.exists(db_file):
                    zipf.write(db_file, f"database/{db_file}")
        except Exception as e:
            self.logger.error(f"Veritabanı yedekleme hatası: {e}")
    
    def _backup_files(self, zipf):
        """Dosyaları yedekle"""
        try:
            # Upload dizinini yedekle
            if os.path.exists('uploads'):
                for root, dirs, files in os.walk('uploads'):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, 'uploads')
                        zipf.write(file_path, f"files/{arcname}")
        except Exception as e:
            self.logger.error(f"Dosya yedekleme hatası: {e}")
    
    def _backup_config(self, zipf):
        """Konfigürasyonu yedekle"""
        try:
            # Konfigürasyon dosyalarını yedekle
            config_files = ['config.json', 'settings.py', '.env']
            for config_file in config_files:
                if os.path.exists(config_file):
                    zipf.write(config_file, f"config/{config_file}")
        except Exception as e:
            self.logger.error(f"Konfigürasyon yedekleme hatası: {e}")
    
    def _restore_backup_file(self, backup_info: Dict[str, Any], restore_type: str, force: bool) -> bool:
        """Yedek dosyasını geri yükle"""
        try:
            import zipfile
            
            with zipfile.ZipFile(backup_info['path'], 'r') as zipf:
                if restore_type in ['full', 'database']:
                    # Veritabanını geri yükle
                    self._restore_database(zipf, force)
                
                if restore_type in ['full', 'files']:
                    # Dosyaları geri yükle
                    self._restore_files(zipf, force)
                
                if restore_type in ['full', 'config']:
                    # Konfigürasyonu geri yükle
                    self._restore_config(zipf, force)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Yedek geri yükleme hatası: {e}")
            return False
    
    def _restore_database(self, zipf, force: bool):
        """Veritabanını geri yükle"""
        try:
            # Veritabanı dosyalarını geri yükle
            for member in zipf.namelist():
                if member.startswith('database/'):
                    if force or not os.path.exists(member[9:]):
                        zipf.extract(member, '.')
        except Exception as e:
            self.logger.error(f"Veritabanı geri yükleme hatası: {e}")
    
    def _restore_files(self, zipf, force: bool):
        """Dosyaları geri yükle"""
        try:
            # Dosyaları geri yükle
            for member in zipf.namelist():
                if member.startswith('files/'):
                    target_path = member[6:]  # 'files/' kısmını kaldır
                    if force or not os.path.exists(target_path):
                        zipf.extract(member, 'uploads')
        except Exception as e:
            self.logger.error(f"Dosya geri yükleme hatası: {e}")
    
    def _restore_config(self, zipf, force: bool):
        """Konfigürasyonu geri yükle"""
        try:
            # Konfigürasyon dosyalarını geri yükle
            for member in zipf.namelist():
                if member.startswith('config/'):
                    target_path = member[7:]  # 'config/' kısmını kaldır
                    if force or not os.path.exists(target_path):
                        zipf.extract(member, '.')
        except Exception as e:
            self.logger.error(f"Konfigürasyon geri yükleme hatası: {e}")
    
    def _save_backup_info(self, backup_info: Dict[str, Any]):
        """Yedek bilgilerini kaydet"""
        try:
            info_file = os.path.join(self.backup_dir, f"{backup_info['id']}.json")
            with open(info_file, 'w') as f:
                json.dump(backup_info, f, indent=2)
        except Exception as e:
            self.logger.error(f"Yedek bilgileri kaydedilemedi: {e}")
    
    def _delete_backup_info(self, backup_id: str):
        """Yedek bilgilerini sil"""
        try:
            info_file = os.path.join(self.backup_dir, f"{backup_id}.json")
            if os.path.exists(info_file):
                os.remove(info_file)
        except Exception as e:
            self.logger.error(f"Yedek bilgileri silinemedi: {e}")
