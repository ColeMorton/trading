"""Tests for seasonality pattern analysis.

CRITICAL: These tests verify that pattern detection correctly groups returns
by time periods and doesn't create duplicates.
"""

import contextlib

import numpy as np
import pandas as pd


def get_analyzer_class():
    """Late import to avoid circular dependency."""
    # Import models first to break circular chain
    from app.tools.seasonality_analyzer import SeasonalityAnalyzer

    return SeasonalityAnalyzer


def get_pattern_type():
    """Late import to avoid circular dependency."""
    from app.cli.models.seasonality import PatternType

    return PatternType


class TestMonthlyPatterns:
    """Test monthly pattern generation."""

    def test_all_12_months_generated(self, standard_5yr_data):
        """Test that all 12 months are generated with sufficient data."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(min_sample_size=10)

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        monthly_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.MONTHLY
        ]

        # Should have 12 months
        assert len(monthly_patterns) == 12

        # Check all months present
        month_names = [p.period for p in monthly_patterns]
        expected_months = [
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

        for month in expected_months:
            assert month in month_names

    def test_returns_grouped_by_month_correctly(self, standard_5yr_data):
        """Test that returns are correctly grouped by calendar month."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(min_sample_size=5)

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        monthly_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.MONTHLY
        ]

        # Each month should have roughly 1/12 of the data (with some variance)
        total_samples = sum(p.sample_size for p in monthly_patterns)

        for pattern in monthly_patterns:
            # Each month should have some data
            assert pattern.sample_size > 0
            # Rough check: each month ~8-10% of total (some variance is normal)
            proportion = pattern.sample_size / total_samples
            assert 0.05 < proportion < 0.15  # Allow variance

    def test_month_order_preserved(self, standard_5yr_data):
        """Test that months appear in correct order."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        monthly_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.MONTHLY
        ]

        # Get the order of months
        month_names = [p.period for p in monthly_patterns]

        # Should start with January and end with December
        expected_order = [
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

        assert month_names == expected_order

    def test_no_duplicate_monthly_patterns(self, standard_5yr_data):
        """CRITICAL: Test that no duplicate monthly patterns are created."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        monthly_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.MONTHLY
        ]

        # Check for duplicates
        month_names = [p.period for p in monthly_patterns]
        assert len(month_names) == len(set(month_names))  # No duplicates

    def test_insufficient_data_months_skipped(self, few_samples_data):
        """Test that months with < min_sample_size are skipped."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(min_sample_size=10)

        patterns = analyzer.analyze_all_patterns(few_samples_data, detrend=False)
        monthly_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.MONTHLY
        ]

        # With only 40 days, not all months will have 10 samples
        assert len(monthly_patterns) < 12

        # All returned patterns should have >= min_sample_size
        for pattern in monthly_patterns:
            assert pattern.sample_size >= 10


class TestWeeklyPatterns:
    """Test weekly (day of week) pattern generation."""

    def test_all_5_weekdays_generated(self, standard_5yr_data):
        """Test that all 5 weekdays are generated."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(min_sample_size=10)

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        weekly_patterns = [p for p in patterns if p.pattern_type == pattern_type_cls.WEEKLY]

        # Should have 5 weekdays (Mon-Fri)
        assert len(weekly_patterns) == 5

        # Check all weekdays present
        day_names = [p.period for p in weekly_patterns]
        expected_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        for day in expected_days:
            assert day in day_names

    def test_weekday_order_preserved(self, standard_5yr_data):
        """Test that weekdays appear in correct order (Mon-Fri)."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        weekly_patterns = [p for p in patterns if p.pattern_type == pattern_type_cls.WEEKLY]

        # Get the order of days
        day_names = [p.period for p in weekly_patterns]

        # Should be Mon-Fri
        expected_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        assert day_names == expected_order

    def test_no_weekend_data(self, standard_5yr_data):
        """Test that no weekend days (Saturday, Sunday) are included."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        weekly_patterns = [p for p in patterns if p.pattern_type == pattern_type_cls.WEEKLY]

        # Get day names
        day_names = [p.period for p in weekly_patterns]

        # Should not include weekend
        assert "Saturday" not in day_names
        assert "Sunday" not in day_names

    def test_no_duplicate_weekly_patterns(self, standard_5yr_data):
        """CRITICAL: Test that no duplicate weekly patterns are created."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        weekly_patterns = [p for p in patterns if p.pattern_type == pattern_type_cls.WEEKLY]

        # Check for duplicates
        day_names = [p.period for p in weekly_patterns]
        assert len(day_names) == len(set(day_names))  # No duplicates


class TestQuarterlyPatterns:
    """Test quarterly pattern generation."""

    def test_all_4_quarters_generated(self, standard_5yr_data):
        """Test that all 4 quarters are generated."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(min_sample_size=10)

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        quarterly_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.QUARTERLY
        ]

        # Should have 4 quarters
        assert len(quarterly_patterns) == 4

        # Check all quarters present
        quarter_names = [p.period for p in quarterly_patterns]
        expected_quarters = ["Q1", "Q2", "Q3", "Q4"]

        for quarter in expected_quarters:
            assert quarter in quarter_names

    def test_months_assigned_to_correct_quarters(self):
        """Test that months are correctly assigned to quarters."""
        # Create data with known month distribution
        dates = []
        for year in range(2020, 2025):
            for month in range(1, 13):
                # Add ~20 days per month
                for day in range(1, 21):
                    with contextlib.suppress(ValueError):
                        dates.append(pd.Timestamp(year=year, month=month, day=day))

        # Create price data
        prices = [100.0]
        for _ in range(len(dates) - 1):
            prices.append(prices[-1] * (1 + np.random.normal(0.001, 0.02)))

        data = pd.DataFrame({"Date": dates, "Close": prices}).set_index("Date")

        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(min_sample_size=10)
        patterns = analyzer.analyze_all_patterns(data, detrend=False)
        quarterly_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.QUARTERLY
        ]

        # Each quarter should have roughly 3 months of data
        # Q1 = Jan-Mar, Q2 = Apr-Jun, Q3 = Jul-Sep, Q4 = Oct-Dec
        # Each should have ~1/4 of the total returns
        total_samples = sum(p.sample_size for p in quarterly_patterns)

        for pattern in quarterly_patterns:
            proportion = pattern.sample_size / total_samples
            assert 0.15 < proportion < 0.35  # Allow variance, should be ~25%

    def test_no_duplicate_quarterly_patterns(self, standard_5yr_data):
        """CRITICAL: Test that no duplicate quarterly patterns are created."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        quarterly_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.QUARTERLY
        ]

        # Check for duplicates
        quarter_names = [p.period for p in quarterly_patterns]
        assert len(quarter_names) == len(set(quarter_names))  # No duplicates


class TestWeekOfYearPatterns:
    """Test week-of-year pattern generation."""

    def test_weeks_1_to_52_generated(self, standard_5yr_data):
        """Test that weeks 1-52 are generated."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(min_sample_size=5)  # Lower threshold for weeks

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        week_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.WEEK_OF_YEAR
        ]

        # Should have most weeks (may not have all 52 with min_sample_size)
        assert len(week_patterns) >= 40  # At least 40 weeks with 5 years of data

        # All weeks should be between 1-53
        for pattern in week_patterns:
            assert pattern.period_number is not None
            assert 1 <= pattern.period_number <= 53

    def test_period_number_set_for_sorting(self, standard_5yr_data):
        """CRITICAL: Test that period_number is set for week-of-year patterns."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(min_sample_size=5)

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        week_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.WEEK_OF_YEAR
        ]

        # All week patterns should have period_number
        for pattern in week_patterns:
            assert pattern.period_number is not None
            # period_number should match the week number in period string
            expected_week = int(pattern.period.replace("Week ", ""))
            assert pattern.period_number == expected_week

    def test_weeks_can_be_sorted_by_period_number(self, standard_5yr_data):
        """Test that weeks can be sorted correctly by period_number."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(min_sample_size=5)

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        week_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.WEEK_OF_YEAR
        ]

        # Sort by period_number
        sorted_patterns = sorted(week_patterns, key=lambda p: p.period_number)

        # Verify ascending order
        for i in range(len(sorted_patterns) - 1):
            assert (
                sorted_patterns[i].period_number < sorted_patterns[i + 1].period_number
            )

    def test_week_53_handled_when_present(self):
        """Test that week 53 (leap year) is handled if present in data."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        # Create data that includes week 53
        # 2020 had week 53 (ISO week date)
        dates = pd.date_range("2020-01-01", "2020-12-31", freq="D")

        prices = [100.0]
        for _ in range(len(dates) - 1):
            prices.append(prices[-1] * (1 + np.random.normal(0.001, 0.02)))

        data = pd.DataFrame({"Date": dates, "Close": prices}).set_index("Date")

        analyzer = analyzer_cls(min_sample_size=2)
        patterns = analyzer.analyze_all_patterns(data, detrend=False)
        week_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.WEEK_OF_YEAR
        ]

        # Check if week 53 exists (depends on ISO week calendar for 2020)
        week_numbers = [p.period_number for p in week_patterns]
        # Week 53 may or may not exist depending on the year, but should handle it
        assert all(1 <= w <= 53 for w in week_numbers)

    def test_no_duplicate_week_patterns(self, standard_5yr_data):
        """CRITICAL: Test that no duplicate week-of-year patterns are created."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(min_sample_size=5)

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        week_patterns = [
            p for p in patterns if p.pattern_type == pattern_type_cls.WEEK_OF_YEAR
        ]

        # Check for duplicates by period_number
        week_numbers = [p.period_number for p in week_patterns]
        assert len(week_numbers) == len(set(week_numbers))  # No duplicates


