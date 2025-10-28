"""
Monte Carlo Parameter Robustness Testing for MA Cross Strategies

This module implements comprehensive parameter stability analysis using Monte Carlo
methods to evaluate the robustness of MA crossover strategy parameters across
different market conditions and data variations.

Key Features:
- Bootstrap sampling of price data for robust parameter testing
- Confidence interval calculation for performance metrics
- Parameter stability analysis across market regimes
- Integration with existing MA Cross parameter testing framework
"""

from collections.abc import Callable
from dataclasses import dataclass, field
import os
import random
from typing import Any

import numpy as np
import polars as pl

from app.tools.get_data import download_data
from app.tools.setup_logging import setup_logging
from app.tools.strategy.sensitivity_analysis import analyze_window_combination


@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo parameter robustness testing."""

    # Core Monte Carlo parameters
    num_simulations: int = 1000
    bootstrap_block_size: int = 252  # 1 year of daily data
    confidence_level: float = 0.95

    # Parameter testing ranges
    parameter_noise_std: float = 0.1  # Standard deviation for parameter perturbation
    min_data_fraction: float = 0.7  # Minimum fraction of data to use in bootstrap

    # Market regime analysis
    enable_regime_analysis: bool = True
    regime_window: int = 63  # ~3 months for regime detection

    # Performance thresholds for stability
    min_performance_correlation: float = (
        0.7  # Correlation threshold for stable parameters
    )
    max_performance_variance: float = 0.25  # Maximum acceptable variance in returns

    # Output options
    export_distributions: bool = True
    create_visualizations: bool = True
    save_bootstrap_samples: bool = False


@dataclass
class ParameterStabilityResult:
    """Results of parameter stability analysis."""

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
            self.stability_score > 0.7
            and self.parameter_robustness > 0.6
            and self.regime_consistency > 0.5
        )


class ParameterRobustnessAnalyzer:
    """
    Monte Carlo parameter robustness analyzer for MA Cross strategies.

    This class provides comprehensive analysis of parameter stability using
    bootstrap sampling and Monte Carlo simulation methods.
    """

    def __init__(self, mc_config: MonteCarloConfig, log: Callable | None = None):
        """
        Initialize the parameter robustness analyzer.

        Args:
            mc_config: Monte Carlo configuration
            log: Optional logging function
        """
        self.mc_config = mc_config
        self.log = log or print
        self.results: list[ParameterStabilityResult] = []

    def bootstrap_prices(
        self,
        data: pl.DataFrame,
        seed: int | None = None,
    ) -> pl.DataFrame:
        """
        Create bootstrap sample of price data using block bootstrap method.

        Args:
            data: Original price data DataFrame
            seed: Random seed for reproducibility

        Returns:
            Bootstrap sample of price data
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        n_periods = len(data)
        block_size = self.mc_config.bootstrap_block_size
        min_periods = int(n_periods * self.mc_config.min_data_fraction)

        # Ensure we have enough data
        if n_periods < block_size:
            # For short series, use simple random sampling with replacement
            sample_size = max(min_periods, int(n_periods * 0.8))
            indices = np.random.choice(n_periods, size=sample_size, replace=True)
            return data[sorted(indices)]

        # Block bootstrap for time series data
        n_blocks = max(1, min_periods // block_size)
        sampled_data = []

        for _ in range(n_blocks):
            # Random starting point for block
            start_idx = np.random.randint(0, max(1, n_periods - block_size))
            end_idx = min(start_idx + block_size, n_periods)
            block = data[start_idx:end_idx]
            sampled_data.append(block)

        # Combine blocks
        bootstrap_sample = pl.concat(sampled_data)

        # Add some additional random sampling if needed
        current_size = len(bootstrap_sample)
        if current_size < min_periods:
            additional_needed = min_periods - current_size
            additional_indices = np.random.choice(
                n_periods,
                size=additional_needed,
                replace=True,
            )
            additional_data = data[sorted(additional_indices)]
            bootstrap_sample = pl.concat([bootstrap_sample, additional_data])

        return bootstrap_sample.sort("Date")

    def add_parameter_noise(self, short: int, long: int) -> tuple[int, int]:
        """
        Add small random variations to parameters for robustness testing.

        Args:
            short: Fast period parameter
            long: Slow period parameter

        Returns:
            Perturbed parameter values
        """
        noise_std = self.mc_config.parameter_noise_std

        # Add Gaussian noise and ensure integer values
        short_noisy = max(2, int(short + np.random.normal(0, short * noise_std)))
        long_noisy = max(
            short_noisy + 1,
            int(long + np.random.normal(0, long * noise_std)),
        )

        return short_noisy, long_noisy

    def detect_market_regimes(self, data: pl.DataFrame) -> pl.DataFrame:
        """
        Detect market regimes using rolling volatility and returns.

        Args:
            data: Price data DataFrame

        Returns:
            DataFrame with regime classifications
        """
        window = self.mc_config.regime_window

        # Calculate rolling metrics
        data = data.with_columns(
            [
                (pl.col("Close") / pl.col("Close").shift(1) - 1).alias("Returns"),
            ],
        )

        data = data.with_columns(
            [
                pl.col("Returns").rolling_mean(window).alias("Rolling_Return"),
                pl.col("Returns").rolling_std(window).alias("Rolling_Volatility"),
            ],
        )

        # Simple regime classification based on volatility percentiles
        vol_75 = data["Rolling_Volatility"].quantile(0.75)
        vol_25 = data["Rolling_Volatility"].quantile(0.25)

        ret_75 = data["Rolling_Return"].quantile(0.75)
        ret_25 = data["Rolling_Return"].quantile(0.25)

        # Classify regimes
        regime_conditions = [
            (pl.col("Rolling_Volatility") > vol_75, "High_Vol"),
            (pl.col("Rolling_Volatility") < vol_25, "Low_Vol"),
            (pl.col("Rolling_Return") > ret_75, "Bull"),
            (pl.col("Rolling_Return") < ret_25, "Bear"),
        ]

        regime_expr = pl.when(regime_conditions[0][0]).then(
            pl.lit(regime_conditions[0][1]),
        )
        for condition, label in regime_conditions[1:]:
            regime_expr = regime_expr.when(condition).then(pl.lit(label))
        regime_expr = regime_expr.otherwise(pl.lit("Normal"))

        return data.with_columns(regime_expr.alias("Market_Regime"))

    def calculate_performance_stability(
        self,
        results: list[dict[str, Any]],
    ) -> dict[str, float]:
        """
        Calculate stability metrics from Monte Carlo results.

        Args:
            results: List of performance results from simulations

        Returns:
            Dictionary of stability metrics
        """
        if not results:
            return {"stability_score": 0.0, "robustness": 0.0}

        # Key performance metrics to analyze
        key_metrics = [
            "Sharpe Ratio",
            "Total Return [%]",
            "Max Drawdown [%]",
            "Win Rate [%]",
        ]

        stability_scores = []

        for metric in key_metrics:
            values = [r.get(metric, 0) for r in results if r.get(metric) is not None]
            if len(values) < 2:
                continue

            # Calculate coefficient of variation (inverse stability)
            cv = np.std(values) / (abs(np.mean(values)) + 1e-8)
            stability = max(0, 1 - cv)  # Higher stability = lower variation
            stability_scores.append(stability)

        overall_stability = np.mean(stability_scores) if stability_scores else 0.0

        # Calculate robustness (percentage of successful simulations)
        successful_sims = sum(1 for r in results if r.get("Total Return [%]", 0) > 0)
        robustness = successful_sims / len(results) if results else 0.0

        return {
            "stability_score": overall_stability,
            "robustness": robustness,
            "successful_simulations": successful_sims,
            "total_simulations": len(results),
        }

    def analyze_parameter_robustness(
        self,
        ticker: str,
        fast_period: int,
        slow_period: int,
        config: dict[str, Any],
    ) -> ParameterStabilityResult:
        """
        Perform Monte Carlo robustness analysis for a specific parameter combination.

        Args:
            ticker: Ticker symbol
            fast_period: Short MA window
            slow_period: Long MA window
            config: Strategy configuration

        Returns:
            Parameter stability analysis results
        """
        self.log(
            f"Analyzing parameter robustness for {ticker}: {fast_period}/{slow_period}",
        )

        # Download original data
        original_data = download_data(ticker, config, self.log)
        if original_data is None or len(original_data) == 0:
            self.log(f"No data available for {ticker}", "error")
            return ParameterStabilityResult((fast_period, slow_period), {}, [])

        # Add market regime detection if enabled
        if self.mc_config.enable_regime_analysis:
            original_data = self.detect_market_regimes(original_data)

        # Calculate base performance on original data
        base_result = analyze_window_combination(
            original_data,
            fast_period,
            slow_period,
            config,
            self.log,
        )

        if base_result is None:
            self.log(
                f"Base analysis failed for {ticker}: {fast_period}/{slow_period}",
                "error",
            )
            return ParameterStabilityResult((fast_period, slow_period), {}, [])

        # Monte Carlo simulations
        monte_carlo_results = []
        successful_simulations = 0

        for simulation in range(self.mc_config.num_simulations):
            try:
                # Create bootstrap sample
                bootstrap_data = self.bootstrap_prices(original_data, seed=simulation)

                # Add parameter noise
                noisy_short, noisy_long = self.add_parameter_noise(
                    fast_period,
                    slow_period,
                )

                # Analyze with noisy parameters on bootstrap data
                result = analyze_window_combination(
                    bootstrap_data,
                    noisy_short,
                    noisy_long,
                    config,
                    self.log,
                )

                if result is not None:
                    result["simulation_id"] = simulation
                    result["bootstrap_periods"] = len(bootstrap_data)
                    result["parameter_noise_short"] = noisy_short - fast_period
                    result["parameter_noise_long"] = noisy_long - slow_period

                    if self.mc_config.enable_regime_analysis:
                        # Analyze regime-specific performance
                        regime_data = self.detect_market_regimes(bootstrap_data)
                        regime_counts = regime_data["Market_Regime"].value_counts()
                        result["regime_distribution"] = regime_counts.to_dict()

                    monte_carlo_results.append(result)
                    successful_simulations += 1

            except Exception as e:
                self.log(f"Simulation {simulation} failed: {e!s}", "warning")
                continue

            # Progress logging
            if (simulation + 1) % 100 == 0:
                self.log(
                    f"Completed {simulation + 1}/{self.mc_config.num_simulations} simulations",
                )

        self.log(
            f"Monte Carlo analysis complete: {successful_simulations}/{self.mc_config.num_simulations} successful",
        )

        # Calculate stability metrics
        stability_metrics = self.calculate_performance_stability(monte_carlo_results)

        # Calculate statistical measures
        performance_stats = self._calculate_statistical_measures(monte_carlo_results)

        # Create result object
        result = ParameterStabilityResult(
            parameter_combination=(fast_period, slow_period),
            base_performance=base_result,
            monte_carlo_results=monte_carlo_results,
            **performance_stats,
        )

        result.stability_score = stability_metrics["stability_score"]
        result.parameter_robustness = stability_metrics["robustness"]

        # Calculate regime consistency if enabled
        if self.mc_config.enable_regime_analysis:
            result.regime_consistency = self._calculate_regime_consistency(
                monte_carlo_results,
            )

        return result

    def _calculate_statistical_measures(
        self,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate statistical measures for Monte Carlo results."""
        if not results:
            return {
                "performance_mean": {},
                "performance_std": {},
                "confidence_intervals": {},
            }

        key_metrics = [
            "Sharpe Ratio",
            "Total Return [%]",
            "Max Drawdown [%]",
            "Win Rate [%]",
            "Profit Factor",
        ]

        performance_mean = {}
        performance_std = {}
        confidence_intervals = {}

        alpha = 1 - self.mc_config.confidence_level

        for metric in key_metrics:
            values = [r.get(metric, 0) for r in results if r.get(metric) is not None]
            if not values:
                continue

            values = np.array(values)
            performance_mean[metric] = np.mean(values)
            performance_std[metric] = np.std(values)

            # Calculate confidence intervals
            ci_lower = np.percentile(values, (alpha / 2) * 100)
            ci_upper = np.percentile(values, (1 - alpha / 2) * 100)
            confidence_intervals[metric] = (ci_lower, ci_upper)

        return {
            "performance_mean": performance_mean,
            "performance_std": performance_std,
            "confidence_intervals": confidence_intervals,
        }

    def _calculate_regime_consistency(self, results: list[dict[str, Any]]) -> float:
        """Calculate consistency across different market regimes."""
        if not results:
            return 0.0

        # This is a simplified version - could be expanded with more sophisticated regime analysis
        regime_performances = {}

        for result in results:
            regime_dist = result.get("regime_distribution", {})
            performance = result.get("Total Return [%]", 0)

            # Weight performance by regime presence
            for regime in regime_dist:
                if regime not in regime_performances:
                    regime_performances[regime] = []
                regime_performances[regime].append(performance)

        # Calculate consistency as inverse of performance variance across regimes
        if len(regime_performances) < 2:
            return 0.5  # Neutral score if insufficient regime data

        regime_means = [np.mean(perfs) for perfs in regime_performances.values()]
        consistency = 1.0 / (1.0 + np.std(regime_means))

        return min(1.0, consistency)

    def export_results(self, output_dir: str) -> None:
        """
        Export Monte Carlo parameter robustness results.

        Args:
            output_dir: Directory to save results
        """
        os.makedirs(output_dir, exist_ok=True)

        # Export summary results
        summary_data = []
        for result in self.results:
            short, long = result.parameter_combination
            summary_data.append(
                {
                    "Fast_Period": short,
                    "Slow_Period": long,
                    "Stability_Score": result.stability_score,
                    "Parameter_Robustness": result.parameter_robustness,
                    "Regime_Consistency": result.regime_consistency,
                    "Is_Stable": result.is_stable,
                    "Base_Sharpe": result.base_performance.get("Sharpe Ratio", 0),
                    "Mean_Sharpe": result.performance_mean.get("Sharpe Ratio", 0),
                    "Sharpe_CI_Lower": result.confidence_intervals.get(
                        "Sharpe Ratio",
                        (0, 0),
                    )[0],
                    "Sharpe_CI_Upper": result.confidence_intervals.get(
                        "Sharpe Ratio",
                        (0, 0),
                    )[1],
                    "Simulations_Count": len(result.monte_carlo_results),
                },
            )

        summary_df = pl.DataFrame(summary_data)
        summary_df.write_csv(
            os.path.join(output_dir, "parameter_robustness_summary.csv"),
        )

        # Export detailed results if requested
        if self.mc_config.save_bootstrap_samples:
            detailed_results = []
            for result in self.results:
                short, long = result.parameter_combination
                for mc_result in result.monte_carlo_results:
                    detailed_results.append(
                        {"Fast_Period": short, "Slow_Period": long, **mc_result},
                    )

            if detailed_results:
                detailed_df = pl.DataFrame(detailed_results)
                detailed_df.write_csv(
                    os.path.join(output_dir, "monte_carlo_detailed_results.csv"),
                )

        self.log(f"Results exported to {output_dir}")


def run_parameter_robustness_analysis(
    tickers: list[str],
    parameter_ranges: dict[str, list[int]],
    strategy_config: dict[str, Any],
    mc_config: MonteCarloConfig | None = None,
) -> dict[str, list[ParameterStabilityResult]]:
    """
    Run comprehensive parameter robustness analysis across multiple tickers.

    Args:
        tickers: List of ticker symbols to analyze
        parameter_ranges: Dictionary with 'short_windows' and 'long_windows' lists
        strategy_config: Base strategy configuration
        mc_config: Monte Carlo configuration (uses defaults if None)

    Returns:
        Dictionary mapping tickers to their robustness analysis results
    """
    if mc_config is None:
        mc_config = MonteCarloConfig()

    # Setup logging
    log, log_close, _, _ = setup_logging(
        module_name="monte_carlo",
        log_file="parameter_robustness.log",
    )

    analyzer = ParameterRobustnessAnalyzer(mc_config, log)
    all_results = {}

    try:
        for ticker in tickers:
            log(f"Starting parameter robustness analysis for {ticker}")
            ticker_results = []

            # Update config for current ticker
            current_config = strategy_config.copy()
            current_config["TICKER"] = ticker

            # Analyze all parameter combinations
            for short in parameter_ranges["short_windows"]:
                for long in parameter_ranges["long_windows"]:
                    if short < long:  # Only valid combinations
                        result = analyzer.analyze_parameter_robustness(
                            ticker,
                            short,
                            long,
                            current_config,
                        )
                        ticker_results.append(result)

            all_results[ticker] = ticker_results
            analyzer.results.extend(ticker_results)

            log(
                f"Completed analysis for {ticker}: {len(ticker_results)} parameter combinations",
            )

        # Export results
        output_dir = (
            f"data/outputs/monte_carlo/parameter_robustness_{len(tickers)}_tickers"
        )
        analyzer.export_results(output_dir)

        # Log summary statistics
        total_combinations = sum(len(results) for results in all_results.values())
        stable_combinations = sum(
            1
            for results in all_results.values()
            for result in results
            if result.is_stable
        )

        log(
            f"Analysis complete: {stable_combinations}/{total_combinations} stable parameter combinations",
        )

    finally:
        log_close()

    return all_results


# Example usage configuration
if __name__ == "__main__":
    # Example configuration for testing
    test_config = {
        "DIRECTION": "Long",
        "USE_HOURLY": False,
        "USE_YEARS": True,
        "YEARS": 3,
        "USE_SYNTHETIC": False,
        "STRATEGY_TYPE": "EMA",
    }

    mc_config = MonteCarloConfig(
        num_simulations=500,  # Reduced for testing
        confidence_level=0.95,
        enable_regime_analysis=True,
    )

    parameter_ranges = {
        "short_windows": [10, 15, 20, 25],
        "long_windows": [30, 40, 50, 60],
    }

    results = run_parameter_robustness_analysis(
        tickers=["BTC-USD"],
        parameter_ranges=parameter_ranges,
        strategy_config=test_config,
        mc_config=mc_config,
    )

    print("Parameter robustness analysis complete!")
