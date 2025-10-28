"""
Transaction Cost Analysis Module for SPDS

This module provides transaction cost estimation and integration for the SPDS
scoring system, enabling cost-aware signal generation and turnover optimization.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any


@dataclass
class TransactionCostEstimate:
    """Transaction cost estimate for a trading signal."""

    ticker: str
    signal: str
    estimated_spread: float
    market_impact: float
    commission: float
    total_cost_bps: float
    liquidity_penalty: float
    turnover_penalty: float
    cost_adjusted_confidence: float


class TransactionCostAnalyzer:
    """
    Analyzer for transaction costs and market impact.

    Provides cost estimation and signal adjustment based on expected
    transaction costs, market liquidity, and trading frequency.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize transaction cost analyzer.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Cost model parameters
        self.base_commission_bps = 0.5  # 0.5 basis points base commission
        self.min_spread_bps = 1.0  # Minimum 1 bp spread
        self.impact_factor = 0.3  # Market impact scaling factor

        # Turnover tracking for penalty calculation
        self.signal_history: dict[str, list] = {}

    def estimate_transaction_costs(
        self,
        ticker: str,
        signal: str,
        volume_metrics: dict[str, Any],
        current_price: float = 100.0,
    ) -> TransactionCostEstimate:
        """
        Estimate transaction costs for a given signal.

        Args:
            ticker: Stock ticker
            signal: Trading signal (BUY, SELL, HOLD, etc.)
            volume_metrics: Volume and liquidity metrics
            current_price: Current stock price for cost calculation

        Returns:
            TransactionCostEstimate with detailed cost breakdown
        """
        try:
            # Extract volume metrics
            liquidity_score = volume_metrics.get("liquidity_score", 50.0)
            avg_volume = volume_metrics.get("avg_volume_20d", 1_000_000)
            relative_volume = volume_metrics.get("relative_volume", 1.0)

            # Estimate bid-ask spread based on liquidity
            estimated_spread = self._estimate_spread(liquidity_score, current_price)

            # Estimate market impact based on volume characteristics
            market_impact = self._estimate_market_impact(
                avg_volume,
                relative_volume,
                current_price,
                liquidity_score,
            )

            # Commission costs
            commission = self.base_commission_bps

            # Liquidity penalty for low-liquidity stocks
            liquidity_penalty = self._calculate_liquidity_penalty(liquidity_score)

            # Turnover penalty for frequent signals
            turnover_penalty = self._calculate_turnover_penalty(ticker, signal)

            # Total transaction cost
            total_cost_bps = (
                estimated_spread
                + market_impact
                + commission
                + liquidity_penalty
                + turnover_penalty
            )

            # Adjust confidence based on transaction costs
            cost_adjusted_confidence = self._adjust_confidence_for_costs(total_cost_bps)

            # Update signal history
            self._update_signal_history(ticker, signal)

            return TransactionCostEstimate(
                ticker=ticker,
                signal=signal,
                estimated_spread=float(estimated_spread),
                market_impact=float(market_impact),
                commission=float(commission),
                total_cost_bps=float(total_cost_bps),
                liquidity_penalty=float(liquidity_penalty),
                turnover_penalty=float(turnover_penalty),
                cost_adjusted_confidence=float(cost_adjusted_confidence),
            )

        except Exception as e:
            self.logger.exception(
                f"Transaction cost estimation failed for {ticker}: {e}"
            )
            return self._default_cost_estimate(ticker, signal)

    def _estimate_spread(self, liquidity_score: float, price: float) -> float:
        """Estimate bid-ask spread in basis points."""
        # Higher liquidity = lower spread
        if liquidity_score >= 90:
            spread_bps = 1.0  # Very liquid
        elif liquidity_score >= 70:
            spread_bps = 2.0  # Liquid
        elif liquidity_score >= 50:
            spread_bps = 5.0  # Moderate liquidity
        elif liquidity_score >= 30:
            spread_bps = 10.0  # Low liquidity
        else:
            spread_bps = 20.0  # Very low liquidity

        # Price impact (lower prices tend to have higher spreads)
        if price < 5.0:
            spread_bps *= 3.0  # Penny stocks
        elif price < 20.0:
            spread_bps *= 1.5  # Low-priced stocks

        return max(self.min_spread_bps, spread_bps)

    def _estimate_market_impact(
        self,
        avg_volume: float,
        relative_volume: float,
        price: float,
        liquidity_score: float,
    ) -> float:
        """Estimate market impact in basis points."""
        # Base impact calculation
        daily_dollar_volume = avg_volume * price

        # Impact based on dollar volume (higher volume = lower impact)
        if daily_dollar_volume > 100_000_000:  # >$100M
            base_impact = 0.5
        elif daily_dollar_volume > 10_000_000:  # >$10M
            base_impact = 1.0
        elif daily_dollar_volume > 1_000_000:  # >$1M
            base_impact = 2.0
        else:
            base_impact = 5.0

        # Adjust for relative volume (unusual volume increases impact)
        volume_adjustment = 1.0
        if relative_volume > 3.0:
            volume_adjustment = 1.5  # High unusual volume
        elif relative_volume > 2.0:
            volume_adjustment = 1.2
        elif relative_volume < 0.5:
            volume_adjustment = 1.3  # Low volume also increases impact

        # Liquidity adjustment
        liquidity_adjustment = max(0.5, 2.0 - (liquidity_score / 50.0))

        return (
            base_impact * volume_adjustment * liquidity_adjustment * self.impact_factor
        )

    def _calculate_liquidity_penalty(self, liquidity_score: float) -> float:
        """Calculate penalty for trading illiquid stocks."""
        if liquidity_score >= 70:
            return 0.0  # No penalty for liquid stocks
        if liquidity_score >= 50:
            return 1.0  # Small penalty
        if liquidity_score >= 30:
            return 3.0  # Moderate penalty
        return 6.0  # High penalty for illiquid stocks

    def _calculate_turnover_penalty(self, ticker: str, signal: str) -> float:
        """Calculate penalty for high turnover (frequent signal changes)."""
        history = self.signal_history.get(ticker, [])

        if len(history) < 2:
            return 0.0  # No penalty for first signals

        # Look at recent signal changes (last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_signals = [
            s
            for s in history
            if datetime.fromisoformat(s["timestamp"]) >= recent_cutoff
        ]

        if len(recent_signals) < 2:
            return 0.0

        # Count signal changes
        signal_changes = 0
        for i in range(1, len(recent_signals)):
            if recent_signals[i]["signal"] != recent_signals[i - 1]["signal"]:
                signal_changes += 1

        # Penalty based on frequency of changes
        if signal_changes >= 10:  # >10 changes per month
            return 8.0  # High turnover penalty
        if signal_changes >= 5:  # >5 changes per month
            return 4.0  # Moderate turnover penalty
        if signal_changes >= 3:  # >3 changes per month
            return 2.0  # Low turnover penalty
        return 0.0  # No penalty for low turnover

    def _adjust_confidence_for_costs(self, total_cost_bps: float) -> float:
        """Adjust confidence level based on transaction costs."""
        # Higher costs reduce confidence in the signal
        if total_cost_bps <= 5.0:
            adjustment = 1.0  # No adjustment for low costs
        elif total_cost_bps <= 15.0:
            adjustment = 0.95  # Small reduction
        elif total_cost_bps <= 30.0:
            adjustment = 0.90  # Moderate reduction
        elif total_cost_bps <= 50.0:
            adjustment = 0.80  # Significant reduction
        else:
            adjustment = 0.70  # Large reduction for high costs

        return adjustment

    def _update_signal_history(self, ticker: str, signal: str) -> None:
        """Update signal history for turnover tracking."""
        if ticker not in self.signal_history:
            self.signal_history[ticker] = []

        # Add new signal
        signal_record = {"timestamp": datetime.now().isoformat(), "signal": signal}
        self.signal_history[ticker].append(signal_record)

        # Keep only recent history (last 100 signals)
        if len(self.signal_history[ticker]) > 100:
            self.signal_history[ticker] = self.signal_history[ticker][-100:]

    def adjust_signal_for_costs(
        self,
        original_signal: str,
        original_confidence: float,
        cost_estimate: TransactionCostEstimate,
    ) -> tuple[str, float, str]:
        """
        Adjust trading signal based on transaction cost analysis.

        Args:
            original_signal: Original trading signal
            original_confidence: Original confidence level
            cost_estimate: Transaction cost estimate

        Returns:
            Tuple of (adjusted_signal, adjusted_confidence, reasoning)
        """
        try:
            # Apply cost-based confidence adjustment
            adjusted_confidence = (
                original_confidence * cost_estimate.cost_adjusted_confidence
            )

            # Determine if costs are too high to justify the signal
            adjusted_signal = original_signal
            reasoning_parts = []

            # High cost thresholds for signal modification
            if cost_estimate.total_cost_bps > 50.0:
                # Very high costs - consider downgrading signal
                if original_signal == "STRONG_BUY":
                    adjusted_signal = "BUY"
                    reasoning_parts.append(
                        "Downgraded STRONG_BUY due to high transaction costs",
                    )
                elif original_signal == "STRONG_SELL":
                    adjusted_signal = "SELL"
                    reasoning_parts.append(
                        "Downgraded STRONG_SELL due to high transaction costs",
                    )
                elif original_signal in ["BUY", "SELL"]:
                    adjusted_signal = "HOLD"
                    reasoning_parts.append(
                        f"Downgraded {original_signal} to HOLD due to prohibitive costs",
                    )

                adjusted_confidence *= 0.8  # Additional confidence reduction

            elif cost_estimate.total_cost_bps > 30.0:
                # Moderate costs - reduce confidence but keep signal
                reasoning_parts.append("Moderate transaction costs reduce confidence")
                adjusted_confidence *= 0.9

            # High turnover penalty
            if cost_estimate.turnover_penalty > 5.0:
                reasoning_parts.append("High turnover penalty applied")
                if adjusted_signal in ["BUY", "SELL"]:
                    adjusted_signal = "HOLD"
                    reasoning_parts.append(
                        "Signal changed to HOLD due to excessive turnover",
                    )

            # Low liquidity penalty
            if cost_estimate.liquidity_penalty > 3.0:
                reasoning_parts.append("Low liquidity increases transaction costs")

            # Ensure confidence stays within reasonable bounds
            adjusted_confidence = max(0.3, min(0.95, adjusted_confidence))

            # Build reasoning string
            cost_reasoning = f"Transaction costs: {cost_estimate.total_cost_bps:.1f}bps"
            if reasoning_parts:
                cost_reasoning += f"; {'; '.join(reasoning_parts)}"

            return adjusted_signal, adjusted_confidence, cost_reasoning

        except Exception as e:
            self.logger.exception(f"Signal adjustment failed: {e}")
            return original_signal, original_confidence, "Cost adjustment failed"

    def _default_cost_estimate(
        self,
        ticker: str,
        signal: str,
    ) -> TransactionCostEstimate:
        """Return default cost estimate when calculation fails."""
        return TransactionCostEstimate(
            ticker=ticker,
            signal=signal,
            estimated_spread=5.0,
            market_impact=2.0,
            commission=0.5,
            total_cost_bps=10.0,
            liquidity_penalty=2.0,
            turnover_penalty=0.0,
            cost_adjusted_confidence=0.9,
        )

    def get_cost_analysis_summary(self) -> dict[str, Any]:
        """Get summary of transaction cost analysis across all tickers."""
        try:
            summary = {
                "total_tickers_tracked": len(self.signal_history),
                "analysis_timestamp": datetime.now().isoformat(),
                "turnover_stats": {},
            }

            # Calculate turnover statistics
            total_signals = 0
            total_changes = 0

            for ticker, history in self.signal_history.items():
                signal_count = len(history)
                changes = 0

                for i in range(1, len(history)):
                    if history[i]["signal"] != history[i - 1]["signal"]:
                        changes += 1

                total_signals += signal_count
                total_changes += changes

                if signal_count > 1:
                    turnover_rate = changes / (signal_count - 1)
                    summary["turnover_stats"][ticker] = {
                        "signal_count": signal_count,
                        "changes": changes,
                        "turnover_rate": turnover_rate,
                    }

            summary["overall_turnover_rate"] = total_changes / max(
                1,
                total_signals - len(self.signal_history),
            )

            return summary

        except Exception as e:
            self.logger.exception(f"Cost analysis summary failed: {e}")
            return {"error": str(e)}


def create_transaction_cost_analyzer(
    logger: logging.Logger | None = None,
) -> TransactionCostAnalyzer:
    """Factory function to create transaction cost analyzer."""
    return TransactionCostAnalyzer(logger)
