"""
Authentication validation schemas
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime

from app.features.auth.types import UserRole


class LoginRequest(BaseModel):
    """
    Login request validation schema
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class RegisterRequest(BaseModel):
    """
    Register request validation schema
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=2, max_length=100, description="User full name")
    role: Optional[UserRole] = Field(default=UserRole.USER, description="User role")
    
    @validator("password")
    def validate_password(cls, v):
        """
        Validate password strength
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v
    
    @validator("full_name")
    def validate_full_name(cls, v):
        """
        Validate full name
        """
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        
        if len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "full_name": "John Doe",
                "role": "user"
            }
        }


class RefreshTokenRequest(BaseModel):
    """
    Refresh token request validation schema
    """
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ChangePasswordRequest(BaseModel):
    """
    Change password request validation schema
    """
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator("new_password")
    def validate_new_password(cls, v):
        """
        Validate new password strength
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "NewSecurePass123"
            }
        }


class ResetPasswordRequest(BaseModel):
    """
    Reset password request validation schema
    """
    email: EmailStr = Field(..., description="User email address")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResetPasswordConfirmRequest(BaseModel):
    """
    Reset password confirm request validation schema
    """
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator("new_password")
    def validate_new_password(cls, v):
        """
        Validate new password strength
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset_token_here",
                "new_password": "NewSecurePass123"
            }
        }


class AuthResponse(BaseModel):
    """
    Authentication response schema
    """
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=1800, description="Token expiration time in seconds")
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    permissions: List[str] = Field(default=[], description="User permissions")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user_id": "user_123",
                "email": "user@example.com",
                "role": "user",
                "permissions": ["user:read", "product:read"]
            }
        }


class UserResponse(BaseModel):
    """
    User response schema
    """
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role")
    permissions: List[str] = Field(default=[], description="User permissions")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="User email verification status")
    created_at: Optional[datetime] = Field(None, description="User creation timestamp")
    last_login: Optional[datetime] = Field(None, description="User last login timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "user_123",
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "user",
                "permissions": ["user:read", "product:read"],
                "is_active": True,
                "is_verified": True,
                "created_at": "2023-01-01T00:00:00Z",
                "last_login": "2023-01-01T12:00:00Z"
            }
        }


class SessionResponse(BaseModel):
    """
    Session response schema
    """
    id: str = Field(..., description="Session ID")
    created_at: Optional[datetime] = Field(None, description="Session creation timestamp")
    last_activity: Optional[datetime] = Field(None, description="Session last activity timestamp")
    ip_address: Optional[str] = Field(None, description="Session IP address")
    user_agent: Optional[str] = Field(None, description="Session user agent")
    is_current: bool = Field(default=False, description="Current session indicator")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "session_123",
                "created_at": "2023-01-01T00:00:00Z",
                "last_activity": "2023-01-01T12:00:00Z",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "is_current": True
            }
        }


class TokenStatusResponse(BaseModel):
    """
    Token status response schema
    """
    valid: bool = Field(..., description="Token validity status")
    user_id: Optional[str] = Field(None, description="User ID if token is valid")
    email: Optional[str] = Field(None, description="User email if token is valid")
    role: Optional[str] = Field(None, description="User role if token is valid")
    expires_at: Optional[datetime] = Field(None, description="Token expiration timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "user_id": "user_123",
                "email": "user@example.com",
                "role": "user",
                "expires_at": "2023-01-01T12:30:00Z"
            }
        }


class PasswordStrengthResponse(BaseModel):
    """
    Password strength response schema
    """
    strength: str = Field(..., description="Password strength level")
    score: int = Field(..., description="Password strength score")
    issues: List[str] = Field(default=[], description="Password issues")
    is_valid: bool = Field(..., description="Password validity status")
    
    class Config:
        schema_extra = {
            "example": {
                "strength": "strong",
                "score": 5,
                "issues": [],
                "is_valid": True
            }
        }


class MessageResponse(BaseModel):
    """
    Generic message response schema
    """
    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Operation success status")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Operation completed successfully",
                "success": True
            }
        }


class ErrorResponse(BaseModel):
    """
    Error response schema
    """
    error: bool = Field(default=True, description="Error indicator")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict = Field(default={}, description="Error details")
    status_code: int = Field(..., description="HTTP status code")
    
    class Config:
        schema_extra = {
            "example": {
                "error": True,
                "error_code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": {"field_errors": {"email": "Invalid email format"}},
                "status_code": 422
            }
        }
