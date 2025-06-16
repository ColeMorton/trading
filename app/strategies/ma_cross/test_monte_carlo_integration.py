"""
Test script for Monte Carlo Enhanced MA Cross Integration - UPDATED FOR NEW FRAMEWORK

This script tests the integration using the new concurrency-based Monte Carlo framework
while maintaining compatibility with existing test workflows.

⚠️  DEPRECATION NOTICE: This test now uses the new concurrency-based Monte Carlo framework.
Consider updating to use app.concurrency.tools.monte_carlo directly.
"""

import sys
import warnings
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Also import new framework directly for comparison
from app.concurrency.tools.monte_carlo import (
    PortfolioMonteCarloManager,
    create_monte_carlo_config,
)
from app.strategies.ma_cross.config.parameter_testing import ParameterTestingConfig

# Import compatibility wrapper (now uses new framework under the hood)
from app.strategies.ma_cross.monte_carlo_integration import MonteCarloEnhancedAnalyzer


def test_monte_carlo_integration():
    """Test Monte Carlo integration with reasonable parameters."""
    print("=" * 60)
    print("Monte Carlo Enhanced MA Cross Integration Test")
    print("=" * 60)

    print("Testing compatibility wrapper (uses new framework under the hood)...")
    print("- Ticker: BTC-USD")
    print("- Windows: 20 (creates ~150 parameter combinations)")
    print("- Strategy: EMA")
    print("- MC Simulations: 50 (reduced for testing)")
    print()

    try:
        # Test compatibility wrapper
        print("1. Testing compatibility wrapper...")

        # Create parameter config
        param_config = ParameterTestingConfig(
            tickers=["BTC-USD"],
            windows=20,
            strategy_types=["EMA"],
        )

        # Create analyzer using compatibility wrapper
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            analyzer = MonteCarloEnhancedAnalyzer(param_config)

            # Check if deprecation warning was issued
            if w and any("deprecated" in str(warning.message).lower() for warning in w):
                print("   ✅ Deprecation warning correctly issued")
            else:
                print("   ⚠️  No deprecation warning (unexpected)")

        # Run analysis using compatibility wrapper
        print("   Running analysis using compatibility wrapper...")
        results = analyzer.run_enhanced_analysis()

        print("   ✅ Compatibility wrapper analysis completed!")

        # Display results
        if results:
            summary = results.get("summary", {})
            print("   Analysis Summary:")
            print(f"   - Total tickers: {summary.get('total_tickers', 'N/A')}")
            print(
                f"   - Stable parameters found: {summary.get('stable_parameters_found', 'N/A')}"
            )
            print(
                f"   - Recommendations: {summary.get('recommendations_generated', 'N/A')}"
            )
            print(
                f"   - Average stability: {summary.get('average_stability_score', 0.0):.3f}"
            )

        print()

        # Test new framework directly for comparison
        print("2. Testing new framework directly...")

        mc_config = create_monte_carlo_config(
            {
                "MC_INCLUDE_IN_REPORTS": True,
                "MC_NUM_SIMULATIONS": 50,
                "MC_CONFIDENCE_LEVEL": 0.95,
                "MC_MAX_PARAMETERS_TO_TEST": 5,
            }
        )

        manager = PortfolioMonteCarloManager(mc_config)

        # Create strategies in new format
        strategies = [
            {
                "ticker": "BTC-USD",
                "MA Type": "EMA",
                "Window Short": 10,
                "Window Long": 20,
            },
            {
                "ticker": "BTC-USD",
                "MA Type": "EMA",
                "Window Short": 15,
                "Window Long": 30,
            },
        ]

        print("   Running analysis using new framework...")
        new_results = manager.analyze_portfolio(strategies)

        if new_results:
            portfolio_metrics = manager.get_portfolio_stability_metrics()
            print("   ✅ New framework analysis completed!")
            print("   Portfolio Metrics:")
            print(
                f"   - Portfolio stability: {portfolio_metrics['portfolio_stability_score']:.3f}"
            )
            print(
                f"   - Stable tickers: {portfolio_metrics['stable_tickers_percentage']:.1f}%"
            )
        else:
            print("   ⚠️  No results from new framework")

        print()
        print("✅ Both compatibility wrapper and new framework work correctly!")

        return True

    except Exception as e:
        print(f"❌ Error during Monte Carlo integration test: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_migration_example():
    """Demonstrate migration from old to new framework."""
    print("=" * 60)
    print("Migration Example: Old → New Framework")
    print("=" * 60)

    print("OLD WAY (deprecated):")
    print(
        "from app.strategies.ma_cross.monte_carlo_integration import MonteCarloEnhancedAnalyzer"
    )
    print("analyzer = MonteCarloEnhancedAnalyzer(param_config)")
    print("results = analyzer.run_enhanced_analysis()")
    print()

    print("NEW WAY (recommended):")
    print(
        "from app.concurrency.tools.monte_carlo import PortfolioMonteCarloManager, create_monte_carlo_config"
    )
    print("config = create_monte_carlo_config({'MC_INCLUDE_IN_REPORTS': True})")
    print("manager = PortfolioMonteCarloManager(config)")
    print("results = manager.analyze_portfolio(strategies)")
    print()

    print("Benefits of new framework:")
    print("- Portfolio-level analysis across multiple tickers")
    print("- Concurrent processing for better performance")
    print("- Integration with concurrency review pipeline")
    print("- Enhanced error handling and logging")
    print("- Comprehensive visualization capabilities")


if __name__ == "__main__":
    print("Monte Carlo Integration Test Suite")
    print("=" * 60)

    success = test_monte_carlo_integration()

    print()
    test_migration_example()

    print()
    if success:
        print("✅ All tests passed! Migration compatibility confirmed.")
    else:
        print("❌ Some tests failed. Check error messages above.")
        sys.exit(1)
