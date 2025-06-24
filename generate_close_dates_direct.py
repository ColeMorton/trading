"""
Direct Last Position Close Date Generator

This script directly generates the missing Last Position Close Date values
by using the backtesting engine directly without the concurrency module.
It processes each strategy individually and extracts close dates from the
portfolio's trade records.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import polars as pl

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.tools.backtest_strategy import backtest_strategy
from app.tools.get_data import get_data
from app.tools.strategy.factory import factory


def log_function(message: str, level: str = "info"):
    """Simple logging function."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level.upper()}: {message}")


def load_live_signals() -> pd.DataFrame:
    """Load the live_signals.csv file."""
    csv_path = "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"
    return pd.read_csv(csv_path)


def generate_signals_for_strategy(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: int = 0,
) -> Optional[pl.DataFrame]:
    """Generate trading signals for a specific strategy configuration."""
    try:
        # Create config for data fetching and signal generation
        config = {
            "BASE_DIR": "/Users/colemorton/Projects/trading",
            "STRATEGY_TYPE": strategy_type,
            "DIRECTION": "Long",
            "USE_HOURLY": False,
            "USE_RSI": False,
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window if signal_window > 0 else None,
            "REFRESH": False,  # Use cached data to speed up processing
        }

        log_function(f"Fetching data for {ticker}")

        # Get price data
        data = get_data(ticker, config, log_function)

        if data is None or data.is_empty():
            log_function(f"No data available for {ticker}", "warning")
            return None

        log_function(
            f"Generating {strategy_type} signals for {ticker} ({short_window}/{long_window})"
        )

        # Generate signals using strategy factory
        strategy = factory.create_strategy(strategy_type)

        if strategy_type == "MACD":
            # MACD strategy uses different parameter structure
            result = strategy.calculate(
                data=data,
                short_window=short_window,
                long_window=long_window,
                signal_window=signal_window,
                config=config,
                log=log_function,
            )
        else:
            # SMA/EMA strategies
            result = strategy.calculate(
                data=data,
                short_window=short_window,
                long_window=long_window,
                config=config,
                log=log_function,
            )

        if result is None or result.is_empty():
            log_function(f"No signals generated for {ticker}", "warning")
            return None

        log_function(f"Generated {len(result)} rows of data with signals for {ticker}")
        return result

    except Exception as e:
        log_function(f"Error generating signals for {ticker}: {e}", "error")
        return None


def run_backtest_and_get_close_date(
    data_with_signals: pl.DataFrame, target_params: Dict
) -> Optional[str]:
    """Run backtest and extract the last position close date."""
    try:
        # Extract parameters
        ticker = target_params["ticker"]
        strategy_type = target_params["strategy_type"]
        short_window = target_params["short_window"]
        long_window = target_params["long_window"]
        signal_window = target_params.get("signal_window", 0)

        # Create backtest config
        config = {
            "USE_HOURLY": False,
            "DIRECTION": "Long",
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window,
            "STOP_LOSS": None,  # No stop loss for simplicity
            "EXPORT_TRADE_HISTORY": False,  # We'll extract from portfolio directly
        }

        log_function(f"Running backtest for {ticker}")

        # Run backtest
        portfolio = backtest_strategy(
            data=data_with_signals,
            config=config,
            log=log_function,
            export_trade_history=False,
        )

        # Get trades from portfolio
        trades = portfolio.trades.records_readable

        if trades is None or len(trades) == 0:
            log_function(f"No trades found for {ticker}", "warning")
            return None

        log_function(f"Found {len(trades)} trades for {ticker}")

        # CRITICAL: Find the specific trade that corresponds to the Last Position Open Date
        # We need to match the position opened on that specific date, not just any recent trade

        # First, convert Last Position Open Date to data index
        last_open_date = target_params.get("last_position_open_date")
        if not last_open_date:
            log_function(f"No Last Position Open Date provided for {ticker}", "warning")
            return None

        log_function(f"Looking for position opened on {last_open_date} for {ticker}")

        # Find the data index corresponding to the last position open date
        try:
            # Convert target date to comparable format
            target_date = pd.to_datetime(last_open_date).date()

            # Get the index of this date in our dataset by iterating through rows
            open_date_idx = None
            for idx, row in enumerate(data_with_signals.iter_rows(named=True)):
                row_date = pd.to_datetime(row["Date"]).date()
                if row_date == target_date:
                    open_date_idx = idx
                    break

            if open_date_idx is None:
                log_function(
                    f"Could not find index for open date {last_open_date} for {ticker}",
                    "warning",
                )
                return None

            log_function(
                f"Found open date {last_open_date} at index {open_date_idx} for {ticker}"
            )

        except Exception as e:
            log_function(f"Error finding open date index for {ticker}: {e}", "warning")
            return None

        # Find the trade that starts ON or AFTER the Last Position Open Date
        # CRITICAL: Never use trades that started BEFORE the target date
        matching_trades = trades[trades["Entry Timestamp"] >= open_date_idx]

        if len(matching_trades) == 0:
            log_function(
                f"No trade found with entry on or after {last_open_date} (index {open_date_idx}) for {ticker}",
                "warning",
            )
            return None

        # Sort by entry timestamp to get the FIRST trade on or after the target date
        matching_trades = matching_trades.sort_values("Entry Timestamp")
        log_function(
            f"Found {len(matching_trades)} potential trades on/after {last_open_date} for {ticker}, using the first one",
            "info",
        )

        # Get the specific trade that opened on the Last Position Open Date
        target_trade = matching_trades.iloc[0]

        # Show actual vs target date if different
        actual_entry_idx = target_trade["Entry Timestamp"]
        if actual_entry_idx != open_date_idx:
            try:
                actual_entry_row = data_with_signals.slice(int(actual_entry_idx), 1)
                if not actual_entry_row.is_empty():
                    actual_entry_date = pd.to_datetime(
                        actual_entry_row.select("Date").item()
                    ).strftime("%Y-%m-%d")
                    days_diff = int(actual_entry_idx - open_date_idx)
                    log_function(
                        f"Using first available trade for {ticker}: target={last_open_date}, actual={actual_entry_date} (+{days_diff} days)"
                    )
            except:
                pass

        log_function(
            f"Found trade for {ticker}: Entry={target_trade['Entry Timestamp']}, Exit={target_trade['Exit Timestamp']}, Status={target_trade['Status']}"
        )

        # Check if this specific trade is closed
        if target_trade["Status"] != "Closed":
            log_function(
                f"Position opened on {last_open_date} for {ticker} is still OPEN - no close date",
                "info",
            )
            return None

        # Get the exit timestamp for this specific trade
        exit_idx = target_trade["Exit Timestamp"]

        if pd.isna(exit_idx):
            log_function(
                f"Trade marked as Closed but has no Exit Timestamp for {ticker}",
                "warning",
            )
            return None

        # Convert exit index to actual date
        try:
            exit_date_row = data_with_signals.slice(int(exit_idx), 1)
            if not exit_date_row.is_empty():
                exit_timestamp = exit_date_row.select("Date").item()
                exit_date = pd.to_datetime(exit_timestamp).strftime("%Y-%m-%d")
                log_function(
                    f"Position opened on {last_open_date} for {ticker} was closed on {exit_date}"
                )
                return exit_date
            else:
                log_function(
                    f"Could not find date for exit index {exit_idx} for {ticker}",
                    "warning",
                )
                return None
        except Exception as e:
            log_function(
                f"Error converting exit index {exit_idx} to date for {ticker}: {e}",
                "warning",
            )
            return None

    except Exception as e:
        log_function(f"Error running backtest for {ticker}: {e}", "error")
        return None


