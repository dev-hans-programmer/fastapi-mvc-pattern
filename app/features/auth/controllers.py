"""
Authentication controllers.
"""
from fastapi import HTTPException, status
from typing import Dict, Any
import logging

from app.features.auth.services import AuthService
from app.features.auth.types import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.features.auth.validation import validate_login_request, validate_register_request
from app.core.exceptions import AuthenticationException, ValidationException

logger = logging.getLogger(__name__)


class AuthController:
    """Authentication controller."""
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
    
    async def register(self, request: RegisterRequest) -> RegisterResponse:
        """Register a new user."""
        try:
            # Validate request
            validate_register_request(request)
            
            # Register user
            user = await self.auth_service.register_user(
                email=request.email,
                password=request.password,
                full_name=request.full_name,
            )
            
            logger.info(f"User registered successfully: {user.email}")
            
            return RegisterResponse(
                message="User registered successfully",
                user_id=user.id,
                email=user.email,
            )
        
        except ValidationException as e:
            logger.error(f"Validation error in register: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in register: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed",
            )
    
    async def login(self, request: LoginRequest) -> LoginResponse:
        """Login user."""
        try:
            # Validate request
            validate_login_request(request)
            
            # Authenticate user
            tokens = await self.auth_service.authenticate_user(
                email=request.email,
                password=request.password,
            )
            
            logger.info(f"User logged in successfully: {request.email}")
            
            return LoginResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type="bearer",
            )
        
        except AuthenticationException as e:
            logger.error(f"Authentication error in login: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=e.message,
            )
        except ValidationException as e:
            logger.error(f"Validation error in login: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed",
            )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token."""
        try:
            new_tokens = await self.auth_service.refresh_token(refresh_token)
            
            logger.info("Token refreshed successfully")
            
            return {
                "access_token": new_tokens["access_token"],
                "refresh_token": new_tokens["refresh_token"],
                "token_type": "bearer",
            }
        
        except AuthenticationException as e:
            logger.error(f"Authentication error in refresh: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in refresh: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed",
            )
    
    async def logout(self, user_id: int) -> Dict[str, str]:
        """Logout user."""
        try:
            await self.auth_service.logout_user(user_id)
            
            logger.info(f"User logged out successfully: {user_id}")
            
            return {"message": "Logged out successfully"}
        
        except Exception as e:
            logger.error(f"Error in logout: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed",
            )
