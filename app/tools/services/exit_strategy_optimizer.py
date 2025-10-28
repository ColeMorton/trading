#!/usr/bin/env python3
"""
Exit Strategy Optimizer Service

Optimizes exit strategies based on statistical analysis, market conditions,
and risk management parameters from the SPDS system.

Features:
- Multi-scenario exit optimization
- Dynamic parameter adjustment
- Risk-adjusted exit timing
- Market condition integration
- Performance prediction modeling
"""

from dataclasses import dataclass
from enum import Enum
import logging
import sys

from .signal_data_aggregator import StrategyData


logger = logging.getLogger(__name__)


class ExitScenario(Enum):
    """Exit scenario types"""

    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"
    TIME_BASED = "time_based"
    MOMENTUM_EXIT = "momentum_exit"
    STATISTICAL_EXIT = "statistical_exit"


class MarketCondition(Enum):
    """Market condition assessment"""

    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


@dataclass
class ExitRecommendation:
    """Exit strategy recommendation"""

    scenario: ExitScenario
    priority: int  # 1 (highest) to 5 (lowest)
    trigger_price: float | None
    trigger_condition: str
    confidence: float  # 0.0 to 1.0
    expected_return: float
    risk_score: float  # 0.0 to 10.0
    timing_urgency: str  # "immediate", "high", "moderate", "low"
    execution_notes: str

    def __post_init__(self):
        """Validate recommendation data"""
        self.confidence = max(0.0, min(1.0, self.confidence))
        self.risk_score = max(0.0, min(10.0, self.risk_score))


@dataclass
class OptimizationResult:
    """Complete exit strategy optimization result"""

    primary_recommendation: ExitRecommendation
    alternative_scenarios: list[ExitRecommendation]
    market_assessment: MarketCondition
    optimization_confidence: float
    expected_outcomes: dict[str, float]
    risk_mitigation_plan: list[str]
    monitoring_thresholds: dict[str, float]


