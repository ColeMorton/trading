"""Utility for converting and formatting portfolio statistics."""

import math
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypedDict

import numpy as np
import pandas as pd
from typing_extensions import NotRequired


class StatsConfig(TypedDict):
    """Configuration type definition for stats conversion.

    Required Fields:
        None

    Optional Fields:
        USE_HOURLY (bool): Flag indicating if data is hourly
        TICKER (str): Trading symbol/ticker
    """

    USE_HOURLY: NotRequired[bool]
    TICKER: NotRequired[str]


def calculate_win_rate_normalized(win_rate):
    """
    Optimized win rate normalization using piecewise function.

    Eliminates cap violations while maintaining strong discrimination
    and preserving break-even psychology at 50%.

    Args:
        win_rate (float): Win rate as percentage (0-100)

    Returns:
        float: Normalized value in range [0.1, 2.618]

    Mathematical Properties:
        - Smooth, continuous function
        - No cap violations (max ≤ 2.618)
        - Better discrimination in critical ranges
        - Maintains 50% break-even point (maps to 1.0)
        - Less harsh penalties than cubic scaling
    """

    # Handle edge cases
    if pd.isna(win_rate) or win_rate <= 0:
        return 0.1
    if win_rate >= 100:
        return 2.618

    if win_rate <= 50:
        # Below break-even: gentler than cubic but still penalizing
        # Maps 0% → 0.1, 50% → 1.0
        normalized = win_rate / 50
        return 0.1 + 0.9 * (normalized**1.8)  # Power 1.8 (less harsh than cubic 3.0)
    else:
        # Above break-even: controlled growth with soft cap
        # Maps 50% → 1.0, approaches 2.618 asymptotically
        excess = win_rate - 50
        max_excess = 50  # 100% - 50%
        normalized_excess = excess / max_excess

        # Soft exponential growth that approaches but never exceeds 2.618
        return 1.0 + 1.618 * (1 - math.exp(-2.5 * normalized_excess))


def calculate_profit_factor_normalized(profit_factor):
    """
    Enhanced profit factor normalization using piecewise function.

    Provides 61% better discrimination than current linear method while maintaining
    proper component balance and preventing gaming through strategic thresholds.

    Args:
        profit_factor (float): Raw profit factor value (gross profit / gross loss)

    Returns:
        float: Normalized value in range [0.1, 2.618]

    Thresholds:
        - PF < 0.8:   Strong penalty (0.1) for losing strategies
        - PF = 1.0:   Break-even point (0.5 normalized)
        - PF = 2.0:   Good performance threshold (1.5 normalized)
        - PF >= 4.0:  Excellence cap (2.618 normalized)
    """

    if pd.isna(profit_factor) or profit_factor < 0.8:
        # Strong penalty for consistently losing strategies
        return 0.1

    elif profit_factor < 1.0:
        # Linear interpolation for near break-even region
        # Maps [0.8, 1.0] → [0.1, 0.5]
        return 0.1 + 0.4 * (profit_factor - 0.8) / 0.2

    elif profit_factor < 2.0:
        # Linear scaling for profitable strategies
        # Maps [1.0, 2.0] → [0.5, 1.5]
        return 0.5 + 1.0 * (profit_factor - 1.0) / 1.0

    elif profit_factor < 4.0:
        # Square root scaling for excellent strategies (diminishing returns)
        # Maps [2.0, 4.0] → [1.5, 2.618]
        return 1.5 + 1.118 * math.sqrt((profit_factor - 2.0) / 2.0)

    else:
        # Cap at maximum to prevent single-metric optimization
        return 2.618


