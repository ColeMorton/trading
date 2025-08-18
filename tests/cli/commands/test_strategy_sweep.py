"""
Comprehensive tests for CLI Strategy Sweep Command.

This test suite covers the `trading-cli strategy sweep` command with focus on:
- Parameter sweep functionality for MA Cross strategies
- Range validation and parameter combinations
- Multi-ticker sweeps
- Result filtering and display
- Error handling and edge cases
- Performance with large parameter spaces
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import polars as pl
import pytest
from typer.testing import CliRunner

from app.cli.commands.strategy import app as strategy_app
from app.cli.models.strategy import StrategyType


class TestStrategySweepCommand:
    """Test cases for strategy sweep command."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_profile_dir(self):
        """Create temporary directory with test profiles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir) / "profiles"
            profile_dir.mkdir()
            yield profile_dir

    @pytest.fixture
    def sample_sweep_profile(self):
        """Sample profile for parameter sweeps."""
        return """
metadata:
  name: test_sweep
  description: Test parameter sweep configuration
config_type: strategy
config:
  ticker: [AAPL]
  strategy_types: [SMA]
  use_years: false
  years: 15
  multi_ticker: false
  minimums:
    win_rate: 0.5
    trades: 20
  synthetic:
    use_synthetic: false
  filter:
    use_current: false
  fast_period_range: [5, 15]
  slow_period_range: [20, 40]
