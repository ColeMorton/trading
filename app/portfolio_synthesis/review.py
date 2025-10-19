import json
import os

import polars as pl

from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd_and_signals import calculate_macd_and_signals
from app.tools.get_config import get_config
from app.tools.get_data import get_data
from app.tools.setup_logging import setup_logging
from app.utils import backtest_strategy


# Verified conversions:
# "hourly" → USE_HOURLY=True, USE_4HOUR=False, USE_2DAY=False
# "4hour"  → USE_HOURLY=False, USE_4HOUR=True, USE_2DAY=False
# "2day"   → USE_HOURLY=False, USE_4HOUR=False, USE_2DAY=True
# "daily"  → USE_HOURLY=False, USE_4HOUR=False, USE_2DAY=False

# "SMA"    → USE_SMA=True, STRATEGY_TYPE="SMA"
# "EMA"    → USE_SMA=False, STRATEGY_TYPE="EMA"
# "MACD"   → USE_SMA=False, STRATEGY_TYPE="MACD"
# "ATR"    → USE_SMA=False, STRATEGY_TYPE="ATR"

DEFAULT_STRATEGY_TYPE = "SMA"

CONFIG_BTC = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": "max",
    "TIMEFRAME": "2day",
    "TICKER": "BTC-USD",
    "USE_SYNTHETIC": False,
    "TICKER_1": "BTC-USD",
    "TICKER_2": "SPY",
    "FAST_PERIOD": 14,
    "SLOW_PERIOD": 16,
    # "STOP_LOSS": 3.62,
    "SHORT": False,
    "USE_GBM": False,
    "STRATEGY_TYPE": "SMA",
    "SIGNAL_PERIOD": 9,
    "BASE_DIR": "C:/Projects/trading",
    "WINDOWS": 89,
}

CONFIG_SOL = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": "max",
    "TIMEFRAME": "daily",
    "TICKER": "SOL-USD",
    "USE_SYNTHETIC": False,
    "TICKER_1": "BTC-USD",
    "TICKER_2": "SPY",
    "FAST_PERIOD": 14,
    "SLOW_PERIOD": 32,
    "STOP_LOSS": None,
    "SHORT": False,
    "USE_GBM": False,
    "STRATEGY_TYPE": "SMA",
    "SIGNAL_PERIOD": 9,
    "BASE_DIR": "C:/Projects/trading",
    "WINDOWS": 89,
}

CONFIG_SUI = {
    "YEARS": 1.5369,
    "USE_YEARS": True,
    "PERIOD": "max",
    "TIMEFRAME": "daily",
    "TICKER": "SUI20947-USD",
    "USE_SYNTHETIC": False,
    "TICKER_1": "BTC-USD",
    "TICKER_2": "SPY",
    "FAST_PERIOD": 38,
    "SLOW_PERIOD": 59,
    "STOP_LOSS": None,
    "SHORT": False,
    "USE_GBM": False,
    "STRATEGY_TYPE": "SMA",
    "SIGNAL_PERIOD": 9,
    "BASE_DIR": "C:/Projects/trading",
    "WINDOWS": 89,
}

CONFIG_SPY = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": "max",
    "TIMEFRAME": "daily",
    "TICKER": "SPY",
    "USE_SYNTHETIC": False,
    "TICKER_1": "BTC-USD",
    "TICKER_2": "SPY",
    "FAST_PERIOD": 10,
    "SLOW_PERIOD": 30,
    "SHORT": False,
    "USE_GBM": False,
    "STRATEGY_TYPE": "EMA",
    "SIGNAL_PERIOD": 9,
    "BASE_DIR": "C:/Projects/trading",
    "WINDOWS": 89,
}

CONFIG_OP = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": "max",
    "TIMEFRAME": "daily",
    "TICKER": "OP-USD",
    "USE_SYNTHETIC": False,
    "TICKER_1": "BTC-USD",
    "TICKER_2": "SPY",
    "FAST_PERIOD": 81,
    "SLOW_PERIOD": 83,
    "SHORT": False,
    "USE_GBM": False,
    "STRATEGY_TYPE": "SMA",
    "SIGNAL_PERIOD": 9,
    "BASE_DIR": "C:/Projects/trading",
    "WINDOWS": 89,
}

CONFIG = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": "max",
    "TIMEFRAME": "daily",
    "SHORT": False,
    "USE_GBM": False,
    "STRATEGY_TYPE": "SMA",
    "SIGNAL_PERIOD": 9,
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
            # For MACD strategies, we need the signal period
            signal_period = config.get(
                "SIGNAL_PERIOD", 9
            )  # Default to 9 if not specified
            data = calculate_macd_and_signals(
                data,
                config["FAST_PERIOD"],  # Fast EMA
                config["SLOW_PERIOD"],  # Slow EMA
                signal_period,  # Signal line EMA
                config,
                log,
            )
        else:
            # Default to MA strategy
            data = calculate_ma_and_signals(
                data, config["FAST_PERIOD"], config["SLOW_PERIOD"], config, log
            )

        portfolio = backtest_strategy(data, config, log)
        return portfolio
    except Exception as e:
        log(f"Error processing strategy: {e!s}", "error")
        return None


