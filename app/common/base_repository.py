"""
Base repository class for database operations
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import and_, or_, desc, asc
from pydantic import BaseModel

from app.core.exceptions import ResourceNotFoundException, ValidationException

logger = logging.getLogger(__name__)

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=DeclarativeMeta)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model
    
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        try:
            obj_in_data = obj_in.dict()
            db_obj = self.model(**obj_in_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            
            logger.info(f"Created new {self.model.__name__} with ID: {db_obj.id}")
            return db_obj
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create {self.model.__name__}: {str(e)}")
            raise ValidationException(f"Failed to create {self.model.__name__}: {str(e)}")
    
    def get(self, id: Any) -> Optional[ModelType]:
        """Get a record by ID."""
        try:
            obj = self.db.query(self.model).filter(self.model.id == id).first()
            if obj:
                logger.debug(f"Retrieved {self.model.__name__} with ID: {id}")
            return obj
        
        except Exception as e:
            logger.error(f"Failed to get {self.model.__name__} with ID {id}: {str(e)}")
            raise
    
    def get_by_id(self, id: Any) -> ModelType:
        """Get a record by ID, raise exception if not found."""
        obj = self.get(id)
        if not obj:
            raise ResourceNotFoundException(self.model.__name__, id)
        return obj
    
    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """Get multiple records with optional filtering and pagination."""
        try:
            query = self.db.query(self.model)
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key) and value is not None:
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, key).in_(value))
                        else:
                            query = query.filter(getattr(self.model, key) == value)
            
            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                if order_desc:
                    query = query.order_by(desc(getattr(self.model, order_by)))
                else:
                    query = query.order_by(asc(getattr(self.model, order_by)))
            
            # Apply pagination
            objects = query.offset(skip).limit(limit).all()
            
            logger.debug(f"Retrieved {len(objects)} {self.model.__name__} records")
            return objects
        
        except Exception as e:
            logger.error(f"Failed to get multiple {self.model.__name__}: {str(e)}")
            raise
    
    def update(self, id: Any, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        """Update a record."""
        try:
            db_obj = self.get_by_id(id)
            
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            self.db.commit()
            self.db.refresh(db_obj)
            
            logger.info(f"Updated {self.model.__name__} with ID: {id}")
            return db_obj
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update {self.model.__name__} with ID {id}: {str(e)}")
            raise ValidationException(f"Failed to update {self.model.__name__}: {str(e)}")
    
    def delete(self, id: Any) -> bool:
        """Delete a record."""
        try:
            db_obj = self.get_by_id(id)
            self.db.delete(db_obj)
            self.db.commit()
            
            logger.info(f"Deleted {self.model.__name__} with ID: {id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete {self.model.__name__} with ID {id}: {str(e)}")
            raise ValidationException(f"Failed to delete {self.model.__name__}: {str(e)}")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        try:
            query = self.db.query(self.model)
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key) and value is not None:
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, key).in_(value))
                        else:
                            query = query.filter(getattr(self.model, key) == value)
            
            count = query.count()
            logger.debug(f"Counted {count} {self.model.__name__} records")
            return count
        
        except Exception as e:
            logger.error(f"Failed to count {self.model.__name__}: {str(e)}")
            raise
    
    def exists(self, id: Any) -> bool:
        """Check if a record exists."""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first() is not None
        
        except Exception as e:
            logger.error(f"Failed to check existence of {self.model.__name__} with ID {id}: {str(e)}")
            raise
    
    def bulk_create(self, objects: List[CreateSchemaType]) -> List[ModelType]:
        """Create multiple records in bulk."""
        try:
            db_objects = []
            for obj_in in objects:
                obj_in_data = obj_in.dict()
                db_obj = self.model(**obj_in_data)
                db_objects.append(db_obj)
            
            self.db.add_all(db_objects)
            self.db.commit()
            
            # Refresh all objects
            for db_obj in db_objects:
                self.db.refresh(db_obj)
            
            logger.info(f"Bulk created {len(db_objects)} {self.model.__name__} records")
            return db_objects
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to bulk create {self.model.__name__}: {str(e)}")
            raise ValidationException(f"Failed to bulk create {self.model.__name__}: {str(e)}")
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> bool:
        """Update multiple records in bulk."""
        try:
            for update_data in updates:
                if 'id' not in update_data:
                    continue
                
                obj_id = update_data.pop('id')
                self.db.query(self.model).filter(self.model.id == obj_id).update(update_data)
            
            self.db.commit()
            logger.info(f"Bulk updated {len(updates)} {self.model.__name__} records")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to bulk update {self.model.__name__}: {str(e)}")
            raise ValidationException(f"Failed to bulk update {self.model.__name__}: {str(e)}")
    
    def bulk_delete(self, ids: List[Any]) -> bool:
        """Delete multiple records in bulk."""
        try:
            self.db.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
            self.db.commit()
            
            logger.info(f"Bulk deleted {len(ids)} {self.model.__name__} records")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to bulk delete {self.model.__name__}: {str(e)}")
            raise ValidationException(f"Failed to bulk delete {self.model.__name__}: {str(e)}")
    
    def search(self, query: str, fields: List[str]) -> List[ModelType]:
        """Search records by query string in specified fields."""
        try:
            db_query = self.db.query(self.model)
            
            # Build search conditions
            conditions = []
            for field in fields:
                if hasattr(self.model, field):
                    conditions.append(getattr(self.model, field).ilike(f"%{query}%"))
            
            if conditions:
                db_query = db_query.filter(or_(*conditions))
            
            results = db_query.all()
            logger.debug(f"Search returned {len(results)} {self.model.__name__} records")
            return results
        
        except Exception as e:
            logger.error(f"Failed to search {self.model.__name__}: {str(e)}")
            raise
