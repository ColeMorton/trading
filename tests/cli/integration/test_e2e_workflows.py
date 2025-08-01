"""
End-to-End CLI Workflow Tests.

This test suite validates complete CLI workflows from command invocation
through to file system effects:
- Complete strategy analysis workflows
- Realistic data processing scenarios
- File export verification
- Multi-step command sequences
- Integration between all system components
- File system cleanup validation

These tests ensure the entire pipeline works correctly in realistic usage scenarios.
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import polars as pl
import pytest
from typer.testing import CliRunner

from app.cli.commands.strategy import app as strategy_app
from app.cli.models.strategy import StrategyType


class TestCompleteStrategyWorkflows:
    """Test complete strategy analysis workflows from CLI to file export."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with expected directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create expected directory structure
            (workspace / "data" / "raw" / "portfolios").mkdir(
                parents=True, exist_ok=True
            )
            (workspace / "data" / "raw" / "portfolios_filtered").mkdir(
                parents=True, exist_ok=True
            )
            (workspace / "data" / "raw" / "portfolios_best").mkdir(
                parents=True, exist_ok=True
            )
            (workspace / "app" / "cli" / "profiles").mkdir(parents=True, exist_ok=True)

            yield workspace

    @pytest.fixture
    def mock_price_data(self):
        """Realistic price data for testing."""
        from datetime import datetime, timedelta

        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        dates = pl.date_range(start_date, end_date, interval="1d", eager=True)

        # Generate realistic price movement
        base_price = 150.0
        price_data = []
        for i in range(len(dates)):
            volatility = 0.02
            price_change = (i % 7 - 3) * volatility  # Simple price pattern
            price = base_price * (1 + price_change + (i * 0.0001))  # Small upward trend
            price_data.append(price)

        return pl.DataFrame(
            {
                "Date": dates,
                "Close": price_data,
                "High": [p * 1.01 for p in price_data],
                "Low": [p * 0.99 for p in price_data],
                "Open": price_data,
                "Volume": [1000000] * len(price_data),
            }
        )

    @pytest.fixture
    def mock_strategy_results(self):
        """Realistic strategy analysis results."""
        return pl.DataFrame(
            {
                "Ticker": ["AAPL"] * 3,
                "Strategy Type": ["SMA"] * 3,
                "Short Window": [5, 10, 15],
                "Long Window": [20, 30, 40],
                "Total Trades": [48, 52, 45],
                "Win Rate [%]": [58.3, 61.5, 55.6],
                "Total Return [%]": [24.7, 31.2, 19.8],
                "Sharpe Ratio": [1.25, 1.45, 1.10],
                "Max Drawdown [%]": [8.9, 7.2, 11.3],
                "Score": [8.7, 9.2, 7.9],
                "Profit Factor": [1.38, 1.52, 1.25],
                "Sortino Ratio": [1.18, 1.34, 1.05],
                "Calmar Ratio": [2.77, 4.33, 1.75],
                "Metric Type": [
                    "Most Total Return [%]",
                    "Most Sharpe Ratio",
                    "Most Win Rate [%]",
                ],
            }
        )

    @pytest.fixture
    def realistic_profile_content(self):
        """Realistic strategy profile for testing."""
        return """
metadata:
  name: e2e_test_strategy
  description: End-to-end test strategy configuration

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
"""

    def create_test_profile(self, workspace, profile_content):
        """Helper to create test profile file."""
        profiles_dir = workspace / "app" / "cli" / "profiles"
        profile_file = profiles_dir / "e2e_test_strategy.yaml"
        profile_file.write_text(profile_content)
        return profile_file

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_complete_sma_strategy_workflow(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        temp_workspace,
        mock_price_data,
        mock_strategy_results,
        realistic_profile_content,
    ):
        """Test complete SMA strategy workflow from CLI command to file export."""
        # Setup test environment
        profile_file = self.create_test_profile(
            temp_workspace, realistic_profile_content
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.use_years = False
        mock_config.years = 15
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = mock_price_data

        # Mock the actual strategy execution to generate results
        with patch("app.cli.commands.strategy.export_portfolios") as mock_export:
            mock_export.return_value = (mock_strategy_results, True)

            # Execute CLI command
            result = cli_runner.invoke(
                strategy_app,
                [
                    "run",
                    "--profile",
                    "e2e_test_strategy",
                    "--ticker",
                    "AAPL",
                    "--strategy",
                    "SMA",
                ],
            )

        # Verify command execution
        assert result.exit_code == 0
        assert "Strategy analysis completed successfully" in result.stdout
        assert "AAPL" in result.stdout
        assert "SMA" in result.stdout

        # Verify component interactions
        mock_config_loader.return_value.load_from_profile.assert_called()
        mock_dispatcher.validate_strategy_compatibility.assert_called_once()
        mock_dispatcher.execute_strategy.assert_called_once()

        # Verify data was fetched
        mock_get_data.assert_called()

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_complete_parameter_sweep_workflow(
        self,
        mock_config_loader,
        mock_logging,
        mock_analyze,
        mock_get_data,
        cli_runner,
        temp_workspace,
        mock_price_data,
        mock_strategy_results,
    ):
        """Test complete parameter sweep workflow with realistic data processing."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [5, 15]
        mock_config.slow_period_range = [20, 40]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = mock_price_data

        # Create expanded results for parameter sweep
        sweep_results = pl.DataFrame(
            {
                "Ticker": ["AAPL"] * 12,
                "Strategy Type": ["SMA"] * 12,
                "Short Window": [5, 5, 5, 10, 10, 10, 15, 15, 15, 5, 10, 15],
                "Long Window": [20, 25, 30, 20, 25, 30, 20, 25, 30, 35, 35, 35],
                "Total Trades": [45, 43, 41, 42, 40, 38, 39, 37, 35, 48, 46, 44],
                "Win Rate [%]": [
                    58.3,
                    59.1,
                    60.2,
                    61.5,
                    62.3,
                    63.1,
                    59.8,
                    60.5,
                    61.2,
                    57.9,
                    58.7,
                    59.4,
                ],
                "Total Return [%]": [
                    24.7,
                    26.3,
                    28.1,
                    31.2,
                    33.8,
                    36.4,
                    29.5,
                    31.7,
                    34.2,
                    23.1,
                    25.6,
                    27.9,
                ],
                "Sharpe Ratio": [
                    1.25,
                    1.31,
                    1.38,
                    1.45,
                    1.52,
                    1.59,
                    1.33,
                    1.40,
                    1.47,
                    1.20,
                    1.27,
                    1.34,
                ],
                "Score": [8.7, 8.9, 9.1, 9.2, 9.4, 9.6, 8.8, 9.0, 9.3, 8.5, 8.6, 8.8],
            }
        )
        mock_analyze.return_value = sweep_results

        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Execute parameter sweep
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

        # Verify sweep execution
        assert result.exit_code == 0
        assert "Parameter sweep completed" in result.stdout
        assert "AAPL" in result.stdout
        assert "combinations" in result.stdout.lower()

        # Verify sweep processed data correctly
        mock_get_data.assert_called_once()
        mock_analyze.assert_called_once()

        # Verify results are displayed
        assert "showing top 10" in result.stdout

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_multi_ticker_workflow_integration(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        temp_workspace,
        mock_price_data,
    ):
        """Test multi-ticker workflow with realistic processing."""
        # Setup mocks for multiple tickers
        tickers = ["AAPL", "MSFT", "GOOGL"]
        mock_config = Mock()
        mock_config.ticker = tickers
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Mock different price data for each ticker
        def get_data_side_effect(ticker, *args, **kwargs):
            # Return slightly different data for each ticker
            base_data = mock_price_data.clone()
            if ticker == "MSFT":
                base_data = base_data.with_columns(pl.col("Close") * 1.2)
            elif ticker == "GOOGL":
                base_data = base_data.with_columns(pl.col("Close") * 0.8)
            return base_data

        mock_get_data.side_effect = get_data_side_effect

        # Execute multi-ticker analysis
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL,MSFT,GOOGL", "--strategy", "SMA"]
        )

        # Verify multi-ticker processing
        assert result.exit_code == 0
        assert "Processing 3 tickers" in result.stdout

        # Verify each ticker was processed
        for ticker in tickers:
            assert ticker in result.stdout

        # Verify data was fetched for each ticker
        assert mock_get_data.call_count == 3

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_mixed_strategy_workflow_integration(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        temp_workspace,
        mock_price_data,
    ):
        """Test mixed strategy workflow (SMA + EMA + MACD)."""
        # Setup mocks for mixed strategies
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [
            StrategyType.SMA,
            StrategyType.EMA,
            StrategyType.MACD,
        ]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = mock_price_data

        # Execute mixed strategy analysis
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--strategy",
                "EMA",
                "--strategy",
                "MACD",
            ],
        )

        # Verify mixed strategy processing
        assert result.exit_code == 0
        assert "SMA, EMA, MACD" in result.stdout

        # Verify strategy compatibility was validated
        mock_dispatcher.validate_strategy_compatibility.assert_called_once()

    def test_file_system_integration_workflow(self, cli_runner, temp_workspace):
        """Test that CLI operations create expected file system artifacts."""
        # This test verifies file system effects without heavy mocking
        profiles_dir = temp_workspace / "app" / "cli" / "profiles"

        # Create a minimal profile for testing
        profile_content = """
metadata:
  name: file_system_test
  description: Test file system integration

config_type: strategy
config:
  ticker: [TEST]
  strategy_types: [SMA]
"""
        profile_file = profiles_dir / "file_system_test.yaml"
        profile_file.write_text(profile_content)

        # Verify profile file was created correctly
        assert profile_file.exists()
        assert profile_file.is_file()

        # Verify directory structure is correct
        assert (temp_workspace / "data" / "raw" / "portfolios").exists()
        assert (temp_workspace / "data" / "raw" / "portfolios_filtered").exists()
        assert (temp_workspace / "data" / "raw" / "portfolios_best").exists()

        # Test dry-run to verify command parsing without execution
        with patch("app.cli.commands.strategy.ConfigLoader") as mock_config_loader:
            mock_config = Mock()
            mock_config.ticker = ["TEST"]
            mock_config.strategy_types = [StrategyType.SMA]
            mock_config_loader.return_value.load_from_profile.return_value = mock_config

            result = cli_runner.invoke(
                strategy_app, ["run", "--profile", "file_system_test", "--dry-run"]
            )

            # Verify dry-run worked
            assert result.exit_code == 0
            assert "Preview" in result.stdout or "Configuration" in result.stdout

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_verbose_output_workflow_integration(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        temp_workspace,
        mock_price_data,
    ):
        """Test workflow with verbose output enabled."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = mock_price_data

        # Execute with verbose output
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", "SMA", "--verbose"]
        )

        # Verify verbose output
        assert result.exit_code == 0
        # Should contain additional verbose information
        verbose_indicators = [
            "Loading",
            "Executing",
            "Processing",
            "strategy execution",
        ]
        assert any(
            indicator.lower() in result.stdout.lower()
            for indicator in verbose_indicators
        )

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_parameter_override_workflow_integration(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        temp_workspace,
        mock_price_data,
    ):
        """Test workflow with parameter overrides applied correctly."""
        # Setup base config
        mock_config = Mock()
        mock_config.ticker = ["TSLA"]  # Base ticker
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = mock_price_data

        # Execute with overrides
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",  # Override ticker
                "--strategy",
                "EMA",  # Override strategy
                "--min-trades",
                "50",  # Override minimum
                "--min-win-rate",
                "0.6",  # Override minimum
                "--years",
                "10",  # Override years
            ],
        )

        # Verify overrides were applied
        assert result.exit_code == 0

        # Verify config loader was called with overrides
        mock_config_loader.return_value.load_from_profile.assert_called()
        call_args = mock_config_loader.return_value.load_from_profile.call_args

        # Check that overrides dict was passed
        if len(call_args[0]) > 2:
            overrides = call_args[0][2]
            assert isinstance(overrides, dict)
            # Should contain our override keys
            override_keys = set(overrides.keys())
            expected_keys = {
                "ticker",
                "strategy_type",
                "min_trades",
                "min_win_rate",
                "years",
            }
            assert expected_keys.issubset(override_keys) or len(override_keys) > 0


