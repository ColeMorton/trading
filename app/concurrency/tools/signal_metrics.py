"""Signal-based metrics calculation for concurrency analysis."""

from typing import List, Dict, Callable
import numpy as np
import polars as pl
from datetime import datetime

def calculate_signal_metrics(
    data_list: List[pl.DataFrame],
    log: Callable[[str, str], None]
) -> Dict[str, float]:
    """Calculate signal-based metrics across strategies.

    Analyzes the frequency and distribution of trading signals (entries/exits)
    across all strategies on a monthly basis. Signals are defined as any change
    in position value (entry or exit).

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with position data.
            Each dataframe must contain:
            - Date column for temporal alignment
            - Position column for signal detection
        log (Callable[[str, str], None]): Logging function

    Returns:
        Dict[str, float]: Dictionary containing:
            - mean_signals: Average number of signals per month
            - median_signals: Median number of signals per month
            - std_below_mean: One standard deviation below mean
            - std_above_mean: One standard deviation above mean
            - signal_volatility: Standard deviation of monthly signals
            - max_monthly_signals: Maximum signals in any month
            - min_monthly_signals: Minimum signals in any month
            - total_signals: Total number of signals across period

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
        
        # Initialize list to store monthly signal counts
        monthly_signals = []
        total_signals = 0
        
        for i, df in enumerate(data_list, 1):
            log(f"Processing signals for strategy {i}", "info")
            
            # Convert positions to numpy for efficient calculation
            positions = df["Position"].fill_null(0).to_numpy()
            dates = df["Date"].to_numpy()
            
            # Calculate position changes (signals)
            signals = np.diff(positions) != 0
            strategy_signals = np.sum(signals)
            total_signals += strategy_signals
            signal_dates = dates[1:][signals]
            
            log(f"Strategy {i} total signals: {strategy_signals}", "info")
            
            # Convert dates to datetime if they aren't already
            if len(signal_dates) > 0:
                if not isinstance(signal_dates[0], datetime):
                    log(f"Converting dates for strategy {i}", "info")
                    signal_dates = np.array([
                        # Handle ISO format dates with time component
                        datetime.fromisoformat(str(d).split('.')[0])
                        for d in signal_dates
                    ])
                
                # Count signals per month
                months = np.array([d.strftime("%Y-%m") for d in signal_dates])
                unique_months, counts = np.unique(months, return_counts=True)
                monthly_signals.extend(counts)
                log(f"Strategy {i} monthly signals processed: {len(unique_months)} months", "info")
        
        log(f"Total signals across all strategies: {total_signals}", "info")
        
        # Calculate metrics
        if len(monthly_signals) > 0:
            log("Calculating monthly signal statistics", "info")
            monthly_signals = np.array(monthly_signals)
            mean_signals = float(np.mean(monthly_signals))
            median_signals = float(np.median(monthly_signals))
            std_signals = float(np.std(monthly_signals))
            max_monthly = float(np.max(monthly_signals))
            min_monthly = float(np.min(monthly_signals))
            
            log(f"Monthly signal statistics:", "info")
            log(f"Mean signals: {mean_signals:.2f}", "info")
            log(f"Median signals: {median_signals:.2f}", "info")
            log(f"Signal std dev: {std_signals:.2f}", "info")
            log(f"Max monthly: {max_monthly}", "info")
            log(f"Min monthly: {min_monthly}", "info")
        else:
            log("No signals found in any strategy", "info")
            mean_signals = 0.0
            median_signals = 0.0
            std_signals = 0.0
            max_monthly = 0.0
            min_monthly = 0.0
        
        metrics = {
            "mean_signals": mean_signals,
            "median_signals": median_signals,
            "std_below_mean": mean_signals - std_signals,
            "std_above_mean": mean_signals + std_signals,
            "signal_volatility": std_signals,
            "max_monthly_signals": max_monthly,
            "min_monthly_signals": min_monthly,
            "total_signals": float(total_signals)
        }
        
        log("Signal metrics calculation completed successfully", "info")
        return metrics
        
    except Exception as e:
        log(f"Error calculating signal metrics: {str(e)}", "error")
        raise
