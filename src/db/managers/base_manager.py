"""
Base Manager module - Temel manager

Bu modül tüm database manager'lar için temel sınıfı sağlar.
Ortak CRUD işlemleri ve database işlemlerini içerir.
"""

from typing import Dict, Any, List, Optional, Type, Union
from datetime import datetime
from peewee import Model, DoesNotExist, IntegrityError
import threading

from ...core.constants import LogLevel
from ...utils.logger import logger


class BaseManager:
    """
    Temel database manager sınıfı.
    
    Bu sınıf tüm database manager'lar için ortak fonksiyonları sağlar.
    """
    
    def __init__(self, model_class: Type[Model]):
        """
        BaseManager'ı başlatır.
        
        Args:
            model_class: Yönetilecek Peewee model sınıfı
        """
        self.model_class = model_class
        self.logger = logger
        self.lock = threading.Lock()
        
        # Manager istatistikleri
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def create(self, **kwargs) -> Optional[Model]:
        """
        Yeni kayıt oluşturur.
        
        Args:
            **kwargs: Model field'ları
            
        Returns:
            Oluşturulan model instance
        """
        try:
            with self.lock:
                # Timestamps ekle
                if hasattr(self.model_class, 'created_at') and 'created_at' not in kwargs:
                    kwargs['created_at'] = datetime.now()
                
                if hasattr(self.model_class, 'updated_at') and 'updated_at' not in kwargs:
                    kwargs['updated_at'] = datetime.now()
                
                # Model oluştur
                instance = self.model_class.create(**kwargs)
                
                self.stats["total_queries"] += 1
                self.stats["successful_queries"] += 1
                
                self.logger.debug(f"Created {self.model_class.__name__} with id: {instance.id}")
                return instance
                
        except IntegrityError as e:
            self.logger.error(f"Integrity error creating {self.model_class.__name__}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return None
        except Exception as e:
            self.logger.error(f"Error creating {self.model_class.__name__}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return None
    
    def get_by_id(self, record_id: int) -> Optional[Model]:
        """
        ID'ye göre kayıt getirir.
        
        Args:
            record_id: Kayıt ID'si
            
        Returns:
            Model instance veya None
        """
        try:
            instance = self.model_class.get_by_id(record_id)
            
            self.stats["total_queries"] += 1
            self.stats["successful_queries"] += 1
            
            return instance
            
        except DoesNotExist:
            self.logger.warning(f"{self.model_class.__name__} not found with id: {record_id}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return None
        except Exception as e:
            self.logger.error(f"Error getting {self.model_class.__name__} by id {record_id}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return None
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[Model]:
        """
        Belirli field'a göre kayıt getirir.
        
        Args:
            field_name: Field adı
            value: Aranacak değer
            
        Returns:
            Model instance veya None
        """
        try:
            field = getattr(self.model_class, field_name)
            instance = self.model_class.get(field == value)
            
            self.stats["total_queries"] += 1
            self.stats["successful_queries"] += 1
            
            return instance
            
        except DoesNotExist:
            self.logger.warning(f"{self.model_class.__name__} not found with {field_name}: {value}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return None
        except Exception as e:
            self.logger.error(f"Error getting {self.model_class.__name__} by {field_name}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return None
    
    def get_all(self, limit: int = None, offset: int = None, order_by: str = None) -> List[Model]:
        """
        Tüm kayıtları getirir.
        
        Args:
            limit: Maksimum kayıt sayısı
            offset: Başlangıç offset'i
            order_by: Sıralama field'ı
            
        Returns:
            Model instance listesi
        """
        try:
            query = self.model_class.select()
            
            # Sıralama
            if order_by:
                if order_by.startswith('-'):
                    # Descending order
                    field_name = order_by[1:]
                    field = getattr(self.model_class, field_name)
                    query = query.order_by(field.desc())
                else:
                    # Ascending order
                    field = getattr(self.model_class, order_by)
                    query = query.order_by(field)
            
            # Pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            instances = list(query)
            
            self.stats["total_queries"] += 1
            self.stats["successful_queries"] += 1
            
            return instances
            
        except Exception as e:
            self.logger.error(f"Error getting all {self.model_class.__name__}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return []
    
    def get_by_filters(self, filters: Dict[str, Any], limit: int = None, 
                      offset: int = None, order_by: str = None) -> List[Model]:
        """
        Filtrelere göre kayıtları getirir.
        
        Args:
            filters: Filtre dictionary'si
            limit: Maksimum kayıt sayısı
            offset: Başlangıç offset'i
            order_by: Sıralama field'ı
            
        Returns:
            Model instance listesi
        """
        try:
            query = self.model_class.select()
            
            # Filtreleri uygula
            for field_name, value in filters.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    if isinstance(value, list):
                        # IN operatörü
                        query = query.where(field.in_(value))
                    elif isinstance(value, dict) and 'operator' in value:
                        # Özel operatör
                        operator = value['operator']
                        val = value['value']
                        
                        if operator == 'like':
                            query = query.where(field.contains(val))
                        elif operator == 'ilike':
                            query = query.where(field.icontains(val))
                        elif operator == 'gt':
                            query = query.where(field > val)
                        elif operator == 'gte':
                            query = query.where(field >= val)
                        elif operator == 'lt':
                            query = query.where(field < val)
                        elif operator == 'lte':
                            query = query.where(field <= val)
                        elif operator == 'ne':
                            query = query.where(field != val)
                        else:
                            query = query.where(field == val)
                    else:
                        # Eşitlik kontrolü
                        query = query.where(field == value)
            
            # Sıralama
            if order_by:
                if order_by.startswith('-'):
                    # Descending order
                    field_name = order_by[1:]
                    field = getattr(self.model_class, field_name)
                    query = query.order_by(field.desc())
                else:
                    # Ascending order
                    field = getattr(self.model_class, order_by)
                    query = query.order_by(field)
            
            # Pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            instances = list(query)
            
            self.stats["total_queries"] += 1
            self.stats["successful_queries"] += 1
            
            return instances
            
        except Exception as e:
            self.logger.error(f"Error getting {self.model_class.__name__} by filters: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return []
    
    def update(self, record_id: int, **kwargs) -> bool:
        """
        Kayıt günceller.
        
        Args:
            record_id: Güncellenecek kayıt ID'si
            **kwargs: Güncellenecek field'lar
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            with self.lock:
                # Instance'ı bul
                instance = self.get_by_id(record_id)
                if not instance:
                    return False
                
                # Updated timestamp ekle
                if hasattr(self.model_class, 'updated_at'):
                    kwargs['updated_at'] = datetime.now()
                
                # Field'ları güncelle
                for field_name, value in kwargs.items():
                    if hasattr(instance, field_name):
                        setattr(instance, field_name, value)
                
                # Kaydet
                instance.save()
                
                self.stats["total_queries"] += 1
                self.stats["successful_queries"] += 1
                
                self.logger.debug(f"Updated {self.model_class.__name__} with id: {record_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating {self.model_class.__name__} with id {record_id}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return False
    
    def delete(self, record_id: int) -> bool:
        """
        Kayıt siler.
        
        Args:
            record_id: Silinecek kayıt ID'si
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            with self.lock:
                # Instance'ı bul
                instance = self.get_by_id(record_id)
                if not instance:
                    return False
                
                # Sil
                instance.delete_instance()
                
                self.stats["total_queries"] += 1
                self.stats["successful_queries"] += 1
                
                self.logger.debug(f"Deleted {self.model_class.__name__} with id: {record_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting {self.model_class.__name__} with id {record_id}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return False
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Kayıt sayısını döndürür.
        
        Args:
            filters: Filtre dictionary'si (opsiyonel)
            
        Returns:
            Kayıt sayısı
        """
        try:
            query = self.model_class.select()
            
            # Filtreleri uygula
            if filters:
                for field_name, value in filters.items():
                    if hasattr(self.model_class, field_name):
                        field = getattr(self.model_class, field_name)
                        query = query.where(field == value)
            
            count = query.count()
            
            self.stats["total_queries"] += 1
            self.stats["successful_queries"] += 1
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting {self.model_class.__name__}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return 0
    
    def exists(self, **kwargs) -> bool:
        """
        Kayıt var mı kontrol eder.
        
        Args:
            **kwargs: Kontrol edilecek field'lar
            
        Returns:
            True if exists, False otherwise
        """
        try:
            query = self.model_class.select()
            
            # Filtreleri uygula
            for field_name, value in kwargs.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    query = query.where(field == value)
            
            exists = query.exists()
            
            self.stats["total_queries"] += 1
            self.stats["successful_queries"] += 1
            
            return exists
            
        except Exception as e:
            self.logger.error(f"Error checking existence in {self.model_class.__name__}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return False
    
    def bulk_create(self, records: List[Dict[str, Any]]) -> int:
        """
        Toplu kayıt oluşturur.
        
        Args:
            records: Oluşturulacak kayıtların listesi
            
        Returns:
            Oluşturulan kayıt sayısı
        """
        try:
            with self.lock:
                created_count = 0
                
                # Timestamps ekle
                now = datetime.now()
                for record in records:
                    if hasattr(self.model_class, 'created_at') and 'created_at' not in record:
                        record['created_at'] = now
                    
                    if hasattr(self.model_class, 'updated_at') and 'updated_at' not in record:
                        record['updated_at'] = now
                
                # Bulk insert
                with self.model_class._meta.database.atomic():
                    for batch in self._batch_iterator(records, 100):  # 100'er batch
                        created_count += len(self.model_class.insert_many(batch).execute())
                
                self.stats["total_queries"] += 1
                self.stats["successful_queries"] += 1
                
                self.logger.info(f"Bulk created {created_count} {self.model_class.__name__} records")
                return created_count
                
        except Exception as e:
            self.logger.error(f"Error bulk creating {self.model_class.__name__}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return 0
    
    def bulk_update(self, updates: List[Dict[str, Any]], id_field: str = 'id') -> int:
        """
        Toplu güncelleme yapar.
        
        Args:
            updates: Güncellenecek kayıtların listesi (id ve field'lar içermeli)
            id_field: ID field adı
            
        Returns:
            Güncellenen kayıt sayısı
        """
        try:
            with self.lock:
                updated_count = 0
                now = datetime.now()
                
                with self.model_class._meta.database.atomic():
                    for update_data in updates:
                        if id_field not in update_data:
                            continue
                        
                        record_id = update_data.pop(id_field)
                        
                        # Updated timestamp ekle
                        if hasattr(self.model_class, 'updated_at'):
                            update_data['updated_at'] = now
                        
                        # Güncelle
                        query = self.model_class.update(**update_data).where(
                            getattr(self.model_class, id_field) == record_id
                        )
                        updated_count += query.execute()
                
                self.stats["total_queries"] += 1
                self.stats["successful_queries"] += 1
                
                self.logger.info(f"Bulk updated {updated_count} {self.model_class.__name__} records")
                return updated_count
                
        except Exception as e:
            self.logger.error(f"Error bulk updating {self.model_class.__name__}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return 0
    
    def bulk_delete(self, filters: Dict[str, Any]) -> int:
        """
        Toplu silme yapar.
        
        Args:
            filters: Silinecek kayıtların filtreleri
            
        Returns:
            Silinen kayıt sayısı
        """
        try:
            with self.lock:
                query = self.model_class.delete()
                
                # Filtreleri uygula
                for field_name, value in filters.items():
                    if hasattr(self.model_class, field_name):
                        field = getattr(self.model_class, field_name)
                        query = query.where(field == value)
                
                deleted_count = query.execute()
                
                self.stats["total_queries"] += 1
                self.stats["successful_queries"] += 1
                
                self.logger.info(f"Bulk deleted {deleted_count} {self.model_class.__name__} records")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Error bulk deleting {self.model_class.__name__}: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Manager istatistiklerini döndürür.
        
        Returns:
            Manager istatistikleri
        """
        try:
            with self.lock:
                total_records = self.count()
                success_rate = (self.stats["successful_queries"] / self.stats["total_queries"] * 100) \
                               if self.stats["total_queries"] > 0 else 0
                
                return {
                    "model_name": self.model_class.__name__,
                    "total_records": total_records,
                    "total_queries": self.stats["total_queries"],
                    "successful_queries": self.stats["successful_queries"],
                    "failed_queries": self.stats["failed_queries"],
                    "success_rate_percent": round(success_rate, 2),
                    "cache_hits": self.stats["cache_hits"],
                    "cache_misses": self.stats["cache_misses"]
                }
                
        except Exception as e:
            self.logger.error(f"Error getting statistics for {self.model_class.__name__}: {e}")
            return {}
    
    def _batch_iterator(self, iterable: List, batch_size: int):
        """
        Listeyi batch'lere böler.
        
        Args:
            iterable: Bölünecek liste
            batch_size: Batch boyutu
            
        Yields:
            Batch'ler
        """
        for i in range(0, len(iterable), batch_size):
            yield iterable[i:i + batch_size]
