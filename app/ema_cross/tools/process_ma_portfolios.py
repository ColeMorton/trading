import polars as pl
from typing import Optional, Tuple, Callable
from app.tools.get_data import get_data
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.backtest_strategy import backtest_strategy

def process_ma_portfolios(
    ticker: str, 
    sma_fast: Optional[int], 
    sma_slow: Optional[int], 
    ema_fast: Optional[int], 
    ema_slow: Optional[int],
    config: dict,
    log: Callable
) -> Optional[Tuple[Optional[pl.DataFrame], Optional[pl.DataFrame], dict]]:
    """
    Process SMA and/or EMA portfolios for a given ticker.

    Args:
        ticker: Ticker symbol
        sma_fast: Fast SMA window (optional)
        sma_slow: Slow SMA window (optional)
        ema_fast: Fast EMA window (optional)
        ema_slow: Slow EMA window (optional)
        config: Configuration dictionary including USE_HOURLY setting
        log: Logging function for recording events and errors

    Returns:
        Optional tuple of (SMA portfolio DataFrame or None, EMA portfolio DataFrame or None, config)
        Returns None if processing fails entirely
    """
    try:
        # Update config with ticker and strategy settings while preserving USE_HOURLY
        strategy_config = config.copy()
        strategy_config["TICKER"] = ticker
        strategy_config["SHORT"] = False  # Long-only strategy
        
        # Get data - now passing the log parameter
        data = get_data(ticker, strategy_config, log)
        if data is None or len(data) == 0:
            log(f"No data available for {ticker}", "error")
            return None
            
        sma_portfolio = None
        ema_portfolio = None
        
        # Process SMA if both windows provided
        if sma_fast is not None and sma_slow is not None:
            strategy_config["USE_SMA"] = True
            sma_data = calculate_ma_and_signals(
                data.clone(), 
                sma_fast, 
                sma_slow, 
                strategy_config,
                log  # Pass the log parameter here
            )
            if sma_data is not None:
                sma_portfolio = backtest_strategy(sma_data, strategy_config, log)
                if sma_portfolio is None:
                    log(f"Failed to backtest SMA strategy for {ticker}", "error")
            else:
                log(f"Failed to calculate SMA signals for {ticker}", "error")
        
        # Process EMA if both windows provided
        if ema_fast is not None and ema_slow is not None:
            strategy_config["USE_SMA"] = False
            ema_data = calculate_ma_and_signals(
                data.clone(), 
                ema_fast, 
                ema_slow, 
                strategy_config,
                log  # Pass the log parameter here
            )
            if ema_data is not None:
                ema_portfolio = backtest_strategy(ema_data, strategy_config, log)
                if ema_portfolio is None:
                    log(f"Failed to backtest EMA strategy for {ticker}", "error")
            else:
                log(f"Failed to calculate EMA signals for {ticker}", "error")
        
        # Return results if at least one strategy was processed
        if sma_portfolio is not None or ema_portfolio is not None:
            return sma_portfolio, ema_portfolio, strategy_config
        else:
            log(f"No valid strategies processed for {ticker}", "error")
            return None
        
    except Exception as e:
        log(f"Failed to process {ticker}: {e}", "error")
        return None
