"""
Unit tests for equity memory optimizer functionality.

This module tests the memory optimization capabilities including streaming,
chunking, and data type optimization for equity data export operations.
"""

from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from app.tools.equity_data_extractor import EquityData
from app.tools.equity_memory_optimizer import (
    EquityDataOptimizer,
    MemoryOptimizationConfig,
    StreamingEquityExporter,
    analyze_memory_requirements,
    create_memory_efficient_export_function,
)


@pytest.mark.integration
class TestMemoryOptimizationConfig:
    """Test MemoryOptimizationConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MemoryOptimizationConfig()

        assert config.enable_streaming is True
        assert config.chunk_size == 50
        assert config.enable_garbage_collection is True
        assert config.optimize_data_types is True
        assert config.memory_threshold_mb == 1000.0
        assert config.enable_progress_logging is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = MemoryOptimizationConfig(
            enable_streaming=False,
            chunk_size=25,
            enable_garbage_collection=False,
            optimize_data_types=False,
            memory_threshold_mb=500.0,
            enable_progress_logging=False,
        )

        assert config.enable_streaming is False
        assert config.chunk_size == 25
        assert config.enable_garbage_collection is False
        assert config.optimize_data_types is False
        assert config.memory_threshold_mb == 500.0
        assert config.enable_progress_logging is False


@pytest.mark.integration
class TestEquityDataOptimizer:
    """Test EquityDataOptimizer functionality."""

    def create_sample_equity_data(self, size: int = 100) -> EquityData:
        """Create sample equity data for testing."""
        timestamp = pd.date_range("2023-01-01", periods=size, freq="D")
        return EquityData(
            timestamp=timestamp,
            equity=np.array(range(size), dtype=np.float64),
            equity_pct=np.array(range(size), dtype=np.float64) / 100,
            equity_change=np.ones(size, dtype=np.float64),
            equity_change_pct=np.ones(size, dtype=np.float64),
            drawdown=np.zeros(size, dtype=np.float64),
            drawdown_pct=np.zeros(size, dtype=np.float64),
            peak_equity=np.array(range(size), dtype=np.float64),
            mfe=np.array(range(size), dtype=np.float64),
            mae=np.zeros(size, dtype=np.float64),
        )

    def test_optimize_equity_data_float64_to_float32(self):
        """Test optimization of float64 arrays to float32."""
        equity_data = self.create_sample_equity_data(50)

        # Ensure original data is float64
        assert equity_data.equity.dtype == np.float64

        optimizer = EquityDataOptimizer()
        optimized_data = optimizer.optimize_equity_data(equity_data)

        # Check that float arrays were optimized (if precision allows)
        # Note: The optimization depends on whether the values can be safely converted
        assert optimized_data.timestamp.equals(equity_data.timestamp)
        assert len(optimized_data.equity) == len(equity_data.equity)

        # Values should be approximately equal even if type changed
        np.testing.assert_array_almost_equal(
            optimized_data.equity,
            equity_data.equity,
            decimal=5,
        )

    def test_optimize_equity_data_large_values(self):
        """Test optimization with values that cannot be safely downcasted."""
        timestamp = pd.date_range("2023-01-01", periods=10, freq="D")

        # Create data with large values that would lose precision in float32
        large_values = np.array(
            [1e10, 2e10, 3e10, 4e10, 5e10, 6e10, 7e10, 8e10, 9e10, 1e11],
            dtype=np.float64,
        )

        equity_data = EquityData(
            timestamp=timestamp,
            equity=large_values,
            equity_pct=large_values / 1e8,
            equity_change=large_values,
            equity_change_pct=large_values / 1e8,
            drawdown=np.zeros(10, dtype=np.float64),
            drawdown_pct=np.zeros(10, dtype=np.float64),
            peak_equity=large_values,
            mfe=large_values,
            mae=np.zeros(10, dtype=np.float64),
        )

        optimizer = EquityDataOptimizer()
        optimized_data = optimizer.optimize_equity_data(equity_data)

        # Large values should remain float64 to preserve precision
        assert optimized_data.equity.dtype == np.float64
        np.testing.assert_array_equal(optimized_data.equity, equity_data.equity)

    def test_estimate_memory_usage(self):
        """Test memory usage estimation."""
        equity_data = self.create_sample_equity_data(1000)

        optimizer = EquityDataOptimizer()
        memory_mb = optimizer.estimate_memory_usage(equity_data)

        # Should return a positive value
        assert memory_mb > 0

        # Larger datasets should use more memory
        large_equity_data = self.create_sample_equity_data(10000)
        large_memory_mb = optimizer.estimate_memory_usage(large_equity_data)

        assert large_memory_mb > memory_mb

    def test_estimate_memory_usage_different_types(self):
        """Test memory estimation with different data types."""
        timestamp = pd.date_range("2023-01-01", periods=100, freq="D")

        # Float64 data
        float64_data = EquityData(
            timestamp=timestamp,
            equity=np.ones(100, dtype=np.float64),
            equity_pct=np.ones(100, dtype=np.float64),
            equity_change=np.ones(100, dtype=np.float64),
            equity_change_pct=np.ones(100, dtype=np.float64),
            drawdown=np.ones(100, dtype=np.float64),
            drawdown_pct=np.ones(100, dtype=np.float64),
            peak_equity=np.ones(100, dtype=np.float64),
            mfe=np.ones(100, dtype=np.float64),
            mae=np.ones(100, dtype=np.float64),
        )

        # Float32 data
        float32_data = EquityData(
            timestamp=timestamp,
            equity=np.ones(100, dtype=np.float32),
            equity_pct=np.ones(100, dtype=np.float32),
            equity_change=np.ones(100, dtype=np.float32),
            equity_change_pct=np.ones(100, dtype=np.float32),
            drawdown=np.ones(100, dtype=np.float32),
            drawdown_pct=np.ones(100, dtype=np.float32),
            peak_equity=np.ones(100, dtype=np.float32),
            mfe=np.ones(100, dtype=np.float32),
            mae=np.ones(100, dtype=np.float32),
        )

        optimizer = EquityDataOptimizer()
        float64_memory = optimizer.estimate_memory_usage(float64_data)
        float32_memory = optimizer.estimate_memory_usage(float32_data)

        # Float64 should use more memory than float32
        assert float64_memory > float32_memory


@pytest.mark.integration
class TestStreamingEquityExporter:
    """Test StreamingEquityExporter functionality."""

    def create_test_portfolios(self, count: int) -> list:
        """Create test portfolios for streaming tests."""
        portfolios = []
        for i in range(count):
            timestamp = pd.date_range("2023-01-01", periods=10, freq="D")
            equity_data = EquityData(
                timestamp=timestamp,
                equity=np.array(range(10), dtype=np.float32),
                equity_pct=np.array(range(10), dtype=np.float32),
                equity_change=np.ones(10, dtype=np.float32),
                equity_change_pct=np.ones(10, dtype=np.float32),
                drawdown=np.zeros(10, dtype=np.float32),
                drawdown_pct=np.zeros(10, dtype=np.float32),
                peak_equity=np.array(range(10), dtype=np.float32),
                mfe=np.array(range(10), dtype=np.float32),
                mae=np.zeros(10, dtype=np.float32),
            )

            portfolio = {
                "Ticker": f"TEST{i:03d}",
                "Strategy Type": "SMA",
                "Fast Period": 20,
                "Slow Period": 50,
                "Signal Period": None,
                "_equity_data": equity_data,
            }
            portfolios.append(portfolio)

        return portfolios

    def test_streaming_exporter_initialization(self):
        """Test streaming exporter initialization."""
        config = MemoryOptimizationConfig(chunk_size=25)
        exporter = StreamingEquityExporter(config)

        assert exporter.config.chunk_size == 25
        assert exporter.processed_count == 0
        assert exporter.exported_count == 0
        assert exporter.memory_peak == 0.0

    def test_chunk_portfolios(self):
        """Test portfolio chunking functionality."""
        config = MemoryOptimizationConfig(chunk_size=3)
        exporter = StreamingEquityExporter(config)

        portfolios = self.create_test_portfolios(10)
        chunks = list(exporter.chunk_portfolios(portfolios))

        # Should have 4 chunks: 3, 3, 3, 1
        assert len(chunks) == 4
        assert len(chunks[0]) == 3
        assert len(chunks[1]) == 3
        assert len(chunks[2]) == 3
        assert len(chunks[3]) == 1

        # Verify all portfolios are included
        total_portfolios = sum(len(chunk) for chunk in chunks)
        assert total_portfolios == 10

    def test_chunk_portfolios_exact_division(self):
        """Test chunking when portfolio count is exactly divisible by chunk size."""
        config = MemoryOptimizationConfig(chunk_size=5)
        exporter = StreamingEquityExporter(config)

        portfolios = self.create_test_portfolios(15)
        chunks = list(exporter.chunk_portfolios(portfolios))

        # Should have exactly 3 chunks of 5 each
        assert len(chunks) == 3
        for chunk in chunks:
            assert len(chunk) == 5

    @patch("app.tools.equity_export.export_equity_data_to_csv")
    def test_stream_export_equity_data_disabled(self, mock_export):
        """Test streaming export when export is disabled."""
        config = MemoryOptimizationConfig()
        exporter = StreamingEquityExporter(config)

        portfolios = self.create_test_portfolios(5)
        export_config = {"EQUITY_DATA": {"EXPORT": False, "METRIC": "mean"}}

        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        results = exporter.stream_export_equity_data(
            portfolios,
            mock_log,
            export_config,
        )

        assert results["total_portfolios"] == 5
        assert results["exported_count"] == 0
        assert results["skipped_count"] == 5
        assert results["error_count"] == 0

        # Should not call export function
        mock_export.assert_not_called()

        # Should log disabled message
        info_messages = [msg for msg, level in log_messages if level == "info"]
        assert any("disabled" in msg for msg in info_messages)

    @patch("app.tools.equity_export.export_equity_data_to_csv")
    def test_stream_export_equity_data_enabled(self, mock_export):
        """Test streaming export when export is enabled."""
        mock_export.return_value = True

        config = MemoryOptimizationConfig(chunk_size=3, enable_progress_logging=True)
        exporter = StreamingEquityExporter(config)

        portfolios = self.create_test_portfolios(7)
        export_config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"}}

        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        results = exporter.stream_export_equity_data(
            portfolios,
            mock_log,
            export_config,
        )

        assert results["total_portfolios"] == 7
        assert results["exported_count"] == 7
        assert results["skipped_count"] == 0
        assert results["error_count"] == 0
        assert results["chunks_processed"] == 3  # 3, 3, 1
        assert results["memory_optimized"] is True

        # Should call export function for each portfolio
        assert mock_export.call_count == 7

        # Should log progress messages
        info_messages = [msg for msg, level in log_messages if level == "info"]
        progress_messages = [msg for msg in info_messages if "Processing chunk" in msg]
        assert len(progress_messages) == 3  # One per chunk

    @patch("app.tools.equity_export.export_equity_data_to_csv")
    def test_stream_export_with_optimization_disabled(self, mock_export):
        """Test streaming export with data type optimization disabled."""
        mock_export.return_value = True

        config = MemoryOptimizationConfig(
            chunk_size=2,
            optimize_data_types=False,
            enable_streaming=False,
        )
        exporter = StreamingEquityExporter(config)

        portfolios = self.create_test_portfolios(3)
        export_config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"}}

        def mock_log(msg, level):
            pass

        with patch("app.tools.equity_export.export_equity_data_batch") as mock_batch:
            mock_batch.return_value = {"exported_count": 3, "total_portfolios": 3}

            exporter.stream_export_equity_data(portfolios, mock_log, export_config)

            # Should fall back to batch export
            mock_batch.assert_called_once()
            mock_export.assert_not_called()

    def test_stream_export_portfolios_without_equity_data(self):
        """Test streaming export with portfolios missing equity data."""
        config = MemoryOptimizationConfig(chunk_size=2)
        exporter = StreamingEquityExporter(config)

        # Create portfolios without equity data
        portfolios = [
            {"Ticker": "TEST1", "Strategy Type": "SMA"},
            {"Ticker": "TEST2", "Strategy Type": "EMA"},
            {"Ticker": "TEST3", "Strategy Type": "MACD"},
        ]

        export_config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"}}

        def mock_log(msg, level):
            pass

        results = exporter.stream_export_equity_data(
            portfolios,
            mock_log,
            export_config,
        )

        assert results["total_portfolios"] == 3
        assert results["exported_count"] == 0
        assert results["skipped_count"] == 3
        assert results["error_count"] == 0


@pytest.mark.integration
class TestMemoryEfficientExportFunction:
    """Test memory-efficient export function creation."""

    def test_create_memory_efficient_export_function_default(self):
        """Test creating memory-efficient export function with defaults."""
        export_func = create_memory_efficient_export_function()

        # Should return a callable
        assert callable(export_func)

    def test_create_memory_efficient_export_function_custom_config(self):
        """Test creating memory-efficient export function with custom config."""
        config = MemoryOptimizationConfig(chunk_size=10)
        export_func = create_memory_efficient_export_function(config)

        assert callable(export_func)

    @patch("app.tools.equity_memory_optimizer.StreamingEquityExporter")
    def test_optimized_export_function_execution(self, mock_exporter_class):
        """Test execution of optimized export function."""
        mock_exporter = Mock()
        mock_exporter.stream_export_equity_data.return_value = {"exported_count": 5}
        mock_exporter_class.return_value = mock_exporter

        export_func = create_memory_efficient_export_function()

        portfolios = [{"_equity_data": Mock()}]
        config = {"EQUITY_DATA": {"EXPORT": True}}

        def mock_log(msg, level):
            pass

        result = export_func(portfolios, mock_log, config)

        # Should create exporter and call stream_export_equity_data
        mock_exporter_class.assert_called_once()
        mock_exporter.stream_export_equity_data.assert_called_once_with(
            portfolios,
            mock_log,
            config,
        )
        assert result == {"exported_count": 5}


@pytest.mark.integration
class TestMemoryAnalysis:
    """Test memory analysis functionality."""

    def create_test_portfolios_for_analysis(self) -> list:
        """Create test portfolios for memory analysis."""
        portfolios = []

        # Mix of portfolios with and without equity data
        for i in range(5):
            timestamp = pd.date_range(
                "2023-01-01",
                periods=100 * (i + 1),
                freq="D",
            )  # Varying sizes
            equity_data = EquityData(
                timestamp=timestamp,
                equity=np.ones(100 * (i + 1), dtype=np.float64),
                equity_pct=np.ones(100 * (i + 1), dtype=np.float64),
                equity_change=np.ones(100 * (i + 1), dtype=np.float64),
                equity_change_pct=np.ones(100 * (i + 1), dtype=np.float64),
                drawdown=np.ones(100 * (i + 1), dtype=np.float64),
                drawdown_pct=np.ones(100 * (i + 1), dtype=np.float64),
                peak_equity=np.ones(100 * (i + 1), dtype=np.float64),
                mfe=np.ones(100 * (i + 1), dtype=np.float64),
                mae=np.ones(100 * (i + 1), dtype=np.float64),
            )

            strategy_types = ["SMA", "EMA", "MACD"]
            portfolio = {
                "Ticker": f"TEST{i:03d}",
                "Strategy Type": strategy_types[i % len(strategy_types)],
                "_equity_data": equity_data,
            }
            portfolios.append(portfolio)

        # Add some portfolios without equity data
        for i in range(3):
            portfolio = {
                "Ticker": f"NODATA{i:03d}",
                "Strategy Type": "SMA",
                # No _equity_data field
            }
            portfolios.append(portfolio)

        return portfolios

    def test_analyze_memory_requirements(self):
        """Test memory requirements analysis."""
        portfolios = self.create_test_portfolios_for_analysis()

        analysis = analyze_memory_requirements(portfolios)

        assert analysis["total_portfolios"] == 8
        assert analysis["portfolios_with_equity_data"] == 5
        assert analysis["estimated_memory_mb"] > 0
        assert analysis["largest_equity_dataset_mb"] > 0
        assert len(analysis["memory_by_strategy"]) > 0
        assert isinstance(analysis["recommendations"], list)

        # Check strategy breakdown
        strategy_breakdown = analysis["memory_by_strategy"]
        assert "SMA" in strategy_breakdown
        assert strategy_breakdown["SMA"]["count"] > 0
        assert strategy_breakdown["SMA"]["total_memory_mb"] > 0

    def test_analyze_memory_requirements_empty_portfolios(self):
        """Test memory analysis with no portfolios."""
        analysis = analyze_memory_requirements([])

        assert analysis["total_portfolios"] == 0
        assert analysis["portfolios_with_equity_data"] == 0
        assert analysis["estimated_memory_mb"] == 0.0
        assert analysis["largest_equity_dataset_mb"] == 0.0
        assert analysis["memory_by_strategy"] == {}

    def test_analyze_memory_requirements_no_equity_data(self):
        """Test memory analysis with portfolios but no equity data."""
        portfolios = [
            {"Ticker": "TEST1", "Strategy Type": "SMA"},
            {"Ticker": "TEST2", "Strategy Type": "EMA"},
        ]

        analysis = analyze_memory_requirements(portfolios)

        assert analysis["total_portfolios"] == 2
        assert analysis["portfolios_with_equity_data"] == 0
        assert analysis["estimated_memory_mb"] == 0.0

    def test_analyze_memory_requirements_recommendations(self):
        """Test memory analysis recommendations."""
        # Create small dataset (should get optimal recommendation)
        small_portfolios = [
            {
                "Ticker": "SMALL",
                "Strategy Type": "SMA",
                "_equity_data": EquityData(
                    timestamp=pd.date_range("2023-01-01", periods=10, freq="D"),
                    equity=np.ones(10, dtype=np.float32),
                    equity_pct=np.ones(10, dtype=np.float32),
                    equity_change=np.ones(10, dtype=np.float32),
                    equity_change_pct=np.ones(10, dtype=np.float32),
                    drawdown=np.ones(10, dtype=np.float32),
                    drawdown_pct=np.ones(10, dtype=np.float32),
                    peak_equity=np.ones(10, dtype=np.float32),
                    mfe=np.ones(10, dtype=np.float32),
                    mae=np.ones(10, dtype=np.float32),
                ),
            },
        ]

        analysis = analyze_memory_requirements(small_portfolios)
        recommendations = analysis["recommendations"]

        # Should recommend that current dataset is optimal
        assert any("optimal memory limits" in rec for rec in recommendations)
