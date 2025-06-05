"""
Parameter Testing Engine

This module provides a unified parameter testing and optimization engine that consolidates
the parameter sweeping logic from multiple strategy execution patterns into a single,
efficient, and consistent implementation.

Key Features:
- Unified parameter optimization across all strategy types
- Parallel execution with configurable concurrency
- Progressive filtering and early termination
- Comprehensive performance metrics calculation
- Memory-efficient batch processing
- Robust error handling and recovery
"""

import asyncio
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from itertools import product
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import polars as pl
from pydantic import BaseModel, Field

from app.core.strategy_framework import UnifiedStrategyConfig, UnifiedStrategyResult


@dataclass
class ParameterSet:
    """Individual parameter combination for testing."""
    
    id: str
    parameters: Dict[str, Any]
    priority: float = 1.0  # Higher priority = tested first
    
    def __post_init__(self):
        """Generate ID if not provided."""
        if not self.id:
            param_str = "_".join(f"{k}={v}" for k, v in sorted(self.parameters.items()))
            self.id = f"params_{hash(param_str)}"


@dataclass
class OptimizationConstraints:
    """Constraints for parameter optimization."""
    
    min_trades: int = 10
    max_drawdown: float = 0.30  # 30%
    min_sharpe: float = 0.5
    min_win_rate: float = 0.40  # 40%
    min_profit_factor: float = 1.1
    
    def validate_result(self, result: UnifiedStrategyResult) -> bool:
        """Check if result meets all constraints."""
        metrics = result.metrics
        
        # Check minimum trades
        if metrics.get("Trades", 0) < self.min_trades:
            return False
        
        # Check maximum drawdown
        if metrics.get("Max Drawdown [%]", 100) > self.max_drawdown * 100:
            return False
        
        # Check minimum Sharpe ratio
        if metrics.get("Sharpe Ratio", -999) < self.min_sharpe:
            return False
        
        # Check minimum win rate
        if metrics.get("Win Rate [%]", 0) < self.min_win_rate * 100:
            return False
        
        # Check minimum profit factor
        if metrics.get("Profit Factor", 0) < self.min_profit_factor:
            return False
        
        return True


