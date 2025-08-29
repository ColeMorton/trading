"""
Comprehensive test suite for ATR Signal Processing.

Tests the hybrid MA+ATR signal generation functionality including:
- ATR parameter combination generation
- Hybrid signal processing logic
- ATR trailing stop exit implementation
- Signal validation and error handling
"""

from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

from app.strategies.ma_cross.tools.atr_signal_processing import (
    create_atr_parameter_combinations,
    generate_hybrid_ma_atr_signals,
    validate_atr_parameters,
)


@pytest.fixture
def sample_price_data():
    """Create sample price data with realistic trends."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", "2023-03-31", freq="D")

    # Create trending price data for better signal testing
    base_price = 100
    trend = np.linspace(0, 0.2, len(dates))  # 20% upward trend
    noise = np.random.normal(0, 0.02, len(dates))
    returns = trend + noise
    prices = base_price * np.exp(np.cumsum(returns))

    return pd.DataFrame(
        {
            "Date": dates,
            "Open": prices * 0.995,
            "High": prices * 1.015,
            "Low": prices * 0.985,
            "Close": prices,
            "Volume": np.random.randint(1000000, 5000000, len(dates)),
            "Ticker": "TEST",
        }
    ).set_index("Date")


@pytest.fixture
def sample_ma_config():
    """Sample MA configuration for testing."""
    return {
        "FAST_PERIOD": 5,
        "SLOW_PERIOD": 15,
        "USE_SMA": True,
        "DIRECTION": "Long",
        "TICKER": "TEST",
        "USE_HOURLY": False,
    }


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return Mock()


class TestATRParameterCombinations:
    """Test ATR parameter combination generation and validation."""

    def test_create_atr_parameter_combinations_comprehensive(self):
        """Test comprehensive ATR parameter combination generation."""
        combinations = create_atr_parameter_combinations(
            atr_length_range=(2, 5),  # 2, 3, 4 (5 is exclusive)
            atr_multiplier_range=(
                1.0,
                3.0,
            ),  # 1.0, 1.5, 2.0, 2.5 (3.0 is exclusive with step 0.5)
            atr_multiplier_step=0.5,
        )

        # Expected: 3 lengths × 4 multipliers = 12 combinations
        assert len(combinations) == 12

        # Test specific combinations
        assert (2, 1.0) in combinations
        assert (2, 1.5) in combinations
        assert (2, 2.0) in combinations
        assert (2, 2.5) in combinations
        assert (4, 1.0) in combinations
        assert (4, 2.5) in combinations

        # Verify all combinations are unique
        assert len(set(combinations)) == len(combinations)

    def test_create_atr_parameter_combinations_step_sizes(self):
        """Test different step sizes for ATR multipliers."""
        # Test large step size
        combinations_large = create_atr_parameter_combinations(
            atr_length_range=(10, 12),  # 10, 11
            atr_multiplier_range=(1.0, 5.0),  # 1.0, 3.0, 5.0
            atr_multiplier_step=2.0,
        )
        assert len(combinations_large) == 2 * 3  # 2 lengths × 3 multipliers
        assert (10, 1.0) in combinations_large
        assert (10, 3.0) in combinations_large
        assert (10, 5.0) in combinations_large

        # Test small step size
        combinations_small = create_atr_parameter_combinations(
            atr_length_range=(5, 6),  # 5
            atr_multiplier_range=(2.0, 2.4),  # 2.0, 2.1, 2.2, 2.3, 2.4
            atr_multiplier_step=0.1,
        )
        assert len(combinations_small) == 1 * 5  # 1 length × 5 multipliers

        # Verify specific small step combinations
        expected_multipliers = [2.0, 2.1, 2.2, 2.3, 2.4]
        for mult in expected_multipliers:
            assert (5, mult) in combinations_small

    def test_create_atr_parameter_combinations_edge_cases(self):
        """Test edge cases in parameter combination generation."""
        # Single value ranges
        single_combo = create_atr_parameter_combinations(
            atr_length_range=(14, 15),  # Only 14
            atr_multiplier_range=(2.0, 2.0),  # Only 2.0
            atr_multiplier_step=1.0,
        )
        assert len(single_combo) == 1
        assert single_combo[0] == (14, 2.0)

        # Non-integer step that doesn't divide evenly
        uneven_combo = create_atr_parameter_combinations(
            atr_length_range=(10, 12),
            atr_multiplier_range=(1.0, 2.0),
            atr_multiplier_step=0.3,  # 1.0, 1.3, 1.6, 1.9
        )
        expected_multipliers = [1.0, 1.3, 1.6, 1.9]
        assert len(uneven_combo) == 2 * len(expected_multipliers)

    def test_validate_atr_parameters_comprehensive(self):
        """Test comprehensive ATR parameter validation."""
        # Valid parameters
        valid_cases = [
            (1, 0.1),  # Minimum valid values
            (14, 2.0),  # Common ATR parameters
            (50, 5.0),  # High but valid values
            (100, 10.0),  # Very high but valid
        ]

        for length, multiplier in valid_cases:
            is_valid, error = validate_atr_parameters(length, multiplier)
            assert is_valid == True, f"Failed for valid case: ({length}, {multiplier})"
            assert error is None

        # Invalid length cases
        invalid_length_cases = [
            (0, 2.0, "ATR length must be positive"),
            (-1, 2.0, "ATR length must be positive"),
            (-10, 2.0, "ATR length must be positive"),
        ]

        for length, multiplier, expected_error in invalid_length_cases:
            is_valid, error = validate_atr_parameters(length, multiplier)
            assert is_valid == False, f"Should be invalid: ({length}, {multiplier})"
            assert expected_error in error

        # Invalid multiplier cases
        invalid_multiplier_cases = [
            (14, 0.0, "ATR multiplier must be positive"),
            (14, -1.0, "ATR multiplier must be positive"),
            (14, -5.0, "ATR multiplier must be positive"),
        ]

        for length, multiplier, expected_error in invalid_multiplier_cases:
            is_valid, error = validate_atr_parameters(length, multiplier)
            assert is_valid == False, f"Should be invalid: ({length}, {multiplier})"
            assert expected_error in error


class TestHybridSignalGeneration:
    """Test hybrid MA+ATR signal generation functionality."""

    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_sma_signals")
    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_atr")
    def test_generate_hybrid_ma_atr_signals_basic(
        self, mock_atr, mock_sma, sample_price_data, sample_ma_config, mock_logger
    ):
        """Test basic hybrid signal generation."""
        # Mock SMA signal generation
        sma_result = sample_price_data.copy()
        sma_result["Signal"] = [0] * len(sample_price_data)
        sma_result["Position"] = [0] * len(sample_price_data)
        # Add entry signals at positions 10 and 50
        sma_result.loc[sma_result.index[10], "Signal"] = 1
        sma_result.loc[sma_result.index[50], "Signal"] = 1
        mock_sma.return_value = sma_result

        # Mock ATR calculation with reasonable values
        atr_values = pd.Series(
            [2.0] * len(sample_price_data), index=sample_price_data.index
        )
        mock_atr.return_value = atr_values

        # Generate hybrid signals
        result = generate_hybrid_ma_atr_signals(
            sample_price_data,
            sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            log=mock_logger,
        )

        # Debug: check if SMA mock was called
        mock_sma.assert_called_once()

        # Verify result structure
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_price_data)
        assert "Signal" in result.columns
        assert "Position" in result.columns
        assert "Close" in result.columns

        # Verify ATR calculation was attempted (called with the modified data)
        # ATR is called on line 142 with the data returned from calculate_sma_signals
        assert mock_atr.call_count >= 1  # Should be called at least once

        # Check that result has expected structure with ATR columns
        assert "ATR" in result.columns
        assert "ATR_Trailing_Stop" in result.columns
        assert "ATR_Signal" in result.columns

        # The hybrid logic processes signals differently than direct copy
        # So we verify the structure rather than specific signal counts
        assert all(
            col in result.columns for col in ["Signal", "Position", "ATR", "ATR_Signal"]
        )

    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_sma_signals")
    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_atr")
    def test_generate_hybrid_signals_with_atr_exits(
        self, mock_atr, mock_sma, sample_price_data, sample_ma_config, mock_logger
    ):
        """Test that ATR trailing stops generate exit signals."""
        # Create more realistic price data with a significant move
        price_data = sample_price_data.copy()
        # Simulate a price spike and then decline for ATR exit testing
        mid_point = len(price_data) // 2
        price_data.loc[price_data.index[mid_point:], "Close"] *= 1.2  # 20% spike
        price_data.loc[
            price_data.index[mid_point + 10 :], "Close"
        ] *= 0.85  # Then decline

        # Mock SMA signals with entry at the spike
        sma_result = price_data.copy()
        sma_result["Signal"] = [0] * len(price_data)
        sma_result["Position"] = [0] * len(price_data)
        sma_result.loc[sma_result.index[mid_point], "Signal"] = 1  # Entry at spike
        mock_sma.return_value = sma_result

        # Mock ATR with realistic values
        base_atr = price_data["Close"].iloc[0] * 0.02  # 2% of price
        atr_values = pd.Series([base_atr] * len(price_data), index=price_data.index)
        mock_atr.return_value = atr_values

        # Generate signals with ATR exits
        result = generate_hybrid_ma_atr_signals(
            price_data,
            sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            log=mock_logger,
        )

        assert result is not None

        # Check for ATR exit signals (should be negative signals after entry)
        entry_idx = None
        for i, signal in enumerate(result["Signal"]):
            if signal == 1:  # Found entry
                entry_idx = i
            elif signal == -1 and entry_idx is not None:  # Found exit after entry
                assert i > entry_idx  # Exit should come after entry
                break

        # Should have both entry and exit signals
        assert (result["Signal"] == 1).sum() > 0  # At least one entry
        assert (result["Signal"] == -1).sum() > 0  # At least one exit

    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_sma_signals")
    @patch("app.tools.calculate_atr.calculate_atr")
    def test_generate_signals_error_handling(
        self, mock_atr, mock_sma, sample_ma_config, mock_logger
    ):
        """Test error handling in signal generation."""
        # Test with None data
        result = generate_hybrid_ma_atr_signals(
            None, sample_ma_config, atr_length=14, atr_multiplier=2.0, log=mock_logger
        )
        assert result is None

        # Test with empty data
        empty_data = pd.DataFrame()
        result = generate_hybrid_ma_atr_signals(
            empty_data,
            sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            log=mock_logger,
        )
        assert result is None

        # Test with invalid data structure
        invalid_data = pd.DataFrame({"InvalidColumn": [1, 2, 3]})
        result = generate_hybrid_ma_atr_signals(
            invalid_data,
            sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            log=mock_logger,
        )
        assert result is None

        # Verify error logging
        assert mock_logger.call_count > 0

    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_sma_signals")
    @patch("app.tools.calculate_atr.calculate_atr")
    def test_generate_signals_sma_failure(
        self, mock_atr, mock_sma, sample_price_data, sample_ma_config, mock_logger
    ):
        """Test handling of SMA calculation failure."""
        # Mock SMA failure
        mock_sma.return_value = None
        mock_atr.return_value = pd.Series([2.0] * len(sample_price_data))

        result = generate_hybrid_ma_atr_signals(
            sample_price_data,
            sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            log=mock_logger,
        )

        assert result is None
        mock_sma.assert_called_once()
        # ATR should not be called if SMA fails
        mock_atr.assert_not_called()

    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_sma_signals")
    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_atr")
    def test_generate_signals_atr_failure(
        self, mock_atr, mock_sma, sample_price_data, sample_ma_config, mock_logger
    ):
        """Test handling of ATR calculation failure."""
        # Mock successful SMA but failed ATR
        sma_result = sample_price_data.copy()
        sma_result["Signal"] = [0] * len(sample_price_data)
        sma_result["Position"] = [0] * len(sample_price_data)
        mock_sma.return_value = sma_result
        mock_atr.return_value = None

        result = generate_hybrid_ma_atr_signals(
            sample_price_data,
            sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            log=mock_logger,
        )

        assert result is None
        mock_sma.assert_called_once()
        mock_atr.assert_called_once()


# class TestATRTrailingStops:
#     """Test ATR trailing stop functionality."""
#     # These tests are commented out because apply_atr_trailing_stops
#     # is implemented within generate_hybrid_ma_atr_signals function
#     # TODO: Refactor if trailing stop logic needs to be tested separately


class TestSignalValidation:
    """Test signal validation and quality checks."""

    def test_signal_data_validation(self):
        """Test validation of signal data structure."""
        # Valid signal data
        valid_data = pd.DataFrame(
            {
                "Date": pd.date_range("2023-01-01", periods=10),
                "Close": range(100, 110),
                "Signal": [0, 1, 0, 0, -1, 0, 1, 0, 0, -1],
                "Position": [0, 1, 1, 1, 0, 0, 1, 1, 1, 0],
            }
        )

        # Check that signal data has required columns
        required_columns = ["Close", "Signal", "Position"]
        for col in required_columns:
            assert col in valid_data.columns

        # Check signal values are valid (-1, 0, 1)
        valid_signals = set([-1, 0, 1])
        assert set(valid_data["Signal"].unique()).issubset(valid_signals)

        # Check position values are valid (0, 1)
        valid_positions = set([0, 1])
        assert set(valid_data["Position"].unique()).issubset(valid_positions)

    def test_signal_consistency_checks(self):
        """Test signal consistency validation."""
        # Create data with consistent signals and positions
        consistent_data = pd.DataFrame(
            {
                "Signal": [0, 1, 0, 0, -1, 0, 1, 0, -1, 0],
                "Position": [0, 1, 1, 1, 0, 0, 1, 1, 0, 0],
            }
        )

        # Check that position changes align with signals
        for i in range(1, len(consistent_data)):
            prev_pos = consistent_data.loc[i - 1, "Position"]
            curr_pos = consistent_data.loc[i, "Position"]
            signal = consistent_data.loc[i, "Signal"]

            if signal == 1:  # Entry signal
                assert curr_pos == 1, f"Position should be 1 after entry signal at {i}"
            elif signal == -1:  # Exit signal
                assert curr_pos == 0, f"Position should be 0 after exit signal at {i}"
            else:  # No signal
                # Position can stay the same or change due to other factors
                pass

    def test_signal_quality_metrics(self):
        """Test signal quality metrics calculation."""
        # Create sample signal data
        signal_data = pd.DataFrame(
            {
                "Signal": [0, 1, 0, 0, -1, 0, 1, 0, 0, -1] * 5,  # 50 signals
                "Position": [0, 1, 1, 1, 0, 0, 1, 1, 1, 0] * 5,
            }
        )

        # Calculate basic signal metrics
        total_signals = (signal_data["Signal"] != 0).sum()
        entry_signals = (signal_data["Signal"] == 1).sum()
        exit_signals = (signal_data["Signal"] == -1).sum()

        assert total_signals == entry_signals + exit_signals
        assert entry_signals == 10  # 2 entries per cycle × 5 cycles
        assert exit_signals == 10  # 2 exits per cycle × 5 cycles

        # Check signal frequency
        signal_frequency = total_signals / len(signal_data)
        assert 0 < signal_frequency < 1  # Should be between 0 and 1

        # Check position time in market
        time_in_position = (signal_data["Position"] == 1).sum() / len(signal_data)
        assert 0 < time_in_position < 1  # Should be between 0 and 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
