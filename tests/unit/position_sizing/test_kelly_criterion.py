"""
Unit tests for Kelly Criterion Calculator

Tests Excel B17-B21 formula accuracy against known values.
"""

import pytest

from app.tools.position_sizing.kelly_criterion import (
    ConfidenceMetrics,
    KellyCriterionSizer,
    KellyMetrics,
)


@pytest.mark.unit
class TestKellyCriterionSizer:
    """Test Kelly Criterion calculator functionality and Excel formula accuracy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = KellyCriterionSizer()

    def test_calculate_confidence_metrics(self):
        """Test confidence metrics calculation from trading journal."""
        # Test case: 85 primary trades, 15 outliers
        num_primary = 85
        num_outliers = 15

        result = self.calculator.calculate_confidence_metrics(num_primary, num_outliers)

        assert isinstance(result, ConfidenceMetrics)
        assert result.num_primary == 85
        assert result.num_outliers == 15
        assert result.total_trades == 100
        assert result.confidence_ratio == 0.85
        assert result.primary_percentage == 85.0
        assert result.outlier_percentage == 15.0

    def test_excel_b20_equivalent(self):
        """Test Excel B20 formula: =B17/(B17+B18)."""
        # Excel B17 = 85 (primary), B18 = 15 (outliers)
        num_primary = 85
        num_outliers = 15
        expected = 85 / (85 + 15)  # 0.85

        result = self.calculator.calculate_excel_b20_equivalent(
            num_primary,
            num_outliers,
        )

        assert result == expected
        assert result == 0.85

    def test_excel_b21_equivalent(self):
        """Test Excel B21 formula: =B19*B20."""
        # Excel B19 = 0.25 (Kelly), B20 = 0.85 (confidence)
        num_primary = 85
        num_outliers = 15
        kelly_criterion = 0.25
        expected = 0.25 * 0.85  # 0.2125

        result = self.calculator.calculate_excel_b21_equivalent(
            num_primary,
            num_outliers,
            kelly_criterion,
        )

        assert result == expected
        assert result == 0.2125

    def test_calculate_kelly_position(self):
        """Test Kelly position calculation with confidence adjustment."""
        test_cases = [
            # (primary, outliers, kelly, expected)
            (85, 15, 0.25, 0.2125),  # 85% confidence
            (90, 10, 0.30, 0.27),  # 90% confidence
            (50, 50, 0.20, 0.10),  # 50% confidence
            (100, 0, 0.35, 0.35),  # 100% confidence
        ]

        for primary, outliers, kelly, expected in test_cases:
            result = self.calculator.calculate_kelly_position(primary, outliers, kelly)
            assert abs(result - expected) < 1e-10

    def test_get_max_risk_per_position(self):
        """Test maximum risk calculation based on portfolio value."""
        portfolio_value = 100000.0
        risk_percentage = 0.118  # 11.8%
        expected = 100000.0 * 0.118  # $11,800

        result = self.calculator.get_max_risk_per_position(
            portfolio_value,
            risk_percentage,
        )

        assert result == expected
        assert result == 11800.0

    def test_calculate_recommended_position_size(self):
        """Test recommended position size calculation."""
        num_primary = 85
        num_outliers = 15
        kelly_criterion = 0.25
        portfolio_value = 100000.0
        risk_percentage = 0.118

        # Kelly adjustment: 0.25 * 0.85 = 0.2125
        # Max risk: 100000 * 0.118 = 11800
        # Recommended: 11800 * 0.2125 = 2507.5
        expected = 11800.0 * 0.2125

        result = self.calculator.calculate_recommended_position_size(
            num_primary,
            num_outliers,
            kelly_criterion,
            portfolio_value,
            risk_percentage,
        )

        assert abs(result - expected) < 1e-10
        assert result == 2507.5

    def test_get_complete_kelly_analysis(self):
        """Test complete Kelly analysis matching Excel B17-B21."""
        num_primary = 85  # Excel B17
        num_outliers = 15  # Excel B18
        kelly_criterion = 0.25  # Excel B19
        portfolio_value = 100000.0  # Excel B2

        result = self.calculator.get_complete_kelly_analysis(
            num_primary,
            num_outliers,
            kelly_criterion,
            portfolio_value,
        )

        assert isinstance(result, KellyMetrics)
        assert result.kelly_criterion == 0.25
        assert result.confidence_metrics.confidence_ratio == 0.85  # B20
        assert result.position_size_multiplier == 0.2125  # B21
        assert result.max_risk_per_position == 11800.0
        assert result.recommended_position_size == 2507.5

    def test_validate_kelly_inputs(self):
        """Test input validation for Kelly parameters."""
        # Valid inputs
        is_valid, message = self.calculator.validate_kelly_inputs(85, 15, 0.25)
        assert is_valid
        assert "valid" in message.lower()

        # Invalid inputs
        test_cases = [
            (-1, 15, 0.25, "negative"),  # Negative primary
            (85, -1, 0.25, "negative"),  # Negative outliers
            (0, 0, 0.25, "zero"),  # Zero trades
            (85, 15, -0.1, "negative"),  # Negative Kelly
        ]

        for primary, outliers, kelly, expected_error in test_cases:
            is_valid, message = self.calculator.validate_kelly_inputs(
                primary,
                outliers,
                kelly,
            )
            assert not is_valid
            assert expected_error in message.lower()

    def test_zero_trades_handling(self):
        """Test handling of zero total trades."""
        with pytest.raises(ValueError, match="Total trades cannot be zero"):
            self.calculator.calculate_confidence_metrics(0, 0)

    def test_high_kelly_warning(self):
        """Test warning for high Kelly criterion values."""
        is_valid, message = self.calculator.validate_kelly_inputs(85, 15, 0.75)
        assert is_valid  # Still valid but with warning
        assert "High Kelly criterion" in message

    def test_high_outlier_warning(self):
        """Test warning for high outlier ratio."""
        is_valid, message = self.calculator.validate_kelly_inputs(30, 70, 0.25)
        assert is_valid  # Still valid but with warning
        assert "High outlier ratio" in message

    def test_get_kelly_statistics_summary(self):
        """Test comprehensive Kelly statistics summary."""
        num_primary = 85
        num_outliers = 15
        kelly_criterion = 0.25

        result = self.calculator.get_kelly_statistics_summary(
            num_primary,
            num_outliers,
            kelly_criterion,
        )

        assert "trading_journal_stats" in result
        assert "kelly_analysis" in result
        assert "excel_references" in result

        # Check Excel references
        excel_refs = result["excel_references"]
        assert excel_refs["B17_primary_trades"] == 85
        assert excel_refs["B18_outlier_trades"] == 15
        assert excel_refs["B19_kelly_criterion"] == 0.25
        assert excel_refs["B20_confidence_ratio"] == 0.85
        assert excel_refs["B21_adjusted_position_size"] == 0.2125

    def test_excel_formula_precision(self):
        """Test that calculations maintain Excel-level precision."""
        test_cases = [
            # (primary, outliers, kelly, expected_B20, expected_B21)
            (85, 15, 0.25, 0.85, 0.2125),
            (90, 10, 0.30, 0.90, 0.27),
            (75, 25, 0.20, 0.75, 0.15),
        ]

        for primary, outliers, kelly, expected_b20, expected_b21 in test_cases:
            b20_result = self.calculator.calculate_excel_b20_equivalent(
                primary,
                outliers,
            )
            b21_result = self.calculator.calculate_excel_b21_equivalent(
                primary,
                outliers,
                kelly,
            )

            assert abs(b20_result - expected_b20) < 1e-15  # High precision match
            assert abs(b21_result - expected_b21) < 1e-15  # High precision match
