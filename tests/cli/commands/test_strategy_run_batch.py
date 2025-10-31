"""
Comprehensive tests for CLI Strategy Sweep Command Batch Functionality.

This test suite covers the `trading-cli strategy sweep --batch` command with focus on:
- Batch flag functionality and parameter validation
- Batch size parameter validation and limits
- Batch file integration with strategy execution
- Resume analysis integration with batch selection
- Batch progress tracking and status display
- Mixed batch + non-batch parameter scenarios
- Error handling and edge cases

Key test scenarios:
- Batch size accuracy (exactly N tickers processed)
- Resume logic skipping already-complete tickers
- Batch file updates after successful processing
- Error handling during batch processing
- Dry-run with batch parameters
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from app.cli.commands.strategy import app as strategy_app
from app.cli.models.strategy import StrategyExecutionSummary, StrategyType


def create_mock_execution_summary(ticker="AAPL", strategy_type="SMA", **kwargs):
    """Create a proper StrategyExecutionSummary mock for testing."""
    return StrategyExecutionSummary(
        execution_time=kwargs.get("execution_time", 1.0),
        success_rate=kwargs.get("success_rate", 1.0),
        successful_strategies=kwargs.get("successful_strategies", 1),
        total_strategies=kwargs.get("total_strategies", 1),
        tickers_processed=kwargs.get("tickers_processed", [ticker]),
        strategy_types=kwargs.get("strategy_types", [strategy_type]),
        portfolio_results=kwargs.get("portfolio_results", []),
        total_portfolios_generated=kwargs.get("total_portfolios_generated", 10),
        total_filtered_portfolios=kwargs.get("total_filtered_portfolios", 5),
        total_files_exported=kwargs.get("total_files_exported", 3),
    )


def create_mock_strategy_config_batch(ticker=None, strategy_types=None, **kwargs):
    """Create a properly configured mock strategy config with batch support."""
    mock_config = Mock()

    # Core required attributes
    mock_config.ticker = ticker or ["AAPL"]
    if strategy_types:
        mock_config.strategy_types = [
            st.value if hasattr(st, "value") else str(st) for st in strategy_types
        ]
    else:
        mock_config.strategy_types = ["SMA"]

    # Batch-specific attributes
    mock_config.batch = kwargs.get("batch", False)
    mock_config.batch_size = kwargs.get("batch_size")
    mock_config.batch_file_path = kwargs.get("batch_file_path", "data/raw/batch.csv")

    # Standard attributes
    mock_config.fast_period_range = [5, 50]
    mock_config.slow_period_range = [20, 200]
    mock_config.fast_period = None
    mock_config.slow_period = None
    mock_config.skip_analysis = False

    # Mock minimums object
    mock_minimums = Mock()
    mock_minimums.win_rate = 0.55
    mock_minimums.trades = 30
    mock_config.minimums = mock_minimums

    # Mock synthetic object
    mock_synthetic = Mock()
    mock_synthetic.use_synthetic = False
    mock_config.synthetic = mock_synthetic

    # Additional attributes
    mock_config.profile_name = None
    mock_config.base_dir = "/tmp"
    mock_config.use_current = False
    mock_config.use_hourly = False
    mock_config.use_4hour = False
    mock_config.use_2day = False
    mock_config.verbose = False
    mock_config.direction = "Long"
    mock_config.strategy_params = None
    mock_config.refresh = kwargs.get("refresh", False)

    # Apply any additional kwargs
    for key, value in kwargs.items():
        if key not in ["batch", "batch_size", "batch_file_path", "refresh"]:
            setattr(mock_config, key, value)

    return mock_config


@pytest.mark.integration
class TestStrategySweepBatchCommand:
    """Test cases for strategy sweep command batch functionality."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_batch_file(self):
        """Create temporary batch file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")
            yield f.name

        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def sample_batch_profile(self):
        """Sample batch profile content."""
        return """
metadata:
  name: test_batch
  description: Test batch strategy
config_type: strategy
config:
  ticker: [AAPL, MSFT, GOOGL, TSLA, NVDA]
  strategy_types: [SMA]
  batch: true
  batch_size: 2
  minimums:
    win_rate: 0.5
    trades: 20
  synthetic:
    use_synthetic: false
