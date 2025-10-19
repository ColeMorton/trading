"""
Permutation Optimization Service.

This service provides strategy combination optimization using systematic
permutation analysis to find the most efficient portfolio configurations.
"""

from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import itertools
import time
from typing import Any

from app.concurrency.config import ConcurrencyConfig
from app.concurrency.tools.analysis import analyze_concurrency
from app.concurrency.tools.strategy_id import generate_strategy_id
from app.concurrency.tools.strategy_processor import process_strategies
from app.tools.exceptions import TradingSystemError
from app.tools.portfolio import StrategyConfig


@dataclass
class OptimizationResult:
    """Result of permutation optimization."""

    best_permutation: list[str]
    best_efficiency: float
    best_results: dict[str, Any]
    total_analyzed: int
    execution_time: float
    improvement_percentage: float
    convergence_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationProgress:
    """Progress tracking for optimization."""

    total_permutations: int = 0
    completed_permutations: int = 0
    current_best_efficiency: float = -float("inf")
    current_best_permutation: list[str] | None = None
    start_time: float | None = None
    estimated_remaining_time: float | None = None

    def get_progress_percentage(self) -> float:
        """Get completion percentage."""
        if self.total_permutations == 0:
            return 0.0
        return (self.completed_permutations / self.total_permutations) * 100

    def update_progress(
        self,
        completed: int,
        efficiency: float | None = None,
        permutation: list[str] | None = None,
    ):
        """Update progress tracking."""
        self.completed_permutations = completed

        if efficiency is not None and efficiency > self.current_best_efficiency:
            self.current_best_efficiency = efficiency
            self.current_best_permutation = permutation

        # Calculate estimated remaining time
        if self.start_time and completed > 0:
            elapsed = time.time() - self.start_time
            avg_time_per_permutation = elapsed / completed
            remaining_permutations = self.total_permutations - completed
            self.estimated_remaining_time = (
                avg_time_per_permutation * remaining_permutations
            )


