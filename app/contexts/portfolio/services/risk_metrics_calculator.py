"""
Risk Metrics Calculator Service

Unified service for calculating comprehensive risk metrics for portfolios
and trading strategies.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics for a portfolio or strategy."""

    # Value at Risk metrics
    var_95: float
    var_99: float
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    cvar_99: float

    # Volatility metrics
    volatility: float
    annualized_volatility: float
    downside_volatility: float

    # Drawdown metrics
    max_drawdown: float
    avg_drawdown: float
    max_drawdown_duration: int

    # Risk-adjusted returns
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Distribution metrics
    skewness: float
    kurtosis: float
    jarque_bera_pvalue: float

    # Tail risk metrics
    tail_ratio: float  # 95th percentile / 5th percentile
    maximum_loss: float

    # Additional metrics
    hit_ratio: float  # Percentage of positive returns
    pain_index: float  # Average drawdown over time


@dataclass
class PortfolioRiskProfile:
    """Complete risk profile for a portfolio."""

    risk_metrics: RiskMetrics
    confidence_intervals: dict[str, tuple[float, float]]
    stress_test_results: dict[str, float]
    risk_attribution: dict[str, float] | None = None


class RiskMetricsCalculator:
    """
    Service for calculating comprehensive risk metrics.

    Provides standardized risk calculations including:
    - Value at Risk (VaR) and Conditional VaR (CVaR)
    - Volatility and downside risk measures
    - Drawdown analysis
    - Risk-adjusted performance ratios
    - Distribution and tail risk analysis
    """

    def __init__(self, risk_free_rate: float = 0.0, logger=None):
        """
        Initialize risk metrics calculator.

        Args:
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
            logger: Optional logger instance
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logger

    def calculate_comprehensive_risk_metrics(
        self,
        returns: pd.Series | np.ndarray,
        prices: pd.Series | np.ndarray | None = None,
        frequency: int = 252,  # Trading days per year
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics for a returns series.

        Args:
            returns: Series of returns (daily, weekly, etc.)
            prices: Optional price series for drawdown calculations
            frequency: Number of periods per year for annualization

        Returns:
            RiskMetrics object with all calculated metrics
        """
        try:
            # Convert to numpy array for calculations
            if isinstance(returns, pd.Series):
                returns_array = returns.values
            else:
                returns_array = returns

            # Remove any NaN values
            returns_array = returns_array[~np.isnan(returns_array)]

            if len(returns_array) == 0:
                return self._get_empty_risk_metrics()

            # Calculate VaR and CVaR
            var_95, var_99, cvar_95, cvar_99 = self._calculate_var_cvar(returns_array)

            # Calculate volatility metrics
            volatility = np.std(returns_array)
            annualized_volatility = volatility * np.sqrt(frequency)
            downside_volatility = self._calculate_downside_volatility(
                returns_array, frequency
            )

            # Calculate drawdown metrics
            if prices is not None:
                max_dd, avg_dd, max_dd_duration = self._calculate_drawdown_metrics(
                    prices
                )
            else:
                # Estimate from returns if prices not available
                cumulative_returns = np.cumprod(1 + returns_array)
                max_dd, avg_dd, max_dd_duration = self._calculate_drawdown_from_returns(
                    cumulative_returns
                )

            # Calculate risk-adjusted ratios
            mean_return = np.mean(returns_array)
            sharpe_ratio = self._calculate_sharpe_ratio(returns_array, frequency)
            sortino_ratio = self._calculate_sortino_ratio(returns_array, frequency)
            calmar_ratio = self._calculate_calmar_ratio(mean_return, max_dd, frequency)

            # Calculate distribution metrics
            skewness = stats.skew(returns_array)
            kurtosis = stats.kurtosis(returns_array)
            jarque_bera_stat, jarque_bera_pvalue = stats.jarque_bera(returns_array)

            # Calculate tail risk metrics
            tail_ratio = self._calculate_tail_ratio(returns_array)
            maximum_loss = np.min(returns_array)

            # Calculate additional metrics
            hit_ratio = np.mean(returns_array > 0) * 100
            pain_index = self._calculate_pain_index(returns_array)

            return RiskMetrics(
                var_95=var_95,
                var_99=var_99,
                cvar_95=cvar_95,
                cvar_99=cvar_99,
                volatility=volatility,
                annualized_volatility=annualized_volatility,
                downside_volatility=downside_volatility,
                max_drawdown=max_dd,
                avg_drawdown=avg_dd,
                max_drawdown_duration=max_dd_duration,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                skewness=skewness,
                kurtosis=kurtosis,
                jarque_bera_pvalue=jarque_bera_pvalue,
                tail_ratio=tail_ratio,
                maximum_loss=maximum_loss,
                hit_ratio=hit_ratio,
                pain_index=pain_index,
            )

        except Exception as e:
            self._log(f"Error calculating risk metrics: {e!s}", "error")
            return self._get_empty_risk_metrics()

    def calculate_portfolio_risk_profile(
        self,
        returns: pd.Series | np.ndarray,
        prices: pd.Series | np.ndarray | None = None,
        confidence_level: float = 0.95,
        bootstrap_samples: int = 1000,
    ) -> PortfolioRiskProfile:
        """
        Calculate complete risk profile with confidence intervals.

        Args:
            returns: Returns series
            prices: Optional prices series
            confidence_level: Confidence level for intervals
            bootstrap_samples: Number of bootstrap samples

        Returns:
            PortfolioRiskProfile with metrics and confidence intervals
        """
        try:
            # Calculate base risk metrics
            risk_metrics = self.calculate_comprehensive_risk_metrics(returns, prices)

            # Calculate confidence intervals using bootstrap
            confidence_intervals = self._calculate_confidence_intervals(
                returns, confidence_level, bootstrap_samples
            )

            # Perform stress tests
            stress_test_results = self._perform_stress_tests(returns)

            return PortfolioRiskProfile(
                risk_metrics=risk_metrics,
                confidence_intervals=confidence_intervals,
                stress_test_results=stress_test_results,
            )

        except Exception as e:
            self._log(f"Error calculating portfolio risk profile: {e!s}", "error")
            return PortfolioRiskProfile(
                risk_metrics=self._get_empty_risk_metrics(),
                confidence_intervals={},
                stress_test_results={},
            )

    def _calculate_var_cvar(
        self, returns: np.ndarray
    ) -> tuple[float, float, float, float]:
        """Calculate Value at Risk and Conditional VaR at 95% and 99% levels."""
        try:
            if len(returns) == 0:
                return 0.0, 0.0, 0.0, 0.0

            # Sort returns for percentile calculations
            sorted_returns = np.sort(returns)

            # Calculate VaR (negative of percentile since we want losses)
            var_95 = -np.percentile(sorted_returns, 5)  # 95% VaR
            var_99 = -np.percentile(sorted_returns, 1)  # 99% VaR

            # Calculate CVaR (expected shortfall)
            # Average of returns beyond the VaR threshold
            var_95_threshold = np.percentile(sorted_returns, 5)
            var_99_threshold = np.percentile(sorted_returns, 1)

            tail_95 = sorted_returns[sorted_returns <= var_95_threshold]
            tail_99 = sorted_returns[sorted_returns <= var_99_threshold]

            cvar_95 = -np.mean(tail_95) if len(tail_95) > 0 else 0.0
            cvar_99 = -np.mean(tail_99) if len(tail_99) > 0 else 0.0

            return var_95, var_99, cvar_95, cvar_99

        except Exception as e:
            self._log(f"Error calculating VaR/CVaR: {e!s}", "warning")
            return 0.0, 0.0, 0.0, 0.0

    def _calculate_downside_volatility(
        self, returns: np.ndarray, frequency: int
    ) -> float:
        """Calculate downside volatility (volatility of negative returns only)."""
        try:
            negative_returns = returns[returns < 0]
            if len(negative_returns) == 0:
                return 0.0

            downside_vol = np.std(negative_returns) * np.sqrt(frequency)
            return downside_vol

        except Exception:
            return 0.0

    def _calculate_drawdown_metrics(
        self, prices: pd.Series | np.ndarray
    ) -> tuple[float, float, int]:
        """Calculate drawdown metrics from price series."""
        try:
            if isinstance(prices, pd.Series):
                prices_array = prices.values
            else:
                prices_array = prices

            # Calculate running maximum
            cummax = np.maximum.accumulate(prices_array)

            # Calculate drawdowns
            drawdowns = (prices_array - cummax) / cummax

            # Maximum drawdown
            max_drawdown = np.min(drawdowns)

            # Average drawdown
            negative_drawdowns = drawdowns[drawdowns < 0]
            avg_drawdown = (
                np.mean(negative_drawdowns) if len(negative_drawdowns) > 0 else 0.0
            )

            # Maximum drawdown duration
            max_dd_duration = self._calculate_max_drawdown_duration(drawdowns)

            return abs(max_drawdown), abs(avg_drawdown), max_dd_duration

        except Exception as e:
            self._log(f"Error calculating drawdown metrics: {e!s}", "warning")
            return 0.0, 0.0, 0

    def _calculate_drawdown_from_returns(
        self, cumulative_returns: np.ndarray
    ) -> tuple[float, float, int]:
        """Calculate drawdown metrics from cumulative returns."""
        try:
            return self._calculate_drawdown_metrics(cumulative_returns)
        except Exception:
            return 0.0, 0.0, 0

    def _calculate_max_drawdown_duration(self, drawdowns: np.ndarray) -> int:
        """Calculate maximum drawdown duration in periods."""
        try:
            current_duration = 0
            max_duration = 0

            for dd in drawdowns:
                if dd < 0:
                    current_duration += 1
                    max_duration = max(max_duration, current_duration)
                else:
                    current_duration = 0

            return max_duration

        except Exception:
            return 0

    def _calculate_sharpe_ratio(self, returns: np.ndarray, frequency: int) -> float:
        """Calculate Sharpe ratio."""
        try:
            if len(returns) < 2:
                return 0.0

            mean_return = np.mean(returns) * frequency
            std_return = np.std(returns) * np.sqrt(frequency)

            if std_return == 0:
                return 0.0

            return (mean_return - self.risk_free_rate) / std_return

        except Exception:
            return 0.0

    def _calculate_sortino_ratio(self, returns: np.ndarray, frequency: int) -> float:
        """Calculate Sortino ratio (using downside volatility)."""
        try:
            if len(returns) < 2:
                return 0.0

            mean_return = np.mean(returns) * frequency
            downside_vol = self._calculate_downside_volatility(returns, frequency)

            if downside_vol == 0:
                return 0.0

            return (mean_return - self.risk_free_rate) / downside_vol

        except Exception:
            return 0.0

    def _calculate_calmar_ratio(
        self, mean_return: float, max_drawdown: float, frequency: int
    ) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)."""
        try:
            annual_return = mean_return * frequency
            if max_drawdown == 0:
                return 0.0

            return annual_return / max_drawdown

        except Exception:
            return 0.0

    def _calculate_tail_ratio(self, returns: np.ndarray) -> float:
        """Calculate tail ratio (95th percentile / 5th percentile)."""
        try:
            if len(returns) < 20:  # Need sufficient data
                return 1.0

            p95 = np.percentile(returns, 95)
            p5 = np.percentile(returns, 5)

            if p5 == 0:
                return float("inf") if p95 > 0 else 1.0

            return abs(p95 / p5)

        except Exception:
            return 1.0

    def _calculate_pain_index(self, returns: np.ndarray) -> float:
        """Calculate pain index (average of squared drawdowns)."""
        try:
            cumulative_returns = np.cumprod(1 + returns)
            cummax = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - cummax) / cummax

            # Pain index is the square root of mean squared drawdowns
            pain_index = np.sqrt(np.mean(drawdowns**2))

            return pain_index

        except Exception:
            return 0.0

    def _calculate_confidence_intervals(
        self, returns: np.ndarray, confidence_level: float, bootstrap_samples: int
    ) -> dict[str, tuple[float, float]]:
        """Calculate confidence intervals for key metrics using bootstrap."""
        try:
            # Bootstrap sampling
            bootstrap_metrics = []

            for _ in range(bootstrap_samples):
                # Sample with replacement
                bootstrap_returns = np.random.choice(
                    returns, size=len(returns), replace=True
                )

                # Calculate metrics for this sample
                metrics = self.calculate_comprehensive_risk_metrics(bootstrap_returns)
                bootstrap_metrics.append(metrics)

            # Calculate confidence intervals
            alpha = 1 - confidence_level
            lower_percentile = (alpha / 2) * 100
            upper_percentile = (1 - alpha / 2) * 100

            confidence_intervals = {}

            # VaR confidence intervals
            var_95_values = [m.var_95 for m in bootstrap_metrics]
            confidence_intervals["var_95"] = (
                np.percentile(var_95_values, lower_percentile),
                np.percentile(var_95_values, upper_percentile),
            )

            # Sharpe ratio confidence intervals
            sharpe_values = [m.sharpe_ratio for m in bootstrap_metrics]
            confidence_intervals["sharpe_ratio"] = (
                np.percentile(sharpe_values, lower_percentile),
                np.percentile(sharpe_values, upper_percentile),
            )

            return confidence_intervals

        except Exception as e:
            self._log(f"Error calculating confidence intervals: {e!s}", "warning")
            return {}

    def _perform_stress_tests(self, returns: np.ndarray) -> dict[str, float]:
        """Perform stress tests on the returns."""
        try:
            stress_results = {}

            # Market crash scenario (-20% shock)
            stressed_returns = returns - 0.20
            crash_var_95 = -np.percentile(stressed_returns, 5)
            stress_results["market_crash_var_95"] = crash_var_95

            # High volatility scenario (double volatility)
            current_vol = np.std(returns)
            high_vol_returns = returns + np.random.normal(0, current_vol, len(returns))
            high_vol_var_95 = -np.percentile(high_vol_returns, 5)
            stress_results["high_volatility_var_95"] = high_vol_var_95

            # Tail risk scenario (focus on worst 5% of returns)
            worst_returns = np.percentile(returns, 5)
            stress_results["worst_case_scenario"] = worst_returns

            return stress_results

        except Exception as e:
            self._log(f"Error performing stress tests: {e!s}", "warning")
            return {}

    def _get_empty_risk_metrics(self) -> RiskMetrics:
        """Return empty risk metrics object for error cases."""
        return RiskMetrics(
            var_95=0.0,
            var_99=0.0,
            cvar_95=0.0,
            cvar_99=0.0,
            volatility=0.0,
            annualized_volatility=0.0,
            downside_volatility=0.0,
            max_drawdown=0.0,
            avg_drawdown=0.0,
            max_drawdown_duration=0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            skewness=0.0,
            kurtosis=0.0,
            jarque_bera_pvalue=1.0,
            tail_ratio=1.0,
            maximum_loss=0.0,
            hit_ratio=0.0,
            pain_index=0.0,
        )

    def _log(self, message: str, level: str = "info"):
        """Log message using provided logger or print."""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")
