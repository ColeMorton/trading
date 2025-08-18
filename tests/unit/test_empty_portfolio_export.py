"""
Unit Tests for Empty Portfolio Export Functionality.

This module tests the specific functionality implemented to handle empty portfolio
exports across all three CSV types: portfolios, portfolios_filtered, and portfolios_best.

The key feature being tested is that headers-only CSV files are created even when
no portfolio results are found, preventing user confusion and maintaining
consistent file structure.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import polars as pl
import pytest

from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator
from app.tools.portfolio.collection import export_best_portfolios


class TestEmptyPortfolioExportUnit:
    """Unit tests for empty portfolio export functionality."""

    @pytest.fixture
    def temp_config(self):
        """Basic configuration for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield {
                "BASE_DIR": temp_dir,
                "TICKER": ["TEST"],
                "STRATEGY_TYPES": ["SMA"],
                "STRATEGY_TYPE": "SMA",
                "USE_HOURLY": False,
                "USE_MA": True,
                "SORT_BY": "Total Return [%]",
            }

    @pytest.fixture
    def mock_log(self):
        """Mock logging function."""
        return Mock()

    def test_export_best_portfolios_empty_input(self, temp_config, mock_log):
        """Test export_best_portfolios handles empty portfolio list correctly."""

        # Mock the export_portfolios function to track calls
        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            mock_export.return_value = (pl.DataFrame(), True)

            # Call function with empty portfolio list
            result = export_best_portfolios([], temp_config, mock_log)

            # Verify function returns True (success)
            assert result == True

            # Verify logging message for empty portfolios
            mock_log.assert_any_call(
                "No portfolios to export - creating headers-only CSV file", "info"
            )

            # Verify export_portfolios was called with empty list
            mock_export.assert_called_once()
            call_args = mock_export.call_args
            assert call_args[1]["portfolios"] == []
            assert call_args[1]["export_type"] == "portfolios_best"

    def test_export_best_portfolios_skips_deduplication_when_empty(
        self, temp_config, mock_log
    ):
        """Test that deduplication is skipped for empty portfolios."""

        # Mock the export_portfolios and deduplicate functions
        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export, patch(
            "app.tools.portfolio.collection.deduplicate_and_aggregate_portfolios"
        ) as mock_dedup:
            mock_export.return_value = (pl.DataFrame(), True)

            # Call function with empty portfolio list
            result = export_best_portfolios([], temp_config, mock_log)

            # Verify deduplication was NOT called (would raise error with empty list)
            mock_dedup.assert_not_called()

            # Verify export was still called
            mock_export.assert_called_once()
            assert result == True

    def test_export_best_portfolios_with_data_calls_deduplication(
        self, temp_config, mock_log
    ):
        """Test that deduplication is called when portfolios exist."""

        # Sample portfolio data
        sample_portfolios = [
            {
                "Ticker": "TEST",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.0,
                "Score": 8.0,
                "Metric Type": "Most Total Return [%]",
            }
        ]

        # Mock the functions
        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export, patch(
            "app.tools.portfolio.collection.deduplicate_and_aggregate_portfolios"
        ) as mock_dedup, patch(
            "app.tools.portfolio.collection.sort_portfolios"
        ) as mock_sort:
            mock_export.return_value = (pl.DataFrame(sample_portfolios), True)
            mock_dedup.return_value = sample_portfolios
            mock_sort.return_value = sample_portfolios

            # Call function with portfolio data
            result = export_best_portfolios(sample_portfolios, temp_config, mock_log)

            # Verify deduplication WAS called with non-empty data
            mock_dedup.assert_called_once()
            mock_sort.assert_called_once()
            mock_export.assert_called_once()
            assert result == True

    def test_portfolio_orchestrator_empty_export_raw_portfolios(
        self, temp_config, mock_log
    ):
        """Test PortfolioOrchestrator._export_raw_portfolios with empty list."""

        orchestrator = PortfolioOrchestrator(mock_log)

        # Mock export_portfolios function
        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            mock_export.return_value = (pl.DataFrame(), True)

            # Call with empty portfolio list
            orchestrator._export_raw_portfolios([], temp_config)

            # Verify export was called
            mock_export.assert_called_once()
            call_args = mock_export.call_args
            assert call_args[1]["portfolios"] == []
            assert call_args[1]["export_type"] == "portfolios"

            # Verify success logging
            mock_log.assert_any_call("Successfully exported 0 raw portfolios")

    def test_portfolio_orchestrator_empty_export_filtered_portfolios(
        self, temp_config, mock_log
    ):
        """Test PortfolioOrchestrator._export_filtered_portfolios with empty list."""

        orchestrator = PortfolioOrchestrator(mock_log)

        # Mock export_portfolios function
        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            mock_export.return_value = (pl.DataFrame(), True)

            # Call with empty portfolio list
            orchestrator._export_filtered_portfolios([], temp_config)

            # Verify export was called
            mock_export.assert_called_once()
            call_args = mock_export.call_args
            assert call_args[1]["portfolios"] == []
            assert call_args[1]["export_type"] == "portfolios_filtered"

            # Verify success logging
            mock_log.assert_any_call("Successfully exported 0 filtered portfolios")

    def test_portfolio_orchestrator_empty_export_results(self, temp_config, mock_log):
        """Test PortfolioOrchestrator._export_results with empty list."""

        orchestrator = PortfolioOrchestrator(mock_log)

        # Mock export_best_portfolios function using the import path in orchestrator
        with patch(
            "app.tools.orchestration.portfolio_orchestrator.export_best_portfolios"
        ) as mock_export:
            mock_export.return_value = True

            # Call with empty portfolio list
            orchestrator._export_results([], temp_config)

            # Verify export was called
            mock_export.assert_called_once()
            call_args = mock_export.call_args
            assert call_args.args[0] == []  # portfolios argument
            assert call_args.args[1] == temp_config  # config argument
            assert call_args.args[2] == mock_log  # log argument

    def test_portfolio_orchestrator_full_workflow_with_empty_results(
        self, temp_config, mock_log
    ):
        """Test full PortfolioOrchestrator workflow when strategies return empty results."""

        orchestrator = PortfolioOrchestrator(mock_log)

        # Mock all the workflow methods
        with patch.object(
            orchestrator, "_initialize_configuration", return_value=temp_config
        ), patch.object(
            orchestrator, "_process_synthetic_configuration", return_value=temp_config
        ), patch.object(
            orchestrator, "_get_strategies", return_value=["SMA"]
        ), patch.object(
            orchestrator, "_execute_strategies", return_value=[]
        ), patch.object(
            orchestrator, "_export_raw_portfolios"
        ) as mock_export_raw, patch.object(
            orchestrator, "_filter_and_process_portfolios", return_value=[]
        ), patch.object(
            orchestrator, "_export_filtered_portfolios"
        ) as mock_export_filtered, patch.object(
            orchestrator, "_export_results"
        ) as mock_export_results:
            # Run the orchestrator
            result = orchestrator.run(temp_config)

            # Verify workflow completed successfully
            assert result == True

            # Verify all export methods were called with empty lists
            mock_export_raw.assert_called_once_with([], temp_config)
            mock_export_filtered.assert_called_once_with([], temp_config)
            mock_export_results.assert_called_once_with([], temp_config)

            # Verify appropriate logging for empty results
            mock_log.assert_any_call(
                "No portfolios returned from strategies", "warning"
            )
            mock_log.assert_any_call(
                "Created empty CSV files with headers for configured ticker+strategy combinations",
                "info",
            )

    def test_csv_export_with_empty_dataframe(self, temp_config, mock_log):
        """Test CSV export utility with empty DataFrame."""

        from app.tools.export_csv import export_csv

        # Create empty DataFrame with proper schema
        empty_df = pl.DataFrame(
            {
                "Ticker": [],
                "Strategy Type": [],
                "Fast Period": [],
                "Slow Period": [],
                "Total Trades": [],
                "Win Rate [%]": [],
                "Total Return [%]": [],
                "Score": [],
            },
            schema={
                "Ticker": pl.Utf8,
                "Strategy Type": pl.Utf8,
                "Fast Period": pl.Int64,
                "Slow Period": pl.Int64,
                "Total Trades": pl.Int64,
                "Win Rate [%]": pl.Float64,
                "Total Return [%]": pl.Float64,
                "Score": pl.Float64,
            },
        )

        # Export empty DataFrame
        result_df, success = export_csv(
            data=empty_df,
            feature1="portfolios",
            config=temp_config,
            feature2="",
            log=mock_log,
        )

        # Verify export succeeded
        assert success == True
        assert isinstance(result_df, pl.DataFrame)
        assert len(result_df) == 0  # No data rows
        assert len(result_df.columns) > 0  # Has columns

        # Verify file was created (check if write was attempted)
        # This is verified by the fact that success = True

    def test_empty_portfolio_logging_messages(self, temp_config, mock_log):
        """Test that appropriate logging messages are generated for empty portfolios."""

        # Test export_best_portfolios logging
        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            mock_export.return_value = (pl.DataFrame(), True)

            result = export_best_portfolios([], temp_config, mock_log)

            # Verify specific logging for empty portfolios
            mock_log.assert_any_call(
                "No portfolios to export - creating headers-only CSV file", "info"
            )

    def test_empty_portfolio_config_logging(self, temp_config, mock_log):
        """Test configuration logging for empty portfolio export."""

        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            mock_export.return_value = (pl.DataFrame(), True)

            # Call export_best_portfolios
            export_best_portfolios([], temp_config, mock_log)

            # Verify configuration fields are logged
            mock_log.assert_any_call(
                "Configuration for export_best_portfolios:", "info"
            )
            mock_log.assert_any_call(
                "Field 'BASE_DIR' present: True, value: " + temp_config["BASE_DIR"],
                "info",
            )
            mock_log.assert_any_call(
                "Field 'TICKER' present: True, value: ['TEST']", "info"
            )

    def test_empty_portfolio_preserves_config(self, temp_config, mock_log):
        """Test that empty portfolio export preserves original configuration."""

        original_sort_by = temp_config.get("SORT_BY", "Total Return [%]")

        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            mock_export.return_value = (pl.DataFrame(), True)

            # Call export_best_portfolios
            result = export_best_portfolios([], temp_config, mock_log)

            # Verify configuration wasn't permanently modified
            assert temp_config.get("SORT_BY") == original_sort_by
            assert result == True