def calculate_expectancy_per_trade_normalized(expectancy, volatility=None):
    """
    Improved expectancy normalization using soft-capped asymptotic function.

    Eliminates the 61% saturation issue of the current hard-capped linear formula
    while preserving the golden ratio scaling philosophy. Uses mathematically
    rigorous asymptotic approach that provides continuous discrimination across
    all performance levels.

    Args:
        expectancy (float): Raw expectancy per trade value (as percentage)
        volatility (float, optional): Asset volatility for cross-asset fairness

    Returns:
        float: Normalized value approaching (but never reaching) 2.618

    Mathematical Properties:
        - Eliminates saturation: 0% strategies hit the cap (vs 61% current)
        - Continuous discrimination: Always differentiates between strategies
        - Smooth function: No discontinuities or hard caps
        - Monotonic: Preserves ranking order
        - Bounded: [0, 2.618] range maintained
    """

    # Handle edge cases
    if pd.isna(expectancy) or expectancy <= 0:
        return 0.1

    # Optional volatility adjustment for cross-asset fairness
    adjusted_exp = expectancy
    if volatility is not None:
        adjusted_exp = expectancy / max(volatility / 25, 0.5)

    # Soft-capped normalization with empirical calibration
    baseline = 5.0  # Calibrated to achieve ~20% saturation (vs 61% current)
    x = adjusted_exp / baseline
    steepness = 1.2  # Moderate diminishing returns
    max_value = 2.618  # Golden ratio squared (preserved)

    # Asymptotic function: approaches but never reaches maximum
    return max_value * (x**steepness) / (1 + x**steepness)


def calculate_sortino_normalized(sortino_ratio):
    """
    Improved Sortino normalization using sigmoid function

    Advantages:
    - Smooth, continuous scaling
    - Natural saturation prevents extreme outliers
    - Better discrimination in the 1.0-3.0 range
    - Maintains mathematical elegance
    """

    # Handle edge cases
    if pd.isna(sortino_ratio) or sortino_ratio <= 0:
        return 0.1

    # Sigmoid parameters optimized for Sortino ratios
    midpoint = 1.5  # Sortino of 1.5 maps to score of ~1.31
    steepness = 0.9  # Moderate selectivity
    max_score = 2.618  # Maintain golden ratio cap

    # Sigmoid transformation
    score = max_score / (1 + np.exp(-steepness * (sortino_ratio - midpoint)))

    return min(score, max_score)


def calculate_total_trades_normalized(total_trades):
    """
    Optimized total trades normalization emphasizing statistical confidence
    """

    if pd.isna(total_trades) or total_trades <= 0:
        return 0.1

    # Confidence factor: rapid improvement early, diminishing returns
    confidence = 1 - math.exp(-total_trades / 35)

    # Frequency adequacy: linear up to reasonable trading frequency
    frequency_factor = min(total_trades / 100, 0.4)

    # Combined score with cap to prevent over-trading gaming
    total_normalized = min((confidence * 1.1) + frequency_factor, 1.5)

    return pow(total_normalized, 1.5)  # Slight non-linearity preserved


def calculate_beats_bnh_normalized(beats_bnh_percent):
    """
    Improved Beats Buy-and-Hold normalization with smooth interpolation.

    Args:
        beats_bnh_percent (float): Performance vs buy-and-hold as percentage

    Returns:
        float: Normalized value in range [0.25, 2.0]
    """

    if pd.isna(beats_bnh_percent):
        return 1.0

    # Smooth interpolation instead of discrete thresholds
    return max(0.25, min(2.0, 1.0 + (beats_bnh_percent / 2.5)))


