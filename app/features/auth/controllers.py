"""
Authentication controllers
"""
import logging
from typing import Dict, Any
from fastapi import Depends, Request, HTTPException, status

from app.common.base_controller import BaseController
from app.features.auth.services import AuthService
from app.features.auth.schemas import (
    UserCreate,
    UserLogin,
    UserLoginResponse,
    TokenRefresh,
    TokenResponse,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    EmailVerification,
    ResendVerification,
    UserResponse,
    SecurityStatsResponse,
)
from app.core.exceptions import (
    AuthenticationException,
    ValidationException,
    BusinessLogicException,
)
from app.core.dependencies import get_current_user_id

logger = logging.getLogger(__name__)


class AuthController(BaseController):
    """Authentication controller for handling auth operations."""
    
    def __init__(self, auth_service: AuthService):
        super().__init__(auth_service)
        self.auth_service = auth_service
    
    async def register(self, user_data: UserCreate, request: Request) -> UserResponse:
        """Register a new user."""
        try:
            # Get client IP and user agent
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            user = await self.auth_service.register_user(
                user_data=user_data,
                client_ip=client_ip,
                user_agent=user_agent
            )
            
            logger.info(f"User registered successfully: {user.email}")
            return user
        
        except ValidationException as e:
            logger.error(f"Validation error during registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except BusinessLogicException as e:
            logger.error(f"Business logic error during registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    async def login(self, login_data: UserLogin, request: Request) -> UserLoginResponse:
        """Authenticate user and return tokens."""
        try:
            # Get client IP and user agent
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            login_response = await self.auth_service.authenticate_user(
                login_data=login_data,
                client_ip=client_ip,
                user_agent=user_agent
            )
            
            logger.info(f"User logged in successfully: {login_data.email}")
            return login_response
        
        except AuthenticationException as e:
            logger.error(f"Authentication failed for {login_data.email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )
    
    async def refresh_token(self, token_data: TokenRefresh) -> TokenResponse:
        """Refresh access token using refresh token."""
        try:
            token_response = await self.auth_service.refresh_access_token(
                token_data.refresh_token
            )
            
            logger.info("Token refreshed successfully")
            return token_response
        
        except AuthenticationException as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed"
            )
    
    async def logout(self, current_user_id: str = Depends(get_current_user_id)) -> Dict[str, str]:
        """Logout user and revoke tokens."""
        try:
            await self.auth_service.logout_user(current_user_id)
            
            logger.info(f"User logged out successfully: {current_user_id}")
            return {"message": "Logged out successfully"}
        
        except Exception as e:
            logger.error(f"Unexpected error during logout: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )
    
    async def change_password(
        self,
        password_data: PasswordChange,
        current_user_id: str = Depends(get_current_user_id)
    ) -> Dict[str, str]:
        """Change user password."""
        try:
            await self.auth_service.change_password(
                user_id=current_user_id,
                current_password=password_data.current_password,
                new_password=password_data.new_password
            )
            
            logger.info(f"Password changed successfully for user: {current_user_id}")
            return {"message": "Password changed successfully"}
        
        except ValidationException as e:
            logger.error(f"Validation error during password change: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except AuthenticationException as e:
            logger.error(f"Authentication error during password change: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error during password change: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password change failed"
            )
    
    async def request_password_reset(self, reset_data: PasswordReset) -> Dict[str, str]:
        """Request password reset."""
        try:
            await self.auth_service.request_password_reset(reset_data.email)
            
            logger.info(f"Password reset requested for: {reset_data.email}")
            return {"message": "Password reset instructions sent to email"}
        
        except Exception as e:
            logger.error(f"Unexpected error during password reset request: {str(e)}")
            # Don't expose whether email exists or not
            return {"message": "Password reset instructions sent to email"}
    
    async def confirm_password_reset(
        self,
        reset_data: PasswordResetConfirm
    ) -> Dict[str, str]:
        """Confirm password reset with token."""
        try:
            await self.auth_service.confirm_password_reset(
                token=reset_data.token,
                new_password=reset_data.new_password
            )
            
            logger.info("Password reset confirmed successfully")
            return {"message": "Password reset successfully"}
        
        except ValidationException as e:
            logger.error(f"Validation error during password reset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except AuthenticationException as e:
            logger.error(f"Authentication error during password reset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error during password reset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset failed"
            )
    
    async def verify_email(self, verification_data: EmailVerification) -> Dict[str, str]:
        """Verify user email."""
        try:
            await self.auth_service.verify_email(verification_data.token)
            
            logger.info("Email verified successfully")
            return {"message": "Email verified successfully"}
        
        except ValidationException as e:
            logger.error(f"Validation error during email verification: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        except AuthenticationException as e:
            logger.error(f"Authentication error during email verification: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error during email verification: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email verification failed"
            )
    
    async def resend_verification(
        self,
        resend_data: ResendVerification
    ) -> Dict[str, str]:
        """Resend email verification."""
        try:
            await self.auth_service.resend_verification_email(resend_data.email)
            
            logger.info(f"Verification email resent to: {resend_data.email}")
            return {"message": "Verification email sent"}
        
        except Exception as e:
            logger.error(f"Unexpected error during verification resend: {str(e)}")
            # Don't expose whether email exists or not
            return {"message": "Verification email sent"}
    
    async def get_current_user(
        self,
        current_user_id: str = Depends(get_current_user_id)
    ) -> UserResponse:
        """Get current authenticated user."""
        try:
            user = await self.auth_service.get_current_user(current_user_id)
            
            return user
        
        except Exception as e:
            logger.error(f"Unexpected error getting current user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user information"
            )
    
    async def get_security_stats(
        self,
        current_user_id: str = Depends(get_current_user_id)
    ) -> SecurityStatsResponse:
        """Get security statistics (admin only)."""
        try:
            # Check if user is admin
            user = await self.auth_service.get_current_user(current_user_id)
            if not user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
            
            stats = await self.auth_service.get_security_stats()
            
            return stats
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error getting security stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get security statistics"
            )
