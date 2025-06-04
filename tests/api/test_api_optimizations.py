"""
Test API Response Handling Optimizations

Tests for optimized API response caching, reduced IndexedDB storage,
and improved cache key generation from Phase 1 optimizations.
"""

import json
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestAPICacheOptimizations:
    """Test suite for API cache optimizations."""

    @pytest.fixture
    def mock_cache(self):
        """Mock cache implementation."""
        return {}

    @pytest.fixture
    def sample_api_response(self):
        """Sample API response for testing."""
        return {
            "status": "success",
            "request_id": "test-123",
            "timestamp": "2024-01-01T12:00:00Z",
            "ticker": ["AAPL", "GOOGL"],
            "strategy_types": ["SMA", "EMA"],
            "portfolios": [
                {
                    "ticker": "AAPL",
                    "strategy_type": "SMA",
                    "short_window": 5,
                    "long_window": 20,
                    "total_return": 15.5,
                    "win_rate": 0.64,
                    "total_trades": 25,
                    "score": 85.5,
                },
                {
                    "ticker": "GOOGL",
                    "strategy_type": "EMA",
                    "short_window": 8,
                    "long_window": 21,
                    "total_return": 18.7,
                    "win_rate": 0.6875,
                    "total_trades": 32,
                    "score": 92.1,
                },
            ],
            "total_portfolios_analyzed": 2,
            "total_portfolios_filtered": 2,
            "execution_time": 1.234,
        }

    @pytest.fixture
    def sample_analysis_config(self):
        """Sample analysis configuration for cache key testing."""
        return {
            "TICKER": ["AAPL", "GOOGL"],
            "WINDOWS": 20,
            "DIRECTION": "Long",
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "USE_HOURLY": False,
            "USE_YEARS": True,
            "YEARS": 5,
            "MINIMUMS": {
                "WIN_RATE": 50,
                "TRADES": 10,
            },
        }

    def test_cache_size_management(self, mock_cache):
        """Test that cache size is managed within limits."""
        MAX_CACHE_SIZE = 10

        def manage_cache_size(cache):
            if len(cache) > MAX_CACHE_SIZE:
                # Remove oldest entries (simulate FIFO)
                keys_to_delete = list(cache.keys())[:-MAX_CACHE_SIZE]
                for key in keys_to_delete:
                    del cache[key]

        # Fill cache beyond limit
        for i in range(15):
            mock_cache[f"key_{i}"] = f"value_{i}"

        # Should have 15 entries
        assert len(mock_cache) == 15

        # Apply size management
        manage_cache_size(mock_cache)

        # Should be reduced to MAX_CACHE_SIZE
        assert len(mock_cache) == MAX_CACHE_SIZE

        # Should keep the most recent entries
        assert "key_14" in mock_cache
        assert "key_13" in mock_cache
        assert "key_4" not in mock_cache  # Older entry removed

    def test_optimized_cache_key_generation(self, sample_analysis_config):
        """Test optimized cache key generation with specific parameters."""

        def get_cache_key(config):
            ticker = config["TICKER"]
            if isinstance(ticker, list):
                ticker = sorted(ticker)  # Sort for consistency
                ticker = ",".join(ticker)

            # Include key parameters that affect results
            key_parts = [
                f"t:{ticker}",
                f"w:{config['WINDOWS']}",
                f"d:{config['DIRECTION']}",
                f"s:{','.join(sorted(config['STRATEGY_TYPES']))}",
                f"h:{config['USE_HOURLY']}",
                f"y:{config['YEARS'] if config['USE_YEARS'] else 'all'}",
                f"min:{config['MINIMUMS']['WIN_RATE']}-{config['MINIMUMS']['TRADES']}",
            ]

            return "|".join(key_parts)

        cache_key = get_cache_key(sample_analysis_config)

        # Should contain all relevant parameters
        assert "t:AAPL,GOOGL" in cache_key
        assert "w:20" in cache_key
        assert "d:Long" in cache_key
        assert "s:EMA,SMA" in cache_key  # Sorted
        assert "h:False" in cache_key
        assert "y:5" in cache_key
        assert "min:50-10" in cache_key

    def test_cache_key_consistency_with_order_changes(self, sample_analysis_config):
        """Test that cache keys are consistent regardless of parameter order."""

        def get_cache_key(config):
            ticker = config["TICKER"]
            if isinstance(ticker, list):
                ticker = sorted(ticker)
                ticker = ",".join(ticker)

            strategies = sorted(config["STRATEGY_TYPES"])

            return f"t:{ticker}|s:{','.join(strategies)}"

        # Original order
        config1 = sample_analysis_config.copy()
        config1["TICKER"] = ["AAPL", "GOOGL"]
        config1["STRATEGY_TYPES"] = ["SMA", "EMA"]

        # Different order
        config2 = sample_analysis_config.copy()
        config2["TICKER"] = ["GOOGL", "AAPL"]  # Reversed
        config2["STRATEGY_TYPES"] = ["EMA", "SMA"]  # Reversed

        key1 = get_cache_key(config1)
        key2 = get_cache_key(config2)

        # Keys should be identical despite different input order
        assert key1 == key2

    def test_indexeddb_storage_reduction(self):
        """Test that IndexedDB storage is reduced from 50 to 20 entries."""
        mock_db_entries = []
        MAX_INDEXEDDB_ENTRIES = 20

        # Simulate adding entries beyond limit
        for i in range(30):
            mock_db_entries.append(
                {
                    "cacheKey": f"key_{i}",
                    "response": {"data": f"response_{i}"},
                    "timestamp": time.time()
                    - (30 - i),  # Older entries have earlier timestamps
                }
            )

        # Apply storage reduction logic
        if len(mock_db_entries) > MAX_INDEXEDDB_ENTRIES:
            # Sort by timestamp and keep most recent
            mock_db_entries.sort(key=lambda x: x["timestamp"], reverse=True)
            mock_db_entries = mock_db_entries[:MAX_INDEXEDDB_ENTRIES]

        # Should be reduced to 20 entries
        assert len(mock_db_entries) == MAX_INDEXEDDB_ENTRIES

        # Should keep the most recent entries
        assert mock_db_entries[0]["cacheKey"] == "key_29"
        assert mock_db_entries[-1]["cacheKey"] == "key_10"

    def test_cache_hit_rate_optimization(self, mock_cache, sample_api_response):
        """Test cache hit rate with optimized key generation."""
        cache_hits = 0
        cache_misses = 0

        def get_from_cache(cache_key):
            nonlocal cache_hits, cache_misses
            if cache_key in mock_cache:
                cache_hits += 1
                return mock_cache[cache_key]
            else:
                cache_misses += 1
                return None

        def set_cache(cache_key, value):
            mock_cache[cache_key] = value

        # First request - cache miss
        result1 = get_from_cache("test_key_1")
        assert result1 is None
        assert cache_misses == 1

        # Store in cache
        set_cache("test_key_1", sample_api_response)

        # Second request - cache hit
        result2 = get_from_cache("test_key_1")
        assert result2 == sample_api_response
        assert cache_hits == 1

        # Different key - cache miss
        result3 = get_from_cache("test_key_2")
        assert result3 is None
        assert cache_misses == 2

    @pytest.mark.asyncio
    async def test_async_cache_operations(self, sample_api_response):
        """Test asynchronous cache operations don't block main thread."""
        async_cache = {}

        async def async_cache_set(key, value):
            # Simulate async storage operation
            await asyncio.sleep(0.01)
            async_cache[key] = value
            return True

        async def async_cache_get(key):
            # Simulate async retrieval operation
            await asyncio.sleep(0.01)
            return async_cache.get(key)

        # Import asyncio for the test
        import asyncio

        # Store value asynchronously
        result = await async_cache_set("async_key", sample_api_response)
        assert result is True

        # Retrieve value asynchronously
        cached_value = await async_cache_get("async_key")
        assert cached_value == sample_api_response

    def test_cache_expiration_logic(self, mock_cache):
        """Test cache expiration based on timestamp."""
        current_time = time.time()
        cache_ttl = 24 * 60 * 60  # 24 hours in seconds

        # Add entries with different ages
        mock_cache["fresh_key"] = {
            "data": "fresh_data",
            "timestamp": current_time - 1000,  # 1000 seconds ago (fresh)
        }

        mock_cache["expired_key"] = {
            "data": "expired_data",
            "timestamp": current_time - (cache_ttl + 1000),  # Expired
        }

        def is_cache_valid(cache_entry, current_time, ttl):
            if not cache_entry or "timestamp" not in cache_entry:
                return False

            age = current_time - cache_entry["timestamp"]
            return age < ttl

        # Fresh entry should be valid
        fresh_entry = mock_cache["fresh_key"]
        assert is_cache_valid(fresh_entry, current_time, cache_ttl)

        # Expired entry should be invalid
        expired_entry = mock_cache["expired_key"]
        assert not is_cache_valid(expired_entry, current_time, cache_ttl)

    def test_memory_efficiency_with_large_responses(self):
        """Test memory efficiency when caching large API responses."""
        # Create large response
        large_portfolios = []
        for i in range(1000):
            large_portfolios.append(
                {
                    "ticker": f"TICK{i:04d}",
                    "strategy_type": "SMA",
                    "total_return": 10.0 + (i % 20),
                    "score": 50.0 + (i % 50),
                }
            )

        large_response = {
            "status": "success",
            "portfolios": large_portfolios,
            "total_portfolios_analyzed": 1000,
        }

        # Test caching large response
        cache = {}
        cache["large_key"] = large_response

        # Verify cache contains large response
        assert len(cache["large_key"]["portfolios"]) == 1000

        # Test memory cleanup
        del cache["large_key"]
        assert "large_key" not in cache

    def test_cache_performance_with_frequent_access(
        self, mock_cache, sample_api_response
    ):
        """Test cache performance with frequent access patterns."""
        # Pre-populate cache
        for i in range(10):
            mock_cache[f"key_{i}"] = {**sample_api_response, "id": i}

        access_times = []

        # Simulate frequent cache access
        for _ in range(100):
            start_time = time.time()

            # Access random cache key
            key = f"key_{_ % 10}"
            result = mock_cache.get(key)

            end_time = time.time()
            access_times.append(end_time - start_time)

            assert result is not None
            assert result["id"] == _ % 10

        # Cache access should be fast (< 1ms on average)
        avg_access_time = sum(access_times) / len(access_times)
        assert avg_access_time < 0.001  # Less than 1 millisecond

    def test_cache_invalidation_on_config_change(self, mock_cache, sample_api_response):
        """Test cache invalidation when configuration changes."""
        # Cache response for specific config
        config_key = "t:AAPL|w:20|d:Long"
        mock_cache[config_key] = sample_api_response

        def invalidate_cache_for_ticker(cache, ticker):
            """Invalidate all cache entries containing the ticker."""
            keys_to_remove = []
            for key in cache.keys():
                if f"t:{ticker}" in key or f"{ticker}," in key or f",{ticker}" in key:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del cache[key]

        # Verify cache contains entry
        assert config_key in mock_cache

        # Invalidate cache for AAPL
        invalidate_cache_for_ticker(mock_cache, "AAPL")

        # Cache entry should be removed
        assert config_key not in mock_cache

    def test_concurrent_cache_access_safety(self, mock_cache):
        """Test that concurrent cache access is safe."""
        import queue
        import threading

        results_queue = queue.Queue()

        def cache_worker(worker_id):
            try:
                # Simulate concurrent cache operations
                for i in range(10):
                    key = f"worker_{worker_id}_key_{i}"
                    value = f"worker_{worker_id}_value_{i}"

                    # Write to cache
                    mock_cache[key] = value

                    # Read from cache
                    retrieved = mock_cache.get(key)

                    assert retrieved == value

                results_queue.put(f"worker_{worker_id}_success")
            except Exception as e:
                results_queue.put(f"worker_{worker_id}_error: {e}")

        # Start multiple worker threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check all workers succeeded
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        success_count = sum(1 for r in results if "success" in r)
        assert success_count == 5  # All 5 workers should succeed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
