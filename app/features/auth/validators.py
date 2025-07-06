"""
Authentication validators
"""
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.common.validators import BaseValidator, PasswordValidator, CustomValidationError
from app.core.exceptions import ValidationError


class AuthValidator(BaseValidator):
    """Authentication-specific validators"""
    
    @staticmethod
    def validate_login_credentials(email: str, password: str) -> None:
        """Validate login credentials"""
        # Validate email format
        AuthValidator.validate_email_format(email)
        
        # Validate password is not empty
        if not password or not password.strip():
            raise ValidationError("Password cannot be empty")
        
        # Basic password length check
        if len(password) < 1:
            raise ValidationError("Password is required")
    
    @staticmethod
    def validate_registration_data(
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None
    ) -> None:
        """Validate registration data"""
        # Validate email
        AuthValidator.validate_email_format(email)
        
        # Validate password strength
        AuthValidator.validate_password_strength(password)
        
        # Validate names
        AuthValidator.validate_name(first_name, "First name")
        AuthValidator.validate_name(last_name, "Last name")
        
        # Validate phone if provided
        if phone:
            AuthValidator.validate_phone_number(phone)
    
    @staticmethod
    def validate_name(name: str, field_name: str) -> None:
        """Validate name fields"""
        if not name or not name.strip():
            raise ValidationError(f"{field_name} cannot be empty")
        
        name = name.strip()
        
        # Check length
        if len(name) < 1 or len(name) > 50:
            raise ValidationError(f"{field_name} must be between 1 and 50 characters")
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise ValidationError(f"{field_name} can only contain letters, spaces, hyphens, and apostrophes")
    
    @staticmethod
    def validate_password_change(
        old_password: str,
        new_password: str,
        current_password_hash: str
    ) -> None:
        """Validate password change request"""
        from app.core.security import SecurityUtils
        
        # Validate old password
        if not old_password:
            raise ValidationError("Current password is required")
        
        # Verify old password
        if not SecurityUtils.verify_password(old_password, current_password_hash):
            raise ValidationError("Current password is incorrect")
        
        # Validate new password strength
        AuthValidator.validate_password_strength(new_password)
        
        # Ensure new password is different from old password
        if SecurityUtils.verify_password(new_password, current_password_hash):
            raise ValidationError("New password must be different from current password")
    
    @staticmethod
    def validate_token_format(token: str, token_type: str = "token") -> None:
        """Validate token format"""
        if not token or not token.strip():
            raise ValidationError(f"{token_type} cannot be empty")
        
        token = token.strip()
        
        # Basic token format validation
        if len(token) < 10:
            raise ValidationError(f"Invalid {token_type} format")
        
        # Check for potentially dangerous characters
        if re.search(r'[<>&"\'\\]', token):
            raise ValidationError(f"Invalid {token_type} format")
    
    @staticmethod
    def validate_jwt_token(token: str) -> None:
        """Validate JWT token format"""
        if not token or not token.strip():
            raise ValidationError("JWT token cannot be empty")
        
        token = token.strip()
        
        # JWT tokens should have 3 parts separated by dots
        parts = token.split('.')
        if len(parts) != 3:
            raise ValidationError("Invalid JWT token format")
        
        # Each part should be base64-encoded
        for part in parts:
            if not part or not re.match(r'^[A-Za-z0-9_-]+$', part):
                raise ValidationError("Invalid JWT token format")
    
    @staticmethod
    def validate_refresh_token(token: str) -> None:
        """Validate refresh token"""
        AuthValidator.validate_jwt_token(token)
        
        # Additional refresh token validation could be added here
        # For example, checking if it's properly formatted for refresh tokens
    
    @staticmethod
    def validate_reset_token(token: str) -> None:
        """Validate password reset token"""
        AuthValidator.validate_token_format(token, "reset token")
        
        # Additional validation for reset tokens
        if len(token) < 32:
            raise ValidationError("Invalid reset token format")
    
    @staticmethod
    def validate_verification_token(token: str) -> None:
        """Validate email verification token"""
        AuthValidator.validate_token_format(token, "verification token")
        
        # Additional validation for verification tokens
        if len(token) < 32:
            raise ValidationError("Invalid verification token format")
    
    @staticmethod
    def validate_session_data(session_data: Dict[str, Any]) -> None:
        """Validate session data"""
        required_fields = ['user_id']
        
        for field in required_fields:
            if field not in session_data:
                raise ValidationError(f"Missing required session field: {field}")
        
        # Validate user_id
        if not isinstance(session_data['user_id'], int) or session_data['user_id'] <= 0:
            raise ValidationError("Invalid user_id in session data")
        
        # Validate optional fields
        if 'ip_address' in session_data:
            AuthValidator.validate_ip_address(session_data['ip_address'])
        
        if 'user_agent' in session_data:
            AuthValidator.validate_user_agent(session_data['user_agent'])
    
    @staticmethod
    def validate_ip_address(ip_address: str) -> None:
        """Validate IP address format"""
        if not ip_address:
            return
        
        # IPv4 validation
        ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        
        # IPv6 validation (simplified)
        ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        
        if not (re.match(ipv4_pattern, ip_address) or re.match(ipv6_pattern, ip_address)):
            raise ValidationError("Invalid IP address format")
    
    @staticmethod
    def validate_user_agent(user_agent: str) -> None:
        """Validate user agent string"""
        if not user_agent:
            return
        
        # Basic user agent validation
        if len(user_agent) > 500:
            raise ValidationError("User agent string too long")
        
        # Check for potentially dangerous characters
        if re.search(r'[<>&"\'\\]', user_agent):
            raise ValidationError("Invalid user agent format")
    
    @staticmethod
    def validate_device_info(device_info: str) -> None:
        """Validate device information"""
        if not device_info:
            return
        
        if len(device_info) > 200:
            raise ValidationError("Device info string too long")
        
        # Check for potentially dangerous characters
        if re.search(r'[<>&"\'\\]', device_info):
            raise ValidationError("Invalid device info format")
    
    @staticmethod
    def validate_two_factor_code(code: str) -> None:
        """Validate two-factor authentication code"""
        if not code or not code.strip():
            raise ValidationError("2FA code cannot be empty")
        
        code = code.strip()
        
        # Standard TOTP codes are 6 digits
        if not re.match(r'^\d{6}$', code):
            raise ValidationError("2FA code must be 6 digits")
    
    @staticmethod
    def validate_backup_code(code: str) -> None:
        """Validate backup code"""
        if not code or not code.strip():
            raise ValidationError("Backup code cannot be empty")
        
        code = code.strip()
        
        # Backup codes are typically 8 digits
        if not re.match(r'^\d{8}$', code):
            raise ValidationError("Backup code must be 8 digits")
    
    @staticmethod
    def validate_security_event(event_type: str, description: str) -> None:
        """Validate security event data"""
        valid_event_types = [
            'LOGIN_SUCCESS',
            'LOGIN_FAILURE',
            'LOGOUT',
            'PASSWORD_CHANGE',
            'PASSWORD_RESET',
            'EMAIL_VERIFICATION',
            'ACCOUNT_LOCKED',
            'ACCOUNT_UNLOCKED',
            'TWO_FACTOR_ENABLED',
            'TWO_FACTOR_DISABLED',
            'TOKEN_REFRESH',
            'SESSION_CREATED',
            'SESSION_EXPIRED'
        ]
        
        if event_type not in valid_event_types:
            raise ValidationError(f"Invalid event type: {event_type}")
        
        if not description or not description.strip():
            raise ValidationError("Event description cannot be empty")
        
        if len(description) > 500:
            raise ValidationError("Event description too long")
    
    @staticmethod
    def validate_login_attempt_data(
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Validate login attempt data"""
        # Validate email
        AuthValidator.validate_email_format(email)
        
        # Validate optional fields
        if ip_address:
            AuthValidator.validate_ip_address(ip_address)
        
        if user_agent:
            AuthValidator.validate_user_agent(user_agent)
    
    @staticmethod
    def validate_account_lock_duration(duration: int) -> None:
        """Validate account lock duration"""
        if not isinstance(duration, int) or duration <= 0:
            raise ValidationError("Lock duration must be a positive integer")
        
        # Maximum lock duration (24 hours)
        max_duration = 24 * 60 * 60
        if duration > max_duration:
            raise ValidationError(f"Lock duration cannot exceed {max_duration} seconds")
    
    @staticmethod
    def validate_password_history(
        new_password: str,
        password_history: List[str],
        history_limit: int = 5
    ) -> None:
        """Validate password against history"""
        from app.core.security import SecurityUtils
        
        # Check against recent passwords
        for old_password_hash in password_history[-history_limit:]:
            if SecurityUtils.verify_password(new_password, old_password_hash):
                raise ValidationError(f"Password cannot be the same as your last {history_limit} passwords")
    
    @staticmethod
    def validate_rate_limit_data(
        identifier: str,
        max_attempts: int,
        window_minutes: int
    ) -> None:
        """Validate rate limit data"""
        if not identifier or not identifier.strip():
            raise ValidationError("Rate limit identifier cannot be empty")
        
        if not isinstance(max_attempts, int) or max_attempts <= 0:
            raise ValidationError("Max attempts must be a positive integer")
        
        if not isinstance(window_minutes, int) or window_minutes <= 0:
            raise ValidationError("Time window must be a positive integer")
        
        # Reasonable limits
        if max_attempts > 1000:
            raise ValidationError("Max attempts cannot exceed 1000")
        
        if window_minutes > 1440:  # 24 hours
            raise ValidationError("Time window cannot exceed 1440 minutes")
    
    @staticmethod
    def validate_token_expiry(expires_at: datetime) -> None:
        """Validate token expiry time"""
        if expires_at <= datetime.utcnow():
            raise ValidationError("Token expiry time must be in the future")
        
        # Maximum token lifetime (30 days)
        max_lifetime = timedelta(days=30)
        if expires_at > datetime.utcnow() + max_lifetime:
            raise ValidationError("Token lifetime cannot exceed 30 days")


class LoginValidator(AuthValidator):
    """Login-specific validators"""
    
    @staticmethod
    def validate_login_request(email: str, password: str, remember_me: bool = False) -> None:
        """Validate login request"""
        AuthValidator.validate_login_credentials(email, password)
        
        # Validate remember_me flag
        if not isinstance(remember_me, bool):
            raise ValidationError("Remember me flag must be a boolean")
    
    @staticmethod
    def validate_login_attempt_limit(email: str, failed_attempts: int, max_attempts: int = 5) -> None:
        """Validate login attempt limits"""
        if failed_attempts >= max_attempts:
            raise ValidationError(f"Too many failed login attempts for {email}. Please try again later.")


class RegistrationValidator(AuthValidator):
    """Registration-specific validators"""
    
    @staticmethod
    def validate_registration_request(
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None
    ) -> None:
        """Validate registration request"""
        AuthValidator.validate_registration_data(email, password, first_name, last_name, phone)
        
        # Additional registration-specific validation
        RegistrationValidator.validate_email_availability(email)
    
    @staticmethod
    def validate_email_availability(email: str) -> None:
        """Validate email availability (placeholder)"""
        # This would typically check against the database
        # For now, we'll just validate the format
        AuthValidator.validate_email_format(email)
    
    @staticmethod
    def validate_terms_acceptance(accepted: bool) -> None:
        """Validate terms and conditions acceptance"""
        if not accepted:
            raise ValidationError("You must accept the terms and conditions")


class PasswordResetValidator(AuthValidator):
    """Password reset-specific validators"""
    
    @staticmethod
    def validate_reset_request(email: str) -> None:
        """Validate password reset request"""
        AuthValidator.validate_email_format(email)
    
    @staticmethod
    def validate_reset_completion(token: str, new_password: str) -> None:
        """Validate password reset completion"""
        AuthValidator.validate_reset_token(token)
        AuthValidator.validate_password_strength(new_password)
