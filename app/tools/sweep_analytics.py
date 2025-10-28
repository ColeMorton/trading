"""
Sweep Analytics Engine

Financial analytics engine for MA parameter sweep analysis, providing
comprehensive performance metrics, rankings, and optimization recommendations.
"""

from dataclasses import dataclass
import json
import math
import os
from typing import Any


@dataclass
class SweepPerformanceData:
    """Individual period performance data."""

    ticker: str
    period: int
    ma_type: str
    sharpe_ratio: float
    sortino_ratio: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    volatility: float
    calmar_ratio: float
    information_ratio: float
    trend_direction: str
    trend_strength: str
    r_squared: float
    data_points: int

    @property
    def risk_adjusted_score(self) -> float:
        """Advanced composite risk-adjusted performance score with normalization."""
        try:
            # Normalize individual metrics using sophisticated functions
            sharpe_norm = self._normalize_sharpe_ratio(self.sharpe_ratio)
            sortino_norm = self._normalize_sortino_ratio(self.sortino_ratio)
            calmar_norm = self._normalize_calmar_ratio(self.calmar_ratio)

            # Weighted composite with rebalanced weights for better discrimination
            base_score = (
                sharpe_norm * 0.35
                + sortino_norm * 0.35  # Risk-adjusted return quality
                + calmar_norm  # Downside protection strength
                * 0.30  # Drawdown management effectiveness
            )

            # Apply statistical confidence adjustment based on data quality
            confidence_multiplier = self._calculate_confidence_multiplier(
                self.data_points
            )

            # Final bounded score
            final_score = base_score * confidence_multiplier

            # Ensure score is bounded and valid
            return max(0.1, min(2.618, final_score))

        except Exception:
            # Fallback to minimum score for any calculation errors
            return 0.1

    def _normalize_sharpe_ratio(self, sharpe: float) -> float:
        """Sigmoid normalization for Sharpe ratio with natural saturation."""
        if math.isnan(sharpe) or math.isinf(sharpe) or sharpe <= 0:
            return 0.1

        # Cap extreme values before normalization
        sharpe = min(sharpe, 10.0)  # Reasonable cap for daily strategies

        # Sigmoid parameters optimized for Sharpe ratios
        midpoint = 1.5  # Good Sharpe ratio benchmark
        steepness = 0.8  # Moderate selectivity
        max_score = 2.618  # Golden ratio squared cap

        # Sigmoid transformation with smooth saturation
        score = max_score / (1 + math.exp(-steepness * (sharpe - midpoint)))
        return max(0.1, min(max_score, score))

    def _normalize_sortino_ratio(self, sortino: float) -> float:
        """Asymptotic normalization for Sortino ratio preventing infinity."""
        if math.isnan(sortino) or math.isinf(sortino) or sortino <= 0:
            return 0.1

        # Cap extreme values to prevent overflow
        sortino = min(sortino, 50.0)  # Generous cap for long-term strategies

        # Asymptotic function parameters
        baseline = 2.0  # Calibrated baseline for good performance
        steepness = 1.2  # Moderate diminishing returns
        max_score = 2.618

        # Asymptotic transformation: approaches but never reaches maximum
        score = max_score * (sortino**steepness) / (baseline + sortino**steepness)
        return float(max(0.1, min(max_score, score)))

    def _normalize_calmar_ratio(self, calmar: float) -> float:
        """Bounded normalization for Calmar ratio with soft caps."""
        if math.isnan(calmar) or math.isinf(calmar) or calmar <= 0:
            return 0.1

        # Handle extreme values with hard cap
        if calmar >= 5.0:
            return 2.618

        # Smooth scaling with diminishing returns
        normalized = (calmar / 5.0) ** 0.8  # Power scaling for smooth curve
        score = 0.1 + 2.518 * normalized  # Map to [0.1, 2.618] range

        return float(max(0.1, min(2.618, score)))

    def _calculate_confidence_multiplier(self, data_points: int) -> float:
        """Statistical confidence adjustment based on data quality."""
        if data_points < 500:
            # Very low confidence: harsh penalty for insufficient data
            return 0.3 + 0.2 * (data_points / 500) ** 2
        if data_points < 1000:
            # Low confidence: moderate penalty
            return 0.5 + 0.3 * ((data_points - 500) / 500) ** 1.5
        if data_points < 2000:
            # Moderate confidence: light penalty
            return 0.8 + 0.2 * ((data_points - 1000) / 1000)
        # High confidence: full score
        return 1.0


