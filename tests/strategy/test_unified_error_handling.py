"""
Test Suite for Unified Error Handling System

This module tests the consolidated error handling functionality to ensure
it properly handles all error scenarios across trading strategies.
"""

import logging
from unittest.mock import Mock, patch

import polars as pl
import pytest

from app.tools.strategy.error_handling import (
    ConfigurationError,
    DataError,
    ErrorHandlerBase,
    ErrorHandlerFactory,
    ErrorSeverity,
    ExportError,
    ParameterError,
    PermissiveErrorHandler,
    PortfolioError,
    SignalError,
    StandardErrorHandler,
    StrategyError,
    StrategyErrorCode,
    create_error_handler,
    handle_strategy_error,
    validate_data_sufficiency,
    validate_parameters,
)


class TestErrorSeverity:
    """Test cases for ErrorSeverity enum."""

    def test_error_severity_values(self):
        """Test that error severity enum has correct values."""
        assert ErrorSeverity.DEBUG.value == "debug"
        assert ErrorSeverity.INFO.value == "info"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestStrategyErrorCode:
    """Test cases for StrategyErrorCode enum."""

    def test_error_code_categories(self):
        """Test that error codes are properly categorized."""
        # Data-related errors
        assert StrategyErrorCode.INSUFFICIENT_DATA.value == "INSUFFICIENT_DATA"
        assert StrategyErrorCode.INVALID_DATA_FORMAT.value == "INVALID_DATA_FORMAT"

        # Parameter-related errors
        assert StrategyErrorCode.INVALID_PARAMETERS.value == "INVALID_PARAMETERS"
        assert (
            StrategyErrorCode.MISSING_REQUIRED_PARAMETERS.value
            == "MISSING_REQUIRED_PARAMETERS"
        )

        # Signal-related errors
        assert (
            StrategyErrorCode.SIGNAL_CALCULATION_FAILED.value
            == "SIGNAL_CALCULATION_FAILED"
        )
        assert StrategyErrorCode.NO_SIGNALS_GENERATED.value == "NO_SIGNALS_GENERATED"

        # Portfolio-related errors
        assert (
            StrategyErrorCode.PORTFOLIO_CREATION_FAILED.value
            == "PORTFOLIO_CREATION_FAILED"
        )
        assert StrategyErrorCode.BACKTESTING_FAILED.value == "BACKTESTING_FAILED"


class TestStrategyError:
    """Test cases for StrategyError base exception."""

    def test_strategy_error_creation(self):
        """Test creating a strategy error."""
        error = StrategyError(
            "Test error message",
            StrategyErrorCode.INVALID_PARAMETERS,
            ErrorSeverity.ERROR,
            {"param": "value"},
        )

        assert error.message == "Test error message"
        assert error.error_code == StrategyErrorCode.INVALID_PARAMETERS
        assert error.severity == ErrorSeverity.ERROR
        assert error.context == {"param": "value"}

    def test_strategy_error_defaults(self):
        """Test strategy error with default values."""
        error = StrategyError("Test message")

        assert error.message == "Test message"
        assert error.error_code == StrategyErrorCode.UNKNOWN_ERROR
        assert error.severity == ErrorSeverity.ERROR
        assert error.context == {}

    def test_strategy_error_string_representation(self):
        """Test string representation of strategy error."""
        error = StrategyError("Test error", StrategyErrorCode.INVALID_PARAMETERS)

        assert str(error) == "[INVALID_PARAMETERS] Test error"

    def test_strategy_error_to_dict(self):
        """Test converting strategy error to dictionary."""
        error = StrategyError(
            "Test error",
            StrategyErrorCode.INVALID_PARAMETERS,
            ErrorSeverity.WARNING,
            {"context": "test"},
        )

        error_dict = error.to_dict()

        assert error_dict == {
            "message": "Test error",
            "error_code": "INVALID_PARAMETERS",
            "severity": "warning",
            "context": {"context": "test"},
        }


