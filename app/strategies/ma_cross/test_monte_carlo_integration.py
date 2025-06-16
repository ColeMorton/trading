"""
Test script for Monte Carlo Enhanced MA Cross Integration

This script tests the integration with reasonable parameters to avoid timeout.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.strategies.ma_cross.monte_carlo_integration import (
    run_monte_carlo_enhanced_ma_cross,
)


def test_monte_carlo_integration():
    """Test Monte Carlo integration with reasonable parameters."""
    print("=" * 60)
    print("Monte Carlo Enhanced MA Cross Integration Test")
    print("=" * 60)

    print("Running Monte Carlo enhanced analysis with test parameters...")
    print("- Ticker: BTC-USD")
    print("- Windows: 20 (creates ~150 parameter combinations)")
    print("- Strategy: EMA")
    print("- MC Simulations: 100 (reduced for testing)")
    print("- Direction: Long")
    print()

    try:
        # Run with much smaller parameter space for testing
        results = run_monte_carlo_enhanced_ma_cross(
            tickers=["BTC-USD"],
            windows=20,  # Much smaller: 5-19 short × 20-60 long = ~600 combinations
            strategy_types=["EMA"],
            mc_simulations=100,  # Reduced for testing
            direction="Long",
        )

        print("✅ Analysis completed successfully!")
        print()

        # Display summary
        summary = results.get("summary", {})
        print("Analysis Summary:")
        print(
            f"- Total parameter combinations: {summary.get('total_parameter_combinations', 'N/A')}"
        )
        print(f"- Tested combinations: {summary.get('tested_combinations', 'N/A')}")
        print(f"- Stable combinations: {summary.get('stable_combinations', 'N/A')}")
        print(f"- Stability rate: {summary.get('stability_rate', 0)*100:.1f}%")
        print(
            f"- Monte Carlo simulations: {summary.get('monte_carlo_simulations', 'N/A')}"
        )
        print()

        # Display top recommendations
        recommendations = results.get("recommendations", [])
        if recommendations:
            print("Top 3 Parameter Recommendations:")
            print("-" * 50)
            for i, rec in enumerate(recommendations[:3]):
                print(f"{i+1}. Windows {rec['Short_Window']}/{rec['Long_Window']}:")
                print(f"   Recommendation Score: {rec['Recommendation_Score']:.3f}")
                print(f"   Assessment: {rec['Assessment']}")
                print(f"   Standard Sharpe: {rec['Standard_Sharpe']:.3f}")
                print(f"   Stability Score: {rec['Stability_Score']:.3f}")
                print(f"   Parameter Robustness: {rec['Parameter_Robustness']:.3f}")
                print()

        print("✅ Monte Carlo enhanced MA Cross integration test passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_monte_carlo_integration()
    sys.exit(0 if success else 1)
