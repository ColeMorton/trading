"""
Enhanced Risk Assessment Module for SPDS

This module provides advanced risk assessment capabilities including:
- Dynamic risk-free rate calculation using real-time Treasury rates
- Market beta calculation and risk adjustment
- Volatility regime detection and adjustment
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import yfinance as yf


@dataclass
class RiskFreeRateData:
    """Data class for risk-free rate information."""

    rate: float
    source: str
    timestamp: datetime
    maturity: str = "3M"
    is_fallback: bool = False


class DynamicRiskFreeRateProvider:
    """
    Provider for dynamic risk-free rate calculation.

    Fetches real-time Treasury rates with fallback mechanisms and caching.
    """

    def __init__(self, cache_dir: str = "./cache", cache_ttl_hours: int = 6):
        """
        Initialize the risk-free rate provider.

        Args:
            cache_dir: Directory for caching rate data
            cache_ttl_hours: Time-to-live for cached rates in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.logger = logging.getLogger(__name__)

        # Fallback rates for different scenarios
        self.fallback_rates = {
            "default": 0.02,  # 2% annual
            "high_vol": 0.025,  # 2.5% in high volatility periods
            "crisis": 0.01,  # 1% during crisis periods
        }

    def get_current_risk_free_rate(
        self, volatility_regime: str = "normal"
    ) -> RiskFreeRateData:
        """
        Get current risk-free rate with caching and fallback.

        Args:
            volatility_regime: Current market volatility regime

        Returns:
            RiskFreeRateData object with rate information
        """
        # Try to get from cache first
        cached_rate = self._get_cached_rate()
        if cached_rate and not self._is_cache_expired(cached_rate):
            self.logger.debug(f"Using cached risk-free rate: {cached_rate.rate:.3%}")
            return cached_rate

        # Try to fetch live data
        live_rate = self._fetch_live_treasury_rate()
        if live_rate:
            self._cache_rate(live_rate)
            return live_rate

        # Use fallback with volatility adjustment
        fallback_rate = self._get_fallback_rate(volatility_regime)
        self.logger.warning(f"Using fallback risk-free rate: {fallback_rate.rate:.3%}")
        return fallback_rate

    def _fetch_live_treasury_rate(self) -> RiskFreeRateData | None:
        """Fetch live Treasury rate data."""
        try:
            # Fetch 3-month Treasury bill rate (^IRX)
            treasury_3m = yf.Ticker("^IRX")
            hist = treasury_3m.history(period="5d")

            if hist.empty:
                self.logger.warning("No Treasury rate data available")
                return None

            # Get most recent rate
            latest_rate = (
                hist["Close"].iloc[-1] / 100.0
            )  # Convert percentage to decimal

            return RiskFreeRateData(
                rate=float(latest_rate),
                source="^IRX (3M Treasury)",
                timestamp=datetime.now(),
                maturity="3M",
                is_fallback=False,
            )

        except Exception as e:
            self.logger.error(f"Failed to fetch live Treasury rate: {e}")
            return None

    def _get_cached_rate(self) -> RiskFreeRateData | None:
        """Load cached rate data."""
        cache_file = self.cache_dir / "risk_free_rate.json"

        try:
            if not cache_file.exists():
                return None

            with open(cache_file) as f:
                data = json.load(f)

            return RiskFreeRateData(
                rate=data["rate"],
                source=data["source"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                maturity=data.get("maturity", "3M"),
                is_fallback=data.get("is_fallback", False),
            )

        except Exception as e:
            self.logger.warning(f"Failed to load cached rate: {e}")
            return None

    def _cache_rate(self, rate_data: RiskFreeRateData) -> None:
        """Cache rate data."""
        cache_file = self.cache_dir / "risk_free_rate.json"

        try:
            data = {
                "rate": rate_data.rate,
                "source": rate_data.source,
                "timestamp": rate_data.timestamp.isoformat(),
                "maturity": rate_data.maturity,
                "is_fallback": rate_data.is_fallback,
            }

            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.warning(f"Failed to cache rate: {e}")

    def _is_cache_expired(self, rate_data: RiskFreeRateData) -> bool:
        """Check if cached rate is expired."""
        return datetime.now() - rate_data.timestamp > self.cache_ttl

    def _get_fallback_rate(self, volatility_regime: str) -> RiskFreeRateData:
        """Get fallback rate based on volatility regime."""
        if volatility_regime == "high":
            rate = self.fallback_rates["high_vol"]
        elif volatility_regime == "crisis":
            rate = self.fallback_rates["crisis"]
        else:
            rate = self.fallback_rates["default"]

        return RiskFreeRateData(
            rate=rate,
            source=f"Fallback ({volatility_regime} regime)",
            timestamp=datetime.now(),
            maturity="3M",
            is_fallback=True,
        )


class MarketBetaCalculator:
    """
    Calculator for market beta and systematic risk metrics.
    """

    def __init__(self, market_index: str = "SPY", lookback_days: int = 252):
        """
        Initialize beta calculator.

        Args:
            market_index: Market index ticker for beta calculation
            lookback_days: Number of days for beta calculation
        """
        self.market_index = market_index
        self.lookback_days = lookback_days
        self.logger = logging.getLogger(__name__)

    def calculate_beta(
        self, ticker: str, returns: np.ndarray | None = None
    ) -> dict[str, float]:
        """
        Calculate market beta and related metrics.

        Args:
            ticker: Stock ticker
            returns: Optional pre-calculated returns array

        Returns:
            Dictionary with beta metrics
        """
        try:
            if returns is None:
                # Fetch stock data
                stock = yf.Ticker(ticker)
                stock_hist = stock.history(period=f"{self.lookback_days + 50}d")

                if stock_hist.empty:
                    return self._default_beta_metrics()

                stock_returns = np.diff(np.log(stock_hist["Close"].values))
            else:
                stock_returns = returns

            # Fetch market data
            market = yf.Ticker(self.market_index)
            market_hist = market.history(period=f"{self.lookback_days + 50}d")

            if market_hist.empty:
                return self._default_beta_metrics()

            market_returns = np.diff(np.log(market_hist["Close"].values))

            # Align data lengths
            min_length = min(len(stock_returns), len(market_returns))
            stock_returns = stock_returns[-min_length:]
            market_returns = market_returns[-min_length:]

            if min_length < 30:  # Minimum data requirement
                return self._default_beta_metrics()

            # Calculate beta and related metrics
            covariance = np.cov(stock_returns, market_returns)[0, 1]
            market_variance = np.var(market_returns)

            beta = covariance / market_variance if market_variance > 0 else 1.0

            # R-squared (correlation squared)
            correlation = np.corrcoef(stock_returns, market_returns)[0, 1]
            r_squared = correlation**2 if not np.isnan(correlation) else 0.0

            # Alpha calculation
            stock_mean = np.mean(stock_returns)
            market_mean = np.mean(market_returns)
            alpha = stock_mean - beta * market_mean

            # Systematic vs idiosyncratic risk
            systematic_risk = beta**2 * np.var(market_returns)
            total_risk = np.var(stock_returns)
            idiosyncratic_risk = total_risk - systematic_risk

            return {
                "beta": float(beta),
                "alpha": float(alpha),
                "r_squared": float(r_squared),
                "correlation": float(correlation),
                "systematic_risk": float(systematic_risk),
                "idiosyncratic_risk": float(max(0, idiosyncratic_risk)),
                "total_risk": float(total_risk),
                "systematic_risk_pct": (
                    float(systematic_risk / total_risk) if total_risk > 0 else 0.0
                ),
            }

        except Exception as e:
            self.logger.error(f"Beta calculation failed for {ticker}: {e}")
            return self._default_beta_metrics()

    def _default_beta_metrics(self) -> dict[str, float]:
        """Return default beta metrics when calculation fails."""
        return {
            "beta": 1.0,
            "alpha": 0.0,
            "r_squared": 0.5,
            "correlation": 0.7,
            "systematic_risk": 0.5,
            "idiosyncratic_risk": 0.5,
            "total_risk": 1.0,
            "systematic_risk_pct": 0.5,
        }


class VolatilityRegimeDetector:
    """
    Detector for market volatility regimes.
    """

    def __init__(self, vix_ticker: str = "^VIX"):
        """
        Initialize volatility regime detector.

        Args:
            vix_ticker: VIX ticker symbol
        """
        self.vix_ticker = vix_ticker
        self.logger = logging.getLogger(__name__)

        # Volatility regime thresholds
        self.thresholds = {
            "very_low": 12,
            "low": 16,
            "normal": 25,
            "high": 35,
            "crisis": 50,
        }

    def detect_regime(self) -> tuple[str, float, dict[str, Any]]:
        """
        Detect current volatility regime.

        Returns:
            Tuple of (regime_name, vix_level, regime_data)
        """
        try:
            # Fetch VIX data
            vix = yf.Ticker(self.vix_ticker)
            vix_hist = vix.history(period="30d")

            if vix_hist.empty:
                return self._default_regime()

            current_vix = float(vix_hist["Close"].iloc[-1])
            avg_vix_20d = float(vix_hist["Close"].tail(20).mean())

            # Determine regime
            if current_vix < self.thresholds["very_low"]:
                regime = "very_low"
            elif current_vix < self.thresholds["low"]:
                regime = "low"
            elif current_vix < self.thresholds["normal"]:
                regime = "normal"
            elif current_vix < self.thresholds["high"]:
                regime = "high"
            else:
                regime = "crisis"

            # Additional regime characteristics
            regime_data = {
                "current_vix": current_vix,
                "avg_vix_20d": avg_vix_20d,
                "regime": regime,
                "threshold_adjustments": self._get_threshold_adjustments(regime),
                "weight_adjustments": self._get_weight_adjustments(regime),
            }

            return regime, current_vix, regime_data

        except Exception as e:
            self.logger.error(f"VIX regime detection failed: {e}")
            return self._default_regime()

    def _get_threshold_adjustments(self, regime: str) -> dict[str, float]:
        """Get enhanced threshold adjustments for different market regimes."""
        adjustments = {
            "very_low": {
                "strong_buy": -8,
                "buy": -5,
                "sell": -2,
                "strong_sell": -3,
            },  # More aggressive in strong bull markets
            "low": {
                "strong_buy": -5,
                "buy": -3,
                "sell": -1,
                "strong_sell": -2,
            },  # Moderately aggressive in bull markets
            "normal": {
                "strong_buy": 0,
                "buy": 0,
                "sell": 0,
                "strong_sell": 0,
            },  # Baseline thresholds
            "high": {
                "strong_buy": 10,
                "buy": 6,
                "sell": 4,
                "strong_sell": 8,
            },  # More conservative in volatile markets
            "crisis": {
                "strong_buy": 18,
                "buy": 12,
                "sell": 8,
                "strong_sell": 15,
            },  # Very conservative in crisis
        }
        return adjustments.get(regime, adjustments["normal"])

    def _get_weight_adjustments(self, regime: str) -> dict[str, float]:
        """Get enhanced weight adjustments for different market regimes."""
        adjustments = {
            "very_low": {
                "risk": 0.8,
                "momentum": 1.2,
                "trend": 1.1,
                "risk_adj": 0.9,
                "mean_rev": 0.7,
                "volume": 1.0,
            },  # Trend-following in bull markets
            "low": {
                "risk": 0.9,
                "momentum": 1.1,
                "trend": 1.05,
                "risk_adj": 0.95,
                "mean_rev": 0.85,
                "volume": 1.0,
            },  # Moderately trend-following
            "normal": {
                "risk": 1.0,
                "momentum": 1.0,
                "trend": 1.0,
                "risk_adj": 1.0,
                "mean_rev": 1.0,
                "volume": 1.0,
            },  # Baseline weights
            "high": {
                "risk": 1.25,
                "momentum": 0.75,
                "trend": 0.85,
                "risk_adj": 1.15,
                "mean_rev": 1.4,
                "volume": 1.1,
            },  # Risk-focused in volatile markets
            "crisis": {
                "risk": 1.5,
                "momentum": 0.5,
                "trend": 0.7,
                "risk_adj": 1.3,
                "mean_rev": 1.6,
                "volume": 1.2,
            },  # Heavily risk-focused in crisis
        }
        return adjustments.get(regime, adjustments["normal"])

    def _default_regime(self) -> tuple[str, float, dict[str, Any]]:
        """Return default regime when detection fails."""
        return (
            "normal",
            20.0,
            {
                "current_vix": 20.0,
                "avg_vix_20d": 20.0,
                "regime": "normal",
                "threshold_adjustments": self._get_threshold_adjustments("normal"),
                "weight_adjustments": self._get_weight_adjustments("normal"),
            },
        )


def create_risk_free_rate_provider(
    cache_dir: str = "./cache",
) -> DynamicRiskFreeRateProvider:
    """Factory function to create risk-free rate provider."""
    return DynamicRiskFreeRateProvider(cache_dir)


def create_beta_calculator(market_index: str = "SPY") -> MarketBetaCalculator:
    """Factory function to create beta calculator."""
    return MarketBetaCalculator(market_index)


def create_volatility_detector() -> VolatilityRegimeDetector:
    """Factory function to create volatility regime detector."""
    return VolatilityRegimeDetector()
