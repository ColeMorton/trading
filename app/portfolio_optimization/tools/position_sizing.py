"""Core position sizing calculations."""

from collections.abc import Callable
from typing import TypedDict

import numpy as np
import yfinance as yf

from app.portfolio_optimization.tools.position_sizing_types import (
    Asset,
    PositionSizingConfig,
)


class AssetMetrics(TypedDict):
    """Asset metrics type definition.

    Required Fields:
        initial_value (float): Initial value of the asset
        leveraged_value (float): Leveraged value of the asset
        position_size (float): Position size of the asset
        allocation (float): Allocation of the asset in the portfolio
    """

    initial_value: float
    leveraged_value: float
    position_size: float
    allocation: float
    weight: float
    annualized_return: float
    downside_volatility: float
    sortino_ratio: float
    var: float
    cvar: float


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
        return float(data["Close"].ewm(span=ema_period, adjust=False).mean().iloc[-1])
    return float(data["Close"].iloc[-1])


def get_returns(ticker: str) -> np.ndarray:
    """Fetch historical returns for a given ticker.

    Args:
        ticker (str): Asset ticker symbol

    Returns:
        np.ndarray: Array of historical returns
    """
    data = yf.Ticker(ticker).history(period="max")
    returns = data["Close"].pct_change().dropna().to_numpy()
    return returns


def calculate_var_cvar(
    returns: np.ndarray, confidence_levels: list[float]
) -> dict[float, tuple[float, float]]:
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
    assets: list[Asset], config: PositionSizingConfig, log: Callable[[str, str], None]
) -> list[AssetMetrics]:
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
                ticker, config["use_ema"], config["ema_period"]
            )

        # Calculate initial and leveraged values
        initial_values = {}
        leveraged_values = {}

        if config.get("use_target_value", False):
            # When using target value, work backwards from target
            target_value = config["target_value"]
            for asset in assets:
                # Calculate leveraged value based on weight
                leveraged_values[asset["ticker"]] = target_value * (
                    asset["weight"] / 100
                )
                # Calculate initial value by dividing leveraged value by leverage
                initial_values[asset["ticker"]] = (
                    leveraged_values[asset["ticker"]] / asset["leverage"]
                )
        else:
            # When not using target value:
            # 1. Distribute initial value according to weights to get initial values
            # 2. Apply leverage to get leveraged values
            initial_value = config["initial_value"]
            for asset in assets:
                initial_values[asset["ticker"]] = initial_value * (
                    asset["weight"] / 100
                )
                leveraged_values[asset["ticker"]] = (
                    initial_values[asset["ticker"]] * asset["leverage"]
                )

        # Use original weights from config for allocations
        allocations = {asset["ticker"]: asset["weight"] for asset in assets}

        # Calculate position sizes
        position_sizes = {
            ticker: leveraged_values[ticker] / prices[ticker] for ticker in prices
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
            # Get returns for the asset
            returns = get_returns(ticker)

            # Calculate asset metrics
            asset_return = returns.mean() * 252
            downside_returns = returns[returns < 0]
            downside_volatility = (
                downside_returns.std() * np.sqrt(252)
                if len(downside_returns) > 0
                else 0
            )
            sortino_ratio = (
                asset_return / downside_volatility if downside_volatility != 0 else 0
            )

            # Calculate VaR and CVaR
            var_threshold = np.percentile(returns, (1 - 0.95) * 100)
            cvar_threshold = returns[returns <= var_threshold].mean()

            metrics: AssetMetrics = {
                "initial_value": initial_values[ticker],
                "leveraged_value": leveraged_values[ticker],
                "position_size": position_sizes[ticker],
                "allocation": allocations[ticker],
                "weight": asset["weight"],
                "annualized_return": asset_return,
                "downside_volatility": downside_volatility,
                "sortino_ratio": sortino_ratio,
                "var": var_threshold,
                "cvar": cvar_threshold,
            }
            results.append(metrics)

            log(f"Completed calculations for {ticker}", "info")

        return results

    except Exception as e:
        log(f"Error in position size calculations: {e!s}", "error")
        raise
