#!/usr/bin/env python3
"""
Debug SMCI percentile calculation in detail

This script examines the actual percentile data being used in the SMCI calculation
to understand why the percentile rank is not correctly calculated.
"""

from pathlib import Path
import sys


sys.path.append(str(Path(__file__).parent.parent.parent))

import logging

from app.tools.analysis.divergence_detector import DivergenceDetector
from app.tools.config.statistical_analysis_config import SPDSConfig


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def debug_percentile_calculation():
    """Debug the exact percentile calculation process"""

    # Create mock percentiles with known values
    class MockPercentiles:
        def __init__(self):
            self.p5 = 0.01
            self.p10 = 0.02
            self.p25 = 0.04
            self.p50 = 0.08
            self.p70 = 0.1274  # This is the key P70 threshold
            self.p75 = 0.14
            self.p80 = 0.16
            self.p90 = 0.20
            self.p95 = 0.25
            self.p99 = 0.30

    config = SPDSConfig(PORTFOLIO="live_signals.csv")
    detector = DivergenceDetector(config)

    mock_percentiles = MockPercentiles()
    smci_value = 0.1297  # 12.97%

    print(f"SMCI value: {smci_value:.6f}")
    print(f"P70 value: {mock_percentiles.p70:.6f}")
    print(f"P75 value: {mock_percentiles.p75:.6f}")
    print(f"P80 value: {mock_percentiles.p80:.6f}")

    # Check where SMCI value falls in the percentile range
    if smci_value < mock_percentiles.p70:
        print(f"❌ SMCI value {smci_value:.6f} < P70 {mock_percentiles.p70:.6f}")
    elif smci_value >= mock_percentiles.p70 and smci_value < mock_percentiles.p75:
        print(f"✅ SMCI value {smci_value:.6f} is between P70 and P75")
        print("   Expected percentile rank: between 70 and 75")
    elif smci_value >= mock_percentiles.p75 and smci_value < mock_percentiles.p80:
        print(f"✅ SMCI value {smci_value:.6f} is between P75 and P80")
        print("   Expected percentile rank: between 75 and 80")
    else:
        print(f"✅ SMCI value {smci_value:.6f} > P80")
        print("   Expected percentile rank: > 80")

    # Test the actual calculation
    calculated_rank = detector._estimate_percentile_rank(smci_value, mock_percentiles)
    print(f"\nCalculated percentile rank: {calculated_rank:.2f}")

    # Manual calculation for verification
    # SMCI = 0.1297, P70 = 0.1274, P75 = 0.14
    # Linear interpolation: 70 + (75-70) * (0.1297-0.1274)/(0.14-0.1274)
    if smci_value >= mock_percentiles.p70 and smci_value <= mock_percentiles.p75:
        manual_rank = 70 + (75 - 70) * (smci_value - mock_percentiles.p70) / (
            mock_percentiles.p75 - mock_percentiles.p70
        )
        print(f"Manual calculation (P70-P75 interpolation): {manual_rank:.2f}")

    # Check if the calculated rank is correct
    if smci_value > mock_percentiles.p70:
        if calculated_rank > 70:
            print(f"✅ Calculation is correct: {calculated_rank:.2f} > 70")
        else:
            print(f"❌ Calculation is incorrect: {calculated_rank:.2f} <= 70")

    # Check signal generation logic
    print("\nSignal generation analysis:")
    print(f"  P70 threshold: {mock_percentiles.p70:.6f} (12.74%)")
    print(f"  SMCI value: {smci_value:.6f} (12.97%)")
    print(f"  Value > P70: {smci_value > mock_percentiles.p70}")
    print(f"  Calculated rank: {calculated_rank:.2f}")
    print(f"  Rank > 80 (SELL threshold): {calculated_rank > 80}")

    # The issue might be in the signal generation logic
    # If SMCI is above P70 but calculated rank is ~70.9, it should still trigger SELL
    # because the assessment said P70 = 12.74% and SMCI = 12.97% > 12.74%

    print("\nExpected behavior:")
    print("  Since SMCI (12.97%) > P70 (12.74%), it should be ranked > 70")
    print("  Since rank should be > 70, it should trigger SELL signal")

    return calculated_rank


if __name__ == "__main__":
    debug_percentile_calculation()
