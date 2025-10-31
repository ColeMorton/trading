"""
Comprehensive unit tests for PositionCalculator class.

Tests all calculation methods, validation logic, error handling, and precision
requirements to ensure accurate P&L calculations and prevent regression of
the original SMCI position calculation bug ($376.53 vs $13.17).
"""

import logging
import unittest
from datetime import datetime
from unittest.mock import Mock

import pytest
from hypothesis import given, strategies as st

from app.tools.position_calculator import (
    STANDARD_DAYS_PRECISION,
    STANDARD_EFFICIENCY_PRECISION,
    STANDARD_MFE_MAE_PRECISION,
    STANDARD_PNL_PRECISION,
    STANDARD_RATIO_PRECISION,
    STANDARD_RETURN_PRECISION,
    PositionCalculator,
    calculate_position_pnl_return,
    get_position_calculator,
    refresh_position_calculations,
    validate_position_data,
)


@pytest.mark.unit
class TestPositionCalculator(unittest.TestCase):
    """Unit tests for PositionCalculator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = PositionCalculator()
        self.mock_logger = Mock(spec=logging.Logger)
        self.calculator_with_logger = PositionCalculator(self.mock_logger)

        # Test data reflecting the original SMCI bug scenario
        self.smci_test_data = {
            "Avg_Entry_Price": 434.53,
            "Avg_Exit_Price": 447.70,
            "Position_Size": 1.0,
            "Direction": "Long",
            "PnL": 376.53,  # Incorrect value from bug
            "Return": 8.6618,  # Incorrect value from bug
            "Max_Favourable_Excursion": 0.434553,
            "Max_Adverse_Excursion": 0.062141,
            "MFE_MAE_Ratio": 7.0223,
            "Exit_Efficiency_Fixed": 0.6966,
            "Entry_Timestamp": "2025-06-23",
            "Current_Unrealized_PnL": 8.6618,
        }

        # Expected correct values for SMCI
        self.smci_expected = {
            "PnL": 13.17,
            "Return": 0.0303,  # (447.70 - 434.53) / 434.53 = 0.03027... ≈ 0.0303
        }

    def test_precision_constants(self):
        """Test that precision constants are correctly defined."""
        self.assertEqual(STANDARD_PNL_PRECISION, 2)
        self.assertEqual(STANDARD_RETURN_PRECISION, 4)
        self.assertEqual(STANDARD_MFE_MAE_PRECISION, 6)
        self.assertEqual(STANDARD_RATIO_PRECISION, 4)
        self.assertEqual(STANDARD_DAYS_PRECISION, 0)
        self.assertEqual(STANDARD_EFFICIENCY_PRECISION, 4)

    def test_calculate_pnl_and_return_long_position(self):
        """Test P&L and return calculation for Long positions."""
        # Test the SMCI bug scenario
        pnl, return_pct = self.calculator.calculate_pnl_and_return(
            entry_price=434.53,
            exit_price=447.70,
            position_size=1.0,
            direction="Long",
        )

        self.assertEqual(pnl, 13.17)
        self.assertEqual(return_pct, 0.0303)

        # Test with different position size
        pnl, return_pct = self.calculator.calculate_pnl_and_return(
            entry_price=100.0,
            exit_price=110.0,
            position_size=2.0,
            direction="Long",
        )

        self.assertEqual(pnl, 20.0)  # (110-100) * 2
        self.assertEqual(return_pct, 0.1)  # (110-100) / 100

    def test_calculate_pnl_and_return_short_position(self):
        """Test P&L and return calculation for Short positions."""
        pnl, return_pct = self.calculator.calculate_pnl_and_return(
            entry_price=100.0,
            exit_price=90.0,
            position_size=1.0,
            direction="Short",
        )

        self.assertEqual(pnl, 10.0)  # (100-90) * 1
        self.assertEqual(return_pct, 0.1)  # (100-90) / 100

        # Test losing short position
        pnl, return_pct = self.calculator.calculate_pnl_and_return(
            entry_price=100.0,
            exit_price=110.0,
            position_size=1.0,
            direction="Short",
        )

        self.assertEqual(pnl, -10.0)  # (100-110) * 1
        self.assertEqual(return_pct, -0.1)  # (100-110) / 100

    def test_calculate_pnl_and_return_case_insensitive(self):
        """Test that direction parameter is case insensitive."""
        test_cases = ["LONG", "long", "Long", "SHORT", "short", "Short"]

        for direction in test_cases:
            pnl, return_pct = self.calculator.calculate_pnl_and_return(
                entry_price=100.0,
                exit_price=110.0,
                position_size=1.0,
                direction=direction,
            )

            if direction.upper() == "LONG":
                self.assertEqual(pnl, 10.0)
                self.assertEqual(return_pct, 0.1)
            else:
                self.assertEqual(pnl, -10.0)
                self.assertEqual(return_pct, -0.1)

    def test_calculate_pnl_and_return_precision_rounding(self):
        """Test that P&L and return values are rounded to correct precision."""
        # Test with values that need rounding
        pnl, return_pct = self.calculator.calculate_pnl_and_return(
            entry_price=100.333,
            exit_price=103.666,
            position_size=1.5,
            direction="Long",
        )

        # Manual calculation: (103.666 - 100.333) * 1.5 = 4.9995 -> 5.00
        # Return: (103.666 - 100.333) / 100.333 = 0.033208... -> 0.0332
        self.assertEqual(pnl, 5.00)
        self.assertEqual(return_pct, 0.0332)

    def test_calculate_pnl_and_return_error_handling(self):
        """Test error handling in P&L calculation."""
        # Test with invalid inputs
        pnl, return_pct = self.calculator_with_logger.calculate_pnl_and_return(
            entry_price="invalid",
            exit_price=100.0,
            position_size=1.0,
            direction="Long",
        )

        self.assertEqual(pnl, 0.0)
        self.assertEqual(return_pct, 0.0)
        self.mock_logger.error.assert_called()

    def test_calculate_days_since_entry(self):
        """Test days since entry calculation."""
        # Test with specific date
        test_date = datetime(2023, 6, 15)
        entry_timestamp = "2023-06-10"

        days = self.calculator.calculate_days_since_entry(entry_timestamp, test_date)
        self.assertEqual(days, 5)

        # Test with current date (should be >= 0)
        days = self.calculator.calculate_days_since_entry("2023-01-01")
        self.assertGreaterEqual(days, 0)

    def test_calculate_days_since_entry_different_formats(self):
        """Test days calculation with different timestamp formats."""
        test_date = datetime(2023, 6, 15)

        test_cases = ["2023-06-10", "2023/06/10", "06-10-2023", "2023-06-10 10:30:00"]

        for timestamp in test_cases:
            days = self.calculator.calculate_days_since_entry(timestamp, test_date)
            self.assertIsInstance(days, int)
            self.assertGreaterEqual(days, 0)

    def test_calculate_days_since_entry_error_handling(self):
        """Test error handling in days calculation."""
        days = self.calculator_with_logger.calculate_days_since_entry("invalid_date")
        self.assertEqual(days, 0)
        self.mock_logger.error.assert_called()

    def test_calculate_exit_efficiency(self):
        """Test exit efficiency calculation."""
        # Test normal case
        efficiency = self.calculator.calculate_exit_efficiency(0.05, 0.08)
        self.assertEqual(efficiency, 0.625)  # 0.05 / 0.08 = 0.625

        # Test with SMCI data
        efficiency = self.calculator.calculate_exit_efficiency(0.0303, 0.434553)
        expected = round(0.0303 / 0.434553, STANDARD_EFFICIENCY_PRECISION)
        self.assertEqual(efficiency, expected)

    def test_calculate_exit_efficiency_edge_cases(self):
        """Test exit efficiency edge cases."""
        # Test with zero MFE
        efficiency = self.calculator.calculate_exit_efficiency(0.05, 0.0)
        self.assertIsNone(efficiency)

        # Test with negative MFE
        efficiency = self.calculator.calculate_exit_efficiency(0.05, -0.02)
        self.assertIsNone(efficiency)

        # Test with None MFE
        efficiency = self.calculator.calculate_exit_efficiency(0.05, None)
        self.assertIsNone(efficiency)

    def test_calculate_exit_efficiency_error_handling(self):
        """Test error handling in exit efficiency calculation."""
        efficiency = self.calculator_with_logger.calculate_exit_efficiency(
            "invalid",
            0.08,
        )
        self.assertIsNone(efficiency)
        self.mock_logger.error.assert_called()

    def test_calculate_excursion_status(self):
        """Test excursion status calculation."""
        self.assertEqual(self.calculator.calculate_excursion_status(0.05), "Favorable")
        self.assertEqual(self.calculator.calculate_excursion_status(-0.03), "Adverse")
        self.assertEqual(self.calculator.calculate_excursion_status(0.0), "Neutral")

    def test_calculate_excursion_status_error_handling(self):
        """Test error handling in excursion status calculation."""
        status = self.calculator_with_logger.calculate_excursion_status("invalid")
        self.assertEqual(status, "Unknown")
        self.mock_logger.error.assert_called()

    def test_assess_trade_quality(self):
        """Test trade quality assessment."""
        # Test excellent trade (high reward, low risk)
        quality = self.calculator.assess_trade_quality(mfe=0.08, mae=0.02)
        self.assertEqual(quality, "Excellent")  # ratio = 4.0

        # Test good trade
        quality = self.calculator.assess_trade_quality(mfe=0.06, mae=0.03)
        self.assertEqual(quality, "Excellent")  # ratio = 2.0

        # Test poor trade
        quality = self.calculator.assess_trade_quality(mfe=0.02, mae=0.04)
        self.assertEqual(quality, "Poor")  # ratio = 0.5

        # Test poor setup (high risk, low reward)
        quality = self.calculator.assess_trade_quality(mfe=0.01, mae=0.06)
        self.assertEqual(quality, "Poor Setup - High Risk, Low Reward")

    def test_assess_trade_quality_with_final_return(self):
        """Test trade quality assessment with final return consideration."""
        # Test failed upside capture
        quality = self.calculator.assess_trade_quality(
            mfe=0.05,
            mae=0.02,
            final_return=-0.08,
        )
        self.assertEqual(quality, "Failed to Capture Upside")

    def test_assess_trade_quality_edge_cases(self):
        """Test trade quality edge cases."""
        # Test with None values
        quality = self.calculator.assess_trade_quality(mfe=None, mae=0.02)
        self.assertEqual(quality, "Unknown")

        quality = self.calculator.assess_trade_quality(mfe=0.05, mae=None)
        self.assertEqual(quality, "Unknown")

        # Test with zero MAE (infinite ratio)
        quality = self.calculator.assess_trade_quality(mfe=0.05, mae=0.0)
        self.assertEqual(quality, "Excellent")

    def test_calculate_mfe_mae_ratio(self):
        """Test MFE/MAE ratio calculation."""
        # Test normal case
        ratio = self.calculator.calculate_mfe_mae_ratio(0.08, 0.02)
        self.assertEqual(ratio, 4.0)

        # Test SMCI case
        ratio = self.calculator.calculate_mfe_mae_ratio(0.434553, 0.062141)
        expected = round(0.434553 / 0.062141, STANDARD_RATIO_PRECISION)
        self.assertEqual(ratio, expected)

    def test_calculate_mfe_mae_ratio_edge_cases(self):
        """Test MFE/MAE ratio edge cases."""
        # Test with zero MAE
        ratio = self.calculator.calculate_mfe_mae_ratio(0.05, 0.0)
        self.assertEqual(ratio, float("inf"))

        # Test with None MAE
        ratio = self.calculator.calculate_mfe_mae_ratio(0.05, None)
        self.assertEqual(ratio, float("inf"))

        # Test with zero MFE, zero MAE
        ratio = self.calculator.calculate_mfe_mae_ratio(0.0, 0.0)
        self.assertEqual(ratio, 0.0)

        # Test with None MFE, positive MAE
        ratio = self.calculator.calculate_mfe_mae_ratio(None, 0.02)
        self.assertEqual(ratio, 0.0)

    def test_validate_calculation_consistency_smci_bug(self):
        """Test validation catches the original SMCI bug."""
        result = self.calculator.validate_calculation_consistency(self.smci_test_data)

        # Should detect errors
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 2)  # P&L and Return errors

        # Check specific error details
        pnl_error = next((e for e in result["errors"] if e["field"] == "PnL"), None)
        self.assertIsNotNone(pnl_error)
        self.assertEqual(pnl_error["expected"], 13.17)
        self.assertEqual(pnl_error["actual"], 376.53)

        return_error = next(
            (e for e in result["errors"] if e["field"] == "Return"),
            None,
        )
        self.assertIsNotNone(return_error)
        self.assertEqual(return_error["expected"], 0.0303)
        self.assertEqual(return_error["actual"], 8.6618)

        # Check corrected values
        self.assertEqual(result["corrected_values"]["PnL"], 13.17)
        self.assertEqual(result["corrected_values"]["Return"], 0.0303)

    def test_validate_calculation_consistency_valid_data(self):
        """Test validation passes for correct data."""
        correct_data = self.smci_test_data.copy()
        correct_data["PnL"] = 13.17
        correct_data["Return"] = 0.0303

        result = self.calculator.validate_calculation_consistency(correct_data)

        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_validate_calculation_consistency_missing_data(self):
        """Test validation handles missing critical data."""
        incomplete_data = {"Avg_Entry_Price": 100.0}  # Missing other fields

        result = self.calculator.validate_calculation_consistency(incomplete_data)

        self.assertTrue(result["valid"])  # Should pass but with warnings
        self.assertIn("Missing critical data", str(result["warnings"]))

    def test_apply_standard_rounding(self):
        """Test standardized rounding application."""
        test_values = {
            "PnL": 13.16789,
            "Return": 0.030271234,
            "Max_Favourable_Excursion": 0.4345534567,
            "MFE_MAE_Ratio": 7.02234567,
            "Exit_Efficiency_Fixed": 0.69664321,
            "Days_Since_Entry": 42.7,
            "Other_Field": "unchanged",
        }

        rounded = self.calculator.apply_standard_rounding(test_values)

        self.assertEqual(rounded["PnL"], 13.17)
        self.assertEqual(rounded["Return"], 0.0303)
        self.assertEqual(rounded["Max_Favourable_Excursion"], 0.434553)
        self.assertEqual(rounded["MFE_MAE_Ratio"], 7.0223)
        self.assertEqual(rounded["Exit_Efficiency_Fixed"], 0.6966)
        self.assertEqual(rounded["Days_Since_Entry"], 43)
        self.assertEqual(rounded["Other_Field"], "unchanged")

    def test_apply_standard_rounding_infinity(self):
        """Test standard rounding handles infinity values."""
        test_values = {"MFE_MAE_Ratio": float("inf")}
        rounded = self.calculator.apply_standard_rounding(test_values)
        self.assertEqual(rounded["MFE_MAE_Ratio"], float("inf"))

    def test_comprehensive_position_refresh_smci_bug(self):
        """Test comprehensive refresh fixes the SMCI bug."""
        result = self.calculator.comprehensive_position_refresh(self.smci_test_data)

        # Check that data was corrected
        refreshed_data = result["data"]
        self.assertEqual(refreshed_data["PnL"], 13.17)
        self.assertEqual(refreshed_data["Return"], 0.0303)
        self.assertEqual(refreshed_data["Current_Unrealized_PnL"], 0.0303)

        # Check that changes were tracked
        changes = result["changes"]
        self.assertGreater(len(changes), 0)
        self.assertTrue(any("PnL:" in change for change in changes))
        self.assertTrue(any("Return:" in change for change in changes))

        # Check validation results
        validation = result["validation"]
        self.assertTrue(validation["valid"])

    def test_comprehensive_position_refresh_with_mfe_mae_update(self):
        """Test comprehensive refresh with MFE/MAE updates."""
        result = self.calculator.comprehensive_position_refresh(
            self.smci_test_data,
            mfe=0.5,
            mae=0.1,  # New MFE  # New MAE
        )

        refreshed_data = result["data"]
        self.assertEqual(refreshed_data["Max_Favourable_Excursion"], 0.5)
        self.assertEqual(refreshed_data["Max_Adverse_Excursion"], 0.1)

        # Check that ratio was recalculated
        expected_ratio = round(0.5 / 0.1, STANDARD_RATIO_PRECISION)
        self.assertEqual(refreshed_data["MFE_MAE_Ratio"], expected_ratio)

    def test_comprehensive_position_refresh_error_handling(self):
        """Test comprehensive refresh error handling."""
        # Test with invalid data (missing critical fields)
        invalid_data = {"Avg_Entry_Price": "invalid"}

        result = self.calculator_with_logger.comprehensive_position_refresh(
            invalid_data,
        )

        # Should return original data with warnings (not errors)
        self.assertEqual(result["data"], invalid_data)
        self.assertEqual(len(result["changes"]), 0)
        self.assertTrue(
            result["validation"]["valid"],
        )  # Valid but with warnings for missing data
        self.assertIn("Missing critical data", str(result["validation"]["warnings"]))

    def test_global_calculator_instance(self):
        """Test global calculator instance functionality."""
        calc1 = get_position_calculator()
        calc2 = get_position_calculator()

        # Should return same instance
        self.assertIs(calc1, calc2)

        # Should be PositionCalculator instance
        self.assertIsInstance(calc1, PositionCalculator)

    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test calculate_position_pnl_return
        pnl, return_pct = calculate_position_pnl_return(100.0, 110.0, 1.0, "Long")
        self.assertEqual(pnl, 10.0)
        self.assertEqual(return_pct, 0.1)

        # Test validate_position_data
        result = validate_position_data(self.smci_test_data)
        self.assertFalse(result["valid"])

        # Test refresh_position_calculations
        result = refresh_position_calculations(self.smci_test_data)
        self.assertEqual(result["data"]["PnL"], 13.17)


@pytest.mark.unit
class TestPositionCalculatorRegression(unittest.TestCase):
    """Regression tests for specific bugs and edge cases."""

    def setUp(self):
        """Set up regression test fixtures."""
        self.calculator = PositionCalculator()

    def test_smci_bug_regression(self):
        """Regression test for SMCI P&L calculation bug."""
        # Original bug: SMCI position calculated as $376.53 instead of $13.17
        pnl, return_pct = self.calculator.calculate_pnl_and_return(
            entry_price=434.53,
            exit_price=447.70,
            position_size=1.0,
            direction="Long",
        )

        # Ensure the bug doesn't reoccur
        self.assertEqual(pnl, 13.17)
        self.assertNotEqual(pnl, 376.53)
        self.assertEqual(return_pct, 0.0303)

    def test_amzn_calculation_accuracy(self):
        """Test AMZN position calculation accuracy from original analysis."""
        # Based on conversation summary AMZN example
        pnl, return_pct = self.calculator.calculate_pnl_and_return(
            entry_price=193.31,
            exit_price=201.64,
            position_size=1.0,
            direction="Long",
        )

        expected_pnl = 8.33  # 201.64 - 193.31
        expected_return = 0.0431  # 8.33 / 193.31

        self.assertEqual(pnl, expected_pnl)
        self.assertEqual(return_pct, expected_return)

    def test_precision_consistency_across_operations(self):
        """Test that precision remains consistent across all operations."""
        test_data = {
            "Avg_Entry_Price": 100.333333,
            "Avg_Exit_Price": 105.777777,
            "Position_Size": 1.5,
            "Direction": "Long",
            "PnL": 0.0,  # Will be corrected
            "Return": 0.0,  # Will be corrected
            "Max_Favourable_Excursion": 0.066666666,
            "Max_Adverse_Excursion": 0.022222222,
        }

        result = self.calculator.comprehensive_position_refresh(test_data)
        refreshed = result["data"]

        # Verify all values have correct precision
        self.assertEqual(
            len(str(refreshed["PnL"]).split(".")[-1]),
            2,
        )  # 2 decimal places
        self.assertEqual(
            len(str(refreshed["Return"]).split(".")[-1]),
            4,
        )  # 4 decimal places
        self.assertEqual(
            len(str(refreshed["Max_Favourable_Excursion"]).split(".")[-1]),
            6,
        )  # 6 decimal places


@pytest.mark.unit
class TestPositionCalculatorPropertyBased(unittest.TestCase):
    """Property-based tests using Hypothesis to validate calculation consistency."""

    def setUp(self):
        """Set up property-based test fixtures."""
        self.calculator = PositionCalculator()

    @given(
        entry_price=st.floats(
            min_value=0.01,
            max_value=10000.0,
            allow_nan=False,
            allow_infinity=False,
        ),
        exit_price=st.floats(
            min_value=0.01,
            max_value=10000.0,
            allow_nan=False,
            allow_infinity=False,
        ),
        position_size=st.floats(
            min_value=0.1,
            max_value=1000.0,
            allow_nan=False,
            allow_infinity=False,
        ),
    )
    def test_pnl_calculation_properties_long(
        self,
        entry_price,
        exit_price,
        position_size,
    ):
        """Property-based test for Long position P&L calculations."""
        pnl, return_pct = self.calculator.calculate_pnl_and_return(
            entry_price,
            exit_price,
            position_size,
            "Long",
        )

        # Property: P&L should match manual calculation
        expected_pnl = round(
            (exit_price - entry_price) * position_size,
            STANDARD_PNL_PRECISION,
        )
        self.assertEqual(pnl, expected_pnl)

        # Property: Return should match manual calculation
        expected_return = round(
            (exit_price - entry_price) / entry_price,
            STANDARD_RETURN_PRECISION,
        )
        self.assertEqual(return_pct, expected_return)

        # Property: P&L and return should have consistent signs
        if exit_price > entry_price:
            self.assertGreaterEqual(pnl, 0)
            self.assertGreaterEqual(return_pct, 0)
        elif exit_price < entry_price:
            self.assertLessEqual(pnl, 0)
            self.assertLessEqual(return_pct, 0)

    @given(
        entry_price=st.floats(
            min_value=0.01,
            max_value=10000.0,
            allow_nan=False,
            allow_infinity=False,
        ),
        exit_price=st.floats(
            min_value=0.01,
            max_value=10000.0,
            allow_nan=False,
            allow_infinity=False,
        ),
        position_size=st.floats(
            min_value=0.1,
            max_value=1000.0,
            allow_nan=False,
            allow_infinity=False,
        ),
    )
    def test_pnl_calculation_properties_short(
        self,
        entry_price,
        exit_price,
        position_size,
    ):
        """Property-based test for Short position P&L calculations."""
        pnl, return_pct = self.calculator.calculate_pnl_and_return(
            entry_price,
            exit_price,
            position_size,
            "Short",
        )

        # Property: P&L should match manual calculation
        expected_pnl = round(
            (entry_price - exit_price) * position_size,
            STANDARD_PNL_PRECISION,
        )
        self.assertEqual(pnl, expected_pnl)

        # Property: Return should match manual calculation
        expected_return = round(
            (entry_price - exit_price) / entry_price,
            STANDARD_RETURN_PRECISION,
        )
        self.assertEqual(return_pct, expected_return)

        # Property: P&L and return should have consistent signs
        if exit_price < entry_price:  # Profitable short
            self.assertGreaterEqual(pnl, 0)
            self.assertGreaterEqual(return_pct, 0)
        elif exit_price > entry_price:  # Losing short
            self.assertLessEqual(pnl, 0)
            self.assertLessEqual(return_pct, 0)

    @given(
        mfe=st.floats(
            min_value=0.001,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False,
        ),
        mae=st.floats(
            min_value=0.001,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False,
        ),
    )
    def test_mfe_mae_ratio_properties(self, mfe, mae):
        """Property-based test for MFE/MAE ratio calculations."""
        ratio = self.calculator.calculate_mfe_mae_ratio(mfe, mae)

        # Property: Ratio should be positive
        self.assertGreater(ratio, 0)

        # Property: Ratio should match manual calculation
        expected_ratio = round(mfe / mae, STANDARD_RATIO_PRECISION)
        self.assertEqual(ratio, expected_ratio)

        # Property: Higher MFE should give higher ratio (for same MAE)
        higher_mfe_ratio = self.calculator.calculate_mfe_mae_ratio(mfe * 2, mae)
        self.assertGreater(higher_mfe_ratio, ratio)

    @given(
        final_return=st.floats(
            min_value=-1.0,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False,
        ),
        mfe=st.floats(
            min_value=0.001,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False,
        ),
    )
    def test_exit_efficiency_properties(self, final_return, mfe):
        """Property-based test for exit efficiency calculations."""
        efficiency = self.calculator.calculate_exit_efficiency(final_return, mfe)

        # Property: Efficiency should not be None for positive MFE
        self.assertIsNotNone(efficiency)

        # Property: Efficiency should match manual calculation
        expected_efficiency = round(final_return / mfe, STANDARD_EFFICIENCY_PRECISION)
        self.assertEqual(efficiency, expected_efficiency)

        # Property: Better final return should give higher efficiency (for same MFE)
        if final_return < 0.5:  # Leave room for improvement
            better_efficiency = self.calculator.calculate_exit_efficiency(
                final_return + 0.1,
                mfe,
            )
            self.assertGreater(better_efficiency, efficiency)


@pytest.mark.unit
class TestPositionCalculatorPerformance(unittest.TestCase):
    """Performance tests for PositionCalculator operations."""

    def setUp(self):
        """Set up performance test fixtures."""
        self.calculator = PositionCalculator()

    def test_calculation_performance(self):
        """Test that calculations perform within reasonable time limits."""
        import time

        # Test large batch of calculations
        start_time = time.time()

        for i in range(1000):
            self.calculator.calculate_pnl_and_return(
                entry_price=100.0 + i * 0.1,
                exit_price=110.0 + i * 0.1,
                position_size=1.0,
                direction="Long",
            )

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete 1000 calculations in under 1 second
        self.assertLess(execution_time, 1.0)

    def test_comprehensive_refresh_performance(self):
        """Test performance of comprehensive position refresh."""
        import time

        test_data = {
            "Avg_Entry_Price": 434.53,
            "Avg_Exit_Price": 447.70,
            "Position_Size": 1.0,
            "Direction": "Long",
            "PnL": 376.53,
            "Return": 8.6618,
            "Max_Favourable_Excursion": 0.434553,
            "Max_Adverse_Excursion": 0.062141,
            "Entry_Timestamp": "2025-06-23",
        }

        start_time = time.time()

        for _i in range(100):
            self.calculator.comprehensive_position_refresh(test_data)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete 100 comprehensive refreshes in under 1 second
        self.assertLess(execution_time, 1.0)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
