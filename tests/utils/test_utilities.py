"""
Comprehensive Testing Utilities.

This module provides reusable testing utilities for the trading CLI test suite:
- MockDataFactory: Generate realistic mock data for testing
- CLITestRunner: Simplified CLI testing with common patterns
- ExportValidator: Validate exported files and data
- ConfigBuilder: Build test configurations programmatically
- AssertionHelpers: Custom assertion helpers for trading data

These utilities reduce code duplication and improve test maintainability.
"""

import csv
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import MagicMock, Mock

import pandas as pd
import polars as pl
from typer.testing import CliRunner

from app.cli.config.loader import ConfigLoader
from app.cli.models.strategy import StrategyConfig, StrategyType


class MockDataFactory:
    """Factory for generating realistic mock data for testing."""

    @staticmethod
    def create_price_data(
        ticker: str = "AAPL",
        start_date: str = "2023-01-01",
        end_date: str = "2023-12-31",
        base_price: float = 100.0,
        volatility: float = 0.02,
        trend: float = 0.0001,
    ) -> pl.DataFrame:
        """Create realistic price data with trend and volatility."""
        dates = pl.date_range(
            start=pl.date(*map(int, start_date.split("-"))),
            end=pl.date(*map(int, end_date.split("-"))),
            interval="1d",
        )

        prices = []
        current_price = base_price

        for i, date in enumerate(dates):
            # Add trend
            current_price *= 1 + trend

            # Add volatility (random-like but deterministic for testing)
            daily_change = volatility * ((i % 7 - 3) / 3)  # -1 to 1 range
            current_price *= 1 + daily_change

            # Ensure positive prices
            current_price = max(current_price, 0.01)
            prices.append(current_price)

        return pl.DataFrame(
            {
                "Date": dates,
                "Close": prices,
                "High": [p * 1.02 for p in prices],
                "Low": [p * 0.98 for p in prices],
                "Open": [p * (1 + ((i % 5 - 2) * 0.005)) for i, p in enumerate(prices)],
                "Volume": [1000000 + (i % 500000) for i in range(len(prices))],
            }
        )

    @staticmethod
    def create_crypto_price_data(
        ticker: str = "BTC-USD",
        start_date: str = "2023-01-01",
        end_date: str = "2023-12-31",
        base_price: float = 45000.0,
    ) -> pl.DataFrame:
        """Create realistic crypto price data with higher volatility."""
        return MockDataFactory.create_price_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            base_price=base_price,
            volatility=0.05,  # Higher volatility for crypto
            trend=0.0002,
        )

    @staticmethod
    def create_strategy_results(
        ticker: str = "AAPL",
        strategy_type: str = "SMA",
        num_results: int = 10,
        base_score: float = 8.0,
    ) -> pl.DataFrame:
        """Create realistic strategy analysis results."""
        results = []

        for i in range(num_results):
            fast_period = 5 + (i * 2)
            slow_period = fast_period + 15 + (i * 3)

            # Generate correlated metrics
            win_rate = 50.0 + (i * 2) + (i % 3)
            total_return = 15.0 + (i * 3) + (i % 5)
            sharpe_ratio = 0.8 + (i * 0.1) + (i % 4) * 0.05
            score = base_score + (i * 0.2) + (i % 3) * 0.1

            result = {
                "Ticker": ticker,
                "Strategy Type": strategy_type,
                "Fast Period": fast_period,
                "Slow Period": slow_period,
                "Total Trades": 40 + i * 2,
                "Win Rate [%]": min(win_rate, 85.0),
                "Total Return [%]": total_return,
                "Sharpe Ratio": sharpe_ratio,
                "Max Drawdown [%]": 5.0 + (i % 7),
                "Score": min(score, 10.0),
                "Profit Factor": 1.2 + (i * 0.05),
                "Sortino Ratio": sharpe_ratio * 1.1,
                "Calmar Ratio": total_return / (5.0 + (i % 7)),
                "Metric Type": MockDataFactory._get_metric_type(i),
            }

            # Add MACD-specific columns if needed
            if strategy_type == "MACD":
                result["Signal Period"] = 5 + (i % 10)

            results.append(result)

        return pl.DataFrame(results)

    @staticmethod
    def create_multi_ticker_results(
        tickers: List[str], strategy_types: List[str], results_per_combination: int = 3
    ) -> pl.DataFrame:
        """Create multi-ticker, multi-strategy results."""
        all_results = []

        for ticker in tickers:
            for strategy_type in strategy_types:
                ticker_results = MockDataFactory.create_strategy_results(
                    ticker=ticker,
                    strategy_type=strategy_type,
                    num_results=results_per_combination,
                    base_score=7.0 + (len(ticker) % 3),  # Vary base score by ticker
                )
                all_results.append(ticker_results)

        return pl.concat(all_results)

    @staticmethod
    def create_empty_results() -> pl.DataFrame:
        """Create empty results DataFrame with correct schema."""
        return pl.DataFrame({"Ticker": [], "Strategy Type": [], "Score": []})

    @staticmethod
    def create_minimal_results(ticker: str = "TEST") -> pl.DataFrame:
        """Create minimal results (single row) for edge case testing."""
        return pl.DataFrame(
            {
                "Ticker": [ticker],
                "Strategy Type": ["SMA"],
                "Fast Period": [10],
                "Slow Period": [20],
                "Total Trades": [25],
                "Win Rate [%]": [55.0],
                "Total Return [%]": [15.5],
                "Sharpe Ratio": [1.2],
                "Score": [7.5],
                "Metric Type": ["Most Total Return [%]"],
            }
        )

    @staticmethod
    def _get_metric_type(index: int) -> str:
        """Get metric type based on index for variety."""
        metric_types = [
            "Most Total Return [%]",
            "Most Sharpe Ratio",
            "Most Win Rate [%]",
            "Most Profit Factor",
            "Most Calmar Ratio",
        ]
        return metric_types[index % len(metric_types)]

    @staticmethod
    def create_mock_config(
        ticker: Union[str, List[str]] = "AAPL",
        strategy_types: List[StrategyType] = None,
        **kwargs,
    ) -> Mock:
        """Create mock strategy configuration."""
        if strategy_types is None:
            strategy_types = [StrategyType.SMA]

        if isinstance(ticker, str):
            ticker = [ticker]

        mock_config = Mock()
        mock_config.ticker = ticker
        mock_config.strategy_types = strategy_types
        mock_config.use_years = kwargs.get("use_years", False)
        mock_config.years = kwargs.get("years", 15)
        mock_config.use_hourly = kwargs.get("use_hourly", False)
        mock_config.minimums = Mock()
        mock_config.minimums.win_rate = kwargs.get("min_win_rate", 0.5)
        mock_config.minimums.trades = kwargs.get("min_trades", 20)
        mock_config.minimums.profit_factor = kwargs.get("min_profit_factor", 1.0)

        # Add parameter ranges for sweeps
        mock_config.fast_period_range = kwargs.get("fast_period_range", [5, 50])
        mock_config.slow_period_range = kwargs.get("slow_period_range", [20, 100])

        return mock_config


