#!/usr/bin/env python3
"""
ATR Strategy Regression Tests - Algorithm Breakage Prevention

This test suite prevents regression to historical bugs and ensures
critical ATR algorithm functionality remains intact:
- Prevent always-true entry signal bug
- Ensure Score calculation (not always 0)
- Validate proper ticker naming in exports
- Prevent excessive short-term trade generation
- Maintain ATR-specific parameter mappings
- Validate duration field exports

Focus: Regression prevention with specific tests for historical bugs
"""

import unittest

import numpy as np
import pandas as pd

from app.strategies.atr.tools.strategy_execution import (
    analyze_params,
    calculate_atr,
    generate_signals,
)


class TestATRRegressionPrevention(unittest.TestCase):
    """Test cases to prevent regression to specific historical bugs."""

    def setUp(self):
        """Set up test data for regression testing."""
        # Create controlled test data that exposed historical bugs
        self.dates = pd.date_range("2020-01-01", periods=200, freq="D")

        # Pattern that historically caused issues:
        # Declining prices that led to always-true entry signals
        declining_prices = [100 - i * 0.2 for i in range(200)]  # 100 down to 60

        # Add some volatility but maintain overall decline
        prices = [p + np.random.normal(0, 1) for p in declining_prices]

        # Create realistic OHLC
        highs = [p + abs(np.random.normal(0, 0.8)) for p in prices]
        lows = [p - abs(np.random.normal(0, 0.8)) for p in prices]

        self.regression_test_data = pd.DataFrame(
            {
                "Date": self.dates,
                "Open": prices,
                "High": highs,
                "Low": lows,
                "Close": prices,
                "Volume": [100000] * len(prices),
            },
        ).set_index("Date")

        # Mock logger
        self.log_messages = []
        self.test_log = lambda msg, level="info": self.log_messages.append(
            f"{level}: {msg}",
        )

    def test_prevent_always_true_entry_signals(self):
        """REGRESSION TEST: Prevent entry signals from always being true."""
        # Historical bug: entry condition was current_close >= current_close - atr*multiplier
        # which is always true, causing excessive signal generation

        # Test with declining price data that should NOT always generate entry signals
        signals_df = generate_signals(self.regression_test_data, 14, 2.0)

        # Extract signal values (skip NaN values from initial ATR calculation period)
        signal_values = signals_df["Signal"].dropna().values

        # CRITICAL REGRESSION CHECK: Not all signals should be entry signals (1)
        unique_signals = np.unique(signal_values)

        # Should have variety in signals, not just all 1s
        self.assertGreater(
            len(unique_signals),
            1,
            "REGRESSION BUG: All signals are entry signals (always-true entry condition)",
        )

        # In declining market, should have exit signals (0)
        self.assertIn(
            0,
            signal_values,
            "REGRESSION BUG: No exit signals in declining market (entry always true)",
        )

        # Should not have more entry than exit signals in declining market
        entry_signals = np.sum(signal_values == 1)
        exit_signals = np.sum(signal_values == 0)

        # In a declining market, entries should be limited
        self.assertLessEqual(
            entry_signals,
            exit_signals * 2,  # Allow some ratio tolerance
            "REGRESSION BUG: Too many entry signals in declining market",
        )

    def test_prevent_score_always_zero(self):
        """REGRESSION TEST: Ensure Score calculation works (not always 0)."""
        # Historical bug: ATR strategy was bypassing convert_stats() function
        # causing Score to always be 0 regardless of performance

        # Test with data that should produce measurable performance
        result = analyze_params(
            self.regression_test_data,
            atr_length=10,
            atr_multiplier=2.5,
            ticker="REGRESSION_TEST",
            log=self.test_log,
        )

        # CRITICAL REGRESSION CHECK: Score should be calculated
        score = result["Score"]

        if result["Total Trades"] > 0:
            # If there are trades, Score should not be 0 (unless truly awful performance)
            self.assertNotEqual(
                score,
                0.0,
                "REGRESSION BUG: Score calculation is broken (always 0)",
            )

            # Score should be a reasonable numeric value
            self.assertIsInstance(score, (int, float), "Score should be numeric")
            self.assertFalse(np.isnan(score), "Score should not be NaN")

    def test_prevent_ticker_corruption(self):
        """REGRESSION TEST: Prevent ticker name corruption in exports."""
        # Historical bug: Ticker was showing as "UNKNOWN" in CSV exports
        # due to config not being passed to convert_stats()

        test_ticker = "SPECIFIC_TICKER_NAME"

        result = analyze_params(
            self.regression_test_data,
            atr_length=15,
            atr_multiplier=2.0,
            ticker=test_ticker,
            log=self.test_log,
        )

        # CRITICAL REGRESSION CHECK: Ticker name should be preserved
        self.assertEqual(
            result["Ticker"],
            test_ticker,
            "REGRESSION BUG: Ticker name corrupted (showing as UNKNOWN)",
        )

    def test_prevent_wrong_strategy_type_export(self):
        """REGRESSION TEST: Prevent ATR strategies being exported as SMA."""
        # Historical bug: ATR strategies were being exported with Strategy Type = "SMA"
        # instead of "ATR"

        result = analyze_params(
            self.regression_test_data,
            atr_length=12,
            atr_multiplier=3.0,
            ticker="ATR_TYPE_TEST",
            log=self.test_log,
        )

        # CRITICAL REGRESSION CHECK: Strategy Type should be "ATR"
        self.assertEqual(
            result["Strategy Type"],
            "ATR",
            "REGRESSION BUG: ATR strategy exported as wrong type (SMA)",
        )

    def test_prevent_hardcoded_period_values(self):
        """REGRESSION TEST: Prevent hardcoded Fast/Slow Period values (20,50)."""
        # Historical bug: Fast Period and Slow Period were showing as hardcoded 20,50
        # instead of actual ATR length and multiplier values

        test_atr_length = 8
        test_atr_multiplier = 4.5

        result = analyze_params(
            self.regression_test_data,
            atr_length=test_atr_length,
            atr_multiplier=test_atr_multiplier,
            ticker="PERIOD_TEST",
            log=self.test_log,
        )

        # CRITICAL REGRESSION CHECK: Parameters should reflect actual ATR values
        self.assertEqual(
            result["Fast Period"],
            test_atr_length,
            "REGRESSION BUG: Fast Period shows hardcoded value instead of ATR length",
        )

        # Slow Period should represent multiplier (multiplied by 10 for display)
        expected_slow_period = int(test_atr_multiplier * 10)
        self.assertEqual(
            result["Slow Period"],
            expected_slow_period,
            "REGRESSION BUG: Slow Period shows hardcoded value instead of ATR multiplier",
        )

        # Signal Period should be 0 for ATR (not applicable)
        self.assertEqual(
            result["Signal Period"],
            0,
            "REGRESSION BUG: Signal Period should be 0 for ATR strategy",
        )

    def test_prevent_excessive_trade_generation(self):
        """REGRESSION TEST: Prevent excessive trade generation (70 vs 5 positions)."""
        # Historical bug: ATR was generating 70+ short-term trades instead of
        # 5 long-term positions as validated externally

        # Use longer test period similar to external validation (14 years ≈ 3650 days)
        long_dates = pd.date_range("2010-01-01", periods=3650, freq="D")

        # Create TSLA-like pattern with realistic long-term trends
        np.random.seed(123)  # Different seed for this test
        base_price = 20.0

        # Simulate multi-year growth with periods of consolidation
        price_changes = []
        for i in range(len(long_dates)):
            # Different phases: early growth, volatility, recent action
            if i < 1200:  # Years 1-3: modest growth
                trend = 0.0005
                vol = 0.025
            elif i < 2400:  # Years 4-6: acceleration
                trend = 0.0012
                vol = 0.040
            elif i < 3000:  # Years 7-8: peak volatility
                trend = 0.0003
                vol = 0.055
            else:  # Years 9-14: maturation
                trend = 0.0002
                vol = 0.030

            change = np.random.normal(trend, vol)
            price_changes.append(change)

        prices = base_price * np.exp(np.cumsum(price_changes))

        # Create long-term test data
        long_term_data = pd.DataFrame(
            {
                "Date": long_dates,
                "Open": prices,
                "High": prices * 1.015,
                "Low": prices * 0.985,
                "Close": prices,
                "Volume": np.random.randint(1000000, 20000000, len(prices)),
            },
        ).set_index("Date")

        # Test ATR(15, 1.5) as per external validation
        result = analyze_params(
            long_term_data,
            atr_length=15,
            atr_multiplier=1.5,
            ticker="LONG_TERM_TEST",
            log=self.test_log,
        )

        total_trades = result["Total Trades"]

        # CRITICAL REGRESSION CHECK: Should not generate excessive trades
        # External validation showed ~5 positions over 14 years
        # Allow reasonable tolerance but prevent 70+ trade bug
        self.assertLess(
            total_trades,
            50,  # Much less than bug level of 70+
            "REGRESSION BUG: Excessive trade generation (short-term vs long-term positions)",
        )

        # Should generate some trades (not 0)
        self.assertGreater(
            total_trades,
            0,
            "Should generate some trades in long-term trending market",
        )

    def test_prevent_duration_export_errors(self):
        """REGRESSION TEST: Prevent duration field export errors."""
        # Historical bug: Duration fields were causing export errors due to
        # nanosecond/microsecond datatype issues in Polars

        result = analyze_params(
            self.regression_test_data,
            atr_length=10,
            atr_multiplier=2.0,
            ticker="DURATION_TEST",
            log=self.test_log,
        )

        # Check for duration-related fields
        duration_fields = [key for key in result if "duration" in key.lower()]

        for field in duration_fields:
            value = result[field]

            # CRITICAL REGRESSION CHECK: Duration values should be exportable
            # Should be numeric or string, not complex datatype
            self.assertIsInstance(
                value,
                (int, float, str, type(None)),
                f"REGRESSION BUG: Duration field {field} has non-exportable type: {type(value)}",
            )

            # Should not be NaN or complex object
            if isinstance(value, int | float):
                self.assertFalse(
                    np.isnan(value),
                    f"Duration field {field} should not be NaN",
                )

    def test_prevent_signal_entry_always_true_export(self):
        """REGRESSION TEST: Prevent Signal Entry always being 'true' in CSV."""
        # Historical bug: Signal Entry field was always 'true' for every row
        # regardless of actual signal conditions

        # Create multiple results with different conditions
        test_cases = [
            {"atr_length": 5, "atr_multiplier": 1.5},
            {"atr_length": 10, "atr_multiplier": 2.0},
            {"atr_length": 20, "atr_multiplier": 3.0},
        ]

        results = []
        for case in test_cases:
            result = analyze_params(
                self.regression_test_data,
                atr_length=case["atr_length"],
                atr_multiplier=case["atr_multiplier"],
                ticker="SIGNAL_ENTRY_TEST",
                log=self.test_log,
            )
            results.append(result)

        # Check Signal Entry values across results
        signal_entries = [r.get("Signal Entry", "missing") for r in results]

        if any(entry != "missing" for entry in signal_entries):
            # If Signal Entry field exists, it should not always be the same value
            unique_entries = {str(entry).lower() for entry in signal_entries}

            # CRITICAL REGRESSION CHECK: Should have variety in Signal Entry values
            # In realistic scenarios with different parameters, some should be true, some false
            self.assertTrue(
                len(unique_entries) > 1 or "false" in unique_entries,
                "REGRESSION BUG: Signal Entry is always 'true' across different conditions",
            )

    def test_prevent_atr_calculation_regression(self):
        """REGRESSION TEST: Prevent ATR calculation algorithm regression."""
        # Ensure ATR calculation remains mathematically correct

        # Test with controlled data for which we can calculate ATR manually
        controlled_dates = pd.date_range("2023-01-01", periods=20, freq="D")
        controlled_prices = [
            100,
            102,
            101,
            105,
            103,
            107,
            104,
            108,
            106,
            110,
            108,
            112,
            109,
            113,
            111,
            115,
            112,
            116,
            114,
            118,
        ]

        controlled_data = pd.DataFrame(
            {
                "Date": controlled_dates,
                "Open": controlled_prices,
                "High": [p + 1 for p in controlled_prices],
                "Low": [p - 1 for p in controlled_prices],
                "Close": controlled_prices,
                "Volume": [100000] * 20,
            },
        ).set_index("Date")

        # Calculate ATR with our implementation
        atr_length = 5
        atr_series = calculate_atr(controlled_data, atr_length)

        # Manual calculation for validation (simplified check)
        manual_tr = []
        for i in range(1, len(controlled_data)):
            high = controlled_data["High"].iloc[i]
            low = controlled_data["Low"].iloc[i]
            prev_close = controlled_data["Close"].iloc[i - 1]

            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            manual_tr.append(tr)

        # Check that our ATR values are reasonable
        atr_values = atr_series.dropna()

        self.assertGreater(len(atr_values), 0, "ATR calculation should produce values")
        self.assertTrue((atr_values > 0).all(), "All ATR values should be positive")

        # ATR should be in reasonable range relative to price movements
        price_range = controlled_data["High"].max() - controlled_data["Low"].min()
        max_atr = atr_values.max()

        self.assertLess(
            max_atr,
            price_range,
            "ATR values should be reasonable relative to price range",
        )

    def test_prevent_position_calculation_regression(self):
        """REGRESSION TEST: Prevent position calculation regression."""
        # Ensure position-aware trailing stop behavior remains correct

        signals_df = generate_signals(self.regression_test_data, 10, 2.0)

        # Check position-aware behavior
        prev_trailing_stop = None
        in_position = False

        for i in range(len(signals_df)):
            row = signals_df.iloc[i]
            signal = row["Signal"]
            trailing_stop = row["ATR_Trailing_Stop"]

            if pd.isna(trailing_stop):
                continue

            # Track position state
            if not in_position and signal == 1:
                in_position = True
            elif in_position and signal == 0:
                in_position = False

            # CRITICAL REGRESSION CHECK: When in position, trailing stop should not decrease
            if (
                in_position
                and prev_trailing_stop is not None
                and not pd.isna(prev_trailing_stop)
            ):
                self.assertGreaterEqual(
                    trailing_stop,
                    prev_trailing_stop - 1e-6,  # Allow small floating point tolerance
                    f"REGRESSION BUG: Trailing stop decreased while in position at index {i}",
                )

            prev_trailing_stop = trailing_stop


if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)
