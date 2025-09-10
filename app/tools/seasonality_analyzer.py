"""Seasonality analysis engine for stock price data."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import polars as pl
from scipy import stats

from app.cli.models.seasonality import PatternType, SeasonalityPattern


class SeasonalityAnalyzer:
    """Analyzes seasonal patterns in price data."""

    def __init__(
        self,
        confidence_level: float = 0.95,
        min_sample_size: int = 10,
        time_period_days: int = 1,
        current_date: Optional[datetime] = None,
    ):
        """Initialize the analyzer.

        Args:
            confidence_level: Confidence level for statistical tests
            min_sample_size: Minimum sample size for pattern analysis
            time_period_days: Number of days for return calculations (default 1 for daily)
            current_date: Current date for forward-looking analysis (default today)
        """
        self.confidence_level = confidence_level
        self.min_sample_size = min_sample_size
        self.time_period_days = time_period_days
        self.current_date = (
            current_date.date() if current_date else datetime.now().date()
        )

    def analyze_all_patterns(
        self, data: pd.DataFrame, detrend: bool = True
    ) -> List[SeasonalityPattern]:
        """Analyze all seasonal patterns in the data.

        Args:
            data: Price data with Date index and at least Close column
            detrend: Whether to remove trend before analysis

        Returns:
            List of seasonal patterns found
        """
        # Calculate returns
        returns = self._calculate_returns(data)

        if detrend:
            returns = self._detrend_returns(returns)

        patterns = []

        # Analyze different pattern types
        monthly_patterns = self.analyze_monthly_patterns(returns)
        patterns.extend(monthly_patterns)

        weekly_patterns = self.analyze_weekly_patterns(returns)
        patterns.extend(weekly_patterns)

        quarterly_patterns = self.analyze_quarterly_patterns(returns)
        patterns.extend(quarterly_patterns)

        day_of_month_patterns = self.analyze_day_of_month_patterns(returns)
        patterns.extend(day_of_month_patterns)

        # Add current date context and filter for current date actionable analysis
        current_date_patterns = []
        for pattern in patterns:
            # Create current date specific version of each pattern
            current_date_pattern = self._create_current_date_pattern(pattern, returns)
            if current_date_pattern:
                current_date_patterns.append(current_date_pattern)

        # If we have current date patterns, use those; otherwise fall back to general patterns
        if current_date_patterns:
            patterns = current_date_patterns

        # Add current date context to patterns
        for i, pattern in enumerate(patterns):
            patterns[i] = self._add_current_date_context(pattern)

        return patterns

    def analyze_monthly_patterns(self, returns: pd.Series) -> List[SeasonalityPattern]:
        """Analyze monthly seasonal patterns.

        Args:
            returns: Daily returns series with datetime index

        Returns:
            List of monthly patterns
        """
        patterns = []
        monthly_data = {}

        # Group returns by month
        for date, ret in returns.items():
            month = date.strftime("%B")
            if month not in monthly_data:
                monthly_data[month] = []
            monthly_data[month].append(ret)

        # Calculate statistics for each month
        months_order = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        for month in months_order:
            if month in monthly_data:
                month_returns = np.array(monthly_data[month])

                if len(month_returns) >= self.min_sample_size:
                    pattern = self._create_pattern(
                        pattern_type=PatternType.MONTHLY,
                        period=month,
                        returns=month_returns,
                        all_returns=returns.values,
                    )
                    patterns.append(pattern)

        return patterns

    def analyze_weekly_patterns(self, returns: pd.Series) -> List[SeasonalityPattern]:
        """Analyze weekly (day of week) seasonal patterns.

        Args:
            returns: Daily returns series with datetime index

        Returns:
            List of weekly patterns
        """
        patterns = []
        weekly_data = {}

        # Group returns by day of week
        for date, ret in returns.items():
            day_name = date.strftime("%A")
            if day_name not in weekly_data:
                weekly_data[day_name] = []
            weekly_data[day_name].append(ret)

        # Calculate statistics for each day
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        for day in days_order:
            if day in weekly_data:
                day_returns = np.array(weekly_data[day])

                if len(day_returns) >= self.min_sample_size:
                    pattern = self._create_pattern(
                        pattern_type=PatternType.WEEKLY,
                        period=day,
                        returns=day_returns,
                        all_returns=returns.values,
                    )
                    patterns.append(pattern)

        return patterns

    def analyze_quarterly_patterns(
        self, returns: pd.Series
    ) -> List[SeasonalityPattern]:
        """Analyze quarterly seasonal patterns.

        Args:
            returns: Daily returns series with datetime index

        Returns:
            List of quarterly patterns
        """
        patterns = []
        quarterly_data = {}

        # Group returns by quarter
        for date, ret in returns.items():
            quarter = f"Q{(date.month - 1) // 3 + 1}"
            if quarter not in quarterly_data:
                quarterly_data[quarter] = []
            quarterly_data[quarter].append(ret)

        # Calculate statistics for each quarter
        for quarter in ["Q1", "Q2", "Q3", "Q4"]:
            if quarter in quarterly_data:
                quarter_returns = np.array(quarterly_data[quarter])

                if len(quarter_returns) >= self.min_sample_size:
                    pattern = self._create_pattern(
                        pattern_type=PatternType.QUARTERLY,
                        period=quarter,
                        returns=quarter_returns,
                        all_returns=returns.values,
                    )
                    patterns.append(pattern)

        return patterns

    def analyze_day_of_month_patterns(
        self, returns: pd.Series
    ) -> List[SeasonalityPattern]:
        """Analyze day of month seasonal patterns.

        Args:
            returns: Daily returns series with datetime index

        Returns:
            List of day of month patterns
        """
        patterns = []
        day_of_month_data = {}

        # Group returns by day of month
        for date, ret in returns.items():
            day = date.day
            if day not in day_of_month_data:
                day_of_month_data[day] = []
            day_of_month_data[day].append(ret)

        # Analyze beginning, middle, and end of month
        periods = [
            ("Beginning", list(range(1, 8))),
            ("Middle", list(range(11, 21))),
            ("End", list(range(25, 32))),
        ]

        for period_name, days in periods:
            period_returns = []
            for day in days:
                if day in day_of_month_data:
                    period_returns.extend(day_of_month_data[day])

            if len(period_returns) >= self.min_sample_size:
                pattern = self._create_pattern(
                    pattern_type=PatternType.DAY_OF_MONTH,
                    period=period_name,
                    returns=np.array(period_returns),
                    all_returns=returns.values,
                )
                patterns.append(pattern)

        return patterns

    def calculate_seasonal_strength(self, patterns: List[SeasonalityPattern]) -> float:
        """Calculate overall seasonal strength score.

        Args:
            patterns: List of seasonal patterns

        Returns:
            Score between 0 and 1 indicating strength of seasonality
        """
        if not patterns:
            return 0.0

        # Calculate weighted average of statistical significance
        total_weight = 0
        weighted_sum = 0

        for pattern in patterns:
            weight = pattern.sample_size
            total_weight += weight
            weighted_sum += pattern.statistical_significance * weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _calculate_returns(self, data: pd.DataFrame) -> pd.Series:
        """Calculate N-day returns from price data based on time_period_days."""
        if "Close" not in data.columns:
            raise ValueError("Data must have 'Close' column")

        if self.time_period_days == 1:
            # Standard daily returns
            returns = data["Close"].pct_change().dropna()
        else:
            # N-day returns: (price[t] - price[t-N]) / price[t-N]
            returns = (
                data["Close"] / data["Close"].shift(self.time_period_days) - 1
            ).dropna()

        return returns

    def _detrend_returns(self, returns: pd.Series) -> pd.Series:
        """Remove linear trend from returns."""
        x = np.arange(len(returns))
        y = returns.values

        # Fit linear trend
        slope, intercept, _, _, _ = stats.linregress(x, y)
        trend = slope * x + intercept

        # Remove trend
        detrended = y - trend
        return pd.Series(detrended, index=returns.index)

    def _create_pattern(
        self,
        pattern_type: PatternType,
        period: str,
        returns: np.ndarray,
        all_returns: np.ndarray,
    ) -> SeasonalityPattern:
        """Create a seasonality pattern from returns data."""
        avg_return = np.mean(returns) * 100  # Convert to percentage
        std_dev = np.std(returns) * 100
        win_rate = np.sum(returns > 0) / len(returns)

        # Statistical test against all returns
        t_stat, p_value = stats.ttest_ind(returns, all_returns)
        statistical_significance = 1 - p_value if p_value < self.confidence_level else 0

        # Confidence interval
        se = std_dev / np.sqrt(len(returns))
        margin = se * stats.t.ppf((1 + self.confidence_level) / 2, len(returns) - 1)
        ci_lower = avg_return - margin
        ci_upper = avg_return + margin

        return SeasonalityPattern(
            pattern_type=pattern_type,
            period=period,
            average_return=avg_return,
            std_dev=std_dev,
            win_rate=win_rate,
            sample_size=len(returns),
            statistical_significance=statistical_significance,
            p_value=p_value,
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
        )

    def _add_current_date_context(
        self, pattern: SeasonalityPattern
    ) -> SeasonalityPattern:
        """Add current date context to seasonal pattern.

        Args:
            pattern: Original seasonal pattern

        Returns:
            Enhanced pattern with current date context
        """
        # Calculate days until this pattern period starts
        days_to_pattern = self._calculate_days_to_pattern(pattern)

        # Create new pattern with same data (no direct metadata field modification needed)
        enhanced_pattern = SeasonalityPattern(
            pattern_type=pattern.pattern_type,
            period=pattern.period,
            average_return=pattern.average_return,
            std_dev=pattern.std_dev,
            win_rate=pattern.win_rate,
            sample_size=pattern.sample_size,
            statistical_significance=pattern.statistical_significance,
            p_value=pattern.p_value,
            confidence_interval_lower=pattern.confidence_interval_lower,
            confidence_interval_upper=pattern.confidence_interval_upper,
        )

        return enhanced_pattern

    def _calculate_days_to_pattern(self, pattern: SeasonalityPattern) -> int:
        """Calculate days from current date to when this pattern typically occurs.

        Args:
            pattern: Seasonal pattern

        Returns:
            Number of days until pattern period
        """
        current_date = self.current_date

        if pattern.pattern_type == PatternType.MONTHLY:
            # For monthly patterns, calculate days to that month
            month_names = [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]
            try:
                target_month = month_names.index(pattern.period) + 1
                current_month = current_date.month

                if target_month >= current_month:
                    # Same year
                    target_date = current_date.replace(month=target_month, day=1)
                else:
                    # Next year
                    target_date = current_date.replace(
                        year=current_date.year + 1, month=target_month, day=1
                    )

                return (target_date - current_date).days
            except (ValueError, AttributeError):
                return 0

        elif pattern.pattern_type == PatternType.WEEKLY:
            # For weekly patterns, calculate days to that day of week
            day_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            try:
                target_weekday = day_names.index(pattern.period)
                current_weekday = current_date.weekday()

                days_ahead = target_weekday - current_weekday
                if days_ahead <= 0:
                    days_ahead += 7

                return days_ahead
            except (ValueError, AttributeError):
                return 0

        elif pattern.pattern_type == PatternType.QUARTERLY:
            # For quarterly patterns
            quarter_map = {"Q1": 1, "Q2": 4, "Q3": 7, "Q4": 10}
            try:
                target_month = quarter_map.get(pattern.period, 1)
                current_month = current_date.month

                if target_month >= current_month:
                    # Same year
                    target_date = current_date.replace(month=target_month, day=1)
                else:
                    # Next year
                    target_date = current_date.replace(
                        year=current_date.year + 1, month=target_month, day=1
                    )

                return (target_date - current_date).days
            except (ValueError, AttributeError):
                return 0

        return 0

    def _create_current_date_pattern(
        self, pattern: SeasonalityPattern, returns: pd.Series
    ) -> Optional[SeasonalityPattern]:
        """Create a current date specific version of a seasonal pattern.

        This filters historical returns to only include positions that were initiated
        on dates similar to today's date in previous years.

        Args:
            pattern: Original seasonal pattern
            returns: Full returns series

        Returns:
            Enhanced pattern based on current date analysis or None if insufficient data
        """
        current_date = self.current_date
        date_window_days = 7  # ±7 days around current date

        # Filter returns to current date window across all years
        current_date_returns = []
        for date, ret in returns.items():
            # Calculate day of year for both dates
            current_day_of_year = current_date.timetuple().tm_yday
            return_day_of_year = date.timetuple().tm_yday

            # Check if this return is within the date window
            day_diff = abs(current_day_of_year - return_day_of_year)
            # Handle year-end wraparound (e.g., Dec 30 vs Jan 5)
            day_diff = min(day_diff, 365 - day_diff)

            if day_diff <= date_window_days:
                current_date_returns.append(ret)

        # Need sufficient data for reliable analysis
        if len(current_date_returns) < self.min_sample_size:
            return None

        # Create new pattern based on current date filtered data
        current_date_returns_series = pd.Series(current_date_returns)

        # Calculate statistics for current date specific returns
        avg_return = current_date_returns_series.mean() * 100  # Convert to percentage
        std_dev = current_date_returns_series.std() * 100
        win_rate = (current_date_returns_series > 0).mean()

        # Statistical significance test
        from scipy.stats import ttest_1samp

        t_stat, p_value = ttest_1samp(current_date_returns_series, 0)
        statistical_significance = 1 - p_value if p_value < self.confidence_level else 0

        # Confidence interval
        se = std_dev / np.sqrt(len(current_date_returns))
        from scipy.stats import t

        margin = se * t.ppf(
            (1 + self.confidence_level) / 2, len(current_date_returns) - 1
        )
        ci_lower = avg_return - margin
        ci_upper = avg_return + margin

        # Create enhanced pattern with current date context
        current_month = current_date.strftime("%B")
        current_weekday = current_date.strftime("%A")
        current_quarter = f"Q{(current_date.month - 1) // 3 + 1}"

        # Determine the most relevant pattern type for current date
        if pattern.pattern_type == PatternType.MONTHLY:
            period = f"{current_month} (Today+{self.time_period_days}d)"
        elif pattern.pattern_type == PatternType.WEEKLY:
            period = f"{current_weekday} (Today+{self.time_period_days}d)"
        elif pattern.pattern_type == PatternType.QUARTERLY:
            period = f"{current_quarter} (Today+{self.time_period_days}d)"
        else:
            period = f"Current Date (Today+{self.time_period_days}d)"

        return SeasonalityPattern(
            pattern_type=pattern.pattern_type,
            period=period,
            average_return=avg_return,
            std_dev=std_dev,
            win_rate=win_rate,
            sample_size=len(current_date_returns),
            statistical_significance=statistical_significance,
            p_value=p_value,
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
        )