class PermutationOptimizationService:
    """Service for finding optimal strategy combinations through permutation analysis.

    This service systematically evaluates different combinations of trading strategies
    to find the subset that maximizes efficiency while maintaining diversification.
    """

    def __init__(
        self,
        enable_parallel_processing: bool = False,
        max_workers: int | None = None,
        enable_early_stopping: bool = True,
        convergence_threshold: float = 0.001,
        convergence_window: int = 50,
        log: Callable[[str, str], None] | None = None,
    ):
        """Initialize the permutation optimization service.

        Args:
            enable_parallel_processing: Enable parallel execution
            max_workers: Maximum worker threads/processes
            enable_early_stopping: Enable early stopping when convergence detected
            convergence_threshold: Threshold for convergence detection
            convergence_window: Window size for convergence detection
            log: Logging function
        """
        self.enable_parallel_processing = enable_parallel_processing
        self.max_workers = max_workers or 4
        self.enable_early_stopping = enable_early_stopping
        self.convergence_threshold = convergence_threshold
        self.convergence_window = convergence_window
        self.log = log or self._default_log

        # Progress tracking
        self.progress = OptimizationProgress()

        # Convergence tracking
        self.efficiency_history: list[float] = []
        self.convergence_detected = False

    def optimize_strategy_selection(
        self,
        strategies: list[StrategyConfig],
        min_strategies: int = 3,
        max_permutations: int | None = None,
        allocation_mode: str = "EQUAL",
        config_overrides: dict[str, Any] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> OptimizationResult:
        """Find optimal strategy combination using permutation analysis.

        Args:
            strategies: List of strategy configurations
            min_strategies: Minimum strategies per combination
            max_permutations: Maximum permutations to evaluate
            allocation_mode: Allocation strategy for optimization
            config_overrides: Configuration overrides
            progress_callback: Progress callback function

        Returns:
            OptimizationResult containing the best combination found
        """
        try:
            self.log(f"Starting optimization with {len(strategies)} strategies", "info")

            # Initialize progress tracking
            self.progress.start_time = time.time()

            # Generate permutations
            permutations = list(
                self._generate_permutations(
                    strategies, min_strategies, max_permutations
                )
            )

            self.progress.total_permutations = len(permutations)
            self.log(f"Generated {len(permutations)} permutations to evaluate", "info")

            # Build optimization configuration
            config = self._build_optimization_config(allocation_mode, config_overrides)

            # Run optimization
            if self.enable_parallel_processing and len(permutations) > 10:
                result = self._run_parallel_optimization(
                    permutations, config, progress_callback
                )
            else:
                result = self._run_sequential_optimization(
                    permutations, config, progress_callback
                )

            # Calculate improvement percentage
            if len(strategies) > 0:
                baseline_efficiency = self._calculate_baseline_efficiency(
                    strategies, config
                )
                improvement = (
                    (result.best_efficiency - baseline_efficiency) / baseline_efficiency
                ) * 100
                result.improvement_percentage = improvement

            execution_time = time.time() - self.progress.start_time
            result.execution_time = execution_time

            self.log(f"Optimization completed in {execution_time:.2f}s", "info")
            self.log(f"Best efficiency: {result.best_efficiency:.4f}", "info")
            self.log(f"Best combination: {result.best_permutation}", "info")

            return result

        except Exception as e:
            error_msg = f"Strategy optimization failed: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def optimize_with_constraints(
        self,
        strategies: list[StrategyConfig],
        constraints: dict[str, Any],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> OptimizationResult:
        """Optimize strategy selection with additional constraints.

        Args:
            strategies: List of strategy configurations
            constraints: Optimization constraints
            progress_callback: Progress callback function

        Returns:
            OptimizationResult with constraint-compliant combination
        """
        try:
            self.log("Starting constrained optimization", "info")

            # Extract constraints
            constraints.get("min_strategies", 3)
            constraints.get("max_strategies", len(strategies))
            constraints.get("max_correlation", 0.8)
            constraints.get("min_diversification", 0.2)
            constraints.get("sector_limits", {})

            # Generate valid permutations with constraints
            valid_permutations = list(
                self._generate_constrained_permutations(strategies, constraints)
            )

            self.log(
                f"Generated {len(valid_permutations)} constraint-compliant permutations",
                "info",
            )

            if not valid_permutations:
                raise TradingSystemError(
                    "No permutations satisfy the given constraints"
                )

            # Run optimization on valid permutations
            config = self._build_optimization_config("EQUAL", constraints)

            best_efficiency = -float("inf")
            best_permutation = None
            best_results = None

            for i, permutation in enumerate(valid_permutations):
                # Update progress
                if progress_callback:
                    progress_callback(i, len(valid_permutations))

                # Evaluate permutation
                efficiency, results = self._evaluate_permutation(permutation, config)

                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    best_permutation = [generate_strategy_id(s) for s in permutation]
                    best_results = results

            return OptimizationResult(
                best_permutation=best_permutation,
                best_efficiency=best_efficiency,
                best_results=best_results,
                total_analyzed=len(valid_permutations),
                execution_time=time.time() - self.progress.start_time,
                improvement_percentage=0.0,  # Would calculate against baseline
            )

        except Exception as e:
            error_msg = f"Constrained optimization failed: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def _generate_permutations(
        self,
        strategies: list[StrategyConfig],
        min_strategies: int,
        max_permutations: int | None,
    ) -> Iterator[list[StrategyConfig]]:
        """Generate strategy permutations for optimization."""
        n_strategies = len(strategies)

        if n_strategies < min_strategies:
            self.log(
                f"Not enough strategies ({n_strategies}) for minimum requirement ({min_strategies})",
                "warning",
            )
            return

        total_generated = 0

        # Generate combinations from min_strategies to n_strategies
        for size in range(min_strategies, n_strategies + 1):
            for combination in itertools.combinations(strategies, size):
                if max_permutations and total_generated >= max_permutations:
                    return

                yield list(combination)
                total_generated += 1

    def _generate_constrained_permutations(
        self,
        strategies: list[StrategyConfig],
        constraints: dict[str, Any],
    ) -> Iterator[list[StrategyConfig]]:
        """Generate permutations that satisfy constraints."""
        min_strategies = constraints.get("min_strategies", 3)
        max_strategies = constraints.get("max_strategies", len(strategies))
        sector_limits = constraints.get("sector_limits", {})

        for size in range(min_strategies, min(max_strategies + 1, len(strategies) + 1)):
            for combination in itertools.combinations(strategies, size):
                # Check sector constraints
                if self._satisfies_sector_constraints(combination, sector_limits):
                    yield list(combination)

    def _satisfies_sector_constraints(
        self,
        combination: tuple[StrategyConfig, ...],
        sector_limits: dict[str, int],
    ) -> bool:
        """Check if combination satisfies sector constraints."""
        if not sector_limits:
            return True

        sector_counts = {}
        for strategy in combination:
            # Extract sector from ticker (simplified logic)
            ticker = strategy.get("ticker", strategy.get("Ticker", ""))
            sector = self._get_ticker_sector(ticker)
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

        # Check limits
        for sector, limit in sector_limits.items():
            if sector_counts.get(sector, 0) > limit:
                return False

        return True

    def _get_ticker_sector(self, ticker: str) -> str:
        """Get sector for ticker (simplified mapping)."""
        # This would integrate with a proper sector mapping service
        tech_tickers = {"AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"}
        crypto_tickers = {"BTC-USD", "ETH-USD"}

        if ticker in tech_tickers:
            return "technology"
        if ticker in crypto_tickers:
            return "cryptocurrency"
        return "other"

    def _run_parallel_optimization(
        self,
        permutations: list[list[StrategyConfig]],
        config: ConcurrencyConfig,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> OptimizationResult:
        """Run optimization using parallel processing."""
        self.log(
            f"Running parallel optimization with {self.max_workers} workers", "info"
        )

        best_efficiency = -float("inf")
        best_permutation = None
        best_results = None
        completed = 0

        # Use ThreadPoolExecutor for I/O bound tasks
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_permutation = {
                executor.submit(self._evaluate_permutation, perm, config): perm
                for perm in permutations
            }

            # Process completed tasks
            for future in as_completed(future_to_permutation):
                permutation = future_to_permutation[future]
                completed += 1

                try:
                    efficiency, results = future.result()

                    if efficiency > best_efficiency:
                        best_efficiency = efficiency
                        best_permutation = [
                            generate_strategy_id(s) for s in permutation
                        ]
                        best_results = results

                    # Update progress
                    self.progress.update_progress(
                        completed, efficiency, best_permutation
                    )

                    if progress_callback:
                        progress_callback(completed, len(permutations))

                    # Check for early stopping
                    if self._check_convergence(efficiency):
                        self.log("Convergence detected, stopping early", "info")
                        break

                except Exception as e:
                    self.log(f"Error evaluating permutation: {e!s}", "warning")

        return OptimizationResult(
            best_permutation=best_permutation,
            best_efficiency=best_efficiency,
            best_results=best_results,
            total_analyzed=completed,
            execution_time=0.0,  # Will be set by caller
            improvement_percentage=0.0,  # Will be calculated by caller
        )

    def _run_sequential_optimization(
        self,
        permutations: list[list[StrategyConfig]],
        config: ConcurrencyConfig,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> OptimizationResult:
        """Run optimization sequentially."""
        self.log("Running sequential optimization", "info")

        best_efficiency = -float("inf")
        best_permutation = None
        best_results = None

        for i, permutation in enumerate(permutations):
            try:
                # Evaluate permutation
                efficiency, results = self._evaluate_permutation(permutation, config)

                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    best_permutation = [generate_strategy_id(s) for s in permutation]
                    best_results = results

                # Update progress
                self.progress.update_progress(i + 1, efficiency, best_permutation)

                if progress_callback:
                    progress_callback(i + 1, len(permutations))

                # Check for early stopping
                if self._check_convergence(efficiency):
                    self.log("Convergence detected, stopping early", "info")
                    break

            except Exception as e:
                self.log(f"Error evaluating permutation {i}: {e!s}", "warning")
                continue

        return OptimizationResult(
            best_permutation=best_permutation,
            best_efficiency=best_efficiency,
            best_results=best_results,
            total_analyzed=i + 1,
            execution_time=0.0,  # Will be set by caller
            improvement_percentage=0.0,  # Will be calculated by caller
        )

    def _evaluate_permutation(
        self,
        permutation: list[StrategyConfig],
        config: ConcurrencyConfig,
    ) -> tuple[float, dict[str, Any]]:
        """Evaluate a single permutation."""
        try:
            # Process strategies
            processed_data = process_strategies(permutation, config)

            if not processed_data:
                return 0.0, {}

            # Run concurrency analysis
            results = analyze_concurrency(processed_data, config)

            # Extract efficiency score
            efficiency = results.get("portfolio_efficiency", {}).get(
                "efficiency_score", 0.0
            )

            return efficiency, results

        except Exception as e:
            self.log(f"Error evaluating permutation: {e!s}", "warning")
            return 0.0, {}

    def _check_convergence(self, efficiency: float) -> bool:
        """Check if optimization has converged."""
        if not self.enable_early_stopping:
            return False

        self.efficiency_history.append(efficiency)

        # Need enough history to check convergence
        if len(self.efficiency_history) < self.convergence_window:
            return False

        # Check if recent improvements are below threshold
        recent_history = self.efficiency_history[-self.convergence_window :]
        max_recent = max(recent_history)
        min_recent = min(recent_history)

        improvement = (max_recent - min_recent) / max_recent if max_recent > 0 else 0

        if improvement < self.convergence_threshold:
            self.convergence_detected = True
            return True

        return False

    def _calculate_baseline_efficiency(
        self,
        strategies: list[StrategyConfig],
        config: ConcurrencyConfig,
    ) -> float:
        """Calculate baseline efficiency using all strategies."""
        try:
            efficiency, _ = self._evaluate_permutation(strategies, config)
            return efficiency
        except Exception:
            return 0.0

    def _build_optimization_config(
        self,
        allocation_mode: str,
        config_overrides: dict[str, Any] | None = None,
    ) -> ConcurrencyConfig:
        """Build configuration for optimization."""
        config = {
            "ALLOCATION_MODE": allocation_mode,
            "REFRESH": False,  # Use cached data for faster optimization
            "VISUALIZATION": False,  # Disable visualization during optimization
            "EXPORT_TRADE_HISTORY": False,  # Disable export during optimization
        }

        if config_overrides:
            config.update(config_overrides)

        return config

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging implementation."""
        print(f"[{level.upper()}] {message}")


# Convenience functions
def find_optimal_strategy_combination(
    strategies: list[StrategyConfig],
    min_strategies: int = 3,
    max_permutations: int | None = None,
    enable_parallel_processing: bool = False,
    progress_callback: Callable[[int, int], None] | None = None,
) -> OptimizationResult:
    """Find optimal strategy combination using permutation optimization.

    This is a convenience function that creates and uses a PermutationOptimizationService.
    """
    service = PermutationOptimizationService(
        enable_parallel_processing=enable_parallel_processing
    )

    return service.optimize_strategy_selection(
        strategies=strategies,
        min_strategies=min_strategies,
        max_permutations=max_permutations,
        progress_callback=progress_callback,
    )


def optimize_with_risk_constraints(
    strategies: list[StrategyConfig],
    max_correlation: float = 0.8,
    max_sector_concentration: float = 0.5,
    min_diversification: float = 0.2,
    progress_callback: Callable[[int, int], None] | None = None,
) -> OptimizationResult:
    """Optimize strategy selection with risk constraints.

    This is a convenience function for risk-aware optimization.
    """
    constraints = {
        "max_correlation": max_correlation,
        "min_diversification": min_diversification,
        "sector_limits": {
            "technology": int(len(strategies) * max_sector_concentration),
            "cryptocurrency": int(len(strategies) * max_sector_concentration),
        },
    }

    service = PermutationOptimizationService()
    return service.optimize_with_constraints(
        strategies=strategies,
        constraints=constraints,
        progress_callback=progress_callback,
    )
