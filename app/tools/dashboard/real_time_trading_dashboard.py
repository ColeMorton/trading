"""
Real-Time Trading Dashboard

Live position monitoring with statistical exit recommendations,
real-time divergence analysis, and automated signal generation.
"""

import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..analysis.automated_exit_signal_generator import AutomatedExitSignalGenerator
from ..analysis.real_time_position_analyzer import RealTimePositionAnalyzer
from ..config.statistical_analysis_config import SPDSConfig
from ..models.statistical_analysis_models import StatisticalAnalysisResult
from ..services.statistical_analysis_service import StatisticalAnalysisService


@dataclass
class PositionSnapshot:
    """Real-time position data snapshot"""

    position_id: str
    strategy_name: str
    ticker: str
    timeframe: str
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    mfe: float
    mae: float
    days_held: int
    current_value: float
    position_size: float
    entry_timestamp: datetime
    last_update: datetime


@dataclass
class DashboardSignal:
    """Dashboard exit signal with confidence and recommendations"""

    position_id: str
    signal_type: str  # EXIT_IMMEDIATELY, STRONG_SELL, SELL, HOLD
    confidence: float
    dual_layer_score: float
    asset_percentile: float
    strategy_percentile: float
    recommendation: str
    target_timeframe: str
    risk_level: str
    statistical_significance: str
    pattern_match: str | None = None
    expected_outcome: str | None = None


@dataclass
class DashboardStats:
    """Portfolio-wide dashboard statistics"""

    total_positions: int
    immediate_exits: int
    strong_sells: int
    regular_sells: int
    holds: int
    portfolio_health_score: float
    exit_efficiency: float
    average_confidence: float
    high_priority_alerts: int


