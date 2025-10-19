"""
RSI Utilities Module

This module provides utility functions for RSI calculations and masking in heatmap visualizations.
"""

import numpy as np
import pandas as pd
import polars as pl

from app.tools.calculate_rsi import calculate_rsi


def calculate_latest_rsi_matrix(
    last_bar: pd.Series,
    price_history: pd.Series,
    rsi_windows: np.ndarray,
    rsi_thresholds: np.ndarray,
    log: callable,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculate RSI values and create a mask matrix for the heatmap visualization.

    This function:
    1. Calculates RSI for each window length using the provided price history
    2. For each window/threshold combination:
       - Computes the RSI value using that window length
       - Compares the RSI value to the threshold
       - Creates a mask entry (True if RSI >= threshold, False otherwise)
    3. Logs the status of each combination for monitoring

    Args:
        last_bar (pd.Series): Latest price bar containing at least Close price
        price_history (pd.Series): Historical Close prices including the last bar
        rsi_windows (np.ndarray): Array of RSI window lengths to analyze
        rsi_thresholds (np.ndarray): Array of RSI threshold values to analyze
        log (Callable): Logging function for recording events and errors

    Returns:
        Tuple[np.ndarray, np.ndarray]: Tuple containing:
            - Matrix of RSI values for each window/threshold combination
            - Boolean mask matrix where True indicates RSI >= threshold

    Raises:
        Exception: If RSI calculation fails for any window length
    """
    # Initialize matrices
    rsi_matrix = np.zeros((len(rsi_windows), len(rsi_thresholds)))
    mask_matrix = np.zeros_like(rsi_matrix, dtype=bool)

    # Convert price history to Polars DataFrame with enough data for RSI calculation
    # We need at least max(rsi_windows) periods of data for accurate calculation
    min_periods = int(max(rsi_windows) * 3)  # Use 3x window size for better accuracy
    price_df = pl.DataFrame({"Close": price_history.tail(min_periods).values})

    log("Starting RSI parameter analysis...", "info")
    log(f"Using {min_periods} periods for RSI calculation", "info")
    log(
        f"Analyzing {len(rsi_windows)} windows and {len(rsi_thresholds)} thresholds",
        "info",
    )

    # Calculate RSI for each window length
    for i, window in enumerate(rsi_windows):
        try:
            # Calculate RSI using our existing function
            rsi_df = calculate_rsi(price_df, int(window))
            rsi_value = rsi_df["RSI"].tail(1).item()

            # Fill the RSI matrix row with this value
            rsi_matrix[i, :] = rsi_value

            # Create mask where RSI >= threshold and log status
            for j, threshold in enumerate(rsi_thresholds):
                is_active = rsi_value >= threshold
                mask_matrix[i, j] = is_active
                status = "ACTIVE" if is_active else "INACTIVE"
                log(
                    f"RSI Analysis - Window: {window:2.0f}, Threshold: {threshold:2.0f}, Value: {rsi_value:5.2f}, Status: {status}",
                    "info",
                )
        except Exception as e:
            log(f"Failed to calculate RSI for window {window}: {e!s}", "error")
            raise

    return rsi_matrix, mask_matrix


def apply_rsi_mask(metric_matrix: np.ndarray, mask_matrix: np.ndarray) -> np.ndarray:
    """
    Apply RSI-based mask to the metric matrix for visualization.

    This function applies a boolean mask to a metric matrix, replacing values
    where the mask is False with NaN. This is used to hide values in the
    heatmap visualization that don't meet the RSI threshold criteria.

    Args:
        metric_matrix (np.ndarray): Original matrix of performance metrics
        mask_matrix (np.ndarray): Boolean mask where True indicates values to keep

    Returns:
        np.ndarray: Masked metric matrix with NaN where mask is False
    """
    return np.where(mask_matrix, metric_matrix, np.nan)