class CLITestRunner:
    """Simplified CLI testing with common patterns and utilities."""

    def __init__(self):
        self.runner = CliRunner()
        self.mock_data_factory = MockDataFactory()

    def run_strategy_command(
        self,
        app,
        ticker: str = "AAPL",
        strategy: str = "SMA",
        profile: Optional[str] = None,
        dry_run: bool = False,
        **kwargs,
    ):
        """Run strategy command with common parameters."""
        cmd_args = ["run"]

        if profile:
            cmd_args.extend(["--profile", profile])

        cmd_args.extend(["--ticker", ticker, "--strategy", strategy])

        # Add optional parameters
        if kwargs.get("min_trades"):
            cmd_args.extend(["--min-trades", str(kwargs["min_trades"])])
        if kwargs.get("min_win_rate"):
            cmd_args.extend(["--min-win-rate", str(kwargs["min_win_rate"])])
        if kwargs.get("years"):
            cmd_args.extend(["--years", str(kwargs["years"])])
        if kwargs.get("use_years"):
            cmd_args.append("--use-years")
        if kwargs.get("verbose"):
            cmd_args.append("--verbose")
        if dry_run:
            cmd_args.append("--dry-run")

        return self.runner.invoke(app, cmd_args)

    def run_sweep_command(
        self,
        app,
        ticker: str = "AAPL",
        fast_min: int = 5,
        fast_max: int = 50,
        slow_min: int = 20,
        slow_max: int = 100,
        max_results: Optional[int] = None,
        **kwargs,
    ):
        """Run parameter sweep command with common parameters."""
        cmd_args = [
            "sweep",
            "--ticker",
            ticker,
            "--fast-min",
            str(fast_min),
            "--fast-max",
            str(fast_max),
            "--slow-min",
            str(slow_min),
            "--slow-max",
            str(slow_max),
        ]

        if max_results:
            cmd_args.extend(["--max-results", str(max_results)])

        if kwargs.get("profile"):
            cmd_args.extend(["--profile", kwargs["profile"]])

        return self.runner.invoke(app, cmd_args)

    def setup_strategy_mocks(
        self,
        config_loader_mock,
        dispatcher_class_mock,
        get_data_mock,
        ticker: str = "AAPL",
        strategy_types: List[StrategyType] = None,
        return_data: Optional[pl.DataFrame] = None,
        execution_success: bool = True,
    ):
        """Setup common strategy execution mocks."""
        if strategy_types is None:
            strategy_types = [StrategyType.SMA]

        if return_data is None:
            return_data = self.mock_data_factory.create_price_data(ticker)

        # Setup config mock
        mock_config = self.mock_data_factory.create_mock_config(ticker, strategy_types)
        config_loader_mock.return_value.load_from_profile.return_value = mock_config

        # Setup dispatcher mock
        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = execution_success
        dispatcher_class_mock.return_value = mock_dispatcher

        # Setup data mock
        get_data_mock.return_value = return_data

        return mock_config, mock_dispatcher

    def setup_sweep_mocks(
        self,
        config_loader_mock,
        analyze_mock,
        get_data_mock,
        logging_mock,
        ticker: str = "AAPL",
        return_results: Optional[pl.DataFrame] = None,
    ):
        """Setup common parameter sweep mocks."""
        if return_results is None:
            return_results = self.mock_data_factory.create_strategy_results(ticker)

        # Setup config mock
        mock_config = self.mock_data_factory.create_mock_config(ticker)
        config_loader_mock.return_value.load_from_profile.return_value = mock_config

        # Setup analysis mocks
        get_data_mock.return_value = self.mock_data_factory.create_price_data(ticker)
        analyze_mock.return_value = return_results

        # Setup logging mock
        logging_mock.return_value.__enter__ = Mock()
        logging_mock.return_value.__exit__ = Mock()

        return mock_config


