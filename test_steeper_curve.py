#!/usr/bin/env python3
"""Test the steeper power curve for Phase 1."""

import math

import pandas as pd


def calculate_total_trades_normalized_steep(total_trades):
    """New implementation with steeper Phase 1 curve."""
    if pd.isna(total_trades) or total_trades <= 0:
        return 0.1

    if total_trades < 54:
        # Phase 1: Extremely steep confidence penalty
        normalized_trades = total_trades / 54
        return 0.1 + 0.4 * (normalized_trades**4.5)  # Very steep power curve

    elif total_trades <= 100:
        # Phase 2: Meaningful significance zone
        progress = (total_trades - 54) / (100 - 54)
        return 0.5 + 0.7 * progress

    else:
        # Phase 3: Diminishing returns
        excess_trades = total_trades - 100
        return 1.2 + 0.8 * (1 - math.exp(-excess_trades / 120))


def test_steeper_curve():
    """Test the steeper curve behavior."""
    test_values = [1, 5, 10, 15, 25, 35, 45, 54, 75, 100]

    print("Trades | New Score | Confidence Level")
    print("-------|-----------|------------------")

    for trades in test_values:
        score = calculate_total_trades_normalized_steep(trades)

        if trades < 10:
            level = "Virtually None"
        elif trades < 25:
            level = "Extremely Low"
        elif trades < 54:
            level = "Very Low"
        elif trades < 100:
            level = "Meaningful"
        else:
            level = "Strong"

        print(f"{trades:6d} | {score:9.4f} | {level}")


if __name__ == "__main__":
    test_steeper_curve()
