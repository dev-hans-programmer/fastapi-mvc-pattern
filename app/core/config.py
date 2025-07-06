"""
Application configuration management
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings with environment-specific configurations
    """
    
    # Application settings
    PROJECT_NAME: str = Field(default="FastAPI Backend", description="Project name")
    ENVIRONMENT: str = Field(default="development", description="Environment (development, qa, production)")
    DEBUG: bool = Field(default=True, description="Debug mode")
    PORT: int = Field(default=8000, description="Server port")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    WORKERS: int = Field(default=4, description="Number of worker processes")
    
    # Security settings
    SECRET_KEY: str = Field(default="your-secret-key-here", description="Secret key for JWT")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration")
    
    # Database settings
    DATABASE_URL: Optional[str] = Field(default=None, description="Database connection URL")
    PGDATABASE: Optional[str] = Field(default=None, description="PostgreSQL database name")
    PGHOST: Optional[str] = Field(default=None, description="PostgreSQL host")
    PGPASSWORD: Optional[str] = Field(default=None, description="PostgreSQL password")
    PGPORT: Optional[str] = Field(default=None, description="PostgreSQL port")
    PGUSER: Optional[str] = Field(default=None, description="PostgreSQL user")
    
    # Redis settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    
    # Celery settings
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", description="Celery result backend")
    CELERY_TASK_SERIALIZER: str = Field(default="json", description="Celery task serializer")
    CELERY_RESULT_SERIALIZER: str = Field(default="json", description="Celery result serializer")
    CELERY_ACCEPT_CONTENT: List[str] = Field(default=["json"], description="Celery accepted content types")
    CELERY_TIMEZONE: str = Field(default="UTC", description="Celery timezone")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path")
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], description="Allowed CORS origins")
    
    # Thread pool settings
    THREAD_POOL_MAX_WORKERS: int = Field(default=10, description="Maximum thread pool workers")
    THREAD_POOL_TIMEOUT: int = Field(default=30, description="Thread pool timeout in seconds")
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Rate limit requests per minute")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")
    
    # API settings
    API_PREFIX: str = Field(default="/api/v1", description="API prefix")
    API_VERSION: str = Field(default="v1", description="API version")
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Maximum file size in bytes (10MB)")
    ALLOWED_FILE_TYPES: List[str] = Field(default=["image/jpeg", "image/png", "image/gif"], description="Allowed file types")
    
    # Cache settings
    CACHE_TTL: int = Field(default=300, description="Cache TTL in seconds")
    CACHE_MAX_SIZE: int = Field(default=1000, description="Maximum cache size")
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment values"""
        allowed_environments = ["development", "qa", "production"]
        if v not in allowed_environments:
            raise ValueError(f"Environment must be one of: {allowed_environments}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level values"""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {allowed_levels}")
        return v.upper()
    
    @validator("DEBUG", pre=True)
    def set_debug_mode(cls, v, values):
        """Set debug mode based on environment"""
        environment = values.get("ENVIRONMENT", "development")
        if environment == "production":
            return False
        return v
    
    def get_database_url(self) -> Optional[str]:
        """Get database URL from environment or construct from components"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        if all([self.PGHOST, self.PGUSER, self.PGPASSWORD, self.PGDATABASE]):
            port = self.PGPORT or "5432"
            return f"postgresql://{self.PGUSER}:{self.PGPASSWORD}@{self.PGHOST}:{port}/{self.PGDATABASE}"
        
        return None
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            """Customize settings sources priority"""
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    env = os.getenv("ENVIRONMENT", "development")
    env_file = f"configs/{env}.env"
    
    if os.path.exists(env_file):
        logger.info(f"Loading environment configuration from: {env_file}")
        return Settings(_env_file=env_file)
    else:
        logger.warning(f"Environment file not found: {env_file}, using default settings")
        return Settings()


def get_environment_settings(environment: str) -> Settings:
    """
    Get settings for a specific environment
    """
    env_file = f"configs/{environment}.env"
    if os.path.exists(env_file):
        return Settings(_env_file=env_file)
    else:
        raise FileNotFoundError(f"Environment configuration file not found: {env_file}")
