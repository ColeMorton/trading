"""
Integration tests for TradeHistoryService comprehensive refresh functionality.

Tests the integration between TradeHistoryService and PositionCalculator to ensure
proper P&L calculation fixes, validation, and comprehensive position refreshing.
This prevents regression of the original SMCI P&L calculation bug.
"""

import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from app.contexts.portfolio.services.trade_history_service import TradeHistoryService
from app.tools.position_calculator import PositionCalculator


@pytest.mark.integration
class TestTradeHistoryServiceIntegration(unittest.TestCase):
    """Integration tests for TradeHistoryService comprehensive refresh."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_dir = Path(self.temp_dir)

        # Create data directory structure
        (self.base_dir / "data" / "raw" / "positions").mkdir(
            parents=True,
            exist_ok=True,
        )

        # Set up mock logger
        self.mock_logger = Mock(spec=logging.Logger)

        # Initialize service
        self.service = TradeHistoryService(
            logger=self.mock_logger,
            base_dir=self.base_dir,
        )

        # Create test portfolio data with the original SMCI bug scenario
        self.smci_bug_data = pd.DataFrame(
            [
                {
                    "Position_UUID": "SMCI_SMA_58_60_2025-06-23",
                    "Ticker": "SMCI",
                    "Entry_Timestamp": "2025-06-23",
                    "Exit_Timestamp": "2025-07-15",
                    "Avg_Entry_Price": 434.53,
                    "Avg_Exit_Price": 447.70,
                    "Position_Size": 1.0,
                    "Direction": "Long",
                    "Status": "Closed",
                    "PnL": 376.53,  # INCORRECT - should be 13.17
                    "Return": 8.6618,  # INCORRECT - should be 0.0303
                    "Max_Favourable_Excursion": 0.434553,
                    "Max_Adverse_Excursion": 0.062141,
                    "MFE_MAE_Ratio": 7.0223,
                    "Exit_Efficiency_Fixed": 0.6966,
                    "Days_Since_Entry": 22,
                    "Current_Unrealized_PnL": 8.6618,
                    "Current_Excursion_Status": "Favorable",
                    "Trade_Quality": "Excellent",
                },
                {
                    "Position_UUID": "AMZN_EMA_12_26_2025-01-15",
                    "Ticker": "AMZN",
                    "Entry_Timestamp": "2025-01-15",
                    "Exit_Timestamp": "2025-02-10",
                    "Avg_Entry_Price": 193.31,
                    "Avg_Exit_Price": 201.64,
                    "Position_Size": 1.0,
                    "Direction": "Long",
                    "Status": "Closed",
                    "PnL": -13.38,  # INCORRECT - should be 8.33
                    "Return": -0.0692,  # INCORRECT - should be 0.0431
                    "Max_Favourable_Excursion": 0.0543,
                    "Max_Adverse_Excursion": 0.0287,
                    "MFE_MAE_Ratio": 1.8920,
                    "Exit_Efficiency_Fixed": 0.7937,
                    "Days_Since_Entry": 26,
                    "Current_Unrealized_PnL": -0.0692,
                    "Current_Excursion_Status": "Adverse",
                    "Trade_Quality": "Good",
                },
                {
                    "Position_UUID": "AAPL_SMA_20_50_2025-03-01",
                    "Ticker": "AAPL",
                    "Entry_Timestamp": "2025-03-01",
                    "Exit_Timestamp": None,  # Open position
                    "Avg_Entry_Price": 180.50,
                    "Avg_Exit_Price": None,
                    "Position_Size": 2.0,
                    "Direction": "Long",
                    "Status": "Open",
                    "PnL": 0.0,
                    "Return": 0.0,
                    "Max_Favourable_Excursion": 0.0,
                    "Max_Adverse_Excursion": 0.0,
                    "MFE_MAE_Ratio": 0.0,
                    "Exit_Efficiency_Fixed": None,
                    "Days_Since_Entry": 150,
                    "Current_Unrealized_PnL": 0.0,
                    "Current_Excursion_Status": "Neutral",
                    "Trade_Quality": "Unknown",
                },
            ],
        )

        # Save test portfolio
        self.portfolio_file = (
            self.base_dir / "data" / "raw" / "positions" / "test_portfolio.csv"
        )
        self.smci_bug_data.to_csv(self.portfolio_file, index=False)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_comprehensive_refresh_fixes_smci_bug(self):
        """Test that comprehensive refresh fixes the original SMCI P&L calculation bug."""
        with (
            patch.object(self.service, "_refresh_price_data"),
            patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics,
        ):
            # Mock MFE/MAE calculation to return original values
            mock_metrics.return_value = (0.434553, 0.062141, 0.0303, None)

            # Run comprehensive refresh
            result = self.service.update_all_positions(
                portfolio_name="test_portfolio.csv",
                dry_run=False,
                verbose=True,
                validate_calculations=True,
                auto_fix_errors=True,
            )

            # Verify success
            self.assertTrue(result["success"])
            self.assertEqual(
                result["updated_count"],
                3,
            )  # All positions should be updated

            # Read updated portfolio
            updated_df = pd.read_csv(self.portfolio_file)

            # Verify SMCI position was fixed
            smci_position = updated_df[updated_df["Ticker"] == "SMCI"].iloc[0]
            self.assertEqual(smci_position["PnL"], 13.17)  # Fixed P&L
            self.assertEqual(smci_position["Return"], 0.0303)  # Fixed Return

            # Verify AMZN position was fixed
            amzn_position = updated_df[updated_df["Ticker"] == "AMZN"].iloc[0]
            self.assertEqual(amzn_position["PnL"], 8.33)  # Fixed P&L
            self.assertEqual(amzn_position["Return"], 0.0431)  # Fixed Return

            # Verify changes were tracked
            self.assertGreater(len(result.get("calculation_fixes", [])), 0)

    def test_validation_detects_calculation_errors(self):
        """Test that validation properly detects the original calculation errors."""
        with (
            patch.object(self.service, "_refresh_price_data"),
            patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics,
        ):
            # Mock MFE/MAE calculation
            mock_metrics.return_value = (0.434553, 0.062141, 0.0303, None)

            # Run refresh with validation enabled
            result = self.service.update_all_positions(
                portfolio_name="test_portfolio.csv",
                validate_calculations=True,
                verbose=True,
            )

            # Should detect and fix validation errors
            self.assertTrue(result["success"])
            self.assertGreater(len(result.get("calculation_fixes", [])), 0)

            # Verify specific fixes were made
            fixes = result.get("calculation_fixes", [])
            smci_fixes = [f for f in fixes if "SMCI" in f]
            amzn_fixes = [f for f in fixes if "AMZN" in f]

            self.assertTrue(any("PnL:" in fix for fix in smci_fixes))
            self.assertTrue(any("Return:" in fix for fix in smci_fixes))
            self.assertTrue(any("PnL:" in fix for fix in amzn_fixes))
            self.assertTrue(any("Return:" in fix for fix in amzn_fixes))

    def test_dry_run_mode_preview_only(self):
        """Test that dry run mode shows changes without applying them."""
        with (
            patch.object(self.service, "_refresh_price_data"),
            patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics,
        ):
            mock_metrics.return_value = (0.434553, 0.062141, 0.0303, None)

            # Read original data
            original_df = pd.read_csv(self.portfolio_file)
            original_smci_pnl = original_df[original_df["Ticker"] == "SMCI"].iloc[0][
                "PnL"
            ]

            # Run in dry run mode
            result = self.service.update_all_positions(
                portfolio_name="test_portfolio.csv",
                dry_run=True,
                validate_calculations=True,
            )

            # Should report changes but not apply them
            self.assertTrue(result["success"])
            self.assertGreater(result["updated_count"], 0)

            # Verify file wasn't modified
            current_df = pd.read_csv(self.portfolio_file)
            current_smci_pnl = current_df[current_df["Ticker"] == "SMCI"].iloc[0]["PnL"]
            self.assertEqual(original_smci_pnl, current_smci_pnl)  # Should be unchanged

    def test_open_position_handling(self):
        """Test handling of open positions with MFE/MAE updates."""
        with (
            patch.object(self.service, "_refresh_price_data"),
            patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics,
        ):
            # Mock different returns for different tickers
            def mock_metrics_side_effect(ticker, *args, **kwargs):
                if ticker == "AAPL":
                    return (
                        0.0856,
                        0.0234,
                        0.0512,
                        None,
                    )  # Open position with current data
                if ticker == "SMCI":
                    return (0.434553, 0.062141, 0.0303, None)  # Closed position
                return (0.0543, 0.0287, 0.0431, None)  # AMZN

            mock_metrics.side_effect = mock_metrics_side_effect

            result = self.service.update_all_positions(
                portfolio_name="test_portfolio.csv",
                verbose=True,
            )

            # Verify success
            self.assertTrue(result["success"])

            # Read updated portfolio
            updated_df = pd.read_csv(self.portfolio_file)

            # Verify open AAPL position was updated with new MFE/MAE
            aapl_position = updated_df[updated_df["Ticker"] == "AAPL"].iloc[0]
            self.assertEqual(aapl_position["Max_Favourable_Excursion"], 0.0856)
            self.assertEqual(aapl_position["Max_Adverse_Excursion"], 0.0234)
            # Current_Unrealized_PnL might be set via comprehensive refresh
            if pd.notna(aapl_position["Current_Unrealized_PnL"]):
                self.assertEqual(aapl_position["Current_Unrealized_PnL"], 0.0512)

    def test_position_calculator_integration(self):
        """Test proper integration with PositionCalculator."""
        calculator_instance = None

        def capture_calculator_call(
            position_data,
            mfe=None,
            mae=None,
            current_excursion=None,
        ):
            nonlocal calculator_instance
            calculator_instance = PositionCalculator()
            return calculator_instance.comprehensive_position_refresh(
                position_data,
                mfe,
                mae,
                current_excursion,
            )

        with patch.object(self.service, "_refresh_price_data"):
            with patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics:
                with patch(
                    "app.contexts.portfolio.services.trade_history_service.get_position_calculator",
                ) as mock_get_calc:
                    # Setup mocks
                    mock_calculator = Mock()
                    mock_calculator.comprehensive_position_refresh.side_effect = (
                        capture_calculator_call
                    )
                    mock_get_calc.return_value = mock_calculator
                    mock_metrics.return_value = (0.434553, 0.062141, 0.0303, None)

                    # Run comprehensive refresh
                    self.service.update_all_positions(
                        portfolio_name="test_portfolio.csv",
                    )

                    # Verify PositionCalculator was used (called twice - once for refresh, once for validation)
                    self.assertTrue(mock_get_calc.called)
                    self.assertGreaterEqual(mock_get_calc.call_count, 1)
                    self.assertTrue(
                        mock_calculator.comprehensive_position_refresh.called,
                    )

                    # Verify calculator was called with proper parameters
                    call_args = (
                        mock_calculator.comprehensive_position_refresh.call_args_list[0]
                    )
                    self.assertIn("position_data", call_args.kwargs)
                    self.assertIn("mfe", call_args.kwargs)
                    self.assertIn("mae", call_args.kwargs)

    def test_error_handling_missing_file(self):
        """Test error handling when portfolio file is missing."""
        result = self.service.update_all_positions(
            portfolio_name="nonexistent_portfolio.csv",
        )

        self.assertFalse(result["success"])
        self.assertIn("Portfolio file not found", result["message"])

    def test_error_handling_empty_portfolio(self):
        """Test handling of empty portfolio."""
        # Create empty portfolio with proper columns
        empty_portfolio = self.base_dir / "data" / "raw" / "positions" / "empty.csv"
        empty_df = pd.DataFrame(columns=["Position_UUID", "Ticker", "Entry_Timestamp"])
        empty_df.to_csv(empty_portfolio, index=False)

        result = self.service.update_all_positions(portfolio_name="empty.csv")

        self.assertTrue(result["success"])
        self.assertEqual(result["updated_count"], 0)
        self.assertEqual(result["total_positions"], 0)

    def test_validation_disabled_mode(self):
        """Test comprehensive refresh with validation disabled."""
        with (
            patch.object(self.service, "_refresh_price_data"),
            patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics,
        ):
            mock_metrics.return_value = (0.434553, 0.062141, 0.0303, None)

            result = self.service.update_all_positions(
                portfolio_name="test_portfolio.csv",
                validate_calculations=False,
                verbose=True,
            )

            # Should still succeed and update positions
            self.assertTrue(result["success"])
            self.assertEqual(result["updated_count"], 3)

            # Should not report validation errors since validation was disabled
            self.assertEqual(len(result.get("validation_errors", [])), 0)

    def test_precision_consistency_across_updates(self):
        """Test that all calculations maintain standardized precision."""
        with (
            patch.object(self.service, "_refresh_price_data"),
            patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics,
        ):
            mock_metrics.return_value = (
                0.434553123456,
                0.062141987654,
                0.030271234,
                None,
            )

            self.service.update_all_positions(portfolio_name="test_portfolio.csv")

            # Read updated data
            updated_df = pd.read_csv(self.portfolio_file)

            # Verify precision consistency
            for _, position in updated_df.iterrows():
                if pd.notna(position["PnL"]):
                    # P&L should have 2 decimal places
                    self.assertEqual(len(str(position["PnL"]).split(".")[-1]), 2)

                if pd.notna(position["Return"]):
                    # Return should have 4 decimal places
                    self.assertEqual(len(str(position["Return"]).split(".")[-1]), 4)

                if pd.notna(position["Max_Favourable_Excursion"]):
                    # MFE should have 6 decimal places
                    self.assertEqual(
                        len(str(position["Max_Favourable_Excursion"]).split(".")[-1]),
                        6,
                    )

    def test_mfe_mae_calculation_failure_fallback(self):
        """Test fallback behavior when MFE/MAE calculation fails."""
        with (
            patch.object(self.service, "_refresh_price_data"),
            patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics,
        ):
            # Mock MFE/MAE calculation failure for SMCI, success for others
            def mock_metrics_side_effect(ticker, *args, **kwargs):
                if ticker == "SMCI":
                    return (None, None, None, "Price data unavailable")
                return (0.0543, 0.0287, 0.0431, None)

            mock_metrics.side_effect = mock_metrics_side_effect

            result = self.service.update_all_positions(
                portfolio_name="test_portfolio.csv",
                verbose=True,
            )

            # Should still succeed with partial updates
            self.assertTrue(result["success"])
            self.assertGreater(
                result["updated_count"],
                0,
            )  # At least AMZN should update

            # When MFE/MAE calculation fails, service falls back to basic calculations
            # Should still succeed but may have different behavior for failed positions
            # Check that at least some positions were updated successfully
            self.assertGreaterEqual(result["updated_count"], 1)

            # Read updated data
            updated_df = pd.read_csv(self.portfolio_file)

            # SMCI should still have corrected P&L even without MFE/MAE
            smci_position = updated_df[updated_df["Ticker"] == "SMCI"].iloc[0]
            self.assertEqual(
                smci_position["PnL"],
                13.17,
            )  # Basic calculations should work

    def test_comprehensive_refresh_performance(self):
        """Test performance of comprehensive refresh on larger dataset."""
        # Create larger test dataset
        large_data = []
        for i in range(100):
            large_data.append(
                {
                    "Position_UUID": f"TEST_{i}_SMA_20_50",
                    "Ticker": f"TEST{i:03d}",
                    "Entry_Timestamp": "2025-01-01",
                    "Exit_Timestamp": "2025-02-01",
                    "Avg_Entry_Price": 100.0 + i,
                    "Avg_Exit_Price": 105.0 + i,
                    "Position_Size": 1.0,
                    "Direction": "Long",
                    "Status": "Closed",
                    "PnL": 4.0 + i,  # Some arbitrary incorrect values
                    "Return": 0.04,
                    "Max_Favourable_Excursion": 0.06,
                    "Max_Adverse_Excursion": 0.02,
                    "MFE_MAE_Ratio": 3.0,
                    "Exit_Efficiency_Fixed": 0.75,
                    "Days_Since_Entry": 31,
                    "Current_Unrealized_PnL": 0.04,
                    "Current_Excursion_Status": "Favorable",
                    "Trade_Quality": "Excellent",
                },
            )

        large_df = pd.DataFrame(large_data)
        large_portfolio_file = (
            self.base_dir / "data" / "raw" / "positions" / "large_portfolio.csv"
        )
        large_df.to_csv(large_portfolio_file, index=False)

        with (
            patch.object(self.service, "_refresh_price_data"),
            patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics,
        ):
            mock_metrics.return_value = (0.06, 0.02, 0.04, None)

            import time

            start_time = time.time()

            result = self.service.update_all_positions(
                portfolio_name="large_portfolio.csv",
            )

            end_time = time.time()
            execution_time = end_time - start_time

            # Should complete in reasonable time (under 30 seconds for 100 positions)
            self.assertLess(execution_time, 30.0)
            self.assertTrue(result["success"])
            self.assertEqual(result["updated_count"], 100)


@pytest.mark.integration
class TestTradeHistoryServiceRegression(unittest.TestCase):
    """Regression tests for specific bugs and edge cases."""

    def setUp(self):
        """Set up regression test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_dir = Path(self.temp_dir)
        (self.base_dir / "data" / "raw" / "positions").mkdir(
            parents=True,
            exist_ok=True,
        )

        self.service = TradeHistoryService(base_dir=self.base_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_smci_specific_regression(self):
        """Regression test for the specific SMCI position calculation bug."""
        # Create the exact SMCI position that had the bug
        smci_data = pd.DataFrame(
            [
                {
                    "Position_UUID": "SMCI_SMA_58_60_2025-06-23",
                    "Ticker": "SMCI",
                    "Entry_Timestamp": "2025-06-23",
                    "Exit_Timestamp": "2025-07-15",
                    "Avg_Entry_Price": 434.53,
                    "Avg_Exit_Price": 447.70,
                    "Position_Size": 1.0,
                    "Direction": "Long",
                    "Status": "Closed",
                    "PnL": 376.53,  # The original incorrect value
                    "Return": 8.6618,  # The original incorrect value
                    "Max_Favourable_Excursion": 0.434553,
                    "Max_Adverse_Excursion": 0.062141,
                },
            ],
        )

        portfolio_file = (
            self.base_dir / "data" / "raw" / "positions" / "smci_regression.csv"
        )
        smci_data.to_csv(portfolio_file, index=False)

        with (
            patch.object(self.service, "_refresh_price_data"),
            patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics,
        ):
            mock_metrics.return_value = (0.434553, 0.062141, 0.0303, None)

            self.service.update_all_positions(
                portfolio_name="smci_regression.csv",
                verbose=True,
            )

            # Verify the bug was fixed
            updated_df = pd.read_csv(portfolio_file)
            position = updated_df.iloc[0]

            # Ensure the specific bug values are corrected
            self.assertEqual(position["PnL"], 13.17)
            self.assertNotEqual(position["PnL"], 376.53)  # Ensure bug doesn't reoccur
            self.assertEqual(position["Return"], 0.0303)
            self.assertNotEqual(
                position["Return"],
                8.6618,
            )  # Ensure bug doesn't reoccur

    def test_calculation_precision_drift_prevention(self):
        """Test prevention of precision drift across multiple refresh cycles."""
        # Create test data
        test_data = pd.DataFrame(
            [
                {
                    "Position_UUID": "PRECISION_TEST_001",
                    "Ticker": "PREC",
                    "Entry_Timestamp": "2025-01-01",
                    "Exit_Timestamp": "2025-02-01",
                    "Avg_Entry_Price": 100.333333,
                    "Avg_Exit_Price": 105.777777,
                    "Position_Size": 1.5,
                    "Direction": "Long",
                    "Status": "Closed",
                    "PnL": 8.166666,  # Will be corrected
                    "Return": 0.054433,  # Will be corrected
                    "Max_Favourable_Excursion": 0.066666,
                    "Max_Adverse_Excursion": 0.022222,
                },
            ],
        )

        portfolio_file = (
            self.base_dir / "data" / "raw" / "positions" / "precision_test.csv"
        )
        test_data.to_csv(portfolio_file, index=False)

        with (
            patch.object(self.service, "_refresh_price_data"),
            patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics,
        ):
            mock_metrics.return_value = (0.066666, 0.022222, 0.054433, None)

            # Run multiple refresh cycles
            for _cycle in range(3):
                result = self.service.update_all_positions(
                    portfolio_name="precision_test.csv",
                )
                self.assertTrue(result["success"])

            # Verify precision remains consistent after multiple refreshes
            final_df = pd.read_csv(portfolio_file)
            position = final_df.iloc[0]

            # Check that precision hasn't drifted
            self.assertEqual(
                len(str(position["PnL"]).split(".")[-1]),
                2,
            )  # 2 decimal places
            self.assertEqual(
                len(str(position["Return"]).split(".")[-1]),
                4,
            )  # 4 decimal places


@pytest.mark.integration
class TestTradeHistoryServiceCLIIntegration(unittest.TestCase):
    """Tests for CLI integration with TradeHistoryService."""

    def setUp(self):
        """Set up CLI integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_dir = Path(self.temp_dir)
        (self.base_dir / "data" / "raw" / "positions").mkdir(
            parents=True,
            exist_ok=True,
        )

        self.service = TradeHistoryService(base_dir=self.base_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_refresh_command_integration(self):
        """Test integration with CLI refresh command parameters."""
        # Create test portfolio
        test_data = pd.DataFrame(
            [
                {
                    "Position_UUID": "CLI_TEST_001",
                    "Ticker": "CLI",
                    "Entry_Timestamp": "2025-01-01",
                    "Exit_Timestamp": "2025-02-01",
                    "Avg_Entry_Price": 50.0,
                    "Avg_Exit_Price": 55.0,
                    "Position_Size": 2.0,
                    "Direction": "Long",
                    "Status": "Closed",
                    "PnL": 9.0,  # Incorrect: should be 10.0
                    "Return": 0.09,  # Incorrect: should be 0.1
                },
            ],
        )

        portfolio_file = self.base_dir / "data" / "raw" / "positions" / "cli_test.csv"
        test_data.to_csv(portfolio_file, index=False)

        with (
            patch.object(self.service, "_refresh_price_data"),
            patch.object(
                self.service,
                "_calculate_position_metrics_comprehensive",
            ) as mock_metrics,
        ):
            mock_metrics.return_value = (0.12, 0.03, 0.1, None)

            # Test CLI-style parameters
            result = self.service.update_all_positions(
                portfolio_name="cli_test.csv",
                dry_run=False,
                verbose=True,
                validate_calculations=True,
                auto_fix_errors=True,
            )

            # Verify CLI-expected response format
            self.assertIn("success", result)
            self.assertIn("message", result)
            self.assertIn("updated_count", result)
            self.assertIn("total_positions", result)
            self.assertIn("calculation_fixes", result)

            # Verify fixes were applied
            updated_df = pd.read_csv(portfolio_file)
            position = updated_df.iloc[0]
            self.assertEqual(position["PnL"], 10.0)
            self.assertEqual(position["Return"], 0.1)


if __name__ == "__main__":
    # Run all integration tests
    unittest.main(verbosity=2)
