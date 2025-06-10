"""
Performance Optimization Utilities for MACD Parameter Testing

This module provides utilities for optimizing MACD parameter combination performance,
including intelligent parameter limiting, async execution recommendations, and
performance monitoring.

Key Features:
- Parameter combination estimation and limiting
- Async execution threshold recommendations
- Performance monitoring and metrics
- Resource usage optimization
- Progress tracking for large parameter spaces
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.api.models.strategy_analysis import MACrossRequest, StrategyTypeEnum


logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution mode recommendations based on parameter complexity"""
    SYNC_FAST = "sync_fast"
    SYNC_STANDARD = "sync_standard"
    ASYNC_RECOMMENDED = "async_recommended"
    ASYNC_REQUIRED = "async_required"


@dataclass
class ParameterComplexity:
    """Analysis of parameter space complexity"""
    total_combinations: int
    ticker_count: int
    strategy_count: int
    estimated_execution_time: float
    recommended_mode: ExecutionMode
    memory_estimate_mb: float
    should_limit_parameters: bool
    max_recommended_combinations: int


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    start_time: float
    end_time: Optional[float] = None
    combinations_processed: int = 0
    total_combinations: int = 0
    current_ticker: Optional[str] = None
    current_strategy: Optional[str] = None
    memory_usage_mb: float = 0.0
    error_count: int = 0

    @property
    def elapsed_time(self) -> float:
        """Get elapsed execution time"""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def progress_percentage(self) -> float:
        """Get completion percentage"""
        if self.total_combinations == 0:
            return 0.0
        return (self.combinations_processed / self.total_combinations) * 100

    @property
    def estimated_time_remaining(self) -> float:
        """Estimate remaining execution time"""
        if self.combinations_processed == 0:
            return 0.0
        
        rate = self.combinations_processed / self.elapsed_time
        remaining = self.total_combinations - self.combinations_processed
        return remaining / rate if rate > 0 else 0.0