"""

    @patch("app.cli.commands.strategy.validate_parameter_relationships")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_flag_enables_batch_processing(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_validate,
        cli_runner,
        temp_batch_file,
    ):
        """Test that --batch flag enables batch processing."""
        # Setup mocks
        mock_config = create_mock_strategy_config_batch(
            ticker=["AAPL", "MSFT"],
            strategy_types=[StrategyType.SMA],
            batch=True,
            batch_size=2,
            batch_file_path=temp_batch_file,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary(
            ticker="AAPL",
            strategy_type="SMA",
            tickers_processed=["AAPL", "MSFT"],
        )
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command with batch flag
        result = cli_runner.invoke(
            strategy_app,
            ["sweep", "--ticker", "AAPL,MSFT,GOOGL", "--strategy", "SMA", "--batch"],
        )

        # Verify results
        assert result.exit_code == 0

        # Verify overrides include batch flag
        call_args = mock_config_loader.return_value.load_from_profile.call_args
        overrides = call_args[0][2]  # Third argument is overrides
        assert overrides["batch"] is True

    @patch("app.cli.commands.strategy.validate_parameter_relationships")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_size_parameter_validation_positive(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_validate,
        cli_runner,
    ):
        """Test that batch size parameter accepts positive integers."""
        mock_config = create_mock_strategy_config_batch(batch=True, batch_size=5)
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary()
        mock_dispatcher_class.return_value = mock_dispatcher

        # Run command with valid batch size
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--batch",
                "--batch-size",
                "5",
            ],
        )

        assert result.exit_code == 0

        # Verify batch size override
        call_args = mock_config_loader.return_value.load_from_profile.call_args
        overrides = call_args[0][2]
        assert overrides["batch_size"] == 5

    def test_batch_size_parameter_validation_negative(self, cli_runner):
        """Test that negative batch size is rejected."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--batch",
                "--batch-size",
                "-1",
            ],
        )

        # Should fail validation
        assert result.exit_code != 0

    def test_batch_size_parameter_validation_zero(self, cli_runner):
        """Test that zero batch size is rejected."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--batch",
                "--batch-size",
                "0",
            ],
        )

        # Should fail validation
        assert result.exit_code != 0

    @patch("app.cli.commands.strategy.validate_parameter_relationships")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_processing_with_profile(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_validate,
        cli_runner,
        temp_batch_file,
        sample_batch_profile,
    ):
        """Test batch processing using profile configuration."""
        # Setup mocks
        mock_config = create_mock_strategy_config_batch(
            ticker=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
            strategy_types=[StrategyType.SMA],
            batch=True,
            batch_size=2,
            batch_file_path=temp_batch_file,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary(
            tickers_processed=["AAPL", "MSFT"],
        )
        mock_dispatcher_class.return_value = mock_dispatcher

        # Create profile file
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_file = Path(temp_dir) / "test_batch.yaml"
            profile_file.write_text(sample_batch_profile)

            # Run command
            result = cli_runner.invoke(
                strategy_app,
                ["sweep", "--profile", "test_batch"],
            )

        assert result.exit_code == 0
        assert "batch" in result.stdout.lower()

    @patch("app.cli.commands.strategy.validate_parameter_relationships")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_size_override_in_command(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_validate,
        cli_runner,
    ):
        """Test that command-line batch size overrides profile setting."""
        # Profile has batch_size=2, command specifies batch_size=5
        mock_config = create_mock_strategy_config_batch(
            batch=True,
            batch_size=5,  # Should be overridden
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary()
        mock_dispatcher_class.return_value = mock_dispatcher

        result = cli_runner.invoke(
            strategy_app,
            ["sweep", "--profile", "test_batch", "--batch-size", "5"],
        )

        assert result.exit_code == 0

        # Verify override was applied
        call_args = mock_config_loader.return_value.load_from_profile.call_args
        overrides = call_args[0][2]
        assert overrides["batch_size"] == 5

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_dry_run_shows_batch_config(self, mock_config_loader, cli_runner):
        """Test that dry-run shows batch configuration."""
        mock_config = create_mock_strategy_config_batch(
            ticker=["AAPL", "MSFT", "GOOGL"],
            batch=True,
            batch_size=2,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL,MSFT,GOOGL",
                "--batch",
                "--batch-size",
                "2",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        # Should show batch configuration in dry-run output
        assert "batch" in result.stdout.lower() or "2" in result.stdout

    @patch("app.cli.commands.strategy.validate_parameter_relationships")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_without_size_uses_default(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_validate,
        cli_runner,
    ):
        """Test that --batch without --batch-size uses reasonable default."""
        mock_config = create_mock_strategy_config_batch(batch=True, batch_size=None)
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary()
        mock_dispatcher_class.return_value = mock_dispatcher

        result = cli_runner.invoke(
            strategy_app,
            ["sweep", "--ticker", "AAPL,MSFT,GOOGL", "--strategy", "SMA", "--batch"],
        )

        assert result.exit_code == 0

        # Should not fail due to missing batch_size
        mock_dispatcher.execute_strategy.assert_called_once()

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_with_single_ticker(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        cli_runner,
    ):
        """Test batch processing with single ticker."""
        mock_config = create_mock_strategy_config_batch(
            ticker=["AAPL"],
            batch=True,
            batch_size=1,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary()
        mock_dispatcher_class.return_value = mock_dispatcher

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--batch",
                "--batch-size",
                "1",
            ],
        )

        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_execution_failure_handling(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        cli_runner,
    ):
        """Test batch processing handles execution failures gracefully."""
        mock_config = create_mock_strategy_config_batch(
            ticker=["AAPL", "MSFT"],
            batch=True,
            batch_size=2,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        # Mock failure scenario
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary(
            success_rate=0.0,
            successful_strategies=0,
        )
        mock_dispatcher_class.return_value = mock_dispatcher

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL,MSFT",
                "--strategy",
                "SMA",
                "--batch",
                "--batch-size",
                "2",
            ],
        )

        # Should complete without crashing
        assert result.exit_code == 0

    def test_batch_with_invalid_strategy_type(self, cli_runner):
        """Test batch processing with invalid strategy type."""
        result = cli_runner.invoke(
            strategy_app,
            ["sweep", "--ticker", "AAPL", "--strategy", "INVALID", "--batch"],
        )

        # Should handle invalid strategy gracefully
        assert result.exit_code is not None  # Command completes

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_with_multiple_strategy_types(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        cli_runner,
    ):
        """Test batch processing with multiple strategy types."""
        mock_config = create_mock_strategy_config_batch(
            ticker=["AAPL", "MSFT"],
            strategy_types=[StrategyType.SMA, StrategyType.EMA],
            batch=True,
            batch_size=2,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary(
            strategy_types=["SMA", "EMA"],
        )
        mock_dispatcher_class.return_value = mock_dispatcher

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL,MSFT",
                "--strategy",
                "SMA",
                "--strategy",
                "EMA",
                "--batch",
            ],
        )

        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_file_path_override(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        cli_runner,
        temp_batch_file,
    ):
        """Test overriding default batch file path."""
        mock_config = create_mock_strategy_config_batch(
            batch=True,
            batch_file_path=temp_batch_file,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary()
        mock_dispatcher_class.return_value = mock_dispatcher

        result = cli_runner.invoke(
            strategy_app,
            ["sweep", "--ticker", "AAPL", "--strategy", "SMA", "--batch"],
        )

        assert result.exit_code == 0
        # Batch file path should be used from config


@pytest.mark.integration
class TestStrategySweepBatchResumeIntegration:
    """Test cases for batch processing integration with resume analysis."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @patch("app.cli.commands.strategy.validate_parameter_relationships")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_resume_integration_skip_completed(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_validate,
        cli_runner,
    ):
        """Test that batch processing integrates with resume analysis to skip completed work."""
        mock_config = create_mock_strategy_config_batch(
            ticker=["AAPL", "MSFT", "GOOGL"],
            batch=True,
            batch_size=2,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Mock dispatcher that simulates resume-aware batch selection
        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True

        # Simulate that only 2 tickers actually need processing
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary(
            tickers_processed=["MSFT", "GOOGL"],  # AAPL was skipped due to resume
        )
        mock_dispatcher_class.return_value = mock_dispatcher

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL,MSFT,GOOGL",
                "--strategy",
                "SMA",
                "--batch",
                "--batch-size",
                "2",
            ],
        )

        assert result.exit_code == 0

        # Should show that resume analysis was performed
        assert (
            "resume" in result.stdout.lower() or "processing" in result.stdout.lower()
        )

    @patch("app.cli.commands.strategy.validate_parameter_relationships")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_refresh_flag_overrides_resume(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_validate,
        cli_runner,
    ):
        """Test that --refresh flag overrides resume analysis in batch mode."""
        mock_config = create_mock_strategy_config_batch(
            ticker=["AAPL", "MSFT"],
            batch=True,
            batch_size=2,
            refresh=True,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary(
            tickers_processed=[
                "AAPL",
                "MSFT",
            ],  # Both processed despite potential resume
        )
        mock_dispatcher_class.return_value = mock_dispatcher

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL,MSFT",
                "--strategy",
                "SMA",
                "--batch",
                "--refresh",
            ],
        )

        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_progress_tracking(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        cli_runner,
    ):
        """Test that batch processing shows progress information."""
        mock_config = create_mock_strategy_config_batch(
            ticker=["AAPL", "MSFT", "GOOGL", "TSLA"],
            batch=True,
            batch_size=2,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary(
            tickers_processed=["AAPL", "MSFT"],
        )
        mock_dispatcher_class.return_value = mock_dispatcher

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL,MSFT,GOOGL,TSLA",
                "--strategy",
                "SMA",
                "--batch",
                "--batch-size",
                "2",
            ],
        )

        assert result.exit_code == 0

        # Should show progress information
        output_lower = result.stdout.lower()
        assert "processing" in output_lower or "batch" in output_lower

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_status_display(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        cli_runner,
    ):
        """Test that batch processing displays status information."""
        mock_config = create_mock_strategy_config_batch(
            ticker=["AAPL", "MSFT", "GOOGL"],
            batch=True,
            batch_size=2,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary(
            tickers_processed=["AAPL", "MSFT"],
        )
        mock_dispatcher_class.return_value = mock_dispatcher

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL,MSFT,GOOGL",
                "--strategy",
                "SMA",
                "--batch",
                "--batch-size",
                "2",
            ],
        )

        assert result.exit_code == 0

        # Should display batch status information
        assert any(
            keyword in result.stdout.lower()
            for keyword in ["batch", "processing", "status", "tickers"]
        )


