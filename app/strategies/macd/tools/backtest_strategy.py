import logging

import numpy as np
import pandas as pd
import polars as pl
import vectorbt as vbt


def backtest_strategy(data: pl.DataFrame, short: bool) -> vbt.Portfolio:
    """Backtest the MACD cross strategy."""
    try:
        # Convert to pandas DataFrame with datetime index
        df = pd.DataFrame(
            {"Close": data["Close"].to_numpy(), "Signal": data["Signal"].to_numpy()},
            index=pd.DatetimeIndex(data["Date"].to_numpy()),
        )

        if short:
            # For short-only strategy
            entries = df["Signal"] == -1  # Short entries
            exits = df["Signal"] == 0  # Exit signals

            # Log entry/exit points
            entry_points = df[entries].index
            exit_points = df[exits].index
            logging.info("\nShort strategy signals:")
            logging.info(f"Number of entry points: {len(entry_points)}")
            logging.info(f"Number of exit points: {len(exit_points)}")
            if len(entry_points) > 0:
                logging.info(f"First few entry points: {entry_points[:5]}")

            portfolio = vbt.Portfolio.from_signals(
                close=df["Close"],
                short_entries=entries,
                short_exits=exits,
                init_cash=1000,
                fees=0.001,
                freq="1D",
                direction="short",
            )
        else:
            # For long-only strategy
            entries = df["Signal"] == 1  # Long entries
            exits = df["Signal"] == 0  # Exit signals

            # Log entry/exit points
            entry_points = df[entries].index
            exit_points = df[exits].index
            logging.info("\nLong strategy signals:")
            logging.info(f"Number of entry points: {len(entry_points)}")
            logging.info(f"Number of exit points: {len(exit_points)}")
            if len(entry_points) > 0:
                logging.info(f"First few entry points: {entry_points[:5]}")

            portfolio = vbt.Portfolio.from_signals(
                close=df["Close"],
                entries=entries,
                exits=exits,
                init_cash=1000,
                fees=0.001,
                freq="1D",
                direction="longonly",
            )

        # Log portfolio statistics
        stats = portfolio.stats()
        logging.info("\nPortfolio Statistics:")
        logging.info(f"Total Return: {stats['Total Return [%]']:.2f}%")
        logging.info(f"Total Trades: {stats['Total Trades']}")
        logging.info(
            f"Win Rate: {stats['Win Rate [%]']:.2f}%"
            if not np.isnan(stats["Win Rate [%]"])
            else "Win Rate: N/A"
        )

        return portfolio

    except Exception as e:
        logging.error(f"Failed to backtest strategy: {e}")
        raise
