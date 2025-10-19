"""
Configuration management for the unified trading CLI.

This package handles YAML-based configuration profiles with inheritance,
validation, and type safety using Pydantic models.
"""

from .loader import ConfigLoader
from .manager import ConfigManager, ProfileManager
from .profiles import Profile, ProfileConfig


__all__ = [
    "ConfigLoader",
    "ConfigManager",
    "Profile",
    "ProfileConfig",
    "ProfileManager",
]
