"""
Optimized Horizon Calculation Module.

This module provides efficient calculation of horizon metrics with caching
and optimized data processing for improved performance.
"""

from collections.abc import Callable
from pathlib import Path
import time
from typing import Any, TypeVar

import numpy as np

from app.tools.setup_logging import setup_logging


# Type definitions
T = TypeVar("T")
HorizonMetrics = dict[str, dict[str, float]]
HorizonCache = dict[str, dict[int, np.ndarray]]


class HorizonCalculator:
    """Class for efficient calculation of horizon metrics with caching."""

    def __init__(self, log: Callable[[str, str], None] | None = None):
        """Initialize the HorizonCalculator class.

        Args:
            log: Optional logging function. If not provided, a default logger will be created.
        """
        if log is None:
            # Create a default logger if none provided
            self.log, _, _, _ = setup_logging(
                "horizon_calculator",
                Path("./logs"),
                "horizon_calculator.log",
            )
        else:
            self.log = log

        # Initialize cache
        self._reset_cache()

    def _reset_cache(self) -> None:
        """Reset the internal cache."""
        # Cache structure: {cache_key: {horizon: horizon_returns_array}}
        self._cache: HorizonCache = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dict[str, int]: Dictionary with cache statistics
        """
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_size": len(self._cache),
            "hit_ratio": (
                self._cache_hits / (self._cache_hits + self._cache_misses)
                if (self._cache_hits + self._cache_misses) > 0
                else 0
            ),
        }

    def _generate_cache_key(self, signals: np.ndarray, returns: np.ndarray) -> str:
        """Generate a unique cache key for the input arrays.

        Args:
            signals: Array of signals
            returns: Array of returns

        Returns:
            str: Cache key
        """
        # Use hash of arrays for cache key
        signals_hash = hash(signals.tobytes())
        returns_hash = hash(returns.tobytes())
        return f"{signals_hash}_{returns_hash}"

    def calculate_horizon_metrics(
        self,
        signals: np.ndarray,
        returns: np.ndarray,
        horizons: list[int] | None = None,
        min_sample_size: int = 20,
        use_cache: bool = True,
    ) -> HorizonMetrics:
        """Calculate performance metrics for different time horizons with optimized processing.

        Args:
            signals: Array of signals
            returns: Array of returns
            horizons: List of horizon periods to calculate (default: [1, 3, 5, 10])
            min_sample_size: Minimum sample size for valid horizon metrics
            use_cache: Whether to use caching (default: True)

        Returns:
            Dict[str, Dict[str, float]]: Dictionary of horizon metrics
        """
        start_time = time.time()

        try:
            if horizons is None:
                horizons = [1, 3, 5, 10]

            self.log(f"Calculating horizon metrics for periods: {horizons}", "info")

            # Validate inputs
            if len(signals) != len(returns):
                self.log(
                    f"Signal and return arrays must be the same length: {len(signals)} vs {len(returns)}",
                    "error",
                )
                return {}

            # Check if we have enough data for any horizon
            if len(returns) <= min(horizons):
                self.log("Insufficient data for any horizon", "warning")
                return {}

            # Generate cache key if using cache
            cache_key = None
            if use_cache:
                cache_key = self._generate_cache_key(signals, returns)

                # Check if we have this data in cache
                if cache_key in self._cache:
                    self._cache_hits += 1
                    self.log(
                        f"Cache hit for horizon calculation (key: {cache_key[:10]}...)",
                        "debug",
                    )
                else:
                    self._cache_misses += 1
                    self.log(
                        f"Cache miss for horizon calculation (key: {cache_key[:10]}...)",
                        "debug",
                    )
                    # Initialize cache for this key
                    self._cache[cache_key] = {}

            # Create a position array from signals (only once)
            positions = np.zeros_like(signals)
            for i in range(1, len(signals)):
                if signals[i - 1] != 0:
                    positions[i] = signals[i - 1]

            # Calculate results for each horizon
            results = {}

            for horizon in horizons:
                # Skip if we don't have enough data
                if len(returns) <= horizon:
                    self.log(f"Insufficient data for horizon {horizon}", "warning")
                    continue

                # Check if we have this horizon in cache
                horizon_returns_np = None
                if (
                    use_cache
                    and cache_key in self._cache
                    and horizon in self._cache[cache_key]
                ):
                    horizon_returns_np = self._cache[cache_key][horizon]
                    self.log(
                        f"Using cached horizon returns for horizon {horizon}",
                        "debug",
                    )
                else:
                    # Calculate horizon returns
                    horizon_returns = self._calculate_horizon_returns(
                        positions,
                        returns,
                        horizon,
                    )

                    # Skip if no positions were active
                    if len(horizon_returns) == 0:
                        self.log(
                            f"No active positions for horizon {horizon}",
                            "warning",
                        )
                        continue

                    # Convert to numpy array for calculations
                    horizon_returns_np = np.array(horizon_returns)

                    # Store in cache if using cache
                    if use_cache and cache_key is not None:
                        self._cache[cache_key][horizon] = horizon_returns_np

                # Skip if insufficient sample size
                if len(horizon_returns_np) < min_sample_size:
                    self.log(
                        f"Insufficient sample size for horizon {horizon}: {len(horizon_returns_np)} < {min_sample_size}",
                        "warning",
                    )
                    continue

                # Calculate metrics for this horizon
                metrics = self._calculate_metrics_from_returns(horizon_returns_np)
                results[str(horizon)] = metrics

            elapsed_time = time.time() - start_time
            self.log(
                f"Horizon metrics calculation completed in {elapsed_time:.4f} seconds",
                "info",
            )

            return results
        except Exception as e:
            self.log(f"Error calculating horizon metrics: {e!s}", "error")
            return {}

    def _calculate_horizon_returns(
        self,
        positions: np.ndarray,
        returns: np.ndarray,
        horizon: int,
    ) -> list[float]:
        """Calculate returns over a specific horizon for all positions.

        Args:
            positions: Array of positions
            returns: Array of returns
            horizon: Horizon period

        Returns:
            List[float]: List of horizon returns
        """
        # Pre-allocate list with estimated size
        max(100, len(positions) // 10)  # Rough estimate
        horizon_returns: list[float] = []
        horizon_returns_append = (
            horizon_returns.append
        )  # Local reference for faster append

        # Use vectorized operations where possible
        # Create a rolling window view of returns for efficient slicing
        # This avoids creating new arrays for each position
        for i in range(len(positions) - horizon):
            if positions[i] != 0:  # If there's an active position
                if positions[i] > 0:  # Long position
                    # Use direct slicing for small horizons, sum in place
                    horizon_return = np.sum(returns[i : i + horizon])
                else:  # Short position
                    horizon_return = -np.sum(returns[i : i + horizon])

                horizon_returns_append(horizon_return)

        return horizon_returns

    def _calculate_metrics_from_returns(self, returns: np.ndarray) -> dict[str, float]:
        """Calculate metrics from an array of returns.

        Args:
            returns: Array of returns

        Returns:
            Dict[str, float]: Dictionary of metrics
        """
        # Calculate metrics efficiently
        avg_return = float(np.mean(returns))
        win_rate = float(np.mean(returns > 0))
        std_return = float(np.std(returns)) if len(returns) > 1 else 0.0
        sharpe = float(avg_return / std_return) if std_return > 0 else 0.0

        return {
            "avg_return": avg_return,
            "win_rate": win_rate,
            "sharpe": sharpe,
            "sample_size": len(returns),
        }

    def find_best_horizon(
        self,
        horizon_metrics: HorizonMetrics,
        config: dict[str, Any] | None = None,
    ) -> int | None:
        """Find the best performing time horizon.

        Args:
            horizon_metrics: Dictionary of horizon metrics
            config: Configuration dictionary with weights and thresholds
                - SHARPE_WEIGHT: Weight for Sharpe ratio (default: 0.6)
                - WIN_RATE_WEIGHT: Weight for win rate (default: 0.3)
                - SAMPLE_SIZE_WEIGHT: Weight for sample size (default: 0.1)
                - SAMPLE_SIZE_FACTOR: Normalization factor for sample size (default: 100)
                - MIN_SAMPLE_SIZE: Minimum sample size (default: 20)

        Returns:
            Optional[int]: Best horizon period or None if no valid horizons
        """
        try:
            if not horizon_metrics:
                return None

            # Default configuration
            if config is None:
                config = {
                    "SHARPE_WEIGHT": 0.6,
                    "WIN_RATE_WEIGHT": 0.3,
                    "SAMPLE_SIZE_WEIGHT": 0.1,
                    "SAMPLE_SIZE_FACTOR": 100,
                    "MIN_SAMPLE_SIZE": 20,
                }

            best_horizon = None
            best_score = -float("inf")

            # Extract configuration parameters
            sharpe_weight = config.get("SHARPE_WEIGHT", 0.6)
            win_rate_weight = config.get("WIN_RATE_WEIGHT", 0.3)
            sample_size_weight = config.get("SAMPLE_SIZE_WEIGHT", 0.1)
            sample_size_factor = config.get("SAMPLE_SIZE_FACTOR", 100)
            min_sample_size = config.get("MIN_SAMPLE_SIZE", 20)

            for horizon_str, metrics in horizon_metrics.items():
                # Get metrics with defaults
                sharpe = metrics.get("sharpe", 0)
                win_rate = metrics.get("win_rate", 0)
                sample_size = metrics.get("sample_size", 0)

                # Skip horizons with insufficient data
                if sample_size < min_sample_size:
                    continue

                # Calculate a combined score
                sample_size_norm = min(1.0, sample_size / sample_size_factor)
                combined_score = (
                    sharpe_weight * sharpe
                    + win_rate_weight * win_rate
                    + sample_size_weight * sample_size_norm
                )

                if combined_score > best_score:
                    best_score = combined_score
                    best_horizon = int(horizon_str)

            return best_horizon
        except Exception as e:
            self.log(f"Error finding best horizon: {e!s}", "error")
            return None


# Singleton instance for global use
_horizon_calculator = None


def get_horizon_calculator(
    log: Callable[[str, str], None] | None = None,
) -> HorizonCalculator:
    """Get or create the singleton HorizonCalculator instance.

    Args:
        log: Optional logging function

    Returns:
        HorizonCalculator: Singleton instance
    """
    global _horizon_calculator
    if _horizon_calculator is None:
        _horizon_calculator = HorizonCalculator(log)
    return _horizon_calculator


def calculate_horizon_metrics(
    signals: np.ndarray,
    returns: np.ndarray,
    horizons: list[int] | None = None,
    min_sample_size: int = 20,
    use_cache: bool = True,
    log: Callable[[str, str], None] | None = None,
) -> HorizonMetrics:
    """Calculate horizon metrics using the singleton calculator.

    Args:
        signals: Array of signals
        returns: Array of returns
        horizons: List of horizon periods to calculate
        min_sample_size: Minimum sample size for valid horizon metrics
        use_cache: Whether to use caching
        log: Optional logging function

    Returns:
        Dict[str, Dict[str, float]]: Dictionary of horizon metrics
    """
    calculator = get_horizon_calculator(log)
    return calculator.calculate_horizon_metrics(
        signals,
        returns,
        horizons,
        min_sample_size,
        use_cache,
    )


def find_best_horizon(
    horizon_metrics: HorizonMetrics,
    config: dict[str, Any] | None = None,
    log: Callable[[str, str], None] | None = None,
) -> int | None:
    """Find the best horizon using the singleton calculator.

    Args:
        horizon_metrics: Dictionary of horizon metrics
        config: Configuration dictionary
        log: Optional logging function

    Returns:
        Optional[int]: Best horizon period or None if no valid horizons
    """
    calculator = get_horizon_calculator(log)
    return calculator.find_best_horizon(horizon_metrics, config)


def get_cache_stats(log: Callable[[str, str], None] | None = None) -> dict[str, int]:
    """Get cache statistics from the singleton calculator.

    Args:
        log: Optional logging function

    Returns:
        Dict[str, int]: Dictionary with cache statistics
    """
    calculator = get_horizon_calculator(log)
    return calculator.get_cache_stats()


def reset_cache(log: Callable[[str, str], None] | None = None) -> None:
    """Reset the cache in the singleton calculator.

    Args:
        log: Optional logging function
    """
    calculator = get_horizon_calculator(log)
    calculator._reset_cache()
