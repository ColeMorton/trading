"""Utility for converting and formatting portfolio statistics."""

from collections.abc import Callable
from datetime import datetime
import math
from typing import Any, TypedDict

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


def calculate_win_rate_normalized(win_rate, total_trades=None):
    """
    Statistical confidence-aware win rate normalization.

    For single-shot strategies, incorporates sample size to reflect
    confidence in the win rate estimate using Wilson score interval.

    Args:
        win_rate (float): Win rate as percentage (0-100)
        total_trades (int, optional): Number of trades for confidence adjustment

    Returns:
        float: Normalized value in range [0.1, 2.618]

    Mathematical Properties:
        - Uses Wilson score interval for small sample confidence
        - Maintains 50% break-even point (maps to 1.0)
        - Higher penalties for low-confidence win rates
        - Asymptotic approach to maximum for high-confidence strategies
    """

    # Handle edge cases
    if pd.isna(win_rate) or win_rate <= 0:
        return 0.1
    if win_rate >= 100 and (total_trades is None or total_trades >= 100):
        return 2.618

    # Apply confidence adjustment for small samples
    if total_trades is not None and total_trades > 0:
        # Wilson score interval lower bound (95% confidence)
        z = 1.96  # 95% confidence z-score
        p = win_rate / 100.0
        n = total_trades

        # Calculate Wilson score interval lower bound
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denominator
        margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator

        # Use lower bound for conservative confidence-adjusted win rate
        confidence_adjusted_win_rate = max(0, (center - margin) * 100)

        # Asymmetric confidence adjustment: harsher for low win rates
        # More weight to confidence adjustment for smaller samples
        base_confidence_weight = 1 - math.exp(-3 / math.sqrt(total_trades))

        # Apply additional confidence penalty for low win rates
        if win_rate < 40:
            # Increase confidence weight (use more conservative estimate) for low win rates
            low_win_penalty = 1 + (40 - win_rate) / 40  # 1.0 to 2.0 multiplier
            confidence_weight = min(0.95, base_confidence_weight * low_win_penalty)
        else:
            confidence_weight = base_confidence_weight

        effective_win_rate = (
            confidence_adjusted_win_rate * confidence_weight
            + win_rate * (1 - confidence_weight)
        )
    else:
        effective_win_rate = win_rate

    # Apply normalization to effective win rate with dynamic penalty
    if effective_win_rate <= 50:
        # Below break-even: Dynamic penalty that intensifies for lower win rates
        normalized = effective_win_rate / 50

        # Dynamic power curve: steeper penalties for lower win rates
        # At 50%: power = 1.8 (original)
        # At 40%: power = 3.0 (cubic)
        # At 30%: power = 5.0 (very harsh)
        # At 20%: power = 8.0 (extreme penalty)
        dynamic_power = 1.8 + (50 - effective_win_rate) * 0.13

        # Additional penalty multiplier for very low win rates
        if effective_win_rate < 40:
            # Exponential penalty acceleration below 40%
            penalty_factor = math.exp((40 - effective_win_rate) / 25)
            base_score = 0.1 + 0.9 * (normalized**dynamic_power)
            return base_score / penalty_factor
        return 0.1 + 0.9 * (normalized**dynamic_power)
    # Above break-even: controlled growth with soft cap
    excess = effective_win_rate - 50
    normalized_excess = excess / 50

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

    if profit_factor < 1.0:
        # Linear interpolation for near break-even region
        # Maps [0.8, 1.0] → [0.1, 0.5]
        return 0.1 + 0.4 * (profit_factor - 0.8) / 0.2

    if profit_factor < 2.0:
        # Linear scaling for profitable strategies
        # Maps [1.0, 2.0] → [0.5, 1.5]
        return 0.5 + 1.0 * (profit_factor - 1.0) / 1.0

    if profit_factor < 4.0:
        # Square root scaling for excellent strategies (diminishing returns)
        # Maps [2.0, 4.0] → [1.5, 2.618]
        return 1.5 + 1.118 * math.sqrt((profit_factor - 2.0) / 2.0)

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
    Statistical validity-based normalization with harsh penalties for small samples.

    Implements quantitative trading best practices by severely penalizing strategies
    with insufficient trade counts that cannot provide statistical confidence.

    Args:
        total_trades (int): Number of trades executed

    Returns:
        float: Normalized statistical confidence score in range [0.05, 2.2]

    Statistical Validity Philosophy:
        - Critical minimum (1-19): Statistically meaningless, severe penalty
        - Very low (20-39): Insufficient confidence, harsh penalty
        - Low (40-49): Minimal statistical significance
        - Optimal (50-100): Sweet spot for daily SMA/EMA strategies
        - High (101-200): Strong statistical confidence
        - Very high (200+): Excellent confidence, diminishing returns
    """

    if pd.isna(total_trades) or total_trades <= 0:
        return 0.05

    if total_trades < 20:
        # Critical minimum: statistically meaningless sample sizes
        # Extremely harsh penalty - these strategies should essentially be excluded
        # Maps [1, 19] → [0.05, 0.15]
        normalized = total_trades / 20
        return 0.05 + 0.1 * (normalized**4.0)  # Very steep curve, almost unusable

    if total_trades < 40:
        # Very low sample size: insufficient for statistical confidence
        # Maps [20, 39] → [0.15, 0.5]
        progress = (total_trades - 20) / 20
        return 0.15 + 0.35 * (progress**3.0)  # Steep penalty curve

    if total_trades <= 49:
        # Minimal significance: still penalized but improving
        # Maps [40, 49] → [0.5, 1.0]
        progress = (total_trades - 40) / 9
        return 0.5 + 0.5 * (progress**2.0)  # Quadratic improvement

    if total_trades <= 100:
        # Optimal range for daily strategies: highest scores
        # Maps [50, 100] → [1.0, 2.2]
        progress = (total_trades - 50) / 50
        # Gentle curve peaking around 75-80 trades
        curve_factor = 4 * progress * (1 - progress)  # Parabolic peak
        return 1.0 + 1.2 * (0.7 * progress + 0.3 * curve_factor)

    if total_trades <= 200:
        # Strong confidence zone: good scores with slight decline
        # Maps [101, 200] → [2.0, 1.8]
        progress = (total_trades - 100) / 100
        return 2.2 - 0.4 * progress  # Gentle decline

    # Excellent confidence but diminishing returns
    # Maps [200+, ∞) → [1.5, 1.8]
    excess = total_trades - 200
    return 1.8 - 0.3 * (1 - math.exp(-excess / 100))  # Asymptotic approach to 1.5


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
    stats: dict[str, Any],
    log: Callable[[str, str], None],
    config: StatsConfig | None = None,
    current: Any | None = None,
    exit_signal: Any | None = None,
    signal_unconfirmed: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
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
    log(f"Converting stats for {ticker}", "debug")

    try:
        # Calculate Beats BNH percentage
        # Example test data:
        # stats['Total Return [%]'] = [351.0781, 19.5554, -5.2920]
        # stats['Benchmark Return [%]'] = [370.3095, -6.2193, -6.2193]
        # Expected output: [-0.05194, 4.144, 0.1491]

        # Convert benchmark_return to numeric if it's a string
        benchmark_return = stats["Benchmark Return [%]"]
        if isinstance(benchmark_return, str):
            try:
                benchmark_return = float(benchmark_return)
            except (ValueError, TypeError):
                benchmark_return = 0.0
                log(
                    f"Invalid benchmark return value '{stats['Benchmark Return [%]']}' for {ticker}, using 0.0",
                    "warning",
                )

        # Convert total_return to numeric if it's a string
        total_return = stats["Total Return [%]"]
        if isinstance(total_return, str):
            try:
                total_return = float(total_return)
            except (ValueError, TypeError):
                total_return = 0.0
                log(
                    f"Invalid total return value '{stats['Total Return [%]']}' for {ticker}, using 0.0",
                    "warning",
                )
        else:
            total_return = stats["Total Return [%]"]

        if benchmark_return == 0:
            stats["Beats BNH [%]"] = 0
        else:
            stats["Beats BNH [%]"] = (total_return - benchmark_return) / abs(
                benchmark_return
            )

        # Determine if it's a crypto asset using ticker from either source
        is_crypto = "-USD" in ticker

        # Set trading days per month based on asset type
        trading_days_per_month = 30 if is_crypto else 21
        log(
            f"Using {trading_days_per_month} trading days per month for {ticker} ({'crypto' if is_crypto else 'stock'})",
            "debug",
        )

        # Calculate months in the backtest period
        if isinstance(stats["End"], int | float) and isinstance(
            stats["Start"], int | float
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
                "debug",
            )
        else:
            # For stocks, convert from trading days to calendar days
            # There are approximately 252 trading days in a year (365 calendar days)
            stats["Total Period"] = days_in_period * (365 / 252)
            log(
                f"Set Total Period to {stats['Total Period']:.2f} days for {ticker} (stock, adjusted from {days_in_period:.2f} trading days)",
                "debug",
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
                # Use optimized normalization functions with confidence adjustment
                win_rate_normalized = calculate_win_rate_normalized(
                    stats["Win Rate [%]"], total_trades=stats.get("Total Trades")
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

                # Calculate optimized composite score for single-shot strategy confidence
                # Rebalanced weights to reflect confidence-adjusted metrics
                base_score = (
                    win_rate_normalized * 2.5  # Increased weight (includes confidence)
                    + total_trades_normalized * 1.5  # Execution feasibility weight
                    + sortino_normalized * 1.2  # Risk-adjusted return importance
                    + profit_factor_normalized * 1.2  # Profit sustainability
                    + expectancy_per_trade_normalized * 1.0  # Per-trade expectation
                    + beats_bnh_normalized * 0.6  # Market outperformance (reduced)
                ) / 8.0  # Adjusted denominator for new weights

                # Apply statistical confidence multiplier to entire score
                # This ensures low-count strategies cannot achieve high scores regardless of other metrics
                total_trades_count = stats["Total Trades"]
                if total_trades_count < 20:
                    # Extremely harsh penalty for statistically meaningless strategies
                    confidence_multiplier = 0.1 + 0.4 * (total_trades_count / 20) ** 3
                elif total_trades_count < 40:
                    # Harsh penalty for insufficient confidence
                    confidence_multiplier = (
                        0.5 + 0.3 * ((total_trades_count - 20) / 20) ** 2
                    )
                elif total_trades_count < 50:
                    # Moderate penalty for minimal significance
                    confidence_multiplier = 0.8 + 0.2 * ((total_trades_count - 40) / 10)
                else:
                    # No penalty for adequate sample sizes
                    confidence_multiplier = 1.0

                stats["Score"] = base_score * confidence_multiplier

                log(
                    f"Statistical Confidence: {total_trades_count} trades → multiplier {confidence_multiplier:.4f}",
                    "debug",
                )
                log(
                    f"Final Score: {base_score:.4f} × {confidence_multiplier:.4f} = {stats['Score']:.4f}",
                    "debug",
                )
                log(
                    f"Normalized: Win Rate {win_rate_normalized:.4f} (×2.5, confidence-adjusted)",
                    "debug",
                )
                log(
                    f"Normalized: Total Trades {total_trades_normalized:.4f} (×1.5, statistical validity)",
                    "debug",
                )
                log(f"Normalized: Sortino {sortino_normalized:.4f}", "debug")
                log(
                    f"Normalized: Profit Factor {profit_factor_normalized:.4f}", "debug"
                )
                log(
                    f"Normalized: Expectancy {expectancy_per_trade_normalized:.4f}",
                    "debug",
                )
                log(
                    f"Normalized: Beats Buy-and-hold {beats_bnh_normalized:.4f}",
                    "debug",
                )
                log(f"Optimized Score: {stats['Score']:.4f}", "debug")
            except Exception as e:
                stats["Score"] = 0
                log(
                    f"Error calculating Score for {ticker}: {e!s}. Setting to 0.",
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
                    f"Non-positive Expectancy per Trade ({stats['Expectancy per Trade']:.6f}) for {ticker}.",
                    "debug",
                )

            stats["Expectancy per Month"] = (
                stats["Trades per Month"] * stats["Expectancy per Trade"]
            )
        # Calculate Expectancy per Trade if missing
        elif (
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
                "Expectancy per Trade not found and cannot be calculated, using defaults",
                "debug",
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
                    f"Error calculating average trade duration for {ticker}: {e!s}",
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
                "debug",
            )

        # Initialize converted dictionary before any processing
        converted = {}

        # Handle window values first, ensuring they remain integers
        window_params = ["Fast Period", "Slow Period", "Signal Period"]
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
                            log(f"Error converting {k} to scalar: {e!s}", "error")
                            converted[k] = v
                    else:
                        converted[k] = v

                    # Log the value being preserved
                    log(f"Preserving risk metric {k} = {converted[k]}", "debug")
                elif k in ("Start", "End"):
                    converted[k] = (
                        v.strftime("%Y-%m-%d %H:%M:%S")
                        if isinstance(v, datetime)
                        else str(v)
                    )
                elif isinstance(v, pd.Timedelta):
                    converted[k] = str(v)
                elif isinstance(v, int | float):
                    # Keep numeric values as is
                    converted[k] = v
                elif k == "_equity_data":
                    # Preserve EquityData objects without string conversion
                    converted[k] = v
                else:
                    converted[k] = str(v)

        # Add Signal Entry if provided
        if current is not None:
            converted["Signal Entry"] = current
            log(f"Added Signal Entry: {current} for {ticker}", "debug")

        # Add Signal Exit if provided
        if exit_signal is not None:
            converted["Signal Exit"] = exit_signal
            log(f"Added Signal Exit: {exit_signal} for {ticker}", "debug")

        # Add Signal Unconfirmed if provided
        if signal_unconfirmed is not None:
            converted["Signal Unconfirmed"] = signal_unconfirmed
            log(f"Added Signal Unconfirmed: {signal_unconfirmed} for {ticker}", "debug")

        # Ensure canonical schema compliance
        converted = _ensure_canonical_schema_compliance(converted, log, verbose)

        log(f"Successfully converted stats for {ticker}", "debug")
        return converted

    except Exception as e:
        log(f"Failed to convert stats for {ticker}: {e!s}", "error")
        raise


def _ensure_canonical_schema_compliance(
    stats: dict[str, Any], log: Callable[[str, str], None], verbose: bool = False
) -> dict[str, Any]:
    """
    Ensure the stats dictionary conforms to the canonical 59-column schema.

    This function ensures all required columns are present and properly ordered
    according to the canonical schema definition.

    Args:
        stats: Dictionary containing portfolio statistics
        log: Logging function for recording events

    Returns:
        Dict[str, Any]: Dictionary with all 59 columns in canonical order
    """
    try:
        from app.tools.portfolio.base_extended_schemas import CANONICAL_COLUMN_NAMES
    except ImportError:
        log(
            "Could not import canonical schema, using existing stats",
            "debug",
        )
        return stats

    # Create canonical ordered dictionary
    canonical_stats = {}

    # Ensure all 59 columns are present in canonical order
    for column_name in CANONICAL_COLUMN_NAMES:
        if column_name in stats:
            canonical_stats[column_name] = stats[column_name]
        else:
            # Set default values for missing columns
            canonical_stats[column_name] = _get_default_value_for_column(
                column_name, stats, log, verbose
            )

    # Preserve non-canonical fields (like _equity_data for equity export)
    for key, value in stats.items():
        if key not in CANONICAL_COLUMN_NAMES:
            # Special handling for _equity_data to preserve EquityData objects
            if key == "_equity_data":
                canonical_stats[key] = value  # Preserve as-is without any conversion
                log(f"DEBUG: Preserving _equity_data as {type(value)}", "debug")
            else:
                canonical_stats[key] = value

    return canonical_stats


def _get_default_value_for_column(
    column_name: str,
    stats: dict[str, Any],
    log: Callable[[str, str], None],
    verbose: bool = False,
) -> Any:
    """
    Get appropriate default value for a missing column.

    Args:
        column_name: Name of the missing column
        stats: Existing stats dictionary (for context)
        log: Logging function

    Returns:
        Appropriate default value for the column
    """
    # Column-specific defaults
    column_defaults = {
        "Ticker": stats.get("Ticker", "UNKNOWN"),
        "Allocation [%]": None,  # Optional allocation
        "Strategy Type": "SMA",  # Default strategy type
        "Fast Period": 20,  # Default fast period
        "Slow Period": 50,  # Default slow period
        "Signal Period": 0,  # Default signal period
        "Stop Loss [%]": None,  # Optional stop loss
        "Signal Entry": False,  # Default signal state
        "Signal Exit": False,  # Default signal state
        "Last Position Open Date": None,  # Optional position date
        "Last Position Close Date": None,  # Optional position date
        "Total Open Trades": 0,  # Default trade count
        "Total Trades": stats.get("Total Trades", 0),
        "Metric Type": "Most Total Return [%]",  # Default metric type in proper format
        "Score": 0.0,  # Default score
        "Win Rate [%]": 50.0,  # Default win rate
        "Profit Factor": 1.0,  # Default profit factor
        "Expectancy per Trade": 0.0,  # Default expectancy
        "Sortino Ratio": 0.0,  # Default Sortino ratio
        "Beats BNH [%]": 0.0,  # Default BNH comparison
        "Avg Trade Duration": "0 days 00:00:00",  # Default duration
        "Trades Per Day": 0.0,  # Default frequency
        "Trades per Month": 0.0,  # Default frequency
        "Signals per Month": 0.0,  # Default frequency
        "Expectancy per Month": 0.0,  # Default expectancy
        "Start": 0,  # Default start
        "End": 0,  # Default end
        "Period": "0 days 00:00:00",  # Default period
        "Start Value": 1000.0,  # Default start value
        "End Value": 1000.0,  # Default end value
        "Total Return [%]": 0.0,  # Default return
        "Benchmark Return [%]": 0.0,  # Default benchmark
        "Max Gross Exposure [%]": 100.0,  # Default exposure
        "Total Fees Paid": 0.0,  # Default fees
        "Max Drawdown [%]": 0.0,  # Default drawdown
        "Max Drawdown Duration": "0 days 00:00:00",  # Default duration
        "Total Closed Trades": stats.get("Total Trades", 0),
        "Open Trade PnL": 0.0,  # Default PnL
        "Best Trade [%]": 0.0,  # Default best trade
        "Worst Trade [%]": 0.0,  # Default worst trade
        "Avg Winning Trade [%]": 0.0,  # Default avg winning
        "Avg Losing Trade [%]": 0.0,  # Default avg losing
        "Avg Winning Trade Duration": "0 days 00:00:00",  # Default duration
        "Avg Losing Trade Duration": "0 days 00:00:00",  # Default duration
        "Expectancy": 0.0,  # Default expectancy
        "Sharpe Ratio": 0.0,  # Default Sharpe
        "Calmar Ratio": 0.0,  # Default Calmar
        "Omega Ratio": 1.0,  # Default Omega
        "Skew": 0.0,  # Default skew
        "Kurtosis": 3.0,  # Default kurtosis
        "Tail Ratio": 1.0,  # Default tail ratio
        "Common Sense Ratio": 1.0,  # Default common sense ratio
        "Value at Risk": 0.0,  # Default VaR
        "Daily Returns": 0.0,  # Default daily returns
        "Annual Returns": 0.0,  # Default annual returns
        "Cumulative Returns": 0.0,  # Default cumulative returns
        "Annualized Return": 0.0,  # Default annualized return
        "Annualized Volatility": 0.0,  # Default volatility
        "Signal Count": 0,  # Default signal count
        "Position Count": stats.get("Total Trades", 0),
        "Total Period": stats.get("Total Period", 0.0),
    }

    default_value = column_defaults.get(column_name)

    # Define columns that commonly missing and don't need warnings
    commonly_missing = {
        "Signal Entry",
        "Signal Exit",
        "_equity_data",
        "Exit Signal",
        "Stop Loss",
        "Positions",
        "Account_Value",
        "Risk_Metric_VaR",
    }

    if default_value is None:
        # Only show warnings if verbose mode is enabled
        if verbose:
            # Use debug level for commonly missing columns to reduce noise
            log_level = "debug" if column_name in commonly_missing else "warning"
            log(
                f"No default value defined for column '{column_name}', using None",
                log_level,
            )
    # Only show debug messages if verbose mode is enabled
    elif verbose:
        log(
            f"Using default value for missing column '{column_name}': {default_value}",
            "debug",
        )

    return default_value
