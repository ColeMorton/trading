"""Signal-based metrics calculation for concurrency analysis."""

from typing import List, Dict, Callable
import numpy as np
import polars as pl
from datetime import datetime
from collections import defaultdict

def calculate_signal_metrics(
    data_list: List[pl.DataFrame],
    log: Callable[[str, str], None]
) -> Dict[str, float]:
    """Calculate portfolio-level signal-based metrics.

    Analyzes the frequency and distribution of trading signals (entries/exits)
    at the portfolio level on a monthly basis. Signals from all strategies are
    aggregated per month to reflect total portfolio activity. Signals are defined
    as any change in position value (entry or exit).

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with position data.
            Each dataframe must contain:
            - Date column for temporal alignment
            - Position column for signal detection
        log (Callable[[str, str], None]): Logging function

    Returns:
        Dict[str, float]: Dictionary containing portfolio-level metrics:
            - mean_signals: Average number of total portfolio signals per month
            - median_signals: Median number of total portfolio signals per month
            - std_below_mean: One standard deviation below portfolio mean
            - std_above_mean: One standard deviation above portfolio mean
            - signal_volatility: Standard deviation of monthly portfolio signals
            - max_monthly_signals: Maximum portfolio signals in any month
            - min_monthly_signals: Minimum portfolio signals in any month
            - total_signals: Total number of portfolio signals across period

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

        log(f"Calculating portfolio signal metrics for {len(data_list)} strategies", "info")
        
        # Initialize dictionary to store portfolio signals by month
        portfolio_monthly_signals = defaultdict(int)
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
                
                # Aggregate signals by month at portfolio level
                for date in signal_dates:
                    month_key = date.strftime("%Y-%m")
                    portfolio_monthly_signals[month_key] += 1
                
                log(f"Strategy {i} signals aggregated into portfolio totals", "info")
        
        log(f"Total portfolio signals across all strategies: {total_signals}", "info")
        
        # Calculate portfolio-level metrics
        if portfolio_monthly_signals:
            log("Calculating portfolio monthly signal statistics", "info")
            monthly_totals = np.array(list(portfolio_monthly_signals.values()))
            mean_signals = float(np.mean(monthly_totals))
            median_signals = float(np.median(monthly_totals))
            std_signals = float(np.std(monthly_totals))
            max_monthly = float(np.max(monthly_totals))
            min_monthly = float(np.min(monthly_totals))
            
            log(f"Portfolio monthly signal statistics:", "info")
            log(f"Mean portfolio signals per month: {mean_signals:.2f}", "info")
            log(f"Median portfolio signals per month: {median_signals:.2f}", "info")
            log(f"Portfolio signal std dev: {std_signals:.2f}", "info")
            log(f"Max monthly portfolio signals: {max_monthly}", "info")
            log(f"Min monthly portfolio signals: {min_monthly}", "info")
        else:
            log("No signals found in portfolio", "info")
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
        
        log("Portfolio signal metrics calculation completed successfully", "info")
        return metrics
        
    except Exception as e:
        log(f"Error calculating portfolio signal metrics: {str(e)}", "error")
        raise
