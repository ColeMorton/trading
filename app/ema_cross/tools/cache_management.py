import os
import pandas as pd
from typing import Tuple, Callable, Optional, Dict, List

def get_portfolio_path(
    ticker: str,
    use_ewm: bool,
    freq: str,
    log: Optional[Callable] = None
) -> str:
    """
    Get the portfolio file path.

    Args:
        ticker: Ticker symbol
        use_ewm: Whether EMA or SMA is used
        freq: Data frequency
        log: Optional logging function

    Returns:
        str: Path to portfolio file
    """
    ma_type = 'EMA' if use_ewm else 'SMA'
    freq_type = 'H' if freq == '1H' else 'D'
    portfolio_path = f"csv/ma_cross/portfolios/{ticker}_{freq_type}_{ma_type}.csv"
    if log:
        log(f"Portfolio path: {portfolio_path}")
    return portfolio_path

def load_portfolio_data(
    portfolio_path: str,
    log: Optional[Callable] = None
) -> Tuple[pd.Series, pd.Series]:
    """
    Load portfolio data from CSV.

    Args:
        portfolio_path: Path to portfolio file
        log: Optional logging function

    Returns:
        Tuple[pd.Series, pd.Series]: Returns and expectancy data
    """
    try:
        if not os.path.exists(portfolio_path):
            if log:
                log(f"Portfolio file not found: {portfolio_path}")
            return pd.Series(dtype=float), pd.Series(dtype=float)

        if log:
            log(f"Loading portfolio data from: {portfolio_path}")
        df = pd.read_csv(portfolio_path)
        
        # Convert to multi-index series
        index = pd.MultiIndex.from_tuples(
            list(zip(df['Long Window'], df['Short Window'])),
            names=['slow_window', 'fast_window']
        )
        
        # Extract returns and expectancy
        returns = pd.Series(df['Total Return [%]'].values, index=index)
        expectancy = pd.Series(df['Expectancy'].values, index=index)
        
        if log:
            log(f"Successfully loaded portfolio data from: {portfolio_path}")
        return returns, expectancy
    except Exception as e:
        if log:
            log(f"Failed to load portfolio data from {portfolio_path}: {str(e)}", "error")
        return pd.Series(dtype=float), pd.Series(dtype=float)
