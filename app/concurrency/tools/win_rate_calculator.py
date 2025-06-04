#!/usr/bin/env python3
"""
Standardized win rate calculation module.

This module provides consistent win rate calculations across all trading modules,
addressing the 18.8% discrepancy between signal-based and trade-based calculations.

Classes:
    WinRateCalculator: Standardized win rate calculation methods
    WinRateType: Enumeration of different win rate calculation types
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Union

import numpy as np
import pandas as pd


class WinRateType(Enum):
    """Types of win rate calculations."""

    SIGNAL = "signal"  # Win rate based on individual signal returns
    TRADE = "trade"  # Win rate based on completed trade returns
    WEIGHTED = "weighted"  # Portfolio-weighted win rate


@dataclass
class WinRateComponents:
    """Components of a win rate calculation."""

    wins: int
    losses: int
    total: int
    win_rate: float
    zero_returns: int = 0
    calculation_type: str = "unknown"


class WinRateCalculator:
    """
    Standardized win rate calculator addressing calculation discrepancies.

    This class provides consistent methods for calculating win rates across
    different contexts (signals vs trades) and ensures proper handling of
    edge cases like zero returns.
    """

    def __init__(self, use_fixed: bool | None = None):
        """
        Initialize the win rate calculator.

        Args:
            use_fixed: Whether to use fixed calculation. If None, reads from environment.
        """
        if use_fixed is None:
            use_fixed = os.getenv("USE_FIXED_WIN_RATE_CALC", "true").lower() == "true"
        self.use_fixed = use_fixed

    def calculate_signal_win_rate(
        self, returns: np.ndarray, signals: np.ndarray, include_zeros: bool = False
    ) -> WinRateComponents:
        """
        Calculate win rate based on signal returns.

        This method calculates the win rate using returns only when signals are active.

        Args:
            returns: Array of period returns
            signals: Array of signal values (0 = no signal, ±1 = signal active)
            include_zeros: Whether to include zero returns in calculation

        Returns:
            WinRateComponents with signal-based win rate
        """
        if len(returns) != len(signals):
            raise ValueError("Returns and signals arrays must have same length")

        # Filter to only periods with active signals
        active_mask = signals != 0
        signal_returns = returns[active_mask]

        if len(signal_returns) == 0:
            return WinRateComponents(0, 0, 0, 0.0, 0, "signal")

        return self._calculate_from_returns(signal_returns, include_zeros, "signal")

    def calculate_trade_win_rate(
        self, trade_returns: np.ndarray, include_zeros: bool = False
    ) -> WinRateComponents:
        """
        Calculate win rate based on completed trade returns.

        This method calculates the win rate using returns from completed trades
        (entry to exit).

        Args:
            trade_returns: Array of completed trade returns
            include_zeros: Whether to include zero returns in calculation

        Returns:
            WinRateComponents with trade-based win rate
        """
        return self._calculate_from_returns(trade_returns, include_zeros, "trade")

    def calculate_weighted_win_rate(
        self, returns: np.ndarray, weights: np.ndarray, include_zeros: bool = False
    ) -> WinRateComponents:
        """
        Calculate portfolio-weighted win rate.

        This method calculates win rate using position-weighted returns.

        Args:
            returns: Array of returns
            weights: Array of position weights
            include_zeros: Whether to include zero returns in calculation

        Returns:
            WinRateComponents with weighted win rate
        """
        if len(returns) != len(weights):
            raise ValueError("Returns and weights arrays must have same length")

        weighted_returns = returns * weights
        return self._calculate_from_returns(weighted_returns, include_zeros, "weighted")

    def _calculate_from_returns(
        self, returns: np.ndarray, include_zeros: bool, calc_type: str
    ) -> WinRateComponents:
        """
        Internal method to calculate win rate from returns array.

        Args:
            returns: Array of returns
            include_zeros: Whether to include zero returns
            calc_type: Type of calculation for labeling

        Returns:
            WinRateComponents with calculated win rate
        """
        if len(returns) == 0:
            return WinRateComponents(0, 0, 0, 0.0, 0, calc_type)

        # Handle zero returns
        zero_count = int(np.sum(returns == 0))

        if not include_zeros:
            returns = returns[returns != 0]

        if len(returns) == 0:
            return WinRateComponents(0, 0, 0, 0.0, zero_count, calc_type)

        # Calculate wins and losses
        wins = int(np.sum(returns > 0))
        losses = int(np.sum(returns < 0))

        if include_zeros:
            # Zero returns count as neither wins nor losses for win rate
            total = wins + losses
        else:
            total = len(returns)

        win_rate = float(wins / total) if total > 0 else 0.0

        return WinRateComponents(
            wins=wins,
            losses=losses,
            total=total,
            win_rate=win_rate,
            zero_returns=zero_count,
            calculation_type=calc_type,
        )

    def calculate_legacy_win_rate(self, returns: np.ndarray) -> float:
        """
        Calculate win rate using legacy method for comparison.

        Args:
            returns: Array of returns

        Returns:
            Legacy win rate calculation
        """
        if len(returns) == 0:
            return 0.0

        # Legacy: include all returns, including zeros
        positive_returns = returns > 0
        return float(np.mean(positive_returns))

    def compare_calculations(
        self, returns: np.ndarray, signals: np.ndarray | None = None
    ) -> Dict[str, WinRateComponents]:
        """
        Compare different win rate calculation methods.

        Args:
            returns: Array of returns
            signals: Optional array of signals for signal-based calculation

        Returns:
            Dictionary comparing different calculation methods
        """
        results = {}

        # Standard trade-based calculation
        results["trade_standard"] = self.calculate_trade_win_rate(
            returns, include_zeros=False
        )
        results["trade_with_zeros"] = self.calculate_trade_win_rate(
            returns, include_zeros=True
        )

        # Signal-based calculation if signals provided
        if signals is not None:
            results["signal_standard"] = self.calculate_signal_win_rate(
                returns, signals, include_zeros=False
            )
            results["signal_with_zeros"] = self.calculate_signal_win_rate(
                returns, signals, include_zeros=True
            )

        # Legacy calculation
        legacy_rate = self.calculate_legacy_win_rate(returns)
        results["legacy"] = WinRateComponents(
            wins=int(np.sum(returns > 0)),
            losses=int(np.sum(returns <= 0)),
            total=len(returns),
            win_rate=legacy_rate,
            zero_returns=int(np.sum(returns == 0)),
            calculation_type="legacy",
        )

        return results

    def validate_win_rate(self, win_rate: float, tolerance: float = 0.01) -> bool:
        """
        Validate that a win rate is reasonable.

        Args:
            win_rate: Win rate to validate
            tolerance: Tolerance for validation

        Returns:
            True if win rate is valid
        """
        return 0.0 <= win_rate <= 1.0

    def calculate_from_dataframe(
        self,
        df: pd.DataFrame,
        return_col: str = "returns",
        signal_col: str = "signal",
        weight_col: str | None = None,
        method: WinRateType = WinRateType.TRADE,
    ) -> WinRateComponents:
        """
        Calculate win rate from pandas DataFrame.

        Args:
            df: DataFrame containing returns and signals
            return_col: Name of returns column
            signal_col: Name of signals column
            weight_col: Name of weights column (for weighted calculation)
            method: Type of win rate calculation to perform

        Returns:
            WinRateComponents with calculated win rate
        """
        if return_col not in df.columns:
            raise ValueError(f"Return column '{return_col}' not found in DataFrame")

        returns = df[return_col].values

        if method == WinRateType.SIGNAL:
            if signal_col not in df.columns:
                raise ValueError(f"Signal column '{signal_col}' not found in DataFrame")
            signals = df[signal_col].values
            return self.calculate_signal_win_rate(returns, signals)

        elif method == WinRateType.WEIGHTED:
            if weight_col is None or weight_col not in df.columns:
                raise ValueError(f"Weight column '{weight_col}' not found in DataFrame")
            weights = df[weight_col].values
            return self.calculate_weighted_win_rate(returns, weights)

        else:  # TRADE
            return self.calculate_trade_win_rate(returns)


def calculate_win_rate_standardized(
    returns: Union[np.ndarray, List[float]],
    method: str = "trade",
    signals: np.ndarray | None = None,
    include_zeros: bool = False,
) -> float:
    """
    Convenience function for standardized win rate calculation.

    Args:
        returns: Array or list of returns
        method: Calculation method ("trade", "signal", "legacy")
        signals: Signal array (required for signal method)
        include_zeros: Whether to include zero returns

    Returns:
        Calculated win rate as float
    """
    calc = WinRateCalculator()
    returns_array = np.array(returns)

    if method == "signal":
        if signals is None:
            raise ValueError("Signals array required for signal method")
        result = calc.calculate_signal_win_rate(
            returns_array, np.array(signals), include_zeros
        )
    elif method == "legacy":
        return calc.calculate_legacy_win_rate(returns_array)
    else:  # trade
        result = calc.calculate_trade_win_rate(returns_array, include_zeros)

    return result.win_rate
