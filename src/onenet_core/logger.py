"""Centralized logging configuration for onenet_core package."""
import logging
import sys
from typing import Optional

# Configure logging format
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s:%(funcName)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(level: int = logging.DEBUG):
    """
    Setup logging configuration for the application.
    
    Args:
        level: Logging level (default: DEBUG for development)
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        stream=sys.stdout,
        force=True  # Override any existing configuration
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Name of the module (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def mask_session_id(session_id: Optional[str]) -> str:
    """
    Mask session ID for logging (show only first and last 4 characters).
    
    Args:
        session_id: Session ID to mask
    
    Returns:
        Masked session ID or 'None'
    """
    if not session_id:
        return "None"
    if len(session_id) <= 8:
        return "****"
    return f"{session_id[:4]}...{session_id[-4:]}"

def get_client_ip(request) -> str:
    """
    Extract client IP address from request.
    
    Args:
        request: FastAPI Request object
    
    Returns:
        Client IP address
    """
    # Check for forwarded IP first (behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded.split(",")[0].strip()
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"

# Initialize logging when module is imported
setup_logging()