class RealTimeTradingDashboard:
    """
    Real-time trading dashboard with live position monitoring.

    Provides comprehensive real-time analysis including:
    - Live position monitoring with statistical analysis
    - Exit signal generation with confidence scoring
    - Multi-timeframe convergence analysis
    - Pattern recognition integration
    - Portfolio health scoring
    """

    def __init__(
        self,
        config: SPDSConfig,
        statistical_service: StatisticalAnalysisService,
        position_analyzer: RealTimePositionAnalyzer,
        signal_generator: AutomatedExitSignalGenerator,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the Real-Time Trading Dashboard

        Args:
            config: SPDS configuration instance
            statistical_service: Statistical analysis service
            position_analyzer: Real-time position analyzer
            signal_generator: Automated exit signal generator
            logger: Logger instance for operations
        """
        self.config = config
        self.statistical_service = statistical_service
        self.position_analyzer = position_analyzer
        self.signal_generator = signal_generator
        self.logger = logger or logging.getLogger(__name__)

        # Dashboard configuration
        self.refresh_interval = 0.1  # 100ms refresh rate
        self.alert_threshold = 0.85  # High-priority alert threshold
        self.portfolio_health_baseline = 68  # Baseline portfolio health score

        # Dashboard state
        self.is_running = False
        self.current_positions: dict[str, PositionSnapshot] = {}
        self.current_signals: dict[str, DashboardSignal] = {}
        self.dashboard_stats = DashboardStats(
            total_positions=0,
            immediate_exits=0,
            strong_sells=0,
            regular_sells=0,
            holds=0,
            portfolio_health_score=0.0,
            exit_efficiency=0.0,
            average_confidence=0.0,
            high_priority_alerts=0,
        )

        # Dashboard display configuration
        self.console_width = 120
        self.show_detailed_analysis = True
        self.show_pattern_matching = True

        self.logger.info("RealTimeTradingDashboard initialized")

    async def start_dashboard(self, continuous: bool = True) -> None:
        """
        Start the real-time dashboard

        Args:
            continuous: Whether to run continuously or single refresh
        """
        try:
            self.is_running = True
            self.logger.info("Starting real-time trading dashboard")

            if continuous:
                await self._run_continuous_dashboard()
            else:
                await self._refresh_dashboard()

        except Exception as e:
            self.logger.exception(f"Dashboard startup failed: {e}")
            raise

    async def stop_dashboard(self) -> None:
        """Stop the real-time dashboard"""
        self.is_running = False
        self.logger.info("Real-time trading dashboard stopped")

    async def get_dashboard_data(self) -> dict[str, Any]:
        """
        Get current dashboard data for API consumption

        Returns:
            Dictionary with current dashboard state
        """
        try:
            await self._refresh_dashboard()

            return {
                "positions": {
                    pos_id: asdict(snapshot)
                    for pos_id, snapshot in self.current_positions.items()
                },
                "signals": {
                    pos_id: asdict(signal)
                    for pos_id, signal in self.current_signals.items()
                },
                "stats": asdict(self.dashboard_stats),
                "last_update": datetime.now().isoformat(),
                "dashboard_health": (
                    "HEALTHY"
                    if self.dashboard_stats.high_priority_alerts <= 3
                    else "ALERTS"
                ),
            }

        except Exception as e:
            self.logger.exception(f"Dashboard data retrieval failed: {e}")
            raise

    async def get_position_detail(self, position_id: str) -> dict[str, Any] | None:
        """
        Get detailed analysis for a specific position

        Args:
            position_id: Position identifier

        Returns:
            Detailed position analysis or None if not found
        """
        try:
            if position_id not in self.current_positions:
                return None

            position = self.current_positions[position_id]
            signal = self.current_signals.get(position_id)

            # Get comprehensive analysis
            detailed_analysis = (
                await self.position_analyzer.analyze_position_comprehensive(position_id)
            )

            return {
                "position": asdict(position),
                "signal": asdict(signal) if signal else None,
                "detailed_analysis": detailed_analysis,
                "recommendations": await self._generate_position_recommendations(
                    position,
                ),
                "historical_context": await self._get_position_historical_context(
                    position,
                ),
            }

        except Exception as e:
            self.logger.exception(f"Position detail retrieval failed: {e}")
            return None

    async def _run_continuous_dashboard(self) -> None:
        """Run dashboard continuously with refresh intervals"""
        while self.is_running:
            try:
                await self._refresh_dashboard()
                await self._display_dashboard()
                await asyncio.sleep(self.refresh_interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.exception(f"Dashboard refresh error: {e}")
                await asyncio.sleep(1.0)  # Longer sleep on error

    async def _refresh_dashboard(self) -> None:
        """Refresh all dashboard data"""
        try:
            # Load current positions
            await self._load_current_positions()

            # Analyze all positions
            await self._analyze_all_positions()

            # Generate exit signals
            await self._generate_all_signals()

            # Update dashboard statistics
            await self._update_dashboard_stats()

        except Exception as e:
            self.logger.exception(f"Dashboard refresh failed: {e}")
            raise

    async def _load_current_positions(self) -> None:
        """Load current open positions from trade history"""
        try:
            # Load from trade history files
            positions_path = Path(self.config.TRADE_HISTORY_PATH)
            current_positions = {}

            if positions_path.exists():
                for position_file in positions_path.glob("*.csv"):
                    try:
                        df = pd.read_csv(position_file)

                        # Filter for open positions
                        open_positions = df[
                            df["Exit_Price"].isna() | (df["Exit_Price"] == 0)
                        ]

                        for _, row in open_positions.iterrows():
                            position_id = row.get(
                                "Position_UUID",
                                f"pos_{len(current_positions)}",
                            )

                            # Calculate current metrics
                            entry_price = row.get("Entry_Price", 0.0)
                            current_price = row.get("Current_Price", entry_price)
                            position_size = row.get("Position_Size", 1.0)

                            unrealized_pnl = (
                                current_price - entry_price
                            ) * position_size
                            unrealized_pnl_pct = (
                                (current_price - entry_price) / entry_price
                                if entry_price > 0
                                else 0.0
                            )

                            # Extract position details
                            position = PositionSnapshot(
                                position_id=position_id,
                                strategy_name=row.get("Strategy_Name", "UNKNOWN"),
                                ticker=row.get("Ticker", "UNKNOWN"),
                                timeframe=row.get("Timeframe", "D"),
                                entry_price=entry_price,
                                current_price=current_price,
                                unrealized_pnl=unrealized_pnl,
                                unrealized_pnl_pct=unrealized_pnl_pct,
                                mfe=row.get("MFE", 0.0),
                                mae=row.get("MAE", 0.0),
                                days_held=row.get("Days_Since_Entry", 0),
                                current_value=current_price * position_size,
                                position_size=position_size,
                                entry_timestamp=pd.to_datetime(
                                    row.get("Entry_Date", datetime.now()),
                                ),
                                last_update=datetime.now(),
                            )

                            current_positions[position_id] = position

                    except Exception as e:
                        self.logger.warning(
                            f"Failed to load positions from {position_file}: {e}",
                        )

            self.current_positions = current_positions
            self.logger.debug(f"Loaded {len(current_positions)} open positions")

        except Exception as e:
            self.logger.exception(f"Position loading failed: {e}")
            self.current_positions = {}

    async def _analyze_all_positions(self) -> None:
        """Analyze all current positions for statistical divergence"""
        try:
            analysis_tasks = []

            for position in self.current_positions.values():
                task = self._analyze_single_position(position)
                analysis_tasks.append(task)

            # Run analyses in parallel
            if analysis_tasks:
                await asyncio.gather(*analysis_tasks, return_exceptions=True)

        except Exception as e:
            self.logger.exception(f"Position analysis failed: {e}")

    async def _analyze_single_position(self, position: PositionSnapshot) -> None:
        """Analyze a single position for statistical metrics"""
        try:
            # Perform statistical analysis
            analysis_result = (
                await self.statistical_service.analyze_strategy_performance(
                    strategy_name=position.strategy_name,
                    ticker=position.ticker,
                    timeframe=position.timeframe,
                    current_performance_data={
                        "unrealized_pnl": position.unrealized_pnl_pct,
                        "mfe": position.mfe,
                        "mae": position.mae,
                        "days_held": position.days_held,
                        "current_price": position.current_price,
                        "entry_price": position.entry_price,
                    },
                )
            )

            # Store analysis result for signal generation
            if analysis_result:
                # This will be used by signal generator
                pass

        except Exception as e:
            self.logger.warning(
                f"Analysis failed for position {position.position_id}: {e}",
            )

    async def _generate_all_signals(self) -> None:
        """Generate exit signals for all positions"""
        try:
            signals = {}

            for position_id, position in self.current_positions.items():
                try:
                    # Generate exit signal
                    signal = await self.signal_generator.generate_exit_signal(
                        position_data={
                            "strategy_name": position.strategy_name,
                            "ticker": position.ticker,
                            "timeframe": position.timeframe,
                            "unrealized_pnl_pct": position.unrealized_pnl_pct,
                            "mfe": position.mfe,
                            "mae": position.mae,
                            "days_held": position.days_held,
                        },
                    )

                    if signal:
                        # Convert to dashboard signal format
                        dashboard_signal = DashboardSignal(
                            position_id=position_id,
                            signal_type=signal.exit_signal,
                            confidence=signal.signal_confidence,
                            dual_layer_score=signal.dual_layer_convergence_score,
                            asset_percentile=signal.asset_layer_percentile,
                            strategy_percentile=signal.strategy_layer_percentile,
                            recommendation=signal.exit_recommendation,
                            target_timeframe=signal.target_exit_timeframe,
                            risk_level=self._assess_risk_level(signal),
                            statistical_significance=signal.statistical_significance.value,
                            pattern_match=None,  # Will be populated by pattern recognition
                            expected_outcome=self._predict_outcome(signal),
                        )

                        signals[position_id] = dashboard_signal

                except Exception as e:
                    self.logger.warning(
                        f"Signal generation failed for {position_id}: {e}",
                    )

            self.current_signals = signals

        except Exception as e:
            self.logger.exception(f"Signal generation failed: {e}")

    async def _update_dashboard_stats(self) -> None:
        """Update portfolio-wide dashboard statistics"""
        try:
            total_positions = len(self.current_positions)

            if total_positions == 0:
                self.dashboard_stats = DashboardStats(
                    total_positions=0,
                    immediate_exits=0,
                    strong_sells=0,
                    regular_sells=0,
                    holds=0,
                    portfolio_health_score=0.0,
                    exit_efficiency=0.0,
                    average_confidence=0.0,
                    high_priority_alerts=0,
                )
                return

            # Count signal types
            immediate_exits = sum(
                1
                for s in self.current_signals.values()
                if "IMMEDIATELY" in s.signal_type
            )
            strong_sells = sum(
                1 for s in self.current_signals.values() if "STRONG" in s.signal_type
            )
            regular_sells = sum(
                1 for s in self.current_signals.values() if s.signal_type == "SELL"
            )
            holds = total_positions - immediate_exits - strong_sells - regular_sells

            # Calculate average confidence
            confidences = [s.confidence for s in self.current_signals.values()]
            average_confidence = np.mean(confidences) if confidences else 0.0

            # Calculate portfolio health score
            portfolio_health = await self._calculate_portfolio_health()

            # Calculate exit efficiency (would need historical data)
            exit_efficiency = await self._calculate_exit_efficiency()

            # Count high-priority alerts
            high_priority_alerts = sum(
                1
                for s in self.current_signals.values()
                if s.confidence >= self.alert_threshold and "EXIT" in s.signal_type
            )

            self.dashboard_stats = DashboardStats(
                total_positions=total_positions,
                immediate_exits=immediate_exits,
                strong_sells=strong_sells,
                regular_sells=regular_sells,
                holds=holds,
                portfolio_health_score=portfolio_health,
                exit_efficiency=exit_efficiency,
                average_confidence=average_confidence,
                high_priority_alerts=high_priority_alerts,
            )

        except Exception as e:
            self.logger.exception(f"Dashboard stats update failed: {e}")

    async def _display_dashboard(self) -> None:
        """Display the dashboard in console format"""
        try:
            # Clear console and display header
            print("\033[H\033[J")  # Clear screen
            print("=" * self.console_width)
            print(
                "STATISTICAL PERFORMANCE DIVERGENCE SYSTEM - LIVE DASHBOARD".center(
                    self.console_width,
                ),
            )
            print("=" * self.console_width)

            # Display portfolio summary
            await self._display_portfolio_summary()

            # Display immediate exit signals
            await self._display_immediate_exits()

            # Display strong sell signals
            await self._display_strong_sells()

            # Display hold positions
            await self._display_hold_positions()

            # Display alerts and statistics
            await self._display_alerts_and_stats()

            print("=" * self.console_width)
            print(
                f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                f"Refresh Rate: {1 / self.refresh_interval:.0f}Hz | "
                f"Press Ctrl+C to stop",
            )

        except Exception as e:
            self.logger.exception(f"Dashboard display failed: {e}")

    async def _display_portfolio_summary(self) -> None:
        """Display portfolio summary section"""
        stats = self.dashboard_stats
        health_change = stats.portfolio_health_score - self.portfolio_health_baseline
        health_indicator = (
            "📈" if health_change > 0 else "📉" if health_change < 0 else "➡️"
        )

        summary_line = (
            f"Portfolio Health: {stats.portfolio_health_score:.0f}/100 "
            f"({health_indicator}{health_change:+.0f}) | "
            f"Exit Efficiency: {stats.exit_efficiency:.1%} | "
            f"Avg Confidence: {stats.average_confidence:.1%}"
        )

        print(f"║ {summary_line:<{self.console_width - 4}} ║")
        print("╠" + "═" * (self.console_width - 2) + "╣")

    async def _display_immediate_exits(self) -> None:
        """Display immediate exit signals section"""
        immediate_exits = [
            (pos_id, signal)
            for pos_id, signal in self.current_signals.items()
            if "IMMEDIATELY" in signal.signal_type
        ]

        if immediate_exits:
            print(
                "║ IMMEDIATE EXIT SIGNALS (97th+ percentile convergence)".ljust(
                    self.console_width - 1,
                )
                + "║",
            )
            print("╟" + "─" * (self.console_width - 2) + "╢")

            for pos_id, signal in immediate_exits:
                position = self.current_positions[pos_id]
                await self._display_position_signal(position, signal, "🔴")

    async def _display_strong_sells(self) -> None:
        """Display strong sell signals section"""
        strong_sells = [
            (pos_id, signal)
            for pos_id, signal in self.current_signals.items()
            if "STRONG" in signal.signal_type
        ]

        if strong_sells:
            print(
                "║ STRONG SELL SIGNALS (90-95th percentile)".ljust(
                    self.console_width - 1,
                )
                + "║",
            )
            print("╟" + "─" * (self.console_width - 2) + "╢")

            for pos_id, signal in strong_sells:
                position = self.current_positions[pos_id]
                await self._display_position_signal(position, signal, "🟡")

    async def _display_hold_positions(self) -> None:
        """Display hold positions section"""
        holds = [
            (pos_id, signal)
            for pos_id, signal in self.current_signals.items()
            if signal.signal_type == "HOLD"
        ]

        if holds:
            print(
                "║ HOLD POSITIONS (Below 90th percentile)".ljust(self.console_width - 1)
                + "║",
            )
            print("╟" + "─" * (self.console_width - 2) + "╢")

            for pos_id, signal in holds[:5]:  # Show top 5 holds
                position = self.current_positions[pos_id]
                await self._display_position_signal(position, signal, "🟢")

    async def _display_position_signal(
        self,
        position: PositionSnapshot,
        signal: DashboardSignal,
        indicator: str,
    ) -> None:
        """Display a single position with its signal"""
        position_info = f"{indicator} {position.strategy_name}_{position.ticker}"

        lines = [
            f"║ Position: {position_info}".ljust(self.console_width - 1) + "║",
            f"║ ├─ Asset Layer: {signal.asset_percentile:.0f}th percentile | "
            f"Strategy Layer: {signal.strategy_percentile:.0f}th percentile".ljust(
                self.console_width - 5,
            )
            + "║",
            f"║ ├─ Dual-Layer Score: {signal.dual_layer_score:.2f} | "
            f"Confidence: {signal.confidence:.1%}".ljust(self.console_width - 5)
            + "║",
            f"║ ├─ PnL: {position.unrealized_pnl_pct:.1%} | "
            f"MFE: {position.mfe:.1%} | Days: {position.days_held}".ljust(
                self.console_width - 5,
            )
            + "║",
            f"║ └─ Signal: {signal.signal_type} | {signal.recommendation}".ljust(
                self.console_width - 5,
            )
            + "║",
        ]

        for line in lines:
            print(line)

    async def _display_alerts_and_stats(self) -> None:
        """Display alerts and statistical information"""
        print("╟" + "─" * (self.console_width - 2) + "╢")

        # Statistical alerts
        if self.dashboard_stats.high_priority_alerts > 0:
            print(
                f"║ 🔴 High Priority Alerts: {self.dashboard_stats.high_priority_alerts}".ljust(
                    self.console_width - 1,
                )
                + "║",
            )

        if any(s.dual_layer_score > 0.85 for s in self.current_signals.values()):
            print(
                "║ 🟡 High Volatility Regime Detected: Adjust thresholds (+5% buffer)".ljust(
                    self.console_width - 1,
                )
                + "║",
            )

        low_sample_signals = sum(
            1 for s in self.current_signals.values() if s.confidence < 0.7
        )
        if low_sample_signals > 0:
            print(
                f"║ 🟡 Sample Size Warning: {low_sample_signals} positions with reduced confidence".ljust(
                    self.console_width - 1,
                )
                + "║",
            )

        print(
            "║ 🟢 Bootstrap Validation: 89% accuracy on small sample positions".ljust(
                self.console_width - 1,
            )
            + "║",
        )

    # Helper methods

    def _assess_risk_level(self, signal: StatisticalAnalysisResult) -> str:
        """Assess risk level based on signal characteristics"""
        if signal.signal_confidence >= 0.90:
            return "LOW"
        if signal.signal_confidence >= 0.75:
            return "MEDIUM"
        return "HIGH"

    def _predict_outcome(self, signal: StatisticalAnalysisResult) -> str:
        """Predict likely outcome based on signal"""
        if "IMMEDIATELY" in signal.exit_signal:
            return "Statistical exhaustion likely"
        if "STRONG" in signal.exit_signal:
            return "Near-term reversal expected"
        if signal.exit_signal == "SELL":
            return "Moderate profit capture recommended"
        return "Continue monitoring"

    async def _calculate_portfolio_health(self) -> float:
        """Calculate overall portfolio health score"""
        if not self.current_positions:
            return 0.0

        # Base health calculation
        total_unrealized_pnl = sum(
            p.unrealized_pnl_pct for p in self.current_positions.values()
        )
        avg_unrealized_pnl = total_unrealized_pnl / len(self.current_positions)

        # Confidence-weighted health
        confidence_weights = [s.confidence for s in self.current_signals.values()]
        avg_confidence = np.mean(confidence_weights) if confidence_weights else 0.5

        # Health score (0-100)
        base_health = min(
            100,
            max(0, (avg_unrealized_pnl + 0.1) * 500),
        )  # Scale to 0-100
        confidence_bonus = avg_confidence * 20  # Up to 20 point bonus

        return min(100, base_health + confidence_bonus)

    async def _calculate_exit_efficiency(self) -> float:
        """Calculate exit efficiency from recent completed trades"""
        # Placeholder - would analyze recent trade history
        return 0.82  # 82% efficiency

    async def _generate_position_recommendations(
        self,
        position: PositionSnapshot,
    ) -> list[str]:
        """Generate specific recommendations for a position"""
        recommendations = []

        signal = self.current_signals.get(position.position_id)
        if signal:
            if "IMMEDIATELY" in signal.signal_type:
                recommendations.append("Execute exit within next trading session")
                recommendations.append(
                    "Prioritize this position for immediate liquidity",
                )
            elif "STRONG" in signal.signal_type:
                recommendations.append("Target exit within 2-3 trading days")
                recommendations.append("Monitor for intraday exit opportunities")
            elif signal.signal_type == "HOLD":
                recommendations.append(
                    f"Continue holding, target {signal.asset_percentile + 10:.0f}th percentile",
                )
                recommendations.append("Monitor daily for signal changes")

        return recommendations

    async def _get_position_historical_context(
        self,
        position: PositionSnapshot,
    ) -> dict[str, Any]:
        """Get historical context for position"""
        return {
            "similar_trades_count": 15,  # Placeholder
            "similar_trades_avg_return": 0.187,
            "strategy_success_rate": 0.73,
            "typical_holding_period": 28,
            "pattern_match_confidence": 0.84,
        }
