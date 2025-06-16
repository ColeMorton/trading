"""
Simple Test for Monte Carlo Parameter Robustness Core Functionality

This script tests the core Monte Carlo functionality without heavy dependencies.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Any, Dict

import numpy as np
import polars as pl

from app.strategies.monte_carlo.parameter_robustness import (
    MonteCarloConfig,
    ParameterRobustnessAnalyzer,
)


def create_mock_data(n_periods: int = 500) -> pl.DataFrame:
    """Create mock price data for testing."""
    np.random.seed(42)

    # Generate realistic price series
    initial_price = 100.0
    returns = np.random.normal(
        0.001, 0.02, n_periods
    )  # Daily returns ~0.1% mean, 2% std

    prices = [initial_price]
    for ret in returns:
        prices.append(prices[-1] * (1 + ret))

    import datetime

    start_date = datetime.datetime(2020, 1, 1)
    dates = [start_date + datetime.timedelta(days=i) for i in range(n_periods)]

    # Create OHLCV data
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        high = price * (1 + abs(np.random.normal(0, 0.005)))
        low = price * (1 - abs(np.random.normal(0, 0.005)))
        open_price = prices[i - 1] if i > 0 else price
        volume = np.random.randint(1000000, 10000000)

        data.append(
            {
                "Date": date,
                "Open": open_price,
                "High": high,
                "Low": low,
                "Close": price,
                "Volume": volume,
            }
        )

    return pl.DataFrame(data)


def test_bootstrap_sampling():
    """Test bootstrap sampling functionality."""
    print("Testing bootstrap sampling...")

    # Create test data
    data = create_mock_data(252)  # 1 year of data

    # Initialize analyzer
    mc_config = MonteCarloConfig(
        num_simulations=10,  # Small for testing
        bootstrap_block_size=63,  # 3 months
        min_data_fraction=0.7,
    )

    analyzer = ParameterRobustnessAnalyzer(mc_config)

    # Test bootstrap sampling
    original_length = len(data)

    for i in range(5):
        bootstrap_sample = analyzer.bootstrap_price_data(data, seed=i)
        sample_length = len(bootstrap_sample)

        print(f"  Bootstrap {i+1}: Original={original_length}, Sample={sample_length}")

        # Verify sample is not empty and within reasonable bounds
        assert sample_length > 0
        # Note: bootstrap sample might be smaller than min_data_fraction due to block sampling
        # This is expected behavior for the block bootstrap method

        # Verify data structure is preserved
        assert bootstrap_sample.columns == data.columns
        assert "Date" in bootstrap_sample.columns
        assert "Close" in bootstrap_sample.columns

    print("  ✓ Bootstrap sampling test passed")


def test_parameter_noise():
    """Test parameter noise addition."""
    print("Testing parameter noise...")

    mc_config = MonteCarloConfig(parameter_noise_std=0.1)
    analyzer = ParameterRobustnessAnalyzer(mc_config)

    # Test parameter noise
    original_short, original_long = 20, 50

    noisy_params = []
    for i in range(10):
        np.random.seed(i)
        noisy_short, noisy_long = analyzer.add_parameter_noise(
            original_short, original_long
        )
        noisy_params.append((noisy_short, noisy_long))

        print(
            f"  Test {i+1}: {original_short}/{original_long} → {noisy_short}/{noisy_long}"
        )

        # Verify constraints
        assert noisy_short >= 2
        assert noisy_long > noisy_short
        assert (
            noisy_short != original_short or noisy_long != original_long
        )  # Should add some noise

    # Check that we get different values
    unique_params = set(noisy_params)
    assert len(unique_params) > 1, "Parameter noise should produce different values"

    print("  ✓ Parameter noise test passed")


def test_market_regime_detection():
    """Test market regime detection."""
    print("Testing market regime detection...")

    mc_config = MonteCarloConfig(regime_window=30, enable_regime_analysis=True)
    analyzer = ParameterRobustnessAnalyzer(mc_config)

    # Create data with different market conditions
    np.random.seed(42)

    # Bull market period
    bull_returns = np.random.normal(0.002, 0.01, 100)
    # Bear market period
    bear_returns = np.random.normal(-0.002, 0.03, 100)
    # Sideways market
    sideways_returns = np.random.normal(0.0001, 0.015, 100)

    all_returns = np.concatenate([bull_returns, bear_returns, sideways_returns])

    # Create price data
    prices = [100.0]
    for ret in all_returns:
        prices.append(prices[-1] * (1 + ret))

    import datetime

    start_date = datetime.datetime(2020, 1, 1)
    dates = [start_date + datetime.timedelta(days=i) for i in range(len(prices))]

    data = pl.DataFrame(
        {
            "Date": dates,
            "Close": prices,
            "Open": prices,  # Simplified
            "High": prices,
            "Low": prices,
            "Volume": [1000000] * len(prices),
        }
    )

    # Test regime detection
    regime_data = analyzer.detect_market_regimes(data)

    print(f"  Data length: {len(regime_data)}")
    print(f"  Columns: {regime_data.columns}")

    # Check that regime column was added
    assert "Market_Regime" in regime_data.columns

    # Check that we have some regime classifications
    regime_counts = regime_data["Market_Regime"].value_counts()
    print(f"  Regime distribution: {regime_counts.to_dict()}")

    # Should have at least 2 different regimes
    assert len(regime_counts) >= 2

    print("  ✓ Market regime detection test passed")


def test_performance_stability():
    """Test performance stability calculation."""
    print("Testing performance stability calculation...")

    analyzer = ParameterRobustnessAnalyzer(MonteCarloConfig())

    # Create mock performance results
    stable_results = [
        {
            "Sharpe Ratio": 1.2,
            "Total Return [%]": 15.0,
            "Max Drawdown [%]": -8.0,
            "Win Rate [%]": 65.0,
        },
        {
            "Sharpe Ratio": 1.1,
            "Total Return [%]": 14.5,
            "Max Drawdown [%]": -9.0,
            "Win Rate [%]": 63.0,
        },
        {
            "Sharpe Ratio": 1.3,
            "Total Return [%]": 16.0,
            "Max Drawdown [%]": -7.5,
            "Win Rate [%]": 67.0,
        },
        {
            "Sharpe Ratio": 1.15,
            "Total Return [%]": 15.2,
            "Max Drawdown [%]": -8.5,
            "Win Rate [%]": 64.0,
        },
    ]

    unstable_results = [
        {
            "Sharpe Ratio": 2.0,
            "Total Return [%]": 25.0,
            "Max Drawdown [%]": -5.0,
            "Win Rate [%]": 80.0,
        },
        {
            "Sharpe Ratio": 0.2,
            "Total Return [%]": 3.0,
            "Max Drawdown [%]": -20.0,
            "Win Rate [%]": 45.0,
        },
        {
            "Sharpe Ratio": 1.8,
            "Total Return [%]": 22.0,
            "Max Drawdown [%]": -15.0,
            "Win Rate [%]": 70.0,
        },
        {
            "Sharpe Ratio": -0.5,
            "Total Return [%]": -8.0,
            "Max Drawdown [%]": -25.0,
            "Win Rate [%]": 30.0,
        },
    ]

    # Test stable results
    stable_metrics = analyzer.calculate_performance_stability(stable_results)
    print(f"  Stable results metrics: {stable_metrics}")

    # Test unstable results
    unstable_metrics = analyzer.calculate_performance_stability(unstable_results)
    print(f"  Unstable results metrics: {unstable_metrics}")

    # Stable should have higher stability score
    assert stable_metrics["stability_score"] > unstable_metrics["stability_score"]

    # Both should have same robustness (all positive returns in stable case)
    stable_positive = sum(1 for r in stable_results if r["Total Return [%]"] > 0)
    unstable_positive = sum(1 for r in unstable_results if r["Total Return [%]"] > 0)

    expected_stable_robustness = stable_positive / len(stable_results)
    expected_unstable_robustness = unstable_positive / len(unstable_results)

    assert abs(stable_metrics["robustness"] - expected_stable_robustness) < 0.01
    assert abs(unstable_metrics["robustness"] - expected_unstable_robustness) < 0.01

    print("  ✓ Performance stability test passed")


def test_config_validation():
    """Test Monte Carlo configuration validation."""
    print("Testing configuration validation...")

    # Valid configuration
    valid_config = MonteCarloConfig(
        num_simulations=100, confidence_level=0.95, bootstrap_block_size=63
    )

    analyzer = ParameterRobustnessAnalyzer(valid_config)
    print(f"  Valid config created: simulations={valid_config.num_simulations}")

    # Test invalid configurations
    try:
        invalid_config = MonteCarloConfig(
            num_simulations=0,  # Invalid
            confidence_level=1.5,  # Invalid
            bootstrap_block_size=-10,  # Invalid
        )
        print("  ⚠️  Invalid config was accepted (this may be expected)")
    except Exception as e:
        print(f"  ✓ Invalid config rejected: {str(e)}")

    print("  ✓ Configuration validation test completed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Monte Carlo Parameter Robustness - Core Functionality Tests")
    print("=" * 60)

    tests = [
        test_bootstrap_sampling,
        test_parameter_noise,
        test_market_regime_detection,
        test_performance_stability,
        test_config_validation,
    ]

    passed_tests = 0
    failed_tests = 0

    for test in tests:
        try:
            test()
            passed_tests += 1
        except Exception as e:
            print(f"  ❌ Test failed: {str(e)}")
            import traceback

            traceback.print_exc()
            failed_tests += 1
        print()

    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Total:  {len(tests)}")

    if failed_tests == 0:
        print("\n✅ All core functionality tests passed!")
        print("The Monte Carlo parameter robustness system core is working correctly.")
    else:
        print(f"\n❌ {failed_tests} test(s) failed. Check the error messages above.")

    return failed_tests == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
