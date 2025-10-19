"""
Tests for the fixed expectancy calculator.

These tests verify that the expectancy calculation fix correctly addresses
the 596,446% variance issue and produces consistent, reasonable results.
"""

import os

from app.concurrency.tools.expectancy_calculator import (
    ExpectancyCalculator,
    fix_legacy_expectancy,
)


class TestExpectancyFix:
    """Test suite for expectancy calculation fixes."""

    def test_standard_formula_correctness(self):
        """Test that the standard formula produces correct results."""
        calc = ExpectancyCalculator(use_fixed=True)

        # Test case: 60% win rate, 2% avg win, 1% avg loss
        win_rate = 0.6
        avg_win = 0.02
        avg_loss = 0.01

        expectancy = calc.calculate_from_components(win_rate, avg_win, avg_loss)

        # Expected: (0.6 * 0.02) - (0.4 * 0.01) = 0.012 - 0.004 = 0.008
        assert abs(expectancy - 0.008) < 0.0001
        assert calc.validate_expectancy(expectancy, "test_standard")

    def test_legacy_vs_fixed_calculation(self):
        """Test the difference between legacy and fixed calculations."""
        calc = ExpectancyCalculator(use_fixed=True)

        # Test with small average loss (causes huge variance in legacy)
        win_rate = 0.5
        avg_win = 0.01
        avg_loss = 0.00001  # Very small loss

        # Legacy calculation (R-ratio)
        legacy = calc.calculate_from_components(
            win_rate, avg_win, avg_loss, legacy_mode=True
        )

        # Fixed calculation
        fixed = calc.calculate_from_components(
            win_rate, avg_win, avg_loss, legacy_mode=False
        )

        # Legacy should produce unreasonable value
        # R = 0.01 / 0.00001 = 1000
        # Legacy = (0.5 * 1000) - 0.5 = 499.5
        assert abs(legacy - 499.5) < 0.1
        assert not calc.validate_expectancy(legacy, "test_legacy")

        # Fixed should produce reasonable value
        # Fixed = (0.5 * 0.01) - (0.5 * 0.00001) = 0.005 - 0.000005 = 0.004995
        assert abs(fixed - 0.004995) < 0.00001
        assert calc.validate_expectancy(fixed, "test_fixed")

        # Verify the massive variance
        variance_ratio = legacy / fixed
        assert variance_ratio > 10000  # Over 10,000x difference!

    def test_calculate_from_returns(self):
        """Test expectancy calculation from actual returns."""
        calc = ExpectancyCalculator(use_fixed=True)

        # Sample returns: 3 wins, 2 losses
        returns = [0.02, 0.03, -0.01, 0.025, -0.015]

        expectancy, components = calc.calculate_from_returns(returns)

        # Verify components
        assert components["win_count"] == 3
        assert components["loss_count"] == 2
        assert abs(components["win_rate"] - 0.6) < 0.001
        assert abs(components["avg_win"] - 0.025) < 0.001
        assert abs(components["avg_loss"] - (-0.0125)) < 0.001

        # Verify expectancy: (0.6 * 0.025) - (0.4 * 0.0125) = 0.015 - 0.005 = 0.01
        assert abs(expectancy - 0.01) < 0.001

    def test_edge_cases(self):
        """Test edge cases in expectancy calculation."""
        calc = ExpectancyCalculator(use_fixed=True)

        # All wins
        expectancy = calc.calculate_from_components(1.0, 0.02, 0.01)
        assert expectancy == 0.02

        # All losses
        expectancy = calc.calculate_from_components(0.0, 0.02, 0.01)
        assert expectancy == -0.01

        # Zero average loss
        expectancy = calc.calculate_from_components(0.5, 0.02, 0.0)
        assert expectancy == 0.01

        # Zero returns
        expectancy, components = calc.calculate_from_returns([])
        assert expectancy == 0.0
        assert components["win_count"] == 0
        assert components["loss_count"] == 0

    def test_stop_loss_calculation(self):
        """Test expectancy calculation with stop loss."""
        calc = ExpectancyCalculator(use_fixed=True)

        # Returns with some that exceed stop loss
        returns = [0.03, -0.05, 0.02, -0.08, 0.04]  # 2 losses exceed 3% stop
        stop_loss = 0.03

        expectancy, components = calc.calculate_with_stop_loss(
            returns, stop_loss, "Long"
        )

        # Losses should be capped at -0.03
        # Adjusted returns: [0.03, -0.03, 0.02, -0.03, 0.04]
        # Win rate: 3/5 = 0.6
        # Avg win: (0.03 + 0.02 + 0.04) / 3 = 0.03
        # Avg loss: (-0.03 + -0.03) / 2 = -0.03
        # Expectancy: (0.6 * 0.03) - (0.4 * 0.03) = 0.018 - 0.012 = 0.006

        assert abs(expectancy - 0.006) < 0.001
        assert components["loss_count"] == 2

    def test_environment_variable_control(self):
        """Test that environment variable controls behavior."""
        # Set environment to use legacy
        os.environ["USE_FIXED_EXPECTANCY_CALC"] = "false"
        calc_legacy = ExpectancyCalculator()
        assert not calc_legacy.use_fixed

        # Set environment to use fixed
        os.environ["USE_FIXED_EXPECTANCY_CALC"] = "true"
        calc_fixed = ExpectancyCalculator()
        assert calc_fixed.use_fixed

        # Clean up
        del os.environ["USE_FIXED_EXPECTANCY_CALC"]

    def test_fix_legacy_expectancy_conversion(self):
        """Test conversion of legacy R-ratio expectancy to percentage."""
        # Legacy expectancy of 2R with 1% average loss
        legacy_expectancy = 2.0
        avg_loss = 0.01

        fixed = fix_legacy_expectancy(legacy_expectancy, avg_loss)

        # Should convert to 2% (2R * 1%)
        assert abs(fixed - 0.02) < 0.0001

    def test_variance_fix_demonstration(self):
        """Demonstrate the fix for the 596,446% variance issue."""
        calc = ExpectancyCalculator(use_fixed=True)

        # Scenario from the data integrity report
        win_rate = 0.6
        avg_win = 0.05
        avg_loss = 0.00001  # Tiny loss causing the issue

        # Calculate both ways
        legacy = calc.calculate_from_components(
            win_rate, avg_win, avg_loss, legacy_mode=True
        )
        fixed = calc.calculate_from_components(
            win_rate, avg_win, avg_loss, legacy_mode=False
        )

        # Print for demonstration
        print("\nVariance Fix Demonstration:")
        print(f"Win Rate: {win_rate:.1%}")
        print(f"Avg Win: {avg_win:.2%}")
        print(f"Avg Loss: {avg_loss:.4%}")
        print(f"\nLegacy (R-ratio) Expectancy: {legacy:.2%}")
        print(f"Fixed (Standard) Expectancy: {fixed:.4%}")
        print(f"Variance: {(legacy/fixed - 1)*100:.0f}%")

        # Verify the fix reduces variance to reasonable levels
        assert legacy > 100  # Legacy produces unreasonable value
        assert 0 < fixed < 0.1  # Fixed produces reasonable value
        assert legacy / fixed > 1000  # Demonstrates massive variance


if __name__ == "__main__":
    # Run a quick demonstration
    test = TestExpectancyFix()
    test.test_variance_fix_demonstration()