class ExportValidator:
    """Validate exported files and data structures."""

    @staticmethod
    def validate_csv_file(file_path: Path) -> Dict[str, Any]:
        """Validate CSV file structure and return metadata."""
        if not file_path.exists():
            raise AssertionError(f"CSV file does not exist: {file_path}")

        if not file_path.is_file():
            raise AssertionError(f"Path is not a file: {file_path}")

        # Read CSV file
        try:
            df_pandas = pd.read_csv(file_path)
            df_polars = pl.read_csv(file_path)
        except Exception as e:
            raise AssertionError(f"Failed to read CSV file {file_path}: {e}")

        # Validate basic structure
        if len(df_pandas) == 0:
            raise AssertionError(f"CSV file is empty: {file_path}")

        if len(df_pandas.columns) == 0:
            raise AssertionError(f"CSV file has no columns: {file_path}")

        # Check for required columns
        required_columns = ["Ticker", "Strategy Type", "Score"]
        missing_columns = [
            col for col in required_columns if col not in df_pandas.columns
        ]
        if missing_columns:
            raise AssertionError(
                f"CSV file missing required columns {missing_columns}: {file_path}"
            )

        return {
            "path": file_path,
            "rows": len(df_pandas),
            "columns": len(df_pandas.columns),
            "column_names": df_pandas.columns.tolist(),
            "data_types": {col: str(dtype) for col, dtype in df_pandas.dtypes.items()},
            "pandas_df": df_pandas,
            "polars_df": df_polars,
        }

    @staticmethod
    def validate_export_directory_structure(base_dir: Path, export_type: str):
        """Validate export directory structure."""
        expected_path = base_dir / "data" / "raw" / export_type

        if not expected_path.exists():
            raise AssertionError(f"Export directory does not exist: {expected_path}")

        if not expected_path.is_dir():
            raise AssertionError(f"Export path is not a directory: {expected_path}")

        # Check for CSV files
        csv_files = list(expected_path.glob("*.csv"))
        if not csv_files:
            raise AssertionError(
                f"No CSV files found in export directory: {expected_path}"
            )

        return {
            "directory": expected_path,
            "csv_files": csv_files,
            "file_count": len(csv_files),
        }

    @staticmethod
    def validate_schema_compliance(df: pl.DataFrame, schema_type: str):
        """Validate DataFrame schema compliance."""
        required_schemas = {
            "portfolios": ["Ticker", "Strategy Type", "Score"],
            "portfolios_filtered": ["Metric Type", "Ticker", "Strategy Type", "Score"],
            "portfolios_best": ["Metric Type", "Ticker", "Strategy Type", "Score"],
        }

        if schema_type not in required_schemas:
            raise ValueError(f"Unknown schema type: {schema_type}")

        required_columns = required_schemas[schema_type]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise AssertionError(
                f"DataFrame missing required columns for {schema_type}: {missing_columns}"
            )

        # Validate column ordering for filtered/best schemas
        if schema_type in ["portfolios_filtered", "portfolios_best"]:
            if df.columns[0] != "Metric Type":
                raise AssertionError(
                    f"First column should be 'Metric Type' for {schema_type}, got: {df.columns[0]}"
                )

        return True

    @staticmethod
    def validate_metric_type_preservation(
        df: pl.DataFrame, expected_metric_types: List[str]
    ):
        """Validate that metric types are preserved correctly."""
        if "Metric Type" not in df.columns:
            raise AssertionError("DataFrame missing 'Metric Type' column")

        actual_metric_types = set(df["Metric Type"].unique().to_list())
        expected_metric_types_set = set(expected_metric_types)

        missing_types = expected_metric_types_set - actual_metric_types
        if missing_types:
            raise AssertionError(f"Missing expected metric types: {missing_types}")

        return True

    @staticmethod
    def validate_numerical_data_integrity(df: pl.DataFrame):
        """Validate numerical data integrity."""
        numerical_columns = [
            "Total Trades",
            "Win Rate [%]",
            "Total Return [%]",
            "Sharpe Ratio",
            "Score",
        ]

        for col in numerical_columns:
            if col in df.columns:
                # Check for null values
                null_count = df[col].null_count()
                if null_count > 0:
                    raise AssertionError(f"Column {col} has {null_count} null values")

                # Check for reasonable ranges
                if col == "Win Rate [%]":
                    values = df[col].to_list()
                    if any(v < 0 or v > 100 for v in values):
                        raise AssertionError(
                            f"Win Rate values outside valid range [0,100]: {values}"
                        )

                if col == "Total Trades":
                    values = df[col].to_list()
                    if any(v <= 0 for v in values):
                        raise AssertionError(
                            f"Total Trades has non-positive values: {values}"
                        )

        return True