class PerformanceOptimizer:
    """Performance optimization utilities for MACD parameter testing"""

    # Configuration thresholds
    SYNC_FAST_THRESHOLD = 50
    SYNC_STANDARD_THRESHOLD = 200
    ASYNC_RECOMMENDED_THRESHOLD = 500
    ASYNC_REQUIRED_THRESHOLD = 1000
    
    # Performance estimates (in seconds per combination)
    MACD_EXECUTION_TIME_PER_COMBINATION = 0.1
    MA_EXECUTION_TIME_PER_COMBINATION = 0.05
    
    # Memory estimates (in MB per combination)
    MEMORY_PER_COMBINATION = 0.5
    MAX_MEMORY_LIMIT_MB = 2048  # 2GB limit

    def __init__(self):
        self.active_metrics: Dict[str, PerformanceMetrics] = {}

    def analyze_parameter_complexity(self, request: MACrossRequest) -> ParameterComplexity:
        """
        Analyze the complexity of parameter combinations and provide recommendations
        
        Args:
            request: The strategy analysis request
            
        Returns:
            ParameterComplexity analysis with recommendations
        """
        # Calculate combinations for each strategy type
        total_combinations = 0
        
        # Get ticker count
        ticker_count = len(request.ticker) if isinstance(request.ticker, list) else 1
        strategy_count = len(request.strategy_types)
        
        for strategy_type in request.strategy_types:
            if strategy_type == StrategyTypeEnum.MACD:
                combinations = self._calculate_macd_combinations(request)
            else:
                combinations = self._calculate_ma_combinations(request)
            
            total_combinations += combinations

        # Multiply by tickers and windows
        total_combinations *= ticker_count * (request.windows or 10)

        # Estimate execution time
        estimated_time = self._estimate_execution_time(total_combinations, request.strategy_types)
        
        # Estimate memory usage
        memory_estimate = total_combinations * self.MEMORY_PER_COMBINATION
        
        # Determine execution mode
        recommended_mode = self._determine_execution_mode(total_combinations)
        
        # Check if parameters should be limited
        should_limit = (
            total_combinations > self.ASYNC_REQUIRED_THRESHOLD or
            memory_estimate > self.MAX_MEMORY_LIMIT_MB
        )
        
        max_recommended = self._calculate_max_recommended_combinations(
            ticker_count, strategy_count
        )

        return ParameterComplexity(
            total_combinations=total_combinations,
            ticker_count=ticker_count,
            strategy_count=strategy_count,
            estimated_execution_time=estimated_time,
            recommended_mode=recommended_mode,
            memory_estimate_mb=memory_estimate,
            should_limit_parameters=should_limit,
            max_recommended_combinations=max_recommended
        )

    def _calculate_macd_combinations(self, request: MACrossRequest) -> int:
        """Calculate MACD parameter combinations"""
        if not hasattr(request, 'short_window_start') or request.short_window_start is None:
            return 1
        
        step = request.step or 1
        
        short_range = max(1, (request.short_window_end - request.short_window_start) // step + 1)
        long_range = max(1, (request.long_window_end - request.long_window_start) // step + 1)
        signal_range = max(1, (request.signal_window_end - request.signal_window_start) // step + 1)
        
        return short_range * long_range * signal_range

    def _calculate_ma_combinations(self, request: MACrossRequest) -> int:
        """Calculate MA (SMA/EMA) parameter combinations"""
        # For MA strategies, combinations are based on window pairs
        windows = request.windows or 10
        return windows * (windows - 1) // 2  # Combination of window pairs

    def _estimate_execution_time(self, combinations: int, strategy_types: List[StrategyTypeEnum]) -> float:
        """Estimate total execution time"""
        time_per_combination = 0
        
        for strategy_type in strategy_types:
            if strategy_type == StrategyTypeEnum.MACD:
                time_per_combination += self.MACD_EXECUTION_TIME_PER_COMBINATION
            else:
                time_per_combination += self.MA_EXECUTION_TIME_PER_COMBINATION
        
        return combinations * time_per_combination

    def _determine_execution_mode(self, combinations: int) -> ExecutionMode:
        """Determine recommended execution mode based on combinations"""
        if combinations <= self.SYNC_FAST_THRESHOLD:
            return ExecutionMode.SYNC_FAST
        elif combinations <= self.SYNC_STANDARD_THRESHOLD:
            return ExecutionMode.SYNC_STANDARD
        elif combinations <= self.ASYNC_RECOMMENDED_THRESHOLD:
            return ExecutionMode.ASYNC_RECOMMENDED
        else:
            return ExecutionMode.ASYNC_REQUIRED

    def _calculate_max_recommended_combinations(self, ticker_count: int, strategy_count: int) -> int:
        """Calculate maximum recommended combinations based on resources"""
        base_limit = self.ASYNC_RECOMMENDED_THRESHOLD
        
        # Adjust based on ticker and strategy count
        adjustment_factor = 1.0 / (ticker_count * strategy_count)
        
        return int(base_limit * adjustment_factor)

    def optimize_request_parameters(self, request: MACrossRequest) -> Tuple[MACrossRequest, List[str]]:
        """
        Optimize request parameters to improve performance
        
        Args:
            request: Original request
            
        Returns:
            Tuple of (optimized_request, optimization_warnings)
        """
        complexity = self.analyze_parameter_complexity(request)
        warnings = []
        optimized_request = request.copy()

        # If parameters should be limited
        if complexity.should_limit_parameters:
            warnings.append(
                f"Parameter combination count ({complexity.total_combinations}) exceeds "
                f"recommended limit. Consider reducing parameter ranges."
            )

            # Auto-optimize MACD parameters if present
            if StrategyTypeEnum.MACD in request.strategy_types:
                optimized_request = self._optimize_macd_parameters(optimized_request, warnings)

            # Recommend async execution
            if not optimized_request.async_execution:
                optimized_request.async_execution = True
                warnings.append("Enabling async execution for large parameter space.")

        # Memory optimization warnings
        if complexity.memory_estimate_mb > self.MAX_MEMORY_LIMIT_MB:
            warnings.append(
                f"Estimated memory usage ({complexity.memory_estimate_mb:.1f}MB) "
                f"exceeds limit ({self.MAX_MEMORY_LIMIT_MB}MB). Consider reducing scope."
            )

        return optimized_request, warnings

    def _optimize_macd_parameters(self, request: MACrossRequest, warnings: List[str]) -> MACrossRequest:
        """Optimize MACD parameters to reduce combinations"""
        optimized = request.copy()
        
        # Increase step size if too small
        if (request.step or 1) == 1:
            optimized.step = 2
            warnings.append("Increased MACD step size to 2 for performance.")

        # Reduce window ranges if too large
        short_range = (request.short_window_end or 15) - (request.short_window_start or 6)
        if short_range > 10:
            optimized.short_window_end = (request.short_window_start or 6) + 10
            warnings.append("Reduced MACD short window range for performance.")

        long_range = (request.long_window_end or 35) - (request.long_window_start or 12)
        if long_range > 15:
            optimized.long_window_end = (request.long_window_start or 12) + 15
            warnings.append("Reduced MACD long window range for performance.")

        signal_range = (request.signal_window_end or 12) - (request.signal_window_start or 5)
        if signal_range > 8:
            optimized.signal_window_end = (request.signal_window_start or 5) + 8
            warnings.append("Reduced MACD signal window range for performance.")

        return optimized

    def start_performance_tracking(self, request_id: str, total_combinations: int) -> PerformanceMetrics:
        """Start performance tracking for a request"""
        metrics = PerformanceMetrics(
            start_time=time.time(),
            total_combinations=total_combinations
        )
        self.active_metrics[request_id] = metrics
        
        logger.info(f"Started performance tracking for {request_id}: {total_combinations} combinations")
        return metrics

    def update_progress(self, request_id: str, combinations_processed: int, 
                       current_ticker: Optional[str] = None, 
                       current_strategy: Optional[str] = None) -> Optional[PerformanceMetrics]:
        """Update progress for an active request"""
        if request_id not in self.active_metrics:
            return None

        metrics = self.active_metrics[request_id]
        metrics.combinations_processed = combinations_processed
        metrics.current_ticker = current_ticker
        metrics.current_strategy = current_strategy

        # Log progress at intervals
        if combinations_processed % 100 == 0:
            logger.info(
                f"Progress {request_id}: {metrics.progress_percentage:.1f}% "
                f"({combinations_processed}/{metrics.total_combinations}) - "
                f"ETA: {metrics.estimated_time_remaining:.1f}s"
            )

        return metrics

    def finish_performance_tracking(self, request_id: str) -> Optional[PerformanceMetrics]:
        """Finish performance tracking and return final metrics"""
        if request_id not in self.active_metrics:
            return None

        metrics = self.active_metrics[request_id]
        metrics.end_time = time.time()

        logger.info(
            f"Completed {request_id}: {metrics.total_combinations} combinations "
            f"in {metrics.elapsed_time:.2f}s "
            f"({metrics.combinations_processed / metrics.elapsed_time:.1f} combinations/sec)"
        )

        # Remove from active tracking
        del self.active_metrics[request_id]
        return metrics

    def get_performance_recommendations(self, request: MACrossRequest) -> Dict[str, Any]:
        """Get comprehensive performance recommendations"""
        complexity = self.analyze_parameter_complexity(request)
        
        recommendations = {
            "execution_mode": complexity.recommended_mode.value,
            "estimated_time_seconds": complexity.estimated_execution_time,
            "estimated_memory_mb": complexity.memory_estimate_mb,
            "total_combinations": complexity.total_combinations,
            "should_use_async": complexity.recommended_mode in [
                ExecutionMode.ASYNC_RECOMMENDED, 
                ExecutionMode.ASYNC_REQUIRED
            ],
            "recommendations": []
        }

        # Add specific recommendations
        if complexity.should_limit_parameters:
            recommendations["recommendations"].append({
                "type": "parameter_optimization",
                "message": "Consider reducing parameter ranges to improve performance",
                "max_recommended_combinations": complexity.max_recommended_combinations
            })

        if complexity.recommended_mode == ExecutionMode.ASYNC_REQUIRED:
            recommendations["recommendations"].append({
                "type": "async_required",
                "message": "Async execution required for this parameter space",
                "reason": f"Combinations ({complexity.total_combinations}) exceed sync limit"
            })

        if complexity.memory_estimate_mb > self.MAX_MEMORY_LIMIT_MB:
            recommendations["recommendations"].append({
                "type": "memory_warning",
                "message": "Memory usage may exceed system limits",
                "estimated_mb": complexity.memory_estimate_mb,
                "limit_mb": self.MAX_MEMORY_LIMIT_MB
            })

        return recommendations


# Global instance for use across the application
performance_optimizer = PerformanceOptimizer()


# Helper functions for easy access
def analyze_request_complexity(request: MACrossRequest) -> ParameterComplexity:
    """Convenience function to analyze request complexity"""
    return performance_optimizer.analyze_parameter_complexity(request)


def get_performance_recommendations(request: MACrossRequest) -> Dict[str, Any]:
    """Convenience function to get performance recommendations"""
    return performance_optimizer.get_performance_recommendations(request)


def optimize_request(request: MACrossRequest) -> Tuple[MACrossRequest, List[str]]:
    """Convenience function to optimize request parameters"""
    return performance_optimizer.optimize_request_parameters(request)