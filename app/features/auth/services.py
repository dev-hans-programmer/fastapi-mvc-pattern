"""
Authentication services.
"""
from typing import Dict, Any
import logging
from datetime import timedelta

from app.features.users.repositories import UserRepository
from app.models.user import User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.core.exceptions import AuthenticationException, ConflictException
from app.tasks.user_tasks import send_welcome_email

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def register_user(self, email: str, password: str, full_name: str) -> User:
        """Register a new user."""
        try:
            # Check if user already exists
            existing_user = await self.user_repository.get_by_email(email)
            if existing_user:
                raise ConflictException("User with this email already exists")
            
            # Hash password
            hashed_password = get_password_hash(password)
            
            # Create user
            user_data = {
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "is_active": True,
            }
            
            user = await self.user_repository.create(user_data)
            
            # Send welcome email (background task)
            send_welcome_email.delay(user.id, user.email, user.full_name)
            
            logger.info(f"User registered: {user.email}")
            return user
        
        except Exception as e:
            logger.error(f"Error in register_user: {str(e)}")
            raise
    
    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return tokens."""
        try:
            # Get user by email
            user = await self.user_repository.get_by_email(email)
            if not user:
                raise AuthenticationException("Invalid email or password")
            
            # Check if user is active
            if not user.is_active:
                raise AuthenticationException("User account is deactivated")
            
            # Verify password
            if not verify_password(password, user.hashed_password):
                raise AuthenticationException("Invalid email or password")
            
            # Create tokens
            access_token = create_access_token(
                data={"sub": str(user.id), "email": user.email}
            )
            refresh_token = create_refresh_token(
                data={"sub": str(user.id), "email": user.email}
            )
            
            # Update last login
            await self.user_repository.update_last_login(user.id)
            
            logger.info(f"User authenticated: {user.email}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_id": user.id,
            }
        
        except Exception as e:
            logger.error(f"Error in authenticate_user: {str(e)}")
            raise
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token."""
        try:
            # Verify refresh token
            payload = verify_refresh_token(refresh_token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationException("Invalid refresh token")
            
            # Get user
            user = await self.user_repository.get_by_id(int(user_id))
            if not user or not user.is_active:
                raise AuthenticationException("User not found or inactive")
            
            # Create new tokens
            access_token = create_access_token(
                data={"sub": str(user.id), "email": user.email}
            )
            new_refresh_token = create_refresh_token(
                data={"sub": str(user.id), "email": user.email}
            )
            
            logger.info(f"Token refreshed for user: {user.email}")
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "user_id": user.id,
            }
        
        except Exception as e:
            logger.error(f"Error in refresh_token: {str(e)}")
            raise
    
    async def logout_user(self, user_id: int) -> None:
        """Logout user."""
        try:
            # Here you would typically invalidate the token
            # For now, we just log the logout
            logger.info(f"User logged out: {user_id}")
            
            # In a real implementation, you might:
            # - Add token to blacklist
            # - Clear user sessions
            # - Update last logout timestamp
            
        except Exception as e:
            logger.error(f"Error in logout_user: {str(e)}")
            raise
    
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        """Change user password."""
        try:
            # Get user
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise AuthenticationException("User not found")
            
            # Verify old password
            if not verify_password(old_password, user.hashed_password):
                raise AuthenticationException("Invalid old password")
            
            # Hash new password
            hashed_password = get_password_hash(new_password)
            
            # Update password
            await self.user_repository.update_password(user_id, hashed_password)
            
            logger.info(f"Password changed for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error in change_password: {str(e)}")
            raise
