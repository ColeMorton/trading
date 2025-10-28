"""
Position-related exceptions for the trading system.

Provides structured exception hierarchy to replace mixed error patterns
(None returns, silent failures) with clear, meaningful exceptions.
"""


class PositionError(Exception):
    """Base exception for all position-related operations."""

    def __init__(self, message: str, position_uuid: str | None = None, **kwargs):
        super().__init__(message)
        self.position_uuid = position_uuid
        self.details = kwargs


class ValidationError(PositionError):
    """Raised when position data fails validation."""



class CalculationError(PositionError):
    """Raised when position calculations fail."""



class DataNotFoundError(PositionError):
    """Raised when required data is not found."""



class PriceDataError(PositionError):
    """Raised when price data is missing or invalid."""



class SignalValidationError(PositionError):
    """Raised when signal validation fails."""



class PortfolioError(PositionError):
    """Raised when portfolio operations fail."""



class ConfigurationError(PositionError):
    """Raised when configuration is invalid or missing."""

