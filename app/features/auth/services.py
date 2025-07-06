"""
Authentication services
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.features.auth.repositories import AuthRepository
from app.features.auth.schemas import (
    UserCreate,
    UserLogin,
    UserLoginResponse,
    TokenResponse,
    UserResponse,
    SecurityStatsResponse,
)
from app.features.auth.models import User, RefreshToken, LoginAttempt
from app.core.security import security_manager, create_tokens
from app.core.exceptions import (
    AuthenticationException,
    ValidationException,
    BusinessLogicException,
)
from app.core.decorators import log_execution_time, retry
from app.core.background_tasks import submit_email_task

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for handling user authentication."""
    
    def __init__(self, auth_repository: AuthRepository):
        self.auth_repository = auth_repository
    
    @log_execution_time
    async def register_user(
        self,
        user_data: UserCreate,
        client_ip: str,
        user_agent: str
    ) -> UserResponse:
        """Register a new user."""
        try:
            # Check if user already exists
            existing_user = self.auth_repository.get_user_by_email(user_data.email)
            if existing_user:
                raise ValidationException("User with this email already exists")
            
            existing_username = self.auth_repository.get_user_by_username(user_data.username)
            if existing_username:
                raise ValidationException("Username already taken")
            
            # Hash password
            hashed_password = security_manager.hash_password(user_data.password)
            
            # Create user
            user = self.auth_repository.create_user(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
            )
            
            # Generate verification token
            verification_token = security_manager.generate_password_reset_token(user.email)
            self.auth_repository.set_verification_token(user.id, verification_token)
            
            # Send verification email
            submit_email_task(
                to_email=user.email,
                subject="Email Verification",
                body=f"Please verify your email with token: {verification_token}",
                template="email_verification",
                context={"user": user.first_name, "token": verification_token}
            )
            
            logger.info(f"User registered successfully: {user.email}")
            return UserResponse.from_orm(user)
        
        except ValidationException:
            raise
        
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            raise BusinessLogicException("Registration failed")
    
    @log_execution_time
    async def authenticate_user(
        self,
        login_data: UserLogin,
        client_ip: str,
        user_agent: str
    ) -> UserLoginResponse:
        """Authenticate user and return tokens."""
        try:
            # Record login attempt
            login_attempt = self.auth_repository.create_login_attempt(
                email=login_data.email,
                ip_address=client_ip,
                user_agent=user_agent,
                successful=False
            )
            
            # Get user by email
            user = self.auth_repository.get_user_by_email(login_data.email)
            if not user:
                login_attempt.failure_reason = "User not found"
                self.auth_repository.save_login_attempt(login_attempt)
                raise AuthenticationException("Invalid email or password")
            
            # Check if account is locked
            if user.is_locked:
                login_attempt.failure_reason = "Account locked"
                self.auth_repository.save_login_attempt(login_attempt)
                raise AuthenticationException("Account is locked")
            
            # Check if account is active
            if not user.is_active:
                login_attempt.failure_reason = "Account inactive"
                self.auth_repository.save_login_attempt(login_attempt)
                raise AuthenticationException("Account is inactive")
            
            # Verify password
            if not security_manager.verify_password(login_data.password, user.hashed_password):
                # Increment failed attempts
                self.auth_repository.increment_failed_attempts(user.id)
                login_attempt.failure_reason = "Invalid password"
                self.auth_repository.save_login_attempt(login_attempt)
                raise AuthenticationException("Invalid email or password")
            
            # Reset failed attempts on successful login
            self.auth_repository.reset_failed_attempts(user.id)
            
            # Update last login
            self.auth_repository.update_last_login(user.id)
            
            # Create tokens
            tokens = create_tokens(str(user.id))
            
            # Store refresh token
            refresh_token_expiry = datetime.utcnow() + timedelta(
                minutes=security_manager.refresh_token_expire_minutes
            )
            self.auth_repository.create_refresh_token(
                user_id=user.id,
                token=tokens["refresh_token"],
                expires_at=refresh_token_expiry
            )
            
            # Update login attempt as successful
            login_attempt.successful = True
            self.auth_repository.save_login_attempt(login_attempt)
            
            logger.info(f"User authenticated successfully: {user.email}")
            return UserLoginResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type=tokens["token_type"],
                expires_in=security_manager.access_token_expire_minutes * 60,
                user=UserResponse.from_orm(user)
            )
        
        except AuthenticationException:
            raise
        
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            raise AuthenticationException("Authentication failed")
    
    @log_execution_time
    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        try:
            # Verify refresh token
            payload = security_manager.verify_token(refresh_token, "refresh")
            if not payload:
                raise AuthenticationException("Invalid refresh token")
            
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationException("Invalid refresh token")
            
            # Check if refresh token exists in database
            db_refresh_token = self.auth_repository.get_refresh_token(refresh_token)
            if not db_refresh_token or db_refresh_token.revoked:
                raise AuthenticationException("Refresh token revoked")
            
            # Check if token is expired
            if db_refresh_token.is_expired:
                raise AuthenticationException("Refresh token expired")
            
            # Get user
            user = self.auth_repository.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationException("User not found or inactive")
            
            # Create new tokens
            tokens = create_tokens(user_id)
            
            # Revoke old refresh token
            self.auth_repository.revoke_refresh_token(refresh_token)
            
            # Store new refresh token
            new_refresh_token_expiry = datetime.utcnow() + timedelta(
                minutes=security_manager.refresh_token_expire_minutes
            )
            self.auth_repository.create_refresh_token(
                user_id=user.id,
                token=tokens["refresh_token"],
                expires_at=new_refresh_token_expiry
            )
            
            logger.info(f"Token refreshed successfully for user: {user_id}")
            return TokenResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type=tokens["token_type"],
                expires_in=security_manager.access_token_expire_minutes * 60
            )
        
        except AuthenticationException:
            raise
        
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise AuthenticationException("Token refresh failed")
    
    @log_execution_time
    async def logout_user(self, user_id: str) -> None:
        """Logout user and revoke all tokens."""
        try:
            # Revoke all refresh tokens for user
            self.auth_repository.revoke_user_refresh_tokens(user_id)
            
            logger.info(f"User logged out successfully: {user_id}")
        
        except Exception as e:
            logger.error(f"Error logging out user: {str(e)}")
            raise BusinessLogicException("Logout failed")
    
    @log_execution_time
    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> None:
        """Change user password."""
        try:
            # Get user
            user = self.auth_repository.get_user_by_id(user_id)
            if not user:
                raise AuthenticationException("User not found")
            
            # Verify current password
            if not security_manager.verify_password(current_password, user.hashed_password):
                raise AuthenticationException("Current password is incorrect")
            
            # Hash new password
            new_hashed_password = security_manager.hash_password(new_password)
            
            # Update password
            self.auth_repository.update_user_password(user_id, new_hashed_password)
            
            # Revoke all refresh tokens (force re-login)
            self.auth_repository.revoke_user_refresh_tokens(user_id)
            
            logger.info(f"Password changed successfully for user: {user_id}")
        
        except AuthenticationException:
            raise
        
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            raise BusinessLogicException("Password change failed")
    
    @log_execution_time
    async def request_password_reset(self, email: str) -> None:
        """Request password reset."""
        try:
            # Get user by email
            user = self.auth_repository.get_user_by_email(email)
            if not user:
                # Don't reveal if email exists
                return
            
            # Generate reset token
            reset_token = security_manager.generate_password_reset_token(email)
            
            # Store reset token
            self.auth_repository.set_password_reset_token(user.id, reset_token)
            
            # Send reset email
            submit_email_task(
                to_email=user.email,
                subject="Password Reset",
                body=f"Reset your password with token: {reset_token}",
                template="password_reset",
                context={"user": user.first_name, "token": reset_token}
            )
            
            logger.info(f"Password reset requested for: {email}")
        
        except Exception as e:
            logger.error(f"Error requesting password reset: {str(e)}")
            # Don't raise exception to avoid revealing email existence
    
    @log_execution_time
    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        """Confirm password reset with token."""
        try:
            # Verify token
            email = security_manager.verify_password_reset_token(token)
            if not email:
                raise AuthenticationException("Invalid or expired reset token")
            
            # Get user
            user = self.auth_repository.get_user_by_email(email)
            if not user:
                raise AuthenticationException("User not found")
            
            # Verify token in database
            if not self.auth_repository.verify_password_reset_token(user.id, token):
                raise AuthenticationException("Invalid or expired reset token")
            
            # Hash new password
            new_hashed_password = security_manager.hash_password(new_password)
            
            # Update password
            self.auth_repository.update_user_password(user.id, new_hashed_password)
            
            # Clear reset token
            self.auth_repository.clear_password_reset_token(user.id)
            
            # Revoke all refresh tokens
            self.auth_repository.revoke_user_refresh_tokens(user.id)
            
            logger.info(f"Password reset confirmed for user: {user.id}")
        
        except AuthenticationException:
            raise
        
        except Exception as e:
            logger.error(f"Error confirming password reset: {str(e)}")
            raise BusinessLogicException("Password reset failed")
    
    @log_execution_time
    async def verify_email(self, token: str) -> None:
        """Verify user email."""
        try:
            # Verify token
            email = security_manager.verify_password_reset_token(token)
            if not email:
                raise AuthenticationException("Invalid or expired verification token")
            
            # Get user
            user = self.auth_repository.get_user_by_email(email)
            if not user:
                raise AuthenticationException("User not found")
            
            # Verify token in database
            if not self.auth_repository.verify_verification_token(user.id, token):
                raise AuthenticationException("Invalid or expired verification token")
            
            # Mark as verified
            self.auth_repository.mark_user_verified(user.id)
            
            # Clear verification token
            self.auth_repository.clear_verification_token(user.id)
            
            logger.info(f"Email verified for user: {user.id}")
        
        except AuthenticationException:
            raise
        
        except Exception as e:
            logger.error(f"Error verifying email: {str(e)}")
            raise BusinessLogicException("Email verification failed")
    
    @log_execution_time
    async def resend_verification_email(self, email: str) -> None:
        """Resend verification email."""
        try:
            # Get user
            user = self.auth_repository.get_user_by_email(email)
            if not user:
                # Don't reveal if email exists
                return
            
            # Check if already verified
            if user.is_verified:
                return
            
            # Generate new verification token
            verification_token = security_manager.generate_password_reset_token(email)
            
            # Store verification token
            self.auth_repository.set_verification_token(user.id, verification_token)
            
            # Send verification email
            submit_email_task(
                to_email=user.email,
                subject="Email Verification",
                body=f"Please verify your email with token: {verification_token}",
                template="email_verification",
                context={"user": user.first_name, "token": verification_token}
            )
            
            logger.info(f"Verification email resent to: {email}")
        
        except Exception as e:
            logger.error(f"Error resending verification email: {str(e)}")
            # Don't raise exception to avoid revealing email existence
    
    @log_execution_time
    async def get_current_user(self, user_id: str) -> UserResponse:
        """Get current user information."""
        try:
            user = self.auth_repository.get_user_by_id(user_id)
            if not user:
                raise AuthenticationException("User not found")
            
            return UserResponse.from_orm(user)
        
        except AuthenticationException:
            raise
        
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            raise BusinessLogicException("Failed to get user information")
    
    @log_execution_time
    async def get_security_stats(self) -> SecurityStatsResponse:
        """Get security statistics."""
        try:
            stats = self.auth_repository.get_security_stats()
            
            return SecurityStatsResponse(
                total_users=stats.get("total_users", 0),
                active_users=stats.get("active_users", 0),
                verified_users=stats.get("verified_users", 0),
                locked_users=stats.get("locked_users", 0),
                recent_login_attempts=stats.get("recent_login_attempts", 0),
                successful_logins=stats.get("successful_logins", 0),
                failed_logins=stats.get("failed_logins", 0)
            )
        
        except Exception as e:
            logger.error(f"Error getting security stats: {str(e)}")
            raise BusinessLogicException("Failed to get security statistics")
