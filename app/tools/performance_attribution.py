"""
Performance Attribution Framework for SPDS

This module provides comprehensive performance attribution and factor analysis
for the SPDS scoring system, enabling detailed tracking of factor contributions
and systematic performance measurement.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class FactorAttribution:
    """Attribution data for a single factor."""

    factor_name: str
    contribution: float
    weight: float
    score: float
    performance_metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class AttributionResult:
    """Complete attribution analysis result."""

    overall_score: float
    signal: str
    confidence: float
    factors: list[FactorAttribution]
    regime_info: dict[str, Any]
    performance_summary: dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceAttributor:
    """
    Framework for analyzing factor performance and attribution.

    Tracks individual factor contributions to overall scoring and provides
    performance analytics for systematic improvement.
    """

    def __init__(self, attribution_dir: str = "./attribution_data"):
        """
        Initialize performance attributor.

        Args:
            attribution_dir: Directory for storing attribution data
        """
        self.attribution_dir = Path(attribution_dir)
        self.attribution_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Factor performance tracking
        self.factor_history: dict[str, list[dict[str, Any]]] = {}

        # Performance metrics cache
        self.performance_cache: dict[str, dict[str, float]] = {}

    def analyze_attribution(
        self,
        component_scores: dict[str, Any],
        analysis_result: dict[str, Any],
    ) -> AttributionResult:
        """
        Perform comprehensive attribution analysis.

        Args:
            component_scores: Component scores from market analyzer
            analysis_result: Full analysis result dictionary

        Returns:
            AttributionResult with detailed attribution breakdown
        """
        try:
            # Extract factor information
            factors = self._extract_factor_attributions(component_scores)

            # Calculate performance metrics for each factor
            for factor in factors:
                factor.performance_metrics = self._calculate_factor_performance(factor)

            # Extract regime information
            regime_info = {
                "volatility_regime": component_scores.get(
                    "volatility_regime",
                    "normal",
                ),
                "current_vix": component_scores.get("current_vix", 20.0),
                "threshold_adjustments": component_scores.get(
                    "threshold_adjustments",
                    {},
                ),
                "weight_adjustments": component_scores.get("weight_adjustments", {}),
            }

            # Create attribution result
            attribution = AttributionResult(
                overall_score=component_scores.get("overall_score", 0.0),
                signal=analysis_result.get("exit_signal", "HOLD"),
                confidence=analysis_result.get("confidence_level", 0.5),
                factors=factors,
                regime_info=regime_info,
                performance_summary=self._calculate_performance_summary(factors),
            )

            # Store attribution for historical analysis
            self._store_attribution(
                attribution,
                analysis_result.get("ticker", "UNKNOWN"),
            )

            return attribution

        except Exception as e:
            self.logger.exception(f"Attribution analysis failed: {e}")
            return self._default_attribution_result()

    def _extract_factor_attributions(
        self,
        component_scores: dict[str, Any],
    ) -> list[FactorAttribution]:
        """Extract factor attribution information from component scores."""
        factors = []

        # Define factor mappings
        factor_mappings = {
            "risk": {
                "contribution": "risk_contribution",
                "score": "risk_score",
                "weight_key": "risk",
            },
            "momentum": {
                "contribution": "momentum_contribution",
                "score": "momentum_score",
                "weight_key": "momentum",
            },
            "trend": {
                "contribution": "trend_contribution",
                "score": "trend_score",
                "weight_key": "trend",
            },
            "risk_adjusted": {
                "contribution": "risk_adjusted_contribution",
                "score": "risk_adjusted_score",
                "weight_key": "risk_adj",
            },
            "mean_reversion": {
                "contribution": "mean_reversion_contribution",
                "score": "mean_reversion_score",
                "weight_key": "mean_rev",
            },
            "volume_liquidity": {
                "contribution": "volume_contribution",
                "score": "volume_liquidity_score",
                "weight_key": "volume",
            },
        }

        # Extract normalized weights
        normalized_weights = component_scores.get("normalized_weights", {})

        # Create factor attributions
        for factor_name, mapping in factor_mappings.items():
            contribution = component_scores.get(mapping["contribution"], 0.0)
            score = component_scores.get(mapping["score"], 0.0)
            weight = normalized_weights.get(mapping["weight_key"], 0.0)

            factor = FactorAttribution(
                factor_name=factor_name,
                contribution=float(contribution),
                weight=float(weight),
                score=float(score),
            )

            factors.append(factor)

        return factors

    def _calculate_factor_performance(
        self,
        factor: FactorAttribution,
    ) -> dict[str, float]:
        """Calculate performance metrics for a single factor."""
        try:
            # Historical performance from cache
            historical_data = self.factor_history.get(factor.factor_name, [])

            if len(historical_data) < 2:
                return self._default_factor_performance()

            # Extract recent scores and contributions
            recent_scores = [d.get("score", 0) for d in historical_data[-20:]]
            recent_contributions = [
                d.get("contribution", 0) for d in historical_data[-20:]
            ]

            # Calculate performance metrics
            return {
                "avg_score": float(np.mean(recent_scores)),
                "score_volatility": float(np.std(recent_scores)),
                "avg_contribution": float(np.mean(recent_contributions)),
                "contribution_consistency": float(
                    1
                    - np.std(recent_contributions)
                    / (abs(np.mean(recent_contributions)) + 0.001),
                ),
                "score_trend": self._calculate_trend(recent_scores),
                "contribution_trend": self._calculate_trend(recent_contributions),
                "factor_efficiency": self._calculate_factor_efficiency(
                    factor,
                    historical_data,
                ),
                "signal_accuracy": self._calculate_signal_accuracy(
                    factor,
                    historical_data,
                ),
            }

        except Exception as e:
            self.logger.warning(
                f"Factor performance calculation failed for {factor.factor_name}: {e}",
            )
            return self._default_factor_performance()

    def _calculate_trend(self, values: list[float]) -> float:
        """Calculate trend direction and strength."""
        if len(values) < 3:
            return 0.0

        try:
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values, 1)
            return float(slope)
        except:
            return 0.0

    def _calculate_factor_efficiency(
        self,
        factor: FactorAttribution,
        historical_data: list[dict[str, Any]],
    ) -> float:
        """Calculate how efficiently the factor contributes to signals."""
        if len(historical_data) < 5:
            return 0.5

        try:
            # Calculate correlation between factor score and overall signal accuracy
            factor_scores = [d.get("score", 0) for d in historical_data[-10:]]
            signal_outcomes = [
                d.get("signal_outcome", 0) for d in historical_data[-10:]
            ]  # Would be populated by backtest

            if len(set(factor_scores)) < 2 or len(set(signal_outcomes)) < 2:
                return 0.5

            correlation = np.corrcoef(factor_scores, signal_outcomes)[0, 1]
            return float(abs(correlation)) if not np.isnan(correlation) else 0.5

        except:
            return 0.5

    def _calculate_signal_accuracy(
        self,
        factor: FactorAttribution,
        historical_data: list[dict[str, Any]],
    ) -> float:
        """Calculate signal accuracy contribution for this factor."""
        if len(historical_data) < 3:
            return 0.5

        try:
            # Simplified accuracy calculation based on score consistency
            scores = [d.get("score", 0) for d in historical_data[-10:]]
            contributions = [d.get("contribution", 0) for d in historical_data[-10:]]

            # Factor that contribute consistently in same direction are more accurate
            sign_consistency = np.mean(
                [
                    1 if s * c >= 0 else 0
                    for s, c in zip(scores, contributions, strict=False)
                ],
            )

            return float(sign_consistency)

        except:
            return 0.5

    def _calculate_performance_summary(
        self,
        factors: list[FactorAttribution],
    ) -> dict[str, float]:
        """Calculate overall performance summary across all factors."""
        try:
            total_contribution = sum(abs(f.contribution) for f in factors)
            positive_contribution = sum(
                f.contribution for f in factors if f.contribution > 0
            )
            negative_contribution = sum(
                f.contribution for f in factors if f.contribution < 0
            )

            # Factor diversification (how evenly distributed are contributions)
            contributions = [abs(f.contribution) for f in factors]
            if total_contribution > 0:
                contrib_shares = [c / total_contribution for c in contributions]
                diversification = 1 - np.std(contrib_shares)
            else:
                diversification = 0.5

            # Weight efficiency (how well do weights match actual contributions)
            weight_efficiency = 0.5
            if len(factors) > 0:
                weight_contrib_corr = np.corrcoef(
                    [f.weight for f in factors],
                    [abs(f.contribution) for f in factors],
                )[0, 1]
                weight_efficiency = (
                    abs(weight_contrib_corr)
                    if not np.isnan(weight_contrib_corr)
                    else 0.5
                )

            return {
                "total_contribution": float(total_contribution),
                "positive_contribution": float(positive_contribution),
                "negative_contribution": float(negative_contribution),
                "contribution_balance": float(
                    positive_contribution / (total_contribution + 0.001),
                ),
                "factor_diversification": float(diversification),
                "weight_efficiency": float(weight_efficiency),
                "factor_count": len(factors),
                "dominant_factor": (
                    max(factors, key=lambda f: abs(f.contribution)).factor_name
                    if factors
                    else "none"
                ),
            }

        except Exception as e:
            self.logger.warning(f"Performance summary calculation failed: {e}")
            return {}

    def _store_attribution(self, attribution: AttributionResult, ticker: str) -> None:
        """Store attribution result for historical analysis."""
        try:
            # Update factor history
            for factor in attribution.factors:
                if factor.factor_name not in self.factor_history:
                    self.factor_history[factor.factor_name] = []

                factor_record = {
                    "timestamp": attribution.timestamp.isoformat(),
                    "ticker": ticker,
                    "score": factor.score,
                    "contribution": factor.contribution,
                    "weight": factor.weight,
                    "performance_metrics": factor.performance_metrics,
                }

                self.factor_history[factor.factor_name].append(factor_record)

                # Keep only recent history (last 100 records per factor)
                if len(self.factor_history[factor.factor_name]) > 100:
                    self.factor_history[factor.factor_name] = self.factor_history[
                        factor.factor_name
                    ][-100:]

            # Save attribution to file
            attribution_file = (
                self.attribution_dir
                / f"{ticker}_{attribution.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            )
            attribution_data = {
                "ticker": ticker,
                "timestamp": attribution.timestamp.isoformat(),
                "overall_score": attribution.overall_score,
                "signal": attribution.signal,
                "confidence": attribution.confidence,
                "factors": [
                    {
                        "name": f.factor_name,
                        "contribution": f.contribution,
                        "weight": f.weight,
                        "score": f.score,
                        "performance_metrics": f.performance_metrics,
                    }
                    for f in attribution.factors
                ],
                "regime_info": attribution.regime_info,
                "performance_summary": attribution.performance_summary,
            }

            with open(attribution_file, "w") as f:
                json.dump(attribution_data, f, indent=2)

        except Exception as e:
            self.logger.warning(f"Failed to store attribution: {e}")

    def get_factor_performance_report(self, lookback_days: int = 30) -> dict[str, Any]:
        """Generate comprehensive factor performance report."""
        try:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            report = {
                "report_period": f"Last {lookback_days} days",
                "generated_at": datetime.now().isoformat(),
                "factors": {},
            }

            for factor_name, history in self.factor_history.items():
                # Filter recent data
                recent_data = [
                    d
                    for d in history
                    if datetime.fromisoformat(d["timestamp"]) >= cutoff_date
                ]

                if not recent_data:
                    continue

                # Calculate aggregated metrics
                scores = [d["score"] for d in recent_data]
                contributions = [d["contribution"] for d in recent_data]

                factor_report = {
                    "sample_size": len(recent_data),
                    "avg_score": float(np.mean(scores)),
                    "score_volatility": float(np.std(scores)),
                    "avg_contribution": float(np.mean(contributions)),
                    "contribution_range": [
                        float(np.min(contributions)),
                        float(np.max(contributions)),
                    ],
                    "consistency": float(
                        1
                        - np.std(contributions) / (abs(np.mean(contributions)) + 0.001),
                    ),
                    "trend_strength": self._calculate_trend(scores),
                    "recent_performance": (
                        recent_data[-1]["performance_metrics"] if recent_data else {}
                    ),
                }

                report["factors"][factor_name] = factor_report

            return report

        except Exception as e:
            self.logger.exception(f"Factor performance report generation failed: {e}")
            return {"error": str(e)}

    def _default_attribution_result(self) -> AttributionResult:
        """Return default attribution result when analysis fails."""
        default_factors = [
            FactorAttribution("risk", 0.0, 0.28, 0.0),
            FactorAttribution("momentum", 0.0, 0.18, 0.0),
            FactorAttribution("trend", 0.0, 0.23, 0.0),
            FactorAttribution("risk_adjusted", 0.0, 0.18, 0.0),
            FactorAttribution("mean_reversion", 0.0, 0.05, 0.0),
            FactorAttribution("volume_liquidity", 0.0, 0.08, 0.0),
        ]

        return AttributionResult(
            overall_score=0.0,
            signal="HOLD",
            confidence=0.5,
            factors=default_factors,
            regime_info={"volatility_regime": "normal", "current_vix": 20.0},
        )

    def _default_factor_performance(self) -> dict[str, float]:
        """Return default factor performance metrics."""
        return {
            "avg_score": 0.0,
            "score_volatility": 1.0,
            "avg_contribution": 0.0,
            "contribution_consistency": 0.5,
            "score_trend": 0.0,
            "contribution_trend": 0.0,
            "factor_efficiency": 0.5,
            "signal_accuracy": 0.5,
        }


def create_performance_attributor(
    attribution_dir: str = "./attribution_data",
) -> PerformanceAttributor:
    """Factory function to create performance attributor."""
    return PerformanceAttributor(attribution_dir)