def process_single_strategy(row: pd.Series, row_index: int) -> Dict:
    """Process a single strategy and return results."""
    ticker = row["Ticker"]
    strategy_type = row["Strategy Type"]
    short_window = int(row["Short Window"])
    long_window = int(row["Long Window"])
    signal_window = int(row["Signal Window"]) if pd.notna(row["Signal Window"]) else 0

    log_function(
        f"Processing strategy {row_index + 1}: {ticker} {strategy_type} {short_window}/{long_window}"
    )

    result = {
        "row_index": row_index,
        "ticker": ticker,
        "strategy_type": strategy_type,
        "short_window": short_window,
        "long_window": long_window,
        "signal_window": signal_window,
        "close_date": None,
        "error": None,
    }

    try:
        # Generate signals
        data_with_signals = generate_signals_for_strategy(
            ticker=ticker,
            strategy_type=strategy_type,
            short_window=short_window,
            long_window=long_window,
            signal_window=signal_window,
        )

        if data_with_signals is None:
            result["error"] = "Failed to generate signals"
            return result

        # Run backtest and get close date
        # Create target_params with the last position open date
        target_params = {
            "ticker": ticker,
            "strategy_type": strategy_type,
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window,
            "last_position_open_date": row["Last Position Open Date"],
        }

        close_date = run_backtest_and_get_close_date(
            data_with_signals=data_with_signals, target_params=target_params
        )

        result["close_date"] = close_date
        if close_date is None:
            result["error"] = "No close date found"

    except Exception as e:
        result["error"] = str(e)
        log_function(f"Error processing {ticker}: {e}", "error")

    return result


def update_csv_with_results(results: List[Dict]) -> None:
    """Update the live_signals.csv file with calculated close dates."""
    csv_path = "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"

    # Load original CSV
    df = pd.read_csv(csv_path)

    # Update rows with calculated close dates
    successful_updates = 0
    for result in results:
        if result["close_date"]:
            df.at[result["row_index"], "Last Position Close Date"] = result[
                "close_date"
            ]
            log_function(
                f"✅ Updated row {result['row_index'] + 1}: {result['ticker']} -> {result['close_date']}"
            )
            successful_updates += 1
        else:
            error_msg = result.get("error", "Unknown error")
            log_function(
                f"❌ Failed row {result['row_index'] + 1}: {result['ticker']} - {error_msg}"
            )

    # Save updated CSV
    df.to_csv(csv_path, index=False)

    log_function(
        f"Updated CSV saved with {successful_updates}/{len(results)} successful calculations"
    )


def main():
    """Main function to generate close dates for all strategies."""
    print("=" * 60)
    print("DIRECT LAST POSITION CLOSE DATE GENERATOR")
    print("=" * 60)

    try:
        # Load live signals
        df = load_live_signals()
        log_function(f"Loaded {len(df)} strategies from live_signals.csv")

        results = []

        # Process each strategy
        for idx, row in df.iterrows():
            log_function(f"\n{'='*50}")
            result = process_single_strategy(row, idx)
            results.append(result)
            log_function(f"{'='*50}")

        # Update CSV with results
        log_function(f"\n{'='*60}")
        log_function("UPDATING CSV WITH RESULTS")
        log_function(f"{'='*60}")

        update_csv_with_results(results)

        # Final summary
        successful = sum(1 for r in results if r["close_date"] is not None)
        failed = len(results) - successful

        print(f"\n{'='*60}")
        print("FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"Total strategies processed: {len(results)}")
        print(f"Successfully calculated: {successful}")
        print(f"Failed calculations: {failed}")
        print(f"Success rate: {(successful/len(results)*100):.1f}%")
        print(f"{'='*60}")

    except Exception as e:
        log_function(f"Critical error in main execution: {e}", "error")
        raise


if __name__ == "__main__":
    main()
