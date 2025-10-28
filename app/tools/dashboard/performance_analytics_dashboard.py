"""
Performance Analytics Dashboard

Statistical performance tracking and analytics with multi-timeframe
analysis, exit efficiency monitoring, and portfolio optimization insights.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config.statistical_analysis_config import SPDSConfig
from ..services.statistical_analysis_service import StatisticalAnalysisService


@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics"""

    total_positions: int
    total_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    realized_pnl: float
    exit_efficiency: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    average_holding_days: float


@dataclass
class ExitEfficiencyAnalysis:
    """Exit efficiency analysis results"""

    current_efficiency: float
    baseline_efficiency: float
    improvement: float
    target_efficiency: float
    progress_to_target: float
    efficiency_by_strategy: dict[str, float]
    efficiency_by_timeframe: dict[str, float]
    efficiency_trend: str


@dataclass
class StatisticalDashboardData:
    """Complete dashboard data structure"""

    timestamp: datetime
    performance_metrics: PerformanceMetrics
    exit_efficiency: ExitEfficiencyAnalysis
    statistical_signals: dict[str, int]
    top_performers: list[dict[str, Any]]
    bottom_performers: list[dict[str, Any]]
    risk_alerts: list[dict[str, Any]]
    portfolio_health_score: float
    recommendations: list[str]


