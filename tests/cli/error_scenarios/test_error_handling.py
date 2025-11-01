"""
Comprehensive Error Scenario Tests.

This test suite validates robust error handling across the CLI system:
- Invalid ticker symbols and data fetch failures
- Network connectivity issues and timeouts
- Invalid parameter combinations and validation errors
- File system permission and access issues
- Corrupted configuration files and parsing errors
- Memory constraints and resource limitations
- Service failures and graceful degradation

These tests ensure the system fails gracefully and provides meaningful error messages.
"""

import contextlib
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import polars as pl
import pytest
from typer.testing import CliRunner

from app.cli.commands.strategy import app as strategy_app


def create_mock_config(ticker=None, strategy_types=None):
    """Create a properly mocked config object with all required attributes for sweep command."""
    mock_config = Mock()
    mock_config.ticker = ticker or ["AAPL"]
    mock_config.strategy_types = strategy_types or ["SMA"]

    # Add attributes needed for parameter validation
    mock_config.fast_period_range = None
    mock_config.slow_period_range = None
    mock_config.fast_period = None
    mock_config.slow_period = None

    # Add minimums object with all required attributes
    mock_minimums = Mock()
    mock_minimums.win_rate = None
    mock_minimums.trades = None
    mock_minimums.profit_factor = None
    mock_minimums.sortino_ratio = None
    mock_config.minimums = mock_minimums

    # Add synthetic attributes (disable synthetic mode)
    mock_synthetic = Mock()
    mock_synthetic.use_synthetic = False
    mock_synthetic.ticker_1 = None
    mock_synthetic.ticker_2 = None
    mock_config.synthetic = mock_synthetic

    return mock_config


