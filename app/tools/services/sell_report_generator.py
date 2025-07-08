#!/usr/bin/env python3
"""
Sell Report Generator Service

Generates comprehensive, data-driven sell signal reports utilizing all available
statistical data from the SPDS (Statistical Performance Divergence System).

Features:
- Executive summary with actionable insights
- Statistical foundation analysis
- Technical divergence assessment
- Exit strategy recommendations
- Risk management framework
- Portfolio impact analysis
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.unified_strategy_models import UnifiedStrategyData
from .signal_data_aggregator import SignalDataAggregator, StrategyData
from .strategy_data_coordinator import (
    DataCoordinationConfig,
    StrategyDataCoordinator,
    StrategyDataCoordinatorError,
)

logger = logging.getLogger(__name__)


class SellReportGenerator:
    """Generates comprehensive sell signal reports with statistical analysis using central data coordination"""

    def __init__(
        self,
        aggregator: Optional[SignalDataAggregator] = None,
        data_coordinator: Optional[StrategyDataCoordinator] = None,
        use_coordinator: bool = True,
    ):
        """Initialize with optional data aggregator or central coordinator"""
        self.use_coordinator = use_coordinator and data_coordinator is not None

        if self.use_coordinator:
            # Use central data coordinator for consistency
            self.data_coordinator = data_coordinator
            self.aggregator = None
            logger.info("SellReportGenerator initialized with central data coordinator")
        else:
            # Fallback to legacy aggregator for backward compatibility
            self.aggregator = aggregator or SignalDataAggregator()
            self.data_coordinator = None
            logger.info(
                "SellReportGenerator initialized with legacy SignalDataAggregator"
            )

    def generate_sell_report(
        self,
        strategy_identifier: str,
        include_raw_data: bool = False,
        snapshot_id: Optional[str] = None,
    ) -> str:
        """
        Generate comprehensive sell signal report using coordinated data

        Args:
            strategy_identifier: Strategy name or Position_UUID
            include_raw_data: Whether to include raw statistical data
            snapshot_id: Optional data snapshot ID for coordinated analysis

        Returns:
            Formatted markdown report
        """
        strategy_data = self._get_strategy_data(strategy_identifier, snapshot_id)
        if not strategy_data:
            return self._generate_error_report(strategy_identifier)

        report_sections = [
            self._generate_header(strategy_data),
            self._generate_executive_summary(strategy_data),
            self._generate_statistical_foundation(strategy_data),
            self._generate_technical_analysis(strategy_data),
            self._generate_exit_strategy(strategy_data),
            self._generate_risk_management(strategy_data),
            self._generate_action_plan(strategy_data),
            self._generate_appendices(strategy_data, include_raw_data),
            self._generate_footer(),
        ]

        return "\n\n".join(report_sections)

    def _get_strategy_data(
        self, strategy_identifier: str, snapshot_id: Optional[str] = None
    ) -> Optional[UnifiedStrategyData]:
        """Get strategy data using coordinator or fallback to aggregator"""
        try:
            if self.use_coordinator and self.data_coordinator:
                # Use central coordinator for data loading
                unified_data = self.data_coordinator.get_strategy_data(
                    strategy_identifier, force_refresh=False, snapshot_id=snapshot_id
                )
                if unified_data:
                    logger.debug(
                        f"Retrieved coordinated data for {strategy_identifier}"
                    )
                    return unified_data
                else:
                    logger.warning(
                        f"No coordinated data found for {strategy_identifier}"
                    )
                    return None
            else:
                # Fallback to legacy aggregator - keep legacy format for backward compatibility
                legacy_data = self.aggregator.get_strategy_data(strategy_identifier)
                if legacy_data:
                    # Convert legacy data to unified format for consistent processing
                    unified_data = UnifiedStrategyData.from_legacy_strategy_data(
                        legacy_data.to_dict()
                        if hasattr(legacy_data, "to_dict")
                        else vars(legacy_data)
                    )
                    logger.debug(
                        f"Retrieved and converted legacy data for {strategy_identifier}"
                    )
                    return unified_data
                else:
                    logger.warning(f"No legacy data found for {strategy_identifier}")
                    return None

        except (StrategyDataCoordinatorError, Exception) as e:
            logger.error(
                f"Error retrieving strategy data for {strategy_identifier}: {e}"
            )
            return None

    def _generate_header(self, data: UnifiedStrategyData) -> str:
        """Generate report header"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        signal_emoji = self._get_signal_emoji(data.signal.exit_signal)

        return f"""# 🎯 Sell Signal Analysis Report

**Strategy**: {data.strategy_name}
**Ticker**: {data.ticker}
**Position UUID**: `{data.position_uuid}`
**Analysis Date**: {timestamp}
**Current Signal**: {signal_emoji} **{data.signal.exit_signal}**
**Confidence Level**: {data.signal.signal_confidence:.1f}%

---"""

    def _generate_executive_summary(self, data: UnifiedStrategyData) -> str:
        """Generate executive summary with key insights"""
        risk_level = self._assess_risk_level(data)
        urgency = self._assess_urgency(data)
        confidence_rating = self._get_confidence_rating(data.signal.signal_confidence)

        # Determine primary recommendation
        if data.signal.exit_signal == "SELL":
            primary_action = "**PREPARE TO EXIT POSITION**"
            rationale = "Statistical analysis indicates approaching performance limits"
        elif data.signal.exit_signal == "STRONG_SELL":
            primary_action = "**IMMEDIATE EXIT RECOMMENDED**"
            rationale = "High probability of diminishing returns detected"
        elif data.signal.exit_signal == "EXIT_IMMEDIATELY":
            primary_action = "**URGENT: EXIT IMMEDIATELY**"
            rationale = "Statistical exhaustion detected - immediate action required"
        else:
            primary_action = "**CONTINUE MONITORING**"
            rationale = "Position remains within acceptable parameters"

        return f"""## 📊 Executive Summary

### Immediate Action Required
{primary_action}

**Risk Assessment**: {risk_level}
**Urgency Level**: {urgency}
**Analysis Confidence**: {confidence_rating}

### Key Findings
- **Statistical Significance**: {data.statistics.statistical_significance} (p-value: {data.statistics.p_value})
- **Sample Size**: {data.statistics.sample_size:,} observations (95% confidence)
- **Current Performance**: {data.performance.unrealized_pnl:.2f}% unrealized P&L
- **Convergence Analysis**: {data.statistics.dual_layer_convergence_score:.1%} dual-layer agreement

### Rationale
{rationale}. The strategy shows {data.signal.signal_confidence:.1f}% confidence in current signal assessment based on comprehensive statistical analysis of {data.statistics.sample_size:,} historical observations."""

    def _generate_statistical_foundation(self, data: UnifiedStrategyData) -> str:
        """Generate statistical foundation analysis"""
        sample_quality = (
            "Excellent"
            if data.statistics.sample_size >= 5000
            else "Good"
            if data.statistics.sample_size >= 1000
            else "Fair"
        )
        significance_strength = (
            "Strong"
            if data.statistics.p_value <= 0.05
            else "Moderate"
            if data.statistics.p_value <= 0.1
            else "Weak"
        )

        return f"""## 📈 Statistical Foundation

### Sample Validation
- **Sample Size**: {data.statistics.sample_size:,} observations
- **Sample Quality**: {sample_quality} (>1,000 recommended for HIGH validity)
- **Confidence Interval**: {data.statistics.sample_size_confidence:.1%}
- **Statistical Validity**: {data.statistics.statistical_significance}

### Significance Testing
- **P-Value**: {data.statistics.p_value:.3f}
- **Significance Strength**: {significance_strength}
- **Test Type**: {data.statistics.statistical_significance}-confidence interval analysis
- **Alpha Level**: 0.05 (95% confidence threshold)

### Convergence Analysis
- **Asset Layer Percentile**: {data.statistics.asset_layer_percentile:.1f}%
- **Strategy Layer Percentile**: {data.statistics.strategy_layer_percentile:.1f}%
- **Dual-Layer Convergence**: {data.statistics.dual_layer_convergence_score:.1%}

**Interpretation**: The {significance_strength.lower()} statistical significance combined with {sample_quality.lower()} sample quality provides {"high" if data.statistics.statistical_significance == "HIGH" else "moderate"} confidence in the analysis results."""

    def _generate_technical_analysis(self, data: UnifiedStrategyData) -> str:
        """Generate technical divergence analysis"""
        z_score_strength = (
            "Strong"
            if abs(data.statistics.z_score_divergence) > 0.05
            else "Moderate"
            if abs(data.statistics.z_score_divergence) > 0.02
            else "Weak"
        )
        iqr_strength = (
            "High"
            if abs(data.statistics.iqr_divergence) > 0.15
            else "Moderate"
            if abs(data.statistics.iqr_divergence) > 0.08
            else "Low"
        )

        return f"""## 🔍 Technical Analysis

### Divergence Metrics
- **Z-Score Divergence**: {data.statistics.z_score_divergence:.4f}
  - *Strength*: {z_score_strength}
  - *Interpretation*: {"Significant deviation from mean" if abs(data.statistics.z_score_divergence) > 0.03 else "Normal variance range"}

- **IQR Divergence**: {data.statistics.iqr_divergence:.4f}
  - *Strength*: {iqr_strength}
  - *Interpretation*: {"Outside normal quartile range" if abs(data.statistics.iqr_divergence) > 0.1 else "Within expected quartile range"}

- **Rarity Score**: {data.statistics.rarity_score:.6f}
  - *Assessment*: {"Rare event detected" if data.statistics.rarity_score > 0.01 else "Common occurrence"}

### Performance Metrics
- **Current Return**: {data.performance.current_return:.4f} ({data.performance.current_return*100:.2f}%)
- **Max Favorable Excursion (MFE)**: {data.performance.mfe:.4f}
- **Max Adverse Excursion (MAE)**: {data.performance.mae:.4f}
- **Unrealized P&L**: {data.performance.unrealized_pnl:.2f}%

### Momentum Assessment
- **Momentum Exit Threshold**: {data.backtesting.momentum_exit_threshold:.6f}
- **Trend Exit Threshold**: {data.backtesting.trend_exit_threshold:.6f}
- **Current vs. Thresholds**: {"Above momentum threshold" if abs(data.performance.current_return) > data.backtesting.momentum_exit_threshold else "Below momentum threshold"}"""

    def _generate_exit_strategy(self, data: UnifiedStrategyData) -> str:
        """Generate exit strategy recommendations"""
        exit_scenarios = self._build_exit_scenarios(data)
        optimal_scenario = self._determine_optimal_exit(data)

        return f"""## 🎯 Exit Strategy Recommendations

### Optimal Exit Strategy
**Recommended Approach**: {optimal_scenario}

### Multiple Exit Scenarios

#### Scenario 1: Take Profit Exit
- **Target**: {data.backtesting.take_profit_pct:.2f}% profit
- **Timeline**: Execute when reached
- **Probability**: {"High" if data.performance.unrealized_pnl > data.backtesting.take_profit_pct * 0.7 else "Moderate"}

#### Scenario 2: Stop Loss Protection
- **Trigger**: {data.backtesting.stop_loss_pct:.2f}% loss threshold
- **Action**: Immediate exit to limit downside
- **Risk Management**: Capital preservation priority

#### Scenario 3: Trailing Stop
- **Initial Stop**: {data.backtesting.trailing_stop_pct:.2f}% below peak
- **Mechanism**: Dynamic adjustment with price movement
- **Benefit**: Captures upside while protecting gains

#### Scenario 4: Time-Based Exit
- **Minimum Hold**: {data.backtesting.min_holding_days} days
- **Maximum Hold**: {data.backtesting.max_holding_days} days
- **Current Duration**: Assess against holding period guidelines

### Exit Timing Optimization
{self._generate_timing_recommendations(data)}"""

    def _generate_risk_management(self, data: UnifiedStrategyData) -> str:
        """Generate risk management framework"""
        risk_score = self._calculate_risk_score(data)
        portfolio_impact = self._assess_portfolio_impact(data)

        return f"""## ⚠️ Risk Management Framework

### Position-Specific Risk Assessment
- **Overall Risk Score**: {risk_score}/10
- **Statistical Risk**: {"Low" if data.statistics.statistical_significance == "HIGH" else "Moderate"}
- **Volatility Risk**: {self._assess_volatility_risk(data)}
- **Liquidity Risk**: {self._assess_liquidity_risk(data.ticker)}

### Portfolio Impact Analysis
{portfolio_impact}

### Risk Mitigation Strategies
1. **Immediate Risk Controls**
   - Monitor {data.backtesting.trailing_stop_pct:.2f}% trailing stop
   - Set {data.backtesting.stop_loss_pct:.2f}% hard stop loss
   - Track momentum threshold at {data.backtesting.momentum_exit_threshold:.4f}

2. **Contingency Planning**
   - Prepare for rapid exit if signal strengthens
   - Consider partial position reduction
   - Monitor correlation with other positions

3. **Monitoring Thresholds**
   - **Alert Level 1**: Signal confidence >75%
   - **Alert Level 2**: Statistical significance change
   - **Alert Level 3**: Dual-layer convergence <50%

### Regulatory Considerations
- Maintain complete audit trail for position exit
- Document decision rationale for compliance
- Ensure exit timing aligns with trading windows"""

    def _generate_action_plan(self, data: UnifiedStrategyData) -> str:
        """Generate specific action plan"""
        immediate_actions = self._get_immediate_actions(data)
        monitoring_plan = self._get_monitoring_plan(data)

        return f"""## 📋 Action Plan

### Immediate Actions (Next 24 Hours)
{immediate_actions}

### Short-Term Monitoring (1-7 Days)
{monitoring_plan}

### Decision Framework
```
IF signal_confidence > 80% AND exit_signal IN ["SELL", "STRONG_SELL"]:
    → Execute exit within 1-2 trading sessions

ELIF dual_layer_convergence < 0.6 AND statistical_significance == "HIGH":
    → Prepare for exit, monitor closely

ELIF unrealized_pnl > take_profit_pct * 0.8:
    → Consider partial profit taking

ELSE:
    → Continue monitoring with established thresholds
```

### Success Metrics
- [ ] Exit executed within optimal timing window
- [ ] Risk management thresholds respected
- [ ] Position impact on portfolio minimized
- [ ] Complete documentation maintained

### Communication Plan
- [ ] Notify risk management team
- [ ] Update portfolio allocation models
- [ ] Document exit rationale
- [ ] Schedule post-exit analysis"""

    def _generate_appendices(
        self, data: UnifiedStrategyData, include_raw_data: bool
    ) -> str:
        """Generate appendices with supporting data"""
        appendix = f"""## 📚 Appendices

### Appendix A: Parameter Summary
```
Strategy Parameters:
- Take Profit: {data.backtesting.take_profit_pct:.2f}%
- Stop Loss: {data.backtesting.stop_loss_pct:.2f}%
- Trailing Stop: {data.backtesting.trailing_stop_pct:.2f}%
- Min Hold Days: {data.backtesting.min_holding_days}
- Max Hold Days: {data.backtesting.max_holding_days}
- Confidence Level: {data.backtesting.confidence_level:.1%}
```

### Appendix B: Data Sources
- **Statistical Analysis**: exports/statistical_analysis/live_signals.csv
- **Backtesting Parameters**: exports/backtesting_parameters/live_signals.json
- **Generation Timestamp**: {data.generation_timestamp}
- **Analysis Framework**: SPDS v1.0.0"""

        if include_raw_data and data.raw_returns:
            appendix += f"""

### Appendix C: Raw Statistical Data
**Historical Returns Sample** ({len(data.raw_returns)} observations):
```
Mean Return: {sum(data.raw_returns)/len(data.raw_returns):.4f}
Std Deviation: {self._calculate_std_dev(data.raw_returns):.4f}
Min Return: {min(data.raw_returns):.4f}
Max Return: {max(data.raw_returns):.4f}
```"""

        return appendix

    def _generate_footer(self) -> str:
        """Generate report footer"""
        return f"""---

**Report Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
**Analysis Framework**: Statistical Performance Divergence System (SPDS)
**Confidence Level**: High-frequency quantitative analysis
**Disclaimer**: This analysis is for informational purposes only and should not be considered as financial advice.

*🤖 Generated with Statistical Performance Divergence System*"""

    def _generate_error_report(self, strategy_identifier: str) -> str:
        """Generate error report when strategy not found"""
        # Try to get available strategies from coordinator or aggregator
        if self.use_coordinator and self.data_coordinator:
            # For coordinator, we don't have a direct get_all_strategies method
            # so we'll provide a generic message
            available_strategies = ["Check coordinator for available strategies"]
        else:
            available_strategies = (
                self.aggregator.get_all_strategies() if self.aggregator else []
            )

        return f"""# ❌ Strategy Not Found

**Requested Strategy**: `{strategy_identifier}`

## Available Strategies
{chr(10).join([f"- {strategy}" for strategy in available_strategies[:10]])}
{"... and more" if len(available_strategies) > 10 else ""}

## Troubleshooting
1. Verify strategy name spelling
2. Check if strategy exists in live_signals portfolio
3. Try using ticker symbol instead
4. Ensure all SPDS export files are available

**Total Available Strategies**: {len(available_strategies)}"""

    # Helper methods for report generation
    def _get_signal_emoji(self, signal: str) -> str:
        """Get emoji for signal type"""
        emoji_map = {
            "EXIT_IMMEDIATELY": "🚨",
            "STRONG_SELL": "📉",
            "SELL": "⚠️",
            "HOLD": "✅",
            "TIME_EXIT": "⏰",
        }
        return emoji_map.get(signal, "❓")

    def _assess_risk_level(self, data: UnifiedStrategyData) -> str:
        """Assess overall risk level"""
        if data.signal.exit_signal in ["EXIT_IMMEDIATELY", "STRONG_SELL"]:
            return "🔴 HIGH"
        elif data.signal.exit_signal == "SELL":
            return "🟡 MODERATE"
        else:
            return "🟢 LOW"

    def _assess_urgency(self, data: UnifiedStrategyData) -> str:
        """Assess urgency level"""
        if data.signal.exit_signal == "EXIT_IMMEDIATELY":
            return "🚨 IMMEDIATE"
        elif data.signal.signal_confidence > 80:
            return "⚡ HIGH"
        elif data.signal.signal_confidence > 60:
            return "⏰ MODERATE"
        else:
            return "📊 LOW"

    def _get_confidence_rating(self, confidence: float) -> str:
        """Get confidence rating description"""
        if confidence >= 85:
            return "🎯 VERY HIGH"
        elif confidence >= 75:
            return "✅ HIGH"
        elif confidence >= 65:
            return "📊 MODERATE"
        else:
            return "⚠️ LOW"

    def _build_exit_scenarios(self, data: UnifiedStrategyData) -> List[Dict[str, Any]]:
        """Build multiple exit scenarios"""
        return [
            {
                "name": "Take Profit",
                "trigger": f"{data.backtesting.take_profit_pct:.2f}% gain",
                "action": "Full exit",
                "priority": "High"
                if data.performance.unrealized_pnl
                > data.backtesting.take_profit_pct * 0.7
                else "Medium",
            },
            {
                "name": "Stop Loss",
                "trigger": f"{data.backtesting.stop_loss_pct:.2f}% loss",
                "action": "Immediate exit",
                "priority": "Critical",
            },
            {
                "name": "Trailing Stop",
                "trigger": f"{data.backtesting.trailing_stop_pct:.2f}% trailing",
                "action": "Dynamic exit",
                "priority": "High",
            },
        ]

    def _determine_optimal_exit(self, data: UnifiedStrategyData) -> str:
        """
        Determine optimal exit strategy

        Prioritizes actual statistical recommendations over hard-coded templates.
        """
        # First priority: Use actual recommendation from statistical analysis
        if data.signal.exit_recommendation and data.signal.exit_recommendation.strip():
            # Clean up the recommendation text for better presentation
            recommendation = data.signal.exit_recommendation.strip()
            # If the recommendation is comprehensive, use it as-is
            if len(recommendation) > 20 and (
                "confidence" in recommendation.lower()
                or "monitor" in recommendation.lower()
            ):
                return recommendation
            # If it's a short phrase, enhance it with context
            else:
                return f"{recommendation} - Based on comprehensive statistical analysis of {data.statistics.sample_size} observations."

        # Second priority: Use raw analysis data if available
        if data.raw_analysis_data:
            raw_data = data.raw_analysis_data
            if isinstance(raw_data, dict) and "exit_recommendation" in raw_data:
                raw_recommendation = raw_data.get("exit_recommendation", "").strip()
                if raw_recommendation:
                    return raw_recommendation

        # Fallback to enhanced template logic (only if no statistical recommendation available)
        signal_strength = (
            "strong"
            if data.signal.signal_confidence > 80
            else "moderate"
            if data.signal.signal_confidence > 60
            else "weak"
        )

        if data.signal.exit_signal == "SELL":
            if data.signal.signal_confidence > 80:
                return f"Immediate exit recommended - Strong statistical signal ({data.signal.signal_confidence:.1f}% confidence) with high significance."
            elif data.signal.signal_confidence > 70:
                return f"Gradual exit using trailing stop with close monitoring - Moderate statistical signal ({data.signal.signal_confidence:.1f}% confidence)."
            else:
                return f"Prepare for potential exit - {signal_strength} signal ({data.signal.signal_confidence:.1f}% confidence) requires careful monitoring."
        elif data.signal.exit_signal == "STRONG_SELL":
            return f"Urgent exit required - Critical statistical threshold exceeded with {data.signal.signal_confidence:.1f}% confidence."
        elif data.performance.unrealized_pnl > data.backtesting.take_profit_pct * 0.8:
            return f"Take profit exit approaching - Position near target ({data.performance.unrealized_pnl:.2f}% vs {data.backtesting.take_profit_pct:.2f}% target)."
        elif data.performance.unrealized_pnl < -data.backtesting.stop_loss_pct * 0.5:
            return f"Risk management exit - Position approaching stop loss threshold ({data.performance.unrealized_pnl:.2f}% vs -{data.backtesting.stop_loss_pct:.2f}% limit)."
        else:
            convergence_desc = f"dual-layer convergence at {data.statistics.dual_layer_convergence_score*100:.1f}%"
            return f"Maintain position with active {convergence_desc} and strict risk management protocols."

    def _generate_timing_recommendations(self, data: UnifiedStrategyData) -> str:
        """Generate timing recommendations"""
        if data.signal.exit_signal == "SELL":
            return "**Recommended Timing**: Exit within 1-3 trading sessions to optimize price execution while avoiding market impact."
        else:
            return "**Recommended Timing**: Continue monitoring with daily reassessment of statistical indicators."

    def _calculate_risk_score(self, data: UnifiedStrategyData) -> int:
        """Calculate overall risk score (1-10)"""
        score = 5  # Base score

        # Adjust for signal strength
        if data.signal.exit_signal == "EXIT_IMMEDIATELY":
            score += 3
        elif data.signal.exit_signal == "STRONG_SELL":
            score += 2
        elif data.signal.exit_signal == "SELL":
            score += 1

        # Adjust for confidence
        if data.signal.signal_confidence > 80:
            score += 1
        elif data.signal.signal_confidence < 60:
            score -= 1

        # Adjust for statistical validity
        if data.statistics.statistical_significance == "LOW":
            score += 1

        # Adjust for convergence
        if data.statistics.dual_layer_convergence_score < 0.5:
            score += 1

        return max(1, min(10, score))

    def _assess_portfolio_impact(self, data: UnifiedStrategyData) -> str:
        """Assess portfolio impact"""
        return f"""**Position Impact**: Monitor correlation effects with other {data.ticker} positions or sector exposure.
**Liquidity Considerations**: {data.ticker} typically provides adequate liquidity for exit execution.
**Timing Considerations**: Consider market hours and volume patterns for optimal exit timing."""

    def _assess_volatility_risk(self, data: UnifiedStrategyData) -> str:
        """Assess volatility risk"""
        if abs(data.statistics.z_score_divergence) > 0.05:
            return "HIGH - Significant statistical divergence detected"
        elif abs(data.statistics.iqr_divergence) > 0.15:
            return "MODERATE - Above normal quartile range"
        else:
            return "LOW - Within normal statistical parameters"

    def _assess_liquidity_risk(self, ticker: str) -> str:
        """Assess liquidity risk by ticker"""
        major_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]
        if ticker in major_tickers:
            return "LOW - Major stock with high liquidity"
        else:
            return "MODERATE - Monitor intraday volume patterns"

    def _get_immediate_actions(self, data: UnifiedStrategyData) -> str:
        """Get immediate actions list"""
        if data.signal.exit_signal == "SELL":
            return """1. ⚠️ Review position size and portfolio exposure
2. 📊 Set up real-time monitoring alerts
3. 📋 Prepare exit order parameters
4. 🔍 Assess market conditions for optimal timing"""
        else:
            return """1. ✅ Continue monitoring established parameters
2. 📊 Review daily statistical updates
3. 🔍 Monitor threshold breach alerts
4. 📋 Maintain risk management protocols"""

    def _get_monitoring_plan(self, data: UnifiedStrategyData) -> str:
        """Get monitoring plan"""
        return f"""1. **Daily Review**: Signal confidence and statistical parameters
2. **Threshold Monitoring**: {data.backtesting.trailing_stop_pct:.2f}% trailing stop adherence
3. **Convergence Tracking**: Dual-layer convergence score changes
4. **Performance Assessment**: Unrealized P&L vs. target parameters"""

    def _calculate_std_dev(self, returns: List[float]) -> float:
        """Calculate standard deviation of returns"""
        if not returns:
            return 0.0

        mean = sum(returns) / len(returns)
        variance = sum((x - mean) ** 2 for x in returns) / len(returns)
        return variance**0.5


