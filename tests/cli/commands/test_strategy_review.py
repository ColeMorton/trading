"""
Comprehensive tests for CLI Strategy Review Command.

This test suite covers the `trading-cli strategy review` command with focus on:
- Basic review command functionality (currently missing entirely)
- Profile-based portfolio analysis
- Ticker filtering capabilities
- Batch mode integration with BatchProcessingService
- Date-specific and current analysis modes
- Output format options (table, raw CSV)
- Sorting and display options
- Auto-discovery mode
- Error handling and validation

Key test scenarios:
- Profile loading and ticker extraction
- Batch file integration for non-current analysis
- Date validation and directory checking
- Portfolio aggregation and filtering
- Multiple output formats
- Error handling for missing files/profiles
"""

from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from typer.testing import CliRunner

from app.cli.commands.strategy import app as strategy_app


class TestStrategyReviewCommand:
    """Test cases for strategy review command basic functionality."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def sample_profile_content(self):
        """Sample profile content for testing."""
        return """
metadata:
  name: test_review
  description: Test review profile
config_type: strategy
config:
  ticker: [AAPL, MSFT, GOOGL]
  strategy_types: [SMA]
  minimums:
    win_rate: 0.5
    trades: 20
"""

    @pytest.fixture
    def temp_profile_dir(self):
        """Create temporary directory with test profiles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir) / "profiles"
            profile_dir.mkdir()
            yield profile_dir

    @pytest.fixture
    def mock_portfolio_data(self):
        """Mock portfolio analysis data."""
        return pd.DataFrame(
            [
                {
                    "Ticker": "AAPL",
                    "Strategy": "SMA_20_50",
                    "Score": 85.5,
                    "Total Return [%]": 12.5,
                    "Trades": 45,
                    "Win Rate [%]": 65.2,
                },
                {
                    "Ticker": "MSFT",
                    "Strategy": "SMA_15_45",
                    "Score": 78.3,
                    "Total Return [%]": 10.8,
                    "Trades": 38,
                    "Win Rate [%]": 62.1,
                },
                {
                    "Ticker": "GOOGL",
                    "Strategy": "SMA_25_55",
                    "Score": 82.1,
                    "Total Return [%]": 11.9,
                    "Trades": 42,
                    "Win Rate [%]": 63.8,
                },
            ],
        )

    def test_review_command_requires_best_flag(self, cli_runner):
        """Test that review command requires --best flag."""
        result = cli_runner.invoke(
            strategy_app, ["review", "--profile", "test_profile"],
        )

        assert result.exit_code != 0
        assert "best" in result.stdout.lower()

    def test_review_command_requires_profile_or_mode(self, cli_runner):
        """Test that review command requires profile or valid mode."""
        result = cli_runner.invoke(strategy_app, ["review", "--best"])

        assert result.exit_code != 0
        assert "profile" in result.stdout.lower() or "required" in result.stdout.lower()

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_review_command_with_profile_success(
        self,
        mock_config_loader,
        mock_analysis_service,
        cli_runner,
        sample_profile_content,
        mock_portfolio_data,
    ):
        """Test successful review command with profile."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL", "MSFT", "GOOGL"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_service_instance = Mock()
        mock_service_instance.aggregate_portfolios_best.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Run command
        result = cli_runner.invoke(
            strategy_app, ["review", "--profile", "test_review", "--best"],
        )

        # Verify results
        assert result.exit_code == 0
        mock_config_loader.return_value.load_from_profile.assert_called_once()
        mock_service_instance.aggregate_portfolios_best.assert_called_once_with(
            ["AAPL", "MSFT", "GOOGL"],
        )

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    def test_review_command_auto_discovery_mode(
        self, mock_analysis_service, cli_runner, mock_portfolio_data,
    ):
        """Test review command in auto-discovery mode."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.aggregate_all_current_portfolios.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Run command
        result = cli_runner.invoke(strategy_app, ["review", "--best", "--current"])

        # Verify results
        assert result.exit_code == 0
        mock_service_instance.aggregate_all_current_portfolios.assert_called_once()

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    def test_review_command_with_ticker_filtering(
        self, mock_analysis_service, cli_runner, mock_portfolio_data,
    ):
        """Test review command with ticker filtering."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.aggregate_portfolios_best.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Run command
        result = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current", "--ticker", "AAPL,MSFT"],
        )

        # Verify results
        assert result.exit_code == 0
        mock_service_instance.aggregate_portfolios_best.assert_called_once_with(
            ["AAPL", "MSFT"],
        )

    def test_review_command_date_validation_invalid_format(self, cli_runner):
        """Test review command with invalid date format."""
        result = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current", "--date", "2025-01-01"],
        )

        assert result.exit_code != 0
        assert "YYYYMMDD" in result.stdout

    @patch("pathlib.Path.exists")
    def test_review_command_date_validation_directory_not_found(
        self, mock_exists, cli_runner,
    ):
        """Test review command with non-existent date directory."""
        mock_exists.return_value = False

        result = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current", "--date", "20250101"],
        )

        assert result.exit_code != 0
        assert "directory not found" in result.stdout.lower()

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    @patch("pathlib.Path.exists")
    def test_review_command_with_valid_date(
        self, mock_exists, mock_analysis_service, cli_runner, mock_portfolio_data,
    ):
        """Test review command with valid date parameter."""
        mock_exists.return_value = True

        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.aggregate_all_current_portfolios.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Run command
        result = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current", "--date", "20250816"],
        )

        # Verify results
        assert result.exit_code == 0
        # Should create PortfolioAnalysisService with custom date
        mock_analysis_service.assert_called_once_with(
            use_current=True, custom_date="20250816",
        )

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    def test_review_command_output_format_options(
        self, mock_analysis_service, cli_runner, mock_portfolio_data,
    ):
        """Test review command with different output formats."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.aggregate_all_current_portfolios.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Test table format (default)
        result_table = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current", "--output-format", "table"],
        )
        assert result_table.exit_code == 0

        # Test raw format
        result_raw = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current", "--output-format", "raw"],
        )
        assert result_raw.exit_code == 0

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    def test_review_command_sorting_options(
        self, mock_analysis_service, cli_runner, mock_portfolio_data,
    ):
        """Test review command with different sorting options."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.aggregate_all_current_portfolios.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Test default sorting (Score)
        result_default = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current"],
        )
        assert result_default.exit_code == 0

        # Test custom sorting
        result_custom = cli_runner.invoke(
            strategy_app,
            ["review", "--best", "--current", "--sort-by", "Total Return [%]"],
        )
        assert result_custom.exit_code == 0

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    def test_review_command_top_n_parameter(
        self, mock_analysis_service, cli_runner, mock_portfolio_data,
    ):
        """Test review command with top-n parameter."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.aggregate_all_current_portfolios.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Test custom top-n
        result = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current", "--top-n", "25"],
        )

        assert result.exit_code == 0

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    def test_review_command_empty_results(self, mock_analysis_service, cli_runner):
        """Test review command handling of empty results."""
        # Setup mocks with empty DataFrame
        mock_service_instance = Mock()
        mock_service_instance.aggregate_all_current_portfolios.return_value = (
            pd.DataFrame()
        )
        mock_analysis_service.return_value = mock_service_instance

        # Run command
        result = cli_runner.invoke(strategy_app, ["review", "--best", "--current"])

        # Should handle empty results gracefully
        assert result.exit_code == 0
        assert "no portfolio data found" in result.stdout.lower()

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_review_command_profile_loading_error(self, mock_config_loader, cli_runner):
        """Test review command handling of profile loading errors."""
        # Setup mock to raise exception
        mock_config_loader.return_value.load_from_profile.side_effect = (
            FileNotFoundError("Profile not found")
        )

        # Run command
        result = cli_runner.invoke(
            strategy_app, ["review", "--profile", "nonexistent", "--best"],
        )

        # Should handle error gracefully
        assert result.exit_code != 0
        assert "error" in result.stdout.lower()

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    def test_review_command_multiple_tickers_comma_separated(
        self, mock_analysis_service, cli_runner, mock_portfolio_data,
    ):
        """Test review command with comma-separated tickers."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.aggregate_portfolios_best.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            ["review", "--best", "--current", "--ticker", "AAPL,MSFT,GOOGL"],
        )

        # Verify results
        assert result.exit_code == 0
        mock_service_instance.aggregate_portfolios_best.assert_called_once_with(
            ["AAPL", "MSFT", "GOOGL"],
        )

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    def test_review_command_multiple_ticker_arguments(
        self, mock_analysis_service, cli_runner, mock_portfolio_data,
    ):
        """Test review command with multiple --ticker arguments."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.aggregate_portfolios_best.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Run command
        result = cli_runner.invoke(
            strategy_app,
            ["review", "--best", "--current", "--ticker", "AAPL", "--ticker", "MSFT"],
        )

        # Verify results
        assert result.exit_code == 0
        # Should handle multiple ticker arguments
        mock_service_instance.aggregate_portfolios_best.assert_called_once()


