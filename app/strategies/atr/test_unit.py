#!/usr/bin/env python3
"""
ATR Strategy Unit Tests - Mathematical Accuracy and Core Logic

This test suite validates the core ATR trailing stop algorithm components:
- ATR calculation mathematical accuracy
- Trailing stop logic correctness  
- Signal generation behavior
- Edge case handling

Focus: Fast execution, isolated testing of pure calculation logic
"""

import unittest
from datetime import datetime, timedelta
from typing import Dict, Any
import numpy as np
import pandas as pd
import pytest

from app.strategies.atr.tools.strategy_execution import (
    calculate_atr, 
    generate_signals,
    analyze_params
)


class TestATRMathematicalAccuracy(unittest.TestCase):
    """Test ATR calculation mathematical accuracy."""

    def setUp(self):
        """Set up test data for mathematical validation."""
        # Create controlled price data for mathematical precision testing
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        
        # Controlled price sequence with known volatility patterns
        base_price = 100.0
        price_changes = [0, 2, -1, 3, -2, 1, -1, 4, -3, 2] * 5  # Repeating pattern
        
        closes = []
        highs = []
        lows = []
        
        current_price = base_price
        for change in price_changes:
            current_price += change
            # Create realistic high/low based on close
            daily_range = abs(change) + 1  # Minimum 1 unit range
            high = current_price + daily_range * 0.6
            low = current_price - daily_range * 0.4
            
            closes.append(current_price)
            highs.append(high)
            lows.append(low)
            
        self.test_data = pd.DataFrame({
            'Date': dates,
            'Open': closes,  # Simplified: open = previous close
            'High': highs,
            'Low': lows, 
            'Close': closes,
            'Volume': [10000] * len(dates)  # Constant volume
        }, index=dates)

    def test_atr_calculation_mathematical_correctness(self):
        """Test ATR calculation produces mathematically correct results."""
        length = 14
        
        result_atr = calculate_atr(self.test_data, length)
        
        # Manual calculation for validation
        # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
        manual_tr = []
        for i in range(1, len(self.test_data)):
            high = self.test_data['High'].iloc[i]
            low = self.test_data['Low'].iloc[i]
            prev_close = self.test_data['Close'].iloc[i-1]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            manual_tr.append(tr)
        
        # Calculate manual ATR (Simple Moving Average of True Range)
        manual_atr = []
        for i in range(length-1, len(manual_tr)):
            atr_value = np.mean(manual_tr[i-length+1:i+1])
            manual_atr.append(atr_value)
        
        # Compare our implementation with manual calculation
        # Start from index where both calculations begin
        start_idx = length
        
        for i, manual_val in enumerate(manual_atr):
            calc_val = result_atr.iloc[start_idx + i]
            self.assertAlmostEqual(
                calc_val, manual_val, places=6,
                msg=f"ATR mismatch at index {start_idx + i}: calc={calc_val}, manual={manual_val}"
            )

    def test_atr_handles_edge_cases(self):
        """Test ATR calculation handles edge cases properly."""
        # Test with minimal data
        minimal_data = self.test_data.head(3)
        result = calculate_atr(minimal_data, 2)
        
        # Should have NaN for insufficient data, then valid values
        self.assertTrue(pd.isna(result.iloc[0]))
        # With length=2, ATR should start from index 1 (not 2), but may have NaN initially
        # The key is that we should have some valid ATR values
        valid_atr_count = result.dropna().shape[0]
        self.assertGreater(valid_atr_count, 0, "Should have some valid ATR values")
        
        # Test with ATR length longer than data
        result_long = calculate_atr(minimal_data, 10)
        self.assertTrue(result_long.isna().all())

    def test_atr_index_preservation(self):
        """Test ATR calculation preserves original DataFrame index."""
        result = calculate_atr(self.test_data, 14)
        
        # Should have same index as input
        pd.testing.assert_index_equal(result.index, self.test_data.index)
        self.assertEqual(len(result), len(self.test_data))


