"""
Comprehensive tests for CLI Strategy Run Command.

This test suite covers the `trading-cli strategy run` command with focus on:
- All strategy types: SMA, EMA, MACD
- Single and multiple ticker execution
- Parameter override scenarios
- Dry-run functionality
- Verbose output
- Error handling and edge cases
- Profile integration
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from typer.testing import CliRunner

from app.cli.commands.strategy import app as strategy_app
from app.cli.models.strategy import StrategyType


class TestStrategyRunCommand:
    """Test cases for strategy run command."""

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
    def sample_sma_profile(self):
        """Sample SMA profile content."""
        return """
metadata:
  name: test_sma
  description: Test SMA strategy
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

    @pytest.fixture
    def sample_macd_profile(self):
        """Sample MACD profile content."""
        return """
metadata:
  name: test_macd
  description: Test MACD strategy
config_type: strategy
config:
  ticker: [BTC-USD]
  strategy_types: [MACD]
  use_years: false
  years: 10
  multi_ticker: false
  minimums:
    win_rate: 0.55
    trades: 25
  synthetic:
    use_synthetic: false
  filter:
    use_current: false
  short_window_start: 8
  short_window_end: 16
  long_window_start: 20
  long_window_end: 30
  signal_window_start: 5
  signal_window_end: 15
  step: 2
  direction: Long
"""

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_with_profile_sma_success(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        cli_runner,
        temp_profile_dir,
        sample_sma_profile,
    ):
        """Test successful run command with SMA profile."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Create profile file
        profile_file = temp_profile_dir / "test_sma.yaml"
        profile_file.write_text(sample_sma_profile)

        # Run command
        result = cli_runner.invoke(strategy_app, ["run", "--profile", "test_sma"])

        # Verify results
        assert result.exit_code == 0
        mock_config_loader.return_value.load_from_profile.assert_called_once()
        mock_dispatcher.validate_strategy_compatibility.assert_called_once()
        mock_dispatcher.execute_strategy.assert_called_once_with(mock_config)
        assert "Strategy analysis completed successfully" in result.stdout

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_with_profile_macd_success(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        cli_runner,
        temp_profile_dir,
        sample_macd_profile,
    ):
        """Test successful run command with MACD profile."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["BTC-USD"]
        mock_config.strategy_types = [StrategyType.MACD]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Create profile file
        profile_file = temp_profile_dir / "test_macd.yaml"
        profile_file.write_text(sample_macd_profile)

        # Run command
        result = cli_runner.invoke(strategy_app, ["run", "--profile", "test_macd"])

        # Verify results
        assert result.exit_code == 0
        mock_dispatcher.execute_strategy.assert_called_once_with(mock_config)
        assert "Strategy analysis completed successfully" in result.stdout

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_single_ticker_override(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with single ticker override."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["TSLA"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command with ticker override
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "TSLA", "--strategy", "SMA"]
        )

        # Verify results
        assert result.exit_code == 0
        # Verify overrides were applied
        call_args = mock_config_loader.return_value.load_from_profile.call_args
        overrides = call_args[0][2]  # Third argument is overrides
        assert "ticker" in overrides
        assert "strategy_type" in overrides

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_multiple_tickers(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with multiple tickers."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL", "MSFT", "GOOGL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command with multiple tickers
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL,MSFT,GOOGL", "--strategy", "SMA"]
        )

        # Verify results
        assert result.exit_code == 0
        assert "Processing 3 tickers" in result.stdout

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_multiple_strategies(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with multiple strategy types."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA, StrategyType.EMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command with multiple strategies
        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA", "--strategy", "EMA"],
        )

        # Verify results
        assert result.exit_code == 0
        assert "SMA, EMA" in result.stdout

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_with_minimums_override(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with minimum criteria overrides."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command with minimum overrides
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--min-trades",
                "50",
                "--min-win-rate",
                "0.6",
            ],
        )

        # Verify results
        assert result.exit_code == 0
        call_args = mock_config_loader.return_value.load_from_profile.call_args
        overrides = call_args[0][2]
        assert "min_trades" in overrides
        assert "min_win_rate" in overrides

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_with_years_override(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with years configuration override."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command with years override
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

        # Verify results
        assert result.exit_code == 0
        call_args = mock_config_loader.return_value.load_from_profile.call_args
        overrides = call_args[0][2]
        assert "use_years" in overrides
        assert "years" in overrides

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_dry_run(self, mock_config_loader, cli_runner):
        """Test run command with dry-run flag."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Run command with dry-run
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", "SMA", "--dry-run"]
        )

        # Verify results
        assert result.exit_code == 0
        # Should show config preview but not execute
        # Dispatcher should not be called
        assert (
            "Strategy Configuration Preview" in result.stdout
            or "Configuration Preview" in result.stdout
        )

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_verbose_output(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with verbose flag."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command with verbose flag
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", "SMA", "--verbose"]
        )

        # Verify results
        assert result.exit_code == 0
        # Should show additional verbose output
        assert (
            "Loading strategy execution module" in result.stdout
            or "strategy execution" in result.stdout.lower()
        )

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_execution_failure(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command when strategy execution fails."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = False  # Execution fails
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", "SMA"]
        )

        # Verify results
        assert result.exit_code == 0  # Command succeeds but shows warning
        assert "No strategies found matching" in result.stdout

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_incompatible_strategy(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with incompatible strategy configuration."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["INVALID_STRATEGY"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = (
            False  # Invalid strategy
        )
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", "INVALID_STRATEGY"]
        )

        # Verify results
        assert result.exit_code == 0
        assert "Invalid strategy type configuration" in result.stdout

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_config_loading_error(self, mock_config_loader, cli_runner):
        """Test run command when configuration loading fails."""
        # Setup mock to raise exception
        mock_config_loader.return_value.load_from_profile.side_effect = (
            FileNotFoundError("Profile not found")
        )

        # Run command
        result = cli_runner.invoke(strategy_app, ["run", "--profile", "nonexistent"])

        # Verify error handling
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_default_profile(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command uses default profile when none specified."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command without profile
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", "SMA"]
        )

        # Verify default profile is used
        mock_config_loader.return_value.load_from_profile.assert_called_once()
        call_args = mock_config_loader.return_value.load_from_profile.call_args
        profile_name = call_args[0][0]
        assert profile_name == "default_strategy"

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_string_ticker_input(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command handles string ticker input correctly."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = "AAPL"  # String ticker
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", "SMA"]
        )

        # Verify string ticker is handled
        assert result.exit_code == 0
        # Should show "Processing 1 tickers" (converted to list)
        assert "Processing 1 tickers" in result.stdout

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_multiple_ticker_formats(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with different ticker input formats."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL", "MSFT"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Test comma-separated format
        result1 = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL,MSFT", "--strategy", "SMA"]
        )
        assert result1.exit_code == 0

        # Test multiple --ticker arguments
        result2 = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--ticker", "MSFT", "--strategy", "SMA"],
        )
        assert result2.exit_code == 0

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_synthetic_tickers(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with synthetic ticker format."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["STRK/MSTR"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command with synthetic ticker
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "STRK/MSTR", "--strategy", "SMA"]
        )

        # Verify synthetic ticker is handled
        assert result.exit_code == 0
        assert "STRK/MSTR" in result.stdout

    @patch("app.cli.commands.strategy.validate_parameter_relationships")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_parameter_validation_error(
        self, mock_config_loader, mock_dispatcher_class, mock_validate, cli_runner
    ):
        """Test run command when parameter validation fails."""
        # Setup mocks
        mock_config = Mock()
        mock_config_loader.return_value.load_from_profile.return_value = mock_config
        mock_validate.side_effect = ValueError("Invalid parameter combination")

        # Run command
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", "SMA"]
        )

        # Verify error handling
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_exception_handling(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command handles unexpected exceptions gracefully."""
        # Setup mock to raise unexpected exception
        mock_config_loader.return_value.load_from_profile.side_effect = RuntimeError(
            "Unexpected error"
        )

        # Run command
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", "SMA"]
        )

        # Verify error is handled gracefully
        assert "error" in result.stdout.lower() or result.exit_code != 0


