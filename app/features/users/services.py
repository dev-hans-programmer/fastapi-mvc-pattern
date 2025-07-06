"""
User services
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.common.base_service import BaseService
from app.features.users.repositories import (
    UserRepository,
    UserProfileRepository,
    UserPreferencesRepository,
    UserActivityRepository,
    UserSessionRepository
)
from app.features.users.schemas import (
    UserDetailResponse,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    UserPreferencesCreate,
    UserPreferencesUpdate,
    UserPreferencesResponse,
    UserActivityCreate,
    UserActivityResponse,
    UserSessionResponse,
    UserUpdateAdmin,
    UserStatsResponse,
    UserSearchFilters,
    BulkUserAction
)
from app.features.auth.models import User
from app.core.exceptions import ValidationException, ResourceNotFoundException, BusinessLogicException
from app.core.decorators import log_execution_time
from app.core.background_tasks import submit_user_notification_task

logger = logging.getLogger(__name__)


class UserService(BaseService[User, dict, dict, UserRepository]):
    """User service for user management."""
    
    def __init__(
        self,
        user_repository: UserRepository,
        profile_repository: UserProfileRepository,
        preferences_repository: UserPreferencesRepository,
        activity_repository: UserActivityRepository,
        session_repository: UserSessionRepository
    ):
        super().__init__(user_repository)
        self.profile_repository = profile_repository
        self.preferences_repository = preferences_repository
        self.activity_repository = activity_repository
        self.session_repository = session_repository
    
    @log_execution_time
    def get_user_details(self, user_id: str) -> UserDetailResponse:
        """Get user with all details."""
        try:
            user = self.repository.get_user_with_details(user_id)
            if not user:
                raise ResourceNotFoundException("User", user_id)
            
            # Get profile
            profile = self.profile_repository.get_by_user_id(user_id)
            profile_data = UserProfileResponse.from_orm(profile) if profile else None
            
            # Get preferences
            preferences = self.preferences_repository.get_by_user_id(user_id)
            preferences_data = UserPreferencesResponse.from_orm(preferences) if preferences else None
            
            # Get recent activities
            recent_activities = self.activity_repository.get_user_activities(user_id, limit=10)
            activities_data = [UserActivityResponse.from_orm(activity) for activity in recent_activities]
            
            # Get active sessions
            active_sessions = self.session_repository.get_user_sessions(user_id, active_only=True)
            sessions_data = [UserSessionResponse.from_orm(session) for session in active_sessions]
            
            return UserDetailResponse(
                id=str(user.id),
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                profile=profile_data,
                preferences=preferences_data,
                recent_activities=activities_data,
                active_sessions=sessions_data
            )
        
        except ResourceNotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error getting user details: {str(e)}")
            raise BusinessLogicException("Failed to get user details")
    
    @log_execution_time
    def search_users(self, filters: UserSearchFilters, skip: int = 0, limit: int = 100) -> List[UserDetailResponse]:
        """Search users with filters."""
        try:
            users = self.repository.search_users(filters, skip, limit)
            
            return [
                UserDetailResponse(
                    id=str(user.id),
                    email=user.email,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    full_name=user.full_name,
                    is_active=user.is_active,
                    is_verified=user.is_verified,
                    is_superuser=user.is_superuser,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    last_login=user.last_login,
                    profile=None,
                    preferences=None,
                    recent_activities=[],
                    active_sessions=[]
                ) for user in users
            ]
        
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            raise BusinessLogicException("Failed to search users")
    
    @log_execution_time
    def update_user_admin(self, user_id: str, user_data: UserUpdateAdmin) -> UserDetailResponse:
        """Update user (admin operation)."""
        try:
            user = self.repository.get_by_id(user_id)
            if not user:
                raise ResourceNotFoundException("User", user_id)
            
            # Update user
            update_data = user_data.dict(exclude_unset=True)
            updated_user = self.repository.update(user_id, update_data)
            
            # Log activity
            self.activity_repository.create_activity(
                user_id=user_id,
                activity_data=UserActivityCreate(
                    activity_type="user_updated",
                    activity_description="User profile updated by admin",
                    resource_type="user",
                    resource_id=user_id
                )
            )
            
            logger.info(f"User updated by admin: {user_id}")
            return self.get_user_details(user_id)
        
        except ResourceNotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error updating user (admin): {str(e)}")
            raise BusinessLogicException("Failed to update user")
    
    @log_execution_time
    def get_user_stats(self) -> UserStatsResponse:
        """Get user statistics."""
        try:
            stats = self.repository.get_user_stats()
            
            return UserStatsResponse(
                total_users=stats["total_users"],
                active_users=stats["active_users"],
                verified_users=stats["verified_users"],
                new_users_today=stats["new_users_today"],
                new_users_week=stats["new_users_week"],
                new_users_month=stats["new_users_month"],
                users_by_country=stats["users_by_country"],
                activity_stats=stats["activity_stats"]
            )
        
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            raise BusinessLogicException("Failed to get user statistics")
    
    @log_execution_time
    def bulk_user_action(self, action_data: BulkUserAction) -> Dict[str, Any]:
        """Perform bulk action on users."""
        try:
            user_ids = action_data.user_ids
            action = action_data.action
            
            if action == "activate":
                self.repository.bulk_update_users(user_ids, {"is_active": True})
                message = f"Activated {len(user_ids)} users"
            
            elif action == "deactivate":
                self.repository.bulk_update_users(user_ids, {"is_active": False})
                message = f"Deactivated {len(user_ids)} users"
            
            elif action == "verify":
                self.repository.bulk_update_users(user_ids, {"is_verified": True})
                message = f"Verified {len(user_ids)} users"
            
            elif action == "unverify":
                self.repository.bulk_update_users(user_ids, {"is_verified": False})
                message = f"Unverified {len(user_ids)} users"
            
            elif action == "delete":
                self.repository.bulk_delete_users(user_ids)
                message = f"Deleted {len(user_ids)} users"
            
            else:
                raise ValidationException(f"Invalid action: {action}")
            
            # Log bulk action
            for user_id in user_ids:
                self.activity_repository.create_activity(
                    user_id=user_id,
                    activity_data=UserActivityCreate(
                        activity_type="bulk_action",
                        activity_description=f"Bulk action performed: {action}",
                        resource_type="user",
                        resource_id=user_id
                    )
                )
            
            logger.info(f"Bulk action performed: {action} on {len(user_ids)} users")
            return {"message": message, "affected_users": len(user_ids)}
        
        except ValidationException:
            raise
        
        except Exception as e:
            logger.error(f"Error performing bulk action: {str(e)}")
            raise BusinessLogicException("Failed to perform bulk action")
    
    # Profile methods
    @log_execution_time
    def get_user_profile(self, user_id: str) -> Optional[UserProfileResponse]:
        """Get user profile."""
        try:
            profile = self.profile_repository.get_by_user_id(user_id)
            return UserProfileResponse.from_orm(profile) if profile else None
        
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            raise BusinessLogicException("Failed to get user profile")
    
    @log_execution_time
    def create_user_profile(self, user_id: str, profile_data: UserProfileCreate) -> UserProfileResponse:
        """Create user profile."""
        try:
            # Verify user exists
            user = self.repository.get_by_id(user_id)
            if not user:
                raise ResourceNotFoundException("User", user_id)
            
            # Check if profile already exists
            existing_profile = self.profile_repository.get_by_user_id(user_id)
            if existing_profile:
                raise ValidationException("User profile already exists")
            
            profile = self.profile_repository.create_profile(user_id, profile_data)
            
            # Log activity
            self.activity_repository.create_activity(
                user_id=user_id,
                activity_data=UserActivityCreate(
                    activity_type="profile_created",
                    activity_description="User profile created",
                    resource_type="profile",
                    resource_id=str(profile.id)
                )
            )
            
            logger.info(f"User profile created: {user_id}")
            return UserProfileResponse.from_orm(profile)
        
        except (ResourceNotFoundException, ValidationException):
            raise
        
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
            raise BusinessLogicException("Failed to create user profile")
    
    @log_execution_time
    def update_user_profile(self, user_id: str, profile_data: UserProfileUpdate) -> UserProfileResponse:
        """Update user profile."""
        try:
            # Verify user exists
            user = self.repository.get_by_id(user_id)
            if not user:
                raise ResourceNotFoundException("User", user_id)
            
            profile = self.profile_repository.update_profile(user_id, profile_data)
            
            # Log activity
            self.activity_repository.create_activity(
                user_id=user_id,
                activity_data=UserActivityCreate(
                    activity_type="profile_updated",
                    activity_description="User profile updated",
                    resource_type="profile",
                    resource_id=str(profile.id)
                )
            )
            
            logger.info(f"User profile updated: {user_id}")
            return UserProfileResponse.from_orm(profile)
        
        except ResourceNotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            raise BusinessLogicException("Failed to update user profile")
    
    # Preferences methods
    @log_execution_time
    def get_user_preferences(self, user_id: str) -> Optional[UserPreferencesResponse]:
        """Get user preferences."""
        try:
            preferences = self.preferences_repository.get_by_user_id(user_id)
            return UserPreferencesResponse.from_orm(preferences) if preferences else None
        
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            raise BusinessLogicException("Failed to get user preferences")
    
    @log_execution_time
    def update_user_preferences(self, user_id: str, preferences_data: UserPreferencesUpdate) -> UserPreferencesResponse:
        """Update user preferences."""
        try:
            # Verify user exists
            user = self.repository.get_by_id(user_id)
            if not user:
                raise ResourceNotFoundException("User", user_id)
            
            preferences = self.preferences_repository.update_preferences(user_id, preferences_data)
            
            # Log activity
            self.activity_repository.create_activity(
                user_id=user_id,
                activity_data=UserActivityCreate(
                    activity_type="preferences_updated",
                    activity_description="User preferences updated",
                    resource_type="preferences",
                    resource_id=str(preferences.id)
                )
            )
            
            logger.info(f"User preferences updated: {user_id}")
            return UserPreferencesResponse.from_orm(preferences)
        
        except ResourceNotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            raise BusinessLogicException("Failed to update user preferences")
    
    # Activity methods
    @log_execution_time
    def get_user_activities(self, user_id: str, skip: int = 0, limit: int = 50) -> List[UserActivityResponse]:
        """Get user activities."""
        try:
            activities = self.activity_repository.get_user_activities(user_id, skip, limit)
            return [UserActivityResponse.from_orm(activity) for activity in activities]
        
        except Exception as e:
            logger.error(f"Error getting user activities: {str(e)}")
            raise BusinessLogicException("Failed to get user activities")
    
    @log_execution_time
    def create_user_activity(self, user_id: str, activity_data: UserActivityCreate) -> UserActivityResponse:
        """Create user activity."""
        try:
            # Verify user exists
            user = self.repository.get_by_id(user_id)
            if not user:
                raise ResourceNotFoundException("User", user_id)
            
            activity = self.activity_repository.create_activity(user_id, activity_data)
            
            return UserActivityResponse.from_orm(activity)
        
        except ResourceNotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error creating user activity: {str(e)}")
            raise BusinessLogicException("Failed to create user activity")
    
    # Session methods
    @log_execution_time
    def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[UserSessionResponse]:
        """Get user sessions."""
        try:
            sessions = self.session_repository.get_user_sessions(user_id, active_only)
            return [UserSessionResponse.from_orm(session) for session in sessions]
        
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            raise BusinessLogicException("Failed to get user sessions")
    
    @log_execution_time
    def deactivate_user_session(self, user_id: str, session_id: str) -> bool:
        """Deactivate user session."""
        try:
            # Verify user exists
            user = self.repository.get_by_id(user_id)
            if not user:
                raise ResourceNotFoundException("User", user_id)
            
            success = self.session_repository.deactivate_session(session_id)
            
            if success:
                # Log activity
                self.activity_repository.create_activity(
                    user_id=user_id,
                    activity_data=UserActivityCreate(
                        activity_type="session_deactivated",
                        activity_description="User session deactivated",
                        resource_type="session",
                        resource_id=session_id
                    )
                )
            
            logger.info(f"User session deactivated: {session_id}")
            return success
        
        except ResourceNotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error deactivating user session: {str(e)}")
            raise BusinessLogicException("Failed to deactivate user session")
