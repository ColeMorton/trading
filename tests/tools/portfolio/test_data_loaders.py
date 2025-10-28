"""Tests for portfolio data loading functions."""

from unittest.mock import MagicMock, patch

import pytest

from app.cli.models.portfolio import Direction, ReviewStrategyConfig, StrategyType
from app.tools.portfolio.data_loaders import load_strategies_from_raw_csv


class TestLoadStrategiesFromRawCsv:
    """Test suite for load_strategies_from_raw_csv function."""

    @patch("app.tools.portfolio.data_loaders.Path")
    @patch("app.tools.portfolio.data_loaders.pl.read_csv")
    @patch("app.tools.portfolio.data_loaders.convert_csv_to_strategy_config")
    @patch("app.tools.portfolio.data_loaders.ConsoleLogger")
    def test_load_strategies_success(
        self, mock_console_logger, mock_convert, mock_read_csv, mock_path,
    ):
        """Test successful loading of strategies from CSV."""
        # Setup mocks
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_df = MagicMock()
        mock_read_csv.return_value = mock_df

        mock_convert.return_value = [
            {
                "TICKER": "AAPL",
                "STRATEGY_TYPE": "SMA",
                "DIRECTION": "long",
                "FAST_PERIOD": 20,
                "SLOW_PERIOD": 50,
                "SIGNAL_PERIOD": 9,
                "STOP_LOSS": None,
                "POSITION_SIZE": 1.0,
                "USE_HOURLY": False,
                "RSI_WINDOW": None,
                "RSI_THRESHOLD": None,
            },
        ]

        mock_console = MagicMock()
        mock_console_logger.return_value = mock_console

        # Execute
        result = load_strategies_from_raw_csv("test_portfolio")

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], ReviewStrategyConfig)
        assert result[0].ticker == "AAPL"
        assert result[0].strategy_type == StrategyType.SMA
        assert result[0].direction == Direction.LONG
        assert result[0].fast_period == 20
        assert result[0].slow_period == 50
        mock_console.success.assert_called_once()

    @patch("app.tools.portfolio.data_loaders.Path")
    def test_load_strategies_file_not_found(self, mock_path):
        """Test error handling when CSV file doesn't exist."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        with pytest.raises(
            ValueError, match="(does not exist|Failed to load strategies)",
        ):
            load_strategies_from_raw_csv("nonexistent")

    @patch("app.tools.portfolio.data_loaders.Path")
    @patch("app.tools.portfolio.data_loaders.pl.read_csv")
    @patch("app.tools.portfolio.data_loaders.convert_csv_to_strategy_config")
    @patch("app.tools.portfolio.data_loaders.ConsoleLogger")
    def test_load_strategies_with_custom_console(
        self, mock_console_logger_class, mock_convert, mock_read_csv, mock_path,
    ):
        """Test loading strategies with custom console logger."""
        # Setup mocks
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_df = MagicMock()
        mock_read_csv.return_value = mock_df

        mock_convert.return_value = [
            {
                "TICKER": "MSFT",
                "STRATEGY_TYPE": "EMA",
                "DIRECTION": "short",
                "FAST_PERIOD": 10,
                "SLOW_PERIOD": 30,
                "SIGNAL_PERIOD": 9,
                "STOP_LOSS": 0.02,
                "POSITION_SIZE": 0.5,
                "USE_HOURLY": True,
                "RSI_WINDOW": 14,
                "RSI_THRESHOLD": 30,
            },
        ]

        custom_console = MagicMock()

        # Execute
        result = load_strategies_from_raw_csv("test_portfolio", console=custom_console)

        # Verify
        assert len(result) == 1
        assert result[0].ticker == "MSFT"
        assert result[0].strategy_type == StrategyType.EMA
        assert result[0].direction == Direction.SHORT
        assert result[0].use_hourly is True
        custom_console.success.assert_called_once()
        # Should not create a new console logger
        mock_console_logger_class.assert_not_called()

    @patch("app.tools.portfolio.data_loaders.Path")
    @patch("app.tools.portfolio.data_loaders.pl.read_csv")
    @patch("app.tools.portfolio.data_loaders.convert_csv_to_strategy_config")
    @patch("app.tools.portfolio.data_loaders.ConsoleLogger")
    def test_load_strategies_unknown_strategy_type(
        self, mock_console_logger, mock_convert, mock_read_csv, mock_path,
    ):
        """Test handling of unknown strategy type (should default to SMA)."""
        # Setup mocks
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_df = MagicMock()
        mock_read_csv.return_value = mock_df

        mock_convert.return_value = [
            {
                "TICKER": "TSLA",
                "STRATEGY_TYPE": "UNKNOWN_TYPE",
                "DIRECTION": "long",
                "FAST_PERIOD": 15,
                "SLOW_PERIOD": 45,
                "SIGNAL_PERIOD": 9,
            },
        ]

        mock_console = MagicMock()
        mock_console_logger.return_value = mock_console

        # Execute
        result = load_strategies_from_raw_csv("test_portfolio")

        # Verify - should default to SMA
        assert len(result) == 1
        assert result[0].strategy_type == StrategyType.SMA

    @patch("app.tools.portfolio.data_loaders.Path")
    @patch("app.tools.portfolio.data_loaders.pl.read_csv")
    @patch("app.tools.portfolio.data_loaders.convert_csv_to_strategy_config")
    @patch("app.tools.portfolio.data_loaders.ConsoleLogger")
    def test_load_strategies_unknown_direction(
        self, mock_console_logger, mock_convert, mock_read_csv, mock_path,
    ):
        """Test handling of unknown direction (should default to LONG)."""
        # Setup mocks
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_df = MagicMock()
        mock_read_csv.return_value = mock_df

        mock_convert.return_value = [
            {
                "TICKER": "NVDA",
                "STRATEGY_TYPE": "MACD",
                "DIRECTION": "invalid_direction",
                "FAST_PERIOD": 12,
                "SLOW_PERIOD": 26,
                "SIGNAL_PERIOD": 9,
            },
        ]

        mock_console = MagicMock()
        mock_console_logger.return_value = mock_console

        # Execute
        result = load_strategies_from_raw_csv("test_portfolio")

        # Verify - should default to LONG
        assert len(result) == 1
        assert result[0].direction == Direction.LONG

    @patch("app.tools.portfolio.data_loaders.Path")
    @patch("app.tools.portfolio.data_loaders.pl.read_csv")
    def test_load_strategies_read_csv_error(self, mock_read_csv, mock_path):
        """Test error handling when CSV reading fails."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_read_csv.side_effect = Exception("CSV parsing error")

        with pytest.raises(ValueError, match="Failed to load strategies"):
            load_strategies_from_raw_csv("test_portfolio")

    @patch("app.tools.portfolio.data_loaders.Path")
    @patch("app.tools.portfolio.data_loaders.pl.read_csv")
    @patch("app.tools.portfolio.data_loaders.convert_csv_to_strategy_config")
    @patch("app.tools.portfolio.data_loaders.ConsoleLogger")
    def test_load_strategies_multiple_strategies(
        self, mock_console_logger, mock_convert, mock_read_csv, mock_path,
    ):
        """Test loading multiple strategies from CSV."""
        # Setup mocks
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_df = MagicMock()
        mock_read_csv.return_value = mock_df

        mock_convert.return_value = [
            {
                "TICKER": "BTC-USD",
                "STRATEGY_TYPE": "SMA",
                "DIRECTION": "long",
                "FAST_PERIOD": 50,
                "SLOW_PERIOD": 200,
                "SIGNAL_PERIOD": 9,
            },
            {
                "TICKER": "ETH-USD",
                "STRATEGY_TYPE": "EMA",
                "DIRECTION": "short",
                "FAST_PERIOD": 20,
                "SLOW_PERIOD": 100,
                "SIGNAL_PERIOD": 9,
            },
            {
                "TICKER": "SPY",
                "STRATEGY_TYPE": "MACD",
                "DIRECTION": "long",
                "FAST_PERIOD": 12,
                "SLOW_PERIOD": 26,
                "SIGNAL_PERIOD": 9,
            },
        ]

        mock_console = MagicMock()
        mock_console_logger.return_value = mock_console

        # Execute
        result = load_strategies_from_raw_csv("multi_strategy")

        # Verify
        assert len(result) == 3
        assert result[0].ticker == "BTC-USD"
        assert result[1].ticker == "ETH-USD"
        assert result[2].ticker == "SPY"
        assert result[0].strategy_type == StrategyType.SMA
        assert result[1].strategy_type == StrategyType.EMA
        assert result[2].strategy_type == StrategyType.MACD
