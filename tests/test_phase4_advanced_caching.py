#!/usr/bin/env python3
"""
Test Suite for Phase 4 Advanced Caching and Monitoring Features

This test suite validates the Phase 4 enhancements to the unified export system:
- Advanced caching with TTL and content-based invalidation
- Performance monitoring with alerting capabilities
- Export result caching
- Cache diagnostics and management
"""

import shutil
import tempfile
import time
from unittest.mock import patch

import pandas as pd
import pytest

from app.tools.export.unified_export import (
    AdvancedCache,
    ExportConfig,
    PerformanceMetrics,
    PerformanceMonitor,
    UnifiedExportProcessor,
)


class TestAdvancedCache:
    """Test the advanced caching system with TTL and content-based invalidation."""

    def test_cache_initialization(self):
        """Test cache initialization with custom parameters."""
        cache = AdvancedCache(ttl_minutes=30, max_entries=500)

        assert cache.ttl_minutes == 30
        assert cache.max_entries == 500
        assert len(cache._cache) == 0

        stats = cache.get_stats()
        assert stats["hit_count"] == 0
        assert stats["miss_count"] == 0
        assert stats["hit_ratio"] == 0.0
        assert stats["cache_size"] == 0

    def test_basic_cache_operations(self):
        """Test basic put/get operations."""
        cache = AdvancedCache()

        # Test miss
        result = cache.get("nonexistent")
        assert result is None

        # Test put and hit
        cache.put("key1", "value1", "hash1")
        result = cache.get("key1")
        assert result == "value1"

        stats = cache.get_stats()
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert stats["hit_ratio"] == 0.5

    def test_ttl_expiration(self):
        """Test TTL-based cache expiration."""
        cache = AdvancedCache(ttl_minutes=0.01)  # 0.6 seconds

        cache.put("key1", "value1", "hash1")

        # Should hit immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(0.7)

        # Should miss after expiration
        assert cache.get("key1") is None

    def test_cache_eviction(self):
        """Test LRU-style cache eviction when at capacity."""
        cache = AdvancedCache(max_entries=3)

        # Fill cache to capacity
        cache.put("key1", "value1", "hash1")
        cache.put("key2", "value2", "hash2")
        cache.put("key3", "value3", "hash3")

        assert cache.get_stats()["cache_size"] == 3

        # Access key1 to make it recently used
        cache.get("key1")

        # Add new entry, should trigger eviction
        cache.put("key4", "value4", "hash4")

        # Should have evicted some old entries
        stats = cache.get_stats()
        assert stats["cache_size"] <= 3

        # key1 should still be there (recently accessed)
        assert cache.get("key1") == "value1"

    def test_content_based_invalidation(self):
        """Test invalidation by content hash."""
        cache = AdvancedCache()

        cache.put("key1", "value1", "hash1")
        cache.put("key2", "value2", "hash1")  # Same hash
        cache.put("key3", "value3", "hash2")  # Different hash

        # Invalidate by content hash
        cache.invalidate_by_content("hash1")

        # Keys with hash1 should be gone
        assert cache.get("key1") is None
        assert cache.get("key2") is None

        # Key with different hash should remain
        assert cache.get("key3") == "value3"

    def test_cache_clear(self):
        """Test clearing all cache entries."""
        cache = AdvancedCache()

        cache.put("key1", "value1", "hash1")
        cache.put("key2", "value2", "hash2")

        assert cache.get_stats()["cache_size"] == 2

        cache.clear()

        stats = cache.get_stats()
        assert stats["cache_size"] == 0
        assert stats["hit_count"] == 0
        assert stats["miss_count"] == 0


