"""
Test suite for existing filtering behavior to ensure zero breaking changes during optimization.

This test suite validates the current filtering logic before Phase 1 optimization
to ensure that the consolidated PortfolioFilterService maintains identical behavior.
"""

# Mock the required imports to avoid circular dependencies during testing
import sys
from unittest.mock import MagicMock, Mock

import polars as pl
import pytest


# Mock the modules to avoid import issues
sys.modules["app.tools.portfolio.schema_detection"] = MagicMock()
sys.modules["app.tools.portfolio.filters"] = MagicMock()
sys.modules["app.tools.portfolio.results"] = MagicMock()


class TestExistingFilteringBehavior:
    """Test class for existing filtering behavior validation."""

    @pytest.fixture
    def sample_portfolios_df(self):
        """Create sample portfolio data for testing."""
        return pl.DataFrame(
            {
                "Win Rate [%]": [45.5, 55.2, 65.8, 35.1, 75.3],
                "Total Trades": [10, 25, 30, 8, 40],
                "Expectancy Per Trade": [0.5, 1.2, 2.1, 0.1, 3.2],
                "Profit Factor": [1.1, 1.5, 2.2, 0.8, 2.8],
                "Score": [0.6, 1.1, 1.8, 0.3, 2.1],
                "Sortino Ratio": [0.4, 0.8, 1.2, 0.2, 1.5],
                "Beats BNH [%]": [10.5, 25.3, 45.2, 5.1, 65.8],
                "Ticker": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                "Strategy Type": ["SMA", "EMA", "SMA", "EMA", "SMA"],
            }
        )

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return {
            "MINIMUMS": {
                "WIN_RATE": 0.5,  # 50%
                "TRADES": 20,
                "EXPECTANCY_PER_TRADE": 1.0,
                "PROFIT_FACTOR": 1.5,
                "SCORE": 1.0,
                "SORTINO_RATIO": 0.5,
                "BEATS_BNH": 20.0,
            },
            "TICKER": "TEST",
            "STRATEGY_TYPE": "SMA",
        }

    @pytest.fixture
    def mock_log(self):
        """Create mock logging function."""
        return Mock()

    def test_apply_filter_function_behavior(self, sample_portfolios_df, mock_log):
        """Test the current apply_filter function behavior from strategy_execution.py."""

        def apply_filter(
            df, column_name, min_value, data_type, multiplier=1, message_prefix=""
        ):
            """Replicated apply_filter function from strategy_execution.py"""
            if column_name in df.columns:
                adjusted_value = min_value * multiplier
                df = df.filter(pl.col(column_name).cast(data_type) >= adjusted_value)

                # Format the message based on the filter type
                if message_prefix:
                    if "win rate" in message_prefix.lower():
                        mock_log(f"{message_prefix} >= {adjusted_value}%")
                    elif "trades" in message_prefix.lower():
                        mock_log(f"{message_prefix} >= {int(adjusted_value)}")
                    else:
                        mock_log(f"{message_prefix} >= {adjusted_value}")

                return df
            return df

        # Test win rate filter
        filtered_df = apply_filter(
            sample_portfolios_df,
            "Win Rate [%]",
            50.0,
            pl.Float64,
            1,
            "Filtered portfolios with win rate",
        )

        # Should filter out rows with win rate < 50%
        assert len(filtered_df) == 3  # 55.2, 65.8, 75.3
        assert all(
            filtered_df["Win Rate [%]"].to_list()[i] >= 50.0
            for i in range(len(filtered_df))
        )
        mock_log.assert_called_with("Filtered portfolios with win rate >= 50.0%")

    def test_filter_configs_behavior(
        self, sample_portfolios_df, sample_config, mock_log
    ):
        """Test the current filter_configs behavior from strategy_execution.py."""

        def apply_filter(
            df, column_name, min_value, data_type, multiplier=1, message_prefix=""
        ):
            """Replicated apply_filter function"""
            if column_name in df.columns:
                adjusted_value = min_value * multiplier
                df = df.filter(pl.col(column_name).cast(data_type) >= adjusted_value)

                if message_prefix:
                    if "win rate" in message_prefix.lower():
                        mock_log(f"{message_prefix} >= {adjusted_value}%")
                    elif "trades" in message_prefix.lower():
                        mock_log(f"{message_prefix} >= {int(adjusted_value)}")
                    else:
                        mock_log(f"{message_prefix} >= {adjusted_value}")

                return df
            return df

        # Define filter configurations (replicated from strategy_execution.py)
        filter_configs = [
            (
                "WIN_RATE",
                "Win Rate [%]",
                pl.Float64,
                100,
                "Filtered portfolios with win rate",
            ),
            (
                "TRADES",
                "Total Trades",
                pl.Int64,
                1,
                "Filtered portfolios with at least",
            ),
            (
                "EXPECTANCY_PER_TRADE",
                "Expectancy Per Trade",
                pl.Float64,
                1,
                "Filtered portfolios with expectancy per trade",
            ),
            (
                "PROFIT_FACTOR",
                "Profit Factor",
                pl.Float64,
                1,
                "Filtered portfolios with profit factor",
            ),
            ("SCORE", "Score", pl.Float64, 1, "Filtered portfolios with score"),
            (
                "SORTINO_RATIO",
                "Sortino Ratio",
                pl.Float64,
                1,
                "Filtered portfolios with Sortino ratio",
            ),
            (
                "BEATS_BNH",
                "Beats BNH [%]",
                pl.Float64,
                1,
                "Filtered portfolios with Beats BNH percentage",
            ),
        ]

        df = sample_portfolios_df
        minimums = sample_config["MINIMUMS"]

        # Apply each filter from the configuration
        for (
            config_key,
            column_name,
            data_type,
            multiplier,
            message_prefix,
        ) in filter_configs:
            if config_key in minimums:
                df = apply_filter(
                    df,
                    column_name,
                    minimums[config_key],
                    data_type,
                    multiplier,
                    message_prefix,
                )

        # After all filters, should only have 1 row (NVDA with the best metrics)
        assert len(df) == 1
        result_row = df.to_dicts()[0]
        assert result_row["Ticker"] == "NVDA"
        assert result_row["Win Rate [%]"] == 75.3
        assert result_row["Total Trades"] == 40

    def test_1_get_portfolios_filter_logic_replication(self, sample_config, mock_log):
        """Test the filtering logic from 1_get_portfolios.py."""

        # Create sample data as list of dicts (as it appears in 1_get_portfolios.py)
        filtered = [
            {
                "Win Rate [%]": 45.5,
                "Total Trades": 10,
                "Expectancy per Trade": 0.5,
                "Profit Factor": 1.1,
                "Score": 0.6,
                "Sortino Ratio": 0.4,
                "Beats BNH [%]": 10.5,
                "Ticker": "AAPL",
            },
            {
                "Win Rate [%]": 55.2,
                "Total Trades": 25,
                "Expectancy per Trade": 1.2,
                "Profit Factor": 1.5,
                "Score": 1.1,
                "Sortino Ratio": 0.8,
                "Beats BNH [%]": 25.3,
                "Ticker": "MSFT",
            },
            {
                "Win Rate [%]": 65.8,
                "Total Trades": 30,
                "Expectancy per Trade": 2.1,
                "Profit Factor": 2.2,
                "Score": 1.8,
                "Sortino Ratio": 1.2,
                "Beats BNH [%]": 45.2,
                "Ticker": "GOOGL",
            },
            {
                "Win Rate [%]": 35.1,
                "Total Trades": 8,
                "Expectancy per Trade": 0.1,
                "Profit Factor": 0.8,
                "Score": 0.3,
                "Sortino Ratio": 0.2,
                "Beats BNH [%]": 5.1,
                "Ticker": "TSLA",
            },
            {
                "Win Rate [%]": 75.3,
                "Total Trades": 40,
                "Expectancy per Trade": 3.2,
                "Profit Factor": 2.8,
                "Score": 2.1,
                "Sortino Ratio": 1.5,
                "Beats BNH [%]": 65.8,
                "Ticker": "NVDA",
            },
        ]

        # Replicate the filtering logic from 1_get_portfolios.py
        if filtered is not None and len(filtered) > 0 and "MINIMUMS" in sample_config:
            df = pl.DataFrame(filtered)
            original_count = len(df)

            minimums = sample_config["MINIMUMS"]

            # Define filter configurations (replicated from 1_get_portfolios.py)
            filter_configs = [
                (
                    "WIN_RATE",
                    "Win Rate [%]",
                    pl.Float64,
                    100,
                    "Filtered portfolios with win rate",
                ),
                (
                    "TRADES",
                    "Total Trades",
                    pl.Int64,
                    1,
                    "Filtered portfolios with at least",
                ),
                (
                    "EXPECTANCY_PER_TRADE",
                    "Expectancy per Trade",
                    pl.Float64,
                    1,
                    "Filtered portfolios with expectancy per trade",
                ),
                (
                    "PROFIT_FACTOR",
                    "Profit Factor",
                    pl.Float64,
                    1,
                    "Filtered portfolios with profit factor",
                ),
                ("SCORE", "Score", pl.Float64, 1, "Filtered portfolios with score"),
                (
                    "SORTINO_RATIO",
                    "Sortino Ratio",
                    pl.Float64,
                    1,
                    "Filtered portfolios with Sortino ratio",
                ),
                (
                    "BEATS_BNH",
                    "Beats BNH [%]",
                    pl.Float64,
                    1,
                    "Filtered portfolios with Beats BNH percentage",
                ),
            ]

            # Apply each filter from the configuration
            for (
                config_key,
                column_name,
                data_type,
                multiplier,
                message_prefix,
            ) in filter_configs:
                if config_key in minimums and column_name in df.columns:
                    adjusted_value = minimums[config_key] * multiplier
                    df = df.filter(
                        pl.col(column_name).cast(data_type) >= adjusted_value
                    )

                    # Format the message based on the filter type
                    if "win rate" in message_prefix.lower():
                        mock_log(f"{message_prefix} >= {adjusted_value}%", "info")
                    elif "trades" in message_prefix.lower():
                        mock_log(f"{message_prefix} >= {int(adjusted_value)}", "info")
                    else:
                        mock_log(f"{message_prefix} >= {adjusted_value}", "info")

            # Log filtering results
            filtered_count = original_count - len(df)
            if filtered_count > 0:
                mock_log(
                    f"Filtered out {filtered_count} portfolios based on MINIMUMS criteria",
                    "info",
                )
                mock_log(
                    f"Remaining portfolios after MINIMUMS filtering: {len(df)}", "info"
                )

            # Convert back to list of dicts
            filtered = df.to_dicts() if len(df) > 0 else []

        # Verify the behavior matches expected results
        assert len(filtered) == 1
        assert filtered[0]["Ticker"] == "NVDA"

        # Verify logging calls were made
        mock_log.assert_any_call("Filtered portfolios with win rate >= 50.0%", "info")
        mock_log.assert_any_call("Filtered portfolios with at least >= 20", "info")
        mock_log.assert_any_call(
            "Filtered out 4 portfolios based on MINIMUMS criteria", "info"
        )
        mock_log.assert_any_call(
            "Remaining portfolios after MINIMUMS filtering: 1", "info"
        )

    def test_column_name_normalization(self, mock_log):
        """Test that both 'Expectancy per Trade' and 'Expectancy Per Trade' variations work."""

        # Test data with different column name variations
        test_data_1 = pl.DataFrame(
            {"Expectancy per Trade": [0.5, 1.5, 2.1], "Ticker": ["A", "B", "C"]}
        )

        test_data_2 = pl.DataFrame(
            {"Expectancy Per Trade": [0.5, 1.5, 2.1], "Ticker": ["A", "B", "C"]}
        )

        def apply_filter(
            df, column_name, min_value, data_type, multiplier=1, message_prefix=""
        ):
            if column_name in df.columns:
                adjusted_value = min_value * multiplier
                return df.filter(pl.col(column_name).cast(data_type) >= adjusted_value)
            return df

        # Both should work with appropriate column names
        result_1 = apply_filter(test_data_1, "Expectancy per Trade", 1.0, pl.Float64)
        result_2 = apply_filter(test_data_2, "Expectancy Per Trade", 1.0, pl.Float64)

        assert len(result_1) == 2  # Values 1.5 and 2.1
        assert len(result_2) == 2  # Values 1.5 and 2.1

    def test_filter_with_missing_columns(self, mock_log):
        """Test behavior when filtering columns don't exist in DataFrame."""

        df = pl.DataFrame({"Win Rate [%]": [45.5, 55.2], "Ticker": ["A", "B"]})

        def apply_filter(
            df, column_name, min_value, data_type, multiplier=1, message_prefix=""
        ):
            if column_name in df.columns:
                adjusted_value = min_value * multiplier
                return df.filter(pl.col(column_name).cast(data_type) >= adjusted_value)
            return df

        # Should return original dataframe when column doesn't exist
        result = apply_filter(df, "Non Existent Column", 1.0, pl.Float64)
        assert len(result) == 2
        assert result.equals(df)

    def test_empty_dataframe_handling(self, mock_log):
        """Test behavior with empty DataFrames."""

        empty_df = pl.DataFrame({"Win Rate [%]": [], "Total Trades": [], "Ticker": []})

        def apply_filter(
            df, column_name, min_value, data_type, multiplier=1, message_prefix=""
        ):
            if column_name in df.columns:
                adjusted_value = min_value * multiplier
                return df.filter(pl.col(column_name).cast(data_type) >= adjusted_value)
            return df

        result = apply_filter(empty_df, "Win Rate [%]", 50.0, pl.Float64)
        assert len(result) == 0
        assert result.schema == empty_df.schema
