"""
Integration Tests for Export System

This module tests the integration of the new export system with existing
components like PortfolioOrchestrator.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.tools.export import ExportContext, ExportFormat, ExportManager
from app.tools.export.adapters import export_csv_adapter, migrate_to_export_manager
from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator


class TestExportIntegration:
    """Test suite for export system integration."""

    @pytest.fixture
    def test_config(self):
        """Test configuration."""
        return {
            "BASE_DIR": "/tmp/test_export_integration",
            "TICKER": "BTC-USD",
            "USE_HOURLY": False,
            "STRATEGY_TYPE": "SMA",
            "SORT_BY": "Total Return [%]",
        }

    @pytest.fixture
    def sample_portfolios(self):
        """Sample portfolio data."""
        return [
            {
                "Ticker": "BTC-USD",
                "Strategy Type": "SMA",
                "Short Window": 10,
                "Long Window": 20,
                "Total Trades": 100,
                "Win Rate [%]": 55.5,
                "Total Return [%]": 125.5,
                "Sharpe Ratio": 1.25,
            },
            {
                "Ticker": "BTC-USD",
                "Strategy Type": "SMA",
                "Short Window": 20,
                "Long Window": 50,
                "Total Trades": 50,
                "Win Rate [%]": 62.0,
                "Total Return [%]": 189.3,
                "Sharpe Ratio": 1.45,
            },
        ]

    def test_orchestrator_with_new_export(self, test_config, sample_portfolios):
        """Test PortfolioOrchestrator using new export system."""
        log = Mock()

        # Create orchestrator with new export enabled
        orchestrator = PortfolioOrchestrator(log, use_new_export=True)

        with (
            patch("pathlib.Path.mkdir"),
            patch("os.access", return_value=True),
            patch("pathlib.Path.exists", return_value=False),
            patch("pathlib.Path.unlink"),
            patch("polars.DataFrame.write_csv") as mock_write_csv,
        ):
            # Test export
            orchestrator._export_results(sample_portfolios, test_config)

            # Verify export was called
            mock_write_csv.assert_called_once()

            # Verify logging
            log.assert_any_call("Using new unified export system", "info")
            assert any(
                "Exported 2 portfolios" in str(call) for call in log.call_args_list
            )

    def test_orchestrator_backward_compatibility(self, test_config, sample_portfolios):
        """Test PortfolioOrchestrator with legacy export (backward compatibility)."""
        log = Mock()

        # Create orchestrator without new export (default)
        orchestrator = PortfolioOrchestrator(log)

        with patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            # Mock the sort_portfolios function to return the input
            with patch(
                "app.tools.portfolio.collection.sort_portfolios",
                return_value=sample_portfolios,
            ):
                # Test export
                orchestrator._export_results(sample_portfolios, test_config)

                # Verify legacy export was called through export_best_portfolios
                mock_export.assert_called_once()

    def test_export_csv_adapter(self, test_config):
        """Test the export_csv adapter function."""
        import polars as pl

        data = pl.DataFrame({"ticker": ["BTC-USD", "ETH-USD"], "trades": [100, 75]})
        log = Mock()

        with (
            patch("pathlib.Path.mkdir"),
            patch("os.access", return_value=True),
            patch("pathlib.Path.exists", return_value=False),
            patch("pathlib.Path.unlink"),
            patch.object(pl.DataFrame, "write_csv"),
        ):
            # Test adapter
            result_df, success = export_csv_adapter(
                data=data,
                feature1="portfolios",
                config=test_config,
                feature2="test",
                log=log,
            )

            assert success is True
            assert isinstance(result_df, pl.DataFrame)
            assert len(result_df) == 2

    def test_migrate_to_export_manager(self, test_config):
        """Test the migration helper function."""
        data = {"test": "data", "count": 42}
        log = Mock()

        with (
            patch("pathlib.Path.mkdir"),
            patch("builtins.open", create=True),
            patch("json.dump"),
        ):
            # Test migration helper
            result = migrate_to_export_manager(
                data=data,
                export_format=ExportFormat.JSON,
                config=test_config,
                feature_path="analysis",
                filename="test_migration.json",
                log=log,
            )

            assert result.success is True
            assert result.path.endswith("test_migration.json")
            assert result.rows_exported == 1

    def test_export_with_date_subdirectory(self, test_config):
        """Test export with date-based subdirectory."""
        manager = ExportManager()
        log = Mock()

        # Enable date subdirectory
        test_config["USE_CURRENT"] = True
        today = datetime.now().strftime("%Y%m%d")

        with (
            patch("pathlib.Path.mkdir") as mock_mkdir,
            patch("os.access", return_value=True),
            patch("builtins.open", create=True),
            patch("json.dump"),
        ):
            context = ExportContext(
                data={"test": "data"},
                format=ExportFormat.JSON,
                feature_path="strategies",
                config=test_config,
                log=log,
            )

            result = manager.export(context)

            assert result.success is True
            assert today in result.path

    def test_synthetic_ticker_export(self, test_config):
        """Test export with synthetic ticker formatting."""
        manager = ExportManager()
        log = Mock()

        # Configure synthetic ticker
        test_config["TICKER"] = ["STRK", "MSTR"]

        with (
            patch("pathlib.Path.mkdir"),
            patch("os.access", return_value=True),
            patch("builtins.open", create=True),
            patch("json.dump"),
        ):
            context = ExportContext(
                data={"ticker": "STRK_MSTR", "data": "test"},
                format=ExportFormat.JSON,
                feature_path="strategies",
                config=test_config,
                log=log,
            )

            result = manager.export(context)

            assert result.success is True
            # Check that filename contains formatted synthetic ticker
            assert "STRK_MSTR" in result.path

    def test_batch_export_integration(self, test_config):
        """Test batch export functionality."""
        manager = ExportManager()
        log = Mock()

        import polars as pl

        # Create multiple datasets
        csv_data = pl.DataFrame({"ticker": ["BTC-USD"], "value": [100]})
        json_data = {"summary": "test", "total": 42}

        with (
            patch("pathlib.Path.mkdir"),
            patch("os.access", return_value=True),
            patch("pathlib.Path.exists", return_value=False),
            patch("pathlib.Path.unlink"),
            patch.object(pl.DataFrame, "write_csv"),
            patch("builtins.open", create=True),
            patch("json.dump"),
        ):
            # Create contexts
            contexts = [
                ExportContext(
                    data=csv_data,
                    format=ExportFormat.CSV,
                    feature_path="data",
                    config=test_config,
                    filename="batch_test.csv",
                    log=log,
                ),
                ExportContext(
                    data=json_data,
                    format=ExportFormat.JSON,
                    feature_path="reports",
                    config=test_config,
                    filename="batch_test.json",
                    log=log,
                ),
            ]

            # Execute batch export
            results = manager.export_batch(contexts)

            assert len(results) == 2
            assert all(r.success for r in results)
            assert results[0].path.endswith(".csv")
            assert results[1].path.endswith(".json")

            # Check batch progress logging
            batch_logs = [
                call for call in log.call_args_list if "Batch export" in str(call)
            ]
            assert len(batch_logs) >= 2


class TestExportSystemRealFiles:
    """Test suite for export system with real file operations."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for tests."""
        test_dir = tmp_path / "export_test"
        test_dir.mkdir()
        return test_dir

    def test_real_csv_export(self, temp_dir):
        """Test actual CSV file export."""
        import polars as pl

        manager = ExportManager()
        log = Mock()

        # Create test data
        df = pl.DataFrame(
            {
                "ticker": ["BTC-USD", "ETH-USD"],
                "trades": [100, 75],
                "win_rate": [0.555, 0.602],
            }
        )

        config = {"BASE_DIR": str(temp_dir), "TICKER": "CRYPTO", "USE_HOURLY": False}

        context = ExportContext(
            data=df,
            format=ExportFormat.CSV,
            feature_path="test_data",
            config=config,
            filename="real_test.csv",
            log=log,
        )

        result = manager.export(context)

        # Verify file was created
        assert result.success is True
        export_file = Path(result.path)
        assert export_file.exists()
        assert export_file.stat().st_size > 0

        # Read back and verify content
        df_read = pl.read_csv(export_file)
        assert len(df_read) == 2
        assert df_read["ticker"][0] == "BTC-USD"
        assert df_read["trades"][1] == 75

    def test_real_json_export(self, temp_dir):
        """Test actual JSON file export."""
        import json

        manager = ExportManager()
        log = Mock()

        # Create test data
        data = {
            "strategy": "MA Cross",
            "results": {"total_trades": 150, "win_rate": 0.58, "profit": 1250.50},
        }

        config = {"BASE_DIR": str(temp_dir), "TICKER": "BTC-USD"}

        context = ExportContext(
            data=data,
            format=ExportFormat.JSON,
            feature_path="reports",
            config=config,
            filename="real_test.json",
            log=log,
            indent=2,
        )

        result = manager.export(context)

        # Verify file was created
        assert result.success is True
        export_file = Path(result.path)
        assert export_file.exists()

        # Read back and verify content
        with open(export_file, "r") as f:
            loaded_data = json.load(f)

        assert loaded_data["strategy"] == "MA Cross"
        assert loaded_data["results"]["total_trades"] == 150
        assert loaded_data["results"]["profit"] == 1250.50