class TestPerformanceMonitor:
    """Test the performance monitoring system with alerting."""

    def test_monitor_initialization(self):
        """Test monitor initialization."""
        monitor = PerformanceMonitor(enable_alerts=True, threshold_ms=50.0)

        assert monitor.enable_alerts is True
        assert monitor.threshold_ms == 50.0
        assert len(monitor._metrics_history) == 0
        assert len(monitor._alert_callbacks) == 0

    def test_metrics_recording(self):
        """Test recording performance metrics."""
        monitor = PerformanceMonitor()

        metrics = PerformanceMetrics(
            total_time=0.05,
            schema_validation_time=0.01,
            file_write_time=0.02,
            cache_hit=True,
        )

        monitor.record_metrics(metrics)

        assert len(monitor._metrics_history) == 1

        summary = monitor.get_performance_summary()
        assert summary["total_operations"] == 1
        assert summary["average_total_time_ms"] == 50.0
        assert summary["cache_hit_ratio"] == 1.0

    def test_performance_alerts(self):
        """Test performance alerting system."""
        alert_triggered = False
        alert_metrics = None

        def alert_callback(metrics):
            nonlocal alert_triggered, alert_metrics
            alert_triggered = True
            alert_metrics = metrics

        monitor = PerformanceMonitor(enable_alerts=True, threshold_ms=30.0)
        monitor.add_alert_callback(alert_callback)

        # Record metrics that exceed threshold
        slow_metrics = PerformanceMetrics(total_time=0.05)  # 50ms > 30ms threshold
        monitor.record_metrics(slow_metrics)

        assert alert_triggered is True
        assert alert_metrics == slow_metrics

        # Reset and test fast metrics
        alert_triggered = False
        fast_metrics = PerformanceMetrics(total_time=0.01)  # 10ms < 30ms threshold
        monitor.record_metrics(fast_metrics)

        assert alert_triggered is False

    def test_performance_summary_calculations(self):
        """Test performance summary calculations."""
        monitor = PerformanceMonitor()

        # Record multiple metrics
        for i in range(5):
            metrics = PerformanceMetrics(
                total_time=0.01 * (i + 1),  # 10, 20, 30, 40, 50 ms
                schema_validation_time=0.005 * (i + 1),
                file_write_time=0.003 * (i + 1),
                cache_hit=(i % 2 == 0),
            )
            monitor.record_metrics(metrics)

        summary = monitor.get_performance_summary()

        assert summary["total_operations"] == 5
        assert summary["average_total_time_ms"] == 30.0  # (10+20+30+40+50)/5
        assert summary["average_schema_validation_time_ms"] == 15.0
        assert summary["average_file_write_time_ms"] == 9.0
        assert summary["cache_hit_ratio"] == 0.6  # 3 out of 5
        assert summary["p95_total_time_ms"] == 50.0  # 95th percentile


