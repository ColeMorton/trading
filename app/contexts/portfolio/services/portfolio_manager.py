"""
Portfolio Manager Service

Focused service for portfolio management operations.
Extracted from the larger portfolio services for better maintainability.
"""

from dataclasses import dataclass
import logging
from typing import Any

from app.tools.config.statistical_analysis_config import SPDSConfig, get_spds_config


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics."""

    total_return: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    avg_trade_return: float


@dataclass
class PositionSizing:
    """Position sizing parameters."""

    position_size: float
    risk_per_trade: float
    max_position_size: float
    position_weight: float


class PortfolioManager:
    """
    Service for managing portfolio operations.

    This service handles:
    - Portfolio creation and management
    - Position sizing calculations
    - Portfolio optimization
    - Performance tracking
    """

    def __init__(
        self,
        config: SPDSConfig | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize the portfolio manager."""
        self.config = config or get_spds_config()
        self.logger = logger or logging.getLogger(__name__)

    def create_portfolio(
        self, strategies: list[dict[str, Any]], allocation_method: str = "equal_weight"
    ) -> dict[str, Any]:
        """Create a portfolio from multiple strategies."""
        if not strategies:
            return {
                "strategies": [],
                "allocation": {},
                "total_weight": 0.0,
                "portfolio_metrics": None,
            }

        try:
            # Calculate allocations
            allocations = self._calculate_allocations(strategies, allocation_method)

            # Calculate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(
                strategies, allocations
            )

            return {
                "strategies": strategies,
                "allocation": allocations,
                "total_weight": sum(allocations.values()),
                "portfolio_metrics": portfolio_metrics,
                "success": True,
            }

        except Exception as e:
            self.logger.error(f"Portfolio creation failed: {e!s}")
            return {
                "strategies": strategies,
                "allocation": {},
                "total_weight": 0.0,
                "portfolio_metrics": None,
                "error": str(e),
                "success": False,
            }

    def calculate_position_sizing(
        self,
        account_balance: float,
        risk_per_trade: float,
        strategy_count: int,
        max_position_pct: float = 0.1,
    ) -> PositionSizing:
        """Calculate position sizing parameters."""
        if account_balance <= 0 or risk_per_trade <= 0 or strategy_count <= 0:
            return PositionSizing(
                position_size=0.0,
                risk_per_trade=0.0,
                max_position_size=0.0,
                position_weight=0.0,
            )

        # Calculate position size based on risk per trade
        account_balance * risk_per_trade

        # Calculate position weight
        position_weight = 1.0 / strategy_count

        # Calculate actual position size
        position_size = account_balance * position_weight

        # Apply maximum position size limit
        max_position_size = account_balance * max_position_pct
        position_size = min(position_size, max_position_size)

        return PositionSizing(
            position_size=position_size,
            risk_per_trade=risk_per_trade,
            max_position_size=max_position_size,
            position_weight=position_weight,
        )

    def optimize_portfolio(
        self,
        strategies: list[dict[str, Any]],
        optimization_method: str = "sharpe_ratio",
    ) -> dict[str, Any]:
        """Optimize portfolio allocation."""
        if not strategies:
            return {
                "original_allocation": {},
                "optimized_allocation": {},
                "optimization_improvement": 0.0,
                "success": False,
            }

        try:
            # Get current equal-weight allocation
            current_allocation = self._calculate_allocations(strategies, "equal_weight")

            # Calculate optimized allocation
            optimized_allocation = self._optimize_allocation(
                strategies, optimization_method
            )

            # Calculate improvement
            current_metrics = self._calculate_portfolio_metrics(
                strategies, current_allocation
            )
            optimized_metrics = self._calculate_portfolio_metrics(
                strategies, optimized_allocation
            )

            improvement = self._calculate_improvement(
                current_metrics, optimized_metrics, optimization_method
            )

            return {
                "original_allocation": current_allocation,
                "optimized_allocation": optimized_allocation,
                "current_metrics": current_metrics,
                "optimized_metrics": optimized_metrics,
                "optimization_improvement": improvement,
                "success": True,
            }

        except Exception as e:
            self.logger.error(f"Portfolio optimization failed: {e!s}")
            return {
                "original_allocation": {},
                "optimized_allocation": {},
                "optimization_improvement": 0.0,
                "error": str(e),
                "success": False,
            }

    def _calculate_allocations(
        self, strategies: list[dict[str, Any]], allocation_method: str
    ) -> dict[str, float]:
        """Calculate allocation weights for strategies."""
        if not strategies:
            return {}

        allocations = {}

        if allocation_method == "equal_weight":
            weight_per_strategy = 1.0 / len(strategies)
            for i, strategy in enumerate(strategies):
                strategy_key = f"strategy_{i}"
                allocations[strategy_key] = weight_per_strategy

        elif allocation_method == "performance_weighted":
            # Weight by performance metrics
            total_performance = sum(
                strategy.get("performance", {}).get("total_return", 0.0)
                for strategy in strategies
            )

            if total_performance > 0:
                for i, strategy in enumerate(strategies):
                    strategy_key = f"strategy_{i}"
                    performance = strategy.get("performance", {}).get(
                        "total_return", 0.0
                    )
                    allocations[strategy_key] = performance / total_performance
            else:
                # Fall back to equal weight if no positive performance
                return self._calculate_allocations(strategies, "equal_weight")

        elif allocation_method == "risk_adjusted":
            # Weight by risk-adjusted returns (Sharpe ratio)
            total_sharpe = sum(
                max(strategy.get("performance", {}).get("sharpe_ratio", 0.0), 0.0)
                for strategy in strategies
            )

            if total_sharpe > 0:
                for i, strategy in enumerate(strategies):
                    strategy_key = f"strategy_{i}"
                    sharpe = max(
                        strategy.get("performance", {}).get("sharpe_ratio", 0.0), 0.0
                    )
                    allocations[strategy_key] = sharpe / total_sharpe
            else:
                # Fall back to equal weight if no positive Sharpe ratios
                return self._calculate_allocations(strategies, "equal_weight")

        else:
            raise ValueError(f"Unsupported allocation method: {allocation_method}")

        return allocations

    def _calculate_portfolio_metrics(
        self, strategies: list[dict[str, Any]], allocations: dict[str, float]
    ) -> PortfolioMetrics:
        """Calculate portfolio-level metrics."""
        if not strategies or not allocations:
            return PortfolioMetrics(
                total_return=0.0,
                win_rate=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                total_trades=0,
                avg_trade_return=0.0,
            )

        # Calculate weighted portfolio metrics
        total_return = 0.0
        win_rate = 0.0
        sharpe_ratio = 0.0
        max_drawdown = 0.0
        total_trades = 0
        avg_trade_return = 0.0

        for i, strategy in enumerate(strategies):
            strategy_key = f"strategy_{i}"
            weight = allocations.get(strategy_key, 0.0)

            if weight > 0:
                performance = strategy.get("performance", {})
                total_return += weight * performance.get("total_return", 0.0)
                win_rate += weight * performance.get("win_rate", 0.0)
                sharpe_ratio += weight * performance.get("sharpe_ratio", 0.0)
                max_drawdown = max(max_drawdown, performance.get("max_drawdown", 0.0))
                total_trades += performance.get("total_trades", 0)
                avg_trade_return += weight * performance.get("avg_trade_return", 0.0)

        return PortfolioMetrics(
            total_return=total_return,
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_trades=total_trades,
            avg_trade_return=avg_trade_return,
        )

    def _optimize_allocation(
        self, strategies: list[dict[str, Any]], optimization_method: str
    ) -> dict[str, float]:
        """Optimize allocation using specified method."""
        # This is a simplified optimization
        # In practice, you would use more sophisticated optimization algorithms

        if optimization_method == "sharpe_ratio":
            return self._calculate_allocations(strategies, "risk_adjusted")
        if optimization_method == "return":
            return self._calculate_allocations(strategies, "performance_weighted")
        if optimization_method == "equal_weight":
            return self._calculate_allocations(strategies, "equal_weight")
        raise ValueError(f"Unsupported optimization method: {optimization_method}")

    def _calculate_improvement(
        self,
        current_metrics: PortfolioMetrics,
        optimized_metrics: PortfolioMetrics,
        optimization_method: str,
    ) -> float:
        """Calculate improvement from optimization."""
        if optimization_method == "sharpe_ratio":
            if current_metrics.sharpe_ratio == 0:
                return float("inf") if optimized_metrics.sharpe_ratio > 0 else 0.0
            return (
                optimized_metrics.sharpe_ratio - current_metrics.sharpe_ratio
            ) / abs(current_metrics.sharpe_ratio)

        if optimization_method == "return":
            if current_metrics.total_return == 0:
                return float("inf") if optimized_metrics.total_return > 0 else 0.0
            return (
                optimized_metrics.total_return - current_metrics.total_return
            ) / abs(current_metrics.total_return)

        return 0.0

    def rebalance_portfolio(
        self,
        current_positions: dict[str, float],
        target_allocation: dict[str, float],
        total_portfolio_value: float,
    ) -> dict[str, Any]:
        """Calculate rebalancing trades needed."""
        rebalancing_trades = {}

        for strategy_key, target_weight in target_allocation.items():
            target_value = total_portfolio_value * target_weight
            current_value = current_positions.get(strategy_key, 0.0)

            trade_amount = target_value - current_value

            if abs(trade_amount) > 0.01:  # Minimum trade threshold
                rebalancing_trades[strategy_key] = {
                    "current_value": current_value,
                    "target_value": target_value,
                    "trade_amount": trade_amount,
                    "trade_type": "BUY" if trade_amount > 0 else "SELL",
                }

        return {
            "rebalancing_trades": rebalancing_trades,
            "total_trades": len(rebalancing_trades),
            "total_trade_value": sum(
                abs(trade["trade_amount"]) for trade in rebalancing_trades.values()
            ),
        }
