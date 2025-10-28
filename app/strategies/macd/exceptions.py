"""
MACD Strategy Exception Classes

This module defines exception classes specific to the MACD strategy,
providing clear error reporting and handling for strategy-specific errors.
"""

from app.tools.exceptions import (
    ConfigurationError,
    ExportError,
    PortfolioLoadError,
    StrategyProcessingError,
    SyntheticTickerError,
)


class MACDError(Exception):
    """Base exception for MACD strategy errors."""



class MACDConfigurationError(MACDError, ConfigurationError):
    """Exception raised for MACD configuration errors."""



class MACDExecutionError(MACDError, StrategyProcessingError):
    """Exception raised for MACD strategy execution errors."""



class MACDPortfolioError(MACDError, PortfolioLoadError):
    """Exception raised for MACD portfolio processing errors."""



class MACDDataError(MACDError):
    """Exception raised for MACD data processing errors."""



class MACDSyntheticTickerError(MACDError, SyntheticTickerError):
    """Exception raised for MACD synthetic ticker errors."""



class MACDExportError(MACDError, ExportError):
    """Exception raised for MACD export errors."""

