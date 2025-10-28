"""
Automated Exit Signal Generator

Generates production-ready exit signals (HOLD/SELL/EXIT_IMMEDIATELY)
with confidence scoring and automated decision making.
"""

import asyncio
from datetime import datetime
from enum import Enum
import logging
from typing import Any

import numpy as np

from ..config.statistical_analysis_config import SPDSConfig
from ..models.statistical_analysis_models import StatisticalAnalysisResult
from ..services.statistical_analysis_service import StatisticalAnalysisService


class ExitSignalType(Enum):
    """Exit signal types with urgency levels"""

    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    EXIT_IMMEDIATELY = "EXIT_IMMEDIATELY"


class AutomatedExitSignalGenerator:
    """
    Generates automated exit signals with production-ready recommendations.

    Provides sophisticated signal generation including:
    - Multi-layer statistical analysis
    - Confidence-weighted decision making
    - Risk-adjusted signal classification
    - Automated recommendation generation
    """

    def __init__(
        self,
        config: SPDSConfig,
        statistical_service: StatisticalAnalysisService,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the Automated Exit Signal Generator

        Args:
            config: SPDS configuration instance
            statistical_service: Statistical analysis service
            logger: Logger instance for operations
        """
        self.config = config
        self.statistical_service = statistical_service
        self.logger = logger or logging.getLogger(__name__)

        # Signal generation thresholds
        self.exit_immediately_threshold = 0.95
        self.strong_sell_threshold = 0.85
        self.sell_threshold = 0.70

        # Confidence thresholds
        self.high_confidence_threshold = 0.90
        self.medium_confidence_threshold = 0.75
        self.low_confidence_threshold = 0.60

        # Multi-layer weighting
        self.dual_layer_weight = 0.40
        self.asset_layer_weight = 0.30
        self.strategy_layer_weight = 0.30

        # Signal tracking
        self.signals_generated = 0
        self.signal_history: list[dict[str, Any]] = []

        self.logger.info("AutomatedExitSignalGenerator initialized")

    async def generate_exit_signal(
        self,
        position_data: dict[str, Any],
        override_thresholds: dict[str, float] | None = None,
    ) -> StatisticalAnalysisResult | None:
        """
        Generate automated exit signal for a position

        Args:
            position_data: Current position data
            override_thresholds: Optional threshold overrides

        Returns:
            Statistical analysis result with exit signal
        """
        try:
            # Apply threshold overrides if provided
            thresholds = self._get_effective_thresholds(override_thresholds)

            # Perform statistical analysis
            analysis_result = (
                await self.statistical_service.analyze_strategy_performance(
                    strategy_name=position_data.get("strategy_name", "UNKNOWN"),
                    ticker=position_data.get("ticker", "UNKNOWN"),
                    timeframe=position_data.get("timeframe", "D"),
                    current_performance_data={
                        "unrealized_pnl": position_data.get("unrealized_pnl_pct", 0.0),
                        "mfe": position_data.get("mfe", 0.0),
                        "mae": position_data.get("mae", 0.0),
                        "days_held": position_data.get("days_held", 0),
                        "current_price": position_data.get("current_price", 0.0),
                        "entry_price": position_data.get("entry_price", 0.0),
                    },
                )
            )

            if not analysis_result:
                return None

            # Generate enhanced exit signal
            enhanced_signal = await self._generate_enhanced_exit_signal(
                analysis_result, position_data, thresholds
            )

            # Track signal generation
            self._track_signal_generation(enhanced_signal, position_data)

            return enhanced_signal

        except Exception as e:
            self.logger.error(f"Exit signal generation failed: {e}")
            return None

    async def generate_portfolio_signals(
        self, positions_data: list[dict[str, Any]]
    ) -> dict[str, StatisticalAnalysisResult | None]:
        """
        Generate exit signals for multiple positions

        Args:
            positions_data: List of position data dictionaries

        Returns:
            Dictionary mapping position IDs to analysis results
        """
        try:
            # Create signal generation tasks
            signal_tasks: list[tuple[str, Any]] = []
            for position_data in positions_data:
                position_id = position_data.get(
                    "position_id", f"pos_{len(signal_tasks)}"
                )
                task = self.generate_exit_signal(position_data)
                signal_tasks.append((position_id, task))

            # Execute signal generation in parallel
            results = {}
            if signal_tasks:
                task_results = await asyncio.gather(
                    *[task for _, task in signal_tasks], return_exceptions=True
                )

                for (position_id, _), result in zip(
                    signal_tasks, task_results, strict=False
                ):
                    if isinstance(result, Exception):
                        self.logger.warning(
                            f"Signal generation failed for {position_id}: {result}"
                        )
                        results[position_id] = None
                    else:
                        results[position_id] = result

            return results

        except Exception as e:
            self.logger.error(f"Portfolio signal generation failed: {e}")
            return {}

    async def generate_real_time_alerts(
        self, position_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Generate real-time alerts based on exit signals

        Args:
            position_data: Current position data

        Returns:
            List of alert dictionaries
        """
        try:
            signal_result = await self.generate_exit_signal(position_data)
            if not signal_result:
                return []

            alerts = []

            # Generate alerts based on signal strength
            if signal_result.exit_signal == ExitSignalType.EXIT_IMMEDIATELY.value:
                alerts.append(
                    {
                        "type": "IMMEDIATE_EXIT",
                        "urgency": "CRITICAL",
                        "message": f'IMMEDIATE EXIT: {position_data.get("strategy_name", "Unknown")} - {position_data.get("ticker", "Unknown")}',
                        "confidence": signal_result.signal_confidence,
                        "dual_layer_score": signal_result.dual_layer_convergence_score,
                        "recommendation": signal_result.exit_recommendation,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            elif signal_result.exit_signal == ExitSignalType.STRONG_SELL.value:
                alerts.append(
                    {
                        "type": "STRONG_SELL",
                        "urgency": "HIGH",
                        "message": f'STRONG SELL: {position_data.get("strategy_name", "Unknown")} - {position_data.get("ticker", "Unknown")}',
                        "confidence": signal_result.signal_confidence,
                        "target_timeframe": signal_result.target_exit_timeframe,
                        "recommendation": signal_result.exit_recommendation,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # Risk-based alerts
            if signal_result.signal_confidence >= self.high_confidence_threshold:
                alerts.append(
                    {
                        "type": "HIGH_CONFIDENCE_SIGNAL",
                        "urgency": "MEDIUM",
                        "message": f"High confidence exit signal: {signal_result.exit_signal}",
                        "confidence": signal_result.signal_confidence,
                        "statistical_significance": signal_result.statistical_significance.value,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            return alerts

        except Exception as e:
            self.logger.error(f"Alert generation failed: {e}")
            return []

    async def _generate_enhanced_exit_signal(
        self,
        analysis_result: StatisticalAnalysisResult,
        position_data: dict[str, Any],
        thresholds: dict[str, float],
    ) -> StatisticalAnalysisResult:
        """Generate enhanced exit signal with additional analysis"""
        try:
            # Calculate composite signal strength
            composite_score = await self._calculate_composite_signal_strength(
                analysis_result, position_data
            )

            # Determine exit signal based on composite score
            exit_signal = self._classify_exit_signal(composite_score, thresholds)

            # Generate recommendation and timeframe
            recommendation, timeframe = self._generate_recommendation_and_timeframe(
                exit_signal, composite_score, analysis_result
            )

            # Create enhanced result
            enhanced_result = StatisticalAnalysisResult(
                strategy_name=analysis_result.strategy_name,
                ticker=analysis_result.ticker,
                timeframe=analysis_result.timeframe,
                analysis_timestamp=datetime.now(),
                sample_size=analysis_result.sample_size,
                sample_size_confidence=analysis_result.sample_size_confidence,
                dual_layer_convergence_score=analysis_result.dual_layer_convergence_score,
                asset_layer_percentile=analysis_result.asset_layer_percentile,
                strategy_layer_percentile=analysis_result.strategy_layer_percentile,
                exit_signal=exit_signal,
                signal_confidence=composite_score,
                exit_recommendation=recommendation,
                target_exit_timeframe=timeframe,
                statistical_significance=analysis_result.statistical_significance,
                p_value=analysis_result.p_value,
                divergence_metrics=analysis_result.divergence_metrics,
                performance_metrics=analysis_result.performance_metrics,
            )

            return enhanced_result

        except Exception as e:
            self.logger.error(f"Enhanced signal generation failed: {e}")
            return analysis_result

    async def _calculate_composite_signal_strength(
        self, analysis_result: StatisticalAnalysisResult, position_data: dict[str, Any]
    ) -> float:
        """Calculate composite signal strength from multiple factors"""
        try:
            # Base statistical signals
            dual_layer_score = analysis_result.dual_layer_convergence_score
            asset_percentile = analysis_result.asset_layer_percentile / 100.0
            strategy_percentile = analysis_result.strategy_layer_percentile / 100.0

            # Position-specific factors
            unrealized_pnl_pct = position_data.get("unrealized_pnl_pct", 0.0)
            mfe = position_data.get("mfe", 0.0)
            mae = position_data.get("mae", 0.0)
            days_held = position_data.get("days_held", 0)

            # Performance factor (higher performance = stronger exit signal)
            performance_factor = min(1.0, max(0.0, unrealized_pnl_pct * 2 + 0.5))

            # MFE capture factor (higher MFE = stronger signal to exit)
            mfe_factor = min(1.0, mfe * 3) if mfe > 0 else 0.0

            # Duration factor (longer holding = stronger exit signal)
            duration_factor = min(1.0, days_held / 60.0)

            # Risk factor (higher MAE = stronger exit signal)
            risk_factor = min(1.0, abs(mae) * 2) if mae < 0 else 0.0

            # Composite calculation
            composite_score = (
                dual_layer_score * self.dual_layer_weight
                + asset_percentile * self.asset_layer_weight
                + strategy_percentile * self.strategy_layer_weight
            )

            # Apply position-specific adjustments
            position_adjustment = (
                performance_factor * 0.25
                + mfe_factor * 0.25
                + duration_factor * 0.25
                + risk_factor * 0.25
            )

            # Final composite score
            final_score = min(1.0, composite_score * 0.7 + position_adjustment * 0.3)

            return final_score

        except Exception as e:
            self.logger.error(f"Composite signal calculation failed: {e}")
            return analysis_result.dual_layer_convergence_score

    def _classify_exit_signal(
        self, composite_score: float, thresholds: dict[str, float]
    ) -> str:
        """Classify exit signal based on composite score"""
        if composite_score >= thresholds["exit_immediately"]:
            return ExitSignalType.EXIT_IMMEDIATELY.value
        if composite_score >= thresholds["strong_sell"]:
            return ExitSignalType.STRONG_SELL.value
        if composite_score >= thresholds["sell"]:
            return ExitSignalType.SELL.value
        return ExitSignalType.HOLD.value

    def _generate_recommendation_and_timeframe(
        self,
        exit_signal: str,
        composite_score: float,
        analysis_result: StatisticalAnalysisResult,
    ) -> tuple[str, str]:
        """Generate specific recommendation and timeframe"""

        if exit_signal == ExitSignalType.EXIT_IMMEDIATELY.value:
            recommendation = (
                f"Execute immediate exit - statistical exhaustion detected "
                f"(confidence: {composite_score:.1%})"
            )
            timeframe = "Immediate (within current trading session)"

        elif exit_signal == ExitSignalType.STRONG_SELL.value:
            recommendation = (
                f"Strong sell signal - exit within 2-3 trading days "
                f"(confidence: {composite_score:.1%})"
            )
            timeframe = "2-3 trading days"

        elif exit_signal == ExitSignalType.SELL.value:
            recommendation = (
                f"Sell signal - consider exit within one week "
                f"(confidence: {composite_score:.1%})"
            )
            timeframe = "3-7 trading days"

        else:
            # Determine specific hold recommendation
            if composite_score >= 0.60:
                recommendation = (
                    f"Continue holding - monitor for signal strength increase "
                    f"(current strength: {composite_score:.1%})"
                )
            elif analysis_result.asset_layer_percentile >= 75:
                recommendation = (
                    f"Hold with caution - asset showing strength but strategy neutral "
                    f"(asset: {analysis_result.asset_layer_percentile:.0f}th percentile)"
                )
            else:
                recommendation = (
                    f"Maintain position - continue standard monitoring "
                    f"(signal strength: {composite_score:.1%})"
                )
            timeframe = "Ongoing monitoring"

        return recommendation, timeframe

    def _get_effective_thresholds(
        self, override_thresholds: dict[str, float] | None
    ) -> dict[str, float]:
        """Get effective thresholds with overrides applied"""
        base_thresholds = {
            "exit_immediately": self.exit_immediately_threshold,
            "strong_sell": self.strong_sell_threshold,
            "sell": self.sell_threshold,
        }

        if override_thresholds:
            base_thresholds.update(override_thresholds)

        return base_thresholds

    def _track_signal_generation(
        self, signal_result: StatisticalAnalysisResult, position_data: dict[str, Any]
    ) -> None:
        """Track signal generation for analytics"""
        self.signals_generated += 1

        signal_record = {
            "timestamp": datetime.now().isoformat(),
            "strategy_name": signal_result.strategy_name,
            "ticker": signal_result.ticker,
            "exit_signal": signal_result.exit_signal,
            "confidence": signal_result.signal_confidence,
            "dual_layer_score": signal_result.dual_layer_convergence_score,
            "asset_percentile": signal_result.asset_layer_percentile,
            "strategy_percentile": signal_result.strategy_layer_percentile,
            "position_data": {
                "unrealized_pnl_pct": position_data.get("unrealized_pnl_pct", 0.0),
                "mfe": position_data.get("mfe", 0.0),
                "mae": position_data.get("mae", 0.0),
                "days_held": position_data.get("days_held", 0),
            },
        }

        # Keep only recent signal history (last 1000 signals)
        self.signal_history.append(signal_record)
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-1000:]

    def get_signal_statistics(self) -> dict[str, Any]:
        """Get signal generation statistics"""
        if not self.signal_history:
            return {
                "total_signals_generated": self.signals_generated,
                "recent_signals": 0,
                "signal_distribution": {},
                "average_confidence": 0.0,
            }

        recent_signals = self.signal_history[-100:]  # Last 100 signals

        # Signal distribution
        signal_counts = {}
        confidences = []

        for signal in recent_signals:
            signal_type = signal["exit_signal"]
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
            confidences.append(signal["confidence"])

        return {
            "total_signals_generated": self.signals_generated,
            "recent_signals": len(recent_signals),
            "signal_distribution": signal_counts,
            "average_confidence": np.mean(confidences) if confidences else 0.0,
            "high_confidence_signals": sum(
                1 for c in confidences if c >= self.high_confidence_threshold
            ),
            "immediate_exit_signals": signal_counts.get(
                ExitSignalType.EXIT_IMMEDIATELY.value, 0
            ),
            "strong_sell_signals": signal_counts.get(
                ExitSignalType.STRONG_SELL.value, 0
            ),
            "hold_signals": signal_counts.get(ExitSignalType.HOLD.value, 0),
        }

    async def optimize_thresholds(
        self, historical_performance_data: list[dict[str, Any]]
    ) -> dict[str, float]:
        """
        Optimize exit signal thresholds based on historical performance

        Args:
            historical_performance_data: Historical trade performance data

        Returns:
            Optimized threshold values
        """
        try:
            if not historical_performance_data:
                return self._get_effective_thresholds(None)

            # Analyze historical performance to optimize thresholds
            performance_by_signal = {}

            for trade in historical_performance_data:
                exit_signal = trade.get("exit_signal", "UNKNOWN")
                returns = trade.get("return_pct", 0.0)

                if exit_signal not in performance_by_signal:
                    performance_by_signal[exit_signal] = []
                performance_by_signal[exit_signal].append(returns)

            # Calculate optimal thresholds based on performance
            optimized_thresholds = {}

            # If immediate exits perform well, lower the threshold slightly
            immediate_returns = performance_by_signal.get(
                ExitSignalType.EXIT_IMMEDIATELY.value, []
            )
            if immediate_returns and np.mean(immediate_returns) > 0.15:
                optimized_thresholds["exit_immediately"] = max(
                    0.90, self.exit_immediately_threshold - 0.02
                )
            else:
                optimized_thresholds[
                    "exit_immediately"
                ] = self.exit_immediately_threshold

            # Similar logic for other signals
            strong_sell_returns = performance_by_signal.get(
                ExitSignalType.STRONG_SELL.value, []
            )
            if strong_sell_returns and np.mean(strong_sell_returns) > 0.10:
                optimized_thresholds["strong_sell"] = max(
                    0.80, self.strong_sell_threshold - 0.02
                )
            else:
                optimized_thresholds["strong_sell"] = self.strong_sell_threshold

            sell_returns = performance_by_signal.get(ExitSignalType.SELL.value, [])
            if sell_returns and np.mean(sell_returns) > 0.05:
                optimized_thresholds["sell"] = max(0.65, self.sell_threshold - 0.02)
            else:
                optimized_thresholds["sell"] = self.sell_threshold

            self.logger.info(f"Optimized thresholds: {optimized_thresholds}")

            return optimized_thresholds

        except Exception as e:
            self.logger.error(f"Threshold optimization failed: {e}")
            return self._get_effective_thresholds(None)
