"""Signal-based metrics calculation for concurrency analysis."""

from typing import List, Dict, Callable
import numpy as np
import polars as pl
from datetime import datetime
from collections import defaultdict

def calculate_strategy_metrics(monthly_signals: List[int]) -> Dict[str, float]:
    """Calculate signal metrics for a specific strategy or portfolio.

    Args:
        monthly_signals (List[int]): List of monthly signal counts

    Returns:
        Dict[str, float]: Dictionary containing calculated metrics:
            - mean_signals: Average number of signals per month
            - median_signals: Median number of signals per month
            - std_below_mean: One standard deviation below mean
            - std_above_mean: One standard deviation above mean
            - signal_volatility: Standard deviation of monthly signals
            - max_monthly_signals: Maximum signals in any month
            - min_monthly_signals: Minimum signals in any month
            - total_signals: Total number of signals across period
    """
    if not monthly_signals:
        return {
            "mean_signals": 0.0,
            "median_signals": 0.0,
            "std_below_mean": 0.0,
            "std_above_mean": 0.0,
            "signal_volatility": 0.0,
            "max_monthly_signals": 0.0,
            "min_monthly_signals": 0.0,
            "total_signals": 0.0
        }

    monthly_totals = np.array(monthly_signals)
    mean_signals = float(np.mean(monthly_totals))
    median_signals = float(np.median(monthly_totals))
    std_signals = float(np.std(monthly_totals))
    max_monthly = float(np.max(monthly_totals))
    min_monthly = float(np.min(monthly_totals))
    total_signals = float(np.sum(monthly_totals))

    return {
        "mean_signals": mean_signals,
        "median_signals": median_signals,
        "std_below_mean": mean_signals - std_signals,
        "std_above_mean": mean_signals + std_signals,
        "signal_volatility": std_signals,
        "max_monthly_signals": max_monthly,
        "min_monthly_signals": min_monthly,
        "total_signals": total_signals
    }

