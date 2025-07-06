"""
User schemas
"""
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator, HttpUrl

from app.common.schemas import TimestampMixin, IdMixin


class UserProfileBase(BaseModel):
    """Base user profile schema."""
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[HttpUrl] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Preferences
    timezone: Optional[str] = Field("UTC", max_length=50)
    language: Optional[str] = Field("en", max_length=10)
    theme: Optional[str] = Field("light", max_length=20)
    notifications_enabled: Optional[bool] = True
    marketing_emails: Optional[bool] = False
    
    # Social media
    linkedin_url: Optional[HttpUrl] = None
    twitter_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None


class UserProfileCreate(UserProfileBase):
    """User profile creation schema."""
    pass


class UserProfileUpdate(BaseModel):
    """User profile update schema."""
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[HttpUrl] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Preferences
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    theme: Optional[str] = Field(None, max_length=20)
    notifications_enabled: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    
    # Social media
    linkedin_url: Optional[HttpUrl] = None
    twitter_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None


class UserProfileResponse(UserProfileBase, IdMixin, TimestampMixin):
    """User profile response schema."""
    user_id: str
    full_address: Optional[str] = None
    
    class Config:
        orm_mode = True


class UserPreferencesBase(BaseModel):
    """Base user preferences schema."""
    # Notification preferences
    email_notifications: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    
    # Privacy preferences
    profile_visibility: str = Field("public", regex="^(public|private|friends)$")
    show_online_status: bool = True
    show_activity: bool = True
    
    # Communication preferences
    allow_friend_requests: bool = True
    allow_messages: bool = True
    allow_mentions: bool = True
    
    # Content preferences
    content_language: str = Field("en", max_length=10)
    mature_content: bool = False


class UserPreferencesCreate(UserPreferencesBase):
    """User preferences creation schema."""
    pass


class UserPreferencesUpdate(BaseModel):
    """User preferences update schema."""
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    profile_visibility: Optional[str] = Field(None, regex="^(public|private|friends)$")
    show_online_status: Optional[bool] = None
    show_activity: Optional[bool] = None
    allow_friend_requests: Optional[bool] = None
    allow_messages: Optional[bool] = None
    allow_mentions: Optional[bool] = None
    content_language: Optional[str] = Field(None, max_length=10)
    mature_content: Optional[bool] = None


class UserPreferencesResponse(UserPreferencesBase, IdMixin, TimestampMixin):
    """User preferences response schema."""
    user_id: str
    
    class Config:
        orm_mode = True


class UserActivityBase(BaseModel):
    """Base user activity schema."""
    activity_type: str = Field(..., max_length=50)
    activity_description: Optional[str] = None
    resource_type: Optional[str] = Field(None, max_length=50)
    resource_id: Optional[str] = Field(None, max_length=100)
    status: str = Field("completed", max_length=20)


class UserActivityCreate(UserActivityBase):
    """User activity creation schema."""
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    metadata: Optional[str] = None


class UserActivityResponse(UserActivityBase, IdMixin):
    """User activity response schema."""
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


class UserSessionBase(BaseModel):
    """Base user session schema."""
    device_type: Optional[str] = Field(None, max_length=50)
    device_name: Optional[str] = Field(None, max_length=100)
    browser: Optional[str] = Field(None, max_length=100)
    os: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)


class UserSessionResponse(UserSessionBase, IdMixin):
    """User session response schema."""
    user_id: str
    session_token: str
    ip_address: Optional[str] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    last_activity: datetime
    is_expired: bool
    
    class Config:
        orm_mode = True


class UserDetailResponse(BaseModel):
    """Detailed user response schema."""
    id: str
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    full_name: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    # Related data
    profile: Optional[UserProfileResponse] = None
    preferences: Optional[UserPreferencesResponse] = None
    recent_activities: List[UserActivityResponse] = []
    active_sessions: List[UserSessionResponse] = []
    
    class Config:
        orm_mode = True


class UserUpdateAdmin(BaseModel):
    """User update schema for admin operations."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_superuser: Optional[bool] = None
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z0-9_]+$', v):
                raise ValueError('Username can only contain letters, numbers, and underscores')
            return v.lower()
        return v


class UserStatsResponse(BaseModel):
    """User statistics response schema."""
    total_users: int
    active_users: int
    verified_users: int
    new_users_today: int
    new_users_week: int
    new_users_month: int
    users_by_country: dict
    activity_stats: dict


class UserSearchFilters(BaseModel):
    """User search filters schema."""
    email: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_superuser: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_login_after: Optional[datetime] = None
    last_login_before: Optional[datetime] = None
    country: Optional[str] = None
    city: Optional[str] = None


class BulkUserAction(BaseModel):
    """Bulk user action schema."""
    user_ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., regex="^(activate|deactivate|verify|unverify|delete)$")
    reason: Optional[str] = Field(None, max_length=500)
