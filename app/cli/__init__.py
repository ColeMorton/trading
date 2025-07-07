"""
Unified Trading CLI System.

A comprehensive, type-safe CLI interface for trading strategy analysis,
portfolio management, concurrency analysis, Statistical Performance Divergence System (SPDS),
and trade history management using Typer, YAML configuration, and Pydantic validation.
"""

from .config import ConfigLoader, ConfigManager, ProfileManager
from .main import app, main

__version__ = "2.0.0"
__all__ = ["app", "main", "ConfigManager", "ProfileManager", "ConfigLoader"]
