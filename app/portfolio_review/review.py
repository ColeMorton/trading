import json
import os

import polars as pl

from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd_and_signals import calculate_macd_and_signals
from app.tools.get_config import get_config
from app.tools.get_data import get_data
from app.tools.setup_logging import setup_logging
from app.utils import backtest_strategy

DEFAULT_STRATEGY_TYPE = "SMA"

CONFIG_BTC = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": "max",
    "USE_HOURLY": False,
    "TICKER": "BTC-USD",
    "USE_SYNTHETIC": False,
    "TICKER_1": "BTC-USD",
    "TICKER_2": "SPY",
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17,
    "STOP_LOSS": 3.62,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": False,
    "BASE_DIR": "C:/Projects/trading",
    "WINDOWS": 89,
}

CONFIG_SOL = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": "max",
    "USE_HOURLY": False,
    "TICKER": "SOL-USD",
    "USE_SYNTHETIC": False,
    "TICKER_1": "BTC-USD",
    "TICKER_2": "SPY",
    "SHORT_WINDOW": 14,
    "LONG_WINDOW": 32,
    "STOP_LOSS": None,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": True,
    "BASE_DIR": "C:/Projects/trading",
    "WINDOWS": 89,
}

CONFIG_SUI = {
    "YEARS": 1.5369,
    "USE_YEARS": True,
    "PERIOD": "max",
    "USE_HOURLY": False,
    "TICKER": "SUI20947-USD",
    "USE_SYNTHETIC": False,
    "TICKER_1": "BTC-USD",
    "TICKER_2": "SPY",
    "SHORT_WINDOW": 38,
    "LONG_WINDOW": 59,
    "STOP_LOSS": None,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": True,
    "BASE_DIR": "C:/Projects/trading",
    "WINDOWS": 89,
}

CONFIG_SPY = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": "max",
    "USE_HOURLY": False,
    "TICKER": "SPY",
    "USE_SYNTHETIC": False,
    "TICKER_1": "BTC-USD",
    "TICKER_2": "SPY",
    "SHORT_WINDOW": 10,
    "LONG_WINDOW": 30,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": False,
    "BASE_DIR": "C:/Projects/trading",
    "WINDOWS": 89,
}

CONFIG_OP = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": "max",
    "USE_HOURLY": False,
    "TICKER": "OP-USD",
    "USE_SYNTHETIC": False,
    "TICKER_1": "BTC-USD",
    "TICKER_2": "SPY",
    "SHORT_WINDOW": 81,
    "LONG_WINDOW": 83,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": True,
    "BASE_DIR": "C:/Projects/trading",
    "WINDOWS": 89,
}

CONFIG = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": "max",
    "USE_HOURLY": False,
    "SHORT": False,
    "USE_GBM": False,
    "BASE_DIR": "C:/Projects/trading",
    "WINDOWS": 89,
}


def process_strategy(config, log):
    """
    Process an individual strategy.

    Args:
        config (dict): Strategy configuration
        log (Callable): Logging function

    Returns:
        dict: Strategy results or None if failed
    """
    try:
        log(f"Starting portfolio review for {config['TICKER']}")
        data = get_data(config["TICKER"], config, log)

        # Handle different strategy types
        if config.get("STRATEGY_TYPE") == "MACD":
            # For MACD strategies, we need the signal window
            signal_window = config.get(
                "SIGNAL_WINDOW", 9
            )  # Default to 9 if not specified
            data = calculate_macd_and_signals(
                data,
                config["SHORT_WINDOW"],  # Fast EMA
                config["LONG_WINDOW"],  # Slow EMA
                signal_window,  # Signal line EMA
                config,
                log,
            )
        else:
            # Default to MA strategy
            data = calculate_ma_and_signals(
                data, config["SHORT_WINDOW"], config["LONG_WINDOW"], config, log
            )

        portfolio = backtest_strategy(data, config, log)
        return portfolio
    except Exception as e:
        log(f"Error processing strategy: {str(e)}", "error")
        return None


