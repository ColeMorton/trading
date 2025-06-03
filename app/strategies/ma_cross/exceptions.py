"""
MA Cross Strategy Exception Types

This module defines specific exception types for the MA Cross strategy module,
extending the base error handling framework for domain-specific error scenarios.
"""

from app.tools.exceptions import (
    ConfigurationError,
    DataError,
    PortfolioError,
    StrategyError,
    TradingSystemError,
)


class MACrossError(StrategyError):
    """Base exception for MA Cross strategy errors."""

    pass


class MACrossConfigurationError(MACrossError, ConfigurationError):
    """Raised when MA Cross configuration is invalid."""

    def __init__(self, message: str, config_field: str = None, config_value=None):
        details = {
            "config_field": config_field,
            "config_value": config_value,
            "error_type": "configuration",
        }
        super().__init__(message, details)


class MACrossDataError(MACrossError, DataError):
    """Raised when MA Cross data processing fails."""

    def __init__(self, message: str, ticker: str = None, data_type: str = None):
        details = {
            "ticker": ticker,
            "data_type": data_type,
            "error_type": "data_processing",
        }
        super().__init__(message, details)


class MACrossCalculationError(MACrossError):
    """Raised when MA Cross calculations fail."""

    def __init__(self, message: str, ticker: str = None, calculation_type: str = None):
        details = {
            "ticker": ticker,
            "calculation_type": calculation_type,
            "error_type": "calculation",
        }
        super().__init__(message, details)


class MACrossPortfolioError(MACrossError, PortfolioError):
    """Raised when MA Cross portfolio operations fail."""

    def __init__(self, message: str, ticker: str = None, operation: str = None):
        details = {
            "ticker": ticker,
            "operation": operation,
            "error_type": "portfolio_processing",
        }
        super().__init__(message, details)


class MACrossValidationError(MACrossError):
    """Raised when MA Cross input validation fails."""

    def __init__(self, message: str, field: str = None, value=None):
        details = {"field": field, "value": value, "error_type": "validation"}
        super().__init__(message, details)


class MACrossExecutionError(MACrossError):
    """Raised when MA Cross strategy execution fails."""

    def __init__(self, message: str, ticker: str = None, stage: str = None):
        details = {
            "ticker": ticker,
            "execution_stage": stage,
            "error_type": "execution",
        }
        super().__init__(message, details)


class MACrossSyntheticTickerError(MACrossError):
    """Raised when synthetic ticker processing fails."""

    def __init__(
        self, message: str, synthetic_ticker: str = None, component_tickers: list = None
    ):
        details = {
            "synthetic_ticker": synthetic_ticker,
            "component_tickers": component_tickers,
            "error_type": "synthetic_ticker",
        }
        super().__init__(message, details)
