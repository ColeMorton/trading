"""Concrete implementation of logging interface."""

import logging
import logging.config
from typing import Any

from app.core.interfaces import ConfigurationInterface, LoggingInterface


class LoggingService(LoggingInterface):
    """Concrete implementation of logging service."""

    def __init__(self, config: ConfigurationInterface | None | None = None):
        self._config = config
        self._loggers: dict[str, logging.Logger] = {}
        self.configure()

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for the given name."""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]

    def configure(self, config: dict[str, Any] | None = None) -> None:
        """Configure logging settings."""
        if config and "version" in config:
            logging.config.dictConfig(config)
        elif self._config:
            # Load from configuration service
            log_config = self._config.get_section("logging")
            if log_config and "version" in log_config:
                logging.config.dictConfig(log_config)
            else:
                # Use simple configuration from config service or default
                level = (
                    self._config.get("logging.level", "INFO")
                    if self._config
                    else "INFO"
                )
                format_str = (
                    self._config.get(
                        "logging.format",
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    )
                    if self._config
                    else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                logging.basicConfig(
                    level=getattr(logging, level.upper(), logging.INFO),
                    format=format_str,
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
        else:
            self._configure_default()

    def set_level(self, level: str) -> None:
        """Set the logging level."""
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(numeric_level)

        # Update all cached loggers
        for logger in self._loggers.values():
            logger.setLevel(numeric_level)

    def _configure_default(self) -> None:
        """Configure default logging settings."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
