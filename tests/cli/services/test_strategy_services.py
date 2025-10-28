"""
Comprehensive tests for CLI Strategy Services.

This test suite covers MAStrategyService and MACDStrategyService with focus on:
- Configuration conversion from CLI to legacy format
- Strategy type validation and execution paths
- Error handling and edge cases
- Proper isolation through mocking
"""

from unittest.mock import Mock, patch

import pytest

from app.cli.models.strategy import (
    StrategyConfig,
    StrategyMinimums,
    StrategyType,
    SyntheticTickerConfig,
)
from app.cli.services.strategy_services import MACDStrategyService, MAStrategyService


class TestMAStrategyService:
    """Test cases for MAStrategyService."""

    @pytest.fixture
    def ma_service(self):
        """Create MAStrategyService instance."""
        return MAStrategyService()

    @pytest.fixture
    def base_strategy_config(self):
        """Create base strategy configuration."""
        return StrategyConfig(
            ticker=["AAPL"],
            strategy_types=[StrategyType.SMA],
            use_years=False,
            years=15,
            multi_ticker=False,
            use_scanner=False,
            scanner_list="",
            use_gbm=False,
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )

    def test_get_supported_strategy_types(self, ma_service):
        """Test that MA service returns supported strategy types."""
        supported = ma_service.get_supported_strategy_types()
        assert supported == ["SMA", "EMA"]

    def test_convert_config_to_legacy_sma_single_ticker(
        self,
        ma_service,
        base_strategy_config,
    ):
        """Test config conversion for SMA with single ticker."""
        config = base_strategy_config
        config.strategy_types = [StrategyType.SMA]
        config.ticker = ["AAPL"]

        legacy_config = ma_service.convert_config_to_legacy(config)

        assert legacy_config["TICKER"] == ["AAPL"]
        assert legacy_config["STRATEGY_TYPES"] == ["SMA"]
        assert legacy_config["USE_YEARS"] is False
        assert legacy_config["YEARS"] == 15
        assert legacy_config["MULTI_TICKER"] is False
        assert legacy_config["USE_SCANNER"] is False
        assert legacy_config["USE_GBM"] is False
        assert "MINIMUMS" in legacy_config
        assert legacy_config["USE_CURRENT"] is False
        assert legacy_config["SORT_BY"] == "Score"
        assert legacy_config["SORT_ASC"] is False

    def test_convert_config_to_legacy_ema_multiple_tickers(
        self,
        ma_service,
        base_strategy_config,
    ):
        """Test config conversion for EMA with multiple tickers."""
        config = base_strategy_config
        config.strategy_types = [StrategyType.EMA]
        config.ticker = ["AAPL", "MSFT", "GOOGL"]
        config.multi_ticker = True

        legacy_config = ma_service.convert_config_to_legacy(config)

        assert legacy_config["TICKER"] == ["AAPL", "MSFT", "GOOGL"]
        assert legacy_config["STRATEGY_TYPES"] == ["EMA"]
        assert legacy_config["MULTI_TICKER"] is True

    def test_convert_config_to_legacy_mixed_strategies(
        self,
        ma_service,
        base_strategy_config,
    ):
        """Test config conversion with mixed SMA/EMA strategies."""
        config = base_strategy_config
        config.strategy_types = [StrategyType.SMA, StrategyType.EMA]

        legacy_config = ma_service.convert_config_to_legacy(config)

        assert legacy_config["STRATEGY_TYPES"] == ["SMA", "EMA"]

    def test_convert_config_to_legacy_with_minimums(
        self,
        ma_service,
        base_strategy_config,
    ):
        """Test config conversion with minimum criteria."""
        config = base_strategy_config
        config.minimums.win_rate = 0.6
        config.minimums.trades = 50
        config.minimums.expectancy_per_trade = 0.02
        config.minimums.profit_factor = 1.5
        config.minimums.sortino_ratio = 1.2
        config.minimums.beats_bnh = 0.1

        legacy_config = ma_service.convert_config_to_legacy(config)

        assert legacy_config["MINIMUMS"]["WIN_RATE"] == 0.6
        assert legacy_config["MINIMUMS"]["TRADES"] == 50
        assert legacy_config["MINIMUMS"]["EXPECTANCY_PER_TRADE"] == 0.02
        assert legacy_config["MINIMUMS"]["PROFIT_FACTOR"] == 1.5
        assert legacy_config["MINIMUMS"]["SORTINO_RATIO"] == 1.2
        assert legacy_config["MINIMUMS"]["BEATS_BNH"] == 0.1

    def test_convert_config_to_legacy_with_synthetic(
        self,
        ma_service,
        base_strategy_config,
    ):
        """Test config conversion with synthetic ticker configuration."""
        config = base_strategy_config
        config.synthetic.use_synthetic = True
        config.synthetic.ticker_1 = "STRK"
        config.synthetic.ticker_2 = "MSTR"

        legacy_config = ma_service.convert_config_to_legacy(config)

        assert legacy_config["USE_SYNTHETIC"] is True
        assert legacy_config["TICKER_1"] == "STRK"
        assert legacy_config["TICKER_2"] == "MSTR"

    def test_convert_config_to_legacy_with_parameter_ranges(
        self,
        ma_service,
        base_strategy_config,
    ):
        """Test config conversion with parameter ranges for sweeps."""
        config = base_strategy_config
        config.fast_period_range = (5, 50)
        config.slow_period_range = (20, 200)
        config.fast_period = 12
        config.slow_period = 26

        legacy_config = ma_service.convert_config_to_legacy(config)

        assert legacy_config["FAST_PERIOD_RANGE"] == (5, 50)
        assert legacy_config["SLOW_PERIOD_RANGE"] == (20, 200)
        assert legacy_config["FAST_PERIOD"] == 12
        assert legacy_config["SLOW_PERIOD"] == 26

    def test_convert_config_to_legacy_with_filter_settings(
        self,
        ma_service,
        base_strategy_config,
    ):
        """Test config conversion with filter settings."""
        config = base_strategy_config
        config.use_current = True

        legacy_config = ma_service.convert_config_to_legacy(config)

        assert legacy_config["USE_CURRENT"] is True

    @patch("app.cli.services.strategy_services.importlib")
    def test_execute_strategy_success(
        self,
        mock_importlib,
        ma_service,
        base_strategy_config,
    ):
        """Test successful strategy execution."""
        # Mock the MA Cross module
        mock_module = Mock()
        mock_run = Mock(return_value=True)
        mock_module.run = mock_run
        mock_importlib.import_module.return_value = mock_module

        config = base_strategy_config

        result = ma_service.execute_strategy(config)

        assert result is True
        mock_importlib.import_module.assert_called_once_with(
            "app.strategies.ma_cross.1_get_portfolios",
        )
        mock_run.assert_called_once()

    @patch("app.cli.services.strategy_services.importlib")
    @patch("app.cli.services.strategy_services.rprint")
    def test_execute_strategy_failure(
        self,
        mock_rprint,
        mock_importlib,
        ma_service,
        base_strategy_config,
    ):
        """Test strategy execution failure handling."""
        # Mock import failure
        mock_importlib.import_module.side_effect = ImportError("Module not found")

        config = base_strategy_config

        result = ma_service.execute_strategy(config)

        assert result is False
        mock_rprint.assert_called_once()
        assert "Error executing MA Cross strategy" in str(mock_rprint.call_args)

    @patch("app.cli.services.strategy_services.importlib")
    def test_execute_strategy_with_string_ticker(
        self,
        mock_importlib,
        ma_service,
        base_strategy_config,
    ):
        """Test execution with string ticker (backwards compatibility)."""
        mock_module = Mock()
        mock_run = Mock(return_value=True)
        mock_module.run = mock_run
        mock_importlib.import_module.return_value = mock_module

        config = base_strategy_config
        config.ticker = "AAPL"  # String instead of list

        result = ma_service.execute_strategy(config)

        assert result is True
        # Verify the legacy config conversion handled string ticker correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args["TICKER"] == ["AAPL"]  # Should be converted to list


