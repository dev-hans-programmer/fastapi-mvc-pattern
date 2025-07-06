"""
Common utility functions
"""

import hashlib
import hmac
import json
import re
import secrets
import string
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, unquote
import base64


def generate_uuid() -> str:
    """
    Generate a UUID4 string
    """
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """
    Generate a short random ID
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_token(length: int = 32) -> str:
    """
    Generate a secure random token
    """
    return secrets.token_urlsafe(length)


def generate_api_key(prefix: str = "ak", length: int = 32) -> str:
    """
    Generate an API key with prefix
    """
    token = secrets.token_urlsafe(length)
    return f"{prefix}_{token}"


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using the specified algorithm
    """
    if algorithm == "md5":
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(text.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(text.encode()).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(text.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def verify_signature(message: str, signature: str, secret: str, algorithm: str = "sha256") -> bool:
    """
    Verify HMAC signature
    """
    expected_signature = hmac.new(
        secret.encode(),
        message.encode(),
        getattr(hashlib, algorithm)
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


def create_signature(message: str, secret: str, algorithm: str = "sha256") -> str:
    """
    Create HMAC signature
    """
    return hmac.new(
        secret.encode(),
        message.encode(),
        getattr(hashlib, algorithm)
    ).hexdigest()


def encode_base64(data: Union[str, bytes]) -> str:
    """
    Encode data to base64 string
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')


def decode_base64(encoded_data: str) -> bytes:
    """
    Decode base64 string to bytes
    """
    return base64.b64decode(encoded_data)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    """
    # Remove or replace dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'\.+', '.', sanitized)  # Replace multiple dots
    sanitized = sanitized.strip('. ')  # Remove leading/trailing dots and spaces
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = f"file_{generate_short_id()}"
    
    return sanitized


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def validate_email(email: str) -> bool:
    """
    Validate email address format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format (basic)
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a reasonable length (7-15 digits)
    return 7 <= len(digits_only) <= 15


def validate_url(url: str) -> bool:
    """
    Validate URL format
    """
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
    return re.match(pattern, url) is not None


def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Clean and normalize text
    """
    if not text:
        return ""
    
    # Strip whitespace
    cleaned = text.strip()
    
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Truncate if necessary
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()
    
    return cleaned


def extract_numbers(text: str) -> List[float]:
    """
    Extract all numbers from text
    """
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(match) for match in matches if match]


def mask_sensitive_data(data: str, visible_chars: int = 4, mask_char: str = "*") -> str:
    """
    Mask sensitive data showing only first/last characters
    """
    if len(data) <= visible_chars * 2:
        return mask_char * len(data)
    
    start = data[:visible_chars]
    end = data[-visible_chars:]
    middle = mask_char * (len(data) - visible_chars * 2)
    
    return start + middle + end


def format_currency(amount: float, currency: str = "USD", locale: str = "en_US") -> str:
    """
    Format currency amount
    """
    # Simple formatting - in production, use locale-specific formatting
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"€{amount:,.2f}"
    elif currency == "GBP":
        return f"£{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def calculate_age(birth_date: datetime) -> int:
    """
    Calculate age from birth date
    """
    today = datetime.now(timezone.utc)
    age = today.year - birth_date.year
    
    # Adjust if birthday hasn't occurred this year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age


def format_duration(seconds: int) -> str:
    """
    Format duration in human-readable format
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}m {seconds}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


def parse_query_string(query_string: str) -> Dict[str, Any]:
    """
    Parse query string into dictionary
    """
    params = {}
    
    if not query_string:
        return params
    
    for pair in query_string.split('&'):
        if '=' in pair:
            key, value = pair.split('=', 1)
            key = unquote(key)
            value = unquote(value)
            
            # Handle multiple values for same key
            if key in params:
                if not isinstance(params[key], list):
                    params[key] = [params[key]]
                params[key].append(value)
            else:
                params[key] = value
    
    return params


def build_query_string(params: Dict[str, Any]) -> str:
    """
    Build query string from dictionary
    """
    pairs = []
    
    for key, value in params.items():
        if isinstance(value, list):
            for v in value:
                pairs.append(f"{quote(str(key))}={quote(str(v))}")
        else:
            pairs.append(f"{quote(str(key))}={quote(str(value))}")
    
    return '&' if pairs else ''


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(data: Dict[str, Any], separator: str = '.', prefix: str = '') -> Dict[str, Any]:
    """
    Flatten nested dictionary
    """
    items = []
    
    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, separator, new_key).items())
        else:
            items.append((new_key, value))
    
    return dict(items)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates(lst: List[Any], key: Optional[str] = None) -> List[Any]:
    """
    Remove duplicates from list
    """
    if key:
        seen = set()
        result = []
        for item in lst:
            value = item.get(key) if isinstance(item, dict) else getattr(item, key, None)
            if value not in seen:
                seen.add(value)
                result.append(item)
        return result
    else:
        return list(dict.fromkeys(lst))


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """
    Safely parse JSON string
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, default: Any = None, **kwargs) -> Optional[str]:
    """
    Safely serialize data to JSON
    """
    try:
        return json.dumps(data, **kwargs)
    except (TypeError, ValueError):
        return default


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Check if string is a valid UUID
    """
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def get_client_ip(request_headers: Dict[str, str]) -> str:
    """
    Extract client IP from request headers
    """
    # Check for forwarded headers
    forwarded_for = request_headers.get('X-Forwarded-For', '').split(',')
    if forwarded_for and forwarded_for[0].strip():
        return forwarded_for[0].strip()
    
    # Check other headers
    real_ip = request_headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fallback to remote address
    return request_headers.get('Remote-Addr', 'unknown')


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula (in kilometers)
    """
    import math
    
    # Convert latitude and longitude to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in kilometers
    r = 6371
    
    return c * r


class DateTimeUtils:
    """
    Date and time utility functions
    """
    
    @staticmethod
    def now_utc() -> datetime:
        """Get current UTC datetime"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def to_iso_string(dt: datetime) -> str:
        """Convert datetime to ISO string"""
        return dt.isoformat()
    
    @staticmethod
    def from_iso_string(iso_string: str) -> datetime:
        """Parse ISO string to datetime"""
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    
    @staticmethod
    def add_days(dt: datetime, days: int) -> datetime:
        """Add days to datetime"""
        return dt + timedelta(days=days)
    
    @staticmethod
    def start_of_day(dt: datetime) -> datetime:
        """Get start of day"""
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def end_of_day(dt: datetime) -> datetime:
        """Get end of day"""
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    @staticmethod
    def format_relative_time(dt: datetime) -> str:
        """Format time relative to now"""
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
