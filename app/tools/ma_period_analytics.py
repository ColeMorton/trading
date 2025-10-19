"""
Moving Average Period Analytics Module

This module provides weekly and monthly period-specific analysis for moving average data,
including rolling performance metrics, seasonality patterns, and period comparisons.
"""

from typing import Any

import numpy as np
import pandas as pd
import polars as pl

from app.tools.seasonality_analyzer import SeasonalityAnalyzer


def detect_asset_type(ticker: str) -> str:
    """
    Detect asset type based on ticker symbol.

    Args:
        ticker: Ticker symbol (e.g., AAPL, BTC-USD, ETH-USDT)

    Returns:
        Asset type: 'crypto' or 'stock'
    """
    ticker_upper = ticker.upper()

    # Crypto suffixes (trading pairs)
    crypto_suffixes = ["-USD", "-USDT", "-BTC", "-ETH", "-BUSD", "-DAI", "-USDC"]

    # Known crypto symbols
    crypto_symbols = {
        "BTC",
        "ETH",
        "ADA",
        "SOL",
        "DOGE",
        "XRP",
        "DOT",
        "UNI",
        "LINK",
        "LTC",
        "BCH",
        "MATIC",
        "AVAX",
        "ATOM",
        "ICP",
        "FIL",
        "TRX",
        "ETC",
        "XLM",
        "VET",
        "THETA",
        "FTT",
        "ALGO",
        "XMR",
        "MANA",
        "SAND",
        "SHIB",
        "CRO",
        "NEAR",
        "LRC",
        "GALA",
        "ENJ",
        "BAT",
        "ZEC",
        "COMP",
        "MKR",
        "SUSHI",
        "SNX",
        "AAVE",
        "YFI",
        "KSM",
        "WAVES",
        "ICX",
        "ZIL",
        "REN",
        "STORJ",
        "SKL",
        "NKN",
        "OMG",
        "KAVA",
    }

    # Check for crypto trading pair suffixes
    if any(ticker_upper.endswith(suffix) for suffix in crypto_suffixes):
        return "crypto"

    # Check if ticker is a known crypto symbol
    if ticker_upper in crypto_symbols:
        return "crypto"

    # Default to stock for traditional symbols
    return "stock"


def get_rolling_windows(asset_type: str) -> dict[str, int]:
    """
    Get appropriate rolling windows based on asset type.

    Args:
        asset_type: 'crypto' or 'stock'

    Returns:
        Dictionary with weekly and monthly window sizes
    """
    if asset_type == "crypto":
        return {
            "weekly": 7,  # 7 calendar days (crypto trades 24/7)
            "monthly": 30,  # 30 calendar days
        }
    # stock
    return {
        "weekly": 5,  # 5 trading days (Mon-Fri)
        "monthly": 21,  # ~21 trading days per month
    }


def get_period_labels(asset_type: str) -> dict[str, str]:
    """
    Get appropriate period labels based on asset type.

    Args:
        asset_type: 'crypto' or 'stock'

    Returns:
        Dictionary with period labels and trading info
    """
    if asset_type == "crypto":
        return {
            "weekly": "📅 Weekly (7d)",
            "monthly": "🗓️ Monthly (30d)",
            "note": "Crypto markets trade 24/7/365",
        }
    # stock
    return {
        "weekly": "🗓️ Weekly (5d)",
        "monthly": "📅 Monthly (21d)",
        "note": "Based on trading days (Mon-Fri)",
    }


