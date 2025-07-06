"""
User repositories
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.common.base_repository import BaseRepository
from app.features.auth.models import User
from app.features.users.models import UserProfile, UserPreferences, UserActivity, UserSession
from app.features.users.schemas import (
    UserProfileCreate, UserProfileUpdate,
    UserPreferencesCreate, UserPreferencesUpdate,
    UserActivityCreate, UserSearchFilters
)
from app.core.exceptions import ValidationException

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User, dict, dict]):
    """User repository for user management."""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_user_with_details(self, user_id: str) -> Optional[User]:
        """Get user with all related details."""
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user with details: {str(e)}")
            raise
    
    def search_users(self, filters: UserSearchFilters, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users with filters."""
        try:
            query = self.db.query(User)
            
            # Apply filters
            if filters.email:
                query = query.filter(User.email.ilike(f"%{filters.email}%"))
            
            if filters.username:
                query = query.filter(User.username.ilike(f"%{filters.username}%"))
            
            if filters.first_name:
                query = query.filter(User.first_name.ilike(f"%{filters.first_name}%"))
            
            if filters.last_name:
                query = query.filter(User.last_name.ilike(f"%{filters.last_name}%"))
            
            if filters.is_active is not None:
                query = query.filter(User.is_active == filters.is_active)
            
            if filters.is_verified is not None:
                query = query.filter(User.is_verified == filters.is_verified)
            
            if filters.is_superuser is not None:
                query = query.filter(User.is_superuser == filters.is_superuser)
            
            if filters.created_after:
                query = query.filter(User.created_at >= filters.created_after)
            
            if filters.created_before:
                query = query.filter(User.created_at <= filters.created_before)
            
            if filters.last_login_after:
                query = query.filter(User.last_login >= filters.last_login_after)
            
            if filters.last_login_before:
                query = query.filter(User.last_login <= filters.last_login_before)
            
            # Join with profile for location filters
            if filters.country or filters.city:
                query = query.join(UserProfile, User.id == UserProfile.user_id)
                
                if filters.country:
                    query = query.filter(UserProfile.country.ilike(f"%{filters.country}%"))
                
                if filters.city:
                    query = query.filter(UserProfile.city.ilike(f"%{filters.city}%"))
            
            return query.offset(skip).limit(limit).all()
        
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            raise
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        try:
            now = datetime.utcnow()
            today = now.date()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            # Basic counts
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            verified_users = self.db.query(User).filter(User.is_verified == True).count()
            
            # New users
            new_users_today = self.db.query(User).filter(
                func.date(User.created_at) == today
            ).count()
            
            new_users_week = self.db.query(User).filter(
                User.created_at >= week_ago
            ).count()
            
            new_users_month = self.db.query(User).filter(
                User.created_at >= month_ago
            ).count()
            
            # Users by country
            users_by_country = self.db.query(
                UserProfile.country,
                func.count(UserProfile.user_id).label('count')
            ).join(User, UserProfile.user_id == User.id).group_by(
                UserProfile.country
            ).filter(UserProfile.country.isnot(None)).all()
            
            users_by_country_dict = {country: count for country, count in users_by_country}
            
            # Activity stats
            recent_activities = self.db.query(UserActivity).filter(
                UserActivity.created_at >= week_ago
            ).count()
            
            active_sessions = self.db.query(UserSession).filter(
                UserSession.is_active == True
            ).count()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "verified_users": verified_users,
                "new_users_today": new_users_today,
                "new_users_week": new_users_week,
                "new_users_month": new_users_month,
                "users_by_country": users_by_country_dict,
                "activity_stats": {
                    "recent_activities": recent_activities,
                    "active_sessions": active_sessions
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            raise
    
    def bulk_update_users(self, user_ids: List[str], updates: Dict[str, Any]) -> bool:
        """Bulk update users."""
        try:
            self.db.query(User).filter(User.id.in_(user_ids)).update(updates)
            self.db.commit()
            
            logger.info(f"Bulk updated {len(user_ids)} users")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error bulk updating users: {str(e)}")
            raise ValidationException(f"Failed to bulk update users: {str(e)}")
    
    def bulk_delete_users(self, user_ids: List[str]) -> bool:
        """Bulk delete users."""
        try:
            # Delete related records first
            self.db.query(UserProfile).filter(UserProfile.user_id.in_(user_ids)).delete()
            self.db.query(UserPreferences).filter(UserPreferences.user_id.in_(user_ids)).delete()
            self.db.query(UserActivity).filter(UserActivity.user_id.in_(user_ids)).delete()
            self.db.query(UserSession).filter(UserSession.user_id.in_(user_ids)).delete()
            
            # Delete users
            self.db.query(User).filter(User.id.in_(user_ids)).delete()
            self.db.commit()
            
            logger.info(f"Bulk deleted {len(user_ids)} users")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error bulk deleting users: {str(e)}")
            raise ValidationException(f"Failed to bulk delete users: {str(e)}")


class UserProfileRepository(BaseRepository[UserProfile, UserProfileCreate, UserProfileUpdate]):
    """User profile repository."""
    
    def __init__(self, db: Session):
        super().__init__(db, UserProfile)
    
    def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user ID."""
        try:
            return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            raise
    
    def create_profile(self, user_id: str, profile_data: UserProfileCreate) -> UserProfile:
        """Create user profile."""
        try:
            profile = UserProfile(
                user_id=user_id,
                **profile_data.dict()
            )
            
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"Profile created for user: {user_id}")
            return profile
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user profile: {str(e)}")
            raise ValidationException(f"Failed to create user profile: {str(e)}")
    
    def update_profile(self, user_id: str, profile_data: UserProfileUpdate) -> Optional[UserProfile]:
        """Update user profile."""
        try:
            profile = self.get_by_user_id(user_id)
            if not profile:
                # Create profile if it doesn't exist
                create_data = UserProfileCreate(**profile_data.dict(exclude_unset=True))
                return self.create_profile(user_id, create_data)
            
            # Update existing profile
            update_data = profile_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(profile, field):
                    setattr(profile, field, value)
            
            profile.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"Profile updated for user: {user_id}")
            return profile
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user profile: {str(e)}")
            raise ValidationException(f"Failed to update user profile: {str(e)}")


class UserPreferencesRepository(BaseRepository[UserPreferences, UserPreferencesCreate, UserPreferencesUpdate]):
    """User preferences repository."""
    
    def __init__(self, db: Session):
        super().__init__(db, UserPreferences)
    
    def get_by_user_id(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences by user ID."""
        try:
            return self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            raise
    
    def create_preferences(self, user_id: str, preferences_data: UserPreferencesCreate) -> UserPreferences:
        """Create user preferences."""
        try:
            preferences = UserPreferences(
                user_id=user_id,
                **preferences_data.dict()
            )
            
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
            
            logger.info(f"Preferences created for user: {user_id}")
            return preferences
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user preferences: {str(e)}")
            raise ValidationException(f"Failed to create user preferences: {str(e)}")
    
    def update_preferences(self, user_id: str, preferences_data: UserPreferencesUpdate) -> Optional[UserPreferences]:
        """Update user preferences."""
        try:
            preferences = self.get_by_user_id(user_id)
            if not preferences:
                # Create preferences if they don't exist
                create_data = UserPreferencesCreate(**preferences_data.dict(exclude_unset=True))
                return self.create_preferences(user_id, create_data)
            
            # Update existing preferences
            update_data = preferences_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(preferences, field):
                    setattr(preferences, field, value)
            
            preferences.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(preferences)
            
            logger.info(f"Preferences updated for user: {user_id}")
            return preferences
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user preferences: {str(e)}")
            raise ValidationException(f"Failed to update user preferences: {str(e)}")


class UserActivityRepository(BaseRepository[UserActivity, UserActivityCreate, dict]):
    """User activity repository."""
    
    def __init__(self, db: Session):
        super().__init__(db, UserActivity)
    
    def create_activity(self, user_id: str, activity_data: UserActivityCreate) -> UserActivity:
        """Create user activity."""
        try:
            activity = UserActivity(
                user_id=user_id,
                **activity_data.dict()
            )
            
            self.db.add(activity)
            self.db.commit()
            self.db.refresh(activity)
            
            logger.debug(f"Activity created for user: {user_id}")
            return activity
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user activity: {str(e)}")
            raise ValidationException(f"Failed to create user activity: {str(e)}")
    
    def get_user_activities(self, user_id: str, skip: int = 0, limit: int = 50) -> List[UserActivity]:
        """Get user activities."""
        try:
            return self.db.query(UserActivity).filter(
                UserActivity.user_id == user_id
            ).order_by(UserActivity.created_at.desc()).offset(skip).limit(limit).all()
        
        except Exception as e:
            logger.error(f"Error getting user activities: {str(e)}")
            raise
    
    def get_recent_activities(self, hours: int = 24) -> List[UserActivity]:
        """Get recent activities."""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            return self.db.query(UserActivity).filter(
                UserActivity.created_at >= since
            ).order_by(UserActivity.created_at.desc()).all()
        
        except Exception as e:
            logger.error(f"Error getting recent activities: {str(e)}")
            raise


class UserSessionRepository(BaseRepository[UserSession, dict, dict]):
    """User session repository."""
    
    def __init__(self, db: Session):
        super().__init__(db, UserSession)
    
    def create_session(self, user_id: str, session_data: dict) -> UserSession:
        """Create user session."""
        try:
            session = UserSession(
                user_id=user_id,
                **session_data
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.debug(f"Session created for user: {user_id}")
            return session
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user session: {str(e)}")
            raise ValidationException(f"Failed to create user session: {str(e)}")
    
    def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[UserSession]:
        """Get user sessions."""
        try:
            query = self.db.query(UserSession).filter(UserSession.user_id == user_id)
            
            if active_only:
                query = query.filter(UserSession.is_active == True)
            
            return query.order_by(UserSession.last_activity.desc()).all()
        
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            raise
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity."""
        try:
            session = self.get(session_id)
            if session:
                session.last_activity = datetime.utcnow()
                self.db.commit()
                return True
            return False
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating session activity: {str(e)}")
            raise
    
    def deactivate_session(self, session_id: str) -> bool:
        """Deactivate session."""
        try:
            session = self.get(session_id)
            if session:
                session.is_active = False
                self.db.commit()
                return True
            return False
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deactivating session: {str(e)}")
            raise
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            now = datetime.utcnow()
            count = self.db.query(UserSession).filter(
                UserSession.expires_at < now
            ).update({"is_active": False})
            
            self.db.commit()
            
            logger.info(f"Cleaned up {count} expired sessions")
            return count
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            raise
