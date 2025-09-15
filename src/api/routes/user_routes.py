"""
User Routes module - User management endpoint'leri

Bu modül kullanıcı yönetimi ile ilgili API endpoint'lerini içerir.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional
from aiohttp import web
from aiohttp.web import Request, Response

from .base_routes import BaseRoutes
from ...core.constants import API_PREFIX, SUCCESS_MESSAGES, ERROR_MESSAGES
from ...core.settings import settings
from ...db.models import User, UserRole, Role
from ...utils.logger import Logger


class UserRoutes(BaseRoutes):
    """User routes sınıfı"""
    
    def __init__(self):
        """UserRoutes'ı başlat"""
        super().__init__()
        self.logger = Logger(__name__)
    
    def get_routes(self) -> list[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.get(f"{API_PREFIX}/users", self.get_users),
            web.post(f"{API_PREFIX}/users", self.create_user),
            web.get(f"{API_PREFIX}/users/{{user_id}}", self.get_user),
            web.put(f"{API_PREFIX}/users/{{user_id}}", self.update_user),
            web.delete(f"{API_PREFIX}/users/{{user_id}}", self.delete_user),
            web.get(f"{API_PREFIX}/users/{{user_id}}/profile", self.get_user_profile),
            web.put(f"{API_PREFIX}/users/{{user_id}}/profile", self.update_user_profile),
            web.post(f"{API_PREFIX}/users/{{user_id}}/avatar", self.upload_user_avatar),
        ]
    
    async def get_users(self, request: Request) -> Response:
        """Kullanıcı listesi"""
        try:
            # Query parametrelerini al
            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', 20))
            search = request.query.get('search', '')
            role_filter = request.query.get('role', '')
            
            # Sayfalama için offset hesapla
            offset = (page - 1) * limit
            
            # Kullanıcıları al
            query = User.select()
            
            # Arama filtresi
            if search:
                query = query.where(
                    (User.username.contains(search)) |
                    (User.email.contains(search)) |
                    (User.full_name.contains(search))
                )
            
            # Rol filtresi
            if role_filter:
                query = query.join(UserRole).join(Role).where(Role.name == role_filter)
            
            # Toplam sayıyı al
            total = query.count()
            
            # Sayfalama uygula
            users = query.offset(offset).limit(limit)
            
            # Kullanıcı verilerini hazırla
            user_list = []
            for user in users:
                # Kullanıcı rollerini al
                user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
                
                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "is_superuser": user.is_superuser,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "roles": user_roles
                }
                user_list.append(user_data)
            
            # Sayfalama bilgisi
            pagination = {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
            
            return self.create_success_response(
                data={
                    "users": user_list,
                    "pagination": pagination
                },
                message="Kullanıcı listesi başarıyla alındı"
            )
            
        except Exception as e:
            self.logger.error(f"Kullanıcı listesi hatası: {e}")
            return self.create_error_response(
                message="Kullanıcı listesi alınamadı",
                status_code=500
            )
    
    async def create_user(self, request: Request) -> Response:
        """Yeni kullanıcı oluştur"""
        try:
            # Request body'yi al
            data = await request.json()
            
            # Gerekli alanları kontrol et
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if field not in data:
                    return self.create_error_response(
                        message=f"Eksik alan: {field}",
                        status_code=400
                    )
            
            # Kullanıcı adı ve email benzersizlik kontrolü
            if User.select().where(User.username == data['username']).exists():
                return self.create_error_response(
                    message="Bu kullanıcı adı zaten kullanılıyor",
                    status_code=409
                )
            
            if User.select().where(User.email == data['email']).exists():
                return self.create_error_response(
                    message="Bu e-posta adresi zaten kullanılıyor",
                    status_code=409
                )
            
            # Yeni kullanıcı oluştur
            import bcrypt
            hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            
            user = User.create(
                username=data['username'],
                email=data['email'],
                password=hashed_password.decode('utf-8'),
                full_name=data.get('full_name', ''),
                is_active=data.get('is_active', True),
                is_verified=data.get('is_verified', False),
                is_superuser=data.get('is_superuser', False)
            )
            
            # Rolleri ata
            roles = data.get('roles', [])
            for role_name in roles:
                try:
                    role = Role.get(Role.name == role_name)
                    UserRole.create(user=user, role=role)
                except Role.DoesNotExist:
                    self.logger.warning(f"Rol bulunamadı: {role_name}")
            
            # Kullanıcı verilerini hazırla
            user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "roles": user_roles
            }
            
            return self.create_success_response(
                data=user_data,
                message="Kullanıcı başarıyla oluşturuldu"
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Kullanıcı oluşturma hatası: {e}")
            return self.create_error_response(
                message="Kullanıcı oluşturulamadı",
                status_code=500
            )
    
    async def get_user(self, request: Request) -> Response:
        """Kullanıcı detayı"""
        try:
            user_id = int(request.match_info['user_id'])
            
            # Kullanıcıyı al
            user = User.get_by_id(user_id)
            
            # Kullanıcı rollerini al
            user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
            
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "roles": user_roles
            }
            
            return self.create_success_response(
                data=user_data,
                message="Kullanıcı detayları başarıyla alındı"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz kullanıcı ID",
                status_code=400
            )
        except User.DoesNotExist:
            return self.create_error_response(
                message="Kullanıcı bulunamadı",
                status_code=404
            )
        except Exception as e:
            self.logger.error(f"Kullanıcı detayı hatası: {e}")
            return self.create_error_response(
                message="Kullanıcı detayları alınamadı",
                status_code=500
            )
    
    async def update_user(self, request: Request) -> Response:
        """Kullanıcı güncelle"""
        try:
            user_id = int(request.match_info['user_id'])
            data = await request.json()
            
            # Kullanıcıyı al
            user = User.get_by_id(user_id)
            
            # Güncellenebilir alanları kontrol et ve güncelle
            if 'email' in data:
                # Email benzersizlik kontrolü
                if User.select().where((User.email == data['email']) & (User.id != user_id)).exists():
                    return self.create_error_response(
                        message="Bu e-posta adresi zaten kullanılıyor",
                        status_code=409
                    )
                user.email = data['email']
            
            if 'full_name' in data:
                user.full_name = data['full_name']
            
            if 'is_active' in data:
                user.is_active = data['is_active']
            
            if 'is_verified' in data:
                user.is_verified = data['is_verified']
            
            if 'is_superuser' in data:
                user.is_superuser = data['is_superuser']
            
            # Parola güncelleme
            if 'password' in data:
                import bcrypt
                hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
                user.password = hashed_password.decode('utf-8')
            
            # Kullanıcıyı kaydet
            user.save()
            
            # Rolleri güncelle
            if 'roles' in data:
                # Mevcut rolleri sil
                UserRole.delete().where(UserRole.user == user).execute()
                
                # Yeni rolleri ata
                for role_name in data['roles']:
                    try:
                        role = Role.get(Role.name == role_name)
                        UserRole.create(user=user, role=role)
                    except Role.DoesNotExist:
                        self.logger.warning(f"Rol bulunamadı: {role_name}")
            
            # Güncellenmiş kullanıcı verilerini al
            user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "roles": user_roles
            }
            
            return self.create_success_response(
                data=user_data,
                message="Kullanıcı başarıyla güncellendi"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz kullanıcı ID",
                status_code=400
            )
        except User.DoesNotExist:
            return self.create_error_response(
                message="Kullanıcı bulunamadı",
                status_code=404
            )
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Kullanıcı güncelleme hatası: {e}")
            return self.create_error_response(
                message="Kullanıcı güncellenemedi",
                status_code=500
            )
    
    async def delete_user(self, request: Request) -> Response:
        """Kullanıcı sil"""
        try:
            user_id = int(request.match_info['user_id'])
            
            # Kullanıcıyı al
            user = User.get_by_id(user_id)
            
            # Superuser kontrolü (kendini silmeye çalışıyor mu?)
            # Bu kontrolü auth middleware'de yapabiliriz
            
            # Kullanıcıyı sil
            user.delete_instance()
            
            return self.create_success_response(
                data={"deleted_user_id": user_id},
                message="Kullanıcı başarıyla silindi"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz kullanıcı ID",
                status_code=400
            )
        except User.DoesNotExist:
            return self.create_error_response(
                message="Kullanıcı bulunamadı",
                status_code=404
            )
        except Exception as e:
            self.logger.error(f"Kullanıcı silme hatası: {e}")
            return self.create_error_response(
                message="Kullanıcı silinemedi",
                status_code=500
            )
    
    async def get_user_profile(self, request: Request) -> Response:
        """Kullanıcı profil detayı"""
        try:
            user_id = int(request.match_info['user_id'])
            
            # Kullanıcıyı al
            user = User.get_by_id(user_id)
            
            # Kullanıcı rollerini al
            user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
            
            # Profil verilerini hazırla
            profile_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "roles": user_roles,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "avatar_url": getattr(user, 'avatar_url', None),
                "bio": getattr(user, 'bio', ''),
                "phone": getattr(user, 'phone', ''),
                "address": getattr(user, 'address', ''),
                "website": getattr(user, 'website', ''),
                "social_links": getattr(user, 'social_links', {})
            }
            
            return self.create_success_response(
                data=profile_data,
                message="Kullanıcı profili başarıyla alındı"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz kullanıcı ID",
                status_code=400
            )
        except User.DoesNotExist:
            return self.create_error_response(
                message="Kullanıcı bulunamadı",
                status_code=404
            )
        except Exception as e:
            self.logger.error(f"Kullanıcı profili hatası: {e}")
            return self.create_error_response(
                message="Kullanıcı profili alınamadı",
                status_code=500
            )
    
    async def update_user_profile(self, request: Request) -> Response:
        """Kullanıcı profil güncelle"""
        try:
            user_id = int(request.match_info['user_id'])
            data = await request.json()
            
            # Kullanıcıyı al
            user = User.get_by_id(user_id)
            
            # Güncellenebilir profil alanlarını kontrol et ve güncelle
            if 'full_name' in data:
                user.full_name = data['full_name']
            
            if 'bio' in data:
                user.bio = data['bio']
            
            if 'phone' in data:
                user.phone = data['phone']
            
            if 'address' in data:
                user.address = data['address']
            
            if 'website' in data:
                user.website = data['website']
            
            if 'social_links' in data:
                user.social_links = data['social_links']
            
            # Kullanıcıyı kaydet
            user.save()
            
            # Güncellenmiş profil verilerini al
            user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
            profile_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "roles": user_roles,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "avatar_url": getattr(user, 'avatar_url', None),
                "bio": getattr(user, 'bio', ''),
                "phone": getattr(user, 'phone', ''),
                "address": getattr(user, 'address', ''),
                "website": getattr(user, 'website', ''),
                "social_links": getattr(user, 'social_links', {})
            }
            
            return self.create_success_response(
                data=profile_data,
                message="Kullanıcı profili başarıyla güncellendi"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz kullanıcı ID",
                status_code=400
            )
        except User.DoesNotExist:
            return self.create_error_response(
                message="Kullanıcı bulunamadı",
                status_code=404
            )
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Kullanıcı profil güncelleme hatası: {e}")
            return self.create_error_response(
                message="Kullanıcı profili güncellenemedi",
                status_code=500
            )
    
    async def upload_user_avatar(self, request: Request) -> Response:
        """Kullanıcı avatar yükle"""
        try:
            user_id = int(request.match_info['user_id'])
            
            # Kullanıcıyı al
            user = User.get_by_id(user_id)
            
            # Multipart form data'yı parse et
            reader = await request.multipart()
            
            file_field = None
            while True:
                part = await reader.next()
                if part is None:
                    break
                
                if part.name == 'avatar':
                    file_field = part
                    break
            
            if not file_field:
                return self.create_error_response(
                    message="Avatar dosyası bulunamadı",
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
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in allowed_extensions:
                return self.create_error_response(
                    message=f"Desteklenmeyen dosya türü: {file_ext}",
                    status_code=400
                )
            
            # Dosya boyutunu kontrol et (max 5MB)
            max_size = 5 * 1024 * 1024
            file_size = 0
            content = b''
            while True:
                chunk = await file_field.read_chunk()
                if not chunk:
                    break
                content += chunk
                file_size += len(chunk)
                
                if file_size > max_size:
                    return self.create_error_response(
                        message="Dosya boyutu çok büyük. Maksimum: 5MB",
                        status_code=400
                    )
            
            # Avatar dizinini oluştur
            avatar_dir = "avatars"
            if not os.path.exists(avatar_dir):
                os.makedirs(avatar_dir)
            
            # Benzersiz dosya adı oluştur
            import uuid
            file_id = str(uuid.uuid4())
            safe_filename = f"{file_id}_{filename}"
            file_path = os.path.join(avatar_dir, safe_filename)
            
            # Dosyayı kaydet
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Avatar URL'ini oluştur
            avatar_url = f"/api/v1/avatars/{safe_filename}"
            
            # Kullanıcının avatar URL'ini güncelle
            user.avatar_url = avatar_url
            user.save()
            
            # Avatar bilgilerini döndür
            avatar_info = {
                "user_id": user_id,
                "avatar_url": avatar_url,
                "filename": safe_filename,
                "size": file_size,
                "uploaded_at": time.time()
            }
            
            return self.create_success_response(
                data=avatar_info,
                message="Avatar başarıyla yüklendi"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz kullanıcı ID",
                status_code=400
            )
        except User.DoesNotExist:
            return self.create_error_response(
                message="Kullanıcı bulunamadı",
                status_code=404
            )
        except Exception as e:
            self.logger.error(f"Avatar yükleme hatası: {e}")
            return self.create_error_response(
                message="Avatar yüklenemedi",
                status_code=500
            )