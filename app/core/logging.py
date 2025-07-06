"""
Logging configuration and setup
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

from app.core.config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON
        """
        # Create log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
            "process_name": record.processName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "message"
            ]:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output
    """
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors
        """
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            record.levelname = colored_levelname
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname for other formatters
        record.levelname = levelname
        
        return formatted


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    json_format: bool = False,
    enable_colors: bool = True,
) -> None:
    """
    Setup logging configuration
    """
    log_level = log_level or settings.LOG_LEVEL
    log_file = log_file or settings.LOG_FILE
    
    # Create logs directory if using file logging
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": settings.LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(module)s:%(funcName)s:%(lineno)d - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": JSONFormatter,
            },
            "colored": {
                "()": ColoredFormatter,
                "format": settings.LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "colored" if enable_colors and not json_format else "standard",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "celery": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    
    # Add file handler if log file is specified
    if log_file:
        logging_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json" if json_format else "detailed",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        }
        
        # Add file handler to all loggers
        for logger_name in logging_config["loggers"]:
            logging_config["loggers"][logger_name]["handlers"].append("file")
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, File: {log_file or 'None'}")


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance
    """
    return logging.getLogger(name)


def log_request(
    method: str,
    url: str,
    status_code: int,
    duration: float,
    user_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log HTTP request
    """
    logger = get_logger("request")
    
    log_data = {
        "method": method,
        "url": url,
        "status_code": status_code,
        "duration": duration,
        "user_id": user_id,
    }
    
    if extra:
        log_data.update(extra)
    
    logger.info(f"{method} {url} - {status_code} - {duration:.3f}s", extra=log_data)


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
) -> None:
    """
    Log error with context
    """
    logger = get_logger("error")
    
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "user_id": user_id,
    }
    
    if context:
        log_data.update(context)
    
    logger.error(f"Error: {error}", extra=log_data, exc_info=True)


def log_background_task(
    task_name: str,
    task_id: str,
    status: str,
    duration: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log background task execution
    """
    logger = get_logger("background_task")
    
    log_data = {
        "task_name": task_name,
        "task_id": task_id,
        "status": status,
        "duration": duration,
    }
    
    if extra:
        log_data.update(extra)
    
    message = f"Background task {task_name} [{task_id}] - {status}"
    if duration:
        message += f" - {duration:.3f}s"
    
    logger.info(message, extra=log_data)


def log_database_operation(
    operation: str,
    table: str,
    record_id: Optional[str] = None,
    duration: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log database operation
    """
    logger = get_logger("database")
    
    log_data = {
        "operation": operation,
        "table": table,
        "record_id": record_id,
        "duration": duration,
    }
    
    if extra:
        log_data.update(extra)
    
    message = f"Database {operation} on {table}"
    if record_id:
        message += f" [{record_id}]"
    if duration:
        message += f" - {duration:.3f}s"
    
    logger.info(message, extra=log_data)


# Setup logging on module import
if not logging.getLogger().handlers:
    setup_logging()
