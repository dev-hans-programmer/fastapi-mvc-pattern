"""
User models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UserStatus(enum.Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserProfile(Base):
    """User profile model with extended information."""
    
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Profile information
    bio = Column(Text)
    avatar_url = Column(String(500))
    phone = Column(String(20))
    date_of_birth = Column(DateTime)
    
    # Address information
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Preferences
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    theme = Column(String(20), default="light")
    notifications_enabled = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)
    
    # Social media
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))
    github_url = Column(String(500))
    website_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="profile")
    
    @hybrid_property
    def full_address(self):
        """Get full address string."""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.country,
            self.postal_code
        ]
        return ", ".join(filter(None, parts))
    
    def __repr__(self):
        return f"<UserProfile {self.user_id}>"


class UserPreferences(Base):
    """User preferences model."""
    
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    
    # Privacy preferences
    profile_visibility = Column(String(20), default="public")
    show_online_status = Column(Boolean, default=True)
    show_activity = Column(Boolean, default=True)
    
    # Communication preferences
    allow_friend_requests = Column(Boolean, default=True)
    allow_messages = Column(Boolean, default=True)
    allow_mentions = Column(Boolean, default=True)
    
    # Content preferences
    content_language = Column(String(10), default="en")
    mature_content = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences {self.user_id}>"


class UserActivity(Base):
    """User activity tracking model."""
    
    __tablename__ = "user_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Activity details
    activity_type = Column(String(50), nullable=False)
    activity_description = Column(Text)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    
    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    metadata = Column(Text)  # JSON string
    
    # Status
    status = Column(String(20), default="completed")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="activities")
    
    def __repr__(self):
        return f"<UserActivity {self.activity_type} - {self.user_id}>"


class UserSession(Base):
    """User session tracking model."""
    
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session details
    session_token = Column(String(255), unique=True, nullable=False)
    device_type = Column(String(50))
    device_name = Column(String(100))
    browser = Column(String(100))
    os = Column(String(100))
    
    # Location
    ip_address = Column(String(45))
    country = Column(String(100))
    city = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="sessions")
    
    @hybrid_property
    def is_expired(self):
        """Check if session is expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def __repr__(self):
        return f"<UserSession {self.session_token[:10]}... - {self.user_id}>"


# Update User model to include relationships
from app.features.auth.models import User

User.profile = relationship("UserProfile", back_populates="user", uselist=False)
User.preferences = relationship("UserPreferences", back_populates="user", uselist=False)
User.activities = relationship("UserActivity", back_populates="user")
User.sessions = relationship("UserSession", back_populates="user")
