"""
Authentication routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.features.auth.controllers import AuthController
from app.features.auth.services import AuthService
from app.features.auth.repositories import AuthRepository
from app.features.auth.types import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.core.dependencies import get_db, get_current_user_id
from app.core.database import Session

router = APIRouter()
security = HTTPBearer()


def get_auth_controller(db: Session = Depends(get_db)) -> AuthController:
    """Get authentication controller."""
    auth_repository = AuthRepository(db)
    auth_service = AuthService(auth_repository)
    return AuthController(auth_service)


@router.post("/register", response_model=RegisterResponse)
async def register(
    request: RegisterRequest,
    auth_controller: AuthController = Depends(get_auth_controller),
):
    """Register a new user."""
    return await auth_controller.register(request)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_controller: AuthController = Depends(get_auth_controller),
):
    """Login user."""
    return await auth_controller.login(request)


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    auth_controller: AuthController = Depends(get_auth_controller),
):
    """Refresh access token."""
    return await auth_controller.refresh_token(refresh_token)


@router.post("/logout")
async def logout(
    current_user_id: int = Depends(get_current_user_id),
    auth_controller: AuthController = Depends(get_auth_controller),
):
    """Logout user."""
    return await auth_controller.logout(current_user_id)


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user_id: int = Depends(get_current_user_id),
    auth_controller: AuthController = Depends(get_auth_controller),
):
    """Change user password."""
    auth_service = AuthService(AuthRepository(next(get_db())))
    await auth_service.change_password(current_user_id, old_password, new_password)
    return {"message": "Password changed successfully"}
