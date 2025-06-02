"""Logging interface definition."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class LoggingInterface(ABC):
    """Abstract interface for logging operations."""
    
    @abstractmethod
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for the given name."""
        pass
    
    @abstractmethod
    def configure(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Configure logging settings."""
        pass
    
    @abstractmethod
    def set_level(self, level: str) -> None:
        """Set the logging level."""
        pass