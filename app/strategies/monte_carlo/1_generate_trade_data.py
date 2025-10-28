import os
from typing import Any

import numpy as np
import pandas as pd

from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.get_data import download_data
from app.tools.setup_logging import setup_logging
from app.utils import backtest_strategy


# Configuration
default_config: dict[str, Any] = {
    "YEARS": 30,  # Set timeframe in years for daily data
    "USE_HOURLY": False,  # Set to False for daily data
    "USE_SYNTHETIC": False,  # Toggle between synthetic and original ticker
    "TICKER_1": "BTC-USD",  # Ticker for X to USD exchange rate
    "TICKER_2": "BTC-USD",  # Ticker for Y to USD exchange rate
    "SHORT": False,  # Set to True for short-only strategy, False for long-only strategy
    "USE_SMA": True,  # Set to True to use SMAs, False to use EMAs
    "EMA_FAST": 19,
    "EMA_SLOW": 34,
    "RSI_WINDOW": 14,
    "RSI_THRESHOLD": 55,
    "USE_RSI": False,
}


def calculate_max_drawdown(prices: np.ndarray) -> float:
    """
    Calculate the maximum drawdown from a series of prices.

    Args:
        prices (np.ndarray): Array of price values

    Returns:
        float: Maximum drawdown value
    """
    peak = prices[0]
    max_drawdown = 0
    for price in prices:
        peak = max(price, peak)
        drawdown = (peak - price) / peak
        max_drawdown = max(drawdown, max_drawdown)
    return max_drawdown


def run(config: dict[str, Any]) -> bool:
    """
    Generate trade data for Monte Carlo analysis.

    Args:
        config (Dict[str, Any]): Configuration dictionary

    Returns:
        bool: True if successful

    Raises:
        Exception: If data generation fails
    """
    log, log_close, _, _ = setup_logging(
        module_name="monte_carlo", log_file="generate_trade_data.log",
    )

    try:
        log(f"Starting trade data generation for {config['TICKER_1']}")

        # Download historical data
        data = download_data(config["TICKER_1"], config, log)

        data = calculate_ma_and_signals(
            data, config["EMA_FAST"], config["EMA_SLOW"], config, log,
        )

        # Ensure trade history export is not enabled for Monte Carlo data generation
        # Trade history export should only be used through app/concurrency/review.py
        config_copy = config.copy()
        if "EXPORT_TRADE_HISTORY" in config_copy:
            del config_copy["EXPORT_TRADE_HISTORY"]

        portfolio = backtest_strategy(data, config_copy, log)
        stats = portfolio.stats()
        log(f"Portfolio stats: {stats}")

        # Extract trade results from the portfolio object
        trades = portfolio.trades.records_readable

        # Convert 'Date' column to a list for indexing
        date_list = data["Date"].to_list()

        # Calculate maximum drawdown for each trade
        max_drawdowns = []
        for _, trade in trades.iterrows():
            start_idx = trade["Entry Timestamp"]
            end_idx = trade["Exit Timestamp"]
            trade_prices = data["Close"][start_idx : end_idx + 1].to_numpy()
            max_drawdown = calculate_max_drawdown(trade_prices)
            max_drawdowns.append(max_drawdown)

        # Prepare the trade results data
        trade_results = pd.DataFrame(
            {
                "Trade No.": np.arange(len(trades)),
                "Entry Date": [
                    date_list[i].strftime("%Y-%m-%d %H:%M:%S")
                    for i in trades["Entry Timestamp"]
                ],
                "Exit Date": [
                    date_list[i].strftime("%Y-%m-%d %H:%M:%S")
                    for i in trades["Exit Timestamp"]
                ],
                "Entry Price": trades["Avg Entry Price"],
                "Exit Price": trades["Avg Exit Price"],
                "Return (%)": trades["Return"],
                "PnL ($)": trades["PnL"],
                "Size": trades["Size"],
                "Drawdown (%)": max_drawdowns,
            },
        )

        log("\nTrade Results:")
        log(str(trade_results))

        # Create output directory if needed
        csv_dir = "data/outputs/monte_carlo"
        os.makedirs(csv_dir, exist_ok=True)

        # Export results
        csv_filename = os.path.join(
            csv_dir, f'{config["TICKER_1"]}_trade_data_ema_cross.csv',
        )
        trade_results.to_csv(csv_filename, index=False)
        log(f"Exported trade data to {csv_filename}")

        log_close()
        return True

    except Exception as e:
        log(f"Error generating trade data: {e!s}", "error")
        log_close()
        raise


if __name__ == "__main__":
    try:
        result = run(default_config)
        if result:
            print("Trade data generation completed successfully!")
    except Exception as e:
        print(f"Trade data generation failed: {e!s}")
        raise