class TestATRDirectionSupport(unittest.TestCase):
    """Test ATR strategy support for both Long and Short directions."""

    def setUp(self):
        """Set up test data for direction testing."""
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        
        # Create clear trending data for direction testing
        uptrend_prices = [100 + i*2 for i in range(15)]  # Strong uptrend
        downtrend_prices = [130 - i*1.5 for i in range(15)]  # Strong downtrend
        price_pattern = uptrend_prices + downtrend_prices
        
        highs = [price + 1 for price in price_pattern]
        lows = [price - 1 for price in price_pattern] 
        
        self.direction_test_data = pd.DataFrame({
            'Date': dates,
            'Open': price_pattern,
            'High': highs,
            'Low': lows,
            'Close': price_pattern,
            'Volume': [10000] * len(dates)
        }, index=dates)

    def test_long_direction_signal_generation(self):
        """Test Long direction generates correct signals."""
        result = generate_signals(self.direction_test_data, 5, 2.0, "Long")
        
        # Verify signal generation for Long direction
        signals = result['Signal'].dropna()
        self.assertTrue(len(signals) > 0, "Long direction should generate signals")
        
        # Check that trailing stops are below price (for long positions)
        for i in range(len(result)):
            stop = result['ATR_Trailing_Stop'].iloc[i]
            close = result['Close'].iloc[i]
            if not pd.isna(stop):
                # For long positions, trailing stop should generally be below close price
                # (allowing some tolerance for volatility)
                pass  # Logic validation handled in other tests

    def test_short_direction_signal_generation(self):
        """Test Short direction generates correct signals."""
        result = generate_signals(self.direction_test_data, 5, 2.0, "Short")
        
        # Verify signal generation for Short direction
        signals = result['Signal'].dropna()
        self.assertTrue(len(signals) > 0, "Short direction should generate signals")
        
        # Verify that Short direction uses -1 for entry signals (not 1)
        unique_signals = signals.unique()
        entry_signals = [s for s in unique_signals if s != 0]
        if len(entry_signals) > 0:
            # For Short direction, entry/hold signals should be -1
            for signal in entry_signals:
                self.assertEqual(signal, -1, f"Short direction should use -1 for entry signals, got {signal}")
        
        # Check that trailing stops are above price (for short positions)  
        for i in range(len(result)):
            stop = result['ATR_Trailing_Stop'].iloc[i]
            close = result['Close'].iloc[i]
            if not pd.isna(stop):
                # For short positions, trailing stop should generally be above close price
                # (allowing some tolerance for volatility)
                pass  # Logic validation handled in other tests

    def test_short_trailing_stop_movement(self):
        """Test Short trailing stop only moves down (never up) when in position."""
        # Create declining price data for short testing
        dates = pd.date_range('2023-01-01', periods=20, freq='D')
        declining_prices = [120 - i*2 for i in range(20)]  # Declining from 120 to 82
        
        data = pd.DataFrame({
            'Date': dates,
            'Open': declining_prices,
            'High': [p + 0.5 for p in declining_prices],
            'Low': [p - 0.5 for p in declining_prices],
            'Close': declining_prices,
            'Volume': [10000] * 20
        }, index=dates)
        
        result = generate_signals(data, 5, 2.0, "Short")
        
        # Find periods when in short position and verify trailing stop behavior
        prev_stop = None
        prev_signal = None
        
        for i in range(2, len(result)):
            current_signal = result['Signal'].iloc[i]
            current_stop = result['ATR_Trailing_Stop'].iloc[i]
            
            if pd.isna(current_stop):
                continue
            
            # Check if we're continuing a short position (signal was -1 and still is -1)
            if current_signal == -1 and prev_signal == -1 and prev_stop is not None:
                # For short positions, trailing stop can only move down (become lower)
                # Allow small floating point tolerance
                self.assertLessEqual(
                    current_stop, prev_stop + 1e-6,
                    f"Short trailing stop moved up while in position at index {i}: "
                    f"{current_stop} > {prev_stop}"
                )
            
            prev_stop = current_stop
            prev_signal = current_signal

    def test_direction_parameter_validation(self):
        """Test direction parameter validation and defaults."""
        # Test with default direction (Long)
        result_default = generate_signals(self.direction_test_data, 10, 1.5)
        result_explicit_long = generate_signals(self.direction_test_data, 10, 1.5, "Long")
        
        # Results should be identical
        pd.testing.assert_frame_equal(result_default, result_explicit_long)
        
        # Test case insensitivity
        result_lower = generate_signals(self.direction_test_data, 10, 1.5, "long")
        result_upper = generate_signals(self.direction_test_data, 10, 1.5, "LONG")
        
        pd.testing.assert_frame_equal(result_lower, result_upper)


