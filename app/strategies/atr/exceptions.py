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

    pass


class ATRConfigurationError(ATRError, ConfigurationError):
    """Exception raised for ATR configuration errors."""

    pass


class ATRExecutionError(ATRError, StrategyProcessingError):
    """Exception raised for ATR strategy execution errors."""

    pass


class ATRPortfolioError(ATRError, PortfolioLoadError):
    """Exception raised for ATR portfolio processing errors."""

    pass


class ATRDataError(ATRError):
    """Exception raised for ATR data processing errors."""

    pass


class ATRSyntheticTickerError(ATRError, SyntheticTickerError):
    """Exception raised for ATR synthetic ticker errors."""

    pass


class ATRExportError(ATRError, ExportError):
    """Exception raised for ATR export errors."""

    pass
