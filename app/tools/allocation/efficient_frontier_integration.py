"""
Efficient Frontier Integration for Position Sizing

This module integrates with @app/portfolio_review/efficient_frontier.py for automated
allocation calculations and price data fetching.
"""

from pathlib import Path
import sys
from typing import Any

from app.tools.data_types import DataConfig
from app.tools.get_data import get_data


class AllocationOptimizer:
    """Integrates with efficient frontier analysis for automated allocation calculations."""

    def __init__(self, base_dir: str | None = None):
        """Initialize allocation optimizer.

        Args:
            base_dir: Base directory path. If None, uses current working directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.efficient_frontier_path = (
            self.base_dir / "app" / "portfolio_review" / "efficient_frontier.py"
        )

    def _run_efficient_frontier_analysis(
        self,
        assets: list[str],
        half_rule: bool = True,
    ) -> dict[str, Any]:
        """Run efficient frontier analysis for given assets.

        Args:
            assets: List of asset symbols
            half_rule: Whether to apply the half rule constraint

        Returns:
            Dictionary containing analysis results
        """
        # Import the efficient frontier module dynamically
        efficient_frontier_dir = self.efficient_frontier_path.parent
        sys.path.insert(0, str(efficient_frontier_dir))

        try:
            # Temporarily modify the ASSETS list and run analysis
            import efficient_frontier

            # Store original values
            original_assets = efficient_frontier.ASSETS
            original_half_rule = efficient_frontier.HALF_RULE

            # Set our values
            efficient_frontier.ASSETS = assets
            efficient_frontier.HALF_RULE = half_rule

            # Re-run the analysis with our parameters
            import importlib

            importlib.reload(efficient_frontier)

            results = {
                "sharpe_weights": efficient_frontier.optimal_weights_sharpe,
                "sortino_weights": efficient_frontier.optimal_weights_sortino,
                "sharpe_return": efficient_frontier.optimal_return_sharpe,
                "sortino_return": efficient_frontier.optimal_return_sortino,
                "sharpe_volatility": efficient_frontier.optimal_std_sharpe,
                "sortino_volatility": efficient_frontier.optimal_std_sortino,
                "sharpe_ratio": efficient_frontier.optimal_sharpe,
                "sortino_ratio": efficient_frontier.optimal_sortino,
            }

            # Apply half rule if enabled
            if half_rule and hasattr(efficient_frontier, "sharpe_half_rule"):
                results["sharpe_half_rule"] = efficient_frontier.sharpe_half_rule
                results["sortino_half_rule"] = efficient_frontier.sortino_half_rule

            # Restore original values
            efficient_frontier.ASSETS = original_assets
            efficient_frontier.HALF_RULE = original_half_rule

            return results

        finally:
            # Remove from path
            sys.path.remove(str(efficient_frontier_dir))

    def calculate_max_allocation_percentage(
        self,
        assets: list[str],
        use_sortino: bool = True,
        apply_half_rule: bool = True,
    ) -> dict[str, float]:
        """Run efficient frontier analysis and return optimized allocation percentages.

        Args:
            assets: List of asset symbols to analyze
            use_sortino: Whether to use Sortino ratio (True) or Sharpe ratio (False)
            apply_half_rule: Whether to apply the half rule constraint

        Returns:
            Dictionary mapping asset symbols to allocation percentages
        """
        results = self._run_efficient_frontier_analysis(assets, apply_half_rule)

        if apply_half_rule:
            # Use half rule results if available
            if use_sortino and "sortino_half_rule" in results:
                return results["sortino_half_rule"]
            if not use_sortino and "sharpe_half_rule" in results:
                return results["sharpe_half_rule"]

        # Fall back to raw weights
        weights = (
            results["sortino_weights"] if use_sortino else results["sharpe_weights"]
        )

        # Convert to percentage allocation
        allocation = {}
        for i, asset in enumerate(assets):
            allocation[asset] = round(weights[i] * 100, 2)

        return allocation

    def get_prices(self, symbol: str, config: DataConfig | None = None) -> float:
        """Fetch current price using existing @app/tools/get_data.py infrastructure.

        Args:
            symbol: Asset symbol (e.g., 'AAPL', 'BTC-USD')
            config: Data configuration. If None, uses default config.

        Returns:
            Current/latest price for the asset
        """
        if config is None:
            config = {
                "BASE_DIR": str(self.base_dir),
                "REFRESH": False,  # Use cached data if available
                "USE_HOURLY": False,
                "PERIOD": "1d",  # Get minimal data for price
            }

        def log_func(message: str, level: str = "info"):
            """Simple logging function for get_data."""
            # Silent logging for price fetching

        try:
            data = get_data(symbol, config, log_func)

            # Handle synthetic ticker case
            if isinstance(data, tuple):
                data, _ = data

            # Get latest close price
            if len(data) > 0:
                return float(data["Close"].tail(1).item())
            msg = f"No price data available for {symbol}"
            raise ValueError(msg)

        except Exception as e:
            msg = f"Failed to fetch price for {symbol}: {e!s}"
            raise ValueError(msg)

    def get_multiple_prices(self, symbols: list[str]) -> dict[str, float]:
        """Fetch current prices for multiple symbols.

        Args:
            symbols: List of asset symbols

        Returns:
            Dictionary mapping symbols to current prices
        """
        prices = {}
        for symbol in symbols:
            try:
                prices[symbol] = self.get_prices(symbol)
            except Exception as e:
                print(f"Warning: Could not fetch price for {symbol}: {e}")
                prices[symbol] = 0.0

        return prices

    def calculate_position_values(
        self,
        allocations: dict[str, float],
        total_allocation_amount: float,
    ) -> dict[str, float]:
        """Calculate position values based on allocations and total amount.

        Args:
            allocations: Dictionary mapping symbols to allocation percentages
            total_allocation_amount: Total amount to allocate across positions

        Returns:
            Dictionary mapping symbols to position values in dollars
        """
        position_values = {}
        for symbol, percentage in allocations.items():
            position_values[symbol] = (percentage / 100.0) * total_allocation_amount

        return position_values

    def get_efficient_frontier_metrics(self, assets: list[str]) -> dict[str, Any]:
        """Get comprehensive efficient frontier analysis metrics.

        Args:
            assets: List of asset symbols to analyze

        Returns:
            Dictionary containing all efficient frontier metrics
        """
        results = self._run_efficient_frontier_analysis(assets)

        return {
            "sharpe_metrics": {
                "weights": results["sharpe_weights"],
                "return": results["sharpe_return"],
                "volatility": results["sharpe_volatility"],
                "ratio": results["sharpe_ratio"],
            },
            "sortino_metrics": {
                "weights": results["sortino_weights"],
                "return": results["sortino_return"],
                "volatility": results["sortino_volatility"],
                "ratio": results["sortino_ratio"],
            },
        }

    def validate_allocation_constraints(
        self,
        allocations: dict[str, float],
        tolerance: float = 0.01,
    ) -> tuple[bool, str]:
        """Validate that allocations sum to approximately 100% and meet constraints.

        Args:
            allocations: Dictionary mapping symbols to allocation percentages
            tolerance: Tolerance for sum validation (default 1%)

        Returns:
            Tuple of (is_valid, validation_message)
        """
        total = sum(allocations.values())

        if abs(total - 100.0) > tolerance:
            return False, f"Allocations sum to {total:.2f}%, expected ~100%"

        # Check for negative allocations
        negative_assets = [asset for asset, pct in allocations.items() if pct < 0]
        if negative_assets:
            return False, f"Negative allocations found for: {negative_assets}"

        # Check for zero allocations (might be intentional)
        zero_assets = [asset for asset, pct in allocations.items() if pct == 0]
        if zero_assets:
            return True, f"Warning: Zero allocations for: {zero_assets}"

        return True, "Allocations valid"
