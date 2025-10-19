"""
Comprehensive unit tests for Signal Unconfirmed functionality.

Tests the calculate_signal_unconfirmed function with various market scenarios
to ensure correct signal prediction based on moving average positions.
"""

import polars as pl

from app.tools.strategy.signal_utils import calculate_signal_unconfirmed


class TestCalculateSignalUnconfirmed:
    """Test calculate_signal_unconfirmed function across different scenarios."""

    def test_entry_signal_scenario(self):
        """Test Entry signal when fast MA > slow MA with no current position."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "MA_FAST": [100.0, 105.0, 110.0],  # Fast MA trending up
                "MA_SLOW": [98.0, 102.0, 108.0],  # Slow MA, fast > slow
                "Signal": [0, 1, 1],  # Current signal is buy
                "Position": [0, 0, 0],  # No current position for Entry signal
            }
        )

        # When fast > slow and no current position, expect Entry
        result = calculate_signal_unconfirmed(signal_data)
        assert result == "Entry"

    def test_exit_signal_scenario(self):
        """Test Exit signal when fast MA < slow MA with current position."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "MA_FAST": [110.0, 105.0, 100.0],  # Fast MA trending down
                "MA_SLOW": [108.0, 107.0, 102.0],  # Slow MA, fast < slow at end
                "Signal": [1, 1, 0],  # Signal changing to sell
                "Position": [1, 1, 1],  # Currently in position
            }
        )

        # When fast < slow and has current position, expect Exit
        result = calculate_signal_unconfirmed(signal_data)
        assert result == "Exit"

    def test_no_signal_fast_greater_with_position(self):
        """Test None when fast > slow but already in position."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "MA_FAST": [105.0, 110.0, 115.0],  # Fast MA trending up
                "MA_SLOW": [100.0, 105.0, 110.0],  # Slow MA, fast > slow
                "Signal": [1, 1, 1],  # Buy signal
                "Position": [1, 1, 1],  # Already in position
            }
        )

        # Already in position and fast > slow, no new signal
        result = calculate_signal_unconfirmed(signal_data)
        assert result == "None"

    def test_no_signal_fast_less_no_position(self):
        """Test None when fast < slow but no current position."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "MA_FAST": [95.0, 90.0, 85.0],  # Fast MA trending down
                "MA_SLOW": [100.0, 95.0, 90.0],  # Slow MA, fast < slow
                "Signal": [0, 0, 0],  # No buy signal
                "Position": [0, 0, 0],  # No position
            }
        )

        # No position and fast < slow, no signal
        result = calculate_signal_unconfirmed(signal_data)
        assert result == "None"

    def test_equal_moving_averages(self):
        """Test None when fast MA equals slow MA."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "MA_FAST": [100.0, 100.0, 100.0],  # Fast MA
                "MA_SLOW": [100.0, 100.0, 100.0],  # Slow MA, equal
                "Signal": [0, 0, 0],
                "Position": [0, 0, 0],
            }
        )

        # When MAs are equal, no clear signal
        result = calculate_signal_unconfirmed(signal_data)
        assert result == "None"

    def test_empty_dataframe(self):
        """Test None for empty DataFrame."""
        signal_data = pl.DataFrame(
            {
                "timestamp": [],
                "MA_FAST": [],
                "MA_SLOW": [],
                "Signal": [],
                "Position": [],
            }
        )

        result = calculate_signal_unconfirmed(signal_data)
        assert result == "None"

    def test_single_row_dataframe(self):
        """Test with single row DataFrame."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01"],
                "MA_FAST": [105.0],
                "MA_SLOW": [100.0],
                "Signal": [0],
                "Position": [0],
            }
        )

        # Single row with fast > slow and no position
        result = calculate_signal_unconfirmed(signal_data)
        assert result == "Entry"

    def test_missing_columns(self):
        """Test None when required columns are missing."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02"],
                "MA_FAST": [105.0, 110.0],
                # Missing long_mavg, signal, position columns
            }
        )

        result = calculate_signal_unconfirmed(signal_data)
        assert result == "None"

    def test_nan_values(self):
        """Test None when data contains NaN values."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "MA_FAST": [float("nan"), 105.0, 110.0],
                "MA_SLOW": [100.0, float("nan"), 108.0],
                "Signal": [0, 1, 1],
                "Position": [0, 1, 1],
            }
        )

        # With NaN values, should return None for safety
        result = calculate_signal_unconfirmed(signal_data)
        assert result == "None"

    def test_all_nan_values(self):
        """Test None when all values are NaN."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01"],
                "MA_FAST": [float("nan")],
                "MA_SLOW": [float("nan")],
                "Signal": [0],
                "Position": [0],
            }
        )

        result = calculate_signal_unconfirmed(signal_data)
        assert result == "None"

    def test_with_config_parameter(self):
        """Test function works with optional config parameter."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "MA_FAST": [100.0, 105.0, 110.0],
                "MA_SLOW": [98.0, 102.0, 108.0],
                "Signal": [0, 1, 1],
                "Position": [0, 0, 0],  # No position for Entry signal
            }
        )

        config = {"STRATEGY_TYPE": "SMA", "DIRECTION": "Long"}
        result = calculate_signal_unconfirmed(signal_data, config)
        assert result == "Entry"

    def test_none_config_parameter(self):
        """Test function works with None config parameter."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "MA_FAST": [110.0, 105.0, 100.0],
                "MA_SLOW": [108.0, 107.0, 102.0],
                "Signal": [1, 1, 0],
                "Position": [1, 1, 1],  # In position for Exit signal
            }
        )

        result = calculate_signal_unconfirmed(signal_data, None)
        assert result == "Exit"

    def test_crossover_scenarios(self):
        """Test various crossover scenarios."""
        # Fast MA crossing above slow MA (bullish crossover)
        bullish_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "MA_FAST": [99.0, 100.5, 102.0],  # Crossing above
                "MA_SLOW": [100.0, 100.0, 100.0],  # Flat slow MA
                "Signal": [0, 0, 1],
                "Position": [0, 0, 0],  # No position for Entry signal
            }
        )

        result = calculate_signal_unconfirmed(bullish_data)
        assert result == "Entry"

        # Fast MA crossing below slow MA (bearish crossover)
        bearish_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "MA_FAST": [101.0, 100.5, 98.0],  # Crossing below
                "MA_SLOW": [100.0, 100.0, 100.0],  # Flat slow MA
                "Signal": [1, 1, 0],
                "Position": [1, 1, 1],  # In position for Exit signal
            }
        )

        result = calculate_signal_unconfirmed(bearish_data)
        assert result == "Exit"

    def test_alternative_column_names(self):
        """Test with alternative column naming conventions."""
        # Test with 'fast_ma' and 'slow_ma' column names
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01", "2023-01-02"],
                "fast_ma": [105.0, 110.0],
                "slow_ma": [100.0, 105.0],
                "Signal": [0, 1],
                "Position": [0, 1],
            }
        )

        # Should still work if we modify the function to handle alternative names
        # For now, this should return None since it expects specific column names
        result = calculate_signal_unconfirmed(signal_data)
        assert result == "None"

    def test_signal_entry_already_confirmed(self):
        """Test that function returns None when Signal Entry is already true."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01"],
                "MA_FAST": [110.0],
                "MA_SLOW": [100.0],
                "Signal": [1],
                "Position": [0],
                "Signal Entry": [True],  # Already confirmed
                "Signal Exit": [False],
            }
        )

        result = calculate_signal_unconfirmed(signal_data)
        assert result == "None"

    def test_signal_exit_already_confirmed(self):
        """Test that function returns None when Signal Exit is already true."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01"],
                "MA_FAST": [90.0],
                "MA_SLOW": [100.0],
                "Signal": [0],
                "Position": [1],
                "Signal Entry": [False],
                "Signal Exit": [True],  # Already confirmed
            }
        )

        result = calculate_signal_unconfirmed(signal_data)
        assert result == "None"

    def test_both_signals_confirmed(self):
        """Test that function returns None when both signals are confirmed."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01"],
                "MA_FAST": [110.0],
                "MA_SLOW": [100.0],
                "Signal": [1],
                "Position": [1],
                "Signal Entry": [True],
                "Signal Exit": [True],
            }
        )

        result = calculate_signal_unconfirmed(signal_data)
        assert result == "None"

    def test_no_signal_columns_present(self):
        """Test that function works when Signal Entry/Exit columns are not present."""
        signal_data = pl.DataFrame(
            {
                "timestamp": ["2023-01-01"],
                "MA_FAST": [110.0],
                "MA_SLOW": [100.0],
                "Signal": [1],
                "Position": [0],
                # No Signal Entry/Exit columns
            }
        )

        result = calculate_signal_unconfirmed(signal_data)
        assert result == "Entry"  # Should work normally

    def test_return_value_types(self):
        """Test that function only returns valid string values."""
        test_cases = [
            # Entry scenario (no confirmed signals)
            pl.DataFrame(
                {
                    "MA_FAST": [110.0],
                    "MA_SLOW": [100.0],
                    "Signal": [0],
                    "Position": [0],
                    "timestamp": ["2023-01-01"],
                    "Signal Entry": [False],
                    "Signal Exit": [False],
                }
            ),
            # Exit scenario (no confirmed signals)
            pl.DataFrame(
                {
                    "MA_FAST": [90.0],
                    "MA_SLOW": [100.0],
                    "Signal": [1],
                    "Position": [1],
                    "timestamp": ["2023-01-01"],
                    "Signal Entry": [False],
                    "Signal Exit": [False],
                }
            ),
            # None scenario (confirmed signal)
            pl.DataFrame(
                {
                    "MA_FAST": [110.0],
                    "MA_SLOW": [100.0],
                    "Signal": [1],
                    "Position": [1],
                    "timestamp": ["2023-01-01"],
                    "Signal Entry": [True],
                    "Signal Exit": [False],
                }
            ),
        ]

        valid_returns = {"Entry", "Exit", "None"}

        for test_data in test_cases:
            result = calculate_signal_unconfirmed(test_data)
            assert isinstance(
                result, str
            ), f"Result should be string, got {type(result)}"
            assert (
                result in valid_returns
            ), f"Result '{result}' not in valid returns {valid_returns}"
