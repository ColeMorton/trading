"""
Test Parameter Testing Configuration

Tests for the unified configuration management system introduced in Phase 2.
"""

import pytest

from app.strategies.ma_cross.config.parameter_testing import (
    ExecutionOptions,
    ExportOptions,
    FilterCriteria,
    ParameterTestingConfig,
    ValidationResult,
)


class TestParameterTestingConfig:
    """Test suite for ParameterTestingConfig."""

    @pytest.fixture
    def basic_config_dict(self):
        """Basic configuration dictionary for testing."""
        return {
            "TICKER": ["AAPL", "GOOGL"],
            "WINDOWS": 20,
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "DIRECTION": "Long",
            "BASE_DIR": "/Users/colemorton/Projects/trading",
        }

    @pytest.fixture
    def config_with_filters(self):
        """Configuration with filtering criteria."""
        return {
            "TICKER": ["AAPL", "GOOGL", "MSFT"],
            "WINDOWS": 30,
            "STRATEGY_TYPES": ["SMA"],
            "MINIMUMS": {
                "WIN_RATE": 0.6,
                "TRADES": 10,
                "PROFIT_FACTOR": 1.5,
            },
            "BASE_DIR": "/Users/colemorton/Projects/trading",
        }

    def test_from_dict_basic(self, basic_config_dict):
        """Test creating config from basic dictionary."""
        config = ParameterTestingConfig.from_dict(basic_config_dict)

        assert config.tickers == ["AAPL", "GOOGL"]
        assert config.windows == 20
        assert config.strategy_types == ["SMA", "EMA"]
        assert config.direction == "Long"
        assert config.base_directory == "/Users/colemorton/Projects/trading"

    def test_from_dict_with_filters(self, config_with_filters):
        """Test creating config with filter criteria."""
        config = ParameterTestingConfig.from_dict(config_with_filters)

        assert config.filters.min_win_rate == 0.6
        assert config.filters.min_trades == 10
        assert config.filters.min_profit_factor == 1.5

    def test_to_dict_roundtrip(self, basic_config_dict):
        """Test that from_dict -> to_dict is consistent."""
        config = ParameterTestingConfig.from_dict(basic_config_dict)
        result_dict = config.to_dict()

        # Key fields should match
        assert result_dict["TICKER"] == basic_config_dict["TICKER"]
        assert result_dict["WINDOWS"] == basic_config_dict["WINDOWS"]
        assert result_dict["STRATEGY_TYPES"] == basic_config_dict["STRATEGY_TYPES"]

    def test_validate_valid_config(self, basic_config_dict):
        """Test validation of valid configuration."""
        config = ParameterTestingConfig.from_dict(basic_config_dict)
        result = config.validate()

        assert result.is_valid is True
        assert len(result.messages) == 0 or all(
            msg["severity"] in ["warning", "info"] for msg in result.messages
        )

    def test_validate_empty_tickers(self):
        """Test validation with empty tickers."""
        config = ParameterTestingConfig(
            tickers=[],
            windows=20,
            strategy_types=["SMA"],
        )
        result = config.validate()

        assert result.is_valid is False
        error_messages = [
            msg["message"] for msg in result.messages if msg["severity"] == "error"
        ]
        assert any("ticker" in msg.lower() for msg in error_messages)

    def test_validate_invalid_windows(self):
        """Test validation with invalid window size."""
        config = ParameterTestingConfig(
            tickers=["AAPL"],
            windows=1,  # Too small
            strategy_types=["SMA"],
        )
        result = config.validate()

        assert result.is_valid is False
        error_messages = [
            msg["message"] for msg in result.messages if msg["severity"] == "error"
        ]
        assert any("window" in msg.lower() for msg in error_messages)

    def test_validate_invalid_strategy_types(self):
        """Test validation with invalid strategy types."""
        config = ParameterTestingConfig(
            tickers=["AAPL"],
            windows=20,
            strategy_types=["INVALID"],
        )
        result = config.validate()

        assert result.is_valid is False
        error_messages = [
            msg["message"] for msg in result.messages if msg["severity"] == "error"
        ]
        assert any("strategy" in msg.lower() for msg in error_messages)

    def test_validate_warnings_for_large_datasets(self):
        """Test that warnings are generated for large datasets."""
        config = ParameterTestingConfig(
            tickers=[f"TICK{i:02d}" for i in range(15)],  # Large ticker set
            windows=300,  # Large window
            strategy_types=["SMA", "EMA", "WMA"],  # Multiple strategies
        )
        result = config.validate()

        info_messages = [
            msg["message"] for msg in result.messages if msg["severity"] == "info"
        ]
        warning_messages = [
            msg["message"] for msg in result.messages if msg["severity"] == "warning"
        ]

        assert len(info_messages) > 0 or len(warning_messages) > 0

    def test_get_execution_summary(self, basic_config_dict):
        """Test execution summary generation."""
        config = ParameterTestingConfig.from_dict(basic_config_dict)
        summary = config.get_execution_summary()

        assert summary["ticker_count"] == 2
        assert summary["strategy_count"] == 2
        assert summary["window_size"] == 20
        assert summary["estimated_combinations"] == 4  # 2 tickers * 2 strategies
        assert "export_formats" in summary


