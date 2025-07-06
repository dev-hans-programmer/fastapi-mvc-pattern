"""
Users services.
"""
from typing import List, Optional, Tuple, Dict, Any
import logging
from datetime import datetime, timedelta

from app.features.users.repositories import UserRepository
from app.features.users.types import (
    UserCreate, UserUpdate, UserProfileResponse, UserStatsResponse
)
from app.models.user import User
from app.core.exceptions import NotFoundException, ConflictException
from app.core.security import get_password_hash
from app.core.thread_pool import AsyncBatchProcessor
from app.tasks.user_tasks import send_user_update_notification

logger = logging.getLogger(__name__)


class UserService:
    """User service."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            # Check if user already exists
            existing_user = await self.user_repository.get_by_email(user_data.email)
            if existing_user:
                raise ConflictException("User with this email already exists")
            
            # Hash password if provided
            user_dict = user_data.dict()
            if user_data.password:
                user_dict["hashed_password"] = get_password_hash(user_data.password)
                del user_dict["password"]
            
            # Create user
            user = await self.user_repository.create(user_dict)
            
            logger.info(f"User created: {user.email}")
            return user
        
        except Exception as e:
            logger.error(f"Error in create_user: {str(e)}")
            raise
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            return await self.user_repository.get_by_id(user_id)
        except Exception as e:
            logger.error(f"Error in get_user_by_id: {str(e)}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            return await self.user_repository.get_by_email(email)
        except Exception as e:
            logger.error(f"Error in get_user_by_email: {str(e)}")
            raise
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        """Get list of users with pagination and filtering."""
        try:
            return await self.user_repository.get_multi(
                skip=skip,
                limit=limit,
                search=search,
                is_active=is_active,
            )
        except Exception as e:
            logger.error(f"Error in get_users: {str(e)}")
            raise
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user."""
        try:
            # Get existing user
            existing_user = await self.user_repository.get_by_id(user_id)
            if not existing_user:
                raise NotFoundException(f"User with ID {user_id} not found")
            
            # Check email uniqueness if email is being updated
            if user_data.email and user_data.email != existing_user.email:
                email_user = await self.user_repository.get_by_email(user_data.email)
                if email_user:
                    raise ConflictException("User with this email already exists")
            
            # Update user
            update_data = user_data.dict(exclude_unset=True)
            if "password" in update_data:
                update_data["hashed_password"] = get_password_hash(update_data["password"])
                del update_data["password"]
            
            user = await self.user_repository.update(user_id, update_data)
            
            # Send notification (background task)
            if user:
                send_user_update_notification.delay(user.id, user.email)
            
            logger.info(f"User updated: {user.email if user else user_id}")
            return user
        
        except Exception as e:
            logger.error(f"Error in update_user: {str(e)}")
            raise
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user."""
        try:
            # Check if user exists
            existing_user = await self.user_repository.get_by_id(user_id)
            if not existing_user:
                raise NotFoundException(f"User with ID {user_id} not found")
            
            # Soft delete (deactivate) instead of hard delete
            result = await self.user_repository.update(user_id, {"is_active": False})
            
            logger.info(f"User deactivated: {user_id}")
            return result is not None
        
        except Exception as e:
            logger.error(f"Error in delete_user: {str(e)}")
            raise
    
    async def get_user_profile(self, user_id: int) -> Optional[UserProfileResponse]:
        """Get user profile with additional details."""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return None
            
            # Get additional profile information
            profile_data = await self.user_repository.get_user_profile_data(user_id)
            
            return UserProfileResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                order_count=profile_data.get("order_count", 0),
                total_spent=profile_data.get("total_spent", 0.0),
                favorite_products=profile_data.get("favorite_products", []),
            )
        
        except Exception as e:
            logger.error(f"Error in get_user_profile: {str(e)}")
            raise
    
    def calculate_user_stats(self, user_id: int) -> Optional[UserStatsResponse]:
        """Calculate user statistics (CPU-intensive operation)."""
        try:
            # This is a CPU-intensive operation that should run in thread pool
            user = self.user_repository.get_by_id_sync(user_id)
            if not user:
                return None
            
            # Simulate heavy computation
            import time
            time.sleep(0.1)  # Simulate processing time
            
            stats_data = self.user_repository.calculate_user_stats_sync(user_id)
            
            return UserStatsResponse(
                user_id=user_id,
                total_orders=stats_data.get("total_orders", 0),
                total_spent=stats_data.get("total_spent", 0.0),
                average_order_value=stats_data.get("average_order_value", 0.0),
                last_order_date=stats_data.get("last_order_date"),
                favorite_category=stats_data.get("favorite_category"),
                account_age_days=stats_data.get("account_age_days", 0),
            )
        
        except Exception as e:
            logger.error(f"Error in calculate_user_stats: {str(e)}")
            raise
    
    async def bulk_update_users(self, user_updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk update users."""
        try:
            results = []
            
            # Use batch processor for concurrent updates
            async with AsyncBatchProcessor(batch_size=10) as processor:
                
                async def process_user_update(update_data: Dict[str, Any]) -> Dict[str, Any]:
                    try:
                        user_id = update_data.get("id")
                        if not user_id:
                            return {"id": None, "status": "error", "message": "Missing user ID"}
                        
                        # Remove id from update data
                        update_fields = {k: v for k, v in update_data.items() if k != "id"}
                        
                        # Update user
                        user = await self.user_repository.update(user_id, update_fields)
                        
                        if user:
                            return {"id": user_id, "status": "success", "message": "User updated"}
                        else:
                            return {"id": user_id, "status": "error", "message": "User not found"}
                    
                    except Exception as e:
                        return {"id": user_id, "status": "error", "message": str(e)}
                
                # Process all updates
                results = await processor.process_batch(
                    user_updates,
                    process_user_update
                )
            
            logger.info(f"Bulk update completed: {len(results)} users processed")
            return results
        
        except Exception as e:
            logger.error(f"Error in bulk_update_users: {str(e)}")
            raise
    
    async def get_active_users_count(self) -> int:
        """Get count of active users."""
        try:
            return await self.user_repository.get_active_users_count()
        except Exception as e:
            logger.error(f"Error in get_active_users_count: {str(e)}")
            raise
    
    async def get_users_registered_today(self) -> List[User]:
        """Get users registered today."""
        try:
            today = datetime.utcnow().date()
            return await self.user_repository.get_users_by_date_range(today, today)
        except Exception as e:
            logger.error(f"Error in get_users_registered_today: {str(e)}")
            raise