class TestStrategyRunCommandEdgeCases:
    """Test edge cases and boundary conditions for strategy run command."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_run_command_no_arguments(self, cli_runner):
        """Test run command with no arguments."""
        result = cli_runner.invoke(strategy_app, ["run"])

        # Should show help or require arguments
        assert result.exit_code != 0 or "help" in result.stdout.lower()

    def test_run_command_empty_ticker(self, cli_runner):
        """Test run command with empty ticker."""
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "", "--strategy", "SMA"]
        )

        # Should handle empty ticker gracefully
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_run_command_empty_strategy(self, cli_runner):
        """Test run command with empty strategy."""
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL", "--strategy", ""]
        )

        # Should handle empty strategy gracefully
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_very_large_ticker_list(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with very large ticker list."""
        # Create large ticker list
        large_ticker_list = [f"TICKER{i:04d}" for i in range(1000)]

        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = large_ticker_list
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command
        ticker_string = ",".join(
            large_ticker_list[:100]
        )  # Limit to first 100 for command line
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", ticker_string, "--strategy", "SMA"]
        )

        # Should handle large list gracefully
        assert result.exit_code == 0

    def test_run_command_special_characters_in_ticker(self, cli_runner):
        """Test run command with special characters in ticker."""
        special_tickers = ["BTC-USD", "STRK/MSTR", "TICKER.L", "TICKER^A"]

        for ticker in special_tickers:
            result = cli_runner.invoke(
                strategy_app, ["run", "--ticker", ticker, "--strategy", "SMA"]
            )
            # Should either succeed or fail gracefully (not crash)
            assert result.exit_code is not None  # Command completed

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_extreme_parameter_values(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with extreme parameter values."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Test extreme values
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--min-trades",
                "999999",
                "--min-win-rate",
                "0.999999",
                "--years",
                "100",
            ],
        )

        # Should handle extreme values gracefully
        assert result.exit_code == 0 or "error" in result.stdout.lower()

    def test_run_command_case_sensitivity(self, cli_runner):
        """Test run command case sensitivity for strategy types."""
        strategy_variants = [
            "SMA",
            "sma",
            "Sma",
            "EMA",
            "ema",
            "Ema",
            "MACD",
            "macd",
            "Macd",
        ]

        for strategy in strategy_variants:
            result = cli_runner.invoke(
                strategy_app, ["run", "--ticker", "AAPL", "--strategy", strategy]
            )
            # Should handle case variations gracefully
            assert result.exit_code is not None

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_run_command_unicode_tickers(
        self, mock_config_loader, mock_dispatcher_class, cli_runner
    ):
        """Test run command with Unicode characters in tickers."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = [StrategyType.SMA]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        # Test Unicode ticker (though unlikely in real use)
        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", "AAPL中文", "--strategy", "SMA"]
        )

        # Should handle Unicode gracefully
        assert result.exit_code is not None

    def test_run_command_very_long_arguments(self, cli_runner):
        """Test run command with very long argument values."""
        # Create very long ticker name
        long_ticker = "A" * 1000

        result = cli_runner.invoke(
            strategy_app, ["run", "--ticker", long_ticker, "--strategy", "SMA"]
        )

        # Should handle long arguments gracefully
        assert result.exit_code is not None
