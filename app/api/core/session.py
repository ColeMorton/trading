"""
Session management with Redis backend for secure cookie-based authentication.

This module provides session middleware and Redis-backed session storage
for the SSE proxy authentication system.
"""

import json
import secrets
from typing import Any, Optional

from fastapi import FastAPI
from redis.asyncio import Redis
from starlette.middleware.sessions import SessionMiddleware

from .config import settings


class RedisSessionBackend:
    """
    Redis-backed session storage.
    
    Stores session data in Redis with automatic TTL expiration.
    Key format: session:{session_id}
    """
    
    def __init__(self, redis_client: Redis):
        """
        Initialize Redis session backend.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.prefix = "session:"
        self.ttl = settings.SESSION_MAX_AGE
    
    async def get(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieve session data from Redis.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session data dictionary or None if not found
        """
        key = f"{self.prefix}{session_id}"
        data = await self.redis.get(key)
        
        if data is None:
            return None
        
        return json.loads(data)
    
    async def set(self, session_id: str, data: dict[str, Any]) -> None:
        """
        Store session data in Redis with TTL.
        
        Args:
            session_id: Unique session identifier
            data: Session data to store
        """
        key = f"{self.prefix}{session_id}"
        await self.redis.setex(
            key,
            self.ttl,
            json.dumps(data)
        )
    
    async def delete(self, session_id: str) -> None:
        """
        Delete session from Redis.
        
        Args:
            session_id: Unique session identifier
        """
        key = f"{self.prefix}{session_id}"
        await self.redis.delete(key)
    
    async def exists(self, session_id: str) -> bool:
        """
        Check if session exists in Redis.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session exists, False otherwise
        """
        key = f"{self.prefix}{session_id}"
        return await self.redis.exists(key) > 0
    
    async def refresh_ttl(self, session_id: str) -> None:
        """
        Refresh session TTL (sliding expiration).
        
        Args:
            session_id: Unique session identifier
        """
        key = f"{self.prefix}{session_id}"
        await self.redis.expire(key, self.ttl)


def generate_session_secret() -> str:
    """
    Generate a secure random secret key for session encryption.
    
    Returns:
        Hexadecimal secret key string
    """
    return secrets.token_hex(32)


def setup_session_middleware(app: FastAPI) -> None:
    """
    Configure and add session middleware to FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Generate secret key if not provided
    secret_key = settings.SESSION_SECRET_KEY
    if not secret_key or secret_key == "generate-a-secure-random-key-here":
        secret_key = generate_session_secret()
        if settings.ENVIRONMENT == "production":
            raise ValueError(
                "SESSION_SECRET_KEY must be set in production environment"
            )
    
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        session_cookie=settings.SESSION_COOKIE_NAME,
        max_age=settings.SESSION_MAX_AGE,
        https_only=settings.SESSION_COOKIE_SECURE,
        same_site=settings.SESSION_COOKIE_SAMESITE,
        httponly=settings.SESSION_COOKIE_HTTPONLY,
    )


async def validate_session(session_id: str, redis_backend: RedisSessionBackend) -> bool:
    """
    Validate session is active and not expired.
    
    Args:
        session_id: Session identifier
        redis_backend: Redis session backend
        
    Returns:
        True if session is valid, False otherwise
    """
    if not session_id:
        return False
    
    # Check session exists in Redis
    if not await redis_backend.exists(session_id):
        return False
    
    # Refresh TTL for sliding expiration
    await redis_backend.refresh_ttl(session_id)
    
    return True