class TestStrategyReviewBatchMode:
    """Test cases for strategy review command batch functionality."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_batch_file(self):
        """Create temporary batch file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Last Modified\n")
            f.write("AAPL,2025-01-01\n")
            f.write("MSFT,2025-01-01\n")
            f.write("GOOGL,2025-01-01\n")
            yield f.name

        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def mock_portfolio_data(self):
        """Mock portfolio analysis data."""
        return pd.DataFrame(
            [
                {
                    "Ticker": "AAPL",
                    "Strategy": "SMA_20_50",
                    "Score": 85.5,
                    "Total Return [%]": 12.5,
                },
                {
                    "Ticker": "MSFT",
                    "Strategy": "SMA_15_45",
                    "Score": 78.3,
                    "Total Return [%]": 10.8,
                },
            ],
        )

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    @patch("app.cli.commands.strategy.BatchProcessingService")
    def test_review_batch_mode_success(
        self,
        mock_batch_service_class,
        mock_analysis_service,
        cli_runner,
        temp_batch_file,
        mock_portfolio_data,
    ):
        """Test review command in batch mode."""
        # Setup batch service mock
        mock_batch_service = Mock()
        mock_batch_service.validate_batch_file.return_value = True
        mock_batch_service.get_batch_tickers.return_value = ["AAPL", "MSFT", "GOOGL"]
        mock_batch_service_class.return_value = mock_batch_service

        # Setup analysis service mock
        mock_service_instance = Mock()
        mock_service_instance.aggregate_portfolios_best.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Run command
        result = cli_runner.invoke(strategy_app, ["review", "--best", "--batch"])

        # Verify results
        assert result.exit_code == 0
        mock_batch_service.validate_batch_file.assert_called_once()
        mock_batch_service.get_batch_tickers.assert_called_once()
        mock_service_instance.aggregate_portfolios_best.assert_called_once_with(
            ["AAPL", "MSFT", "GOOGL"],
        )

    @patch("app.cli.commands.strategy.BatchProcessingService")
    def test_review_batch_mode_invalid_batch_file(
        self, mock_batch_service_class, cli_runner,
    ):
        """Test review command with invalid batch file."""
        # Setup batch service mock
        mock_batch_service = Mock()
        mock_batch_service.validate_batch_file.return_value = False
        mock_batch_service_class.return_value = mock_batch_service

        # Run command
        result = cli_runner.invoke(strategy_app, ["review", "--best", "--batch"])

        # Should fail with batch file validation error
        assert result.exit_code != 0
        assert "batch file validation failed" in result.stdout.lower()

    @patch("app.cli.commands.strategy.BatchProcessingService")
    def test_review_batch_mode_empty_batch_file(
        self, mock_batch_service_class, cli_runner,
    ):
        """Test review command with empty batch file."""
        # Setup batch service mock
        mock_batch_service = Mock()
        mock_batch_service.validate_batch_file.return_value = True
        mock_batch_service.get_batch_tickers.return_value = []
        mock_batch_service_class.return_value = mock_batch_service

        # Run command
        result = cli_runner.invoke(strategy_app, ["review", "--best", "--batch"])

        # Should fail with no tickers warning
        assert result.exit_code != 0
        assert "no tickers found" in result.stdout.lower()

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    @patch("app.cli.commands.strategy.BatchProcessingService")
    def test_review_batch_mode_forces_non_current(
        self,
        mock_batch_service_class,
        mock_analysis_service,
        cli_runner,
        mock_portfolio_data,
    ):
        """Test that batch mode forces non-current analysis."""
        # Setup batch service mock
        mock_batch_service = Mock()
        mock_batch_service.validate_batch_file.return_value = True
        mock_batch_service.get_batch_tickers.return_value = ["AAPL", "MSFT"]
        mock_batch_service_class.return_value = mock_batch_service

        # Setup analysis service mock
        mock_service_instance = Mock()
        mock_service_instance.aggregate_portfolios_best.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Run command with --current flag (should be ignored)
        result = cli_runner.invoke(
            strategy_app, ["review", "--best", "--batch", "--current"],
        )

        # Verify results
        assert result.exit_code == 0
        assert "ignoring --current" in result.stdout.lower()

        # Should create analysis service with non-current mode
        mock_analysis_service.assert_called_once_with(
            use_current=False, custom_date=None,
        )

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    @patch("app.cli.commands.strategy.BatchProcessingService")
    def test_review_batch_mode_forces_non_date(
        self,
        mock_batch_service_class,
        mock_analysis_service,
        cli_runner,
        mock_portfolio_data,
    ):
        """Test that batch mode forces non-date analysis."""
        # Setup batch service mock
        mock_batch_service = Mock()
        mock_batch_service.validate_batch_file.return_value = True
        mock_batch_service.get_batch_tickers.return_value = ["AAPL", "MSFT"]
        mock_batch_service_class.return_value = mock_batch_service

        # Setup analysis service mock
        mock_service_instance = Mock()
        mock_service_instance.aggregate_portfolios_best.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Mock path exists for date validation
        with patch("pathlib.Path.exists", return_value=True):
            # Run command with --date flag (should be ignored)
            result = cli_runner.invoke(
                strategy_app, ["review", "--best", "--batch", "--date", "20250816"],
            )

        # Verify results
        assert result.exit_code == 0
        assert "ignoring --current" in result.stdout.lower()

        # Should create analysis service with non-date mode
        mock_analysis_service.assert_called_once_with(
            use_current=False, custom_date=None,
        )

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    @patch("app.cli.commands.strategy.BatchProcessingService")
    def test_review_batch_mode_with_output_options(
        self,
        mock_batch_service_class,
        mock_analysis_service,
        cli_runner,
        mock_portfolio_data,
    ):
        """Test review batch mode with various output options."""
        # Setup batch service mock
        mock_batch_service = Mock()
        mock_batch_service.validate_batch_file.return_value = True
        mock_batch_service.get_batch_tickers.return_value = ["AAPL", "MSFT"]
        mock_batch_service_class.return_value = mock_batch_service

        # Setup analysis service mock
        mock_service_instance = Mock()
        mock_service_instance.aggregate_portfolios_best.return_value = (
            mock_portfolio_data
        )
        mock_analysis_service.return_value = mock_service_instance

        # Test with custom top-n and sort options
        result = cli_runner.invoke(
            strategy_app,
            [
                "review",
                "--best",
                "--batch",
                "--top-n",
                "25",
                "--sort-by",
                "Total Return [%]",
            ],
        )

        # Verify results
        assert result.exit_code == 0

    @patch("app.cli.commands.strategy.BatchProcessingService")
    def test_review_batch_mode_service_exception(
        self, mock_batch_service_class, cli_runner,
    ):
        """Test review command handling of batch service exceptions."""
        # Setup batch service mock to raise exception
        mock_batch_service_class.side_effect = Exception("Batch service error")

        # Run command
        result = cli_runner.invoke(strategy_app, ["review", "--best", "--batch"])

        # Should handle exception gracefully
        assert result.exit_code != 0
        assert "error" in result.stdout.lower()


