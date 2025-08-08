"""
Integration tests for unified position workflows.

Tests the complete position lifecycle through the new PositionService
architecture, ensuring that the consolidation maintains all functionality
while providing improved consistency and error handling.
"""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from app.exceptions import (
    DataNotFoundError,
    PortfolioError,
    PriceDataError,
    SignalValidationError,
    ValidationError,
)
from app.services import PositionService
from app.services.position_service import TradingSystemConfig


class TestPositionWorkflowsIntegration(unittest.TestCase):
    """Integration tests for complete position workflows."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TradingSystemConfig(self.temp_dir)
        self.service = PositionService(self.config)
        
        # Create test directories
        self.config.ensure_directories()
        
        # Create sample price data
        self._create_sample_price_data()
        
        # Create sample portfolio
        self._create_sample_portfolio()

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_sample_price_data(self):
        """Create sample price data for testing."""
        # Sample AAPL price data
        dates = pd.date_range("2025-01-01", "2025-02-28", freq="D")
        price_data = pd.DataFrame({
            "Date": dates,
            "Open": [150.0 + i * 0.1 for i in range(len(dates))],
            "High": [152.0 + i * 0.1 for i in range(len(dates))],
            "Low": [148.0 + i * 0.1 for i in range(len(dates))],
            "Close": [151.0 + i * 0.1 for i in range(len(dates))],
            "Volume": [1000000] * len(dates),
        })
        
        price_file = self.config.get_prices_file("AAPL", "D")
        price_data.to_csv(price_file, index=False)
        
        # Sample TSLA price data with higher volatility
        tsla_data = pd.DataFrame({
            "Date": dates,
            "Open": [200.0 + i * 0.5 for i in range(len(dates))],
            "High": [205.0 + i * 0.5 for i in range(len(dates))],
            "Low": [195.0 + i * 0.5 for i in range(len(dates))],
            "Close": [202.0 + i * 0.5 for i in range(len(dates))],
            "Volume": [2000000] * len(dates),
        })
        
        tsla_file = self.config.get_prices_file("TSLA", "D")
        tsla_data.to_csv(tsla_file, index=False)

    def _create_sample_portfolio(self):
        """Create sample portfolio for testing."""
        portfolio_data = pd.DataFrame({
            "Position_UUID": ["TEST_SMA_20_50_20250101"],
            "Ticker": ["TEST"],
            "Strategy_Type": ["SMA"],
            "Short_Window": [20],
            "Long_Window": [50],
            "Signal_Window": [0],
            "Entry_Timestamp": ["2025-01-01"],
            "Exit_Timestamp": [None],
            "Avg_Entry_Price": [100.0],
            "Avg_Exit_Price": [None],
            "Position_Size": [1.0],
            "Direction": ["Long"],
            "Status": ["Open"],
            "PnL": [0.0],
            "Return": [0.0],
        })
        
        portfolio_file = self.config.get_portfolio_file("test_portfolio")
        portfolio_data.to_csv(portfolio_file, index=False)

    def test_complete_position_lifecycle(self):
        """Test complete position lifecycle from creation to closure."""
        # Step 1: Create new position
        position_uuid = self.service.add_position_to_portfolio(
            ticker="AAPL",
            strategy_type="SMA",
            short_window=20,
            long_window=50,
            entry_date="2025-01-15",
            entry_price=155.0,
            position_size=100.0,
            direction="Long",
            portfolio_name="test_workflow",
            verify_signal=False,  # Skip signal verification for test
        )
        
        # Verify position was created
        self.assertIsNotNone(position_uuid)
        self.assertIn("AAPL", position_uuid)
        self.assertIn("SMA", position_uuid)
        self.assertIn("20250115", position_uuid)
        
        # Step 2: Verify position exists in portfolio
        positions = self.service.list_positions("test_workflow")
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]["Position_UUID"], position_uuid)
        self.assertEqual(positions[0]["Status"], "Open")
        
        # Step 3: Get specific position
        position = self.service.get_position(position_uuid, "test_workflow")
        self.assertEqual(position["Ticker"], "AAPL")
        self.assertEqual(position["Strategy_Type"], "SMA")
        self.assertEqual(position["Avg_Entry_Price"], 155.0)
        self.assertEqual(position["Position_Size"], 100.0)
        
        # Step 4: Close position
        result = self.service.close_position(
            position_uuid=position_uuid,
            portfolio_name="test_workflow",
            exit_price=165.0,
            exit_date="2025-02-15",
        )
        
        # Verify closing result
        self.assertTrue(result["success"])
        self.assertEqual(result["exit_price"], 165.0)
        self.assertEqual(result["pnl"], 1000.0)  # (165-155) * 100
        self.assertEqual(result["return"], 0.0645)  # 10/155 ≈ 0.0645
        
        # Step 5: Verify position is now closed
        closed_position = self.service.get_position(position_uuid, "test_workflow")
        self.assertEqual(closed_position["Status"], "Closed")
        self.assertEqual(closed_position["Avg_Exit_Price"], 165.0)
        self.assertEqual(closed_position["PnL"], 1000.0)

    def test_position_validation_errors(self):
        """Test that position validation errors are properly raised."""
        # Test invalid ticker
        with self.assertRaises(ValidationError):
            self.service.add_position_to_portfolio(
                ticker="",  # Invalid empty ticker
                strategy_type="SMA",
                short_window=20,
                long_window=50,
                entry_date="2025-01-15",
                entry_price=155.0,
                portfolio_name="test_validation",
                verify_signal=False,
            )
        
        # Test invalid strategy type
        with self.assertRaises(ValidationError):
            self.service.add_position_to_portfolio(
                ticker="AAPL",
                strategy_type="INVALID",  # Invalid strategy
                short_window=20,
                long_window=50,
                entry_date="2025-01-15",
                entry_price=155.0,
                portfolio_name="test_validation",
                verify_signal=False,
            )
        
        # Test invalid date format
        with self.assertRaises(ValidationError):
            self.service.add_position_to_portfolio(
                ticker="AAPL",
                strategy_type="SMA",
                short_window=20,
                long_window=50,
                entry_date="invalid-date",  # Invalid date
                entry_price=155.0,
                portfolio_name="test_validation",
                verify_signal=False,
            )

    def test_duplicate_position_prevention(self):
        """Test that duplicate positions are prevented."""
        # Add first position
        position_uuid = self.service.add_position_to_portfolio(
            ticker="AAPL",
            strategy_type="SMA",
            short_window=20,
            long_window=50,
            entry_date="2025-01-15",
            entry_price=155.0,
            portfolio_name="test_duplicates",
            verify_signal=False,
        )
        
        # Try to add the same position again
        with self.assertRaises(PortfolioError):
            self.service.add_position_to_portfolio(
                ticker="AAPL",
                strategy_type="SMA",
                short_window=20,
                long_window=50,
                entry_date="2025-01-15",  # Same date = same UUID
                entry_price=155.0,
                portfolio_name="test_duplicates",
                verify_signal=False,
            )

    def test_portfolio_operations(self):
        """Test portfolio-level operations."""
        # Add multiple positions
        positions = [
            ("AAPL", "SMA", 20, 50, "2025-01-15", 155.0),
            ("TSLA", "EMA", 12, 26, "2025-01-20", 210.0),
            ("AAPL", "SMA", 10, 30, "2025-01-25", 160.0),
        ]
        
        for ticker, strategy, short, long, date, price in positions:
            self.service.add_position_to_portfolio(
                ticker=ticker,
                strategy_type=strategy,
                short_window=short,
                long_window=long,
                entry_date=date,
                entry_price=price,
                portfolio_name="test_portfolio_ops",
                verify_signal=False,
            )
        
        # Test list all positions
        all_positions = self.service.list_positions("test_portfolio_ops")
        self.assertEqual(len(all_positions), 3)
        
        # Test filter by status (all should be Open)
        open_positions = self.service.list_positions("test_portfolio_ops", "Open")
        self.assertEqual(len(open_positions), 3)
        
        closed_positions = self.service.list_positions("test_portfolio_ops", "Closed")
        self.assertEqual(len(closed_positions), 0)
        
        # Close one position
        position_uuid = all_positions[0]["Position_UUID"]
        self.service.close_position(
            position_uuid=position_uuid,
            portfolio_name="test_portfolio_ops",
            exit_price=170.0,
        )
        
        # Verify status filtering works after closing
        open_positions = self.service.list_positions("test_portfolio_ops", "Open")
        self.assertEqual(len(open_positions), 2)
        
        closed_positions = self.service.list_positions("test_portfolio_ops", "Closed")
        self.assertEqual(len(closed_positions), 1)

    def test_mfe_mae_calculation_integration(self):
        """Test MFE/MAE calculation integration."""
        # Add position with actual price data
        position_uuid = self.service.add_position_to_portfolio(
            ticker="AAPL",
            strategy_type="SMA",
            short_window=20,
            long_window=50,
            entry_date="2025-01-15",
            entry_price=155.0,
            portfolio_name="test_mfe_mae",
            verify_signal=False,
        )
        
        # Get position and verify MFE/MAE were calculated
        position = self.service.get_position(position_uuid, "test_mfe_mae")
        
        # Should have MFE/MAE values based on our sample price data
        self.assertIsNotNone(position.get("Max_Favourable_Excursion"))
        self.assertIsNotNone(position.get("Max_Adverse_Excursion"))
        self.assertIsNotNone(position.get("Trade_Quality"))
        
        # MFE should be positive for our ascending price data
        mfe = position["Max_Favourable_Excursion"]
        mae = position["Max_Adverse_Excursion"]
        
        if mfe is not None and mae is not None:
            self.assertGreater(mfe, 0)
            self.assertGreater(mae, 0)
            
            # Close position and verify exit efficiency calculation
            result = self.service.close_position(
                position_uuid=position_uuid,
                portfolio_name="test_mfe_mae",
                exit_price=165.0,
            )
            
            # Get updated position
            closed_position = self.service.get_position(position_uuid, "test_mfe_mae")
            
            # Should have exit efficiency calculated
            self.assertIsNotNone(closed_position.get("Exit_Efficiency_Fixed"))

    @patch('app.services.position_service.get_mfe_mae_calculator')
    def test_mfe_mae_calculation_failure_handling(self, mock_calculator):
        """Test handling of MFE/MAE calculation failures."""
        # Mock calculator to raise exception
        mock_calc_instance = Mock()
        mock_calc_instance.calculate_from_ohlc.side_effect = Exception("Price data error")
        mock_calculator.return_value = mock_calc_instance
        
        # Position should still be created even if MFE/MAE calculation fails
        position_uuid = self.service.add_position_to_portfolio(
            ticker="AAPL",
            strategy_type="SMA",
            short_window=20,
            long_window=50,
            entry_date="2025-01-15",
            entry_price=155.0,
            portfolio_name="test_failure_handling",
            verify_signal=False,
        )
        
        # Position should exist with basic data
        position = self.service.get_position(position_uuid, "test_failure_handling")
        self.assertEqual(position["Ticker"], "AAPL")
        self.assertEqual(position["Status"], "Open")
        
        # MFE/MAE fields should be None due to calculation failure
        self.assertIsNone(position.get("Max_Favourable_Excursion"))
        self.assertIsNone(position.get("Max_Adverse_Excursion"))

    def test_nonexistent_portfolio_error(self):
        """Test handling of nonexistent portfolio operations."""
        # Test listing positions from nonexistent portfolio
        with self.assertRaises(PortfolioError):
            self.service.list_positions("nonexistent_portfolio")
        
        # Test getting position from nonexistent portfolio
        with self.assertRaises(PortfolioError):
            self.service.get_position("some_uuid", "nonexistent_portfolio")
        
        # Test closing position in nonexistent portfolio
        with self.assertRaises(PortfolioError):
            self.service.close_position("some_uuid", "nonexistent_portfolio", 100.0)

    def test_nonexistent_position_error(self):
        """Test handling of nonexistent position operations."""
        # Create empty portfolio
        portfolio_file = self.config.get_portfolio_file("empty_portfolio")
        pd.DataFrame().to_csv(portfolio_file, index=False)
        
        # Test getting nonexistent position
        with self.assertRaises(DataNotFoundError):
            self.service.get_position("nonexistent_uuid", "empty_portfolio")
        
        # Test closing nonexistent position
        with self.assertRaises(DataNotFoundError):
            self.service.close_position("nonexistent_uuid", "empty_portfolio", 100.0)

    def test_signal_verification_workflow(self):
        """Test signal verification in position creation workflow."""
        # This test would require complex price data setup for crossover signals
        # For now, test that signal verification errors are properly handled
        
        with self.assertRaises((SignalValidationError, DataNotFoundError, PriceDataError)):
            self.service.add_position_to_portfolio(
                ticker="AAPL",
                strategy_type="SMA",
                short_window=20,
                long_window=50,
                entry_date="2025-01-15",
                entry_price=155.0,
                portfolio_name="test_signal_verification",
                verify_signal=True,  # Enable signal verification
            )

    def test_configuration_integration(self):
        """Test that configuration is properly integrated throughout workflow."""
        # Test that custom configuration is used
        custom_dir = tempfile.mkdtemp()
        custom_config = TradingSystemConfig(custom_dir)
        custom_service = PositionService(custom_config)
        
        # Ensure directories are created in custom location
        custom_config.ensure_directories()
        self.assertTrue(custom_config.positions_dir.exists())
        self.assertTrue(custom_config.prices_dir.exists())
        
        # Test that service uses custom configuration
        self.assertEqual(str(custom_service.config.base_dir), custom_dir)
        
        # Clean up
        import shutil
        shutil.rmtree(custom_dir, ignore_errors=True)


class TestPositionWorkflowsErrorRecovery(unittest.TestCase):
    """Test error recovery and edge cases in position workflows."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TradingSystemConfig(self.temp_dir)
        self.service = PositionService(self.config)
        self.config.ensure_directories()

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_corrupted_portfolio_recovery(self):
        """Test recovery from corrupted portfolio files."""
        # Create corrupted portfolio file
        portfolio_file = self.config.get_portfolio_file("corrupted")
        with open(portfolio_file, 'w') as f:
            f.write("corrupted,data,here\ninvalid,csv,format")
        
        # Service should handle corrupted file gracefully
        with self.assertRaises((PortfolioError, pd.errors.ParserError)):
            self.service.list_positions("corrupted")

    def test_missing_price_data_handling(self):
        """Test handling of missing price data."""
        # Try to add position for ticker without price data
        with self.assertRaises(PriceDataError):
            position_uuid = self.service.add_position_to_portfolio(
                ticker="MISSING",
                strategy_type="SMA",
                short_window=20,
                long_window=50,
                entry_date="2025-01-15",
                entry_price=155.0,
                portfolio_name="test_missing_price",
                verify_signal=False,
            )

    def test_edge_case_calculations(self):
        """Test edge cases in position calculations."""
        # Test zero position size
        with self.assertRaises(ValidationError):
            self.service.create_position_record(
                ticker="AAPL",
                strategy_type="SMA",
                short_window=20,
                long_window=50,
                entry_date="2025-01-15",
                entry_price=155.0,
                position_size=0.0,  # Invalid zero size
            )
        
        # Test negative prices
        with self.assertRaises(ValidationError):
            self.service.create_position_record(
                ticker="AAPL",
                strategy_type="SMA",
                short_window=20,
                long_window=50,
                entry_date="2025-01-15",
                entry_price=-155.0,  # Invalid negative price
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)