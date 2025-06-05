"""
Test MA Cross API Export Schema Compliance

This test verifies that the MA Cross API service exports CSV files
that conform to the canonical 59-column schema.
"""

import csv
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from app.api.models.ma_cross import MACrossRequest
from app.api.services.ma_cross_service import MACrossService
from app.tools.portfolio.canonical_schema import (
    CANONICAL_COLUMN_COUNT,
    CANONICAL_COLUMN_NAMES,
)


class TestMACrossAPISchemaCompliance:
    """Test that MA Cross API exports conform to canonical schema."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for MACrossService."""
        return {
            "logger": MagicMock(),
            "progress_tracker": MagicMock(),
            "strategy_executor": MagicMock(),
            "strategy_analyzer": MagicMock(),
            "cache": MagicMock(),
            "monitoring": MagicMock(),
            "configuration": MagicMock(),
        }

    @pytest.fixture
    def ma_cross_service(self, mock_dependencies):
        """Create MACrossService instance with mocked dependencies."""
        # Mock the cache to return None (no cached results)
        mock_dependencies["cache"].get.return_value = None

        return MACrossService(**mock_dependencies)

    @pytest.fixture
    def sample_portfolio_data(self) -> List[Dict[str, Any]]:
        """Create sample portfolio data with all canonical columns."""
        return [
            {
                # Core Strategy Configuration
                "Ticker": "BTC-USD",
                "Allocation [%]": 100.0,
                "Strategy Type": "EMA",
                "Short Window": 20,
                "Long Window": 50,
                "Signal Window": 0,
                "Stop Loss [%]": None,
                "Signal Entry": True,
                "Signal Exit": False,
                # Trade Statistics
                "Total Open Trades": 1,
                "Total Trades": 25,
                "Metric Type": "Most Total Return [%]",
                # Performance Metrics
                "Score": 1.8543,
                "Win Rate [%]": 68.0,
                "Profit Factor": 2.345,
                "Expectancy per Trade": 0.0234,
                "Sortino Ratio": 1.567,
                "Beats BNH [%]": 15.67,
                # Timing Metrics
                "Avg Trade Duration": "5 days 12:30:00",
                "Trades Per Day": 0.125,
                "Trades per Month": 3.75,
                "Signals per Month": 7.5,
                "Expectancy per Month": 0.0877,
                # Period Information
                "Start": 0,
                "End": 200,
                "Period": "200 days 00:00:00",
                # Portfolio Values
                "Start Value": 10000.0,
                "End Value": 15678.9,
                "Total Return [%]": 56.789,
                "Benchmark Return [%]": 41.119,
                "Max Gross Exposure [%]": 100.0,
                # Risk and Drawdown
                "Total Fees Paid": 234.56,
                "Max Drawdown [%]": -18.765,
                "Max Drawdown Duration": "23 days 14:30:00",
                "Total Closed Trades": 24,
                # Trade Analysis
                "Open Trade PnL": 123.45,
                "Best Trade [%]": 12.345,
                "Worst Trade [%]": -8.765,
                "Avg Winning Trade [%]": 3.456,
                "Avg Losing Trade [%]": -2.345,
                "Avg Winning Trade Duration": "4 days 08:15:00",
                "Avg Losing Trade Duration": "2 days 16:45:00",
                # Advanced Metrics
                "Expectancy": 0.5432,
                "Sharpe Ratio": 1.234,
                "Calmar Ratio": 0.987,
                "Omega Ratio": 1.456,
                # Risk Metrics (Critical)
                "Skew": -0.234,
                "Kurtosis": 3.456,
                "Tail Ratio": 1.123,
                "Common Sense Ratio": 1.234,
                "Value at Risk": -0.0456,
                "Daily Returns": 0.00234,
                "Annual Returns": 0.5678,
                "Cumulative Returns": 0.5679,
                "Annualized Return": 0.5680,
                "Annualized Volatility": 0.2345,
                # Signal and Position Counts
                "Signal Count": 50,
                "Position Count": 25,
                "Total Period": 200.0,
            }
        ]

    @pytest.mark.asyncio
    async def test_ma_cross_api_export_schema_compliance(
        self, ma_cross_service, sample_portfolio_data, tmp_path
    ):
        """Test that MA Cross API exports conform to canonical 59-column schema."""
        # Create a temporary directory for exports
        export_dir = tmp_path / "csv" / "portfolios_best"
        export_dir.mkdir(parents=True)

        # Mock the execute_strategy to return our sample data
        with patch(
            "app.strategies.ma_cross.tools.strategy_execution.execute_strategy"
        ) as mock_execute:
            mock_execute.return_value = sample_portfolio_data

            # Mock the config to use our temp directory
            with patch("app.api.config.get_config") as mock_config:
                mock_config.return_value = {"BASE_DIR": str(tmp_path)}

                # Create request
                request = MACrossRequest(
                    ticker="BTC-USD",
                    strategy_types=["EMA"],
                    windows=89,
                    direction="Long",
                )

                # Execute analysis
                response = await ma_cross_service.analyze_portfolio(request)

                # Verify response contains portfolios
                assert response.status == "success"
                assert response.portfolios is not None
                assert len(response.portfolios) > 0

        # Check for exported CSV files
        csv_files = list(export_dir.glob("*.csv"))
        assert len(csv_files) > 0, "No CSV files were exported"

        # Verify each exported CSV file
        for csv_file in csv_files:
            with open(csv_file, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                # Verify column count
                assert (
                    len(headers) == CANONICAL_COLUMN_COUNT
                ), f"Expected {CANONICAL_COLUMN_COUNT} columns, got {len(headers)}"

                # Verify column names match canonical schema
                assert (
                    headers == CANONICAL_COLUMN_NAMES
                ), f"Column names don't match canonical schema"

                # Read at least one row to ensure data is present
                rows = list(reader)
                assert len(rows) > 0, "CSV file has no data rows"

                # Verify critical risk metrics are present in the data
                first_row = rows[0]
                risk_metrics = [
                    "Skew",
                    "Kurtosis",
                    "Tail Ratio",
                    "Common Sense Ratio",
                    "Value at Risk",
                ]

                for metric in risk_metrics:
                    assert (
                        metric in first_row
                    ), f"Risk metric '{metric}' missing from exported data"
                    # Verify the value is not empty
                    assert (
                        first_row[metric] != ""
                    ), f"Risk metric '{metric}' has empty value"

    @pytest.mark.asyncio
    async def test_ma_cross_api_preserves_all_columns(
        self, ma_cross_service, sample_portfolio_data, tmp_path
    ):
        """Test that API preserves all columns from source data during export."""
        # Add some extra columns to verify they're preserved
        extra_columns = {
            "Custom Metric 1": 123.456,
            "Custom Metric 2": "Test Value",
        }

        enhanced_portfolio_data = [
            {**portfolio, **extra_columns} for portfolio in sample_portfolio_data
        ]

        # Mock the execute_strategy to return enhanced data
        with patch(
            "app.strategies.ma_cross.tools.strategy_execution.execute_strategy"
        ) as mock_execute:
            mock_execute.return_value = enhanced_portfolio_data

            # Mock the config
            with patch("app.api.config.get_config") as mock_config:
                mock_config.return_value = {"BASE_DIR": str(tmp_path)}

                # Create request
                request = MACrossRequest(
                    ticker="BTC-USD",
                    strategy_types=["EMA"],
                )

                # Execute analysis
                response = await ma_cross_service.analyze_portfolio(request)

                # The response should still be successful
                assert response.status == "success"

        # Verify the exported CSV contains all canonical columns
        export_dir = tmp_path / "csv" / "portfolios_best"
        csv_files = list(export_dir.glob("*.csv"))

        for csv_file in csv_files:
            with open(csv_file, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                # Should have exactly the canonical columns (extra columns may be dropped)
                assert len(headers) == CANONICAL_COLUMN_COUNT
                assert headers == CANONICAL_COLUMN_NAMES

    def test_canonical_schema_constants(self):
        """Verify canonical schema constants are correct."""
        assert CANONICAL_COLUMN_COUNT == 59
        assert len(CANONICAL_COLUMN_NAMES) == 59
        assert CANONICAL_COLUMN_NAMES[0] == "Ticker"
        assert CANONICAL_COLUMN_NAMES[1] == "Allocation [%]"
        assert CANONICAL_COLUMN_NAMES[-1] == "Total Period"

        # Verify critical risk metrics are in the schema
        risk_metrics = [
            "Skew",
            "Kurtosis",
            "Tail Ratio",
            "Common Sense Ratio",
            "Value at Risk",
            "Daily Returns",
            "Annual Returns",
            "Cumulative Returns",
            "Annualized Return",
            "Annualized Volatility",
        ]

        for metric in risk_metrics:
            assert (
                metric in CANONICAL_COLUMN_NAMES
            ), f"Risk metric '{metric}' not in canonical schema"
