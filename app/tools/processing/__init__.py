"""
Performance optimization processing module.

This module provides intelligent caching, parallel execution, batch processing,
and memory optimization capabilities optimized for trading system workloads.

Components:
- cache_manager: Intelligent file-based caching with TTL and LRU cleanup
- parallel_executor: Adaptive ThreadPool with dynamic sizing
- batch_processor: Optimized batch processing for tickers and parameter sweeps
- memory_optimizer: Object pooling, GC management, and memory monitoring
- streaming_processor: Large file streaming with automatic chunking
- data_converter: Optimized Polars-Pandas conversions with lazy evaluation
- mmap_accessor: Memory-mapped file access for large datasets
"""

from .batch_processor import (
    BatchResult,
    MemoryEfficientParameterSweep,
    ParameterSweepProcessor,
    TickerBatchProcessor,
    batch_analyze_tickers,
    batch_parameter_sweep,
    memory_efficient_parameter_sweep,
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
from .data_converter import BatchConverter, DataConverter, to_pandas, to_polars
from .memory_optimizer import (
    DataFramePool,
    MemoryMonitor,
    MemoryOptimizer,
    ObjectPool,
    configure_memory_optimizer,
    get_memory_optimizer,
)
from .mmap_accessor import (
    MemoryMappedFile,
    MMapAccessor,
    MMapCSVReader,
    get_mmap_accessor,
)
from .parallel_executor import (
    AdaptiveThreadPoolExecutor,
    get_executor,
    parallel_parameter_sweep,
    parallel_ticker_analysis,
    shutdown_all_executors,
)
from .streaming_processor import (
    CSVChunkProcessor,
    StreamingProcessor,
    read_large_csv,
    stream_csv,
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
    "MemoryEfficientParameterSweep",
    "BatchResult",
    "batch_analyze_tickers",
    "batch_parameter_sweep",
    "memory_efficient_parameter_sweep",
    # Memory Optimizer
    "MemoryOptimizer",
    "DataFramePool",
    "MemoryMonitor",
    "ObjectPool",
    "get_memory_optimizer",
    "configure_memory_optimizer",
    # Data Converter
    "DataConverter",
    "BatchConverter",
    "to_pandas",
    "to_polars",
    # Streaming Processor
    "StreamingProcessor",
    "CSVChunkProcessor",
    "stream_csv",
    "read_large_csv",
    # Memory-Mapped Accessor
    "MemoryMappedFile",
    "MMapCSVReader",
    "MMapAccessor",
    "get_mmap_accessor",
]
