"""
Base service class for business logic layer
"""

import logging
from typing import Any, Dict, List, Optional
from abc import ABC
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Base service class providing common business logic operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """
        Validate that all required fields are present and not empty
        """
        missing_fields = []
        empty_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                empty_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        if empty_fields:
            raise ValueError(f"Empty required fields: {', '.join(empty_fields)}")
    
    def validate_field_types(self, data: Dict[str, Any], field_types: Dict[str, type]) -> None:
        """
        Validate field types
        """
        invalid_fields = []
        
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    invalid_fields.append(f"{field} (expected {expected_type.__name__}, got {type(data[field]).__name__})")
        
        if invalid_fields:
            raise TypeError(f"Invalid field types: {', '.join(invalid_fields)}")
    
    def sanitize_string_fields(self, data: Dict[str, Any], string_fields: List[str]) -> Dict[str, Any]:
        """
        Sanitize string fields by stripping whitespace
        """
        sanitized_data = data.copy()
        
        for field in string_fields:
            if field in sanitized_data and isinstance(sanitized_data[field], str):
                sanitized_data[field] = sanitized_data[field].strip()
        
        return sanitized_data
    
    def normalize_email(self, email: str) -> str:
        """
        Normalize email address
        """
        if not email:
            return email
        
        return email.strip().lower()
    
    def validate_pagination_params(self, page: int, limit: int, max_limit: int = 1000) -> tuple:
        """
        Validate and normalize pagination parameters
        """
        # Ensure page is at least 1
        page = max(1, page)
        
        # Ensure limit is within bounds
        limit = max(1, min(limit, max_limit))
        
        # Calculate offset
        offset = (page - 1) * limit
        
        return page, limit, offset
    
    def validate_sort_params(self, sort_by: Optional[str], sort_order: str, allowed_fields: List[str]) -> tuple:
        """
        Validate sorting parameters
        """
        # Validate sort field
        if sort_by and sort_by not in allowed_fields:
            raise ValueError(f"Invalid sort field: {sort_by}. Allowed fields: {', '.join(allowed_fields)}")
        
        # Validate sort order
        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "asc"
        
        return sort_by, sort_order.lower()
    
    def apply_date_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply date range filters
        """
        processed_filters = filters.copy()
        
        # Handle date ranges
        if "date_from" in filters and "date_to" in filters:
            date_from = filters["date_from"]
            date_to = filters["date_to"]
            
            if isinstance(date_from, str):
                date_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            if isinstance(date_to, str):
                date_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            
            processed_filters["created_at"] = {
                "gte": date_from,
                "lte": date_to,
            }
            
            # Remove original filters
            processed_filters.pop("date_from", None)
            processed_filters.pop("date_to", None)
        
        return processed_filters
    
    def build_search_filters(self, query: str, search_fields: List[str]) -> Dict[str, Any]:
        """
        Build search filters for text search
        """
        if not query or not search_fields:
            return {}
        
        # For now, we'll use simple LIKE search
        # In production, you might want to use full-text search
        search_filters = {}
        for field in search_fields:
            search_filters[field] = {"like": query}
        
        return search_filters
    
    def log_operation(self, operation: str, entity_type: str, entity_id: Optional[str] = None, 
                     user_id: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None):
        """
        Log business operation
        """
        log_data = {
            "operation": operation,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        self.logger.info(f"Operation: {operation}", extra=log_data)
    
    def calculate_pagination_info(self, total: int, page: int, limit: int) -> Dict[str, Any]:
        """
        Calculate pagination information
        """
        total_pages = (total + limit - 1) // limit  # Ceiling division
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
            "next_page": page + 1 if has_next else None,
            "prev_page": page - 1 if has_prev else None,
        }
    
    def format_response(self, data: Any, pagination: Optional[Dict[str, Any]] = None, 
                       meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format service response with consistent structure
        """
        response = {
            "data": data,
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if pagination:
            response["pagination"] = pagination
        
        if meta:
            response["meta"] = meta
        
        return response
    
    def format_error_response(self, error: str, error_code: Optional[str] = None, 
                            details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format error response with consistent structure
        """
        response = {
            "data": None,
            "success": False,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if error_code:
            response["error_code"] = error_code
        
        if details:
            response["details"] = details
        
        return response
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Service health check
        """
        return {
            "service": self.__class__.__name__,
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def __enter__(self):
        """
        Context manager entry
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit
        """
        # Clean up resources if needed
        pass
    
    async def __aenter__(self):
        """
        Async context manager entry
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit
        """
        # Clean up resources if needed
        pass
