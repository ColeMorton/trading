"""
Volume and Liquidity Analysis Module for SPDS

This module provides volume and liquidity scoring capabilities including:
- Volume trend analysis
- Relative volume calculations
- Bid-ask spread estimation
- Liquidity risk assessment
"""

from dataclasses import dataclass
import logging
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf


@dataclass
class VolumeMetrics:
    """Data class for volume and liquidity metrics."""

    avg_volume_20d: float
    current_volume: float
    relative_volume: float
    volume_trend: float
    volume_consistency: float
    liquidity_score: float


class VolumeLiquidityAnalyzer:
    """
    Analyzer for volume and liquidity characteristics.

    Provides comprehensive volume analysis including trends, relative volume,
    and liquidity scoring for market impact assessment.
    """

    def __init__(self, ticker: str, logger: logging.Logger | None = None):
        """
        Initialize volume liquidity analyzer.

        Args:
            ticker: Stock ticker symbol
            logger: Optional logger instance
        """
        self.ticker = ticker
        self.logger = logger or logging.getLogger(__name__)
        self.volume_data: pd.DataFrame | None = None

    def fetch_volume_data(self, period_days: int = 60) -> bool:
        """
        Fetch volume data for analysis.

        Args:
            period_days: Number of days of volume data to fetch

        Returns:
            True if data fetched successfully, False otherwise
        """
        try:
            self.logger.debug(f"Fetching volume data for {self.ticker}")

            # Fetch data using yfinance
            ticker_obj = yf.Ticker(self.ticker)
            hist = ticker_obj.history(period=f"{period_days + 10}d")

            if hist.empty:
                self.logger.warning(f"No volume data available for {self.ticker}")
                return False

            # Convert to pandas DataFrame for easier processing
            self.volume_data = hist[["Volume", "Close", "High", "Low"]].copy()
            self.volume_data = self.volume_data.dropna()

            if len(self.volume_data) < 20:
                self.logger.warning(
                    f"Insufficient volume data for {self.ticker}: {len(self.volume_data)} days",
                )
                return False

            self.logger.debug(
                f"Successfully fetched {len(self.volume_data)} days of volume data",
            )
            return True

        except Exception as e:
            self.logger.exception(f"Failed to fetch volume data for {self.ticker}: {e}")
            return False

    def calculate_volume_metrics(self) -> VolumeMetrics:
        """
        Calculate comprehensive volume and liquidity metrics.

        Returns:
            VolumeMetrics object with calculated metrics
        """
        if self.volume_data is None or len(self.volume_data) < 20:
            return self._default_volume_metrics()

        try:
            volumes = self.volume_data["Volume"].values
            closes = self.volume_data["Close"].values
            highs = self.volume_data["High"].values
            lows = self.volume_data["Low"].values

            # Basic volume metrics
            avg_volume_20d = float(np.mean(volumes[-20:]))
            current_volume = float(volumes[-1])

            # Relative volume (current vs average)
            relative_volume = (
                current_volume / avg_volume_20d if avg_volume_20d > 0 else 1.0
            )

            # Volume trend (regression slope over 20 days)
            if len(volumes) >= 20:
                x = np.arange(20)
                slope, _ = np.polyfit(x, volumes[-20:], 1)
                volume_trend = slope / avg_volume_20d if avg_volume_20d > 0 else 0.0
            else:
                volume_trend = 0.0

            # Volume consistency (coefficient of variation)
            volume_std = np.std(volumes[-20:])
            volume_consistency = (
                1 - (volume_std / avg_volume_20d) if avg_volume_20d > 0 else 0.5
            )
            volume_consistency = max(
                0, min(1, volume_consistency),
            )  # Clamp between 0 and 1

            # Liquidity score estimation
            liquidity_score = self._calculate_liquidity_score(
                volumes, closes, highs, lows,
            )

            return VolumeMetrics(
                avg_volume_20d=avg_volume_20d,
                current_volume=current_volume,
                relative_volume=relative_volume,
                volume_trend=volume_trend,
                volume_consistency=volume_consistency,
                liquidity_score=liquidity_score,
            )

        except Exception as e:
            self.logger.exception(f"Failed to calculate volume metrics: {e}")
            return self._default_volume_metrics()

    def _calculate_liquidity_score(
        self,
        volumes: np.ndarray,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
    ) -> float:
        """
        Calculate liquidity score based on volume and price data.

        Args:
            volumes: Array of volume data
            closes: Array of closing prices
            highs: Array of high prices
            lows: Array of low prices

        Returns:
            Liquidity score (0-100, higher = more liquid)
        """
        try:
            # Average daily dollar volume (higher = more liquid)
            dollar_volumes = volumes * closes
            avg_dollar_volume = np.mean(dollar_volumes[-20:])

            # Dollar volume score (log scale)
            if avg_dollar_volume > 100_000_000:  # >$100M daily
                dollar_vol_score = 100
            elif avg_dollar_volume > 50_000_000:  # >$50M daily
                dollar_vol_score = 90
            elif avg_dollar_volume > 10_000_000:  # >$10M daily
                dollar_vol_score = 80
            elif avg_dollar_volume > 1_000_000:  # >$1M daily
                dollar_vol_score = 60
            elif avg_dollar_volume > 100_000:  # >$100K daily
                dollar_vol_score = 40
            else:
                dollar_vol_score = 20

            # Bid-ask spread proxy using high-low range
            price_ranges = (highs - lows) / closes
            avg_range = np.mean(price_ranges[-20:])

            # Spread score (lower spread = higher liquidity)
            if avg_range < 0.01:  # <1% daily range
                spread_score = 100
            elif avg_range < 0.02:  # <2% daily range
                spread_score = 80
            elif avg_range < 0.05:  # <5% daily range
                spread_score = 60
            elif avg_range < 0.10:  # <10% daily range
                spread_score = 40
            else:
                spread_score = 20

            # Volume consistency score
            volume_cv = np.std(volumes[-20:]) / np.mean(volumes[-20:])
            if volume_cv < 0.5:  # Low variability
                consistency_score = 100
            elif volume_cv < 1.0:
                consistency_score = 80
            elif volume_cv < 2.0:
                consistency_score = 60
            else:
                consistency_score = 40

            # Combined liquidity score (weighted average)
            liquidity_score = (
                dollar_vol_score * 0.5
                + spread_score * 0.3  # Dollar volume most important
                + consistency_score  # Spread second most important
                * 0.2  # Consistency third
            )

            return float(liquidity_score)

        except Exception as e:
            self.logger.warning(f"Liquidity score calculation failed: {e}")
            return 50.0  # Default moderate liquidity

    def score_volume_liquidity(self) -> float:
        """
        Generate volume/liquidity factor score (-100 to +100).

        Returns:
            Volume/liquidity score
        """
        if not self.fetch_volume_data():
            return 0.0  # Neutral score for missing data

        metrics = self.calculate_volume_metrics()

        try:
            total_score = 0.0

            # Relative volume scoring (-30 to +30 points)
            if metrics.relative_volume > 2.0:  # >2x average volume
                rel_vol_score = min(30, (metrics.relative_volume - 1) * 15)
            elif metrics.relative_volume > 1.5:  # >1.5x average volume
                rel_vol_score = (metrics.relative_volume - 1) * 20
            elif metrics.relative_volume < 0.5:  # <50% average volume
                rel_vol_score = max(-30, (metrics.relative_volume - 0.5) * 60)
            else:
                rel_vol_score = (metrics.relative_volume - 1) * 10

            total_score += rel_vol_score

            # Volume trend scoring (-25 to +25 points)
            trend_score = max(-25, min(25, metrics.volume_trend * 1000))
            total_score += trend_score

            # Liquidity scoring (-20 to +20 points)
            if metrics.liquidity_score > 80:  # High liquidity
                liquidity_factor = 20
            elif metrics.liquidity_score > 60:
                liquidity_factor = 10
            elif metrics.liquidity_score > 40:
                liquidity_factor = 0
            elif metrics.liquidity_score > 20:
                liquidity_factor = -10
            else:  # Low liquidity
                liquidity_factor = -20

            total_score += liquidity_factor

            # Volume consistency bonus (-15 to +15 points)
            consistency_bonus = (metrics.volume_consistency - 0.5) * 30
            total_score += consistency_bonus

            # Large dollar volume bonus (0 to +10 points)
            if metrics.avg_volume_20d * 100 > 10_000_000:  # Assume $100 average price
                dollar_vol_bonus = min(10, (metrics.avg_volume_20d * 100) / 10_000_000)
            else:
                dollar_vol_bonus = 0

            total_score += dollar_vol_bonus

            # Cap final score
            return max(-100, min(100, total_score))

        except Exception as e:
            self.logger.exception(f"Volume scoring failed: {e}")
            return 0.0

    def _default_volume_metrics(self) -> VolumeMetrics:
        """Return default volume metrics when calculation fails."""
        return VolumeMetrics(
            avg_volume_20d=1_000_000,
            current_volume=1_000_000,
            relative_volume=1.0,
            volume_trend=0.0,
            volume_consistency=0.5,
            liquidity_score=50.0,
        )

    def get_volume_analysis(self) -> dict[str, Any]:
        """
        Get comprehensive volume analysis results.

        Returns:
            Dictionary with volume analysis results
        """
        if not self.fetch_volume_data():
            return {
                "volume_score": 0.0,
                "metrics": self._default_volume_metrics().__dict__,
                "analysis_status": "data_unavailable",
            }

        metrics = self.calculate_volume_metrics()
        score = self.score_volume_liquidity()

        return {
            "volume_score": float(score),
            "volume_metrics": {
                "avg_volume_20d": metrics.avg_volume_20d,
                "current_volume": metrics.current_volume,
                "relative_volume": metrics.relative_volume,
                "volume_trend": metrics.volume_trend,
                "volume_consistency": metrics.volume_consistency,
                "liquidity_score": metrics.liquidity_score,
            },
            "analysis_status": "success",
        }


def create_volume_analyzer(
    ticker: str, logger: logging.Logger | None = None,
) -> VolumeLiquidityAnalyzer:
    """Factory function to create volume liquidity analyzer."""
    return VolumeLiquidityAnalyzer(ticker, logger)