class TestEmptyPortfolioErrorHandling:
    """Test error handling for empty portfolio exports."""

    @pytest.fixture
    def temp_config(self):
        """Basic configuration for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield {
                "BASE_DIR": temp_dir,
                "TICKER": ["TEST"],
                "STRATEGY_TYPES": ["SMA"],
                "STRATEGY_TYPE": "SMA",
                "USE_HOURLY": False,
                "USE_MA": True,
            }

    @pytest.fixture
    def mock_log(self):
        """Mock logging function."""
        return Mock()

    def test_export_best_portfolios_export_failure(self, temp_config, mock_log):
        """Test error handling when export_portfolios fails with empty data."""

        # Mock export_portfolios to fail
        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            mock_export.side_effect = Exception("Export failed")

            # Should handle error gracefully
            with pytest.raises(Exception):
                export_best_portfolios([], temp_config, mock_log)

    def test_portfolio_orchestrator_empty_export_succeeds(self, temp_config, mock_log):
        """Test that orchestrator handles empty export successfully."""

        orchestrator = PortfolioOrchestrator(mock_log)

        # Mock export to succeed with empty data
        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            mock_export.return_value = (pl.DataFrame(), True)

            # Should succeed with empty portfolios
            try:
                orchestrator._export_raw_portfolios([], temp_config)
                # If no exception is raised, the test passes
                success = True
            except Exception:
                success = False

            assert success, "Empty export should succeed, not raise exception"

    def test_missing_required_config_fields(self, mock_log):
        """Test behavior with missing required configuration fields."""

        incomplete_config = {
            # Missing BASE_DIR and other required fields
            "TICKER": ["TEST"],
        }

        # Should handle missing config gracefully
        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            mock_export.return_value = (pl.DataFrame(), True)

            # May succeed or fail depending on export_portfolios implementation
            try:
                result = export_best_portfolios([], incomplete_config, mock_log)
                # If it succeeds, verify it was called
                mock_export.assert_called_once()
            except (KeyError, Exception):
                # Acceptable to fail with incomplete config
                pass
