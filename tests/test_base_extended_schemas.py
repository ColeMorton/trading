"""
Comprehensive test suite for base_extended_schemas.py

Tests schema definitions, transformations, detection, and edge cases
to ensure 100% code coverage and robust schema handling.
"""

from typing import Any, Dict, List

import polars as pl
import pytest

from app.tools.portfolio.base_extended_schemas import (  # Backward compatibility imports
    CANONICAL_COLUMN_COUNT,
    CANONICAL_COLUMN_NAMES,
    CANONICAL_SCHEMA,
    BasePortfolioSchema,
    CanonicalPortfolioSchema,
    ExtendedPortfolioSchema,
    FilteredPortfolioSchema,
    SchemaTransformer,
    SchemaType,
)


class TestSchemaDefinitions:
    """Test schema class definitions and properties."""

    def test_base_schema_properties(self):
        """Test BasePortfolioSchema properties."""
        assert BasePortfolioSchema.get_column_count() == 60
        assert len(BasePortfolioSchema.COLUMNS) == 60

        # Verify key columns exist
        column_names = BasePortfolioSchema.get_column_names()
        assert "Ticker" in column_names
        assert "Total Return [%]" in column_names
        assert "Score" in column_names
        assert "Signal Unconfirmed" in column_names

        # Verify Signal Unconfirmed position (after Signal Exit)
        assert column_names.index("Signal Unconfirmed") == 7
        assert column_names[6] == "Signal Exit"
        assert column_names[8] == "Total Open Trades"

        # Verify new exit parameter columns are present
        assert "Exit Fast Period" in column_names
        assert "Exit Slow Period" in column_names
        assert "Exit Signal Period" in column_names

        # Verify excluded columns are not present
        assert "Allocation [%]" not in column_names
        assert "Stop Loss [%]" not in column_names
        assert "Last Position Open Date" not in column_names
        assert "Metric Type" not in column_names

    def test_extended_schema_properties(self):
        """Test ExtendedPortfolioSchema properties."""
        assert ExtendedPortfolioSchema.get_column_count() == 64
        assert len(ExtendedPortfolioSchema.COLUMNS) == 64

        # Verify it includes base columns plus allocation, stop loss, and position dates
        column_names = ExtendedPortfolioSchema.get_column_names()
        assert "Ticker" in column_names
        assert "Total Return [%]" in column_names
        assert "Score" in column_names
        assert "Exit Fast Period" in column_names
        assert "Exit Slow Period" in column_names
        assert "Exit Signal Period" in column_names
        assert "Allocation [%]" in column_names
        assert "Stop Loss [%]" in column_names
        assert "Last Position Open Date" in column_names
        assert "Last Position Close Date" in column_names

        # Verify metric type is still not present (it's prepended in filtered)
        assert "Metric Type" not in column_names

    def test_filtered_schema_properties(self):
        """Test FilteredPortfolioSchema properties."""
        assert FilteredPortfolioSchema.get_column_count() == 65

        # Verify metric type is first column
        column_names = FilteredPortfolioSchema.get_column_names()
        assert column_names[0] == "Metric Type"

        # Verify it includes all extended columns
        assert "Ticker" in column_names
        assert "Allocation [%]" in column_names
        assert "Stop Loss [%]" in column_names
        assert "Last Position Open Date" in column_names
        assert "Last Position Close Date" in column_names

    def test_column_ordering_consistency(self):
        """Test that column ordering is consistent across schemas."""
        # Extended should have base columns in same order, plus allocation/stop loss/last position date
        base_cols = BasePortfolioSchema.COLUMNS
        extended_cols = ExtendedPortfolioSchema.COLUMNS[
            :60
        ]  # First 60 columns (base with exit params)

        assert base_cols == extended_cols

        # Extended should have allocation, stop loss, and position dates at the end
        extended_names = ExtendedPortfolioSchema.get_column_names()
        assert extended_names[-4:] == [
            "Allocation [%]",
            "Stop Loss [%]",
            "Last Position Open Date",
            "Last Position Close Date",
        ]

        # Filtered should have metric type first, then extended columns
        filtered_names = FilteredPortfolioSchema.get_column_names()
        assert filtered_names[0] == "Metric Type"
        assert filtered_names[1:] == extended_names


