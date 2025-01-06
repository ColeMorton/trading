from typing import TypedDict, List, Dict
import os
import polars as pl
import yfinance as yf
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Set interactive backend
from skfolio import RiskMeasure
from skfolio.optimization import MeanRisk, ObjectiveFunction
from skfolio.preprocessing import prices_to_returns as sk_prices_to_returns
from app.tools.setup_logging import setup_logging

class PortfolioConfig(TypedDict):
    """Portfolio optimization configuration.

    Required Fields:
        min_weight (float): Minimum weight allocation per asset
        max_weight (float): Maximum weight allocation per asset
        risk_free_rate (float): Risk-free rate for calculations
    """
    min_weight: float
    max_weight: float
    risk_free_rate: float

def download_data(ticker: str, log: callable) -> pl.DataFrame:
    """
    Download historical data from Yahoo Finance.

    Args:
        ticker (str): Stock ticker symbol
        log (callable): Logging function

    Returns:
        pl.DataFrame: DataFrame with adjusted close prices

    Raises:
        Exception: If data download fails
    """
    try:
        log(f"Downloading data for {ticker}")
        data = yf.download(ticker, period="max", interval="1d")
        return pl.from_pandas(data[['Adj Close']])
    except Exception as e:
        log(f"Error downloading {ticker}: {str(e)}", "error")
        raise

def combine_price_data(tickers: List[str], log: callable) -> pl.DataFrame:
    """
    Combine price data for multiple tickers into a single DataFrame.

    Args:
        tickers (List[str]): List of stock ticker symbols
        log (callable): Logging function

    Returns:
        pl.DataFrame: Combined price data for all tickers
    """
    log("Combining price data")
    dfs = []
    for ticker in tickers:
        df = download_data(ticker, log)
        df = df.rename({"Adj Close": ticker})
        dfs.append(df)
    
    return pl.concat(dfs, how="horizontal")

def calculate_var(returns: np.ndarray, confidence_level: float = 0.95) -> float:
    """
    Calculate Value at Risk (VaR) for a given return series.

    Args:
        returns (np.ndarray): Array of returns
        confidence_level (float): Confidence level for VaR calculation (default: 0.95)

    Returns:
        float: VaR value as a positive number representing the potential loss percentage
    """
    # Convert returns to percentages for more intuitive values
    returns_pct = returns * 100
    
    sorted_returns = np.sort(returns_pct)
    cutoff_index = int((1 - confidence_level) * len(sorted_returns))
    var = -sorted_returns[cutoff_index]  # Convert to positive value
    return var

def calculate_cvar(returns: np.ndarray, confidence_level: float = 0.95) -> float:
    """
    Calculate Conditional Value at Risk (CVaR) for a given return series.

    Args:
        returns (np.ndarray): Array of returns
        confidence_level (float): Confidence level for CVaR calculation (default: 0.95)

    Returns:
        float: CVaR value as a positive number representing the expected loss percentage beyond VaR
    """
    # Convert returns to percentages for more intuitive values
    returns_pct = returns * 100
    
    sorted_returns = np.sort(returns_pct)
    cutoff_index = int((1 - confidence_level) * len(sorted_returns))
    var = sorted_returns[cutoff_index]
    
    # Calculate CVaR as the mean of returns below VaR
    cvar = -sorted_returns[sorted_returns <= var].mean()  # Convert to positive value
    
    return cvar