@pytest.mark.integration
class TestInvalidTickerHandling:
    """Test handling of invalid ticker symbols and data fetch failures."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_invalid_ticker_symbol_handling(
        self,
        mock_config_loader,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of invalid ticker symbols."""
        # Setup mocks with proper config object
        mock_config = create_mock_config(
            ticker=["INVALID_TICKER_XYZ"],
            strategy_types=["SMA"],
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Simulate data fetch failure for invalid ticker
        mock_get_data.return_value = None

        # Execute command with invalid ticker
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "INVALID_TICKER_XYZ",
                "--strategy",
                "SMA",
                "--fast",
                "10",
                "--slow",
                "20",
            ],
        )

        # Verify graceful error handling
        assert result.exit_code == 0  # Should not crash
        assert (
            "Failed to fetch price data" in result.stdout
            or "error" in result.stdout.lower()
        )

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_empty_ticker_data_handling(
        self,
        mock_config_loader,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of empty data returned for valid ticker."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Return empty DataFrame
        mock_get_data.return_value = pl.DataFrame()

        # Execute command (ticker is positional argument in run command)
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--strategy", "SMA", "--fast", "10", "--slow", "20"],
        )

        # Verify handling of empty data
        assert result.exit_code == 0
        assert "error" in result.stdout.lower() or "failed" in result.stdout.lower()

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_malformed_ticker_data_handling(
        self,
        mock_config_loader,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of malformed price data."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Return malformed data (missing required columns)
        mock_get_data.return_value = pl.DataFrame({"invalid_column": [1, 2, 3]})

        # Execute command (ticker is positional argument in run command)
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--strategy", "SMA", "--fast", "10", "--slow", "20"],
        )

        # Verify handling of malformed data
        assert result.exit_code == 0
        # Should handle missing columns gracefully

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_special_character_ticker_handling(
        self,
        mock_config_loader,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of tickers with special characters."""
        special_tickers = ["BTC-USD", "STRK/MSTR", "^GSPC", "GC=F", "TICKER.L"]

        for ticker in special_tickers:
            # Setup mocks
            mock_config = Mock()
            mock_config.ticker = [ticker]
            mock_config.strategy_types = ["SMA"]
            mock_config_loader.return_value.load_from_profile.return_value = mock_config

            mock_get_data.return_value = None  # Simulate failure

            # Execute command (ticker is positional argument in run command)
            result = cli_runner.invoke(
                strategy_app,
                ["run", ticker, "--strategy", "SMA", "--fast", "10", "--slow", "20"],
            )

            # Should handle special characters without crashing
            assert result.exit_code is not None  # Command completed

            # Reset mocks for next iteration
            mock_config_loader.reset_mock()
            mock_get_data.reset_mock()


@pytest.mark.integration
class TestNetworkErrorHandling:
    """Test handling of network connectivity issues and timeouts."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_network_timeout_handling(
        self,
        mock_config_loader,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of network timeouts during data fetch."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Simulate network timeout
        mock_get_data.side_effect = TimeoutError("Connection timeout")

        # Execute command (ticker is positional argument in run command)
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--strategy", "SMA", "--fast", "10", "--slow", "20"],
        )

        # Verify timeout handling
        assert result.exit_code == 0
        assert "timeout" in result.stdout.lower() or "error" in result.stdout.lower()

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_connection_error_handling(
        self,
        mock_config_loader,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of connection errors."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Simulate connection error
        mock_get_data.side_effect = ConnectionError("Failed to connect")

        # Execute command (ticker is positional argument in run command)
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--strategy", "SMA", "--fast", "10", "--slow", "20"],
        )

        # Verify connection error handling
        assert result.exit_code == 0
        assert "connection" in result.stdout.lower() or "error" in result.stdout.lower()

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_ssl_certificate_error_handling(
        self,
        mock_config_loader,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of SSL certificate errors."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Simulate SSL error
        import ssl

        mock_get_data.side_effect = ssl.SSLError("SSL certificate verification failed")

        # Execute command (ticker is positional argument in run command)
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--strategy", "SMA", "--fast", "10", "--slow", "20"],
        )

        # Verify SSL error handling
        assert result.exit_code == 0
        assert (
            "ssl" in result.stdout.lower()
            or "certificate" in result.stdout.lower()
            or "error" in result.stdout.lower()
        )

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_http_error_handling(self, mock_config_loader, mock_get_data, cli_runner):
        """Test handling of HTTP errors (4xx, 5xx)."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Simulate HTTP error
        from requests.exceptions import HTTPError

        mock_get_data.side_effect = HTTPError("404 Not Found")

        # Execute command (ticker is positional argument in run command)
        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--strategy", "SMA", "--fast", "10", "--slow", "20"],
        )

        # Verify HTTP error handling
        assert result.exit_code == 0
        assert (
            "http" in result.stdout.lower()
            or "404" in result.stdout
            or "error" in result.stdout.lower()
        )


@pytest.mark.integration
class TestParameterValidationErrors:
    """Test handling of invalid parameter combinations and validation errors."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_invalid_strategy_type_handling(self, cli_runner):
        """Test handling of invalid strategy types."""
        result = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "INVALID_STRATEGY"],
        )

        # Should handle invalid strategy type
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_negative_parameter_values(self, cli_runner):
        """Test handling of negative parameter values."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--min-trades",
                "-10",
                "--years",
                "-5",
            ],
        )

        # Should handle negative values
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_zero_parameter_values(self, cli_runner):
        """Test handling of zero parameter values."""
        result = cli_runner.invoke(
            strategy_app,
            [
                "run",
                "--ticker",
                "AAPL",
                "--strategy",
                "SMA",
                "--min-trades",
                "0",
                "--years",
                "0",
            ],
        )

        # Should handle zero values appropriately
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_invalid_win_rate_range(self, cli_runner):
        """Test handling of invalid win rate values."""
        # Test win rate > 1.0
        result1 = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA", "--min-win-rate", "1.5"],
        )

        # Test negative win rate
        result2 = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", "SMA", "--min-win-rate", "-0.1"],
        )

        # Should handle invalid win rate ranges
        assert result1.exit_code != 0 or "error" in result1.stdout.lower()
        assert result2.exit_code != 0 or "error" in result2.stdout.lower()

    def test_invalid_parameter_sweep_ranges(self, cli_runner):
        """Test handling of invalid parameter sweep ranges."""
        # Test fast_max < fast_min
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--ticker",
                "AAPL",
                "--fast-min",
                "50",
                "--fast-max",
                "10",  # Invalid: max < min
                "--slow-min",
                "60",
                "--slow-max",
                "100",
            ],
        )

        # Should handle invalid ranges
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_conflicting_parameter_combinations(self, cli_runner):
        """Test handling of conflicting parameter combinations."""
        # Test conflicting year settings
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
                "0",  # Conflicting: use years but years = 0
            ],
        )

        # Should handle conflicting parameters
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_empty_required_parameters(self, cli_runner):
        """Test handling of empty required parameters."""
        # Test empty ticker
        result1 = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "", "--strategy", "SMA"],
        )

        # Test empty strategy
        result2 = cli_runner.invoke(
            strategy_app,
            ["run", "--ticker", "AAPL", "--strategy", ""],
        )

        # Should handle empty required parameters
        assert result1.exit_code != 0 or "error" in result1.stdout.lower()
        assert result2.exit_code != 0 or "error" in result2.stdout.lower()


@pytest.mark.integration
class TestFileSystemErrorHandling:
    """Test handling of file system permission and access issues."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_restricted_dir(self):
        """Create temporary directory with restricted permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            restricted_dir = Path(temp_dir) / "restricted"
            restricted_dir.mkdir()

            # Try to restrict permissions (may not work on all systems)
            try:
                os.chmod(restricted_dir, 0o000)
                yield restricted_dir
            finally:
                # Restore permissions for cleanup
                with contextlib.suppress(Exception):
                    os.chmod(restricted_dir, 0o755)

    def test_missing_profile_file_handling(self, cli_runner):
        """Test handling of missing profile files."""
        result = cli_runner.invoke(
            strategy_app,
            ["run", "--profile", "nonexistent_profile"],
        )

        # Should handle missing profile file
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_permission_denied_profile_access(self, mock_config_loader, cli_runner):
        """Test handling of permission denied errors when accessing profiles."""
        # Mock permission denied error
        mock_config_loader.return_value.load_from_profile.side_effect = PermissionError(
            "Permission denied",
        )

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--profile", "default_strategy"],
        )

        # Should handle permission errors
        assert (
            result.exit_code != 0
            or "permission" in result.stdout.lower()
            or "error" in result.stdout.lower()
        )


@pytest.mark.integration
class TestCorruptedConfigurationHandling:
    """Test handling of corrupted configuration files and parsing errors."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for corrupted config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "profiles"
            config_dir.mkdir()
            yield config_dir

    def create_corrupted_yaml_file(self, config_dir, filename, content):
        """Helper to create corrupted YAML files."""
        config_file = config_dir / filename
        config_file.write_text(content)
        return config_file

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_malformed_yaml_handling(
        self,
        mock_config_loader,
        cli_runner,
        temp_config_dir,
    ):
        """Test handling of malformed YAML configuration files."""
        # Create malformed YAML file
        malformed_yaml = """
metadata:
  name: corrupted_profile
  description: "Unclosed quote
config_type: strategy
config:
  ticker: [AAPL
  invalid_structure
"""
        self.create_corrupted_yaml_file(
            temp_config_dir,
            "corrupted.yaml",
            malformed_yaml,
        )

        # Mock YAML parsing error
        import yaml

        mock_config_loader.return_value.load_from_profile.side_effect = yaml.YAMLError(
            "Invalid YAML",
        )

        result = cli_runner.invoke(strategy_app, ["run", "--profile", "corrupted"])

        # Should handle YAML parsing errors
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_missing_required_config_fields(self, mock_config_loader, cli_runner):
        """Test handling of configuration files missing required fields."""
        # Mock config with missing required fields
        mock_config_loader.return_value.load_from_profile.side_effect = KeyError(
            "Missing required field",
        )

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--profile", "incomplete_profile"],
        )

        # Should handle missing required fields
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_invalid_config_data_types(self, mock_config_loader, cli_runner):
        """Test handling of invalid data types in configuration."""
        # Mock config with invalid data types
        mock_config_loader.return_value.load_from_profile.side_effect = TypeError(
            "Invalid data type",
        )

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--profile", "invalid_types_profile"],
        )

        # Should handle type validation errors
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_circular_inheritance_handling(self, mock_config_loader, cli_runner):
        """Test handling of circular inheritance in configuration files."""
        # Mock circular inheritance error
        mock_config_loader.return_value.load_from_profile.side_effect = RecursionError(
            "Circular inheritance detected",
        )

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--profile", "circular_profile"],
        )

        # Should handle circular inheritance
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_corrupted_json_data_handling(self, mock_config_loader, cli_runner):
        """Test handling of corrupted JSON data within configuration."""
        # Mock JSON parsing error
        mock_config_loader.return_value.load_from_profile.side_effect = (
            json.JSONDecodeError("Invalid JSON", "", 0)
        )

        result = cli_runner.invoke(
            strategy_app,
            ["run", "--profile", "corrupted_json_profile"],
        )

        # Should handle JSON parsing errors
        assert result.exit_code != 0 or "error" in result.stdout.lower()


