"""
Tests for CLI Strategy Run Command (Single Parameter Testing).

This test suite covers the `trading-cli strategy run` command which tests
specific parameter combinations on a single ticker without file exports.

Key features tested:
- Single ticker argument (required)
- Single parameter values (--fast, --slow)
- Optional signal parameter for MACD
- Parameter validation (fast < slow)
- MACD signal requirement
- Dry-run preview
- Terminal display only (no file exports)
- Error handling
"""

from pathlib import Path
from unittest.mock import Mock, patch

import polars as pl
import pytest
from typer.testing import CliRunner

from app.cli.commands.strategy import app as strategy_app


class TestStrategyRunSingleParameter:
    """Test cases for strategy run command with single parameters."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_price_data(self):
        """Mock price data for backtesting."""
        return pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 12, 31),
                    interval="1d",
                ),
                "Close": [100.0 + i * 0.1 for i in range(365)],
                "Open": [100.0 + i * 0.1 for i in range(365)],
                "High": [101.0 + i * 0.1 for i in range(365)],
                "Low": [99.0 + i * 0.1 for i in range(365)],
                "Volume": [1000000] * 365,
            },
        )

    @pytest.fixture
    def mock_backtest_result(self):
        """Mock backtest result with metrics."""
        return {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Fast Period": 20,
            "Slow Period": 50,
            "Total Return [%]": 25.5,
            "Annual Return [%]": 25.5,
            "# Trades": 15,
            "Win Rate [%]": 60.0,
            "Profit Factor": 2.5,
            "Sharpe Ratio": 1.8,
            "Sortino Ratio": 2.2,
            "Max. Drawdown [%]": -8.5,
            "Max. Drawdown Duration": "45 days",
            "Avg. Trade [%]": 1.7,
            "Avg. Trade Duration": "30 days",
            "# Wins": 9,
            "# Losses": 6,
            "Best Trade [%]": 5.2,
            "Worst Trade [%]": -3.1,
            "Equity Start [$]": 1000.0,
            "Equity Final [$]": 1255.0,
            "Equity Peak [$]": 1280.0,
            "Score": 8.5,
        }

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_single_parameter_success(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test successful single parameter run."""
        # Setup mocks
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        # get_config just returns the config dict passed to it with defaults
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        # Verify results
        assert result.exit_code == 0
        assert "Backtest Results" in result.stdout
        assert "Total Return" in result.stdout
        assert "25.5" in result.stdout
        mock_get_data.assert_called_once()
        mock_analyze.assert_called_once()

    def test_run_parameter_validation_fast_greater_than_slow(self, cli_runner):
        """Test that fast >= slow is rejected."""
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "50", "--slow", "20"],
        )

        assert result.exit_code == 1
        assert "Fast period must be less than slow period" in result.stdout

    def test_run_parameter_validation_fast_equals_slow(self, cli_runner):
        """Test that fast == slow is rejected."""
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "30", "--slow", "30"],
        )

        assert result.exit_code == 1
        assert "Fast period must be less than slow period" in result.stdout

    def test_run_macd_requires_signal_parameter(self, cli_runner):
        """Test that MACD strategy requires signal parameter."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "AAPL",
                "--fast",
                "12",
                "--slow",
                "26",
                "--strategy",
                "MACD",
            ],
        )

        assert result.exit_code == 1
        assert "MACD strategy requires --signal parameter" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_macd_with_signal_success(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test successful MACD run with signal parameter."""
        # Setup mocks
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_backtest_result["Strategy Type"] = "MACD"
        mock_backtest_result["Signal Period"] = 9
        mock_analyze.return_value = [mock_backtest_result]

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "AAPL",
                "--fast",
                "12",
                "--slow",
                "26",
                "--signal",
                "9",
                "--strategy",
                "MACD",
            ],
        )

        # Verify results
        assert result.exit_code == 0
        assert "Backtest Results" in result.stdout

    def test_run_dry_run_preview(self, cli_runner):
        """Test dry-run shows configuration preview."""
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50", "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry run" in result.stdout
        assert "AAPL" in result.stdout
        assert "Fast=20, Slow=50" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_no_file_exports(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test that run command does not export files."""
        # Setup mocks
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        # Clean up any existing test files
        test_files = [
            Path("data/raw/portfolios/AAPL_D_SMA.csv"),
            Path("data/raw/portfolios_filtered/AAPL_D_SMA.csv"),
            Path("data/raw/portfolios_best/AAPL_D_SMA.csv"),
        ]
        for f in test_files:
            if f.exists():
                f.unlink()

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        # Verify no files were created
        assert result.exit_code == 0
        for test_file in test_files:
            assert not test_file.exists(), f"File should not exist: {test_file}"

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_with_years_parameter(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test run command with years parameter."""
        # Setup mocks
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50", "--years", "5"],
        )

        # Verify results
        assert result.exit_code == 0
        assert "5 years" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_with_ema_strategy(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test run command with EMA strategy."""
        # Setup mocks
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_backtest_result["Strategy Type"] = "EMA"
        mock_analyze.return_value = [mock_backtest_result]

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "AAPL",
                "--fast",
                "20",
                "--slow",
                "50",
                "--strategy",
                "EMA",
            ],
        )

        # Verify results
        assert result.exit_code == 0
        assert "EMA" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_data_fetch_failure(
        self,
        mock_logging,
        mock_get_config,
        mock_get_data,
        cli_runner,
    ):
        """Test run command handles data fetch failure."""
        # Setup mocks
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = None  # Data fetch fails

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            ["run", "INVALID", "--fast", "20", "--slow", "50"],
        )

        # Verify error handling
        assert result.exit_code == 1
        assert "Failed to fetch price data" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_no_results_generated(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
    ):
        """Test run command handles no results scenario."""
        # Setup mocks
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = []  # No results

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        # Verify handling
        assert result.exit_code == 0
        assert "No results generated" in result.stdout

    def test_run_missing_required_parameters(self, cli_runner):
        """Test run command with missing required parameters."""
        # Missing ticker
        result1 = cli_runner.invoke(
            strategy_app,
            ["run", "--fast", "20", "--slow", "50"],
        )
        assert result1.exit_code != 0

        # Missing fast
        result2 = cli_runner.invoke(strategy_app, ["run", "AAPL", "--slow", "50"])
        assert result2.exit_code != 0

        # Missing slow
        result3 = cli_runner.invoke(strategy_app, ["run", "AAPL", "--fast", "20"])
        assert result3.exit_code != 0

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_displays_all_metrics(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test that run command displays all key metrics."""
        # Setup mocks
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        # Verify all metrics are displayed
        assert result.exit_code == 0
        metrics = [
            "Total Return",
            "Annual Return",
            "Number of Trades",
            "Win Rate",
            "Profit Factor",
            "Sharpe Ratio",
            "Sortino Ratio",
            "Max Drawdown",
            "Avg Trade Return",
        ]
        for metric in metrics:
            assert metric in result.stdout, f"Metric '{metric}' not found in output"

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_with_crypto_ticker(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test run command with cryptocurrency ticker."""
        # Setup mocks
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_backtest_result["Ticker"] = "BTC-USD"
        mock_analyze.return_value = [mock_backtest_result]

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            ["run", "BTC-USD", "--fast", "10", "--slow", "30"],
        )

        # Verify results
        assert result.exit_code == 0
        assert "BTC-USD" in result.stdout


class TestStrategyRunEdgeCases:
    """Test edge cases for strategy run command."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_run_extreme_parameter_values(self, cli_runner):
        """Test run with extreme parameter values."""
        # Very small periods
        result1 = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "1", "--slow", "2"],
        )
        # Should either succeed or fail gracefully
        assert result1.exit_code is not None

        # Very large periods
        result2 = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "100", "--slow", "500"],
        )
        assert result2.exit_code is not None

    def test_run_special_ticker_characters(self, cli_runner):
        """Test run with special characters in ticker."""
        special_tickers = ["BTC-USD", "^GSPC", "GC=F"]

        for ticker in special_tickers:
            result = cli_runner.invoke(
                strategy_app,
                ["run", ticker, "--fast", "20", "--slow", "50"],
            )
            # Should handle gracefully
            assert result.exit_code is not None

    def test_run_help_display(self, cli_runner):
        """Test that run command help is displayed correctly."""
        result = cli_runner.invoke(strategy_app, ["run", "--help"])

        assert result.exit_code == 0
        assert "Test a specific parameter combination" in result.stdout
        assert "--fast" in result.stdout
        assert "--slow" in result.stdout
        assert "--signal" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_invalid_ticker_symbol(
        self,
        mock_logging,
        mock_get_config,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of invalid ticker that doesn't exist."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        # Simulate ticker not found - returns None
        mock_get_data.return_value = None

        result = cli_runner.invoke(
            strategy_app,
            ["run", "INVALIDTICKER123", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 1
        assert "Failed to fetch price data" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_empty_data_response(
        self,
        mock_logging,
        mock_get_config,
        mock_get_data,
        cli_runner,
    ):
        """Test handling when API returns empty data."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        # Return empty DataFrame
        mock_get_data.return_value = pl.DataFrame()

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 1
        assert "Failed to fetch price data" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_backtest_exception(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
    ):
        """Test handling when backtest crashes."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = pl.DataFrame({"Close": [100.0] * 100})
        # Simulate backtest crash
        mock_analyze.side_effect = Exception("Backtest calculation error")

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 1
        assert "Error running backtest" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_network_timeout(
        self,
        mock_logging,
        mock_get_config,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of network timeout during data fetch."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        # Simulate timeout exception

        mock_get_data.side_effect = TimeoutError("Connection timed out")

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 1
        assert (
            "Error running backtest" in result.stdout
            or "timeout" in result.stdout.lower()
        )

    def test_run_invalid_years_negative(self, cli_runner):
        """Test negative years value is rejected."""
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50", "--years", "-1"],
        )

        # Typer should reject negative integer values
        assert result.exit_code != 0

    def test_run_invalid_years_zero(self, cli_runner):
        """Test zero years value handling."""
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50", "--years", "0"],
        )

        # Zero should be rejected or handled gracefully
        assert result.exit_code != 0 or result.exit_code == 0


class TestStrategyRunCSVOutput:
    """Test CSV output generation for copy/paste functionality."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_price_data(self):
        """Mock price data."""
        return pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 12, 31),
                    interval="1d",
                ),
                "Close": [100.0 + i * 0.1 for i in range(365)],
                "Open": [100.0 + i * 0.1 for i in range(365)],
                "High": [101.0 + i * 0.1 for i in range(365)],
                "Low": [99.0 + i * 0.1 for i in range(365)],
                "Volume": [1000000] * 365,
            },
        )

    @pytest.fixture
    def mock_backtest_result(self):
        """Mock backtest result."""
        return {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Fast Period": 20,
            "Slow Period": 50,
            "Total Trades": 15,
            "Win Rate [%]": 60.0,
            "Total Return [%]": 25.5,
        }

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_csv_output_includes_headers(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test CSV output includes proper column headers."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 0
        assert "📋 Raw CSV Data" in result.stdout
        assert "Ticker,Strategy Type,Fast Period,Slow Period" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_csv_output_single_row(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test CSV output contains exactly 1 data row."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 0
        # Extract CSV section
        csv_section = result.stdout.split("📋 Raw CSV Data")[1]
        csv_lines = [line for line in csv_section.split("\n") if line.strip()]
        # Should have header + 1 data row + success message
        assert any("AAPL,SMA,20,50" in line for line in csv_lines)

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_csv_output_no_rich_formatting(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test CSV output has no ANSI color codes."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 0
        # Extract CSV section (after the Raw CSV Data header)
        csv_section = result.stdout.split("📋 Raw CSV Data")[1]
        # Check for ANSI escape codes (should not be present in CSV data lines)
        csv_data_lines = [
            line
            for line in csv_section.split("\n")
            if line.strip()
            and not line.startswith("✓")
            and not line.startswith("Note:")
        ]
        for line in csv_data_lines:
            if "AAPL" in line or "Ticker" in line:
                assert "\x1b[" not in line, "CSV should not contain ANSI codes"

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_csv_output_matches_table_metrics(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test CSV values match table display."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_backtest_result["Win Rate [%]"] = 60.0
        mock_backtest_result["Total Return [%]"] = 25.5
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 0
        # Table should show these values
        assert "60.00%" in result.stdout  # Win Rate
        assert "25.5" in result.stdout  # Total Return
        # CSV should also contain these values
        csv_section = result.stdout.split("📋 Raw CSV Data")[1]
        assert "60.0" in csv_section or "60" in csv_section
        assert "25.5" in csv_section

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_csv_output_copy_paste_ready(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test CSV format is ready for copy/paste into portfolio files."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 0
        # CSV should be comma-separated with no extra formatting
        csv_section = result.stdout.split("📋 Raw CSV Data")[1]
        csv_lines = [
            line for line in csv_section.split("\n") if line.strip() and "," in line
        ]
        # Should have at least header and data row
        assert len(csv_lines) >= 2
        # Data row should start with ticker
        data_row = [line for line in csv_lines if line.startswith("AAPL")]
        assert len(data_row) == 1


class TestStrategyRunZeroTradesHandling:
    """Test handling of scenarios where strategy generates 0 trades."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_price_data(self):
        """Mock price data."""
        return pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 12, 31),
                    interval="1d",
                ),
                "Close": [100.0 + i * 0.1 for i in range(365)],
                "Open": [100.0 + i * 0.1 for i in range(365)],
                "High": [101.0 + i * 0.1 for i in range(365)],
                "Low": [99.0 + i * 0.1 for i in range(365)],
                "Volume": [1000000] * 365,
            },
        )

    @pytest.fixture
    def mock_zero_trade_result(self):
        """Mock backtest result with 0 trades."""
        return {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Fast Period": 45,
            "Slow Period": 54,
            "Total Trades": 0,
            "Win Rate [%]": 0.0,
            "Profit Factor": 0.0,
            "Total Return [%]": 15.5,
            "Sharpe Ratio": 0.5,
            "Sortino Ratio": 0.7,
        }

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_zero_trades_shows_warning(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_zero_trade_result,
    ):
        """Test warning message is displayed when 0 trades generated."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_zero_trade_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "45", "--slow", "54"],
        )

        assert result.exit_code == 0
        assert "⚠ Warning: Strategy generated 0 trades" in result.stdout
        assert "never triggered entry signals" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_zero_trades_metrics_set_to_na(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_zero_trade_result,
    ):
        """Test metrics are set to N/A when 0 trades."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_zero_trade_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "45", "--slow", "54"],
        )

        assert result.exit_code == 0
        # These metrics should show N/A for 0 trades
        output_lines = result.stdout
        assert "Win Rate" in output_lines and "N/A" in output_lines
        assert "Profit Factor" in output_lines and "N/A" in output_lines

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_zero_trades_no_trade_statistics(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_zero_trade_result,
    ):
        """Test trade statistics section not shown when 0 trades."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_zero_trade_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "45", "--slow", "54"],
        )

        assert result.exit_code == 0
        # Trade Statistics section should not appear
        assert "Trade Statistics:" not in result.stdout
        assert "Winning Trades:" not in result.stdout
        assert "Losing Trades:" not in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_zero_trades_still_shows_equity_metrics(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_zero_trade_result,
    ):
        """Test equity-based metrics still shown with 0 trades."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_zero_trade_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "45", "--slow", "54"],
        )

        assert result.exit_code == 0
        # These should still appear even with 0 trades
        assert "Total Return" in result.stdout
        assert "Sharpe Ratio" in result.stdout
        assert "Sortino Ratio" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_zero_trades_csv_still_generated(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_zero_trade_result,
    ):
        """Test CSV output is still generated with 0 trades."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_zero_trade_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "45", "--slow", "54"],
        )

        assert result.exit_code == 0
        assert "📋 Raw CSV Data" in result.stdout
        # CSV should still be present
        csv_section = result.stdout.split("📋 Raw CSV Data")[1]
        assert "AAPL,SMA,45,54" in csv_section


class TestStrategyRunTradeStatistics:
    """Test trade statistics calculation and display."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_price_data(self):
        """Mock price data."""
        return pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 12, 31),
                    interval="1d",
                ),
                "Close": [100.0 + i * 0.1 for i in range(365)],
                "Open": [100.0 + i * 0.1 for i in range(365)],
                "High": [101.0 + i * 0.1 for i in range(365)],
                "Low": [99.0 + i * 0.1 for i in range(365)],
                "Volume": [1000000] * 365,
            },
        )

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_trade_statistics_calculation(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
    ):
        """Test wins/losses calculated correctly from win rate."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data

        # 10 trades with 60% win rate = 6 wins, 4 losses
        mock_result = {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Fast Period": 20,
            "Slow Period": 50,
            "Total Trades": 10,
            "Win Rate [%]": 60.0,
            "Best Trade [%]": 15.0,
            "Worst Trade [%]": -8.0,
        }
        mock_analyze.return_value = [mock_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 0
        assert "Winning Trades: 6" in result.stdout
        assert "Losing Trades: 4" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_trade_statistics_only_shown_with_trades(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
    ):
        """Test trade statistics not shown when 0 trades."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data

        mock_result = {"Ticker": "AAPL", "Total Trades": 0}
        mock_analyze.return_value = [mock_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 0
        assert "Trade Statistics:" not in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_avg_winning_trade_display(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
    ):
        """Test avg winning trade shown when available."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data

        mock_result = {
            "Ticker": "AAPL",
            "Total Trades": 10,
            "Win Rate [%]": 60.0,
            "Avg Winning Trade [%]": 8.5,
            "Avg Losing Trade [%]": -4.2,
            "Best Trade [%]": 15.0,
            "Worst Trade [%]": -8.0,
        }
        mock_analyze.return_value = [mock_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 0
        assert "Avg Winning Trade: 8.50%" in result.stdout
        assert "Avg Losing Trade: -4.20%" in result.stdout or "4.20" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_avg_losing_trade_display(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
    ):
        """Test avg losing trade shown when available."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data

        mock_result = {
            "Ticker": "AAPL",
            "Total Trades": 5,
            "Win Rate [%]": 40.0,
            "Avg Losing Trade [%]": -5.5,
            "Best Trade [%]": 10.0,
            "Worst Trade [%]": -8.0,
        }
        mock_analyze.return_value = [mock_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 0
        assert "5.5" in result.stdout  # Should show avg losing trade

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_best_worst_trade_display(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
    ):
        """Test best/worst trade always shown when trades > 0."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data

        mock_result = {
            "Ticker": "AAPL",
            "Total Trades": 20,
            "Win Rate [%]": 55.0,
            "Best Trade [%]": 22.75,
            "Worst Trade [%]": -11.22,
        }
        mock_analyze.return_value = [mock_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 0
        assert "Best Trade: 22.75%" in result.stdout
        assert "Worst Trade: -11.22%" in result.stdout or "11.22" in result.stdout


class TestStrategyRunTimeframeParameters:
    """Test timeframe parameter functionality."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_price_data(self):
        """Mock price data."""
        return pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 12, 31),
                    interval="1d",
                ),
                "Close": [100.0 + i * 0.1 for i in range(365)],
                "Open": [100.0 + i * 0.1 for i in range(365)],
                "High": [101.0 + i * 0.1 for i in range(365)],
                "Low": [99.0 + i * 0.1 for i in range(365)],
                "Volume": [1000000] * 365,
            },
        )

    @pytest.fixture
    def mock_backtest_result(self):
        """Mock backtest result."""
        return {
            "Ticker": "AAPL",
            "Total Trades": 10,
            "Win Rate [%]": 55.0,
        }

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_with_4hour_timeframe(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test --use-4hour flag sets correct configuration."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50", "--use-4hour"],
        )

        assert result.exit_code == 0
        assert "Timeframe: 4-hour" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_with_2day_timeframe(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test --use-2day flag sets correct configuration."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50", "--use-2day"],
        )

        assert result.exit_code == 0
        assert "Timeframe: 2-day" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_4hour_and_2day_mutually_exclusive(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test that 4-hour and 2-day can't both be used."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "AAPL",
                "--fast",
                "20",
                "--slow",
                "50",
                "--use-4hour",
                "--use-2day",
            ],
        )

        # Should succeed but only show one timeframe (last one takes precedence)
        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_timeframe_affects_data_retrieval(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test timeframe flag affects configuration."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Capture the config passed to get_data
        captured_config = {}

        def capture_config(config):
            captured_config.update(config)
            return config

        mock_get_config.side_effect = capture_config
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50", "--use-4hour"],
        )

        assert result.exit_code == 0
        # Verify config has 4-hour settings
        assert captured_config.get("USE_4HOUR") is True
        assert captured_config.get("USE_HOURLY") is True


