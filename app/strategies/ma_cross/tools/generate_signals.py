from collections.abc import Callable

import numpy as np
import pandas as pd
import polars as pl

from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd_and_signals import calculate_macd_and_signals


def generate_signals(
    data_dict: dict[str, pd.DataFrame], config: dict, log: Callable,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate entry and exit signals for multiple strategies.

    Args:
        data_dict (Dict[str, pd.DataFrame]): Dictionary of price data for each symbol
        config (Dict): Configuration dictionary containing strategy parameters
        log (Callable): Logging function for recording events and errors

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Entry and exit signals for each strategy
    """
    try:
        # Get a reference index from the first dataframe
        reference_index = next(iter(data_dict.values())).index

        # Find common date range across all dataframes
        common_index = reference_index
        for df in data_dict.values():
            common_index = common_index.intersection(df.index)

        log(f"Found common date range with {len(common_index)} periods")

        # Initialize DataFrames for entries and exits
        entries_df = pd.DataFrame(index=common_index)
        exits_df = pd.DataFrame(index=common_index)

        # Process each strategy
        for strategy_name, strategy in config["strategies"].items():
            log(f"Processing strategy: {strategy_name}")

            symbol = strategy["symbol"]
            df = data_dict[symbol]

            # Filter to common date range
            df = df.loc[common_index]

            # Create polars DataFrame with Date and Close columns
            price_df = pl.DataFrame(
                {"Date": df.index.to_list(), "Close": df["Close"].values},
            )

            # Create strategy-specific config
            strategy_config = {
                "USE_SMA": strategy.get("use_sma", config.get("USE_SMA", False)),
                "USE_RSI": strategy.get("use_rsi", config.get("USE_RSI", False)),
                "RSI_THRESHOLD": strategy.get(
                    "rsi_threshold", config.get("RSI_THRESHOLD", 70),
                ),
                "SHORT": strategy.get("short", config.get("SHORT", False)),
            }

            log(f"Strategy config for {strategy_name}: {strategy_config}")

            # Calculate signals based on strategy type
            strategy_type = strategy.get("strategy_type", "SMA")

            if strategy_type == "MACD":
                # Use MACD signal calculation
                signal_period = strategy.get("signal_period", 9)
                ma_signals = calculate_macd_and_signals(
                    price_df,
                    strategy["fast_period"],
                    strategy["slow_period"],
                    signal_period,
                    strategy_config,
                    log,
                )
            else:
                # Use MA signal calculation for SMA/EMA strategies
                ma_signals = calculate_ma_and_signals(
                    price_df,
                    strategy["fast_period"],
                    strategy["slow_period"],
                    strategy_config,
                    log,
                )

            # Convert to numpy for easier manipulation
            close_np = df["Close"].to_numpy()
            signal_np = ma_signals.get_column("Signal").to_numpy()

            # Create arrays for entries and exits based on Signal column
            entries_np = np.zeros_like(signal_np, dtype=bool)
            exits_np = np.zeros_like(signal_np, dtype=bool)

            # Initialize position tracking
            in_position = False
            entry_price = 0.0
            stop_loss_price = 0.0

            # Process signals and stop loss
            for i in range(len(close_np)):
                current_price = close_np[i]

                if not in_position:
                    if signal_np[i] != 0:  # Non-zero signal indicates entry
                        # Enter position
                        in_position = True
                        entry_price = current_price
                        entries_np[i] = True
                        # Calculate stop loss price if stop_loss is specified
                        if "stop_loss" in strategy:
                            stop_loss_price = entry_price * (
                                1 - strategy["stop_loss"] / 100
                            )
                # Check for stop loss (if configured) or signal reversal
                elif (
                    "stop_loss" in strategy and current_price <= stop_loss_price
                ) or signal_np[i] == 0:
                    # Exit position
                    in_position = False
                    entries_np[i] = False
                    exits_np[i] = True
                    entry_price = 0.0
                    stop_loss_price = 0.0

            # Add signals to DataFrames
            entries_df[strategy_name] = entries_np
            exits_df[strategy_name] = exits_np

            log(
                f"Generated signals for {strategy_name}: {sum(entries_np)} entries, {sum(exits_np)} exits",
            )

        return entries_df, exits_df

    except Exception as e:
        log(f"Error generating signals: {e!s}", "error")
        raise
