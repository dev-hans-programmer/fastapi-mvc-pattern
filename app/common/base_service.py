"""
Base service class for business logic
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel

from app.common.base_repository import BaseRepository
from app.core.exceptions import ValidationException, BusinessLogicException
from app.core.decorators import log_execution_time, retry

logger = logging.getLogger(__name__)

# Type variables for generic service
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType, RepositoryType]):
    """Base service class with common business logic operations."""
    
    def __init__(self, repository: RepositoryType):
        self.repository = repository
    
    @log_execution_time
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new entity with business logic validation."""
        try:
            # Pre-creation validation
            self._validate_create(obj_in)
            
            # Create the entity
            entity = self.repository.create(obj_in)
            
            # Post-creation processing
            self._post_create(entity)
            
            logger.info(f"Successfully created {entity.__class__.__name__} with ID: {entity.id}")
            return entity
        
        except Exception as e:
            logger.error(f"Failed to create entity: {str(e)}")
            raise
    
    @log_execution_time
    def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get an entity by ID with business logic."""
        try:
            entity = self.repository.get_by_id(id)
            
            # Post-retrieval processing
            self._post_get(entity)
            
            return entity
        
        except Exception as e:
            logger.error(f"Failed to get entity by ID {id}: {str(e)}")
            raise
    
    @log_execution_time
    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """Get multiple entities with business logic filtering."""
        try:
            # Apply business logic filters
            business_filters = self._apply_business_filters(filters)
            
            entities = self.repository.get_multi(
                skip=skip,
                limit=limit,
                filters=business_filters,
                order_by=order_by,
                order_desc=order_desc
            )
            
            # Post-retrieval processing for each entity
            for entity in entities:
                self._post_get(entity)
            
            return entities
        
        except Exception as e:
            logger.error(f"Failed to get multiple entities: {str(e)}")
            raise
    
    @log_execution_time
    def update(self, id: Any, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        """Update an entity with business logic validation."""
        try:
            # Get existing entity
            existing_entity = self.repository.get_by_id(id)
            
            # Pre-update validation
            self._validate_update(existing_entity, obj_in)
            
            # Update the entity
            updated_entity = self.repository.update(id, obj_in)
            
            # Post-update processing
            self._post_update(existing_entity, updated_entity)
            
            logger.info(f"Successfully updated {updated_entity.__class__.__name__} with ID: {id}")
            return updated_entity
        
        except Exception as e:
            logger.error(f"Failed to update entity with ID {id}: {str(e)}")
            raise
    
    @log_execution_time
    def delete(self, id: Any) -> bool:
        """Delete an entity with business logic validation."""
        try:
            # Get existing entity
            existing_entity = self.repository.get_by_id(id)
            
            # Pre-delete validation
            self._validate_delete(existing_entity)
            
            # Delete the entity
            success = self.repository.delete(id)
            
            # Post-delete processing
            self._post_delete(existing_entity)
            
            logger.info(f"Successfully deleted {existing_entity.__class__.__name__} with ID: {id}")
            return success
        
        except Exception as e:
            logger.error(f"Failed to delete entity with ID {id}: {str(e)}")
            raise
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with business logic filtering."""
        try:
            business_filters = self._apply_business_filters(filters)
            return self.repository.count(business_filters)
        
        except Exception as e:
            logger.error(f"Failed to count entities: {str(e)}")
            raise
    
    def exists(self, id: Any) -> bool:
        """Check if an entity exists."""
        try:
            return self.repository.exists(id)
        
        except Exception as e:
            logger.error(f"Failed to check existence of entity with ID {id}: {str(e)}")
            raise
    
    @log_execution_time
    def bulk_create(self, objects: List[CreateSchemaType]) -> List[ModelType]:
        """Create multiple entities with business logic validation."""
        try:
            # Validate all objects
            for obj_in in objects:
                self._validate_create(obj_in)
            
            # Create entities
            entities = self.repository.bulk_create(objects)
            
            # Post-creation processing
            for entity in entities:
                self._post_create(entity)
            
            logger.info(f"Successfully bulk created {len(entities)} entities")
            return entities
        
        except Exception as e:
            logger.error(f"Failed to bulk create entities: {str(e)}")
            raise
    
    def search(self, query: str, fields: List[str]) -> List[ModelType]:
        """Search entities with business logic."""
        try:
            entities = self.repository.search(query, fields)
            
            # Post-retrieval processing
            for entity in entities:
                self._post_get(entity)
            
            return entities
        
        except Exception as e:
            logger.error(f"Failed to search entities: {str(e)}")
            raise
    
    # Abstract methods for business logic customization
    def _validate_create(self, obj_in: CreateSchemaType) -> None:
        """Validate object before creation. Override in subclasses."""
        pass
    
    def _validate_update(self, existing_entity: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> None:
        """Validate object before update. Override in subclasses."""
        pass
    
    def _validate_delete(self, existing_entity: ModelType) -> None:
        """Validate object before deletion. Override in subclasses."""
        pass
    
    def _post_create(self, entity: ModelType) -> None:
        """Post-creation processing. Override in subclasses."""
        pass
    
    def _post_get(self, entity: ModelType) -> None:
        """Post-retrieval processing. Override in subclasses."""
        pass
    
    def _post_update(self, old_entity: ModelType, new_entity: ModelType) -> None:
        """Post-update processing. Override in subclasses."""
        pass
    
    def _post_delete(self, entity: ModelType) -> None:
        """Post-deletion processing. Override in subclasses."""
        pass
    
    def _apply_business_filters(self, filters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Apply business logic filters. Override in subclasses."""
        return filters
    
    # Utility methods
    def _validate_required_fields(self, obj: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate that required fields are present and not empty."""
        for field in required_fields:
            if field not in obj or obj[field] is None:
                raise ValidationException(f"Field '{field}' is required")
            
            if isinstance(obj[field], str) and not obj[field].strip():
                raise ValidationException(f"Field '{field}' cannot be empty")
    
    def _validate_unique_fields(self, obj: Dict[str, Any], unique_fields: List[str], exclude_id: Optional[Any] = None) -> None:
        """Validate that unique fields don't conflict with existing records."""
        for field in unique_fields:
            if field in obj and obj[field] is not None:
                filters = {field: obj[field]}
                existing = self.repository.get_multi(filters=filters)
                
                if existing:
                    # If updating, exclude the current record
                    if exclude_id is not None:
                        existing = [e for e in existing if e.id != exclude_id]
                    
                    if existing:
                        raise ValidationException(f"Value '{obj[field]}' for field '{field}' already exists")
    
    def _validate_enum_fields(self, obj: Dict[str, Any], enum_fields: Dict[str, List[str]]) -> None:
        """Validate that enum fields have valid values."""
        for field, valid_values in enum_fields.items():
            if field in obj and obj[field] is not None:
                if obj[field] not in valid_values:
                    raise ValidationException(f"Invalid value '{obj[field]}' for field '{field}'. Valid values are: {valid_values}")
    
    def _validate_business_rules(self, obj: Dict[str, Any], entity: Optional[ModelType] = None) -> None:
        """Validate business rules. Override in subclasses."""
        pass
