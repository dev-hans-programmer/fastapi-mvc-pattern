"""
Logging configuration and utilities
"""
import logging
import logging.config
import sys
from typing import Dict, Any
from pathlib import Path

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured information."""
        # Add extra fields to the record
        record.environment = settings.ENVIRONMENT
        record.service = settings.PROJECT_NAME
        
        # Call parent formatter
        return super().format(record)


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration based on environment."""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "()": StructuredFormatter,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(environment)s - %(service)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s - %(message)s"
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(environment)s %(service)s %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed" if settings.is_development else "json",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "celery": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            }
        }
    }
    
    # In production, remove console handler and use only file handlers
    if settings.is_production:
        config["loggers"][""]["handlers"] = ["file", "error_file"]
    
    return config


def setup_logging() -> None:
    """Setup logging configuration."""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Get the root logger
    logger = logging.getLogger()
    
    logger.info(f"Logging setup complete for environment: {settings.ENVIRONMENT}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


# Context manager for logging with extra context
class LogContext:
    """Context manager for adding extra context to log messages."""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.extra = kwargs
        self.old_extra = getattr(logger, '_extra', {})
    
    def __enter__(self):
        self.logger._extra = {**self.old_extra, **self.extra}
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger._extra = self.old_extra


def log_with_context(logger: logging.Logger, **kwargs):
    """Create a log context with extra information."""
    return LogContext(logger, **kwargs)
