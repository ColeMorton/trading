"""
Core Monte Carlo Parameter Robustness Analysis Engine.

Provides the main MonteCarloAnalyzer class for portfolio-level parameter
robustness testing using bootstrap sampling and parameter noise injection.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Any

import numpy as np
import polars as pl


# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.concurrency.tools.monte_carlo.bootstrap import (
    BootstrapSampler,
    create_bootstrap_sampler,
)
from app.concurrency.tools.monte_carlo.config import MonteCarloConfig
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals


@dataclass
class ParameterStabilityResult:
    """Results of parameter stability analysis for a single parameter combination."""

    parameter_combination: tuple[int, int]  # (fast_period, slow_period)
    base_performance: dict[str, float]  # Performance on original data
    monte_carlo_results: list[dict[str, Any]]  # Results from all simulations

    # Statistical measures
    performance_mean: dict[str, float] = field(default_factory=dict)
    performance_std: dict[str, float] = field(default_factory=dict)
    confidence_intervals: dict[str, tuple[float, float]] = field(default_factory=dict)

    # Stability metrics
    stability_score: float = 0.0
    parameter_robustness: float = 0.0
    regime_consistency: float = 0.0

    @property
    def is_stable(self) -> bool:
        """Check if parameter combination is considered stable."""
        return (
            self.stability_score > 0.5  # Reduced from 0.7 for more realistic thresholds
            and self.parameter_robustness > 0.4  # Reduced from 0.6
            and self.regime_consistency > 0.4  # Reduced from 0.5
        )


@dataclass
class MonteCarloPortfolioResult:
    """Results of Monte Carlo analysis for an entire portfolio."""

    ticker: str
    parameter_results: list[ParameterStabilityResult]
    portfolio_stability_score: float = 0.0
    recommended_parameters: tuple[int, int] | None = None
    analysis_metadata: dict[str, Any] = field(default_factory=dict)


class MonteCarloAnalyzer:
    """Portfolio-level Monte Carlo parameter robustness analyzer.

    This class provides comprehensive analysis of parameter stability using
    bootstrap sampling and Monte Carlo simulation methods, designed to work
    with the concurrency framework for multi-ticker portfolio analysis.
    """

    def __init__(
        self, config: MonteCarloConfig, log: Callable[[str, str], None] | None = None,
    ):
        """Initialize the Monte Carlo analyzer.

        Args:
            config: Monte Carlo configuration
            log: Optional logging function following concurrency patterns
        """
        self.config = config
        self.log = log or self._default_log
        self.bootstrap_sampler = self._create_bootstrap_sampler()
        self.results: list[MonteCarloPortfolioResult] = []

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging function."""
        print(f"[{level.upper()}] {message}")

    def _create_bootstrap_sampler(self) -> BootstrapSampler:
        """Create bootstrap sampler from configuration."""
        config_dict = self.config.to_dict()
        # Add bootstrap-specific defaults if not present
        config_dict.setdefault("MC_BOOTSTRAP_BLOCK_SIZE", 63)  # ~3 months
        config_dict.setdefault("MC_MIN_DATA_FRACTION", 0.7)

        return create_bootstrap_sampler(config_dict)

    def analyze_parameter_stability(
        self,
        ticker: str,
        data: pl.DataFrame,
        parameter_combinations: list[tuple[int, int]],
        strategy_type: str = "EMA",
        strategy_config: dict[str, Any] | None = None,
    ) -> MonteCarloPortfolioResult:
        """Analyze parameter stability for a single ticker.

        Args:
            ticker: Ticker symbol
            data: Price data DataFrame with Date, Open, High, Low, Close columns
            parameter_combinations: List of (fast_period, slow_period) tuples to test
            strategy_type: Strategy type (EMA, SMA, MACD, etc.)
            strategy_config: Strategy configuration dictionary (required for MACD strategies)

        Returns:
            MonteCarloPortfolioResult with stability analysis
        """
        self.log(f"Starting Monte Carlo analysis for {ticker}", "info")

        # Limit parameter combinations if configured
        if len(parameter_combinations) > self.config.max_parameters_to_test:
            parameter_combinations = parameter_combinations[
                : self.config.max_parameters_to_test
            ]
            self.log(
                f"Limited analysis to {self.config.max_parameters_to_test} parameters",
                "info",
            )

        parameter_results = []

        for fast_period, slow_period in parameter_combinations:
            self.log(f"Analyzing parameters: {fast_period}/{slow_period}", "debug")

            stability_result = self._analyze_single_parameter_combination(
                data, fast_period, slow_period, strategy_type, strategy_config,
            )
            parameter_results.append(stability_result)

        # Calculate portfolio-level metrics
        portfolio_result = MonteCarloPortfolioResult(
            ticker=ticker,
            parameter_results=parameter_results,
            portfolio_stability_score=self._calculate_portfolio_stability_score(
                parameter_results,
            ),
            recommended_parameters=self._select_most_stable_parameters(
                parameter_results,
            ),
            analysis_metadata={
                "num_simulations": self.config.num_simulations,
                "confidence_level": self.config.confidence_level,
                "parameters_tested": len(parameter_combinations),
            },
        )

        self.results.append(portfolio_result)
        self.log(f"Completed Monte Carlo analysis for {ticker}", "info")

        return portfolio_result

    def _analyze_single_parameter_combination(
        self,
        data: pl.DataFrame,
        fast_period: int,
        slow_period: int,
        strategy_type: str = "EMA",
        strategy_config: dict[str, Any] | None = None,
    ) -> ParameterStabilityResult:
        """Analyze stability of a single parameter combination."""

        # Calculate base performance on original data
        base_performance = self._calculate_strategy_performance(
            data, fast_period, slow_period, strategy_type, strategy_config,
        )

        # Run Monte Carlo simulations
        monte_carlo_results = []

        for simulation in range(self.config.num_simulations):
            # Create bootstrap sample
            bootstrap_data = self.bootstrap_sampler.block_bootstrap_sample(
                data, seed=simulation,
            )

            # Add parameter noise
            noisy_short, noisy_long = self.bootstrap_sampler.parameter_noise_injection(
                fast_period, slow_period, noise_std=0.1,
            )

            # Calculate performance on bootstrap sample with noisy parameters
            sim_performance = self._calculate_strategy_performance(
                bootstrap_data, noisy_short, noisy_long, strategy_type, strategy_config,
            )

            monte_carlo_results.append(
                {
                    "simulation_id": simulation,
                    "parameters": (noisy_short, noisy_long),
                    "performance": sim_performance,
                },
            )

        # Calculate stability metrics
        stability_result = ParameterStabilityResult(
            parameter_combination=(fast_period, slow_period),
            base_performance=base_performance,
            monte_carlo_results=monte_carlo_results,
        )

        self._calculate_stability_metrics(stability_result)

        return stability_result

    def _standardize_field_names(
        self, strategy_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Standardize field names from CSV format to internal format."""
        field_mapping = {
            # CSV header -> Internal field name
            "Signal Period": "SIGNAL_PERIOD",
            "Fast Period": "FAST_PERIOD",
            "Slow Period": "SLOW_PERIOD",
            "Strategy Type": "STRATEGY_TYPE",
            "Ticker": "TICKER",
            "Stop Loss [%]": "STOP_LOSS",
            "Signal Entry": "SIGNAL_ENTRY",
            "Signal Exit": "SIGNAL_EXIT",
        }

        standardized = {}
        for key, value in strategy_config.items():
            # Map CSV field name to internal name if mapping exists
            internal_key = field_mapping.get(key, key)
            standardized[internal_key] = value

            # Also keep original key for backward compatibility
            if key != internal_key:
                standardized[key] = value

        return standardized

    def _calculate_strategy_performance(
        self,
        data: pl.DataFrame,
        fast_period: int,
        slow_period: int,
        strategy_type: str = "EMA",
        strategy_config: dict[str, Any] | None = None,
    ) -> dict[str, float]:
        """Calculate strategy performance for given parameters."""
        try:
            # Calculate MA signals - merge provided strategy config with defaults
            config = {"BASE_DIR": "."}  # Basic config for signal calculation
            if strategy_config:
                # Standardize field names for strategy config
                standardized_config = self._standardize_field_names(strategy_config)
                config.update(standardized_config)

            # Ensure STRATEGY_TYPE is set correctly in config (takes precedence in calculate_ma_and_signals)
            config["STRATEGY_TYPE"] = strategy_type
            signals_data = calculate_ma_and_signals(
                data,
                fast_period,
                slow_period,
                config,
                self.log,
                strategy_type=strategy_type,
            )

            if signals_data is None or len(signals_data) == 0:
                return {"total_return": 0.0, "sharpe_ratio": 0.0, "max_drawdown": 1.0}

            # Calculate returns from position and price data
            positions = signals_data.get_column("Position").to_numpy()
            close_prices = signals_data.get_column("Close").to_numpy()

            if len(positions) == 0 or len(close_prices) == 0:
                return {"total_return": 0.0, "sharpe_ratio": 0.0, "max_drawdown": 1.0}

            # Calculate price returns
            price_returns = np.diff(close_prices) / close_prices[:-1]

            # Apply position-based returns (position from previous day affects current return)
            if len(positions) > 1:
                strategy_returns = positions[:-1] * price_returns
            else:
                strategy_returns = np.array([0.0])

            if len(strategy_returns) == 0 or np.all(strategy_returns == 0):
                return {"total_return": 0.0, "sharpe_ratio": 0.0, "max_drawdown": 1.0}

            # Calculate basic metrics
            total_return = np.prod(1 + strategy_returns) - 1

            # Sharpe ratio (annualized, assuming daily data)
            mean_return = np.mean(strategy_returns) * 252
            return_std = np.std(strategy_returns) * np.sqrt(252)
            sharpe_ratio = mean_return / return_std if return_std > 0 else 0.0

            # Maximum drawdown
            cumulative = np.cumprod(1 + strategy_returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdowns = (cumulative - running_max) / running_max
            max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0

            return {
                "total_return": total_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
            }

        except Exception as e:
            self.log(f"Error calculating performance: {e!s}", "warning")
            return {"total_return": 0.0, "sharpe_ratio": 0.0, "max_drawdown": 1.0}

    def _calculate_stability_metrics(self, result: ParameterStabilityResult) -> None:
        """Calculate stability metrics for parameter combination."""

        # Extract performance values from Monte Carlo results
        returns = [
            sim["performance"]["total_return"] for sim in result.monte_carlo_results
        ]
        sharpe_ratios = [
            sim["performance"]["sharpe_ratio"] for sim in result.monte_carlo_results
        ]

        if not returns or not sharpe_ratios:
            result.stability_score = 0.0
            result.parameter_robustness = 0.0
            result.regime_consistency = 0.0
            return

        # Calculate statistical measures
        result.performance_mean = {
            "total_return": np.mean(returns),
            "sharpe_ratio": np.mean(sharpe_ratios),
        }

        result.performance_std = {
            "total_return": np.std(returns),
            "sharpe_ratio": np.std(sharpe_ratios),
        }

        # Calculate confidence intervals
        alpha = 1 - self.config.confidence_level
        result.confidence_intervals = {
            "total_return": self._calculate_confidence_interval(returns, alpha),
            "sharpe_ratio": self._calculate_confidence_interval(sharpe_ratios, alpha),
        }

        # Stability score: consistency of performance across simulations
        result.base_performance.get("total_return", 0.0)

        # Stability score: consistency of performance across simulations
        # Use coefficient of variation as a more reliable stability measure
        if len(returns) > 1 and result.performance_mean["total_return"] != 0:
            # Calculate consistency as inverse of coefficient of variation
            cv = result.performance_std["total_return"] / abs(
                result.performance_mean["total_return"],
            )
            return_correlation = max(
                0.0, 1.0 - min(cv, 2.0) / 2.0,
            )  # Scale CV to 0-1 range
        else:
            return_correlation = 0.0

        # Parameter robustness: low variance in performance
        return_cv = (
            result.performance_std["total_return"]
            / abs(result.performance_mean["total_return"])
            if result.performance_mean["total_return"] != 0
            else float("inf")
        )
        robustness = 1.0 / (1.0 + return_cv) if return_cv < float("inf") else 0.0

        # Regime consistency: percentage of simulations with positive performance
        positive_returns = sum(1 for r in returns if r > 0) / len(returns)

        result.stability_score = return_correlation
        result.parameter_robustness = robustness
        result.regime_consistency = positive_returns

    def _calculate_confidence_interval(
        self, values: list[float], alpha: float,
    ) -> tuple[float, float]:
        """Calculate confidence interval for a list of values."""
        if not values:
            return (0.0, 0.0)

        sorted_values = sorted(values)
        n = len(sorted_values)

        lower_idx = int(alpha / 2 * n)
        upper_idx = int((1 - alpha / 2) * n)

        lower_bound = sorted_values[min(lower_idx, n - 1)]
        upper_bound = sorted_values[min(upper_idx, n - 1)]

        return (lower_bound, upper_bound)

    def _calculate_portfolio_stability_score(
        self, parameter_results: list[ParameterStabilityResult],
    ) -> float:
        """Calculate overall portfolio stability score."""
        if not parameter_results:
            return 0.0

        stability_scores = [result.stability_score for result in parameter_results]
        return np.mean(stability_scores)

    def _select_most_stable_parameters(
        self, parameter_results: list[ParameterStabilityResult],
    ) -> tuple[int, int] | None:
        """Select the most stable parameter combination."""
        if not parameter_results:
            return None

        # Score based on stability, robustness, and consistency
        best_result = max(
            parameter_results,
            key=lambda r: (
                r.stability_score * 0.4
                + r.parameter_robustness * 0.4
                + r.regime_consistency * 0.2
            ),
        )

        return best_result.parameter_combination
