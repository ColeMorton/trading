#!/usr/bin/env python3
"""
Test the risk calculation fix on the actual portfolio_d_20250530 data.
"""

import os
import sys
from pathlib import Path


# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Ensure fixed calculation is used
os.environ["USE_FIXED_RISK_CALC"] = "true"

from app.concurrency.review import run_concurrency_review


def main():
    print("=" * 80)
    print("Testing Risk Calculation Fix on portfolio_d_20250530")
    print("=" * 80)
    print()

    # Run concurrency analysis on the portfolio
    print("Running concurrency analysis with fixed risk calculations...")

    try:
        # Run analysis without visualization to focus on calculations
        config = {
            "PORTFOLIO": "portfolio_d_20250530",
            "VISUALIZATION": False,
            "OPTIMIZE": False,
            "USE_FIXED_RISK_CALC": True,
        }

        results = run_concurrency_review("portfolio_d_20250530", config)

        # Extract risk contributions from results
        if "strategies" in results:
            print(f"\nAnalyzed {len(results['strategies'])} strategies")

            # Calculate sum of risk contributions
            total_risk_contrib = 0
            for strategy in results["strategies"]:
                if (
                    "risk_metrics" in strategy
                    and "risk_contribution" in strategy["risk_metrics"]
                ):
                    contrib = strategy["risk_metrics"]["risk_contribution"]["value"]
                    total_risk_contrib += contrib
                    print(f"{strategy['id']}: {contrib*100:.2f}%")

            print(f"\nTotal Risk Contributions: {total_risk_contrib*100:.2f}%")

            # Check portfolio metrics
            if (
                "portfolio_metrics" in results
                and "risk" in results["portfolio_metrics"]
            ):
                risk_metrics = results["portfolio_metrics"]["risk"]
                print("\nPortfolio Risk Metrics:")
                print(
                    f"  VaR 95%: {risk_metrics.get('var_95', {}).get('value', 'N/A')}",
                )
                print(
                    f"  CVaR 95%: {risk_metrics.get('cvar_95', {}).get('value', 'N/A')}",
                )
                print(
                    f"  Risk Concentration Index: {risk_metrics.get('risk_concentration_index', {}).get('value', 'N/A')}",
                )

            # Final verdict
            print("\n" + "=" * 80)
            if abs(total_risk_contrib - 1.0) < 0.01:
                print("✅ SUCCESS: Risk contributions correctly sum to 100%!")
                print("   The 441% error has been fixed!")
            else:
                print(
                    f"⚠️  WARNING: Risk contributions sum to {total_risk_contrib*100:.2f}%",
                )
            print("=" * 80)

        else:
            print("❌ No strategy data found in results")

    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
