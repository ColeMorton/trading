"""
SMA_ATR Strategy Exceptions

This module defines custom exceptions for the SMA_ATR strategy implementation.
"""


class SMAAtrError(Exception):
    """Base exception for all SMA_ATR strategy errors."""

    pass


class SMAAtrConfigurationError(SMAAtrError):
    """Raised when there's an error in SMA_ATR configuration."""

    pass


class SMAAtrExecutionError(SMAAtrError):
    """Raised when there's an error during SMA_ATR strategy execution."""

    pass


class SMAAtrPortfolioError(SMAAtrError):
    """Raised when there's an error in SMA_ATR portfolio processing."""

    pass


class SMAAtrDataError(SMAAtrError):
    """Raised when there's an error with data processing in SMA_ATR."""

    pass


class SMAAtrSignalError(SMAAtrError):
    """Raised when there's an error in signal generation for SMA_ATR."""

    pass