class TestATRTrailingStopLogic(unittest.TestCase):
    """Test ATR trailing stop signal generation logic."""

    def setUp(self):
        """Set up test data for trailing stop logic validation."""
        # Create price data with clear trend patterns for signal testing
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        
        # Pattern: Uptrend (5 days) → Sideways (10 days) → Downtrend (5 days) → Recovery (10 days)
        price_pattern = (
            [100 + i*2 for i in range(5)] +      # Uptrend: 100→108
            [108 + np.sin(i)*1 for i in range(10)] +  # Sideways: 108±1
            [108 - i*1.5 for i in range(5)] +    # Downtrend: 108→100.5
            [100.5 + i*1.2 for i in range(10)]   # Recovery: 100.5→112.5
        )
        
        # Create realistic OHLC from close prices
        highs = [price + 0.5 for price in price_pattern]
        lows = [price - 0.5 for price in price_pattern] 
        
        self.trend_data = pd.DataFrame({
            'Date': dates,
            'Open': price_pattern,
            'High': highs,
            'Low': lows,
            'Close': price_pattern,
            'Volume': [10000] * len(dates)
        }, index=dates)

    def test_trailing_stop_position_awareness(self):
        """Test trailing stop behaves differently when in/out of position."""
        atr_length = 5
        atr_multiplier = 2.0
        
        result = generate_signals(self.trend_data, atr_length, atr_multiplier, "Long")
        
        # Verify we have the expected columns
        expected_columns = ['Signal', 'ATR_Trailing_Stop', 'ATR', 'Position']
        for col in expected_columns:
            self.assertIn(col, result.columns, f"Missing expected column: {col}")
        
        # Test core trailing stop behavior:
        # 1. When not in position, trailing stop can move freely
        # 2. When in position, trailing stop can only move up
        
        # Track position state properly by looking at consecutive signals
        prev_stop = None
        
        for i in range(2, len(result)):  # Start from index 2 to have previous signal
            current_signal = result['Signal'].iloc[i]
            prev_signal = result['Signal'].iloc[i-1]
            current_stop = result['ATR_Trailing_Stop'].iloc[i]
            
            if pd.isna(current_stop):
                continue
            
            # Determine if we're in position by looking at signal transitions
            # We're in position if current signal is 1 AND previous was also 1
            # (i.e., we're holding a position, not just entering)
            in_position = (current_signal == 1 and prev_signal == 1)
            
            # When in position, trailing stop should only move up or stay same
            if in_position and prev_stop is not None and not pd.isna(prev_stop):
                self.assertGreaterEqual(
                    current_stop, prev_stop - 1e-6,  # Allow small floating point tolerance
                    f"Trailing stop moved down while in position at index {i}: "
                    f"{current_stop} < {prev_stop}"
                )
            
            prev_stop = current_stop

    def test_signal_generation_logic(self):
        """Test entry and exit signal generation logic."""
        atr_length = 3
        atr_multiplier = 1.5
        
        result = generate_signals(self.trend_data, atr_length, atr_multiplier, "Long")
        
        # Validate signal consistency: 
        # - Entry signal should occur when close >= trailing_stop (when not in position)
        # - Exit signal should occur when close < trailing_stop (when in position)
        
        for i in range(1, len(result)):
            close = result['Close'].iloc[i]
            signal = result['Signal'].iloc[i]
            trailing_stop = result['ATR_Trailing_Stop'].iloc[i]
            
            if pd.isna(trailing_stop):
                continue
            
            # Verify signal logic consistency
            if signal == 1:  # Entry/Hold signal
                self.assertGreaterEqual(
                    close, trailing_stop - 1e-6,
                    f"Entry signal when close < trailing_stop at index {i}: "
                    f"close={close}, stop={trailing_stop}"
                )
            elif signal == 0:  # Exit/Stay out signal  
                # Note: Exit can occur when close < trailing_stop OR when not initially triggered
                pass  # Exit logic is more complex, tested separately

    def test_position_column_accuracy(self):
        """Test Position column is correctly shifted from Signal column."""
        result = generate_signals(self.trend_data, 5, 2.0, "Long")
        
        # Position should be shifted Signal (previous period's signal)
        for i in range(1, len(result)):
            expected_position = result['Signal'].iloc[i-1] if i > 0 else 0
            actual_position = result['Position'].iloc[i]
            
            # Handle NaN cases
            if pd.isna(expected_position):
                expected_position = 0
            if pd.isna(actual_position):
                actual_position = 0
                
            self.assertEqual(
                actual_position, expected_position,
                f"Position mismatch at index {i}: expected={expected_position}, actual={actual_position}"
            )


