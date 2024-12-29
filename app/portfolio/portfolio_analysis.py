from typing import TypedDict, List, Dict
import polars as pl
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from skfolio import PerfMeasure, RiskMeasure
from skfolio.optimization import MeanRisk
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
        annualized_volatility = asset_return.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility != 0 else 0
        
        # Calculate Sortino ratio
        downside_returns = asset_return[asset_return < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = annualized_return / downside_volatility if downside_volatility != 0 else 0
        
        metrics[asset] = {
            "weight": weights[asset],
            "annualized_return": annualized_return,
            "annualized_volatility": annualized_volatility,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio
        }
    
    return metrics

def main() -> None:
    """Main function to run portfolio optimization and analysis."""
    
    # Setup logging
    log, log_close, _, _ = setup_logging("portfolio", "portfolio_analysis.log")
    
    try:
        TICKERS = [
            'NVDA', 'NFLX', 'AMD', 'AMAT',
            'AMZN', 'MU', 'AAPL'
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
        model = MeanRisk(
            risk_measure=RiskMeasure.SEMI_VARIANCE,
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
        
        # Calculate portfolio metrics
        log("Calculating portfolio metrics")
        portfolio_returns = sum(returns[asset] * weight for asset, weight in weights.items())
        
        annualized_return = portfolio_returns.mean() * 252
        annualized_volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility != 0 else 0
        
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252)
        sortino_ratio = annualized_return / downside_volatility if downside_volatility != 0 else 0
        
        # Print portfolio results
        log("\nOptimal portfolio weights:")
        for asset, weight in weights.items():
            log(f"{asset}: {weight:.2%}")
        
        log("\nPortfolio Metrics:")
        log(f"Annualized Return: {annualized_return:.2%}")
        log(f"Annualized Volatility: {annualized_volatility:.2%}")
        log(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        log(f"Sortino Ratio: {sortino_ratio:.2f}")
        
        # Calculate and print individual asset metrics
        asset_metrics = calculate_asset_metrics(pl.from_pandas(returns), weights)
        
        for asset, metrics in asset_metrics.items():
            log(f"\n{asset} Metrics:")
            log(f"Weight: {metrics['weight']:.2%}")
            log(f"Annualized Return: {metrics['annualized_return']:.2%}")
            log(f"Annualized Volatility: {metrics['annualized_volatility']:.2%}")
            log(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            log(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        
        # Plot portfolio composition
        log("\nGenerating portfolio composition plot")
        portfolio = model.predict(returns)
        fig = portfolio.plot_composition()
        plt.show()
        
        log_close()
        
    except Exception as e:
        log(f"An error occurred: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    main()
