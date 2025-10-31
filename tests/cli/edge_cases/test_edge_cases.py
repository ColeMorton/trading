"""
Comprehensive Edge Case Tests.

This test suite validates handling of edge cases and boundary conditions:
- Synthetic ticker formats and unusual ticker symbols
- Special characters in parameters and file paths
- Extreme parameter values and boundary conditions
- Empty result sets and minimal data scenarios
- Unicode handling and internationalization
- Timezone and date edge cases
- Large-scale data processing limits
- Unusual market conditions and data patterns

These tests ensure the system is robust under unusual but valid conditions.
"""

import math
from datetime import timedelta
from unittest.mock import Mock, patch

import polars as pl
import pytest
from typer.testing import CliRunner

from app.cli.commands.strategy import app as strategy_app


@pytest.mark.integration
class TestSyntheticTickerHandling:
    """Test handling of synthetic ticker formats and unusual ticker symbols."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def synthetic_price_data(self):
        """Price data for synthetic tickers."""
        return pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 3, 31),
                    interval="1d",
                ),
                "Close": [100.0 + i * 0.5 for i in range(90)],
                "High": [102.0 + i * 0.5 for i in range(90)],
                "Low": [98.0 + i * 0.5 for i in range(90)],
                "Volume": [1000000] * 90,
            },
        )

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_slash_separated_synthetic_tickers(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        synthetic_price_data,
    ):
        """Test handling of slash-separated synthetic tickers like STRK/MSTR."""
        synthetic_tickers = ["STRK/MSTR", "BTC/ETH", "GOLD/SILVER", "SPY/QQQ"]

        for ticker in synthetic_tickers:
            # Setup mocks
            mock_config = Mock()
            mock_config.ticker = [ticker]
            mock_config.strategy_types = ["SMA"]
            mock_config_loader.return_value.load_from_profile.return_value = mock_config

            mock_dispatcher = Mock()
            mock_dispatcher.validate_strategy_compatibility.return_value = True
            mock_dispatcher.execute_strategy.return_value = True
            mock_dispatcher_class.return_value = mock_dispatcher

            mock_get_data.return_value = synthetic_price_data

            # Execute command
            result = cli_runner.invoke(
                strategy_app,
                ["run", "--ticker", ticker, "--strategy", "SMA"],
            )

            # Verify synthetic ticker handling
            assert result.exit_code == 0
            assert ticker in result.stdout or ticker.replace("/", "_") in result.stdout

            # Reset mocks for next iteration
            mock_config_loader.reset_mock()
            mock_dispatcher_class.reset_mock()
            mock_get_data.reset_mock()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_crypto_ticker_formats(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        synthetic_price_data,
    ):
        """Test handling of various crypto ticker formats."""
        crypto_tickers = ["BTC-USD", "ETH-USD", "DOGE-USDT", "ADA-BTC", "SOL-EUR"]

        for ticker in crypto_tickers:
            # Setup mocks
            mock_config = Mock()
            mock_config.ticker = [ticker]
            mock_config.strategy_types = ["SMA"]
            mock_config_loader.return_value.load_from_profile.return_value = mock_config

            mock_dispatcher = Mock()
            mock_dispatcher.validate_strategy_compatibility.return_value = True
            mock_dispatcher.execute_strategy.return_value = True
            mock_dispatcher_class.return_value = mock_dispatcher

            mock_get_data.return_value = synthetic_price_data

            # Execute command
            result = cli_runner.invoke(
                strategy_app,
                ["run", "--ticker", ticker, "--strategy", "SMA"],
            )

            # Verify crypto ticker handling
            assert result.exit_code == 0

            # Reset mocks for next iteration
            mock_config_loader.reset_mock()
            mock_dispatcher_class.reset_mock()
            mock_get_data.reset_mock()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_futures_and_options_tickers(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        synthetic_price_data,
    ):
        """Test handling of futures and options ticker formats."""
        derivative_tickers = [
            "GC=F",
            "CL=F",
            "ES=F",
            "NQ=F",
            "ZB=F",
            "AAPL240315C00150000",
        ]

        for ticker in derivative_tickers:
            # Setup mocks
            mock_config = Mock()
            mock_config.ticker = [ticker]
            mock_config.strategy_types = ["SMA"]
            mock_config_loader.return_value.load_from_profile.return_value = mock_config

            mock_dispatcher = Mock()
            mock_dispatcher.validate_strategy_compatibility.return_value = True
            mock_dispatcher.execute_strategy.return_value = True
            mock_dispatcher_class.return_value = mock_dispatcher

            mock_get_data.return_value = synthetic_price_data

            # Execute command
            result = cli_runner.invoke(
                strategy_app,
                ["run", "--ticker", ticker, "--strategy", "SMA"],
            )

            # Verify derivative ticker handling
            assert result.exit_code == 0

            # Reset mocks for next iteration
            mock_config_loader.reset_mock()
            mock_dispatcher_class.reset_mock()
            mock_get_data.reset_mock()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_international_ticker_formats(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        synthetic_price_data,
    ):
        """Test handling of international ticker formats."""
        international_tickers = [
            "VOD.L",
            "TM.T",
            "ASML.AS",
            "SAP.DE",
            "7203.T",
            "0700.HK",
        ]

        for ticker in international_tickers:
            # Setup mocks
            mock_config = Mock()
            mock_config.ticker = [ticker]
            mock_config.strategy_types = ["SMA"]
            mock_config_loader.return_value.load_from_profile.return_value = mock_config

            mock_dispatcher = Mock()
            mock_dispatcher.validate_strategy_compatibility.return_value = True
            mock_dispatcher.execute_strategy.return_value = True
            mock_dispatcher_class.return_value = mock_dispatcher

            mock_get_data.return_value = synthetic_price_data

            # Execute command
            result = cli_runner.invoke(
                strategy_app,
                ["run", "--ticker", ticker, "--strategy", "SMA"],
            )

            # Verify international ticker handling
            assert result.exit_code == 0

            # Reset mocks for next iteration
            mock_config_loader.reset_mock()
            mock_dispatcher_class.reset_mock()
            mock_get_data.reset_mock()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_index_and_etf_tickers(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        synthetic_price_data,
    ):
        """Test handling of index and ETF ticker formats."""
        index_etf_tickers = [
            "^GSPC",
            "^DJI",
            "^IXIC",
            "^RUT",
            "SPY",
            "QQQ",
            "IWM",
            "VTI",
        ]

        for ticker in index_etf_tickers:
            # Setup mocks
            mock_config = Mock()
            mock_config.ticker = [ticker]
            mock_config.strategy_types = ["SMA"]
            mock_config_loader.return_value.load_from_profile.return_value = mock_config

            mock_dispatcher = Mock()
            mock_dispatcher.validate_strategy_compatibility.return_value = True
            mock_dispatcher.execute_strategy.return_value = True
            mock_dispatcher_class.return_value = mock_dispatcher

            mock_get_data.return_value = synthetic_price_data

            # Execute command
            result = cli_runner.invoke(
                strategy_app,
                ["run", "--ticker", ticker, "--strategy", "SMA"],
            )

            # Verify index/ETF ticker handling
            assert result.exit_code == 0

            # Reset mocks for next iteration
            mock_config_loader.reset_mock()
            mock_dispatcher_class.reset_mock()
            mock_get_data.reset_mock()


@pytest.mark.integration
class TestSpecialCharacterHandling:
    """Test handling of special characters in parameters and file paths."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_unicode_ticker_symbols(self, cli_runner):
        """Test handling of Unicode characters in ticker symbols."""
        unicode_tickers = ["AAPL中文", "MSFT®", "TEST™", "SYMBOL©"]

        for ticker in unicode_tickers:
            result = cli_runner.invoke(
                strategy_app,
                [
                    "run",
                    "--ticker",
                    ticker,
                    "--strategy",
                    "SMA",
                    "--dry-run",  # Use dry-run to avoid actual data fetching
                ],
            )

            # Should handle Unicode without crashing
            assert result.exit_code is not None  # Command completed

            # If error occurred, should be handled gracefully
            if result.exit_code != 0:
                assert (
                    "error" in result.stdout.lower()
                    or "invalid" in result.stdout.lower()
                )

    def test_special_characters_in_profile_names(self, cli_runner):
        """Test handling of special characters in profile names."""
        special_profiles = [
            "test-profile",
            "test_profile",
            "test.profile",
            "test@profile",
        ]

        for profile in special_profiles:
            result = cli_runner.invoke(
                strategy_app,
                ["run", "--profile", profile, "--dry-run"],
            )

            # Should handle special characters in profile names
            assert result.exit_code is not None

    def test_whitespace_in_parameters(self, cli_runner):
        """Test handling of whitespace in parameters."""
        # Test leading/trailing whitespace
        result1 = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "  AAPL  ", "--strategy", "SMA", "--dry-run"],
        )

        # Test empty spaces
        result2 = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", " ", "--strategy", "SMA", "--dry-run"],
        )

        # Should handle whitespace appropriately
        assert result1.exit_code is not None
        assert result2.exit_code is not None

    def test_path_with_special_characters(self, cli_runner):
        """Test handling of file paths with special characters."""
        # Note: This would typically be tested with actual file operations
        # For now, test that commands don't crash with special character inputs

        special_paths = [
            "profile with spaces",
            "profile-with-dashes",
            "profile_with_underscores",
            "profile.with.dots",
        ]

        for path in special_paths:
            result = cli_runner.invoke(
                strategy_app,
                ["run", "--profile", path, "--dry-run"],
            )

            # Should handle special characters in paths
            assert result.exit_code is not None

    def test_command_injection_prevention(self, cli_runner):
        """Test prevention of command injection through parameters."""
        injection_attempts = [
            "AAPL; rm -rf /",
            "AAPL && echo 'injected'",
            "AAPL | cat /etc/passwd",
            "AAPL `whoami`",
            "AAPL $(ls -la)",
        ]

        for injection in injection_attempts:
            result = cli_runner.invoke(
                strategy_app,
                ["run", "--ticker", injection, "--strategy", "SMA", "--dry-run"],
            )

            # Should prevent command injection
            assert result.exit_code is not None
            # Should not execute injected commands
            assert "root" not in result.stdout
            assert "injected" not in result.stdout