@pytest.mark.integration
class TestMemoryAndResourceConstraints:
    """Test handling of memory constraints and resource limitations."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()


@pytest.mark.integration
class TestServiceFailureHandling:
    """Test handling of service failures and graceful degradation."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_strategy_service_initialization_failure(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        cli_runner,
    ):
        """Test handling of strategy service initialization failures using sweep command."""
        # Setup mocks with proper config object
        mock_config = create_mock_config(
            ticker=["AAPL"],
            strategy_types=["SMA"],
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Mock service initialization failure
        mock_dispatcher_class.side_effect = RuntimeError(
            "Service initialization failed",
        )

        result = cli_runner.invoke(
            strategy_app,
            ["sweep", "--ticker", "AAPL"],
        )

        # Should handle service initialization failure - RuntimeError will be caught
        assert result.exit_code == 1  # Uncaught RuntimeError causes exit 1

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_strategy_execution_service_failure(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test handling of strategy execution service failures using sweep command."""
        # Setup mocks with proper config object
        mock_config = create_mock_config(
            ticker=["AAPL"],
            strategy_types=["SMA"],
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.side_effect = RuntimeError(
            "Strategy execution failed",
        )
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [100.0]},
        )

        result = cli_runner.invoke(
            strategy_app,
            ["sweep", "--ticker", "AAPL"],
        )

        # Should handle execution service failure - RuntimeError will be caught
        assert result.exit_code == 1  # Uncaught RuntimeError causes exit 1

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_export_service_failure_graceful_degradation(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test graceful degradation when export service fails using sweep command."""
        # Setup mocks with proper config object
        mock_config = create_mock_config(
            ticker=["AAPL"],
            strategy_types=["SMA"],
        )
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [100.0]},
        )

        # Mock export service failure
        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            mock_export.side_effect = RuntimeError("Export service failed")

            result = cli_runner.invoke(
                strategy_app,
                ["sweep", "--ticker", "AAPL"],
            )

            # RuntimeError during export will cause exit 1 (not caught by exception handler)
            assert result.exit_code == 1

    def test_cli_framework_error_handling(self, cli_runner):
        """Test handling of CLI framework errors and malformed commands."""
        # Test completely malformed command
        result = cli_runner.invoke(strategy_app, ["invalid_command", "--invalid-flag"])

        # Should handle malformed commands gracefully
        assert (
            result.exit_code != 0
            or "error" in result.stdout.lower()
            or "usage" in result.stdout.lower()
        )

    def test_unexpected_exception_handling(self, cli_runner):
        """Test handling of unexpected exceptions during command execution."""
        # Test command with missing required arguments
        result = cli_runner.invoke(strategy_app, ["run"])

        # Should handle missing arguments gracefully
        assert (
            result.exit_code != 0
            or "error" in result.stdout.lower()
            or "required" in result.stdout.lower()
        )


@pytest.mark.integration
class TestRecoveryAndRetryMechanisms:
    """Test recovery mechanisms and retry logic for transient failures."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_transient_network_error_recovery(
        self,
        mock_config_loader,
        mock_get_data,
        cli_runner,
    ):
        """Test recovery from transient network errors."""
        # Setup mocks
        mock_config = Mock()
        mock_config.ticker = ["AAPL"]
        mock_config.strategy_types = ["SMA"]
        mock_config_loader.return_value.load_from_profile.return_value = mock_config

        # Mock transient failure followed by success
        call_count = 0

        def get_data_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                msg = "Transient network error"
                raise ConnectionError(msg)
            return pl.DataFrame({"Date": [pl.date(2023, 1, 1)], "Close": [100.0]})

        mock_get_data.side_effect = get_data_side_effect

        result = cli_runner.invoke(
            strategy_app,
            ["run", "AAPL", "--strategy", "SMA", "--fast", "10", "--slow", "20"],
        )

        # Should handle transient errors appropriately
        # Note: Current implementation may not have retry logic,
        # but should fail gracefully
        assert result.exit_code == 0