class TestSpecificErrorTypes:
    """Test cases for specific error type classes."""

    def test_data_error(self):
        """Test DataError class."""
        error = DataError("Data error", StrategyErrorCode.INSUFFICIENT_DATA)

        assert isinstance(error, StrategyError)
        assert error.message == "Data error"
        assert error.error_code == StrategyErrorCode.INSUFFICIENT_DATA

    def test_parameter_error(self):
        """Test ParameterError class."""
        error = ParameterError("Parameter error", StrategyErrorCode.INVALID_PARAMETERS)

        assert isinstance(error, StrategyError)
        assert error.message == "Parameter error"
        assert error.error_code == StrategyErrorCode.INVALID_PARAMETERS

    def test_signal_error(self):
        """Test SignalError class."""
        error = SignalError("Signal error", StrategyErrorCode.SIGNAL_CALCULATION_FAILED)

        assert isinstance(error, StrategyError)
        assert error.message == "Signal error"
        assert error.error_code == StrategyErrorCode.SIGNAL_CALCULATION_FAILED

    def test_portfolio_error(self):
        """Test PortfolioError class."""
        error = PortfolioError(
            "Portfolio error",
            StrategyErrorCode.PORTFOLIO_CREATION_FAILED,
        )

        assert isinstance(error, StrategyError)
        assert error.message == "Portfolio error"
        assert error.error_code == StrategyErrorCode.PORTFOLIO_CREATION_FAILED

    def test_export_error(self):
        """Test ExportError class."""
        error = ExportError("Export error", StrategyErrorCode.EXPORT_FAILED)

        assert isinstance(error, StrategyError)
        assert error.message == "Export error"
        assert error.error_code == StrategyErrorCode.EXPORT_FAILED

    def test_configuration_error(self):
        """Test ConfigurationError class."""
        error = ConfigurationError(
            "Config error",
            StrategyErrorCode.INVALID_CONFIGURATION,
        )

        assert isinstance(error, StrategyError)
        assert error.message == "Config error"
        assert error.error_code == StrategyErrorCode.INVALID_CONFIGURATION


