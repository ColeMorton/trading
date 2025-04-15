"""
Standardized Signal Metrics Module.

This module provides a unified framework for calculating signal metrics,
combining frequency, distribution, and quality metrics in a consistent manner.
This is a refactored version that uses the new unified modules for metrics calculation,
normalization, error handling, and data processing.
"""

from typing import Dict, Any, List, Optional, Callable, Union
import polars as pl
import pandas as pd
from pathlib import Path

from app.tools.setup_logging import setup_logging
from app.tools.metrics_calculation import MetricsCalculator, calculate_signal_metrics as calc_metrics
from app.tools.metrics_calculation import calculate_signal_quality_metrics as calc_quality_metrics
from app.tools.normalization import Normalizer
from app.tools.error_handling import ErrorHandler, validate_dataframe
from app.tools.data_processing import DataProcessor


class SignalMetrics:
    """Class for calculating comprehensive signal metrics.
    
    This class is a wrapper around the new unified modules for metrics calculation,
    normalization, error handling, and data processing. It provides backward compatibility
    with the old API while leveraging the new optimized implementations.
    """
    
    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        """Initialize the SignalMetrics class.
        
        Args:
            log: Optional logging function. If not provided, a default logger will be created.
        """
        if log is None:
            # Create a default logger if none provided
            self.log, _, _, _ = setup_logging("signal_metrics", Path("./logs"), "signal_metrics.log")
        else:
            self.log = log
        
        # Initialize the component classes
        self.metrics_calculator = MetricsCalculator(log)
        self.normalizer = Normalizer(log)
        self.error_handler = ErrorHandler(log)
        self.data_processor = DataProcessor(log)
    
    def calculate_frequency_metrics(
        self,
        data: Union[pl.DataFrame, pd.DataFrame],
        signal_column: str = "Signal",
        date_column: str = "Date"
    ) -> Dict[str, Any]:
        """Calculate signal frequency metrics.
        
        Args:
            data: DataFrame containing signal data
            signal_column: Name of the signal column
            date_column: Name of the date column
            
        Returns:
            Dict[str, Any]: Dictionary of frequency metrics
        """
        try:
            # Validate input data
            validate_dataframe(data, [signal_column], "Signal data")
            
            # Use the metrics calculator to calculate frequency metrics
            return self.metrics_calculator.calculate_frequency_metrics(
                data, signal_column, date_column
            )
        except Exception as e:
            self.log(f"Error calculating signal frequency metrics: {str(e)}", "error")
            return self.metrics_calculator._get_empty_frequency_metrics()
    
    def calculate_quality_metrics(
        self,
        signals_df: Union[pl.DataFrame, pd.DataFrame],
        returns_df: Union[pl.DataFrame, pd.DataFrame],
        strategy_id: str,
        signal_column: str = "signal",
        return_column: str = "return",
        date_column: str = "Date"
    ) -> Dict[str, Any]:
        """Calculate signal quality metrics.
        
        Args:
            signals_df: DataFrame containing signal data
            returns_df: DataFrame containing return data
            strategy_id: Identifier for the strategy
            signal_column: Name of the signal column
            return_column: Name of the return column
            date_column: Name of the date column
            
        Returns:
            Dict[str, Any]: Dictionary of signal quality metrics
        """
        try:
            # Validate input data
            validate_dataframe(signals_df, [signal_column, date_column], "Signals data")
            validate_dataframe(returns_df, [return_column, date_column], "Returns data")
            
            # Use the metrics calculator to calculate quality metrics
            metrics = self.metrics_calculator.calculate_signal_quality_metrics(
                signals_df, returns_df, strategy_id, signal_column, return_column, date_column
            )
            
            # Normalize the metrics for consistent scaling
            normalized_metrics = self.normalizer.normalize_metrics(metrics)
            
            return metrics
        except Exception as e:
            self.log(f"Error calculating signal quality metrics for {strategy_id}: {str(e)}", "error")
            return {"signal_count": 0, "signal_quality_score": 0.0}
    
    def calculate_portfolio_metrics(
        self,
        data_list: List[Union[pl.DataFrame, pd.DataFrame]],
        strategy_ids: List[str],
        signal_column: str = "Signal",
        date_column: str = "Date"
    ) -> Dict[str, Any]:
        """Calculate portfolio-level signal metrics.
        
        Args:
            data_list: List of DataFrames containing signal data
            strategy_ids: List of strategy identifiers
            signal_column: Name of the signal column
            date_column: Name of the date column
            
        Returns:
            Dict[str, Any]: Dictionary of portfolio-level metrics
        """
        try:
            # Validate input data
            if not data_list:
                self.log("Empty data list provided for portfolio metrics calculation", "warning")
                return {}
            
            # Use the metrics calculator to calculate portfolio metrics
            return self.metrics_calculator.calculate_portfolio_metrics(
                data_list, strategy_ids, signal_column, date_column
            )
        except Exception as e:
            self.log(f"Error calculating portfolio-level signal metrics: {str(e)}", "error")
            return {
                "portfolio_mean_signals_per_month": 0.0,
                "portfolio_median_signals_per_month": 0.0,
                "portfolio_signal_volatility": 0.0,
                "portfolio_max_monthly_signals": 0,
                "portfolio_min_monthly_signals": 0,
                "portfolio_total_signals": 0
            }


# Convenience functions for backward compatibility

def calculate_signal_metrics(
    aligned_data: List[pl.DataFrame],
    log: Optional[Callable] = None
) -> Dict[str, Any]:
    """Calculate signal metrics for all strategies (legacy function).
    
    Args:
        aligned_data: List of DataFrames containing signal data
        log: Optional logging function
        
    Returns:
        Dict[str, Any]: Dictionary of signal metrics
    """
    return calc_metrics(aligned_data, log)


def calculate_signal_quality_metrics(
    signals_df: pl.DataFrame,
    returns_df: pl.DataFrame,
    strategy_id: str,
    log: Callable[[str, str], None]
) -> Dict[str, Any]:
    """Calculate signal quality metrics for a strategy (legacy function).
    
    Args:
        signals_df: DataFrame containing signal data
        returns_df: DataFrame containing return data
        strategy_id: Identifier for the strategy
        log: Logging function
        
    Returns:
        Dict[str, Any]: Dictionary of signal quality metrics
    """
    return calc_quality_metrics(signals_df, returns_df, strategy_id, log)
