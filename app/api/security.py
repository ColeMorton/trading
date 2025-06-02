"""
Security configuration and middleware for production deployment
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import time
import hashlib
import hmac
import os
from typing import Optional, List
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = defaultdict(list)
        
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Special handling for health check endpoints
        if request.url.path.startswith("/health"):
            return await call_next(request)
            
        # Get current time
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if req_time > minute_ago
        ]
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute"
                }
            )
        
        # Record request
        self.request_counts[client_ip].append(now)
        
        # Process request
        return await call_next(request)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS (only in production with HTTPS)
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP for API endpoints
        if request.url.path.startswith("/api"):
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
            
        return response

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate incoming requests for security
    """
    
    def __init__(self, app, max_content_length: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_content_length = max_content_length
        
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "Request entity too large",
                    "max_size": self.max_content_length
                }
            )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            
            # Allow specific content types
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
                "text/plain"  # For GraphQL
            ]
            
            if not any(allowed in content_type for allowed in allowed_types):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={
                        "error": "Unsupported media type",
                        "allowed_types": allowed_types
                    }
                )
        
        return await call_next(request)

class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API key authentication for production
    """
    
    def __init__(self, app, protected_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.protected_paths = protected_paths or ["/api/scripts/execute"]
        self.api_key = os.getenv("API_KEY")
        
    async def dispatch(self, request: Request, call_next):
        # Skip if no API key is configured
        if not self.api_key:
            return await call_next(request)
            
        # Check if path requires authentication
        path = request.url.path
        requires_auth = any(path.startswith(protected) for protected in self.protected_paths)
        
        if requires_auth:
            # Check API key in header
            provided_key = request.headers.get("X-API-Key")
            
            if not provided_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"error": "API key required"}
                )
                
            # Validate API key
            if not hmac.compare_digest(provided_key, self.api_key):
                logger.warning(f"Invalid API key attempt from IP: {request.client.host}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Invalid API key"}
                )
        
        return await call_next(request)

def get_cors_origins() -> List[str]:
    """
    Get allowed CORS origins based on environment
    """
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "development":
        return ["*"]
    else:
        # Production origins
        origins = os.getenv("CORS_ORIGINS", "").split(",")
        return [origin.strip() for origin in origins if origin.strip()]

def setup_security_middleware(app):
    """
    Setup all security middleware for the application
    """
    # Add trusted host middleware (production only)
    if os.getenv("ENVIRONMENT") == "production":
        allowed_hosts = os.getenv("ALLOWED_HOSTS", "").split(",")
        if allowed_hosts:
            app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=[host.strip() for host in allowed_hosts if host.strip()]
            )
    
    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add request validation
    app.add_middleware(RequestValidationMiddleware)
    
    # Add rate limiting
    rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    app.add_middleware(RateLimitMiddleware, requests_per_minute=rate_limit)
    
    # Add API key authentication (if configured)
    if os.getenv("API_KEY"):
        app.add_middleware(APIKeyMiddleware)
    
    logger.info("Security middleware configured")