def run(config_dict=None, portfolio_file=None):
    """
    Run portfolio review analysis.

    Args:
        config_dict (dict, optional): Configuration dictionary
        portfolio_file (str, optional): Path to portfolio JSON file

    Returns:
        bool: True if analysis successful
    """
    log, log_close, _, _ = setup_logging(
        module_name="portfolio_review", log_file="review.log"
    )

    try:
        # Handle portfolio file if provided
        if portfolio_file and os.path.exists(portfolio_file):
            log(f"Loading portfolio from {portfolio_file}")
            with open(portfolio_file, "r") as f:
                portfolio_data = json.load(f)

            results = []
            for strategy in portfolio_data:
                log(f"Processing strategy: {strategy}")

                # Create config from strategy
                config = {
                    "TICKER": strategy["ticker"],
                    "USE_HOURLY": strategy["timeframe"].lower() == "hourly",
                    "SHORT_WINDOW": strategy["short_window"],
                    "LONG_WINDOW": strategy["long_window"],
                    "DIRECTION": strategy["direction"],
                    "USE_SMA": strategy["type"] == "SMA",
                    "STRATEGY_TYPE": strategy["type"],
                }

                # Add RSI parameters if present
                if "rsi_period" in strategy:
                    config["RSI_WINDOW"] = strategy["rsi_period"]
                if "rsi_threshold" in strategy:
                    config["RSI_THRESHOLD"] = strategy["rsi_threshold"]

                # Add signal window for MACD if present
                if "signal_window" in strategy:
                    config["SIGNAL_WINDOW"] = strategy["signal_window"]

                # Process individual strategy
                portfolio = process_strategy(config, log)
                if portfolio:
                    results.append({"config": config, "portfolio": portfolio})

            log(f"Processed {len(results)} strategies")
            log_close()
            return True

        # Handle direct config dictionary
        elif config_dict:
            config = get_config(config_dict)
            log(f"Starting portfolio review for {config['TICKER']}")

            data = get_data(config["TICKER"], config, log)

            # Determine strategy type
            strategy_type = config.get("STRATEGY_TYPE", DEFAULT_STRATEGY_TYPE)

            if strategy_type == "MACD":
                # For MACD strategies, we need the signal window
                signal_window = config.get(
                    "SIGNAL_WINDOW", 9
                )  # Default to 9 if not specified
                data = calculate_macd_and_signals(
                    data,
                    config["SHORT_WINDOW"],  # Fast EMA
                    config["LONG_WINDOW"],  # Slow EMA
                    signal_window,  # Signal line EMA
                    config,
                    log,
                )
            else:
                # Default to MA strategy
                data = calculate_ma_and_signals(
                    data, config["SHORT_WINDOW"], config["LONG_WINDOW"], config, log
                )

            portfolio = backtest_strategy(data, config, log)

        stats = portfolio.stats()
        log(f"Portfolio stats: {stats}")

        # Extract value series and convert to DataFrame
        value_series = portfolio.value()
        initial_value = value_series[0]
        equity_curve = pl.DataFrame(
            {"Date": value_series.index, "Close": value_series.values / initial_value}
        )

        # Export to CSV - use appropriate directory based on strategy type
        strategy_type = config.get("STRATEGY_TYPE", DEFAULT_STRATEGY_TYPE)
        strategy_type_dir = "macd" if strategy_type == "MACD" else "ma_cross"
        csv_path = f'data/outputs/portfolio/{strategy_type_dir}/equity_curve/{config["TICKER"]}.csv'

        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        equity_curve.write_csv(csv_path)
        log(f"Exported equity curve to {csv_path}")

        # Generate portfolio plots and save to files
        from app.tools.plotting import create_portfolio_plot_files

        created_files = create_portfolio_plot_files(portfolio, config, log)
        if created_files:
            log(f"Generated portfolio plots: {', '.join(created_files)}")
        else:
            log("Portfolio plots generation completed (files saved to disk)", "warning")

        log_close()
        return True

    except Exception as e:
        log(f"Error during portfolio review: {str(e)}", "error")
        log_close()
        raise


if __name__ == "__main__":
    try:
        result = run(CONFIG_OP)
        if result:
            print("Portfolio review completed successfully!")
    except Exception as e:
        print(f"Portfolio review failed: {str(e)}")
        raise
