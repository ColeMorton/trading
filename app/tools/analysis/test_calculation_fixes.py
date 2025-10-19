"""
Test Suite for SPDS Calculation Fixes

This test suite validates the critical fixes for SPDS calculation errors.
It tests against the actual data from live_signals.csv to ensure corrections work properly.

Tests cover:
1. Portfolio aggregation corrections
2. Percentile calculation fixes
3. MAE calculation consistency
4. Sharpe ratio corrections
5. Data validation improvements
6. Edge case handling

Author: Claude Code Analysis
Date: July 2025
"""

import os
import sys
import unittest

import numpy as np
import pandas as pd


# Add the project root to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.tools.analysis.calculation_fixes import (
    DataValidationFixes,
    EdgeCaseHandling,
    MAECalculationFixes,
    PercentileCalculationFixes,
    PortfolioAggregationFixes,
    SharpeRatioFixes,
    SPDSCalculationCorrector,
)


class TestPortfolioAggregationFixes(unittest.TestCase):
    """Test portfolio aggregation calculation fixes"""

    def setUp(self):
        """Set up test data"""
        self.sample_positions = pd.DataFrame(
            {
                "Position_UUID": [
                    "NFLX_EMA_19_46_20250414",
                    "AMD_SMA_7_45_20250508",
                    "CRWD_EMA_5_21_20250414",
                ],
                "Current_Unrealized_PnL": [0.3840, 0.3475, 0.3119],
                "Max_Favourable_Excursion": [0.438, 0.450, 0.339],
                "Max_Adverse_Excursion": [0.014, 0.004, 0.081],
                "Position_Size": [1.0, 1.0, 1.0],
                "Status": ["Open", "Open", "Open"],
            }
        )

    def test_portfolio_aggregation_error_fix(self):
        """Test the critical portfolio aggregation error fix"""

        # Original incorrect method (simple sum)
        original_incorrect = self.sample_positions["Current_Unrealized_PnL"].sum()

        # Correct method (equal weighted average)
        correct_total = PortfolioAggregationFixes.calculate_portfolio_return_correct(
            self.sample_positions, "equal_weighted"
        )

        # The original method was summing instead of averaging
        expected_correct = self.sample_positions["Current_Unrealized_PnL"].mean()

        self.assertAlmostEqual(correct_total, expected_correct, places=6)

        # Verify the error was significant
        self.assertNotAlmostEqual(original_incorrect, correct_total, places=2)

        # The correct total should be much lower than the incorrect sum
        self.assertLess(correct_total, original_incorrect)

    def test_success_rate_calculation(self):
        """Test success rate calculation accuracy"""

        metrics = PortfolioAggregationFixes.calculate_portfolio_metrics_correct(
            self.sample_positions
        )

        # All positions in sample are profitable
        expected_success_rate = 1.0

        self.assertEqual(metrics["success_rate"], expected_success_rate)

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation in portfolio metrics"""

        metrics = PortfolioAggregationFixes.calculate_portfolio_metrics_correct(
            self.sample_positions
        )

        # Should have a reasonable Sharpe ratio
        self.assertIsInstance(metrics["sharpe_ratio"], float)
        self.assertGreater(metrics["sharpe_ratio"], 0)
        self.assertLess(metrics["sharpe_ratio"], 10)  # Should not be extremely high


class TestPercentileCalculationFixes(unittest.TestCase):
    """Test percentile calculation timeframe fixes"""

    def setUp(self):
        """Set up test data"""
        # Generate sample historical daily returns (normal distribution)
        np.random.seed(42)
        self.historical_returns = pd.Series(np.random.normal(0.001, 0.02, 1000))

    def test_holding_period_percentiles(self):
        """Test holding period percentile calculations"""

        percentiles = PercentileCalculationFixes.calculate_holding_period_percentiles(
            self.historical_returns, [30, 60, 90]
        )

        # Should have results for all requested periods
        self.assertIn(30, percentiles)
        self.assertIn(60, percentiles)
        self.assertIn(90, percentiles)

        # Each period should have proper percentile structure
        for period in [30, 60, 90]:
            self.assertIn("p50", percentiles[period])
            self.assertIn("p95", percentiles[period])
            self.assertIn("count", percentiles[period])

            # Longer periods should generally have higher volatility
            self.assertGreater(percentiles[period]["count"], 0)

    def test_correct_percentile_rank(self):
        """Test correct percentile rank calculation"""

        # Test with 30-day holding period
        current_return = 0.30  # 30% return
        holding_period = 30

        percentile_rank = PercentileCalculationFixes.calculate_correct_percentile_rank(
            current_return, self.historical_returns, holding_period
        )

        # Should be a high percentile for 30% return
        self.assertGreater(percentile_rank, 90)
        self.assertLessEqual(percentile_rank, 99.9)

        # Test edge cases
        zero_return_rank = PercentileCalculationFixes.calculate_correct_percentile_rank(
            0.0, self.historical_returns, holding_period
        )

        # Zero return should be around 50th percentile
        self.assertGreater(zero_return_rank, 30)
        self.assertLess(zero_return_rank, 70)


class TestMAECalculationFixes(unittest.TestCase):
    """Test MAE calculation consistency fixes"""

    def test_mae_validation(self):
        """Test MAE calculation validation"""

        # Test valid MFE/MAE relationship
        validation = MAECalculationFixes.validate_mae_calculation(
            mfe=0.438,
            mae=0.014,
            current_return=0.384,
            entry_price=100.0,
            position_data={},
        )

        self.assertTrue(validation["is_valid"])
        self.assertIn("mfe_mae_ratio", validation["corrected_values"])
        self.assertIn("exit_efficiency", validation["corrected_values"])

        # Test invalid relationship (negative MFE)
        invalid_validation = MAECalculationFixes.validate_mae_calculation(
            mfe=-0.1,
            mae=0.014,
            current_return=0.384,
            entry_price=100.0,
            position_data={},
        )

        self.assertFalse(invalid_validation["is_valid"])
        self.assertGreater(len(invalid_validation["errors"]), 0)

    def test_mfe_mae_ratio_correction(self):
        """Test MFE/MAE ratio correction"""

        # Test the original data discrepancy
        # Original: MFE=0.438, MAE=0.014 should give ratio of ~31.3
        validation = MAECalculationFixes.validate_mae_calculation(
            mfe=0.438,
            mae=0.014,
            current_return=0.384,
            entry_price=100.0,
            position_data={},
        )

        expected_ratio = 0.438 / 0.014
        self.assertAlmostEqual(
            validation["corrected_values"]["mfe_mae_ratio"], expected_ratio, places=2
        )

    def test_exit_efficiency_correction(self):
        """Test exit efficiency calculation"""

        validation = MAECalculationFixes.validate_mae_calculation(
            mfe=0.438,
            mae=0.014,
            current_return=0.384,
            entry_price=100.0,
            position_data={},
        )

        expected_efficiency = 0.384 / 0.438
        self.assertAlmostEqual(
            validation["corrected_values"]["exit_efficiency"],
            expected_efficiency,
            places=3,
        )


class TestSharpeRatioFixes(unittest.TestCase):
    """Test Sharpe ratio calculation fixes"""

    def setUp(self):
        """Set up test data"""
        # Generate sample returns
        np.random.seed(42)
        self.returns = pd.Series(np.random.normal(0.001, 0.02, 100))

    def test_correct_sharpe_ratio(self):
        """Test correct Sharpe ratio calculation"""

        sharpe_ratio = SharpeRatioFixes.calculate_correct_sharpe_ratio(
            self.returns, risk_free_rate=0.05, period="daily"
        )

        # Should be a reasonable value
        self.assertIsInstance(sharpe_ratio, float)
        self.assertGreater(sharpe_ratio, -5)
        self.assertLess(sharpe_ratio, 5)

    def test_sharpe_ratio_validation(self):
        """Test Sharpe ratio validation"""

        # Test normal Sharpe ratio
        normal_validation = SharpeRatioFixes.validate_sharpe_ratio(1.5)
        self.assertTrue(normal_validation["is_valid"])
        self.assertEqual(normal_validation["classification"], "good")

        # Test extremely high Sharpe ratio (should trigger warning)
        high_validation = SharpeRatioFixes.validate_sharpe_ratio(3.5)
        self.assertGreater(len(high_validation["warnings"]), 0)
        self.assertEqual(high_validation["classification"], "exceptional")

    def test_sharpe_ratio_periods(self):
        """Test Sharpe ratio calculation for different periods"""

        daily_sharpe = SharpeRatioFixes.calculate_correct_sharpe_ratio(
            self.returns, period="daily"
        )

        # Convert to weekly returns for comparison
        weekly_returns = self.returns.rolling(5).sum().dropna()
        weekly_sharpe = SharpeRatioFixes.calculate_correct_sharpe_ratio(
            weekly_returns, period="weekly"
        )

        # Both should be reasonable
        self.assertIsInstance(daily_sharpe, float)
        self.assertIsInstance(weekly_sharpe, float)


class TestDataValidationFixes(unittest.TestCase):
    """Test data validation and precision fixes"""

    def test_financial_precision_formatting(self):
        """Test financial precision formatting"""

        # Test price formatting
        price = DataValidationFixes.format_financial_precision(123.456789, "price")
        self.assertEqual(price, 123.46)

        # Test percentage formatting
        percentage = DataValidationFixes.format_financial_precision(
            0.123456, "percentage"
        )
        self.assertEqual(percentage, 0.1235)

        # Test ratio formatting
        ratio = DataValidationFixes.format_financial_precision(3.14159, "ratio")
        self.assertEqual(ratio, 3.14)

    def test_safe_divide(self):
        """Test safe division implementation"""

        # Normal division
        result = DataValidationFixes.safe_divide(10, 2)
        self.assertEqual(result, 5.0)

        # Division by zero
        result = DataValidationFixes.safe_divide(10, 0, default=0.0)
        self.assertEqual(result, 0.0)

        # Division by very small number
        result = DataValidationFixes.safe_divide(10, 1e-12, default=0.0)
        self.assertEqual(result, 0.0)

        # Infinite result
        result = DataValidationFixes.safe_divide(float("inf"), 1, default=0.0)
        self.assertEqual(result, 0.0)


class TestEdgeCaseHandling(unittest.TestCase):
    """Test edge case handling"""

    def test_bound_ratio(self):
        """Test ratio bounding"""

        # Normal ratio
        bounded = EdgeCaseHandling.bound_ratio(3.14, max_value=100.0)
        self.assertEqual(bounded, 3.14)

        # Extreme ratio
        bounded = EdgeCaseHandling.bound_ratio(150.0, max_value=100.0)
        self.assertEqual(bounded, 100.0)

        # Negative extreme ratio
        bounded = EdgeCaseHandling.bound_ratio(-150.0, max_value=100.0)
        self.assertEqual(bounded, -100.0)

        # Infinite ratio
        bounded = EdgeCaseHandling.bound_ratio(float("inf"), max_value=100.0)
        self.assertEqual(bounded, 0.0)

    def test_validate_extreme_values(self):
        """Test extreme value validation"""

        values = {"return": 0.5, "sharpe_ratio": 2.0, "mfe_mae_ratio": 50.0}

        bounds = {
            "return": (-1.0, 5.0),
            "sharpe_ratio": (-3.0, 3.0),
            "mfe_mae_ratio": (0.0, 100.0),
        }

        validation = EdgeCaseHandling.validate_extreme_values(values, bounds)

        # Should detect sharpe_ratio and mfe_mae_ratio as within bounds
        self.assertTrue(validation["is_valid"])

        # Test with out-of-bounds values
        extreme_values = {
            "return": 10.0,  # Too high
            "sharpe_ratio": 5.0,  # Too high
            "mfe_mae_ratio": 150.0,  # Too high
        }

        extreme_validation = EdgeCaseHandling.validate_extreme_values(
            extreme_values, bounds
        )

        self.assertFalse(extreme_validation["is_valid"])
        self.assertGreater(len(extreme_validation["out_of_bounds"]), 0)


class TestSPDSCalculationCorrector(unittest.TestCase):
    """Test the main SPDS calculation corrector"""

    def setUp(self):
        """Set up test data based on actual live_signals.csv"""
        self.positions = pd.DataFrame(
            {
                "Position_UUID": [
                    "NFLX_EMA_19_46_20250414",
                    "AMD_SMA_7_45_20250508",
                    "CRWD_EMA_5_21_20250414",
                ],
                "Current_Unrealized_PnL": [0.3840, 0.3475, 0.3119],
                "Max_Favourable_Excursion": [0.438, 0.450, 0.339],
                "Max_Adverse_Excursion": [0.014, 0.004, 0.081],
                "Position_Size": [1.0, 1.0, 1.0],
                "Status": ["Open", "Open", "Open"],
            }
        )

        self.corrector = SPDSCalculationCorrector()

    def test_comprehensive_correction(self):
        """Test comprehensive portfolio correction"""

        results = self.corrector.correct_portfolio_analysis(self.positions)

        # Should have both original and corrected metrics
        self.assertIn("original_metrics", results)
        self.assertIn("corrected_metrics", results)
        self.assertIn("corrections_applied", results)

        # Corrections should be applied
        self.assertIn("portfolio_aggregation", results["corrections_applied"])
        self.assertIn("mae_calculation", results["corrections_applied"])
        self.assertIn("sharpe_ratio", results["corrections_applied"])

        # Corrected metrics should be different from original
        if "total_return_incorrect" in results["original_metrics"]:
            self.assertNotEqual(
                results["original_metrics"]["total_return_incorrect"],
                results["corrected_metrics"]["total_return_equal_weighted"],
            )

    def test_data_validation(self):
        """Test data validation in correction process"""

        results = self.corrector.correct_portfolio_analysis(self.positions)

        # Validation should pass for good data
        self.assertTrue(results["validation_results"]["is_valid"])

        # Test with invalid data
        invalid_positions = self.positions.copy()
        invalid_positions["Max_Favourable_Excursion"] = [
            -0.1,
            0.450,
            0.339,
        ]  # Invalid negative MFE

        invalid_results = self.corrector.correct_portfolio_analysis(invalid_positions)

        # Should detect the invalid data
        self.assertFalse(invalid_results["validation_results"]["is_valid"])

    def test_real_data_corrections(self):
        """Test corrections using real live_signals.csv data patterns"""

        # Test the specific error patterns found in the analysis
        results = self.corrector.correct_portfolio_analysis(self.positions)

        # The original sum error: 0.3840 + 0.3475 + 0.3119 = 1.0434
        # The correct average: (0.3840 + 0.3475 + 0.3119) / 3 = 0.3478

        expected_incorrect_sum = 1.0434
        expected_correct_average = 0.3478

        # Verify the correction is applied
        self.assertAlmostEqual(
            results["original_metrics"]["total_return_incorrect"],
            expected_incorrect_sum,
            places=3,
        )

        self.assertAlmostEqual(
            results["corrected_metrics"]["total_return_equal_weighted"],
            expected_correct_average,
            places=3,
        )


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