class TestBackwardCompatibility:
    """Test backward compatibility with canonical schema constants."""

    def test_canonical_aliases(self):
        """Test that canonical aliases work correctly."""
        assert CANONICAL_SCHEMA == ExtendedPortfolioSchema
        assert CanonicalPortfolioSchema == ExtendedPortfolioSchema
        assert CANONICAL_COLUMN_COUNT == 64
        assert CANONICAL_COLUMN_NAMES == ExtendedPortfolioSchema.get_column_names()

    def test_canonical_usage_patterns(self):
        """Test common usage patterns with canonical constants."""
        # Test accessing column count
        assert CANONICAL_COLUMN_COUNT == len(CANONICAL_COLUMN_NAMES)

        # Test schema class properties
        assert hasattr(CANONICAL_SCHEMA, "COLUMNS")
        assert hasattr(CANONICAL_SCHEMA, "get_column_count")

        # Test column access
        assert "Ticker" in CANONICAL_COLUMN_NAMES
        assert "Allocation [%]" in CANONICAL_COLUMN_NAMES


class TestSchemaTransformer:
    """Test SchemaTransformer functionality."""

    def setup_method(self):
        """Set up test data."""
        self.transformer = SchemaTransformer()

        # Sample base portfolio data (57 columns)
        self.base_portfolio = {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Fast Period": 20,
            "Slow Period": 50,
            "Signal Period": 0,
            "Signal Entry": False,
            "Signal Exit": False,
            "Signal Unconfirmed": "None",
            "Total Open Trades": 0,
            "Total Trades": 100,
            "Score": 1.5,
            "Win Rate [%]": 65.0,
            "Profit Factor": 1.8,
            "Expectancy per Trade": 0.05,
            "Sortino Ratio": 1.2,
            "Beats BNH [%]": 15.0,
            "Avg Trade Duration": "5 days 00:00:00",
            "Trades Per Day": 0.2,
            "Trades per Month": 6.0,
            "Signals per Month": 12.0,
            "Expectancy per Month": 0.3,
            "Start": "2023-01-01",
            "End": "2023-12-31",
            "Period": "365 days 00:00:00",
            "Start Value": 10000.0,
            "End Value": 11500.0,
            "Total Return [%]": 15.0,
            "Benchmark Return [%]": 10.0,
            "Max Gross Exposure [%]": 100.0,
            "Total Fees Paid": 150.0,
            "Max Drawdown [%]": 8.0,
            "Max Drawdown Duration": "30 days 00:00:00",
            "Total Closed Trades": 100,
            "Open Trade PnL": 0.0,
            "Best Trade [%]": 12.0,
            "Worst Trade [%]": -5.0,
            "Avg Winning Trade [%]": 4.0,
            "Avg Losing Trade [%]": -2.0,
            "Avg Winning Trade Duration": "4 days 00:00:00",
            "Avg Losing Trade Duration": "2 days 00:00:00",
            "Expectancy": 0.05,
            "Sharpe Ratio": 1.1,
            "Calmar Ratio": 1.9,
            "Omega Ratio": 1.3,
            "Skew": 0.2,
            "Kurtosis": 3.1,
            "Tail Ratio": 1.1,
            "Common Sense Ratio": 1.2,
            "Value at Risk": 2.5,
            "Daily Returns": 0.041,
            "Annual Returns": 0.15,
            "Cumulative Returns": 0.15,
            "Annualized Return": 0.15,
            "Annualized Volatility": 0.18,
            "Signal Count": 200,
            "Position Count": 100,
            "Total Period": 365.0,
        }

    def test_detect_schema_type_base(self):
        """Test detection of base schema."""
        schema_type = self.transformer.detect_schema_type(self.base_portfolio)
        assert schema_type == SchemaType.BASE

    def test_detect_schema_type_extended(self):
        """Test detection of extended schema."""
        extended_portfolio = self.base_portfolio.copy()
        extended_portfolio["Allocation [%]"] = 25.0
        extended_portfolio["Stop Loss [%]"] = 5.0

        schema_type = self.transformer.detect_schema_type(extended_portfolio)
        assert schema_type == SchemaType.EXTENDED

    def test_detect_schema_type_filtered(self):
        """Test detection of filtered schema."""
        filtered_portfolio = self.base_portfolio.copy()
        filtered_portfolio["Allocation [%]"] = 25.0
        filtered_portfolio["Stop Loss [%]"] = 5.0
        filtered_portfolio["Metric Type"] = "Most Total Return [%]"

        schema_type = self.transformer.detect_schema_type(filtered_portfolio)
        assert schema_type == SchemaType.FILTERED

    def test_detect_schema_type_invalid(self):
        """Test detection of invalid schema."""
        invalid_portfolio = {"Ticker": "AAPL"}  # Too few columns

        schema_type = self.transformer.detect_schema_type(invalid_portfolio)
        assert schema_type == SchemaType.UNKNOWN

    def test_transform_base_to_extended(self):
        """Test transforming base schema to extended."""
        extended = self.transformer.transform_to_extended(
            self.base_portfolio, allocation_pct=25.0, stop_loss_pct=5.0
        )

        # Should have all base columns plus allocation and stop loss
        assert len(extended) == 64
        assert extended["Allocation [%]"] == 25.0
        assert extended["Stop Loss [%]"] == 5.0
        assert extended["Ticker"] == "AAPL"  # Original data preserved

    def test_transform_base_to_filtered(self):
        """Test transforming base schema to filtered."""
        filtered = self.transformer.transform_to_filtered(
            self.base_portfolio,
            metric_type="Most Total Return [%]",
            allocation_pct=25.0,
            stop_loss_pct=5.0,
        )

        # Should have 59 columns with metric type first
        assert len(filtered) == 65
        assert filtered["Metric Type"] == "Most Total Return [%]"
        assert filtered["Allocation [%]"] == 25.0
        assert filtered["Stop Loss [%]"] == 5.0
        assert filtered["Ticker"] == "AAPL"

    def test_transform_extended_to_filtered(self):
        """Test transforming extended schema to filtered."""
        extended_portfolio = self.base_portfolio.copy()
        extended_portfolio["Allocation [%]"] = 25.0
        extended_portfolio["Stop Loss [%]"] = 5.0

        filtered = self.transformer.transform_to_filtered(
            extended_portfolio, metric_type="Most Total Return [%]"
        )

        assert len(filtered) == 65
        assert filtered["Metric Type"] == "Most Total Return [%]"
        assert filtered["Allocation [%]"] == 25.0

    def test_normalize_to_schema_base(self):
        """Test normalizing portfolio to base schema."""
        normalized = self.transformer.normalize_to_schema(
            self.base_portfolio, SchemaType.BASE
        )

        assert len(normalized) == 60
        assert "Allocation [%]" not in normalized
        assert "Stop Loss [%]" not in normalized
        assert "Last Position Open Date" not in normalized
        assert "Last Position Close Date" not in normalized
        assert "Metric Type" not in normalized

    def test_normalize_to_schema_extended(self):
        """Test normalizing portfolio to extended schema."""
        normalized = self.transformer.normalize_to_schema(
            self.base_portfolio,
            SchemaType.EXTENDED,
            allocation_pct=30.0,
            stop_loss_pct=7.0,
        )

        assert len(normalized) == 64
        assert normalized["Allocation [%]"] == 30.0
        assert normalized["Stop Loss [%]"] == 7.0

    def test_normalize_to_schema_filtered(self):
        """Test normalizing portfolio to filtered schema."""
        normalized = self.transformer.normalize_to_schema(
            self.base_portfolio,
            SchemaType.FILTERED,
            metric_type="Mean Score",
            allocation_pct=30.0,
            stop_loss_pct=7.0,
        )

        assert len(normalized) == 65
        assert normalized["Metric Type"] == "Mean Score"
        assert normalized["Allocation [%]"] == 30.0

    def test_get_default_values(self):
        """Test getting default values for missing columns."""
        defaults = self.transformer._get_default_values({})

        # Test key defaults
        assert defaults["Ticker"] == "UNKNOWN"
        assert defaults["Strategy Type"] == "SMA"
        assert defaults["Score"] == 0.0
        assert defaults["Win Rate [%]"] == 50.0
        assert defaults["Allocation [%]"] is None
        assert defaults["Stop Loss [%]"] is None

    def test_missing_columns_handling(self):
        """Test handling of missing columns in transformation."""
        minimal_portfolio = {"Ticker": "AAPL", "Score": 1.5}

        extended = self.transformer.transform_to_extended(
            minimal_portfolio, allocation_pct=25.0, stop_loss_pct=5.0
        )

        # Should have all 60 base columns plus 4 allocation/stop loss columns with defaults for missing ones
        assert len(extended) == 64
        assert extended["Ticker"] == "AAPL"
        assert extended["Score"] == 1.5
        assert extended["Strategy Type"] == "SMA"  # Default
        assert extended["Win Rate [%]"] == 50.0  # Default

    def test_column_ordering_preservation(self):
        """Test that column ordering is preserved during transformation."""
        extended = self.transformer.transform_to_extended(
            self.base_portfolio, allocation_pct=25.0, stop_loss_pct=5.0
        )

        # Check that columns are in correct order
        extended_keys = list(extended.keys())
        expected_keys = ExtendedPortfolioSchema.get_column_names()
        assert extended_keys == expected_keys

    def test_edge_case_empty_portfolio(self):
        """Test handling of empty portfolio."""
        empty_portfolio = {}

        schema_type = self.transformer.detect_schema_type(empty_portfolio)
        assert schema_type == SchemaType.UNKNOWN

        # Transformation should still work with defaults
        extended = self.transformer.transform_to_extended(
            empty_portfolio, allocation_pct=25.0, stop_loss_pct=5.0
        )
        assert len(extended) == 64
        assert extended["Ticker"] == "UNKNOWN"

    def test_edge_case_none_values(self):
        """Test handling of None values in portfolio."""
        portfolio_with_nones = self.base_portfolio.copy()
        portfolio_with_nones["Score"] = None
        portfolio_with_nones["Win Rate [%]"] = None

        extended = self.transformer.transform_to_extended(
            portfolio_with_nones, allocation_pct=25.0, stop_loss_pct=5.0
        )

        # None values should be preserved
        assert extended["Score"] is None
        assert extended["Win Rate [%]"] is None
        assert extended["Ticker"] == "AAPL"  # Non-None values preserved


