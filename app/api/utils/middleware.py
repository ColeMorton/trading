"""
Middleware utilities for the API.

This module provides FastAPI dependencies and middleware for cross-cutting concerns
like rate limiting, authentication, and request tracking.
"""

from fastapi import Request, HTTPException, Depends
from typing import Optional
import math

from .rate_limiter import get_analysis_limiter, get_cache_limiter


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address
    """
    # Check for forwarded headers (proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct connection IP
    return request.client.host if request.client else "unknown"


def rate_limit_analysis(request: Request = None) -> None:
    """
    FastAPI dependency for rate limiting analysis endpoints.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    if request is None:
        return  # Skip rate limiting if no request (testing)
    
    client_ip = get_client_ip(request)
    limiter = get_analysis_limiter()
    
    allowed, retry_after = limiter.is_allowed(client_ip)
    
    if not allowed:
        retry_after_int = math.ceil(retry_after) if retry_after else 60
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many analysis requests. Please try again later.",
                "retry_after": retry_after_int
            },
            headers={"Retry-After": str(retry_after_int)}
        )


def rate_limit_cache(request: Request = None) -> None:
    """
    FastAPI dependency for rate limiting cache management endpoints.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    if request is None:
        return  # Skip rate limiting if no request (testing)
    
    client_ip = get_client_ip(request)
    limiter = get_cache_limiter()
    
    allowed, retry_after = limiter.is_allowed(client_ip)
    
    if not allowed:
        retry_after_int = math.ceil(retry_after) if retry_after else 60
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many cache requests. Please try again later.",
                "retry_after": retry_after_int
            },
            headers={"Retry-After": str(retry_after_int)}
        )


def get_request_info(request: Request) -> dict:
    """
    Extract useful information from request for logging/monitoring.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary with request information
    """
    return {
        "client_ip": get_client_ip(request),
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers)
    }