def calculate_signal_metrics(
    data_list: List[pl.DataFrame],
    log: Callable[[str, str], None]
) -> Dict[str, Dict]:
    """Calculate portfolio-level and strategy-specific signal metrics.

    Analyzes the frequency and distribution of trading signals (entries/exits)
    at both the portfolio and individual strategy levels on a monthly basis.
    Signals are defined as any change in position value (entry or exit).

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with position data.
            Each dataframe must contain:
            - Date column for temporal alignment
            - Position column for signal detection
        log (Callable[[str, str], None]): Logging function

    Returns:
        Dict[str, Dict]: Dictionary containing:
            Portfolio-level metrics at root level:
            - mean_signals: Average number of total portfolio signals per month
            - median_signals: Median number of total portfolio signals per month
            - std_below_mean: One standard deviation below portfolio mean
            - std_above_mean: One standard deviation above portfolio mean
            - signal_volatility: Standard deviation of monthly portfolio signals
            - max_monthly_signals: Maximum portfolio signals in any month
            - min_monthly_signals: Minimum portfolio signals in any month
            - total_signals: Total number of portfolio signals across period

            Strategy-specific metrics under 'strategy_signal_metrics' key:
            Dictionary with strategy_N keys containing same metrics as above
            but calculated per strategy

    Raises:
        ValueError: If input data is invalid or missing required columns
        Exception: If calculation fails
    """
    try:
        if not data_list:
            log("Empty data list provided", "error")
            raise ValueError("Data list cannot be empty")

        # Validate required columns
        required_cols = ["Date", "Position"]
        for i, df in enumerate(data_list, 1):
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                log(f"Strategy {i} missing required columns: {missing}", "error")
                raise ValueError(f"Strategy {i} missing required columns: {missing}")

        log(f"Calculating signal metrics for {len(data_list)} strategies", "info")
        
        # Initialize dictionaries to store signals by month
        portfolio_monthly_signals = defaultdict(int)
        strategy_monthly_signals = [defaultdict(int) for _ in data_list]
        metrics = {}
        strategy_signal_metrics = {}  # New dictionary for strategy-specific metrics
        
        for i, df in enumerate(data_list, 1):
            log(f"Processing signals for strategy {i}", "info")
            
            # Verify and process position data
            positions = df["Position"].fill_null(0).to_numpy()
            dates = df["Date"].to_numpy()
            
            # Log position statistics
            unique_positions = np.unique(positions)
            non_zero_positions = positions != 0
            position_count = np.sum(non_zero_positions)
            
            log(f"Strategy {i} position analysis:", "info")
            log(f"  Unique position values: {unique_positions}", "info")
            log(f"  Total periods with positions: {position_count}", "info")
            log(f"  Position ratio: {position_count/len(positions):.2%}", "info")
            
            # Calculate signals from position changes
            initial_signal = positions[0] != 0
            position_changes = np.diff(positions) != 0
            signals = np.concatenate(([initial_signal], position_changes))
            signal_dates = dates[signals]
            strategy_signals = len(signal_dates)
            
            # Verify signal detection
            if strategy_signals > 0:
                log(f"Strategy {i} signals detected:", "info")
                log(f"  Initial position: {positions[0]}", "info")
                log(f"  Position changes: {np.sum(position_changes)}", "info")
                log(f"  Total signals: {strategy_signals}", "info")
                log(f"  First signal: {signal_dates[0]}", "info")
                log(f"  Last signal: {signal_dates[-1]}", "info")
            else:
                log(f"Warning: No signals detected for strategy {i}", "warning")
            
            # Convert all dates to datetime for consistent handling
            dates_dt = np.array([
                datetime.fromisoformat(str(d).split('.')[0])
                if not isinstance(d, datetime) else d
                for d in dates
            ])
            
            # Group signals by month with enhanced validation
            monthly_counts = defaultdict(int)
            signal_months = set()
            
            for date, is_signal in zip(dates_dt, signals):
                if is_signal:
                    month_key = date.strftime("%Y-%m")
                    monthly_counts[month_key] += 1
                    portfolio_monthly_signals[month_key] += 1
                    signal_months.add(month_key)
            
            # Ensure all months in the date range are represented
            all_months = {d.strftime("%Y-%m") for d in dates_dt}
            for month in all_months:
                if month not in monthly_counts:
                    monthly_counts[month] = 0
            
            # Store monthly counts for this strategy
            strategy_monthly_signals[i-1] = monthly_counts
            
            # Log monthly signal distribution
            log(f"Strategy {i} monthly signal distribution:", "info")
            log(f"  Total months: {len(all_months)}", "info")
            log(f"  Months with signals: {len(signal_months)}", "info")
            log(f"  Signal distribution:", "info")
            for month, count in sorted(monthly_counts.items()):
                if count > 0:
                    log(f"    {month}: {count} signals", "info")

            # Calculate and validate strategy metrics
            monthly_values = list(monthly_counts.values())
            total_signals = sum(monthly_values)
            
            log(f"Strategy {i} metrics calculation:", "info")
            log(f"  Monthly values: {len(monthly_values)} months", "info")
            log(f"  Signal months: {len([v for v in monthly_values if v > 0])}", "info")
            log(f"  Total signals: {total_signals}", "info")
            
            if total_signals == 0:
                log(f"Warning: Strategy {i} has no signals - verifying position data", "warning")
                non_zero_pos = np.sum(positions != 0)
                pos_changes = np.sum(np.diff(positions) != 0)
                log(f"  Position verification:", "info")
                log(f"    Non-zero positions: {non_zero_pos}", "info")
                log(f"    Position changes: {pos_changes}", "info")
            
            strategy_metrics = calculate_strategy_metrics(monthly_values)
            
            # Store metrics in both formats
            strategy_signal_metrics[f"strategy_{i}"] = strategy_metrics
            for key, value in strategy_metrics.items():
                metrics[f"strategy_{i}_{key}"] = value
                
            if total_signals == 0:
                log(f"Warning: Strategy {i} has no signals - this may indicate an issue", "warning")
        
        log(f"Calculating portfolio-level metrics", "info")
        
        # Calculate portfolio-level metrics
        portfolio_metrics = calculate_strategy_metrics(
            list(portfolio_monthly_signals.values())
        )
        
        # Add portfolio metrics to root level
        metrics.update(portfolio_metrics)
        
        # Add strategy signal metrics under the new key
        metrics["strategy_signal_metrics"] = strategy_signal_metrics
        
        log("Signal metrics calculation completed successfully", "info")
        return metrics
        
    except Exception as e:
        log(f"Error calculating signal metrics: {str(e)}", "error")
        raise