class TestSchemaValidation:
    """Test schema validation functionality."""

    def setup_method(self):
        """Set up test data."""
        self.transformer = SchemaTransformer()

    def test_validate_base_schema_valid(self):
        """Test validation of valid base schema."""
        valid_base = {
            col: "test_value" for col in BasePortfolioSchema.get_column_names()
        }

        is_valid, errors = self.transformer.validate_schema(valid_base, SchemaType.BASE)
        assert is_valid
        assert len(errors) == 0

    def test_validate_base_schema_invalid(self):
        """Test validation of invalid base schema."""
        invalid_base = {"Ticker": "AAPL", "Score": 1.5}  # Missing columns

        is_valid, errors = self.transformer.validate_schema(
            invalid_base, SchemaType.BASE
        )
        assert not is_valid
        assert len(errors) > 0
        assert any("Missing columns" in error for error in errors)

    def test_validate_extended_schema_valid(self):
        """Test validation of valid extended schema."""
        valid_extended = {
            col: "test_value" for col in ExtendedPortfolioSchema.get_column_names()
        }

        is_valid, errors = self.transformer.validate_schema(
            valid_extended, SchemaType.EXTENDED
        )
        assert is_valid
        assert len(errors) == 0

    def test_validate_filtered_schema_valid(self):
        """Test validation of valid filtered schema."""
        # FilteredPortfolioSchema uses get_column_names() method, not COLUMNS attribute
        valid_filtered = {
            col: "test_value" for col in FilteredPortfolioSchema.get_column_names()
        }

        is_valid, errors = self.transformer.validate_schema(
            valid_filtered, SchemaType.FILTERED
        )
        assert is_valid
        assert len(errors) == 0

    def test_validate_schema_extra_columns(self):
        """Test validation with extra columns."""
        portfolio_with_extra = {
            col: "test_value" for col in BasePortfolioSchema.get_column_names()
        }
        portfolio_with_extra["Extra Column"] = "extra_value"

        is_valid, errors = self.transformer.validate_schema(
            portfolio_with_extra, SchemaType.BASE
        )
        assert not is_valid
        assert any("Extra columns" in error for error in errors)


