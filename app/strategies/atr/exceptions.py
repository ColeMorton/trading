"""
ATR Strategy Exception Classes

This module defines exception classes specific to the ATR trailing stop strategy,
providing clear error reporting and handling for strategy-specific errors.
"""

from app.tools.exceptions import (
    ConfigurationError,
    ExportError,
    PortfolioLoadError,
    StrategyProcessingError,
    SyntheticTickerError,
)


class ATRError(Exception):
    """Base exception for ATR strategy errors."""


class ATRConfigurationError(ATRError, ConfigurationError):
    """Exception raised for ATR configuration errors."""


class ATRExecutionError(ATRError, StrategyProcessingError):
    """Exception raised for ATR strategy execution errors."""


class ATRPortfolioError(ATRError, PortfolioLoadError):
    """Exception raised for ATR portfolio processing errors."""


class ATRDataError(ATRError):
    """Exception raised for ATR data processing errors."""


class ATRSyntheticTickerError(ATRError, SyntheticTickerError):
    """Exception raised for ATR synthetic ticker errors."""


class ATRExportError(ATRError, ExportError):
    """Exception raised for ATR export errors."""
