"""
Users controllers.
"""
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
import logging

from app.features.users.services import UserService
from app.features.users.types import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserProfileResponse, UserStatsResponse
)
from app.features.users.validation import validate_user_create, validate_user_update
from app.core.exceptions import NotFoundException, ValidationException
from app.core.thread_pool import run_in_thread

logger = logging.getLogger(__name__)


class UserController:
    """User controller."""
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user."""
        try:
            # Validate request
            validate_user_create(user_data)
            
            # Create user
            user = await self.user_service.create_user(user_data)
            
            logger.info(f"User created successfully: {user.email}")
            
            return UserResponse.from_orm(user)
        
        except ValidationException as e:
            logger.error(f"Validation error in create_user: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in create_user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )
    
    async def get_user(self, user_id: int) -> UserResponse:
        """Get user by ID."""
        try:
            user = await self.user_service.get_user_by_id(user_id)
            
            if not user:
                raise NotFoundException(f"User with ID {user_id} not found")
            
            return UserResponse.from_orm(user)
        
        except NotFoundException as e:
            logger.error(f"User not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in get_user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user",
            )
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> UserListResponse:
        """Get list of users."""
        try:
            users, total = await self.user_service.get_users(
                skip=skip,
                limit=limit,
                search=search,
                is_active=is_active,
            )
            
            user_responses = [UserResponse.from_orm(user) for user in users]
            
            return UserListResponse(
                users=user_responses,
                total=total,
                skip=skip,
                limit=limit,
            )
        
        except Exception as e:
            logger.error(f"Error in get_users: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get users",
            )
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """Update user."""
        try:
            # Validate request
            validate_user_update(user_data)
            
            # Update user
            user = await self.user_service.update_user(user_id, user_data)
            
            if not user:
                raise NotFoundException(f"User with ID {user_id} not found")
            
            logger.info(f"User updated successfully: {user.email}")
            
            return UserResponse.from_orm(user)
        
        except NotFoundException as e:
            logger.error(f"User not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except ValidationException as e:
            logger.error(f"Validation error in update_user: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in update_user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user",
            )
    
    async def delete_user(self, user_id: int) -> Dict[str, str]:
        """Delete user."""
        try:
            success = await self.user_service.delete_user(user_id)
            
            if not success:
                raise NotFoundException(f"User with ID {user_id} not found")
            
            logger.info(f"User deleted successfully: {user_id}")
            
            return {"message": "User deleted successfully"}
        
        except NotFoundException as e:
            logger.error(f"User not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in delete_user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user",
            )
    
    async def get_user_profile(self, user_id: int) -> UserProfileResponse:
        """Get user profile with additional details."""
        try:
            profile = await self.user_service.get_user_profile(user_id)
            
            if not profile:
                raise NotFoundException(f"User with ID {user_id} not found")
            
            return profile
        
        except NotFoundException as e:
            logger.error(f"User not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in get_user_profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user profile",
            )
    
    @run_in_thread
    def get_user_stats(self, user_id: int) -> UserStatsResponse:
        """Get user statistics (CPU-intensive operation)."""
        try:
            stats = self.user_service.calculate_user_stats(user_id)
            
            if not stats:
                raise NotFoundException(f"User with ID {user_id} not found")
            
            return stats
        
        except NotFoundException as e:
            logger.error(f"User not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in get_user_stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user statistics",
            )
    
    async def bulk_update_users(self, user_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update users."""
        try:
            results = await self.user_service.bulk_update_users(user_updates)
            
            logger.info(f"Bulk update completed: {len(results)} users processed")
            
            return {
                "message": "Bulk update completed",
                "processed": len(results),
                "results": results,
            }
        
        except Exception as e:
            logger.error(f"Error in bulk_update_users: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to bulk update users",
            )
