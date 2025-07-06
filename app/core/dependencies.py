"""
Dependency injection for FastAPI
"""
from typing import Generator, AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_async_db
from app.core.security import get_current_user_id
from app.features.users.repositories import UserRepository
from app.features.users.services import UserService
from app.features.products.repositories import ProductRepository
from app.features.products.services import ProductService
from app.features.orders.repositories import OrderRepository
from app.features.orders.services import OrderService
from app.features.auth.services import AuthService


# Database dependencies
def get_db_session() -> Generator[Session, None, None]:
    """Get database session dependency."""
    yield from get_db()


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session dependency."""
    async for session in get_async_db():
        yield session


# Repository dependencies
def get_user_repository(
    db: Session = Depends(get_db_session)
) -> UserRepository:
    """Get user repository dependency."""
    return UserRepository(db)


def get_product_repository(
    db: Session = Depends(get_db_session)
) -> ProductRepository:
    """Get product repository dependency."""
    return ProductRepository(db)


def get_order_repository(
    db: Session = Depends(get_db_session)
) -> OrderRepository:
    """Get order repository dependency."""
    return OrderRepository(db)


# Service dependencies
def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """Get auth service dependency."""
    return AuthService(user_repo)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Get user service dependency."""
    return UserService(user_repo)


def get_product_service(
    product_repo: ProductRepository = Depends(get_product_repository)
) -> ProductService:
    """Get product service dependency."""
    return ProductService(product_repo)


def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> OrderService:
    """Get order service dependency."""
    return OrderService(order_repo, product_repo, user_repo)


# Authentication dependencies
def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """Get current authenticated user."""
    user = user_service.get_by_id(current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_superuser(
    current_user = Depends(get_current_user)
):
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Pagination dependencies
def get_pagination_params(
    page: int = 1,
    size: int = 20
) -> dict:
    """Get pagination parameters."""
    from app.core.config import settings
    
    if page < 1:
        page = 1
    if size < 1:
        size = settings.DEFAULT_PAGE_SIZE
    if size > settings.MAX_PAGE_SIZE:
        size = settings.MAX_PAGE_SIZE
    
    return {
        "page": page,
        "size": size,
        "offset": (page - 1) * size
    }
