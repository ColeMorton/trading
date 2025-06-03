"""Configuration interface definition."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConfigurationInterface(ABC):
    """Interface for configuration management."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass

    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        pass

    @abstractmethod
    def load_from_file(self, path: Path) -> None:
        """Load configuration from file."""
        pass

    @abstractmethod
    def save_to_file(self, path: Path) -> None:
        """Save configuration to file."""
        pass

    @abstractmethod
    def merge(self, config: Dict[str, Any]) -> None:
        """Merge configuration with existing."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate configuration integrity."""
        pass

    @abstractmethod
    def get_environment(self) -> str:
        """Get current environment (dev, test, prod)."""
        pass

    @abstractmethod
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all configuration keys."""
        pass

    @abstractmethod
    def reload(self) -> None:
        """Reload configuration from source."""
        pass
