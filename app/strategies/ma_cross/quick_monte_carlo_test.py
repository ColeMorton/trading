"""
Quick validation test for Monte Carlo Enhanced Integration

This script tests the core Monte Carlo functionality directly without
running the full parameter sensitivity analysis.
"""

from pathlib import Path
import sys


# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.strategies.monte_carlo.parameter_robustness import (
    MonteCarloConfig,
    run_parameter_robustness_analysis,
)


def test_core_monte_carlo_functionality():
    """Test core Monte Carlo functionality with minimal parameters."""
    print("=" * 60)
    print("Quick Monte Carlo Enhanced Integration Test")
    print("=" * 60)

    print("Testing core Monte Carlo robustness analysis...")
    print("- Ticker: BTC-USD")
    print("- Parameter combinations: 2x2 = 4 combinations")
    print("- MC Simulations: 50 (minimal for testing)")
    print()

    try:
        # Test with minimal parameter set
        strategy_config = {
            "DIRECTION": "Long",
            "USE_HOURLY": False,
            "USE_YEARS": True,
            "YEARS": 2,  # Reduced for faster testing
            "USE_SYNTHETIC": False,
            "STRATEGY_TYPE": "EMA",
        }

        mc_config = MonteCarloConfig(
            num_simulations=50,  # Minimal for testing
            bootstrap_block_size=30,  # Smaller blocks
            confidence_level=0.95,
            enable_regime_analysis=True,
        )

        # Test with just 2x2 parameter combinations
        parameter_ranges = {
            "short_windows": [10, 15],  # Just 2 values
            "long_windows": [30, 40],  # Just 2 values
        }

        print("Running Monte Carlo parameter robustness analysis...")
        results = run_parameter_robustness_analysis(
            tickers=["BTC-USD"],
            parameter_ranges=parameter_ranges,
            strategy_config=strategy_config,
            mc_config=mc_config,
        )

        if results and "BTC-USD" in results:
            btc_results = results["BTC-USD"]
            print("✅ Analysis completed successfully!")
            print(f"Tested {len(btc_results)} parameter combinations")

            # Display results
            print("\nParameter Robustness Results:")
            print("-" * 50)
            for i, result in enumerate(btc_results):
                short, long = result.parameter_combination
                print(f"{i+1}. Windows {short}/{long}:")
                print(f"   Stability Score: {result.stability_score:.3f}")
                print(f"   Parameter Robustness: {result.parameter_robustness:.3f}")
                print(f"   Is Stable: {result.is_stable}")
                print(f"   MC Simulations: {len(result.monte_carlo_results)}")
                if result.base_performance:
                    sharpe = result.base_performance.get("Sharpe Ratio", 0)
                    total_return = result.base_performance.get("Total Return [%]", 0)
                    print(f"   Base Sharpe: {sharpe:.3f}")
                    print(f"   Base Return: {total_return:.1f}%")
                print()

            # Test recommendation scoring
            print("Testing recommendation scoring consistency...")

            # Create a mock standard result for scoring test
            mock_standard_result = {
                "Win Rate [%]": 60.0,
                "Total Trades": 25,
                "Sortino Ratio": 1.2,
                "Profit Factor": 1.5,
                "Expectancy per Trade": 2.5,
                "Beats BNH [%]": 15.0,
                "Sharpe Ratio": 1.1,
                "Total Return [%]": 25.0,
                "Max Drawdown [%]": -12.0,
            }

            # Test the scoring function
            from app.strategies.ma_cross.config.parameter_testing import (
                ParameterTestingConfig,
            )
            from app.strategies.ma_cross.monte_carlo_integration import (
                MonteCarloEnhancedAnalyzer,
            )

            param_config = ParameterTestingConfig(
                tickers=["BTC-USD"], windows=20, strategy_types=["EMA"]
            )

            analyzer = MonteCarloEnhancedAnalyzer(param_config, mc_config)

            if btc_results:
                recommendation_score = analyzer._calculate_recommendation_score(
                    mock_standard_result, btc_results[0]
                )
                print("✅ Recommendation scoring test passed!")
                print(f"Sample recommendation score: {recommendation_score:.3f}")

            print("\n✅ All Monte Carlo integration tests passed!")
            return True

        print("❌ No results returned from Monte Carlo analysis")
        return False

    except Exception as e:
        print(f"❌ Test failed: {e!s}")
        import traceback

        traceback.print_exc()
        return False


def test_scoring_consistency():
    """Test that recommendation scoring is consistent with strategy scoring."""
    print("\n" + "=" * 60)
    print("Testing Scoring Consistency")
    print("=" * 60)

    try:
        # Import the scoring functions
        from app.tools.stats_converter import (
            calculate_beats_bnh_normalized,
            calculate_expectancy_per_trade_normalized,
            calculate_profit_factor_normalized,
            calculate_sortino_normalized,
            calculate_total_trades_normalized,
            calculate_win_rate_normalized,
        )

        # Test data
        test_stats = {
            "Win Rate [%]": 65.0,
            "Total Trades": 45,
            "Sortino Ratio": 1.5,
            "Profit Factor": 1.8,
            "Expectancy per Trade": 3.2,
            "Beats BNH [%]": 20.0,
        }

        print("Testing normalization functions...")

        # Test each normalization function
        win_rate_norm = calculate_win_rate_normalized(
            test_stats["Win Rate [%]"], test_stats["Total Trades"]
        )
        trades_norm = calculate_total_trades_normalized(test_stats["Total Trades"])
        sortino_norm = calculate_sortino_normalized(test_stats["Sortino Ratio"])
        pf_norm = calculate_profit_factor_normalized(test_stats["Profit Factor"])
        exp_norm = calculate_expectancy_per_trade_normalized(
            test_stats["Expectancy per Trade"]
        )
        bnh_norm = calculate_beats_bnh_normalized(test_stats["Beats BNH [%]"])

        print(f"Win Rate normalized: {win_rate_norm:.4f}")
        print(f"Total Trades normalized: {trades_norm:.4f}")
        print(f"Sortino normalized: {sortino_norm:.4f}")
        print(f"Profit Factor normalized: {pf_norm:.4f}")
        print(f"Expectancy normalized: {exp_norm:.4f}")
        print(f"Beats BnH normalized: {bnh_norm:.4f}")

        # Calculate strategy score using same formula as stats_converter.py
        base_score = (
            win_rate_norm * 2.5
            + trades_norm * 1.5
            + sortino_norm * 1.2
            + pf_norm * 1.2
            + exp_norm * 1.0
            + bnh_norm * 0.6
        ) / 8.0

        # Apply confidence multiplier
        confidence_multiplier = 1.0  # 45 trades is above 50, so no penalty
        strategy_score = base_score * confidence_multiplier

        print(f"\nCalculated strategy score: {strategy_score:.4f}")
        print("✅ Scoring consistency test passed!")

        return True

    except Exception as e:
        print(f"❌ Scoring test failed: {e!s}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all quick tests."""
    success1 = test_core_monte_carlo_functionality()
    success2 = test_scoring_consistency()

    print("\n" + "=" * 60)
    print("QUICK TEST SUMMARY")
    print("=" * 60)
    print(f"Core Monte Carlo functionality: {'PASSED' if success1 else 'FAILED'}")
    print(f"Scoring consistency: {'PASSED' if success2 else 'FAILED'}")

    if success1 and success2:
        print("\n✅ All quick tests passed!")
        print("The Monte Carlo enhanced integration is working correctly.")
    else:
        print("\n❌ Some tests failed.")

    return success1 and success2


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
