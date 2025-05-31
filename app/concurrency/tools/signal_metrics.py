"""Signal Metrics Analysis Module for Trading Strategies.

This module provides functionality for calculating signal metrics
to analyze the frequency and distribution of trading signals.
"""

import os
from typing import Dict, Any, List, Optional
import polars as pl
import numpy as np
import pandas as pd
from pathlib import Path

from app.tools.setup_logging import setup_logging
from .signal_processor import SignalProcessor, SignalDefinition

# Get configuration
USE_FIXED_SIGNAL_PROC = os.getenv('USE_FIXED_SIGNAL_PROC', 'true').lower() == 'true'


def calculate_signal_metrics(
    aligned_data: List[pl.DataFrame],
    log: Optional[callable] = None
) -> Dict[str, Any]:
    """Calculate signal metrics for all strategies.

    Args:
        aligned_data (List[pl.DataFrame]): List of aligned dataframes with signal data
        log (Optional[callable]): Logging function

    Returns:
        Dict[str, Any]: Dictionary of signal metrics
    """
    if log is None:
        # Create a default logger if none provided
        log, _, _, _ = setup_logging("signal_metrics", Path("./logs"), "signal_metrics.log")

    try:
        log("Calculating signal metrics", "info")
        
        # Initialize metrics dictionary
        metrics = {}
        
        # Calculate portfolio-level metrics
        all_signals = []
        
        # Initialize signal processor
        signal_processor = SignalProcessor(use_fixed=USE_FIXED_SIGNAL_PROC)
        
        # Process each strategy
        for i, df in enumerate(aligned_data, 1):
            # Convert to pandas for date handling
            df_pd = df.to_pandas()
            
            # Set Date as index for proper time-based operations
            if 'Date' in df_pd.columns:
                df_pd = df_pd.set_index('Date')
            
            if USE_FIXED_SIGNAL_PROC:
                # Use standardized signal processing
                signal_def = SignalDefinition(
                    signal_column='Signal' if 'Signal' in df_pd.columns else 'Position',
                    position_column='Position'
                )
                
                # Get comprehensive signal counts
                signal_counts = signal_processor.get_comprehensive_counts(df_pd, signal_def)
                
                # Use position signals for time-based analysis (consistent with legacy)
                position_count = signal_processor.count_position_signals(df_pd, signal_def)
                _, filtered_signals_df = signal_processor.count_filtered_signals(df_pd, signal_def)
                
                # Create signals dataframe for monthly analysis
                if len(filtered_signals_df) > 0:
                    signals = filtered_signals_df.copy()
                else:
                    # Fallback to position-based signals
                    df_pd['signal'] = df_pd['Position'].diff().fillna(0)
                    signals = df_pd[df_pd['signal'] != 0].copy()
            else:
                # Legacy signal extraction
                df_pd['signal'] = df_pd['Position'].diff().fillna(0)
                signals = df_pd[df_pd['signal'] != 0].copy()  # Create an explicit copy
            
            # Add to all signals for portfolio metrics
            all_signals.append(signals)
            
            # Calculate monthly signal counts
            signals.loc[:, 'month'] = signals.index.to_period('M')
            monthly_counts = signals.groupby('month').size()
            
            # Calculate metrics
            if len(monthly_counts) > 0:
                mean_signals = monthly_counts.mean()
                median_signals = monthly_counts.median()
                signal_volatility = monthly_counts.std() if len(monthly_counts) > 1 else 0
                max_monthly = monthly_counts.max()
                min_monthly = monthly_counts.min()
                total_signals = len(signals)
                
                # Store strategy-specific metrics
                metrics[f"strategy_{i}_mean_signals"] = mean_signals
                metrics[f"strategy_{i}_median_signals"] = median_signals
                metrics[f"strategy_{i}_signal_volatility"] = signal_volatility
                metrics[f"strategy_{i}_max_monthly_signals"] = max_monthly
                metrics[f"strategy_{i}_min_monthly_signals"] = min_monthly
                metrics[f"strategy_{i}_total_signals"] = total_signals
            else:
                # No signals for this strategy
                metrics[f"strategy_{i}_mean_signals"] = 0
                metrics[f"strategy_{i}_median_signals"] = 0
                metrics[f"strategy_{i}_signal_volatility"] = 0
                metrics[f"strategy_{i}_max_monthly_signals"] = 0
                metrics[f"strategy_{i}_min_monthly_signals"] = 0
                metrics[f"strategy_{i}_total_signals"] = 0
        
        # Calculate portfolio-level metrics
        if all_signals:
            # Combine all signals
            combined_signals = pd.concat(all_signals).copy()  # Create an explicit copy
            
            # Ensure index is properly set for period operations
            if not isinstance(combined_signals.index, pd.DatetimeIndex):
                log("Warning: Combined signals index is not a DatetimeIndex", "warning")
                # Try to recover by using the first Date column found
                for col in combined_signals.columns:
                    if col.lower() == 'date':
                        combined_signals = combined_signals.set_index(col)
                        break
            
            combined_signals.loc[:, 'month'] = combined_signals.index.to_period('M')
            
            # Calculate monthly counts across all strategies
            portfolio_monthly_counts = combined_signals.groupby('month').size()
            
            if len(portfolio_monthly_counts) > 0:
                mean_signals = portfolio_monthly_counts.mean()
                median_signals = portfolio_monthly_counts.median()
                signal_volatility = portfolio_monthly_counts.std() if len(portfolio_monthly_counts) > 1 else 0
                max_monthly = portfolio_monthly_counts.max()
                min_monthly = portfolio_monthly_counts.min()
                total_signals = len(combined_signals)
                
                # Calculate standard deviation bounds
                std_below_mean = max(0, mean_signals - signal_volatility)
                std_above_mean = mean_signals + signal_volatility
                
                # Store portfolio metrics
                metrics["mean_signals"] = mean_signals
                metrics["median_signals"] = median_signals
                metrics["signal_volatility"] = signal_volatility
                metrics["max_monthly_signals"] = max_monthly
                metrics["min_monthly_signals"] = min_monthly
                metrics["total_signals"] = total_signals
                metrics["std_below_mean"] = std_below_mean
                metrics["std_above_mean"] = std_above_mean
            else:
                # No signals for the portfolio
                metrics["mean_signals"] = 0
                metrics["median_signals"] = 0
                metrics["signal_volatility"] = 0
                metrics["max_monthly_signals"] = 0
                metrics["min_monthly_signals"] = 0
                metrics["total_signals"] = 0
                metrics["std_below_mean"] = 0
                metrics["std_above_mean"] = 0
        
        log("Signal metrics calculation completed", "info")
        return metrics
        
    except Exception as e:
        log(f"Error calculating signal metrics: {str(e)}", "error")
        # Return empty metrics on error
        return {
            "mean_signals": 0,
            "median_signals": 0,
            "signal_volatility": 0,
            "max_monthly_signals": 0,
            "min_monthly_signals": 0,
            "total_signals": 0,
            "std_below_mean": 0,
            "std_above_mean": 0
        }
