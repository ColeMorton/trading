"""Signal-based metrics calculation for concurrency analysis."""

from typing import List, Dict
import numpy as np
import polars as pl
from datetime import datetime

def calculate_signal_metrics(data_list: List[pl.DataFrame]) -> Dict[str, float]:
    """Calculate signal-based metrics across strategies.

    Analyzes the frequency and distribution of trading signals (entries/exits)
    across all strategies on a monthly basis. Signals are defined as any change
    in position value (entry or exit).

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with position data.
            Each dataframe must contain:
            - Date column for temporal alignment
            - Position column for signal detection

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
    """
    # Initialize list to store monthly signal counts
    monthly_signals = []
    total_signals = 0
    
    for df in data_list:
        # Convert positions to numpy for efficient calculation
        positions = df["Position"].fill_null(0).to_numpy()
        dates = df["Date"].to_numpy()
        
        # Calculate position changes (signals)
        signals = np.diff(positions) != 0
        total_signals += np.sum(signals)
        signal_dates = dates[1:][signals]
        
        # Convert dates to datetime if they aren't already
        if len(signal_dates) > 0:
            if not isinstance(signal_dates[0], datetime):
                signal_dates = np.array([
                    # Handle ISO format dates with time component
                    datetime.fromisoformat(str(d).split('.')[0])
                    for d in signal_dates
                ])
            
            # Count signals per month
            months = np.array([d.strftime("%Y-%m") for d in signal_dates])
            unique_months, counts = np.unique(months, return_counts=True)
            monthly_signals.extend(counts)
    
    # Calculate metrics
    if len(monthly_signals) > 0:
        monthly_signals = np.array(monthly_signals)
        mean_signals = float(np.mean(monthly_signals))
        median_signals = float(np.median(monthly_signals))
        std_signals = float(np.std(monthly_signals))
        max_monthly = float(np.max(monthly_signals))
        min_monthly = float(np.min(monthly_signals))
    else:
        mean_signals = 0.0
        median_signals = 0.0
        std_signals = 0.0
        max_monthly = 0.0
        min_monthly = 0.0
    
    return {
        "mean_signals": mean_signals,
        "median_signals": median_signals,
        "std_below_mean": mean_signals - std_signals,
        "std_above_mean": mean_signals + std_signals,
        "signal_volatility": std_signals,
        "max_monthly_signals": max_monthly,
        "min_monthly_signals": min_monthly,
        "total_signals": float(total_signals)
    }