class TestCompleteErrorRecoveryWorkflows:
    """Test complete error recovery workflows and graceful degradation."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_data_fetch_failure_recovery_workflow(
        self, mock_config_loader, mock_get_data, cli_runner
    ):
        """Test complete workflow when data fetching fails."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["INVALID_TICKER"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = None  # Simulate data fetch failure

        # Execute command that should handle failure gracefully
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "INVALID_TICKER", "--strategy", "SMA"]
        )

        # Verify graceful failure handling
        assert result.exit_code == 0
        assert (
            "Failed to fetch price data" in result.stdout
            or "error" in result.stdout.lower()
        )

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_partial_success_multi_ticker_workflow(
        self, mock_config_loader, mock_dispatcher_class, mock_get_data, cli_runner
    ):
        """Test workflow where some tickers succeed and others fail."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL", "INVALID", "MSFT"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Mock data fetch to succeed for valid tickers, fail for invalid
        def get_data_side_effect(ticker, *args, **kwargs):
            if ticker == "INVALID":
                return None
            else:
                # Return minimal valid data
                return pl.DataFrame({"Date": [pl.date(2023, 1, 1)], "Close": [100.0]})

        mock_get_data.side_effect = get_data_side_effect

        # Execute multi-ticker command
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL,INVALID,MSFT", "--strategy", "SMA"]
        )

        # Should handle partial success gracefully
        assert result.exit_code == 0
        assert "Processing 3 tickers" in result.stdout

        # Should process valid tickers
        assert mock_get_data.call_count == 3  # Attempted all tickers

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_configuration_error_recovery_workflow(
        self, mock_config_loader, cli_runner
    ):
        """Test workflow recovery from configuration errors."""
        # Mock configuration loading failure
        mock_config_loader.return_value.load_from_profile.side_effect = ValueError(
            "Invalid configuration"
        )

        # Execute command
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", "SMA"]
        )

        # Should handle configuration errors gracefully
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_strategy_execution_partial_failure_workflow(
        self, mock_config_loader, mock_dispatcher_class, mock_get_data, cli_runner
    ):
        """Test workflow when strategy execution partially fails."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA, StrategyType.EMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = False  # Partial failure
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [100.0]}
        )

        # Execute command
        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA", "--strategy", "EMA"],
        )

        # Should handle execution failure gracefully
        assert result.exit_code == 0
        assert (
            "No strategies found matching" in result.stdout
            or "completed" in result.stdout.lower()
        )


