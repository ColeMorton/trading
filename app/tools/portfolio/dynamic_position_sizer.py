"""Dynamic position sizing based on statistical performance analysis.

This module provides adaptive position sizing capabilities that adjust
allocation based on statistical analysis and performance metrics.
"""

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.tools.models.statistical_analysis_models import (
    PositionData,
    StatisticalAnalysisResult,
)


logger = logging.getLogger(__name__)


@dataclass
class PositionSizeRecommendation:
    """Position size recommendation with rationale."""

    position_id: str
    current_size: float
    recommended_size: float
    size_change_pct: float
    rationale: str
    confidence: float
    risk_level: str
    statistical_basis: str


@dataclass
class PortfolioSizingResult:
    """Result of portfolio-wide position sizing analysis."""

    total_capital: float
    recommendations: list[PositionSizeRecommendation]
    risk_budget_utilization: float
    expected_portfolio_volatility: float
    diversification_score: float
    sizing_methodology: str


class DynamicPositionSizer:
    """Dynamic position sizer using statistical performance analysis.

    This sizer provides:
    - Kelly criterion-based sizing
    - Risk parity allocation
    - Statistical confidence-based sizing
    - Volatility-adjusted sizing
    - Maximum drawdown-based limits
    """

    def __init__(
        self,
        base_risk_per_trade: float = 0.02,
        max_position_size: float = 0.15,
        min_position_size: float = 0.005,
        kelly_fraction: float = 0.25,
        volatility_lookback: int = 20,
    ):
        """Initialize dynamic position sizer.

        Args:
            base_risk_per_trade: Base risk percentage per trade (2%)
            max_position_size: Maximum position size (15%)
            min_position_size: Minimum position size (0.5%)
            kelly_fraction: Fraction of Kelly criterion to use (25%)
            volatility_lookback: Days for volatility calculation
        """
        self.base_risk_per_trade = base_risk_per_trade
        self.max_position_size = max_position_size
        self.min_position_size = min_position_size
        self.kelly_fraction = kelly_fraction
        self.volatility_lookback = volatility_lookback

    def calculate_portfolio_sizing(
        self,
        positions: list[PositionData],
        analysis_results: list[StatisticalAnalysisResult],
        total_capital: float,
        historical_data: pd.DataFrame | None = None,
    ) -> PortfolioSizingResult:
        """Calculate optimal position sizes for entire portfolio.

        Args:
            positions: List of current positions
            analysis_results: Statistical analysis for each position
            total_capital: Total available capital
            historical_data: Historical performance data

        Returns:
            Portfolio sizing result with recommendations
        """
        logger.info(f"Calculating position sizing for {len(positions)} positions")

        recommendations = []

        for pos, analysis in zip(positions, analysis_results, strict=False):
            recommendation = self.calculate_position_size(
                pos,
                analysis,
                total_capital,
                historical_data,
            )
            recommendations.append(recommendation)

        # Calculate portfolio-level metrics
        portfolio_metrics = self._calculate_portfolio_metrics(
            recommendations,
            total_capital,
        )

        # Apply portfolio-level constraints
        adjusted_recommendations = self._apply_portfolio_constraints(
            recommendations,
            total_capital,
            portfolio_metrics,
        )

        return PortfolioSizingResult(
            total_capital=total_capital,
            recommendations=adjusted_recommendations,
            risk_budget_utilization=portfolio_metrics["risk_utilization"],
            expected_portfolio_volatility=portfolio_metrics["portfolio_volatility"],
            diversification_score=portfolio_metrics["diversification_score"],
            sizing_methodology="statistical_adaptive",
        )

    def calculate_position_size(
        self,
        position: PositionData,
        analysis: StatisticalAnalysisResult,
        total_capital: float,
        historical_data: pd.DataFrame | None = None,
    ) -> PositionSizeRecommendation:
        """Calculate optimal position size for a single position.

        Args:
            position: Position data
            analysis: Statistical analysis results
            total_capital: Total available capital
            historical_data: Historical performance data

        Returns:
            Position size recommendation
        """
        # Calculate different sizing methods
        kelly_size = self._calculate_kelly_size(position, analysis, historical_data)
        risk_parity_size = self._calculate_risk_parity_size(
            position,
            analysis,
            total_capital,
        )
        confidence_size = self._calculate_confidence_based_size(position, analysis)
        volatility_size = self._calculate_volatility_adjusted_size(
            position,
            analysis,
            historical_data,
        )

        # Combine methods with weights
        combined_size = self._combine_sizing_methods(
            kelly_size,
            risk_parity_size,
            confidence_size,
            volatility_size,
            analysis,
        )

        # Apply constraints
        final_size = np.clip(
            combined_size,
            self.min_position_size,
            self.max_position_size,
        )

        # Calculate current size (placeholder - would come from actual portfolio)
        current_size = 0.05  # Default 5% if unknown

        # Generate rationale
        rationale = self._generate_sizing_rationale(
            position,
            analysis,
            final_size,
            kelly_size,
            risk_parity_size,
            confidence_size,
            volatility_size,
        )

        # Calculate confidence and risk level
        confidence = self._calculate_sizing_confidence(analysis)
        risk_level = self._assess_position_risk_level(position, analysis)

        return PositionSizeRecommendation(
            position_id=position.position_id,
            current_size=current_size,
            recommended_size=final_size,
            size_change_pct=(final_size - current_size) / current_size * 100,
            rationale=rationale,
            confidence=confidence,
            risk_level=risk_level,
            statistical_basis=self._get_statistical_basis(analysis),
        )

    def _calculate_kelly_size(
        self,
        position: PositionData,
        analysis: StatisticalAnalysisResult,
        historical_data: pd.DataFrame | None,
    ) -> float:
        """Calculate Kelly criterion position size."""
        if not analysis.return_distribution:
            return self.base_risk_per_trade

        # Get win rate and average win/loss
        win_rate = analysis.return_distribution.win_rate
        avg_win = abs(analysis.return_distribution.mean_positive_return)
        avg_loss = abs(analysis.return_distribution.mean_negative_return)

        if avg_loss == 0 or win_rate <= 0:
            return self.base_risk_per_trade

        # Kelly formula: f = (bp - q) / b
        # where b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate

        kelly_fraction = (b * p - q) / b

        # Apply fraction of Kelly and constraints
        kelly_size = max(0, kelly_fraction * self.kelly_fraction)

        return min(kelly_size, self.max_position_size)

    def _calculate_risk_parity_size(
        self,
        position: PositionData,
        analysis: StatisticalAnalysisResult,
        total_capital: float,
    ) -> float:
        """Calculate risk parity position size."""
        # Base size on inverse volatility
        if (
            analysis.volatility_analysis
            and analysis.volatility_analysis.current_volatility > 0
        ):
            volatility = analysis.volatility_analysis.current_volatility
        else:
            # Estimate volatility from position data
            volatility = abs(position.mae) if position.mae > 0 else 0.1

        # Inverse volatility sizing
        target_risk = self.base_risk_per_trade
        position_size = target_risk / volatility

        return np.clip(position_size, self.min_position_size, self.max_position_size)

    def _calculate_confidence_based_size(
        self,
        position: PositionData,
        analysis: StatisticalAnalysisResult,
    ) -> float:
        """Calculate size based on statistical confidence."""
        base_size = self.base_risk_per_trade

        # Confidence multipliers
        confidence_multiplier = 1.0

        # Sample size confidence
        if analysis.sample_size_analysis:
            sample_confidence = analysis.sample_size_analysis.confidence_level
            confidence_multiplier *= sample_confidence

        # Dual layer convergence
        if analysis.divergence_analysis:
            convergence = analysis.divergence_analysis.dual_layer_convergence_score
            confidence_multiplier *= 0.5 + 0.5 * convergence

        # Statistical significance
        if analysis.significance_testing:
            significance = analysis.significance_testing.overall_significance
            confidence_multiplier *= significance

        adjusted_size = base_size * confidence_multiplier

        return np.clip(adjusted_size, self.min_position_size, self.max_position_size)

    def _calculate_volatility_adjusted_size(
        self,
        position: PositionData,
        analysis: StatisticalAnalysisResult,
        historical_data: pd.DataFrame | None,
    ) -> float:
        """Calculate volatility-adjusted position size."""
        # Get recent volatility
        if (
            historical_data is not None
            and len(historical_data) > self.volatility_lookback
        ):
            recent_returns = historical_data.tail(self.volatility_lookback)
            if "return" in recent_returns.columns:
                volatility = recent_returns["return"].std()
            else:
                volatility = 0.1  # Default
        else:
            # Use position MAE as volatility proxy
            volatility = position.mae if position.mae > 0 else 0.1

        # Inverse volatility sizing with target risk
        target_volatility = 0.02  # 2% daily risk
        size_multiplier = target_volatility / max(volatility, 0.001)

        base_size = self.base_risk_per_trade
        adjusted_size = base_size * size_multiplier

        return np.clip(adjusted_size, self.min_position_size, self.max_position_size)

    def _combine_sizing_methods(
        self,
        kelly_size: float,
        risk_parity_size: float,
        confidence_size: float,
        volatility_size: float,
        analysis: StatisticalAnalysisResult,
    ) -> float:
        """Combine different sizing methods with adaptive weights."""
        # Base weights
        weights = {
            "kelly": 0.3,
            "risk_parity": 0.2,
            "confidence": 0.3,
            "volatility": 0.2,
        }

        # Adjust weights based on data quality
        if analysis.sample_size_analysis:
            sample_size = analysis.sample_size_analysis.sample_size
            if sample_size < 30:
                # Reduce Kelly weight for small samples
                weights["kelly"] *= 0.5
                weights["confidence"] += 0.15
                weights["volatility"] += 0.15

        # Adjust for statistical significance
        if analysis.significance_testing:
            significance = analysis.significance_testing.overall_significance
            if significance < 0.7:
                # Reduce aggressive sizing for low significance
                weights["kelly"] *= 0.7
                weights["risk_parity"] += 0.1
                weights["volatility"] += 0.1

        # Normalize weights
        total_weight = sum(weights.values())
        for key in weights:
            weights[key] /= total_weight

        # Calculate weighted average
        return (
            weights["kelly"] * kelly_size
            + weights["risk_parity"] * risk_parity_size
            + weights["confidence"] * confidence_size
            + weights["volatility"] * volatility_size
        )

    def _generate_sizing_rationale(
        self,
        position: PositionData,
        analysis: StatisticalAnalysisResult,
        final_size: float,
        kelly_size: float,
        risk_parity_size: float,
        confidence_size: float,
        volatility_size: float,
    ) -> str:
        """Generate human-readable rationale for position size."""
        components = []

        # Primary driver
        sizes = {
            "Kelly": kelly_size,
            "Risk Parity": risk_parity_size,
            "Confidence": confidence_size,
            "Volatility": volatility_size,
        }

        primary_driver = max(sizes, key=sizes.get)
        components.append(f"Primary driver: {primary_driver}")

        # Statistical factors
        if analysis.divergence_analysis:
            convergence = analysis.divergence_analysis.dual_layer_convergence_score
            if convergence > 0.8:
                components.append("High dual-layer convergence supports larger size")
            elif convergence < 0.5:
                components.append("Low dual-layer convergence suggests smaller size")

        # Sample size considerations
        if analysis.sample_size_analysis:
            sample_size = analysis.sample_size_analysis.sample_size
            if sample_size < 30:
                components.append(
                    f"Small sample size ({sample_size}) reduces confidence",
                )
            elif sample_size > 100:
                components.append(
                    f"Large sample size ({sample_size}) increases confidence",
                )

        # Risk assessment
        if final_size > self.base_risk_per_trade * 1.5:
            components.append("Above-average allocation due to favorable statistics")
        elif final_size < self.base_risk_per_trade * 0.7:
            components.append("Below-average allocation due to risk concerns")

        return "; ".join(components)

    def _calculate_sizing_confidence(
        self,
        analysis: StatisticalAnalysisResult,
    ) -> float:
        """Calculate confidence in sizing recommendation."""
        confidence_factors = []

        # Sample size confidence
        if analysis.sample_size_analysis:
            confidence_factors.append(analysis.sample_size_analysis.confidence_level)

        # Statistical significance
        if analysis.significance_testing:
            confidence_factors.append(
                analysis.significance_testing.overall_significance,
            )

        # Convergence confidence
        if analysis.divergence_analysis:
            convergence = analysis.divergence_analysis.dual_layer_convergence_score
            confidence_factors.append(convergence)

        if confidence_factors:
            return np.mean(confidence_factors)
        return 0.5  # Moderate confidence as default

    def _assess_position_risk_level(
        self,
        position: PositionData,
        analysis: StatisticalAnalysisResult,
    ) -> str:
        """Assess overall risk level of position."""
        risk_score = 0

        # Volatility risk
        if position.mae > 0.15:  # >15% MAE
            risk_score += 2
        elif position.mae > 0.08:  # >8% MAE
            risk_score += 1

        # Duration risk
        if position.days_held > 60:  # >60 days
            risk_score += 1

        # Statistical risk
        if analysis.divergence_analysis:
            rarity = analysis.divergence_analysis.statistical_rarity_score
            if rarity > 0.95:  # Very rare outcome
                risk_score += 2
            elif rarity > 0.90:
                risk_score += 1

        # Sample size risk
        if analysis.sample_size_analysis:
            if analysis.sample_size_analysis.sample_size < 20:
                risk_score += 1

        # Classify risk level
        if risk_score >= 4:
            return "HIGH"
        if risk_score >= 2:
            return "MEDIUM"
        return "LOW"

    def _get_statistical_basis(self, analysis: StatisticalAnalysisResult) -> str:
        """Get statistical basis for sizing decision."""
        basis_elements = []

        if analysis.sample_size_analysis:
            sample_size = analysis.sample_size_analysis.sample_size
            basis_elements.append(f"n={sample_size}")

        if analysis.divergence_analysis:
            convergence = analysis.divergence_analysis.dual_layer_convergence_score
            basis_elements.append(f"convergence={convergence:.2f}")

        if analysis.significance_testing:
            significance = analysis.significance_testing.overall_significance
            basis_elements.append(f"significance={significance:.2f}")

        return ", ".join(basis_elements) if basis_elements else "limited_data"

    def _calculate_portfolio_metrics(
        self,
        recommendations: list[PositionSizeRecommendation],
        total_capital: float,
    ) -> dict[str, float]:
        """Calculate portfolio-level metrics."""
        total_allocation = sum(rec.recommended_size for rec in recommendations)

        # Risk budget utilization
        risk_utilization = total_allocation

        # Portfolio volatility (simplified)
        weights = [rec.recommended_size for rec in recommendations]
        portfolio_volatility = np.sqrt(np.sum(np.square(weights))) if weights else 0

        # Diversification score (based on concentration)
        if weights:
            hhi = sum(w**2 for w in weights)  # Herfindahl index
            diversification_score = (
                (1 - hhi) / (1 - 1 / len(weights)) if len(weights) > 1 else 0
            )
        else:
            diversification_score = 0

        return {
            "risk_utilization": risk_utilization,
            "portfolio_volatility": portfolio_volatility,
            "diversification_score": diversification_score,
        }

    def _apply_portfolio_constraints(
        self,
        recommendations: list[PositionSizeRecommendation],
        total_capital: float,
        portfolio_metrics: dict[str, float],
    ) -> list[PositionSizeRecommendation]:
        """Apply portfolio-level constraints to position sizes."""
        # Check if total allocation exceeds limits
        total_allocation = sum(rec.recommended_size for rec in recommendations)
        max_total_allocation = 0.95  # Maximum 95% allocation

        if total_allocation > max_total_allocation:
            # Scale down proportionally
            scaling_factor = max_total_allocation / total_allocation

            for rec in recommendations:
                rec.recommended_size *= scaling_factor
                rec.rationale += f"; Scaled down by {(1-scaling_factor)*100:.1f}% for portfolio limits"

        # Ensure minimum diversification
        if len(recommendations) > 1:
            max_single_position = 0.40  # Maximum 40% in single position

            for rec in recommendations:
                if rec.recommended_size > max_single_position:
                    rec.recommended_size = max_single_position
                    rec.rationale += f"; Capped at {max_single_position*100:.0f}% for diversification"

        return recommendations
