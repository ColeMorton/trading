"""Logging interface definition."""

from abc import ABC, abstractmethod
import logging
from typing import Any


class LoggingInterface(ABC):
    """Abstract interface for logging operations."""

    @abstractmethod
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for the given name."""

    @abstractmethod
    def configure(self, config: dict[str, Any] | None = None) -> None:
        """Configure logging settings."""

    @abstractmethod
    def set_level(self, level: str) -> None:
        """Set the logging level."""