class ExitStrategyOptimizer:
    """Optimizes exit strategies using statistical and market analysis"""

    def __init__(self):
        """Initialize optimizer with default parameters"""
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        self.market_volatility = 0.20  # 20% assumed market volatility

    def optimize_exit_strategy(
        self,
        strategy_data: StrategyData,
        current_price: float | None = None,
        market_condition: MarketCondition | None = None,
    ) -> OptimizationResult:
        """
        Optimize exit strategy based on comprehensive analysis

        Args:
            strategy_data: Complete strategy data from aggregator
            current_price: Current market price (optional)
            market_condition: Current market condition assessment (optional)

        Returns:
            OptimizationResult with primary and alternative exit strategies
        """
        try:
            # Assess market conditions if not provided
            if market_condition is None:
                market_condition = self._assess_market_condition(strategy_data)

            # Generate all possible exit scenarios
            exit_scenarios = self._generate_exit_scenarios(strategy_data, current_price)

            # Score and rank scenarios
            ranked_scenarios = self._rank_scenarios(
                exit_scenarios,
                strategy_data,
                market_condition,
            )

            # Select primary recommendation
            primary = (
                ranked_scenarios[0]
                if ranked_scenarios
                else self._create_default_recommendation()
            )
            alternatives = ranked_scenarios[1:5]  # Top 4 alternatives

            # Calculate expected outcomes
            expected_outcomes = self._calculate_expected_outcomes(
                ranked_scenarios,
                strategy_data,
            )

            # Generate risk mitigation plan
            risk_plan = self._generate_risk_mitigation_plan(strategy_data, primary)

            # Set monitoring thresholds
            monitoring_thresholds = self._calculate_monitoring_thresholds(
                strategy_data,
                primary,
            )

            # Calculate overall optimization confidence
            optimization_confidence = self._calculate_optimization_confidence(
                strategy_data,
                ranked_scenarios,
            )

            return OptimizationResult(
                primary_recommendation=primary,
                alternative_scenarios=alternatives,
                market_assessment=market_condition,
                optimization_confidence=optimization_confidence,
                expected_outcomes=expected_outcomes,
                risk_mitigation_plan=risk_plan,
                monitoring_thresholds=monitoring_thresholds,
            )

        except Exception as e:
            logger.exception(f"Error optimizing exit strategy: {e}")
            return self._create_fallback_result(strategy_data)

    def _generate_exit_scenarios(
        self,
        data: StrategyData,
        current_price: float | None,
    ) -> list[ExitRecommendation]:
        """Generate all possible exit scenarios"""
        scenarios = []

        # Take Profit Scenario
        if data.take_profit_pct > 0:
            scenarios.append(self._create_take_profit_scenario(data, current_price))

        # Stop Loss Scenario
        if data.stop_loss_pct > 0:
            scenarios.append(self._create_stop_loss_scenario(data, current_price))

        # Trailing Stop Scenario
        if data.trailing_stop_pct > 0:
            scenarios.append(self._create_trailing_stop_scenario(data, current_price))

        # Time-Based Exit Scenario
        scenarios.append(self._create_time_based_scenario(data))

        # Momentum Exit Scenario
        if data.momentum_exit_threshold > 0:
            scenarios.append(self._create_momentum_exit_scenario(data))

        # Statistical Exit Scenario (based on SPDS signal)
        scenarios.append(self._create_statistical_exit_scenario(data))

        return [s for s in scenarios if s is not None]

    def _create_take_profit_scenario(
        self,
        data: StrategyData,
        current_price: float | None,
    ) -> ExitRecommendation:
        """Create take profit exit scenario"""
        trigger_condition = f"Price reaches {data.take_profit_pct:.2f}% gain"

        # Calculate confidence based on current position relative to target
        confidence = 0.8
        if data.unrealized_pnl > 0:
            progress = data.unrealized_pnl / data.take_profit_pct
            confidence = 0.6 + (0.3 * min(1.0, progress))

        # Assess urgency based on how close we are to target
        urgency = "low"
        if data.unrealized_pnl > data.take_profit_pct * 0.8:
            urgency = "high"
        elif data.unrealized_pnl > data.take_profit_pct * 0.6:
            urgency = "moderate"

        return ExitRecommendation(
            scenario=ExitScenario.TAKE_PROFIT,
            priority=2 if data.unrealized_pnl > data.take_profit_pct * 0.7 else 3,
            trigger_price=None,  # Would need entry price to calculate
            trigger_condition=trigger_condition,
            confidence=confidence,
            expected_return=data.take_profit_pct / 100.0,
            risk_score=2.0,  # Low risk - securing gains
            timing_urgency=urgency,
            execution_notes=f"Execute when {data.take_profit_pct:.2f}% profit target is reached. Consider partial profit-taking if very close to target.",
        )

    def _create_stop_loss_scenario(
        self,
        data: StrategyData,
        current_price: float | None,
    ) -> ExitRecommendation:
        """Create stop loss exit scenario"""
        trigger_condition = f"Price falls to {data.stop_loss_pct:.2f}% loss"

        # High confidence - this is risk management
        confidence = 0.95

        # Urgency based on how close we are to stop loss
        urgency = "low"
        if data.unrealized_pnl < -data.stop_loss_pct * 0.5:
            urgency = "high"
        elif data.unrealized_pnl < -data.stop_loss_pct * 0.3:
            urgency = "moderate"

        risk_score = 1.0 if data.unrealized_pnl > -data.stop_loss_pct * 0.3 else 8.0

        return ExitRecommendation(
            scenario=ExitScenario.STOP_LOSS,
            priority=1,  # Highest priority - risk management
            trigger_price=None,
            trigger_condition=trigger_condition,
            confidence=confidence,
            expected_return=-data.stop_loss_pct / 100.0,
            risk_score=risk_score,
            timing_urgency=urgency,
            execution_notes=f"MANDATORY exit at {data.stop_loss_pct:.2f}% loss to limit downside risk. No exceptions.",
        )

    def _create_trailing_stop_scenario(
        self,
        data: StrategyData,
        current_price: float | None,
    ) -> ExitRecommendation:
        """Create trailing stop exit scenario"""
        trigger_condition = (
            f"Price falls {data.trailing_stop_pct:.2f}% from recent peak"
        )

        # Confidence based on current performance
        confidence = 0.75
        if data.unrealized_pnl > 0:
            confidence = 0.85  # Higher confidence when in profit

        urgency = "moderate"  # Trailing stops are dynamic

        return ExitRecommendation(
            scenario=ExitScenario.TRAILING_STOP,
            priority=2,
            trigger_price=None,
            trigger_condition=trigger_condition,
            confidence=confidence,
            expected_return=max(
                0,
                data.unrealized_pnl / 100.0 - data.trailing_stop_pct / 100.0,
            ),
            risk_score=3.0,
            timing_urgency=urgency,
            execution_notes=f"Dynamic exit: Set trailing stop at {data.trailing_stop_pct:.2f}% below the highest price achieved during the holding period.",
        )

    def _create_time_based_scenario(self, data: StrategyData) -> ExitRecommendation:
        """Create time-based exit scenario"""
        trigger_condition = f"Position held for {data.max_holding_days} days"

        # Confidence based on statistical validity
        confidence = 0.6 if data.statistical_validity == "HIGH" else 0.4

        urgency = "low"  # Time-based exits are typically not urgent

        return ExitRecommendation(
            scenario=ExitScenario.TIME_BASED,
            priority=4,
            trigger_price=None,
            trigger_condition=trigger_condition,
            confidence=confidence,
            expected_return=data.current_return,
            risk_score=5.0,  # Moderate risk - no price-based trigger
            timing_urgency=urgency,
            execution_notes=f"Exit after {data.max_holding_days} days regardless of performance to maintain strategy discipline.",
        )

    def _create_momentum_exit_scenario(self, data: StrategyData) -> ExitRecommendation:
        """Create momentum-based exit scenario"""
        trigger_condition = (
            f"Momentum indicator reaches {data.momentum_exit_threshold:.4f} threshold"
        )

        # Confidence based on signal strength
        confidence = min(0.9, data.signal_confidence / 100.0 + 0.2)

        # Urgency based on current momentum vs threshold
        current_momentum = abs(data.current_return)
        urgency = (
            "high" if current_momentum > data.momentum_exit_threshold else "moderate"
        )

        return ExitRecommendation(
            scenario=ExitScenario.MOMENTUM_EXIT,
            priority=3,
            trigger_price=None,
            trigger_condition=trigger_condition,
            confidence=confidence,
            expected_return=data.current_return,
            risk_score=4.0,
            timing_urgency=urgency,
            execution_notes=f"Exit when momentum exceeds {data.momentum_exit_threshold:.4f} threshold to capture momentum reversal.",
        )

    def _create_statistical_exit_scenario(
        self,
        data: StrategyData,
    ) -> ExitRecommendation:
        """Create statistical signal-based exit scenario"""
        signal_priority_map = {
            "EXIT_IMMEDIATELY": 1,
            "STRONG_SELL": 1,
            "SELL": 2,
            "HOLD": 5,
            "TIME_EXIT": 3,
        }

        urgency_map = {
            "EXIT_IMMEDIATELY": "immediate",
            "STRONG_SELL": "high",
            "SELL": "moderate",
            "HOLD": "low",
            "TIME_EXIT": "moderate",
        }

        risk_map = {
            "EXIT_IMMEDIATELY": 9.0,
            "STRONG_SELL": 7.0,
            "SELL": 5.0,
            "HOLD": 2.0,
            "TIME_EXIT": 4.0,
        }

        return ExitRecommendation(
            scenario=ExitScenario.STATISTICAL_EXIT,
            priority=signal_priority_map.get(data.exit_signal, 3),
            trigger_price=None,
            trigger_condition=f"SPDS signal: {data.exit_signal} with {data.signal_confidence:.1f}% confidence",
            confidence=data.signal_confidence / 100.0,
            expected_return=data.current_return,
            risk_score=risk_map.get(data.exit_signal, 5.0),
            timing_urgency=urgency_map.get(data.exit_signal, "moderate"),
            execution_notes=f"{data.exit_recommendation} Based on {data.sample_size:,} observations with {data.statistical_significance} significance.",
        )

    def _rank_scenarios(
        self,
        scenarios: list[ExitRecommendation],
        data: StrategyData,
        market_condition: MarketCondition,
    ) -> list[ExitRecommendation]:
        """Rank scenarios by overall score"""

        def scenario_score(scenario: ExitRecommendation) -> float:
            """Calculate composite score for scenario ranking"""
            # Base score from priority (lower priority = higher score)
            priority_score = (6 - scenario.priority) * 20

            # Confidence score
            confidence_score = scenario.confidence * 30

            # Risk-adjusted return score
            risk_adjusted_score = (scenario.expected_return * 100) - (
                scenario.risk_score * 2
            )

            # Urgency bonus for time-sensitive situations
            urgency_bonus = {"immediate": 20, "high": 15, "moderate": 5, "low": 0}.get(
                scenario.timing_urgency,
                0,
            )

            # Market condition adjustment
            market_bonus = 0
            if (
                market_condition == MarketCondition.BEARISH
                and scenario.scenario
                in [
                    ExitScenario.STOP_LOSS,
                    ExitScenario.STATISTICAL_EXIT,
                ]
            ) or (
                market_condition == MarketCondition.BULLISH
                and scenario.scenario == ExitScenario.TAKE_PROFIT
            ):
                market_bonus = 10

            return (
                priority_score
                + confidence_score
                + risk_adjusted_score
                + urgency_bonus
                + market_bonus
            )

        return sorted(scenarios, key=scenario_score, reverse=True)

    def _assess_market_condition(self, data: StrategyData) -> MarketCondition:
        """Assess market condition based on available data"""
        # Use divergence metrics to assess market condition
        z_score = data.z_score_divergence
        iqr_div = data.iqr_divergence

        if abs(z_score) > 0.05 or abs(iqr_div) > 0.15:
            return MarketCondition.VOLATILE
        if z_score > 0.02:
            return MarketCondition.BULLISH
        if z_score < -0.02:
            return MarketCondition.BEARISH
        return MarketCondition.SIDEWAYS

    def _calculate_expected_outcomes(
        self,
        scenarios: list[ExitRecommendation],
        data: StrategyData,
    ) -> dict[str, float]:
        """Calculate expected outcomes for different scenarios"""
        if not scenarios:
            return {}

        # Weight scenarios by confidence and priority
        total_weight = sum(s.confidence * (6 - s.priority) for s in scenarios)
        if total_weight == 0:
            return {}

        weighted_return = (
            sum(s.expected_return * s.confidence * (6 - s.priority) for s in scenarios)
            / total_weight
        )
        weighted_risk = (
            sum(s.risk_score * s.confidence * (6 - s.priority) for s in scenarios)
            / total_weight
        )

        return {
            "expected_return": weighted_return,
            "expected_risk": weighted_risk,
            "risk_adjusted_return": weighted_return - (weighted_risk * 0.01),
            "confidence_weighted_return": weighted_return,
            "probability_of_loss": max(0, min(1, weighted_risk / 10.0)),
        }

    def _generate_risk_mitigation_plan(
        self,
        data: StrategyData,
        primary: ExitRecommendation,
    ) -> list[str]:
        """Generate risk mitigation plan"""
        plan = []

        # Always include stop loss if available
        if data.stop_loss_pct > 0:
            plan.append(
                f"Maintain hard stop loss at {data.stop_loss_pct:.2f}% to limit maximum downside",
            )

        # Add position sizing recommendation
        if primary.risk_score > 7:
            plan.append(
                "Consider reducing position size by 25-50% to manage high risk exposure",
            )

        # Add monitoring recommendations
        if data.exit_signal in ["SELL", "STRONG_SELL"]:
            plan.append("Implement enhanced monitoring with hourly signal updates")

        # Add correlation risk management
        plan.append(
            f"Monitor correlation with other {data.ticker} positions and sector exposure",
        )

        # Add liquidity management
        plan.append(
            "Ensure adequate liquidity for exit execution during normal trading hours",
        )

        return plan

    def _calculate_monitoring_thresholds(
        self,
        data: StrategyData,
        primary: ExitRecommendation,
    ) -> dict[str, float]:
        """Calculate key monitoring thresholds"""
        thresholds = {}

        # Signal confidence threshold
        thresholds["signal_confidence_alert"] = max(75.0, data.signal_confidence - 10.0)

        # Statistical significance threshold
        thresholds["p_value_alert"] = data.p_value * 1.5  # Alert if p-value increases

        # Performance thresholds
        if data.take_profit_pct > 0:
            thresholds["take_profit_alert"] = data.take_profit_pct * 0.8

        if data.stop_loss_pct > 0:
            thresholds["stop_loss_warning"] = -data.stop_loss_pct * 0.5

        # Convergence threshold
        thresholds["convergence_alert"] = max(
            0.5,
            data.dual_layer_convergence_score - 0.1,
        )

        return thresholds

    def _calculate_optimization_confidence(
        self,
        data: StrategyData,
        scenarios: list[ExitRecommendation],
    ) -> float:
        """Calculate overall confidence in optimization"""
        if not scenarios:
            return 0.0

        # Base confidence from data quality
        data_confidence = 0.5
        if data.statistical_validity == "HIGH":
            data_confidence += 0.2
        if data.sample_size > 5000:
            data_confidence += 0.2
        if data.p_value <= 0.05:
            data_confidence += 0.1

        # Scenario consensus confidence
        scenario_confidence = sum(s.confidence for s in scenarios[:3]) / min(
            3,
            len(scenarios),
        )

        # Final confidence is weighted average
        return (data_confidence * 0.4) + (scenario_confidence * 0.6)

    def _create_default_recommendation(self) -> ExitRecommendation:
        """Create default recommendation when no scenarios available"""
        return ExitRecommendation(
            scenario=ExitScenario.STOP_LOSS,
            priority=1,
            trigger_price=None,
            trigger_condition="Implement basic risk management",
            confidence=0.5,
            expected_return=0.0,
            risk_score=5.0,
            timing_urgency="moderate",
            execution_notes="Insufficient data for optimization. Implement basic risk management protocols.",
        )

    def _create_fallback_result(self, data: StrategyData) -> OptimizationResult:
        """Create fallback result when optimization fails"""
        default_rec = self._create_default_recommendation()

        return OptimizationResult(
            primary_recommendation=default_rec,
            alternative_scenarios=[],
            market_assessment=MarketCondition.UNKNOWN,
            optimization_confidence=0.3,
            expected_outcomes={"expected_return": 0.0, "expected_risk": 5.0},
            risk_mitigation_plan=[
                "Implement conservative risk management",
                "Monitor position closely",
            ],
            monitoring_thresholds={"signal_confidence_alert": 60.0},
        )


