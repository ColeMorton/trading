"""
Divergence Detector

Dual-layer divergence detection for asset distribution and strategy performance
analysis. Identifies statistical outliers and anomalies across multiple timeframes.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from ..config.statistical_analysis_config import SPDSConfig
from ..models.statistical_analysis_models import (
    AssetDistributionAnalysis,
    ConfidenceLevel,
    DivergenceMetrics,
    DualLayerConvergence,
    StrategyDistributionAnalysis,
)


class DivergenceDetector:
    """
    Detects statistical divergence using dual-layer analysis.

    Performs outlier detection and convergence analysis across:
    - Asset distribution layer (return distributions)
    - Strategy performance layer (equity curves or trade history)
    """

    def __init__(self, config: SPDSConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the Divergence Detector

        Args:
            config: SPDS configuration instance
            logger: Logger instance for operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Detection thresholds
        self.z_score_threshold = 2.0  # Standard z-score threshold
        self.iqr_multiplier = 1.5  # IQR outlier detection multiplier
        self.percentile_extreme_threshold = 95.0  # Extreme percentile threshold

        self.logger.info("DivergenceDetector initialized")

    async def detect_asset_divergence(
        self,
        asset_analysis: AssetDistributionAnalysis,
        current_position_data: Optional[Dict[str, Any]] = None,
    ) -> DivergenceMetrics:
        """
        Detect divergence in asset-level performance

        Args:
            asset_analysis: Asset distribution analysis results
            current_position_data: Current position data for context

        Returns:
            Divergence metrics for asset layer
        """
        try:
            # Extract current return or use most recent return
            current_return = asset_analysis.current_return
            if current_return is None and current_position_data:
                current_return = current_position_data.get("current_return", 0.0)

            if current_return is None:
                # Use median as fallback
                current_return = asset_analysis.statistics.median
                self.logger.warning(
                    f"No current return available for {asset_analysis.ticker}, using median"
                )

            # Calculate z-score
            z_score = self._calculate_z_score(
                current_return,
                asset_analysis.statistics.mean,
                asset_analysis.statistics.std,
            )

            # Calculate IQR position
            iqr_position = self._calculate_iqr_position(
                current_return,
                asset_analysis.percentiles.p25,
                asset_analysis.percentiles.p75,
            )

            # Calculate percentile rank
            percentile_rank = self._estimate_percentile_rank(
                current_return, asset_analysis.percentiles
            )

            # Assess rarity
            rarity_score = self._calculate_rarity_score(z_score, percentile_rank)

            # Outlier detection
            is_outlier, outlier_method = self._detect_outlier(
                current_return, asset_analysis.statistics, asset_analysis.percentiles
            )

            # Temporal context (simplified - would need historical data for full implementation)
            consecutive_periods = self._estimate_consecutive_periods(percentile_rank)
            trend_direction = self._determine_trend_direction(asset_analysis.statistics)

            return DivergenceMetrics(
                z_score=z_score,
                iqr_position=iqr_position,
                percentile_rank=percentile_rank,
                rarity_score=rarity_score,
                is_outlier=is_outlier,
                outlier_method=outlier_method,
                consecutive_periods_above_threshold=consecutive_periods,
                trend_direction=trend_direction,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to detect asset divergence for {asset_analysis.ticker}: {e}"
            )
            raise

    async def detect_strategy_divergence(
        self,
        strategy_analysis: StrategyDistributionAnalysis,
        current_position_data: Optional[Dict[str, Any]] = None,
    ) -> DivergenceMetrics:
        """
        Detect divergence in strategy-level performance

        Args:
            strategy_analysis: Strategy distribution analysis results
            current_position_data: Current position data for context

        Returns:
            Divergence metrics for strategy layer
        """
        try:
            # Determine current strategy performance metric
            current_performance = self._extract_current_strategy_performance(
                strategy_analysis, current_position_data
            )

            # Calculate z-score
            z_score = self._calculate_z_score(
                current_performance,
                strategy_analysis.statistics.mean,
                strategy_analysis.statistics.std,
            )

            # Calculate IQR position
            iqr_position = self._calculate_iqr_position(
                current_performance,
                strategy_analysis.percentiles.p25,
                strategy_analysis.percentiles.p75,
            )

            # Calculate percentile rank
            percentile_rank = self._estimate_percentile_rank(
                current_performance, strategy_analysis.percentiles
            )

            # Assess rarity with strategy-specific adjustments
            rarity_score = self._calculate_strategy_rarity_score(
                z_score, percentile_rank, strategy_analysis
            )

            # Outlier detection
            is_outlier, outlier_method = self._detect_outlier(
                current_performance,
                strategy_analysis.statistics,
                strategy_analysis.percentiles,
            )

            # Temporal context
            consecutive_periods = self._estimate_consecutive_periods(percentile_rank)
            trend_direction = self._determine_trend_direction(
                strategy_analysis.statistics
            )

            return DivergenceMetrics(
                z_score=z_score,
                iqr_position=iqr_position,
                percentile_rank=percentile_rank,
                rarity_score=rarity_score,
                is_outlier=is_outlier,
                outlier_method=outlier_method,
                consecutive_periods_above_threshold=consecutive_periods,
                trend_direction=trend_direction,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to detect strategy divergence for {strategy_analysis.strategy_name} "
                f"on {strategy_analysis.ticker}: {e}"
            )
            raise

    async def analyze_dual_layer_convergence(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
        asset_divergence: DivergenceMetrics,
        strategy_divergence: DivergenceMetrics,
    ) -> DualLayerConvergence:
        """
        Analyze convergence between asset and strategy layers

        Args:
            asset_analysis: Asset layer analysis
            strategy_analysis: Strategy layer analysis
            asset_divergence: Asset layer divergence metrics
            strategy_divergence: Strategy layer divergence metrics

        Returns:
            Dual-layer convergence analysis results
        """
        try:
            # Extract percentiles from divergence metrics
            asset_percentile = asset_divergence.percentile_rank
            strategy_percentile = strategy_divergence.percentile_rank

            # Calculate convergence score based on percentile alignment
            convergence_score = self._calculate_convergence_score(
                asset_percentile, strategy_percentile
            )

            # Classify convergence strength
            convergence_strength = self._classify_convergence_strength(
                convergence_score
            )

            # Multi-timeframe validation (simplified - would use actual timeframe data)
            timeframe_agreement, total_timeframes = self._analyze_timeframe_agreement(
                asset_analysis, strategy_analysis
            )

            # Cross-timeframe score
            cross_timeframe_score = timeframe_agreement / max(total_timeframes, 1)

            return DualLayerConvergence(
                asset_layer_percentile=asset_percentile,
                strategy_layer_percentile=strategy_percentile,
                convergence_score=convergence_score,
                convergence_strength=convergence_strength,
                timeframe_agreement=timeframe_agreement,
                total_timeframes=total_timeframes,
                cross_timeframe_score=cross_timeframe_score,
            )

        except Exception as e:
            self.logger.error(f"Failed to analyze dual-layer convergence: {e}")
            raise

    # Helper methods

    def _calculate_z_score(self, value: float, mean: float, std: float) -> float:
        """Calculate z-score for a value"""
        if std == 0:
            return 0.0
        return (value - mean) / std

    def _calculate_iqr_position(self, value: float, q25: float, q75: float) -> float:
        """Calculate position relative to IQR"""
        iqr = q75 - q25
        if iqr == 0:
            return 0.0

        if value < q25:
            return (value - q25) / iqr  # Negative value
        elif value > q75:
            return (value - q75) / iqr  # Positive value
        else:
            return (value - q25) / iqr - 0.5  # Normalized to [-0.5, 0.5] within IQR

    def _estimate_percentile_rank(self, value: float, percentiles: Any) -> float:
        """Estimate percentile rank for a value using available percentiles"""
        # Create interpolation points
        percentile_values = [
            (5, percentiles.p5),
            (10, percentiles.p10),
            (25, percentiles.p25),
            (50, percentiles.p50),
            (75, percentiles.p75),
            (90, percentiles.p90),
            (95, percentiles.p95),
            (99, percentiles.p99),
        ]

        # Sort by value
        percentile_values.sort(key=lambda x: x[1])

        # Handle edge cases
        if value <= percentile_values[0][1]:
            return max(percentile_values[0][0] * (value / percentile_values[0][1]), 0.0)
        if value >= percentile_values[-1][1]:
            return min(
                percentile_values[-1][0] + (100 - percentile_values[-1][0]) * 0.5, 100.0
            )

        # Linear interpolation
        for i in range(len(percentile_values) - 1):
            rank1, val1 = percentile_values[i]
            rank2, val2 = percentile_values[i + 1]

            if val1 <= value <= val2:
                if val2 == val1:
                    return rank1
                ratio = (value - val1) / (val2 - val1)
                return rank1 + ratio * (rank2 - rank1)

        return 50.0  # Fallback to median

    def _calculate_rarity_score(self, z_score: float, percentile_rank: float) -> float:
        """Calculate statistical rarity score"""
        # Combine z-score and percentile information
        z_score_weight = min(abs(z_score) / 3.0, 1.0)  # Cap at 3 sigma

        # Percentile extremity (distance from 50th percentile)
        percentile_extremity = abs(percentile_rank - 50.0) / 50.0

        # Weighted combination
        rarity_score = z_score_weight * 0.6 + percentile_extremity * 0.4

        return min(rarity_score, 1.0)

    def _calculate_strategy_rarity_score(
        self,
        z_score: float,
        percentile_rank: float,
        strategy_analysis: StrategyDistributionAnalysis,
    ) -> float:
        """Calculate strategy-specific rarity score with confidence adjustments"""
        base_rarity = self._calculate_rarity_score(z_score, percentile_rank)

        # Adjust based on confidence level
        confidence_multiplier = {
            ConfidenceLevel.HIGH: 1.0,
            ConfidenceLevel.MEDIUM: 0.9,
            ConfidenceLevel.LOW: 0.8,
        }.get(strategy_analysis.confidence_level, 0.8)

        return base_rarity * confidence_multiplier

    def _detect_outlier(
        self, value: float, statistics: Any, percentiles: Any
    ) -> Tuple[bool, str]:
        """Detect if value is a statistical outlier"""
        # Method 1: Z-score test
        z_score = self._calculate_z_score(value, statistics.mean, statistics.std)
        if abs(z_score) > self.z_score_threshold:
            return True, "z_score"

        # Method 2: IQR test
        iqr = percentiles.p75 - percentiles.p25
        lower_bound = percentiles.p25 - self.iqr_multiplier * iqr
        upper_bound = percentiles.p75 + self.iqr_multiplier * iqr

        if value < lower_bound or value > upper_bound:
            return True, "iqr"

        # Method 3: Extreme percentile test
        percentile_rank = self._estimate_percentile_rank(value, percentiles)
        if percentile_rank > self.percentile_extreme_threshold or percentile_rank < (
            100 - self.percentile_extreme_threshold
        ):
            return True, "percentile"

        return False, "none"

    def _estimate_consecutive_periods(self, percentile_rank: float) -> int:
        """Estimate consecutive periods above threshold (simplified)"""
        # Simplified estimation based on percentile extremity
        if percentile_rank > 90:
            return 3
        elif percentile_rank > 80:
            return 2
        elif percentile_rank > 70:
            return 1
        else:
            return 0

    def _determine_trend_direction(self, statistics: Any) -> str:
        """Determine trend direction based on distribution characteristics"""
        # Use skewness as trend indicator
        if statistics.skewness > 0.5:
            return "up"
        elif statistics.skewness < -0.5:
            return "down"
        else:
            return "neutral"

    def _extract_current_strategy_performance(
        self,
        strategy_analysis: StrategyDistributionAnalysis,
        current_position_data: Optional[Dict],
    ) -> float:
        """Extract current strategy performance metric"""
        # Try to get current performance from position data
        if current_position_data:
            # Look for various performance indicators
            for key in ["current_return", "unrealized_pnl_pct", "total_return_pct"]:
                if key in current_position_data:
                    return float(current_position_data[key])

        # Fallback to median performance
        return strategy_analysis.statistics.median

    def _calculate_convergence_score(
        self, asset_percentile: float, strategy_percentile: float
    ) -> float:
        """Calculate convergence score between two percentiles"""
        # Calculate absolute difference
        percentile_diff = abs(asset_percentile - strategy_percentile)

        # Convert to convergence score (0 = no convergence, 1 = perfect convergence)
        max_diff = 100.0  # Maximum possible percentile difference
        convergence_score = 1.0 - (percentile_diff / max_diff)

        return max(convergence_score, 0.0)

    def _classify_convergence_strength(self, convergence_score: float) -> str:
        """Classify convergence strength"""
        if convergence_score >= 0.85:
            return "strong"
        elif convergence_score >= 0.70:
            return "moderate"
        else:
            return "weak"

    def _analyze_timeframe_agreement(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
    ) -> Tuple[int, int]:
        """Analyze agreement across timeframes (simplified)"""
        # In a full implementation, this would analyze multiple timeframes
        # For now, return simplified agreement based on data quality

        total_timeframes = len(self.config.TIMEFRAMES)

        # Estimate agreement based on sample sizes and confidence
        if (
            asset_analysis.statistics.count >= self.config.PREFERRED_SAMPLE_SIZE
            and strategy_analysis.statistics.count >= self.config.PREFERRED_SAMPLE_SIZE
        ):
            agreement = max(total_timeframes - 1, 1)  # High agreement
        elif (
            asset_analysis.statistics.count >= self.config.MIN_SAMPLE_SIZE
            and strategy_analysis.statistics.count >= self.config.MIN_SAMPLE_SIZE
        ):
            agreement = max(total_timeframes // 2, 1)  # Moderate agreement
        else:
            agreement = 1  # Low agreement

        return agreement, total_timeframes
