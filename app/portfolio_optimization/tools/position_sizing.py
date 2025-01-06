"""Core position sizing calculations."""

import numpy as np
import yfinance as yf
from typing import List, Dict, Tuple, Callable
from app.portfolio_optimization.tools.position_sizing_types import Asset, PositionSizingConfig, AssetMetrics

def get_price_or_ema(ticker: str, use_ema: bool, ema_period: int) -> float:
    """Fetch the current price or EMA for a given ticker.
    
    Args:
        ticker (str): Asset ticker symbol
        use_ema (bool): Whether to use EMA
        ema_period (int): Period for EMA calculation
        
    Returns:
        float: Current price or EMA value
    """
    data = yf.Ticker(ticker).history(period="1mo")
    if use_ema:
        return float(data['Close'].ewm(span=ema_period, adjust=False).mean().iloc[-1])
    return float(data['Close'].iloc[-1])

def get_returns(ticker: str) -> np.ndarray:
    """Fetch historical returns for a given ticker.
    
    Args:
        ticker (str): Asset ticker symbol
        
    Returns:
        np.ndarray: Array of historical returns
    """
    data = yf.Ticker(ticker).history(period="max")
    returns = data['Close'].pct_change().dropna().to_numpy()
    return returns

def calculate_var_cvar(returns: np.ndarray, confidence_levels: List[float]) -> Dict[float, Tuple[float, float]]:
    """Calculate VaR and CVaR for given returns at multiple confidence levels.
    
    Args:
        returns (np.ndarray): Array of historical returns
        confidence_levels (List[float]): List of confidence levels
        
    Returns:
        Dict[float, Tuple[float, float]]: Dictionary mapping confidence levels to (VaR, CVaR) tuples
    """
    results = {}
    for cl in confidence_levels:
        var_threshold = np.percentile(returns, (1 - cl) * 100)
        cvar_threshold = returns[returns <= var_threshold].mean()
        results[cl] = (var_threshold, cvar_threshold)
    return results

def calculate_position_sizes(
    assets: List[Asset],
    config: PositionSizingConfig,
    log: Callable[[str, str], None]
) -> List[AssetMetrics]:
    """Calculate optimal position sizes for multiple assets.
    
    Args:
        assets (List[Asset]): List of assets with their configurations
        config (PositionSizingConfig): Position sizing configuration
        log (Callable[[str, str], None]): Logging function
        
    Returns:
        List[AssetMetrics]: List of calculated metrics for each asset
    """
    try:
        log("Starting position size calculations", "info")
        
        # Get current prices
        prices = {}
        for asset in assets:
            ticker = asset["ticker"]
            log(f"Fetching price data for {ticker}", "info")
            prices[ticker] = get_price_or_ema(
                ticker,
                config["use_ema"],
                config["ema_period"]
            )
        
        # Calculate initial values needed to achieve target leveraged allocations
        target_value = config.get("target_value", config["initial_value"])
        initial_values = {}
        
        for asset in assets:
            # Calculate what initial value we need to achieve target allocation after leverage
            target_leveraged = target_value * (asset["weight"] / 100)
            initial_values[asset["ticker"]] = target_leveraged / asset["leverage"]
        
        # Calculate leveraged values by applying leverage
        leveraged_values = {
            asset["ticker"]: initial_values[asset["ticker"]] * asset["leverage"]
            for asset in assets
        }
        
        # Calculate allocations based on leveraged values
        total_leveraged = sum(leveraged_values.values())
        allocations = {
            ticker: (value / total_leveraged) * 100
            for ticker, value in leveraged_values.items()
        }
        
        # Calculate position sizes
        position_sizes = {
            ticker: leveraged_values[ticker] / prices[ticker]
            for ticker in prices
        }
        
        # Calculate VaR and CVaR for each asset
        var_cvar_results = {}
        for asset in assets:
            ticker = asset["ticker"]
            log(f"Calculating risk metrics for {ticker}", "info")
            returns = get_returns(ticker)
            var_cvar = calculate_var_cvar(returns, config["var_confidence_levels"])
            var_cvar_results[ticker] = var_cvar
        
        # Compile results
        results = []
        for asset in assets:
            ticker = asset["ticker"]
            metrics: AssetMetrics = {
                "initial_value": initial_values[ticker],
                "leveraged_value": leveraged_values[ticker],
                "position_size": position_sizes[ticker],
                "allocation": allocations[ticker],
                "var_cvar": var_cvar_results[ticker]
            }
            results.append(metrics)
            
            log(f"Completed calculations for {ticker}", "info")
            
        return results
        
    except Exception as e:
        log(f"Error in position size calculations: {str(e)}", "error")
        raise