class TestPolarsIntegration:
    """Test integration with Polars DataFrames."""

    def setup_method(self):
        """Set up test data."""
        self.transformer = SchemaTransformer()

        # Sample DataFrame data
        self.df_data = {
            "Ticker": ["AAPL", "GOOGL"],
            "Strategy Type": ["SMA", "EMA"],
            "Score": [1.5, 1.8],
            "Win Rate [%]": [65.0, 70.0],
            "Total Return [%]": [15.0, 20.0],
        }

    def test_polars_dataframe_detection(self):
        """Test schema detection with Polars DataFrame."""
        df = pl.DataFrame(self.df_data)

        # Add columns to make it look like base schema
        for col in BasePortfolioSchema.get_column_names():
            if col not in df.columns:
                df = df.with_columns(pl.lit(None).alias(col))

        # Test with first row
        first_row = df.row(0, named=True)
        schema_type = self.transformer.detect_schema_type(first_row)
        assert schema_type == SchemaType.BASE

    def test_dataframe_transformation(self):
        """Test transforming DataFrame rows."""
        df = pl.DataFrame(self.df_data)

        # Transform first row to extended schema
        first_row = df.row(0, named=True)
        extended = self.transformer.transform_to_extended(
            first_row, allocation_pct=25.0, stop_loss_pct=5.0
        )

        assert len(extended) == 64
        assert extended["Ticker"] == "AAPL"
        assert extended["Allocation [%]"] == 25.0


