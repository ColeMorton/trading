"""Exception types for the trading system.

This module defines specific exception types for different error scenarios,
following the Single Responsibility Principle by separating error types
by their domain and purpose.
"""

from typing import Any, Dict, Optional


class TradingSystemError(Exception):
    """Base exception for all trading system errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize with message and optional details dictionary.

        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ConfigurationError(TradingSystemError):
    """Raised when there's an issue with configuration parameters."""


class PortfolioError(TradingSystemError):
    """Base class for portfolio-related errors."""


class PortfolioLoadError(PortfolioError):
    """Raised when a portfolio cannot be loaded."""


class PortfolioProcessingError(PortfolioError):
    """Raised when there's an error processing a portfolio."""


class StrategyError(TradingSystemError):
    """Base class for strategy-related errors."""


class StrategyProcessingError(StrategyError):
    """Raised when there's an error processing a strategy."""


class SyntheticTickerError(StrategyError):
    """Raised when there's an issue with synthetic ticker processing."""


class DataError(TradingSystemError):
    """Base class for data-related errors."""


class DataLoadError(DataError):
    """Raised when data cannot be loaded."""


class ExportError(TradingSystemError):
    """Raised when results cannot be exported."""


class RiskCalculationError(TradingSystemError):
    """Base class for portfolio risk calculation errors."""


class DataAlignmentError(RiskCalculationError):
    """Raised when return series alignment fails."""


class CovarianceMatrixError(RiskCalculationError):
    """Raised when covariance matrix calculation fails."""


class PortfolioVarianceError(RiskCalculationError):
    """Raised when portfolio variance calculation fails."""