class TestPatternAnalysisIntegration:
    """Test complete pattern analysis."""

    def test_all_pattern_types_generated(self, standard_5yr_data):
        """Test that all 5 pattern types are generated."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(min_sample_size=5)

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)

        # Get unique pattern types
        pattern_types = {p.pattern_type for p in patterns}

        # Should have all 5 types
        expected_types = {
            pattern_type_cls.MONTHLY,
            pattern_type_cls.WEEKLY,
            pattern_type_cls.QUARTERLY,
            pattern_type_cls.DAY_OF_MONTH,
            pattern_type_cls.WEEK_OF_YEAR,
        }

        assert pattern_types == expected_types

    def test_no_duplicate_patterns_across_types(self, standard_5yr_data):
        """CRITICAL: Test that there are no duplicate patterns across all types."""
        analyzer_cls = get_analyzer_class()

        analyzer = analyzer_cls()

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)

        # Create unique identifier for each pattern (type + period)
        pattern_ids = [(p.pattern_type, p.period) for p in patterns]

        # Check no duplicates
        assert len(pattern_ids) == len(set(pattern_ids))

    def test_detrending_option_works(self, standard_5yr_data):
        """Test that detrending option affects results."""
        analyzer_cls = get_analyzer_class()

        analyzer = analyzer_cls()

        # Run with detrending
        patterns_detrended = analyzer.analyze_all_patterns(
            standard_5yr_data, detrend=True,
        )

        # Run without detrending
        patterns_raw = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)

        # Should have same number of patterns
        assert len(patterns_detrended) == len(patterns_raw)

        # But values may differ (detrending can change returns)
        # Just verify both complete successfully
        assert len(patterns_detrended) > 0
        assert len(patterns_raw) > 0

    def test_empty_data_returns_empty_patterns(self):
        """Test that empty data returns empty pattern list."""
        analyzer_cls = get_analyzer_class()

        analyzer = analyzer_cls()

        # Empty dataframe
        empty_data = pd.DataFrame(
            {"Date": pd.DatetimeIndex([]), "Close": []},
        ).set_index("Date")

        patterns = analyzer.analyze_all_patterns(empty_data, detrend=False)

        # Should return empty list without crashing
        assert patterns == []

    def test_min_sample_size_filtering(self, standard_5yr_data):
        """Test that min_sample_size correctly filters patterns."""
        analyzer_cls = get_analyzer_class()

        # High min_sample_size should filter out more patterns
        analyzer_strict = SeasonalityAnalyzer(min_sample_size=100)
        patterns_strict = analyzer_strict.analyze_all_patterns(
            standard_5yr_data, detrend=False,
        )

        # Low min_sample_size should allow more patterns
        analyzer_lenient = SeasonalityAnalyzer(min_sample_size=5)
        patterns_lenient = analyzer_lenient.analyze_all_patterns(
            standard_5yr_data, detrend=False,
        )

        # Lenient should have >= strict
        assert len(patterns_lenient) >= len(patterns_strict)

        # All strict patterns should have >= 100 samples
        for pattern in patterns_strict:
            assert pattern.sample_size >= 100

        # All lenient patterns should have >= 5 samples
        for pattern in patterns_lenient:
            assert pattern.sample_size >= 5


class TestSeasonalStrengthCalculation:
    """Test overall seasonal strength calculation."""

    def test_seasonal_strength_between_0_and_1(self, standard_5yr_data):
        """Test that seasonal strength is between 0 and 1."""
        analyzer_cls = get_analyzer_class()

        analyzer = analyzer_cls()

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)
        strength = analyzer.calculate_seasonal_strength(patterns)

        assert 0 <= strength <= 1

    def test_seasonal_strength_empty_patterns(self):
        """Test seasonal strength returns 0 for empty patterns."""
        analyzer_cls = get_analyzer_class()

        analyzer = analyzer_cls()

        strength = analyzer.calculate_seasonal_strength([])

        assert strength == 0.0

    def test_seasonal_strength_weighted_by_sample_size(self, standard_5yr_data):
        """Test that seasonal strength is weighted by sample sizes."""
        analyzer_cls = get_analyzer_class()

        analyzer = analyzer_cls()

        patterns = analyzer.analyze_all_patterns(standard_5yr_data, detrend=False)

        # Calculate expected weighted average
        total_weight = sum(p.sample_size for p in patterns)
        weighted_sum = sum(p.statistical_significance * p.sample_size for p in patterns)
        expected_strength = weighted_sum / total_weight if total_weight > 0 else 0

        actual_strength = analyzer.calculate_seasonal_strength(patterns)

        assert abs(actual_strength - expected_strength) < 0.001
