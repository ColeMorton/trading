"""
Memory optimization utilities for equity data export functionality.

This module provides memory-efficient processing techniques for large-scale
equity data export operations, including streaming, chunking, and data optimization.
"""

import gc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

import numpy as np
import pandas as pd

from app.tools.equity_data_extractor import EquityData
from app.tools.equity_export import export_equity_data_to_csv


@dataclass
class MemoryOptimizationConfig:
    """Configuration for memory optimization."""

    enable_streaming: bool = True
    chunk_size: int = 50
    enable_garbage_collection: bool = True
    optimize_data_types: bool = True
    memory_threshold_mb: float = 1000.0
    enable_progress_logging: bool = True


class EquityDataOptimizer:
    """Optimizes equity data for memory efficiency."""

    @staticmethod
    def optimize_equity_data(equity_data: EquityData) -> EquityData:
        """
        Optimize equity data by downcasting numeric types and reducing memory usage.

        Args:
            equity_data: Original equity data

        Returns:
            Memory-optimized equity data
        """

        # Convert arrays to optimal data types
        def optimize_array(arr: np.ndarray) -> np.ndarray:
            if arr.dtype == np.float64:
                # Try to downcast to float32 if precision allows
                arr_32 = arr.astype(np.float32)
                if np.allclose(arr, arr_32, rtol=1e-6):
                    return arr_32
            elif arr.dtype == np.int64:
                # Try to downcast integers
                if np.all(
                    (arr >= np.iinfo(np.int32).min) & (arr <= np.iinfo(np.int32).max)
                ):
                    return arr.astype(np.int32)
                elif np.all(
                    (arr >= np.iinfo(np.int16).min) & (arr <= np.iinfo(np.int16).max)
                ):
                    return arr.astype(np.int16)
            return arr

        return EquityData(
            timestamp=equity_data.timestamp,  # Keep timestamp as-is
            equity=optimize_array(equity_data.equity),
            equity_pct=optimize_array(equity_data.equity_pct),
            equity_change=optimize_array(equity_data.equity_change),
            equity_change_pct=optimize_array(equity_data.equity_change_pct),
            drawdown=optimize_array(equity_data.drawdown),
            drawdown_pct=optimize_array(equity_data.drawdown_pct),
            peak_equity=optimize_array(equity_data.peak_equity),
            mfe=optimize_array(equity_data.mfe),
            mae=optimize_array(equity_data.mae),
        )

    @staticmethod
    def estimate_memory_usage(equity_data: EquityData) -> float:
        """
        Estimate memory usage of equity data in MB.

        Args:
            equity_data: Equity data to analyze

        Returns:
            Estimated memory usage in MB
        """
        total_bytes = 0

        # Timestamp index
        if hasattr(equity_data.timestamp, "memory_usage"):
            memory_usage = equity_data.timestamp.memory_usage(deep=True)
            if hasattr(memory_usage, "sum"):
                total_bytes += memory_usage.sum()
            else:
                total_bytes += memory_usage
        else:
            total_bytes += len(equity_data.timestamp) * 8  # Approximate datetime64 size

        # Numeric arrays
        for field_name in [
            "equity",
            "equity_pct",
            "equity_change",
            "equity_change_pct",
            "drawdown",
            "drawdown_pct",
            "peak_equity",
            "mfe",
            "mae",
        ]:
            arr = getattr(equity_data, field_name)
            total_bytes += arr.nbytes

        return total_bytes / (1024 * 1024)  # Convert to MB


