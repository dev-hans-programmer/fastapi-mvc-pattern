"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Dict, Any

from app.features.auth.controllers import AuthController
from app.features.auth.validation import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ResetPasswordRequest,
    AuthResponse,
)
from app.core.dependencies import get_current_user, get_current_user_optional
from app.core.exceptions import AuthenticationException, ValidationException

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    controller: AuthController = Depends(),
):
    """
    Register a new user
    """
    try:
        result = await controller.register(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    controller: AuthController = Depends(),
):
    """
    Authenticate user and return tokens
    """
    try:
        result = await controller.login(request)
        return result
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    controller: AuthController = Depends(),
):
    """
    Refresh access token
    """
    try:
        result = await controller.refresh_token(request)
        return result
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: AuthController = Depends(),
):
    """
    Logout user and invalidate tokens
    """
    try:
        await controller.logout(current_user["id"])
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: AuthController = Depends(),
):
    """
    Change user password
    """
    try:
        await controller.change_password(current_user["id"], request)
        return {"message": "Password changed successfully"}
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    controller: AuthController = Depends(),
):
    """
    Reset user password
    """
    try:
        await controller.reset_password(request)
        return {"message": "Password reset email sent"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/verify-email")
async def verify_email(
    token: str,
    controller: AuthController = Depends(),
):
    """
    Verify user email
    """
    try:
        await controller.verify_email(token)
        return {"message": "Email verified successfully"}
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: AuthController = Depends(),
):
    """
    Get current user information
    """
    try:
        user_info = await controller.get_user_info(current_user["id"])
        return user_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/check-token")
async def check_token(
    current_user: Dict[str, Any] = Depends(get_current_user_optional),
):
    """
    Check if token is valid
    """
    if current_user:
        return {
            "valid": True,
            "user_id": current_user["id"],
            "email": current_user.get("email"),
            "role": current_user.get("role"),
        }
    else:
        return {"valid": False}


@router.post("/revoke-token")
async def revoke_token(
    token: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: AuthController = Depends(),
):
    """
    Revoke a specific token
    """
    try:
        await controller.revoke_token(token, current_user["id"])
        return {"message": "Token revoked successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/revoke-all-tokens")
async def revoke_all_tokens(
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: AuthController = Depends(),
):
    """
    Revoke all tokens for the user
    """
    try:
        await controller.revoke_all_tokens(current_user["id"])
        return {"message": "All tokens revoked successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/sessions")
async def get_user_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: AuthController = Depends(),
):
    """
    Get user active sessions
    """
    try:
        sessions = await controller.get_user_sessions(current_user["id"])
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: AuthController = Depends(),
):
    """
    Revoke a specific session
    """
    try:
        await controller.revoke_session(session_id, current_user["id"])
        return {"message": "Session revoked successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Export router
auth_router = router
