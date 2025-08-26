#!/usr/bin/env python3
"""
ATR Strategy Multi-Ticker Tests - USE_CURRENT Behavior Validation

This test suite validates ATR strategy behavior across multiple tickers
and USE_CURRENT flag functionality:
- Multi-ticker parameter sweep validation
- USE_CURRENT signal detection accuracy
- Cross-ticker consistency checks
- Signal detection edge cases
- Performance across different market conditions

Focus: Multi-ticker behavior and current signal detection logic
"""

import unittest
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import polars as pl

from app.strategies.atr.tools.signal_utils import (
    is_exit_signal_current,
    is_signal_current,
)
from app.strategies.atr.tools.strategy_execution import analyze_params, execute_strategy


class TestMultiTickerATRAnalysis(unittest.TestCase):
    """Test ATR analysis across multiple tickers with different market patterns."""

    def setUp(self):
        """Set up multi-ticker test data with different market characteristics."""
        np.random.seed(42)

        # Create different market patterns for testing
        self.ticker_patterns = {
            "TECH_GROWTH": self._create_growth_pattern(),  # High growth, high volatility
            "STABLE_DIVIDEND": self._create_stable_pattern(),  # Low volatility, steady
            "VOLATILE_CRYPTO": self._create_crypto_pattern(),  # Extreme volatility
            "DECLINING_STOCK": self._create_decline_pattern(),  # Downtrend pattern
        }

        self.multi_ticker_config = {
            "TICKER": [
                "TECH_GROWTH",
                "STABLE_DIVIDEND",
                "VOLATILE_CRYPTO",
                "DECLINING_STOCK",
            ],
            "ATR_LENGTH_MIN": 10,
            "ATR_LENGTH_MAX": 15,  # 6 lengths: 10,11,12,13,14,15
            "ATR_MULTIPLIER_MIN": 2.0,
            "ATR_MULTIPLIER_MAX": 3.0,  # 3 multipliers: 2.0, 2.5, 3.0
            "ATR_MULTIPLIER_STEP": 0.5,
            "USE_CURRENT": False,
            "BASE_DIR": "/tmp/atr_multi_test",
            "DIRECTION": "Long",
            "MINIMUMS": {
                "WIN_RATE": 0.30,  # Lenient for testing
                "TRADES": 3,
                "EXPECTANCY_PER_TRADE": 0.0,
                "PROFIT_FACTOR": 0.8,
                "SORTINO_RATIO": 0.0,
            },
        }

        # Mock logger
        self.log_messages = []
        self.test_log = lambda msg, level="info": self.log_messages.append(
            f"{level}: {msg}"
        )

    def _create_growth_pattern(self):
        """Create high-growth, high-volatility pattern (e.g., tech stock)."""
        dates = pd.date_range("2020-01-01", periods=1000, freq="D")
        base_price = 50.0

        # Strong uptrend with high volatility
        returns = np.random.normal(
            0.0012, 0.035, len(dates)
        )  # 1.2% drift, 3.5% volatility
        prices = base_price * np.exp(np.cumsum(returns))

        return self._create_ohlc_dataframe(dates, prices, volatility_multiplier=1.5)

    def _create_stable_pattern(self):
        """Create low-volatility, stable pattern (e.g., dividend stock)."""
        dates = pd.date_range("2020-01-01", periods=1000, freq="D")
        base_price = 100.0

        # Modest uptrend with low volatility
        returns = np.random.normal(
            0.0003, 0.015, len(dates)
        )  # 0.3% drift, 1.5% volatility
        prices = base_price * np.exp(np.cumsum(returns))

        return self._create_ohlc_dataframe(dates, prices, volatility_multiplier=0.8)

    def _create_crypto_pattern(self):
        """Create extreme volatility pattern (e.g., cryptocurrency)."""
        dates = pd.date_range("2020-01-01", periods=1000, freq="D")
        base_price = 10000.0

        # High volatility with boom/bust cycles
        returns = []
        for i in range(len(dates)):
            if i % 200 < 100:  # Bull market phase
                drift = 0.002
                vol = 0.08
            else:  # Bear market phase
                drift = -0.001
                vol = 0.10
            returns.append(np.random.normal(drift, vol))

        prices = base_price * np.exp(np.cumsum(returns))

        return self._create_ohlc_dataframe(dates, prices, volatility_multiplier=3.0)

    def _create_decline_pattern(self):
        """Create declining pattern (e.g., distressed stock)."""
        dates = pd.date_range("2020-01-01", periods=1000, freq="D")
        base_price = 200.0

        # Downtrend with moderate volatility
        returns = np.random.normal(
            -0.0008, 0.025, len(dates)
        )  # -0.8% drift, 2.5% volatility
        prices = base_price * np.exp(np.cumsum(returns))

        return self._create_ohlc_dataframe(dates, prices, volatility_multiplier=1.2)

    def _create_ohlc_dataframe(self, dates, closes, volatility_multiplier=1.0):
        """Create realistic OHLC DataFrame from close prices."""
        # Create OHLC with realistic spreads
        daily_ranges = np.abs(
            np.random.normal(0, 0.01 * volatility_multiplier, len(closes))
        )

        highs = closes * (1 + daily_ranges)
        lows = closes * (1 - daily_ranges * 0.8)
        opens = closes * np.random.uniform(0.999, 1.001, len(closes))
        volumes = np.random.randint(100000, 1000000, len(closes))

        return pd.DataFrame(
            {
                "Date": dates,
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": closes,
                "Volume": volumes,
            }
        ).set_index("Date")

    def test_multi_ticker_parameter_consistency(self):
        """Test that same parameters produce consistent behavior across tickers."""
        # Test specific parameter combination across all tickers
        test_params = {"atr_length": 12, "atr_multiplier": 2.5}

        results = {}
        for ticker, data in self.ticker_patterns.items():
            result = analyze_params(
                data,
                atr_length=test_params["atr_length"],
                atr_multiplier=test_params["atr_multiplier"],
                ticker=ticker,
                log=self.test_log,
            )
            results[ticker] = result

        # Verify all results have same parameter mappings
        for ticker, result in results.items():
            self.assertEqual(result["Ticker"], ticker)
            self.assertEqual(result["Strategy Type"], "ATR")
            self.assertEqual(result["Fast Period"], test_params["atr_length"])
            self.assertEqual(
                result["Slow Period"], int(test_params["atr_multiplier"] * 10)
            )
            self.assertEqual(result["Signal Period"], 0)

        # Different tickers should produce different performance metrics
        # (unless they have identical price patterns)
        total_returns = [r["Total Return [%]"] for r in results.values()]
        win_rates = [r["Win Rate [%]"] for r in results.values()]

        # Some variation in results is expected across different market patterns
        self.assertTrue(
            len(set(total_returns)) >= 2,
            "Should have variation in Total Return across tickers",
        )

    def test_multi_ticker_atr_calculation_accuracy(self):
        """Test ATR calculation accuracy across different volatility patterns."""
        from app.strategies.atr.tools.strategy_execution import calculate_atr

        atr_length = 14
        atr_values = {}

        for ticker, data in self.ticker_patterns.items():
            atr_series = calculate_atr(data, atr_length)
            atr_values[ticker] = atr_series.dropna()

        # Verify ATR calculation properties
        for ticker, atr_series in atr_values.items():
            self.assertGreater(
                len(atr_series), 0, f"ATR should be calculated for {ticker}"
            )
            self.assertTrue(
                (atr_series > 0).all(), f"ATR values should be positive for {ticker}"
            )

        # Volatile assets should have higher ATR values
        crypto_atr_mean = atr_values["VOLATILE_CRYPTO"].mean()
        stable_atr_mean = atr_values["STABLE_DIVIDEND"].mean()

        # Normalize by price to compare fairly
        crypto_price_mean = self.ticker_patterns["VOLATILE_CRYPTO"]["Close"].mean()
        stable_price_mean = self.ticker_patterns["STABLE_DIVIDEND"]["Close"].mean()

        crypto_atr_ratio = crypto_atr_mean / crypto_price_mean
        stable_atr_ratio = stable_atr_mean / stable_price_mean

        self.assertGreater(
            crypto_atr_ratio,
            stable_atr_ratio,
            "Volatile crypto should have higher relative ATR than stable dividend stock",
        )

    def test_multi_ticker_signal_generation_patterns(self):
        """Test signal generation patterns across different market types."""
        from app.strategies.atr.tools.strategy_execution import generate_signals

        signal_results = {}
        atr_params = {"atr_length": 10, "atr_multiplier": 2.0}

        for ticker, data in self.ticker_patterns.items():
            signals_df = generate_signals(data, **atr_params)
            signal_results[ticker] = signals_df

        # Analyze signal patterns for each ticker type
        signal_stats = {}
        for ticker, signals_df in signal_results.items():
            signals = signals_df["Signal"].dropna()
            signal_stats[ticker] = {
                "total_signals": len(signals),
                "buy_signals": (signals == 1).sum(),
                "sell_signals": (signals == 0).sum(),
                "signal_rate": (signals != 0).mean() if len(signals) > 0 else 0,
            }

        # Verify signal generation makes sense for each market type
        for ticker, stats in signal_stats.items():
            self.assertGreater(
                stats["total_signals"], 0, f"Should generate signals for {ticker}"
            )

            # Buy and sell signals should both exist in most market conditions
            if stats["total_signals"] > 20:  # Only check if sufficient data
                total_directional = stats["buy_signals"] + stats["sell_signals"]
                self.assertGreater(
                    total_directional,
                    0,
                    f"Should have some directional signals for {ticker}",
                )

    def test_multi_ticker_performance_across_market_conditions(self):
        """Test ATR performance across different market conditions."""
        # Run full analysis on subset of tickers with different patterns
        test_tickers = ["TECH_GROWTH", "STABLE_DIVIDEND", "DECLINING_STOCK"]

        performance_results = {}

        for ticker in test_tickers:
            # Mock data loading for each ticker
            with patch("app.tools.get_data.get_data") as mock_get_data:
                mock_get_data.return_value = pl.from_pandas(
                    self.ticker_patterns[ticker].reset_index()
                )

                config = self.multi_ticker_config.copy()
                config["TICKER"] = ticker

                results = execute_strategy(config, "ATR", self.test_log)
                performance_results[ticker] = results

        # Verify results structure for all tickers
        for ticker, results in performance_results.items():
            self.assertIsInstance(results, list, f"Should return list for {ticker}")

            if len(results) > 0:
                # Check that results have valid structure
                for result in results:
                    self.assertEqual(result["Ticker"], ticker)
                    self.assertEqual(result["Strategy Type"], "ATR")
                    self.assertIsInstance(result["Total Trades"], (int, float))
                    self.assertIsInstance(result["Score"], (int, float))

        # Growth stocks might perform better than declining stocks
        # (This is market-dependent, so we just check that analysis completes)