class TestFilterCriteria:
    """Test suite for FilterCriteria."""

    def test_validate_valid_criteria(self):
        """Test validation of valid filter criteria."""
        criteria = FilterCriteria(
            min_win_rate=0.6,
            min_trades=10,
            min_profit_factor=1.5,
        )
        result = criteria.validate()

        assert result.is_valid is True

    def test_validate_invalid_win_rate(self):
        """Test validation with invalid win rate."""
        criteria = FilterCriteria(min_win_rate=1.5)  # > 1
        result = criteria.validate()

        assert result.is_valid is False
        assert any("win rate" in msg["message"].lower() for msg in result.messages)

    def test_validate_negative_trades(self):
        """Test validation with negative trades."""
        criteria = FilterCriteria(min_trades=-5)
        result = criteria.validate()

        assert result.is_valid is False
        assert any("trades" in msg["message"].lower() for msg in result.messages)

    def test_validate_extreme_drawdown(self):
        """Test validation with extreme max drawdown."""
        criteria = FilterCriteria(max_drawdown=-150)  # > 100%
        result = criteria.validate()

        assert result.is_valid is False
        assert any("drawdown" in msg["message"].lower() for msg in result.messages)


class TestExportOptions:
    """Test suite for ExportOptions."""

    def test_validate_valid_options(self):
        """Test validation of valid export options."""
        options = ExportOptions(
            export_csv=True,
            max_results=100,
            filename_prefix="test_analysis",
        )
        result = options.validate()

        assert result.is_valid is True

    def test_validate_invalid_max_results(self):
        """Test validation with invalid max results."""
        options = ExportOptions(max_results=0)
        result = options.validate()

        assert result.is_valid is False
        assert any("max results" in msg["message"].lower() for msg in result.messages)

    def test_validate_empty_filename_prefix(self):
        """Test validation with empty filename prefix."""
        options = ExportOptions(filename_prefix="")
        result = options.validate()

        assert result.is_valid is False
        assert any("filename" in msg["message"].lower() for msg in result.messages)

    def test_validate_large_result_set_warning(self):
        """Test warning for large result sets."""
        options = ExportOptions(max_results=50000)
        result = options.validate()

        warning_messages = [
            msg["message"] for msg in result.messages if msg["severity"] == "warning"
        ]
        assert any("performance" in msg.lower() for msg in warning_messages)


class TestExecutionOptions:
    """Test suite for ExecutionOptions."""

    def test_validate_valid_options(self):
        """Test validation of valid execution options."""
        options = ExecutionOptions(
            max_workers=4,
            timeout_seconds=1800,
            cache_ttl_seconds=3600,
        )
        result = options.validate()

        assert result.is_valid is True

    def test_validate_invalid_max_workers(self):
        """Test validation with invalid max workers."""
        options = ExecutionOptions(max_workers=0)
        result = options.validate()

        assert result.is_valid is False
        assert any("workers" in msg["message"].lower() for msg in result.messages)

    def test_validate_invalid_timeout(self):
        """Test validation with invalid timeout."""
        options = ExecutionOptions(timeout_seconds=-100)
        result = options.validate()

        assert result.is_valid is False
        assert any("timeout" in msg["message"].lower() for msg in result.messages)

    def test_validate_high_worker_count_warning(self):
        """Test warning for high worker count."""
        options = ExecutionOptions(max_workers=32)
        result = options.validate()

        warning_messages = [
            msg["message"] for msg in result.messages if msg["severity"] == "warning"
        ]
        assert any("worker" in msg.lower() for msg in warning_messages)


class TestValidationResult:
    """Test suite for ValidationResult."""

    def test_add_error(self):
        """Test adding error messages."""
        result = ValidationResult(is_valid=True)
        result.add_error("Test error", "test_field")

        assert result.is_valid is False
        assert len(result.messages) == 1
        assert result.messages[0]["severity"] == "error"
        assert result.messages[0]["message"] == "Test error"
        assert result.messages[0]["field"] == "test_field"

    def test_add_warning(self):
        """Test adding warning messages."""
        result = ValidationResult(is_valid=True)
        result.add_warning("Test warning")

        assert result.is_valid is True  # Warnings don't invalidate
        assert len(result.messages) == 1
        assert result.messages[0]["severity"] == "warning"

    def test_add_info(self):
        """Test adding info messages."""
        result = ValidationResult(is_valid=True)
        result.add_info("Test info")

        assert result.is_valid is True
        assert len(result.messages) == 1
        assert result.messages[0]["severity"] == "info"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
