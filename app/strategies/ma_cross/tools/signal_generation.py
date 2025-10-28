from collections.abc import Callable
from datetime import datetime

import numpy as np
import polars as pl

from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.config_service import ConfigService
from app.tools.export_csv import export_csv
from app.tools.get_data import get_data
from app.tools.strategy.signal_utils import check_signal_match, is_signal_current
from app.tools.strategy.types import StrategyConfig as Config


def get_current_signals(
    data: pl.DataFrame,
    fast_periods: list[int],
    slow_periods: list[int],
    config: dict,
    log: Callable,
) -> pl.DataFrame:
    """
    Get current signals for all period combinations.

    Args:
        data: Price data DataFrame
        fast_periods: List of fast period values
        slow_periods: List of slow period values
        config: Configuration dictionary
        log: Logging function for recording events and errors

    Returns:
        DataFrame containing period combinations with current signals
    """
    try:
        signals = []

        # Get strategy type from config or default to SMA
        strategy_type = config.get("STRATEGY_TYPE", "SMA")

        for fast in fast_periods:
            for slow in slow_periods:
                if fast < slow:  # Ensure fast period is always less than slow period
                    temp_data = data.clone()
                    temp_data = calculate_ma_and_signals(
                        temp_data, fast, slow, config, log, strategy_type,
                    )

                    if temp_data is not None and len(temp_data) > 0:
                        current = is_signal_current(temp_data, config)
                        if current:
                            signals.append(
                                {"Fast Period": int(fast), "Slow Period": int(slow)},
                            )

        # Create DataFrame with explicit schema
        if signals:
            return pl.DataFrame(
                signals, schema={"Fast Period": pl.Int32, "Slow Period": pl.Int32},
            )
        return pl.DataFrame(schema={"Fast Period": pl.Int32, "Slow Period": pl.Int32})
    except Exception as e:
        log(f"Failed to get current signals: {e}", "error")
        return pl.DataFrame(schema={"Fast Period": pl.Int32, "Slow Period": pl.Int32})


def generate_current_signals(config: Config, log: Callable) -> pl.DataFrame:
    """
    Generate current signals for a given configuration.

    Args:
        config: Configuration dictionary
        log: Logging function for recording events and errors

    Returns:
        DataFrame containing current signals
    """
    try:
        from app.strategies.ma_cross.tools.signal_utils import set_last_trading_day

        config = ConfigService.process_config(config)
        config_copy = config.copy()
        config_copy["USE_CURRENT"] = True  # Ensure holiday check is enabled

        # Handle synthetic tickers properly
        ticker = config["TICKER"]
        if (
            config.get("USE_SYNTHETIC", False)
            and isinstance(ticker, str)
            and "_" in ticker
        ):
            # Extract original tickers from synthetic ticker name
            ticker_parts = ticker.split("_")
            if len(ticker_parts) >= 2:
                # Store original ticker parts for later use
                config_copy["TICKER_1"] = ticker_parts[0]
                if "TICKER_2" not in config_copy:
                    config_copy["TICKER_2"] = ticker_parts[1]
                log(
                    f"Extracted ticker components: {config_copy['TICKER_1']} and {config_copy['TICKER_2']}",
                )

        # Get data for the actual ticker first to determine last trading day
        data_result = get_data(config["TICKER"], config_copy, log)
        if isinstance(data_result, tuple):
            data, _ = data_result
        else:
            data = data_result

        if data is None:
            log("Failed to get price data", "error")
            return pl.DataFrame(
                schema={"Fast Period": pl.Int32, "Slow Period": pl.Int32},
            )

        # Set the last trading day from the data
        last_date = data["Date"].max()
        if isinstance(last_date, datetime):
            last_date = last_date.date()
        elif isinstance(last_date, str):
            try:
                # Try parsing with timestamp first
                last_date = datetime.strptime(last_date, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                try:
                    # Try parsing with just date if timestamp fails
                    last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
                except ValueError:
                    # Try parsing ISO format if both above fail
                    last_date = datetime.fromisoformat(last_date).date()

        log(f"Using last trading day: {last_date}")
        set_last_trading_day(last_date)

        # Check if specific windows are provided
        fast_period = config.get("FAST_PERIOD")
        slow_period = config.get("SLOW_PERIOD")

        if fast_period is not None and slow_period is not None:
            # Use specific windows from config
            current_signals = get_current_signals(
                data, [fast_period], [slow_period], config, log,
            )
        else:
            # Use window permutations from explicit ranges for full analysis
            fast_range = config.get("FAST_PERIOD_RANGE")
            slow_range = config.get("SLOW_PERIOD_RANGE")

            # DEBUG: Check what we received
            log(f"DEBUG: Config keys: {list(config.keys())}", "info")
            log(f"DEBUG: FAST_PERIOD_RANGE = {fast_range}", "info")
            log(f"DEBUG: SLOW_PERIOD_RANGE = {slow_range}", "info")

            # Backward compatibility: fallback to WINDOWS if ranges not specified
            if fast_range is None or slow_range is None:
                if "WINDOWS" in config:
                    import warnings

                    warnings.warn(
                        "WINDOWS parameter is deprecated. Use FAST_PERIOD_RANGE and SLOW_PERIOD_RANGE instead.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    windows = config.get("WINDOWS")
                    if windows is None or windows < 2:
                        log("Missing or invalid WINDOWS parameter", "error")
                        return pl.DataFrame(
                            schema={"Fast Period": pl.Int32, "Slow Period": pl.Int32},
                        )
                    # Legacy behavior
                    fast_periods = list(np.arange(2, windows))
                    slow_periods = list(np.arange(2, windows))
                else:
                    # Default ranges
                    log(
                        "No parameter ranges specified. Using defaults: FAST=[5,89], SLOW=[8,89]",
                        "warning",
                    )
                    fast_periods = list(np.arange(5, 90))  # [5, 6, ..., 89]
                    slow_periods = list(np.arange(8, 90))  # [8, 9, ..., 89]
            else:
                # Use explicit ranges
                fast_periods = list(np.arange(fast_range[0], fast_range[1] + 1))
                slow_periods = list(np.arange(slow_range[0], slow_range[1] + 1))

            current_signals = get_current_signals(
                data, fast_periods, slow_periods, config, log,
            )

        if not config.get("USE_SCANNER", False):
            export_csv(current_signals, "ma_cross", config, "current_signals")

            if len(current_signals) == 0:
                print("No signals found for today")

        return current_signals

    except Exception as e:
        log(f"Failed to generate current signals: {e}", "error")
        return pl.DataFrame(schema={"Fast Period": pl.Int32, "Slow Period": pl.Int32})


def process_ma_signals(
    ticker: str,
    ma_type: str,
    config: Config,
    fast_period: int,
    slow_period: int,
    log: Callable,
) -> bool:
    """
    Process moving average signals for a given ticker and configuration.

    Args:
        ticker: The ticker symbol to process
        ma_type: Type of moving average ('SMA' or 'EMA')
        config: Configuration dictionary
        fast_period: Fast period value from scanner
        slow_period: Slow period value from scanner
        log: Logging function for recording events and errors

    Returns:
        bool: True if current signal is found, False otherwise
    """
    ma_config = config.copy()
    ma_config.update(
        {
            "TICKER": ticker,
            "USE_SMA": ma_type == "SMA",
            "FAST_PERIOD": fast_period,
            "SLOW_PERIOD": slow_period,
        },
    )

    signals = generate_current_signals(ma_config, log)

    return check_signal_match(
        signals.to_dicts() if len(signals) > 0 else [], fast_period, slow_period,
    )

