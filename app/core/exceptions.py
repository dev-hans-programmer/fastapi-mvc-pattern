"""
Custom exceptions and error handling
"""

import logging
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
import traceback

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class BaseAPIException(Exception):
    """
    Base exception class for API errors
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary
        """
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code,
        }


class ValidationException(BaseAPIException):
    """
    Validation error exception
    """
    
    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.field_errors = field_errors or {}
        combined_details = {"field_errors": self.field_errors}
        if details:
            combined_details.update(details)
        
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=combined_details,
        )


class AuthenticationException(BaseAPIException):
    """
    Authentication error exception
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class AuthorizationException(BaseAPIException):
    """
    Authorization error exception
    """
    
    def __init__(
        self,
        message: str = "Access denied",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )


class NotFoundException(BaseAPIException):
    """
    Resource not found exception
    """
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        combined_details = {}
        if resource_type:
            combined_details["resource_type"] = resource_type
        if resource_id:
            combined_details["resource_id"] = resource_id
        if details:
            combined_details.update(details)
        
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=combined_details,
        )


class ConflictException(BaseAPIException):
    """
    Conflict error exception
    """
    
    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT_ERROR",
            details=details,
        )


class BusinessLogicException(BaseAPIException):
    """
    Business logic error exception
    """
    
    def __init__(
        self,
        message: str = "Business logic error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details,
        )


class ExternalServiceException(BaseAPIException):
    """
    External service error exception
    """
    
    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        combined_details = {}
        if service_name:
            combined_details["service_name"] = service_name
        if details:
            combined_details.update(details)
        
        super().__init__(
            message=message,
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=combined_details,
        )


class RateLimitException(BaseAPIException):
    """
    Rate limit exceeded exception
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        combined_details = {}
        if retry_after:
            combined_details["retry_after"] = retry_after
        if details:
            combined_details.update(details)
        
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=combined_details,
        )


class DatabaseException(BaseAPIException):
    """
    Database error exception
    """
    
    def __init__(
        self,
        message: str = "Database error",
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        combined_details = {}
        if operation:
            combined_details["operation"] = operation
        if details:
            combined_details.update(details)
        
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=combined_details,
        )


class FileUploadException(BaseAPIException):
    """
    File upload error exception
    """
    
    def __init__(
        self,
        message: str = "File upload error",
        file_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        combined_details = {}
        if file_name:
            combined_details["file_name"] = file_name
        if details:
            combined_details.update(details)
        
        super().__init__(
            message=message,
            status_code=400,
            error_code="FILE_UPLOAD_ERROR",
            details=combined_details,
        )


# Exception handlers
async def base_api_exception_handler(request: Request, exc: BaseAPIException):
    """
    Handler for BaseAPIException and its subclasses
    """
    logger.error(
        f"API Exception: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler for HTTPException
    """
    logger.error(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": "HTTP_ERROR",
            "message": exc.detail,
            "details": {},
            "status_code": exc.status_code,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for RequestValidationError
    """
    field_errors = {}
    
    for error in exc.errors():
        field_name = ".".join(str(loc) for loc in error["loc"])
        field_errors[field_name] = error["msg"]
    
    logger.error(
        f"Validation Exception: {field_errors}",
        extra={
            "field_errors": field_errors,
            "path": request.url.path,
            "method": request.method,
        },
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": "Validation failed",
            "details": {"field_errors": field_errors},
            "status_code": 422,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handler for generic exceptions
    """
    error_id = id(exc)
    
    logger.error(
        f"Unhandled Exception [{error_id}]: {type(exc).__name__} - {str(exc)}",
        extra={
            "error_id": error_id,
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
        exc_info=True,
    )
    
    # Don't expose internal errors in production
    if settings.ENVIRONMENT == "production":
        message = "Internal server error"
        details = {"error_id": error_id}
    else:
        message = str(exc)
        details = {
            "error_id": error_id,
            "error_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        }
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": message,
            "details": details,
            "status_code": 500,
        },
    )


def setup_exception_handlers(app):
    """
    Setup exception handlers for the FastAPI app
    """
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")