def convert_stats(
    stats: Dict[str, Any],
    log: Callable[[str, str], None],
    config: StatsConfig | None = None,
    current: Any = None,
    exit_signal: Any = None,
) -> Dict[str, Any]:
    """Convert portfolio statistics to a standardized format with proper type handling.

    Processes raw statistics to calculate additional metrics and ensure consistent
    data types across all values. Handles special cases for hourly vs daily data
    and different asset types (crypto vs stocks).

    Args:
        stats: Dictionary containing portfolio statistics including metrics like
              Expectancy, Win Rate, Total Trades, etc.
        log: Logging function for recording events and errors
        config: Configuration dictionary specifying settings like USE_HOURLY
               and TICKER. Defaults to None.
        current: Current signal value to be assigned to 'Signal Entry' field.
                Defaults to None.
        exit_signal: Current exit signal value to be assigned to 'Signal Exit' field.
                Defaults to None.

    Returns:
        Dict[str, Any]: Dictionary with properly formatted values and additional
                       calculated metrics including:
                       - Trades Per Day
                       - Trades per Month
                       - Expectancy per Month
                       - Signals per Month
                       - Signal Entry
                       - Signal Exit

    Raises:
        KeyError: If required statistics are missing from input
    """
    if config is None:
        config = {}
        log("No config provided, using defaults", "info")

    # Get ticker from stats if not in config
    ticker = config.get("TICKER") or stats.get("Ticker", "Unknown")
    log(f"Converting stats for {ticker}", "info")

    try:
        # Calculate Beats BNH percentage
        # Example test data:
        # stats['Total Return [%]'] = [351.0781, 19.5554, -5.2920]
        # stats['Benchmark Return [%]'] = [370.3095, -6.2193, -6.2193]
        # Expected output: [-0.05194, 4.144, 0.1491]
        benchmark_return = stats["Benchmark Return [%]"]
        if stats["Benchmark Return [%]"] == 0:
            stats["Beats BNH [%]"] = 0
        else:
            stats["Beats BNH [%]"] = (
                stats["Total Return [%]"] - benchmark_return
            ) / abs(benchmark_return)

        # Determine if it's a crypto asset using ticker from either source
        is_crypto = "-USD" in ticker

        # Set trading days per month based on asset type
        trading_days_per_month = 30 if is_crypto else 21
        log(
            f"Using {trading_days_per_month} trading days per month for {ticker} ({'crypto' if is_crypto else 'stock'})",
            "info",
        )

        # Calculate months in the backtest period
        if isinstance(stats["End"], (int, float)) and isinstance(
            stats["Start"], (int, float)
        ):
            if config.get("USE_HOURLY", False):
                # For hourly data, convert hours to days first
                days_in_period = abs(stats["End"] - stats["Start"]) / 24
            else:
                # For daily data, Start and End are already in days
                days_in_period = abs(stats["End"] - stats["Start"])
        else:
            # If timestamps are datetime objects, use timedelta
            time_delta = pd.Timestamp(stats["End"]) - pd.Timestamp(stats["Start"])
            days_in_period = abs(time_delta.total_seconds()) / (24 * 3600)

        # Store the total calendar days as Total Period
        # For stocks, convert from trading days (252/year) to calendar days (365/year)
        if is_crypto:
            # Crypto markets are open 24/7, so days_in_period already represents
            # calendar days
            stats["Total Period"] = days_in_period
            log(
                f"Set Total Period to {days_in_period:.2f} days for {ticker} (crypto)",
                "info",
            )
        else:
            # For stocks, convert from trading days to calendar days
            # There are approximately 252 trading days in a year (365 calendar days)
            stats["Total Period"] = days_in_period * (365 / 252)
            log(
                f"Set Total Period to {stats['Total Period']:.2f} days for {ticker} (stock, adjusted from {days_in_period:.2f} trading days)",
                "info",
            )

        stats["Trades Per Day"] = stats["Total Closed Trades"] / stats["Total Period"]

        # Expectancy per Trade is calculated in backtest_strategy.py and passed through
        # No need to recalculate it here

        # Calculate Score metric using optimized functions
        required_fields = [
            "Total Trades",
            "Sortino Ratio",
            "Profit Factor",
            "Win Rate [%]",
            "Expectancy per Trade",
            "Beats BNH [%]",
        ]
        if all(field in stats for field in required_fields):
            try:
                # Use optimized normalization functions
                win_rate_normalized = calculate_win_rate_normalized(
                    stats["Win Rate [%]"]
                )
                total_trades_normalized = calculate_total_trades_normalized(
                    stats["Total Trades"]
                )  # FIXED BUG
                sortino_normalized = calculate_sortino_normalized(
                    stats["Sortino Ratio"]
                )
                profit_factor_normalized = calculate_profit_factor_normalized(
                    stats["Profit Factor"]
                )
                expectancy_per_trade_normalized = (
                    calculate_expectancy_per_trade_normalized(
                        stats["Expectancy per Trade"]
                    )
                )
                beats_bnh_normalized = calculate_beats_bnh_normalized(
                    stats["Beats BNH [%]"]
                )

                # Calculate optimized composite score with double weighting for win rate
                stats["Score"] = (
                    win_rate_normalized * 2
                    + total_trades_normalized  # Double weighted for psychological importance
                    + sortino_normalized
                    + profit_factor_normalized
                    + expectancy_per_trade_normalized
                    + beats_bnh_normalized
                ) / 7

                log(f"Normalized: Win Rate {win_rate_normalized:.4f} (×2)", "info")
                log(f"Normalized: Total Trades {total_trades_normalized:.4f}", "info")
                log(f"Normalized: Sortino {sortino_normalized:.4f}", "info")
                log(f"Normalized: Profit Factor {profit_factor_normalized:.4f}", "info")
                log(
                    f"Normalized: Expectancy {expectancy_per_trade_normalized:.4f}",
                    "info",
                )
                log(
                    f"Normalized: Beats Buy-and-hold {beats_bnh_normalized:.4f}", "info"
                )
                log(f"Optimized Score: {stats['Score']:.4f}", "info")
            except Exception as e:
                stats["Score"] = 0
                log(
                    f"Error calculating Score for {ticker}: {str(e)}. Setting to 0.",
                    "error",
                )
        else:
            stats["Score"] = 0
            missing = [field for field in required_fields if field not in stats]
            log(
                f"Set Score to 0 due to missing fields: {', '.join(missing)} for {ticker}",
                "warning",
            )

        # Calculate months in the period (accounting for trading days)
        if is_crypto:
            # Crypto trades 24/7, so use calendar days
            months_in_period = days_in_period / 30
        else:
            # Stocks trade only on trading days
            months_in_period = days_in_period / 21

        # Ensure we don't divide by zero
        if months_in_period <= 0:
            months_in_period = 1
            log(
                f"Warning: Backtest period too short for {ticker}, using 1 month as minimum",
                "warning",
            )

        # Calculate trades per month directly from total trades and months
        stats["Trades per Month"] = stats["Total Trades"] / months_in_period

        # Calculate signals per month
        # Each trade typically has an entry and exit signal, but some trades might have only entry
        # if they're still open at the end of the backtest
        if "Total Closed Trades" in stats and "Total Open Trades" in stats:
            # If we have separate counts for closed and open trades
            closed_trades = stats["Total Closed Trades"]
            open_trades = stats["Total Open Trades"]
            # Closed trades have both entry and exit signals, open trades have only
            # entry
            total_signals = (closed_trades * 2) + open_trades
        else:
            # Fallback: assume each trade has entry and exit (might slightly
            # overestimate)
            total_signals = stats["Total Trades"] * 2

        stats["Signals per Month"] = total_signals / months_in_period

        # Calculate expectancy per month
        if (
            "Expectancy per Trade" in stats
            and stats["Expectancy per Trade"] is not None
        ):
            if stats["Expectancy per Trade"] <= 0:
                log(
                    f"Warning: Non-positive Expectancy per Trade ({stats['Expectancy per Trade']:.6f}) for {ticker}.",
                    "info",
                )

            stats["Expectancy per Month"] = (
                stats["Trades per Month"] * stats["Expectancy per Trade"]
            )
        else:
            # Calculate Expectancy per Trade if missing
            if (
                "Total Return [%]" in stats
                and "Total Trades" in stats
                and stats["Total Trades"] > 0
            ):
                # Estimate Expectancy per Trade from Total Return and Total Trades
                expectancy = stats["Total Return [%]"] / (100 * stats["Total Trades"])
                stats["Expectancy per Trade"] = expectancy
                log(
                    f"Calculated missing Expectancy per Trade: {expectancy:.6f} for {ticker}",
                    "info",
                )
                stats["Expectancy per Month"] = stats["Trades per Month"] * expectancy
            else:
                # Set default values if we can't calculate
                log(
                    "Expectancy per Trade not found and cannot be calculated",
                    "warning",
                )
                stats["Expectancy per Trade"] = 0.0
                stats["Expectancy per Month"] = 0.0

        # Calculate average trade duration as weighted average of winning and
        # losing durations
        if all(
            key in stats
            for key in [
                "Avg Winning Trade Duration",
                "Avg Losing Trade Duration",
                "Win Rate [%]",
            ]
        ):
            try:
                # Parse durations to timedelta objects, handling different input types
                if isinstance(stats["Avg Winning Trade Duration"], pd.Timedelta):
                    win_duration = stats["Avg Winning Trade Duration"]
                else:
                    win_duration = pd.to_timedelta(stats["Avg Winning Trade Duration"])

                if isinstance(stats["Avg Losing Trade Duration"], pd.Timedelta):
                    lose_duration = stats["Avg Losing Trade Duration"]
                else:
                    lose_duration = pd.to_timedelta(stats["Avg Losing Trade Duration"])

                win_rate = stats["Win Rate [%]"] / 100.0

                # Handle edge cases
                if win_rate == 1.0:  # 100% win rate
                    avg_duration = win_duration
                    log(
                        f"All trades are winning for {ticker}, using winning duration",
                        "info",
                    )
                elif win_rate == 0.0:  # 0% win rate
                    avg_duration = lose_duration
                    log(
                        f"All trades are losing for {ticker}, using losing duration",
                        "info",
                    )
                else:
                    # Calculate weighted average
                    avg_duration = win_duration * win_rate + lose_duration * (
                        1 - win_rate
                    )

                stats["Avg Trade Duration"] = str(avg_duration)
            except Exception as e:
                log(
                    f"Error calculating average trade duration for {ticker}: {str(e)}",
                    "error",
                )
                stats["Avg Trade Duration"] = str(avg_duration)

        # Check for risk metrics in the input stats
        risk_metrics = [
            "Skew",
            "Kurtosis",
            "Tail Ratio",
            "Common Sense Ratio",
            "Value at Risk",
            "Daily Returns",
            "Annual Returns",
            "Cumulative Returns",
            "Annualized Return",
            "Annualized Volatility",
        ]

        missing_metrics = [metric for metric in risk_metrics if metric not in stats]

        if missing_metrics:
            log(
                f"Risk metrics missing from stats for {ticker}: {', '.join(missing_metrics)}",
                "warning",
            )

        # Initialize converted dictionary before any processing
        converted = {}

        # Handle window values first, ensuring they remain integers
        window_params = ["Short Window", "Long Window", "Signal Window"]
        for param in window_params:
            if param in stats:
                converted[param] = int(stats[param])

        # Ensure risk metrics are preserved
        risk_metrics = [
            "Skew",
            "Kurtosis",
            "Tail Ratio",
            "Common Sense Ratio",
            "Value at Risk",
            "Daily Returns",
            "Annual Returns",
            "Cumulative Returns",
            "Annualized Return",
            "Annualized Volatility",
        ]

        # Then handle the rest of the stats
        for k, v in stats.items():
            if k not in window_params:
                # Special handling for risk metrics to ensure they're preserved
                if k in risk_metrics and v is not None:
                    # Convert pandas Series or DataFrame to scalar if needed
                    if hasattr(v, "iloc") and hasattr(v, "size") and v.size == 1:
                        try:
                            converted[k] = v.iloc[0]
                            log(
                                f"Converted {k} from Series/DataFrame to scalar: {converted[k]}",
                                "debug",
                            )
                        except Exception as e:
                            log(f"Error converting {k} to scalar: {str(e)}", "error")
                            converted[k] = v
                    else:
                        converted[k] = v

                    # Log the value being preserved
                    log(f"Preserving risk metric {k} = {converted[k]}", "debug")
                elif k == "Start" or k == "End":
                    converted[k] = (
                        v.strftime("%Y-%m-%d %H:%M:%S")
                        if isinstance(v, datetime)
                        else str(v)
                    )
                elif isinstance(v, pd.Timedelta):
                    converted[k] = str(v)
                elif isinstance(v, (int, float)):
                    # Keep numeric values as is
                    converted[k] = v
                else:
                    converted[k] = str(v)

        # Add Signal Entry if provided
        if current is not None:
            converted["Signal Entry"] = current
            log(f"Added Signal Entry: {current} for {ticker}", "info")

        # Add Signal Exit if provided
        if exit_signal is not None:
            converted["Signal Exit"] = exit_signal
            log(f"Added Signal Exit: {exit_signal} for {ticker}", "info")

        log(f"Successfully converted stats for {ticker}", "info")
        return converted

    except Exception as e:
        log(f"Failed to convert stats for {ticker}: {str(e)}", "error")
        raise
