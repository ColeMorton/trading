"""
Integration Tests for Empty Portfolio Export Workflows.

This module tests the complete end-to-end workflows for empty portfolio export
functionality across all three CSV types, ensuring that headers-only CSV files
are created when no portfolio results are found.

These tests use real file operations and verify the actual behavior of the system
when empty portfolios are encountered.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import polars as pl
import pytest

from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator
from app.tools.portfolio.collection import export_best_portfolios
from app.tools.strategy.export_portfolios import export_portfolios


class TestEmptyExportIntegration:
    """Integration tests for empty portfolio export functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def test_config(self, temp_dir):
        """Test configuration with temporary directory."""
        return {
            "BASE_DIR": temp_dir,
            "TICKER": ["TEST"],
            "STRATEGY_TYPES": ["SMA"],
            "STRATEGY_TYPE": "SMA",
            "USE_HOURLY": False,
            "USE_MA": True,
            "SORT_BY": "Total Return [%]",
            "MINIMUMS": {"WIN_RATE": 0.45, "TRADES": 50},
        }

    @pytest.fixture
    def mock_log(self):
        """Mock logging function that collects log messages."""
        log_messages = []

        def log_func(message, level="info"):
            log_messages.append((message, level))

        log_func.messages = log_messages
        return log_func

    def test_export_portfolios_empty_creates_headers_only_file(
        self,
        test_config,
        temp_dir,
        mock_log,
    ):
        """Test that export_portfolios creates headers-only CSV with empty portfolio list."""

        # Call export_portfolios with empty list
        df, success = export_portfolios(
            portfolios=[],
            config=test_config,
            export_type="portfolios",
            log=mock_log,
        )

        # Verify export succeeded
        assert success is True
        assert isinstance(df, pl.DataFrame)
        assert len(df) == 0  # No data rows
        assert len(df.columns) > 0  # Has header columns

        # Verify file was created
        export_path = Path(temp_dir) / "data" / "raw" / "portfolios"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        # Verify file contains only headers
        csv_file = csv_files[0]
        df_read = pl.read_csv(csv_file)
        assert len(df_read) == 0  # No data rows
        assert len(df_read.columns) > 0  # Has header columns

        # Verify expected columns are present
        expected_columns = [
            "Ticker",
            "Strategy Type",
            "Total Trades",
            "Win Rate [%]",
            "Total Return [%]",
        ]
        for col in expected_columns:
            assert col in df_read.columns

    def test_export_portfolios_filtered_empty_creates_headers_only_file(
        self,
        test_config,
        temp_dir,
        mock_log,
    ):
        """Test that export_portfolios creates headers-only CSV for portfolios_filtered."""

        # Call export_portfolios with empty list
        df, success = export_portfolios(
            portfolios=[],
            config=test_config,
            export_type="portfolios_filtered",
            log=mock_log,
        )

        # Verify export succeeded
        assert success is True
        assert isinstance(df, pl.DataFrame)
        assert len(df) == 0  # No data rows
        assert len(df.columns) > 0  # Has header columns

        # Verify file was created
        export_path = Path(temp_dir) / "data" / "raw" / "portfolios_filtered"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        # Verify file contains only headers including Metric Type
        csv_file = csv_files[0]
        df_read = pl.read_csv(csv_file)
        assert len(df_read) == 0  # No data rows
        assert len(df_read.columns) > 0  # Has header columns
        assert "Metric Type" in df_read.columns  # Filtered schema has Metric Type

    def test_export_portfolios_best_empty_creates_headers_only_file(
        self,
        test_config,
        temp_dir,
        mock_log,
    ):
        """Test that export_portfolios skips export for empty portfolios_best."""

        # Call export_portfolios with empty list
        df, success = export_portfolios(
            portfolios=[],
            config=test_config,
            export_type="portfolios_best",
            log=mock_log,
        )

        # Verify export was skipped (new behavior)
        assert success is False  # Changed: now returns False for empty portfolios_best
        assert isinstance(df, pl.DataFrame)
        assert len(df) == 0  # No data rows
        assert len(df.columns) == 0  # No columns since no export happened

        # Verify no file was created (new behavior)
        export_path = Path(temp_dir) / "data" / "raw" / "portfolios_best"
        if export_path.exists():
            csv_files = list(export_path.glob("*.csv"))
            assert len(csv_files) == 0  # No files should be created
        # Directory may not exist if no export happened, which is acceptable

    def test_export_best_portfolios_empty_creates_file(
        self,
        test_config,
        temp_dir,
        mock_log,
    ):
        """Test that export_best_portfolios creates headers-only CSV with empty list."""

        # Call export_best_portfolios with empty list
        result = export_best_portfolios([], test_config, mock_log)

        # Verify function succeeded
        assert result is True

        # Verify appropriate log messages
        log_messages = [msg[0] for msg in mock_log.messages]
        assert any(
            "No portfolios to export - creating headers-only CSV file" in msg
            for msg in log_messages
        )

        # Verify file was created
        export_path = Path(temp_dir) / "data" / "raw" / "portfolios_best"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        # Verify file contains only headers
        csv_file = csv_files[0]
        df_read = pl.read_csv(csv_file)
        assert len(df_read) == 0  # No data rows
        assert len(df_read.columns) > 0  # Has header columns

    def test_portfolio_orchestrator_empty_workflow(
        self,
        test_config,
        temp_dir,
        mock_log,
    ):
        """Test complete PortfolioOrchestrator workflow with empty results."""

        orchestrator = PortfolioOrchestrator(mock_log)

        # Configure to use skip analysis mode (which should work with empty data)
        test_config["skip_analysis"] = True

        # Create empty portfolio files for testing
        portfolios_dir = Path(temp_dir) / "data" / "raw" / "portfolios"
        portfolios_dir.mkdir(parents=True, exist_ok=True)

        # Create empty CSV file that skip analysis would try to load
        empty_csv = portfolios_dir / "TEST_D.csv"
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
        empty_df.write_csv(empty_csv)

        # Run orchestrator
        result = orchestrator.run(test_config)

        # Verify orchestrator succeeded
        assert result is True

        # Verify all three export types were created
        export_dirs = ["portfolios", "portfolios_filtered", "portfolios_best"]

        for export_dir in export_dirs:
            export_path = Path(temp_dir) / "data" / "raw" / export_dir
            assert (
                export_path.exists()
            ), f"Export directory {export_dir} was not created"

            csv_files = list(export_path.glob("*.csv"))
            assert len(csv_files) > 0, f"No CSV files found in {export_dir}"

            # Verify files contain headers but no data
            for csv_file in csv_files:
                df_read = pl.read_csv(csv_file)
                assert len(df_read) == 0, f"Expected empty data in {csv_file}"
                assert len(df_read.columns) > 0, f"Expected headers in {csv_file}"

    def test_all_export_types_with_different_strategies(self, temp_dir, mock_log):
        """Test empty exports work for different strategy types."""

        strategy_types = ["SMA", "EMA", "MACD"]

        for strategy in strategy_types:
            config = {
                "BASE_DIR": temp_dir,
                "TICKER": [f"TEST_{strategy}"],
                "STRATEGY_TYPES": [strategy],
                "STRATEGY_TYPE": strategy,
                "USE_HOURLY": False,
                "USE_MA": True,
            }

            # Test all three export types
            export_types = ["portfolios", "portfolios_filtered", "portfolios_best"]

            for export_type in export_types:
                # Call export_portfolios with empty list
                df, success = export_portfolios(
                    portfolios=[],
                    config=config,
                    export_type=export_type,
                    log=mock_log,
                )

                # Verify export succeeded
                assert success is True, f"Export failed for {strategy} {export_type}"
                assert len(df) == 0  # No data rows
                assert len(df.columns) > 0  # Has header columns

                # Verify file was created
                export_path = Path(temp_dir) / "data" / "raw" / export_type
                csv_files = list(export_path.glob(f"*{strategy}*.csv"))
                assert (
                    len(csv_files) > 0
                ), f"No files created for {strategy} {export_type}"

    def test_multiple_tickers_empty_export(self, temp_dir, mock_log):
        """Test empty export with multiple tickers configuration."""

        config = {
            "BASE_DIR": temp_dir,
            "TICKER": ["TEST1", "TEST2", "TEST3"],
            "STRATEGY_TYPES": ["SMA"],
            "STRATEGY_TYPE": "SMA",
            "USE_HOURLY": False,
            "USE_MA": True,
        }

        # Test with portfolios export
        df, success = export_portfolios(
            portfolios=[],
            config=config,
            export_type="portfolios",
            log=mock_log,
        )

        # Verify export succeeded
        assert success is True
        assert len(df) == 0  # No data rows
        assert len(df.columns) > 0  # Has header columns

        # Verify file was created
        export_path = Path(temp_dir) / "data" / "raw" / "portfolios"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

    def test_empty_export_file_overwrite_behavior(
        self,
        test_config,
        temp_dir,
        mock_log,
    ):
        """Test that empty exports properly overwrite existing files."""

        export_path = Path(temp_dir) / "data" / "raw" / "portfolios"
        export_path.mkdir(parents=True, exist_ok=True)

        # Create existing file with some content
        existing_file = export_path / "TEST_D_SMA.csv"
        existing_content = "Old,Content\n1,2\n"
        existing_file.write_text(existing_content)

        # Verify file exists with old content
        assert existing_file.exists()
        old_content = existing_file.read_text()
        assert "Old,Content" in old_content

        # Export empty portfolios (should overwrite)
        df, success = export_portfolios(
            portfolios=[],
            config=test_config,
            export_type="portfolios",
            log=mock_log,
        )

        # Verify export succeeded
        assert success is True

        # Verify file was overwritten with new headers
        assert existing_file.exists()
        new_content = existing_file.read_text()
        assert "Old,Content" not in new_content  # Old content removed
        assert len(new_content) > 0  # New content added

        # Verify new content is proper CSV with headers
        df_read = pl.read_csv(existing_file)
        assert len(df_read) == 0  # No data rows
        assert len(df_read.columns) > 0  # Has header columns

    def test_empty_export_logging_behavior(self, test_config, temp_dir, mock_log):
        """Test that appropriate log messages are generated for empty exports."""

        # Test export_portfolios logging
        df, success = export_portfolios(
            portfolios=[],
            config=test_config,
            export_type="portfolios",
            log=mock_log,
        )

        assert success is True

        # Check log messages
        log_messages = [msg[0] for msg in mock_log.messages]

        # Should have messages about empty export
        assert any("No portfolios to export" in msg for msg in log_messages)
        assert any("empty CSV with headers only" in msg for msg in log_messages)
        assert any("Successfully exported results" in msg for msg in log_messages)

    def test_empty_export_schema_compliance(self, test_config, temp_dir, mock_log):
        """Test that empty exports maintain proper schema compliance."""

        export_types = ["portfolios", "portfolios_filtered", "portfolios_best"]

        for export_type in export_types:
            # Export empty portfolios
            df, success = export_portfolios(
                portfolios=[],
                config=test_config,
                export_type=export_type,
                log=mock_log,
            )

            assert success is True
            assert len(df) == 0  # No data rows
            assert len(df.columns) > 0  # Has header columns

            # Verify required columns based on export type
            required_columns = [
                "Ticker",
                "Strategy Type",
                "Total Trades",
                "Win Rate [%]",
                "Total Return [%]",
            ]
            for col in required_columns:
                assert col in df.columns, f"Missing {col} in {export_type}"

            # Filtered and best exports should have Metric Type
            if export_type in ["portfolios_filtered", "portfolios_best"]:
                assert (
                    "Metric Type" in df.columns
                ), f"Missing Metric Type in {export_type}"


