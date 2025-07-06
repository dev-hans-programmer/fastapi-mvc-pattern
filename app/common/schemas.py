"""
Common Pydantic schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class TimestampMixin(BaseModel):
    """Mixin for entities with timestamp fields."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IdMixin(BaseModel):
    """Mixin for entities with ID field."""
    id: Optional[Union[int, str]] = None


class PaginationParams(BaseModel):
    """Pagination parameters schema."""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database queries."""
        return (self.page - 1) * self.size


class SortParams(BaseModel):
    """Sort parameters schema."""
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_desc: bool = Field(False, description="Sort in descending order")


class FilterParams(BaseModel):
    """Base filter parameters schema."""
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter parameters")


class SearchParams(BaseModel):
    """Search parameters schema."""
    query: str = Field(..., min_length=1, description="Search query")
    fields: List[str] = Field(..., min_items=1, description="Fields to search in")


class PaginatedResponse(BaseModel):
    """Paginated response schema."""
    items: List[Any]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")
    
    @validator('pages', pre=True, always=True)
    def calculate_pages(cls, v, values):
        """Calculate total pages based on total and size."""
        total = values.get('total', 0)
        size = values.get('size', 1)
        return (total + size - 1) // size if size > 0 else 1


class BulkCreateResponse(BaseModel):
    """Bulk create response schema."""
    message: str
    count: int
    items: List[Any]


class BulkUpdateResponse(BaseModel):
    """Bulk update response schema."""
    message: str
    count: int
    updated_ids: List[Union[int, str]]


class BulkDeleteResponse(BaseModel):
    """Bulk delete response schema."""
    message: str
    count: int
    deleted_ids: List[Union[int, str]]


class CountResponse(BaseModel):
    """Count response schema."""
    count: int


class ExistsResponse(BaseModel):
    """Exists response schema."""
    exists: bool
    id: Union[int, str]


class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: Dict[str, Any] = Field(
        ...,
        description="Error details",
        example={
            "message": "Validation failed",
            "code": 422,
            "details": {},
            "type": "ValidationError"
        }
    )


class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment")
    checks: Dict[str, Any] = Field(..., description="Individual health checks")


class TaskStatusResponse(BaseModel):
    """Background task status response schema."""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskSubmissionResponse(BaseModel):
    """Task submission response schema."""
    task_id: str
    message: str
    status: str = "submitted"


class ValidationErrorDetail(BaseModel):
    """Validation error detail schema."""
    field: str
    message: str
    value: Optional[Any] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""
    message: str = "Validation failed"
    errors: List[ValidationErrorDetail]


class StatusResponse(BaseModel):
    """Generic status response schema."""
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class MetricsResponse(BaseModel):
    """Metrics response schema."""
    metrics: Dict[str, Any]
    timestamp: datetime
    period: str


class ConfigResponse(BaseModel):
    """Configuration response schema."""
    environment: str
    debug: bool
    version: str
    features: Dict[str, bool]


# Base schemas for common operations
class BaseCreateSchema(BaseModel):
    """Base schema for create operations."""
    pass


class BaseUpdateSchema(BaseModel):
    """Base schema for update operations."""
    pass


class BaseResponseSchema(BaseModel):
    """Base schema for response operations."""
    pass


class BaseFilterSchema(BaseModel):
    """Base schema for filter operations."""
    pass


# Utility functions for schema validation
def validate_email(email: str) -> str:
    """Validate email format."""
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    return email.lower()


def validate_phone(phone: str) -> str:
    """Validate phone number format."""
    import re
    
    # Remove all non-digit characters
    cleaned = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    if len(cleaned) < 10 or len(cleaned) > 15:
        raise ValueError("Invalid phone number length")
    
    return cleaned


def validate_password_strength(password: str) -> str:
    """Validate password strength."""
    import re
    
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        raise ValueError("Password must contain at least one special character")
    
    return password