class MAPeriodAnalytics:
    """Period-specific analytics calculator for moving average data."""

    def __init__(self, ma_data: pl.DataFrame, ticker: str, period: int, ma_type: str):
        """
        Initialize period analytics with MA price data.

        Args:
            ma_data: DataFrame with Date, Open, High, Low, Close, Volume columns
            ticker: Ticker symbol
            period: Moving average period
            ma_type: Moving average type (SMA or EMA)
        """
        self.ma_data = ma_data
        self.ticker = ticker
        self.period = period
        self.ma_type = ma_type

        # Detect asset type and set appropriate rolling windows
        self.asset_type = detect_asset_type(ticker)
        self.rolling_windows = get_rolling_windows(self.asset_type)
        self.period_labels = get_period_labels(self.asset_type)

        # Convert to pandas for easier time series operations
        self.df = self._prepare_pandas_data()
        self.returns = self._calculate_returns()

    def _prepare_pandas_data(self) -> pd.DataFrame:
        """Convert polars data to pandas and prepare for analysis."""
        # Convert to pandas
        df = self.ma_data.to_pandas()

        # Parse dates if they're strings
        if df["Date"].dtype == "object":
            df["Date"] = pd.to_datetime(df["Date"])

        # Set date as index
        df = df.set_index("Date")

        return df

    def _calculate_returns(self) -> pd.Series:
        """Calculate daily returns from MA values."""
        return self.df["Close"].pct_change().dropna()

    def calculate_all_period_metrics(self) -> dict[str, Any]:
        """Calculate all period-specific metrics."""
        return {
            "rolling_performance": self._calculate_rolling_performance(),
            "seasonality_patterns": self._analyze_seasonality_patterns(),
            "period_comparison": self._calculate_period_comparison(),
            "calendar_analysis": self._analyze_calendar_patterns(),
            "asset_info": {
                "asset_type": self.asset_type,
                "period_labels": self.period_labels,
                "rolling_windows": self.rolling_windows,
                "ticker": self.ticker,
            },
        }

    def _calculate_rolling_performance(self) -> dict[str, dict[str, float]]:
        """Calculate rolling performance metrics for different periods."""
        rolling_metrics = {}

        # Weekly rolling (dynamic based on asset type)
        weekly_window = self.rolling_windows["weekly"]
        weekly_metrics = self._calculate_rolling_metrics(
            window=weekly_window, period_name=f"Weekly ({weekly_window}d)"
        )
        rolling_metrics["weekly"] = weekly_metrics

        # Monthly rolling (dynamic based on asset type)
        monthly_window = self.rolling_windows["monthly"]
        monthly_metrics = self._calculate_rolling_metrics(
            window=monthly_window, period_name=f"Monthly ({monthly_window}d)"
        )
        rolling_metrics["monthly"] = monthly_metrics

        return rolling_metrics

    def _calculate_rolling_metrics(
        self, window: int, period_name: str
    ) -> dict[str, float]:
        """Calculate rolling metrics for a specific window size."""
        if len(self.returns) < window:
            return self._get_empty_rolling_metrics()

        # Rolling returns
        rolling_returns = self.returns.rolling(window=window).sum()

        # Rolling volatility (annualized)
        rolling_vol = self.returns.rolling(window=window).std() * np.sqrt(252)

        # Rolling Sharpe ratio (assume 2% risk-free rate)
        risk_free_rate = 0.02
        excess_returns = self.returns - risk_free_rate / 252
        rolling_sharpe = (
            excess_returns.rolling(window=window).mean()
            / self.returns.rolling(window=window).std()
            * np.sqrt(252)
        )

        # Rolling maximum drawdown
        rolling_prices = self.df["Close"].rolling(window=window)
        rolling_max_dd = []

        for price_window in rolling_prices:
            if len(price_window.dropna()) >= window:
                peak = np.maximum.accumulate(price_window.dropna())
                drawdown = (price_window.dropna() - peak) / peak
                rolling_max_dd.append(abs(drawdown.min()) * 100)
            else:
                rolling_max_dd.append(np.nan)

        rolling_max_dd = pd.Series(rolling_max_dd, index=self.df.index)

        # Calculate summary statistics
        return {
            "avg_return": (
                float(rolling_returns.mean() * 100)
                if not rolling_returns.isna().all()
                else 0.0
            ),
            "avg_volatility": (
                float(rolling_vol.mean() * 100) if not rolling_vol.isna().all() else 0.0
            ),
            "avg_sharpe": (
                float(rolling_sharpe.mean()) if not rolling_sharpe.isna().all() else 0.0
            ),
            "avg_max_drawdown": (
                float(rolling_max_dd.mean()) if not rolling_max_dd.isna().all() else 0.0
            ),
            "best_return": (
                float(rolling_returns.max() * 100)
                if not rolling_returns.isna().all()
                else 0.0
            ),
            "worst_return": (
                float(rolling_returns.min() * 100)
                if not rolling_returns.isna().all()
                else 0.0
            ),
            "win_rate": (
                float((rolling_returns > 0).mean() * 100)
                if not rolling_returns.isna().all()
                else 0.0
            ),
        }

    def _get_empty_rolling_metrics(self) -> dict[str, float]:
        """Return empty metrics when insufficient data."""
        return {
            "avg_return": 0.0,
            "avg_volatility": 0.0,
            "avg_sharpe": 0.0,
            "avg_max_drawdown": 0.0,
            "best_return": 0.0,
            "worst_return": 0.0,
            "win_rate": 0.0,
        }

    def _analyze_seasonality_patterns(self) -> dict[str, Any]:
        """Analyze seasonal patterns in MA data using existing seasonality analyzer."""
        try:
            # Create seasonality analyzer
            analyzer = SeasonalityAnalyzer(confidence_level=0.95, min_sample_size=10)

            # Analyze patterns - note: SeasonalityAnalyzer expects pandas DataFrame
            patterns = analyzer.analyze_all_patterns(self.df, detrend=True)

            # Group patterns by type
            pattern_dict = {
                "weekly": [],
                "monthly": [],
                "quarterly": [],
            }

            for pattern in patterns:
                if pattern.pattern_type.value == "Weekly":
                    pattern_dict["weekly"].append(
                        {
                            "period": pattern.period,
                            "avg_return": pattern.average_return * 100,
                            "win_rate": pattern.win_rate * 100,
                            "sample_size": pattern.sample_size,
                            "significance": pattern.statistical_significance,
                            "p_value": pattern.p_value,
                        }
                    )
                elif pattern.pattern_type.value == "Monthly":
                    pattern_dict["monthly"].append(
                        {
                            "period": pattern.period,
                            "avg_return": pattern.average_return * 100,
                            "win_rate": pattern.win_rate * 100,
                            "sample_size": pattern.sample_size,
                            "significance": pattern.statistical_significance,
                            "p_value": pattern.p_value,
                        }
                    )
                elif pattern.pattern_type.value == "Quarterly":
                    pattern_dict["quarterly"].append(
                        {
                            "period": pattern.period,
                            "avg_return": pattern.average_return * 100,
                            "win_rate": pattern.win_rate * 100,
                            "sample_size": pattern.sample_size,
                            "significance": pattern.statistical_significance,
                            "p_value": pattern.p_value,
                        }
                    )

            # Find strongest patterns
            all_patterns = (
                pattern_dict["weekly"]
                + pattern_dict["monthly"]
                + pattern_dict["quarterly"]
            )
            strongest_pattern = None
            if all_patterns:
                strongest_pattern = max(all_patterns, key=lambda x: x["significance"])

            return {
                "patterns": pattern_dict,
                "strongest_pattern": strongest_pattern,
                "total_patterns": len(all_patterns),
            }

        except Exception as e:
            # Return empty results if seasonality analysis fails
            return {
                "patterns": {"weekly": [], "monthly": [], "quarterly": []},
                "strongest_pattern": None,
                "total_patterns": 0,
                "error": str(e),
            }

    def _calculate_period_comparison(self) -> dict[str, Any]:
        """Compare performance across different time periods."""
        comparison = {}

        # Weekly vs Monthly performance
        weekly_returns = self.returns.resample("W-FRI").sum()  # Week ending Friday
        monthly_returns = self.returns.resample("M").sum()  # Month end

        if len(weekly_returns) > 0 and len(monthly_returns) > 0:
            comparison["weekly_vs_monthly"] = {
                "weekly_avg": float(weekly_returns.mean() * 100),
                "monthly_avg": float(monthly_returns.mean() * 100),
                "weekly_vol": float(weekly_returns.std() * 100),
                "monthly_vol": float(monthly_returns.std() * 100),
                "weekly_sharpe": self._calculate_sharpe(weekly_returns),
                "monthly_sharpe": self._calculate_sharpe(monthly_returns),
                "correlation": float(self._calculate_period_correlation()),
            }

        # Best/Worst periods
        comparison["best_worst"] = self._find_best_worst_periods()

        return comparison

    def _calculate_sharpe(
        self, returns: pd.Series, risk_free_rate: float = 0.02
    ) -> float:
        """Calculate Sharpe ratio for a return series."""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        # Adjust risk-free rate based on return frequency
        if len(returns) < 60:  # Monthly data
            adjusted_rf = risk_free_rate / 12
        else:  # Weekly data
            adjusted_rf = risk_free_rate / 52

        excess_returns = returns.mean() - adjusted_rf
        return float(excess_returns / returns.std())

    def _calculate_period_correlation(self) -> float:
        """Calculate correlation between weekly and monthly returns."""
        try:
            # Resample to monthly and align
            weekly_monthly = self.returns.resample("W-FRI").sum().resample("M").sum()
            monthly_returns = self.returns.resample("M").sum()

            # Align periods
            aligned_weekly, aligned_monthly = weekly_monthly.align(
                monthly_returns, join="inner"
            )

            if len(aligned_weekly) > 1 and len(aligned_monthly) > 1:
                return aligned_weekly.corr(aligned_monthly)
            return 0.0
        except:
            return 0.0

    def _find_best_worst_periods(self) -> dict[str, Any]:
        """Find best and worst performing periods."""
        best_worst = {}

        # Weekly analysis
        weekly_returns = self.returns.resample("W-FRI").sum()
        if len(weekly_returns) > 0:
            best_week_idx = weekly_returns.idxmax()
            worst_week_idx = weekly_returns.idxmin()

            best_worst["weekly"] = {
                "best_week": (
                    best_week_idx.strftime("%Y-%m-%d")
                    if pd.notna(best_week_idx)
                    else None
                ),
                "best_return": (
                    float(weekly_returns.max() * 100)
                    if pd.notna(weekly_returns.max())
                    else 0.0
                ),
                "worst_week": (
                    worst_week_idx.strftime("%Y-%m-%d")
                    if pd.notna(worst_week_idx)
                    else None
                ),
                "worst_return": (
                    float(weekly_returns.min() * 100)
                    if pd.notna(weekly_returns.min())
                    else 0.0
                ),
            }

        # Monthly analysis
        monthly_returns = self.returns.resample("M").sum()
        if len(monthly_returns) > 0:
            best_month_idx = monthly_returns.idxmax()
            worst_month_idx = monthly_returns.idxmin()

            best_worst["monthly"] = {
                "best_month": (
                    best_month_idx.strftime("%Y-%m")
                    if pd.notna(best_month_idx)
                    else None
                ),
                "best_return": (
                    float(monthly_returns.max() * 100)
                    if pd.notna(monthly_returns.max())
                    else 0.0
                ),
                "worst_month": (
                    worst_month_idx.strftime("%Y-%m")
                    if pd.notna(worst_month_idx)
                    else None
                ),
                "worst_return": (
                    float(monthly_returns.min() * 100)
                    if pd.notna(monthly_returns.min())
                    else 0.0
                ),
            }

        return best_worst

    def _analyze_calendar_patterns(self) -> dict[str, Any]:
        """Analyze calendar-based patterns (day of week, month of year effects)."""
        calendar_analysis = {}

        # Day of week effects
        dow_grouped = self.returns.groupby(self.returns.index.dayofweek)
        dow_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        dow_results = []

        for day_num, group in dow_grouped:
            if (
                day_num < len(dow_names) and len(group) > 5
            ):  # Only include days with sufficient data
                dow_results.append(
                    {
                        "day": dow_names[day_num],
                        "avg_return": float(group.mean() * 100),
                        "volatility": float(group.std() * 100),
                        "sample_size": len(group),
                    }
                )

        calendar_analysis["day_of_week"] = dow_results

        # Month of year effects
        moy_grouped = self.returns.groupby(self.returns.index.month)
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        moy_results = []

        for month_num, group in moy_grouped:
            if len(group) > 5:  # Only include months with sufficient data
                moy_results.append(
                    {
                        "month": month_names[month_num - 1],
                        "avg_return": float(group.mean() * 100),
                        "volatility": float(group.std() * 100),
                        "sample_size": len(group),
                    }
                )

        calendar_analysis["month_of_year"] = moy_results

        return calendar_analysis


def analyze_ma_periods(
    ma_data: pl.DataFrame, ticker: str, period: int, ma_type: str
) -> dict[str, Any]:
    """
    Convenience function to analyze MA period data and return all metrics.

    Args:
        ma_data: DataFrame with MA price data
        ticker: Ticker symbol
        period: Moving average period
        ma_type: Moving average type

    Returns:
        Dictionary containing all calculated period metrics
    """
    analyzer = MAPeriodAnalytics(ma_data, ticker, period, ma_type)
    return analyzer.calculate_all_period_metrics()
