"""
Comprehensive Schema Validation Tests for CSV Exports.

This test suite validates that exported CSV files match expected schemas:
- Column presence and ordering
- Data types and formats
- Metric type preservation
- Schema compliance across all export types
- File format validation (actual CSV reading)
- Regression prevention for schema issues
"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import polars as pl
import pytest

from app.tools.strategy.export_portfolios import export_portfolios


class TestExportedCSVSchemaValidation:
    """Test actual CSV file schema validation."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for export testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def sample_portfolio_data(self):
        """Sample portfolio data with diverse metric types."""
        return [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.5,
                "Profit Factor": 1.35,
                "Expectancy per Trade": 0.025,
                "Sortino Ratio": 1.15,
                "Beats BNH [%]": 8.2,
                "Sharpe Ratio": 1.2,
                "Score": 8.5,
                "Metric Type": "Most Total Return [%]",
                "Max Drawdown [%]": 12.3,
                "Calmar Ratio": 2.07,
                "Skew": 0.25,
                "Kurtosis": 3.1,
                "Tail Ratio": 1.15,
                "Common Sense Ratio": 1.08,
                "Value at Risk": -3.2,
                "Daily Returns": 0.098,
                "Annual Returns": 24.8,
                "Cumulative Returns": 25.5,
                "Annualized Return": 23.9,
                "Annualized Volatility": 19.9,
            },
            {
                "Ticker": "MSFT",
                "Strategy Type": "EMA",
                "Fast Period": 12,
                "Slow Period": 26,
                "Total Trades": 45,
                "Win Rate [%]": 62.0,
                "Total Return [%]": 32.1,
                "Profit Factor": 1.52,
                "Expectancy per Trade": 0.035,
                "Sortino Ratio": 1.28,
                "Beats BNH [%]": 12.5,
                "Sharpe Ratio": 1.4,
                "Score": 9.0,
                "Metric Type": "Most Sharpe Ratio",
                "Max Drawdown [%]": 9.8,
                "Calmar Ratio": 3.27,
                "Skew": 0.18,
                "Kurtosis": 2.9,
                "Tail Ratio": 1.22,
                "Common Sense Ratio": 1.12,
                "Value at Risk": -2.8,
                "Daily Returns": 0.125,
                "Annual Returns": 31.2,
                "Cumulative Returns": 32.1,
                "Annualized Return": 30.5,
                "Annualized Volatility": 21.8,
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "MACD",
                "Fast Period": 12,
                "Slow Period": 26,
                "Signal Period": 9,
                "Total Trades": 38,
                "Win Rate [%]": 68.0,
                "Total Return [%]": 45.3,
                "Profit Factor": 1.78,
                "Expectancy per Trade": 0.048,
                "Sortino Ratio": 1.45,
                "Beats BNH [%]": 18.7,
                "Sharpe Ratio": 1.6,
                "Score": 9.8,
                "Metric Type": "Most Win Rate [%]",
                "Max Drawdown [%]": 7.2,
                "Calmar Ratio": 6.29,
                "Skew": 0.32,
                "Kurtosis": 3.3,
                "Tail Ratio": 1.35,
                "Common Sense Ratio": 1.18,
                "Value at Risk": -2.1,
                "Daily Returns": 0.165,
                "Annual Returns": 43.8,
                "Cumulative Returns": 45.3,
                "Annualized Return": 42.1,
                "Annualized Volatility": 26.3,
            },
        ]

    @pytest.fixture
    def base_config(self, temp_export_dir):
        """Base configuration for exports."""
        return {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["AAPL", "MSFT", "GOOGL"],
            "STRATEGY_TYPES": ["SMA", "EMA", "MACD"],
            "USE_HOURLY": False,
            "USE_MA": False,  # Multiple strategies
            "STRATEGY_TYPE": "Multi",
        }

    def read_csv_file(self, file_path):
        """Helper to read CSV file and return both pandas and polars versions."""
        df_pandas = pd.read_csv(file_path)
        df_polars = pl.read_csv(file_path)
        return df_pandas, df_polars

    def test_portfolios_csv_schema_validation(
        self,
        sample_portfolio_data,
        base_config,
        temp_export_dir,
    ):
        """Test that portfolios CSV export matches extended schema."""
        config = base_config.copy()

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=sample_portfolio_data,
                config=config,
                export_type="portfolios",
                log=Mock(),
            )

        assert success is True

        # Find the exported CSV file
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        # Read the actual CSV file
        csv_file = csv_files[0]
        df_pandas, df_polars = self.read_csv_file(csv_file)

        # Verify file has correct number of rows
        assert len(df_pandas) == 3
        assert len(df_polars) == 3

        # Verify key columns are present
        expected_columns = [
            "Ticker",
            "Strategy Type",
            "Fast Period",
            "Slow Period",
            "Total Trades",
            "Win Rate [%]",
            "Total Return [%]",
            "Sharpe Ratio",
            "Score",
        ]
        for col in expected_columns:
            assert col in df_pandas.columns
            assert col in df_polars.columns

        # Verify data types are correct
        assert df_pandas["Total Trades"].dtype in ["int64", "Int64"]
        assert df_pandas["Win Rate [%]"].dtype in ["float64", "Float64"]
        assert df_pandas["Ticker"].dtype == "object"

        # Verify specific values are preserved
        assert "AAPL" in df_pandas["Ticker"].values
        assert "MSFT" in df_pandas["Ticker"].values
        assert "GOOGL" in df_pandas["Ticker"].values

    def test_portfolios_filtered_csv_schema_validation(
        self,
        sample_portfolio_data,
        base_config,
        temp_export_dir,
    ):
        """Test that portfolios_filtered CSV export matches filtered schema."""
        config = base_config.copy()

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=sample_portfolio_data,
                config=config,
                export_type="portfolios_filtered",
                log=Mock(),
            )

        assert success is True

        # Find the exported CSV file
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_filtered"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        # Read the actual CSV file
        csv_file = csv_files[0]
        df_pandas, df_polars = self.read_csv_file(csv_file)

        # Verify file has correct number of rows
        assert len(df_pandas) == 3

        # Verify Metric Type column is present and first
        assert "Metric Type" in df_pandas.columns
        assert df_pandas.columns[0] == "Metric Type"

        # Verify metric type values are preserved correctly
        metric_types = df_pandas["Metric Type"].unique()
        assert "Most Total Return [%]" in metric_types
        assert "Most Sharpe Ratio" in metric_types
        assert "Most Win Rate [%]" in metric_types

        # Verify other required columns are present
        expected_columns = [
            "Ticker",
            "Strategy Type",
            "Fast Period",
            "Slow Period",
            "Total Trades",
            "Win Rate [%]",
            "Total Return [%]",
            "Sharpe Ratio",
            "Score",
        ]
        for col in expected_columns:
            assert col in df_pandas.columns

        # Verify the CSV has more columns than basic portfolios (filtered schema)
        assert len(df_pandas.columns) > 50  # Filtered schema should have 63 columns

    def test_portfolios_best_csv_schema_validation(
        self,
        sample_portfolio_data,
        base_config,
        temp_export_dir,
    ):
        """Test that portfolios_best CSV export matches best schema with timestamp."""
        config = base_config.copy()

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=sample_portfolio_data,
                config=config,
                export_type="portfolios_best",
                log=Mock(),
            )

        assert success is True

        # Find the exported CSV file
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_best"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        # Verify filename contains timestamp
        csv_file = csv_files[0]
        filename = csv_file.name
        assert any(char.isdigit() for char in filename)  # Contains timestamp

        # Read the actual CSV file
        df_pandas, df_polars = self.read_csv_file(csv_file)

        # Verify file has correct number of rows
        assert len(df_pandas) == 3

        # Verify Metric Type column is present and preserved
        assert "Metric Type" in df_pandas.columns
        metric_types = df_pandas["Metric Type"].tolist()
        assert "Most Total Return [%]" in metric_types
        assert "Most Sharpe Ratio" in metric_types
        assert "Most Win Rate [%]" in metric_types

        # Verify analysis-specific columns have appropriate defaults
        if "Allocation [%]" in df_pandas.columns:
            # Should be None/null for analysis exports
            allocation_values = df_pandas["Allocation [%]"].dropna()
            assert len(allocation_values) == 0  # All should be null

        # Verify required columns are present
        expected_columns = [
            "Ticker",
            "Strategy Type",
            "Fast Period",
            "Slow Period",
            "Total Trades",
            "Win Rate [%]",
            "Total Return [%]",
            "Sharpe Ratio",
            "Score",
            "Metric Type",
        ]
        for col in expected_columns:
            assert col in df_pandas.columns

    def test_csv_column_ordering_consistency(
        self,
        sample_portfolio_data,
        base_config,
        temp_export_dir,
    ):
        """Test that CSV column ordering is consistent and follows canonical order."""
        config = base_config.copy()
        export_types = ["portfolios", "portfolios_filtered", "portfolios_best"]
        csv_column_orders = {}

        for export_type in export_types:
            with patch("app.tools.strategy.export_portfolios.logging_context"):
                df, success = export_portfolios(
                    portfolios=sample_portfolio_data,
                    config=config,
                    export_type=export_type,
                    log=Mock(),
                )

            assert success is True

            # Find and read the exported CSV file
            export_path = Path(temp_export_dir) / "data" / "raw" / export_type
            csv_files = list(export_path.glob("*.csv"))
            assert len(csv_files) > 0

            df_pandas, _ = self.read_csv_file(csv_files[0])
            csv_column_orders[export_type] = df_pandas.columns.tolist()

        # Verify filtered and best exports have Metric Type as first column
        assert csv_column_orders["portfolios_filtered"][0] == "Metric Type"
        assert csv_column_orders["portfolios_best"][0] == "Metric Type"

        # Verify common columns appear in consistent relative order
        common_columns = [
            "Ticker",
            "Strategy Type",
            "Fast Period",
            "Slow Period",
            "Score",
        ]

        for i, col in enumerate(common_columns[:-1]):
            next_col = common_columns[i + 1]

            for export_type in export_types:
                columns = csv_column_orders[export_type]
                if col in columns and next_col in columns:
                    col_idx = columns.index(col)
                    next_col_idx = columns.index(next_col)
                    # Next column should appear after current column
                    assert (
                        next_col_idx > col_idx
                    ), f"Column order violated in {export_type}: {col} -> {next_col}"

    def test_csv_data_type_preservation(
        self,
        sample_portfolio_data,
        base_config,
        temp_export_dir,
    ):
        """Test that data types are preserved correctly in CSV export."""
        config = base_config.copy()

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=sample_portfolio_data,
                config=config,
                export_type="portfolios_filtered",
                log=Mock(),
            )

        assert success is True

        # Find and read the exported CSV file
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_filtered"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        df_pandas, df_polars = self.read_csv_file(csv_files[0])

        # Test string columns
        string_columns = ["Ticker", "Strategy Type", "Metric Type"]
        for col in string_columns:
            if col in df_pandas.columns:
                assert df_pandas[col].dtype == "object"

        # Test numeric columns
        numeric_columns = ["Total Trades", "Fast Period", "Slow Period"]
        for col in numeric_columns:
            if col in df_pandas.columns:
                assert df_pandas[col].dtype in ["int64", "Int64", "float64", "Float64"]

        # Test percentage columns
        percentage_columns = ["Win Rate [%]", "Total Return [%]", "Max Drawdown [%]"]
        for col in percentage_columns:
            if col in df_pandas.columns:
                assert df_pandas[col].dtype in ["float64", "Float64"]

        # Test that numeric values are actually numeric (not strings)
        assert isinstance(df_pandas["Total Trades"].iloc[0], int | float)
        assert isinstance(df_pandas["Win Rate [%]"].iloc[0], int | float)

    def test_csv_special_values_handling(self, base_config, temp_export_dir):
        """Test that special values (None, NaN, inf) are handled correctly in CSV."""
        # Create portfolio data with special values
        special_portfolio = [
            {
                "Ticker": "TEST",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.5,
                "Sharpe Ratio": float("inf"),  # Infinity
                "Score": 8.5,
                "Metric Type": "Most Total Return [%]",
                "Max Drawdown [%]": None,  # None value
                "Allocation [%]": None,  # None value
                "Stop Loss [%]": None,  # None value
                "Skew": float("nan"),  # NaN value
            },
        ]

        config = base_config.copy()
        config["TICKER"] = ["TEST"]

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=special_portfolio,
                config=config,
                export_type="portfolios_filtered",
                log=Mock(),
            )

        assert success is True

        # Find and read the exported CSV file
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_filtered"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        df_pandas, _ = self.read_csv_file(csv_files[0])

        # Verify file can be read without errors
        assert len(df_pandas) == 1

        # Verify special values are handled appropriately
        # None values should become NaN in pandas
        if "Max Drawdown [%]" in df_pandas.columns:
            assert pd.isna(df_pandas["Max Drawdown [%]"].iloc[0])

        # Verify the CSV file is well-formed
        with open(csv_files[0]) as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) >= 2  # Header + at least one data row

    def test_csv_metric_type_aggregation_preservation(
        self,
        base_config,
        temp_export_dir,
    ):
        """Test that aggregated metric types are preserved correctly in CSV."""
        # Create portfolio data that would trigger aggregation
        aggregated_portfolios = [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.5,
                "Sharpe Ratio": 1.2,
                "Score": 8.5,
                "Metric Type": "Most Total Return [%], Most Sharpe Ratio",  # Compound metric type
            },
            {
                "Ticker": "MSFT",
                "Strategy Type": "EMA",
                "Fast Period": 12,
                "Slow Period": 26,
                "Total Trades": 45,
                "Win Rate [%]": 62.0,
                "Total Return [%]": 32.1,
                "Sharpe Ratio": 1.4,
                "Score": 9.0,
                "Metric Type": "Most Win Rate [%], Most Profit Factor",  # Compound metric type
            },
        ]

        config = base_config.copy()
        config["TICKER"] = ["AAPL", "MSFT"]

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=aggregated_portfolios,
                config=config,
                export_type="portfolios_best",
                log=Mock(),
            )

        assert success is True

        # Find and read the exported CSV file
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_best"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        df_pandas, _ = self.read_csv_file(csv_files[0])

        # Verify compound metric types are preserved
        assert len(df_pandas) == 2
        metric_types = df_pandas["Metric Type"].tolist()

        # Check that compound metric types are preserved
        compound_metrics_found = any("," in str(mt) for mt in metric_types)
        if compound_metrics_found:
            # If aggregation was applied, compound metrics should be preserved
            assert any("Most Total Return [%]" in str(mt) for mt in metric_types)
            assert any("Most Sharpe Ratio" in str(mt) for mt in metric_types)

    def test_csv_large_dataset_schema_validation(self, base_config, temp_export_dir):
        """Test schema validation with large dataset to ensure scalability."""
        # Create large portfolio dataset
        large_portfolios = []
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"] * 20  # 100 tickers

        for i, ticker in enumerate(tickers):
            portfolio = {
                "Ticker": ticker,
                "Strategy Type": ["SMA", "EMA", "MACD"][i % 3],
                "Fast Period": 10 + (i % 10),
                "Slow Period": 20 + (i % 20),
                "Total Trades": 30 + (i % 50),
                "Win Rate [%]": 50.0 + (i % 30),
                "Total Return [%]": 10.0 + (i % 40),
                "Sharpe Ratio": 1.0 + (i % 10) * 0.1,
                "Score": 5.0 + (i % 50) * 0.1,
                "Metric Type": [
                    "Most Total Return [%]",
                    "Most Sharpe Ratio",
                    "Most Win Rate [%]",
                ][i % 3],
            }
            large_portfolios.append(portfolio)

        config = base_config.copy()
        config["TICKER"] = tickers[:5]  # First 5 unique tickers

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=large_portfolios,
                config=config,
                export_type="portfolios_filtered",
                log=Mock(),
            )

        assert success is True

        # Find and read the exported CSV file
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_filtered"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        df_pandas, df_polars = self.read_csv_file(csv_files[0])

        # Verify large dataset is handled correctly
        assert len(df_pandas) == 100
        assert len(df_polars) == 100

        # Verify schema is maintained for large dataset
        assert "Metric Type" in df_pandas.columns
        assert df_pandas.columns[0] == "Metric Type"

        # Verify data integrity
        assert len(df_pandas["Ticker"].unique()) <= 5  # Max 5 unique tickers
        assert len(df_pandas["Strategy Type"].unique()) <= 3  # Max 3 strategy types
        assert all(isinstance(score, int | float) for score in df_pandas["Score"])

    def test_csv_encoding_and_formatting(
        self,
        sample_portfolio_data,
        base_config,
        temp_export_dir,
    ):
        """Test that CSV files are properly encoded and formatted."""
        config = base_config.copy()

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=sample_portfolio_data,
                config=config,
                export_type="portfolios",
                log=Mock(),
            )

        assert success is True

        # Find the exported CSV file
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        csv_file = csv_files[0]

        # Test file encoding
        with open(csv_file, encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 0

        # Test CSV format compliance
        with open(csv_file, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

            # Should have header + data rows
            assert len(rows) >= 4  # Header + 3 data rows

            # Header should not be empty
            header = rows[0]
            assert len(header) > 0
            assert all(col.strip() for col in header)  # No empty column names

            # Data rows should have same number of columns as header
            for i, row in enumerate(rows[1:], 1):
                assert len(row) == len(
                    header,
                ), f"Row {i} has {len(row)} columns, expected {len(header)}"

        # Test that file can be read by both pandas and polars without errors
        df_pandas = pd.read_csv(csv_file)
        df_polars = pl.read_csv(csv_file)

        assert len(df_pandas) == len(df_polars) == 3
        assert list(df_pandas.columns) == df_polars.columns
