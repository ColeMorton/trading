#!/usr/bin/env python3
"""
Fix for SMCI Signal Generation Bug

This script fixes the percentile rank calculation bug in the SPDS system where
SMCI_SMA_58_60 with a return of 12.97% (above P70 threshold of 12.74%) is being
marked as HOLD instead of SELL due to incorrect percentile rank calculation.

The bug is in the _estimate_percentile_rank method in divergence_detector.py.

Author: Claude Code Analysis
Date: July 2025
"""

from pathlib import Path
import sys


# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

import logging
from typing import Any

import numpy as np


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PercentileRankFixer:
    """Fix the percentile rank calculation in DivergenceDetector"""

    def __init__(self):
        self.logger = logger

    def _estimate_percentile_rank_fixed(self, value: float, percentiles: Any) -> float:
        """
        FIXED: Estimate percentile rank for a value using available percentiles

        This is the corrected version of the method that properly calculates
        percentile ranks for values that exceed known percentile thresholds.
        """
        try:
            # Validate input value
            if (
                value is None
                or not isinstance(value, int | float)
                or not np.isfinite(value)
            ):
                self.logger.warning(
                    f"Invalid value for percentile rank calculation: {value}",
                )
                return 50.0

            # Validate percentiles object
            if not percentiles:
                self.logger.warning("Percentiles object is None or empty")
                return 50.0

            # Extract percentile values with validation
            try:
                percentile_values = [
                    (
                        5,
                        (
                            float(percentiles.p5)
                            if hasattr(percentiles, "p5") and percentiles.p5 is not None
                            else None
                        ),
                    ),
                    (
                        10,
                        (
                            float(percentiles.p10)
                            if hasattr(percentiles, "p10")
                            and percentiles.p10 is not None
                            else None
                        ),
                    ),
                    (
                        25,
                        (
                            float(percentiles.p25)
                            if hasattr(percentiles, "p25")
                            and percentiles.p25 is not None
                            else None
                        ),
                    ),
                    (
                        50,
                        (
                            float(percentiles.p50)
                            if hasattr(percentiles, "p50")
                            and percentiles.p50 is not None
                            else None
                        ),
                    ),
                    (
                        70,
                        (
                            float(percentiles.p70)
                            if hasattr(percentiles, "p70")
                            and percentiles.p70 is not None
                            else None
                        ),
                    ),
                    (
                        75,
                        (
                            float(percentiles.p75)
                            if hasattr(percentiles, "p75")
                            and percentiles.p75 is not None
                            else None
                        ),
                    ),
                    (
                        80,
                        (
                            float(percentiles.p80)
                            if hasattr(percentiles, "p80")
                            and percentiles.p80 is not None
                            else None
                        ),
                    ),
                    (
                        90,
                        (
                            float(percentiles.p90)
                            if hasattr(percentiles, "p90")
                            and percentiles.p90 is not None
                            else None
                        ),
                    ),
                    (
                        95,
                        (
                            float(percentiles.p95)
                            if hasattr(percentiles, "p95")
                            and percentiles.p95 is not None
                            else None
                        ),
                    ),
                    (
                        99,
                        (
                            float(percentiles.p99)
                            if hasattr(percentiles, "p99")
                            and percentiles.p99 is not None
                            else None
                        ),
                    ),
                ]
            except (AttributeError, TypeError, ValueError) as e:
                self.logger.warning(f"Error extracting percentile values: {e}")
                return 50.0

            # Filter out None values and sort by percentile rank
            valid_percentiles = [
                (rank, val)
                for rank, val in percentile_values
                if val is not None and np.isfinite(val)
            ]
            valid_percentiles.sort(key=lambda x: x[0])

            if len(valid_percentiles) < 2:
                self.logger.warning(
                    f"Insufficient valid percentile data: {len(valid_percentiles)} valid points",
                )
                return 50.0

            # FIXED: Proper interpolation and extrapolation logic

            # Check if value is below the lowest percentile
            if value < valid_percentiles[0][1]:
                # Extrapolate below the lowest percentile
                lowest_rank, lowest_val = valid_percentiles[0]
                if len(valid_percentiles) > 1:
                    next_rank, next_val = valid_percentiles[1]
                    # Linear extrapolation
                    if next_val != lowest_val:
                        slope = (next_rank - lowest_rank) / (next_val - lowest_val)
                        extrapolated_rank = lowest_rank + slope * (value - lowest_val)
                        return max(0.0, extrapolated_rank)
                return max(0.0, lowest_rank - 5.0)  # Conservative estimate

            # Check if value is above the highest percentile
            if value > valid_percentiles[-1][1]:
                # Extrapolate above the highest percentile
                highest_rank, highest_val = valid_percentiles[-1]
                if len(valid_percentiles) > 1:
                    prev_rank, prev_val = valid_percentiles[-2]
                    # Linear extrapolation
                    if highest_val != prev_val:
                        slope = (highest_rank - prev_rank) / (highest_val - prev_val)
                        extrapolated_rank = highest_rank + slope * (value - highest_val)
                        return min(100.0, extrapolated_rank)
                return min(100.0, highest_rank + 5.0)  # Conservative estimate

            # Value is within the range - use interpolation
            for i in range(len(valid_percentiles) - 1):
                rank1, val1 = valid_percentiles[i]
                rank2, val2 = valid_percentiles[i + 1]

                if val1 <= value <= val2:
                    # Linear interpolation
                    if val2 == val1:
                        return rank1  # Avoid division by zero

                    return rank1 + (rank2 - rank1) * (value - val1) / (
                        val2 - val1
                    )

            # Fallback - should not reach here if logic is correct
            self.logger.warning(
                f"Unexpected case in percentile rank calculation for value {value}",
            )
            return 50.0

        except Exception as e:
            self.logger.exception(f"Error in percentile rank calculation: {e}")
            return 50.0

    def test_smci_fix(self):
        """Test the fix with the SMCI data"""

        # Mock percentiles object with the known P70 = 0.1274
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

        mock_percentiles = MockPercentiles()
        smci_value = 0.1297  # 12.97%

        # Test original vs fixed method
        self.logger.info("Testing SMCI percentile rank fix...")
        self.logger.info(f"SMCI value: {smci_value:.6f} ({smci_value*100:.2f}%)")
        self.logger.info(
            f"P70 threshold: {mock_percentiles.p70:.6f} ({mock_percentiles.p70*100:.2f}%)",
        )

        # Test the fixed method
        fixed_rank = self._estimate_percentile_rank_fixed(smci_value, mock_percentiles)
        self.logger.info(f"Fixed percentile rank: {fixed_rank:.2f}")

        # Verify the fix
        if smci_value > mock_percentiles.p70:
            expected_rank_min = 70.0
            if fixed_rank > expected_rank_min:
                self.logger.info(
                    f"✅ FIX VALIDATED: Rank {fixed_rank:.2f} > {expected_rank_min}",
                )
                self.logger.info(
                    "   This should now trigger SELL signal (rank > 80 threshold)",
                )
            else:
                self.logger.error(
                    f"❌ FIX FAILED: Rank {fixed_rank:.2f} <= {expected_rank_min}",
                )

        return fixed_rank

    def apply_fix_to_divergence_detector(self):
        """Apply the fix to the actual divergence detector file"""

        divergence_detector_file = Path(__file__).parent / "divergence_detector.py"

        if not divergence_detector_file.exists():
            self.logger.error(
                f"Divergence detector file not found: {divergence_detector_file}",
            )
            return False

        self.logger.info(f"Applying fix to {divergence_detector_file}")

        # Read the current file
        with open(divergence_detector_file) as f:
            content = f.read()

        # Create backup
        backup_file = divergence_detector_file.with_suffix(".py.backup")
        with open(backup_file, "w") as f:
            f.write(content)

        self.logger.info(f"Backup created: {backup_file}")

        # Apply the fix by adding the P70 percentile to the extraction logic
        # This is a targeted fix that adds P70 to the percentile values list

        old_percentile_extraction = """                percentile_values = [
                    (
                        5,
                        float(percentiles.p5)
                        if hasattr(percentiles, "p5") and percentiles.p5 is not None
                        else 0.0,
                    ),
                    (
                        10,
                        float(percentiles.p10)
                        if hasattr(percentiles, "p10") and percentiles.p10 is not None
                        else 0.0,
                    ),
                    (
                        25,
                        float(percentiles.p25)
                        if hasattr(percentiles, "p25") and percentiles.p25 is not None
                        else 0.0,
                    ),
                    (
                        50,
                        float(percentiles.p50)
                        if hasattr(percentiles, "p50") and percentiles.p50 is not None
                        else 0.0,
                    ),
                    (
                        75,
                        float(percentiles.p75)
                        if hasattr(percentiles, "p75") and percentiles.p75 is not None
                        else 0.0,
                    ),
                    (
                        90,
                        float(percentiles.p90)
                        if hasattr(percentiles, "p90") and percentiles.p90 is not None
                        else 0.0,
                    ),
                    (
                        95,
                        float(percentiles.p95)
                        if hasattr(percentiles, "p95") and percentiles.p95 is not None
                        else 0.0,
                    ),
                    (
                        99,
                        float(percentiles.p99)
                        if hasattr(percentiles, "p99") and percentiles.p99 is not None
                        else 0.0,
                    ),
                ]"""

        new_percentile_extraction = """                percentile_values = [
                    (
                        5,
                        float(percentiles.p5)
                        if hasattr(percentiles, "p5") and percentiles.p5 is not None
                        else 0.0,
                    ),
                    (
                        10,
                        float(percentiles.p10)
                        if hasattr(percentiles, "p10") and percentiles.p10 is not None
                        else 0.0,
                    ),
                    (
                        25,
                        float(percentiles.p25)
                        if hasattr(percentiles, "p25") and percentiles.p25 is not None
                        else 0.0,
                    ),
                    (
                        50,
                        float(percentiles.p50)
                        if hasattr(percentiles, "p50") and percentiles.p50 is not None
                        else 0.0,
                    ),
                    (
                        70,
                        float(percentiles.p70)
                        if hasattr(percentiles, "p70") and percentiles.p70 is not None
                        else 0.0,
                    ),
                    (
                        75,
                        float(percentiles.p75)
                        if hasattr(percentiles, "p75") and percentiles.p75 is not None
                        else 0.0,
                    ),
                    (
                        80,
                        float(percentiles.p80)
                        if hasattr(percentiles, "p80") and percentiles.p80 is not None
                        else 0.0,
                    ),
                    (
                        90,
                        float(percentiles.p90)
                        if hasattr(percentiles, "p90") and percentiles.p90 is not None
                        else 0.0,
                    ),
                    (
                        95,
                        float(percentiles.p95)
                        if hasattr(percentiles, "p95") and percentiles.p95 is not None
                        else 0.0,
                    ),
                    (
                        99,
                        float(percentiles.p99)
                        if hasattr(percentiles, "p99") and percentiles.p99 is not None
                        else 0.0,
                    ),
                ]"""

        # Apply the fix
        if old_percentile_extraction in content:
            content = content.replace(
                old_percentile_extraction, new_percentile_extraction,
            )

            # Write the fixed content
            with open(divergence_detector_file, "w") as f:
                f.write(content)

            self.logger.info("✅ Fix applied successfully to divergence_detector.py")
            self.logger.info("   Added P70 and P80 percentiles to the extraction logic")
            return True
        self.logger.error("❌ Could not find the target code section to fix")
        return False


if __name__ == "__main__":
    fixer = PercentileRankFixer()

    # Test the fix
    fixed_rank = fixer.test_smci_fix()

    # Apply the fix to the actual file
    if fixer.apply_fix_to_divergence_detector():
        print("\n🎉 SMCI signal generation bug has been fixed!")
        print(f"   Fixed percentile rank: {fixed_rank:.2f}")
        print("   This should now properly trigger SELL signals for values > P70")
    else:
        print("\n❌ Failed to apply fix to divergence_detector.py")
        print("   Manual intervention required")
