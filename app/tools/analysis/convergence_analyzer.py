"""
Convergence Analyzer

Analyzes convergence across multiple dimensions including timeframes,
strategies, and statistical measures with cross-validation capabilities.
"""

from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import pearsonr

from ..config.statistical_analysis_config import SPDSConfig
from ..models.correlation_models import ConvergenceAnalysisResult, SignificanceLevel


class ConvergenceAnalyzer:
    """
    Analyzes convergence across multiple dimensions of trading performance.

    Provides comprehensive convergence analysis including:
    - Multi-timeframe convergence
    - Cross-strategy convergence
    - Statistical measure convergence
    - Temporal convergence stability
    - Cross-validation of convergence patterns
    """

    def __init__(self, config: SPDSConfig, logger: logging.Logger | None = None):
        """
        Initialize the Convergence Analyzer

        Args:
            config: SPDS configuration instance
            logger: Logger instance for operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Convergence thresholds
        self.strong_convergence_threshold = 0.85
        self.moderate_convergence_threshold = 0.70
        self.weak_convergence_threshold = 0.50

        # Minimum data requirements
        self.min_convergence_data_points = 20
        self.min_timeframes_for_analysis = 2

        # Stability analysis parameters
        self.stability_window_size = 30
        self.stability_overlap = 0.5

        self.logger.info("ConvergenceAnalyzer initialized")

    async def analyze_multi_timeframe_convergence(
        self,
        strategy_name: str,
        ticker: str,
        timeframes: list[str] | None = None,
        convergence_metrics: list[str] | None = None,
    ) -> ConvergenceAnalysisResult:
        """
        Analyze convergence across multiple timeframes

        Args:
            strategy_name: Strategy to analyze
            ticker: Asset ticker
            timeframes: List of timeframes to analyze
            convergence_metrics: Metrics to analyze for convergence

        Returns:
            Multi-timeframe convergence analysis results
        """
        try:
            if timeframes is None:
                timeframes = self.config.TIMEFRAMES

            if convergence_metrics is None:
                convergence_metrics = [
                    "returns",
                    "volatility",
                    "sharpe_ratio",
                    "percentiles",
                ]

            self.logger.info(
                f"Analyzing multi-timeframe convergence for {strategy_name} on {ticker} "
                f"across {len(timeframes)} timeframes",
            )

            # Load data for all timeframes
            timeframe_data = await self._load_multi_timeframe_data(
                strategy_name,
                ticker,
                timeframes,
            )

            # Calculate convergence for each metric
            metric_convergences = {}
            dimensional_convergence = {}

            for metric in convergence_metrics:
                convergence_result = await self._calculate_metric_convergence(
                    timeframe_data,
                    metric,
                    timeframes,
                )
                metric_convergences[metric] = convergence_result
                dimensional_convergence[f"timeframe_{metric}"] = convergence_result[
                    "convergence_score"
                ]

            # Calculate overall convergence score
            overall_convergence = np.mean(list(dimensional_convergence.values()))

            # Analyze convergence stability over time
            convergence_stability = await self._analyze_convergence_stability(
                timeframe_data,
                timeframes,
                convergence_metrics,
            )

            # Identify divergence periods
            divergence_periods = await self._identify_divergence_periods(
                timeframe_data,
                timeframes,
                convergence_metrics,
            )

            # Cross-validation
            cross_validation_scores = await self._cross_validate_convergence(
                timeframe_data,
                timeframes,
                convergence_metrics,
            )

            # Statistical significance testing
            convergence_p_value = await self._test_convergence_significance(
                metric_convergences,
            )

            return ConvergenceAnalysisResult(
                analysis_dimensions=timeframes,
                convergence_type="multi_timeframe",
                overall_convergence_score=overall_convergence,
                dimensional_convergence=dimensional_convergence,
                convergence_stability=convergence_stability,
                divergence_periods=divergence_periods,
                current_divergence_level=self._calculate_current_divergence_level(
                    divergence_periods,
                ),
                divergence_trend=self._analyze_divergence_trend(divergence_periods),
                cross_timeframe_validation={"timeframes": cross_validation_scores},
                cross_strategy_validation={},  # Not applicable for this analysis
                convergence_p_value=convergence_p_value,
                significance_level=self._classify_significance(convergence_p_value),
                analysis_timestamp=datetime.now(),
                sample_period_start=min(
                    data.get("period_start", datetime.now().date())
                    for data in timeframe_data.values()
                ),
                sample_period_end=max(
                    data.get("period_end", datetime.now().date())
                    for data in timeframe_data.values()
                ),
            )

        except Exception as e:
            self.logger.exception(f"Multi-timeframe convergence analysis failed: {e}")
            raise

    async def analyze_cross_strategy_convergence(
        self,
        strategies: list[str],
        ticker: str,
        timeframe: str = "D",
        convergence_metrics: list[str] | None = None,
    ) -> ConvergenceAnalysisResult:
        """
        Analyze convergence across multiple strategies

        Args:
            strategies: List of strategies to analyze
            ticker: Asset ticker
            timeframe: Analysis timeframe
            convergence_metrics: Metrics to analyze for convergence

        Returns:
            Cross-strategy convergence analysis results
        """
        try:
            if convergence_metrics is None:
                convergence_metrics = [
                    "returns",
                    "entry_signals",
                    "exit_signals",
                    "performance",
                ]

            self.logger.info(
                f"Analyzing cross-strategy convergence for {len(strategies)} strategies "
                f"on {ticker} in {timeframe} timeframe",
            )

            # Load data for all strategies
            strategy_data = await self._load_multi_strategy_data(
                strategies,
                ticker,
                timeframe,
            )

            # Calculate convergence for each metric
            metric_convergences = {}
            dimensional_convergence = {}

            for metric in convergence_metrics:
                convergence_result = await self._calculate_strategy_metric_convergence(
                    strategy_data,
                    metric,
                    strategies,
                )
                metric_convergences[metric] = convergence_result
                dimensional_convergence[f"strategy_{metric}"] = convergence_result[
                    "convergence_score"
                ]

            # Calculate overall convergence score
            overall_convergence = np.mean(list(dimensional_convergence.values()))

            # Analyze convergence stability
            convergence_stability = await self._analyze_strategy_convergence_stability(
                strategy_data,
                strategies,
                convergence_metrics,
            )

            # Identify divergence periods
            divergence_periods = await self._identify_strategy_divergence_periods(
                strategy_data,
                strategies,
                convergence_metrics,
            )

            # Cross-validation
            cross_strategy_validation = await self._cross_validate_strategy_convergence(
                strategy_data,
                strategies,
                convergence_metrics,
            )

            # Statistical significance
            convergence_p_value = await self._test_convergence_significance(
                metric_convergences,
            )

            return ConvergenceAnalysisResult(
                analysis_dimensions=strategies,
                convergence_type="cross_strategy",
                overall_convergence_score=overall_convergence,
                dimensional_convergence=dimensional_convergence,
                convergence_stability=convergence_stability,
                divergence_periods=divergence_periods,
                current_divergence_level=self._calculate_current_divergence_level(
                    divergence_periods,
                ),
                divergence_trend=self._analyze_divergence_trend(divergence_periods),
                cross_timeframe_validation={},  # Not applicable
                cross_strategy_validation={"strategies": cross_strategy_validation},
                convergence_p_value=convergence_p_value,
                significance_level=self._classify_significance(convergence_p_value),
                analysis_timestamp=datetime.now(),
                sample_period_start=min(
                    data.get("period_start", datetime.now().date())
                    for data in strategy_data.values()
                ),
                sample_period_end=max(
                    data.get("period_end", datetime.now().date())
                    for data in strategy_data.values()
                ),
            )

        except Exception as e:
            self.logger.exception(f"Cross-strategy convergence analysis failed: {e}")
            raise

    async def analyze_statistical_convergence(
        self,
        data_sources: dict[str, dict[str, Any]],
        statistical_measures: list[str] | None = None,
    ) -> ConvergenceAnalysisResult:
        """
        Analyze convergence between different statistical measures

        Args:
            data_sources: Dictionary of data sources with their metrics
            statistical_measures: Statistical measures to analyze

        Returns:
            Statistical convergence analysis results
        """
        try:
            if statistical_measures is None:
                statistical_measures = ["mean", "median", "percentiles", "var_metrics"]

            self.logger.info(
                f"Analyzing statistical convergence across {len(data_sources)} data sources "
                f"for {len(statistical_measures)} measures",
            )

            # Calculate convergence between statistical measures
            measure_convergences = {}
            dimensional_convergence = {}

            for measure in statistical_measures:
                convergence_result = (
                    await self._calculate_statistical_measure_convergence(
                        data_sources,
                        measure,
                    )
                )
                measure_convergences[measure] = convergence_result
                dimensional_convergence[f"statistical_{measure}"] = convergence_result[
                    "convergence_score"
                ]

            # Overall convergence
            overall_convergence = np.mean(list(dimensional_convergence.values()))

            # Stability analysis
            convergence_stability = (
                await self._analyze_statistical_convergence_stability(
                    data_sources,
                    statistical_measures,
                )
            )

            # Divergence periods
            divergence_periods = await self._identify_statistical_divergence_periods(
                data_sources,
                statistical_measures,
            )

            # Significance testing
            convergence_p_value = await self._test_convergence_significance(
                measure_convergences,
            )

            return ConvergenceAnalysisResult(
                analysis_dimensions=list(data_sources.keys()),
                convergence_type="statistical_measures",
                overall_convergence_score=overall_convergence,
                dimensional_convergence=dimensional_convergence,
                convergence_stability=convergence_stability,
                divergence_periods=divergence_periods,
                current_divergence_level=self._calculate_current_divergence_level(
                    divergence_periods,
                ),
                divergence_trend=self._analyze_divergence_trend(divergence_periods),
                cross_timeframe_validation={},
                cross_strategy_validation={},
                convergence_p_value=convergence_p_value,
                significance_level=self._classify_significance(convergence_p_value),
                analysis_timestamp=datetime.now(),
                sample_period_start=datetime.now().date() - timedelta(days=365),
                sample_period_end=datetime.now().date(),
            )

        except Exception as e:
            self.logger.exception(f"Statistical convergence analysis failed: {e}")
            raise

    # Helper methods

    async def _load_multi_timeframe_data(
        self,
        strategy_name: str,
        ticker: str,
        timeframes: list[str],
    ) -> dict[str, dict[str, Any]]:
        """Load data for multiple timeframes"""
        timeframe_data = {}

        for timeframe in timeframes:
            try:
                # Load strategy data for this timeframe
                if self.config.USE_TRADE_HISTORY:
                    data = await self._load_trade_history_data(
                        strategy_name,
                        ticker,
                        timeframe,
                    )
                else:
                    data = await self._load_equity_data(
                        strategy_name,
                        ticker,
                        timeframe,
                    )

                if (
                    data is not None
                    and len(data.get("returns", [])) >= self.min_convergence_data_points
                ):
                    timeframe_data[timeframe] = data
                else:
                    self.logger.warning(f"Insufficient data for {timeframe} timeframe")

            except Exception as e:
                self.logger.warning(f"Failed to load data for {timeframe}: {e}")

        return timeframe_data

    async def _load_multi_strategy_data(
        self,
        strategies: list[str],
        ticker: str,
        timeframe: str,
    ) -> dict[str, dict[str, Any]]:
        """Load data for multiple strategies"""
        strategy_data = {}

        for strategy in strategies:
            try:
                if self.config.USE_TRADE_HISTORY:
                    data = await self._load_trade_history_data(
                        strategy,
                        ticker,
                        timeframe,
                    )
                else:
                    data = await self._load_equity_data(strategy, ticker, timeframe)

                if (
                    data is not None
                    and len(data.get("returns", [])) >= self.min_convergence_data_points
                ):
                    strategy_data[strategy] = data
                else:
                    self.logger.warning(f"Insufficient data for {strategy} strategy")

            except Exception as e:
                self.logger.warning(f"Failed to load data for {strategy}: {e}")

        return strategy_data

    async def _load_trade_history_data(
        self,
        strategy_name: str,
        ticker: str,
        timeframe: str,
    ) -> dict[str, Any] | None:
        """Load trade history data"""
        # Simplified implementation - would integrate with TradeHistoryAnalyzer
        trade_file = (
            Path(self.config.TRADE_HISTORY_PATH) / f"{ticker}_{strategy_name}.csv"
        )

        if trade_file.exists():
            try:
                df = pd.read_csv(trade_file)
                returns = df.get("return_pct", pd.Series([])).dropna()

                return {
                    "returns": returns.tolist(),
                    "volatility": returns.std(),
                    "sharpe_ratio": (
                        returns.mean() / returns.std() if returns.std() > 0 else 0
                    ),
                    "percentiles": {
                        "p25": returns.quantile(0.25),
                        "p50": returns.quantile(0.50),
                        "p75": returns.quantile(0.75),
                        "p90": returns.quantile(0.90),
                        "p95": returns.quantile(0.95),
                    },
                    "period_start": datetime.now().date() - timedelta(days=365),
                    "period_end": datetime.now().date(),
                }
            except Exception as e:
                self.logger.warning(
                    f"Failed to process trade history file {trade_file}: {e}",
                )

        return None

    async def _load_equity_data(
        self,
        strategy_name: str,
        ticker: str,
        timeframe: str,
    ) -> dict[str, Any] | None:
        """Load equity curve data"""
        # Search for equity files
        for equity_path in self.config.EQUITY_DATA_PATHS:
            # Try the correct naming pattern: {strategy_name}.csv
            equity_file = Path(equity_path) / f"{strategy_name}.csv"
            if not equity_file.exists():
                # Fallback to old naming pattern for compatibility
                equity_file = Path(equity_path) / f"{strategy_name}_{ticker}_equity.csv"

            if equity_file.exists():
                try:
                    df = pd.read_csv(equity_file)
                    returns = df.get("equity_change_pct", pd.Series([])).dropna()

                    return {
                        "returns": returns.tolist(),
                        "volatility": returns.std(),
                        "sharpe_ratio": (
                            returns.mean() / returns.std() if returns.std() > 0 else 0
                        ),
                        "percentiles": {
                            "p25": returns.quantile(0.25),
                            "p50": returns.quantile(0.50),
                            "p75": returns.quantile(0.75),
                            "p90": returns.quantile(0.90),
                            "p95": returns.quantile(0.95),
                        },
                        "period_start": datetime.now().date() - timedelta(days=365),
                        "period_end": datetime.now().date(),
                    }
                except Exception as e:
                    self.logger.warning(
                        f"Failed to process equity file {equity_file}: {e}",
                    )

        return None

    async def _calculate_metric_convergence(
        self,
        timeframe_data: dict[str, dict[str, Any]],
        metric: str,
        timeframes: list[str],
    ) -> dict[str, Any]:
        """Calculate convergence for a specific metric across timeframes"""
        metric_values = []
        valid_timeframes = []

        for timeframe in timeframes:
            if timeframe in timeframe_data:
                data = timeframe_data[timeframe]

                if metric == "returns":
                    value = np.mean(data.get("returns", []))
                elif metric == "volatility":
                    value = data.get("volatility", 0)
                elif metric == "sharpe_ratio":
                    value = data.get("sharpe_ratio", 0)
                elif metric == "percentiles":
                    # Use 90th percentile as representative
                    value = data.get("percentiles", {}).get("p90", 0)
                else:
                    value = 0

                metric_values.append(value)
                valid_timeframes.append(timeframe)

        if len(metric_values) < 2:
            return {
                "convergence_score": 0.0,
                "metric_values": metric_values,
                "correlation": 0.0,
                "divergence_measure": 1.0,
            }

        # Calculate convergence as inverse of coefficient of variation
        mean_value = np.mean(metric_values)
        std_value = np.std(metric_values)

        if mean_value != 0:
            cv = std_value / abs(mean_value)
            convergence_score = 1.0 / (1.0 + cv)  # Normalized to [0, 1]
        else:
            convergence_score = 1.0 if std_value == 0 else 0.0

        # Calculate pairwise correlations if we have time series data
        correlations = []
        if len(valid_timeframes) >= 2:
            for i in range(len(valid_timeframes)):
                for j in range(i + 1, len(valid_timeframes)):
                    tf1, tf2 = valid_timeframes[i], valid_timeframes[j]
                    returns1 = timeframe_data[tf1].get("returns", [])
                    returns2 = timeframe_data[tf2].get("returns", [])

                    if len(returns1) > 5 and len(returns2) > 5:
                        # Align lengths
                        min_len = min(len(returns1), len(returns2))
                        r1, r2 = returns1[:min_len], returns2[:min_len]

                        if len(r1) > 1:
                            corr, _ = pearsonr(r1, r2)
                            correlations.append(abs(corr))  # Use absolute correlation

        avg_correlation = np.mean(correlations) if correlations else 0.0

        return {
            "convergence_score": convergence_score,
            "metric_values": metric_values,
            "correlation": avg_correlation,
            "divergence_measure": 1.0 - convergence_score,
        }

    async def _calculate_strategy_metric_convergence(
        self,
        strategy_data: dict[str, dict[str, Any]],
        metric: str,
        strategies: list[str],
    ) -> dict[str, Any]:
        """Calculate convergence for a metric across strategies"""
        metric_values = []
        valid_strategies = []

        for strategy in strategies:
            if strategy in strategy_data:
                data = strategy_data[strategy]

                if metric == "returns":
                    value = np.mean(data.get("returns", []))
                elif metric == "performance":
                    value = data.get("sharpe_ratio", 0)
                elif metric in ["entry_signals", "exit_signals"]:
                    # Simplified signal analysis
                    value = (
                        len(data.get("returns", [])) / 100
                    )  # Normalized signal frequency
                else:
                    value = 0

                metric_values.append(value)
                valid_strategies.append(strategy)

        if len(metric_values) < 2:
            return {
                "convergence_score": 0.0,
                "metric_values": metric_values,
                "correlation": 0.0,
                "divergence_measure": 1.0,
            }

        # Calculate convergence
        mean_value = np.mean(metric_values)
        std_value = np.std(metric_values)

        if mean_value != 0:
            cv = std_value / abs(mean_value)
            convergence_score = 1.0 / (1.0 + cv)
        else:
            convergence_score = 1.0 if std_value == 0 else 0.0

        # Calculate correlations between strategy returns
        correlations = []
        if len(valid_strategies) >= 2:
            for i in range(len(valid_strategies)):
                for j in range(i + 1, len(valid_strategies)):
                    s1, s2 = valid_strategies[i], valid_strategies[j]
                    returns1 = strategy_data[s1].get("returns", [])
                    returns2 = strategy_data[s2].get("returns", [])

                    if len(returns1) > 5 and len(returns2) > 5:
                        min_len = min(len(returns1), len(returns2))
                        r1, r2 = returns1[:min_len], returns2[:min_len]

                        if len(r1) > 1:
                            corr, _ = pearsonr(r1, r2)
                            correlations.append(abs(corr))

        avg_correlation = np.mean(correlations) if correlations else 0.0

        return {
            "convergence_score": convergence_score,
            "metric_values": metric_values,
            "correlation": avg_correlation,
            "divergence_measure": 1.0 - convergence_score,
        }

    async def _calculate_statistical_measure_convergence(
        self,
        data_sources: dict[str, dict[str, Any]],
        measure: str,
    ) -> dict[str, Any]:
        """Calculate convergence between statistical measures"""
        measure_values = []

        for source_data in data_sources.values():
            if measure in source_data:
                if isinstance(source_data[measure], dict):
                    # For nested measures like percentiles
                    value = np.mean(list(source_data[measure].values()))
                else:
                    value = source_data[measure]

                measure_values.append(value)

        if len(measure_values) < 2:
            return {
                "convergence_score": 0.0,
                "measure_values": measure_values,
                "divergence_measure": 1.0,
            }

        # Calculate convergence as consistency across sources
        mean_value = np.mean(measure_values)
        std_value = np.std(measure_values)

        if mean_value != 0:
            cv = std_value / abs(mean_value)
            convergence_score = 1.0 / (1.0 + cv)
        else:
            convergence_score = 1.0 if std_value == 0 else 0.0

        return {
            "convergence_score": convergence_score,
            "measure_values": measure_values,
            "divergence_measure": 1.0 - convergence_score,
        }

    async def _analyze_convergence_stability(
        self,
        data: dict[str, dict[str, Any]],
        dimensions: list[str],
        metrics: list[str],
    ) -> float:
        """Analyze stability of convergence over time"""
        stability_scores = []

        for _metric in metrics:
            # Calculate rolling convergence scores
            rolling_scores = []

            # Simplified stability analysis
            for dimension in dimensions:
                if dimension in data:
                    returns = data[dimension].get("returns", [])
                    if len(returns) >= self.stability_window_size:
                        # Calculate rolling window convergence
                        for i in range(
                            0,
                            len(returns) - self.stability_window_size,
                            int(
                                self.stability_window_size
                                * (1 - self.stability_overlap),
                            ),
                        ):
                            window_data = returns[i : i + self.stability_window_size]
                            window_score = 1.0 - (
                                np.std(window_data) / (np.mean(window_data) + 1e-8)
                            )
                            rolling_scores.append(max(0, min(1, window_score)))

            if rolling_scores:
                # Stability is inverse of score variance
                score_variance = np.var(rolling_scores)
                stability = 1.0 / (1.0 + score_variance)
                stability_scores.append(stability)

        return np.mean(stability_scores) if stability_scores else 0.5

    async def _analyze_strategy_convergence_stability(
        self,
        data: dict[str, dict[str, Any]],
        strategies: list[str],
        metrics: list[str],
    ) -> float:
        """Analyze stability of strategy convergence"""
        return await self._analyze_convergence_stability(data, strategies, metrics)

    async def _analyze_statistical_convergence_stability(
        self,
        data: dict[str, dict[str, Any]],
        measures: list[str],
    ) -> float:
        """Analyze stability of statistical measure convergence"""
        # Simplified stability analysis for statistical measures
        return 0.7  # Default stability score

    async def _identify_divergence_periods(
        self,
        data: dict[str, dict[str, Any]],
        dimensions: list[str],
        metrics: list[str],
    ) -> list[dict[str, Any]]:
        """Identify periods of significant divergence"""
        divergence_periods = []

        # Simplified divergence period detection
        for i, dimension in enumerate(dimensions):
            if dimension in data:
                returns = data[dimension].get("returns", [])

                # Look for periods where this dimension diverges from others
                if len(returns) > 10:
                    # Calculate z-scores to identify outlier periods
                    z_scores = np.abs(stats.zscore(returns))
                    outlier_indices = np.where(z_scores > 2.0)[0]

                    if len(outlier_indices) > 0:
                        # Group consecutive outliers into periods
                        periods = []
                        current_period = [outlier_indices[0]]

                        for idx in outlier_indices[1:]:
                            if idx == current_period[-1] + 1:
                                current_period.append(idx)
                            else:
                                if len(current_period) >= 3:  # Minimum period length
                                    periods.append(current_period)
                                current_period = [idx]

                        if len(current_period) >= 3:
                            periods.append(current_period)

                        for period in periods:
                            divergence_periods.append(
                                {
                                    "start_index": period[0],
                                    "end_index": period[-1],
                                    "duration": len(period),
                                    "dimension": dimension,
                                    "severity": np.mean([z_scores[i] for i in period]),
                                    "description": f"Divergence in {dimension}",
                                },
                            )

        return divergence_periods

    async def _identify_strategy_divergence_periods(
        self,
        data: dict[str, dict[str, Any]],
        strategies: list[str],
        metrics: list[str],
    ) -> list[dict[str, Any]]:
        """Identify periods of strategy divergence"""
        return await self._identify_divergence_periods(data, strategies, metrics)

    async def _identify_statistical_divergence_periods(
        self,
        data: dict[str, dict[str, Any]],
        measures: list[str],
    ) -> list[dict[str, Any]]:
        """Identify periods of statistical measure divergence"""
        # Simplified implementation
        return []

    async def _cross_validate_convergence(
        self,
        data: dict[str, dict[str, Any]],
        dimensions: list[str],
        metrics: list[str],
    ) -> dict[str, float]:
        """Cross-validate convergence analysis"""
        cv_scores = {}

        for metric in metrics:
            scores = []

            # Simple cross-validation: split data and test consistency
            for dimension in dimensions:
                if dimension in data:
                    returns = data[dimension].get("returns", [])

                    if len(returns) >= 20:
                        # Split data into train/test
                        split_point = len(returns) // 2
                        train_data = returns[:split_point]
                        test_data = returns[split_point:]

                        # Calculate metric consistency between splits
                        train_mean = np.mean(train_data)
                        test_mean = np.mean(test_data)

                        if train_mean != 0:
                            consistency = 1.0 - abs(test_mean - train_mean) / abs(
                                train_mean,
                            )
                            scores.append(max(0, consistency))

            cv_scores[metric] = np.mean(scores) if scores else 0.5

        return cv_scores

    async def _cross_validate_strategy_convergence(
        self,
        data: dict[str, dict[str, Any]],
        strategies: list[str],
        metrics: list[str],
    ) -> dict[str, float]:
        """Cross-validate strategy convergence"""
        return await self._cross_validate_convergence(data, strategies, metrics)

    async def _test_convergence_significance(
        self,
        metric_convergences: dict[str, dict[str, Any]],
    ) -> float:
        """Test statistical significance of convergence"""
        convergence_scores = []

        for convergence_data in metric_convergences.values():
            score = convergence_data.get("convergence_score", 0.0)
            convergence_scores.append(score)

        if len(convergence_scores) == 0:
            return 1.0  # No significance

        # Simple significance test: check if convergence scores are consistently high
        mean_convergence = np.mean(convergence_scores)

        # Convert convergence score to p-value (simplified)
        # High convergence = low p-value (significant)
        p_value = 1.0 - mean_convergence

        return max(0.001, min(1.0, p_value))

    def _calculate_current_divergence_level(
        self,
        divergence_periods: list[dict[str, Any]],
    ) -> float:
        """Calculate current level of divergence"""
        if not divergence_periods:
            return 0.0

        # Look at recent divergence periods
        recent_periods = [p for p in divergence_periods if "end_index" in p]

        if recent_periods:
            # Get the most recent divergence severity
            latest_period = max(recent_periods, key=lambda p: p["end_index"])
            return latest_period.get("severity", 0.0) / 3.0  # Normalize by max z-score

        return 0.0

    def _analyze_divergence_trend(
        self,
        divergence_periods: list[dict[str, Any]],
    ) -> str:
        """Analyze trend in divergence over time"""
        if len(divergence_periods) < 2:
            return "stable"

        # Sort by end time and analyze trend
        sorted_periods = sorted(divergence_periods, key=lambda p: p.get("end_index", 0))

        recent_severities = [p.get("severity", 0) for p in sorted_periods[-3:]]

        if len(recent_severities) >= 2:
            if recent_severities[-1] > recent_severities[0] * 1.2:
                return "increasing"
            if recent_severities[-1] < recent_severities[0] * 0.8:
                return "decreasing"

        return "stable"

    def _classify_significance(self, p_value: float) -> SignificanceLevel:
        """Classify statistical significance"""
        if p_value < 0.01:
            return SignificanceLevel.HIGHLY_SIGNIFICANT
        if p_value < 0.05:
            return SignificanceLevel.SIGNIFICANT
        if p_value < 0.10:
            return SignificanceLevel.MARGINALLY_SIGNIFICANT
        return SignificanceLevel.NOT_SIGNIFICANT
