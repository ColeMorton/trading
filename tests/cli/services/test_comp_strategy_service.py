"""
Unit tests for COMPStrategyService.

Tests the COMP strategy service including:
- Configuration conversion
- Strategy execution
- Error handling
- File path resolution
"""

from unittest.mock import Mock, patch

import pytest

from app.cli.models.strategy import (
    StrategyConfig,
    StrategyMinimums,
    SyntheticTickerConfig,
)
from app.cli.services.strategy_services import COMPStrategyService


class TestCOMPStrategyService:
    """Test cases for COMPStrategyService."""

    @pytest.fixture
    def comp_service(self):
        """Create COMPStrategyService instance."""
        return COMPStrategyService()

    @pytest.fixture
    def base_comp_config(self):
        """Create base COMP strategy configuration."""
        return StrategyConfig(
            ticker=["BTC-USD"],
            strategy_types=[],  # Not used for COMP
            use_years=False,
            years=15,
            multi_ticker=False,
            use_scanner=False,
            scanner_list="",
            use_gbm=False,
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )

    def test_get_supported_strategy_types(self, comp_service):
        """Test that COMP service returns supported strategy types."""
        supported = comp_service.get_supported_strategy_types()
        assert supported == ["COMP"]

    def test_convert_config_to_legacy_basic(self, comp_service, base_comp_config):
        """Test basic config conversion for COMP strategy."""
        config = base_comp_config
        config.ticker = ["BTC-USD"]

        legacy_config = comp_service.convert_config_to_legacy(config)

        assert legacy_config["TICKER"] == ["BTC-USD"]
        assert legacy_config["STRATEGY_TYPES"] == ["COMP"]
        assert legacy_config["USE_YEARS"] is False
        assert legacy_config["YEARS"] == 15
        assert "BASE_DIR" in legacy_config

    def test_convert_config_to_legacy_with_years(self, comp_service, base_comp_config):
        """Test config conversion with year limit."""
        config = base_comp_config
        config.use_years = True
        config.years = 3

        legacy_config = comp_service.convert_config_to_legacy(config)

        assert legacy_config["USE_YEARS"] is True
        assert legacy_config["YEARS"] == 3

    def test_convert_config_to_legacy_with_timeframe(self, comp_service):
        """Test config conversion with different timeframes."""
        # Test 4-hour timeframe
        config_4h = StrategyConfig(
            ticker=["BTC-USD"],
            strategy_types=[],
            use_4hour=True,
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )

        legacy_config_4h = comp_service.convert_config_to_legacy(config_4h)
        assert legacy_config_4h.get("USE_4HOUR") is True

        # Test 2-day timeframe
        config_2d = StrategyConfig(
            ticker=["BTC-USD"],
            strategy_types=[],
            use_2day=True,
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )

        legacy_config_2d = comp_service.convert_config_to_legacy(config_2d)
        assert legacy_config_2d.get("USE_2DAY") is True

    def test_convert_config_to_legacy_multiple_tickers(
        self, comp_service, base_comp_config
    ):
        """Test config conversion with multiple tickers."""
        config = base_comp_config
        config.ticker = ["BTC-USD", "ETH-USD", "SOL-USD"]

        legacy_config = comp_service.convert_config_to_legacy(config)

        assert legacy_config["TICKER"] == ["BTC-USD", "ETH-USD", "SOL-USD"]

    @patch("app.cli.services.strategy_services.importlib")
    def test_execute_strategy_success(
        self, mock_importlib, comp_service, base_comp_config
    ):
        """Test successful strategy execution."""
        # Mock the COMP strategy module
        mock_module = Mock()
        mock_run = Mock(return_value=True)
        mock_module.run = mock_run
        mock_importlib.import_module.return_value = mock_module

        config = base_comp_config
        config.ticker = ["BTC-USD"]

        result = comp_service.execute_strategy(config)

        assert result is True
        mock_importlib.import_module.assert_called_once_with(
            "app.strategies.comp.strategy"
        )
        mock_run.assert_called_once()

        # Verify the legacy config was passed correctly
        call_args = mock_run.call_args[0][0]
        assert call_args["TICKER"] == ["BTC-USD"]
        assert call_args["STRATEGY_TYPES"] == ["COMP"]

    @patch("app.cli.services.strategy_services.importlib")
    @patch("app.cli.services.strategy_services.rprint")
    def test_execute_strategy_missing_csv(
        self, mock_rprint, mock_importlib, comp_service, base_comp_config
    ):
        """Test execution when component CSV file is missing."""
        # Mock the COMP strategy module to simulate missing CSV
        mock_module = Mock()
        mock_run = Mock(return_value=False)  # Returns False when CSV not found
        mock_module.run = mock_run
        mock_importlib.import_module.return_value = mock_module

        config = base_comp_config
        config.ticker = ["NONEXISTENT-TICKER"]

        result = comp_service.execute_strategy(config)

        # Execution should fail gracefully
        assert result is False

    @patch("app.cli.services.strategy_services.importlib")
    @patch("app.cli.services.strategy_services.rprint")
    def test_execute_strategy_import_error(
        self, mock_rprint, mock_importlib, comp_service, base_comp_config
    ):
        """Test strategy execution handles import failures gracefully."""
        # Mock import failure
        mock_importlib.import_module.side_effect = ImportError("Module not found")

        config = base_comp_config

        result = comp_service.execute_strategy(config)

        assert result is False
        # rprint is called twice: once for error message, once for traceback
        assert mock_rprint.call_count == 2
        # Check the first call contains the error message
        first_call = str(mock_rprint.call_args_list[0])
        assert "Error executing COMP strategy" in first_call


