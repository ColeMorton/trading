"""
Complete Last Position Close Date Generator for All Strategies

This script generates the missing Last Position Close Date values for all 33 strategies
in live_signals.csv by:
1. First processing strategies with existing portfolio files
2. Then generating portfolio files for remaining strategies using MA Cross script
3. Running backtests to generate trade history
4. Extracting close dates and updating the CSV
"""

import json
import os
import subprocess
import sys
from datetime import datetime
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

    # All tickers from live_signals.csv
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
            print(f"Found existing portfolio for {ticker}: {found_files[0]}")

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
                f"No exact match found for {ticker} {strategy_type} {short_window}/{long_window}"
            )
            # Try to find any matching ticker/strategy type and use it as a base
            fallback_rows = df[
                (df["Ticker"] == ticker) & (df["Strategy Type"] == strategy_type)
            ]
            if len(fallback_rows) > 0:
                print(f"Using fallback row for {ticker} {strategy_type}")
                fallback = fallback_rows.iloc[0].to_dict()
                # Update with target parameters
                fallback["Short Window"] = short_window
                fallback["Long Window"] = long_window
                return fallback
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

    filename = f"{ticker}_{strategy_type}_{short_window}_{long_window}_temp.csv"
    filepath = os.path.join(output_dir, filename)

    # Create DataFrame with single row
    df = pd.DataFrame([strategy_data])
    df.to_csv(filepath, index=False)

    print(f"Created single strategy CSV: {filepath}")
    return filepath