def generate_sell_report(
    strategy_identifier: str,
    base_path: Optional[Path] = None,
    include_raw_data: bool = False,
    use_coordinator: bool = True,
    data_coordinator: Optional[StrategyDataCoordinator] = None,
    snapshot_id: Optional[str] = None,
) -> str:
    """
    Convenience function to generate sell report with optional central data coordination

    Args:
        strategy_identifier: Strategy name or Position_UUID
        base_path: Optional base path to trading system
        include_raw_data: Whether to include raw statistical data
        use_coordinator: Whether to use central data coordinator (default: True)
        data_coordinator: Optional data coordinator instance
        snapshot_id: Optional data snapshot ID for coordinated analysis

    Returns:
        Formatted markdown report
    """
    if use_coordinator and (data_coordinator or base_path is None):
        # Use central data coordination for consistency
        coordinator = data_coordinator or StrategyDataCoordinator(
            config=DataCoordinationConfig(), logger=None
        )
        generator = SellReportGenerator(
            aggregator=None, data_coordinator=coordinator, use_coordinator=True
        )
        return generator.generate_sell_report(
            strategy_identifier, include_raw_data, snapshot_id
        )
    else:
        # Fallback to legacy aggregator
        aggregator = SignalDataAggregator(base_path)
        generator = SellReportGenerator(aggregator, use_coordinator=False)
        return generator.generate_sell_report(strategy_identifier, include_raw_data)


# CLI support
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sell Report Generator")
    parser.add_argument(
        "--strategy", required=True, help="Strategy name or Position_UUID"
    )
    parser.add_argument("--output", help="Output file path")
    parser.add_argument(
        "--include-raw", action="store_true", help="Include raw statistical data"
    )
    parser.add_argument("--base-path", help="Base path to trading system")

    args = parser.parse_args()

    report = generate_sell_report(
        args.strategy,
        Path(args.base_path) if args.base_path else None,
        args.include_raw,
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to: {args.output}")
    else:
        print(report)
