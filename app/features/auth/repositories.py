"""
Authentication repositories
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.common.base_repository import BaseRepository
from app.features.auth.models import User, RefreshToken, LoginAttempt, Role, Permission
from app.features.auth.schemas import UserCreate, UserUpdate
from app.core.exceptions import ValidationException

logger = logging.getLogger(__name__)


class AuthRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Authentication repository for user management."""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            return self.db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            raise
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            return self.db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            raise
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            raise
    
    def create_user(
        self,
        email: str,
        username: str,
        hashed_password: str,
        first_name: str,
        last_name: str,
        is_active: bool = True,
        is_verified: bool = False,
        is_superuser: bool = False
    ) -> User:
        """Create a new user."""
        try:
            user = User(
                email=email,
                username=username,
                hashed_password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active,
                is_verified=is_verified,
                is_superuser=is_superuser
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User created: {user.email}")
            return user
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise ValidationException(f"Failed to create user: {str(e)}")
    
    def update_user_password(self, user_id: str, hashed_password: str) -> bool:
        """Update user password."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.hashed_password = hashed_password
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Password updated for user: {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating password: {str(e)}")
            raise
    
    def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.debug(f"Last login updated for user: {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating last login: {str(e)}")
            raise
    
    def increment_failed_attempts(self, user_id: str) -> bool:
        """Increment failed login attempts."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(hours=1)
            
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.warning(f"Failed login attempt #{user.failed_login_attempts} for user: {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error incrementing failed attempts: {str(e)}")
            raise
    
    def reset_failed_attempts(self, user_id: str) -> bool:
        """Reset failed login attempts."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.failed_login_attempts = 0
            user.locked_until = None
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.debug(f"Failed attempts reset for user: {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resetting failed attempts: {str(e)}")
            raise
    
    def mark_user_verified(self, user_id: str) -> bool:
        """Mark user as verified."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.is_verified = True
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"User marked as verified: {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking user as verified: {str(e)}")
            raise
    
    def set_password_reset_token(self, user_id: str, token: str) -> bool:
        """Set password reset token."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.password_reset_token = token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=24)
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Password reset token set for user: {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error setting password reset token: {str(e)}")
            raise
    
    def verify_password_reset_token(self, user_id: str, token: str) -> bool:
        """Verify password reset token."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            if user.password_reset_token != token:
                return False
            
            if user.password_reset_expires and user.password_reset_expires < datetime.utcnow():
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error verifying password reset token: {str(e)}")
            raise
    
    def clear_password_reset_token(self, user_id: str) -> bool:
        """Clear password reset token."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.password_reset_token = None
            user.password_reset_expires = None
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Password reset token cleared for user: {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error clearing password reset token: {str(e)}")
            raise
    
    def set_verification_token(self, user_id: str, token: str) -> bool:
        """Set email verification token."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.verification_token = token
            user.verification_expires = datetime.utcnow() + timedelta(hours=48)
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Verification token set for user: {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error setting verification token: {str(e)}")
            raise
    
    def verify_verification_token(self, user_id: str, token: str) -> bool:
        """Verify email verification token."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            if user.verification_token != token:
                return False
            
            if user.verification_expires and user.verification_expires < datetime.utcnow():
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error verifying verification token: {str(e)}")
            raise
    
    def clear_verification_token(self, user_id: str) -> bool:
        """Clear email verification token."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.verification_token = None
            user.verification_expires = None
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Verification token cleared for user: {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error clearing verification token: {str(e)}")
            raise
    
    def create_refresh_token(self, user_id: str, token: str, expires_at: datetime) -> RefreshToken:
        """Create refresh token."""
        try:
            refresh_token = RefreshToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at
            )
            
            self.db.add(refresh_token)
            self.db.commit()
            self.db.refresh(refresh_token)
            
            logger.debug(f"Refresh token created for user: {user_id}")
            return refresh_token
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating refresh token: {str(e)}")
            raise
    
    def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token."""
        try:
            return self.db.query(RefreshToken).filter(RefreshToken.token == token).first()
        except Exception as e:
            logger.error(f"Error getting refresh token: {str(e)}")
            raise
    
    def revoke_refresh_token(self, token: str) -> bool:
        """Revoke refresh token."""
        try:
            refresh_token = self.get_refresh_token(token)
            if not refresh_token:
                return False
            
            refresh_token.revoked = True
            self.db.commit()
            
            logger.debug(f"Refresh token revoked: {token[:10]}...")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error revoking refresh token: {str(e)}")
            raise
    
    def revoke_user_refresh_tokens(self, user_id: str) -> bool:
        """Revoke all refresh tokens for a user."""
        try:
            self.db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            ).update({"revoked": True})
            
            self.db.commit()
            
            logger.info(f"All refresh tokens revoked for user: {user_id}")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error revoking user refresh tokens: {str(e)}")
            raise
    
    def create_login_attempt(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        successful: bool = False,
        failure_reason: str = None
    ) -> LoginAttempt:
        """Create login attempt record."""
        try:
            login_attempt = LoginAttempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                successful=successful,
                failure_reason=failure_reason
            )
            
            self.db.add(login_attempt)
            self.db.commit()
            self.db.refresh(login_attempt)
            
            logger.debug(f"Login attempt recorded for: {email}")
            return login_attempt
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating login attempt: {str(e)}")
            raise
    
    def save_login_attempt(self, login_attempt: LoginAttempt) -> bool:
        """Save login attempt."""
        try:
            self.db.commit()
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving login attempt: {str(e)}")
            raise
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        try:
            # Get current time for recent calculations
            now = datetime.utcnow()
            recent_time = now - timedelta(hours=24)
            
            # Count users
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            verified_users = self.db.query(User).filter(User.is_verified == True).count()
            locked_users = self.db.query(User).filter(User.locked_until > now).count()
            
            # Count login attempts
            recent_login_attempts = self.db.query(LoginAttempt).filter(
                LoginAttempt.timestamp >= recent_time
            ).count()
            
            successful_logins = self.db.query(LoginAttempt).filter(
                LoginAttempt.timestamp >= recent_time,
                LoginAttempt.successful == True
            ).count()
            
            failed_logins = self.db.query(LoginAttempt).filter(
                LoginAttempt.timestamp >= recent_time,
                LoginAttempt.successful == False
            ).count()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "verified_users": verified_users,
                "locked_users": locked_users,
                "recent_login_attempts": recent_login_attempts,
                "successful_logins": successful_logins,
                "failed_logins": failed_logins
            }
        
        except Exception as e:
            logger.error(f"Error getting security stats: {str(e)}")
            raise
