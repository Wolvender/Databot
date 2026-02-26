# logger.py - Centralized logging for debugging and monitoring
"""
Production-grade logging with file rotation and structured logging
Supports different log levels for dev/prod environments
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json

class StructuredLogger:
    """Custom logger with JSON formatting for enterprise monitoring."""
    
    def __init__(self, name: str = "databot", log_dir: str = "logs", level: str = "INFO"):
        """Initialize logger with file and console handlers."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create logs directory
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # File handler with rotation (10MB per file, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_path / f"{name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def log_event(self, level: str, event: str, **kwargs):
        """Log structured event with metadata."""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            **kwargs
        }
        
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        """Log info level message."""
        self.log_event("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message."""
        self.log_event("warning", message, **kwargs)
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error level message with exception details."""
        error_data = kwargs.copy()
        if error:
            error_data["error_type"] = type(error).__name__
            error_data["error_message"] = str(error)
        self.log_event("error", message, **error_data)
    
    def debug(self, message: str, **kwargs):
        """Log debug level message."""
        self.log_event("debug", message, **kwargs)

# Global logger instance
logger = StructuredLogger()

# Usage examples:
# logger.info("User logged in", username="admin", ip="192.168.1.1")
# logger.error("LLM API failed", error=e, file_name="invoice.pdf", retry_count=3)
# logger.warning("Low confidence extraction", confidence=0.45, document_type="receipt")