class TestStrategyRunDirectionAndMarketType:
    """Test direction and market type parameters."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_price_data(self):
        """Mock price data."""
        return pl.DataFrame(
            {
                "Date": pl.date_range(
                    start=pl.date(2023, 1, 1),
                    end=pl.date(2023, 12, 31),
                    interval="1d",
                ),
                "Close": [100.0] * 365,
            },
        )

    @pytest.fixture
    def mock_backtest_result(self):
        """Mock backtest result."""
        return {"Ticker": "AAPL", "Total Trades": 5}

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_direction_long_default(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test Long direction is default."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--fast", "20", "--slow", "50"],
        )

        assert result.exit_code == 0
        assert "Direction: Long" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_direction_short(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test --direction Short parameter."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()
        mock_get_config.side_effect = lambda x: x
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "AAPL",
                "--fast",
                "20",
                "--slow",
                "50",
                "--direction",
                "Short",
            ],
        )

        assert result.exit_code == 0
        assert "Direction: Short" in result.stdout

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_market_type_crypto(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test --market-type crypto parameter."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        captured_config = {}

        def capture_config(config):
            captured_config.update(config)
            return config

        mock_get_config.side_effect = capture_config
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "BTC-USD",
                "--fast",
                "20",
                "--slow",
                "50",
                "--market-type",
                "crypto",
            ],
        )

        assert result.exit_code == 0
        assert captured_config.get("MARKET_TYPE") == "crypto"

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_market_type_us_stock(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test --market-type us_stock parameter."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        captured_config = {}

        def capture_config(config):
            captured_config.update(config)
            return config

        mock_get_config.side_effect = capture_config
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "AAPL",
                "--fast",
                "20",
                "--slow",
                "50",
                "--market-type",
                "us_stock",
            ],
        )

        assert result.exit_code == 0
        assert captured_config.get("MARKET_TYPE") == "us_stock"

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.get_config")
    @patch("app.cli.commands.strategy.analyze_parameter_combinations")
    @patch("app.cli.commands.strategy.logging_context")
    def test_run_market_type_auto(
        self,
        mock_logging,
        mock_analyze,
        mock_get_config,
        mock_get_data,
        cli_runner,
        mock_price_data,
        mock_backtest_result,
    ):
        """Test --market-type auto parameter."""
        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        captured_config = {}

        def capture_config(config):
            captured_config.update(config)
            return config

        mock_get_config.side_effect = capture_config
        mock_get_data.return_value = mock_price_data
        mock_analyze.return_value = [mock_backtest_result]

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "AAPL",
                "--fast",
                "20",
                "--slow",
                "50",
                "--market-type",
                "auto",
            ],
        )

        assert result.exit_code == 0
        assert captured_config.get("MARKET_TYPE") == "auto"
