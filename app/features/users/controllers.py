"""
User controllers
"""
import logging
from typing import List, Dict, Any
from fastapi import Depends, HTTPException, status, Query

from app.common.base_controller import BaseController
from app.features.users.services import UserService
from app.features.users.schemas import (
    UserDetailResponse,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
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
from app.core.dependencies import get_current_user_id, get_current_superuser
from app.core.exceptions import ResourceNotFoundException, ValidationException, BusinessLogicException

logger = logging.getLogger(__name__)


class UserController(BaseController):
    """User controller for handling user operations."""
    
    def __init__(self, user_service: UserService):
        super().__init__(user_service)
        self.user_service = user_service
    
    async def get_user_details(self, user_id: str) -> UserDetailResponse:
        """Get user details by ID."""
        try:
            return self.user_service.get_user_details(user_id)
        
        except ResourceNotFoundException as e:
            logger.error(f"User not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error getting user details: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user details"
            )
    
    async def get_current_user_details(
        self,
        current_user_id: str = Depends(get_current_user_id)
    ) -> UserDetailResponse:
        """Get current user details."""
        return await self.get_user_details(current_user_id)
    
    async def search_users(
        self,
        filters: UserSearchFilters,
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        current_user = Depends(get_current_superuser)
    ) -> Dict[str, Any]:
        """Search users (admin only)."""
        try:
            users = self.user_service.search_users(filters, skip, limit)
            total_count = len(users)  # This is a simplified count
            
            return {
                "items": users,
                "total": total_count,
                "page": (skip // limit) + 1,
                "size": limit,
                "pages": (total_count + limit - 1) // limit
            }
        
        except Exception as e:
            logger.error(f"Unexpected error searching users: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search users"
            )
    
    async def update_user_admin(
        self,
        user_id: str,
        user_data: UserUpdateAdmin,
        current_user = Depends(get_current_superuser)
    ) -> UserDetailResponse:
        """Update user (admin only)."""
        try:
            return self.user_service.update_user_admin(user_id, user_data)
        
        except ResourceNotFoundException as e:
            logger.error(f"User not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        except ValidationException as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error updating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
    
    async def get_user_stats(
        self,
        current_user = Depends(get_current_superuser)
    ) -> UserStatsResponse:
        """Get user statistics (admin only)."""
        try:
            return self.user_service.get_user_stats()
        
        except Exception as e:
            logger.error(f"Unexpected error getting user stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user statistics"
            )
    
    async def bulk_user_action(
        self,
        action_data: BulkUserAction,
        current_user = Depends(get_current_superuser)
    ) -> Dict[str, Any]:
        """Perform bulk action on users (admin only)."""
        try:
            return self.user_service.bulk_user_action(action_data)
        
        except ValidationException as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error performing bulk action: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to perform bulk action"
            )
    
    # Profile methods
    async def get_user_profile(
        self,
        user_id: str = None,
        current_user_id: str = Depends(get_current_user_id)
    ) -> UserProfileResponse:
        """Get user profile."""
        try:
            target_user_id = user_id or current_user_id
            profile = self.user_service.get_user_profile(target_user_id)
            
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found"
                )
            
            return profile
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error getting user profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user profile"
            )
    
    async def create_user_profile(
        self,
        profile_data: UserProfileCreate,
        current_user_id: str = Depends(get_current_user_id)
    ) -> UserProfileResponse:
        """Create user profile."""
        try:
            return self.user_service.create_user_profile(current_user_id, profile_data)
        
        except ResourceNotFoundException as e:
            logger.error(f"User not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        except ValidationException as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error creating user profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile"
            )
    
    async def update_user_profile(
        self,
        profile_data: UserProfileUpdate,
        current_user_id: str = Depends(get_current_user_id)
    ) -> UserProfileResponse:
        """Update user profile."""
        try:
            return self.user_service.update_user_profile(current_user_id, profile_data)
        
        except ResourceNotFoundException as e:
            logger.error(f"User not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error updating user profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )
    
    # Preferences methods
    async def get_user_preferences(
        self,
        current_user_id: str = Depends(get_current_user_id)
    ) -> UserPreferencesResponse:
        """Get user preferences."""
        try:
            preferences = self.user_service.get_user_preferences(current_user_id)
            
            if not preferences:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User preferences not found"
                )
            
            return preferences
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error getting user preferences: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user preferences"
            )
    
    async def update_user_preferences(
        self,
        preferences_data: UserPreferencesUpdate,
        current_user_id: str = Depends(get_current_user_id)
    ) -> UserPreferencesResponse:
        """Update user preferences."""
        try:
            return self.user_service.update_user_preferences(current_user_id, preferences_data)
        
        except ResourceNotFoundException as e:
            logger.error(f"User not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error updating user preferences: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user preferences"
            )
    
    # Activity methods
    async def get_user_activities(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        current_user_id: str = Depends(get_current_user_id)
    ) -> List[UserActivityResponse]:
        """Get user activities."""
        try:
            return self.user_service.get_user_activities(current_user_id, skip, limit)
        
        except Exception as e:
            logger.error(f"Unexpected error getting user activities: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user activities"
            )
    
    async def create_user_activity(
        self,
        activity_data: UserActivityCreate,
        current_user_id: str = Depends(get_current_user_id)
    ) -> UserActivityResponse:
        """Create user activity."""
        try:
            return self.user_service.create_user_activity(current_user_id, activity_data)
        
        except ResourceNotFoundException as e:
            logger.error(f"User not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error creating user activity: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user activity"
            )
    
    # Session methods
    async def get_user_sessions(
        self,
        active_only: bool = Query(True),
        current_user_id: str = Depends(get_current_user_id)
    ) -> List[UserSessionResponse]:
        """Get user sessions."""
        try:
            return self.user_service.get_user_sessions(current_user_id, active_only)
        
        except Exception as e:
            logger.error(f"Unexpected error getting user sessions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user sessions"
            )
    
    async def deactivate_user_session(
        self,
        session_id: str,
        current_user_id: str = Depends(get_current_user_id)
    ) -> Dict[str, Any]:
        """Deactivate user session."""
        try:
            success = self.user_service.deactivate_user_session(current_user_id, session_id)
            
            if success:
                return {"message": "Session deactivated successfully", "session_id": session_id}
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
        
        except HTTPException:
            raise
        
        except ResourceNotFoundException as e:
            logger.error(f"User not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error deactivating user session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate user session"
            )