class TestErrorHandlerBase:
    """Test cases for ErrorHandlerBase abstract class."""

    def test_error_handler_base_is_abstract(self):
        """Test that ErrorHandlerBase cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ErrorHandlerBase("SMA")

    def test_error_handler_base_implementation(self):
        """Test concrete implementation of ErrorHandlerBase."""

        class TestErrorHandler(ErrorHandlerBase):
            def handle_error(self, error, context=None, reraise=False):
                return {"handled": True}

        handler = TestErrorHandler("SMA")
        assert handler.strategy_type == "SMA"
        assert isinstance(handler.logger, logging.Logger)
        assert all(count == 0 for count in handler.error_counts.values())


class TestStandardErrorHandler:
    """Test cases for StandardErrorHandler."""

    def test_standard_error_handler_initialization(self):
        """Test standard error handler initialization."""
        handler = StandardErrorHandler("SMA", fail_fast=True, max_warnings=50)

        assert handler.strategy_type == "SMA"
        assert handler.fail_fast is True
        assert handler.max_warnings == 50

    def test_handle_strategy_error(self):
        """Test handling a StrategyError."""
        handler = StandardErrorHandler("SMA", fail_fast=False)

        error = StrategyError(
            "Test error",
            StrategyErrorCode.INVALID_PARAMETERS,
            ErrorSeverity.WARNING,
        )

        result = handler.handle_error(error)

        assert result is not None
        assert result["message"] == "Test error"
        assert result["error_code"] == "INVALID_PARAMETERS"
        assert result["severity"] == "warning"

    def test_handle_generic_exception(self):
        """Test handling a generic exception."""
        handler = StandardErrorHandler("SMA", fail_fast=False)

        error = ValueError("Invalid value")

        result = handler.handle_error(error)

        assert result is not None
        assert result["message"] == "Invalid value"
        assert result["error_code"] == "INVALID_PARAMETERS"
        assert result["severity"] == "error"

    def test_fail_fast_behavior(self):
        """Test fail-fast behavior."""
        handler = StandardErrorHandler("SMA", fail_fast=True)

        error = StrategyError(
            "Critical error",
            StrategyErrorCode.OPERATION_FAILED,
            ErrorSeverity.ERROR,
        )

        result = handler.handle_error(error)

        assert result is None  # Should return None due to fail-fast

    def test_fail_fast_with_reraise(self):
        """Test fail-fast behavior with reraise."""
        handler = StandardErrorHandler("SMA", fail_fast=True)

        error = StrategyError(
            "Critical error",
            StrategyErrorCode.OPERATION_FAILED,
            ErrorSeverity.ERROR,
        )

        with pytest.raises(StrategyError):
            handler.handle_error(error, reraise=True)

    def test_max_warnings_exceeded(self):
        """Test behavior when max warnings is exceeded."""
        handler = StandardErrorHandler("SMA", fail_fast=False, max_warnings=2)

        warning_error = StrategyError(
            "Warning",
            StrategyErrorCode.INVALID_PARAMETERS,
            ErrorSeverity.WARNING,
        )

        # First two warnings should be handled normally
        result1 = handler.handle_error(warning_error)
        assert result1 is not None

        result2 = handler.handle_error(warning_error)
        assert result2 is not None

        # Third warning should trigger max warnings exceeded
        result3 = handler.handle_error(warning_error)
        assert result3 is None

    def test_log_error(self):
        """Test error logging functionality."""
        handler = StandardErrorHandler("SMA")

        with patch.object(handler.logger, "error") as mock_error:
            handler.log_error(
                "Test error message",
                ErrorSeverity.ERROR,
                StrategyErrorCode.INVALID_PARAMETERS,
                {"context": "test"},
            )

            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert "[SMA]" in call_args
            assert "[INVALID_PARAMETERS]" in call_args
            assert "Test error message" in call_args
            assert "Context: {'context': 'test'}" in call_args

    def test_error_summary(self):
        """Test error summary functionality."""
        handler = StandardErrorHandler("SMA", fail_fast=False)

        # Handle different types of errors
        handler.handle_error(ValueError("Error 1"))
        handler.handle_error(StrategyError("Warning", severity=ErrorSeverity.WARNING))
        handler.handle_error(KeyError("Error 2"))

        summary = handler.get_error_summary()

        assert summary[ErrorSeverity.ERROR] == 2
        assert summary[ErrorSeverity.WARNING] == 1
        assert summary[ErrorSeverity.INFO] == 0

    def test_reset_error_counts(self):
        """Test resetting error counts."""
        handler = StandardErrorHandler("SMA", fail_fast=False)

        # Generate some errors
        handler.handle_error(ValueError("Error"))
        handler.handle_error(StrategyError("Warning", severity=ErrorSeverity.WARNING))

        # Verify counts
        summary = handler.get_error_summary()
        assert summary[ErrorSeverity.ERROR] == 1
        assert summary[ErrorSeverity.WARNING] == 1

        # Reset and verify
        handler.reset_error_counts()
        summary = handler.get_error_summary()
        assert all(count == 0 for count in summary.values())


class TestPermissiveErrorHandler:
    """Test cases for PermissiveErrorHandler."""

    def test_permissive_error_handler_initialization(self):
        """Test permissive error handler initialization."""
        handler = PermissiveErrorHandler("MACD", collect_errors=True)

        assert handler.strategy_type == "MACD"
        assert handler.collect_errors is True
        assert handler.collected_errors == []

    def test_handle_error_permissively(self):
        """Test permissive error handling."""
        handler = PermissiveErrorHandler("MACD", collect_errors=True)

        error = StrategyError(
            "Test error",
            StrategyErrorCode.SIGNAL_CALCULATION_FAILED,
            ErrorSeverity.ERROR,
        )

        result = handler.handle_error(error)

        assert result is not None
        assert result["message"] == "Test error"
        assert len(handler.collected_errors) == 1

    def test_handle_critical_error_with_reraise(self):
        """Test handling critical error with reraise."""
        handler = PermissiveErrorHandler("MACD")

        error = StrategyError(
            "Critical error",
            StrategyErrorCode.OPERATION_FAILED,
            ErrorSeverity.CRITICAL,
        )

        with pytest.raises(StrategyError):
            handler.handle_error(error, reraise=True)

    def test_collected_errors_functionality(self):
        """Test error collection functionality."""
        handler = PermissiveErrorHandler("MACD", collect_errors=True)

        # Handle multiple errors
        handler.handle_error(ValueError("Error 1"))
        handler.handle_error(KeyError("Error 2"))
        handler.handle_error(StrategyError("Error 3"))

        collected = handler.get_collected_errors()
        assert len(collected) == 3

        # Clear errors
        handler.clear_collected_errors()
        assert len(handler.get_collected_errors()) == 0

    def test_no_error_collection(self):
        """Test handler with error collection disabled."""
        handler = PermissiveErrorHandler("MACD", collect_errors=False)

        handler.handle_error(ValueError("Error"))

        assert len(handler.collected_errors) == 0


class TestErrorHandlerFactory:
    """Test cases for ErrorHandlerFactory."""

    def test_create_standard_handler(self):
        """Test creating standard error handler."""
        handler = ErrorHandlerFactory.create_handler("standard", "SMA")

        assert isinstance(handler, StandardErrorHandler)
        assert handler.strategy_type == "SMA"

    def test_create_permissive_handler(self):
        """Test creating permissive error handler."""
        handler = ErrorHandlerFactory.create_handler("permissive", "MACD")

        assert isinstance(handler, PermissiveErrorHandler)
        assert handler.strategy_type == "MACD"

    def test_create_handler_with_kwargs(self):
        """Test creating handler with additional arguments."""
        handler = ErrorHandlerFactory.create_handler(
            "standard",
            "SMA",
            fail_fast=False,
            max_warnings=200,
        )

        assert isinstance(handler, StandardErrorHandler)
        assert handler.fail_fast is False
        assert handler.max_warnings == 200

    def test_create_unknown_handler_type(self):
        """Test creating handler with unknown type."""
        with pytest.raises(ValueError, match="Unknown handler type: unknown"):
            ErrorHandlerFactory.create_handler("unknown", "SMA")

    def test_get_available_handlers(self):
        """Test getting available handler types."""
        handlers = ErrorHandlerFactory.get_available_handlers()

        assert "standard" in handlers
        assert "permissive" in handlers
        assert len(handlers) == 2


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    def test_create_error_handler(self):
        """Test create_error_handler convenience function."""
        handler = create_error_handler("SMA", "standard", fail_fast=True)

        assert isinstance(handler, StandardErrorHandler)
        assert handler.strategy_type == "SMA"
        assert handler.fail_fast is True

    def test_handle_strategy_error_with_log_function(self):
        """Test handle_strategy_error with log function."""
        mock_log = Mock()

        error = StrategyError(
            "Test error",
            StrategyErrorCode.INVALID_PARAMETERS,
            ErrorSeverity.WARNING,
        )

        result = handle_strategy_error(error, "SMA", mock_log)

        assert result is None
        mock_log.assert_called_once_with("[INVALID_PARAMETERS] Test error", "warning")

    def test_handle_strategy_error_with_reraise(self):
        """Test handle_strategy_error with reraise."""
        mock_log = Mock()

        error = StrategyError("Test error")

        with pytest.raises(StrategyError):
            handle_strategy_error(error, "SMA", mock_log, reraise=True)

    def test_handle_strategy_error_without_log_function(self):
        """Test handle_strategy_error without log function."""
        error = StrategyError("Test error", severity=ErrorSeverity.WARNING)

        result = handle_strategy_error(error, "SMA")

        assert result is not None
        assert result["message"] == "Test error"


class TestValidationFunctions:
    """Test cases for validation functions."""

    def test_validate_data_sufficiency_success(self):
        """Test successful data validation."""
        data = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "Close": [100.0, 101.0, 102.0],
                "Volume": [1000, 1100, 1200],
            },
        )

        result = validate_data_sufficiency(
            data,
            min_rows=2,
            strategy_type="SMA",
            required_columns=["Date", "Close"],
        )

        assert result is True

    def test_validate_data_sufficiency_insufficient_rows(self):
        """Test data validation with insufficient rows."""
        data = pl.DataFrame({"Date": ["2023-01-01"], "Close": [100.0]})

        result = validate_data_sufficiency(data, min_rows=5, strategy_type="SMA")

        assert result is False

    def test_validate_data_sufficiency_missing_columns(self):
        """Test data validation with missing columns."""
        data = pl.DataFrame(
            {"Date": ["2023-01-01", "2023-01-02"], "Close": [100.0, 101.0]},
        )

        result = validate_data_sufficiency(
            data,
            min_rows=2,
            strategy_type="SMA",
            required_columns=["Date", "Close", "Volume"],
        )

        assert result is False

    def test_validate_data_sufficiency_with_error_handler(self):
        """Test data validation with error handler."""
        data = pl.DataFrame({"Close": [100.0]})
        handler = StandardErrorHandler("SMA", fail_fast=False)

        result = validate_data_sufficiency(
            data,
            min_rows=5,
            strategy_type="SMA",
            error_handler=handler,
        )

        assert result is False
        assert handler.error_counts[ErrorSeverity.WARNING] == 1

    def test_validate_parameters_success(self):
        """Test successful parameter validation."""
        parameters = {"fast_period": 10, "slow_period": 20, "signal_period": 9}

        result = validate_parameters(parameters, ["fast_period", "slow_period"], "MACD")

        assert result is True

    def test_validate_parameters_missing_required(self):
        """Test parameter validation with missing required parameters."""
        parameters = {"fast_period": 10}

        result = validate_parameters(parameters, ["fast_period", "slow_period"], "MACD")

        assert result is False

    def test_validate_parameters_none_values(self):
        """Test parameter validation with None values."""
        parameters = {"fast_period": 10, "slow_period": None}

        result = validate_parameters(parameters, ["fast_period", "slow_period"], "MACD")

        assert result is False

    def test_validate_parameters_with_error_handler(self):
        """Test parameter validation with error handler."""
        parameters = {"fast_period": 10}
        handler = StandardErrorHandler("MACD", fail_fast=False)

        result = validate_parameters(
            parameters,
            ["fast_period", "slow_period"],
            "MACD",
            handler,
        )

        assert result is False
        assert handler.error_counts[ErrorSeverity.ERROR] == 1


if __name__ == "__main__":
    pytest.main([__file__])
