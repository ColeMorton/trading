"""
API Security Utility

This module provides security functionality for the API server.
It includes utilities for future authentication and authorization.
"""

import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional


class APIKeyManager:
    """
    API key management class.

    This class provides functionality for managing API keys.
    Note: This is a placeholder for future implementation.
    """

    def __init__(self, logger: logging.Logger):
        """
        Initialize the API key manager.

        Args:
            logger (logging.Logger): Logger instance
        """
        self.logger = logger
        self.api_keys = {}

    def generate_api_key(self, user_id: str, expiration_days: int = 365) -> str:
        """
        Generate a new API key.

        Args:
            user_id (str): User ID
            expiration_days (int): Number of days until the key expires

        Returns:
            str: Generated API key
        """
        # Generate a random API key
        api_key = secrets.token_urlsafe(32)

        # Set expiration date
        expiration = datetime.now() + timedelta(days=expiration_days)

        # Store API key
        self.api_keys[api_key] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "expires_at": expiration,
            "is_active": True,
        }

        self.logger.info(f"Generated API key for user {user_id}")

        return api_key

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate an API key.

        Args:
            api_key (str): API key to validate

        Returns:
            bool: True if the API key is valid, False otherwise
        """
        if api_key not in self.api_keys:
            return False

        key_info = self.api_keys[api_key]

        # Check if the key is active
        if not key_info["is_active"]:
            return False

        # Check if the key has expired
        if datetime.now() > key_info["expires_at"]:
            return False

        return True

    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key.

        Args:
            api_key (str): API key to revoke

        Returns:
            bool: True if the API key was revoked, False otherwise
        """
        if api_key not in self.api_keys:
            return False

        self.api_keys[api_key]["is_active"] = False

        user_id = self.api_keys[api_key]["user_id"]
        self.logger.info(f"Revoked API key for user {user_id}")

        return True


def validate_path(
    path: str, allowed_dirs: List[str], base_dir: Optional[str] = None
) -> bool:
    """
    Validate that a path is within allowed directories.

    Args:
        path (str): Path to validate
        allowed_dirs (List[str]): List of allowed directories
        base_dir (Optional[str]): Base directory

    Returns:
        bool: True if the path is valid, False otherwise
    """
    # Normalize path
    normalized_path = os.path.normpath(path)

    # Check if path is within any allowed directory
    for allowed_dir in allowed_dirs:
        # If base_dir is provided, prepend it to the allowed_dir
        if base_dir:
            full_allowed_dir = os.path.join(base_dir, allowed_dir)
        else:
            full_allowed_dir = allowed_dir

        # Normalize the allowed directory path
        full_allowed_dir = os.path.normpath(full_allowed_dir)

        # Check if the path starts with the allowed directory
        if normalized_path.startswith(full_allowed_dir):
            return True

    return False