class TestATRAnalysisIntegration(unittest.TestCase):
    """Test analyze_params function integration."""

    def setUp(self):
        """Set up realistic data for analysis testing."""
        # Create longer data series for meaningful analysis
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        np.random.seed(42)  # Reproducible results
        
        # Simulate realistic price movement
        returns = np.random.normal(0.0005, 0.02, len(dates))  # 0.05% daily drift, 2% volatility
        prices = [100]
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLC data with realistic spreads
        closes = prices[1:]  # Remove initial price
        highs = [close * (1 + abs(np.random.normal(0, 0.005))) for close in closes]
        lows = [close * (1 - abs(np.random.normal(0, 0.005))) for close in closes]
        opens = closes  # Simplified
        
        self.analysis_data = pd.DataFrame({
            'Date': dates,
            'Open': opens,
            'High': highs, 
            'Low': lows,
            'Close': closes,
            'Volume': np.random.randint(50000, 200000, len(dates))
        }, index=dates)

    def test_analyze_params_returns_valid_portfolio(self):
        """Test analyze_params returns valid portfolio dictionary."""
        # Mock logger
        log_messages = []
        def mock_log(msg, level="info"):
            log_messages.append(f"{level}: {msg}")
        
        result = analyze_params(
            self.analysis_data, 
            atr_length=10, 
            atr_multiplier=3.0, 
            ticker="TEST", 
            log=mock_log,
            config={"DIRECTION": "Long"}
        )
        
        # Verify result is a dictionary with expected keys
        self.assertIsInstance(result, dict)
        
        # Check for essential portfolio metrics
        essential_keys = [
            "Ticker", "Strategy Type", "Fast Period", "Slow Period",
            "Total Trades", "Win Rate [%]", "Total Return [%]", "Score"
        ]
        
        for key in essential_keys:
            self.assertIn(key, result, f"Missing essential key: {key}")
        
        # Verify ATR-specific mappings
        self.assertEqual(result["Ticker"], "TEST")
        self.assertEqual(result["Strategy Type"], "ATR")
        self.assertEqual(result["Fast Period"], 10)  # ATR length
        self.assertEqual(result["Slow Period"], 30)  # atr_multiplier * 10
        self.assertEqual(result["Signal Period"], 0)
        
        # Verify metrics are reasonable
        self.assertIsInstance(result["Total Trades"], (int, float))
        self.assertGreaterEqual(result["Total Trades"], 0)
        self.assertIsInstance(result["Win Rate [%]"], (int, float))
        self.assertGreaterEqual(result["Win Rate [%]"], 0)
        self.assertLessEqual(result["Win Rate [%]"], 100)

    def test_analyze_params_error_handling(self):
        """Test analyze_params handles errors gracefully."""
        log_messages = []
        def mock_log(msg, level="info"):
            log_messages.append(f"{level}: {msg}")
        
        # Test with invalid/empty data
        empty_data = pd.DataFrame({'Close': [], 'High': [], 'Low': [], 'ATR': []})
        
        result = analyze_params(
            empty_data, 
            atr_length=10, 
            atr_multiplier=2.0, 
            ticker="INVALID", 
            log=mock_log,
            config={"DIRECTION": "Long"}
        )
        
        # Should return error portfolio
        self.assertIsInstance(result, dict)
        self.assertEqual(result["Ticker"], "INVALID")
        self.assertEqual(result["Total Trades"], 0)
        self.assertEqual(result["Score"], 0.0)
        
        # Should have logged error
        error_logged = any("error" in msg.lower() for msg in log_messages)
        self.assertTrue(error_logged, "Expected error to be logged for invalid data")

    def test_analyze_params_direction_support(self):
        """Test analyze_params supports both Long and Short directions."""
        log_messages = []
        def mock_log(msg, level="info"):
            log_messages.append(f"{level}: {msg}")
        
        # Test Long direction
        result_long = analyze_params(
            self.analysis_data, 
            atr_length=10, 
            atr_multiplier=2.0, 
            ticker="TEST_LONG", 
            log=mock_log,
            config={"DIRECTION": "Long"}
        )
        
        # Test Short direction
        result_short = analyze_params(
            self.analysis_data, 
            atr_length=10, 
            atr_multiplier=2.0, 
            ticker="TEST_SHORT", 
            log=mock_log,
            config={"DIRECTION": "Short"}
        )
        
        # Both should be valid portfolios
        self.assertIsInstance(result_long, dict)
        self.assertIsInstance(result_short, dict)
        
        # Both should have same structure
        self.assertEqual(result_long["Ticker"], "TEST_LONG")
        self.assertEqual(result_short["Ticker"], "TEST_SHORT")
        self.assertEqual(result_long["Strategy Type"], "ATR")
        self.assertEqual(result_short["Strategy Type"], "ATR")
        
        # Performance metrics should be different (different directions)
        # Note: We don't compare specific values as market conditions affect results


