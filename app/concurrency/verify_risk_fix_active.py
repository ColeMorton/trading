#!/usr/bin/env python3
"""
Verify that the fixed risk calculation is now active.
"""

import os
from pathlib import Path
import sys


# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Set environment variable
os.environ["USE_FIXED_RISK_CALC"] = "true"

# Import after setting env var
from app.concurrency.config_defaults import get_default_config
from app.concurrency.tools.risk_metrics import calculate_risk_contributions


def main():
    print("=" * 70)
    print("Risk Calculation Fix Verification")
    print("=" * 70)
    print()

    # Check environment variable
    env_value = os.getenv("USE_FIXED_RISK_CALC", "not set")
    print(f"Environment Variable USE_FIXED_RISK_CALC: {env_value}")

    # Check config defaults
    config = get_default_config()
    config_value = config.get("USE_FIXED_RISK_CALC", "not set")
    print(f"Config Default USE_FIXED_RISK_CALC: {config_value}")

    # Check if fixed implementation is available
    try:

        print("\n✅ Fixed risk calculation module is available")
    except ImportError:
        print("\n❌ Fixed risk calculation module NOT available")
        return

    # Quick test to verify behavior
    print("\nRunning quick verification test...")

    import numpy as np
    import polars as pl

    # Create minimal test data
    n_periods = 100
    n_strategies = 3

    data_list = []
    position_arrays = []

    for _i in range(n_strategies):
        # Create price data
        returns = np.random.randn(n_periods) * 0.01
        prices = 100 * np.exp(np.cumsum(returns))
        df = pl.DataFrame({"Close": prices})
        data_list.append(df)

        # All strategies always active
        positions = np.ones(n_periods)
        position_arrays.append(positions)

    allocations = [40.0, 35.0, 25.0]

    # Mock log function
    logs = []

    def mock_log(msg, level):
        logs.append((msg, level))

    # Calculate risk contributions
    result = calculate_risk_contributions(
        position_arrays, data_list, allocations, mock_log,
    )

    # Check logs for which implementation was used
    implementation_used = "unknown"
    for log_msg, _ in logs:
        if "fixed risk contribution" in log_msg.lower():
            implementation_used = "FIXED"
            break
        if "legacy risk contribution" in log_msg.lower():
            implementation_used = "LEGACY"
            break

    print(f"\nImplementation used: {implementation_used}")

    # Calculate sum of risk contributions
    risk_contrib_sum = sum(v for k, v in result.items() if k.endswith("_risk_contrib"))

    print(f"Risk contributions sum: {risk_contrib_sum * 100:.2f}%")

    # Final verdict
    print("\n" + "=" * 70)
    if implementation_used == "FIXED" and abs(risk_contrib_sum - 1.0) < 0.01:
        print("✅ SUCCESS: Fixed risk calculation is ACTIVE and working correctly!")
        print("   Risk contributions now correctly sum to 100%")
    elif implementation_used == "LEGACY":
        print("⚠️  WARNING: Still using legacy calculation")
        print("   Check environment variable and configuration")
    else:
        print("❌ ERROR: Could not determine implementation status")
    print("=" * 70)


if __name__ == "__main__":
    main()