class TestMACDStrategyService:
    """Test cases for MACDStrategyService."""

    @pytest.fixture
    def macd_service(self):
        """Create MACDStrategyService instance."""
        return MACDStrategyService()

    @pytest.fixture
    def macd_strategy_config(self):
        """Create MACD strategy configuration."""
        config = StrategyConfig(
            ticker=["AAPL"],
            strategy_types=[StrategyType.MACD],
            use_years=False,
            years=15,
            multi_ticker=False,
            use_scanner=False,
            scanner_list="",
            use_gbm=False,
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )
        # Add MACD-specific parameters
        config.short_window_start = 8
        config.short_window_end = 16
        config.long_window_start = 20
        config.long_window_end = 30
        config.signal_window_start = 5
        config.signal_window_end = 15
        config.step = 2
        config.direction = "Long"
        config.use_current = False
        config.use_hourly = False
        config.refresh = True
        return config

    def test_get_supported_strategy_types(self, macd_service):
        """Test that MACD service returns supported strategy types."""
        supported = macd_service.get_supported_strategy_types()
        assert supported == ["MACD"]

    def test_convert_config_to_legacy_macd_complete(
        self,
        macd_service,
        macd_strategy_config,
    ):
        """Test config conversion for MACD with complete parameters."""
        config = macd_strategy_config

        legacy_config = macd_service.convert_config_to_legacy(config)

        assert legacy_config["TICKER"] == ["AAPL"]
        assert legacy_config["STRATEGY_TYPE"] == "MACD"
        assert legacy_config["STRATEGY_TYPES"] == ["MACD"]
        assert legacy_config["SHORT_WINDOW_START"] == 8
        assert legacy_config["SHORT_WINDOW_END"] == 16
        assert legacy_config["LONG_WINDOW_START"] == 20
        assert legacy_config["LONG_WINDOW_END"] == 30
        assert legacy_config["SIGNAL_WINDOW_START"] == 5
        assert legacy_config["SIGNAL_WINDOW_END"] == 15
        assert legacy_config["SIGNAL_PERIOD"] == 5  # Fallback value
        assert legacy_config["STEP"] == 2
        assert legacy_config["DIRECTION"] == "Long"
        assert legacy_config["USE_CURRENT"] is False
        assert legacy_config["USE_HOURLY"] is False
        assert legacy_config["USE_YEARS"] is False
        assert legacy_config["YEARS"] == 15
        assert legacy_config["REFRESH"] is True
        assert legacy_config["MULTI_TICKER"] is False
        assert legacy_config["SORT_BY"] == "Score"
        assert legacy_config["SORT_ASC"] is False

    def test_convert_config_to_legacy_missing_parameters(self, macd_service):
        """Test config conversion fails with missing MACD parameters."""
        config = StrategyConfig(
            ticker=["AAPL"],
            strategy_types=[StrategyType.MACD],
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )
        # Missing MACD-specific parameters

        with pytest.raises(ValueError) as exc_info:
            macd_service.convert_config_to_legacy(config)

        assert "Incomplete MACD configuration" in str(exc_info.value)

    def test_convert_config_to_legacy_with_minimums(
        self,
        macd_service,
        macd_strategy_config,
    ):
        """Test MACD config conversion with minimum criteria."""
        config = macd_strategy_config
        config.minimums.win_rate = 0.55
        config.minimums.trades = 30
        config.minimums.profit_factor = 1.3

        legacy_config = macd_service.convert_config_to_legacy(config)

        assert legacy_config["MINIMUMS"]["WIN_RATE"] == 0.55
        assert legacy_config["MINIMUMS"]["TRADES"] == 30
        assert legacy_config["MINIMUMS"]["PROFIT_FACTOR"] == 1.3

    def test_convert_config_to_legacy_multiple_tickers(
        self,
        macd_service,
        macd_strategy_config,
    ):
        """Test MACD config conversion with multiple tickers."""
        config = macd_strategy_config
        config.ticker = ["AAPL", "MSFT", "GOOGL"]
        config.multi_ticker = True

        legacy_config = macd_service.convert_config_to_legacy(config)

        assert legacy_config["TICKER"] == ["AAPL", "MSFT", "GOOGL"]
        assert legacy_config["MULTI_TICKER"] is True

    @patch("app.cli.services.strategy_services.importlib")
    def test_execute_strategy_success(
        self,
        mock_importlib,
        macd_service,
        macd_strategy_config,
    ):
        """Test successful MACD strategy execution."""
        # Mock the MACD module
        mock_module = Mock()
        mock_run = Mock(return_value=True)
        mock_module.run = mock_run
        mock_importlib.import_module.return_value = mock_module

        config = macd_strategy_config

        result = macd_service.execute_strategy(config)

        assert result is True
        mock_importlib.import_module.assert_called_once_with(
            "app.strategies.macd.1_get_portfolios",
        )
        mock_run.assert_called_once()

    @patch("app.cli.services.strategy_services.importlib")
    @patch("app.cli.services.strategy_services.rprint")
    def test_execute_strategy_import_failure(
        self,
        mock_rprint,
        mock_importlib,
        macd_service,
        macd_strategy_config,
    ):
        """Test MACD strategy execution with import failure."""
        mock_importlib.import_module.side_effect = ImportError("MACD module not found")

        config = macd_strategy_config

        result = macd_service.execute_strategy(config)

        assert result is False
        mock_rprint.assert_called_once()
        assert "Error executing MACD strategy" in str(mock_rprint.call_args)

    @patch("app.cli.services.strategy_services.importlib")
    @patch("app.cli.services.strategy_services.rprint")
    def test_execute_strategy_runtime_failure(
        self,
        mock_rprint,
        mock_importlib,
        macd_service,
        macd_strategy_config,
    ):
        """Test MACD strategy execution with runtime failure."""
        mock_module = Mock()
        mock_run = Mock(side_effect=RuntimeError("Strategy execution failed"))
        mock_module.run = mock_run
        mock_importlib.import_module.return_value = mock_module

        config = macd_strategy_config

        result = macd_service.execute_strategy(config)

        assert result is False
        mock_rprint.assert_called_once()
        assert "Error executing MACD strategy" in str(mock_rprint.call_args)

    def test_convert_config_short_direction(self, macd_service, macd_strategy_config):
        """Test MACD config conversion with Short direction."""
        config = macd_strategy_config
        config.direction = "Short"

        legacy_config = macd_service.convert_config_to_legacy(config)

        assert legacy_config["DIRECTION"] == "Short"

    def test_convert_config_with_custom_step(self, macd_service, macd_strategy_config):
        """Test MACD config conversion with custom step size."""
        config = macd_strategy_config
        config.step = 5

        legacy_config = macd_service.convert_config_to_legacy(config)

        assert legacy_config["STEP"] == 5

    def test_convert_config_with_hourly_data(self, macd_service, macd_strategy_config):
        """Test MACD config conversion with hourly data enabled."""
        config = macd_strategy_config
        config.use_hourly = True
        config.use_years = True
        config.years = 5

        legacy_config = macd_service.convert_config_to_legacy(config)

        assert legacy_config["USE_HOURLY"] is True
        assert legacy_config["USE_YEARS"] is True
        assert legacy_config["YEARS"] == 5


