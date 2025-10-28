"""Utility functions for the RAG project."""
import logging
from typing import Optional
from functools import wraps
import time


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string for log messages
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry a function on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} attempts: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
            
        return wrapper
    return decorator


def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    import re
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    return url_pattern.match(url) is not None


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of the output
        suffix: Suffix to add if text is truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_document_metadata(metadata: dict) -> str:
    """
    Format document metadata for display.
    
    Args:
        metadata: Dictionary of metadata
        
    Returns:
        Formatted string
    """
    if not metadata:
        return "No metadata available"
    
    formatted = []
    for key, value in metadata.items():
        formatted.append(f"{key.title()}: {value}")
    
    return ", ".join(formatted)