def calculate_asset_metrics(returns: pl.DataFrame, weights: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """
    Calculate performance metrics for individual assets.

    Args:
        returns (pl.DataFrame): Asset returns
        weights (Dict[str, float]): Portfolio weights

    Returns:
        Dict[str, Dict[str, float]]: Performance metrics by asset
    """
    metrics = {}
    
    for asset in returns.columns:
        asset_return = returns[asset].to_numpy()
        
        # Calculate metrics
        annualized_return = asset_return.mean() * 252
        
        # Calculate downside volatility for Sortino ratio
        downside_returns = asset_return[asset_return < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = annualized_return / downside_volatility if downside_volatility != 0 else 0
        
        # Calculate VaR and CVaR on raw returns
        weight = weights[asset]
        var = calculate_var(asset_return)  # Returns percentage value
        cvar = calculate_cvar(asset_return)  # Returns percentage value
        
        metrics[asset] = {
            "weight": weight,
            "annualized_return": annualized_return,
            "downside_volatility": downside_volatility,
            "sortino_ratio": sortino_ratio,
            "var": var,
            "cvar": cvar
        }
    
    return metrics

def main() -> None:
    """Main function to run portfolio optimization and analysis."""
    
    # Setup logging
    log, log_close, _, _ = setup_logging("portfolio", "analysis.log")
    
    try:
        # The max VaR for any individual position should not exclude the current Kelly Criterion risk amount (this accounts for 1.33x upper bound)
        # Current: 115

        # Stock Portfolio
        # TOTAL_PORTFOLIO_VALUE = 22958.68
        TOTAL_PORTFOLIO_VALUE = 50000

        # Investment Portfolio (Crypto + Stock)
        # TOTAL_PORTFOLIO_VALUE = 83500

        TICKERS = [
            # 'AAPL', 'NTES', 'APTV', 'DXCM', 'ROST', 'WST', 'OKTA', 'CNC', 'MCD', 'LRCX', 'FTNT'
            # 'BTC-USD', 'SOL-USD'
            'SPY', 'QQQ', 'BTC-USD', 'SOL-USD'
        ]
        
        # Calculate weights dynamically based on number of tickers
        equal_weight = 1.0 / len(TICKERS)
        min_weight = equal_weight * (2/3)  # Makes max_weight twice min_weight while averaging to equal_weight
        max_weight = min_weight * 2
        
        config: PortfolioConfig = {
            "min_weight": min_weight,
            "max_weight": max_weight,
            "risk_free_rate": 0.0
        }
        
        # Get and combine data
        data = combine_price_data(TICKERS, log)
        
        # Convert to pandas for skfolio compatibility
        data_pd = data.to_pandas()
        
        # Calculate returns
        log("Calculating returns")
        returns = sk_prices_to_returns(data_pd)
        
        # Create optimization model
        log("Creating optimization model")
        # Create optimization model that maximizes Sortino ratio
        model = MeanRisk(
            risk_measure=RiskMeasure.SEMI_DEVIATION,
            objective_function=ObjectiveFunction.MAXIMIZE_RATIO,
            min_weights=config["min_weight"],
            max_weights=config["max_weight"],
            portfolio_params=dict(
                name="Optimized Portfolio",
                risk_free_rate=config["risk_free_rate"]
            )
        )
        
        # Fit model and get weights
        log("Fitting optimization model")
        model.fit(returns)
        weights = dict(zip(TICKERS, model.weights_))
        
        # Get optimized portfolio
        log("Calculating portfolio metrics")
        portfolio = model.predict(returns)
        weights = dict(zip(TICKERS, model.weights_))
        
        # Calculate metrics using skfolio's Portfolio object
        annualized_return = portfolio.mean * 252  # annualize the mean return
        downside_volatility = portfolio.semi_deviation * np.sqrt(252)  # annualize the downside volatility
        sortino_ratio = portfolio.sortino_ratio
        
        # Calculate asset-specific metrics
        log("\nCalculating portfolio and asset metrics")
        asset_metrics = calculate_asset_metrics(pl.from_pandas(returns), weights)
        
        # Calculate VaR and CVaR
        portfolio_returns = portfolio.returns
        portfolio_var = calculate_var(portfolio_returns)
        portfolio_cvar = calculate_cvar(portfolio_returns)
        portfolio_var_usd = portfolio_var * TOTAL_PORTFOLIO_VALUE / 100
        portfolio_cvar_usd = portfolio_cvar * TOTAL_PORTFOLIO_VALUE / 100

        # Print portfolio summary
        log("\nOptimal Portfolio Allocation:")
        for asset, metrics in asset_metrics.items():
            usd_allocation = metrics["weight"] * TOTAL_PORTFOLIO_VALUE
            # Convert percentage risk to USD based on position size
            var_usd = (metrics["var"] / 100) * usd_allocation  # e.g. 2.5% of $1000 = $25
            cvar_usd = (metrics["cvar"] / 100) * usd_allocation  # e.g. 3.5% of $1000 = $35
            log(f"{asset}: {metrics['weight']:.2%} (${usd_allocation:,.2f}, VaR: ${var_usd:,.2f}, CVaR: ${cvar_usd:,.2f})")

        # Print portfolio metrics
        log("\nPortfolio Risk Metrics:")
        log(f"Annualized Return: {annualized_return:.2%}")
        log(f"Downside Volatility: {downside_volatility:.2%}")
        log(f"Sortino Ratio: {sortino_ratio:.2f}")
        log(f"Value at Risk (VaR): ${portfolio_var_usd:,.2f}")
        log(f"Conditional Value at Risk (CVaR): ${portfolio_cvar_usd:,.2f}")

        # Print detailed asset metrics
        log("\nDetailed Asset Metrics:")
        for asset, metrics in asset_metrics.items():
            log(f"\n{asset}:")
            log(f"  Weight: {metrics['weight']:.2%}")
            log(f"  Annualized Return: {metrics['annualized_return']:.2%}")
            log(f"  Downside Volatility: {metrics['downside_volatility']:.2%}")
            log(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        
        log_close()
        
    except Exception as e:
        log(f"An error occurred: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    main()
