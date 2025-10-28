"""
Moving Average Financial Analytics Module

This module provides comprehensive financial analysis for moving average data,
including risk metrics, performance statistics, and trend analysis.
"""

from typing import Any

import numpy as np
import polars as pl


class MAAnalytics:
    """Financial analytics calculator for moving average data."""

    def __init__(self, ma_data: pl.DataFrame, ticker: str, period: int, ma_type: str):
        """
        Initialize MA analytics with price data.

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
        self.returns = self._calculate_returns()
        self.prices = ma_data.select("Close").to_series()

    def _calculate_returns(self) -> pl.Series:
        """Calculate daily returns from MA values."""
        close_prices = self.ma_data.select("Close").to_series()
        return close_prices.pct_change().drop_nulls()

    def calculate_all_metrics(self) -> dict[str, Any]:
        """Calculate all financial metrics and return as dictionary."""
        return {
            "summary": self._get_data_summary(),
            "risk_metrics": self._calculate_risk_metrics(),
            "performance_metrics": self._calculate_performance_metrics(),
            "trend_metrics": self._calculate_trend_metrics(),
            "statistical_metrics": self._calculate_statistical_metrics(),
        }

    def _get_data_summary(self) -> dict[str, Any]:
        """Get basic data summary information."""
        dates = self.ma_data.select("Date").to_series()

        # Handle date parsing if dates are strings
        try:
            # Try to parse dates if they're strings
            parsed_dates = dates.str.strptime(
                pl.Datetime, format="%Y-%m-%dT%H:%M:%S%.f", strict=False,
            )
        except:
            try:
                # Fallback to simpler date format
                parsed_dates = dates.str.strptime(
                    pl.Datetime, format="%Y-%m-%d", strict=False,
                )
            except:
                # If all parsing fails, treat as strings
                parsed_dates = dates

        try:
            start_date = parsed_dates.min()
            end_date = parsed_dates.max()

            # Calculate date range days if possible
            if hasattr(start_date, "date") and hasattr(end_date, "date"):
                date_range_days = (end_date.date() - start_date.date()).days
            elif len(dates) > 1:
                date_range_days = len(dates)  # Approximate with number of data points
            else:
                date_range_days = 0
        except:
            start_date = dates.first() if len(dates) > 0 else "Unknown"
            end_date = dates.last() if len(dates) > 0 else "Unknown"
            date_range_days = len(dates) if len(dates) > 1 else 0

        return {
            "ticker": self.ticker,
            "period": self.period,
            "ma_type": self.ma_type,
            "data_points": len(self.ma_data),
            "start_date": start_date,
            "end_date": end_date,
            "date_range_days": date_range_days,
        }

    def _calculate_risk_metrics(self) -> dict[str, float]:
        """Calculate risk-related metrics."""
        returns_np = self.returns.to_numpy()

        if len(returns_np) == 0:
            return self._get_zero_metrics("risk")

        # Risk-free rate (assume 2% annually)
        risk_free_rate = 0.02

        return {
            "sharpe_ratio": self._calculate_sharpe_ratio(returns_np, risk_free_rate),
            "sortino_ratio": self._calculate_sortino_ratio(returns_np, risk_free_rate),
            "max_drawdown": self._calculate_max_drawdown(),
            "volatility": self._calculate_volatility(returns_np),
            "var_95": self._calculate_var(returns_np, 0.95),
            "cvar_95": self._calculate_cvar(returns_np, 0.95),
        }

    def _calculate_performance_metrics(self) -> dict[str, float]:
        """Calculate performance-related metrics."""
        if len(self.returns) == 0:
            return self._get_zero_metrics("performance")

        returns_np = self.returns.to_numpy()
        prices_np = self.prices.to_numpy()

        if len(prices_np) < 2:
            return self._get_zero_metrics("performance")

        days_total = len(returns_np)
        years = max(days_total / 252.0, 1.0)  # Assume 252 trading days per year

        total_return = (prices_np[-1] - prices_np[0]) / prices_np[0] * 100
        annualized_return = ((prices_np[-1] / prices_np[0]) ** (1 / years) - 1) * 100

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "cagr": annualized_return,  # Same as annualized return
            "calmar_ratio": self._calculate_calmar_ratio(annualized_return),
            "information_ratio": self._calculate_information_ratio(returns_np),
        }

    def _calculate_trend_metrics(self) -> dict[str, Any]:
        """Calculate trend analysis metrics."""
        if len(self.prices) < 2:
            return {
                "trend_direction": "Unknown",
                "trend_strength": "Unknown",
                "r_squared": 0.0,
                "smoothness_factor": 0.0,
                "linear_slope": 0.0,
            }

        prices_np = self.prices.to_numpy()
        x = np.arange(len(prices_np))

        # Linear regression
        slope, r_squared = self._calculate_linear_regression(x, prices_np)

        return {
            "trend_direction": (
                "Upward" if slope > 0 else "Downward" if slope < 0 else "Sideways"
            ),
            "trend_strength": self._categorize_trend_strength(r_squared),
            "r_squared": r_squared,
            "smoothness_factor": self._calculate_smoothness_factor(prices_np),
            "linear_slope": slope,
        }

    def _calculate_statistical_metrics(self) -> dict[str, float]:
        """Calculate statistical metrics."""
        if len(self.returns) == 0:
            return self._get_zero_metrics("statistical")

        returns_np = self.returns.to_numpy()
        prices_np = self.prices.to_numpy()

        return {
            "mean_return": float(np.mean(returns_np)),
            "std_deviation": float(np.std(returns_np)),
            "skewness": self._calculate_skewness(returns_np),
            "kurtosis": self._calculate_kurtosis(returns_np),
            "autocorrelation": self._calculate_autocorrelation(returns_np),
            "price_mean": float(np.mean(prices_np)),
            "price_median": float(np.median(prices_np)),
        }

    # Risk calculation methods
    def _calculate_sharpe_ratio(
        self, returns: np.ndarray, risk_free_rate: float,
    ) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        excess_returns = np.mean(returns) - risk_free_rate / 252
        return float(excess_returns / np.std(returns) * np.sqrt(252))

    def _calculate_sortino_ratio(
        self, returns: np.ndarray, risk_free_rate: float,
    ) -> float:
        """Calculate Sortino ratio (downside deviation only)."""
        if len(returns) == 0:
            return 0.0
        excess_returns = np.mean(returns) - risk_free_rate / 252
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float("inf") if excess_returns > 0 else 0.0
        downside_std = np.std(downside_returns)
        return (
            float(excess_returns / downside_std * np.sqrt(252))
            if downside_std > 0
            else 0.0
        )

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        prices_np = self.prices.to_numpy()
        if len(prices_np) == 0:
            return 0.0
        peak = np.maximum.accumulate(prices_np)
        drawdown = (prices_np - peak) / peak
        return float(abs(np.min(drawdown)) * 100)

    def _calculate_volatility(self, returns: np.ndarray) -> float:
        """Calculate annualized volatility."""
        if len(returns) == 0:
            return 0.0
        return float(np.std(returns) * np.sqrt(252) * 100)

    def _calculate_var(self, returns: np.ndarray, confidence_level: float) -> float:
        """Calculate Value at Risk."""
        if len(returns) == 0:
            return 0.0
        return float(np.percentile(returns, (1 - confidence_level) * 100) * 100)

    def _calculate_cvar(self, returns: np.ndarray, confidence_level: float) -> float:
        """Calculate Conditional Value at Risk."""
        if len(returns) == 0:
            return 0.0
        var = np.percentile(returns, (1 - confidence_level) * 100)
        tail_returns = returns[returns <= var]
        return float(np.mean(tail_returns) * 100) if len(tail_returns) > 0 else 0.0

    # Performance calculation methods
    def _calculate_calmar_ratio(self, annualized_return: float) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)."""
        max_dd = self._calculate_max_drawdown()
        return float(annualized_return / max_dd) if max_dd > 0 else 0.0

    def _calculate_information_ratio(self, returns: np.ndarray) -> float:
        """Calculate Information ratio."""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        return float(np.mean(returns) / np.std(returns) * np.sqrt(252))

    # Trend calculation methods
    def _calculate_linear_regression(
        self, x: np.ndarray, y: np.ndarray,
    ) -> tuple[float, float]:
        """Calculate linear regression slope and R-squared."""
        if len(x) < 2:
            return 0.0, 0.0

        # Calculate slope and R-squared
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)
        np.sum(y * y)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        # R-squared calculation
        y_mean = np.mean(y)
        ss_tot = np.sum((y - y_mean) ** 2)
        y_pred = slope * x + (sum_y - slope * sum_x) / n
        ss_res = np.sum((y - y_pred) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return float(slope), float(max(0.0, min(1.0, r_squared)))

    def _categorize_trend_strength(self, r_squared: float) -> str:
        """Categorize trend strength based on R-squared."""
        if r_squared >= 0.8:
            return "Very Strong"
        if r_squared >= 0.6:
            return "Strong"
        if r_squared >= 0.4:
            return "Moderate"
        if r_squared >= 0.2:
            return "Weak"
        return "Very Weak"

    def _calculate_smoothness_factor(self, prices: np.ndarray) -> float:
        """Calculate smoothness factor (1 - relative volatility)."""
        if len(prices) < 2:
            return 0.0
        price_changes = np.diff(prices)
        if np.mean(np.abs(prices)) == 0:
            return 0.0
        relative_volatility = np.std(price_changes) / np.mean(np.abs(prices))
        return float(max(0.0, min(1.0, 1 - relative_volatility)))

    # Statistical calculation methods
    def _calculate_skewness(self, returns: np.ndarray) -> float:
        """Calculate skewness of returns."""
        if len(returns) < 3:
            return 0.0
        mean_ret = np.mean(returns)
        std_ret = np.std(returns)
        if std_ret == 0:
            return 0.0
        return float(np.mean(((returns - mean_ret) / std_ret) ** 3))

    def _calculate_kurtosis(self, returns: np.ndarray) -> float:
        """Calculate kurtosis of returns."""
        if len(returns) < 4:
            return 0.0
        mean_ret = np.mean(returns)
        std_ret = np.std(returns)
        if std_ret == 0:
            return 0.0
        return float(np.mean(((returns - mean_ret) / std_ret) ** 4) - 3)

    def _calculate_autocorrelation(self, returns: np.ndarray, lag: int = 1) -> float:
        """Calculate autocorrelation of returns."""
        if len(returns) <= lag:
            return 0.0
        return (
            float(np.corrcoef(returns[:-lag], returns[lag:])[0, 1])
            if len(returns) > lag
            else 0.0
        )

    def _get_zero_metrics(self, category: str) -> dict[str, float]:
        """Return dictionary of zero metrics for a category when no data is available."""
        if category == "risk":
            return {
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "max_drawdown": 0.0,
                "volatility": 0.0,
                "var_95": 0.0,
                "cvar_95": 0.0,
            }
        if category == "performance":
            return {
                "total_return": 0.0,
                "annualized_return": 0.0,
                "cagr": 0.0,
                "calmar_ratio": 0.0,
                "information_ratio": 0.0,
            }
        if category == "statistical":
            return {
                "mean_return": 0.0,
                "std_deviation": 0.0,
                "skewness": 0.0,
                "kurtosis": 0.0,
                "autocorrelation": 0.0,
                "price_mean": 0.0,
                "price_median": 0.0,
            }
        return {}


def analyze_ma_data(
    ma_data: pl.DataFrame, ticker: str, period: int, ma_type: str,
) -> dict[str, Any]:
    """
    Convenience function to analyze MA data and return all metrics.

    Args:
        ma_data: DataFrame with MA price data
        ticker: Ticker symbol
        period: Moving average period
        ma_type: Moving average type

    Returns:
        Dictionary containing all calculated metrics
    """
    analyzer = MAAnalytics(ma_data, ticker, period, ma_type)
    return analyzer.calculate_all_metrics()
