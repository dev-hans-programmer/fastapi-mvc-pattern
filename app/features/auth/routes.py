"""
Authentication routes
"""
from fastapi import APIRouter, Depends, Request

from app.features.auth.controllers import AuthController
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
from app.core.dependencies import get_auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,
    request: Request,
    auth_service = Depends(get_auth_service)
):
    """Register a new user."""
    controller = AuthController(auth_service)
    return await controller.register(user_data, request)


@router.post("/login", response_model=UserLoginResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    auth_service = Depends(get_auth_service)
):
    """Authenticate user and return tokens."""
    controller = AuthController(auth_service)
    return await controller.login(login_data, request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    auth_service = Depends(get_auth_service)
):
    """Refresh access token."""
    controller = AuthController(auth_service)
    return await controller.refresh_token(token_data)


@router.post("/logout")
async def logout(
    auth_service = Depends(get_auth_service)
):
    """Logout user."""
    controller = AuthController(auth_service)
    return await controller.logout()


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    auth_service = Depends(get_auth_service)
):
    """Change user password."""
    controller = AuthController(auth_service)
    return await controller.change_password(password_data)


@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    auth_service = Depends(get_auth_service)
):
    """Request password reset."""
    controller = AuthController(auth_service)
    return await controller.request_password_reset(reset_data)


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    auth_service = Depends(get_auth_service)
):
    """Confirm password reset."""
    controller = AuthController(auth_service)
    return await controller.confirm_password_reset(reset_data)


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerification,
    auth_service = Depends(get_auth_service)
):
    """Verify email address."""
    controller = AuthController(auth_service)
    return await controller.verify_email(verification_data)


@router.post("/resend-verification")
async def resend_verification(
    resend_data: ResendVerification,
    auth_service = Depends(get_auth_service)
):
    """Resend email verification."""
    controller = AuthController(auth_service)
    return await controller.resend_verification(resend_data)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    auth_service = Depends(get_auth_service)
):
    """Get current user information."""
    controller = AuthController(auth_service)
    return await controller.get_current_user()


@router.get("/security-stats", response_model=SecurityStatsResponse)
async def get_security_stats(
    auth_service = Depends(get_auth_service)
):
    """Get security statistics (admin only)."""
    controller = AuthController(auth_service)
    return await controller.get_security_stats()
