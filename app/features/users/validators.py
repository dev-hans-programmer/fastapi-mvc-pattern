"""
User validators
"""
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, date

from app.common.validators import BaseValidator, CustomValidationError
from app.core.exceptions import ValidationError


class UserValidator(BaseValidator):
    """User-specific validators"""
    
    @staticmethod
    def validate_user_creation_data(
        email: str,
        first_name: str,
        last_name: str,
        password: str,
        phone: Optional[str] = None,
        role: Optional[str] = None
    ) -> None:
        """Validate user creation data"""
        # Validate email
        UserValidator.validate_email_format(email)
        
        # Validate names
        UserValidator.validate_user_name(first_name, "First name")
        UserValidator.validate_user_name(last_name, "Last name")
        
        # Validate password
        UserValidator.validate_password_strength(password)
        
        # Validate phone if provided
        if phone:
            UserValidator.validate_phone_number(phone)
        
        # Validate role if provided
        if role:
            UserValidator.validate_user_role(role)
    
    @staticmethod
    def validate_user_update_data(
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        role: Optional[str] = None,
        bio: Optional[str] = None,
        location: Optional[str] = None,
        date_of_birth: Optional[datetime] = None
    ) -> None:
        """Validate user update data"""
        # Validate email if provided
        if email:
            UserValidator.validate_email_format(email)
        
        # Validate names if provided
        if first_name:
            UserValidator.validate_user_name(first_name, "First name")
        
        if last_name:
            UserValidator.validate_user_name(last_name, "Last name")
        
        # Validate phone if provided
        if phone:
            UserValidator.validate_phone_number(phone)
        
        # Validate role if provided
        if role:
            UserValidator.validate_user_role(role)
        
        # Validate bio if provided
        if bio:
            UserValidator.validate_user_bio(bio)
        
        # Validate location if provided
        if location:
            UserValidator.validate_location(location)
        
        # Validate date of birth if provided
        if date_of_birth:
            UserValidator.validate_date_of_birth(date_of_birth)
    
    @staticmethod
    def validate_user_name(name: str, field_name: str) -> None:
        """Validate user name fields"""
        if not name or not name.strip():
            raise ValidationError(f"{field_name} cannot be empty")
        
        name = name.strip()
        
        # Check length
        if len(name) < 1 or len(name) > 50:
            raise ValidationError(f"{field_name} must be between 1 and 50 characters")
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise ValidationError(f"{field_name} can only contain letters, spaces, hyphens, and apostrophes")
        
        # Check for reasonable patterns
        if re.match(r"^[\s\-']+$", name):
            raise ValidationError(f"{field_name} must contain at least one letter")
    
    @staticmethod
    def validate_user_role(role: str) -> None:
        """Validate user role"""
        valid_roles = ["admin", "user", "moderator", "guest"]
        UserValidator.validate_choice(role, valid_roles, "Role")
    
    @staticmethod
    def validate_user_bio(bio: str) -> None:
        """Validate user bio"""
        if len(bio) > 500:
            raise ValidationError("Bio cannot exceed 500 characters")
        
        # Check for potentially dangerous content
        if re.search(r'<script|javascript:|<iframe|<object|<embed', bio, re.IGNORECASE):
            raise ValidationError("Bio contains potentially dangerous content")
    
    @staticmethod
    def validate_location(location: str) -> None:
        """Validate user location"""
        if len(location) > 100:
            raise ValidationError("Location cannot exceed 100 characters")
        
        # Basic format validation
        if not re.match(r"^[a-zA-Z0-9\s,.-]+$", location):
            raise ValidationError("Location contains invalid characters")
    
    @staticmethod
    def validate_date_of_birth(dob: datetime) -> None:
        """Validate date of birth"""
        today = datetime.now().date()
        birth_date = dob.date() if isinstance(dob, datetime) else dob
        
        # Check if date is in the future
        if birth_date > today:
            raise ValidationError("Date of birth cannot be in the future")
        
        # Check if age is reasonable (not older than 150 years)
        age_limit = today.replace(year=today.year - 150)
        if birth_date < age_limit:
            raise ValidationError("Date of birth is too far in the past")
        
        # Check if user is at least 13 years old (COPPA compliance)
        min_age_date = today.replace(year=today.year - 13)
        if birth_date > min_age_date:
            raise ValidationError("User must be at least 13 years old")
    
    @staticmethod
    def validate_gender(gender: str) -> None:
        """Validate gender field"""
        valid_genders = ["male", "female", "other", "prefer_not_to_say"]
        UserValidator.validate_choice(gender, valid_genders, "Gender")
    
    @staticmethod
    def validate_timezone(timezone: str) -> None:
        """Validate timezone"""
        # This is a simplified validation - in production, you'd use pytz
        common_timezones = [
            "UTC", "America/New_York", "America/Chicago", "America/Denver",
            "America/Los_Angeles", "Europe/London", "Europe/Paris",
            "Europe/Berlin", "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney"
        ]
        
        if timezone not in common_timezones:
            # For now, just check basic format
            if not re.match(r"^[A-Za-z_]+/[A-Za-z_]+$", timezone):
                raise ValidationError("Invalid timezone format")
    
    @staticmethod
    def validate_avatar_url(url: str) -> None:
        """Validate avatar URL"""
        UserValidator.validate_url(url)
        
        # Check if it's an image URL (basic check)
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        if not any(url.lower().endswith(ext) for ext in image_extensions):
            # If no extension, check for common image hosting patterns
            image_hosts = ['imgur.com', 'gravatar.com', 'cloudinary.com', 'amazonaws.com']
            if not any(host in url.lower() for host in image_hosts):
                raise ValidationError("URL does not appear to be a valid image URL")
    
    @staticmethod
    def validate_user_profile_data(profile_data: Dict[str, Any]) -> None:
        """Validate user profile data"""
        allowed_fields = [
            'first_name', 'last_name', 'phone', 'bio', 'avatar_url',
            'date_of_birth', 'gender', 'location', 'timezone'
        ]
        
        # Check for invalid fields
        invalid_fields = [field for field in profile_data.keys() if field not in allowed_fields]
        if invalid_fields:
            raise ValidationError(f"Invalid profile fields: {', '.join(invalid_fields)}")
        
        # Validate each field
        for field, value in profile_data.items():
            if value is None:
                continue
                
            if field in ['first_name', 'last_name']:
                UserValidator.validate_user_name(value, field.replace('_', ' ').title())
            elif field == 'phone':
                UserValidator.validate_phone_number(value)
            elif field == 'bio':
                UserValidator.validate_user_bio(value)
            elif field == 'avatar_url':
                UserValidator.validate_avatar_url(value)
            elif field == 'date_of_birth':
                if isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        raise ValidationError("Invalid date format for date_of_birth")
                UserValidator.validate_date_of_birth(value)
            elif field == 'gender':
                UserValidator.validate_gender(value)
            elif field == 'location':
                UserValidator.validate_location(value)
            elif field == 'timezone':
                UserValidator.validate_timezone(value)
    
    @staticmethod
    def validate_bulk_user_data(users_data: List[Dict[str, Any]]) -> None:
        """Validate bulk user creation data"""
        if not users_data:
            raise ValidationError("No user data provided")
        
        if len(users_data) > 1000:
            raise ValidationError("Cannot create more than 1000 users at once")
        
        emails = []
        for i, user_data in enumerate(users_data):
            try:
                # Validate required fields
                required_fields = ['email', 'first_name', 'last_name', 'password']
                for field in required_fields:
                    if field not in user_data:
                        raise ValidationError(f"Missing required field: {field}")
                
                # Validate individual user data
                UserValidator.validate_user_creation_data(
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    password=user_data['password'],
                    phone=user_data.get('phone'),
                    role=user_data.get('role')
                )
                
                # Check for duplicate emails in the batch
                if user_data['email'] in emails:
                    raise ValidationError(f"Duplicate email in batch: {user_data['email']}")
                emails.append(user_data['email'])
                
            except ValidationError as e:
                raise ValidationError(f"User {i+1}: {str(e)}")
    
    @staticmethod
    def validate_user_search_params(
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> None:
        """Validate user search parameters"""
        # Validate search term
        if not search_term or not search_term.strip():
            raise ValidationError("Search term cannot be empty")
        
        search_term = search_term.strip()
        if len(search_term) < 2:
            raise ValidationError("Search term must be at least 2 characters long")
        
        if len(search_term) > 100:
            raise ValidationError("Search term cannot exceed 100 characters")
        
        # Validate search fields
        valid_search_fields = ['first_name', 'last_name', 'email', 'phone']
        invalid_fields = [field for field in search_fields if field not in valid_search_fields]
        if invalid_fields:
            raise ValidationError(f"Invalid search fields: {', '.join(invalid_fields)}")
        
        # Validate pagination parameters
        UserValidator.validate_positive_number(skip + 1, "Skip")  # skip can be 0
        UserValidator.validate_positive_number(limit, "Limit")
        
        if limit > 1000:
            raise ValidationError("Limit cannot exceed 1000")
    
    @staticmethod
    def validate_user_filter_params(filters: Dict[str, Any]) -> None:
        """Validate user filter parameters"""
        valid_filters = [
            'role', 'is_active', 'is_verified', 'created_after',
            'created_before', 'last_login_after', 'last_login_before'
        ]
        
        invalid_filters = [key for key in filters.keys() if key not in valid_filters]
        if invalid_filters:
            raise ValidationError(f"Invalid filter parameters: {', '.join(invalid_filters)}")
        
        # Validate specific filter values
        if 'role' in filters:
            UserValidator.validate_user_role(filters['role'])
        
        if 'is_active' in filters and not isinstance(filters['is_active'], bool):
            raise ValidationError("is_active filter must be a boolean")
        
        if 'is_verified' in filters and not isinstance(filters['is_verified'], bool):
            raise ValidationError("is_verified filter must be a boolean")
        
        # Validate date filters
        date_filters = ['created_after', 'created_before', 'last_login_after', 'last_login_before']
        for date_filter in date_filters:
            if date_filter in filters:
                try:
                    if isinstance(filters[date_filter], str):
                        datetime.fromisoformat(filters[date_filter].replace('Z', '+00:00'))
                except ValueError:
                    raise ValidationError(f"Invalid date format for {date_filter}")


class UserPasswordValidator(UserValidator):
    """User password-specific validators"""
    
    @staticmethod
    def validate_password_change_request(
        old_password: str,
        new_password: str,
        confirm_password: str
    ) -> None:
        """Validate password change request"""
        if not old_password:
            raise ValidationError("Current password is required")
        
        if not new_password:
            raise ValidationError("New password is required")
        
        if not confirm_password:
            raise ValidationError("Password confirmation is required")
        
        if new_password != confirm_password:
            raise ValidationError("New password and confirmation do not match")
        
        # Validate new password strength
        UserPasswordValidator.validate_password_strength(new_password)
        
        # Ensure new password is different from old password
        if old_password == new_password:
            raise ValidationError("New password must be different from current password")


class UserRoleValidator(UserValidator):
    """User role-specific validators"""
    
    @staticmethod
    def validate_role_change_request(
        current_role: str,
        new_role: str,
        requester_role: str
    ) -> None:
        """Validate role change request"""
        # Validate roles
        UserRoleValidator.validate_user_role(new_role)
        UserRoleValidator.validate_user_role(requester_role)
        
        # Check permissions
        if requester_role != 'admin':
            raise ValidationError("Only administrators can change user roles")
        
        # Prevent demoting the last admin
        if current_role == 'admin' and new_role != 'admin':
            # In a real implementation, you'd check if this is the last admin
            pass  # Placeholder for admin count check
        
        # Role hierarchy validation
        role_hierarchy = {
            'guest': 0,
            'user': 1,
            'moderator': 2,
            'admin': 3
        }
        
        current_level = role_hierarchy.get(current_role, 0)
        new_level = role_hierarchy.get(new_role, 0)
        requester_level = role_hierarchy.get(requester_role, 0)
        
        # Requester must have higher privileges than both current and new roles
        if requester_level <= max(current_level, new_level):
            raise ValidationError("Insufficient privileges to change to this role")


class UserImportValidator(UserValidator):
    """User import-specific validators"""
    
    @staticmethod
    def validate_import_format(file_format: str) -> None:
        """Validate import file format"""
        valid_formats = ['csv', 'json', 'xlsx']
        if file_format.lower() not in valid_formats:
            raise ValidationError(f"Unsupported import format. Supported formats: {', '.join(valid_formats)}")
    
    @staticmethod
    def validate_import_data_structure(data: List[Dict[str, Any]], format: str) -> None:
        """Validate import data structure"""
        if not data:
            raise ValidationError("Import data cannot be empty")
        
        if len(data) > 10000:
            raise ValidationError("Cannot import more than 10,000 users at once")
        
        # Validate headers/structure
        required_fields = ['email', 'first_name', 'last_name']
        first_row = data[0]
        
        missing_fields = [field for field in required_fields if field not in first_row]
        if missing_fields:
            raise ValidationError(f"Missing required fields in import data: {', '.join(missing_fields)}")
        
        # Validate each row
        emails = set()
        for i, row in enumerate(data):
            try:
                # Check required fields
                for field in required_fields:
                    if not row.get(field):
                        raise ValidationError(f"Row {i+1}: Missing value for required field '{field}'")
                
                # Check for duplicate emails
                email = row['email'].lower()
                if email in emails:
                    raise ValidationError(f"Row {i+1}: Duplicate email '{email}' found in import data")
                emails.add(email)
                
                # Validate data format
                UserValidator.validate_email_format(row['email'])
                UserValidator.validate_user_name(row['first_name'], 'First name')
                UserValidator.validate_user_name(row['last_name'], 'Last name')
                
                # Validate optional fields
                if row.get('phone'):
                    UserValidator.validate_phone_number(row['phone'])
                
                if row.get('role'):
                    UserValidator.validate_user_role(row['role'])
                    
            except ValidationError as e:
                raise ValidationError(f"Row {i+1}: {str(e)}")
