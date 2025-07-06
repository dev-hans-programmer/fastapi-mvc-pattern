"""
Users validation utilities.
"""
import re
from typing import List
from app.features.users.types import UserCreate, UserUpdate
from app.core.exceptions import ValidationException


def validate_email_format(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> List[str]:
    """Validate password strength."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    return errors


def validate_full_name(full_name: str) -> List[str]:
    """Validate full name."""
    errors = []
    
    if not full_name or len(full_name.strip()) < 2:
        errors.append("Full name must be at least 2 characters long")
    
    if len(full_name.strip()) > 100:
        errors.append("Full name must be less than 100 characters")
    
    # Check for invalid characters
    if re.search(r'[<>"\']', full_name):
        errors.append("Full name contains invalid characters")
    
    return errors


def validate_user_create(user_data: UserCreate) -> None:
    """Validate user creation data."""
    errors = []
    
    # Validate email
    if not validate_email_format(user_data.email):
        errors.append("Invalid email format")
    
    # Validate password
    password_errors = validate_password_strength(user_data.password)
    errors.extend(password_errors)
    
    # Validate full name
    name_errors = validate_full_name(user_data.full_name)
    errors.extend(name_errors)
    
    if errors:
        raise ValidationException(
            message="User creation validation failed",
            details={"errors": errors}
        )


def validate_user_update(user_data: UserUpdate) -> None:
    """Validate user update data."""
    errors = []
    
    # Validate email if provided
    if user_data.email and not validate_email_format(user_data.email):
        errors.append("Invalid email format")
    
    # Validate password if provided
    if user_data.password:
        password_errors = validate_password_strength(user_data.password)
        errors.extend(password_errors)
    
    # Validate full name if provided
    if user_data.full_name:
        name_errors = validate_full_name(user_data.full_name)
        errors.extend(name_errors)
    
    if errors:
        raise ValidationException(
            message="User update validation failed",
            details={"errors": errors}
        )


def sanitize_user_input(input_string: str) -> str:
    """Sanitize user input."""
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', input_string)
    return sanitized.strip()


def validate_user_id(user_id: int) -> None:
    """Validate user ID."""
    if user_id <= 0:
        raise ValidationException("Invalid user ID")


def validate_pagination_params(skip: int, limit: int) -> None:
    """Validate pagination parameters."""
    errors = []
    
    if skip < 0:
        errors.append("Skip parameter cannot be negative")
    
    if limit <= 0:
        errors.append("Limit parameter must be positive")
    
    if limit > 1000:
        errors.append("Limit parameter cannot exceed 1000")
    
    if errors:
        raise ValidationException(
            message="Pagination validation failed",
            details={"errors": errors}
        )
