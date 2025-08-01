"""
Market Data Analyzer for True Asset Distribution Analysis

This module provides comprehensive statistical analysis of underlying asset price data,
focusing on return distributions, volatility analysis, and risk metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import polars as pl
import yfinance as yf
from scipy import stats

from app.tools.data_types import DataConfig
from app.tools.enhanced_risk_assessment import (
    create_beta_calculator,
    create_risk_free_rate_provider,
    create_volatility_detector,
)
from app.tools.get_data import get_data
from app.tools.performance_attribution import create_performance_attributor
from app.tools.transaction_cost_analyzer import create_transaction_cost_analyzer
from app.tools.volume_liquidity_analyzer import create_volume_analyzer


class MarketDataAnalyzer:
    """
    Analyzer for market data and asset distribution characteristics.

    Performs statistical analysis on raw price data to understand underlying
    asset characteristics independent of trading strategies.
    """

    def __init__(self, ticker: str, logger: Optional[logging.Logger] = None):
        """Initialize market data analyzer."""
        self.ticker = ticker
        self.logger = logger or logging.getLogger(__name__)
        self.prices: Optional[pl.DataFrame] = None
        self.returns: Optional[np.ndarray] = None

        # Initialize enhanced risk assessment components
        self.risk_free_provider = create_risk_free_rate_provider()
        self.beta_calculator = create_beta_calculator()
        self.volatility_detector = create_volatility_detector()
        self.volume_analyzer = create_volume_analyzer(ticker, logger)
        self.performance_attributor = create_performance_attributor()
        self.transaction_cost_analyzer = create_transaction_cost_analyzer(logger)

    def fetch_data(self, period_days: int = 252 * 2) -> bool:
        """
        Fetch market data for the ticker.

        Args:
            period_days: Number of days of historical data to fetch

        Returns:
            True if data fetched successfully, False otherwise
        """
        try:
            self.logger.info(f"Fetching market data for {self.ticker}")

            # Create data config for smart caching
            config = DataConfig(
                TICKER=self.ticker,
                BASE_DIR="./",
                USE_HOURLY=False,
                REFRESH=False,  # Use cached data if available
                USE_YEARS=True,
                YEARS=period_days / 365,
            )

            # Use get_data for smart caching - will check cache first, only download if needed
            result = get_data(self.ticker, config, self.logger.info)

            # Handle both single DataFrame and tuple (DataFrame, synthetic_ticker) return types
            if isinstance(result, tuple):
                data, synthetic_ticker = result
                self.logger.info(f"Received synthetic ticker data: {synthetic_ticker}")
            else:
                data = result

            if data is None or data.is_empty():
                self.logger.error(f"No data received for {self.ticker}")
                return False

            self.prices = data
            self.logger.info(
                f"Successfully fetched {len(data)} data points for {self.ticker}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to fetch data for {self.ticker}: {e}")
            return False

    def calculate_returns(self) -> bool:
        """
        Calculate returns from price data.

        Returns:
            True if returns calculated successfully, False otherwise
        """
        if self.prices is None:
            self.logger.error("No price data available for return calculation")
            return False

        try:
            # Get closing prices
            if "Close" in self.prices.columns:
                prices = self.prices["Close"].to_numpy()
            elif "close" in self.prices.columns:
                prices = self.prices["close"].to_numpy()
            else:
                # Use first numeric column
                numeric_cols = self.prices.select(pl.col(pl.Float64, pl.Int64)).columns
                if not numeric_cols:
                    self.logger.error("No numeric price columns found")
                    return False
                prices = self.prices[numeric_cols[0]].to_numpy()

            # Calculate log returns
            self.returns = np.diff(np.log(prices))

            # Remove any NaN or infinite values
            self.returns = self.returns[np.isfinite(self.returns)]

            self.logger.info(f"Calculated {len(self.returns)} return observations")
            return True

        except Exception as e:
            self.logger.error(f"Failed to calculate returns: {e}")
            return False

    def analyze_distribution(self) -> Dict[str, Any]:
        """
        Perform comprehensive distribution analysis on returns.

        Returns:
            Dictionary containing distribution metrics and characteristics
        """
        if self.returns is None:
            self.logger.error("No returns data available for analysis")
            return {}

        try:
            returns = self.returns

            # Basic statistics
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            variance = np.var(returns)

            # Distribution shape
            skewness = stats.skew(returns)
            kurtosis_excess = stats.kurtosis(returns, fisher=True)  # Excess kurtosis

            # Quantiles and percentiles
            percentiles = np.percentile(returns, [1, 5, 10, 25, 50, 75, 90, 95, 99])

            # Risk metrics
            var_95 = np.percentile(returns, 5)  # 95% VaR (5th percentile)
            var_99 = np.percentile(returns, 1)  # 99% VaR (1st percentile)

            # Conditional VaR (Expected Shortfall)
            cvar_95 = np.mean(returns[returns <= var_95])
            cvar_99 = np.mean(returns[returns <= var_99])

            # Volatility measures (annualized)
            daily_vol = std_return
            annual_vol = daily_vol * np.sqrt(252)

            # Maximum drawdown approximation from returns
            cumulative_returns = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdown)

            # Normality test
            jarque_bera_stat, jarque_bera_pvalue = stats.jarque_bera(returns)

            # Distribution fitting
            dist_params = self._fit_distributions(returns)

            # Beta and market risk metrics
            beta_metrics = self.beta_calculator.calculate_beta(self.ticker, returns)

            # Volume and liquidity metrics
            volume_analysis = self.volume_analyzer.get_volume_analysis()

            # Momentum and trend metrics
            momentum_metrics = self._calculate_momentum_metrics(returns)
            trend_metrics = self._calculate_trend_metrics()
            risk_adjusted_metrics = self._calculate_risk_adjusted_metrics(
                mean_return, std_return
            )

            analysis_result = {
                # Basic statistics
                "sample_size": len(returns),
                "mean_daily_return": float(mean_return),
                "std_daily_return": float(std_return),
                "variance": float(variance),
                "annualized_volatility": float(annual_vol),
                # Distribution shape
                "skewness": float(skewness),
                "excess_kurtosis": float(kurtosis_excess),
                # Percentiles
                "percentile_1": float(percentiles[0]),
                "percentile_5": float(percentiles[1]),
                "percentile_10": float(percentiles[2]),
                "percentile_25": float(percentiles[3]),
                "median": float(percentiles[4]),
                "percentile_75": float(percentiles[5]),
                "percentile_90": float(percentiles[6]),
                "percentile_95": float(percentiles[7]),
                "percentile_99": float(percentiles[8]),
                # Risk metrics
                "var_95": float(var_95),
                "var_99": float(var_99),
                "cvar_95": float(cvar_95),
                "cvar_99": float(cvar_99),
                "max_drawdown_approx": float(max_drawdown),
                # Normality test
                "jarque_bera_statistic": float(jarque_bera_stat),
                "jarque_bera_pvalue": float(jarque_bera_pvalue),
                "is_normal_distribution": bool(jarque_bera_pvalue > 0.05),
                # Distribution fitting
                "best_fit_distribution": dist_params,
                # Beta and market risk metrics
                **beta_metrics,
                # Volume and liquidity metrics
                **volume_analysis,
                # Momentum and trend metrics
                **momentum_metrics,
                **trend_metrics,
                **risk_adjusted_metrics,
                # Meta information
                "analysis_timestamp": datetime.now().isoformat(),
                "ticker": self.ticker,
            }

            self.logger.info(f"Completed distribution analysis for {self.ticker}")
            return analysis_result

        except Exception as e:
            self.logger.error(f"Failed to analyze distribution: {e}")
            return {}

    def _fit_distributions(self, returns: np.ndarray) -> Dict[str, Any]:
        """
        Fit various distributions to the returns data.

        Args:
            returns: Array of return observations

        Returns:
            Dictionary with distribution fitting results
        """
        distributions = ["norm", "t", "skewnorm", "genextreme"]
        results = {}

        for dist_name in distributions:
            try:
                dist = getattr(stats, dist_name)
                params = dist.fit(returns)

                # Calculate goodness of fit (Kolmogorov-Smirnov test)
                ks_stat, ks_pvalue = stats.kstest(
                    returns, lambda x: dist.cdf(x, *params)
                )

                results[dist_name] = {
                    "parameters": [float(p) for p in params],
                    "ks_statistic": float(ks_stat),
                    "ks_pvalue": float(ks_pvalue),
                }

            except Exception as e:
                self.logger.warning(f"Failed to fit {dist_name} distribution: {e}")
                continue

        # Find best fitting distribution (highest p-value)
        if results:
            best_dist = max(results.keys(), key=lambda k: results[k]["ks_pvalue"])
            results["best_fit"] = best_dist

        return results

    def _calculate_momentum_metrics(self, returns: np.ndarray) -> Dict[str, Any]:
        """
        Calculate momentum-based metrics for trend identification.

        Args:
            returns: Array of return observations

        Returns:
            Dictionary with momentum metrics
        """
        try:
            # Recent vs historical performance (last 20% vs overall)
            split_point = int(len(returns) * 0.8)
            recent_returns = returns[split_point:]
            historical_returns = returns[:split_point]

            recent_mean = np.mean(recent_returns) if len(recent_returns) > 0 else 0
            historical_mean = (
                np.mean(historical_returns) if len(historical_returns) > 0 else 0
            )

            # Momentum score: recent performance vs historical
            momentum_differential = recent_mean - historical_mean

            # Rolling momentum calculation (multiple timeframes)
            momentum_5d = self._rolling_momentum(returns, 5)
            momentum_20d = self._rolling_momentum(returns, 20)
            momentum_60d = self._rolling_momentum(returns, 60)

            # Acceleration (second derivative of price trend)
            if len(returns) >= 10:
                cumulative_returns = np.cumprod(1 + returns)
                price_acceleration = np.diff(np.diff(cumulative_returns[-10:]))
                avg_acceleration = (
                    np.mean(price_acceleration) if len(price_acceleration) > 0 else 0
                )
            else:
                avg_acceleration = 0

            return {
                "momentum_differential": float(momentum_differential),
                "recent_avg_return": float(recent_mean),
                "historical_avg_return": float(historical_mean),
                "momentum_5d": float(momentum_5d),
                "momentum_20d": float(momentum_20d),
                "momentum_60d": float(momentum_60d),
                "price_acceleration": float(avg_acceleration),
            }

        except Exception as e:
            self.logger.warning(f"Failed to calculate momentum metrics: {e}")
            return {
                "momentum_differential": 0.0,
                "recent_avg_return": 0.0,
                "historical_avg_return": 0.0,
                "momentum_5d": 0.0,
                "momentum_20d": 0.0,
                "momentum_60d": 0.0,
                "price_acceleration": 0.0,
            }

    def _rolling_momentum(self, returns: np.ndarray, window: int) -> float:
        """Calculate rolling momentum over specified window."""
        if len(returns) < window:
            return 0.0

        recent_window = returns[-window:]
        return float(np.mean(recent_window))

    def _calculate_trend_metrics(self) -> Dict[str, Any]:
        """
        Calculate trend strength and direction metrics.

        Returns:
            Dictionary with trend metrics
        """
        try:
            if self.prices is None or len(self.prices) < 20:
                return self._default_trend_metrics()

            # Convert polars dataframe to pandas for .values access
            close_prices = self.prices.select("Close").to_pandas()["Close"].values

            # Moving averages for trend detection
            ma_20 = (
                np.mean(close_prices[-20:])
                if len(close_prices) >= 20
                else close_prices[-1]
            )
            ma_50 = np.mean(close_prices[-50:]) if len(close_prices) >= 50 else ma_20
            ma_200 = np.mean(close_prices[-200:]) if len(close_prices) >= 200 else ma_50

            current_price = close_prices[-1]

            # Trend direction (price relative to moving averages)
            trend_direction_20 = (current_price - ma_20) / ma_20 if ma_20 != 0 else 0
            trend_direction_50 = (current_price - ma_50) / ma_50 if ma_50 != 0 else 0
            trend_direction_200 = (
                (current_price - ma_200) / ma_200 if ma_200 != 0 else 0
            )

            # Trend consistency (how many days price was above/below MA)
            days_above_ma20 = (
                np.sum(close_prices[-20:] > ma_20) if len(close_prices) >= 20 else 0
            )
            trend_consistency = days_above_ma20 / 20 if len(close_prices) >= 20 else 0.5

            # Linear regression slope for trend strength
            if len(close_prices) >= 20:
                x = np.arange(20)
                slope, _ = np.polyfit(x, close_prices[-20:], 1)
                trend_slope = (
                    slope / ma_20 if ma_20 != 0 else 0
                )  # Normalize by price level
            else:
                trend_slope = 0

            return {
                "trend_direction_20d": float(trend_direction_20),
                "trend_direction_50d": float(trend_direction_50),
                "trend_direction_200d": float(trend_direction_200),
                "trend_consistency": float(trend_consistency),
                "trend_slope": float(trend_slope),
                "ma_20": float(ma_20),
                "ma_50": float(ma_50),
                "ma_200": float(ma_200),
                "current_price": float(current_price),
            }

        except Exception as e:
            self.logger.warning(f"Failed to calculate trend metrics: {e}")
            return self._default_trend_metrics()

    def _default_trend_metrics(self) -> Dict[str, Any]:
        """Return default trend metrics when calculation fails."""
        return {
            "trend_direction_20d": 0.0,
            "trend_direction_50d": 0.0,
            "trend_direction_200d": 0.0,
            "trend_consistency": 0.5,
            "trend_slope": 0.0,
            "ma_20": 0.0,
            "ma_50": 0.0,
            "ma_200": 0.0,
            "current_price": 0.0,
        }

    def _calculate_risk_adjusted_metrics(
        self, mean_return: float, std_return: float
    ) -> Dict[str, Any]:
        """
        Calculate risk-adjusted return metrics.

        Args:
            mean_return: Mean daily return
            std_return: Standard deviation of daily returns

        Returns:
            Dictionary with risk-adjusted metrics
        """
        try:
            # Get dynamic risk-free rate
            volatility_regime, _, _ = self.volatility_detector.detect_regime()
            rf_data = self.risk_free_provider.get_current_risk_free_rate(
                volatility_regime
            )
            risk_free_rate = rf_data.rate / 252  # Convert annual to daily

            excess_return = mean_return - risk_free_rate
            sharpe_ratio = excess_return / std_return if std_return != 0 else 0

            # Annualized Sharpe ratio
            annualized_sharpe = sharpe_ratio * np.sqrt(252)

            # Sortino ratio (downside deviation)
            if self.returns is not None:
                downside_returns = self.returns[self.returns < 0]
                downside_std = (
                    np.std(downside_returns)
                    if len(downside_returns) > 0
                    else std_return
                )
                sortino_ratio = excess_return / downside_std if downside_std != 0 else 0
                annualized_sortino = sortino_ratio * np.sqrt(252)
            else:
                sortino_ratio = 0
                annualized_sortino = 0

            # Return to risk ratio
            return_to_risk = abs(mean_return / std_return) if std_return != 0 else 0

            return {
                "sharpe_ratio": float(sharpe_ratio),
                "annualized_sharpe": float(annualized_sharpe),
                "sortino_ratio": float(sortino_ratio),
                "annualized_sortino": float(annualized_sortino),
                "return_to_risk_ratio": float(return_to_risk),
            }

        except Exception as e:
            self.logger.warning(f"Failed to calculate risk-adjusted metrics: {e}")
            return {
                "sharpe_ratio": 0.0,
                "annualized_sharpe": 0.0,
                "sortino_ratio": 0.0,
                "annualized_sortino": 0.0,
                "return_to_risk_ratio": 0.0,
            }

    def generate_recommendation(
        self, analysis: Dict[str, Any], include_components: bool = False
    ) -> Union[Tuple[str, float, str], Tuple[str, float, str, Dict[str, float]]]:
        """
        Generate comprehensive recommendation based on asset analysis.

        Args:
            analysis: Complete distribution and trend analysis results
            include_components: If True, return component scores as fourth element

        Returns:
            Tuple of (recommendation, confidence, reasoning) or
            (recommendation, confidence, reasoning, component_scores) if include_components=True
        """
        if not analysis:
            base_result = ("HOLD", 0.5, "Insufficient data for analysis")
            if include_components:
                return base_result + ({},)
            return base_result

        try:
            # Extract key metrics for legacy risk scoring
            annual_vol = analysis.get("annualized_volatility", 0)
            skewness = analysis.get("skewness", 0)
            excess_kurtosis = analysis.get("excess_kurtosis", 0)
            var_95 = analysis.get("var_95", 0)
            is_normal = analysis.get("is_normal_distribution", True)

            # Legacy risk scoring components (0-100, higher = more risk)
            volatility_score = self._score_volatility(annual_vol)
            tail_risk_score = self._score_tail_risk(var_95, excess_kurtosis)
            distribution_score = self._score_distribution_shape(
                skewness, excess_kurtosis, is_normal
            )

            # Market beta risk adjustment
            beta = analysis.get("beta", 1.0)
            systematic_risk_pct = analysis.get("systematic_risk_pct", 0.5)
            beta_risk_adjustment = self._calculate_beta_risk_adjustment(
                beta, systematic_risk_pct
            )

            # Combine risk components with beta adjustment
            base_risk_score = (
                volatility_score + tail_risk_score + distribution_score
            ) / 3
            risk_score = base_risk_score * beta_risk_adjustment

            # New positive scoring components (-100 to +100)
            momentum_score = self._score_momentum(analysis)
            trend_score = self._score_trend_strength(analysis)
            risk_adj_score = self._score_risk_adjusted_returns(analysis)
            mean_rev_score = self._score_mean_reversion(analysis)
            volume_score = analysis.get("volume_score", 0)  # From volume analyzer

            # Combine scores into overall recommendation score (-100 to +100)
            # Risk converts to negative score component
            risk_component = -(risk_score - 50)  # Convert 0-100 risk to -50 to +50

            # Get volatility regime for dynamic weight adjustments
            (
                volatility_regime,
                current_vix,
                regime_data,
            ) = self.volatility_detector.detect_regime()
            weight_adjustments = regime_data.get("weight_adjustments", {})

            # Apply dynamic weight adjustments based on market regime (rebalanced for better signal distribution)
            base_weights = {
                "risk": 0.25,
                "momentum": 0.20,
                "trend": 0.25,
                "risk_adj": 0.18,
                "mean_rev": 0.05,
                "volume": 0.07,
            }

            adjusted_weights = {}
            for factor, base_weight in base_weights.items():
                adjustment = weight_adjustments.get(factor, 1.0)
                adjusted_weights[factor] = base_weight * adjustment

            # Normalize weights to ensure they sum to 1.0
            total_weight = sum(adjusted_weights.values())
            normalized_weights = {
                k: v / total_weight for k, v in adjusted_weights.items()
            }

            # Optimized weighted combination with dynamic adjustments
            overall_score = (
                risk_component * normalized_weights["risk"]
                + momentum_score * normalized_weights["momentum"]
                + trend_score * normalized_weights["trend"]
                + risk_adj_score * normalized_weights["risk_adj"]
                + mean_rev_score * normalized_weights["mean_rev"]
                + volume_score * normalized_weights["volume"]
            )

            # Cap final score
            overall_score = max(-100, min(100, overall_score))

            # Use already fetched regime data for threshold adjustments
            threshold_adjustments = regime_data.get("threshold_adjustments", {})

            # Apply regime-aware threshold adjustments (recalibrated based on actual score ranges)
            strong_buy_threshold = 20 + threshold_adjustments.get("strong_buy", 0)
            buy_threshold = 8 + threshold_adjustments.get("buy", 0)
            sell_threshold = -8 + threshold_adjustments.get("sell", 0)
            strong_sell_threshold = -20 + threshold_adjustments.get("strong_sell", 0)

            # Generate recommendation and confidence with regime-aware thresholds
            if overall_score >= strong_buy_threshold:
                signal = "STRONG_BUY"
                confidence = (
                    0.80 + (overall_score - strong_buy_threshold) * 0.003
                )  # 0.80-0.92
                reasoning = f"Strong positive indicators: trend={trend_score:.0f}, momentum={momentum_score:.0f} (VIX regime: {volatility_regime})"
            elif overall_score >= buy_threshold:
                signal = "BUY"
                confidence = (
                    0.70 + (overall_score - buy_threshold) * 0.0025
                )  # 0.70-0.80
                reasoning = f"Positive outlook: trend={trend_score:.0f}, risk={risk_score:.0f} (VIX regime: {volatility_regime})"
            elif overall_score >= sell_threshold:
                signal = "HOLD"
                confidence = 0.60 + abs(overall_score) * 0.005  # 0.60-0.70
                reasoning = f"Mixed signals: score={overall_score:.0f}, vol={annual_vol:.1%} (VIX regime: {volatility_regime})"
            elif overall_score >= strong_sell_threshold:
                signal = "SELL"
                confidence = (
                    0.70 + (abs(overall_score) - abs(sell_threshold)) * 0.0025
                )  # 0.70-0.80
                reasoning = f"Negative indicators: risk={risk_score:.0f}, trend={trend_score:.0f} (VIX regime: {volatility_regime})"
            else:
                signal = "STRONG_SELL"
                confidence = (
                    0.80 + (abs(overall_score) - abs(strong_sell_threshold)) * 0.003
                )  # 0.80-0.92
                reasoning = f"Strong negative signals: high risk={risk_score:.0f}, poor momentum (VIX regime: {volatility_regime})"

            # Integrate transaction cost analysis
            volume_analysis_data = analysis.get("volume_metrics", {})
            current_price = analysis.get("current_price", 100.0)

            cost_estimate = self.transaction_cost_analyzer.estimate_transaction_costs(
                self.ticker, signal, volume_analysis_data, current_price
            )

            # Adjust signal and confidence based on transaction costs
            (
                final_signal,
                final_confidence,
                cost_reasoning,
            ) = self.transaction_cost_analyzer.adjust_signal_for_costs(
                signal, confidence, cost_estimate
            )

            # Combine original reasoning with cost reasoning
            final_reasoning = f"{reasoning}; {cost_reasoning}"

            base_result = (final_signal, min(final_confidence, 0.95), final_reasoning)

            if include_components:
                # Component scores for detailed analysis
                component_scores = {
                    "risk_score": float(risk_component),
                    "momentum_score": float(momentum_score),
                    "trend_score": float(trend_score),
                    "risk_adjusted_score": float(risk_adj_score),
                    "mean_reversion_score": float(mean_rev_score),
                    "volume_liquidity_score": float(volume_score),
                    "overall_score": float(overall_score),
                    # Include raw components for debugging
                    "raw_risk_score": float(risk_score),
                    "volatility_score": float(volatility_score),
                    "tail_risk_score": float(tail_risk_score),
                    "distribution_score": float(distribution_score),
                    "beta_risk_adjustment": float(beta_risk_adjustment),
                    # Regime information and dynamic weights
                    "volatility_regime": volatility_regime,
                    "current_vix": float(current_vix),
                    "threshold_adjustments": threshold_adjustments,
                    "weight_adjustments": weight_adjustments,
                    "base_weights": base_weights,
                    "normalized_weights": normalized_weights,
                    # Dynamic weighted contributions
                    "risk_contribution": float(
                        risk_component * normalized_weights["risk"]
                    ),
                    "momentum_contribution": float(
                        momentum_score * normalized_weights["momentum"]
                    ),
                    "trend_contribution": float(
                        trend_score * normalized_weights["trend"]
                    ),
                    "risk_adjusted_contribution": float(
                        risk_adj_score * normalized_weights["risk_adj"]
                    ),
                    "mean_reversion_contribution": float(
                        mean_rev_score * normalized_weights["mean_rev"]
                    ),
                    "volume_contribution": float(
                        volume_score * normalized_weights["volume"]
                    ),
                }

                # Add transaction cost information to component scores
                component_scores["transaction_cost_analysis"] = {
                    "estimated_spread_bps": cost_estimate.estimated_spread,
                    "market_impact_bps": cost_estimate.market_impact,
                    "commission_bps": cost_estimate.commission,
                    "total_cost_bps": cost_estimate.total_cost_bps,
                    "liquidity_penalty_bps": cost_estimate.liquidity_penalty,
                    "turnover_penalty_bps": cost_estimate.turnover_penalty,
                    "cost_adjusted_confidence": cost_estimate.cost_adjusted_confidence,
                    "original_signal": signal,
                    "cost_adjusted_signal": final_signal,
                    "confidence_impact": final_confidence - confidence,
                }

                # Perform performance attribution analysis
                attribution_result = self.performance_attributor.analyze_attribution(
                    component_scores,
                    {
                        **analysis,
                        "exit_signal": final_signal,
                        "confidence_level": final_confidence,
                    },
                )

                # Add attribution information to component scores
                component_scores["performance_attribution"] = {
                    "factor_performance": [
                        {
                            "factor": f.factor_name,
                            "contribution": f.contribution,
                            "weight": f.weight,
                            "score": f.score,
                            "performance_metrics": f.performance_metrics,
                        }
                        for f in attribution_result.factors
                    ],
                    "performance_summary": attribution_result.performance_summary,
                    "attribution_timestamp": attribution_result.timestamp.isoformat(),
                }

                return base_result + (component_scores,)

            return base_result

        except Exception as e:
            self.logger.error(f"Failed to generate recommendation: {e}")
            return "HOLD", 0.50, f"Recommendation generation error: {str(e)}"

    def generate_exit_signal(self, analysis: Dict[str, Any]) -> Tuple[str, float, str]:
        """
        Legacy method for backward compatibility.
        Calls generate_recommendation internally.
        """
        return self.generate_recommendation(analysis)

    def _score_volatility(self, annual_vol: float) -> float:
        """Score volatility component (0-100)."""
        if annual_vol > 0.80:  # >80% annual volatility
            return 100
        elif annual_vol > 0.60:  # >60% annual volatility
            return 80 + (annual_vol - 0.60) * 100  # 80-100
        elif annual_vol > 0.40:  # >40% annual volatility
            return 60 + (annual_vol - 0.40) * 100  # 60-80
        elif annual_vol > 0.20:  # >20% annual volatility
            return 30 + (annual_vol - 0.20) * 150  # 30-60
        else:
            return annual_vol * 150  # 0-30

    def _score_tail_risk(self, var_95: float, excess_kurtosis: float) -> float:
        """Score tail risk component (0-100)."""
        # VaR component (more negative = higher risk)
        var_score = min(
            100, max(0, (-var_95 - 0.02) * 2000)
        )  # -2% daily VaR = 40 points

        # Kurtosis component (fat tails = higher risk)
        kurtosis_score = min(
            100, max(0, excess_kurtosis * 10)
        )  # Excess kurtosis of 10 = 100 points

        return (var_score + kurtosis_score) / 2

    def _score_distribution_shape(
        self, skewness: float, excess_kurtosis: float, is_normal: bool
    ) -> float:
        """Score distribution shape component (0-100)."""
        # Skewness penalty (extreme skewness is concerning)
        skew_score = min(100, abs(skewness) * 30)  # |skewness| of 3.33 = 100 points

        # Kurtosis penalty
        kurtosis_score = min(
            100, max(0, excess_kurtosis * 5)
        )  # Excess kurtosis of 20 = 100 points

        # Non-normality penalty
        normal_penalty = 0 if is_normal else 25

        return (skew_score + kurtosis_score + normal_penalty) / 3

    def _calculate_beta_risk_adjustment(
        self, beta: float, systematic_risk_pct: float
    ) -> float:
        """Calculate risk adjustment factor based on market beta."""
        # Base adjustment for beta deviation from 1.0
        beta_deviation = abs(beta - 1.0)
        beta_adjustment = 1 + (beta_deviation * 0.3)  # Up to 30% adjustment

        # Additional adjustment for systematic risk concentration
        # High systematic risk (>70%) increases risk, low systematic risk (<30%) decreases risk
        if systematic_risk_pct > 0.7:
            systematic_adjustment = (
                1 + (systematic_risk_pct - 0.7) * 0.5
            )  # Up to 15% increase
        elif systematic_risk_pct < 0.3:
            systematic_adjustment = (
                1 - (0.3 - systematic_risk_pct) * 0.3
            )  # Up to 9% decrease
        else:
            systematic_adjustment = 1.0

        # Combine adjustments
        total_adjustment = beta_adjustment * systematic_adjustment

        # Cap adjustment between 0.7 and 1.5
        return max(0.7, min(1.5, total_adjustment))

    def _score_momentum(self, analysis: Dict[str, Any]) -> float:
        """Score momentum component (-100 to +100) with volatility adjustment."""
        try:
            momentum_diff = analysis.get("momentum_differential", 0)
            momentum_5d = analysis.get("momentum_5d", 0)
            momentum_20d = analysis.get("momentum_20d", 0)
            acceleration = analysis.get("price_acceleration", 0)
            annual_vol = analysis.get(
                "annualized_volatility", 0.2
            )  # Default 20% volatility

            # Volatility adjustment factor (reduce momentum signals in high volatility)
            vol_adjustment = 1 / (
                1 + max(0, annual_vol - 0.15)
            )  # Adjust for volatility > 15%

            # Recent vs historical momentum (higher recent = positive) - optimized multipliers
            momentum_score = momentum_diff * 5000 * vol_adjustment

            # Short-term momentum boost (more sensitive to volatility) - optimized multipliers
            short_term_score = momentum_5d * 2500 * vol_adjustment

            # Medium-term momentum (less sensitive to volatility) - optimized multipliers
            medium_term_score = momentum_20d * 1250 * (vol_adjustment + 0.3)

            # Price acceleration bonus/penalty (highly sensitive to volatility) - optimized multipliers
            acceleration_score = acceleration * 500 * vol_adjustment * 0.7

            total_score = (
                momentum_score
                + short_term_score
                + medium_term_score
                + acceleration_score
            )

            # Cap at [-100, +100]
            return max(-100, min(100, total_score))

        except Exception:
            return 0.0

    def _score_trend_strength(self, analysis: Dict[str, Any]) -> float:
        """Score trend strength component (-100 to +100)."""
        try:
            trend_20d = analysis.get("trend_direction_20d", 0)
            trend_50d = analysis.get("trend_direction_50d", 0)
            trend_200d = analysis.get("trend_direction_200d", 0)
            trend_consistency = analysis.get("trend_consistency", 0.5)
            trend_slope = analysis.get("trend_slope", 0)

            # Trend direction scores (positive when price above MA) - optimized multipliers
            trend_20_score = trend_20d * 120  # 10% above 20-day MA = 12 points
            trend_50_score = trend_50d * 90  # 10% above 50-day MA = 9 points
            trend_200_score = trend_200d * 60  # 10% above 200-day MA = 6 points

            # Trend consistency (>0.5 = uptrend, <0.5 = downtrend) - optimized multiplier
            consistency_score = (trend_consistency - 0.5) * 120  # Range: -60 to +60

            # Trend slope (normalized) - optimized multiplier
            slope_score = trend_slope * 600

            # Weight shorter-term trends more heavily
            weighted_score = (
                trend_20_score * 0.4
                + trend_50_score * 0.3
                + trend_200_score * 0.2
                + consistency_score * 0.05
                + slope_score * 0.05
            )

            # Cap at [-100, +100]
            return max(-100, min(100, weighted_score))

        except Exception:
            return 0.0

    def _score_risk_adjusted_returns(self, analysis: Dict[str, Any]) -> float:
        """Score risk-adjusted returns component (-100 to +100)."""
        try:
            sharpe_ratio = analysis.get("annualized_sharpe", 0)
            sortino_ratio = analysis.get("annualized_sortino", 0)
            return_to_risk = analysis.get("return_to_risk_ratio", 0)
            mean_return = analysis.get("mean_daily_return", 0)

            # Sharpe ratio scoring (>1.0 is good, >2.0 is excellent)
            if sharpe_ratio > 2.0:
                sharpe_score = 50 + (sharpe_ratio - 2.0) * 25  # 50-100 range
            elif sharpe_ratio > 1.0:
                sharpe_score = (sharpe_ratio - 1.0) * 50  # 0-50 range
            elif sharpe_ratio > 0:
                sharpe_score = sharpe_ratio * 25 - 25  # -25 to 0 range
            else:
                sharpe_score = max(-50, sharpe_ratio * 25)  # -50 to -25 range

            # Sortino ratio (similar to Sharpe but focuses on downside)
            sortino_score = min(50, max(-50, sortino_ratio * 25))

            # Raw return component - optimized multiplier
            return_score = mean_return * 5000  # Daily return to score

            # Combined score
            total_score = sharpe_score * 0.5 + sortino_score * 0.3 + return_score * 0.2

            # Cap at [-100, +100]
            return max(-100, min(100, total_score))

        except Exception:
            return 0.0

    def _score_mean_reversion(self, analysis: Dict[str, Any]) -> float:
        """Score mean reversion opportunities (-100 to +100) with bidirectional signals."""
        try:
            var_95 = analysis.get("var_95", 0)
            var_5 = analysis.get("percentile_5", 0)  # 5th percentile for overbought
            current_vs_mean = analysis.get("trend_direction_20d", 0)
            volatility = analysis.get("annualized_volatility", 0)
            percentile_95 = analysis.get("percentile_95", 0)

            total_score = 0

            # Oversold conditions (positive scores for buying opportunities)
            if var_95 < -0.05:  # More than 5% daily loss in 5th percentile
                oversold_score = min(50, abs(var_95) * 500)  # Potential bounce
                total_score += oversold_score

            # Price significantly below recent average (potential bounce)
            if current_vs_mean < -0.1:  # More than 10% below 20-day MA
                mean_reversion_buy_score = min(30, abs(current_vs_mean) * 200)
                total_score += mean_reversion_buy_score

            # Overbought conditions (negative scores for selling opportunities)
            if percentile_95 > 0.05:  # More than 5% daily gain in 95th percentile
                overbought_score = -min(50, percentile_95 * 500)  # Potential pullback
                total_score += overbought_score

            # Price significantly above recent average (potential pullback)
            if current_vs_mean > 0.1:  # More than 10% above 20-day MA
                mean_reversion_sell_score = -min(30, current_vs_mean * 200)
                total_score += mean_reversion_sell_score

            # High volatility increases mean reversion potential (bidirectional)
            if volatility > 0.3:
                vol_boost = min(20, (volatility - 0.3) * 50)
                if total_score > 0:
                    total_score += vol_boost  # Boost buy signals
                elif total_score < 0:
                    total_score -= vol_boost  # Boost sell signals
                else:
                    total_score += vol_boost * 0.5  # Neutral boost for high volatility

            # Statistical significance check using volatility regime
            if volatility > 0.5:  # Very high volatility
                total_score *= 1.2  # Increase mean reversion signals
            elif volatility < 0.1:  # Very low volatility
                total_score *= 0.7  # Decrease mean reversion signals

            # Cap at [-100, +100]
            return max(-100, min(100, total_score))

        except Exception:
            return 0.0

    async def analyze(
        self, period_days: int = 252 * 2, include_components: bool = False
    ) -> Dict[str, Any]:
        """
        Perform complete market data analysis.

        Args:
            period_days: Number of days of historical data to analyze
            include_components: If True, include detailed component scores

        Returns:
            Complete analysis results including exit signal and optionally component scores
        """
        self.logger.info(f"Starting market data analysis for {self.ticker}")

        # Fetch data
        if not self.fetch_data(period_days):
            return {
                "error": "Failed to fetch market data",
                "ticker": self.ticker,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        # Calculate returns
        if not self.calculate_returns():
            return {
                "error": "Failed to calculate returns",
                "ticker": self.ticker,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        # Analyze distribution
        analysis = self.analyze_distribution()
        if not analysis:
            return {
                "error": "Failed to analyze distribution",
                "ticker": self.ticker,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        # Generate recommendation with optional component scores
        recommendation_result = self.generate_recommendation(
            analysis, include_components
        )

        if include_components and len(recommendation_result) == 4:
            signal, confidence, reasoning, component_scores = recommendation_result
        else:
            signal, confidence, reasoning = recommendation_result[:3]
            component_scores = None

        # Combine results
        result = {
            **analysis,
            "exit_signal": signal,  # Keep for backward compatibility
            "recommendation": signal,  # New field name
            "confidence_level": confidence,
            "signal_reasoning": reasoning,
            "p_value": max(0.01, 1.0 - confidence),
            "data_source": "MARKET_DATA",
            "analysis_mode": "ASSET_DISTRIBUTION",
        }

        # Add component scores if requested
        if component_scores:
            result["component_scores"] = component_scores

        self.logger.info(
            f"Completed market data analysis for {self.ticker}: {signal} ({confidence:.1%})"
        )
        return result


def create_market_data_analyzer(
    ticker: str, logger: Optional[logging.Logger] = None
) -> MarketDataAnalyzer:
    """
    Create a market data analyzer instance.

    Args:
        ticker: Stock ticker symbol
        logger: Optional logger instance

    Returns:
        MarketDataAnalyzer instance
    """
    return MarketDataAnalyzer(ticker, logger)
