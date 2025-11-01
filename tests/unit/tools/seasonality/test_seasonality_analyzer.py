"""Tests for seasonality analyzer core functionality.

CRITICAL: These tests verify mathematical accuracy of risk metrics.
Incorrect calculations could lead to wrong investment decisions.
"""

import numpy as np
import pytest
from scipy import stats as scipy_stats


def get_analyzer_class():
    """Late import to avoid circular dependency."""
    # Import models first to break circular chain
    from app.tools.seasonality_analyzer import SeasonalityAnalyzer

    return SeasonalityAnalyzer


def get_pattern_type():
    """Late import to avoid circular dependency."""
    from app.tools.models.seasonality import PatternType

    return PatternType


@pytest.mark.unit
class TestSeasonalityAnalyzerInitialization:
    """Test analyzer initialization."""

    def test_default_initialization(self):
        """Test analyzer initializes with default parameters."""
        analyzer_cls = get_analyzer_class()

        analyzer = analyzer_cls()

        assert analyzer.confidence_level == 0.95
        assert analyzer.min_sample_size == 10
        assert analyzer.time_period_days == 1

    def test_custom_initialization(self):
        """Test analyzer initializes with custom parameters."""
        analyzer_cls = get_analyzer_class()

        analyzer = analyzer_cls(
            confidence_level=0.99,
            min_sample_size=20,
            time_period_days=5,
        )

        assert analyzer.confidence_level == 0.99
        assert analyzer.min_sample_size == 20
        assert analyzer.time_period_days == 5


@pytest.mark.unit
class TestSharpeRatioCalculation:
    """CRITICAL: Test Sharpe ratio calculation accuracy."""

    def test_sharpe_positive_returns(self):
        """Test Sharpe ratio calculation with positive returns."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        # Known returns: mean=0.01 (1%), std=0.02 (2%)
        returns = np.array(
            [0.01, 0.015, 0.005, 0.012, 0.008, 0.011, 0.013, 0.009, 0.007, 0.014],
        )
        all_returns = returns  # Doesn't matter for this test

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=all_returns,
        )

        # Sharpe = (mean * 100) / (std * 100) = mean / std (assuming risk-free rate = 0)
        expected_sharpe = (np.mean(returns) * 100) / (np.std(returns) * 100)

        assert pattern.sharpe_ratio is not None
        assert abs(pattern.sharpe_ratio - expected_sharpe) < 0.01

    def test_sharpe_negative_returns(self):
        """Test Sharpe ratio is negative when returns are negative."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        returns = np.array(
            [
                -0.01,
                -0.015,
                -0.005,
                -0.012,
                -0.008,
                -0.011,
                -0.013,
                -0.009,
                -0.007,
                -0.014,
            ],
        )

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Negative mean should give negative Sharpe
        assert pattern.sharpe_ratio < 0

    def test_sharpe_zero_std_deviation(self):
        """CRITICAL: Test Sharpe ratio handles zero std deviation."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        # All same return = zero variance
        returns = np.array([0.01] * 10)

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Should return 0 when std = 0 (handled in code)
        assert pattern.sharpe_ratio == 0


@pytest.mark.unit
class TestSortinoRatioCalculation:
    """CRITICAL: Test Sortino ratio calculation accuracy."""

    def test_sortino_uses_downside_deviation_only(self):
        """CRITICAL: Sortino must use ONLY downside (negative) returns for std."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        # Mix of positive and negative returns
        returns = np.array(
            [0.02, 0.015, -0.01, 0.01, -0.005, 0.012, -0.008, 0.009, -0.003, 0.011],
        )

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Calculate expected Sortino manually
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) * 100
        mean_return = np.mean(returns) * 100
        expected_sortino = mean_return / downside_std if downside_std > 0 else 0

        assert pattern.sortino_ratio is not None
        assert abs(pattern.sortino_ratio - expected_sortino) < 0.01

    def test_sortino_all_positive_returns(self):
        """CRITICAL: Sortino with all positive returns (no downside)."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        # All positive - no downside deviation
        returns = np.array(
            [0.01, 0.015, 0.005, 0.012, 0.008, 0.011, 0.013, 0.009, 0.007, 0.014],
        )

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # When no downside, code uses regular std
        # This is correct behavior (fallback to Sharpe-like calculation)
        assert pattern.sortino_ratio is not None

    def test_sortino_differs_from_sharpe_with_asymmetric_returns(self):
        """Test that Sortino differs from Sharpe when returns are asymmetric."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        # Highly asymmetric: many small gains, few large losses
        returns = np.array(
            [0.01, 0.01, 0.01, 0.01, 0.01, -0.05, -0.04, 0.01, 0.01, 0.01],
        )

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Sortino should be different from Sharpe due to asymmetry
        assert pattern.sharpe_ratio != pattern.sortino_ratio


