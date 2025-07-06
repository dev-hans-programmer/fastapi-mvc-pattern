"""
Authentication schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator

from app.common.schemas import validate_email, validate_password_strength


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower()


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        return validate_password_strength(v)
    
    @validator('confirm_password')
    def validate_passwords_match(cls, v, values):
        """Validate that passwords match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z0-9_]+$', v):
                raise ValueError('Username can only contain letters, numbers, and underscores')
            return v.lower()
        return v


class UserResponse(UserBase):
    """User response schema."""
    id: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    full_name: str
    
    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class UserLoginResponse(BaseModel):
    """User login response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenRefresh(BaseModel):
    """Token refresh schema."""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordChange(BaseModel):
    """Password change schema."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        return validate_password_strength(v)
    
    @validator('confirm_new_password')
    def validate_passwords_match(cls, v, values):
        """Validate that passwords match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordReset(BaseModel):
    """Password reset schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        return validate_password_strength(v)
    
    @validator('confirm_new_password')
    def validate_passwords_match(cls, v, values):
        """Validate that passwords match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class EmailVerification(BaseModel):
    """Email verification schema."""
    token: str


class ResendVerification(BaseModel):
    """Resend verification schema."""
    email: EmailStr


class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_default: bool = False


class RoleCreate(RoleBase):
    """Role creation schema."""
    permission_ids: List[str] = []


class RoleUpdate(BaseModel):
    """Role update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    permission_ids: Optional[List[str]] = None


class RoleResponse(RoleBase):
    """Role response schema."""
    id: str
    created_at: datetime
    permissions: List['PermissionResponse'] = []
    
    class Config:
        orm_mode = True


class PermissionBase(BaseModel):
    """Base permission schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)


class PermissionCreate(PermissionBase):
    """Permission creation schema."""
    pass


class PermissionUpdate(BaseModel):
    """Permission update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    resource: Optional[str] = Field(None, min_length=1, max_length=100)
    action: Optional[str] = Field(None, min_length=1, max_length=50)


class PermissionResponse(PermissionBase):
    """Permission response schema."""
    id: str
    created_at: datetime
    
    class Config:
        orm_mode = True


class UserRoleAssignment(BaseModel):
    """User role assignment schema."""
    user_id: str
    role_id: str


class UserPermissionCheck(BaseModel):
    """User permission check schema."""
    user_id: str
    permission: str


class LoginAttemptResponse(BaseModel):
    """Login attempt response schema."""
    id: str
    email: str
    ip_address: str
    user_agent: Optional[str] = None
    successful: bool
    failure_reason: Optional[str] = None
    timestamp: datetime
    
    class Config:
        orm_mode = True


class SecurityStatsResponse(BaseModel):
    """Security statistics response schema."""
    total_users: int
    active_users: int
    verified_users: int
    locked_users: int
    recent_login_attempts: int
    successful_logins: int
    failed_logins: int


# Update forward references
RoleResponse.update_forward_refs()
