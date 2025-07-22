#!/usr/bin/env python3
"""
Test script to debug the SMCI signal generation bug

This script analyzes the SMCI_SMA_58_60 position to understand why it's being marked as HOLD
instead of SELL when the current return (12.97%) exceeds the P70 threshold (12.74%).

Author: Claude Code Analysis
Date: July 2025
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

import asyncio
import logging

import pandas as pd

from app.tools.config.statistical_analysis_config import SPDSConfig
from app.tools.services.statistical_analysis_service import StatisticalAnalysisService

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_smci_signal_generation():
    """Test the SMCI signal generation logic"""

    # Load positions data
    positions_file = Path("data/raw/positions/live_signals.csv")
    positions_df = pd.read_csv(positions_file)

    # Find SMCI position
    smci_position = positions_df[
        positions_df["Position_UUID"] == "SMCI_SMA_58_60_20250623"
    ]

    if smci_position.empty:
        logger.error("SMCI position not found")
        return

    smci_row = smci_position.iloc[0]
    current_return = smci_row["Current_Unrealized_PnL"]

    logger.info(
        f"SMCI Current Return: {current_return:.6f} ({current_return*100:.2f}%)"
    )

    # Create SPDS config
    config = SPDSConfig(PORTFOLIO="live_signals.csv", USE_TRADE_HISTORY=True)

    # Create service
    service = StatisticalAnalysisService(config)

    # Test the percentile calculation logic
    logger.info("Testing percentile calculation logic...")

    # Mock a simple distribution for testing
    import numpy as np

    # Create a mock distribution where P70 = 0.1274 (12.74%)
    # and current value = 0.1297 (12.97%)
    test_distribution = np.random.normal(0.05, 0.03, 1000)
    test_distribution = np.sort(test_distribution)

    # Set P70 to exactly 0.1274
    p70_index = int(0.7 * len(test_distribution))
    test_distribution[p70_index] = 0.1274

    # Calculate where 0.1297 would rank
    current_value = 0.1297
    percentile_rank = (
        np.searchsorted(test_distribution, current_value) / len(test_distribution)
    ) * 100

    logger.info(f"Test P70 value: {test_distribution[p70_index]:.6f}")
    logger.info(f"Current value: {current_value:.6f}")
    logger.info(f"Calculated percentile rank: {percentile_rank:.2f}")

    # Check signal generation thresholds
    logger.info(f"Signal thresholds from config:")
    logger.info(
        f"  Exit immediately: {config.PERCENTILE_THRESHOLDS['exit_immediately']}"
    )
    logger.info(f"  Strong sell: {config.PERCENTILE_THRESHOLDS['strong_sell']}")
    logger.info(f"  Sell: {config.PERCENTILE_THRESHOLDS['sell']}")
    logger.info(f"  Hold: {config.PERCENTILE_THRESHOLDS['hold']}")

    # Expected behavior
    if percentile_rank > config.PERCENTILE_THRESHOLDS["sell"]:
        expected_signal = "SELL"
    elif percentile_rank > config.PERCENTILE_THRESHOLDS["hold"]:
        expected_signal = "SELL"  # Above P70 should be SELL
    else:
        expected_signal = "HOLD"

    logger.info(f"Expected signal based on percentile rank: {expected_signal}")

    # Test the actual percentile rank estimation
    logger.info("Testing _estimate_percentile_rank method...")

    # Create mock percentiles object
    class MockPercentiles:
        def __init__(self):
            self.p5 = 0.01
            self.p10 = 0.02
            self.p25 = 0.04
            self.p50 = 0.08
            self.p70 = 0.1274  # This is the key value from the assessment
            self.p75 = 0.14
            self.p80 = 0.16
            self.p90 = 0.20
            self.p95 = 0.25
            self.p99 = 0.30

    from app.tools.analysis.divergence_detector import DivergenceDetector

    detector = DivergenceDetector(config)

    mock_percentiles = MockPercentiles()
    estimated_rank = detector._estimate_percentile_rank(current_value, mock_percentiles)

    logger.info(
        f"Estimated percentile rank from divergence detector: {estimated_rank:.2f}"
    )

    # The bug analysis
    logger.info("\n=== BUG ANALYSIS ===")
    logger.info(
        f"SMCI current return: {current_return:.6f} ({current_return*100:.2f}%)"
    )
    logger.info(f"P70 threshold: 0.1274 (12.74%)")
    logger.info(f"Condition: {current_return:.6f} > 0.1274 = {current_return > 0.1274}")
    logger.info(f"Estimated percentile rank: {estimated_rank:.2f}")
    logger.info(f"Should trigger SELL if rank > 80.0: {estimated_rank > 80.0}")

    if current_return > 0.1274 and estimated_rank <= 80.0:
        logger.error(
            "BUG DETECTED: Current return exceeds P70 but percentile rank is too low!"
        )
        logger.error("This indicates a problem in the percentile rank calculation.")

    return {
        "current_return": current_return,
        "estimated_rank": estimated_rank,
        "expected_signal": expected_signal,
        "bug_detected": current_return > 0.1274 and estimated_rank <= 80.0,
    }


if __name__ == "__main__":
    result = asyncio.run(test_smci_signal_generation())

    if result and result["bug_detected"]:
        print("\n🚨 BUG CONFIRMED: SMCI signal generation is incorrect!")
        print(f"   Current return: {result['current_return']*100:.2f}%")
        print(f"   Estimated percentile rank: {result['estimated_rank']:.2f}")
        print(f"   Expected signal: {result['expected_signal']}")
    else:
        print("\n✅ No bug detected in signal generation logic")
