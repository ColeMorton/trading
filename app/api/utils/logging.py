"""
API Logging Utility

This module extends the project's logging setup for API-specific logging.
It provides consistent logging across the API server.
"""

import os
import time
import logging
from typing import Callable, Tuple
from app.tools.setup_logging import setup_logging as base_setup_logging

def setup_api_logging() -> Tuple[Callable[[str, str], None], Callable[[], None], logging.Logger, logging.FileHandler]:
    """
    Sets up API-specific logging configuration.
    
    This function extends the base logging setup with API-specific configuration.
    
    Returns:
        Tuple[Callable, Callable, logging.Logger, logging.FileHandler]: 
            - log: Pre-configured logging function
            - log_close: Function to close logging and print execution time
            - logger: Configured logger instance
            - file_handler: Configured file handler
    """
    # Use the base setup_logging function with API-specific parameters
    log, log_close, logger, file_handler = base_setup_logging(
        module_name='api',
        log_file='api_server.log',
        level=logging.INFO,
        mode='a',  # Append to log file instead of overwriting
        log_subdir='server'  # Store logs in logs/api/server/
    )
    
    # Log API server startup
    log("API server logging initialized")
    
    return log, log_close, logger, file_handler

def log_request(logger: logging.Logger, request_method: str, request_path: str, 
                status_code: int, processing_time: float) -> None:
    """
    Logs API request information.
    
    Args:
        logger (logging.Logger): Logger instance
        request_method (str): HTTP method (GET, POST, etc.)
        request_path (str): Request path
        status_code (int): HTTP status code
        processing_time (float): Request processing time in seconds
    """
    logger.info(
        f"Request: {request_method} {request_path} | "
        f"Status: {status_code} | "
        f"Time: {processing_time:.4f}s"
    )

class RequestLoggingMiddleware:
    """Middleware for logging API requests and responses."""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize the middleware with a logger.
        
        Args:
            logger (logging.Logger): Logger instance
        """
        self.logger = logger
    
    async def __call__(self, request, call_next):
        """
        Process the request, log details, and pass to the next middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware in the chain
            
        Returns:
            The response from the next middleware
        """
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log request details
        log_request(
            self.logger,
            request.method,
            request.url.path,
            response.status_code,
            processing_time
        )
        
        return response