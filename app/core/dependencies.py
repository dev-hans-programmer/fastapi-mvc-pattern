"""
Dependency injection for the application.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.features.users.repositories import UserRepository
from app.features.users.services import UserService
from app.features.products.repositories import ProductRepository
from app.features.products.services import ProductService
from app.features.orders.repositories import OrderRepository
from app.features.orders.services import OrderService

# Security
security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """Get current user ID from token."""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    return int(user_id)


def get_optional_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[int]:
    """Get current user ID from token (optional)."""
    if not credentials:
        return None
    
    try:
        return get_current_user_id(credentials)
    except HTTPException:
        return None


# Repository dependencies
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


def get_product_repository(db: Session = Depends(get_db)) -> ProductRepository:
    """Get product repository instance."""
    return ProductRepository(db)


def get_order_repository(db: Session = Depends(get_db)) -> OrderRepository:
    """Get order repository instance."""
    return OrderRepository(db)


# Service dependencies
def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    """Get user service instance."""
    return UserService(user_repo)


def get_product_service(
    product_repo: ProductRepository = Depends(get_product_repository),
) -> ProductService:
    """Get product service instance."""
    return ProductService(product_repo)


def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
) -> OrderService:
    """Get order service instance."""
    return OrderService(order_repo, user_repo, product_repo)
