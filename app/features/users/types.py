"""
User types and models
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator, EmailStr
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.common.validators import BaseValidator


class User(Base):
    """User database model"""
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_logout: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Profile fields
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    
    @validator('email')
    def validate_email(cls, v):
        return BaseValidator.validate_email_format(v)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            return BaseValidator.validate_phone_number(v)
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        BaseValidator.validate_string_length(v, min_length=1, max_length=50)
        return v.strip()


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8, description="User password")
    role: Optional[str] = Field("user", description="User role")
    is_active: Optional[bool] = Field(True, description="User active status")
    is_verified: Optional[bool] = Field(False, description="Email verification status")
    
    @validator('password')
    def validate_password(cls, v):
        BaseValidator.validate_password_strength(v)
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v:
            valid_roles = ["admin", "user", "moderator", "guest"]
            BaseValidator.validate_choice(v, valid_roles, "Role")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "role": "user",
                "is_active": True,
                "is_verified": False
            }
        }


class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = Field(None, description="User email address")
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    role: Optional[str] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="User active status")
    is_verified: Optional[bool] = Field(None, description="Email verification status")
    bio: Optional[str] = Field(None, description="User bio")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    location: Optional[str] = Field(None, description="Location")
    timezone: Optional[str] = Field(None, description="Timezone")
    
    @validator('email')
    def validate_email(cls, v):
        if v:
            return BaseValidator.validate_email_format(v)
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            return BaseValidator.validate_phone_number(v)
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v:
            BaseValidator.validate_string_length(v, min_length=1, max_length=50)
            return v.strip()
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v:
            valid_roles = ["admin", "user", "moderator", "guest"]
            BaseValidator.validate_choice(v, valid_roles, "Role")
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        if v:
            valid_genders = ["male", "female", "other", "prefer_not_to_say"]
            BaseValidator.validate_choice(v, valid_genders, "Gender")
        return v
    
    @validator('avatar_url')
    def validate_avatar_url(cls, v):
        if v:
            BaseValidator.validate_url(v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "bio": "Software developer and tech enthusiast",
                "location": "New York, NY",
                "timezone": "America/New_York"
            }
        }


class UserResponse(BaseModel):
    """User response model"""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="Email verification status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
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
                "role": "user",
                "is_active": True,
                "is_verified": True,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "last_login": "2024-01-01T12:00:00"
            }
        }


class UserProfile(BaseModel):
    """User profile model"""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="Email verification status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    bio: Optional[str] = Field(None, description="User bio")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    location: Optional[str] = Field(None, description="Location")
    timezone: Optional[str] = Field(None, description="Timezone")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "role": "user",
                "is_active": True,
                "is_verified": True,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "last_login": "2024-01-01T12:00:00",
                "bio": "Software developer and tech enthusiast",
                "location": "New York, NY",
                "timezone": "America/New_York"
            }
        }


class UserListResponse(BaseModel):
    """User list response model"""
    users: list[UserResponse] = Field(..., description="List of users")
    total_count: int = Field(..., description="Total number of users")
    
    class Config:
        schema_extra = {
            "example": {
                "users": [
                    {
                        "id": 1,
                        "email": "user@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "phone": "+1234567890",
                        "role": "user",
                        "is_active": True,
                        "is_verified": True,
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00",
                        "last_login": "2024-01-01T12:00:00"
                    }
                ],
                "total_count": 1
            }
        }


class UserStatistics(BaseModel):
    """User statistics model"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    verified_users: int = Field(..., description="Number of verified users")
    recent_users: int = Field(..., description="Number of recent users")
    inactive_users: int = Field(..., description="Number of inactive users")
    unverified_users: int = Field(..., description="Number of unverified users")
    verification_rate: float = Field(..., description="Email verification rate")
    activity_rate: float = Field(..., description="User activity rate")
    
    class Config:
        schema_extra = {
            "example": {
                "total_users": 1000,
                "active_users": 850,
                "verified_users": 900,
                "recent_users": 50,
                "inactive_users": 150,
                "unverified_users": 100,
                "verification_rate": 90.0,
                "activity_rate": 85.0
            }
        }


class UserActivity(BaseModel):
    """User activity model"""
    user_id: int = Field(..., description="User ID")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    last_logout: Optional[datetime] = Field(None, description="Last logout timestamp")
    login_count: int = Field(0, description="Total login count")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last profile update timestamp")
    is_active: bool = Field(..., description="Account active status")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "last_login": "2024-01-01T12:00:00",
                "last_logout": "2024-01-01T18:00:00",
                "login_count": 25,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "is_active": True
            }
        }