class PerformanceAnalyticsDashboard:
    """
    Performance analytics dashboard with statistical tracking.

    Provides comprehensive performance analytics including:
    - Multi-timeframe statistical performance tracking
    - Exit efficiency monitoring and optimization
    - Portfolio health scoring and risk analysis
    - Statistical signal distribution analysis
    - Performance attribution and recommendations
    """

    def __init__(
        self,
        config: SPDSConfig,
        statistical_service: StatisticalAnalysisService,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the Performance Analytics Dashboard

        Args:
            config: SPDS configuration instance
            statistical_service: Statistical analysis service
            logger: Logger instance for operations
        """
        self.config = config
        self.statistical_service = statistical_service
        self.logger = logger or logging.getLogger(__name__)

        # Dashboard configuration
        self.baseline_exit_efficiency = 0.57
        self.target_exit_efficiency = 0.85
        self.baseline_portfolio_health = 68

        # Analytics tracking
        self.performance_history: list[PerformanceMetrics] = []
        self.efficiency_history: list[ExitEfficiencyAnalysis] = []

        # Analytics cache
        self.cache_ttl = 300  # 5 minutes
        self.analytics_cache: dict[str, tuple[datetime, Any]] = {}

        self.logger.info("PerformanceAnalyticsDashboard initialized")

    async def get_dashboard_analytics(
        self, force_refresh: bool = False,
    ) -> StatisticalDashboardData:
        """
        Get comprehensive dashboard analytics

        Args:
            force_refresh: Force cache refresh

        Returns:
            Complete dashboard data
        """
        try:
            cache_key = "dashboard_analytics"

            # Check cache
            if not force_refresh and cache_key in self.analytics_cache:
                cache_time, cached_data = self.analytics_cache[cache_key]
                if (datetime.now() - cache_time).total_seconds() < self.cache_ttl:
                    return cached_data

            # Generate fresh analytics
            dashboard_data = await self._generate_dashboard_analytics()

            # Cache the result
            self.analytics_cache[cache_key] = (datetime.now(), dashboard_data)

            return dashboard_data

        except Exception as e:
            self.logger.exception(f"Dashboard analytics generation failed: {e}")
            raise

    async def get_exit_efficiency_analysis(self) -> ExitEfficiencyAnalysis:
        """
        Analyze exit efficiency across strategies and timeframes

        Returns:
            Exit efficiency analysis results
        """
        try:
            # Load completed trades
            completed_trades = await self._load_completed_trades()

            if not completed_trades:
                return ExitEfficiencyAnalysis(
                    current_efficiency=self.baseline_exit_efficiency,
                    baseline_efficiency=self.baseline_exit_efficiency,
                    improvement=0.0,
                    target_efficiency=self.target_exit_efficiency,
                    progress_to_target=0.0,
                    efficiency_by_strategy={},
                    efficiency_by_timeframe={},
                    efficiency_trend="stable",
                )

            # Calculate overall efficiency
            exit_efficiencies = [
                trade.get("exit_efficiency", 0.5)
                for trade in completed_trades
                if trade.get("exit_efficiency") is not None
            ]

            current_efficiency = (
                np.mean(exit_efficiencies)
                if exit_efficiencies
                else self.baseline_exit_efficiency
            )
            improvement = current_efficiency - self.baseline_exit_efficiency
            progress_to_target = improvement / (
                self.target_exit_efficiency - self.baseline_exit_efficiency
            )

            # Calculate efficiency by strategy
            efficiency_by_strategy = await self._calculate_efficiency_by_strategy(
                completed_trades,
            )

            # Calculate efficiency by timeframe
            efficiency_by_timeframe = await self._calculate_efficiency_by_timeframe(
                completed_trades,
            )

            # Determine trend
            efficiency_trend = await self._calculate_efficiency_trend(completed_trades)

            return ExitEfficiencyAnalysis(
                current_efficiency=current_efficiency,
                baseline_efficiency=self.baseline_exit_efficiency,
                improvement=improvement,
                target_efficiency=self.target_exit_efficiency,
                progress_to_target=max(0.0, min(1.0, progress_to_target)),
                efficiency_by_strategy=efficiency_by_strategy,
                efficiency_by_timeframe=efficiency_by_timeframe,
                efficiency_trend=efficiency_trend,
            )

        except Exception as e:
            self.logger.exception(f"Exit efficiency analysis failed: {e}")
            raise

    async def get_performance_attribution(self) -> dict[str, Any]:
        """
        Analyze performance attribution across strategies and assets

        Returns:
            Performance attribution analysis
        """
        try:
            # Load all position data
            await self._load_all_positions()
            completed_trades = await self._load_completed_trades()

            # Strategy attribution
            strategy_performance = defaultdict(list)
            for trade in completed_trades:
                strategy = trade.get("strategy_name", "UNKNOWN")
                returns = trade.get("return_pct", 0.0)
                strategy_performance[strategy].append(returns)

            strategy_attribution = {}
            for strategy, returns in strategy_performance.items():
                strategy_attribution[strategy] = {
                    "total_return": sum(returns),
                    "average_return": np.mean(returns),
                    "trade_count": len(returns),
                    "win_rate": (
                        sum(1 for r in returns if r > 0) / len(returns)
                        if returns
                        else 0
                    ),
                    "sharpe_ratio": self._calculate_sharpe_ratio(returns),
                }

            # Asset attribution
            asset_performance = defaultdict(list)
            for trade in completed_trades:
                ticker = trade.get("ticker", "UNKNOWN")
                returns = trade.get("return_pct", 0.0)
                asset_performance[ticker].append(returns)

            asset_attribution = {}
            for ticker, returns in asset_performance.items():
                asset_attribution[ticker] = {
                    "total_return": sum(returns),
                    "average_return": np.mean(returns),
                    "trade_count": len(returns),
                    "volatility": np.std(returns) if len(returns) > 1 else 0,
                    "max_return": max(returns) if returns else 0,
                    "min_return": min(returns) if returns else 0,
                }

            # Timeframe attribution
            timeframe_performance = defaultdict(list)
            for trade in completed_trades:
                timeframe = trade.get("timeframe", "D")
                returns = trade.get("return_pct", 0.0)
                timeframe_performance[timeframe].append(returns)

            timeframe_attribution = {}
            for timeframe, returns in timeframe_performance.items():
                timeframe_attribution[timeframe] = {
                    "total_return": sum(returns),
                    "average_return": np.mean(returns),
                    "trade_count": len(returns),
                    "efficiency": np.mean(
                        [
                            trade.get("exit_efficiency", 0.5)
                            for trade in completed_trades
                            if trade.get("timeframe") == timeframe
                        ],
                    ),
                }

            return {
                "strategy_attribution": strategy_attribution,
                "asset_attribution": asset_attribution,
                "timeframe_attribution": timeframe_attribution,
                "analysis_timestamp": datetime.now().isoformat(),
                "total_trades_analyzed": len(completed_trades),
            }

        except Exception as e:
            self.logger.exception(f"Performance attribution analysis failed: {e}")
            return {}

    async def get_statistical_signal_analysis(self) -> dict[str, Any]:
        """
        Analyze statistical signal distribution and performance

        Returns:
            Statistical signal analysis
        """
        try:
            # Load recent signals from trade history
            completed_trades = await self._load_completed_trades()

            # Analyze signal distribution
            signal_distribution: dict[str, int] = defaultdict(int)
            signal_performance = defaultdict(list)

            for trade in completed_trades:
                exit_signal = trade.get("exit_signal", "UNKNOWN")
                returns = trade.get("return_pct", 0.0)

                signal_distribution[exit_signal] += 1
                signal_performance[exit_signal].append(returns)

            # Calculate signal effectiveness
            signal_effectiveness = {}
            for signal, returns in signal_performance.items():
                if returns:
                    signal_effectiveness[signal] = {
                        "average_return": np.mean(returns),
                        "win_rate": sum(1 for r in returns if r > 0) / len(returns),
                        "total_trades": len(returns),
                        "best_return": max(returns),
                        "worst_return": min(returns),
                        "return_volatility": np.std(returns),
                    }

            # Calculate signal confidence analysis
            confidence_ranges = {
                "high_confidence": (0.85, 1.0),
                "medium_confidence": (0.70, 0.85),
                "low_confidence": (0.0, 0.70),
            }

            confidence_analysis = {}
            for range_name, (min_conf, max_conf) in confidence_ranges.items():
                range_trades = [
                    trade
                    for trade in completed_trades
                    if min_conf <= trade.get("signal_confidence", 0.5) < max_conf
                ]

                if range_trades:
                    returns = [trade.get("return_pct", 0.0) for trade in range_trades]
                    confidence_analysis[range_name] = {
                        "trade_count": len(range_trades),
                        "average_return": np.mean(returns),
                        "win_rate": sum(1 for r in returns if r > 0) / len(returns),
                        "average_confidence": np.mean(
                            [
                                trade.get("signal_confidence", 0.5)
                                for trade in range_trades
                            ],
                        ),
                    }

            return {
                "signal_distribution": dict(signal_distribution),
                "signal_effectiveness": signal_effectiveness,
                "confidence_analysis": confidence_analysis,
                "analysis_timestamp": datetime.now().isoformat(),
                "total_signals_analyzed": sum(signal_distribution.values()),
            }

        except Exception as e:
            self.logger.exception(f"Statistical signal analysis failed: {e}")
            return {}

    async def get_portfolio_health_analysis(self) -> dict[str, Any]:
        """
        Analyze portfolio health and risk metrics

        Returns:
            Portfolio health analysis
        """
        try:
            # Load current positions
            positions = await self._load_all_positions()
            completed_trades = await self._load_completed_trades()

            if not positions and not completed_trades:
                return {
                    "portfolio_health_score": 0,
                    "risk_level": "UNKNOWN",
                    "health_components": {},
                    "recommendations": [],
                }

            # Calculate health components
            health_components = {}

            # Performance component
            if completed_trades:
                recent_returns = [
                    trade.get("return_pct", 0.0)
                    for trade in completed_trades[-20:]  # Last 20 trades
                ]
                avg_return = np.mean(recent_returns) if recent_returns else 0
                health_components["performance"] = min(
                    100, max(0, (avg_return + 0.1) * 500),
                )
            else:
                health_components["performance"] = 50

            # Risk component
            if positions:
                unrealized_pnls = [
                    pos.get("unrealized_pnl_pct", 0.0) for pos in positions
                ]
                max_drawdown = min(unrealized_pnls) if unrealized_pnls else 0
                health_components["risk"] = min(
                    100, max(0, (max_drawdown + 0.2) * 250 + 50),
                )
            else:
                health_components["risk"] = 75

            # Diversification component
            if positions:
                unique_strategies = len(
                    {pos.get("strategy_name", "") for pos in positions},
                )
                unique_tickers = len({pos.get("ticker", "") for pos in positions})
                diversification_score = min(
                    100, (unique_strategies * 20) + (unique_tickers * 10),
                )
                health_components["diversification"] = diversification_score
            else:
                health_components["diversification"] = 0

            # Exit efficiency component
            exit_efficiency_analysis = await self.get_exit_efficiency_analysis()
            health_components["exit_efficiency"] = (
                exit_efficiency_analysis.current_efficiency * 100
            )

            # Calculate composite health score
            weights = {
                "performance": 0.3,
                "risk": 0.25,
                "diversification": 0.2,
                "exit_efficiency": 0.25,
            }

            portfolio_health_score = sum(
                health_components[component] * weight
                for component, weight in weights.items()
                if component in health_components
            )

            # Risk level assessment
            if portfolio_health_score >= 80:
                risk_level = "LOW"
            elif portfolio_health_score >= 60:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"

            # Generate recommendations
            recommendations = self._generate_health_recommendations(
                health_components, portfolio_health_score,
            )

            return {
                "portfolio_health_score": round(portfolio_health_score, 1),
                "risk_level": risk_level,
                "health_components": health_components,
                "recommendations": recommendations,
                "baseline_health": self.baseline_portfolio_health,
                "health_improvement": portfolio_health_score
                - self.baseline_portfolio_health,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.exception(f"Portfolio health analysis failed: {e}")
            return {}

    async def _generate_dashboard_analytics(self) -> StatisticalDashboardData:
        """Generate complete dashboard analytics"""

        # Load data
        positions = await self._load_all_positions()
        completed_trades = await self._load_completed_trades()

        # Calculate performance metrics
        performance_metrics = await self._calculate_performance_metrics(
            positions, completed_trades,
        )

        # Exit efficiency analysis
        exit_efficiency = await self.get_exit_efficiency_analysis()

        # Statistical signals distribution
        signal_analysis = await self.get_statistical_signal_analysis()
        statistical_signals = signal_analysis.get("signal_distribution", {})

        # Top and bottom performers
        top_performers = await self._identify_top_performers(completed_trades)
        bottom_performers = await self._identify_bottom_performers(completed_trades)

        # Risk alerts
        risk_alerts = await self._generate_risk_alerts(positions)

        # Portfolio health
        health_analysis = await self.get_portfolio_health_analysis()
        portfolio_health_score = health_analysis.get("portfolio_health_score", 0)

        # Recommendations
        recommendations = await self._generate_dashboard_recommendations(
            performance_metrics, exit_efficiency, health_analysis,
        )

        return StatisticalDashboardData(
            timestamp=datetime.now(),
            performance_metrics=performance_metrics,
            exit_efficiency=exit_efficiency,
            statistical_signals=statistical_signals,
            top_performers=top_performers,
            bottom_performers=bottom_performers,
            risk_alerts=risk_alerts,
            portfolio_health_score=portfolio_health_score,
            recommendations=recommendations,
        )

    async def _calculate_performance_metrics(
        self, positions: list[dict[str, Any]], completed_trades: list[dict[str, Any]],
    ) -> PerformanceMetrics:
        """Calculate portfolio performance metrics"""

        # Position metrics
        total_positions = len(positions)
        total_value = sum(pos.get("current_value", 0) for pos in positions)
        unrealized_pnl = sum(pos.get("unrealized_pnl", 0) for pos in positions)
        unrealized_pnl_pct = unrealized_pnl / total_value if total_value > 0 else 0

        # Trade metrics
        if completed_trades:
            returns = [trade.get("return_pct", 0) for trade in completed_trades]
            realized_pnl = sum(returns)
            win_rate = sum(1 for r in returns if r > 0) / len(returns)

            # Profit factor
            winning_trades = [r for r in returns if r > 0]
            losing_trades = [r for r in returns if r < 0]
            profit_factor = (
                (sum(winning_trades) / abs(sum(losing_trades)))
                if losing_trades
                else float("inf")
            )

            # Sharpe ratio
            sharpe_ratio = self._calculate_sharpe_ratio(returns)

            # Max drawdown
            max_drawdown = min(returns) if returns else 0

            # Average holding days
            durations = [trade.get("duration_days", 0) for trade in completed_trades]
            average_holding_days = np.mean(durations) if durations else 0

            # Exit efficiency
            efficiencies = [
                trade.get("exit_efficiency", 0.5)
                for trade in completed_trades
                if trade.get("exit_efficiency")
            ]
            exit_efficiency = np.mean(efficiencies) if efficiencies else 0.5
        else:
            realized_pnl = 0
            win_rate = 0
            profit_factor = 0
            sharpe_ratio = 0
            max_drawdown = 0
            average_holding_days = 0
            exit_efficiency = 0.5

        return PerformanceMetrics(
            total_positions=total_positions,
            total_value=total_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            realized_pnl=realized_pnl,
            exit_efficiency=exit_efficiency,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            average_holding_days=average_holding_days,
        )

    def _calculate_sharpe_ratio(self, returns: list[float]) -> float:
        """Calculate Sharpe ratio"""
        if not returns or len(returns) < 2:
            return 0.0

        avg_return = np.mean(returns)
        std_return = np.std(returns)

        return avg_return / std_return if std_return > 0 else 0.0

    async def _calculate_efficiency_by_strategy(
        self, completed_trades: list[dict[str, Any]],
    ) -> dict[str, float]:
        """Calculate exit efficiency by strategy"""
        strategy_efficiencies = defaultdict(list)

        for trade in completed_trades:
            strategy = trade.get("strategy_name", "UNKNOWN")
            efficiency = trade.get("exit_efficiency")
            if efficiency is not None:
                strategy_efficiencies[strategy].append(efficiency)

        return {
            strategy: np.mean(efficiencies)
            for strategy, efficiencies in strategy_efficiencies.items()
        }

    async def _calculate_efficiency_by_timeframe(
        self, completed_trades: list[dict[str, Any]],
    ) -> dict[str, float]:
        """Calculate exit efficiency by timeframe"""
        timeframe_efficiencies = defaultdict(list)

        for trade in completed_trades:
            timeframe = trade.get("timeframe", "D")
            efficiency = trade.get("exit_efficiency")
            if efficiency is not None:
                timeframe_efficiencies[timeframe].append(efficiency)

        return {
            timeframe: np.mean(efficiencies)
            for timeframe, efficiencies in timeframe_efficiencies.items()
        }

    async def _calculate_efficiency_trend(
        self, completed_trades: list[dict[str, Any]],
    ) -> str:
        """Calculate efficiency trend"""
        if len(completed_trades) < 10:
            return "insufficient_data"

        # Get efficiency for recent trades
        recent_trades = completed_trades[-10:]
        earlier_trades = (
            completed_trades[-20:-10]
            if len(completed_trades) >= 20
            else completed_trades[:-10]
        )

        recent_efficiency = np.mean(
            [
                trade.get("exit_efficiency", 0.5)
                for trade in recent_trades
                if trade.get("exit_efficiency") is not None
            ],
        )

        earlier_efficiency = np.mean(
            [
                trade.get("exit_efficiency", 0.5)
                for trade in earlier_trades
                if trade.get("exit_efficiency") is not None
            ],
        )

        if recent_efficiency > earlier_efficiency * 1.05:
            return "improving"
        if recent_efficiency < earlier_efficiency * 0.95:
            return "declining"
        return "stable"

    async def _identify_top_performers(
        self, completed_trades: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Identify top performing trades"""
        if not completed_trades:
            return []

        # Sort by return and take top 5
        sorted_trades = sorted(
            completed_trades, key=lambda x: x.get("return_pct", 0), reverse=True,
        )

        return [
            {
                "strategy_name": trade.get("strategy_name", "UNKNOWN"),
                "ticker": trade.get("ticker", "UNKNOWN"),
                "return_pct": trade.get("return_pct", 0),
                "exit_efficiency": trade.get("exit_efficiency", 0.5),
                "duration_days": trade.get("duration_days", 0),
                "exit_signal": trade.get("exit_signal", "UNKNOWN"),
            }
            for trade in sorted_trades[:5]
        ]

    async def _identify_bottom_performers(
        self, completed_trades: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Identify bottom performing trades"""
        if not completed_trades:
            return []

        # Sort by return and take bottom 5
        sorted_trades = sorted(completed_trades, key=lambda x: x.get("return_pct", 0))

        return [
            {
                "strategy_name": trade.get("strategy_name", "UNKNOWN"),
                "ticker": trade.get("ticker", "UNKNOWN"),
                "return_pct": trade.get("return_pct", 0),
                "exit_efficiency": trade.get("exit_efficiency", 0.5),
                "duration_days": trade.get("duration_days", 0),
                "exit_signal": trade.get("exit_signal", "UNKNOWN"),
            }
            for trade in sorted_trades[:5]
        ]

    async def _generate_risk_alerts(
        self, positions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate risk alerts for current positions"""
        alerts = []

        for position in positions:
            unrealized_pnl_pct = position.get("unrealized_pnl_pct", 0)
            days_held = position.get("days_held", 0)

            # Large loss alert
            if unrealized_pnl_pct < -0.15:
                alerts.append(
                    {
                        "type": "LARGE_LOSS",
                        "severity": "HIGH",
                        "position": f"{position.get('strategy_name', 'UNKNOWN')}_{position.get('ticker', 'UNKNOWN')}",
                        "message": f"Large unrealized loss: {unrealized_pnl_pct:.1%}",
                        "value": unrealized_pnl_pct,
                    },
                )

            # Extended holding alert
            if days_held > 60:
                alerts.append(
                    {
                        "type": "EXTENDED_HOLDING",
                        "severity": "MEDIUM",
                        "position": f"{position.get('strategy_name', 'UNKNOWN')}_{position.get('ticker', 'UNKNOWN')}",
                        "message": f"Extended holding period: {days_held} days",
                        "value": days_held,
                    },
                )

        return alerts

    def _generate_health_recommendations(
        self, health_components: dict[str, float], portfolio_health_score: float,
    ) -> list[str]:
        """Generate health-based recommendations"""
        recommendations = []

        if health_components.get("performance", 0) < 40:
            recommendations.append(
                "Consider reviewing strategy performance and optimizing parameters",
            )

        if health_components.get("risk", 0) < 50:
            recommendations.append(
                "High risk detected - review position sizes and stop-loss levels",
            )

        if health_components.get("diversification", 0) < 30:
            recommendations.append(
                "Increase portfolio diversification across strategies and assets",
            )

        if health_components.get("exit_efficiency", 0) < 70:
            recommendations.append(
                "Focus on improving exit timing through statistical analysis",
            )

        if portfolio_health_score < 60:
            recommendations.append(
                "Portfolio health below target - prioritize risk management",
            )

        return recommendations

    async def _generate_dashboard_recommendations(
        self,
        performance_metrics: PerformanceMetrics,
        exit_efficiency: ExitEfficiencyAnalysis,
        health_analysis: dict[str, Any],
    ) -> list[str]:
        """Generate dashboard recommendations"""
        recommendations = []

        # Exit efficiency recommendations
        if exit_efficiency.current_efficiency < exit_efficiency.target_efficiency:
            gap = exit_efficiency.target_efficiency - exit_efficiency.current_efficiency
            recommendations.append(
                f"Exit efficiency gap: {gap:.1%} - implement statistical exit signals",
            )

        # Performance recommendations
        if performance_metrics.win_rate < 0.6:
            recommendations.append(
                f"Win rate {performance_metrics.win_rate:.1%} below target - review entry criteria",
            )

        if performance_metrics.sharpe_ratio < 1.0:
            recommendations.append(
                f"Sharpe ratio {performance_metrics.sharpe_ratio:.2f} below 1.0 - optimize risk-adjusted returns",
            )

        # Health recommendations
        recommendations.extend(health_analysis.get("recommendations", []))

        return recommendations[:10]  # Limit to top 10 recommendations

    async def _load_all_positions(self) -> list[dict[str, Any]]:
        """Load all current positions"""
        # Simplified implementation - would load from actual position tracking
        return []

    async def _load_completed_trades(self) -> list[dict[str, Any]]:
        """Load completed trades from trade history"""
        completed_trades = []

        try:
            positions_path = Path(self.config.TRADE_HISTORY_PATH)

            if positions_path.exists():
                for position_file in positions_path.glob("*.csv"):
                    try:
                        df = pd.read_csv(position_file)

                        # Filter for completed trades
                        completed = df[
                            (df["Exit_Price"].notna()) & (df["Exit_Price"] > 0)
                        ]

                        for _, row in completed.iterrows():
                            trade = {
                                "strategy_name": row.get("Strategy_Name", "UNKNOWN"),
                                "ticker": row.get("Ticker", "UNKNOWN"),
                                "timeframe": row.get("Timeframe", "D"),
                                "return_pct": row.get("Return", 0.0),
                                "duration_days": row.get("Duration_Days", 0),
                                "exit_efficiency": row.get("Exit_Efficiency", None),
                                "exit_signal": row.get("Exit_Signal", "UNKNOWN"),
                                "signal_confidence": row.get("Signal_Confidence", 0.5),
                                "mfe": row.get("MFE", 0.0),
                                "mae": row.get("MAE", 0.0),
                            }
                            completed_trades.append(trade)

                    except Exception as e:
                        self.logger.warning(
                            f"Failed to load trades from {position_file}: {e}",
                        )

        except Exception as e:
            self.logger.exception(f"Trade loading failed: {e}")

        return completed_trades
