import polars as pl
from app.tools.get_data import get_data
from app.tools.setup_logging import setup_logging
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.ema_cross.tools.backtest_strategy import backtest_strategy
from app.ema_cross.tools.convert_stats import convert_stats
from typing import Optional, Tuple
import os

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Setup logging
log_dir = os.path.join(project_root, 'logs', 'ma_cross')
log, log_close, _, _ = setup_logging('ma_cross', log_dir, 'process_ma_portfolios.log')

def process_ma_portfolios(ticker: str, sma_fast: int, sma_slow: int, ema_fast: int, ema_slow: int) -> Optional[Tuple[pl.DataFrame, pl.DataFrame, dict]]:
    """
    Process both SMA and EMA portfolios for a given ticker.

    Args:
        ticker: Ticker symbol
        sma_fast: Fast SMA window
        sma_slow: Slow SMA window
        ema_fast: Fast EMA window
        ema_slow: Slow EMA window

    Returns:
        Optional tuple of (SMA portfolio DataFrame, EMA portfolio DataFrame, config)
        Returns None if processing fails
    """
    try:
        config = {
            "TICKER": ticker,
            "SHORT": False,  # Long-only strategy
            "USE_HOURLY": False  # Using daily data
        }
        
        # Get data
        data = get_data(ticker, config)
        if data is None or len(data) == 0:
            log(f"No data available for {ticker}", "error")
            return None
        
        # Process SMA
        config["USE_SMA"] = True
        sma_data = calculate_ma_and_signals(data.clone(), sma_fast, sma_slow, config)
        if sma_data is None:
            log(f"Failed to calculate SMA signals for {ticker}", "error")
            return None
        sma_portfolio = backtest_strategy(sma_data, config)
        if sma_portfolio is None:
            log(f"Failed to backtest SMA strategy for {ticker}", "error")
            return None
        
        # Process EMA
        config["USE_SMA"] = False
        ema_data = calculate_ma_and_signals(data.clone(), ema_fast, ema_slow, config)
        if ema_data is None:
            log(f"Failed to calculate EMA signals for {ticker}", "error")
            return None
        ema_portfolio = backtest_strategy(ema_data, config)
        if ema_portfolio is None:
            log(f"Failed to backtest EMA strategy for {ticker}", "error")
            return None
        
        return sma_portfolio, ema_portfolio, config
        
    except Exception as e:
        log(f"Failed to process {ticker}: {e}", "error")
        return None