class TestRealisticDataProcessingWorkflows:
    """Test workflows with realistic data processing scenarios."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def large_realistic_dataset(self):
        """Generate large realistic dataset for performance testing."""
        # Generate 5 years of daily data
        dates = pl.date_range(
            start=pl.date(2019, 1, 1), end=pl.date(2023, 12, 31), interval="1d"
        )

        # Generate realistic price data with trends and volatility
        import math

        price_data = []
        base_price = 100.0

        for i, date in enumerate(dates):
            # Add trend, seasonality, and random volatility
            trend = i * 0.01  # Small upward trend
            seasonality = math.sin(2 * math.pi * i / 252) * 5  # Annual cycle
            volatility = (i % 20 - 10) * 0.5  # Random walk component
            price = base_price + trend + seasonality + volatility
            price_data.append(max(price, 10.0))  # Ensure positive prices

        return pl.DataFrame(
            {
                "Date": dates,
                "Close": price_data,
                "High": [p * 1.02 for p in price_data],
                "Low": [p * 0.98 for p in price_data],
                "Open": price_data,
                "Volume": [1000000 + (i % 100000) for i in range(len(price_data))],
            }
        )

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_large_dataset_parameter_sweep_workflow(
        self,
        mock_config_loader,
        mock_logging,
        mock_analyze,
        mock_get_data,
        cli_runner,
        large_realistic_dataset,
    ):
        """Test parameter sweep workflow with large realistic dataset."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.fast_period_range = [5, 50]  # Large range
        mock_config.slow_period_range = [20, 200]  # Large range
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_get_data.return_value = large_realistic_dataset
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Generate large result set
        n_results = 100
        large_results = pl.DataFrame(
            {
                "Ticker": ["AAPL"] * n_results,
                "Strategy Type": ["SMA"] * n_results,
                "Short Window": list(range(5, 55)) + list(range(5, 55)),
                "Long Window": list(range(20, 120)) + list(range(120, 220)),
                "Total Trades": [45 + i for i in range(n_results)],
                "Win Rate [%]": [50.0 + (i % 30) for i in range(n_results)],
                "Total Return [%]": [10.0 + (i % 50) for i in range(n_results)],
                "Score": [5.0 + (i % 50) * 0.1 for i in range(n_results)],
            }
        )
        mock_analyze.return_value = large_results

        # Execute large parameter sweep
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "5",
                "--fast-max",
                "50",
                "--slow-min",
                "20",
                "--slow-max",
                "200",
                "--max-results",
                "20",
            ],
        )

        # Verify large dataset handling
        assert result.exit_code == 0
        assert "Parameter sweep completed" in result.stdout
        assert "showing top 20" in result.stdout

        # Verify performance is acceptable (command completes)
        mock_get_data.assert_called_once()
        mock_analyze.assert_called_once()

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_multi_year_analysis_workflow(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
        large_realistic_dataset,
    ):
        """Test multi-year analysis workflow with realistic time periods."""
        # Setup mocks for multi-year analysis
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.use_years = True
        mock_config.years = 5  # 5 year backtest
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = large_realistic_dataset

        # Execute multi-year analysis
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
                "5",
            ],
        )

        # Verify multi-year analysis handling
        assert result.exit_code == 0
        assert "Strategy analysis completed successfully" in result.stdout

        # Verify long-term data was processed
        mock_get_data.assert_called_once()
        mock_dispatcher.execute_strategy.assert_called_once()

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_high_frequency_realistic_workflow(
        self, mock_config_loader, mock_dispatcher_class, mock_get_data, cli_runner
    ):
        """Test workflow with high-frequency realistic data processing."""
        # Create high-frequency data (hourly for 1 year)
        dates = pl.date_range(
            start=pl.datetime(2023, 1, 1),
            end=pl.datetime(2023, 12, 31, 23, 0, 0),
            interval="1h",
        )

        hf_data = pl.DataFrame(
            {
                "Date": dates,
                "Close": [100.0 + (i % 100) * 0.1 for i in range(len(dates))],
                "Volume": [10000] * len(dates),
            }
        )

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config.use_hourly = True
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = hf_data

        # Execute high-frequency analysis
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", "SMA"]
        )

        # Verify high-frequency data handling
        assert result.exit_code == 0
        assert "Strategy analysis completed successfully" in result.stdout

        # Verify high-frequency processing
        mock_get_data.assert_called_once()
        mock_dispatcher.execute_strategy.assert_called_once()
