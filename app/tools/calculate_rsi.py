import logging

import numpy as np
import polars as pl


def calculate_rsi(data: pl.DataFrame, period: int) -> pl.DataFrame:
    """Calculate RSI using Wilder's smoothing method.

    This implementation follows Wilder's original RSI calculation:
    1. Calculate price changes
    2. Split into gains and losses
    3. Calculate initial SMA of gains and losses
    4. Use Wilder's smoothing for subsequent periods
    5. Calculate RS and RSI

    Args:
        data: DataFrame with Close prices
        period: RSI window (lookback window)

    Returns:
        DataFrame with RSI column added
    """
    logging.info(f"Calculating RSI with period: {period}")
    try:
        # Calculate price changes
        close_series = data["Close"]
        delta = close_series.diff()

        # Split into gains and losses
        gains = pl.when(delta > 0).then(delta).otherwise(0).fill_null(0)
        losses = pl.when(delta < 0).then(-delta).otherwise(0).fill_null(0)
        # Collect expressions and convert to numpy
        gains_np = data.select(gains).to_series().to_numpy()
        losses_np = data.select(losses).to_series().to_numpy()

        # Initialize arrays for averages
        avg_gains = np.zeros_like(gains_np)
        avg_losses = np.zeros_like(losses_np)

        # First period is simple average
        avg_gains[period - 1] = np.mean(gains_np[:period])
        avg_losses[period - 1] = np.mean(losses_np[:period])

        # Calculate subsequent values using Wilder's smoothing
        for i in range(period, len(gains_np)):
            avg_gains[i] = (avg_gains[i - 1] * (period - 1) + gains_np[i]) / period
            avg_losses[i] = (avg_losses[i - 1] * (period - 1) + losses_np[i]) / period

        # Calculate RS and RSI
        rs = np.where(avg_losses == 0, float("inf"), avg_gains / avg_losses)
        rsi = np.where(rs == float("inf"), 100.0, 100 - (100 / (1 + rs)))

        # Create Series with NaN padding
        values = [float("nan")] * (period - 1) + rsi[period - 1 :].tolist()
        rsi_full = pl.Series("RSI", values)

        return data.with_columns([rsi_full])
    except Exception as e:
        logging.error(f"Failed to calculate RSI: {e}")
        raise
