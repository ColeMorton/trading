#!/usr/bin/env python3
"""
Portfolio Constructor for Optimal Portfolio Creation

Constructs optimal portfolios by testing different sizes (5, 7, 9) and selecting
the configuration with the highest efficiency_score.
"""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from app.concurrency.tools.asset_strategy_loader import AssetStrategyLoader
from app.concurrency.tools.permutation import find_optimal_permutation
from app.concurrency.tools.types import StrategyConfig
from app.tools.exceptions import DataLoadError


logger = logging.getLogger(__name__)


@dataclass
class PortfolioConstructionResult:
    """Result of portfolio construction process."""

    asset: str
    optimal_size: int
    optimal_portfolio: list[StrategyConfig]
    efficiency_score: float
    portfolio_stats: dict[str, Any]
    size_comparison: dict[int, dict[str, Any]]
    total_strategies_evaluated: int


class PortfolioConstructor:
    """Constructs optimal portfolios from strategy universe."""

    def __init__(self, strategy_loader: AssetStrategyLoader | None = None):
        """Initialize constructor with optional strategy loader."""
        self.strategy_loader = strategy_loader or AssetStrategyLoader()

    def construct_optimal_portfolio(
        self,
        asset: str,
        process_strategies_func: Callable,
        analyze_concurrency_func: Callable,
        log_func: Callable[[str, str], None],
        portfolio_sizes: list[int] | None = None,
        min_score: float = 1.0,
    ) -> PortfolioConstructionResult:
        """
        Construct optimal portfolio for given asset.

        Args:
            asset: Asset symbol (e.g., 'MSFT', 'NVDA')
            process_strategies_func: Function to process strategies
            analyze_concurrency_func: Function to analyze concurrency
            log_func: Logging function
            portfolio_sizes: List of portfolio sizes to test (default: [5, 7, 9])
            min_score: Minimum Score threshold for strategy inclusion

        Returns:
            PortfolioConstructionResult with optimal portfolio and analysis

        Raises:
            DataLoadError: If no viable portfolios can be constructed
        """
        if portfolio_sizes is None:
            portfolio_sizes = [5, 7, 9]

        log_func(f"Starting portfolio construction for {asset}", "info")

        # Load strategies for asset
        try:
            strategies = self.strategy_loader.load_strategies_for_asset(
                asset,
                min_score=min_score,
            )
        except DataLoadError as e:
            log_func(f"Failed to load strategies for {asset}: {e}", "error")
            raise

        log_func(
            f"Loaded {len(strategies)} strategies for {asset} (Score >= {min_score})",
            "info",
        )

        # Validate we have enough strategies for largest portfolio
        max_size = max(portfolio_sizes)
        if len(strategies) < max_size:
            log_func(
                f"Warning: Only {len(strategies)} strategies available, reducing portfolio sizes",
                "warning",
            )
            portfolio_sizes = [
                size for size in portfolio_sizes if size <= len(strategies)
            ]

        if not portfolio_sizes:
            msg = f"Not enough strategies for any portfolio construction (need at least {min(portfolio_sizes or [5])})"
            raise DataLoadError(
                msg,
            )

        # Test each portfolio size
        size_results = {}
        best_size = None
        best_score = -1
        best_portfolio = None
        best_stats = None

        for size in portfolio_sizes:
            log_func(f"Testing portfolio size: {size}", "info")

            try:
                # Find optimal permutation for this size
                optimal_strategies, stats, _ = find_optimal_permutation(
                    strategies=strategies,
                    process_strategies_func=process_strategies_func,
                    analyze_concurrency_func=analyze_concurrency_func,
                    log=log_func,
                    min_strategies=size,
                    max_permutations=5000,  # Reasonable limit for performance
                )

                efficiency_score = stats.get("efficiency_score", 0.0)

                size_results[size] = {
                    "strategies": optimal_strategies,
                    "efficiency_score": efficiency_score,
                    "stats": stats,
                    "strategy_count": len(optimal_strategies),
                }

                log_func(
                    f"Size {size} - Efficiency Score: {efficiency_score:.4f}",
                    "info",
                )

                # Track best result
                if efficiency_score > best_score:
                    best_score = efficiency_score
                    best_size = size
                    best_portfolio = optimal_strategies
                    best_stats = stats

            except Exception as e:
                log_func(f"Failed to optimize portfolio size {size}: {e}", "error")
                size_results[size] = {"error": str(e), "efficiency_score": 0.0}

        # Validate we found at least one viable portfolio
        if best_portfolio is None:
            msg = f"Failed to construct viable portfolio for {asset}"
            raise DataLoadError(msg)

        log_func(
            f"Optimal portfolio: {best_size} strategies with efficiency_score {best_score:.4f}",
            "info",
        )

        # Create result
        return PortfolioConstructionResult(
            asset=asset,
            optimal_size=best_size,
            optimal_portfolio=best_portfolio,
            efficiency_score=best_score,
            portfolio_stats=best_stats,
            size_comparison=size_results,
            total_strategies_evaluated=len(strategies),
        )

    def generate_construction_report(
        self,
        result: PortfolioConstructionResult,
    ) -> dict[str, Any]:
        """Generate comprehensive report of portfolio construction process."""

        # Strategy composition analysis
        strategy_composition = []
        for strategy in result.optimal_portfolio:
            strategy_composition.append(
                {
                    "strategy_id": strategy.strategy_id,
                    "ticker": strategy.ticker,
                    "strategy_type": strategy.strategy_type,
                    "fast_period": strategy.fast_period,
                    "slow_period": strategy.slow_period,
                    "score": strategy.score,
                    "sharpe_ratio": strategy.sharpe_ratio,
                    "total_return": strategy.total_return,
                    "max_drawdown": strategy.max_drawdown,
                    "allocation": strategy.allocation,
                },
            )

        # Size comparison summary
        size_comparison_summary = {}
        for size, data in result.size_comparison.items():
            if "error" not in data:
                size_comparison_summary[size] = {
                    "efficiency_score": data["efficiency_score"],
                    "strategy_count": data["strategy_count"],
                    "selected": size == result.optimal_size,
                }
            else:
                size_comparison_summary[size] = {
                    "error": data["error"],
                    "selected": False,
                }

        # Portfolio metrics summary
        portfolio_metrics = {}
        if result.portfolio_stats:
            portfolio_metrics = {
                "efficiency_score": result.efficiency_score,
                "total_weighted_efficiency": result.portfolio_stats.get(
                    "total_weighted_efficiency",
                    0.0,
                ),
                "average_efficiency": result.portfolio_stats.get(
                    "average_efficiency",
                    0.0,
                ),
                "total_periods": result.portfolio_stats.get("total_periods", 0),
                "concurrent_periods": result.portfolio_stats.get(
                    "concurrent_periods",
                    0,
                ),
                "diversification_score": result.portfolio_stats.get(
                    "diversification_score",
                    0.0,
                ),
                "independence_factor": result.portfolio_stats.get(
                    "independence_factor",
                    0.0,
                ),
            }

        # Strategy type and parameter analysis
        strategy_types = {}
        parameter_ranges = {"fast_periods": [], "slow_periods": []}

        for strategy in result.optimal_portfolio:
            strategy_types[strategy.strategy_type] = (
                strategy_types.get(strategy.strategy_type, 0) + 1
            )
            if strategy.fast_period > 0:
                parameter_ranges["fast_periods"].append(strategy.fast_period)
            if strategy.slow_period > 0:
                parameter_ranges["slow_periods"].append(strategy.slow_period)

        parameter_summary = {}
        if parameter_ranges["fast_periods"]:
            parameter_summary["fast_period_range"] = {
                "min": min(parameter_ranges["fast_periods"]),
                "max": max(parameter_ranges["fast_periods"]),
                "count": len(parameter_ranges["fast_periods"]),
            }
        if parameter_ranges["slow_periods"]:
            parameter_summary["slow_period_range"] = {
                "min": min(parameter_ranges["slow_periods"]),
                "max": max(parameter_ranges["slow_periods"]),
                "count": len(parameter_ranges["slow_periods"]),
            }

        return {
            "construction_summary": {
                "asset": result.asset,
                "optimal_portfolio_size": result.optimal_size,
                "efficiency_score": result.efficiency_score,
                "total_strategies_evaluated": result.total_strategies_evaluated,
                "construction_method": "optimal_permutation_with_size_comparison",
            },
            "strategy_composition": strategy_composition,
            "portfolio_metrics": portfolio_metrics,
            "size_comparison": size_comparison_summary,
            "diversification_analysis": {
                "strategy_types": strategy_types,
                "parameter_ranges": parameter_summary,
            },
            "construction_metadata": {
                "filtering_criteria": "Score >= 1.0",
                "portfolio_sizes_tested": list(result.size_comparison.keys()),
                "optimization_method": "efficiency_score_maximization",
            },
        }

    def validate_construction_feasibility(
        self,
        asset: str,
        min_score: float = 1.0,
    ) -> dict[str, Any]:
        """Validate if portfolio construction is feasible for given asset."""
        try:
            validation = self.strategy_loader.validate_asset_data(asset)

            # Check if construction is feasible
            feasible_sizes = []
            if validation.get("score_filtered_strategies", 0) >= 5:
                feasible_sizes.append(5)
            if validation.get("score_filtered_strategies", 0) >= 7:
                feasible_sizes.append(7)
            if validation.get("score_filtered_strategies", 0) >= 9:
                feasible_sizes.append(9)

            validation["feasible_portfolio_sizes"] = feasible_sizes
            validation["construction_feasible"] = len(feasible_sizes) > 0

            return validation

        except Exception as e:
            return {
                "asset": asset,
                "error": str(e),
                "construction_feasible": False,
                "feasible_portfolio_sizes": [],
            }
