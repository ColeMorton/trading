"""
Real-Time Position Analyzer

Analyzes open positions in real-time using statistical performance
divergence analysis and live market data integration.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config.statistical_analysis_config import SPDSConfig
from ..models.statistical_analysis_models import (
    RealTimePositionAnalysis,
    StatisticalAnalysisResult,
)
from ..services.statistical_analysis_service import StatisticalAnalysisService


class RealTimePositionAnalyzer:
    """
    Real-time position analysis with statistical divergence detection.

    Provides live analysis capabilities including:
    - Real-time statistical scoring of open positions
    - Multi-timeframe convergence analysis
    - Risk assessment with confidence intervals
    - Historical comparison and pattern matching
    """

    def __init__(
        self,
        config: SPDSConfig,
        statistical_service: StatisticalAnalysisService,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the Real-Time Position Analyzer

        Args:
            config: SPDS configuration instance
            statistical_service: Statistical analysis service
            logger: Logger instance for operations
        """
        self.config = config
        self.statistical_service = statistical_service
        self.logger = logger or logging.getLogger(__name__)

        # Analysis configuration
        self.analysis_cache_ttl = 30  # Cache TTL in seconds
        self.position_cache: dict[str, tuple[datetime, RealTimePositionAnalysis]] = {}

        # Risk assessment thresholds
        self.high_risk_threshold = 0.85
        self.medium_risk_threshold = 0.70
        self.confidence_threshold = 0.80

        # Performance tracking
        self.analysis_count = 0
        self.cache_hits = 0

        self.logger.info("RealTimePositionAnalyzer initialized")

    async def analyze_position_real_time(
        self,
        position_id: str,
        position_data: dict[str, Any],
        force_refresh: bool = False,
    ) -> RealTimePositionAnalysis | None:
        """
        Analyze a position in real-time with caching

        Args:
            position_id: Unique position identifier
            position_data: Current position data
            force_refresh: Force cache refresh

        Returns:
            Real-time position analysis result
        """
        try:
            # Check cache first
            if not force_refresh and position_id in self.position_cache:
                cache_time, cached_analysis = self.position_cache[position_id]
                if (
                    datetime.now() - cache_time
                ).total_seconds() < self.analysis_cache_ttl:
                    self.cache_hits += 1
                    return cached_analysis

            # Perform fresh analysis
            analysis = await self._perform_position_analysis(position_data)

            # Cache the result
            if analysis:
                self.position_cache[position_id] = (datetime.now(), analysis)

            self.analysis_count += 1
            return analysis

        except Exception as e:
            self.logger.exception(
                f"Real-time position analysis failed for {position_id}: {e}",
            )
            return None

    async def analyze_position_comprehensive(
        self,
        position_id: str,
    ) -> dict[str, Any] | None:
        """
        Perform comprehensive analysis including historical context

        Args:
            position_id: Position identifier

        Returns:
            Comprehensive analysis with historical context
        """
        try:
            # Load position data
            position_data = await self._load_position_data(position_id)
            if not position_data:
                return None

            # Basic real-time analysis
            real_time_analysis = await self.analyze_position_real_time(
                position_id,
                position_data,
                force_refresh=True,
            )

            if not real_time_analysis:
                return None

            # Additional comprehensive analysis
            historical_context = await self._analyze_historical_context(position_data)
            risk_assessment = await self._perform_risk_assessment(position_data)
            pattern_analysis = await self._analyze_position_patterns(position_data)

            return {
                "real_time_analysis": real_time_analysis,
                "historical_context": historical_context,
                "risk_assessment": risk_assessment,
                "pattern_analysis": pattern_analysis,
                "analysis_metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "position_id": position_id,
                    "comprehensive_analysis": True,
                },
            }

        except Exception as e:
            self.logger.exception(
                f"Comprehensive analysis failed for {position_id}: {e}"
            )
            return None

    async def analyze_portfolio_positions(
        self,
        position_ids: list[str],
    ) -> dict[str, RealTimePositionAnalysis | None]:
        """
        Analyze multiple positions in parallel

        Args:
            position_ids: List of position identifiers

        Returns:
            Dictionary mapping position IDs to analysis results
        """
        try:
            # Create analysis tasks
            analysis_tasks = []
            for position_id in position_ids:
                position_data = await self._load_position_data(position_id)
                if position_data:
                    task = self.analyze_position_real_time(position_id, position_data)
                    analysis_tasks.append((position_id, task))

            # Execute analyses in parallel
            results: dict[str, dict[str, Any]] = {}
            if analysis_tasks:
                task_results = await asyncio.gather(
                    *[task for _, task in analysis_tasks],
                    return_exceptions=True,
                )

                for (position_id, _), result in zip(
                    analysis_tasks,
                    task_results,
                    strict=False,
                ):
                    if isinstance(result, Exception):
                        self.logger.warning(
                            f"Analysis failed for {position_id}: {result}",
                        )
                        results[position_id] = None
                    else:
                        results[position_id] = result

            return results

        except Exception as e:
            self.logger.exception(f"Portfolio analysis failed: {e}")
            return {}

    async def get_position_alerts(self, position_id: str) -> list[dict[str, Any]]:
        """
        Get real-time alerts for a position

        Args:
            position_id: Position identifier

        Returns:
            List of position alerts
        """
        try:
            position_data = await self._load_position_data(position_id)
            if not position_data:
                return []

            analysis = await self.analyze_position_real_time(position_id, position_data)
            if not analysis:
                return []

            alerts = []

            # High-priority alerts
            if analysis.dual_layer_convergence_score >= 0.90:
                alerts.append(
                    {
                        "type": "HIGH_PRIORITY",
                        "message": "Immediate exit recommended - statistical exhaustion detected",
                        "confidence": analysis.signal_confidence,
                        "urgency": "IMMEDIATE",
                    },
                )

            # Risk alerts
            if analysis.signal_confidence >= self.high_risk_threshold:
                alerts.append(
                    {
                        "type": "RISK_ALERT",
                        "message": f"High-confidence exit signal: {analysis.exit_signal}",
                        "confidence": analysis.signal_confidence,
                        "urgency": "HIGH",
                    },
                )

            # Duration alerts
            days_held = position_data.get("days_held", 0)
            if days_held > 45:
                alerts.append(
                    {
                        "type": "DURATION_ALERT",
                        "message": f"Extended holding period: {days_held} days",
                        "confidence": 0.8,
                        "urgency": "MEDIUM",
                    },
                )

            # Performance alerts
            unrealized_pnl_pct = position_data.get("unrealized_pnl_pct", 0.0)
            if unrealized_pnl_pct < -0.10:
                alerts.append(
                    {
                        "type": "PERFORMANCE_ALERT",
                        "message": f"Significant unrealized loss: {unrealized_pnl_pct:.1%}",
                        "confidence": 0.9,
                        "urgency": "HIGH",
                    },
                )

            return alerts

        except Exception as e:
            self.logger.exception(f"Alert generation failed for {position_id}: {e}")
            return []

    async def _perform_position_analysis(
        self,
        position_data: dict[str, Any],
    ) -> RealTimePositionAnalysis | None:
        """Perform core position analysis"""
        try:
            # Extract position details
            strategy_name = position_data.get("strategy_name", "UNKNOWN")
            ticker = position_data.get("ticker", "UNKNOWN")
            timeframe = position_data.get("timeframe", "D")

            # Current performance metrics
            current_performance = {
                "unrealized_pnl": position_data.get("unrealized_pnl_pct", 0.0),
                "mfe": position_data.get("mfe", 0.0),
                "mae": position_data.get("mae", 0.0),
                "days_held": position_data.get("days_held", 0),
                "current_price": position_data.get("current_price", 0.0),
                "entry_price": position_data.get("entry_price", 0.0),
            }

            # Perform statistical analysis
            statistical_result = (
                await self.statistical_service.analyze_strategy_performance(
                    strategy_name=strategy_name,
                    ticker=ticker,
                    timeframe=timeframe,
                    current_performance_data=current_performance,
                )
            )

            if not statistical_result:
                return None

            # Create real-time analysis result
            return RealTimePositionAnalysis(
                position_id=position_data.get("position_id", "unknown"),
                strategy_name=strategy_name,
                ticker=ticker,
                timeframe=timeframe,
                current_price=current_performance["current_price"],
                entry_price=current_performance["entry_price"],
                unrealized_pnl_pct=current_performance["unrealized_pnl"],
                mfe=current_performance["mfe"],
                mae=current_performance["mae"],
                days_held=current_performance["days_held"],
                dual_layer_convergence_score=statistical_result.dual_layer_convergence_score,
                asset_layer_percentile=statistical_result.asset_layer_percentile,
                strategy_layer_percentile=statistical_result.strategy_layer_percentile,
                exit_signal=statistical_result.exit_signal,
                signal_confidence=statistical_result.signal_confidence,
                exit_recommendation=statistical_result.exit_recommendation,
                target_exit_timeframe=statistical_result.target_exit_timeframe,
                statistical_significance=statistical_result.statistical_significance,
                risk_level=self._assess_position_risk_level(statistical_result),
                expected_outcome=self._predict_position_outcome(statistical_result),
                analysis_timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.exception(f"Position analysis failed: {e}")
            return None

    async def _load_position_data(self, position_id: str) -> dict[str, Any] | None:
        """Load position data from trade history"""
        try:
            # Search for position in trade history files
            positions_path = Path(self.config.TRADE_HISTORY_PATH)

            if not positions_path.exists():
                return None

            for position_file in positions_path.glob("*.csv"):
                try:
                    df = pd.read_csv(position_file)

                    # Find position by UUID
                    position_row = df[df["Position_UUID"] == position_id]

                    if not position_row.empty:
                        row = position_row.iloc[0]

                        # Extract position data
                        entry_price = row.get("Entry_Price", 0.0)
                        current_price = row.get("Current_Price", entry_price)

                        return {
                            "position_id": position_id,
                            "strategy_name": row.get("Strategy_Name", "UNKNOWN"),
                            "ticker": row.get("Ticker", "UNKNOWN"),
                            "timeframe": row.get("Timeframe", "D"),
                            "entry_price": entry_price,
                            "current_price": current_price,
                            "unrealized_pnl_pct": (
                                (current_price - entry_price) / entry_price
                                if entry_price > 0
                                else 0.0
                            ),
                            "mfe": row.get("MFE", 0.0),
                            "mae": row.get("MAE", 0.0),
                            "days_held": row.get("Days_Since_Entry", 0),
                            "position_size": row.get("Position_Size", 1.0),
                            "entry_timestamp": pd.to_datetime(
                                row.get("Entry_Date", datetime.now()),
                            ),
                        }

                except Exception as e:
                    self.logger.warning(
                        f"Failed to search position file {position_file}: {e}",
                    )

            return None

        except Exception as e:
            self.logger.exception(
                f"Position data loading failed for {position_id}: {e}"
            )
            return None

    async def _analyze_historical_context(
        self,
        position_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze historical context for the position"""
        try:
            strategy_name = position_data["strategy_name"]
            ticker = position_data["ticker"]

            # Load historical trades for this strategy/ticker combination
            historical_trades = await self._load_historical_trades(
                strategy_name,
                ticker,
            )

            if not historical_trades:
                return {"historical_data_available": False}

            # Calculate historical statistics
            returns = [trade.get("return_pct", 0.0) for trade in historical_trades]
            durations = [trade.get("duration_days", 0) for trade in historical_trades]

            return {
                "historical_data_available": True,
                "total_historical_trades": len(historical_trades),
                "average_return": np.mean(returns) if returns else 0.0,
                "average_duration": np.mean(durations) if durations else 0.0,
                "success_rate": (
                    sum(1 for r in returns if r > 0) / len(returns) if returns else 0.0
                ),
                "best_return": max(returns) if returns else 0.0,
                "worst_return": min(returns) if returns else 0.0,
                "return_volatility": np.std(returns) if returns else 0.0,
                "percentile_ranking": {
                    "25th": np.percentile(returns, 25) if returns else 0.0,
                    "50th": np.percentile(returns, 50) if returns else 0.0,
                    "75th": np.percentile(returns, 75) if returns else 0.0,
                    "90th": np.percentile(returns, 90) if returns else 0.0,
                },
            }

        except Exception as e:
            self.logger.exception(f"Historical context analysis failed: {e}")
            return {"historical_data_available": False, "error": str(e)}

    async def _perform_risk_assessment(
        self,
        position_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform comprehensive risk assessment"""
        try:
            position_data.get("unrealized_pnl_pct", 0.0)
            mfe = position_data.get("mfe", 0.0)
            mae = position_data.get("mae", 0.0)
            days_held = position_data.get("days_held", 0)

            # Calculate risk metrics
            drawdown_risk = abs(mae) if mae < 0 else 0.0
            duration_risk = min(1.0, days_held / 60.0)  # Risk increases after 60 days
            volatility_risk = abs(mfe - mae) if mfe > 0 and mae < 0 else 0.0

            # Composite risk score
            risk_score = (
                drawdown_risk * 0.4 + duration_risk * 0.3 + volatility_risk * 0.3
            )

            # Risk classification
            if risk_score >= 0.8:
                risk_level = "HIGH"
                risk_description = "High risk position requiring immediate attention"
            elif risk_score >= 0.6:
                risk_level = "MEDIUM"
                risk_description = "Moderate risk position requiring monitoring"
            else:
                risk_level = "LOW"
                risk_description = "Low risk position within normal parameters"

            return {
                "overall_risk_score": risk_score,
                "risk_level": risk_level,
                "risk_description": risk_description,
                "risk_components": {
                    "drawdown_risk": drawdown_risk,
                    "duration_risk": duration_risk,
                    "volatility_risk": volatility_risk,
                },
                "risk_recommendations": self._generate_risk_recommendations(
                    risk_level,
                    risk_score,
                ),
            }

        except Exception as e:
            self.logger.exception(f"Risk assessment failed: {e}")
            return {"overall_risk_score": 0.5, "risk_level": "UNKNOWN", "error": str(e)}

    async def _analyze_position_patterns(
        self,
        position_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze patterns in position performance"""
        try:
            # Pattern analysis would integrate with PatternRecognitionSystem
            # For now, providing simplified pattern analysis

            mfe = position_data.get("mfe", 0.0)
            mae = position_data.get("mae", 0.0)
            unrealized_pnl_pct = position_data.get("unrealized_pnl_pct", 0.0)

            # Simple pattern classification
            if mfe > 0.15 and unrealized_pnl_pct > 0.10:
                pattern_type = "strong_momentum"
                pattern_confidence = 0.8
            elif mfe > 0.10 and mae < -0.05:
                pattern_type = "volatile_performer"
                pattern_confidence = 0.7
            elif unrealized_pnl_pct > 0 and mfe / abs(mae) > 2.0:
                pattern_type = "consistent_gainer"
                pattern_confidence = 0.75
            else:
                pattern_type = "developing"
                pattern_confidence = 0.5

            return {
                "pattern_type": pattern_type,
                "pattern_confidence": pattern_confidence,
                "mfe_mae_ratio": mfe / abs(mae) if mae < 0 else float("inf"),
                "performance_trend": (
                    "positive" if unrealized_pnl_pct > 0 else "negative"
                ),
                "pattern_strength": min(
                    1.0,
                    abs(unrealized_pnl_pct) * 5,
                ),  # Scale to 0-1
            }

        except Exception as e:
            self.logger.exception(f"Pattern analysis failed: {e}")
            return {
                "pattern_type": "unknown",
                "pattern_confidence": 0.0,
                "error": str(e),
            }

    async def _load_historical_trades(
        self,
        strategy_name: str,
        ticker: str,
    ) -> list[dict[str, Any]]:
        """Load historical completed trades"""
        try:
            positions_path = Path(self.config.TRADE_HISTORY_PATH)
            historical_trades = []

            if positions_path.exists():
                for position_file in positions_path.glob("*.csv"):
                    try:
                        df = pd.read_csv(position_file)

                        # Filter for completed trades matching strategy and ticker
                        completed_trades = df[
                            (df["Strategy_Name"] == strategy_name)
                            & (df["Ticker"] == ticker)
                            & (df["Exit_Price"].notna())
                            & (df["Exit_Price"] > 0)
                        ]

                        for _, row in completed_trades.iterrows():
                            trade = {
                                "return_pct": row.get("Return", 0.0),
                                "duration_days": row.get("Duration_Days", 0),
                                "mfe": row.get("MFE", 0.0),
                                "mae": row.get("MAE", 0.0),
                                "exit_efficiency": row.get("Exit_Efficiency", 0.0),
                            }
                            historical_trades.append(trade)

                    except Exception as e:
                        self.logger.warning(
                            f"Failed to load historical trades from {position_file}: {e}",
                        )

            return historical_trades

        except Exception as e:
            self.logger.exception(f"Historical trade loading failed: {e}")
            return []

    def _assess_position_risk_level(
        self,
        statistical_result: StatisticalAnalysisResult,
    ) -> str:
        """Assess risk level based on statistical analysis"""
        if statistical_result.signal_confidence >= self.high_risk_threshold:
            return "HIGH"
        if statistical_result.signal_confidence >= self.medium_risk_threshold:
            return "MEDIUM"
        return "LOW"

    def _predict_position_outcome(
        self,
        statistical_result: StatisticalAnalysisResult,
    ) -> str:
        """Predict likely position outcome"""
        if "IMMEDIATELY" in statistical_result.exit_signal:
            return "Statistical exhaustion - immediate exit recommended"
        if "STRONG" in statistical_result.exit_signal:
            return "Near-term reversal likely - exit within 2-3 days"
        if statistical_result.exit_signal == "SELL":
            return "Moderate profit capture opportunity"
        return "Continue monitoring for optimal exit timing"

    def _generate_risk_recommendations(
        self,
        risk_level: str,
        risk_score: float,
    ) -> list[str]:
        """Generate risk-based recommendations"""
        recommendations = []

        if risk_level == "HIGH":
            recommendations.extend(
                [
                    "Consider immediate position review",
                    "Implement tighter stop-loss if not already in place",
                    "Monitor position multiple times per day",
                    "Consider partial position closure to reduce exposure",
                ],
            )
        elif risk_level == "MEDIUM":
            recommendations.extend(
                [
                    "Increase monitoring frequency",
                    "Review stop-loss levels",
                    "Consider position sizing adjustment",
                    "Monitor for exit signal upgrades",
                ],
            )
        else:
            recommendations.extend(
                [
                    "Continue standard monitoring",
                    "Maintain current position management",
                    "Monitor for statistical divergence signals",
                ],
            )

        return recommendations

    def get_analysis_stats(self) -> dict[str, Any]:
        """Get analyzer performance statistics"""
        cache_hit_rate = self.cache_hits / max(1, self.analysis_count)

        return {
            "total_analyses": self.analysis_count,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self.position_cache),
            "cache_ttl_seconds": self.analysis_cache_ttl,
        }