class TestEmptyExportEdgeCases:
    """Test edge cases for empty portfolio exports."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_log(self):
        """Mock logging function."""
        return Mock()

    def test_empty_export_with_invalid_directory_permissions(self, temp_dir, mock_log):
        """Test empty export behavior with directory permission issues."""

        config = {
            "BASE_DIR": "/invalid/nonexistent/path",
            "TICKER": ["TEST"],
            "STRATEGY_TYPE": "SMA",
            "USE_MA": True,
        }

        # This should handle permission errors gracefully
        df, success = export_portfolios(
            portfolios=[],
            config=config,
            export_type="portfolios",
            log=mock_log,
        )

        # May succeed or fail depending on error handling
        # The important thing is it doesn't crash
        assert isinstance(df, pl.DataFrame)
        assert isinstance(success, bool)

    def test_empty_export_with_missing_config_fields(self, temp_dir, mock_log):
        """Test empty export with minimal configuration."""

        minimal_config = {
            "BASE_DIR": temp_dir,
            "TICKER": ["TEST"],
        }

        # Should handle missing optional fields gracefully
        df, success = export_portfolios(
            portfolios=[],
            config=minimal_config,
            export_type="portfolios",
            log=mock_log,
        )

        # Should succeed with reasonable defaults
        assert isinstance(df, pl.DataFrame)
        assert len(df) == 0  # No data rows

    def test_empty_export_with_different_file_formats(self, temp_dir, mock_log):
        """Test that empty export works with different file naming scenarios."""

        configs = [
            # Standard config
            {
                "BASE_DIR": temp_dir,
                "TICKER": ["STANDARD"],
                "STRATEGY_TYPE": "SMA",
                "USE_MA": True,
            },
            # Synthetic ticker format
            {
                "BASE_DIR": temp_dir,
                "TICKER": ["STRK_MSTR"],
                "STRATEGY_TYPE": "SMA",
                "USE_MA": True,
            },
            # Multiple strategies
            {
                "BASE_DIR": temp_dir,
                "TICKER": ["MULTI"],
                "STRATEGY_TYPES": ["SMA", "EMA"],
                "STRATEGY_TYPE": "SMA",
                "USE_MA": False,  # No strategy suffix for multiple
            },
        ]

        for i, config in enumerate(configs):
            df, success = export_portfolios(
                portfolios=[],
                config=config,
                export_type="portfolios",
                log=mock_log,
            )

            assert success is True, f"Config {i} failed"
            assert len(df) == 0  # No data rows
            assert len(df.columns) > 0  # Has header columns

            # Verify file was created
            export_path = Path(temp_dir) / "data" / "raw" / "portfolios"
            csv_files = list(export_path.glob("*.csv"))
            assert (
                len(csv_files) >= i + 1
            ), f"Expected at least {i+1} files after config {i}"
