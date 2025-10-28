"""
Divergence Detector

Dual-layer divergence detection for asset distribution and strategy performance
analysis. Identifies statistical outliers and anomalies across multiple timeframes.
"""

import logging
from typing import Any

import numpy as np

from ..config.statistical_analysis_config import SPDSConfig
from ..models.statistical_analysis_models import (
    AssetDistributionAnalysis,
    ConfidenceLevel,
    DivergenceMetrics,
    DualLayerConvergence,
    EquityAnalysis,
    StrategyDistributionAnalysis,
    TradeHistoryAnalysis,
)


class DivergenceDetector:
    """
    Detects statistical divergence using dual-layer analysis.

    Performs outlier detection and convergence analysis across:
    - Asset distribution layer (return distributions)
    - Strategy performance layer (equity curves or trade history)
    """

    def __init__(self, config: SPDSConfig, logger: logging.Logger | None = None):
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
        current_position_data: dict[str, Any] | None = None,
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
                    f"No current return available for {asset_analysis.ticker}, using median",
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
                current_return, asset_analysis.percentiles,
            )

            # Assess rarity
            rarity_score = self._calculate_rarity_score(z_score, percentile_rank)

            # Outlier detection
            is_outlier, outlier_method = self._detect_outlier(
                current_return, asset_analysis.statistics, asset_analysis.percentiles,
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
            self.logger.exception(
                f"Failed to detect asset divergence for {asset_analysis.ticker}: {e}",
            )
            raise

    async def detect_strategy_divergence(
        self,
        strategy_analysis: StrategyDistributionAnalysis,
        current_position_data: dict[str, Any] | None = None,
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
                strategy_analysis, current_position_data,
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
                current_performance, strategy_analysis.percentiles,
            )

            # Assess rarity with strategy-specific adjustments
            rarity_score = self._calculate_strategy_rarity_score(
                z_score, percentile_rank, strategy_analysis,
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
                strategy_analysis.statistics,
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
            self.logger.exception(
                f"Failed to detect strategy divergence for {strategy_analysis.strategy_name} "
                f"on {strategy_analysis.ticker}: {e}",
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
        Enhanced analyze convergence between asset and strategy layers with triple-layer support

        Args:
            asset_analysis: Asset layer analysis
            strategy_analysis: Strategy layer analysis
            asset_divergence: Asset layer divergence metrics
            strategy_divergence: Strategy layer divergence metrics

        Returns:
            Enhanced dual-layer convergence analysis results
        """
        try:
            # Extract percentiles from divergence metrics
            asset_percentile = asset_divergence.percentile_rank
            strategy_percentile = strategy_divergence.percentile_rank

            # Calculate convergence score based on percentile alignment
            convergence_score = self._calculate_convergence_score(
                asset_percentile, strategy_percentile,
            )

            # Classify convergence strength
            convergence_strength = self._classify_convergence_strength(
                convergence_score,
            )

            # Multi-timeframe validation (simplified - would use actual timeframe data)
            timeframe_agreement, total_timeframes = self._analyze_timeframe_agreement(
                asset_analysis, strategy_analysis,
            )

            # Cross-timeframe score
            cross_timeframe_score = timeframe_agreement / max(total_timeframes, 1)

            # Enhanced multi-source convergence analysis
            trade_history_percentile = None
            equity_curve_percentile = None
            asset_trade_convergence = None
            asset_equity_convergence = None
            trade_equity_convergence = None
            triple_layer_convergence = None
            source_weights = {}
            weighted_convergence_score = convergence_score

            # Check for dual-source strategy analysis
            if (
                strategy_analysis.trade_history_analysis
                and strategy_analysis.equity_analysis
                and strategy_analysis.dual_source_convergence
            ):
                # Calculate source-specific divergence
                trade_divergence = await self.detect_trade_history_divergence(
                    strategy_analysis.trade_history_analysis, strategy_analysis,
                )
                equity_divergence = await self.detect_equity_curve_divergence(
                    strategy_analysis.equity_analysis, strategy_analysis,
                )

                trade_history_percentile = trade_divergence.percentile_rank
                equity_curve_percentile = equity_divergence.percentile_rank

                # Calculate pairwise convergences
                asset_trade_convergence = self._calculate_convergence_score(
                    asset_percentile, trade_history_percentile,
                )
                asset_equity_convergence = self._calculate_convergence_score(
                    asset_percentile, equity_curve_percentile,
                )
                trade_equity_convergence = (
                    strategy_analysis.dual_source_convergence.convergence_score
                )

                # Calculate triple-layer convergence
                triple_layer_convergence = self._calculate_triple_layer_convergence(
                    asset_percentile, trade_history_percentile, equity_curve_percentile,
                )

                # Calculate source weights based on confidence and data quality
                source_weights = self._calculate_source_weights(
                    asset_analysis,
                    strategy_analysis.trade_history_analysis,
                    strategy_analysis.equity_analysis,
                )

                # Calculate weighted convergence score
                weighted_convergence_score = self._calculate_weighted_convergence(
                    convergence_score,
                    source_weights,
                    asset_trade_convergence,
                    asset_equity_convergence,
                    trade_equity_convergence,
                )

            return DualLayerConvergence(
                asset_layer_percentile=asset_percentile,
                strategy_layer_percentile=strategy_percentile,
                trade_history_percentile=trade_history_percentile,
                equity_curve_percentile=equity_curve_percentile,
                convergence_score=convergence_score,
                convergence_strength=convergence_strength,
                asset_trade_convergence=asset_trade_convergence,
                asset_equity_convergence=asset_equity_convergence,
                trade_equity_convergence=trade_equity_convergence,
                triple_layer_convergence=triple_layer_convergence,
                timeframe_agreement=timeframe_agreement,
                total_timeframes=total_timeframes,
                cross_timeframe_score=cross_timeframe_score,
                source_weights=source_weights,
                weighted_convergence_score=weighted_convergence_score,
            )

        except Exception as e:
            self.logger.exception(f"Failed to analyze dual-layer convergence: {e}")
            raise

    async def detect_trade_history_divergence(
        self,
        trade_history_analysis: TradeHistoryAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
        current_position_data: dict[str, Any] | None = None,
    ) -> DivergenceMetrics:
        """
        Detect divergence specifically in trade history analysis

        Args:
            trade_history_analysis: Trade history analysis results
            strategy_analysis: Parent strategy analysis for context
            current_position_data: Current position data for context

        Returns:
            Divergence metrics for trade history source
        """
        try:
            # Extract current performance metric from trade history
            current_performance = self._extract_current_trade_performance(
                trade_history_analysis, current_position_data,
            )

            # Calculate z-score
            z_score = self._calculate_z_score(
                current_performance,
                trade_history_analysis.statistics.mean,
                trade_history_analysis.statistics.std,
            )

            # Calculate IQR position
            iqr_position = self._calculate_iqr_position(
                current_performance,
                trade_history_analysis.percentiles.p25,
                trade_history_analysis.percentiles.p75,
            )

            # Calculate percentile rank
            percentile_rank = self._estimate_percentile_rank(
                current_performance, trade_history_analysis.percentiles,
            )

            # Assess rarity with trade-specific adjustments
            rarity_score = self._calculate_trade_history_rarity_score(
                z_score, percentile_rank, trade_history_analysis,
            )

            # Outlier detection
            is_outlier, outlier_method = self._detect_outlier(
                current_performance,
                trade_history_analysis.statistics,
                trade_history_analysis.percentiles,
            )

            # Temporal context
            consecutive_periods = self._estimate_consecutive_periods(percentile_rank)
            trend_direction = self._determine_trend_direction(
                trade_history_analysis.statistics,
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
            self.logger.exception(f"Failed to detect trade history divergence: {e}")
            raise

    async def detect_equity_curve_divergence(
        self,
        equity_analysis: EquityAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
        current_position_data: dict[str, Any] | None = None,
    ) -> DivergenceMetrics:
        """
        Detect divergence specifically in equity curve analysis

        Args:
            equity_analysis: Equity curve analysis results
            strategy_analysis: Parent strategy analysis for context
            current_position_data: Current position data for context

        Returns:
            Divergence metrics for equity curve source
        """
        try:
            # Extract current performance metric from equity analysis
            current_performance = self._extract_current_equity_performance(
                equity_analysis, current_position_data,
            )

            # Calculate z-score
            z_score = self._calculate_z_score(
                current_performance,
                equity_analysis.statistics.mean,
                equity_analysis.statistics.std,
            )

            # Calculate IQR position
            iqr_position = self._calculate_iqr_position(
                current_performance,
                equity_analysis.percentiles.p25,
                equity_analysis.percentiles.p75,
            )

            # Calculate percentile rank
            percentile_rank = self._estimate_percentile_rank(
                current_performance, equity_analysis.percentiles,
            )

            # Assess rarity with equity-specific adjustments
            rarity_score = self._calculate_equity_rarity_score(
                z_score, percentile_rank, equity_analysis,
            )

            # Outlier detection
            is_outlier, outlier_method = self._detect_outlier(
                current_performance,
                equity_analysis.statistics,
                equity_analysis.percentiles,
            )

            # Temporal context
            consecutive_periods = self._estimate_consecutive_periods(percentile_rank)
            trend_direction = self._determine_trend_direction(
                equity_analysis.statistics,
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
            self.logger.exception(f"Failed to detect equity curve divergence: {e}")
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
        if value > q75:
            return (value - q75) / iqr  # Positive value
        return (value - q25) / iqr - 0.5  # Normalized to [-0.5, 0.5] within IQR

    def _estimate_percentile_rank(self, value: float, data_array: np.ndarray) -> float:
        """
        Calculate percentile rank using scipy (replaces 230-line custom implementation)

        Simplified implementation using scipy.stats.percentileofscore for better
        accuracy and maintainability.
        """
        from scipy.stats import percentileofscore

        # Handle edge cases
        if not isinstance(data_array, np.ndarray) or len(data_array) == 0:
            return 50.0

        if not np.isfinite(value):
            return 50.0

        # Use scipy's percentileofscore (handles all edge cases)
        try:
            percentile = percentileofscore(data_array, value, kind="rank")
            return max(1.0, min(99.0, percentile))
        except Exception as e:
            self.logger.warning(f"Percentile calculation failed: {e}")
            return 50.0

    def _calculate_rarity_score(self, z_score: float, percentile_rank: float) -> float:
        """Calculate statistical rarity score using scipy"""
        from scipy.stats import norm

        # Handle NaN/inf values
        if not np.isfinite(z_score):
            z_score = 0.0
        if not np.isfinite(percentile_rank):
            percentile_rank = 50.0

        # Convert z-score to percentile using scipy
        norm.cdf(z_score) * 100

        # Combine z-score and empirical percentile
        z_score_weight = min(abs(z_score) / 3.0, 1.0)
        percentile_extremity = abs(percentile_rank - 50.0) / 50.0

        rarity_score = z_score_weight * 0.6 + percentile_extremity * 0.4

        return min(max(rarity_score, 0.0), 1.0)

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
        self, value: float, statistics: Any, percentiles: Any,
    ) -> tuple[bool, str]:
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
        if percentile_rank > 80:
            return 2
        if percentile_rank > 70:
            return 1
        return 0

    def _determine_trend_direction(self, statistics: Any) -> str:
        """Determine trend direction based on distribution characteristics"""
        # Use skewness as trend indicator
        if statistics.skewness > 0.5:
            return "up"
        if statistics.skewness < -0.5:
            return "down"
        return "neutral"

    def _extract_current_strategy_performance(
        self,
        strategy_analysis: StrategyDistributionAnalysis,
        current_position_data: dict | None,
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
        self, asset_percentile: float, strategy_percentile: float,
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
        if convergence_score >= 0.70:
            return "moderate"
        return "weak"

    def _analyze_timeframe_agreement(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
    ) -> tuple[int, int]:
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

    def _extract_current_trade_performance(
        self,
        trade_history_analysis: TradeHistoryAnalysis,
        current_position_data: dict | None,
    ) -> float:
        """Extract current trade performance metric"""
        # Try to get current performance from position data
        if current_position_data:
            # Look for trade-specific performance indicators
            for key in [
                "current_trade_return",
                "unrealized_pnl_pct",
                "total_return_pct",
            ]:
                if key in current_position_data:
                    return float(current_position_data[key])

        # Fallback to median trade performance
        return trade_history_analysis.statistics.median

    def _extract_current_equity_performance(
        self,
        equity_analysis: EquityAnalysis,
        current_position_data: dict | None,
    ) -> float:
        """Extract current equity curve performance metric"""
        # Try to get current performance from position data
        if current_position_data:
            # Look for equity-specific performance indicators
            for key in [
                "current_equity_return",
                "total_return_pct",
                "unrealized_pnl_pct",
            ]:
                if key in current_position_data:
                    return float(current_position_data[key])

        # Fallback to median equity performance
        return equity_analysis.statistics.median

    def _calculate_trade_history_rarity_score(
        self,
        z_score: float,
        percentile_rank: float,
        trade_history_analysis: TradeHistoryAnalysis,
    ) -> float:
        """Calculate trade history-specific rarity score with adjustments"""
        base_rarity = self._calculate_rarity_score(z_score, percentile_rank)

        # Adjust based on trade count and win rate
        trade_count_multiplier = min(1.0, trade_history_analysis.total_trades / 100.0)
        win_rate_adjustment = 1.0 + (abs(trade_history_analysis.win_rate - 0.5) * 0.2)

        # Adjust based on confidence level
        confidence_multiplier = {
            ConfidenceLevel.HIGH: 1.0,
            ConfidenceLevel.MEDIUM: 0.9,
            ConfidenceLevel.LOW: 0.8,
        }.get(trade_history_analysis.confidence_level, 0.8)

        return (
            base_rarity
            * trade_count_multiplier
            * win_rate_adjustment
            * confidence_multiplier
        )

    def _calculate_equity_rarity_score(
        self,
        z_score: float,
        percentile_rank: float,
        equity_analysis: EquityAnalysis,
    ) -> float:
        """Calculate equity curve-specific rarity score with adjustments"""
        base_rarity = self._calculate_rarity_score(z_score, percentile_rank)

        # Adjust based on Sharpe ratio and volatility
        sharpe_adjustment = 1.0 + (abs(equity_analysis.sharpe_ratio) * 0.1)
        volatility_adjustment = 1.0 + (min(equity_analysis.volatility, 1.0) * 0.1)

        # Adjust based on confidence level
        confidence_multiplier = {
            ConfidenceLevel.HIGH: 1.0,
            ConfidenceLevel.MEDIUM: 0.9,
            ConfidenceLevel.LOW: 0.8,
        }.get(equity_analysis.confidence_level, 0.8)

        return (
            base_rarity
            * sharpe_adjustment
            * volatility_adjustment
            * confidence_multiplier
        )

    def _calculate_triple_layer_convergence(
        self,
        asset_percentile: float,
        trade_history_percentile: float,
        equity_curve_percentile: float,
    ) -> float:
        """Calculate convergence score across all three layers"""
        # Calculate pairwise convergences
        asset_trade = self._calculate_convergence_score(
            asset_percentile, trade_history_percentile,
        )
        asset_equity = self._calculate_convergence_score(
            asset_percentile, equity_curve_percentile,
        )
        trade_equity = self._calculate_convergence_score(
            trade_history_percentile, equity_curve_percentile,
        )

        # Calculate overall triple convergence as weighted average
        return asset_trade * 0.4 + asset_equity * 0.3 + trade_equity * 0.3


    def _calculate_source_weights(
        self,
        asset_analysis: AssetDistributionAnalysis,
        trade_history_analysis: TradeHistoryAnalysis,
        equity_analysis: EquityAnalysis,
    ) -> dict[str, float]:
        """Calculate weights for each data source based on confidence and data quality"""
        weights = {}

        # Asset layer weight (baseline)
        asset_confidence = min(
            1.0, asset_analysis.statistics.count / self.config.PREFERRED_SAMPLE_SIZE,
        )
        weights["asset"] = asset_confidence * 0.3

        # Trade history weight
        trade_confidence = trade_history_analysis.confidence_score
        trade_count_factor = min(1.0, trade_history_analysis.total_trades / 50.0)
        weights["trade_history"] = trade_confidence * trade_count_factor * 0.4

        # Equity weight
        equity_confidence = equity_analysis.confidence_score
        sharpe_factor = min(1.0, max(0.1, abs(equity_analysis.sharpe_ratio) / 2.0))
        weights["equity"] = equity_confidence * sharpe_factor * 0.3

        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        else:
            # Fallback to equal weights
            weights = {"asset": 0.33, "trade_history": 0.34, "equity": 0.33}

        return weights

    def _calculate_weighted_convergence(
        self,
        base_convergence: float,
        source_weights: dict[str, float],
        asset_trade_convergence: float | None,
        asset_equity_convergence: float | None,
        trade_equity_convergence: float | None,
    ) -> float:
        """Calculate weighted convergence score using source reliability weights"""
        if not (
            asset_trade_convergence
            and asset_equity_convergence
            and trade_equity_convergence
        ):
            return base_convergence

        # Weight individual convergences by source reliability
        weighted_score = (
            asset_trade_convergence
            * (
                source_weights.get("asset", 0.33)
                + source_weights.get("trade_history", 0.34)
            )
            / 2.0
            + asset_equity_convergence
            * (source_weights.get("asset", 0.33) + source_weights.get("equity", 0.33))
            / 2.0
            + trade_equity_convergence
            * (
                source_weights.get("trade_history", 0.34)
                + source_weights.get("equity", 0.33)
            )
            / 2.0
        ) / 3.0

        # Combine with base convergence for stability
        final_score = base_convergence * 0.6 + weighted_score * 0.4

        return min(1.0, max(0.0, final_score))
