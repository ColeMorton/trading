from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from skfolio.optimization import MaximumDiversification
import yfinance as yf

from app.tools.setup_logging import setup_logging


def get_historical_data(
    tickers: list[str], start_date: datetime, end_date: datetime,
) -> pd.DataFrame:
    """
    Download historical data for given tickers.

    Args:
        tickers (List[str]): List of stock tickers
        start_date (datetime): Start date for historical data
        end_date (datetime): End date for historical data

    Returns:
        pd.DataFrame: DataFrame containing historical prices
    """
    return yf.download(tickers, start=start_date, end=end_date)["Adj Close"]


def calculate_returns(prices: pd.DataFrame) -> np.ndarray:
    """
    Calculate returns from price data.

    Args:
        prices (pd.DataFrame): DataFrame of historical prices

    Returns:
        np.ndarray: Array of returns
    """
    return prices.pct_change().dropna().values


def optimize_portfolio(returns: np.ndarray) -> tuple[np.ndarray, dict]:
    """
    Optimize portfolio using Maximum Diversification.

    Args:
        returns (np.ndarray): Array of returns

    Returns:
        Tuple[np.ndarray, dict]: Optimized weights and weights dictionary
    """
    # Create and fit optimizer
    model = MaximumDiversification()
    model.fit(returns)

    # Get the optimized weights from the fitted model
    weights = model.weights_

    # Create weights dictionary
    weights_dict = dict(zip(TICKERS, weights, strict=False))

    return weights, weights_dict


def plot_weights(weights: dict, filename: str = "portfolio_composition.png") -> None:
    """
    Plot portfolio weights.

    Args:
        weights (dict): Dictionary of portfolio weights
        filename (str): Output filename for the plot
    """
    plt.figure(figsize=(12, 6))
    plt.bar(weights.keys(), weights.values())
    plt.title("Maximum Diversification Portfolio Composition")
    plt.xlabel("Assets")
    plt.ylabel("Weight")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def main() -> bool:
    """
    Main function to run the portfolio optimization.

    Returns:
        bool: True if successful, False otherwise
    """
    # Setup logging with correct parameters
    log, log_close, _, _ = setup_logging(
        module_name="portfolio",
        log_file="diversification.log",
        log_subdir="optimization",
    )

    try:
        # Define parameters
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        log("Downloading historical data...", "info")
        prices_df = get_historical_data(TICKERS, start_date, end_date)

        log("Calculating returns...", "info")
        returns = calculate_returns(prices_df)

        log("Optimizing portfolio...", "info")
        weights, weights_dict = optimize_portfolio(returns)

        # Log portfolio weights
        log("Portfolio Weights:", "info")
        for ticker, weight in weights_dict.items():
            log(f"{ticker}: {weight:.4f}", "info")

        # Plot results
        log("Plotting portfolio weights...", "info")
        plot_weights(weights_dict)

        log_close()
        return True

    except Exception as e:
        log(f"Error: {e!s}", "error")
        log_close()
        raise


if __name__ == "__main__":
    TICKERS = ["NVDA", "NFLX", "AMD", "AMAT", "AMZN", "MU", "AAPL"]
    main()