@dataclass
class SweepStatistics:
    """Statistical summary across all periods."""

    metric_name: str
    min_value: float
    max_value: float
    median_value: float
    mean_value: float
    std_dev: float
    q1: float
    q3: float
    best_period: int
    worst_period: int


class SweepAnalyticsEngine:
    """Financial analytics engine for sweep results."""

    def __init__(self, analysis_dir: str = "data/outputs/ma_cross/analysis"):
        """Initialize analytics engine."""
        self.analysis_dir = analysis_dir
        self.performance_data: list[SweepPerformanceData] = []
        self.statistics: dict[str, SweepStatistics] = {}

    def load_sweep_data(
        self, tickers: list[str], periods: list[int], ma_type: str
    ) -> int:
        """Load analytics data from JSON files for given sweep parameters."""
        loaded_count = 0

        for ticker in tickers:
            for period in periods:
                try:
                    json_path = os.path.join(
                        self.analysis_dir, f"{ticker}_{period}.json"
                    )

                    if os.path.exists(json_path):
                        with open(json_path) as f:
                            data = json.load(f)

                        # Extract analytics data
                        analytics = data.get("analytics", {})
                        risk_metrics = analytics.get("risk_metrics", {})
                        perf_metrics = analytics.get("performance_metrics", {})
                        trend_metrics = analytics.get("trend_metrics", {})
                        metadata = data.get("metadata", {})

                        # Extract and validate raw metrics
                        raw_sharpe = risk_metrics.get("sharpe_ratio", 0.0)
                        raw_sortino = risk_metrics.get("sortino_ratio", 0.0)
                        raw_calmar = perf_metrics.get("calmar_ratio", 0.0)
                        raw_volatility = risk_metrics.get("volatility", 0.0)
                        raw_max_dd = risk_metrics.get("max_drawdown", 0.0)
                        raw_data_points = metadata.get("data_points", 0)

                        # Enhanced data validation and outlier detection
                        validated_metrics = self._validate_and_sanitize_metrics(
                            {
                                "sharpe_ratio": raw_sharpe,
                                "sortino_ratio": raw_sortino,
                                "calmar_ratio": raw_calmar,
                                "volatility": raw_volatility,
                                "max_drawdown": raw_max_dd,
                                "total_return": perf_metrics.get("total_return", 0.0),
                                "annualized_return": perf_metrics.get(
                                    "annualized_return", 0.0
                                ),
                                "information_ratio": perf_metrics.get(
                                    "information_ratio", 0.0
                                ),
                                "r_squared": trend_metrics.get("r_squared", 0.0),
                            },
                            ticker,
                            period,
                        )

                        # Create performance data object with validated metrics
                        perf_data = SweepPerformanceData(
                            ticker=ticker,
                            period=period,
                            ma_type=ma_type,
                            sharpe_ratio=validated_metrics["sharpe_ratio"],
                            sortino_ratio=validated_metrics["sortino_ratio"],
                            total_return=validated_metrics["total_return"],
                            annualized_return=validated_metrics["annualized_return"],
                            max_drawdown=validated_metrics["max_drawdown"],
                            volatility=validated_metrics["volatility"],
                            calmar_ratio=validated_metrics["calmar_ratio"],
                            information_ratio=validated_metrics["information_ratio"],
                            trend_direction=trend_metrics.get(
                                "trend_direction", "Unknown"
                            ),
                            trend_strength=trend_metrics.get(
                                "trend_strength", "Unknown"
                            ),
                            r_squared=validated_metrics["r_squared"],
                            data_points=raw_data_points,
                        )

                        self.performance_data.append(perf_data)
                        loaded_count += 1

                except Exception:
                    # Skip corrupted/missing files
                    continue

        # Calculate statistics if data was loaded
        if self.performance_data:
            self._calculate_statistics()

        return loaded_count

    def _validate_and_sanitize_metrics(
        self, metrics: dict[str, float], ticker: str, period: int
    ) -> dict[str, float]:
        """Enhanced validation and sanitization of financial metrics."""
        validated = {}
        warnings = []

        for metric_name, value in metrics.items():
            try:
                # Convert to float and handle None values
                if value is None:
                    validated[metric_name] = 0.0
                    continue

                float_value = float(value)

                # Check for invalid mathematical values
                if math.isnan(float_value):
                    warnings.append(f"{metric_name} is NaN")
                    validated[metric_name] = 0.0
                    continue

                if math.isinf(float_value):
                    warnings.append(f"{metric_name} is infinite ({float_value})")
                    validated[metric_name] = self._get_reasonable_cap(metric_name)
                    continue

                # Outlier detection using context-aware thresholds
                if self._is_metric_outlier(metric_name, float_value):
                    warnings.append(
                        f"{metric_name} is extreme outlier ({float_value:.2f})"
                    )
                    validated[metric_name] = self._get_reasonable_cap(metric_name)
                    continue

                # Value passed all checks
                validated[metric_name] = float_value

            except (ValueError, TypeError, OverflowError) as e:
                warnings.append(f"{metric_name} conversion error: {e}")
                validated[metric_name] = 0.0

        # Log warnings if any were found
        if warnings:
            warning_msg = f"Data quality issues for {ticker} period {period}: {'; '.join(warnings)}"
            # In a real implementation, this would use a proper logger
            # For now, we'll store it internally for potential debugging
            self._validation_warnings = getattr(self, "_validation_warnings", [])
            self._validation_warnings.append(warning_msg)

        return validated

    def _is_metric_outlier(self, metric_name: str, value: float) -> bool:
        """Detect outliers using metric-specific thresholds."""
        outlier_thresholds = {
            "sharpe_ratio": 25.0,  # Extremely high Sharpe ratios are suspicious
            "sortino_ratio": 50.0,  # Very high Sortino ratios indicate near-zero downside
            "calmar_ratio": 10.0,  # Very high Calmar ratios are rare
            "volatility": 200.0,  # Volatility over 200% is extreme
            "max_drawdown": 99.9,  # Drawdown should not exceed 99.9%
            "total_return": 100000.0,  # Returns over 100,000% are suspicious
            "annualized_return": 1000.0,  # Annual returns over 1000% are extreme
            "information_ratio": 20.0,  # Very high information ratios are rare
            "r_squared": 1.1,  # R-squared cannot exceed 1.0
        }

        threshold = outlier_thresholds.get(metric_name, float("inf"))
        return abs(value) > threshold

    def _get_reasonable_cap(self, metric_name: str) -> float:
        """Get reasonable cap values for different metrics."""
        reasonable_caps = {
            "sharpe_ratio": 15.0,  # Cap at excellent but achievable Sharpe
            "sortino_ratio": 25.0,  # Cap at very good Sortino
            "calmar_ratio": 5.0,  # Cap at excellent Calmar
            "volatility": 100.0,  # Cap at high but reasonable volatility
            "max_drawdown": 95.0,  # Cap at extreme but possible drawdown
            "total_return": 50000.0,  # Cap at very high but possible return
            "annualized_return": 500.0,  # Cap at extreme but possible annual return
            "information_ratio": 10.0,  # Cap at excellent information ratio
            "r_squared": 1.0,  # Cap at perfect correlation
        }

        return reasonable_caps.get(metric_name, 1.0)

    def _calculate_statistics(self) -> None:
        """Calculate statistical summaries for all metrics."""
        metrics_map = {
            "sharpe_ratio": "Sharpe Ratio",
            "sortino_ratio": "Sortino Ratio",
            "total_return": "Total Return (%)",
            "annualized_return": "Annualized Return (%)",
            "max_drawdown": "Max Drawdown (%)",
            "volatility": "Volatility (%)",
            "calmar_ratio": "Calmar Ratio",
            "information_ratio": "Information Ratio",
            "r_squared": "R-Squared",
            "risk_adjusted_score": "Risk-Adjusted Score",
        }

        for metric_key, metric_name in metrics_map.items():
            values = []
            period_map = {}

            for data in self.performance_data:
                try:
                    if metric_key == "risk_adjusted_score":
                        value = data.risk_adjusted_score
                    else:
                        value = getattr(data, metric_key)

                    # Validate and sanitize the value
                    clean_value = self._sanitize_numeric_value(value)
                    if clean_value is not None:
                        values.append(clean_value)
                        period_map[clean_value] = data.period
                except Exception:
                    # Skip invalid data points
                    continue

            if values:
                try:
                    sorted_values = sorted(values)
                    n = len(sorted_values)

                    # Robust statistical calculations
                    min_val = min(values)
                    max_val = max(values)
                    mean_val = sum(values) / len(values)
                    median_val = self._robust_median(sorted_values)
                    std_val = (
                        self._robust_std_dev(values, mean_val)
                        if len(values) > 1
                        else 0.0
                    )
                    q1_val = sorted_values[max(0, n // 4)]
                    q3_val = sorted_values[min(n - 1, 3 * n // 4)]

                    self.statistics[metric_key] = SweepStatistics(
                        metric_name=metric_name,
                        min_value=min_val,
                        max_value=max_val,
                        median_value=median_val,
                        mean_value=mean_val,
                        std_dev=std_val,
                        q1=q1_val,
                        q3=q3_val,
                        best_period=(
                            period_map[max_val]
                            if metric_key != "max_drawdown"
                            else period_map[min_val]
                        ),
                        worst_period=(
                            period_map[min_val]
                            if metric_key != "max_drawdown"
                            else period_map[max_val]
                        ),
                    )
                except Exception:
                    # Skip this metric if calculations fail
                    continue

    def _sanitize_numeric_value(self, value: Any) -> float | None:
        """Sanitize and validate numeric values for statistics calculations."""
        try:
            # Convert to float
            float_val = float(value)

            # Check for invalid values
            if math.isnan(float_val) or math.isinf(float_val):
                return None

            # Check for extremely large values that might cause issues
            if abs(float_val) > 1e15:
                return None

            return float_val
        except (ValueError, TypeError, OverflowError):
            return None

    def _robust_median(self, sorted_values: list[float]) -> float:
        """Calculate median using robust method to avoid fraction issues."""
        n = len(sorted_values)
        if n == 0:
            return 0.0

        if n % 2 == 1:
            # Odd number of values
            return float(sorted_values[n // 2])
        # Even number of values - average the two middle values
        mid1 = sorted_values[n // 2 - 1]
        mid2 = sorted_values[n // 2]
        return float((mid1 + mid2) / 2.0)

    def _robust_std_dev(self, values: list[float], mean_val: float) -> float:
        """Calculate standard deviation using robust method."""
        if len(values) <= 1:
            return 0.0

        try:
            # Calculate variance
            variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
            return float(math.sqrt(variance))
        except (ValueError, OverflowError):
            return 0.0

    def get_top_performers(
        self, metric: str, count: int = 3
    ) -> list[SweepPerformanceData]:
        """Get top performers by specified metric."""
        if metric == "risk_adjusted_score":
            sorted_data = sorted(
                self.performance_data, key=lambda x: x.risk_adjusted_score, reverse=True
            )
        elif metric == "max_drawdown":
            # For drawdown, lower is better
            sorted_data = sorted(
                self.performance_data, key=lambda x: getattr(x, metric)
            )
        else:
            sorted_data = sorted(
                self.performance_data, key=lambda x: getattr(x, metric), reverse=True
            )

        return sorted_data[:count]

    def get_ranked_performance(self) -> list[SweepPerformanceData]:
        """Get all periods ranked by risk-adjusted score."""
        return sorted(
            self.performance_data, key=lambda x: x.risk_adjusted_score, reverse=True
        )

    def get_risk_categories(self) -> dict[str, list[SweepPerformanceData]]:
        """Categorize periods by risk level."""
        if not self.performance_data:
            return {"low": [], "medium": [], "high": []}

        volatilities = [data.volatility for data in self.performance_data]
        vol_q1 = sorted(volatilities)[len(volatilities) // 3]
        vol_q3 = sorted(volatilities)[2 * len(volatilities) // 3]

        categories: dict[str, list[SweepPerformanceData]] = {
            "low": [],
            "medium": [],
            "high": [],
        }

        for data in self.performance_data:
            if data.volatility <= vol_q1:
                categories["low"].append(data)
            elif data.volatility <= vol_q3:
                categories["medium"].append(data)
            else:
                categories["high"].append(data)

        return categories

    def get_optimization_recommendations(self) -> dict[str, SweepPerformanceData]:
        """Generate optimization recommendations for different strategy types."""
        if not self.performance_data:
            return {}

        recommendations = {}

        # Best all-around performer (highest risk-adjusted score)
        recommendations["balanced"] = max(
            self.performance_data, key=lambda x: x.risk_adjusted_score
        )

        # Best for aggressive strategies (highest return above median volatility)
        high_vol_data = [
            d
            for d in self.performance_data
            if d.volatility
            > self.statistics.get(
                "volatility", SweepStatistics("", 0, 0, 0, 0, 0, 0, 0, 0, 0)
            ).median_value
        ]
        if high_vol_data:
            recommendations["aggressive"] = max(
                high_vol_data, key=lambda x: x.total_return
            )

        # Best for conservative strategies (highest sharpe with low drawdown)
        low_dd_data = [
            d
            for d in self.performance_data
            if d.max_drawdown
            < self.statistics.get(
                "max_drawdown", SweepStatistics("", 0, 0, 0, 0, 0, 0, 0, 0, 0)
            ).median_value
        ]
        if low_dd_data:
            recommendations["conservative"] = max(
                low_dd_data, key=lambda x: x.sharpe_ratio
            )

        # Most consistent performer (highest sharpe with low volatility)
        recommendations["consistent"] = max(
            self.performance_data, key=lambda x: x.sharpe_ratio / (x.volatility + 1)
        )

        return recommendations

    def get_outlier_analysis(self) -> dict[str, list[SweepPerformanceData]]:
        """Identify statistical outliers in performance."""
        outliers: dict[str, list[SweepPerformanceData]] = {
            "exceptional": [],
            "underperforming": [],
        }

        if not self.performance_data or len(self.performance_data) < 3:
            return outliers

        # Use risk-adjusted score for outlier detection
        scores = [data.risk_adjusted_score for data in self.performance_data]
        mean_score = sum(scores) / len(scores)

        if len(scores) > 1:
            std_score = self._robust_std_dev(scores, mean_score)

            for data in self.performance_data:
                z_score = (data.risk_adjusted_score - mean_score) / std_score

                if z_score > 1.5:  # More than 1.5 standard deviations above mean
                    outliers["exceptional"].append(data)
                elif z_score < -1.5:  # More than 1.5 standard deviations below mean
                    outliers["underperforming"].append(data)

        return outliers
