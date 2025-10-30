"""Adaptive learning engine for dynamic threshold optimization.

This module provides continuous learning capabilities for optimizing
statistical thresholds based on historical performance data.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel

from app.tools.models.statistical_analysis_models import StatisticalThresholds


logger = logging.getLogger(__name__)


@dataclass
class ThresholdPerformance:
    """Performance metrics for a threshold configuration."""

    thresholds: StatisticalThresholds
    exit_efficiency: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    avg_return: float
    sample_size: int
    evaluation_date: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OptimizationResult:
    """Result of threshold optimization."""

    optimal_thresholds: StatisticalThresholds
    expected_improvement: float
    confidence_interval: tuple[float, float]
    optimization_method: str
    convergence_achieved: bool
    iterations: int


class AdaptiveLearningEngine:
    """Adaptive learning engine for continuous threshold optimization.

    This engine provides:
    - Bayesian optimization for threshold tuning
    - Performance-based learning
    - Multi-objective optimization
    - Online learning capabilities
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        exploration_rate: float = 0.2,
        min_samples_for_update: int = 10,
        optimization_window_days: int = 30,
    ):
        """Initialize adaptive learning engine.

        Args:
            learning_rate: Rate of threshold updates
            exploration_rate: Exploration vs exploitation balance
            min_samples_for_update: Minimum samples before updating
            optimization_window_days: Days of history for optimization
        """
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        self.min_samples_for_update = min_samples_for_update
        self.optimization_window_days = optimization_window_days

        # Performance history
        self.performance_history: list[ThresholdPerformance] = []

        # Gaussian Process for Bayesian optimization
        kernel = ConstantKernel(1.0) * RBF(length_scale=1.0)
        self.gp = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=10,
        )

        # Current best thresholds
        self.best_thresholds: StatisticalThresholds | None = None
        self.best_performance: float = 0.0

    def optimize_thresholds(
        self,
        historical_trades: pd.DataFrame,
        current_thresholds: StatisticalThresholds,
        target_metric: str = "exit_efficiency",
    ) -> OptimizationResult:
        """Optimize thresholds based on historical performance.

        Args:
            historical_trades: Historical trade data
            current_thresholds: Current threshold configuration
            target_metric: Metric to optimize (exit_efficiency, sharpe_ratio, etc.)

        Returns:
            Optimization result with new thresholds
        """
        logger.info(f"Optimizing thresholds for {target_metric}")

        # Filter recent trades
        recent_trades = self._filter_recent_trades(historical_trades)

        if len(recent_trades) < self.min_samples_for_update:
            logger.warning(
                f"Insufficient samples for optimization: {len(recent_trades)}",
            )
            return OptimizationResult(
                optimal_thresholds=current_thresholds,
                expected_improvement=0.0,
                confidence_interval=(0.0, 0.0),
                optimization_method="none",
                convergence_achieved=False,
                iterations=0,
            )

        # Choose optimization method based on history
        if len(self.performance_history) < 20:
            # Use grid search for initial exploration
            result = self._grid_search_optimization(
                recent_trades,
                current_thresholds,
                target_metric,
            )
            optimization_method = "grid_search"
        else:
            # Use Bayesian optimization with GP
            result = self._bayesian_optimization(
                recent_trades,
                current_thresholds,
                target_metric,
            )
            optimization_method = "bayesian"

        # Apply learning rate to smooth updates
        optimal_thresholds = self._apply_learning_rate(
            current_thresholds,
            result["thresholds"],
        )

        # Calculate expected improvement
        expected_improvement = self._calculate_expected_improvement(
            recent_trades,
            current_thresholds,
            optimal_thresholds,
            target_metric,
        )

        # Update performance history
        self._update_performance_history(
            optimal_thresholds,
            recent_trades,
            target_metric,
        )

        return OptimizationResult(
            optimal_thresholds=optimal_thresholds,
            expected_improvement=expected_improvement,
            confidence_interval=result.get("confidence_interval", (0.0, 0.0)),
            optimization_method=optimization_method,
            convergence_achieved=result.get("converged", False),
            iterations=result.get("iterations", 0),
        )

    def analyze_threshold_performance(
        self,
        trades: pd.DataFrame,
        threshold_ranges: dict[str, tuple[float, float]],
    ) -> pd.DataFrame:
        """Analyze performance across threshold ranges.

        Args:
            trades: Trade data for analysis
            threshold_ranges: Ranges for each threshold parameter

        Returns:
            DataFrame with performance metrics for each configuration
        """
        results = []

        # Generate threshold combinations
        threshold_configs = self._generate_threshold_configurations(threshold_ranges)

        for config in threshold_configs:
            thresholds = StatisticalThresholds(**config)
            performance = self._evaluate_threshold_performance(trades, thresholds)

            results.append(
                {
                    **config,
                    "exit_efficiency": performance["exit_efficiency"],
                    "sharpe_ratio": performance["sharpe_ratio"],
                    "win_rate": performance["win_rate"],
                    "avg_return": performance["avg_return"],
                },
            )

        return pd.DataFrame(results)

    def predict_performance_improvement(
        self,
        new_thresholds: StatisticalThresholds,
        confidence_level: float = 0.95,
    ) -> tuple[float, tuple[float, float]]:
        """Predict performance improvement with confidence interval.

        Args:
            new_thresholds: Proposed threshold configuration
            confidence_level: Confidence level for interval

        Returns:
            Expected improvement and confidence interval
        """
        if len(self.performance_history) < 5:
            return 0.0, (0.0, 0.0)

        # Convert thresholds to feature vector
        x_features = self._thresholds_to_features(new_thresholds).reshape(1, -1)

        # Predict with GP
        y_pred, y_std = self.gp.predict(X, return_std=True)

        # Calculate confidence interval
        z_score = 1.96 if confidence_level == 0.95 else 2.58
        lower = y_pred[0] - z_score * y_std[0]
        upper = y_pred[0] + z_score * y_std[0]

        # Expected improvement over current best
        improvement = max(0, y_pred[0] - self.best_performance)

        return improvement, (lower, upper)

    def get_adaptive_recommendations(
        self,
        current_performance: dict[str, float],
    ) -> dict[str, Any]:
        """Get adaptive recommendations based on current performance.

        Args:
            current_performance: Current performance metrics

        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            "adjust_thresholds": False,
            "threshold_adjustments": {},
            "exploration_needed": False,
            "confidence": 0.0,
        }

        if not self.best_thresholds:
            recommendations["exploration_needed"] = True
            recommendations["confidence"] = 0.0
            return recommendations

        # Compare current to historical best
        current_efficiency = current_performance.get("exit_efficiency", 0)

        if current_efficiency < self.best_performance * 0.95:  # 5% degradation
            recommendations["adjust_thresholds"] = True

            # Suggest specific adjustments
            if current_performance.get("premature_exits", 0) > 0.2:
                recommendations["threshold_adjustments"]["percentile_threshold"] = (
                    5  # Increase
                )
            if current_performance.get("late_exits", 0) > 0.2:
                recommendations["threshold_adjustments"][
                    "percentile_threshold"
                ] = -5  # Decrease

        # Check if exploration is needed
        if (
            len(self.performance_history) < 50
            or np.random.random() < self.exploration_rate
        ):
            recommendations["exploration_needed"] = True

        # Calculate confidence
        if len(self.performance_history) > 0:
            recent_variance = np.var(
                [p.exit_efficiency for p in self.performance_history[-10:]],
            )
            recommendations["confidence"] = 1.0 - min(recent_variance * 10, 1.0)

        return recommendations

    def _filter_recent_trades(self, trades: pd.DataFrame) -> pd.DataFrame:
        """Filter trades within optimization window."""
        if "exit_date" not in trades.columns:
            return trades

        cutoff_date = datetime.utcnow() - timedelta(days=self.optimization_window_days)
        return trades[pd.to_datetime(trades["exit_date"]) >= cutoff_date]

    def _grid_search_optimization(
        self,
        trades: pd.DataFrame,
        current: StatisticalThresholds,
        target_metric: str,
    ) -> dict[str, Any]:
        """Perform grid search optimization."""
        best_score = -np.inf
        best_thresholds = current

        # Define search ranges
        percentile_range = range(85, 100, 5)
        rarity_range = [0.01, 0.02, 0.05, 0.10]
        timeframe_range = [1, 2, 3, 4]

        iterations = 0
        for percentile in percentile_range:
            for rarity in rarity_range:
                for timeframes in timeframe_range:
                    iterations += 1

                    thresholds = StatisticalThresholds(
                        percentile_threshold=percentile,
                        dual_layer_threshold=current.dual_layer_threshold,
                        sample_size_minimum=current.sample_size_minimum,
                        confidence_levels=current.confidence_levels,
                        rarity_threshold=rarity,
                        multi_timeframe_agreement=timeframes,
                    )

                    performance = self._evaluate_threshold_performance(
                        trades,
                        thresholds,
                    )
                    score = performance[target_metric]

                    if score > best_score:
                        best_score = score
                        best_thresholds = thresholds

        return {
            "thresholds": best_thresholds,
            "score": best_score,
            "iterations": iterations,
            "converged": True,
        }

    def _bayesian_optimization(
        self,
        trades: pd.DataFrame,
        current: StatisticalThresholds,
        target_metric: str,
    ) -> dict[str, Any]:
        """Perform Bayesian optimization using Gaussian Process."""
        # Prepare training data from history
        if self.performance_history:
            x_features = np.array(
                [
                    self._thresholds_to_features(p.thresholds)
                    for p in self.performance_history
                ],
            )
            y = np.array([getattr(p, target_metric) for p in self.performance_history])

            # Fit GP model
            self.gp.fit(X, y)

        # Define objective function
        def objective(params):
            thresholds = StatisticalThresholds(
                percentile_threshold=int(params[0]),
                dual_layer_threshold=params[1],
                rarity_threshold=params[2],
                multi_timeframe_agreement=int(params[3]),
                sample_size_minimum=current.sample_size_minimum,
                confidence_levels=current.confidence_levels,
            )

            performance = self._evaluate_threshold_performance(trades, thresholds)
            return -performance[target_metric]  # Minimize negative performance

        # Define bounds
        bounds = [
            (85, 99),  # percentile_threshold
            (0.6, 0.95),  # dual_layer_threshold
            (0.01, 0.10),  # rarity_threshold
            (1, 4),  # multi_timeframe_agreement
        ]

        # Optimize
        result = differential_evolution(
            objective,
            bounds,
            maxiter=50,
            popsize=15,
            seed=42,
        )

        # Extract optimal thresholds
        optimal_thresholds = StatisticalThresholds(
            percentile_threshold=int(result.x[0]),
            dual_layer_threshold=result.x[1],
            rarity_threshold=result.x[2],
            multi_timeframe_agreement=int(result.x[3]),
            sample_size_minimum=current.sample_size_minimum,
            confidence_levels=current.confidence_levels,
        )

        return {
            "thresholds": optimal_thresholds,
            "score": -result.fun,
            "iterations": result.nit,
            "converged": result.success,
            "confidence_interval": self._calculate_confidence_interval(
                optimal_thresholds,
                trades,
            ),
        }

    def _evaluate_threshold_performance(
        self,
        trades: pd.DataFrame,
        thresholds: StatisticalThresholds,
    ) -> dict[str, float]:
        """Evaluate performance of threshold configuration."""
        if len(trades) == 0:
            return {
                "exit_efficiency": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "avg_return": 0.0,
            }

        # Simulate exits with thresholds
        exit_signals = self._simulate_exits(trades, thresholds)

        # Calculate metrics
        returns = trades["return"].values
        exit_returns = returns[exit_signals]

        if len(exit_returns) == 0:
            exit_efficiency = 0.0
        else:
            # Exit efficiency: how well we captured gains
            potential_gains = trades[trades["return"] > 0]["return"].sum()
            captured_gains = exit_returns[exit_returns > 0].sum()
            exit_efficiency = captured_gains / max(potential_gains, 1e-6)

        # Sharpe ratio
        if len(exit_returns) > 1:
            sharpe_ratio = (
                np.mean(exit_returns) / (np.std(exit_returns) + 1e-6) * np.sqrt(252)
            )
        else:
            sharpe_ratio = 0.0

        # Win rate
        win_rate = len(exit_returns[exit_returns > 0]) / max(len(exit_returns), 1)

        # Average return
        avg_return = np.mean(exit_returns) if len(exit_returns) > 0 else 0.0

        # Max drawdown (simplified)
        cumulative_returns = np.cumprod(1 + exit_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0.0

        return {
            "exit_efficiency": exit_efficiency,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": abs(max_drawdown),
            "win_rate": win_rate,
            "avg_return": avg_return,
        }

    def _simulate_exits(
        self,
        trades: pd.DataFrame,
        thresholds: StatisticalThresholds,
    ) -> np.ndarray:
        """Simulate exit signals based on thresholds."""
        exit_signals = np.zeros(len(trades), dtype=bool)

        for i, trade in trades.iterrows():
            # Check percentile threshold
            if trade.get("strategy_percentile", 0) >= thresholds.percentile_threshold:
                exit_signals[i] = True
                continue

            # Check dual layer convergence
            if trade.get("dual_layer_score", 0) >= thresholds.dual_layer_threshold:
                exit_signals[i] = True
                continue

            # Check statistical rarity
            if trade.get("statistical_rarity", 0) <= thresholds.rarity_threshold:
                exit_signals[i] = True

        return exit_signals

    def _apply_learning_rate(
        self,
        current: StatisticalThresholds,
        optimal: StatisticalThresholds,
    ) -> StatisticalThresholds:
        """Apply learning rate to smooth threshold updates."""
        # Smooth update for continuous parameters
        new_percentile = int(
            current.percentile_threshold * (1 - self.learning_rate)
            + optimal.percentile_threshold * self.learning_rate,
        )

        new_dual_layer = (
            current.dual_layer_threshold * (1 - self.learning_rate)
            + optimal.dual_layer_threshold * self.learning_rate
        )

        new_rarity = (
            current.rarity_threshold * (1 - self.learning_rate)
            + optimal.rarity_threshold * self.learning_rate
        )

        return StatisticalThresholds(
            percentile_threshold=new_percentile,
            dual_layer_threshold=new_dual_layer,
            rarity_threshold=new_rarity,
            multi_timeframe_agreement=optimal.multi_timeframe_agreement,
            sample_size_minimum=current.sample_size_minimum,
            confidence_levels=current.confidence_levels,
        )

    def _calculate_expected_improvement(
        self,
        trades: pd.DataFrame,
        current: StatisticalThresholds,
        optimal: StatisticalThresholds,
        target_metric: str,
    ) -> float:
        """Calculate expected improvement from threshold change."""
        current_performance = self._evaluate_threshold_performance(trades, current)
        optimal_performance = self._evaluate_threshold_performance(trades, optimal)

        current_score = current_performance[target_metric]
        optimal_score = optimal_performance[target_metric]

        return (optimal_score - current_score) / max(abs(current_score), 1e-6)

    def _update_performance_history(
        self,
        thresholds: StatisticalThresholds,
        trades: pd.DataFrame,
        target_metric: str,
    ) -> None:
        """Update performance history with new evaluation."""
        performance = self._evaluate_threshold_performance(trades, thresholds)

        record = ThresholdPerformance(
            thresholds=thresholds,
            exit_efficiency=performance["exit_efficiency"],
            sharpe_ratio=performance["sharpe_ratio"],
            max_drawdown=performance["max_drawdown"],
            win_rate=performance["win_rate"],
            avg_return=performance["avg_return"],
            sample_size=len(trades),
        )

        self.performance_history.append(record)

        # Update best if improved
        metric_value = performance[target_metric]
        if metric_value > self.best_performance:
            self.best_performance = metric_value
            self.best_thresholds = thresholds

        # Limit history size
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]

    def _thresholds_to_features(self, thresholds: StatisticalThresholds) -> np.ndarray:
        """Convert thresholds to feature vector for ML."""
        return np.array(
            [
                thresholds.percentile_threshold,
                thresholds.dual_layer_threshold,
                thresholds.rarity_threshold,
                thresholds.multi_timeframe_agreement,
            ],
        )

    def _generate_threshold_configurations(
        self,
        ranges: dict[str, tuple[float, float]],
    ) -> list[dict[str, Any]]:
        """Generate threshold configurations from ranges."""
        configs = []

        # Simple grid generation (can be enhanced)
        percentile_values = np.linspace(
            ranges.get("percentile_threshold", (85, 99))[0],
            ranges.get("percentile_threshold", (85, 99))[1],
            5,
        )

        dual_layer_values = np.linspace(
            ranges.get("dual_layer_threshold", (0.6, 0.95))[0],
            ranges.get("dual_layer_threshold", (0.6, 0.95))[1],
            5,
        )

        for p in percentile_values:
            for d in dual_layer_values:
                configs.append(
                    {
                        "percentile_threshold": int(p),
                        "dual_layer_threshold": d,
                        "rarity_threshold": 0.05,  # Default
                        "multi_timeframe_agreement": 2,  # Default
                    },
                )

        return configs

    def _calculate_confidence_interval(
        self,
        thresholds: StatisticalThresholds,
        trades: pd.DataFrame,
    ) -> tuple[float, float]:
        """Calculate confidence interval for threshold performance."""
        # Bootstrap confidence interval
        n_bootstrap = 100
        scores = []

        for _ in range(n_bootstrap):
            # Resample trades
            sample = trades.sample(n=len(trades), replace=True)
            performance = self._evaluate_threshold_performance(sample, thresholds)
            scores.append(performance["exit_efficiency"])

        # Calculate percentiles
        lower = np.percentile(scores, 2.5)
        upper = np.percentile(scores, 97.5)

        return (lower, upper)
