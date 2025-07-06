"""
Common response models and utilities
"""
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field

DataType = TypeVar("DataType")


class APIResponse(BaseModel, Generic[DataType]):
    """Base API response model"""
    
    success: bool = Field(description="Whether the request was successful")
    message: str = Field(description="Response message")
    data: Optional[DataType] = Field(None, description="Response data")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ErrorResponse(BaseModel):
    """Error response model"""
    
    success: bool = Field(False, description="Always false for errors")
    error: Dict[str, Any] = Field(description="Error details")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "type": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": {
                        "field": "email",
                        "issue": "Invalid email format"
                    }
                }
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_count: int = Field(description="Total number of items")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[DataType]):
    """Paginated response model"""
    
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(description="Response message")
    data: List[DataType] = Field(description="List of items")
    pagination: PaginationMeta = Field(description="Pagination metadata")


class ListResponse(BaseModel, Generic[DataType]):
    """List response model"""
    
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(description="Response message")
    data: List[DataType] = Field(description="List of items")
    count: int = Field(description="Number of items returned")


class SingleResponse(BaseModel, Generic[DataType]):
    """Single item response model"""
    
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(description="Response message")
    data: DataType = Field(description="Single item data")


class BulkResponse(BaseModel):
    """Bulk operation response model"""
    
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(description="Response message")
    created_count: int = Field(0, description="Number of items created")
    updated_count: int = Field(0, description="Number of items updated")
    deleted_count: int = Field(0, description="Number of items deleted")
    failed_count: int = Field(0, description="Number of items that failed")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors")


class StatusResponse(BaseModel):
    """Status response model"""
    
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(description="Response message")
    status: str = Field(description="Current status")
    timestamp: str = Field(description="Timestamp of the response")


class HealthResponse(BaseModel):
    """Health check response model"""
    
    status: str = Field(description="Health status")
    version: str = Field(description="Application version")
    timestamp: str = Field(description="Timestamp of the health check")
    services: Dict[str, Any] = Field(description="Status of dependent services")
    uptime: float = Field(description="Application uptime in seconds")


class TaskResponse(BaseModel):
    """Background task response model"""
    
    success: bool = Field(True, description="Whether the task was submitted successfully")
    message: str = Field(description="Response message")
    task_id: str = Field(description="Task identifier")
    status: str = Field(description="Task status")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")


class TaskStatusResponse(BaseModel):
    """Task status response model"""
    
    task_id: str = Field(description="Task identifier")
    status: str = Field(description="Task status")
    result: Optional[Any] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
    progress: Optional[Dict[str, Any]] = Field(None, description="Task progress")
    created_at: str = Field(description="Task creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


class FileUploadResponse(BaseModel):
    """File upload response model"""
    
    success: bool = Field(True, description="Whether the upload was successful")
    message: str = Field(description="Response message")
    file_id: str = Field(description="File identifier")
    filename: str = Field(description="Original filename")
    size: int = Field(description="File size in bytes")
    content_type: str = Field(description="File content type")
    url: Optional[str] = Field(None, description="File access URL")


class SearchResponse(BaseModel, Generic[DataType]):
    """Search response model"""
    
    success: bool = Field(True, description="Whether the search was successful")
    message: str = Field(description="Response message")
    query: str = Field(description="Search query")
    results: List[DataType] = Field(description="Search results")
    total_count: int = Field(description="Total number of results")
    search_time: float = Field(description="Search execution time in seconds")
    suggestions: List[str] = Field(default_factory=list, description="Search suggestions")


class ExportResponse(BaseModel):
    """Export response model"""
    
    success: bool = Field(True, description="Whether the export was successful")
    message: str = Field(description="Response message")
    export_id: str = Field(description="Export identifier")
    format: str = Field(description="Export format")
    record_count: int = Field(description="Number of records exported")
    download_url: Optional[str] = Field(None, description="Download URL")
    expires_at: Optional[str] = Field(None, description="URL expiration time")


class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    
    field: str = Field(description="Field name")
    message: str = Field(description="Error message")
    value: Any = Field(description="Invalid value")


class ValidationErrorResponse(BaseModel):
    """Validation error response model"""
    
    success: bool = Field(False, description="Always false for validation errors")
    error: Dict[str, Any] = Field(description="Error details")
    validation_errors: List[ValidationErrorDetail] = Field(description="List of validation errors")


# Response utility functions
def success_response(
    data: Any = None,
    message: str = "Success",
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a success response"""
    response = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    if meta is not None:
        response["meta"] = meta
    
    return response


def error_response(
    message: str,
    error_type: str = "APPLICATION_ERROR",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create an error response"""
    error_data = {
        "type": error_type,
        "message": message
    }
    
    if details:
        error_data["details"] = details
    
    return {
        "success": False,
        "error": error_data
    }


def paginated_response(
    data: List[Any],
    page: int,
    page_size: int,
    total_count: int,
    message: str = "Success"
) -> Dict[str, Any]:
    """Create a paginated response"""
    total_pages = (total_count + page_size - 1) // page_size
    
    return {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


def list_response(
    data: List[Any],
    message: str = "Success",
    count: Optional[int] = None
) -> Dict[str, Any]:
    """Create a list response"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "count": count or len(data)
    }


def single_response(
    data: Any,
    message: str = "Success"
) -> Dict[str, Any]:
    """Create a single item response"""
    return {
        "success": True,
        "message": message,
        "data": data
    }


def bulk_response(
    created_count: int = 0,
    updated_count: int = 0,
    deleted_count: int = 0,
    failed_count: int = 0,
    errors: Optional[List[Dict[str, Any]]] = None,
    message: str = "Bulk operation completed"
) -> Dict[str, Any]:
    """Create a bulk operation response"""
    return {
        "success": True,
        "message": message,
        "created_count": created_count,
        "updated_count": updated_count,
        "deleted_count": deleted_count,
        "failed_count": failed_count,
        "errors": errors or []
    }


def task_response(
    task_id: str,
    status: str = "PENDING",
    message: str = "Task submitted successfully"
) -> Dict[str, Any]:
    """Create a task response"""
    return {
        "success": True,
        "message": message,
        "task_id": task_id,
        "status": status
    }