def optimize_exit_strategy(
    strategy_data: StrategyData,
    current_price: float | None = None,
    market_condition: MarketCondition | None = None,
) -> OptimizationResult:
    """
    Convenience function to optimize exit strategy

    Args:
        strategy_data: Complete strategy data from aggregator
        current_price: Current market price (optional)
        market_condition: Current market condition assessment (optional)

    Returns:
        OptimizationResult with recommendations
    """
    optimizer = ExitStrategyOptimizer()
    return optimizer.optimize_exit_strategy(
        strategy_data,
        current_price,
        market_condition,
    )


# CLI support
if __name__ == "__main__":
    import argparse

    from .signal_data_aggregator import SignalDataAggregator

    parser = argparse.ArgumentParser(description="Exit Strategy Optimizer")
    parser.add_argument(
        "--strategy",
        required=True,
        help="Strategy name or Position_UUID",
    )
    parser.add_argument("--current-price", type=float, help="Current market price")
    parser.add_argument("--base-path", help="Base path to trading system")

    args = parser.parse_args()

    # Get strategy data
    aggregator = SignalDataAggregator()
    strategy_data = aggregator.get_strategy_data(args.strategy)

    if not strategy_data:
        print(f"Strategy '{args.strategy}' not found")
        sys.exit(1)

    # Optimize exit strategy
    result = optimize_exit_strategy(strategy_data, args.current_price)

    # Display results
    print(f"\n=== Exit Strategy Optimization for {strategy_data.strategy_name} ===")
    print(f"Primary Recommendation: {result.primary_recommendation.scenario.value}")
    print(f"Confidence: {result.optimization_confidence:.1%}")
    print(f"Market Assessment: {result.market_assessment.value}")
    print(f"Expected Return: {result.expected_outcomes.get('expected_return', 0):.2%}")
    print(f"Risk Score: {result.primary_recommendation.risk_score}/10")
    print(f"Urgency: {result.primary_recommendation.timing_urgency}")
    print(f"\nExecution Notes: {result.primary_recommendation.execution_notes}")
