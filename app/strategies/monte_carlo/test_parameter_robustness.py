"""
Test Script for Monte Carlo Parameter Robustness Testing

This script demonstrates the Monte Carlo parameter robustness testing system
with a simple example using BTC-USD data.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.strategies.monte_carlo.parameter_robustness import (
    MonteCarloConfig,
    run_parameter_robustness_analysis,
)
from app.strategies.monte_carlo.parameter_visualization import (
    ParameterStabilityVisualizer,
)


def test_basic_parameter_robustness():
    """Test basic parameter robustness analysis with reduced parameters."""
    print("=" * 60)
    print("Monte Carlo Parameter Robustness Testing - Basic Demo")
    print("=" * 60)

    # Configuration for testing (reduced parameters for speed)
    test_config = {
        "DIRECTION": "Long",
        "USE_HOURLY": False,
        "USE_YEARS": True,
        "YEARS": 2,  # Reduced for faster testing
        "USE_SYNTHETIC": False,
        "STRATEGY_TYPE": "EMA",
    }

    # Monte Carlo configuration (reduced simulations for testing)
    mc_config = MonteCarloConfig(
        num_simulations=100,  # Reduced from 1000 for testing
        bootstrap_block_size=63,  # ~3 months
        confidence_level=0.95,
        enable_regime_analysis=True,
        min_data_fraction=0.6,
    )

    # Parameter ranges (small range for testing)
    parameter_ranges = {"short_windows": [10, 15, 20], "long_windows": [30, 40, 50]}

    print(f"Testing configuration:")
    print(f"- Ticker: BTC-USD")
    print(f"- Monte Carlo simulations: {mc_config.num_simulations}")
    print(
        f"- Parameter combinations: {len(parameter_ranges['short_windows']) * len(parameter_ranges['long_windows'])}"
    )
    print(f"- Data period: {test_config['YEARS']} years")
    print(f"- Strategy type: {test_config['STRATEGY_TYPE']}")
    print()

    try:
        # Run the analysis
        print("Starting Monte Carlo parameter robustness analysis...")
        results = run_parameter_robustness_analysis(
            tickers=["BTC-USD"],
            parameter_ranges=parameter_ranges,
            strategy_config=test_config,
            mc_config=mc_config,
        )

        if results and "BTC-USD" in results:
            btc_results = results["BTC-USD"]
            print(f"\nAnalysis completed successfully!")
            print(
                f"Results for BTC-USD: {len(btc_results)} parameter combinations tested"
            )

            # Display summary statistics
            print("\n" + "=" * 50)
            print("PARAMETER ROBUSTNESS SUMMARY")
            print("=" * 50)

            stable_count = sum(1 for result in btc_results if result.is_stable)
            print(f"Stable parameter combinations: {stable_count}/{len(btc_results)}")
            print(f"Stability rate: {stable_count/len(btc_results)*100:.1f}%")

            # Show top 3 most stable combinations
            sorted_results = sorted(
                btc_results, key=lambda x: x.stability_score, reverse=True
            )

            print(f"\nTop 3 Most Stable Parameter Combinations:")
            print("-" * 50)
            for i, result in enumerate(sorted_results[:3]):
                short, long = result.parameter_combination
                print(f"{i+1}. Windows {short}/{long}:")
                print(f"   Stability Score: {result.stability_score:.3f}")
                print(f"   Parameter Robustness: {result.parameter_robustness:.3f}")
                print(f"   Regime Consistency: {result.regime_consistency:.3f}")
                print(
                    f"   Base Sharpe Ratio: {result.base_performance.get('Sharpe Ratio', 0):.3f}"
                )

                if result.performance_mean.get("Sharpe Ratio"):
                    ci = result.confidence_intervals.get("Sharpe Ratio", (0, 0))
                    print(
                        f"   MC Mean Sharpe: {result.performance_mean['Sharpe Ratio']:.3f}"
                    )
                    print(f"   Sharpe 95% CI: [{ci[0]:.3f}, {ci[1]:.3f}]")
                print()

            # Create basic visualizations
            print("Creating visualizations...")
            visualizer = ParameterStabilityVisualizer("png/monte_carlo/test_results")

            # Create stability heatmap
            visualizer.create_stability_heatmap(
                btc_results, "BTC-USD", "stability_score"
            )
            visualizer.create_confidence_interval_plot(
                btc_results, "BTC-USD", "Sharpe Ratio"
            )

            # Create distribution plot for best parameter combination
            if sorted_results:
                visualizer.create_performance_distribution_plot(
                    sorted_results[0], "BTC-USD_best", "Sharpe Ratio"
                )

            print(f"Visualizations saved to: png/monte_carlo/test_results/")

            return True

        else:
            print("No results returned from analysis")
            return False

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_visualization_only():
    """Test visualization functions with mock data."""
    print("\n" + "=" * 60)
    print("Testing Visualization Functions")
    print("=" * 60)

    try:
        # Check if we have results from previous run
        results_file = "data/raw/monte_carlo/parameter_robustness_1_tickers/parameter_robustness_summary.csv"

        if os.path.exists(results_file):
            print(f"Found existing results file: {results_file}")
            print("Creating visualizations from saved results...")

            from app.strategies.monte_carlo.parameter_visualization import (
                visualize_monte_carlo_results,
            )

            visualize_monte_carlo_results(
                results_file, "png/monte_carlo/test_visualizations"
            )

            print("Visualization test completed!")
            return True
        else:
            print(f"No existing results file found at: {results_file}")
            print("Run the basic test first to generate results")
            return False

    except Exception as e:
        print(f"Error during visualization test: {str(e)}")
        return False


def main():
    """Run the test suite."""
    print("Monte Carlo Parameter Robustness Testing - Test Suite")
    print("This script demonstrates the Monte Carlo parameter analysis system")
    print()

    # Test basic functionality
    success1 = test_basic_parameter_robustness()

    # Test visualizations
    success2 = test_visualization_only()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Basic parameter robustness test: {'PASSED' if success1 else 'FAILED'}")
    print(f"Visualization test: {'PASSED' if success2 else 'FAILED'}")

    if success1 and success2:
        print(
            "\nAll tests passed! The Monte Carlo parameter robustness system is working correctly."
        )
        print("\nNext steps:")
        print("1. Review the generated visualizations in png/monte_carlo/test_results/")
        print(
            "2. Check the detailed results in data/raw/monte_carlo/parameter_robustness_1_tickers/"
        )
        print("3. Use the integration script for full pipeline testing")
    else:
        print("\nSome tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()
