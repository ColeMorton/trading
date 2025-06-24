"""
Simplified Last Position Close Date Generator

This script focuses on strategies that have existing portfolio files and
extracts the matching parameter combinations to generate trade history.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.concurrency.review import run_concurrency_review


def find_existing_portfolio_files():
    """Find existing portfolio files that match live_signals tickers."""
    portfolio_base = "/Users/colemorton/Projects/trading/csv/portfolios"

    # Tickers from live_signals.csv
    live_tickers = [
        "LIN",
        "VTR",
        "UHS",
        "TSLA",
        "MA",
        "CRWD",
        "LYV",
        "NFLX",
        "MCO",
        "COST",
        "INTU",
        "ISRG",
        "EQT",
        "GOOGL",
        "HSY",
        "AMZN",
        "FFIV",
        "RTX",
        "GME",
        "AMD",
        "AAPL",
        "GD",
        "LMT",
        "ILMN",
        "SHOP",
        "PWR",
        "PGR",
        "COIN",
        "COR",
        "SMCI",
    ]

    existing_files = {}

    for ticker in live_tickers:
        # Search for portfolio files for this ticker
        import glob

        pattern = f"{portfolio_base}/**/{ticker}_D_*.csv"
        found_files = glob.glob(pattern, recursive=True)

        if found_files:
            # Use the most recent file
            existing_files[ticker] = found_files[0]
            print(f"Found portfolio file for {ticker}: {found_files[0]}")

    return existing_files


def extract_matching_strategy(
    portfolio_file: str, target_params: Dict
) -> Optional[Dict]:
    """Extract the row from portfolio file that matches target parameters."""
    try:
        df = pd.read_csv(portfolio_file)

        # Find matching row
        ticker = target_params["ticker"]
        strategy_type = target_params["strategy_type"]
        short_window = target_params["short_window"]
        long_window = target_params["long_window"]

        # Filter for matching parameters
        matching_rows = df[
            (df["Ticker"] == ticker)
            & (df["Strategy Type"] == strategy_type)
            & (df["Short Window"] == short_window)
            & (df["Long Window"] == long_window)
        ]

        if len(matching_rows) > 0:
            # Return the first match as a dictionary
            return matching_rows.iloc[0].to_dict()
        else:
            print(
                f"No matching row found for {ticker} {strategy_type} {short_window}/{long_window}"
            )
            return None

    except Exception as e:
        print(f"Error reading portfolio file {portfolio_file}: {e}")
        return None


def create_single_strategy_csv(
    strategy_data: Dict, output_dir: str = "./csv/strategies/"
) -> str:
    """Create a CSV file with a single strategy row."""
    os.makedirs(output_dir, exist_ok=True)

    ticker = strategy_data["Ticker"]
    strategy_type = strategy_data["Strategy Type"]
    short_window = int(strategy_data["Short Window"])
    long_window = int(strategy_data["Long Window"])

    filename = f"{ticker}_{strategy_type}_{short_window}_{long_window}_single.csv"
    filepath = os.path.join(output_dir, filename)

    # Create DataFrame with single row
    df = pd.DataFrame([strategy_data])
    df.to_csv(filepath, index=False)

    print(f"Created single strategy CSV: {filepath}")
    return filepath


def get_trade_history_filename(strategy_data: Dict) -> str:
    """Generate expected trade history filename."""
    ticker = strategy_data["Ticker"]
    strategy_type = strategy_data["Strategy Type"]
    short_window = int(strategy_data["Short Window"])
    long_window = int(strategy_data["Long Window"])

    return f"{ticker}_D_{strategy_type}_{short_window}_{long_window}.json"


def extract_last_close_date_from_json(trade_history_path: str) -> Optional[str]:
    """Extract last position close date from trade history JSON."""
    if not os.path.exists(trade_history_path):
        print(f"Trade history file not found: {trade_history_path}")
        return None

    try:
        with open(trade_history_path, "r") as f:
            data = json.load(f)

        trades = data.get("trades", [])
        if not trades:
            print(f"No trades found in {trade_history_path}")
            return None

        # Find latest exit timestamp for closed trades
        closed_trades = [
            t for t in trades if t.get("Status") == "Closed" and t.get("Exit Timestamp")
        ]

        if not closed_trades:
            print(f"No closed trades found in {trade_history_path}")
            return None

        # Get the maximum exit timestamp
        exit_timestamps = [t["Exit Timestamp"] for t in closed_trades]
        last_exit = max(exit_timestamps)

        # Convert to date string
        try:
            dt = pd.to_datetime(last_exit)
            return dt.strftime("%Y-%m-%d")
        except:
            print(f"Failed to parse timestamp: {last_exit}")
            return None

    except Exception as e:
        print(f"Error processing {trade_history_path}: {e}")
        return None


def main():
    """Main function to generate close dates for existing portfolio strategies."""
    print("Starting Simplified Close Date Generation")
    print("=" * 50)

    # Read live signals
    live_signals_csv = (
        "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"
    )
    df = pd.read_csv(live_signals_csv)

    # Find existing portfolio files
    existing_files = find_existing_portfolio_files()

    if not existing_files:
        print("No existing portfolio files found!")
        return

    results = []

    # Process each strategy that has an existing portfolio file
    for idx, row in df.iterrows():
        ticker = row["Ticker"]

        if ticker not in existing_files:
            print(f"Skipping {ticker} - no portfolio file found")
            continue

        print(f"\nProcessing {ticker}...")

        # Target parameters from live_signals
        target_params = {
            "ticker": ticker,
            "strategy_type": row["Strategy Type"],
            "short_window": int(row["Short Window"]),
            "long_window": int(row["Long Window"]),
        }

        # Extract matching strategy from portfolio file
        portfolio_file = existing_files[ticker]
        strategy_data = extract_matching_strategy(portfolio_file, target_params)

        if strategy_data is None:
            print(f"No matching strategy found for {ticker}")
            continue

        # Create single strategy CSV
        csv_file = create_single_strategy_csv(strategy_data)

        # Run concurrency analysis
        try:
            print(f"Running backtest for {ticker}...")
            csv_filename = os.path.basename(csv_file)

            config_overrides = {
                "VISUALIZATION": False,
                "REFRESH": True,
                "EXPORT_TRADE_HISTORY": True,
            }

            success = run_concurrency_review(csv_filename, config_overrides)

            if success:
                # Extract close date from trade history
                trade_history_filename = get_trade_history_filename(strategy_data)
                trade_history_path = f"./json/trade_history/{trade_history_filename}"

                close_date = extract_last_close_date_from_json(trade_history_path)

                results.append(
                    {
                        "row_index": idx,
                        "ticker": ticker,
                        "strategy_type": target_params["strategy_type"],
                        "short_window": target_params["short_window"],
                        "long_window": target_params["long_window"],
                        "close_date": close_date,
                    }
                )

                print(f"Last close date for {ticker}: {close_date}")

            else:
                print(f"Backtest failed for {ticker}")

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    # Update live_signals.csv with results
    print("\nUpdating live_signals.csv...")
    for result in results:
        if result["close_date"]:
            df.at[result["row_index"], "Last Position Close Date"] = result[
                "close_date"
            ]
            print(
                f"Updated row {result['row_index'] + 1}: {result['ticker']} -> {result['close_date']}"
            )

    # Save updated CSV
    df.to_csv(live_signals_csv, index=False)

    print(f"\nCompleted! Successfully processed {len(results)} strategies")
    print(f"Updated CSV saved to: {live_signals_csv}")


if __name__ == "__main__":
    main()