class TestCOMPConfigConversion:
    """Test COMP-specific configuration conversion logic."""

    def test_comp_strategies_csv_path_default(self):
        """Test default CSV path construction."""
        service = COMPStrategyService()
        config = StrategyConfig(
            ticker=["AAPL"],
            strategy_types=[],
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )

        legacy_config = service.convert_config_to_legacy(config)

        # Should have BASE_DIR but not COMP_STRATEGIES_CSV
        assert "BASE_DIR" in legacy_config
        # CSV path is determined dynamically by the strategy module

    def test_comp_strategies_csv_path_custom(self):
        """Test custom CSV path from config."""
        service = COMPStrategyService()
        config = StrategyConfig(
            ticker=["AAPL"],
            strategy_types=[],
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )
        # Add custom CSV path (if supported in future)
        # This is a placeholder for future functionality

        legacy_config = service.convert_config_to_legacy(config)

        assert "BASE_DIR" in legacy_config

    def test_comp_with_timeframes(self):
        """Test COMP config conversion with timeframe options."""
        service = COMPStrategyService()
        config = StrategyConfig(
            ticker=["BTC-USD"],
            strategy_types=[],
            use_4hour=True,
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )

        legacy_config = service.convert_config_to_legacy(config)

        assert legacy_config["USE_4HOUR"] is True
        # USE_HOURLY and USE_2DAY will be False or None based on StrategyConfig defaults
        assert legacy_config.get("USE_2DAY") in [False, None]


class TestCOMPStrategyIntegration:
    """Integration tests for COMP strategy service."""

    def test_comp_strategy_type_identifier(self):
        """Test that COMP is properly identified as a strategy type."""
        service = COMPStrategyService()
        supported = service.get_supported_strategy_types()

        assert "COMP" in supported
        assert len(supported) == 1

    def test_comp_config_has_required_fields(self):
        """Test that converted config has all required fields."""
        service = COMPStrategyService()
        config = StrategyConfig(
            ticker=["BTC-USD"],
            strategy_types=[],
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )

        legacy_config = service.convert_config_to_legacy(config)

        # Check for required fields
        required_fields = ["TICKER", "STRATEGY_TYPES", "BASE_DIR", "USE_YEARS", "YEARS"]
        for field in required_fields:
            assert field in legacy_config, f"Missing required field: {field}"

    @patch("app.cli.services.strategy_services.importlib")
    def test_comp_execution_with_external_log(self, mock_importlib):
        """Test COMP execution with external logging function."""
        service = COMPStrategyService()

        mock_module = Mock()
        mock_run = Mock(return_value=True)
        mock_module.run = mock_run
        mock_importlib.import_module.return_value = mock_module

        config = StrategyConfig(
            ticker=["BTC-USD"],
            strategy_types=[],
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )

        result = service.execute_strategy(config)

        assert result is True
        # The strategy module's run function is called
        mock_run.assert_called_once()