class TestPerformance:
    """Test performance characteristics of schema operations."""

    def setup_method(self):
        """Set up test data."""
        self.transformer = SchemaTransformer()

    def test_schema_detection_performance(self):
        """Test that schema detection is fast for large datasets."""
        import time

        # Create large portfolio
        large_portfolio = {
            col: f"value_{i}"
            for i, col in enumerate(BasePortfolioSchema.get_column_names())
        }

        # Time schema detection
        start_time = time.time()
        for _ in range(1000):
            self.transformer.detect_schema_type(large_portfolio)
        end_time = time.time()

        # Should complete 1000 detections in under 1 second
        assert (end_time - start_time) < 1.0

    def test_transformation_performance(self):
        """Test that schema transformation is fast."""
        import time

        base_portfolio = {
            col: f"value_{i}"
            for i, col in enumerate(BasePortfolioSchema.get_column_names())
        }

        # Time transformation
        start_time = time.time()
        for _ in range(100):
            self.transformer.transform_to_extended(
                base_portfolio, allocation_pct=25.0, stop_loss_pct=5.0
            )
        end_time = time.time()

        # Should complete 100 transformations in under 1 second
        assert (end_time - start_time) < 1.0


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=app.tools.portfolio.base_extended_schemas",
            "--cov-report=term-missing",
        ]
    )
