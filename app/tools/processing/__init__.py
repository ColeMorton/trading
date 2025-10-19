"""
Performance optimization processing module.

This module provides intelligent caching, parallel execution, batch processing,
memory optimization, and advanced monitoring capabilities optimized for trading system workloads.

Phase 1-3 Components:
- cache_manager: Intelligent file-based caching with TTL and LRU cleanup
- parallel_executor: Adaptive ThreadPool with dynamic sizing
- batch_processor: Optimized batch processing for tickers and parameter sweeps
- memory_optimizer: Object pooling, GC management, and memory monitoring
- streaming_processor: Large file streaming with automatic chunking
- data_converter: Optimized Polars-Pandas conversions with lazy evaluation
- mmap_accessor: Memory-mapped file access for large datasets

Phase 4 Advanced Components:
- cache_warmer: Intelligent cache warming based on historical access patterns
- performance_monitor: Structured performance logging with JSON metrics output
- auto_tuner: Auto-tuning system for ThreadPool and memory pool sizes
- precompute_engine: Result pre-computation for common parameter combinations
- performance_dashboard: Performance monitoring dashboard with HTML visualization
"""

from .auto_tuner import (
    AutoTuner,
    ResourceMonitor,
    TuningRecommendation,
    configure_auto_tuning,
    get_auto_tuner,
)
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

# Phase 4 Advanced Components
from .cache_warmer import (
    AccessTracker,
    CacheWarmer,
    configure_cache_warming,
    create_portfolio_generator,
    create_signal_generator,
    get_cache_warmer,
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
from .performance_dashboard import (
    DashboardGenerator,
    LogAnalyzer,
    analyze_performance_logs,
    generate_performance_dashboard,
    get_dashboard_generator,
)
from .performance_monitor import (
    OperationMetrics,
    PerformanceAlert,
    PerformanceMetric,
    PerformanceMonitor,
    add_metric,
    configure_performance_monitoring,
    get_performance_monitor,
    monitor_function,
    monitor_operation,
)
from .precompute_engine import (
    ParameterCombination,
    PrecomputeEngine,
    PrecomputeJob,
    UsageAnalyzer,
    configure_precomputing,
    get_precompute_engine,
)
from .streaming_processor import (
    CSVChunkProcessor,
    StreamingProcessor,
    read_large_csv,
    stream_csv,
)


__all__ = [
    "AccessTracker",
    # Parallel Executor
    "AdaptiveThreadPoolExecutor",
    # Auto-Tuner
    "AutoTuner",
    "BatchConverter",
    "BatchResult",
    "CSVChunkProcessor",
    # Phase 4 Advanced Components
    # Cache Warmer
    "CacheWarmer",
    # Performance Dashboard
    "DashboardGenerator",
    # Data Converter
    "DataConverter",
    "DataFramePool",
    # Cache Manager
    "IntelligentCacheManager",
    "LogAnalyzer",
    "MMapAccessor",
    "MMapCSVReader",
    "MemoryEfficientParameterSweep",
    # Memory-Mapped Accessor
    "MemoryMappedFile",
    "MemoryMonitor",
    # Memory Optimizer
    "MemoryOptimizer",
    "ObjectPool",
    "OperationMetrics",
    "ParameterCombination",
    "ParameterSweepProcessor",
    "PerformanceAlert",
    "PerformanceMetric",
    # Performance Monitor
    "PerformanceMonitor",
    # Pre-compute Engine
    "PrecomputeEngine",
    "PrecomputeJob",
    "ResourceMonitor",
    # Streaming Processor
    "StreamingProcessor",
    # Batch Processor
    "TickerBatchProcessor",
    "TuningRecommendation",
    "UsageAnalyzer",
    "add_metric",
    "analyze_performance_logs",
    "batch_analyze_tickers",
    "batch_parameter_sweep",
    "cache_computation",
    "cache_portfolio_results",
    "cache_signals",
    "configure_auto_tuning",
    "configure_cache_warming",
    "configure_memory_optimizer",
    "configure_performance_monitoring",
    "configure_precomputing",
    "create_portfolio_generator",
    "create_signal_generator",
    "generate_performance_dashboard",
    "get_auto_tuner",
    "get_cache_manager",
    "get_cache_warmer",
    "get_cached_computation",
    "get_cached_portfolio_results",
    "get_cached_signals",
    "get_dashboard_generator",
    "get_executor",
    "get_memory_optimizer",
    "get_mmap_accessor",
    "get_performance_monitor",
    "get_precompute_engine",
    "memory_efficient_parameter_sweep",
    "monitor_function",
    "monitor_operation",
    "parallel_parameter_sweep",
    "parallel_ticker_analysis",
    "read_large_csv",
    "shutdown_all_executors",
    "stream_csv",
    "to_pandas",
    "to_polars",
]
