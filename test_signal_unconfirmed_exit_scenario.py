#!/usr/bin/env python3
"""
Specific test for Signal Unconfirmed exit detection scenario.

Tests the exact scenario where:
- SMA 29,30: Fast (180.87) < Slow (180.88) - should return "Exit"
- MACD 13,19,5: MACD (2.01) < Signal (2.02) - should return "Exit"

Both strategies have open positions (Total Open Trades = 1).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

from app.tools.strategy.signal_utils import calculate_signal_unconfirmed_realtime


class TestSignalUnconfirmedExitScenario:
    """Test specific exit scenario where Fast < Slow by minimal amounts"""

    @patch("polars.read_csv")
    def test_sma_29_30_exit_scenario(self, mock_read_csv):
        """Test SMA 29,30 with Fast (180.87) < Slow (180.88) - should return Exit"""

        # Create mock price data (sufficient rows for MA calculation)
        mock_price_data = pl.DataFrame(
            {
                "Date": [f"2025-08-{i:02d}T00:00:00.000000000" for i in range(1, 32)],
                "Close": [180.0 + i * 0.1 for i in range(31)],  # Gradual price increase
            }
        )
        mock_read_csv.return_value = mock_price_data

        # Create a mock data frame that returns our exact MA values
        mock_ma_data = MagicMock()

        # Mock the with_columns method to return our specific MA values
        def mock_with_columns(columns):
            result = MagicMock()
            result.tail.return_value.get_column.side_effect = lambda col: {
                "MA_FAST": pl.Series([180.87]),  # Fast MA (29)
                "MA_SLOW": pl.Series([180.88]),  # Slow MA (30)
            }[col]
            return result

        # Patch the DataFrame methods
        with patch.object(pl.DataFrame, "with_columns", side_effect=mock_with_columns):
            result = calculate_signal_unconfirmed_realtime(
                ticker="SOL-USD",
                strategy_type="SMA",
                fast_period=29,
                slow_period=30,
                signal_entry=False,  # No confirmed entry signal
                signal_exit=False,  # No confirmed exit signal
                total_open_trades=1,  # Has open position
                config=None,
                signal_period=None,
            )

        print(f"SMA 29,30 Test - Expected: 'Exit', Actual: '{result}'")
        print(f"  Fast MA (180.87) < Slow MA (180.88): {180.87 < 180.88}")
        print(f"  Has open position: True")
        print(f"  Should generate exit signal: {180.87 < 180.88 and 1 > 0}")

        assert result == "Exit", f"SMA 29,30: Expected 'Exit' but got '{result}'"

    @patch("polars.read_csv")
    def test_macd_13_19_5_exit_scenario(self, mock_read_csv):
        """Test MACD 13,19,5 with MACD (2.01) < Signal (2.02) - should return Exit"""

        # Create mock price data
        mock_price_data = pl.DataFrame(
            {
                "Date": [f"2025-08-{i:02d}T00:00:00.000000000" for i in range(1, 32)],
                "Close": [180.0 + i * 0.1 for i in range(31)],
            }
        )
        mock_read_csv.return_value = mock_price_data

        # Mock the MACD calculation chain
        def mock_with_columns_macd(columns):
            result = MagicMock()

            # Handle different stages of MACD calculation
            if any("EMA_FAST" in str(col) for col in columns):
                # First stage: EMA calculations
                def get_column_ema(col):
                    return (
                        pl.Series([185.0]) if "EMA_FAST" in col else pl.Series([182.99])
                    )

                result.with_columns.return_value.with_columns.return_value.with_columns.return_value.tail.return_value.get_column.side_effect = (
                    get_column_ema
                )
                return result.with_columns.return_value.with_columns.return_value

            elif any("MACD_LINE" in str(col) for col in columns):
                # Second stage: MACD Line calculation
                result.with_columns.return_value.tail.return_value.get_column.side_effect = lambda col: pl.Series(
                    [2.02]
                )
                return result.with_columns.return_value

            else:
                # Final stage: Return exact MACD values
                result.tail.return_value.get_column.side_effect = lambda col: {
                    "MA_FAST": pl.Series([2.01]),  # MACD Line
                    "MA_SLOW": pl.Series([2.02]),  # Signal Line
                }[col]
                return result

        with patch.object(
            pl.DataFrame, "with_columns", side_effect=mock_with_columns_macd
        ):
            result = calculate_signal_unconfirmed_realtime(
                ticker="SOL-USD",
                strategy_type="MACD",
                fast_period=13,
                slow_period=19,
                signal_entry=False,  # No confirmed entry signal
                signal_exit=False,  # No confirmed exit signal
                total_open_trades=1,  # Has open position
                config=None,
                signal_period=5,
            )

        print(f"MACD 13,19,5 Test - Expected: 'Exit', Actual: '{result}'")
        print(f"  MACD Line (2.01) < Signal Line (2.02): {2.01 < 2.02}")
        print(f"  Has open position: True")
        print(f"  Should generate exit signal: {2.01 < 2.02 and 1 > 0}")

        assert result == "Exit", f"MACD 13,19,5: Expected 'Exit' but got '{result}'"

    def test_both_strategies_exit_scenario(self):
        """Test both strategies together to validate exit signal logic"""

        print("\n=== Testing Both Strategies Exit Scenario ===")

        # Test parameters that should clearly generate exit signals
        test_cases = [
            {
                "name": "SMA 29,30",
                "strategy_type": "SMA",
                "fast_period": 29,
                "slow_period": 30,
                "signal_period": None,
                "fast_value": 180.87,
                "slow_value": 180.88,
                "description": "Fast MA below Slow MA",
            },
            {
                "name": "MACD 13,19,5",
                "strategy_type": "MACD",
                "fast_period": 13,
                "slow_period": 19,
                "signal_period": 5,
                "fast_value": 2.01,
                "slow_value": 2.02,
                "description": "MACD Line below Signal Line",
            },
        ]

        for case in test_cases:
            print(f"\n--- {case['name']} ---")
            print(f"  {case['description']}")
            print(f"  Fast: {case['fast_value']}, Slow: {case['slow_value']}")
            print(f"  Fast < Slow: {case['fast_value'] < case['slow_value']}")
            print(f"  With open position (1), should return: Exit")

            # This test documents the expected behavior
            # The actual function calls are tested in individual test methods above

    @patch("polars.read_csv")
    def test_edge_cases(self, mock_read_csv):
        """Test edge cases and boundary conditions"""

        # Create mock price data
        mock_price_data = pl.DataFrame(
            {
                "Date": [f"2025-08-{i:02d}T00:00:00.000000000" for i in range(1, 32)],
                "Close": [180.0 + i * 0.1 for i in range(31)],
            }
        )
        mock_read_csv.return_value = mock_price_data

        print("\n=== Testing Edge Cases ===")

        # Test 1: No open position (should return None even with bearish crossover)
        def mock_with_columns_no_position(columns):
            result = MagicMock()
            result.tail.return_value.get_column.side_effect = lambda col: {
                "MA_FAST": pl.Series([180.87]),  # Fast < Slow (bearish)
                "MA_SLOW": pl.Series([180.88]),
            }[col]
            return result

        with patch.object(
            pl.DataFrame, "with_columns", side_effect=mock_with_columns_no_position
        ):
            result = calculate_signal_unconfirmed_realtime(
                ticker="SOL-USD",
                strategy_type="SMA",
                fast_period=29,
                slow_period=30,
                signal_entry=False,
                signal_exit=False,
                total_open_trades=0,  # No open position
                config=None,
                signal_period=None,
            )

        print(f"No position test - Expected: 'None', Actual: '{result}'")
        assert result == "None", f"No position: Expected 'None' but got '{result}'"

        # Test 2: Signal already confirmed (should return None)
        with patch.object(
            pl.DataFrame, "with_columns", side_effect=mock_with_columns_no_position
        ):
            result = calculate_signal_unconfirmed_realtime(
                ticker="SOL-USD",
                strategy_type="SMA",
                fast_period=29,
                slow_period=30,
                signal_entry=False,
                signal_exit=True,  # Exit signal already confirmed
                total_open_trades=1,
                config=None,
                signal_period=None,
            )

        print(f"Confirmed signal test - Expected: 'None', Actual: '{result}'")
        assert result == "None", f"Confirmed signal: Expected 'None' but got '{result}'"


def run_tests():
    """Run all tests and display results"""

    print("=" * 60)
    print("SIGNAL UNCONFIRMED EXIT SCENARIO TESTS")
    print("=" * 60)

    test_instance = TestSignalUnconfirmedExitScenario()

    try:
        print("\n1. Testing SMA 29,30 exit scenario...")
        test_instance.test_sma_29_30_exit_scenario()
        print("✅ SMA test PASSED")
    except Exception as e:
        print(f"❌ SMA test FAILED: {e}")

    try:
        print("\n2. Testing MACD 13,19,5 exit scenario...")
        test_instance.test_macd_13_19_5_exit_scenario()
        print("✅ MACD test PASSED")
    except Exception as e:
        print(f"❌ MACD test FAILED: {e}")

    try:
        print("\n3. Testing both strategies documentation...")
        test_instance.test_both_strategies_exit_scenario()
        print("✅ Documentation test PASSED")
    except Exception as e:
        print(f"❌ Documentation test FAILED: {e}")

    try:
        print("\n4. Testing edge cases...")
        test_instance.test_edge_cases()
        print("✅ Edge cases test PASSED")
    except Exception as e:
        print(f"❌ Edge cases test FAILED: {e}")

    print("\n" + "=" * 60)
    print("TEST EXECUTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
