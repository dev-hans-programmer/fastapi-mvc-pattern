"""
Authentication validation utilities.
"""
import re
from typing import List
from pydantic import ValidationError

from app.features.auth.types import LoginRequest, RegisterRequest
from app.core.exceptions import ValidationException


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> List[str]:
    """Validate password strength and return list of errors."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return errors


def validate_login_request(request: LoginRequest) -> None:
    """Validate login request."""
    errors = []
    
    if not validate_email(request.email):
        errors.append("Invalid email format")
    
    if not request.password:
        errors.append("Password is required")
    
    if errors:
        raise ValidationException(
            message="Login validation failed",
            details={"errors": errors}
        )


def validate_register_request(request: RegisterRequest) -> None:
    """Validate register request."""
    errors = []
    
    if not validate_email(request.email):
        errors.append("Invalid email format")
    
    password_errors = validate_password_strength(request.password)
    errors.extend(password_errors)
    
    if not request.full_name or len(request.full_name.strip()) < 2:
        errors.append("Full name must be at least 2 characters long")
    
    if errors:
        raise ValidationException(
            message="Registration validation failed",
            details={"errors": errors}
        )


def sanitize_input(input_string: str) -> str:
    """Sanitize input string."""
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', input_string)
    return sanitized.strip()


def validate_token_format(token: str) -> bool:
    """Validate JWT token format."""
    parts = token.split('.')
    return len(parts) == 3 and all(part for part in parts)
