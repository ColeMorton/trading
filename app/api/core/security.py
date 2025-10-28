"""
Security utilities for API key management.

This module provides API key generation, hashing, and validation utilities
for securing API endpoints.
"""

import hashlib
import secrets

import bcrypt
from fastapi import Depends, Header, HTTPException, status

from .config import settings


def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure random API key.

    Args:
        length: Length of the API key (default: 32)

    Returns:
        Hexadecimal API key string
    """
    return secrets.token_hex(length)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using bcrypt.

    Args:
        api_key: Plain text API key

    Returns:
        Bcrypt hash of the API key
    """
    salt = bcrypt.gensalt()
    key_bytes = api_key.encode("utf-8")
    hashed = bcrypt.hashpw(key_bytes, salt)
    return hashed.decode("utf-8")


def verify_api_key(api_key: str, key_hash: str) -> bool:
    """
    Verify an API key against its hash.

    Args:
        api_key: Plain text API key
        key_hash: Stored bcrypt hash

    Returns:
        True if key matches hash
    """
    key_bytes = api_key.encode("utf-8")
    hash_bytes = key_hash.encode("utf-8")
    return bcrypt.checkpw(key_bytes, hash_bytes)


def compute_key_fingerprint(api_key: str) -> str:
    """
    Compute a fingerprint for an API key for logging purposes.

    Args:
        api_key: Plain text API key

    Returns:
        SHA256 hash prefix (first 8 characters)
    """
    hash_obj = hashlib.sha256(api_key.encode("utf-8"))
    return hash_obj.hexdigest()[:8]


class APIKey:
    """API key model for dependency injection."""

    def __init__(
        self,
        id: str,
        name: str,
        scopes: list[str],
        rate_limit: int,
        is_active: bool,
    ):
        self.id = id
        self.name = name
        self.scopes = scopes
        self.rate_limit = rate_limit
        self.is_active = is_active

    def has_scope(self, scope: str) -> bool:
        """Check if API key has a specific scope."""
        return scope in self.scopes or "*" in self.scopes


async def get_api_key_from_header(
    x_api_key: str | None = Header(None, alias=settings.API_KEY_HEADER),
) -> str:
    """
    Extract API key from request header.

    Args:
        x_api_key: API key from header

    Returns:
        API key string

    Raises:
        HTTPException: If API key is missing
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": f"{settings.API_KEY_HEADER}"},
        )

    if len(x_api_key) < settings.API_KEY_MIN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"API key must be at least {settings.API_KEY_MIN_LENGTH} characters",
        )

    return x_api_key


async def validate_api_key(
    api_key: str = Depends(get_api_key_from_header),
) -> APIKey:
    """
    Validate API key and return APIKey object.

    This is a placeholder that will be replaced with actual database lookup
    once the database models are implemented.

    Args:
        api_key: Plain text API key from header

    Returns:
        APIKey object with permissions

    Raises:
        HTTPException: If API key is invalid or inactive
    """
    # Development key - ONLY allowed in development environment
    if api_key == "dev-key-" + "0" * 24:
        # Absolutely prevent in production
        if settings.ENVIRONMENT == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Development API keys not valid in production",
            )
        
        # Additional safety: check if DEBUG is disabled
        if not settings.DEBUG:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Development API keys require DEBUG mode",
            )
        
        return APIKey(
            id="00000000-0000-0000-0000-000000000000",
            name="Development Key",
            scopes=["*"],
            rate_limit=settings.RATE_LIMIT_DEFAULT,
            is_active=True,
        )
    
    # TODO: Replace with actual database lookup
    # This is where production keys will be validated
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or inactive API key",
    )


def require_scope(required_scope: str):
    """
    Create a dependency that checks for a specific scope.

    Args:
        required_scope: Required scope name (e.g., 'strategy', 'portfolio')

    Returns:
        Dependency function for FastAPI
    """

    async def _check_scope(api_key: APIKey = Depends(validate_api_key)) -> APIKey:
        """Check if API key has required scope."""
        if not api_key.has_scope(required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{required_scope}' required for this operation",
            )
        return api_key

    return _check_scope


def require_any_scope(*required_scopes: str):
    """
    Create a dependency that checks for any of multiple scopes.

    Args:
        required_scopes: List of acceptable scope names

    Returns:
        Dependency function for FastAPI
    """

    async def _check_scopes(api_key: APIKey = Depends(validate_api_key)) -> APIKey:
        """Check if API key has any of the required scopes."""
        if not any(api_key.has_scope(scope) for scope in required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of scopes {required_scopes} required for this operation",
            )
        return api_key

    return _check_scopes
