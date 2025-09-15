"""
Base service class for all business logic services.

This module provides the foundation for all service classes in the application.
It includes common functionality like logging, error handling, and database access.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from datetime import datetime

from ..utils.logger import logger
from ..db.database import database
from ..db.models import BaseModel

T = TypeVar('T', bound=BaseModel)


class BaseService(ABC, Generic[T]):
    """
    Base service class that provides common functionality for all services.
    
    This class serves as the foundation for all business logic services,
    providing database access, logging, and common CRUD operations.
    """
    
    def __init__(self, model_class: Type[T]):
        """
        Initialize the base service.
        
        Args:
            model_class: The Peewee model class this service manages
        """
        self.model_class = model_class
        self.logger = logger
        self.db = database
    
    async def create(self, **kwargs) -> Optional[T]:
        """
        Create a new record.
        
        Args:
            **kwargs: Field values for the new record
            
        Returns:
            The created record or None if creation failed
        """
        try:
            # Add timestamps if they exist
            if hasattr(self.model_class, 'created_at'):
                kwargs['created_at'] = datetime.now()
            if hasattr(self.model_class, 'updated_at'):
                kwargs['updated_at'] = datetime.now()
            
            # Create the record
            record = self.model_class.create(**kwargs)
            self.logger.info(f"Created {self.model_class.__name__} with ID: {record.id}")
            return record
            
        except Exception as e:
            self.logger.error(f"Failed to create {self.model_class.__name__}: {e}")
            return None
    
    async def get_by_id(self, record_id: int) -> Optional[T]:
        """
        Get a record by its ID.
        
        Args:
            record_id: The ID of the record to retrieve
            
        Returns:
            The record or None if not found
        """
        try:
            record = self.model_class.get_by_id(record_id)
            return record
        except self.model_class.DoesNotExist:
            self.logger.warning(f"{self.model_class.__name__} with ID {record_id} not found")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get {self.model_class.__name__} by ID {record_id}: {e}")
            return None
    
    async def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """
        Get all records with optional pagination.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of records
        """
        try:
            query = self.model_class.select()
            
            if offset > 0:
                query = query.offset(offset)
            
            if limit:
                query = query.limit(limit)
            
            records = list(query)
            self.logger.debug(f"Retrieved {len(records)} {self.model_class.__name__} records")
            return records
            
        except Exception as e:
            self.logger.error(f"Failed to get all {self.model_class.__name__} records: {e}")
            return []
    
    async def update(self, record_id: int, **kwargs) -> Optional[T]:
        """
        Update a record by its ID.
        
        Args:
            record_id: The ID of the record to update
            **kwargs: Field values to update
            
        Returns:
            The updated record or None if update failed
        """
        try:
            # Add updated timestamp if it exists
            if hasattr(self.model_class, 'updated_at'):
                kwargs['updated_at'] = datetime.now()
            
            # Update the record
            query = self.model_class.update(**kwargs).where(self.model_class.id == record_id)
            rows_affected = query.execute()
            
            if rows_affected > 0:
                updated_record = await self.get_by_id(record_id)
                self.logger.info(f"Updated {self.model_class.__name__} with ID: {record_id}")
                return updated_record
            else:
                self.logger.warning(f"No {self.model_class.__name__} found with ID: {record_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to update {self.model_class.__name__} with ID {record_id}: {e}")
            return None
    
    async def delete(self, record_id: int) -> bool:
        """
        Delete a record by its ID.
        
        Args:
            record_id: The ID of the record to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            query = self.model_class.delete().where(self.model_class.id == record_id)
            rows_affected = query.execute()
            
            if rows_affected > 0:
                self.logger.info(f"Deleted {self.model_class.__name__} with ID: {record_id}")
                return True
            else:
                self.logger.warning(f"No {self.model_class.__name__} found with ID: {record_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to delete {self.model_class.__name__} with ID {record_id}: {e}")
            return False
    
    async def exists(self, record_id: int) -> bool:
        """
        Check if a record exists by its ID.
        
        Args:
            record_id: The ID of the record to check
            
        Returns:
            True if the record exists, False otherwise
        """
        try:
            return self.model_class.select().where(self.model_class.id == record_id).exists()
        except Exception as e:
            self.logger.error(f"Failed to check existence of {self.model_class.__name__} with ID {record_id}: {e}")
            return False
    
    async def count(self) -> int:
        """
        Get the total count of records.
        
        Returns:
            The total number of records
        """
        try:
            return self.model_class.select().count()
        except Exception as e:
            self.logger.error(f"Failed to count {self.model_class.__name__} records: {e}")
            return 0
    
    @abstractmethod
    async def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate data for create/update operations.
        
        Args:
            data: The data to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        pass
    
    async def search(self, query: str, fields: List[str]) -> List[T]:
        """
        Search records by text in specified fields.
        
        Args:
            query: The search query
            fields: List of field names to search in
            
        Returns:
            List of matching records
        """
        try:
            search_conditions = []
            for field in fields:
                if hasattr(self.model_class, field):
                    field_obj = getattr(self.model_class, field)
                    search_conditions.append(field_obj.contains(query))
            
            if not search_conditions:
                return []
            
            # Combine conditions with OR
            from peewee import fn
            combined_condition = search_conditions[0]
            for condition in search_conditions[1:]:
                combined_condition |= condition
            
            records = list(self.model_class.select().where(combined_condition))
            self.logger.debug(f"Found {len(records)} {self.model_class.__name__} records matching '{query}'")
            return records
            
        except Exception as e:
            self.logger.error(f"Failed to search {self.model_class.__name__} records: {e}")
            return []
    
    def to_dict(self, record: T) -> Dict[str, Any]:
        """
        Convert a model instance to a dictionary.
        
        Args:
            record: The model instance to convert
            
        Returns:
            Dictionary representation of the record
        """
        try:
            data = {}
            for field in record._meta.fields:
                value = getattr(record, field)
                if isinstance(value, datetime):
                    data[field] = value.isoformat()
                elif hasattr(value, 'id'):  # Foreign key
                    data[field] = value.id
                else:
                    data[field] = value
            return data
        except Exception as e:
            self.logger.error(f"Failed to convert {self.model_class.__name__} to dict: {e}")
            return {}
    
    def from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a dictionary to model field values, handling type conversions.
        
        Args:
            data: Dictionary of field values
            
        Returns:
            Dictionary with properly typed values
        """
        try:
            converted_data = {}
            for field_name, value in data.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    field_type = type(field)
                    
                    # Handle datetime fields
                    if field_type == datetime and isinstance(value, str):
                        converted_data[field_name] = datetime.fromisoformat(value)
                    # Handle foreign key fields
                    elif hasattr(field, 'rel_model') and isinstance(value, int):
                        converted_data[field_name] = value
                    else:
                        converted_data[field_name] = value
            
            return converted_data
        except Exception as e:
            self.logger.error(f"Failed to convert dict to {self.model_class.__name__} fields: {e}")
            return data