class ConfigBuilder:
    """Build test configurations programmatically."""

    def __init__(self):
        self.config = {}
        self.metadata = {
            "name": "test_config",
            "description": "Test configuration",
            "version": "1.0",
        }

    def with_tickers(self, tickers: Union[str, List[str]]):
        """Add tickers to configuration."""
        if isinstance(tickers, str):
            tickers = [tickers]
        self.config["ticker"] = tickers
        return self

    def with_strategies(self, strategies: List[str]):
        """Add strategy types to configuration."""
        self.config["strategy_types"] = strategies
        return self

    def with_years(self, years: int, use_years: bool = True):
        """Add years configuration."""
        self.config["years"] = years
        self.config["use_years"] = use_years
        return self

    def with_minimums(
        self, win_rate: float = 0.5, trades: int = 20, profit_factor: float = 1.0
    ):
        """Add minimum criteria."""
        self.config["minimums"] = {
            "win_rate": win_rate,
            "trades": trades,
            "profit_factor": profit_factor,
        }
        return self

    def with_parameter_ranges(self, fast_range: List[int], slow_range: List[int]):
        """Add parameter ranges for sweeps."""
        self.config["fast_period_range"] = fast_range
        self.config["slow_period_range"] = slow_range
        return self

    def with_metadata(self, name: str, description: str = None):
        """Add metadata."""
        self.metadata["name"] = name
        if description:
            self.metadata["description"] = description
        return self

    def with_inheritance(self, parent: str):
        """Add inheritance."""
        self.metadata["inherits_from"] = parent
        return self

    def build_dict(self) -> Dict[str, Any]:
        """Build configuration dictionary."""
        return {
            "metadata": self.metadata,
            "config_type": "strategy",
            "config": self.config,
        }

    def build_yaml_content(self) -> str:
        """Build YAML configuration content."""
        import yaml

        return yaml.dump(self.build_dict(), default_flow_style=False)

    def save_to_file(self, file_path: Path):
        """Save configuration to YAML file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.build_yaml_content())
        return file_path


class AssertionHelpers:
    """Custom assertion helpers for trading data."""

    @staticmethod
    def assert_valid_ticker_format(ticker: str):
        """Assert ticker has valid format."""
        if not ticker or not isinstance(ticker, str):
            raise AssertionError(f"Invalid ticker format: {ticker}")

        if len(ticker.strip()) == 0:
            raise AssertionError("Ticker cannot be empty")

        # Allow various ticker formats
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/.=^")
        if not all(c in valid_chars for c in ticker.upper().replace(" ", "")):
            raise AssertionError(f"Ticker contains invalid characters: {ticker}")

    @staticmethod
    def assert_valid_strategy_results(df: pl.DataFrame):
        """Assert DataFrame contains valid strategy results."""
        if len(df) == 0:
            raise AssertionError("Strategy results DataFrame is empty")

        required_columns = ["Ticker", "Strategy Type", "Score"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise AssertionError(f"Missing required columns: {missing_columns}")

        # Validate data types and ranges
        if "Score" in df.columns:
            scores = df["Score"].to_list()
            if any(not isinstance(score, (int, float)) for score in scores):
                raise AssertionError("Score column contains non-numeric values")
            if any(score < 0 or score > 10 for score in scores):
                raise AssertionError(
                    f"Score values outside valid range [0,10]: {scores}"
                )

    @staticmethod
    def assert_export_file_naming_convention(
        file_path: Path, ticker: str, strategy: str = None
    ):
        """Assert export file follows naming convention."""
        filename = file_path.name

        # Should contain ticker
        if ticker.replace("/", "_").replace("-", "_") not in filename:
            raise AssertionError(f"Filename should contain ticker {ticker}: {filename}")

        # Should contain strategy if single strategy
        if strategy and len([strategy]) == 1:
            if strategy not in filename:
                raise AssertionError(
                    f"Filename should contain strategy {strategy}: {filename}"
                )

        # Should have .csv extension
        if not filename.endswith(".csv"):
            raise AssertionError(f"Filename should have .csv extension: {filename}")

    @staticmethod
    def assert_cli_command_success(result, expected_messages: List[str] = None):
        """Assert CLI command executed successfully."""
        if result.exit_code != 0:
            raise AssertionError(
                f"CLI command failed with exit code {result.exit_code}. Output: {result.stdout}"
            )

        if expected_messages:
            for message in expected_messages:
                if message not in result.stdout:
                    raise AssertionError(
                        f"Expected message '{message}' not found in output: {result.stdout}"
                    )

    @staticmethod
    def assert_cli_command_failure(result, expected_error_messages: List[str] = None):
        """Assert CLI command failed appropriately."""
        if result.exit_code == 0:
            raise AssertionError(
                f"CLI command should have failed but succeeded. Output: {result.stdout}"
            )

        if expected_error_messages:
            output_lower = result.stdout.lower()
            for error_msg in expected_error_messages:
                if error_msg.lower() not in output_lower:
                    raise AssertionError(
                        f"Expected error message '{error_msg}' not found in output: {result.stdout}"
                    )

    @staticmethod
    def assert_dataframe_equals_with_tolerance(
        df1: pl.DataFrame, df2: pl.DataFrame, tolerance: float = 1e-6
    ):
        """Assert DataFrames are equal with numerical tolerance."""
        if df1.shape != df2.shape:
            raise AssertionError(
                f"DataFrames have different shapes: {df1.shape} vs {df2.shape}"
            )

        if df1.columns != df2.columns:
            raise AssertionError(
                f"DataFrames have different columns: {df1.columns} vs {df2.columns}"
            )

        # Check numerical columns with tolerance
        for col in df1.columns:
            if df1[col].dtype in [pl.Float64, pl.Float32, pl.Int64, pl.Int32]:
                diff = abs(df1[col] - df2[col]).max()
                if diff > tolerance:
                    raise AssertionError(
                        f"Column {col} differs by more than tolerance {tolerance}: max diff = {diff}"
                    )
            else:
                if not df1[col].equals(df2[col]):
                    raise AssertionError(f"Column {col} values are not equal")

    @staticmethod
    def assert_performance_within_bounds(execution_time: float, max_time: float):
        """Assert execution time is within performance bounds."""
        if execution_time > max_time:
            raise AssertionError(
                f"Execution time {execution_time:.2f}s exceeds maximum {max_time:.2f}s"
            )

    @staticmethod
    def assert_memory_usage_reasonable(memory_usage_mb: float, max_memory_mb: float):
        """Assert memory usage is within reasonable bounds."""
        if memory_usage_mb > max_memory_mb:
            raise AssertionError(
                f"Memory usage {memory_usage_mb:.2f}MB exceeds maximum {max_memory_mb:.2f}MB"
            )


# Convenience factory functions
def create_test_workspace() -> Path:
    """Create temporary test workspace with expected directory structure."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create expected directories
    (temp_dir / "data" / "raw" / "portfolios").mkdir(parents=True, exist_ok=True)
    (temp_dir / "data" / "raw" / "portfolios_filtered").mkdir(
        parents=True, exist_ok=True
    )
    (temp_dir / "data" / "raw" / "portfolios_best").mkdir(parents=True, exist_ok=True)
    (temp_dir / "app" / "cli" / "profiles").mkdir(parents=True, exist_ok=True)

    return temp_dir


def create_test_profile(
    workspace: Path, profile_name: str, config_builder: ConfigBuilder
) -> Path:
    """Create test profile file in workspace."""
    profiles_dir = workspace / "app" / "cli" / "profiles"
    profile_file = profiles_dir / f"{profile_name}.yaml"
    return config_builder.save_to_file(profile_file)


# Example usage and integration helpers
class TestingContext:
    """Context manager for comprehensive testing setup."""

    def __init__(self):
        self.workspace = None
        self.cli_runner = CLITestRunner()
        self.data_factory = MockDataFactory()
        self.export_validator = ExportValidator()
        self.config_builder = ConfigBuilder()

    def __enter__(self):
        self.workspace = create_test_workspace()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup workspace
        if self.workspace and self.workspace.exists():
            import shutil

            shutil.rmtree(self.workspace)

    def create_profile(self, name: str) -> ConfigBuilder:
        """Create profile builder for this context."""
        return ConfigBuilder().with_metadata(name)

    def save_profile(self, config_builder: ConfigBuilder) -> Path:
        """Save profile to workspace."""
        profile_name = config_builder.metadata["name"]
        return create_test_profile(self.workspace, profile_name, config_builder)
