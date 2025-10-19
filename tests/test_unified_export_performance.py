#!/usr/bin/env python3
"""
Comprehensive test suite for the Unified Export System.

Tests performance improvements, functionality, and backward compatibility
of the new unified export system against the legacy system.
"""

import logging
from pathlib import Path
import shutil
import tempfile
import time

import pandas as pd
import polars as pl
import pytest

from app.tools.export.unified_export import (
    ExportConfig,
    UnifiedExportProcessor,
    export_portfolio_batch,
    export_portfolio_csv,
)
from app.tools.export_csv import export_portfolio_to_csv  # Legacy function
from app.tools.portfolio.base_extended_schemas import SchemaType


logger = logging.getLogger(__name__)


class TestUnifiedExportPerformance:
    """Test suite focusing on performance improvements."""

    @pytest.fixture
    def sample_portfolio_polars(self) -> pl.DataFrame:
        """Create sample portfolio data in Polars format."""
        return pl.DataFrame(
            {
                "Ticker": ["AAPL", "GOOGL", "MSFT"],
                "Strategy Type": ["EMA", "SMA", "EMA"],
                "Total Return [%]": [15.5, 12.3, 18.7],
                "Sharpe Ratio": [1.2, 1.1, 1.4],
                "Max Drawdown [%]": [-8.5, -10.2, -7.8],
                "Win Rate [%]": [65.0, 58.0, 72.0],
                "Number of Trades": [45, 38, 52],
                "Profit Factor": [1.8, 1.6, 2.1],
            }
        )

    @pytest.fixture
    def sample_portfolio_pandas(self, sample_portfolio_polars) -> pd.DataFrame:
        """Create sample portfolio data in Pandas format."""
        return sample_portfolio_polars.to_pandas()

    @pytest.fixture
    def temp_output_dir(self) -> str:
        """Create temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp(prefix="unified_export_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def export_config(self, temp_output_dir) -> ExportConfig:
        """Create test export configuration."""
        return ExportConfig(
            output_dir=temp_output_dir,
            schema_type=SchemaType.EXTENDED,
            enable_performance_monitoring=True,
            cache_schema_validation=True,
            max_workers=2,
        )

    def test_unified_export_processor_initialization(self, export_config):
        """Test that UnifiedExportProcessor initializes correctly."""
        processor = UnifiedExportProcessor(export_config)

        assert processor.config == export_config
        assert processor.schema_transformer is not None
        assert len(processor._column_cache) == 3  # BASE, EXTENDED, FILTERED
        assert SchemaType.BASE in processor._column_cache
        assert SchemaType.EXTENDED in processor._column_cache
        assert SchemaType.FILTERED in processor._column_cache

    def test_single_export_polars(self, export_config, sample_portfolio_polars):
        """Test single export with Polars DataFrame."""
        processor = UnifiedExportProcessor(export_config)

        result = processor.export_single(
            data=sample_portfolio_polars,
            filename="test_polars_export.csv",
            ticker="AAPL",
            strategy_type="EMA",
        )

        assert result.success is True
        assert result.file_path is not None
        assert Path(result.file_path).exists()
        assert result.execution_time > 0
        assert result.row_count == 3
        assert result.performance_metrics is not None

        # Verify file content
        exported_data = pl.read_csv(result.file_path)
        assert len(exported_data) == 3

    def test_single_export_pandas(self, export_config, sample_portfolio_pandas):
        """Test single export with Pandas DataFrame."""
        processor = UnifiedExportProcessor(export_config)

        result = processor.export_single(
            data=sample_portfolio_pandas,
            filename="test_pandas_export.csv",
            ticker="GOOGL",
            strategy_type="SMA",
        )

        assert result.success is True
        assert result.file_path is not None
        assert Path(result.file_path).exists()
        assert result.execution_time > 0
        assert result.row_count == 3

        # Verify file content
        exported_data = pd.read_csv(result.file_path)
        assert len(exported_data) == 3

    def test_batch_export_performance(self, export_config, sample_portfolio_polars):
        """Test batch export performance and parallel processing."""
        processor = UnifiedExportProcessor(export_config)

        # Create batch of export jobs
        export_jobs = [
            (sample_portfolio_polars, f"batch_test_{i}.csv", {"ticker": f"TICKER_{i}"})
            for i in range(10)
        ]

        start_time = time.time()
        results = processor.export_batch(export_jobs)
        batch_time = time.time() - start_time

        assert len(results) == 10
        assert all(result.success for result in results)
        assert batch_time < 5.0  # Should complete quickly with parallel processing

        # Verify all files were created
        for result in results:
            assert Path(result.file_path).exists()

    def test_schema_type_determination(self, export_config, sample_portfolio_polars):
        """Test automatic schema type determination based on filename."""
        processor = UnifiedExportProcessor(export_config)

        # Test different filename patterns
        test_cases = [
            ("portfolios/test.csv", SchemaType.BASE),
            ("portfolios_filtered/test.csv", SchemaType.FILTERED),
            ("portfolios_best/test.csv", SchemaType.FILTERED),
            ("strategies/test.csv", SchemaType.EXTENDED),  # Default
        ]

        for filename, expected_schema in test_cases:
            determined_schema = processor._determine_target_schema(filename, None)
            assert determined_schema == expected_schema

    def test_performance_monitoring(self, export_config, sample_portfolio_polars):
        """Test performance monitoring and metrics collection."""
        processor = UnifiedExportProcessor(export_config)

        # Perform multiple exports
        for i in range(5):
            processor.export_single(
                data=sample_portfolio_polars, filename=f"perf_test_{i}.csv"
            )

        # Check performance summary
        summary = processor.get_performance_summary()

        assert summary["total_exports"] == 5
        assert "average_total_time" in summary
        assert "average_schema_validation_time" in summary
        assert "cache_hit_ratio" in summary
        assert "performance_improvement" in summary

    def test_schema_caching(self, export_config, sample_portfolio_polars):
        """Test schema validation caching for improved performance."""
        processor = UnifiedExportProcessor(export_config)

        # First export - should cache schema
        result1 = processor.export_single(
            data=sample_portfolio_polars, filename="cache_test_1.csv"
        )

        # Second export with same data - should use cache
        result2 = processor.export_single(
            data=sample_portfolio_polars, filename="cache_test_2.csv"
        )

        assert result1.success and result2.success

        # Cache should contain entries
        assert len(processor._schema_cache) > 0

    def test_convenience_functions(self, temp_output_dir, sample_portfolio_polars):
        """Test backward compatibility convenience functions."""
        # Test single export convenience function
        result = export_portfolio_csv(
            data=sample_portfolio_polars,
            output_dir=temp_output_dir,
            filename="convenience_test.csv",
            schema_type=SchemaType.EXTENDED,
        )

        assert result.success is True
        assert Path(result.file_path).exists()

        # Test batch export convenience function
        export_jobs = [
            (sample_portfolio_polars, f"convenience_batch_{i}.csv", {})
            for i in range(3)
        ]

        results = export_portfolio_batch(
            export_jobs=export_jobs, output_dir=temp_output_dir
        )

        assert len(results) == 3
        assert all(result.success for result in results)

    def test_error_handling(self, export_config):
        """Test error handling for various failure scenarios."""
        processor = UnifiedExportProcessor(export_config)

        # Test with invalid data
        result = processor.export_single(
            data=None,
            filename="error_test.csv",  # Invalid data
        )

        assert result.success is False
        assert result.error_message is not None
        assert result.execution_time > 0

    @pytest.mark.benchmark
    def test_performance_comparison_with_legacy(
        self, temp_output_dir, sample_portfolio_polars, sample_portfolio_pandas
    ):
        """
        Compare performance of unified export vs legacy export system.

        This test requires the legacy export function to be available.
        """
        # Test unified system
        config = ExportConfig(
            output_dir=temp_output_dir, enable_performance_monitoring=True
        )
        processor = UnifiedExportProcessor(config)

        # Unified system timing
        start_time = time.time()
        unified_result = processor.export_single(
            data=sample_portfolio_polars, filename="unified_benchmark.csv"
        )
        unified_time = time.time() - start_time

        # Legacy system timing (if available)
        try:
            start_time = time.time()
            legacy_path = Path(temp_output_dir) / "legacy_benchmark.csv"
            export_portfolio_to_csv(
                data=sample_portfolio_pandas, file_path=str(legacy_path)
            )
            legacy_time = time.time() - start_time

            # Performance comparison
            improvement = ((legacy_time - unified_time) / legacy_time) * 100

            logger.info("Performance comparison:")
            logger.info(f"  Unified system: {unified_time:.4f}s")
            logger.info(f"  Legacy system: {legacy_time:.4f}s")
            logger.info(f"  Improvement: {improvement:.1f}%")

            # Unified system should be faster
            assert (
                unified_time <= legacy_time
            ), f"Unified system should be faster (unified: {unified_time:.4f}s, legacy: {legacy_time:.4f}s)"

        except ImportError:
            # Legacy function not available - skip comparison
            logger.warning("Legacy export function not available for comparison")
            assert unified_result.success is True

    def test_large_dataset_performance(self, export_config):
        """Test performance with larger datasets."""
        # Create larger test dataset
        large_data = pl.DataFrame(
            {
                "Ticker": [f"TICKER_{i}" for i in range(1000)],
                "Strategy Type": ["EMA", "SMA"] * 500,
                "Total Return [%]": [i * 0.1 for i in range(1000)],
                "Sharpe Ratio": [1.0 + (i * 0.001) for i in range(1000)],
                "Max Drawdown [%]": [-10.0 + (i * 0.01) for i in range(1000)],
                "Win Rate [%]": [50.0 + (i * 0.02) for i in range(1000)],
                "Number of Trades": [10 + i for i in range(1000)],
                "Profit Factor": [1.0 + (i * 0.002) for i in range(1000)],
            }
        )

        processor = UnifiedExportProcessor(export_config)

        start_time = time.time()
        result = processor.export_single(
            data=large_data, filename="large_dataset_test.csv"
        )
        execution_time = time.time() - start_time

        assert result.success is True
        assert result.row_count == 1000
        assert execution_time < 10.0  # Should complete within 10 seconds

        # Verify file was created and has correct size
        assert Path(result.file_path).exists()
        exported_data = pl.read_csv(result.file_path)
        assert len(exported_data) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
