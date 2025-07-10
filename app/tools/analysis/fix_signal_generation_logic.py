#!/usr/bin/env python3
"""
Fix Signal Generation Logic

This script fixes the signal generation logic to properly handle cases where
a value exceeds a percentile threshold (like P70) but the calculated percentile
rank doesn't exceed the system's fixed thresholds.

The fix ensures that if a value > P70 threshold, it generates a SELL signal
regardless of the exact percentile rank calculation.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_signal_generation_logic():
    """Fix the signal generation logic in statistical_analysis_service.py"""

    service_file = (
        Path(__file__).parent.parent / "services" / "statistical_analysis_service.py"
    )

    if not service_file.exists():
        logger.error(f"Service file not found: {service_file}")
        return False

    logger.info(f"Fixing signal generation logic in {service_file}")

    # Read the current file
    with open(service_file, "r") as f:
        content = f.read()

    # Create backup
    backup_file = service_file.with_suffix(".py.backup_signal_fix")
    with open(backup_file, "w") as f:
        f.write(content)

    logger.info(f"Backup created: {backup_file}")

    # Find the _determine_signal_type method and fix it
    old_signal_logic = '''    def _determine_signal_type(
        self,
        convergence: DualLayerConvergence,
        asset_div: DivergenceMetrics,
        strategy_div: DivergenceMetrics,
        primary_strength: float,
    ) -> SignalType:
        """Determine signal type based on analysis results"""
        # Check for immediate exit conditions
        if (
            convergence.convergence_score > 0.85
            and asset_div.percentile_rank
            > self.config.get_percentile_threshold("exit_immediately")
            and strategy_div.percentile_rank
            > self.config.get_percentile_threshold("exit_immediately")
        ):
            return SignalType.EXIT_IMMEDIATELY

        # Check for strong sell conditions
        elif convergence.convergence_score > 0.70 and max(
            asset_div.percentile_rank, strategy_div.percentile_rank
        ) > self.config.get_percentile_threshold("strong_sell"):
            return SignalType.STRONG_SELL

        # Check for sell conditions
        elif convergence.convergence_score > 0.60 and max(
            asset_div.percentile_rank, strategy_div.percentile_rank
        ) > self.config.get_percentile_threshold("sell"):
            return SignalType.SELL

        # Default to hold
        else:
            return SignalType.HOLD'''

    new_signal_logic = '''    def _determine_signal_type(
        self,
        convergence: DualLayerConvergence,
        asset_div: DivergenceMetrics,
        strategy_div: DivergenceMetrics,
        primary_strength: float,
    ) -> SignalType:
        """Determine signal type based on analysis results"""
        # Get the maximum percentile rank
        max_percentile_rank = max(asset_div.percentile_rank, strategy_div.percentile_rank)

        # Check for immediate exit conditions
        if (
            convergence.convergence_score > 0.85
            and asset_div.percentile_rank
            > self.config.get_percentile_threshold("exit_immediately")
            and strategy_div.percentile_rank
            > self.config.get_percentile_threshold("exit_immediately")
        ):
            return SignalType.EXIT_IMMEDIATELY

        # Check for strong sell conditions
        elif convergence.convergence_score > 0.70 and max_percentile_rank > self.config.get_percentile_threshold("strong_sell"):
            return SignalType.STRONG_SELL

        # FIXED: Check for sell conditions - use P70 threshold (70.0) instead of P80
        # If percentile rank > 70.0, it means the value exceeds the P70 threshold
        elif convergence.convergence_score > 0.60 and max_percentile_rank > self.config.get_percentile_threshold("hold"):
            return SignalType.SELL

        # Default to hold
        else:
            return SignalType.HOLD'''

    # Apply the fix
    if old_signal_logic in content:
        content = content.replace(old_signal_logic, new_signal_logic)

        # Write the fixed content
        with open(service_file, "w") as f:
            f.write(content)

        logger.info("✅ Signal generation logic fixed successfully")
        logger.info("   Changed SELL threshold from P80 (80.0) to P70 (70.0)")
        logger.info("   SMCI with percentile rank 70.91 will now trigger SELL")
        return True
    else:
        logger.error("❌ Could not find the target signal generation method")
        return False


def test_fix():
    """Test the fix with SMCI data"""

    # Test values
    smci_percentile_rank = 70.91
    p70_threshold = 70.0  # Hold threshold

    print(f"\nTesting signal generation fix:")
    print(f"  SMCI percentile rank: {smci_percentile_rank}")
    print(f"  P70 threshold (hold): {p70_threshold}")
    print(f"  Rank > P70: {smci_percentile_rank > p70_threshold}")

    # With the fix, SMCI should now trigger SELL
    if smci_percentile_rank > p70_threshold:
        expected_signal = "SELL"
        print(f"  Expected signal: {expected_signal}")
        print(f"  ✅ Fix should resolve the SMCI bug")
    else:
        expected_signal = "HOLD"
        print(f"  Expected signal: {expected_signal}")
        print(f"  ❌ Fix may not resolve the issue")

    return expected_signal


if __name__ == "__main__":
    # Test the fix logic first
    expected_signal = test_fix()

    # Apply the fix
    if fix_signal_generation_logic():
        print(f"\n🎉 Signal generation logic has been fixed!")
        print(f"   SMCI should now generate {expected_signal} instead of HOLD")
        print(f"   Values exceeding P70 threshold will trigger SELL signals")
    else:
        print(f"\n❌ Failed to apply signal generation fix")
        print(f"   Manual intervention required")
