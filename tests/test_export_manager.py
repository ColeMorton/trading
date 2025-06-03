"""
Tests for Unified Export Manager

This module tests the ExportManager class and its format-specific handlers.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, call, patch

import pandas as pd
import polars as pl
import pytest

from app.tools.export.formats import CSVExporter, JSONExporter
from app.tools.export.interfaces import ExportContext, ExportFormat
from app.tools.export.manager import ExportManager


class TestExportManager:
    """Test suite for ExportManager functionality."""

    @pytest.fixture
    def export_config(self):
        """Basic export configuration."""
        return {
            "BASE_DIR": "/tmp/test_export",
            "TICKER": "BTC-USD",
            "USE_HOURLY": False,
            "STRATEGY_TYPE": "SMA",
        }

    @pytest.fixture
    def sample_dataframe(self):
        """Sample DataFrame for testing."""
        return pl.DataFrame(
            {
                "Ticker": ["BTC-USD", "BTC-USD"],
                "Strategy Type": ["SMA", "SMA"],
                "Short Window": [10, 20],
                "Long Window": [20, 50],
                "Total Trades": [100, 50],
                "Win Rate [%]": [55.5, 48.2],
            }
        )

    @pytest.fixture
    def sample_dict_data(self):
        """Sample dictionary data for testing."""
        return [
            {"ticker": "BTC-USD", "strategy": "SMA", "trades": 100, "win_rate": 0.555},
            {"ticker": "ETH-USD", "strategy": "EMA", "trades": 75, "win_rate": 0.602},
        ]

    def test_export_manager_initialization(self):
        """Test ExportManager initialization."""
        manager = ExportManager()

        # Check that default exporters are registered
        assert ExportFormat.CSV in manager._exporters
        assert ExportFormat.JSON in manager._exporters
        assert isinstance(manager._exporters[ExportFormat.CSV], CSVExporter)
        assert isinstance(manager._exporters[ExportFormat.JSON], JSONExporter)

    def test_export_csv_with_dataframe(self, export_config, sample_dataframe):
        """Test CSV export with Polars DataFrame."""
        manager = ExportManager()
        log = Mock()

        with patch("os.makedirs"), patch(
            "os.path.exists", return_value=False
        ), patch.object(pl.DataFrame, "write_csv") as mock_write:
            context = ExportContext(
                data=sample_dataframe,
                format=ExportFormat.CSV,
                feature_path="portfolios",
                config=export_config,
                filename="test_export.csv",
                log=log,
            )

            result = manager.export(context)

            assert result.success is True
            assert result.path.endswith("test_export.csv")
            assert result.rows_exported == 2
            mock_write.assert_called_once()

    def test_export_json_with_dict(self, export_config, sample_dict_data):
        """Test JSON export with dictionary data."""
        manager = ExportManager()
        log = Mock()

        with patch("os.makedirs"), patch("os.path.exists", return_value=False), patch(
            "builtins.open", create=True
        ) as mock_open, patch("json.dump") as mock_json_dump:
            context = ExportContext(
                data=sample_dict_data,
                format=ExportFormat.JSON,
                feature_path="strategies",
                config=export_config,
                filename="test_export.json",
                log=log,
            )

            result = manager.export(context)

            assert result.success is True
            assert result.path.endswith("test_export.json")
            assert result.rows_exported == 2
            mock_json_dump.assert_called_once()

    def test_export_with_subdirectory(self, export_config, sample_dataframe):
        """Test export with subdirectory creation."""
        manager = ExportManager()
        log = Mock()

        # Enable date subdirectory
        export_config["USE_CURRENT"] = True

        with patch("pathlib.Path.mkdir") as mock_mkdir, patch(
            "os.access", return_value=True
        ), patch.object(pl.DataFrame, "write_csv"):
            context = ExportContext(
                data=sample_dataframe,
                format=ExportFormat.CSV,
                feature_path="portfolios/portfolios_best",
                config=export_config,
                log=log,
            )

            result = manager.export(context)

            # Check that mkdir was called with parent=True
            mock_mkdir.assert_called_with(parents=True, exist_ok=True)

    def test_export_pandas_dataframe(self, export_config):
        """Test export with Pandas DataFrame."""
        manager = ExportManager()
        log = Mock()

        # Create Pandas DataFrame
        df = pd.DataFrame({"ticker": ["BTC-USD", "ETH-USD"], "trades": [100, 75]})

        with patch("os.makedirs"), patch(
            "os.path.exists", return_value=False
        ), patch.object(pd.DataFrame, "to_csv") as mock_to_csv:
            context = ExportContext(
                data=df,
                format=ExportFormat.CSV,
                feature_path="data",
                config=export_config,
                log=log,
            )

            result = manager.export(context)

            assert result.success is True
            mock_to_csv.assert_called_once_with(result.path, index=False)

    def test_export_with_custom_encoder(self, export_config):
        """Test JSON export with custom encoder."""
        manager = ExportManager()
        log = Mock()

        # Data with special types that need custom encoding
        import numpy as np

        data = {"values": np.array([1.5, 2.5, 3.5]), "count": np.int64(42)}

        class TestEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, np.integer):
                    return int(obj)
                return super().default(obj)

        with patch("os.makedirs"), patch("os.path.exists", return_value=False), patch(
            "builtins.open", create=True
        ) as mock_open, patch("json.dump") as mock_json_dump:
            context = ExportContext(
                data=data,
                format=ExportFormat.JSON,
                feature_path="analysis",
                config=export_config,
                json_encoder=TestEncoder,
                log=log,
            )

            result = manager.export(context)

            assert result.success is True
            # Check that custom encoder was passed
            _, kwargs = mock_json_dump.call_args
            assert kwargs.get("cls") == TestEncoder

    def test_export_error_handling(self, export_config, sample_dataframe):
        """Test error handling during export."""
        manager = ExportManager()
        log = Mock()

        with patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")):
            context = ExportContext(
                data=sample_dataframe,
                format=ExportFormat.CSV,
                feature_path="portfolios",
                config=export_config,
                log=log,
            )

            result = manager.export(context)

            assert result.success is False
            assert "Permission denied" in result.error_message
            # Check that error was logged with correct format
            error_calls = [call for call in log.call_args_list if call[0][1] == "error"]
            assert any(
                "Failed to create directory" in str(call) for call in error_calls
            )

    def test_export_with_filename_formatting(self, export_config):
        """Test automatic filename formatting."""
        manager = ExportManager()
        log = Mock()

        # Test with synthetic ticker
        export_config["TICKER"] = ["STRK", "MSTR"]

        with patch("os.makedirs"), patch("os.path.exists", return_value=False), patch(
            "builtins.open", create=True
        ), patch("json.dump"):
            context = ExportContext(
                data={"test": "data"},
                format=ExportFormat.JSON,
                feature_path="strategies",
                config=export_config,
                log=log,
            )

            result = manager.export(context)

            # Check that synthetic ticker is formatted correctly
            assert "STRK_MSTR" in result.path or result.path.endswith(".json")

    def test_register_custom_exporter(self):
        """Test registering custom exporter."""
        manager = ExportManager()

        # Create custom exporter
        class XMLExporter:
            def export(self, context):
                return {"success": True, "path": "test.xml"}

        xml_exporter = XMLExporter()
        manager.register_exporter("XML", xml_exporter)

        # Check registration
        assert "XML" in manager._exporters
        assert manager._exporters["XML"] == xml_exporter

    def test_batch_export(self, export_config, sample_dataframe):
        """Test batch export to multiple formats."""
        manager = ExportManager()
        log = Mock()

        with patch("os.makedirs"), patch(
            "os.path.exists", return_value=False
        ), patch.object(pl.DataFrame, "write_csv"), patch(
            "builtins.open", create=True
        ), patch(
            "json.dump"
        ):
            # Export to both CSV and JSON
            contexts = [
                ExportContext(
                    data=sample_dataframe,
                    format=ExportFormat.CSV,
                    feature_path="portfolios",
                    config=export_config,
                    filename="test.csv",
                    log=log,
                ),
                ExportContext(
                    data=sample_dataframe.to_dicts(),
                    format=ExportFormat.JSON,
                    feature_path="portfolios",
                    config=export_config,
                    filename="test.json",
                    log=log,
                ),
            ]

            results = manager.export_batch(contexts)

            assert len(results) == 2
            assert all(r.success for r in results)
            assert results[0].path.endswith(".csv")
            assert results[1].path.endswith(".json")


class TestCSVExporter:
    """Test suite for CSV exporter functionality."""

    @pytest.fixture
    def export_config(self):
        """Basic export configuration."""
        return {
            "BASE_DIR": "/tmp/test_export",
            "TICKER": "BTC-USD",
            "USE_HOURLY": False,
            "STRATEGY_TYPE": "SMA",
        }

    def test_csv_column_validation(self, export_config):
        """Test CSV export with column validation."""
        exporter = CSVExporter()
        log = Mock()

        # DataFrame missing some risk metrics
        df = pl.DataFrame(
            {"Ticker": ["BTC-USD"], "Total Trades": [100], "Win Rate [%]": [55.5]}
        )

        with patch("pathlib.Path.mkdir"), patch("os.access", return_value=True), patch(
            "pathlib.Path.exists", return_value=False
        ), patch("pathlib.Path.unlink"), patch.object(pl.DataFrame, "write_csv"):
            context = ExportContext(
                data=df,
                format=ExportFormat.CSV,
                feature_path="portfolios",
                config=export_config,
                log=log,
            )

            result = exporter.export(context)

            # Check that warnings were logged for missing metrics
            warning_calls = [
                call for call in log.call_args_list if call[0][1] == "warning"
            ]
            assert any("Risk metrics missing" in str(call) for call in warning_calls)


class TestJSONExporter:
    """Test suite for JSON exporter functionality."""

    @pytest.fixture
    def export_config(self):
        """Basic export configuration."""
        return {
            "BASE_DIR": "/tmp/test_export",
            "TICKER": "BTC-USD",
            "USE_HOURLY": False,
            "STRATEGY_TYPE": "SMA",
        }

    def test_json_pretty_print(self, export_config):
        """Test JSON export with pretty printing."""
        exporter = JSONExporter()
        log = Mock()

        data = {"test": "data", "nested": {"value": 123}}

        with patch("pathlib.Path.mkdir"), patch(
            "builtins.open", create=True
        ) as mock_open, patch("json.dump") as mock_json_dump:
            context = ExportContext(
                data=data,
                format=ExportFormat.JSON,
                feature_path="config",
                config=export_config,
                indent=4,
                log=log,
            )

            result = exporter.export(context)

            # Check that indent was passed
            _, kwargs = mock_json_dump.call_args
            assert kwargs.get("indent") == 4