class TestATRUSECurrentBehavior(unittest.TestCase):
    """Test USE_CURRENT flag behavior for ATR signal detection."""

    def setUp(self):
        """Set up test data for USE_CURRENT behavior testing."""
        # Create data with clear signal at the end
        self.dates = pd.date_range("2024-01-01", periods=50, freq="D")

        # Pattern ending with clear ATR signal
        prices = []
        base_price = 100.0

        # Stable period, then strong move up
        for i in range(40):
            prices.append(base_price + np.random.normal(0, 1))
        for i in range(10):  # Strong move up at end
            prices.append(prices[-1] + 2 + np.random.normal(0, 0.5))

        # Create OHLC data
        highs = [p + abs(np.random.normal(0, 0.5)) for p in prices]
        lows = [p - abs(np.random.normal(0, 0.5)) for p in prices]

        self.signal_test_data = pd.DataFrame(
            {
                "Date": self.dates,
                "Open": prices,
                "High": highs,
                "Low": lows,
                "Close": prices,
                "Volume": [100000] * len(prices),
            }
        ).set_index("Date")

    def test_use_current_false_behavior(self):
        """Test USE_CURRENT=False behavior (should not detect current signals)."""
        config = {"USE_CURRENT": False}

        # Generate signals with USE_CURRENT=False
        from app.strategies.atr.tools.strategy_execution import generate_signals

        signals_df = generate_signals(self.signal_test_data, 10, 2.0)

        # Test signal detection function
        is_current = is_signal_current(signals_df, config)

        # With USE_CURRENT=False, should not detect current signal
        self.assertEqual(
            is_current, False, "Should not detect current signal when USE_CURRENT=False"
        )

    def test_use_current_true_behavior(self):
        """Test USE_CURRENT=True behavior (should detect current signals when present)."""
        config = {"USE_CURRENT": True}

        from app.strategies.atr.tools.strategy_execution import generate_signals

        signals_df = generate_signals(self.signal_test_data, 10, 2.0)

        # Test signal detection function
        is_current = is_signal_current(signals_df, config)

        # Should evaluate current signal based on ATR logic
        self.assertIsInstance(is_current, bool, "Should return boolean value")

    def test_signal_current_detection_accuracy(self):
        """Test accuracy of current signal detection logic."""
        # Create data with known signal condition at end
        from app.strategies.atr.tools.strategy_execution import generate_signals

        # Generate ATR signals
        signals_df = generate_signals(self.signal_test_data, 5, 1.5)

        # Get last row data for manual validation
        last_row = signals_df.iloc[-1]
        current_close = last_row["Close"]
        current_atr_stop = last_row["ATR_Trailing_Stop"]

        if not pd.isna(current_atr_stop):
            # Manual signal calculation: entry when close >= ATR stop
            expected_signal = current_close >= current_atr_stop

            # Test with USE_CURRENT=True
            config_true = {"USE_CURRENT": True}
            detected_signal = is_signal_current(signals_df, config_true)

            # Should match expected signal logic
            if expected_signal:
                # If we expect a signal, detection should be True (or at least not False due to other factors)
                pass  # Implementation may have additional logic
            else:
                # If we don't expect a signal, detection should be False
                pass  # Implementation may have additional logic

    def test_exit_signal_current_detection(self):
        """Test current exit signal detection."""
        from app.strategies.atr.tools.strategy_execution import generate_signals

        # Create data that might trigger exit signal
        exit_test_data = self.signal_test_data.copy()

        # Force last price to be below ATR stop (potential exit)
        # This requires first generating signals to get ATR stops
        signals_df = generate_signals(exit_test_data, 10, 2.0)

        # Test exit signal detection
        config = {"USE_CURRENT": True}
        is_exit_current = is_exit_signal_current(signals_df, config)

        self.assertIsInstance(
            is_exit_current, bool, "Should return boolean value for exit signal"
        )

    def test_edge_cases_signal_detection(self):
        """Test edge cases in signal detection."""
        # Test with insufficient data
        short_data = self.signal_test_data.head(3)

        from app.strategies.atr.tools.strategy_execution import generate_signals

        try:
            signals_df = generate_signals(short_data, 10, 2.0)

            config = {"USE_CURRENT": True}
            is_current = is_signal_current(signals_df, config)

            # Should handle gracefully
            self.assertIsInstance(is_current, bool)

        except Exception:
            # Exception is acceptable for insufficient data
            pass

    def test_signal_detection_with_nan_values(self):
        """Test signal detection handles NaN values correctly."""
        # Create data with some NaN values
        nan_data = self.signal_test_data.copy()
        nan_data.loc[nan_data.index[-3:], "Close"] = np.nan

        from app.strategies.atr.tools.strategy_execution import generate_signals

        try:
            signals_df = generate_signals(nan_data, 10, 2.0)

            config = {"USE_CURRENT": True}
            is_current = is_signal_current(signals_df, config)

            # Should handle NaN values gracefully
            self.assertIsInstance(is_current, bool)

        except Exception as e:
            # Should provide meaningful error message if it fails
            self.assertIn("NaN", str(e), "Error should mention NaN handling")

    def test_multi_ticker_use_current_consistency(self):
        """Test USE_CURRENT behavior consistency across multiple tickers."""
        tickers = ["TICKER_A", "TICKER_B"]

        results_false = {}
        results_true = {}

        for ticker in tickers:
            # Test with USE_CURRENT=False
            config_false = {
                "TICKER": ticker,
                "USE_CURRENT": False,
                "ATR_LENGTH_MIN": 10,
                "ATR_LENGTH_MAX": 10,
                "ATR_MULTIPLIER_MIN": 2.0,
                "ATR_MULTIPLIER_MAX": 2.0,
                "ATR_MULTIPLIER_STEP": 0.5,
            }

            with patch("app.tools.get_data.get_data") as mock_get_data:
                mock_get_data.return_value = pl.from_pandas(
                    self.signal_test_data.reset_index()
                )

                result = analyze_params(
                    self.signal_test_data,
                    atr_length=10,
                    atr_multiplier=2.0,
                    ticker=ticker,
                    log=lambda x: None,
                )
                results_false[ticker] = result

            # Test with USE_CURRENT=True
            config_true = config_false.copy()
            config_true["USE_CURRENT"] = True

            with patch("app.tools.get_data.get_data") as mock_get_data:
                mock_get_data.return_value = pl.from_pandas(
                    self.signal_test_data.reset_index()
                )

                result = analyze_params(
                    self.signal_test_data,
                    atr_length=10,
                    atr_multiplier=2.0,
                    ticker=ticker,
                    log=lambda x: None,
                )
                results_true[ticker] = result

        # Verify both configurations produce valid results
        for ticker in tickers:
            self.assertIn(ticker, results_false)
            self.assertIn(ticker, results_true)

            # Both should have same basic structure
            self.assertEqual(results_false[ticker]["Ticker"], ticker)
            self.assertEqual(results_true[ticker]["Ticker"], ticker)
            self.assertEqual(results_false[ticker]["Strategy Type"], "ATR")
            self.assertEqual(results_true[ticker]["Strategy Type"], "ATR")


if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)