class TestStrategyServiceIntegration:
    """Integration tests for strategy services."""

    def test_strategy_type_enum_handling(self):
        """Test that both services handle StrategyType enums correctly."""
        ma_service = MAStrategyService()
        macd_service = MACDStrategyService()

        # Test MA service with enum
        ma_config = StrategyConfig(
            ticker=["AAPL"],
            strategy_types=[StrategyType.SMA],  # Enum
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )
        ma_legacy = ma_service.convert_config_to_legacy(ma_config)
        assert ma_legacy["STRATEGY_TYPES"] == ["SMA"]

        # Test MACD service with enum
        macd_config = StrategyConfig(
            ticker=["AAPL"],
            strategy_types=[StrategyType.MACD],  # Enum
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )
        # Add required MACD parameters
        macd_config.short_window_start = 8
        macd_config.short_window_end = 16
        macd_config.long_window_start = 20
        macd_config.long_window_end = 30
        macd_config.signal_window_start = 5
        macd_config.signal_window_end = 15

        macd_legacy = macd_service.convert_config_to_legacy(macd_config)
        assert macd_legacy["STRATEGY_TYPES"] == ["MACD"]

    def test_backward_compatibility_ticker_formats(self):
        """Test backward compatibility with different ticker formats."""
        ma_service = MAStrategyService()

        # Test with string ticker
        config1 = StrategyConfig(
            ticker="AAPL",  # String
            strategy_types=[StrategyType.SMA],
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )
        legacy1 = ma_service.convert_config_to_legacy(config1)
        assert legacy1["TICKER"] == ["AAPL"]

        # Test with list ticker
        config2 = StrategyConfig(
            ticker=["AAPL", "MSFT"],  # List
            strategy_types=[StrategyType.SMA],
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )
        legacy2 = ma_service.convert_config_to_legacy(config2)
        assert legacy2["TICKER"] == ["AAPL", "MSFT"]

    def test_config_consistency_across_services(self):
        """Test that common configuration fields are handled consistently."""
        ma_service = MAStrategyService()
        macd_service = MACDStrategyService()

        base_config_fields = {
            "ticker": ["AAPL"],
            "use_years": True,
            "years": 10,
            "multi_ticker": False,
            "use_scanner": False,
            "use_gbm": False,
        }

        # MA config
        ma_config = StrategyConfig(
            strategy_types=[StrategyType.SMA],
            minimums=StrategyMinimums(win_rate=0.6, trades=25),
            synthetic=SyntheticTickerConfig(),
            use_current=True,
            **base_config_fields,
        )

        # MACD config with required parameters
        macd_config = StrategyConfig(
            strategy_types=[StrategyType.MACD],
            minimums=StrategyMinimums(win_rate=0.6, trades=25),
            synthetic=SyntheticTickerConfig(),
            use_current=True,
            **base_config_fields,
        )
        macd_config.short_window_start = 8
        macd_config.short_window_end = 16
        macd_config.long_window_start = 20
        macd_config.long_window_end = 30
        macd_config.signal_window_start = 5
        macd_config.signal_window_end = 15

        ma_legacy = ma_service.convert_config_to_legacy(ma_config)
        macd_legacy = macd_service.convert_config_to_legacy(macd_config)

        # Test common fields are consistent (only fields that exist in both services)
        common_fields = ["TICKER", "USE_YEARS", "YEARS", "MULTI_TICKER", "USE_CURRENT"]
        for field in common_fields:
            if field in ma_legacy and field in macd_legacy:
                assert (
                    ma_legacy[field] == macd_legacy[field]
                ), f"Field {field} inconsistent between services"

        # Test minimums are consistent
        assert ma_legacy["MINIMUMS"]["WIN_RATE"] == macd_legacy["MINIMUMS"]["WIN_RATE"]
        assert ma_legacy["MINIMUMS"]["TRADES"] == macd_legacy["MINIMUMS"]["TRADES"]
