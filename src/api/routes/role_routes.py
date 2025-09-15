"""
Role Routes module - Role management endpoint'leri

Bu modül rol yönetimi ile ilgili API endpoint'lerini içerir.
"""

import json
from typing import Dict, Any, List, Optional
from aiohttp import web
from aiohttp.web import Request, Response

from .base_routes import BaseRoutes
from ...core.constants import API_PREFIX, SUCCESS_MESSAGES, ERROR_MESSAGES
from ...db.models import Role, UserRole, User
from ...utils.logger import Logger


class RoleRoutes(BaseRoutes):
    """Role routes sınıfı"""
    
    def __init__(self):
        """RoleRoutes'ı başlat"""
        super().__init__()
        self.logger = Logger(__name__)
    
    def get_routes(self) -> list[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.get(f"{API_PREFIX}/roles", self.get_roles),
            web.post(f"{API_PREFIX}/roles", self.create_role),
            web.get(f"{API_PREFIX}/roles/{{role_id}}", self.get_role),
            web.put(f"{API_PREFIX}/roles/{{role_id}}", self.update_role),
            web.delete(f"{API_PREFIX}/roles/{{role_id}}", self.delete_role),
            web.get(f"{API_PREFIX}/permissions", self.get_permissions),
            web.post(f"{API_PREFIX}/users/{{user_id}}/roles", self.assign_role),
            web.delete(f"{API_PREFIX}/users/{{user_id}}/roles/{{role_id}}", self.remove_role),
        ]
    
    async def get_roles(self, request: Request) -> Response:
        """Rol listesi"""
        try:
            # Query parametrelerini al
            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', 20))
            search = request.query.get('search', '')
            
            # Sayfalama için offset hesapla
            offset = (page - 1) * limit
            
            # Rolleri al
            query = Role.select()
            
            # Arama filtresi
            if search:
                query = query.where(
                    (Role.name.contains(search)) |
                    (Role.description.contains(search))
                )
            
            # Toplam sayıyı al
            total = query.count()
            
            # Sayfalama uygula
            roles = query.offset(offset).limit(limit)
            
            # Rol verilerini hazırla
            role_list = []
            for role in roles:
                # Rol kullanıcı sayısını al
                user_count = UserRole.select().where(UserRole.role == role).count()
                
                role_data = {
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "permissions": role.permissions or [],
                    "user_count": user_count,
                    "created_at": role.created_at.isoformat() if role.created_at else None,
                    "updated_at": role.updated_at.isoformat() if role.updated_at else None
                }
                role_list.append(role_data)
            
            # Sayfalama bilgisi
            pagination = {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
            
            return self.create_success_response(
                data={
                    "roles": role_list,
                    "pagination": pagination
                },
                message="Rol listesi başarıyla alındı"
            )
            
        except Exception as e:
            self.logger.error(f"Rol listesi hatası: {e}")
            return self.create_error_response(
                message="Rol listesi alınamadı",
                status_code=500
            )
    
    async def create_role(self, request: Request) -> Response:
        """Yeni rol oluştur"""
        try:
            # Request body'yi al
            data = await request.json()
            
            # Gerekli alanları kontrol et
            required_fields = ['name']
            for field in required_fields:
                if field not in data:
                    return self.create_error_response(
                        message=f"Eksik alan: {field}",
                        status_code=400
                    )
            
            # Rol adı benzersizlik kontrolü
            if Role.select().where(Role.name == data['name']).exists():
                return self.create_error_response(
                    message="Bu rol adı zaten kullanılıyor",
                    status_code=409
                )
            
            # Yeni rol oluştur
            role = Role.create(
                name=data['name'],
                description=data.get('description', ''),
                permissions=data.get('permissions', [])
            )
            
            # Rol verilerini hazırla
            role_data = {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": role.permissions or [],
                "user_count": 0,
                "created_at": role.created_at.isoformat() if role.created_at else None,
                "updated_at": role.updated_at.isoformat() if role.updated_at else None
            }
            
            return self.create_success_response(
                data=role_data,
                message="Rol başarıyla oluşturuldu"
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Rol oluşturma hatası: {e}")
            return self.create_error_response(
                message="Rol oluşturulamadı",
                status_code=500
            )
    
    async def get_role(self, request: Request) -> Response:
        """Rol detayı"""
        try:
            role_id = int(request.match_info['role_id'])
            
            # Rolü al
            role = Role.get_by_id(role_id)
            
            # Rol kullanıcı sayısını al
            user_count = UserRole.select().where(UserRole.role == role).count()
            
            # Rol kullanıcılarını al
            users = []
            for user_role in UserRole.select().where(UserRole.role == role).join(User):
                users.append({
                    "id": user_role.user.id,
                    "username": user_role.user.username,
                    "email": user_role.user.email,
                    "full_name": user_role.user.full_name
                })
            
            role_data = {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": role.permissions or [],
                "user_count": user_count,
                "users": users,
                "created_at": role.created_at.isoformat() if role.created_at else None,
                "updated_at": role.updated_at.isoformat() if role.updated_at else None
            }
            
            return self.create_success_response(
                data=role_data,
                message="Rol detayları başarıyla alındı"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz rol ID",
                status_code=400
            )
        except Role.DoesNotExist:
            return self.create_error_response(
                message="Rol bulunamadı",
                status_code=404
            )
        except Exception as e:
            self.logger.error(f"Rol detayı hatası: {e}")
            return self.create_error_response(
                message="Rol detayları alınamadı",
                status_code=500
            )
    
    async def update_role(self, request: Request) -> Response:
        """Rol güncelle"""
        try:
            role_id = int(request.match_info['role_id'])
            data = await request.json()
            
            # Rolü al
            role = Role.get_by_id(role_id)
            
            # Güncellenebilir alanları kontrol et ve güncelle
            if 'name' in data:
                # Rol adı benzersizlik kontrolü
                if Role.select().where((Role.name == data['name']) & (Role.id != role_id)).exists():
                    return self.create_error_response(
                        message="Bu rol adı zaten kullanılıyor",
                        status_code=409
                    )
                role.name = data['name']
            
            if 'description' in data:
                role.description = data['description']
            
            if 'permissions' in data:
                role.permissions = data['permissions']
            
            # Rolü kaydet
            role.save()
            
            # Güncellenmiş rol verilerini al
            user_count = UserRole.select().where(UserRole.role == role).count()
            role_data = {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": role.permissions or [],
                "user_count": user_count,
                "created_at": role.created_at.isoformat() if role.created_at else None,
                "updated_at": role.updated_at.isoformat() if role.updated_at else None
            }
            
            return self.create_success_response(
                data=role_data,
                message="Rol başarıyla güncellendi"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz rol ID",
                status_code=400
            )
        except Role.DoesNotExist:
            return self.create_error_response(
                message="Rol bulunamadı",
                status_code=404
            )
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Rol güncelleme hatası: {e}")
            return self.create_error_response(
                message="Rol güncellenemedi",
                status_code=500
            )
    
    async def delete_role(self, request: Request) -> Response:
        """Rol sil"""
        try:
            role_id = int(request.match_info['role_id'])
            
            # Rolü al
            role = Role.get_by_id(role_id)
            
            # Rol kullanıcıları var mı kontrol et
            user_count = UserRole.select().where(UserRole.role == role).count()
            if user_count > 0:
                return self.create_error_response(
                    message="Bu rolü kullanan kullanıcılar var. Önce kullanıcılardan rolü kaldırın.",
                    status_code=400
                )
            
            # Rolü sil
            role.delete_instance()
            
            return self.create_success_response(
                data={"deleted_role_id": role_id},
                message="Rol başarıyla silindi"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz rol ID",
                status_code=400
            )
        except Role.DoesNotExist:
            return self.create_error_response(
                message="Rol bulunamadı",
                status_code=404
            )
        except Exception as e:
            self.logger.error(f"Rol silme hatası: {e}")
            return self.create_error_response(
                message="Rol silinemedi",
                status_code=500
            )
    
    async def get_permissions(self, request: Request) -> Response:
        """İzin listesi"""
        try:
            # Sistem izinlerini al
            permissions = [
                {
                    "id": "user.read",
                    "name": "Kullanıcı Okuma",
                    "description": "Kullanıcı bilgilerini görüntüleme izni",
                    "category": "user"
                },
                {
                    "id": "user.write",
                    "name": "Kullanıcı Yazma",
                    "description": "Kullanıcı bilgilerini düzenleme izni",
                    "category": "user"
                },
                {
                    "id": "user.delete",
                    "name": "Kullanıcı Silme",
                    "description": "Kullanıcı silme izni",
                    "category": "user"
                },
                {
                    "id": "role.read",
                    "name": "Rol Okuma",
                    "description": "Rol bilgilerini görüntüleme izni",
                    "category": "role"
                },
                {
                    "id": "role.write",
                    "name": "Rol Yazma",
                    "description": "Rol bilgilerini düzenleme izni",
                    "category": "role"
                },
                {
                    "id": "role.delete",
                    "name": "Rol Silme",
                    "description": "Rol silme izni",
                    "category": "role"
                },
                {
                    "id": "config.read",
                    "name": "Konfigürasyon Okuma",
                    "description": "Sistem konfigürasyonunu görüntüleme izni",
                    "category": "config"
                },
                {
                    "id": "config.write",
                    "name": "Konfigürasyon Yazma",
                    "description": "Sistem konfigürasyonunu düzenleme izni",
                    "category": "config"
                },
                {
                    "id": "admin.access",
                    "name": "Admin Erişimi",
                    "description": "Admin paneli erişim izni",
                    "category": "admin"
                },
                {
                    "id": "file.read",
                    "name": "Dosya Okuma",
                    "description": "Dosya görüntüleme izni",
                    "category": "file"
                },
                {
                    "id": "file.write",
                    "name": "Dosya Yazma",
                    "description": "Dosya yükleme izni",
                    "category": "file"
                },
                {
                    "id": "file.delete",
                    "name": "Dosya Silme",
                    "description": "Dosya silme izni",
                    "category": "file"
                },
                {
                    "id": "log.read",
                    "name": "Log Okuma",
                    "description": "Sistem loglarını görüntüleme izni",
                    "category": "log"
                },
                {
                    "id": "monitor.read",
                    "name": "İzleme Okuma",
                    "description": "Sistem metriklerini görüntüleme izni",
                    "category": "monitor"
                }
            ]
            
            # Kategorilere göre grupla
            categories = {}
            for permission in permissions:
                category = permission['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(permission)
            
            return self.create_success_response(
                data={
                    "permissions": permissions,
                    "categories": categories
                },
                message="İzin listesi başarıyla alındı"
            )
            
        except Exception as e:
            self.logger.error(f"İzin listesi hatası: {e}")
            return self.create_error_response(
                message="İzin listesi alınamadı",
                status_code=500
            )
    
    async def assign_role(self, request: Request) -> Response:
        """Kullanıcıya rol ata"""
        try:
            user_id = int(request.match_info['user_id'])
            data = await request.json()
            
            role_id = data.get('role_id')
            if not role_id:
                return self.create_error_response(
                    message="role_id gerekli",
                    status_code=400
                )
            
            # Kullanıcıyı al
            user = User.get_by_id(user_id)
            
            # Rolü al
            role = Role.get_by_id(role_id)
            
            # Kullanıcının bu rolü zaten var mı kontrol et
            if UserRole.select().where(
                (UserRole.user == user) & (UserRole.role == role)
            ).exists():
                return self.create_error_response(
                    message="Kullanıcının bu rolü zaten var",
                    status_code=409
                )
            
            # Rolü ata
            UserRole.create(user=user, role=role)
            
            # Kullanıcının güncel rollerini al
            user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
            
            return self.create_success_response(
                data={
                    "user_id": user_id,
                    "role_id": role_id,
                    "user_roles": user_roles
                },
                message="Rol başarıyla atandı"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz kullanıcı ID veya rol ID",
                status_code=400
            )
        except User.DoesNotExist:
            return self.create_error_response(
                message="Kullanıcı bulunamadı",
                status_code=404
            )
        except Role.DoesNotExist:
            return self.create_error_response(
                message="Rol bulunamadı",
                status_code=404
            )
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Rol atama hatası: {e}")
            return self.create_error_response(
                message="Rol atanamadı",
                status_code=500
            )
    
    async def remove_role(self, request: Request) -> Response:
        """Kullanıcıdan rol kaldır"""
        try:
            user_id = int(request.match_info['user_id'])
            role_id = int(request.match_info['role_id'])
            
            # Kullanıcıyı al
            user = User.get_by_id(user_id)
            
            # Rolü al
            role = Role.get_by_id(role_id)
            
            # Kullanıcının bu rolü var mı kontrol et
            user_role = UserRole.get_or_none(
                (UserRole.user == user) & (UserRole.role == role)
            )
            
            if not user_role:
                return self.create_error_response(
                    message="Kullanıcının bu rolü yok",
                    status_code=404
                )
            
            # Rolü kaldır
            user_role.delete_instance()
            
            # Kullanıcının güncel rollerini al
            user_roles = [ur.role.name for ur in user.user_roles.select().join(Role)]
            
            return self.create_success_response(
                data={
                    "user_id": user_id,
                    "role_id": role_id,
                    "user_roles": user_roles
                },
                message="Rol başarıyla kaldırıldı"
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz kullanıcı ID veya rol ID",
                status_code=400
            )
        except User.DoesNotExist:
            return self.create_error_response(
                message="Kullanıcı bulunamadı",
                status_code=404
            )
        except Role.DoesNotExist:
            return self.create_error_response(
                message="Rol bulunamadı",
                status_code=404
            )
        except Exception as e:
            self.logger.error(f"Rol kaldırma hatası: {e}")
            return self.create_error_response(
                message="Rol kaldırılamadı",
                status_code=500
            )