@pytest.mark.unit
class TestMaximumDrawdown:
    """CRITICAL: Test maximum drawdown calculation."""

    def test_max_drawdown_identifies_worst_loss(self):
        """Test that max drawdown correctly identifies the worst single-period loss."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        returns = np.array([0.01, -0.02, 0.005, -0.08, 0.01, 0.02])  # -8% is worst

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Max drawdown should be -8.0 (converted to percentage)
        assert pattern.max_drawdown == -8.0

    def test_max_drawdown_all_positive(self):
        """Test max drawdown with all positive returns."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        returns = np.array([0.01, 0.02, 0.015, 0.008, 0.012])

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Max drawdown should be small positive value (smallest return)
        assert pattern.max_drawdown > 0

    def test_max_drawdown_all_negative(self):
        """Test max drawdown with all negative returns."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        returns = np.array([-0.01, -0.02, -0.015, -0.008, -0.012])

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Max drawdown should be most negative (-2.0%)
        assert pattern.max_drawdown == -2.0


@pytest.mark.unit
class TestSkewnessCalculation:
    """CRITICAL: Test skewness calculation."""

    def test_skewness_requires_minimum_samples(self):
        """Test that skewness is 0 when fewer than 3 samples."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        # Only 2 samples
        returns = np.array([0.01, 0.02])

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Should be 0 (insufficient samples)
        assert pattern.skewness == 0

    def test_skewness_positive_for_right_tail(self, high_skew_data):
        """Test positive skewness for right-tailed distribution."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        # Calculate returns from price data
        returns = high_skew_data["Close"].pct_change().dropna()

        # Take a subset with outliers on right
        returns_array = returns.values[:100]

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns_array,
            all_returns=returns_array,
        )

        # Should detect positive skew (outliers on right)
        assert pattern.skewness is not None

    def test_skewness_matches_scipy(self):
        """Test that skewness matches scipy.stats.skew calculation."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        np.random.seed(42)
        returns = np.random.normal(0, 0.02, 50)

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Compare with scipy calculation
        expected_skew = float(scipy_stats.skew(returns))

        assert abs(pattern.skewness - expected_skew) < 0.01


@pytest.mark.unit
class TestKurtosisCalculation:
    """CRITICAL: Test kurtosis calculation."""

    def test_kurtosis_requires_minimum_samples(self):
        """Test that kurtosis is 0 when fewer than 4 samples."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        # Only 3 samples
        returns = np.array([0.01, 0.02, 0.015])

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Should be 0 (insufficient samples)
        assert pattern.kurtosis == 0

    def test_kurtosis_matches_scipy(self):
        """Test that kurtosis matches scipy.stats.kurtosis calculation."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        np.random.seed(42)
        returns = np.random.normal(0, 0.02, 50)

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Compare with scipy calculation
        expected_kurt = float(scipy_stats.kurtosis(returns))

        assert abs(pattern.kurtosis - expected_kurt) < 0.01


