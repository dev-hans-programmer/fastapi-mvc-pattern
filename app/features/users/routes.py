"""
User routes
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query

from app.features.users.controllers import UserController
from app.features.users.schemas import (
    UserDetailResponse,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    UserPreferencesUpdate,
    UserPreferencesResponse,
    UserActivityCreate,
    UserActivityResponse,
    UserSessionResponse,
    UserUpdateAdmin,
    UserStatsResponse,
    UserSearchFilters,
    BulkUserAction
)
from app.core.dependencies import get_user_service

router = APIRouter()


@router.get("/me", response_model=UserDetailResponse)
async def get_current_user_details(
    user_service = Depends(get_user_service)
):
    """Get current user details."""
    controller = UserController(user_service)
    return await controller.get_current_user_details()


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_details(
    user_id: str,
    user_service = Depends(get_user_service)
):
    """Get user details by ID."""
    controller = UserController(user_service)
    return await controller.get_user_details(user_id)


@router.post("/search", response_model=Dict[str, Any])
async def search_users(
    filters: UserSearchFilters,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_service = Depends(get_user_service)
):
    """Search users (admin only)."""
    controller = UserController(user_service)
    return await controller.search_users(filters, skip, limit)


@router.put("/{user_id}/admin", response_model=UserDetailResponse)
async def update_user_admin(
    user_id: str,
    user_data: UserUpdateAdmin,
    user_service = Depends(get_user_service)
):
    """Update user (admin only)."""
    controller = UserController(user_service)
    return await controller.update_user_admin(user_id, user_data)


@router.get("/stats/overview", response_model=UserStatsResponse)
async def get_user_stats(
    user_service = Depends(get_user_service)
):
    """Get user statistics (admin only)."""
    controller = UserController(user_service)
    return await controller.get_user_stats()


@router.post("/bulk-action")
async def bulk_user_action(
    action_data: BulkUserAction,
    user_service = Depends(get_user_service)
):
    """Perform bulk action on users (admin only)."""
    controller = UserController(user_service)
    return await controller.bulk_user_action(action_data)


# Profile routes
@router.get("/profile/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    user_service = Depends(get_user_service)
):
    """Get current user profile."""
    controller = UserController(user_service)
    return await controller.get_user_profile()


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    user_service = Depends(get_user_service)
):
    """Get user profile by ID."""
    controller = UserController(user_service)
    return await controller.get_user_profile(user_id)


@router.post("/profile", response_model=UserProfileResponse, status_code=201)
async def create_user_profile(
    profile_data: UserProfileCreate,
    user_service = Depends(get_user_service)
):
    """Create user profile."""
    controller = UserController(user_service)
    return await controller.create_user_profile(profile_data)


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    user_service = Depends(get_user_service)
):
    """Update user profile."""
    controller = UserController(user_service)
    return await controller.update_user_profile(profile_data)


# Preferences routes
@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    user_service = Depends(get_user_service)
):
    """Get user preferences."""
    controller = UserController(user_service)
    return await controller.get_user_preferences()


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    user_service = Depends(get_user_service)
):
    """Update user preferences."""
    controller = UserController(user_service)
    return await controller.update_user_preferences(preferences_data)


# Activity routes
@router.get("/activities", response_model=List[UserActivityResponse])
async def get_user_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_service = Depends(get_user_service)
):
    """Get user activities."""
    controller = UserController(user_service)
    return await controller.get_user_activities(skip, limit)


@router.post("/activities", response_model=UserActivityResponse, status_code=201)
async def create_user_activity(
    activity_data: UserActivityCreate,
    user_service = Depends(get_user_service)
):
    """Create user activity."""
    controller = UserController(user_service)
    return await controller.create_user_activity(activity_data)


# Session routes
@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(
    active_only: bool = Query(True),
    user_service = Depends(get_user_service)
):
    """Get user sessions."""
    controller = UserController(user_service)
    return await controller.get_user_sessions(active_only)


@router.delete("/sessions/{session_id}")
async def deactivate_user_session(
    session_id: str,
    user_service = Depends(get_user_service)
):
    """Deactivate user session."""
    controller = UserController(user_service)
    return await controller.deactivate_user_session(session_id)