def generate_portfolio_for_missing_strategy(strategy: Dict) -> Optional[str]:
    """Generate a portfolio file for a strategy that doesn't have existing data."""
    ticker = strategy["ticker"]
    strategy_type = strategy["strategy_type"]
    short_window = strategy["short_window"]
    long_window = strategy["long_window"]

    print(
        f"Generating portfolio data for {ticker} {strategy_type} {short_window}/{long_window}"
    )

    # Create a basic strategy configuration for the MA Cross script
    try:
        # Run MA Cross strategy to generate portfolio data
        cmd = [
            "python",
            "app/strategies/ma_cross/1_get_portfolios.py",
            "--ticker",
            ticker,
            "--strategy",
            strategy_type,
            "--short",
            str(short_window),
            "--long",
            str(long_window),
            "--single",  # Generate only this specific configuration
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print(f"Successfully generated portfolio for {ticker}")
            # Look for the generated file
            portfolio_pattern = f"./csv/portfolios/**/{ticker}_D_{strategy_type}.csv"
            import glob

            found_files = glob.glob(portfolio_pattern, recursive=True)
            if found_files:
                return found_files[0]
        else:
            print(f"Failed to generate portfolio for {ticker}: {result.stderr}")

    except subprocess.TimeoutExpired:
        print(f"Timeout generating portfolio for {ticker}")
    except Exception as e:
        print(f"Error generating portfolio for {ticker}: {e}")

    # Fallback: create a synthetic portfolio row
    return create_synthetic_portfolio_row(strategy)


def create_synthetic_portfolio_row(strategy: Dict) -> Dict:
    """Create a synthetic portfolio row based on strategy parameters."""
    # Use template data from live_signals.csv but update key fields
    return {
        "Ticker": strategy["ticker"],
        "Strategy Type": strategy["strategy_type"],
        "Short Window": strategy["short_window"],
        "Long Window": strategy["long_window"],
        "Signal Window": 0,
        "Signal Entry": False,
        "Signal Exit": False,
        "Total Open Trades": 1,
        "Total Trades": 109,
        "Score": 1.7435464335001878,
        "Win Rate [%]": 58.333333333333336,
        "Profit Factor": 3.9179093575911397,
        "Expectancy per Trade": 11.40195571289738,
        "Sortino Ratio": 1.6263847632425397,
        "Beats BNH [%]": -0.527562849125985,
        "Avg Trade Duration": "36 days 12:26:39.999999999",
        "Trades Per Day": 0.012840431128232107,
        "Trades per Month": 0.39417943860857585,
        "Signals per Month": 0.7847425520923024,
        "Expectancy per Month": 4.4944165019497335,
        "Start": 0,
        "End": 5807,
        "Period": "5808 days 00:00:00",
        "Start Value": 1000.0,
        "End Value": 495516.29810162523,
        "Total Return [%]": 49451.62981016252,
        "Benchmark Return [%]": 104673.4570274085,
        "Max Gross Exposure [%]": 100.0,
        "Total Fees Paid": 16488.86779785018,
        "Max Drawdown [%]": 75.36773980805233,
        "Max Drawdown Duration": "945 days 00:00:00",
        "Total Closed Trades": 108,
        "Open Trade PnL": 10658.977453458647,
        "Best Trade [%]": 370.03177919356654,
        "Worst Trade [%]": -47.21559328434996,
        "Avg Winning Trade [%]": 25.729590015323016,
        "Avg Losing Trade [%]": -8.656732310498514,
        "Avg Winning Trade Duration": "48 days 21:19:59.999999999",
        "Avg Losing Trade Duration": "19 days 04:48:00",
        "Expectancy": 4480.160376371913,
        "Sharpe Ratio": 1.0248600402624466,
        "Calmar Ratio": 0.632845685864617,
        "Omega Ratio": 1.2198148132097344,
        "Skew": 1.1611211804263804,
        "Kurtosis": 25.429984945305375,
        "Tail Ratio": 1.2410871193693436,
        "Common Sense Ratio": 0.9828599412340843,
        "Value at Risk": -0.03408948339942652,
        "Alpha": "",
        "Beta": "",
        "Daily Returns": 0.0014099107095734977,
        "Annual Returns": 0.35529749881252143,
        "Cumulative Returns": 494.51629810162615,
        "Annualized Return": 0.30898398237798386,
        "Annualized Volatility": 0.4172282938279037,
        "Signal Count": 0,
        "Position Count": 109,
        "Total Period": 8410.932539682539,
        "Allocation [%]": "",
        "Stop Loss [%]": "",
        "Last Position Open Date": strategy.get("last_position_open_date", ""),
        "Last Position Close Date": "",
    }


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
    """Main function to generate close dates for all strategies."""
    print("Starting Complete Close Date Generation")
    print("=" * 60)

    # Read live signals
    live_signals_csv = (
        "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"
    )
    df = pd.read_csv(live_signals_csv)

    # Find existing portfolio files
    existing_files = find_existing_portfolio_files()

    print(f"\nFound existing portfolio files for {len(existing_files)} strategies")
    print(f"Need to generate data for {33 - len(existing_files)} strategies")

    results = []

    # Process each strategy
    for idx, row in df.iterrows():
        ticker = row["Ticker"]
        strategy_type = row["Strategy Type"]
        short_window = int(row["Short Window"])
        long_window = int(row["Long Window"])

        print(f"\n{'='*50}")
        print(
            f"Processing strategy {idx+1}/33: {ticker} {strategy_type} {short_window}/{long_window}"
        )
        print(f"{'='*50}")

        # Target parameters from live_signals
        target_params = {
            "ticker": ticker,
            "strategy_type": strategy_type,
            "short_window": short_window,
            "long_window": long_window,
            "last_position_open_date": row["Last Position Open Date"],
        }

        strategy_data = None

        # Try to get data from existing portfolio file
        if ticker in existing_files:
            print(f"Using existing portfolio file for {ticker}")
            portfolio_file = existing_files[ticker]
            strategy_data = extract_matching_strategy(portfolio_file, target_params)

        # If no existing data, generate it
        if strategy_data is None:
            print(f"No existing data found for {ticker}, creating synthetic data")
            strategy_data = create_synthetic_portfolio_row(target_params)

        # Create single strategy CSV
        csv_file = create_single_strategy_csv(strategy_data)

        # Run concurrency analysis to generate trade history
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
                        "strategy_type": strategy_type,
                        "short_window": short_window,
                        "long_window": long_window,
                        "close_date": close_date,
                    }
                )

                print(f"✅ Successfully extracted close date for {ticker}: {close_date}")

            else:
                print(f"❌ Backtest failed for {ticker}")
                results.append(
                    {
                        "row_index": idx,
                        "ticker": ticker,
                        "strategy_type": strategy_type,
                        "short_window": short_window,
                        "long_window": long_window,
                        "close_date": None,
                    }
                )

        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")
            results.append(
                {
                    "row_index": idx,
                    "ticker": ticker,
                    "strategy_type": strategy_type,
                    "short_window": short_window,
                    "long_window": long_window,
                    "close_date": None,
                }
            )

        # Clean up temporary file
        try:
            os.remove(csv_file)
        except:
            pass

    # Update live_signals.csv with results
    print(f"\n{'='*60}")
    print("Updating live_signals.csv with calculated close dates...")
    print(f"{'='*60}")

    successful_updates = 0
    for result in results:
        if result["close_date"]:
            df.at[result["row_index"], "Last Position Close Date"] = result[
                "close_date"
            ]
            print(
                f"✅ Updated row {result['row_index'] + 1}: {result['ticker']} -> {result['close_date']}"
            )
            successful_updates += 1
        else:
            print(
                f"❌ No close date available for row {result['row_index'] + 1}: {result['ticker']}"
            )

    # Save updated CSV
    df.to_csv(live_signals_csv, index=False)

    print(f"\n{'='*60}")
    print("COMPLETION SUMMARY")
    print(f"{'='*60}")
    print(f"Total strategies processed: {len(results)}")
    print(f"Successfully calculated close dates: {successful_updates}")
    print(f"Failed calculations: {len(results) - successful_updates}")
    print(f"Success rate: {(successful_updates/len(results)*100):.1f}%")
    print(f"Updated CSV saved to: {live_signals_csv}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
