#!/usr/bin/env python3
"""
Analyze Signal Generation Thresholds

This script analyzes the signal generation thresholds to understand
the correct behavior for SMCI_SMA_58_60.
"""

import sys
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent.parent))

import logging

from app.tools.config.statistical_analysis_config import SPDSConfig


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_signal_thresholds():
    """Analyze the signal generation thresholds"""

    config = SPDSConfig(PORTFOLIO="live_signals.csv")

    print("=== SIGNAL GENERATION THRESHOLDS ===")
    print(f"Exit immediately: {config.PERCENTILE_THRESHOLDS['exit_immediately']}")
    print(f"Strong sell: {config.PERCENTILE_THRESHOLDS['strong_sell']}")
    print(f"Sell: {config.PERCENTILE_THRESHOLDS['sell']}")
    print(f"Hold: {config.PERCENTILE_THRESHOLDS['hold']}")

    print("\n=== SMCI ANALYSIS ===")
    smci_value = 0.1297  # 12.97%
    p70_threshold = 0.1274  # 12.74% from assessment
    smci_percentile_rank = 70.91

    print(f"SMCI value: {smci_value:.6f} ({smci_value * 100:.2f}%)")
    print(f"P70 threshold: {p70_threshold:.6f} ({p70_threshold * 100:.2f}%)")
    print(f"SMCI percentile rank: {smci_percentile_rank:.2f}")
    print(f"Value > P70: {smci_value > p70_threshold}")

    print("\n=== SIGNAL LOGIC ANALYSIS ===")
    print("Current system logic:")
    print(
        f"  - Exit immediately: rank > {config.PERCENTILE_THRESHOLDS['exit_immediately']}",
    )
    print(f"  - Strong sell: rank > {config.PERCENTILE_THRESHOLDS['strong_sell']}")
    print(f"  - Sell: rank > {config.PERCENTILE_THRESHOLDS['sell']}")
    print(f"  - Hold: rank <= {config.PERCENTILE_THRESHOLDS['hold']}")

    print("\nSMCI triggers:")
    print(
        f"  - Exit immediately: {smci_percentile_rank} > {config.PERCENTILE_THRESHOLDS['exit_immediately']} = {smci_percentile_rank > config.PERCENTILE_THRESHOLDS['exit_immediately']}",
    )
    print(
        f"  - Strong sell: {smci_percentile_rank} > {config.PERCENTILE_THRESHOLDS['strong_sell']} = {smci_percentile_rank > config.PERCENTILE_THRESHOLDS['strong_sell']}",
    )
    print(
        f"  - Sell: {smci_percentile_rank} > {config.PERCENTILE_THRESHOLDS['sell']} = {smci_percentile_rank > config.PERCENTILE_THRESHOLDS['sell']}",
    )
    print(
        f"  - Hold: {smci_percentile_rank} <= {config.PERCENTILE_THRESHOLDS['hold']} = {smci_percentile_rank <= config.PERCENTILE_THRESHOLDS['hold']}",
    )

    # Determine current signal
    if smci_percentile_rank > config.PERCENTILE_THRESHOLDS["exit_immediately"]:
        current_signal = "EXIT_IMMEDIATELY"
    elif smci_percentile_rank > config.PERCENTILE_THRESHOLDS["strong_sell"]:
        current_signal = "STRONG_SELL"
    elif smci_percentile_rank > config.PERCENTILE_THRESHOLDS["sell"]:
        current_signal = "SELL"
    else:
        current_signal = "HOLD"

    print(f"\nCurrent signal for SMCI: {current_signal}")

    print("\n=== ASSESSMENT INTERPRETATION ===")
    print("The assessment states:")
    print(
        "  'SMCI_SMA_58_60: Return of 0.1297 > P70 threshold (0.1274) but marked HOLD instead of SELL'",
    )
    print()
    print("Two possible interpretations:")
    print(
        "1. The system should generate SELL when value > P70 (not when percentile rank > 80)",
    )
    print("2. The P70 threshold calculation or percentile ranking is incorrect")
    print()
    print("Analysis:")
    print(
        f"  - SMCI value {smci_value:.6f} > P70 {p70_threshold:.6f}: {smci_value > p70_threshold}",
    )
    print(
        f"  - SMCI percentile rank {smci_percentile_rank:.2f} correctly places it between P70 and P75",
    )
    print("  - Current system requires rank > 80 for SELL, but SMCI is only at 70.91")
    print()
    print("CONCLUSION:")
    print(
        "The bug is likely in the signal generation logic. If a value exceeds the P70 threshold,",
    )
    print(
        "it should generate a SELL signal regardless of the exact percentile rank calculation.",
    )
    print(
        "The system should use value-based thresholds, not percentile-rank-based thresholds.",
    )

    return current_signal


if __name__ == "__main__":
    analyze_signal_thresholds()
