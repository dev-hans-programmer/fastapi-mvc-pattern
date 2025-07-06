"""
Security utilities and authentication
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import get_settings
from app.core.exceptions import AuthenticationException

settings = get_settings()
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            raise AuthenticationException("Token has expired")
        
        return payload
        
    except InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise AuthenticationException("Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise AuthenticationException("Token verification failed")


def refresh_access_token(refresh_token: str) -> str:
    """
    Create new access token from refresh token
    """
    try:
        payload = verify_token(refresh_token)
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            raise AuthenticationException("Invalid refresh token")
        
        # Create new access token
        new_payload = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "permissions": payload.get("permissions", []),
        }
        
        return create_access_token(new_payload)
        
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        raise AuthenticationException("Failed to refresh token")


def extract_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract user information from token
    """
    try:
        payload = verify_token(token)
        
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "permissions": payload.get("permissions", []),
        }
        
    except Exception:
        return None


def generate_api_key(user_id: str, prefix: str = "ak") -> str:
    """
    Generate API key for user
    """
    import secrets
    import string
    
    # Generate random string
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    return f"{prefix}_{user_id}_{key}"


def verify_api_key(api_key: str) -> Optional[str]:
    """
    Verify API key and return user ID
    """
    try:
        parts = api_key.split("_")
        if len(parts) != 3:
            return None
        
        prefix, user_id, key = parts
        
        # In production, verify against database
        # For now, just return user_id if format is correct
        return user_id
        
    except Exception:
        return None


def check_password_strength(password: str) -> Dict[str, Any]:
    """
    Check password strength
    """
    issues = []
    score = 0
    
    # Length check
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    else:
        score += 1
    
    # Character variety checks
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    else:
        score += 1
    
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    else:
        score += 1
    
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")
    else:
        score += 1
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        issues.append("Password must contain at least one special character")
    else:
        score += 1
    
    # Common password check (simplified)
    common_passwords = ["password", "123456", "qwerty", "admin", "user"]
    if password.lower() in common_passwords:
        issues.append("Password is too common")
        score = 0
    
    # Determine strength
    if score >= 5:
        strength = "strong"
    elif score >= 3:
        strength = "medium"
    else:
        strength = "weak"
    
    return {
        "strength": strength,
        "score": score,
        "issues": issues,
        "is_valid": len(issues) == 0,
    }


def sanitize_input(input_string: str) -> str:
    """
    Sanitize input string to prevent XSS
    """
    import html
    
    # HTML escape
    sanitized = html.escape(input_string)
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    return sanitized


def validate_email(email: str) -> bool:
    """
    Validate email format
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_reset_token(email: str) -> str:
    """
    Generate password reset token
    """
    data = {
        "email": email,
        "type": "reset",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Create token with shorter expiry (15 minutes)
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    data["exp"] = expire.timestamp()
    
    token = jwt.encode(
        data,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return token


def verify_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token and return email
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        # Check token type
        if payload.get("type") != "reset":
            return None
        
        # Check expiry
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            return None
        
        return payload.get("email")
        
    except Exception:
        return None


def rate_limit_key(identifier: str, action: str) -> str:
    """
    Generate rate limit key
    """
    return f"rate_limit:{action}:{identifier}"


def generate_otp() -> str:
    """
    Generate 6-digit OTP
    """
    import random
    return str(random.randint(100000, 999999))


def mask_sensitive_data(data: str, mask_char: str = "*", show_chars: int = 4) -> str:
    """
    Mask sensitive data (e.g., email, phone)
    """
    if len(data) <= show_chars * 2:
        return mask_char * len(data)
    
    visible_start = data[:show_chars]
    visible_end = data[-show_chars:]
    masked_middle = mask_char * (len(data) - show_chars * 2)
    
    return visible_start + masked_middle + visible_end


class SecurityUtils:
    """
    Security utility class
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        return hash_password(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)
    
    @staticmethod
    def create_tokens(user_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Create access and refresh tokens
        """
        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        return verify_token(token)
    
    @staticmethod
    def check_password_strength(password: str) -> Dict[str, Any]:
        return check_password_strength(password)
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        return sanitize_input(input_string)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        return validate_email(email)
