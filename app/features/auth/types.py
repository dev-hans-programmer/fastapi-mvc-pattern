"""
Authentication types and models
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator, EmailStr

from app.common.validators import BaseValidator


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(False, description="Remember user login")
    
    @validator('email')
    def validate_email(cls, v):
        return BaseValidator.validate_email_format(v)
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "remember_me": False
            }
        }


class RegisterRequest(BaseModel):
    """Registration request model"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    
    @validator('email')
    def validate_email(cls, v):
        return BaseValidator.validate_email_format(v)
    
    @validator('password')
    def validate_password(cls, v):
        BaseValidator.validate_password_strength(v)
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            return BaseValidator.validate_phone_number(v)
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        BaseValidator.validate_string_length(v, min_length=1, max_length=50)
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890"
            }
        }


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user_id": 1,
                "email": "user@example.com"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        BaseValidator.validate_password_strength(v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "old_password": "oldpassword123",
                "new_password": "NewSecurePass123!"
            }
        }


class ForgotPasswordRequest(BaseModel):
    """Forgot password request model"""
    email: EmailStr = Field(..., description="User email address")
    
    @validator('email')
    def validate_email(cls, v):
        return BaseValidator.validate_email_format(v)
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Reset password request model"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        BaseValidator.validate_password_strength(v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset_token_here",
                "new_password": "NewSecurePass123!"
            }
        }


class VerifyEmailRequest(BaseModel):
    """Verify email request model"""
    token: str = Field(..., description="Email verification token")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "verification_token_here"
            }
        }


class ResendVerificationRequest(BaseModel):
    """Resend verification request model"""
    email: EmailStr = Field(..., description="User email address")
    
    @validator('email')
    def validate_email(cls, v):
        return BaseValidator.validate_email_format(v)
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class AuthUser(BaseModel):
    """Authenticated user model"""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="Email verification status")
    role: str = Field("user", description="User role")
    created_at: datetime = Field(..., description="Account creation date")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "is_active": True,
                "is_verified": True,
                "role": "user",
                "created_at": "2024-01-01T00:00:00",
                "last_login": "2024-01-01T12:00:00"
            }
        }


class LoginSession(BaseModel):
    """Login session model"""
    session_id: str = Field(..., description="Session identifier")
    user_id: int = Field(..., description="User ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    device_info: Optional[str] = Field(None, description="Device information")
    login_time: datetime = Field(..., description="Login timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    is_active: bool = Field(True, description="Session active status")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "session_id": "session_123456",
                "user_id": 1,
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "device_info": "Chrome on Windows",
                "login_time": "2024-01-01T12:00:00",
                "last_activity": "2024-01-01T12:30:00",
                "is_active": True
            }
        }


class SecurityEvent(BaseModel):
    """Security event model"""
    event_id: str = Field(..., description="Event identifier")
    user_id: int = Field(..., description="User ID")
    event_type: str = Field(..., description="Event type")
    description: str = Field(..., description="Event description")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    timestamp: datetime = Field(..., description="Event timestamp")
    severity: str = Field("INFO", description="Event severity")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "event_id": "event_123456",
                "user_id": 1,
                "event_type": "LOGIN_SUCCESS",
                "description": "User logged in successfully",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "timestamp": "2024-01-01T12:00:00",
                "severity": "INFO"
            }
        }


class TwoFactorSetup(BaseModel):
    """Two-factor authentication setup model"""
    secret: str = Field(..., description="2FA secret key")
    qr_code: str = Field(..., description="QR code for setup")
    backup_codes: list[str] = Field(..., description="Backup codes")
    
    class Config:
        schema_extra = {
            "example": {
                "secret": "JBSWY3DPEHPK3PXP",
                "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
                "backup_codes": ["12345678", "87654321", "11111111"]
            }
        }


class TwoFactorVerification(BaseModel):
    """Two-factor authentication verification model"""
    code: str = Field(..., min_length=6, max_length=6, description="2FA code")
    
    @validator('code')
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError('Code must contain only digits')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "code": "123456"
            }
        }


class PasswordResetToken(BaseModel):
    """Password reset token model"""
    token: str = Field(..., description="Reset token")
    user_id: int = Field(..., description="User ID")
    expires_at: datetime = Field(..., description="Token expiration time")
    is_used: bool = Field(False, description="Token usage status")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "token": "reset_token_here",
                "user_id": 1,
                "expires_at": "2024-01-01T13:00:00",
                "is_used": False
            }
        }


class EmailVerificationToken(BaseModel):
    """Email verification token model"""
    token: str = Field(..., description="Verification token")
    user_id: int = Field(..., description="User ID")
    expires_at: datetime = Field(..., description="Token expiration time")
    is_used: bool = Field(False, description="Token usage status")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "token": "verification_token_here",
                "user_id": 1,
                "expires_at": "2024-01-02T00:00:00",
                "is_used": False
            }
        }
