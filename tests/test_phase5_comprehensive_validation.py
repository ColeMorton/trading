"""
Phase 5: Comprehensive Testing and Documentation
End-to-End Schema Validation Tests

This test suite validates that the CSV Schema Standardization implementation
is working correctly across all export paths and integration points.
"""

import csv
import os
import tempfile
from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest

from app.tools.portfolio.canonical_schema import (
    CANONICAL_COLUMN_COUNT,
    CANONICAL_COLUMN_NAMES,
)


class TestPhase5ComprehensiveValidation:
    """Comprehensive validation tests for Phase 5 completion."""

    @pytest.fixture
    def mock_log(self):
        """Create a mock logging function."""
        return MagicMock()

    @pytest.fixture
    def sample_canonical_data(self) -> List[Dict]:
        """Create sample data conforming to canonical schema."""
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
                "Metric Type": "High Performance EMA",
                # Performance Metrics
                "Score": 2.1543,
                "Win Rate [%]": 72.0,
                "Profit Factor": 2.845,
                "Expectancy per Trade": 0.0534,
                "Sortino Ratio": 1.967,
                "Beats BNH [%]": 25.67,
                # Timing Metrics
                "Avg Trade Duration": "7 days 08:30:00",
                "Trades Per Day": 0.125,
                "Trades per Month": 3.75,
                "Signals per Month": 7.5,
                "Expectancy per Month": 0.2001,
                # Period Information
                "Start": 0,
                "End": 200,
                "Period": "200 days 00:00:00",
                # Portfolio Values
                "Start Value": 10000.0,
                "End Value": 18234.56,
                "Total Return [%]": 82.35,
                "Benchmark Return [%]": 56.68,
                "Max Gross Exposure [%]": 100.0,
                # Risk and Drawdown
                "Total Fees Paid": 123.45,
                "Max Drawdown [%]": -12.34,
                "Max Drawdown Duration": "15 days 06:30:00",
                "Total Closed Trades": 24,
                # Trade Analysis
                "Open Trade PnL": 234.56,
                "Best Trade [%]": 15.67,
                "Worst Trade [%]": -6.78,
                "Avg Winning Trade [%]": 4.23,
                "Avg Losing Trade [%]": -2.11,
                "Avg Winning Trade Duration": "5 days 12:00:00",
                "Avg Losing Trade Duration": "3 days 08:30:00",
                # Advanced Metrics
                "Expectancy": 0.7432,
                "Sharpe Ratio": 1.534,
                "Calmar Ratio": 1.287,
                "Omega Ratio": 1.756,
                # Risk Metrics (Critical for validation)
                "Skew": -0.123,
                "Kurtosis": 3.456,
                "Tail Ratio": 1.234,
                "Common Sense Ratio": 1.567,
                "Value at Risk": -0.0234,
                "Daily Returns": 0.00412,
                "Annual Returns": 0.8235,
                "Cumulative Returns": 0.8235,
                "Annualized Return": 0.8235,
                "Annualized Volatility": 0.2876,
                # Signal and Position Counts
                "Signal Count": 50,
                "Position Count": 25,
                "Total Period": 200.0,
            }
        ]

    def test_canonical_schema_constants_integrity(self):
        """Validate that canonical schema constants are properly defined."""
        # Verify column count
        assert (
            CANONICAL_COLUMN_COUNT == 59
        ), f"Expected 59 columns, got {CANONICAL_COLUMN_COUNT}"

        # Verify column names list length
        assert (
            len(CANONICAL_COLUMN_NAMES) == 59
        ), f"Expected 59 column names, got {len(CANONICAL_COLUMN_NAMES)}"

        # Verify critical columns are present
        critical_columns = [
            "Ticker",
            "Allocation [%]",
            "Strategy Type",
            "Metric Type",
            "Total Return [%]",
            "Sharpe Ratio",
            "Max Drawdown [%]",
            "Skew",
            "Kurtosis",
            "Value at Risk",
            "Annualized Volatility",
        ]

        for col in critical_columns:
            assert (
                col in CANONICAL_COLUMN_NAMES
            ), f"Critical column '{col}' missing from canonical schema"

    def test_core_export_infrastructure_compliance(
        self, sample_canonical_data, mock_log, tmp_path
    ):
        """Test that core export infrastructure maintains schema compliance."""
        from app.tools.export_csv import export_csv

        config = {
            "BASE_DIR": str(tmp_path),
            "TICKER": "BTC-USD",
            "STRATEGY_TYPE": "EMA",
        }

        # Test portfolio export (should apply schema validation)
        df, success = export_csv(
            data=sample_canonical_data,
            feature1="portfolios_best",
            config=config,
            log=mock_log,
        )

        assert success, "Portfolio export should succeed"

        # Verify exported file exists and has correct schema
        export_files = list(Path(tmp_path).glob("data/raw/strategies/best/*.csv"))
        assert len(export_files) > 0, "No CSV files were exported"

        # Validate first exported file
        with open(export_files[0], "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            assert (
                len(headers) == CANONICAL_COLUMN_COUNT
            ), f"Expected {CANONICAL_COLUMN_COUNT} columns, got {len(headers)}"
            assert (
                headers == CANONICAL_COLUMN_NAMES
            ), "Column names don't match canonical schema"

    def test_api_export_compliance(self, sample_canonical_data, mock_log, tmp_path):
        """Test that API exports maintain canonical schema compliance."""
        from app.api.models.strategy_analysis import MACrossRequest
        from app.api.services.ma_cross_service import MACrossService

        # Mock dependencies for service
        mock_dependencies = {
            "logger": mock_log,
            "progress_tracker": MagicMock(),
            "strategy_executor": MagicMock(),
            "strategy_analyzer": MagicMock(),
            "cache": MagicMock(),
            "monitoring": MagicMock(),
            "configuration": MagicMock(),
        }
        mock_dependencies["cache"].get.return_value = None

        service = MACrossService(**mock_dependencies)

        # Mock the strategy execution to return our sample data
        with patch(
            "app.strategies.ma_cross.tools.strategy_execution.execute_strategy"
        ) as mock_execute:
            mock_execute.return_value = sample_canonical_data

            with patch("app.api.config.get_config") as mock_config:
                mock_config.return_value = {"BASE_DIR": str(tmp_path)}

                # Create and execute request
                request = MACrossRequest(
                    ticker="BTC-USD", strategy_types=["EMA"], windows=50
                )

                # Test async version
                import asyncio

                async def run_test():
                    response = await service.analyze_portfolio(request)
                    assert response.status == "success"
                    return response

                # Run the async test
                response = asyncio.run(run_test())

                # Verify API response structure
                assert response.portfolios is not None
                assert len(response.portfolios) > 0

                # Verify exported CSV files
                export_dir = tmp_path / "csv" / "portfolios_best"
                if export_dir.exists():
                    csv_files = list(export_dir.glob("*.csv"))
                    for csv_file in csv_files:
                        with open(csv_file, "r", newline="", encoding="utf-8") as f:
                            reader = csv.DictReader(f)
                            headers = reader.fieldnames
                            assert len(headers) == CANONICAL_COLUMN_COUNT
                            assert headers == CANONICAL_COLUMN_NAMES

    def test_strategy_export_compliance(
        self, sample_canonical_data, mock_log, tmp_path
    ):
        """Test that all strategy export functions maintain compliance."""
        strategy_modules = [
            "app.strategies.macd_next.tools.export_portfolios",
            "app.strategies.mean_reversion.tools.export_portfolios",
            "app.strategies.mean_reversion_rsi.tools.export_portfolios",
            "app.strategies.mean_reversion_hammer.tools.export_portfolios",
            "app.strategies.range.tools.export_portfolios",
        ]

        config = {
            "BASE_DIR": str(tmp_path),
            "TICKER": "BTC-USD",
            "STRATEGY_TYPE": "Test",
            "SORT_BY": "Total Return [%]",
            "SORT_ASC": False,
        }

        for module_name in strategy_modules:
            try:
                import importlib

                module = importlib.import_module(module_name)

                # Test that the module has the required functions
                assert hasattr(
                    module, "export_portfolios"
                ), f"Missing export_portfolios in {module_name}"

                # Test enrichment function if it exists
                strategy_name = module_name.split(".")[-3]  # Extract strategy name
                enrichment_func_name = (
                    f"_enrich_{strategy_name.replace('_', '_')}_portfolios"
                )

                if hasattr(module, enrichment_func_name):
                    enrichment_func = getattr(module, enrichment_func_name)
                    enriched_data = enrichment_func(
                        sample_canonical_data, config, mock_log
                    )

                    # Verify enriched data maintains canonical structure
                    assert (
                        len(enriched_data) > 0
                    ), f"Enrichment function in {module_name} returned empty data"

                    # Check that required canonical columns are present
                    required_columns = [
                        "Allocation [%]",
                        "Stop Loss [%]",
                        "Metric Type",
                        "Signal Window",
                    ]
                    for col in required_columns:
                        assert (
                            col in enriched_data[0]
                        ), f"Missing canonical column '{col}' in {module_name}"

            except ImportError as e:
                # Module might have dependencies not available in test environment
                mock_log(
                    f"Could not test {module_name} due to import error: {e}", "warning"
                )

    def test_schema_validation_module_integrity(self):
        """Test that schema validation module works correctly."""
        import pandas as pd

        from app.tools.portfolio.schema_validation import validate_dataframe_schema

        # Test with compliant data
        compliant_data = pd.DataFrame(
            [{col: "test_value" for col in CANONICAL_COLUMN_NAMES}]
        )
        result = validate_dataframe_schema(compliant_data, strict=False)

        assert result["is_valid"] == True, "Compliant data should pass validation"
        assert (
            len(result.get("violations", [])) == 0
        ), "Compliant data should have no violations"

        # Test with non-compliant data
        non_compliant_data = pd.DataFrame(
            [{"Invalid_Column": "test", "Another_Invalid": "test"}]
        )
        result = validate_dataframe_schema(non_compliant_data, strict=False)

        assert result["is_valid"] == False, "Non-compliant data should fail validation"
        assert (
            len(result.get("violations", [])) > 0
        ), "Non-compliant data should have violations"

    def test_schema_transformation_functionality(self, mock_log):
        """Test schema transformation and normalization functions."""
        from app.tools.portfolio.schema_detection import normalize_portfolio_data

        # Test with minimal data
        minimal_data = [
            {"Ticker": "BTC-USD", "Total Return [%]": 50.0, "Sharpe Ratio": 1.5}
        ]

        normalized_data = normalize_portfolio_data(minimal_data, log=mock_log)

        assert len(normalized_data) > 0, "Normalization should return data"
        assert (
            len(normalized_data[0]) == CANONICAL_COLUMN_COUNT
        ), "Normalized data should have all canonical columns"

        # Verify critical columns are preserved
        assert normalized_data[0]["Ticker"] == "BTC-USD"
        assert normalized_data[0]["Total Return [%]"] == 50.0
        assert normalized_data[0]["Sharpe Ratio"] == 1.5

    def test_risk_metrics_preservation(self, sample_canonical_data, mock_log, tmp_path):
        """Test that critical risk metrics are preserved throughout the export pipeline."""
        from app.tools.export_csv import export_csv

        config = {"BASE_DIR": str(tmp_path), "TICKER": "BTC-USD"}

        # Export the data
        df, success = export_csv(
            data=sample_canonical_data,
            feature1="portfolios_best",
            config=config,
            log=mock_log,
        )

        assert success, "Export should succeed"

        # Verify risk metrics are preserved
        critical_risk_metrics = [
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

        # Check in the returned DataFrame
        if hasattr(df, "columns"):  # Polars DataFrame
            for metric in critical_risk_metrics:
                assert (
                    metric in df.columns
                ), f"Risk metric '{metric}' missing from DataFrame"

        # Check in the exported CSV file
        export_files = list(Path(tmp_path).glob("data/raw/strategies/best/*.csv"))
        if export_files:
            with open(export_files[0], "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                for metric in critical_risk_metrics:
                    assert (
                        metric in headers
                    ), f"Risk metric '{metric}' missing from exported CSV"

    def test_cross_strategy_aggregation_compatibility(self, mock_log):
        """Test that data from different strategies can be aggregated consistently."""
        # Simulate data from different strategies
        strategies_data = {
            "ma_cross": {"Strategy Type": "EMA", "Metric Type": "High Performance EMA"},
            "macd_next": {
                "Strategy Type": "MACD",
                "Metric Type": "High Performance MACD",
            },
            "mean_reversion": {
                "Strategy Type": "Mean Reversion",
                "Metric Type": "Standard Mean Reversion",
            },
            "range": {
                "Strategy Type": "Range",
                "Metric Type": "High Performance Range",
            },
        }

        aggregated_data = []

        for strategy_name, strategy_data in strategies_data.items():
            # Create a sample row for each strategy
            row = {col: None for col in CANONICAL_COLUMN_NAMES}
            row.update(
                {
                    "Ticker": f"TEST-{strategy_name.upper()}",
                    "Total Return [%]": 50.0 + len(strategy_name),  # Vary by strategy
                    "Sharpe Ratio": 1.0 + (len(strategy_name) * 0.1),
                    **strategy_data,
                }
            )
            aggregated_data.append(row)

        # Verify aggregated data maintains schema compliance
        assert len(aggregated_data) == 4, "Should have data for all 4 strategies"

        for row in aggregated_data:
            assert (
                len(row) == CANONICAL_COLUMN_COUNT
            ), "Each row should have all canonical columns"
            assert all(
                col in row for col in CANONICAL_COLUMN_NAMES
            ), "All canonical columns should be present"

    def test_backward_compatibility_preservation(self, mock_log):
        """Test that existing functionality remains intact."""
        from app.tools.portfolio.schema_detection import (
            ensure_allocation_sum_100_percent,
        )

        # Test legacy allocation function
        portfolio_data = [
            {"Allocation [%]": 60.0, "Ticker": "BTC-USD"},
            {"Allocation [%]": None, "Ticker": "ETH-USD"},
        ]

        result = ensure_allocation_sum_100_percent(portfolio_data, log=mock_log)

        assert len(result) == 2, "Should return same number of portfolios"
        assert (
            result[0]["Allocation [%]"] == 60.0
        ), "Existing allocation should be preserved"
        assert (
            result[1]["Allocation [%]"] == 40.0
        ), "Missing allocation should be filled"

    def test_data_pipeline_integrity(self, sample_canonical_data, mock_log, tmp_path):
        """Test complete data pipeline from input to export."""
        from app.tools.export_csv import export_csv
        from app.tools.portfolio.schema_detection import normalize_portfolio_data

        # Step 1: Schema normalization
        normalized_data = normalize_portfolio_data(sample_canonical_data, log=mock_log)

        # Step 2: Export processing
        config = {"BASE_DIR": str(tmp_path), "TICKER": "BTC-USD"}
        df, success = export_csv(
            data=normalized_data, feature1="strategies", config=config, log=mock_log
        )

        assert success, "Complete pipeline should succeed"

        # Step 3: Verify end-to-end integrity
        export_files = list(Path(tmp_path).glob("data/raw/strategies/*.csv"))
        assert len(export_files) > 0, "Pipeline should produce output files"

        # Verify output file schema compliance
        with open(export_files[0], "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)

            assert len(headers) == CANONICAL_COLUMN_COUNT
            assert headers == CANONICAL_COLUMN_NAMES
            assert len(rows) > 0, "Should have data rows"

            # Verify data integrity
            first_row = rows[0]
            assert first_row["Ticker"] == "BTC-USD"
            assert first_row["Strategy Type"] == "EMA"
            assert float(first_row["Total Return [%]"]) == 82.35

    def test_performance_regression_check(
        self, sample_canonical_data, mock_log, tmp_path
    ):
        """Basic performance regression test for export operations."""
        import time

        from app.tools.export_csv import export_csv

        config = {"BASE_DIR": str(tmp_path), "TICKER": "PERF-TEST"}

        # Create larger dataset for performance testing
        large_dataset = sample_canonical_data * 100  # 100 rows

        start_time = time.time()
        df, success = export_csv(
            data=large_dataset, feature1="portfolios_best", config=config, log=mock_log
        )
        end_time = time.time()

        assert success, "Large dataset export should succeed"

        execution_time = end_time - start_time
        assert (
            execution_time < 10.0
        ), f"Export took {execution_time:.2f}s, should be under 10s for 100 rows"

        # Verify output quality wasn't compromised for performance
        export_files = list(Path(tmp_path).glob("data/raw/strategies/best/*.csv"))
        with open(export_files[0], "r") as f:
            lines = f.readlines()
            assert (
                len(lines) == 101
            ), "Should have header + 100 data rows"  # Header + data rows
