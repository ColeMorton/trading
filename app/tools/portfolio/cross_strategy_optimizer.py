"""Cross-strategy portfolio optimization using statistical analysis.

This module provides portfolio-level optimization capabilities that analyze
correlations and performance across multiple strategies.
"""

import logging
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import pearsonr, spearmanr

from app.tools.models.statistical_analysis_models import (
    PositionData,
    StatisticalAnalysisResult,
)


logger = logging.getLogger(__name__)


@dataclass
class StrategyCorrelation:
    """Correlation analysis between strategies."""

    strategy1: str
    strategy2: str
    pearson_correlation: float
    spearman_correlation: float
    p_value: float
    correlation_type: str  # 'positive', 'negative', 'uncorrelated'


@dataclass
class PortfolioOptimizationResult:
    """Result of portfolio optimization."""

    optimal_weights: dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    correlation_benefit: float
    diversification_ratio: float
    recommendations: list[str]


class CrossStrategyOptimizer:
    """Portfolio optimizer for cross-strategy analysis and allocation.

    This optimizer provides:
    - Cross-strategy correlation analysis
    - Optimal weight calculation
    - Risk-adjusted portfolio construction
    - Diversification benefit analysis
    """

    def __init__(
        self,
        min_correlation_threshold: float = 0.3,
        max_position_weight: float = 0.4,
        min_position_weight: float = 0.05,
        target_return: float | None = None,
    ):
        """Initialize cross-strategy optimizer.

        Args:
            min_correlation_threshold: Threshold for significant correlation
            max_position_weight: Maximum weight for any position
            min_position_weight: Minimum weight for any position
            target_return: Target portfolio return (None for max Sharpe)
        """
        self.min_correlation_threshold = min_correlation_threshold
        self.max_position_weight = max_position_weight
        self.min_position_weight = min_position_weight
        self.target_return = target_return

    def optimize_portfolio(
        self,
        positions: list[PositionData],
        analysis_results: list[StatisticalAnalysisResult],
        historical_returns: pd.DataFrame,
    ) -> PortfolioOptimizationResult:
        """Optimize portfolio allocation across strategies.

        Args:
            positions: List of current positions
            analysis_results: Statistical analysis for each position
            historical_returns: Historical returns for correlation calculation

        Returns:
            Optimization result with weights and metrics
        """
        logger.info(f"Optimizing portfolio with {len(positions)} positions")

        if len(positions) < 2:
            logger.warning("Insufficient positions for optimization")
            return self._single_position_result(positions[0] if positions else None)

        # Calculate correlation matrix
        correlation_matrix = self._calculate_correlation_matrix(
            positions,
            historical_returns,
        )

        # Calculate expected returns and covariance
        expected_returns = self._calculate_expected_returns(positions, analysis_results)
        covariance_matrix = self._calculate_covariance_matrix(
            positions,
            historical_returns,
        )

        # Optimize weights
        optimal_weights = self._optimize_weights(expected_returns, covariance_matrix)

        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(
            optimal_weights,
            expected_returns,
            covariance_matrix,
        )

        # Analyze correlations
        correlation_benefits = self._analyze_correlation_benefits(
            correlation_matrix,
            optimal_weights,
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            positions,
            optimal_weights,
            correlation_matrix,
            portfolio_metrics,
        )

        return PortfolioOptimizationResult(
            optimal_weights=dict(
                zip([p.position_id for p in positions], optimal_weights, strict=False),
            ),
            expected_return=portfolio_metrics["expected_return"],
            expected_risk=portfolio_metrics["risk"],
            sharpe_ratio=portfolio_metrics["sharpe_ratio"],
            correlation_benefit=correlation_benefits["benefit"],
            diversification_ratio=correlation_benefits["diversification_ratio"],
            recommendations=recommendations,
        )

    def analyze_strategy_correlations(
        self,
        positions: list[PositionData],
        historical_returns: pd.DataFrame,
    ) -> list[StrategyCorrelation]:
        """Analyze correlations between all strategy pairs.

        Args:
            positions: List of positions to analyze
            historical_returns: Historical returns data

        Returns:
            List of correlation analyses
        """
        correlations = []

        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                pos1, pos2 = positions[i], positions[j]

                # Get returns for each position
                returns1 = self._get_position_returns(pos1, historical_returns)
                returns2 = self._get_position_returns(pos2, historical_returns)

                if len(returns1) < 20 or len(returns2) < 20:
                    continue

                # Align returns
                aligned_returns = pd.DataFrame(
                    {"returns1": returns1, "returns2": returns2},
                ).dropna()

                if len(aligned_returns) < 20:
                    continue

                # Calculate correlations
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    pearson_corr, pearson_p = pearsonr(
                        aligned_returns["returns1"],
                        aligned_returns["returns2"],
                    )
                    spearman_corr, spearman_p = spearmanr(
                        aligned_returns["returns1"],
                        aligned_returns["returns2"],
                    )

                # Classify correlation
                avg_corr = (pearson_corr + spearman_corr) / 2
                if avg_corr > self.min_correlation_threshold:
                    corr_type = "positive"
                elif avg_corr < -self.min_correlation_threshold:
                    corr_type = "negative"
                else:
                    corr_type = "uncorrelated"

                correlations.append(
                    StrategyCorrelation(
                        strategy1=pos1.strategy_name,
                        strategy2=pos2.strategy_name,
                        pearson_correlation=pearson_corr,
                        spearman_correlation=spearman_corr,
                        p_value=min(pearson_p, spearman_p),
                        correlation_type=corr_type,
                    ),
                )

        return correlations

    def calculate_diversification_benefit(
        self,
        positions: list[PositionData],
        weights: np.ndarray,
        historical_returns: pd.DataFrame,
    ) -> dict[str, float]:
        """Calculate diversification benefits of portfolio.

        Args:
            positions: List of positions
            weights: Portfolio weights
            historical_returns: Historical returns data

        Returns:
            Dictionary with diversification metrics
        """
        # Calculate individual risks
        individual_risks = []
        for pos in positions:
            returns = self._get_position_returns(pos, historical_returns)
            if len(returns) > 0:
                individual_risks.append(returns.std())
            else:
                individual_risks.append(0.0)

        individual_risks = np.array(individual_risks)

        # Calculate portfolio risk
        covariance_matrix = self._calculate_covariance_matrix(
            positions,
            historical_returns,
        )
        portfolio_risk = np.sqrt(weights @ covariance_matrix @ weights.T)

        # Calculate weighted average risk
        weighted_avg_risk = np.sum(weights * individual_risks)

        # Diversification ratio
        diversification_ratio = weighted_avg_risk / max(portfolio_risk, 1e-6)

        # Risk reduction percentage
        risk_reduction = (weighted_avg_risk - portfolio_risk) / weighted_avg_risk * 100

        return {
            "portfolio_risk": portfolio_risk,
            "weighted_avg_risk": weighted_avg_risk,
            "diversification_ratio": diversification_ratio,
            "risk_reduction_pct": risk_reduction,
            "effective_diversification": diversification_ratio > 1.1,
        }

    def _calculate_correlation_matrix(
        self,
        positions: list[PositionData],
        historical_returns: pd.DataFrame,
    ) -> np.ndarray:
        """Calculate correlation matrix for positions."""
        n = len(positions)
        correlation_matrix = np.eye(n)

        for i in range(n):
            for j in range(i + 1, n):
                returns_i = self._get_position_returns(positions[i], historical_returns)
                returns_j = self._get_position_returns(positions[j], historical_returns)

                # Align returns
                aligned = pd.DataFrame({"i": returns_i, "j": returns_j}).dropna()

                if len(aligned) >= 20:
                    corr = aligned["i"].corr(aligned["j"])
                    if not np.isnan(corr):
                        correlation_matrix[i, j] = corr
                        correlation_matrix[j, i] = corr

        return correlation_matrix

    def _calculate_expected_returns(
        self,
        positions: list[PositionData],
        analysis_results: list[StatisticalAnalysisResult],
    ) -> np.ndarray:
        """Calculate expected returns for each position."""
        expected_returns = []

        for pos, analysis in zip(positions, analysis_results, strict=False):
            # Use statistical analysis to estimate expected return
            if analysis.return_distribution:
                # Use median return as expected return
                expected_return = analysis.return_distribution.median_return
            else:
                # Fallback to current return
                expected_return = pos.current_return

            expected_returns.append(expected_return)

        return np.array(expected_returns)

    def _calculate_covariance_matrix(
        self,
        positions: list[PositionData],
        historical_returns: pd.DataFrame,
    ) -> np.ndarray:
        """Calculate covariance matrix for positions."""
        # Build returns matrix
        returns_data = {}
        for pos in positions:
            returns = self._get_position_returns(pos, historical_returns)
            returns_data[pos.position_id] = returns

        returns_df = pd.DataFrame(returns_data)

        # Calculate covariance
        cov_matrix = returns_df.cov().values

        # Handle NaN values
        cov_matrix = np.nan_to_num(cov_matrix, nan=0.0)

        # Ensure positive semi-definite
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        eigenvalues = np.maximum(eigenvalues, 1e-8)
        return eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T

    def _optimize_weights(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
    ) -> np.ndarray:
        """Optimize portfolio weights using mean-variance optimization."""
        n = len(expected_returns)

        # Objective function (negative Sharpe ratio)
        def objective(weights):
            portfolio_return = weights @ expected_returns
            portfolio_risk = np.sqrt(weights @ covariance_matrix @ weights.T)

            # Sharpe ratio (assuming risk-free rate = 0)
            sharpe = portfolio_return / max(portfolio_risk, 1e-6)
            return -sharpe  # Minimize negative Sharpe

        # Constraints
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]  # Sum to 1

        # Add target return constraint if specified
        if self.target_return is not None:
            constraints.append(
                {
                    "type": "eq",
                    "fun": lambda w: w @ expected_returns - self.target_return,
                },
            )

        # Bounds
        bounds = [(self.min_position_weight, self.max_position_weight)] * n

        # Initial guess (equal weights)
        initial_weights = np.ones(n) / n

        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-9, "maxiter": 1000},
        )

        if result.success:
            return result.x
        logger.warning("Optimization failed, using equal weights")
        return initial_weights

    def _calculate_portfolio_metrics(
        self,
        weights: np.ndarray,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
    ) -> dict[str, float]:
        """Calculate portfolio performance metrics."""
        # Portfolio return
        portfolio_return = weights @ expected_returns

        # Portfolio risk
        portfolio_variance = weights @ covariance_matrix @ weights.T
        portfolio_risk = np.sqrt(portfolio_variance)

        # Sharpe ratio
        sharpe_ratio = portfolio_return / max(portfolio_risk, 1e-6)

        # Annualized metrics (assuming daily returns)
        annual_return = portfolio_return * 252
        annual_risk = portfolio_risk * np.sqrt(252)
        annual_sharpe = sharpe_ratio * np.sqrt(252)

        return {
            "expected_return": portfolio_return,
            "risk": portfolio_risk,
            "sharpe_ratio": sharpe_ratio,
            "annual_return": annual_return,
            "annual_risk": annual_risk,
            "annual_sharpe": annual_sharpe,
        }

    def _analyze_correlation_benefits(
        self,
        correlation_matrix: np.ndarray,
        weights: np.ndarray,
    ) -> dict[str, float]:
        """Analyze benefits from correlation structure."""
        # Average correlation
        n = len(weights)
        if n <= 1:
            return {"benefit": 0.0, "diversification_ratio": 1.0}

        # Extract upper triangle correlations
        upper_correlations = []
        for i in range(n):
            for j in range(i + 1, n):
                upper_correlations.append(correlation_matrix[i, j])

        avg_correlation = np.mean(upper_correlations) if upper_correlations else 0.0

        # Diversification benefit (lower correlation = higher benefit)
        correlation_benefit = 1.0 - avg_correlation

        # Effective number of positions (diversification ratio)
        weighted_correlations = []
        for i in range(n):
            for j in range(n):
                if i != j:
                    weighted_correlations.append(
                        weights[i] * weights[j] * correlation_matrix[i, j],
                    )

        avg_weighted_corr = np.sum(weighted_correlations)
        diversification_ratio = 1.0 / (1.0 + avg_weighted_corr)

        return {
            "benefit": correlation_benefit,
            "diversification_ratio": diversification_ratio,
            "avg_correlation": avg_correlation,
        }

    def _generate_recommendations(
        self,
        positions: list[PositionData],
        weights: np.ndarray,
        correlation_matrix: np.ndarray,
        portfolio_metrics: dict[str, float],
    ) -> list[str]:
        """Generate portfolio optimization recommendations."""
        recommendations = []

        # Check Sharpe ratio
        if portfolio_metrics["annual_sharpe"] > 2.0:
            recommendations.append(
                "Excellent risk-adjusted returns - maintain current allocation",
            )
        elif portfolio_metrics["annual_sharpe"] < 0.5:
            recommendations.append(
                "Low risk-adjusted returns - consider rebalancing or strategy review",
            )

        # Check concentration
        max_weight = np.max(weights)
        if max_weight > 0.5:
            idx = np.argmax(weights)
            recommendations.append(
                f"High concentration in {positions[idx].strategy_name} "
                f"({max_weight:.1%}) - consider diversification",
            )

        # Check correlations
        high_corr_pairs = []
        n = len(positions)
        for i in range(n):
            for j in range(i + 1, n):
                if correlation_matrix[i, j] > 0.7:
                    high_corr_pairs.append((i, j))

        if high_corr_pairs:
            recommendations.append(
                f"Found {len(high_corr_pairs)} highly correlated position pairs - "
                "consider reducing overlap",
            )

        # Check for negative correlations (good for diversification)
        negative_corr_count = np.sum(correlation_matrix < -0.3) / 2
        if negative_corr_count > 0:
            recommendations.append(
                f"Found {int(negative_corr_count)} negatively correlated pairs - "
                "good for risk reduction",
            )

        # Position-specific recommendations
        for i, (pos, weight) in enumerate(zip(positions, weights, strict=False)):
            if weight < self.min_position_weight * 1.5:
                recommendations.append(
                    f"Consider removing {pos.strategy_name} (weight: {weight:.1%})",
                )
            elif weight > self.max_position_weight * 0.9:
                recommendations.append(
                    f"Consider trimming {pos.strategy_name} (weight: {weight:.1%})",
                )

        return recommendations

    def _get_position_returns(
        self,
        position: PositionData,
        historical_returns: pd.DataFrame,
    ) -> pd.Series:
        """Get historical returns for a position."""
        # Try different column naming conventions
        possible_columns = [
            position.position_id,
            position.strategy_name,
            f"{position.ticker}_{position.strategy_name}",
            position.ticker,
        ]

        for col in possible_columns:
            if col in historical_returns.columns:
                return historical_returns[col].dropna()

        # Return empty series if not found
        return pd.Series(dtype=float)

    def _single_position_result(
        self,
        position: PositionData | None,
    ) -> PortfolioOptimizationResult:
        """Create result for single position portfolio."""
        if position:
            return PortfolioOptimizationResult(
                optimal_weights={position.position_id: 1.0},
                expected_return=position.current_return,
                expected_risk=0.0,
                sharpe_ratio=0.0,
                correlation_benefit=0.0,
                diversification_ratio=1.0,
                recommendations=["Single position - no optimization possible"],
            )
        return PortfolioOptimizationResult(
            optimal_weights={},
            expected_return=0.0,
            expected_risk=0.0,
            sharpe_ratio=0.0,
            correlation_benefit=0.0,
            diversification_ratio=1.0,
            recommendations=["No positions to optimize"],
        )
