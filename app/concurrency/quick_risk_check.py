#!/usr/bin/env python3
"""
Quick check of risk contribution fix status.
"""

import os
from pathlib import Path
import sys


# Set to use fixed calculation
os.environ["USE_FIXED_RISK_CALC"] = "true"

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import numpy as np
import polars as pl

from app.concurrency.tools.risk_metrics import calculate_risk_contributions


def main():
    print("\nQuick Risk Contribution Check")
    print("=" * 40)

    # Create simple test data
    n_strategies = 3
    n_periods = 100

    # Mock data
    data_list = []
    position_arrays = []

    np.random.seed(123)
    for i in range(n_strategies):
        prices = 100 + np.cumsum(np.random.randn(n_periods) * 0.5)
        df = pl.DataFrame({"Close": prices})
        data_list.append(df)
        position_arrays.append(np.ones(n_periods))

    allocations = [40.0, 35.0, 25.0]

    # Track logs
    logs = []

    def log_func(msg, level):
        if "risk contribution" in msg.lower() or "sum" in msg.lower():
            logs.append(f"[{level}] {msg}")

    # Calculate
    print("\nCalculating risk contributions...")
    result = calculate_risk_contributions(
        position_arrays, data_list, allocations, log_func,
    )

    # Check implementation
    using_fixed = any("fixed" in log for log in logs)
    print(f"\nUsing {'FIXED' if using_fixed else 'LEGACY'} implementation")

    # Sum contributions
    total = sum(v for k, v in result.items() if k.endswith("_risk_contrib"))
    print(f"Risk contributions sum: {total*100:.2f}%")

    # Individual contributions
    print("\nIndividual contributions:")
    for i in range(n_strategies):
        key = f"strategy_{i+1}_risk_contrib"
        if key in result:
            print(f"  Strategy {i+1}: {result[key]*100:.2f}%")

    # Status
    print("\n" + "=" * 40)
    if abs(total - 1.0) < 0.01:
        print("✅ FIXED calculation is ACTIVE")
        print("   Risk contributions = 100%")
    else:
        print(f"❌ Risk contributions = {total*100:.2f}%")

    # Show relevant logs
    if logs:
        print("\nRelevant logs:")
        for log in logs[:5]:
            print(f"  {log}")


if __name__ == "__main__":
    main()
