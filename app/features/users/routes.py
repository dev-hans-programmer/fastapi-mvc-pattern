"""
Users routes.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional, Dict, Any

from app.features.users.controllers import UserController
from app.features.users.services import UserService
from app.features.users.repositories import UserRepository
from app.features.users.types import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserProfileResponse, UserStatsResponse
)
from app.core.dependencies import get_db, get_current_user_id
from app.core.database import Session

router = APIRouter()


def get_user_controller(db: Session = Depends(get_db)) -> UserController:
    """Get user controller."""
    user_repository = UserRepository(db)
    user_service = UserService(user_repository)
    return UserController(user_service)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_controller: UserController = Depends(get_user_controller),
):
    """Create a new user."""
    return await user_controller.create_user(user_data)


@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search term for email or name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    user_controller: UserController = Depends(get_user_controller),
):
    """Get list of users."""
    return await user_controller.get_users(
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: int = Depends(get_current_user_id),
    user_controller: UserController = Depends(get_user_controller),
):
    """Get current user profile."""
    return await user_controller.get_user(current_user_id)


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user_id: int = Depends(get_current_user_id),
    user_controller: UserController = Depends(get_user_controller),
):
    """Get current user profile with additional details."""
    return await user_controller.get_user_profile(current_user_id)


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_current_user_stats(
    current_user_id: int = Depends(get_current_user_id),
    user_controller: UserController = Depends(get_user_controller),
):
    """Get current user statistics."""
    return await user_controller.get_user_stats(current_user_id)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_controller: UserController = Depends(get_user_controller),
):
    """Get user by ID."""
    return await user_controller.get_user(user_id)


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    user_controller: UserController = Depends(get_user_controller),
):
    """Get user profile by ID."""
    return await user_controller.get_user_profile(user_id)


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: int,
    user_controller: UserController = Depends(get_user_controller),
):
    """Get user statistics by ID."""
    return await user_controller.get_user_stats(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_controller: UserController = Depends(get_user_controller),
):
    """Update user."""
    return await user_controller.update_user(user_id, user_data)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    user_controller: UserController = Depends(get_user_controller),
):
    """Update current user."""
    return await user_controller.update_user(current_user_id, user_data)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    user_controller: UserController = Depends(get_user_controller),
):
    """Delete user."""
    return await user_controller.delete_user(user_id)


@router.post("/bulk-update")
async def bulk_update_users(
    user_updates: List[Dict[str, Any]],
    user_controller: UserController = Depends(get_user_controller),
):
    """Bulk update users."""
    return await user_controller.bulk_update_users(user_updates)
