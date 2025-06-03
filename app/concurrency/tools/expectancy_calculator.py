"""
Fixed Expectancy Calculator for Concurrency Module.

This module provides a corrected implementation of expectancy calculations
that addresses the 596,446% variance issue caused by inconsistent formulas
across different modules.

The fix ensures all expectancy calculations use the standard mathematical
formula rather than the R-ratio based formula that can produce inflated values.
"""

import os
from typing import Dict, List, Tuple, Union

import numpy as np

from app.tools.expectancy import (
    calculate_expectancy,
    calculate_expectancy_from_returns,
    calculate_expectancy_with_stop_loss,
)


class ExpectancyCalculator:
    """Standardized expectancy calculator that fixes the 596,446% variance issue."""

    def __init__(self, use_fixed: bool = None):
        """Initialize the expectancy calculator.

        Args:
            use_fixed: Whether to use fixed calculation. If None, checks environment.
        """
        if use_fixed is None:
            use_fixed = os.getenv("USE_FIXED_EXPECTANCY_CALC", "true").lower() == "true"
        self.use_fixed = use_fixed

    def calculate_from_components(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        legacy_mode: bool = False,
    ) -> float:
        """Calculate expectancy from win rate and average win/loss.

        Args:
            win_rate: Win rate as decimal (0-1)
            avg_win: Average winning return as decimal
            avg_loss: Average losing return as positive decimal
            legacy_mode: If True, uses the incorrect R-ratio formula

        Returns:
            Expectancy value as decimal
        """
        if not self.use_fixed or legacy_mode:
            # Legacy R-ratio formula (incorrect)
            if avg_loss == 0:
                return 0.0
            r_ratio = avg_win / avg_loss
            return (win_rate * r_ratio) - (1 - win_rate)

        # Use the standardized correct formula
        return calculate_expectancy(win_rate, avg_win, avg_loss)

    def calculate_from_returns(
        self, returns: Union[List[float], np.ndarray], legacy_mode: bool = False
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate expectancy from a series of returns.

        Args:
            returns: Array of return values
            legacy_mode: If True, uses the incorrect R-ratio formula

        Returns:
            Tuple of (expectancy, components_dict)
        """
        if legacy_mode and not self.use_fixed:
            # Legacy calculation for comparison
            returns_array = np.array(returns)
            returns_array = returns_array[returns_array != 0]

            if len(returns_array) == 0:
                return 0.0, {
                    "win_rate": 0.0,
                    "avg_win": 0.0,
                    "avg_loss": 0.0,
                    "win_count": 0,
                    "loss_count": 0,
                }

            winning_returns = returns_array[returns_array > 0]
            losing_returns = returns_array[returns_array < 0]

            win_rate = len(winning_returns) / len(returns_array)
            avg_win = np.mean(winning_returns) if len(winning_returns) > 0 else 0
            avg_loss = abs(np.mean(losing_returns)) if len(losing_returns) > 0 else 0

            expectancy = self.calculate_from_components(
                win_rate, avg_win, avg_loss, legacy_mode=True
            )

            return expectancy, {
                "win_rate": win_rate,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "win_count": len(winning_returns),
                "loss_count": len(losing_returns),
            }

        # Use standardized calculation
        return calculate_expectancy_from_returns(returns)

    def calculate_with_stop_loss(
        self,
        returns: Union[List[float], np.ndarray],
        stop_loss: float,
        direction: str = "Long",
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate expectancy with stop loss applied.

        Args:
            returns: Array of return values
            stop_loss: Stop loss as decimal (0-1)
            direction: 'Long' or 'Short'

        Returns:
            Tuple of (expectancy, components_dict)
        """
        return calculate_expectancy_with_stop_loss(returns, stop_loss, direction)

    def validate_expectancy(self, expectancy: float, source: str = "") -> bool:
        """Validate that an expectancy value is reasonable.

        Args:
            expectancy: The expectancy value to validate
            source: Optional source identifier for logging

        Returns:
            True if expectancy is within reasonable bounds
        """
        # Reasonable bounds for per-trade expectancy
        MIN_REASONABLE = -1.0  # -100% (total loss)
        MAX_REASONABLE = 2.0  # 200% (very rare but possible)

        if expectancy < MIN_REASONABLE or expectancy > MAX_REASONABLE:
            print(f"Warning: Unreasonable expectancy {expectancy:.2%} from {source}")
            return False

        return True

    def convert_r_multiple_to_percentage(
        self, r_expectancy: float, avg_loss: float
    ) -> float:
        """Convert R-multiple expectancy to percentage expectancy.

        Args:
            r_expectancy: Expectancy in R-multiples
            avg_loss: Average loss as decimal

        Returns:
            Expectancy as percentage/decimal
        """
        return r_expectancy * avg_loss


def get_fixed_expectancy_calculator() -> ExpectancyCalculator:
    """Get a singleton instance of the fixed expectancy calculator.

    Returns:
        ExpectancyCalculator instance
    """
    if not hasattr(get_fixed_expectancy_calculator, "_instance"):
        get_fixed_expectancy_calculator._instance = ExpectancyCalculator()
    return get_fixed_expectancy_calculator._instance


# Convenience functions for backward compatibility
def calculate_fixed_expectancy(
    win_rate: float, avg_win: float, avg_loss: float
) -> float:
    """Calculate expectancy using the fixed formula.

    This is a convenience function that always uses the correct formula
    regardless of environment settings.
    """
    return calculate_expectancy(win_rate, avg_win, avg_loss)


def fix_legacy_expectancy(legacy_expectancy: float, avg_loss: float) -> float:
    """Convert a legacy R-ratio expectancy to correct percentage expectancy.

    Args:
        legacy_expectancy: Expectancy calculated with R-ratio formula
        avg_loss: Average loss used in the calculation

    Returns:
        Corrected expectancy value
    """
    calculator = ExpectancyCalculator()
    return calculator.convert_r_multiple_to_percentage(legacy_expectancy, avg_loss)
