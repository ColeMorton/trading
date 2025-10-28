"""
SMA_ATR Strategy Exceptions

This module defines custom exceptions for the SMA_ATR strategy implementation.
"""


class SMAAtrError(Exception):
    """Base exception for all SMA_ATR strategy errors."""



class SMAAtrConfigurationError(SMAAtrError):
    """Raised when there's an error in SMA_ATR configuration."""



class SMAAtrExecutionError(SMAAtrError):
    """Raised when there's an error during SMA_ATR strategy execution."""



class SMAAtrPortfolioError(SMAAtrError):
    """Raised when there's an error in SMA_ATR portfolio processing."""



class SMAAtrDataError(SMAAtrError):
    """Raised when there's an error with data processing in SMA_ATR."""



class SMAAtrSignalError(SMAAtrError):
    """Raised when there's an error in signal generation for SMA_ATR."""