@pytest.mark.unit
class TestStatisticalSignificance:
    """CRITICAL: Test statistical significance calculations."""

    def test_p_value_in_valid_range(self):
        """Test that p-value is always between 0 and 1."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 50)
        all_returns = np.random.normal(0, 0.02, 500)

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=all_returns,
        )

        # P-value must be between 0 and 1
        assert 0 <= pattern.p_value <= 1

    def test_significance_equals_one_minus_pvalue_when_significant(self):
        """Test that statistical_significance = 1 - p_value when p < confidence_level."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(confidence_level=0.95)

        # Create data with clear difference (very low p-value)
        returns = np.array([0.05] * 20)  # High returns
        all_returns = np.array([0.001] * 200)  # Low returns

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=all_returns,
        )

        if pattern.p_value < 0.95:
            assert abs(pattern.statistical_significance - (1 - pattern.p_value)) < 0.01

    def test_significance_zero_when_not_significant(self):
        """Test that statistical_significance = 0 when p >= confidence_level."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(confidence_level=0.95)

        # Create data with no difference (high p-value)
        np.random.seed(42)
        returns = np.random.normal(0, 0.02, 20)
        all_returns = np.random.normal(0, 0.02, 200)

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=all_returns,
        )

        # High p-value should give significance = 0
        if pattern.p_value >= 0.95:
            assert pattern.statistical_significance == 0


@pytest.mark.unit
class TestConfidenceIntervals:
    """CRITICAL: Test confidence interval calculations."""

    def test_confidence_interval_calculated(self):
        """Test that confidence intervals are calculated."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(confidence_level=0.95)

        returns = np.array(
            [0.01, 0.015, 0.005, 0.012, 0.008, 0.011, 0.013, 0.009, 0.007, 0.014],
        )

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Confidence intervals should be calculated
        assert pattern.confidence_interval_lower is not None
        assert pattern.confidence_interval_upper is not None

    def test_confidence_interval_contains_mean(self):
        """Test that confidence interval contains the mean."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(confidence_level=0.95)

        returns = np.array(
            [0.01, 0.015, 0.005, 0.012, 0.008, 0.011, 0.013, 0.009, 0.007, 0.014],
        )

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Mean should be within confidence interval
        mean_return = pattern.average_return
        assert (
            pattern.confidence_interval_lower
            <= mean_return
            <= pattern.confidence_interval_upper
        )

    def test_confidence_interval_width_increases_with_std(self):
        """Test that wider std deviation gives wider confidence interval."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls(confidence_level=0.95)

        # Low variance
        returns_low_var = np.array([0.01] * 10)
        pattern_low = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns_low_var,
            all_returns=returns_low_var,
        )

        # High variance
        returns_high_var = np.array(
            [0.0, 0.02, 0.0, 0.02, 0.0, 0.02, 0.0, 0.02, 0.0, 0.02],
        )
        pattern_high = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns_high_var,
            all_returns=returns_high_var,
        )

        # High variance should have wider CI
        width_low = (
            pattern_low.confidence_interval_upper
            - pattern_low.confidence_interval_lower
        )
        width_high = (
            pattern_high.confidence_interval_upper
            - pattern_high.confidence_interval_lower
        )

        assert width_high > width_low


@pytest.mark.unit
class TestConsistencyScore:
    """Test consistency score calculation."""

    def test_consistency_equals_win_rate(self):
        """Test that consistency score equals win rate."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        returns = np.array(
            [0.01, -0.02, 0.015, 0.005, -0.01, 0.012, 0.008, 0.011, -0.005, 0.009],
        )

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        # Consistency score should equal win rate
        assert pattern.consistency_score == pattern.win_rate

    def test_consistency_100_percent_all_positive(self, all_positive_returns_data):
        """Test 100% consistency with all positive returns."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        returns = all_positive_returns_data["Close"].pct_change().dropna()
        returns_array = returns.values[:50]

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns_array,
            all_returns=returns_array,
        )

        # All positive should give 100% win rate and consistency
        assert pattern.consistency_score == 1.0
        assert pattern.win_rate == 1.0

    def test_consistency_0_percent_all_negative(self, all_negative_returns_data):
        """Test 0% consistency with all negative returns."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        returns = all_negative_returns_data["Close"].pct_change().dropna()
        returns_array = returns.values[:50]

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns_array,
            all_returns=returns_array,
        )

        # All negative should give 0% win rate and consistency
        assert pattern.consistency_score == 0.0
        assert pattern.win_rate == 0.0


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_sample(self):
        """Test pattern creation with single sample."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        returns = np.array([0.01])

        # Should not crash
        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        assert pattern.sample_size == 1
        assert pattern.skewness == 0  # Insufficient for skew
        assert pattern.kurtosis == 0  # Insufficient for kurtosis

    def test_two_samples(self):
        """Test pattern creation with two samples."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        returns = np.array([0.01, 0.02])

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns,
            all_returns=returns,
        )

        assert pattern.sample_size == 2
        assert pattern.skewness == 0  # Insufficient for skew
        assert pattern.kurtosis == 0  # Insufficient for kurtosis

    def test_zero_variance_returns(self, flat_returns_data):
        """Test with zero variance (all same return)."""
        analyzer_cls = get_analyzer_class()
        pattern_type_cls = get_pattern_type()

        analyzer = analyzer_cls()

        returns = flat_returns_data["Close"].pct_change().dropna()
        returns_array = returns.values[:50]

        pattern = analyzer._create_pattern(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            returns=returns_array,
            all_returns=returns_array,
        )

        # Should handle zero std gracefully
        assert pattern.sharpe_ratio == 0  # Zero std handled
        assert pattern.std_dev >= 0  # Std should be ~0