class ParameterTestingEngine:
    """
    Unified parameter testing and optimization engine.
    
    This engine consolidates the parameter testing logic from all strategy execution
    patterns, providing a single, efficient, and consistent way to optimize strategy
    parameters across different strategy types.
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        batch_size: int = 50,
        memory_limit_mb: int = 1000,
        enable_early_termination: bool = True
    ):
        """
        Initialize the parameter testing engine.
        
        Args:
            max_workers: Maximum number of parallel workers
            batch_size: Number of parameter sets to process in each batch
            memory_limit_mb: Memory limit for result caching
            enable_early_termination: Enable early termination for poor performers
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.memory_limit_mb = memory_limit_mb
        self.enable_early_termination = enable_early_termination
        
        # Internal state
        self._results_cache: Dict[str, UnifiedStrategyResult] = {}
        self._execution_stats = {
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "early_terminations": 0,
            "total_time": 0.0
        }
    
    def generate_parameter_grid(
        self,
        parameter_ranges: Dict[str, List[Any]],
        strategy_type: str = None
    ) -> List[ParameterSet]:
        """
        Generate parameter combinations from ranges.
        
        Args:
            parameter_ranges: Dictionary of parameter names to value lists
            strategy_type: Strategy type for intelligent prioritization
            
        Returns:
            List of parameter sets ordered by priority
        """
        # Generate all combinations
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())
        
        parameter_sets = []
        for combination in product(*param_values):
            params = dict(zip(param_names, combination))
            param_set = ParameterSet(
                id="",  # Will be auto-generated
                parameters=params,
                priority=self._calculate_priority(params, strategy_type)
            )
            parameter_sets.append(param_set)
        
        # Sort by priority (highest first)
        parameter_sets.sort(key=lambda x: x.priority, reverse=True)
        
        return parameter_sets
    
    def _calculate_priority(
        self, 
        parameters: Dict[str, Any], 
        strategy_type: str = None
    ) -> float:
        """
        Calculate priority for parameter set.
        
        Higher priority parameter sets are tested first, allowing for
        early discovery of good parameter combinations.
        """
        priority = 1.0
        
        if strategy_type == "MA_CROSS":
            # For MA cross, prioritize moderate window sizes and reasonable ratios
            short_window = parameters.get("short_window", 20)
            long_window = parameters.get("long_window", 50)
            
            # Prefer ratios between 2:1 and 4:1
            if long_window > 0:
                ratio = long_window / short_window
                if 2.0 <= ratio <= 4.0:
                    priority += 0.5
                elif ratio < 1.5 or ratio > 6.0:
                    priority -= 0.3
            
            # Prefer moderate window sizes (avoid extremes)
            if 10 <= short_window <= 30 and 30 <= long_window <= 100:
                priority += 0.3
        
        elif strategy_type == "MACD":
            # For MACD, prioritize standard parameters
            short_period = parameters.get("short_period", 12)
            long_period = parameters.get("long_period", 26)
            signal_period = parameters.get("signal_period", 9)
            
            # Standard MACD parameters get highest priority
            if short_period == 12 and long_period == 26 and signal_period == 9:
                priority += 1.0
            
            # Reasonable variations get moderate priority
            if 8 <= short_period <= 15 and 20 <= long_period <= 35 and 7 <= signal_period <= 12:
                priority += 0.5
        
        return priority
    
    async def optimize_parameters(
        self,
        strategy_executor: Callable,
        ticker: str,
        base_config: UnifiedStrategyConfig,
        parameter_ranges: Dict[str, List[Any]],
        constraints: OptimizationConstraints = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Optimize parameters for a single ticker.
        
        Args:
            strategy_executor: Strategy execution function
            ticker: Ticker symbol to optimize
            base_config: Base configuration
            parameter_ranges: Parameter ranges to test
            constraints: Optimization constraints
            progress_callback: Progress reporting callback
            
        Returns:
            Optimization results including best parameters and metrics
        """
        start_time = time.time()
        
        if constraints is None:
            constraints = OptimizationConstraints()
        
        # Generate parameter sets
        parameter_sets = self.generate_parameter_grid(
            parameter_ranges, 
            base_config.strategy_type
        )
        
        self._execution_stats["total_tests"] = len(parameter_sets)
        
        # Execute parameter testing in batches
        all_results = []
        valid_results = []
        
        for i in range(0, len(parameter_sets), self.batch_size):
            batch = parameter_sets[i:i + self.batch_size]
            
            # Execute batch
            batch_results = await self._execute_parameter_batch(
                strategy_executor,
                ticker,
                base_config,
                batch
            )
            
            # Filter and validate results
            for result in batch_results:
                all_results.append(result)
                
                if result and constraints.validate_result(result):
                    valid_results.append(result)
            
            # Progress reporting
            if progress_callback:
                progress = min(100.0, (i + len(batch)) / len(parameter_sets) * 100)
                await progress_callback(f"Testing {ticker}", progress)
            
            # Early termination check
            if self.enable_early_termination and len(valid_results) >= 10:
                # If we have 10+ valid results, check if we should stop early
                avg_performance = np.mean([
                    r.metrics.get("Total Return [%]", 0) for r in valid_results[-10:]
                ])
                
                if avg_performance < 5.0:  # Less than 5% average return
                    self._execution_stats["early_terminations"] += 1
                    break
        
        # Calculate final statistics
        execution_time = time.time() - start_time
        self._execution_stats["total_time"] += execution_time
        self._execution_stats["successful_tests"] = len([r for r in all_results if r is not None])
        self._execution_stats["failed_tests"] = len([r for r in all_results if r is None])
        
        # Find best result
        best_result = None
        if valid_results:
            # Sort by multiple criteria (Sharpe ratio, then total return)
            best_result = max(
                valid_results,
                key=lambda r: (
                    r.metrics.get("Sharpe Ratio", -999),
                    r.metrics.get("Total Return [%]", -999)
                )
            )
        
        return {
            "ticker": ticker,
            "best_result": best_result,
            "best_parameters": best_result.best_parameters if best_result else None,
            "best_metrics": best_result.metrics if best_result else None,
            "total_tested": len(all_results),
            "valid_results": len(valid_results),
            "execution_time": execution_time,
            "all_results": all_results[:100],  # Limit to top 100 for memory
            "constraints": constraints,
            "parameter_ranges": parameter_ranges
        }
    
    async def _execute_parameter_batch(
        self,
        strategy_executor: Callable,
        ticker: str,
        base_config: UnifiedStrategyConfig,
        parameter_sets: List[ParameterSet]
    ) -> List[Optional[UnifiedStrategyResult]]:
        """Execute a batch of parameter sets in parallel."""
        
        # Create tasks for parallel execution
        tasks = []
        for param_set in parameter_sets:
            # Create modified config for this parameter set
            config = base_config.model_copy(deep=True)
            config.parameters.update(param_set.parameters)
            
            # Create execution task
            task = asyncio.create_task(
                self._execute_single_parameter_set(
                    strategy_executor,
                    ticker,
                    config,
                    param_set.id
                )
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, handling exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(None)  # Failed execution
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_single_parameter_set(
        self,
        strategy_executor: Callable,
        ticker: str,
        config: UnifiedStrategyConfig,
        param_set_id: str
    ) -> Optional[UnifiedStrategyResult]:
        """Execute a single parameter set."""
        try:
            # Check cache first
            cache_key = f"{ticker}_{param_set_id}_{hash(str(config.parameters))}"
            if cache_key in self._results_cache:
                return self._results_cache[cache_key]
            
            # Execute strategy
            result = await strategy_executor(ticker, config)
            
            # Cache result (with memory management)
            if len(self._results_cache) < 1000:  # Limit cache size
                self._results_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            # Log error and return None
            print(f"Error testing {ticker} with params {config.parameters}: {str(e)}")
            return None
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return self._execution_stats.copy()
    
    def clear_cache(self) -> None:
        """Clear the results cache."""
        self._results_cache.clear()
    
    def export_results(
        self,
        results: List[Dict[str, Any]],
        output_path: str,
        format: str = "csv"
    ) -> None:
        """
        Export optimization results to file.
        
        Args:
            results: List of optimization results
            output_path: Output file path
            format: Export format (csv, json, parquet)
        """
        if not results:
            return
        
        # Flatten results for export
        flattened_data = []
        
        for result_set in results:
            ticker = result_set["ticker"]
            best_result = result_set["best_result"]
            
            if best_result:
                row = {
                    "ticker": ticker,
                    "execution_time": result_set["execution_time"],
                    "total_tested": result_set["total_tested"],
                    "valid_results": result_set["valid_results"],
                    **best_result.metrics,
                    **best_result.best_parameters
                }
                flattened_data.append(row)
        
        # Export based on format
        df = pd.DataFrame(flattened_data)
        
        if format.lower() == "csv":
            df.to_csv(output_path, index=False)
        elif format.lower() == "json":
            df.to_json(output_path, orient="records", indent=2)
        elif format.lower() == "parquet":
            df.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Utility functions for common optimization scenarios

def create_ma_cross_parameter_ranges(
    short_min: int = 5,
    short_max: int = 50,
    short_step: int = 5,
    long_min: int = 20,
    long_max: int = 200,
    long_step: int = 10
) -> Dict[str, List[int]]:
    """Create parameter ranges for MA Cross strategy optimization."""
    return {
        "short_window": list(range(short_min, short_max + 1, short_step)),
        "long_window": list(range(long_min, long_max + 1, long_step))
    }


def create_macd_parameter_ranges(
    short_min: int = 8,
    short_max: int = 16,
    long_min: int = 20,
    long_max: int = 35,
    signal_min: int = 7,
    signal_max: int = 12
) -> Dict[str, List[int]]:
    """Create parameter ranges for MACD strategy optimization."""
    return {
        "short_period": list(range(short_min, short_max + 1)),
        "long_period": list(range(long_min, long_max + 1)),
        "signal_period": list(range(signal_min, signal_max + 1))
    }


def create_rsi_parameter_ranges(
    window_min: int = 10,
    window_max: int = 25,
    oversold_min: int = 20,
    oversold_max: int = 35,
    overbought_min: int = 65,
    overbought_max: int = 80
) -> Dict[str, List[int]]:
    """Create parameter ranges for RSI strategy optimization."""
    return {
        "rsi_window": list(range(window_min, window_max + 1)),
        "oversold": list(range(oversold_min, oversold_max + 1, 5)),
        "overbought": list(range(overbought_min, overbought_max + 1, 5))
    }