class StreamingEquityExporter:
    """Streaming exporter for large-scale equity data processing."""

    def __init__(self, config: MemoryOptimizationConfig):
        """
        Initialize streaming exporter.

        Args:
            config: Memory optimization configuration
        """
        self.config = config
        self.processed_count = 0
        self.exported_count = 0
        self.memory_peak = 0.0

    def chunk_portfolios(
        self, portfolios: List[Dict[str, Any]]
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Split portfolios into memory-efficient chunks.

        Args:
            portfolios: List of portfolios to chunk

        Yields:
            Chunks of portfolios
        """
        for i in range(0, len(portfolios), self.config.chunk_size):
            chunk = portfolios[i : i + self.config.chunk_size]
            yield chunk

    def stream_export_equity_data(
        self,
        portfolios: List[Dict[str, Any]],
        log: Callable[[str, str], None],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Export equity data using streaming approach for memory efficiency.

        Args:
            portfolios: List of portfolios with equity data
            log: Logging function
            config: Export configuration

        Returns:
            Export results summary
        """
        if not self.config.enable_streaming:
            # Fall back to regular batch export
            from app.tools.equity_export import export_equity_data_batch

            return export_equity_data_batch(portfolios, log, config)

        results = {
            "total_portfolios": len(portfolios),
            "exported_count": 0,
            "skipped_count": 0,
            "error_count": 0,
            "errors": [],
            "chunks_processed": 0,
            "memory_optimized": True,
        }

        # Check if equity export is enabled
        if not config.get("EQUITY_DATA", {}).get("EXPORT", False):
            log("Equity data export is disabled", "info")
            results["skipped_count"] = len(portfolios)
            return results

        log(
            f"Starting streaming equity export for {len(portfolios)} portfolios in chunks of {self.config.chunk_size}",
            "info",
        )

        # Process portfolios in chunks
        for chunk_idx, portfolio_chunk in enumerate(self.chunk_portfolios(portfolios)):
            if self.config.enable_progress_logging:
                log(
                    f"Processing chunk {chunk_idx + 1}, portfolios {chunk_idx * self.config.chunk_size + 1}-{min((chunk_idx + 1) * self.config.chunk_size, len(portfolios))}",
                    "info",
                )

            chunk_results = self._process_portfolio_chunk(portfolio_chunk, log, config)

            # Aggregate results
            results["exported_count"] += chunk_results["exported_count"]
            results["skipped_count"] += chunk_results["skipped_count"]
            results["error_count"] += chunk_results["error_count"]
            results["errors"].extend(chunk_results["errors"])
            results["chunks_processed"] += 1

            # Force garbage collection between chunks if enabled
            if self.config.enable_garbage_collection:
                gc.collect()

            # Check memory usage
            import psutil

            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            self.memory_peak = max(self.memory_peak, memory_usage)

            if memory_usage > self.config.memory_threshold_mb:
                log(
                    f"Memory usage ({memory_usage:.1f} MB) exceeds threshold ({self.config.memory_threshold_mb} MB), forcing garbage collection",
                    "warning",
                )
                gc.collect()

        # Final logging
        success_rate = (
            (results["exported_count"] / results["total_portfolios"]) * 100
            if results["total_portfolios"] > 0
            else 0
        )
        log(
            f"Streaming equity export completed: {results['exported_count']}/{results['total_portfolios']} exported ({success_rate:.1f}% success rate)",
            "info",
        )
        log(f"Memory peak usage: {self.memory_peak:.1f} MB", "info")

        return results

    def _process_portfolio_chunk(
        self,
        portfolio_chunk: List[Dict[str, Any]],
        log: Callable[[str, str], None],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process a single chunk of portfolios.

        Args:
            portfolio_chunk: Chunk of portfolios to process
            log: Logging function
            config: Export configuration

        Returns:
            Chunk processing results
        """
        chunk_results = {
            "exported_count": 0,
            "skipped_count": 0,
            "error_count": 0,
            "errors": [],
        }

        for portfolio in portfolio_chunk:
            try:
                # Check if portfolio has equity data
                equity_data = portfolio.get("_equity_data")
                if not equity_data:
                    chunk_results["skipped_count"] += 1
                    continue

                # Optimize equity data if enabled
                if self.config.optimize_data_types:
                    equity_data = EquityDataOptimizer.optimize_equity_data(equity_data)

                # Extract portfolio parameters
                ticker = portfolio.get("Ticker", "UNKNOWN")
                strategy_type = portfolio.get("Strategy Type", "UNKNOWN")
                fast_period = portfolio.get("Fast Period", 0)
                slow_period = portfolio.get("Slow Period", 0)
                signal_period = portfolio.get("Signal Period")

                # Export equity data
                success = export_equity_data_to_csv(
                    equity_data=equity_data,
                    ticker=ticker,
                    strategy_type=strategy_type,
                    fast_period=fast_period,
                    slow_period=slow_period,
                    signal_period=signal_period,
                    log=log,
                    overwrite=True,
                )

                if success:
                    chunk_results["exported_count"] += 1
                else:
                    chunk_results["skipped_count"] += 1

            except Exception as e:
                error_msg = f"Error exporting equity data for {portfolio.get('Ticker', 'UNKNOWN')}: {str(e)}"
                chunk_results["errors"].append(error_msg)
                chunk_results["error_count"] += 1
                log(error_msg, "error")

        return chunk_results


def create_memory_efficient_export_function(
    optimization_config: Optional[MemoryOptimizationConfig] = None,
) -> Callable:
    """
    Create a memory-efficient export function with optimizations.

    Args:
        optimization_config: Configuration for memory optimizations

    Returns:
        Optimized export function
    """
    if optimization_config is None:
        optimization_config = MemoryOptimizationConfig()

    def optimized_export_function(
        portfolios: List[Dict[str, Any]],
        log: Callable[[str, str], None],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Memory-optimized equity data export function.

        Args:
            portfolios: List of portfolios with equity data
            log: Logging function
            config: Export configuration

        Returns:
            Export results
        """
        exporter = StreamingEquityExporter(optimization_config)
        return exporter.stream_export_equity_data(portfolios, log, config)

    return optimized_export_function


def analyze_memory_requirements(portfolios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze memory requirements for equity data export.

    Args:
        portfolios: List of portfolios to analyze

    Returns:
        Memory analysis results
    """
    analysis = {
        "total_portfolios": len(portfolios),
        "portfolios_with_equity_data": 0,
        "estimated_memory_mb": 0.0,
        "largest_equity_dataset_mb": 0.0,
        "memory_by_strategy": {},
        "recommendations": [],
    }

    optimizer = EquityDataOptimizer()

    for portfolio in portfolios:
        equity_data = portfolio.get("_equity_data")
        if not equity_data:
            continue

        analysis["portfolios_with_equity_data"] += 1

        # Estimate memory usage
        memory_usage = optimizer.estimate_memory_usage(equity_data)
        analysis["estimated_memory_mb"] += memory_usage
        analysis["largest_equity_dataset_mb"] = max(
            analysis["largest_equity_dataset_mb"], memory_usage
        )

        # Track by strategy type
        strategy_type = portfolio.get("Strategy Type", "UNKNOWN")
        if strategy_type not in analysis["memory_by_strategy"]:
            analysis["memory_by_strategy"][strategy_type] = {
                "count": 0,
                "total_memory_mb": 0.0,
            }

        analysis["memory_by_strategy"][strategy_type]["count"] += 1
        analysis["memory_by_strategy"][strategy_type]["total_memory_mb"] += memory_usage

    # Generate recommendations
    if analysis["estimated_memory_mb"] > 1000:  # > 1GB
        analysis["recommendations"].append(
            "Consider enabling streaming export for large datasets"
        )

    if analysis["largest_equity_dataset_mb"] > 100:  # > 100MB for single dataset
        analysis["recommendations"].append(
            "Consider data type optimization for large individual datasets"
        )

    if analysis["portfolios_with_equity_data"] > 500:
        analysis["recommendations"].append(
            "Consider chunked processing for large portfolio counts"
        )

    if not analysis["recommendations"]:
        analysis["recommendations"].append(
            "Current dataset size is within optimal memory limits"
        )

    return analysis
