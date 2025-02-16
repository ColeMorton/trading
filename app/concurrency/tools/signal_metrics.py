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
        Dict[str, float]: Dictionary containing calculated metrics
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
) -> Dict[str, float]:
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
        Dict[str, float]: Dictionary containing:
            Portfolio-level metrics under 'signal_metrics':
            - mean_signals: Average number of total portfolio signals per month
            - median_signals: Median number of total portfolio signals per month
            - std_below_mean: One standard deviation below portfolio mean
            - std_above_mean: One standard deviation above portfolio mean
            - signal_volatility: Standard deviation of monthly portfolio signals
            - max_monthly_signals: Maximum portfolio signals in any month
            - min_monthly_signals: Minimum portfolio signals in any month
            - total_signals: Total number of portfolio signals across period

            Strategy-specific metrics (prefixed with strategy_N_):
            Same metrics as above but calculated per strategy

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
        
        for i, df in enumerate(data_list, 1):
            log(f"Processing signals for strategy {i}", "info")
            
            # Convert positions to numpy for efficient calculation
            positions = df["Position"].fill_null(0).to_numpy()
            dates = df["Date"].to_numpy()
            
            # Calculate position changes (signals)
            signals = np.diff(positions) != 0
            strategy_signals = np.sum(signals)
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
                
                # Aggregate signals by month for both portfolio and strategy
                for date in signal_dates:
                    month_key = date.strftime("%Y-%m")
                    portfolio_monthly_signals[month_key] += 1
                    strategy_monthly_signals[i-1][month_key] += 1
                
                log(f"Strategy {i} signals aggregated", "info")

            # Calculate strategy-specific metrics
            strategy_metrics = calculate_strategy_metrics(
                list(strategy_monthly_signals[i-1].values())
            )
            
            # Add strategy-specific metrics with proper prefixes
            for key, value in strategy_metrics.items():
                metrics[f"strategy_{i}_{key}"] = value
        
        log(f"Calculating portfolio-level metrics", "info")
        
        # Calculate portfolio-level metrics and add them directly to the metrics dictionary
        portfolio_metrics = calculate_strategy_metrics(
            list(portfolio_monthly_signals.values())
        )
        metrics.update(portfolio_metrics)  # Add portfolio metrics directly to the root level
        
        log("Signal metrics calculation completed successfully", "info")
        return metrics
        
    except Exception as e:
        log(f"Error calculating signal metrics: {str(e)}", "error")
        raise
