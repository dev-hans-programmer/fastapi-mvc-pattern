"""
Authentication repositories.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.user import User
from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class AuthRepository:
    """Authentication repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            return user
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            raise
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            return user
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            raise
    
    async def create_user(self, user_data: dict) -> User:
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
    
    async def update_user_password(self, user_id: int, hashed_password: str) -> None:
        """Update user password."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotFoundException("User not found")
            
            user.hashed_password = hashed_password
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating user password: {str(e)}")
            self.db.rollback()
            raise
    
    async def update_user_last_login(self, user_id: int) -> None:
        """Update user last login timestamp."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotFoundException("User not found")
            
            from datetime import datetime
            user.last_login = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating user last login: {str(e)}")
            self.db.rollback()
            raise
    
    async def deactivate_user(self, user_id: int) -> None:
        """Deactivate user account."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotFoundException("User not found")
            
            user.is_active = False
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error deactivating user: {str(e)}")
            self.db.rollback()
            raise
    
    async def activate_user(self, user_id: int) -> None:
        """Activate user account."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotFoundException("User not found")
            
            user.is_active = True
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error activating user: {str(e)}")
            self.db.rollback()
            raise