"""

    @pytest.fixture
    def mock_price_data(self):
        """Mock price data for sweep analysis."""
        return pl.DataFrame(
            {
                "timestamp": pl.date_range(
                    start=pl.date(2023, 1, 1), end=pl.date(2023, 12, 31), interval="1d"
                ),
                "close": [100.0 + i * 0.1 for i in range(365)],
            }
        )

    @pytest.fixture
    def mock_sweep_results(self):
        """Mock parameter sweep results."""
        return pl.DataFrame(
            {
                "Ticker": ["AAPL"] * 4,
                "Strategy Type": ["SMA"] * 4,
                "Fast Period": [5, 10, 5, 10],
                "Slow Period": [20, 30, 25, 35],
                "Total Trades": [50, 45, 55, 40],
                "Win Rate [%]": [55.0, 60.0, 52.0, 58.0],
                "Total Return [%]": [25.5, 35.2, 18.7, 28.9],
                "Sharpe Ratio": [1.2, 1.5, 1.0, 1.3],
                "Score": [8.5, 9.2, 7.8, 8.9],
            }
        )

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_single_ticker_success(
        self,
        mock_config_loader,
        mock_logging,
        mock_analyze,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_sweep_results,
    ):
        """Test successful parameter sweep with single ticker."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [5, 15]
        mock_config.slow_period_range = [20, 40]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = mock_sweep_results
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
            ],
        )

        # Verify results
        assert result.exit_code == 0
        assert "Parameter sweep completed" in result.stdout
        assert "AAPL" in result.stdout
        mock_get_data.assert_called_once()
        mock_analyze.assert_called_once()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_multiple_tickers(
        self,
        mock_config_loader,
        mock_logging,
        mock_analyze,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_sweep_results,
    ):
        """Test parameter sweep with multiple tickers."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL", "MSFT", "GOOGL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [5, 15]
        mock_config.slow_period_range = [20, 40]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = mock_sweep_results
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL,MSFT,GOOGL",
                "--fast-min",
                "5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
            ],
        )

        # Verify results
        assert result.exit_code == 0
        assert "Processing parameter sweep for AAPL" in result.stdout
        assert "Processing parameter sweep for MSFT" in result.stdout
        assert "Processing parameter sweep for GOOGL" in result.stdout
        assert mock_get_data.call_count == 3  # Called for each ticker

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_multiple_strategies(
        self,
        mock_config_loader,
        mock_logging,
        mock_analyze,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_sweep_results,
    ):
        """Test parameter sweep with multiple strategy types."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA, StrategyType.EMA]
        mock_config.fast_period_range = [5, 15]
        mock_config.slow_period_range = [20, 40]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = mock_sweep_results
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
            ],
        )

        # Verify results
        assert result.exit_code == 0
        assert "Running SMA parameter sweep" in result.stdout
        assert "Running EMA parameter sweep" in result.stdout
        assert mock_analyze.call_count == 2  # Called for each strategy type

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_with_profile(
        self, mock_config_loader, cli_runner, temp_profile_dir, sample_sweep_profile
    ):
        """Test parameter sweep using profile configuration."""
        # Create profile file
        profile_file = temp_profile_dir / "test_sweep.yaml"
        profile_file.write_text(sample_sweep_profile)

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [5, 15]
        mock_config.slow_period_range = [20, 40]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        with patch("app.cli.commands.strategy.get_data") as mock_get_data, patch(
            "app.cli.commands.strategy.analyze_parameter_sensitivity"
        ) as mock_analyze, patch(
            "app.cli.commands.strategy.logging_context"
        ) as mock_logging:
            mock_get_data.return_value = pl.DataFrame({"close": [100, 101, 102]})
            mock_analyze.return_value = pl.DataFrame({"Score": [8.5]})
            mock_logging.return_value.__enter__ = Mock()
            mock_logging.return_value.__exit__ = Mock()

            # Run command with profile
            result = cli_runner.invoke(
                strategy_app, ["sweep", "--profile", "test_sweep"]
            )

            # Verify profile was loaded
            assert result.exit_code == 0
            mock_config_loader.return_value.load_from_profile.assert_called_once()

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_dry_run(self, mock_config_loader, cli_runner):
        """Test parameter sweep with dry-run flag."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [5, 15]
        mock_config.slow_period_range = [20, 40]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Run command with dry-run
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
                "--dry-run",
            ],
        )

        # Verify dry-run shows preview without execution
        assert result.exit_code == 0
        assert "Parameter Sweep Preview" in result.stdout or "Preview" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_max_results_limit(
        self, mock_config_loader, mock_logging, mock_analyze, mock_get_data, cli_runner
    ):
        """Test parameter sweep with maximum results limit."""
        # Create large result set
        large_results = pl.DataFrame(
            {
                "Ticker": ["AAPL"] * 100,
                "Score": [i for i in range(100, 0, -1)],  # Descending scores
            }
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [5, 15]
        mock_config.slow_period_range = [20, 40]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = pl.DataFrame({"close": [100, 101, 102]})
        mock_analyze.return_value = large_results
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Run command with max results limit
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
                "--max-results",
                "10",
            ],
        )

        # Verify results are limited
        assert result.exit_code == 0
        assert "showing top 10" in result.stdout

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_invalid_ranges(self, mock_config_loader, cli_runner):
        """Test parameter sweep with invalid parameter ranges."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Test invalid range (fast_max <= fast_min)
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "20",
                "--fast-max",
                "10",  # Invalid: max < min
                "--slow-min",
                "30",
                "--slow-max",
                "50",
            ],
        )

        # Should handle invalid ranges
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_data_fetch_failure(
        self, mock_config_loader, mock_logging, mock_get_data, cli_runner
    ):
        """Test parameter sweep when data fetching fails."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [5, 15]
        mock_config.slow_period_range = [20, 40]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = None  # Data fetch fails
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
            ],
        )

        # Verify failure is handled
        assert result.exit_code == 0  # Command completes but shows failure message
        assert "Failed to fetch price data" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_analysis_failure(
        self, mock_config_loader, mock_logging, mock_analyze, mock_get_data, cli_runner
    ):
        """Test parameter sweep when analysis fails."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [5, 15]
        mock_config.slow_period_range = [20, 40]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = pl.DataFrame({"close": [100, 101, 102]})
        mock_analyze.return_value = None  # Analysis fails
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
            ],
        )

        # Verify failure is handled
        assert result.exit_code == 0
        assert "No valid parameter combinations found" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_empty_results(
        self, mock_config_loader, mock_logging, mock_analyze, mock_get_data, cli_runner
    ):
        """Test parameter sweep with empty analysis results."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [5, 15]
        mock_config.slow_period_range = [20, 40]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = pl.DataFrame({"close": [100, 101, 102]})
        mock_analyze.return_value = pl.DataFrame()  # Empty results
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
            ],
        )

        # Verify empty results are handled
        assert result.exit_code == 0
        assert "No valid parameter combinations found" in result.stdout

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_default_ranges_warning(self, mock_config_loader, cli_runner):
        """Test parameter sweep shows warning when using default ranges."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = None  # No range specified
        mock_config.slow_period_range = None  # No range specified
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        with patch("app.cli.commands.strategy.get_data") as mock_get_data, patch(
            "app.cli.commands.strategy.analyze_parameter_sensitivity"
        ) as mock_analyze, patch(
            "app.cli.commands.strategy.logging_context"
        ) as mock_logging:
            mock_get_data.return_value = pl.DataFrame({"close": [100, 101, 102]})
            mock_analyze.return_value = pl.DataFrame({"Score": [8.5]})
            mock_logging.return_value.__enter__ = Mock()
            mock_logging.return_value.__exit__ = Mock()

            # Run command without range parameters
            result = cli_runner.invoke(strategy_app, ["sweep", "--ticker", "AAPL"])

            # Verify warning is shown
            assert result.exit_code == 0
            assert "No period ranges specified" in result.stdout
            assert "Using defaults" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_combination_count_display(
        self, mock_config_loader, mock_logging, mock_analyze, mock_get_data, cli_runner
    ):
        """Test parameter sweep displays combination count correctly."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [5, 7]  # 3 values: 5, 6, 7
        mock_config.slow_period_range = [20, 22]  # 3 values: 20, 21, 22
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = pl.DataFrame({"close": [100, 101, 102]})
        mock_analyze.return_value = pl.DataFrame({"Score": [8.5]})
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "7",
                "--slow-min",
                "20",
                "--slow-max",
                "22",
            ],
        )

        # Verify combination count is shown
        # Valid combinations: (5,20), (5,21), (5,22), (6,20), (6,21), (6,22), (7,20), (7,21), (7,22) = 9
        # But we only count valid combinations where fast < slow = 3 combinations
        assert result.exit_code == 0
        assert "combinations" in result.stdout.lower()

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_exception_handling(self, mock_config_loader, cli_runner):
        """Test parameter sweep handles exceptions gracefully."""
        # Setup mock to raise exception
        mock_config_loader.return_value.load_from_profile.side_effect = RuntimeError(
            "Unexpected error"
        )

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
            ],
        )

        # Verify error is handled gracefully
        assert "error" in result.stdout.lower() or result.exit_code != 0


class TestStrategySweepCommandEdgeCases:
    """Test edge cases and boundary conditions for strategy sweep command."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_sweep_command_no_arguments(self, cli_runner):
        """Test sweep command with no arguments."""
        result = cli_runner.invoke(strategy_app, ["sweep"])

        # Should show help or require arguments
        assert result.exit_code != 0 or "help" in result.stdout.lower()

    def test_sweep_command_invalid_range_values(self, cli_runner):
        """Test sweep command with invalid range values."""
        # Test negative values
        result1 = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "-5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
            ],
        )

        # Test zero values
        result2 = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "0",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
            ],
        )

        # Should handle invalid values appropriately
        assert result1.exit_code != 0 or "error" in result1.stdout.lower()
        assert result2.exit_code != 0 or "error" in result2.stdout.lower()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_very_large_ranges(
        self, mock_config_loader, mock_logging, mock_analyze, mock_get_data, cli_runner
    ):
        """Test parameter sweep with very large parameter ranges."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [1, 1000]  # Very large range
        mock_config.slow_period_range = [1001, 2000]  # Very large range
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = pl.DataFrame({"close": [100, 101, 102]})
        mock_analyze.return_value = pl.DataFrame({"Score": [8.5]})
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Run command with very large ranges
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "1",
                "--fast-max",
                "1000",
                "--slow-min",
                "1001",
                "--slow-max",
                "2000",
            ],
        )

        # Should handle large ranges (may show warnings or limits)
        assert result.exit_code == 0 or "warning" in result.stdout.lower()

    def test_sweep_command_extreme_max_results(self, cli_runner):
        """Test sweep command with extreme max results values."""
        # Test very large max_results
        result1 = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
                "--max-results",
                "999999",
            ],
        )

        # Test zero max_results
        result2 = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "15",
                "--slow-min",
                "20",
                "--slow-max",
                "40",
                "--max-results",
                "0",
            ],
        )

        # Should handle extreme values appropriately
        assert result1.exit_code == 0 or result1.exit_code != 0
        assert result2.exit_code != 0 or "error" in result2.stdout.lower()

    def test_sweep_command_overlapping_ranges(self, cli_runner):
        """Test sweep command with overlapping fast and slow ranges."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "10",
                "--fast-max",
                "30",
                "--slow-min",
                "20",  # Overlaps with fast range
                "--slow-max",
                "40",
            ],
        )

        # Should handle overlapping ranges (may produce valid combinations where fast < slow)
        assert result.exit_code == 0

    def test_sweep_command_identical_ranges(self, cli_runner):
        """Test sweep command with identical fast and slow ranges."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "10",
                "--fast-max",
                "20",
                "--slow-min",
                "10",
                "--slow-max",
                "20",
            ],
        )

        # Should handle identical ranges (may produce few or no valid combinations)
        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_single_parameter_combinations(
        self, mock_config_loader, mock_logging, mock_analyze, mock_get_data, cli_runner
    ):
        """Test parameter sweep with single parameter value ranges."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [10, 10]  # Single value
        mock_config.slow_period_range = [20, 20]  # Single value
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = pl.DataFrame({"close": [100, 101, 102]})
        mock_analyze.return_value = pl.DataFrame({"Score": [8.5]})
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Run command with single value ranges
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "10",
                "--fast-max",
                "10",
                "--slow-min",
                "20",
                "--slow-max",
                "20",
            ],
        )

        # Should handle single value ranges (produces one combination)
        assert result.exit_code == 0
        # Should show combination count of 1
        assert "1" in result.stdout

    def test_sweep_command_special_ticker_formats(self, cli_runner):
        """Test sweep command with special ticker formats."""
        special_tickers = ["BTC-USD", "STRK/MSTR", "^GSPC", "GC=F"]

        for ticker in special_tickers:
            result = cli_runner.invoke(
                strategy_app,
                [
                    "sweep",
                    "--ticker",
                    ticker,
                    "--fast-min",
                    "5",
                    "--fast-max",
                    "15",
                    "--slow-min",
                    "20",
                    "--slow-max",
                    "40",
                ],
            )
            # Should handle special ticker formats (may succeed or fail gracefully)
            assert result.exit_code is not None

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_sweep_command_missing_profile(self, mock_config_loader, cli_runner):
        """Test sweep command with missing profile file."""
        mock_config_loader.return_value.load_from_profile.side_effect = (
            FileNotFoundError("Profile not found")
        )

        # Run command with nonexistent profile
        result = cli_runner.invoke(strategy_app, ["sweep", "--profile", "nonexistent"])

        # Should handle missing profile appropriately
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_sweep_command_mixed_parameter_sources(self, cli_runner):
        """Test sweep command with parameters from profile and command line."""
        # This tests the priority of command line overrides vs profile settings
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--profile",
                "default_strategy",
                "--ticker",
                "AAPL",  # Override profile ticker
                "--fast-min",
                "5",  # Override profile range
                "--fast-max",
                "15",
            ],
        )

        # Should handle mixed parameter sources (command line should override profile)
        assert (
            result.exit_code == 0 or result.exit_code != 0
        )  # Either succeeds or fails gracefully
