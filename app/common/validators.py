"""
Common validation utilities
"""
import re
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ValidationError as PydanticValidationError, validator
from email_validator import validate_email, EmailNotValidError

from app.core.exceptions import ValidationError


class BaseValidator:
    """Base validator class"""
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate that required fields are present"""
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    @staticmethod
    def validate_string_length(value: str, min_length: int = 0, max_length: int = 255, field_name: str = "Field") -> None:
        """Validate string length"""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        
        if len(value) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters long")
        
        if len(value) > max_length:
            raise ValidationError(f"{field_name} must be no more than {max_length} characters long")
    
    @staticmethod
    def validate_email_format(email: str) -> str:
        """Validate email format"""
        try:
            validated_email = validate_email(email)
            return validated_email.email
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email format: {str(e)}")
    
    @staticmethod
    def validate_phone_number(phone: str) -> str:
        """Validate phone number format"""
        # Remove all non-digit characters
        phone_digits = re.sub(r'[^\d]', '', phone)
        
        # Check if phone number has valid length (10-15 digits)
        if len(phone_digits) < 10 or len(phone_digits) > 15:
            raise ValidationError("Phone number must be between 10 and 15 digits")
        
        # Check if it starts with valid country code patterns
        if not re.match(r'^(\+?1)?[2-9]\d{2}[2-9]\d{2}\d{4}$', phone_digits):
            # If not US format, check for international format
            if not re.match(r'^\+?[1-9]\d{1,14}$', phone_digits):
                raise ValidationError("Invalid phone number format")
        
        return phone_digits
    
    @staticmethod
    def validate_url(url: str) -> None:
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            raise ValidationError("Invalid URL format")
    
    @staticmethod
    def validate_password_strength(password: str) -> None:
        """Validate password strength"""
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:,.<>?]', password):
            raise ValidationError("Password must contain at least one special character")
    
    @staticmethod
    def validate_positive_number(value: Union[int, float], field_name: str = "Value") -> None:
        """Validate that a number is positive"""
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field_name} must be a number")
        
        if value <= 0:
            raise ValidationError(f"{field_name} must be a positive number")
    
    @staticmethod
    def validate_non_negative_number(value: Union[int, float], field_name: str = "Value") -> None:
        """Validate that a number is non-negative"""
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field_name} must be a number")
        
        if value < 0:
            raise ValidationError(f"{field_name} must be a non-negative number")
    
    @staticmethod
    def validate_choice(value: Any, choices: List[Any], field_name: str = "Value") -> None:
        """Validate that a value is in a list of choices"""
        if value not in choices:
            raise ValidationError(f"{field_name} must be one of: {', '.join(map(str, choices))}")
    
    @staticmethod
    def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> None:
        """Validate date format"""
        from datetime import datetime
        
        try:
            datetime.strptime(date_str, format_str)
        except ValueError:
            raise ValidationError(f"Invalid date format. Expected format: {format_str}")
    
    @staticmethod
    def validate_json_structure(data: str, expected_keys: List[str] = None) -> Dict[str, Any]:
        """Validate JSON structure"""
        import json
        
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {str(e)}")
        
        if expected_keys:
            missing_keys = [key for key in expected_keys if key not in parsed_data]
            if missing_keys:
                raise ValidationError(f"Missing required JSON keys: {', '.join(missing_keys)}")
        
        return parsed_data
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> None:
        """Validate file extension"""
        if not filename:
            raise ValidationError("Filename cannot be empty")
        
        file_extension = filename.split('.')[-1].lower()
        allowed_extensions = [ext.lower() for ext in allowed_extensions]
        
        if file_extension not in allowed_extensions:
            raise ValidationError(f"File extension must be one of: {', '.join(allowed_extensions)}")
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int = 10 * 1024 * 1024) -> None:
        """Validate file size (default max 10MB)"""
        if file_size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            raise ValidationError(f"File size must be less than {max_size_mb:.1f}MB")
    
    @staticmethod
    def sanitize_html(html_content: str) -> str:
        """Sanitize HTML content"""
        # Remove potentially dangerous tags and attributes
        import re
        
        # Remove script tags
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove style tags
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove javascript: URLs
        html_content = re.sub(r'javascript:[^"\']*', '', html_content, flags=re.IGNORECASE)
        
        # Remove on* event handlers
        html_content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
        
        return html_content
    
    @staticmethod
    def validate_sql_injection(query: str) -> None:
        """Basic SQL injection validation"""
        dangerous_patterns = [
            r'\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|EXEC|EXECUTE)\b',
            r'[\'"]\s*;\s*[\'"]*',
            r'--',
            r'/\*.*?\*/',
            r'\bUNION\b.*\bSELECT\b',
            r'\bOR\b.*=.*\bOR\b',
            r'\bAND\b.*=.*\bAND\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                raise ValidationError("Potentially dangerous SQL detected")


class PaginationValidator(BaseValidator):
    """Pagination-specific validators"""
    
    @staticmethod
    def validate_pagination_params(page: int, page_size: int, max_page_size: int = 100) -> None:
        """Validate pagination parameters"""
        if page < 1:
            raise ValidationError("Page number must be greater than 0")
        
        if page_size < 1:
            raise ValidationError("Page size must be greater than 0")
        
        if page_size > max_page_size:
            raise ValidationError(f"Page size cannot exceed {max_page_size}")


class SearchValidator(BaseValidator):
    """Search-specific validators"""
    
    @staticmethod
    def validate_search_query(query: str, min_length: int = 2, max_length: int = 100) -> None:
        """Validate search query"""
        if not query or not query.strip():
            raise ValidationError("Search query cannot be empty")
        
        query = query.strip()
        
        if len(query) < min_length:
            raise ValidationError(f"Search query must be at least {min_length} characters long")
        
        if len(query) > max_length:
            raise ValidationError(f"Search query cannot exceed {max_length} characters")
        
        # Check for dangerous patterns
        dangerous_patterns = [r'<script', r'javascript:', r'<iframe', r'<object', r'<embed']
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                raise ValidationError("Search query contains potentially dangerous content")


class BulkOperationValidator(BaseValidator):
    """Bulk operation validators"""
    
    @staticmethod
    def validate_bulk_operation_size(items: List[Any], max_items: int = 1000) -> None:
        """Validate bulk operation size"""
        if len(items) > max_items:
            raise ValidationError(f"Bulk operation cannot exceed {max_items} items")
        
        if len(items) == 0:
            raise ValidationError("Bulk operation must contain at least one item")


class ImageValidator(BaseValidator):
    """Image-specific validators"""
    
    @staticmethod
    def validate_image_dimensions(width: int, height: int, max_width: int = 4096, max_height: int = 4096) -> None:
        """Validate image dimensions"""
        if width > max_width or height > max_height:
            raise ValidationError(f"Image dimensions cannot exceed {max_width}x{max_height}")
        
        if width < 1 or height < 1:
            raise ValidationError("Image dimensions must be positive")
    
    @staticmethod
    def validate_image_format(filename: str) -> None:
        """Validate image format"""
        allowed_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
        BaseValidator.validate_file_extension(filename, allowed_formats)


class CurrencyValidator(BaseValidator):
    """Currency-specific validators"""
    
    @staticmethod
    def validate_currency_code(currency_code: str) -> None:
        """Validate currency code (ISO 4217)"""
        # Common currency codes
        valid_currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'SEK', 'NZD',
            'MXN', 'SGD', 'HKD', 'NOK', 'ZAR', 'BRL', 'RUB', 'INR', 'KRW', 'TRY'
        ]
        
        if currency_code not in valid_currencies:
            raise ValidationError(f"Invalid currency code. Must be one of: {', '.join(valid_currencies)}")
    
    @staticmethod
    def validate_amount(amount: Union[int, float], currency: str = "USD") -> None:
        """Validate monetary amount"""
        BaseValidator.validate_non_negative_number(amount, "Amount")
        
        # Check for reasonable limits (adjust based on currency)
        max_amount = 1000000  # 1 million
        if amount > max_amount:
            raise ValidationError(f"Amount cannot exceed {max_amount}")


class PasswordValidator(BaseValidator):
    """Advanced password validation"""
    
    @staticmethod
    def validate_password_history(new_password: str, old_passwords: List[str]) -> None:
        """Validate password against history"""
        from app.core.security import SecurityUtils
        
        for old_password in old_passwords:
            if SecurityUtils.verify_password(new_password, old_password):
                raise ValidationError("New password cannot be the same as previous passwords")
    
    @staticmethod
    def validate_password_complexity(password: str) -> Dict[str, bool]:
        """Validate password complexity and return details"""
        checks = {
            'length': len(password) >= 8,
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'lowercase': bool(re.search(r'[a-z]', password)),
            'digit': bool(re.search(r'\d', password)),
            'special': bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};:,.<>?]', password)),
            'no_common': password.lower() not in [
                'password', '123456', 'qwerty', 'admin', 'letmein', 'welcome'
            ]
        }
        
        return checks


class CustomValidationError(Exception):
    """Custom validation error with detailed information"""
    
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(self.message)


def validate_with_schema(data: Dict[str, Any], schema: BaseModel) -> BaseModel:
    """Validate data against a Pydantic schema"""
    try:
        return schema(**data)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = '.'.join(str(loc) for loc in error['loc'])
            message = error['msg']
            error_messages.append(f"{field}: {message}")
        
        raise ValidationError(f"Validation failed: {'; '.join(error_messages)}")


def validate_conditional_fields(data: Dict[str, Any], conditions: Dict[str, Any]) -> None:
    """Validate conditional field requirements"""
    for field, condition in conditions.items():
        if condition['if_field'] in data and data[condition['if_field']] == condition['if_value']:
            if field not in data or data[field] is None:
                raise ValidationError(f"Field '{field}' is required when '{condition['if_field']}' is '{condition['if_value']}'")
