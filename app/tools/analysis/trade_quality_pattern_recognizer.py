"""
Trade Quality Pattern Recognizer

Integrates pattern recognition with trade quality analysis for enhanced
decision making and statistical validation of trade outcomes.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import Any

import numpy as np

from ..analysis.pattern_recognition_system import PatternRecognitionSystem
from ..config.statistical_analysis_config import SPDSConfig


class TradeQuality(Enum):
    """Trade quality classifications"""

    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    FAILED = "failed"


@dataclass
class TradeQualityAnalysis:
    """Trade quality analysis result"""

    trade_id: str
    quality_classification: TradeQuality
    quality_score: float
    mfe_mae_ratio: float
    exit_efficiency: float
    duration_score: float
    pattern_match: str | None
    pattern_confidence: float
    risk_assessment: str
    recommendation: str
    similar_trades_count: int
    expected_outcome: str


@dataclass
class QualityPattern:
    """Quality-based pattern definition"""

    pattern_id: str
    quality_level: TradeQuality
    characteristics: dict[str, Any]
    success_indicators: list[str]
    warning_signs: list[str]
    typical_outcomes: dict[str, float]
    sample_size: int


class TradeQualityPatternRecognizer:
    """
    Recognizes trade quality patterns for enhanced decision making.

    Provides comprehensive trade quality analysis including:
    - Quality classification based on MFE/MAE ratios
    - Pattern matching with historical trades
    - Risk assessment and outcome prediction
    - Real-time quality scoring and recommendations
    """

    def __init__(
        self,
        config: SPDSConfig,
        pattern_recognition_system: PatternRecognitionSystem,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the Trade Quality Pattern Recognizer

        Args:
            config: SPDS configuration instance
            pattern_recognition_system: Pattern recognition system
            logger: Logger instance for operations
        """
        self.config = config
        self.pattern_system = pattern_recognition_system
        self.logger = logger or logging.getLogger(__name__)

        # Quality classification thresholds
        self.quality_thresholds = {
            TradeQuality.EXCELLENT: {
                "mfe_mae_ratio": 5.0,
                "exit_efficiency": 0.7,
                "min_return": 0.10,
                "max_duration": 60,
            },
            TradeQuality.GOOD: {
                "mfe_mae_ratio": 2.0,
                "exit_efficiency": 0.5,
                "min_return": 0.05,
                "max_duration": 45,
            },
            TradeQuality.AVERAGE: {
                "mfe_mae_ratio": 1.0,
                "exit_efficiency": 0.3,
                "min_return": 0.0,
                "max_duration": 40,
            },
            TradeQuality.POOR: {
                "mfe_mae_ratio": 0.5,
                "exit_efficiency": 0.2,
                "min_return": -0.05,
                "max_duration": 35,
            },
        }

        # Pattern storage
        self.quality_patterns: dict[TradeQuality, list[QualityPattern]] = {
            quality: [] for quality in TradeQuality
        }

        # Analysis cache
        self.quality_cache: dict[str, TradeQualityAnalysis] = {}

        self.logger.info("TradeQualityPatternRecognizer initialized")

    async def analyze_trade_quality(
        self,
        trade_data: dict[str, Any],
        include_pattern_matching: bool = True,
    ) -> TradeQualityAnalysis:
        """
        Analyze trade quality with pattern matching

        Args:
            trade_data: Trade performance data
            include_pattern_matching: Whether to include pattern matching

        Returns:
            Trade quality analysis result
        """
        try:
            trade_id = trade_data.get(
                "trade_id",
                trade_data.get("position_id", "unknown"),
            )

            # Check cache
            if trade_id in self.quality_cache:
                return self.quality_cache[trade_id]

            # Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(trade_data)

            # Classify trade quality
            quality_classification = self._classify_trade_quality(quality_metrics)

            # Calculate composite quality score
            quality_score = self._calculate_quality_score(
                quality_metrics,
                quality_classification,
            )

            # Pattern matching
            pattern_match = None
            pattern_confidence = 0.0
            if include_pattern_matching:
                pattern_result = await self._find_quality_patterns(
                    trade_data,
                    quality_classification,
                )
                if pattern_result:
                    pattern_match = pattern_result["pattern_name"]
                    pattern_confidence = pattern_result["confidence"]

            # Risk assessment
            risk_assessment = self._assess_trade_risk(
                quality_metrics,
                quality_classification,
            )

            # Generate recommendation
            recommendation = self._generate_quality_recommendation(
                quality_classification,
                quality_metrics,
                pattern_match,
            )

            # Find similar trades
            similar_trades_count = await self._count_similar_trades(
                trade_data,
                quality_classification,
            )

            # Predict outcome
            expected_outcome = self._predict_trade_outcome(
                quality_classification,
                quality_metrics,
                pattern_confidence,
            )

            # Create analysis result
            analysis = TradeQualityAnalysis(
                trade_id=trade_id,
                quality_classification=quality_classification,
                quality_score=quality_score,
                mfe_mae_ratio=quality_metrics["mfe_mae_ratio"],
                exit_efficiency=quality_metrics["exit_efficiency"],
                duration_score=quality_metrics["duration_score"],
                pattern_match=pattern_match,
                pattern_confidence=pattern_confidence,
                risk_assessment=risk_assessment,
                recommendation=recommendation,
                similar_trades_count=similar_trades_count,
                expected_outcome=expected_outcome,
            )

            # Cache result
            self.quality_cache[trade_id] = analysis

            return analysis

        except Exception as e:
            self.logger.exception(f"Trade quality analysis failed for {trade_id}: {e}")
            raise

    async def analyze_portfolio_quality(
        self,
        trades_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Analyze quality distribution across portfolio

        Args:
            trades_data: List of trade data

        Returns:
            Portfolio quality analysis
        """
        try:
            quality_analyses = []

            # Analyze each trade
            for trade_data in trades_data:
                analysis = await self.analyze_trade_quality(trade_data)
                quality_analyses.append(analysis)

            # Calculate portfolio quality metrics
            quality_distribution = {}
            quality_scores = []

            for analysis in quality_analyses:
                quality = analysis.quality_classification.value
                quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
                quality_scores.append(analysis.quality_score)

            # Portfolio statistics
            portfolio_stats = {
                "total_trades": len(quality_analyses),
                "quality_distribution": quality_distribution,
                "average_quality_score": (
                    np.mean(quality_scores) if quality_scores else 0
                ),
                "quality_consistency": np.std(quality_scores) if quality_scores else 0,
                "excellent_trades_pct": quality_distribution.get("excellent", 0)
                / len(quality_analyses)
                * 100,
                "poor_trades_pct": (
                    quality_distribution.get("poor", 0)
                    + quality_distribution.get("failed", 0)
                )
                / len(quality_analyses)
                * 100,
            }

            # Identify patterns in quality distribution
            quality_patterns = await self._identify_portfolio_quality_patterns(
                quality_analyses,
            )

            # Generate portfolio recommendations
            portfolio_recommendations = (
                self._generate_portfolio_quality_recommendations(
                    portfolio_stats,
                    quality_patterns,
                )
            )

            return {
                "portfolio_stats": portfolio_stats,
                "quality_patterns": quality_patterns,
                "recommendations": portfolio_recommendations,
                "individual_analyses": [
                    {
                        "trade_id": analysis.trade_id,
                        "quality": analysis.quality_classification.value,
                        "score": analysis.quality_score,
                        "recommendation": analysis.recommendation,
                    }
                    for analysis in quality_analyses
                ],
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.exception(f"Portfolio quality analysis failed: {e}")
            raise

    async def learn_quality_patterns(
        self,
        historical_trades: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Learn quality patterns from historical trades

        Args:
            historical_trades: Historical trade data with outcomes

        Returns:
            Pattern learning results
        """
        try:
            self.logger.info(
                f"Learning quality patterns from {len(historical_trades)} trades",
            )

            # Group trades by quality
            trades_by_quality = {quality: [] for quality in TradeQuality}

            for trade in historical_trades:
                quality_analysis = await self.analyze_trade_quality(
                    trade,
                    include_pattern_matching=False,
                )
                trades_by_quality[quality_analysis.quality_classification].append(trade)

            # Learn patterns for each quality level
            learned_patterns = {}

            for quality, trades in trades_by_quality.items():
                if len(trades) >= 5:  # Minimum sample size for pattern learning
                    quality_patterns = await self._learn_quality_specific_patterns(
                        quality,
                        trades,
                    )
                    learned_patterns[quality.value] = quality_patterns

                    # Store patterns
                    self.quality_patterns[quality].extend(quality_patterns)

            # Calculate learning statistics
            learning_stats = {
                "total_patterns_learned": sum(
                    len(patterns) for patterns in learned_patterns.values()
                ),
                "patterns_by_quality": {
                    quality.value: len(self.quality_patterns[quality])
                    for quality in TradeQuality
                },
                "sample_sizes": {
                    quality.value: len(trades)
                    for quality, trades in trades_by_quality.items()
                },
            }

            self.logger.info(
                f"Learned {learning_stats['total_patterns_learned']} quality patterns",
            )

            return {
                "learning_stats": learning_stats,
                "learned_patterns": learned_patterns,
                "learning_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.exception(f"Pattern learning failed: {e}")
            raise

    async def get_real_time_quality_assessment(
        self,
        current_position_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get real-time quality assessment for open position

        Args:
            current_position_data: Current position data

        Returns:
            Real-time quality assessment
        """
        try:
            # Simulate completed trade data for quality analysis
            simulated_trade_data = {
                "trade_id": current_position_data.get("position_id", "current"),
                "return_pct": current_position_data.get("unrealized_pnl_pct", 0),
                "mfe": current_position_data.get("mfe", 0),
                "mae": current_position_data.get("mae", 0),
                "duration_days": current_position_data.get("days_held", 0),
                "exit_efficiency": None,  # Cannot calculate for open position
                "strategy_name": current_position_data.get("strategy_name", "UNKNOWN"),
                "ticker": current_position_data.get("ticker", "UNKNOWN"),
            }

            # Analyze current quality
            quality_analysis = await self.analyze_trade_quality(simulated_trade_data)

            # Real-time specific assessments
            return {
                "current_quality": quality_analysis.quality_classification.value,
                "quality_score": quality_analysis.quality_score,
                "quality_trend": self._assess_quality_trend(current_position_data),
                "risk_level": quality_analysis.risk_assessment,
                "immediate_action": self._get_immediate_action_recommendation(
                    quality_analysis,
                ),
                "quality_trajectory": self._predict_quality_trajectory(
                    current_position_data,
                ),
                "pattern_confidence": quality_analysis.pattern_confidence,
                "similar_outcomes": await self._get_similar_trade_outcomes(
                    current_position_data,
                ),
            }

        except Exception as e:
            self.logger.exception(f"Real-time quality assessment failed: {e}")
            return {}

    # Helper methods

    async def _calculate_quality_metrics(
        self,
        trade_data: dict[str, Any],
    ) -> dict[str, float]:
        """Calculate quality metrics from trade data"""

        mfe = trade_data.get("mfe", 0.0)
        mae = trade_data.get("mae", 0.0)
        return_pct = trade_data.get("return_pct", 0.0)
        duration_days = trade_data.get("duration_days", 0)
        exit_efficiency = trade_data.get("exit_efficiency")

        # MFE/MAE ratio
        mfe_mae_ratio = mfe / abs(mae) if mae < 0 else float("inf") if mfe > 0 else 0

        # Duration score (optimal around 20-30 days)
        optimal_duration = 25
        duration_score = 1.0 - abs(duration_days - optimal_duration) / optimal_duration
        duration_score = max(0, min(1, duration_score))

        # Exit efficiency (default to MFE capture if not provided)
        if exit_efficiency is None and mfe > 0:
            exit_efficiency = return_pct / mfe if mfe > 0 else 0
        elif exit_efficiency is None:
            exit_efficiency = 0.5  # Default

        return {
            "mfe_mae_ratio": mfe_mae_ratio,
            "exit_efficiency": exit_efficiency,
            "duration_score": duration_score,
            "return_pct": return_pct,
            "mfe": mfe,
            "mae": mae,
            "duration_days": duration_days,
        }

    def _classify_trade_quality(
        self,
        quality_metrics: dict[str, float],
    ) -> TradeQuality:
        """Classify trade quality based on metrics"""

        mfe_mae_ratio = quality_metrics["mfe_mae_ratio"]
        exit_efficiency = quality_metrics["exit_efficiency"]
        return_pct = quality_metrics["return_pct"]
        duration_days = quality_metrics["duration_days"]

        # Check each quality level (from highest to lowest)
        for quality in [
            TradeQuality.EXCELLENT,
            TradeQuality.GOOD,
            TradeQuality.AVERAGE,
            TradeQuality.POOR,
        ]:
            thresholds = self.quality_thresholds[quality]

            criteria_met = 0
            total_criteria = 0

            # MFE/MAE ratio
            if mfe_mae_ratio >= thresholds["mfe_mae_ratio"]:
                criteria_met += 1
            total_criteria += 1

            # Exit efficiency
            if exit_efficiency >= thresholds["exit_efficiency"]:
                criteria_met += 1
            total_criteria += 1

            # Minimum return
            if return_pct >= thresholds["min_return"]:
                criteria_met += 1
            total_criteria += 1

            # Duration check (bonus criteria)
            if duration_days <= thresholds["max_duration"]:
                criteria_met += 0.5
                total_criteria += 0.5

            # Require 75% of criteria to be met
            if criteria_met / total_criteria >= 0.75:
                return quality

        return TradeQuality.FAILED

    def _calculate_quality_score(
        self,
        quality_metrics: dict[str, float],
        quality_classification: TradeQuality,
    ) -> float:
        """Calculate numerical quality score"""

        # Base score from classification
        base_scores = {
            TradeQuality.EXCELLENT: 0.9,
            TradeQuality.GOOD: 0.7,
            TradeQuality.AVERAGE: 0.5,
            TradeQuality.POOR: 0.3,
            TradeQuality.FAILED: 0.1,
        }

        base_score = base_scores[quality_classification]

        # Adjustments based on metrics
        mfe_mae_adjustment = min(0.1, quality_metrics["mfe_mae_ratio"] / 10)
        efficiency_adjustment = quality_metrics["exit_efficiency"] * 0.1
        duration_adjustment = quality_metrics["duration_score"] * 0.05

        final_score = (
            base_score
            + mfe_mae_adjustment
            + efficiency_adjustment
            + duration_adjustment
        )

        return max(0.0, min(1.0, final_score))

    async def _find_quality_patterns(
        self,
        trade_data: dict[str, Any],
        quality: TradeQuality,
    ) -> dict[str, Any] | None:
        """Find matching quality patterns"""

        quality_patterns = self.quality_patterns.get(quality, [])

        if not quality_patterns:
            return None

        # Simple pattern matching based on characteristics
        best_match = None
        best_confidence = 0

        for pattern in quality_patterns:
            confidence = self._calculate_pattern_match_confidence(trade_data, pattern)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = pattern

        if best_match and best_confidence > 0.6:
            return {
                "pattern_name": best_match.pattern_id,
                "confidence": best_confidence,
                "characteristics": best_match.characteristics,
            }

        return None

    def _calculate_pattern_match_confidence(
        self,
        trade_data: dict[str, Any],
        pattern: QualityPattern,
    ) -> float:
        """Calculate confidence in pattern match"""

        # Simple characteristic matching
        matches = 0
        total_characteristics = 0

        characteristics = pattern.characteristics

        # Strategy matching
        if "strategy_name" in characteristics and "strategy_name" in trade_data:
            total_characteristics += 1
            if trade_data["strategy_name"] == characteristics["strategy_name"]:
                matches += 1

        # Duration range matching
        if "duration_range" in characteristics and "duration_days" in trade_data:
            total_characteristics += 1
            duration_min, duration_max = characteristics["duration_range"]
            if duration_min <= trade_data.get("duration_days", 0) <= duration_max:
                matches += 1

        # Return range matching
        if "return_range" in characteristics and "return_pct" in trade_data:
            total_characteristics += 1
            return_min, return_max = characteristics["return_range"]
            if return_min <= trade_data.get("return_pct", 0) <= return_max:
                matches += 1

        return matches / total_characteristics if total_characteristics > 0 else 0

    def _assess_trade_risk(
        self,
        quality_metrics: dict[str, float],
        quality: TradeQuality,
    ) -> str:
        """Assess trade risk level"""

        if quality in [TradeQuality.EXCELLENT, TradeQuality.GOOD]:
            return "LOW"
        if quality == TradeQuality.AVERAGE:
            return "MEDIUM"
        return "HIGH"

    def _generate_quality_recommendation(
        self,
        quality: TradeQuality,
        metrics: dict[str, float],
        pattern_match: str | None,
    ) -> str:
        """Generate quality-based recommendation"""

        recommendations = {
            TradeQuality.EXCELLENT: "Capture gains immediately - statistical exhaustion likely",
            TradeQuality.GOOD: "Monitor for optimal exit - strong performance continues",
            TradeQuality.AVERAGE: "Apply standard exit criteria - average performance",
            TradeQuality.POOR: "Consider early exit - performance below expectations",
            TradeQuality.FAILED: "Exit on any favorable movement - minimize losses",
        }

        base_recommendation = recommendations[quality]

        if pattern_match:
            base_recommendation += f" (Pattern: {pattern_match})"

        return base_recommendation

    async def _count_similar_trades(
        self,
        trade_data: dict[str, Any],
        quality: TradeQuality,
    ) -> int:
        """Count similar trades in history"""
        # Simplified implementation
        return 15  # Placeholder

    def _predict_trade_outcome(
        self,
        quality: TradeQuality,
        metrics: dict[str, float],
        pattern_confidence: float,
    ) -> str:
        """Predict likely trade outcome"""

        outcomes = {
            TradeQuality.EXCELLENT: "High probability of continued strength",
            TradeQuality.GOOD: "Moderate probability of additional gains",
            TradeQuality.AVERAGE: "Neutral outcome expected",
            TradeQuality.POOR: "Risk of deterioration",
            TradeQuality.FAILED: "Likely continued underperformance",
        }

        return outcomes[quality]

    async def _identify_portfolio_quality_patterns(
        self,
        quality_analyses: list[TradeQualityAnalysis],
    ) -> dict[str, Any]:
        """Identify patterns in portfolio quality"""

        # Strategy quality patterns
        strategy_quality = {}
        for analysis in quality_analyses:
            # Would extract strategy from trade_id
            strategy = "unknown_strategy"  # Placeholder
            if strategy not in strategy_quality:
                strategy_quality[strategy] = []
            strategy_quality[strategy].append(analysis.quality_classification)

        return {
            "strategy_quality_patterns": strategy_quality,
            "quality_consistency": np.std([a.quality_score for a in quality_analyses]),
            "dominant_quality": max(
                {a.quality_classification for a in quality_analyses},
                key=[a.quality_classification for a in quality_analyses].count,
            ),
        }

    def _generate_portfolio_quality_recommendations(
        self,
        portfolio_stats: dict[str, Any],
        quality_patterns: dict[str, Any],
    ) -> list[str]:
        """Generate portfolio-level quality recommendations"""

        recommendations = []

        poor_pct = portfolio_stats.get("poor_trades_pct", 0)
        if poor_pct > 30:
            recommendations.append(
                "High percentage of poor trades - review entry criteria",
            )

        excellent_pct = portfolio_stats.get("excellent_trades_pct", 0)
        if excellent_pct < 20:
            recommendations.append(
                "Low percentage of excellent trades - optimize exit timing",
            )

        consistency = portfolio_stats.get("quality_consistency", 0)
        if consistency > 0.3:
            recommendations.append(
                "High quality variance - standardize trade management",
            )

        return recommendations

    async def _learn_quality_specific_patterns(
        self,
        quality: TradeQuality,
        trades: list[dict[str, Any]],
    ) -> list[QualityPattern]:
        """Learn patterns for specific quality level"""

        # Simplified pattern learning
        patterns = []

        if len(trades) >= 10:
            # Create a pattern based on common characteristics
            returns = [trade.get("return_pct", 0) for trade in trades]
            durations = [trade.get("duration_days", 0) for trade in trades]

            pattern = QualityPattern(
                pattern_id=f"{quality.value}_common_pattern",
                quality_level=quality,
                characteristics={
                    "return_range": (min(returns), max(returns)),
                    "duration_range": (min(durations), max(durations)),
                    "average_return": np.mean(returns),
                    "average_duration": np.mean(durations),
                },
                success_indicators=[f"Returns in {np.mean(returns):.1%} range"],
                warning_signs=[f"Duration beyond {max(durations)} days"],
                typical_outcomes={
                    "average_return": np.mean(returns),
                    "success_rate": sum(1 for r in returns if r > 0) / len(returns),
                },
                sample_size=len(trades),
            )

            patterns.append(pattern)

        return patterns

    def _assess_quality_trend(self, position_data: dict[str, Any]) -> str:
        """Assess quality trend for open position"""
        mfe = position_data.get("mfe", 0)
        mae = position_data.get("mae", 0)
        current_pnl = position_data.get("unrealized_pnl_pct", 0)

        if current_pnl > mfe * 0.8:
            return "improving"
        if current_pnl < mae * 0.8:
            return "deteriorating"
        return "stable"

    def _get_immediate_action_recommendation(
        self,
        quality_analysis: TradeQualityAnalysis,
    ) -> str:
        """Get immediate action recommendation"""
        if quality_analysis.quality_classification == TradeQuality.EXCELLENT:
            return "CAPTURE_GAINS"
        if quality_analysis.quality_classification in [
            TradeQuality.POOR,
            TradeQuality.FAILED,
        ]:
            return "CONSIDER_EXIT"
        return "MONITOR"

    def _predict_quality_trajectory(self, position_data: dict[str, Any]) -> str:
        """Predict quality trajectory"""
        days_held = position_data.get("days_held", 0)
        mfe = position_data.get("mfe", 0)

        if days_held > 30 and mfe > 0.15:
            return "likely_peak"
        if days_held < 10:
            return "developing"
        return "maturing"

    async def _get_similar_trade_outcomes(
        self,
        position_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Get outcomes of similar trades"""
        # Simplified implementation
        return {"similar_count": 12, "average_outcome": 0.087, "success_rate": 0.75}
