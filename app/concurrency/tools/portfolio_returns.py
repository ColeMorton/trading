"""
Portfolio-level return calculation for accurate risk assessment.

This module calculates portfolio returns from combined strategy positions
rather than individual components, providing more accurate risk metrics
that account for actual portfolio behavior.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

import numpy as np
import polars as pl

from app.tools.error_decorators import handle_errors
from app.tools.exceptions import (
    DataAlignmentError,
    PortfolioVarianceError,
    RiskCalculationError,
)


logger = logging.getLogger(__name__)


class PortfolioReturnsCalculator:
    """
    Calculates portfolio-level returns by aggregating individual strategy
    returns using position weights and allocations.
    """

    def __init__(self, log: Callable[[str, str], None] | None = None):
        """
        Initialize the portfolio returns calculator.

        Args:
            log: Optional logging function with signature (message, level)
        """
        self.log = log or self._default_log

    def _default_log(self, message: str, level: str) -> None:
        """Default logging implementation."""
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)

    @handle_errors(PortfolioVarianceError)
    def calculate_portfolio_returns(
        self,
        aligned_returns: pl.DataFrame,
        allocations: list[float],
        position_arrays: list[np.ndarray] | None | None = None,
        strategy_names: list[str] | None | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """
        Calculate portfolio returns from aligned strategy returns and allocations.

        Args:
            aligned_returns: DataFrame with aligned return series (Date + strategy columns)
            allocations: List of allocation percentages for each strategy
            position_arrays: Optional position arrays for each strategy
            strategy_names: Optional list of strategy names

        Returns:
            Tuple of (portfolio_returns_array, diagnostics_dict)

        Raises:
            PortfolioVarianceError: If calculation fails
            DataAlignmentError: If inputs are misaligned
        """
        # Get return columns (exclude Date)
        return_columns = [col for col in aligned_returns.columns if col != "Date"]
        n_strategies = len(return_columns)

        # Validate allocations
        if len(allocations) != n_strategies:
            msg = f"Allocation count ({len(allocations)}) doesn't match strategies ({n_strategies})"
            raise DataAlignmentError(
                msg,
            )

        # Handle missing or zero allocations
        total_allocation = sum(allocations)
        if total_allocation == 0:
            self.log("No allocations provided, using equal weights", "warning")
            weights = np.ones(n_strategies) / n_strategies
        else:
            weights = np.array(allocations) / total_allocation

        self.log(f"Calculating portfolio returns for {n_strategies} strategies", "info")
        self.log(f"Portfolio weights: {weights}", "info")

        # Extract return matrix
        returns_matrix = aligned_returns.select(return_columns).to_numpy()

        # Calculate weighted portfolio returns
        portfolio_returns = self._calculate_weighted_returns(
            returns_matrix,
            weights,
            position_arrays,
        )

        # Calculate diagnostics
        diagnostics = self._calculate_diagnostics(
            portfolio_returns,
            returns_matrix,
            weights,
            return_columns,
        )

        self.log("Portfolio return calculation completed", "info")

        return portfolio_returns, diagnostics

    def _calculate_weighted_returns(
        self,
        returns_matrix: np.ndarray,
        weights: np.ndarray,
        position_arrays: list[np.ndarray] | None | None = None,
    ) -> np.ndarray:
        """
        Calculate weighted portfolio returns accounting for positions.

        Args:
            returns_matrix: Matrix of returns (n_periods x n_strategies)
            weights: Portfolio weights for each strategy
            position_arrays: Optional position arrays

        Returns:
            Array of portfolio returns
        """
        n_periods, n_strategies = returns_matrix.shape

        if position_arrays is None:
            # Simple case: assume always in position
            portfolio_returns = returns_matrix @ weights
        else:
            # Account for actual positions
            portfolio_returns = np.zeros(n_periods)

            for t in range(n_periods):
                # Calculate active weights for this period
                active_weights = np.zeros(n_strategies)
                total_active_weight = 0.0

                for i in range(n_strategies):
                    if i < len(position_arrays) and t < len(position_arrays[i]):
                        if position_arrays[i][t] != 0:  # Strategy is active
                            active_weights[i] = weights[i]
                            total_active_weight += weights[i]

                # Normalize active weights to sum to 1
                if total_active_weight > 0:
                    active_weights = active_weights / total_active_weight
                    # Calculate portfolio return for this period
                    portfolio_returns[t] = returns_matrix[t] @ active_weights
                else:
                    # No strategies active - zero return
                    portfolio_returns[t] = 0.0

        return portfolio_returns

    def _calculate_diagnostics(
        self,
        portfolio_returns: np.ndarray,
        returns_matrix: np.ndarray,
        weights: np.ndarray,
        strategy_names: list[str],
    ) -> dict[str, Any]:
        """Calculate portfolio diagnostics and statistics."""
        # Basic statistics
        portfolio_mean = np.mean(portfolio_returns)
        portfolio_std = np.std(portfolio_returns)
        portfolio_variance = portfolio_std**2

        # Individual strategy statistics
        strategy_means = np.mean(returns_matrix, axis=0)
        strategy_stds = np.std(returns_matrix, axis=0)

        # Diversification ratio
        weighted_avg_std = np.sum(weights * strategy_stds)
        diversification_ratio = (
            weighted_avg_std / portfolio_std if portfolio_std > 0 else 1.0
        )

        # Return distribution
        sorted_returns = np.sort(portfolio_returns)

        diagnostics = {
            "portfolio_statistics": {
                "mean_return": float(portfolio_mean),
                "volatility": float(portfolio_std),
                "variance": float(portfolio_variance),
                "annualized_return": float(portfolio_mean * 252),
                "annualized_volatility": float(portfolio_std * np.sqrt(252)),
                "sharpe_ratio": (
                    float(portfolio_mean / portfolio_std * np.sqrt(252))
                    if portfolio_std > 0
                    else 0.0
                ),
            },
            "diversification": {
                "diversification_ratio": float(diversification_ratio),
                "effective_n": float(
                    1 / np.sum(weights**2),
                ),  # Effective number of strategies
                "concentration": float(np.max(weights)),  # Highest single weight
            },
            "return_distribution": {
                "skewness": float(self._calculate_skewness(portfolio_returns)),
                "kurtosis": float(self._calculate_kurtosis(portfolio_returns)),
                "min_return": float(np.min(portfolio_returns)),
                "max_return": float(np.max(portfolio_returns)),
                "percentile_5": float(np.percentile(sorted_returns, 5)),
                "percentile_95": float(np.percentile(sorted_returns, 95)),
            },
            "strategy_contributions": {
                name: {
                    "weight": float(weights[i]),
                    "mean_return": float(strategy_means[i]),
                    "volatility": float(strategy_stds[i]),
                    "return_contribution": float(weights[i] * strategy_means[i]),
                }
                for i, name in enumerate(strategy_names)
            },
        }

        # Log summary
        self.log(
            f"Portfolio volatility: {portfolio_std:.6f} ({portfolio_std*np.sqrt(252)*100:.2f}% annualized)",
            "info",
        )
        self.log(f"Diversification ratio: {diversification_ratio:.4f}", "info")
        self.log(
            f"Effective number of strategies: {diagnostics['diversification']['effective_n']:.2f}",
            "info",
        )

        return diagnostics

    def _calculate_skewness(self, returns: np.ndarray) -> float:
        """Calculate skewness of return distribution."""
        if len(returns) < 3:
            return 0.0

        mean = np.mean(returns)
        std = np.std(returns)

        if std == 0:
            return 0.0

        n = len(returns)
        return n / ((n - 1) * (n - 2)) * np.sum(((returns - mean) / std) ** 3)

    def _calculate_kurtosis(self, returns: np.ndarray) -> float:
        """Calculate excess kurtosis of return distribution."""
        if len(returns) < 4:
            return 0.0

        mean = np.mean(returns)
        std = np.std(returns)

        if std == 0:
            return 0.0

        len(returns)
        m4 = np.mean((returns - mean) ** 4)
        return m4 / (std**4) - 3

    def calculate_rolling_metrics(
        self,
        portfolio_returns: np.ndarray,
        window: int = 252,
        min_periods: int | None | None = None,
    ) -> pl.DataFrame:
        """
        Calculate rolling portfolio metrics for stability analysis.

        Args:
            portfolio_returns: Array of portfolio returns
            window: Rolling window size (default 252 for 1 year)
            min_periods: Minimum periods for calculation (default window/2)

        Returns:
            DataFrame with rolling metrics
        """
        if min_periods is None:
            min_periods = window // 2

        n_periods = len(portfolio_returns)
        dates = [datetime(2020, 1, 1).date()] * n_periods  # Placeholder dates

        # Create DataFrame for rolling calculations
        df = pl.DataFrame({"date": dates, "returns": portfolio_returns})

        # Calculate rolling metrics
        rolling_df = df.with_columns(
            [
                # Rolling mean
                pl.col("returns")
                .rolling_mean(window, min_periods=min_periods)
                .alias("rolling_mean"),
                # Rolling std
                pl.col("returns")
                .rolling_std(window, min_periods=min_periods)
                .alias("rolling_std"),
                # Rolling Sharpe (annualized)
                (
                    pl.col("returns").rolling_mean(window, min_periods=min_periods)
                    / pl.col("returns").rolling_std(window, min_periods=min_periods)
                    * np.sqrt(252)
                ).alias("rolling_sharpe"),
            ],
        )

        # Calculate rolling VaR and CVaR using a custom function
        var_95_values = []
        cvar_95_values = []

        for i in range(n_periods):
            start = max(0, i - window + 1)
            end = i + 1

            if end - start >= min_periods:
                window_returns = portfolio_returns[start:end]
                sorted_returns = np.sort(window_returns)
                var_95 = np.percentile(sorted_returns, 5)
                cvar_95 = np.mean(sorted_returns[sorted_returns <= var_95])
            else:
                var_95 = np.nan
                cvar_95 = np.nan

            var_95_values.append(var_95)
            cvar_95_values.append(cvar_95)

        # Add VaR and CVaR to DataFrame
        rolling_df = rolling_df.with_columns(
            [
                pl.Series("rolling_var_95", var_95_values),
                pl.Series("rolling_cvar_95", cvar_95_values),
            ],
        )

        self.log(f"Calculated rolling metrics with window {window}", "info")

        return rolling_df

    def calculate_portfolio_metrics_from_positions(
        self,
        data_list: list[pl.DataFrame],
        position_arrays: list[np.ndarray],
        allocations: list[float],
        strategy_names: list[str],
    ) -> dict[str, Any]:
        """
        Calculate complete portfolio metrics from position data.

        This is the main integration point with the existing risk framework.

        Args:
            data_list: List of DataFrames with price data for each strategy
            position_arrays: Position arrays for each strategy
            allocations: Allocation percentages for each strategy
            strategy_names: Names of strategies

        Returns:
            Dictionary with portfolio metrics including returns and risk metrics

        Raises:
            RiskCalculationError: If calculation fails
        """
        try:
            # First align the return series
            from .return_alignment import align_portfolio_returns

            # Prepare portfolios for alignment
            portfolios = []
            for i, (df, positions, name) in enumerate(
                zip(data_list, position_arrays, strategy_names, strict=False),
            ):
                # Add position data
                df_with_position = df.with_columns(
                    [pl.Series("Position", positions[: len(df)])],
                )

                # Parse strategy info from name
                parts = name.split("_")
                ticker = parts[0] if len(parts) > 0 else f"STRATEGY{i+1}"
                strategy_type = parts[1] if len(parts) > 1 else "unknown"
                period = parts[2] if len(parts) > 2 else "D"

                portfolios.append(
                    {
                        "ticker": ticker,
                        "strategy_type": strategy_type,
                        "period": period,
                        "data": df_with_position,
                    },
                )

            # Align returns
            aligned_returns, aligned_names = align_portfolio_returns(
                portfolios,
                self.log,
                min_observations=10,
            )

            # Calculate portfolio returns
            portfolio_returns, diagnostics = self.calculate_portfolio_returns(
                aligned_returns,
                allocations,
                position_arrays,
                aligned_names,
            )

            # Calculate portfolio variance and risk
            portfolio_variance = np.var(portfolio_returns)
            portfolio_std = np.sqrt(portfolio_variance)

            # Calculate VaR and CVaR
            sorted_returns = np.sort(portfolio_returns)
            var_95 = float(np.percentile(sorted_returns, 5))
            var_99 = float(np.percentile(sorted_returns, 1))
            cvar_95 = float(np.mean(sorted_returns[sorted_returns <= var_95]))
            cvar_99 = float(np.mean(sorted_returns[sorted_returns <= var_99]))

            # Combine all metrics
            metrics = {
                "portfolio_returns": portfolio_returns,
                "portfolio_volatility": float(portfolio_std),
                "portfolio_variance": float(portfolio_variance),
                "var_95": var_95,
                "cvar_95": cvar_95,
                "var_99": var_99,
                "cvar_99": cvar_99,
                "diagnostics": diagnostics,
                "n_observations": len(portfolio_returns),
            }

            self.log("Portfolio metrics calculated successfully", "info")
            self.log(f"  Portfolio volatility: {portfolio_std:.6f}", "info")
            self.log(f"  VaR 95%: {var_95:.4f}, CVaR 95%: {cvar_95:.4f}", "info")

            return metrics

        except Exception as e:
            msg = f"Failed to calculate portfolio metrics: {e!s}"
            raise RiskCalculationError(msg)