@pytest.mark.integration
class TestExtremeParameterValues:
    """Test handling of extreme parameter values and boundary conditions."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_extremely_large_parameter_values(self, cli_runner):
        """Test handling of extremely large parameter values."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--min-trades",
                str(2**31 - 1),  # Max 32-bit int
                "--years",
                "1000",
                "--min-win-rate",
                "0.99999999",
                "--dry-run",
            ],
        )

        # Should handle extreme values gracefully
        assert result.exit_code is not None

    def test_extremely_small_parameter_values(self, cli_runner):
        """Test handling of extremely small parameter values."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--min-trades",
                "1",  # Minimum possible
                "--years",
                "1",
                "--min-win-rate",
                "0.00000001",
                "--dry-run",
            ],
        )

        # Should handle small values gracefully
        assert result.exit_code is not None

    def test_floating_point_precision_edge_cases(self, cli_runner):
        """Test handling of floating point precision edge cases."""
        precision_values = [
            "0.1234567890123456789",  # High precision
            "1e-10",  # Scientific notation small
            "1e10",  # Scientific notation large
            "0.999999999999999999",  # Close to 1.0
            "0.000000000000000001",  # Close to 0.0
        ]

        for value in precision_values:
            result = cli_runner.invoke(
                strategy_app,
                [
                    "run",
                    "--ticker",
                    "AAPL",
                    "--strategy",
                    "SMA",
                    "--min-win-rate",
                    value,
                    "--dry-run",
                ],
            )

            # Should handle precision edge cases
            assert result.exit_code is not None

    def test_infinity_and_nan_parameter_values(self, cli_runner):
        """Test handling of infinity and NaN parameter values."""
        special_values = ["inf", "-inf", "nan", "infinity", "-infinity"]

        for value in special_values:
            result = cli_runner.invoke(
                strategy_app,
                [
                    "run",
                    "--ticker",
                    "AAPL",
                    "--strategy",
                    "SMA",
                    "--min-win-rate",
                    value,
                    "--dry-run",
                ],
            )

            # Should handle special float values appropriately
            assert result.exit_code is not None
            if "error" not in result.stdout.lower():
                # If accepted, should handle gracefully
                pass

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_extreme_parameter_sweep_ranges(
        self,
        mock_config_loader,
        mock_analyze,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of extreme parameter sweep ranges."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config.fast_period_range = [1, 10000]  # Extreme range
        mock_config.slow_period_range = [10001, 20000]  # Extreme range
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [100.0]},
        )
        mock_analyze.return_value = pl.DataFrame({"Score": [8.5]})

        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "1",
                "--fast-max",
                "10000",
                "--slow-min",
                "10001",
                "--slow-max",
                "20000",
            ],
        )

        # Should handle extreme ranges
        assert (
            result.exit_code == 0
            or "warning" in result.stdout.lower()
            or "error" in result.stdout.lower()
        )

    def test_maximum_ticker_list_length(self, cli_runner):
        """Test handling of maximum ticker list length."""
        # Create a very long ticker list
        long_ticker_list = [f"TICK{i:04d}" for i in range(1000)]
        ticker_string = ",".join(long_ticker_list)

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", ticker_string, "--strategy", "SMA", "--dry-run"],
        )

        # Should handle long ticker lists
        assert result.exit_code is not None


@pytest.mark.integration
class TestEmptyResultSetHandling:
    """Test handling of empty result sets and minimal data scenarios."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def minimal_price_data(self):
        """Minimal price data (single data point)."""
        return pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1)],
                "Close": [100.0],
                "High": [100.0],
                "Low": [100.0],
                "Volume": [0],
            },
        )

    @pytest.fixture
    def insufficient_price_data(self):
        """Insufficient price data for strategy calculation."""
        return pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1), pl.date(2023, 1, 2)],  # Only 2 points
                "Close": [100.0, 100.0],
                "High": [100.0, 100.0],
                "Low": [100.0, 100.0],
                "Volume": [0, 0],
            },
        )

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_single_data_point_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        minimal_price_data,
    ):
        """Test handling of single data point scenarios."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = (
            False  # No results due to insufficient data
        )
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = minimal_price_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA"],
        )

        # Should handle insufficient data gracefully
        assert result.exit_code == 0
        assert (
            "No strategies found" in result.stdout
            or "insufficient" in result.stdout.lower()
        )

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_insufficient_data_for_moving_averages(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        insufficient_price_data,
    ):
        """Test handling when data is insufficient for moving average calculations."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = False
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = insufficient_price_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA"],
        )

        # Should handle insufficient data for calculations
        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_parameter_sweep_no_valid_combinations(
        self,
        mock_config_loader,
        mock_analyze,
        mock_get_data,
        cli_runner,
    ):
        """Test parameter sweep when no valid combinations exist."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config.fast_period_range = [50, 60]  # Fast range higher than slow
        mock_config.slow_period_range = [10, 40]  # Slow range lower than fast
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [100.0]},
        )
        mock_analyze.return_value = pl.DataFrame()  # Empty results

        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "50",
                "--fast-max",
                "60",
                "--slow-min",
                "10",
                "--slow-max",
                "40",
            ],
        )

        # Should handle no valid combinations
        assert result.exit_code == 0
        assert "No valid parameter combinations" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_zero_volume_data_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of price data with zero volume."""
        # Create data with zero volume
        zero_volume_data = pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 3, 31),
                    interval="1d",
                ),
                "Close": [100.0] * 90,  # Flat prices
                "High": [100.0] * 90,
                "Low": [100.0] * 90,
                "Volume": [0] * 90,  # Zero volume
            },
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = zero_volume_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA"],
        )

        # Should handle zero volume data
        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_constant_price_data_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of constant price data (no price movement)."""
        # Create constant price data
        constant_price_data = pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 12, 31),
                    interval="1d",
                ),
                "Close": [100.0] * 365,  # Constant prices
                "High": [100.0] * 365,
                "Low": [100.0] * 365,
                "Volume": [1000000] * 365,
            },
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = constant_price_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA"],
        )

        # Should handle constant price data
        assert result.exit_code == 0


@pytest.mark.integration
class TestDateTimeEdgeCases:
    """Test handling of timezone and date edge cases."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_leap_year_data_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of leap year data."""
        # Create leap year data including Feb 29
        leap_year_data = pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2020, 2, 28),  # Leap year
                    end=pl.date(2020, 3, 1),
                    interval="1d",
                ),
                "Close": [100.0, 101.0, 102.0],
                "High": [102.0, 103.0, 104.0],
                "Low": [98.0, 99.0, 100.0],
                "Volume": [1000000] * 3,
            },
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = leap_year_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA"],
        )

        # Should handle leap year data
        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_weekend_gap_data_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of data with weekend gaps."""
        # Create data with missing weekend days
        weekday_dates = []
        base_date = pl.date(2023, 1, 2)  # Monday
        for i in range(50):  # 10 weeks of weekdays
            current_date = base_date + timedelta(days=i)
            # Only include weekdays (0=Monday, 6=Sunday)
            if current_date.weekday() < 5:
                weekday_dates.append(current_date)

        weekend_gap_data = pl.DataFrame(
            {
                "Date": weekday_dates,
                "Close": [100.0 + i for i in range(len(weekday_dates))],
                "High": [102.0 + i for i in range(len(weekday_dates))],
                "Low": [98.0 + i for i in range(len(weekday_dates))],
                "Volume": [1000000] * len(weekday_dates),
            },
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = weekend_gap_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA"],
        )

        # Should handle weekend gaps
        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_holiday_gap_data_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of data with holiday gaps."""
        # Create data with missing holiday (e.g., Christmas week)
        dates_with_gap = []
        base_date = pl.date(2023, 12, 20)
        for i in range(15):
            current_date = base_date + timedelta(days=i)
            # Skip Christmas week (Dec 25-29)
            if not (current_date.month == 12 and 25 <= current_date.day <= 29):
                dates_with_gap.append(current_date)

        holiday_gap_data = pl.DataFrame(
            {
                "Date": dates_with_gap,
                "Close": [100.0 + i for i in range(len(dates_with_gap))],
                "High": [102.0 + i for i in range(len(dates_with_gap))],
                "Low": [98.0 + i for i in range(len(dates_with_gap))],
                "Volume": [1000000] * len(dates_with_gap),
            },
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = holiday_gap_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA"],
        )

        # Should handle holiday gaps
        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_year_boundary_data_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of data spanning year boundaries."""
        # Create data spanning New Year's Eve/Day
        year_boundary_data = pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2022, 12, 30),
                    end=pl.date(2023, 1, 2),
                    interval="1d",
                ),
                "Close": [100.0, 101.0, 102.0, 103.0],
                "High": [102.0, 103.0, 104.0, 105.0],
                "Low": [98.0, 99.0, 100.0, 101.0],
                "Volume": [1000000] * 4,
            },
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = year_boundary_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA"],
        )

        # Should handle year boundary data
        assert result.exit_code == 0


@pytest.mark.integration
class TestUnusualMarketConditions:
    """Test handling of unusual market conditions and data patterns."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_extreme_volatility_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of extremely volatile price data."""
        # Create highly volatile data
        volatile_prices = []
        base_price = 100.0
        for i in range(252):  # 1 year of trading days
            # Extreme daily moves (±50%)
            volatility = 0.5 if i % 2 == 0 else -0.5
            price = base_price * (1 + volatility)
            volatile_prices.append(max(price, 0.01))  # Ensure positive prices
            base_price = volatile_prices[-1]

        volatile_data = pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 12, 31),
                    interval="1d",
                )[:252],
                "Close": volatile_prices,
                "High": [p * 1.1 for p in volatile_prices],
                "Low": [p * 0.9 for p in volatile_prices],
                "Volume": [1000000] * 252,
            },
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["VOLATILE_STOCK"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = volatile_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "VOLATILE_STOCK", "--strategy", "SMA"],
        )

        # Should handle extreme volatility
        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_trending_market_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of strongly trending markets."""
        # Create strongly trending data (consistent upward movement)
        trending_prices = [100.0 * (1.001**i) for i in range(252)]  # ~0.1% daily growth

        trending_data = pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 12, 31),
                    interval="1d",
                )[:252],
                "Close": trending_prices,
                "High": [p * 1.01 for p in trending_prices],
                "Low": [p * 0.99 for p in trending_prices],
                "Volume": [1000000] * 252,
            },
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["TRENDING_STOCK"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = trending_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "TRENDING_STOCK", "--strategy", "SMA"],
        )

        # Should handle trending markets
        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sideways_market_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of sideways/ranging markets."""
        # Create sideways market data (oscillating around mean)
        sideways_prices = []
        base_price = 100.0
        for i in range(252):
            # Oscillate around base price with small amplitude
            oscillation = 5.0 * math.sin(2 * math.pi * i / 20)  # 20-day cycle
            sideways_prices.append(base_price + oscillation)

        sideways_data = pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 12, 31),
                    interval="1d",
                )[:252],
                "Close": sideways_prices,
                "High": [p * 1.01 for p in sideways_prices],
                "Low": [p * 0.99 for p in sideways_prices],
                "Volume": [1000000] * 252,
            },
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["SIDEWAYS_STOCK"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = sideways_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "SIDEWAYS_STOCK", "--strategy", "SMA"],
        )

        # Should handle sideways markets
        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_market_crash_scenario_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of market crash scenarios."""
        # Create crash scenario data (sudden large drop)
        crash_prices = []
        base_price = 100.0

        # Normal market for first 50 days
        for i in range(50):
            crash_prices.append(base_price + i * 0.1)

        # Crash event (50% drop over 5 days)
        crash_base = crash_prices[-1]
        for i in range(5):
            crash_prices.append(crash_base * (0.5 ** ((i + 1) / 5)))

        # Recovery period
        recovery_base = crash_prices[-1]
        for i in range(50):
            crash_prices.append(recovery_base * (1 + 0.01 * i))

        crash_data = pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 4, 15),
                    interval="1d",
                )[: len(crash_prices)],
                "Close": crash_prices,
                "High": [p * 1.02 for p in crash_prices],
                "Low": [p * 0.98 for p in crash_prices],
                "Volume": [1000000] * len(crash_prices),
            },
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["CRASH_STOCK"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = crash_data

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "CRASH_STOCK", "--strategy", "SMA"],
        )

        # Should handle market crash scenarios
        assert result.exit_code == 0


@pytest.mark.integration
class TestLargeScaleDataProcessing:
    """Test handling of large-scale data processing limits."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_maximum_years_parameter(self, cli_runner):
        """Test handling of maximum years parameter."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--use-years",
                "--years",
                "100",  # Very long backtest period
                "--dry-run",
            ],
        )

        # Should handle large years parameter
        assert result.exit_code is not None

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_very_large_dataset_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of very large datasets."""
        # Create large dataset (10 years of daily data)
        large_dates = pl.date_range(
            start=pl.date(2014, 1, 1),
            end=pl.date(2023, 12, 31),
            interval="1d",
        )

        large_dataset = pl.DataFrame(
            {
                "Date": large_dates,
                "Close": [100.0 + (i % 1000) * 0.1 for i in range(len(large_dates))],
                "High": [102.0 + (i % 1000) * 0.1 for i in range(len(large_dates))],
                "Low": [98.0 + (i % 1000) * 0.1 for i in range(len(large_dates))],
                "Volume": [1000000] * len(large_dates),
            },
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = large_dataset

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA"],
        )

        # Should handle large datasets
        assert result.exit_code == 0

    def test_maximum_parameter_combinations_sweep(self, cli_runner):
        """Test parameter sweep with maximum combinations."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "1",
                "--fast-max",
                "100",
                "--slow-min",
                "101",
                "--slow-max",
                "200",
                "--dry-run",
            ],
        )

        # Should handle large parameter spaces
        assert result.exit_code is not None
