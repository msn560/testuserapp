"""
Log Routes module - Log management endpoint'leri

Bu modül log yönetimi ile ilgili API endpoint'lerini içerir.
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from aiohttp import web
from aiohttp.web import Request, Response

from .base_routes import BaseRoutes
from ...core.constants import API_PREFIX, SUCCESS_MESSAGES, ERROR_MESSAGES
from ...api.schemas.log_schemas import (
    LogEntry, LogListResponse, LogExportRequest, LogExportResponse,
    LogStatsResponse, LogSearchRequest, LogSearchResponse,
    LogCleanupRequest, LogCleanupResponse
)


class LogRoutes(BaseRoutes):
    """Log routes sınıfı"""
    
    def __init__(self):
        """LogRoutes'ı başlat"""
        super().__init__()
    
    def get_routes(self) -> list[web.RouteDef]:
        """
        Route'ları al
        
        Returns:
            Route listesi
        """
        return [
            web.get(f"{API_PREFIX}/logs", self.get_logs),
            web.get(f"{API_PREFIX}/logs/export", self.export_logs),
            web.delete(f"{API_PREFIX}/logs", self.clear_logs),
            web.get(f"{API_PREFIX}/logs/stats", self.get_log_stats),
            web.post(f"{API_PREFIX}/logs/search", self.search_logs),
            web.post(f"{API_PREFIX}/logs/cleanup", self.cleanup_logs),
            web.get(f"{API_PREFIX}/logs/{{log_id}}", self.get_log_detail),
            web.get(f"{API_PREFIX}/logs/levels", self.get_log_levels),
        ]
    
    async def get_logs(self, request: Request) -> Response:
        """Log kayıtları"""
        try:
            # Query parametrelerini al
            level = request.query.get('level')
            module = request.query.get('module')
            start_date = request.query.get('start_date')
            end_date = request.query.get('end_date')
            limit = int(request.query.get('limit', 100))
            page = int(request.query.get('page', 1))
            
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # API log'larını al
            api_logs = server_manager.get_api_logs()
            
            # Filtreleme
            filtered_logs = []
            for log in api_logs:
                # Level filtresi
                if level and log.get('level') != level:
                    continue
                
                # Module filtresi
                if module and log.get('module') != module:
                    continue
                
                # Tarih filtresi
                if start_date:
                    start_timestamp = datetime.fromisoformat(start_date.replace('Z', '+00:00')).timestamp()
                    if log.get('timestamp', 0) < start_timestamp:
                        continue
                
                if end_date:
                    end_timestamp = datetime.fromisoformat(end_date.replace('Z', '+00:00')).timestamp()
                    if log.get('timestamp', 0) > end_timestamp:
                        continue
                
                filtered_logs.append(log)
            
            # Sayfalama
            offset = (page - 1) * limit
            paginated_logs = filtered_logs[offset:offset + limit]
            
            # Log formatını düzenle
            formatted_logs = []
            for log in paginated_logs:
                formatted_log = {
                    "id": log.get('id', 0),
                    "level": log.get('level', 'INFO'),
                    "module": log.get('module', 'unknown'),
                    "message": log.get('message', ''),
                    "extra_data": log.get('extra_data', {}),
                    "user_id": log.get('user_id'),
                    "ip_address": log.get('ip_address'),
                    "created_at": datetime.fromtimestamp(log.get('timestamp', time.time())).isoformat() + 'Z'
                }
                formatted_logs.append(formatted_log)
            
            response_data = {
                "logs": formatted_logs,
                "total": len(filtered_logs),
                "limit": limit,
                "page": page
            }
            
            return self.create_success_response(
                message="Log'lar alındı",
                data=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Log'lar alınamadı: {e}")
            return self.create_error_response(
                message="Log'lar alınamadı",
                status_code=500
            )
    
    async def export_logs(self, request: Request) -> Response:
        """Log dışa aktarma"""
        try:
            # Query parametrelerini al
            format_type = request.query.get('format', 'json')
            start_date = request.query.get('start_date')
            end_date = request.query.get('end_date')
            
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # Log'ları dışa aktar
            filename = server_manager.export_logs(format_type)
            
            if filename:
                # Download URL oluştur
                download_url = f"/api/v1/logs/download/{filename}"
                expires_at = datetime.now() + timedelta(hours=1)
                
                response_data = {
                    "download_url": download_url,
                    "expires_at": expires_at.isoformat() + 'Z',
                    "file_size": 0,  # Gerçek dosya boyutu hesaplanabilir
                    "record_count": len(server_manager.get_api_logs())
                }
                
                return self.create_success_response(
                    message="Log'lar başarıyla dışa aktarıldı",
                    data=response_data
                )
            else:
                return self.create_error_response(
                    message="Log'lar dışa aktarılamadı",
                    status_code=500
                )
                
        except Exception as e:
            self.logger.error(f"Log export başarısız: {e}")
            return self.create_error_response(
                message="Log'lar dışa aktarılamadı",
                status_code=500
            )
    
    async def clear_logs(self, request: Request) -> Response:
        """Log temizleme"""
        try:
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # Log'ları temizle
            success = server_manager.clear_logs()
            
            if success:
                return self.create_success_response(
                    message="Log'lar başarıyla temizlendi"
                )
            else:
                return self.create_error_response(
                    message="Log'lar temizlenemedi",
                    status_code=500
                )
                
        except Exception as e:
            self.logger.error(f"Log temizleme başarısız: {e}")
            return self.create_error_response(
                message="Log'lar temizlenemedi",
                status_code=500
            )
    
    async def get_log_stats(self, request: Request) -> Response:
        """Log istatistikleri"""
        try:
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # API log'larını al
            api_logs = server_manager.get_api_logs()
            
            # İstatistikleri hesapla
            total_logs = len(api_logs)
            logs_by_level = {}
            logs_by_module = {}
            logs_by_hour = {}
            error_count = 0
            
            for log in api_logs:
                # Level istatistikleri
                level = log.get('level', 'INFO')
                logs_by_level[level] = logs_by_level.get(level, 0) + 1
                
                # Module istatistikleri
                module = log.get('module', 'unknown')
                logs_by_module[module] = logs_by_module.get(module, 0) + 1
                
                # Saat istatistikleri
                timestamp = log.get('timestamp', time.time())
                hour = datetime.fromtimestamp(timestamp).strftime('%H')
                logs_by_hour[hour] = logs_by_hour.get(hour, 0) + 1
                
                # Hata sayısı
                if level in ['ERROR', 'CRITICAL']:
                    error_count += 1
            
            # Error rate hesapla
            error_rate = (error_count / total_logs) if total_logs > 0 else 0
            
            stats = {
                "total_logs": total_logs,
                "logs_by_level": logs_by_level,
                "logs_by_module": logs_by_module,
                "logs_by_hour": logs_by_hour,
                "error_rate": round(error_rate, 4),
                "most_active_users": [],  # Bu bilgi user_id'den hesaplanabilir
                "period": {
                    "start_date": datetime.now().isoformat() + 'Z',
                    "end_date": datetime.now().isoformat() + 'Z'
                }
            }
            
            return self.create_success_response(
                message="Log istatistikleri alındı",
                data=stats
            )
            
        except Exception as e:
            self.logger.error(f"Log istatistikleri alınamadı: {e}")
            return self.create_error_response(
                message="Log istatistikleri alınamadı",
                status_code=500
            )
    
    async def search_logs(self, request: Request) -> Response:
        """Log arama"""
        try:
            # Request body'yi al
            data = await request.json()
            query = data.get('query', '')
            level = data.get('level')
            module = data.get('module')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            limit = data.get('limit', 100)
            offset = data.get('offset', 0)
            
            if not query:
                return self.create_error_response(
                    message="Arama sorgusu gerekli",
                    status_code=400
                )
            
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # API log'larını al
            api_logs = server_manager.get_api_logs()
            
            # Arama yap
            search_results = []
            for log in api_logs:
                # Basit metin araması
                if query.lower() in log.get('message', '').lower():
                    # Filtreleri uygula
                    if level and log.get('level') != level:
                        continue
                    if module and log.get('module') != module:
                        continue
                    
                    search_results.append(log)
            
            # Sayfalama
            paginated_results = search_results[offset:offset + limit]
            
            # Log formatını düzenle
            formatted_logs = []
            for log in paginated_results:
                formatted_log = {
                    "id": log.get('id', 0),
                    "level": log.get('level', 'INFO'),
                    "module": log.get('module', 'unknown'),
                    "message": log.get('message', ''),
                    "extra_data": log.get('extra_data', {}),
                    "user_id": log.get('user_id'),
                    "ip_address": log.get('ip_address'),
                    "created_at": datetime.fromtimestamp(log.get('timestamp', time.time())).isoformat() + 'Z'
                }
                formatted_logs.append(formatted_log)
            
            response_data = {
                "logs": formatted_logs,
                "total": len(search_results),
                "query": query,
                "execution_time": 0.15  # Örnek değer
            }
            
            return self.create_success_response(
                message="Log arama tamamlandı",
                data=response_data
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Log arama başarısız: {e}")
            return self.create_error_response(
                message="Log arama başarısız",
                status_code=500
            )
    
    async def cleanup_logs(self, request: Request) -> Response:
        """Log temizleme"""
        try:
            # Request body'yi al
            data = await request.json()
            older_than_days = data.get('older_than_days', 30)
            level = data.get('level')
            module = data.get('module')
            dry_run = data.get('dry_run', True)
            
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # Tarih hesapla
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            cutoff_timestamp = cutoff_date.timestamp()
            
            # API log'larını al
            api_logs = server_manager.get_api_logs()
            
            # Silinecek log'ları bul
            logs_to_delete = []
            for log in api_logs:
                if log.get('timestamp', 0) < cutoff_timestamp:
                    if level and log.get('level') != level:
                        continue
                    if module and log.get('module') != module:
                        continue
                    logs_to_delete.append(log)
            
            deleted_count = len(logs_to_delete)
            
            if not dry_run:
                # Gerçekten sil
                success = server_manager.clear_logs()
                if not success:
                    return self.create_error_response(
                        message="Log temizleme başarısız",
                        status_code=500
                    )
            
            response_data = {
                "deleted_count": deleted_count,
                "freed_space": deleted_count * 1024,  # Örnek değer
                "dry_run": dry_run
            }
            
            message = f"{deleted_count} log kaydı temizlendi" if not dry_run else f"{deleted_count} log kaydı silinecek (simülasyon)"
            
            return self.create_success_response(
                message=message,
                data=response_data
            )
            
        except json.JSONDecodeError:
            return self.create_error_response(
                message="Geçersiz JSON formatı",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Log temizleme başarısız: {e}")
            return self.create_error_response(
                message="Log temizleme başarısız",
                status_code=500
            )
    
    async def get_log_detail(self, request: Request) -> Response:
        """Log detayı"""
        try:
            log_id = int(request.match_info['log_id'])
            
            # Server manager'ı al
            server_manager = request.app.get('server_manager')
            if not server_manager:
                return self.create_error_response(
                    message="Server manager bulunamadı",
                    status_code=500
                )
            
            # API log'larını al
            api_logs = server_manager.get_api_logs()
            
            # Belirli log'u bul
            log_entry = None
            for log in api_logs:
                if log.get('id') == log_id:
                    log_entry = log
                    break
            
            if not log_entry:
                return self.create_error_response(
                    message="Log bulunamadı",
                    status_code=404
                )
            
            # Log detayını formatla
            log_detail = {
                "id": log_entry.get('id', 0),
                "level": log_entry.get('level', 'INFO'),
                "module": log_entry.get('module', 'unknown'),
                "message": log_entry.get('message', ''),
                "extra_data": log_entry.get('extra_data', {}),
                "user_id": log_entry.get('user_id'),
                "ip_address": log_entry.get('ip_address'),
                "user_agent": log_entry.get('user_agent'),
                "request_id": log_entry.get('request_id'),
                "created_at": datetime.fromtimestamp(log_entry.get('timestamp', time.time())).isoformat() + 'Z',
                "stack_trace": log_entry.get('stack_trace'),
                "context": log_entry.get('context', {})
            }
            
            return self.create_success_response(
                message="Log detayı alındı",
                data=log_detail
            )
            
        except ValueError:
            return self.create_error_response(
                message="Geçersiz log ID",
                status_code=400
            )
        except Exception as e:
            self.logger.error(f"Log detayı alınamadı: {e}")
            return self.create_error_response(
                message="Log detayı alınamadı",
                status_code=500
            )
    
    async def get_log_levels(self, request: Request) -> Response:
        """Log seviyelerini al"""
        try:
            # Log seviyeleri
            log_levels = [
                {
                    "level": "DEBUG",
                    "value": 10,
                    "description": "Detailed information, typically of interest only when diagnosing problems.",
                    "color": "#6c757d"
                },
                {
                    "level": "INFO",
                    "value": 20,
                    "description": "Confirmation that things are working as expected.",
                    "color": "#17a2b8"
                },
                {
                    "level": "WARNING",
                    "value": 30,
                    "description": "An indication that something unexpected happened, or indicative of some problem in the near future.",
                    "color": "#ffc107"
                },
                {
                    "level": "ERROR",
                    "value": 40,
                    "description": "Due to a more serious problem, the software has not been able to perform some function.",
                    "color": "#dc3545"
                },
                {
                    "level": "CRITICAL",
                    "value": 50,
                    "description": "A serious error, indicating that the program itself may be unable to continue running.",
                    "color": "#6f42c1"
                }
            ]
            
            # Mevcut log seviyesi
            current_level = "INFO"  # Bu değer settings'den alınabilir
            
            response_data = {
                "levels": log_levels,
                "current_level": current_level,
                "default_level": "INFO"
            }
            
            return self.create_success_response(
                message="Log seviyeleri alındı",
                data=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Log seviyeleri alınamadı: {e}")
            return self.create_error_response(
                message="Log seviyeleri alınamadı",
                status_code=500
            )