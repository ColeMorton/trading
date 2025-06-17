"""
Performance optimization processing module.

This module provides intelligent caching, parallel execution, and batch processing
capabilities optimized for trading system workloads.

Components:
- cache_manager: Intelligent file-based caching with TTL and LRU cleanup
- parallel_executor: Adaptive ThreadPool with dynamic sizing
- batch_processor: Optimized batch processing for tickers and parameter sweeps
"""

from .batch_processor import (
    BatchResult,
    ParameterSweepProcessor,
    TickerBatchProcessor,
    batch_analyze_tickers,
    batch_parameter_sweep,
)
from .cache_manager import (
    IntelligentCacheManager,
    cache_computation,
    cache_portfolio_results,
    cache_signals,
    get_cache_manager,
    get_cached_computation,
    get_cached_portfolio_results,
    get_cached_signals,
)
from .parallel_executor import (
    AdaptiveThreadPoolExecutor,
    get_executor,
    parallel_parameter_sweep,
    parallel_ticker_analysis,
    shutdown_all_executors,
)

__all__ = [
    # Cache Manager
    "IntelligentCacheManager",
    "get_cache_manager",
    "cache_signals",
    "get_cached_signals",
    "cache_portfolio_results",
    "get_cached_portfolio_results",
    "cache_computation",
    "get_cached_computation",
    # Parallel Executor
    "AdaptiveThreadPoolExecutor",
    "get_executor",
    "shutdown_all_executors",
    "parallel_ticker_analysis",
    "parallel_parameter_sweep",
    # Batch Processor
    "TickerBatchProcessor",
    "ParameterSweepProcessor",
    "BatchResult",
    "batch_analyze_tickers",
    "batch_parameter_sweep",
]