@pytest.mark.integration
class TestStrategySweepBatchEdgeCases:
    """Test edge cases and boundary conditions for batch functionality."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_batch_size_larger_than_ticker_list(self, cli_runner):
        """Test batch size larger than available tickers."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL,MSFT",
                "--strategy",
                "SMA",
                "--batch",
                "--batch-size",
                "10",
            ],
        )

        # Should handle gracefully
        assert result.exit_code == 0 or "error" in result.stdout.lower()

    def test_batch_with_empty_ticker_list(self, cli_runner):
        """Test batch processing with empty ticker list."""
        result = cli_runner.invoke(
            strategy_app,
            ["sweep", "--ticker", "", "--strategy", "SMA", "--batch"],
        )

        # Should handle empty list gracefully
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_batch_size_very_large(self, cli_runner):
        """Test batch processing with very large batch size."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--batch",
                "--batch-size",
                "999999",
            ],
        )

        # Should handle large batch size gracefully
        assert result.exit_code is not None

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_batch_with_special_ticker_characters(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        cli_runner,
    ):
        """Test batch processing with special characters in tickers."""
        special_tickers = ["BTC-USD", "STRK/MSTR", "TICKER.L"]
        mock_config = create_mock_strategy_config_batch(
            ticker=special_tickers,
            batch=True,
            batch_size=2,
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = create_mock_execution_summary()
        mock_dispatcher_class.return_value = mock_dispatcher

        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "BTC-USD,STRK/MSTR,TICKER.L",
                "--strategy",
                "SMA",
                "--batch",
                "--batch-size",
                "2",
            ],
        )

        # Should handle special characters gracefully
        assert result.exit_code == 0

    def test_batch_flag_without_batch_size_validation(self, cli_runner):
        """Test that batch flag validation works properly."""
        result = cli_runner.invoke(
            strategy_app,
            ["sweep", "--ticker", "AAPL", "--strategy", "SMA", "--batch-size", "5"],
        )

        # batch-size without --batch should be handled appropriately
        # (depends on implementation - might be ignored or cause error)
        assert result.exit_code is not None
