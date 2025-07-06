"""
Users repositories.
"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, date
import logging

from app.models.user import User
from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class UserRepository:
    """User repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, user_data: dict) -> User:
        """Create a new user."""
        try:
            user = User(**user_data)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            raise
    
    def get_by_id_sync(self, user_id: int) -> Optional[User]:
        """Get user by ID (synchronous version for thread pool)."""
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID (sync): {str(e)}")
            raise
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            return self.db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            raise
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        """Get multiple users with pagination and filtering."""
        try:
            query = self.db.query(User)
            
            # Apply filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        User.email.ilike(search_term),
                        User.full_name.ilike(search_term),
                    )
                )
            
            if is_active is not None:
                query = query.filter(User.is_active == is_active)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            users = query.offset(skip).limit(limit).all()
            
            return users, total
        
        except Exception as e:
            logger.error(f"Error getting multiple users: {str(e)}")
            raise
    
    async def update(self, user_id: int, update_data: dict) -> Optional[User]:
        """Update user."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            
            return user
        
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            self.db.rollback()
            raise
    
    async def delete(self, user_id: int) -> bool:
        """Delete user."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            self.db.delete(user)
            self.db.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            self.db.rollback()
            raise
    
    async def update_last_login(self, user_id: int) -> None:
        """Update user last login timestamp."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                self.db.commit()
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")
            self.db.rollback()
            raise
    
    async def update_password(self, user_id: int, hashed_password: str) -> None:
        """Update user password."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotFoundException("User not found")
            
            user.hashed_password = hashed_password
            user.updated_at = datetime.utcnow()
            self.db.commit()
        
        except Exception as e:
            logger.error(f"Error updating password: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_user_profile_data(self, user_id: int) -> Dict[str, Any]:
        """Get additional user profile data."""
        try:
            # This would typically join with orders and other related tables
            # For now, return mock data
            return {
                "order_count": 0,
                "total_spent": 0.0,
                "favorite_products": [],
            }
        except Exception as e:
            logger.error(f"Error getting user profile data: {str(e)}")
            raise
    
    def calculate_user_stats_sync(self, user_id: int) -> Dict[str, Any]:
        """Calculate user statistics (synchronous for thread pool)."""
        try:
            # This would typically perform complex calculations
            # For now, return mock data
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # Calculate account age
            account_age = (datetime.utcnow() - user.created_at).days
            
            return {
                "total_orders": 0,
                "total_spent": 0.0,
                "average_order_value": 0.0,
                "last_order_date": None,
                "favorite_category": None,
                "account_age_days": account_age,
            }
        
        except Exception as e:
            logger.error(f"Error calculating user stats: {str(e)}")
            raise
    
    async def get_active_users_count(self) -> int:
        """Get count of active users."""
        try:
            return self.db.query(User).filter(User.is_active == True).count()
        except Exception as e:
            logger.error(f"Error getting active users count: {str(e)}")
            raise
    
    async def get_users_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[User]:
        """Get users registered within date range."""
        try:
            return (
                self.db.query(User)
                .filter(
                    and_(
                        func.date(User.created_at) >= start_date,
                        func.date(User.created_at) <= end_date,
                    )
                )
                .order_by(desc(User.created_at))
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting users by date range: {str(e)}")
            raise
    
    async def search_users(self, search_term: str, limit: int = 10) -> List[User]:
        """Search users by email or name."""
        try:
            search_pattern = f"%{search_term}%"
            return (
                self.db.query(User)
                .filter(
                    or_(
                        User.email.ilike(search_pattern),
                        User.full_name.ilike(search_pattern),
                    )
                )
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            raise
