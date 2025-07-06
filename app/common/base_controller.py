"""
Base controller class for API endpoints
"""
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.common.base_service import BaseService
from app.core.exceptions import (
    BaseAppException,
    ValidationException,
    ResourceNotFoundException,
    BusinessLogicException
)

logger = logging.getLogger(__name__)

# Type variables for generic controller
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)
ServiceType = TypeVar("ServiceType", bound=BaseService)


class BaseController:
    """Base controller class with common CRUD operations."""
    
    def __init__(self, service: ServiceType):
        self.service = service
    
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new entity."""
        try:
            return self.service.create(obj_in)
        
        except ValidationException as e:
            logger.error(f"Validation error during creation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except BaseAppException as e:
            logger.error(f"Application error during creation: {str(e)}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error during creation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_by_id(self, id: Any) -> ModelType:
        """Get an entity by ID."""
        try:
            return self.service.get_by_id(id)
        
        except ResourceNotFoundException as e:
            logger.error(f"Resource not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        except BaseAppException as e:
            logger.error(f"Application error during retrieval: {str(e)}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error during retrieval: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> Dict[str, Any]:
        """Get multiple entities with pagination."""
        try:
            entities = self.service.get_multi(
                skip=skip,
                limit=limit,
                filters=filters,
                order_by=order_by,
                order_desc=order_desc
            )
            
            total_count = self.service.count(filters)
            
            return {
                "items": entities,
                "total": total_count,
                "page": (skip // limit) + 1 if limit > 0 else 1,
                "size": limit,
                "pages": (total_count + limit - 1) // limit if limit > 0 else 1
            }
        
        except BaseAppException as e:
            logger.error(f"Application error during multi-retrieval: {str(e)}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error during multi-retrieval: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def update(self, id: Any, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        """Update an entity."""
        try:
            return self.service.update(id, obj_in)
        
        except ResourceNotFoundException as e:
            logger.error(f"Resource not found during update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        except ValidationException as e:
            logger.error(f"Validation error during update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except BaseAppException as e:
            logger.error(f"Application error during update: {str(e)}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error during update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def delete(self, id: Any) -> Dict[str, Any]:
        """Delete an entity."""
        try:
            success = self.service.delete(id)
            
            if success:
                return {"message": "Entity deleted successfully", "id": id}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete entity"
                )
        
        except ResourceNotFoundException as e:
            logger.error(f"Resource not found during deletion: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        except BusinessLogicException as e:
            logger.error(f"Business logic error during deletion: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        except BaseAppException as e:
            logger.error(f"Application error during deletion: {str(e)}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error during deletion: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def bulk_create(self, objects: List[CreateSchemaType]) -> Dict[str, Any]:
        """Create multiple entities in bulk."""
        try:
            entities = self.service.bulk_create(objects)
            
            return {
                "message": f"Successfully created {len(entities)} entities",
                "count": len(entities),
                "items": entities
            }
        
        except ValidationException as e:
            logger.error(f"Validation error during bulk creation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except BaseAppException as e:
            logger.error(f"Application error during bulk creation: {str(e)}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error during bulk creation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def search(self, query: str, fields: List[str]) -> List[ModelType]:
        """Search entities."""
        try:
            if not query.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Search query cannot be empty"
                )
            
            if not fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Search fields must be specified"
                )
            
            return self.service.search(query, fields)
        
        except BaseAppException as e:
            logger.error(f"Application error during search: {str(e)}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error during search: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """Count entities."""
        try:
            count = self.service.count(filters)
            return {"count": count}
        
        except BaseAppException as e:
            logger.error(f"Application error during count: {str(e)}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error during count: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def exists(self, id: Any) -> Dict[str, bool]:
        """Check if an entity exists."""
        try:
            exists = self.service.exists(id)
            return {"exists": exists, "id": id}
        
        except Exception as e:
            logger.error(f"Unexpected error during existence check: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def _validate_pagination_params(self, page: int, size: int) -> tuple:
        """Validate pagination parameters."""
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be greater than 0"
            )
        
        if size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be greater than 0"
            )
        
        if size > 1000:  # Maximum page size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size cannot exceed 1000"
            )
        
        skip = (page - 1) * size
        return skip, size
    
    def _validate_sort_params(self, sort_by: Optional[str], allowed_fields: List[str]) -> None:
        """Validate sort parameters."""
        if sort_by and sort_by not in allowed_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort field. Allowed fields: {allowed_fields}"
            )
