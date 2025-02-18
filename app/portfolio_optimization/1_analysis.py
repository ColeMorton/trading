from typing import TypedDict, List, Dict
import polars as pl
import yfinance as yf
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Set interactive backend
from skfolio import RiskMeasure
from skfolio.optimization import MeanRisk, ObjectiveFunction
from skfolio.preprocessing import prices_to_returns as sk_prices_to_returns
from app.tools.setup_logging import setup_logging
from app.portfolio_optimization.tools.portfolio_config import (
    load_portfolio_config,
    get_portfolio_value,
    get_portfolio_tickers,
)
import json
from pathlib import Path

config = {
    "portfolio": "all_20250218.json"
}

class OptimizationConfig(TypedDict):
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
        # Load portfolio configuration
        portfolio_config = load_portfolio_config(config["portfolio"])
        
        # Get portfolio values and tickers
        TOTAL_PORTFOLIO_VALUE = get_portfolio_value(portfolio_config)
        INITIAL_VALUE = portfolio_config["initial_value"]
        TICKERS = get_portfolio_tickers(portfolio_config)
        
        # Calculate weights dynamically based on number of tickers
        equal_weight = 1.0 / len(TICKERS)
        min_weight = equal_weight * (2/3)  # Makes max_weight twice min_weight while averaging to equal_weight
        max_weight = min_weight * 2
        
        optimization_config: OptimizationConfig = {
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
            min_weights=optimization_config["min_weight"],
            max_weights=optimization_config["max_weight"],
            portfolio_params=dict(
                name="Optimized Portfolio",
                risk_free_rate=optimization_config["risk_free_rate"]
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
        
        # Calculate VaR and CVaR at 95% and 99% confidence levels
        portfolio_returns = portfolio.returns
        # 95% confidence level
        portfolio_var_95 = calculate_var(portfolio_returns, 0.95)
        portfolio_cvar_95 = calculate_cvar(portfolio_returns, 0.95)
        # Calculate dollar values using total portfolio value
        portfolio_var_95_usd = portfolio_var_95 * TOTAL_PORTFOLIO_VALUE / 100
        portfolio_cvar_95_usd = portfolio_cvar_95 * TOTAL_PORTFOLIO_VALUE / 100
        # 99% confidence level
        portfolio_var_99 = calculate_var(portfolio_returns, 0.99)
        portfolio_cvar_99 = calculate_cvar(portfolio_returns, 0.99)
        portfolio_var_99_usd = portfolio_var_99 * TOTAL_PORTFOLIO_VALUE / 100
        portfolio_cvar_99_usd = portfolio_cvar_99 * TOTAL_PORTFOLIO_VALUE / 100

        # Calculate what percentage these dollar values represent of the initial value
        portfolio_var_95_pct = (portfolio_var_95_usd / INITIAL_VALUE) * 100
        portfolio_cvar_95_pct = (portfolio_cvar_95_usd / INITIAL_VALUE) * 100
        portfolio_var_99_pct = (portfolio_var_99_usd / INITIAL_VALUE) * 100
        portfolio_cvar_99_pct = (portfolio_cvar_99_usd / INITIAL_VALUE) * 100

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
        log(f"Value at Risk (VaR 95%): ${portfolio_var_95_usd:,.2f} ({portfolio_var_95_pct:.2f}% of initial ${INITIAL_VALUE:,.2f})")
        log(f"Conditional Value at Risk (CVaR 95%): ${portfolio_cvar_95_usd:,.2f} ({portfolio_cvar_95_pct:.2f}% of initial ${INITIAL_VALUE:,.2f})")
        log(f"Value at Risk (VaR 99%): ${portfolio_var_99_usd:,.2f} ({portfolio_var_99_pct:.2f}% of initial ${INITIAL_VALUE:,.2f})")
        log(f"Conditional Value at Risk (CVaR 99%): ${portfolio_cvar_99_usd:,.2f} ({portfolio_cvar_99_pct:.2f}% of initial ${INITIAL_VALUE:,.2f})")

        # Print detailed asset metrics
        log("\nDetailed Asset Metrics:")
        for asset, metrics in asset_metrics.items():
            log(f"\n{asset}:")
            log(f"  Weight: {metrics['weight']:.2%}")
            log(f"  Annualized Return: {metrics['annualized_return']:.2%}")
            log(f"  Downside Volatility: {metrics['downside_volatility']:.2%}")
            log(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")

        # Create output data
        output_data = {
            "initial_value": portfolio_config["initial_value"],
            "target_value": portfolio_config["target_value"],
            "use_target_value": portfolio_config["use_target_value"],
            "portfolio": portfolio_config["portfolio"],
            "portfolio_metrics": {
                "annualized_return": annualized_return,
                "downside_volatility": downside_volatility,
                "sortino_ratio": sortino_ratio,
                "var_95": portfolio_var_95_usd,
                "cvar_95": portfolio_cvar_95_usd,
                "var_99": portfolio_var_99_usd,
                "cvar_99": portfolio_cvar_99_usd,
            },
            "asset_metrics": asset_metrics,
        }

        # Write output data to JSON file
        output_path = Path("json/portfolio_optimization")
        output_path.mkdir(parents=True, exist_ok=True)
        file_name = config["portfolio"]
        file_path = output_path / file_name
        with open(file_path, "w") as f:
            json.dump(output_data, f, indent=4)

        log_close()

    except Exception as e:
        log(f"An error occurred: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    main()