def run(
    config_dict=None,
    portfolio_file=None,
    timeframe="daily",
    strategy_type="SMA",
    signal_period=9,
):
    """
    Run portfolio review analysis.

    Args:
        config_dict (dict, optional): Configuration dictionary
        portfolio_file (str, optional): Path to portfolio JSON file
        timeframe (str, optional): Data timeframe - hourly, 4hour, daily (default), 2day
        strategy_type (str, optional): Strategy type - SMA (default), EMA, MACD, ATR
        signal_period (int, optional): Signal period for MACD strategy (default: 9)

    Returns:
        bool: True if analysis successful
    """
    log, log_close, _, _ = setup_logging(
        module_name="portfolio_review", log_file="review.log"
    )

    # Convert new parameters to legacy format for backward compatibility
    def convert_parameters_to_legacy(timeframe, strategy_type, signal_period):
        """Convert new parameter format to legacy config flags."""
        legacy_params = {
            "STRATEGY_TYPE": strategy_type,
            "SIGNAL_PERIOD": signal_period,
        }

        # Convert timeframe to legacy flags
        if timeframe == "hourly":
            legacy_params.update(
                {"USE_HOURLY": True, "USE_4HOUR": False, "USE_2DAY": False}
            )
        elif timeframe == "4hour":
            legacy_params.update(
                {"USE_HOURLY": False, "USE_4HOUR": True, "USE_2DAY": False}
            )
        elif timeframe == "2day":
            legacy_params.update(
                {"USE_HOURLY": False, "USE_4HOUR": False, "USE_2DAY": True}
            )
        else:  # daily (default)
            legacy_params.update(
                {"USE_HOURLY": False, "USE_4HOUR": False, "USE_2DAY": False}
            )

        # Convert strategy_type to legacy USE_SMA flag
        legacy_params["USE_SMA"] = strategy_type == "SMA"

        return legacy_params

    try:
        # Handle portfolio file if provided
        if portfolio_file and os.path.exists(portfolio_file):
            log(f"Loading portfolio from {portfolio_file}")
            with open(portfolio_file) as f:
                portfolio_data = json.load(f)

            results = []
            for strategy in portfolio_data:
                log(f"Processing strategy: {strategy}")

                # Create config from strategy
                config = {
                    "TICKER": strategy["ticker"],
                    "USE_HOURLY": strategy["timeframe"].lower() == "hourly",
                    "FAST_PERIOD": strategy["fast_period"],
                    "SLOW_PERIOD": strategy["slow_period"],
                    "DIRECTION": strategy["direction"],
                    "USE_SMA": strategy["type"] == "SMA",
                    "STRATEGY_TYPE": strategy["type"],
                }

                # Add RSI parameters if present
                if "rsi_period" in strategy:
                    config["RSI_WINDOW"] = strategy["rsi_period"]
                if "rsi_threshold" in strategy:
                    config["RSI_THRESHOLD"] = strategy["rsi_threshold"]

                # Add signal period for MACD if present
                if "signal_period" in strategy:
                    config["SIGNAL_PERIOD"] = strategy["signal_period"]

                # Process individual strategy
                portfolio = process_strategy(config, log)
                if portfolio:
                    results.append({"config": config, "portfolio": portfolio})

            log(f"Processed {len(results)} strategies")
            log_close()
            return True

        # Handle direct config dictionary
        if config_dict:
            # Extract parameters from config_dict if they exist, otherwise use function parameters
            config_timeframe = config_dict.get("TIMEFRAME", timeframe)
            config_strategy_type = config_dict.get("STRATEGY_TYPE", strategy_type)
            config_signal_period = config_dict.get("SIGNAL_PERIOD", signal_period)

            # Apply parameter conversion to config_dict
            legacy_params = convert_parameters_to_legacy(
                config_timeframe, config_strategy_type, config_signal_period
            )
            enhanced_config = {**config_dict, **legacy_params}

            config = get_config(enhanced_config)
            log(f"Starting portfolio review for {config['TICKER']}")

            data = get_data(config["TICKER"], config, log)

            # Determine strategy type
            config_strategy_type = config.get("STRATEGY_TYPE", DEFAULT_STRATEGY_TYPE)

            if config_strategy_type == "MACD":
                # For MACD strategies, we need the signal period
                config_signal_period = config.get(
                    "SIGNAL_PERIOD", 9
                )  # Default to 9 if not specified
                data = calculate_macd_and_signals(
                    data,
                    config["FAST_PERIOD"],  # Fast EMA
                    config["SLOW_PERIOD"],  # Slow EMA
                    config_signal_period,  # Signal line EMA
                    config,
                    log,
                )
            else:
                # Default to MA strategy
                data = calculate_ma_and_signals(
                    data, config["FAST_PERIOD"], config["SLOW_PERIOD"], config, log
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
        export_strategy_type = config.get("STRATEGY_TYPE", DEFAULT_STRATEGY_TYPE)
        strategy_type_dir = "macd" if export_strategy_type == "MACD" else "ma_cross"
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
        log(f"Error during portfolio review: {e!s}", "error")
        log_close()
        raise


if __name__ == "__main__":
    try:
        result = run(CONFIG_BTC)
        if result:
            print("Portfolio review completed successfully!")
    except Exception as e:
        print(f"Portfolio review failed: {e!s}")
        raise