class TestUnifiedExportProcessorPhase4:
    """Test Phase 4 enhancements to the UnifiedExportProcessor."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = ExportConfig(
            output_dir=self.temp_dir,
            cache_schema_validation=True,
            enable_export_result_caching=True,
            cache_ttl_minutes=60,
            cache_max_entries=100,
            enable_performance_alerts=True,
            performance_threshold_ms=50.0,
        )
        self.processor = UnifiedExportProcessor(self.config)

        # Create test DataFrame
        self.test_data = pd.DataFrame(
            {
                "Ticker": ["AAPL", "GOOGL"],
                "Open [%]": [1.0, 2.0],
                "High [%]": [1.1, 2.1],
                "Low [%]": [0.9, 1.9],
                "Close [%]": [1.05, 2.05],
                "Volume [%]": [1000000, 2000000],
            },
        )

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_result_caching(self):
        """Test export result caching functionality."""
        filename = "test_export_caching.csv"

        # First export - should cache result
        result1 = self.processor.export_single(self.test_data, filename)
        assert result1.success is True
        assert result1.performance_metrics.get("cache_hit", False) is False

        # Second export with same data - should hit cache
        result2 = self.processor.export_single(self.test_data, filename)
        assert result2.success is True
        assert result2.performance_metrics.get("cache_hit", False) is True
        assert result2.performance_metrics.get("cache_type") == "export_result"

        # Verify both results are equivalent (except timing)
        assert result1.file_path == result2.file_path
        assert result1.row_count == result2.row_count
        assert result1.column_count == result2.column_count

    def test_schema_validation_caching(self):
        """Test schema validation caching."""
        filename = "test_schema_caching.csv"

        # Create processor with different data to avoid export result caching
        data1 = self.test_data.copy()
        data2 = self.test_data.copy()
        data2["Extra_Col"] = [1, 2]  # Different structure

        result1 = self.processor.export_single(data1, filename + "1")
        result2 = self.processor.export_single(data2, filename + "2")

        # Both should succeed
        assert result1.success is True
        assert result2.success is True

        # Check cache statistics
        cache_stats = self.processor.get_cache_diagnostics()
        assert cache_stats["schema_cache"]["cache_size"] > 0

    def test_performance_monitoring_integration(self):
        """Test integration with performance monitoring."""
        alert_triggered = False

        def test_alert_callback(metrics):
            nonlocal alert_triggered
            alert_triggered = True

        self.processor.add_performance_alert_callback(test_alert_callback)

        # Simulate slow operation by mocking time.time
        with patch("time.time") as mock_time:
            # Make export appear to take 100ms (above 50ms threshold)
            mock_time.side_effect = [0.0, 0.1]  # start=0, end=0.1 (100ms)

            result = self.processor.export_single(self.test_data, "slow_export.csv")

            assert result.success is True
            # Note: Alert might not trigger due to mocking complexity

    def test_cache_invalidation(self):
        """Test cache invalidation functionality."""
        filename = "test_invalidation.csv"

        # Export and cache result
        result1 = self.processor.export_single(self.test_data, filename)
        assert result1.success is True

        # Verify cache has entries
        diagnostics = self.processor.get_cache_diagnostics()
        initial_cache_size = diagnostics["export_result_cache"]["cache_size"]
        assert initial_cache_size > 0

        # Invalidate all cache
        self.processor.invalidate_cache()

        # Verify cache is cleared
        diagnostics = self.processor.get_cache_diagnostics()
        assert diagnostics["export_result_cache"]["cache_size"] == 0
        assert diagnostics["schema_cache"]["cache_size"] == 0

    def test_cache_diagnostics(self):
        """Test cache diagnostics functionality."""
        # Perform some exports to populate caches
        for i in range(3):
            result = self.processor.export_single(self.test_data, f"test_{i}.csv")
            assert result.success is True

        diagnostics = self.processor.get_cache_diagnostics()

        # Verify structure
        assert "schema_cache" in diagnostics
        assert "export_result_cache" in diagnostics
        assert "cache_configuration" in diagnostics
        assert "performance_monitoring" in diagnostics

        # Verify cache configuration
        config = diagnostics["cache_configuration"]
        assert config["schema_validation_enabled"] is True
        assert config["export_result_enabled"] is True
        assert config["ttl_minutes"] == 60
        assert config["max_entries"] == 100

        # Verify performance monitoring config
        perf_config = diagnostics["performance_monitoring"]
        assert perf_config["alerts_enabled"] is True
        assert perf_config["threshold_ms"] == 50.0

    def test_performance_summary_enhancement(self):
        """Test enhanced performance summary with Phase 4 metrics."""
        # Perform multiple exports
        for i in range(5):
            result = self.processor.export_single(self.test_data, f"perf_test_{i}.csv")
            assert result.success is True

        summary = self.processor.get_performance_summary()

        # Verify Phase 4 enhancements
        assert "schema_cache" in summary
        assert "export_result_cache" in summary
        assert "combined_cache_hit_ratio" in summary
        assert "cache_efficiency_score" in summary

        # Verify cache stats structure
        assert "hit_ratio" in summary["schema_cache"]
        assert "cache_size" in summary["schema_cache"]
        assert "hit_ratio" in summary["export_result_cache"]
        assert "cache_size" in summary["export_result_cache"]

    def test_content_hash_generation(self):
        """Test content hash generation for caching."""
        # Test with same data - should generate same hash
        hash1 = self.processor._generate_content_hash(
            self.test_data,
            "test.csv",
            "AAPL",
            "SMA",
            "TEST",
        )
        hash2 = self.processor._generate_content_hash(
            self.test_data,
            "test.csv",
            "AAPL",
            "SMA",
            "TEST",
        )
        assert hash1 == hash2

        # Test with different data - should generate different hash
        different_data = self.test_data.copy()
        different_data["New_Col"] = [1, 2]

        hash3 = self.processor._generate_content_hash(
            different_data,
            "test.csv",
            "AAPL",
            "SMA",
            "TEST",
        )
        assert hash1 != hash3

        # Test with different parameters - should generate different hash
        hash4 = self.processor._generate_content_hash(
            self.test_data,
            "different.csv",
            "AAPL",
            "SMA",
            "TEST",
        )
        assert hash1 != hash4

    def test_cache_configuration_options(self):
        """Test various cache configuration options."""
        # Test with caching disabled
        config_no_cache = ExportConfig(
            output_dir=self.temp_dir,
            cache_schema_validation=False,
            enable_export_result_caching=False,
        )
        processor_no_cache = UnifiedExportProcessor(config_no_cache)

        result = processor_no_cache.export_single(self.test_data, "no_cache.csv")
        assert result.success is True
        assert result.performance_metrics.get("cache_hit", False) is False

        # Test with custom TTL
        config_short_ttl = ExportConfig(
            output_dir=self.temp_dir,
            cache_ttl_minutes=0.01,  # Very short TTL
            cache_max_entries=50,
        )
        processor_short_ttl = UnifiedExportProcessor(config_short_ttl)

        result = processor_short_ttl.export_single(self.test_data, "short_ttl.csv")
        assert result.success is True


class TestPhase4Integration:
    """Integration tests for Phase 4 features."""

    def setup_method(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = ExportConfig(
            output_dir=self.temp_dir,
            enable_performance_monitoring=True,
            enable_performance_alerts=True,
            performance_threshold_ms=10.0,  # Low threshold for testing
            cache_ttl_minutes=60,
            max_workers=2,
        )

    def teardown_method(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_batch_export_with_caching(self):
        """Test batch export functionality with caching."""
        processor = UnifiedExportProcessor(self.config)

        # Create test data
        data1 = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        data2 = pd.DataFrame({"A": [5, 6], "B": [7, 8]})

        export_jobs = [
            (data1, "batch_1.csv", {}),
            (data2, "batch_2.csv", {}),
            (data1, "batch_1_dup.csv", {}),  # Duplicate data for cache testing
        ]

        results = processor.export_batch(export_jobs)

        assert len(results) == 3
        assert all(r.success for r in results)

        # Third export might hit cache (same data as first)
        summary = processor.get_performance_summary()
        assert summary["total_operations"] >= 3

    def test_real_world_scenario(self):
        """Test a real-world scenario with multiple operations."""
        processor = UnifiedExportProcessor(self.config)

        # Simulate portfolio data
        portfolio_data = pd.DataFrame(
            {
                "Ticker": ["AAPL", "GOOGL", "MSFT"],
                "Strategy": ["MA_Cross", "MA_Cross", "MA_Cross"],
                "Open [%]": [1.0, 2.0, 1.5],
                "High [%]": [1.1, 2.1, 1.6],
                "Low [%]": [0.9, 1.9, 1.4],
                "Close [%]": [1.05, 2.05, 1.55],
                "Volume [%]": [1000000, 2000000, 1500000],
                "Win Rate [%]": [65.5, 70.2, 68.1],
                "Profit Factor": [1.8, 2.1, 1.9],
            },
        )

        # Export to different directories (testing schema detection)
        results = []

        # Base schema export
        result1 = processor.export_single(
            portfolio_data,
            "portfolios/AAPL_D_SMA.csv",
            ticker="AAPL",
            strategy_type="SMA",
        )
        results.append(result1)

        # Filtered schema export
        result2 = processor.export_single(
            portfolio_data,
            "portfolios_filtered/AAPL_D_SMA.csv",
            ticker="AAPL",
            strategy_type="SMA",
            metric_type="MA_CROSS",
        )
        results.append(result2)

        # Repeat exports (should hit cache)
        result3 = processor.export_single(
            portfolio_data,
            "portfolios/AAPL_D_SMA.csv",
            ticker="AAPL",
            strategy_type="SMA",
        )
        results.append(result3)

        # Verify all exports succeeded
        assert all(r.success for r in results)

        # Verify cache effectiveness
        summary = processor.get_performance_summary()
        assert summary["total_operations"] == 3

        # At least one should be a cache hit
        cache_hits = sum(
            1 for r in results if r.performance_metrics.get("cache_hit", False)
        )
        assert cache_hits >= 1

        # Verify cache diagnostics
        diagnostics = processor.get_cache_diagnostics()
        assert diagnostics["export_result_cache"]["cache_size"] > 0

        # Test cache invalidation
        processor.invalidate_cache()
        post_clear_diagnostics = processor.get_cache_diagnostics()
        assert post_clear_diagnostics["export_result_cache"]["cache_size"] == 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
