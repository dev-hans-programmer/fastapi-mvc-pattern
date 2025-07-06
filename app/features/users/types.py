"""
Users types and schemas.
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Any
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str
    is_active: bool = True


class UserCreate(UserBase):
    """User creation schema."""
    password: str
    
    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v
    
    @validator("full_name")
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return v.strip()


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator("password")
    def validate_password(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v
    
    @validator("full_name")
    def validate_full_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return v.strip() if v else None


class UserResponse(UserBase):
    """User response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class UserListResponse(BaseModel):
    """User list response schema."""
    users: List[UserResponse]
    total: int
    skip: int
    limit: int


class UserProfileResponse(BaseModel):
    """User profile response schema."""
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    order_count: int
    total_spent: float
    favorite_products: List[str]


class UserStatsResponse(BaseModel):
    """User statistics response schema."""
    user_id: int
    total_orders: int
    total_spent: float
    average_order_value: float
    last_order_date: Optional[datetime] = None
    favorite_category: Optional[str] = None
    account_age_days: int


class UserSearchResponse(BaseModel):
    """User search response schema."""
    users: List[UserResponse]
    total: int
    search_term: str


class UserBulkUpdateRequest(BaseModel):
    """User bulk update request schema."""
    user_updates: List[dict]


class UserBulkUpdateResponse(BaseModel):
    """User bulk update response schema."""
    processed: int
    successful: int
    failed: int
    errors: List[str]
