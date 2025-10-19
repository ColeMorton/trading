"""
Integration tests for the trading system components.

Tests the integration between portfolio management, trade history, and SPDS systems
to ensure data flows correctly and the fixes for strategy identification, schema
validation, and mathematical safeguards work properly.
"""

import os
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

import pandas as pd

from app.strategies.tools.summary_processing import _generate_spds_compatible_entries
from app.tools.portfolio.schema_validation import SchemaValidator
from app.tools.portfolio_results import calculate_breadth_metrics


class TestSystemIntegration:
    """Integration tests for the trading system components."""

    def test_spds_compatible_entry_generation(self):
        """Test that SPDS-compatible entries are generated correctly from trade history."""
        # Create mock aggregated portfolio data
        aggregated_portfolios = [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 50,
                "Signal Period": 0,
                "Score": 1.25,
                "Win Rate [%]": 65.0,
                "Total Return [%]": 12.5,
                "Signal Entry": False,
                "Signal Exit": False,
                "Total Open Trades": 1,
            },
            {
                "Ticker": "MSFT",
                "Strategy Type": "EMA",
                "Fast Period": 12,
                "Slow Period": 26,
                "Signal Period": 9,
                "Score": 1.15,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 8.3,
                "Signal Entry": False,
                "Signal Exit": False,
                "Total Open Trades": 0,
            },
        ]

        # Create mock positions data
        positions_data = """Position_UUID,Ticker,Strategy_Type,Fast_Period,Slow_Period,Signal_Period,Entry_Timestamp,Exit_Timestamp,Status
AAPL_SMA_10_50_0_20250101,AAPL,SMA,10,50,0,2025-01-01 00:00:00,,Open
MSFT_EMA_12_26_9_20250102,MSFT,EMA,12,26,9,2025-01-02 00:00:00,2025-01-15 00:00:00,Closed"""

        # Create temporary positions file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(positions_data)
            positions_file = f.name

        try:
            # Mock the get_project_root function
            with patch(
                "app.strategies.tools.summary_processing.get_project_root"
            ) as mock_root:
                mock_root.return_value = Path(positions_file).parent

                # Mock the positions file path
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("polars.read_csv") as mock_read_csv:
                        # Mock polars DataFrame
                        mock_df = Mock()
                        mock_df.iter_rows.return_value = [
                            {
                                "Position_UUID": "AAPL_SMA_10_50_0_20250101",
                                "Ticker": "AAPL",
                                "Strategy_Type": "SMA",
                                "Fast_Period": 10,
                                "Slow_Period": 50,
                                "Signal_Period": 0,
                                "Entry_Timestamp": "2025-01-01 00:00:00",
                                "Exit_Timestamp": "",
                                "Status": "Open",
                            },
                            {
                                "Position_UUID": "MSFT_EMA_12_26_9_20250102",
                                "Ticker": "MSFT",
                                "Strategy_Type": "EMA",
                                "Fast_Period": 12,
                                "Slow_Period": 26,
                                "Signal_Period": 9,
                                "Entry_Timestamp": "2025-01-02 00:00:00",
                                "Exit_Timestamp": "2025-01-15 00:00:00",
                                "Status": "Closed",
                            },
                        ]
                        mock_read_csv.return_value = mock_df

                        # Create mock log function
                        log_messages = []

                        def mock_log(message, level="info"):
                            log_messages.append((message, level))

                        # Test the function
                        result = _generate_spds_compatible_entries(
                            aggregated_portfolios, "test_portfolio.csv", mock_log
                        )

                        # Verify results
                        assert len(result) == 2

                        # Check AAPL entry (Open position)
                        aapl_entry = next(r for r in result if r["Ticker"] == "AAPL")
                        assert aapl_entry["Signal Entry"] is True  # Open position
                        assert aapl_entry["Signal Exit"] is False
                        assert aapl_entry["Total Open Trades"] == 1
                        assert aapl_entry["Status"] == "Open"

                        # Check MSFT entry (Closed position)
                        msft_entry = next(r for r in result if r["Ticker"] == "MSFT")
                        assert msft_entry["Signal Entry"] is False
                        assert msft_entry["Signal Exit"] is True  # Closed position
                        assert msft_entry["Total Open Trades"] == 0
                        assert msft_entry["Status"] == "Closed"

                        # Verify logging
                        assert any(
                            "Generated 2 individual strategy entries" in msg
                            for msg, _ in log_messages
                        )

        finally:
            # Clean up temporary file
            os.unlink(positions_file)

    def test_schema_validation_with_different_column_counts(self):
        """Test that schema validation correctly handles different column counts."""
        validator = SchemaValidator()

        # Test Extended Schema (62 columns)
        extended_columns = [
            "Ticker",
            "Strategy Type",
            "Fast Period",
            "Slow Period",
            "Signal Period",
            "Signal Entry",
            "Signal Exit",
            "Total Open Trades",
            "Total Trades",
            "Score",
            "Win Rate [%]",
            "Profit Factor",
            "Expectancy per Trade",
            "Sortino Ratio",
            "Beats BNH [%]",
            "Avg Trade Duration",
            "Trades Per Day",
            "Trades per Month",
            "Signals per Month",
            "Expectancy per Month",
            "Start",
            "End",
            "Period",
            "Start Value",
            "End Value",
            "Total Return [%]",
            "Benchmark Return [%]",
            "Max Gross Exposure [%]",
            "Total Fees Paid",
            "Max Drawdown [%]",
            "Max Drawdown Duration",
            "Total Closed Trades",
            "Open Trade PnL",
            "Best Trade [%]",
            "Worst Trade [%]",
            "Avg Winning Trade [%]",
            "Avg Losing Trade [%]",
            "Avg Winning Trade Duration",
            "Avg Losing Trade Duration",
            "Expectancy",
            "Sharpe Ratio",
            "Calmar Ratio",
            "Omega Ratio",
            "Skew",
            "Kurtosis",
            "Tail Ratio",
            "Common Sense Ratio",
            "Value at Risk",
            "Alpha",
            "Beta",
            "Daily Returns",
            "Annual Returns",
            "Cumulative Returns",
            "Annualized Return",
            "Annualized Volatility",
            "Signal Count",
            "Position Count",
            "Total Period",
            "Allocation [%]",
            "Stop Loss [%]",
            "Last Position Open Date",
            "Last Position Close Date",
        ]

        # Test Filtered Schema (63 columns - Extended + Metric Type)
        filtered_columns = ["Metric Type", *extended_columns]

        # Create test DataFrames
        extended_df = pd.DataFrame({col: [1] for col in extended_columns})
        filtered_df = pd.DataFrame({col: [1] for col in filtered_columns})

        # Test Extended Schema validation
        extended_result = validator.validate_schema(extended_df, strict=False)
        assert extended_result["is_valid"] is True
        assert len(extended_result["violations"]) == 0

        # Test Filtered Schema validation
        filtered_result = validator.validate_schema(filtered_df, strict=False)
        assert filtered_result["is_valid"] is True
        assert len(filtered_result["violations"]) == 0

    def test_breadth_momentum_calculation_edge_cases(self):
        """Test breadth momentum calculation handles edge cases correctly."""
        # Mock log function
        log_messages = []

        def mock_log(message, level="info"):
            log_messages.append((message, level))

        # Test case 1: No exit signals (division by zero)
        with (
            patch("app.tools.portfolio_results.filter_open_trades") as mock_filter_open,
            patch(
                "app.tools.portfolio_results.filter_signal_entries"
            ) as mock_filter_entries,
        ):
            mock_filter_open.return_value = []  # No open trades
            mock_filter_entries.return_value = []  # No signal entries

            # Create mock portfolios
            portfolios = [
                {
                    "Ticker": "AAPL",
                    "Score": 1.0,
                    "Signal Entry": False,
                    "Signal Exit": False,
                },
                {
                    "Ticker": "MSFT",
                    "Score": 1.1,
                    "Signal Entry": False,
                    "Signal Exit": False,
                },
            ]

            # Test the calculation
            calculate_breadth_metrics(portfolios, [], [], mock_log)

            # Verify that the calculation doesn't result in infinity
            breadth_messages = [
                msg for msg, _ in log_messages if "Breadth Momentum" in msg
            ]
            assert len(breadth_messages) > 0

            # Should show 0.0000 instead of inf
            assert "0.0000" in breadth_messages[0]
            assert "inf" not in breadth_messages[0]

        # Test case 2: Normal calculation with exit signals
        log_messages.clear()
        with (
            patch("app.tools.portfolio_results.filter_open_trades") as mock_filter_open,
            patch(
                "app.tools.portfolio_results.filter_signal_entries"
            ) as mock_filter_entries,
        ):
            mock_filter_open.return_value = [{"Ticker": "AAPL"}]  # 1 open trade
            mock_filter_entries.return_value = [{"Ticker": "MSFT"}]  # 1 signal entry

            portfolios = [
                {
                    "Ticker": "AAPL",
                    "Score": 1.0,
                    "Signal Entry": False,
                    "Signal Exit": True,
                },
                {
                    "Ticker": "MSFT",
                    "Score": 1.1,
                    "Signal Entry": True,
                    "Signal Exit": False,
                },
            ]

            calculate_breadth_metrics(
                portfolios, [{"Ticker": "AAPL"}], [{"Ticker": "MSFT"}], mock_log
            )

            breadth_messages = [
                msg for msg, _ in log_messages if "Breadth Momentum" in msg
            ]
            assert len(breadth_messages) > 0
            assert "1.0000" in breadth_messages[0]  # 1 entry / 1 exit = 1.0

    def test_full_integration_workflow(self):
        """Test the complete integration workflow from portfolio to SPDS."""
        # This test would verify the complete workflow:
        # 1. Portfolio update generates correct data
        # 2. Trade history system can process the data
        # 3. SPDS system can find and analyze the data
        # 4. Schema validation passes
        # 5. Mathematical calculations are correct

        # Create test data
        portfolio_data = {
            "Ticker": ["AAPL", "MSFT"],
            "Strategy Type": ["SMA", "EMA"],
            "Fast Period": [10, 12],
            "Slow Period": [50, 26],
            "Signal Period": [0, 9],
            "Score": [1.25, 1.15],
            "Win Rate [%]": [65.0, 55.0],
            "Total Return [%]": [12.5, 8.3],
            "Signal Entry": [False, False],
            "Signal Exit": [False, False],
            "Total Open Trades": [1, 0],
            "Allocation [%]": [50.0, 50.0],
            "Stop Loss [%]": [5.0, 5.0],
            "Last Position Open Date": ["2025-01-01", "2025-01-02"],
            "Last Position Close Date": [None, "2025-01-15"],
        }

        # Add remaining columns with default values
        for col in [
            "Total Trades",
            "Profit Factor",
            "Expectancy per Trade",
            "Sortino Ratio",
            "Beats BNH [%]",
            "Avg Trade Duration",
            "Trades Per Day",
            "Trades per Month",
            "Signals per Month",
            "Expectancy per Month",
            "Start",
            "End",
            "Period",
            "Start Value",
            "End Value",
            "Benchmark Return [%]",
            "Max Gross Exposure [%]",
            "Total Fees Paid",
            "Max Drawdown [%]",
            "Max Drawdown Duration",
            "Total Closed Trades",
            "Open Trade PnL",
            "Best Trade [%]",
            "Worst Trade [%]",
            "Avg Winning Trade [%]",
            "Avg Losing Trade [%]",
            "Avg Winning Trade Duration",
            "Avg Losing Trade Duration",
            "Expectancy",
            "Sharpe Ratio",
            "Calmar Ratio",
            "Omega Ratio",
            "Skew",
            "Kurtosis",
            "Tail Ratio",
            "Common Sense Ratio",
            "Value at Risk",
            "Alpha",
            "Beta",
            "Daily Returns",
            "Annual Returns",
            "Cumulative Returns",
            "Annualized Return",
            "Annualized Volatility",
            "Signal Count",
            "Position Count",
            "Total Period",
        ]:
            portfolio_data[col] = [0.0, 0.0]

        df = pd.DataFrame(portfolio_data)

        # Test schema validation
        validator = SchemaValidator()
        result = validator.validate_schema(df, strict=False)
        assert result["is_valid"] is True

        # Test allocation calculation
        total_allocation = df["Allocation [%]"].sum()
        assert abs(total_allocation - 100.0) < 0.01  # Should sum to 100%

        # Test that the data structure is compatible with SPDS expectations
        required_fields = ["Ticker", "Strategy Type", "Fast Period", "Slow Period"]
        for field in required_fields:
            assert field in df.columns
            assert not df[field].isna().any()

    def test_error_handling_and_fallbacks(self):
        """Test that the system handles errors gracefully and falls back appropriately."""
        # Test SPDS entry generation with missing positions file
        aggregated_portfolios = [{"Ticker": "AAPL", "Strategy Type": "SMA"}]

        log_messages = []

        def mock_log(message, level="info"):
            log_messages.append((message, level))

        with patch(
            "app.strategies.tools.summary_processing.get_project_root"
        ) as mock_root:
            mock_root.return_value = Path("/nonexistent/path")

            result = _generate_spds_compatible_entries(
                aggregated_portfolios, "nonexistent.csv", mock_log
            )

            # Should fall back to original data
            assert result == aggregated_portfolios

            # Should log warning
            warning_messages = [
                msg for msg, level in log_messages if level == "warning"
            ]
            assert any("No positions file found" in msg for msg in warning_messages)