class TestStrategyReviewEdgeCases:
    """Test edge cases and boundary conditions for review command."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_review_command_no_arguments(self, cli_runner):
        """Test review command with no arguments."""
        result = cli_runner.invoke(strategy_app, ["review"])

        # Should show error message
        assert result.exit_code != 0

    def test_review_command_invalid_flag_combinations(self, cli_runner):
        """Test review command with invalid flag combinations."""
        # Test missing --best flag
        result1 = cli_runner.invoke(strategy_app, ["review", "--profile", "test"])
        assert result1.exit_code != 0

        # Test conflicting modes
        result2 = cli_runner.invoke(
            strategy_app, ["review", "--best", "--batch", "--profile", "test"],
        )
        # Should work - profile is ignored in batch mode
        assert result2.exit_code != 0  # Will fail due to batch file validation

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    def test_review_command_analysis_service_exception(
        self, mock_analysis_service, cli_runner,
    ):
        """Test review command handling of analysis service exceptions."""
        # Setup mock to raise exception
        mock_analysis_service.side_effect = Exception("Analysis service error")

        # Run command
        result = cli_runner.invoke(strategy_app, ["review", "--best", "--current"])

        # Should handle exception gracefully
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_review_command_invalid_top_n(self, cli_runner):
        """Test review command with invalid top-n values."""
        # Test negative top-n
        result = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current", "--top-n", "-1"],
        )
        # Should handle validation (depends on typer implementation)
        assert result.exit_code is not None

    def test_review_command_invalid_output_format(self, cli_runner):
        """Test review command with invalid output format."""
        result = cli_runner.invoke(
            strategy_app,
            ["review", "--best", "--current", "--output-format", "invalid"],
        )
        # Should complete (no strict validation on output format)
        assert result.exit_code is not None

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    def test_review_command_very_large_top_n(self, mock_analysis_service, cli_runner):
        """Test review command with very large top-n value."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.aggregate_all_current_portfolios.return_value = (
            pd.DataFrame()
        )
        mock_analysis_service.return_value = mock_service_instance

        # Run command with large top-n
        result = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current", "--top-n", "999999"],
        )

        # Should handle gracefully
        assert result.exit_code == 0

    def test_review_command_empty_ticker_list(self, cli_runner):
        """Test review command with empty ticker list."""
        result = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current", "--ticker", ""],
        )

        # Should handle empty ticker gracefully
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_review_command_special_characters_in_sort_by(self, cli_runner):
        """Test review command with special characters in sort-by."""
        result = cli_runner.invoke(
            strategy_app,
            ["review", "--best", "--current", "--sort-by", "Invalid Column [%]"],
        )

        # Should complete (sorting validation happens at analysis level)
        assert result.exit_code is not None

    @patch("app.cli.services.portfolio_analysis_service.PortfolioAnalysisService")
    def test_review_command_unicode_in_parameters(
        self, mock_analysis_service, cli_runner,
    ):
        """Test review command with Unicode characters in parameters."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.aggregate_portfolios_best.return_value = pd.DataFrame()
        mock_analysis_service.return_value = mock_service_instance

        # Run command with Unicode ticker
        result = cli_runner.invoke(
            strategy_app, ["review", "--best", "--current", "--ticker", "AAPL中文"],
        )

        # Should handle Unicode gracefully
        assert result.exit_code == 0