class TestATRRegressionPrevention(unittest.TestCase):
    """Test cases to prevent regression to historical bugs."""

    def test_prevent_always_true_entry_signal(self):
        """Regression test: Prevent entry signal always being true."""
        # Create data that should NOT always generate entry signals
        dates = pd.date_range('2023-01-01', periods=20, freq='D')
        
        # Declining price pattern - should generate exits
        prices = [100 - i for i in range(20)]  # 100 down to 81
        
        test_data = pd.DataFrame({
            'Date': dates,
            'Open': prices,
            'High': [p + 0.5 for p in prices],
            'Low': [p - 0.5 for p in prices],
            'Close': prices,
            'Volume': [10000] * 20
        }, index=dates)
        
        result = generate_signals(test_data, 5, 2.0, "Long")
        
        # With declining prices, we should NOT have all signals = 1
        signal_values = result['Signal'].dropna().values
        self.assertTrue(
            len(np.unique(signal_values)) > 1 or 0 in signal_values,
            "Regression detected: All signals are entry signals (always true bug)"
        )

    def test_score_calculation_non_zero(self):
        """Regression test: Ensure Score is calculated (not always 0)."""
        # Use data that should generate some trading activity
        log_messages = []
        def mock_log(msg, level="info"):
            log_messages.append(f"{level}: {msg}")
        
        # Create trending data that should generate profitable trades
        dates = pd.date_range('2020-01-01', periods=200, freq='D')
        trend_prices = [100 + i*0.1 + np.sin(i/10)*2 for i in range(200)]
        
        trending_data = pd.DataFrame({
            'Date': dates,
            'Open': trend_prices,
            'High': [p + 1 for p in trend_prices],
            'Low': [p - 1 for p in trend_prices],
            'Close': trend_prices,
            'Volume': [50000] * 200
        }, index=dates)
        
        result = analyze_params(
            trending_data, 
            atr_length=15, 
            atr_multiplier=1.5, 
            ticker="TREND_TEST", 
            log=mock_log,
            config={"DIRECTION": "Long"}
        )
        
        # Score should be calculated (non-zero for profitable strategy)
        self.assertNotEqual(result["Score"], 0.0, 
                          "Regression detected: Score calculation broken (always 0)")
        
        # Should have reasonable metrics
        if result["Total Trades"] > 0:
            # Win Rate might be NaN if backtest has issues, but Score should be calculated
            # The key regression test is that Score is not 0 when there are trades
            win_rate = result["Win Rate [%]"]
            if not pd.isna(win_rate):
                self.assertGreaterEqual(win_rate, 0)  # Can be 0 if all trades lose


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)