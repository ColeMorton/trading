"""
Generate Last Position Close Dates for Trading Strategies

This script processes the live_signals.csv file to calculate the missing
'Last Position Close Date' values for each strategy by:
1. Creating individual portfolio CSV files for each strategy configuration
2. Running backtests through the concurrency analysis module
3. Extracting the last position close date from trade history
4. Updating the original CSV with the calculated dates
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.concurrency.review import run_concurrency_review


def parse_live_signals(csv_path: str) -> List[Dict]:
    """Parse the live_signals.csv file and extract strategy configurations."""
    print(f"Reading live signals from: {csv_path}")

    df = pd.read_csv(csv_path)
    strategies = []

    for idx, row in df.iterrows():
        strategy = {
            "row_index": idx,
            "ticker": row["Ticker"],
            "strategy_type": row["Strategy Type"],
            "short_window": int(row["Short Window"]),
            "long_window": int(row["Long Window"]),
            "signal_window": int(row["Signal Window"])
            if pd.notna(row["Signal Window"])
            else 0,
            "last_position_open_date": row["Last Position Open Date"],
            "last_position_close_date": row["Last Position Close Date"]
            if pd.notna(row["Last Position Close Date"])
            else None,
        }
        strategies.append(strategy)

    print(f"Parsed {len(strategies)} strategies")
    return strategies


def create_portfolio_csv(strategy: Dict, output_dir: str = "./csv/strategies/") -> str:
    """Create a single-strategy portfolio CSV file for the given strategy."""
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename based on strategy parameters - use the expected format
    ticker = strategy["ticker"]
    strategy_type = strategy["strategy_type"]
    short_window = strategy["short_window"]
    long_window = strategy["long_window"]
    signal_window = strategy["signal_window"]

    if signal_window > 0:
        filename = f"{ticker}_{strategy_type}_{short_window}_{long_window}_{signal_window}_temp.csv"
    else:
        filename = f"{ticker}_{strategy_type}_{short_window}_{long_window}_temp.csv"

    filepath = os.path.join(output_dir, filename)

    # Create a single-row CSV with the strategy configuration
    # Using the standard portfolio CSV format expected by the system
    portfolio_data = {
        "Ticker": [strategy["ticker"]],
        "Strategy Type": [strategy["strategy_type"]],
        "Short Window": [strategy["short_window"]],
        "Long Window": [strategy["long_window"]],
        "Signal Window": [strategy["signal_window"]],
        "Signal Entry": [False],
        "Signal Exit": [False],
        "Total Open Trades": [1],
        "Total Trades": [109],  # Using the common value from live_signals.csv
        "Score": [1.7435464335001878],  # Using the common value
        "Win Rate [%]": [58.333333333333336],  # Using the common value
        "Profit Factor": [3.9179093575911397],  # Using the common value
        "Expectancy per Trade": [11.40195571289738],  # Using the common value
        "Sortino Ratio": [1.6263847632425397],  # Using the common value
        "Beats BNH [%]": [-0.527562849125985],  # Using the common value
        "Avg Trade Duration": ["36 days 12:26:39.999999999"],  # Using the common value
        "Trades Per Day": [0.012840431128232107],  # Using the common value
        "Trades per Month": [0.39417943860857585],  # Using the common value
        "Signals per Month": [0.7847425520923024],  # Using the common value
        "Expectancy per Month": [4.4944165019497335],  # Using the common value
        "Start": [0],
        "End": [5807],
        "Period": ["5808 days 00:00:00"],
        "Start Value": [1000.0],
        "End Value": [495516.29810162523],
        "Total Return [%]": [49451.62981016252],
        "Benchmark Return [%]": [104673.4570274085],
        "Max Gross Exposure [%]": [100.0],
        "Total Fees Paid": [16488.86779785018],
        "Max Drawdown [%]": [75.36773980805233],
        "Max Drawdown Duration": ["945 days 00:00:00"],
        "Total Closed Trades": [108],
        "Open Trade PnL": [10658.977453458647],
        "Best Trade [%]": [370.03177919356654],
        "Worst Trade [%]": [-47.21559328434996],
        "Avg Winning Trade [%]": [25.729590015323016],
        "Avg Losing Trade [%]": [-8.656732310498514],
        "Avg Winning Trade Duration": ["48 days 21:19:59.999999999"],
        "Avg Losing Trade Duration": ["19 days 04:48:00"],
        "Expectancy": [4480.160376371913],
        "Sharpe Ratio": [1.0248600402624466],
        "Calmar Ratio": [0.632845685864617],
        "Omega Ratio": [1.2198148132097344],
        "Skew": [1.1611211804263804],
        "Kurtosis": [25.429984945305375],
        "Tail Ratio": [1.2410871193693436],
        "Common Sense Ratio": [0.9828599412340843],
        "Value at Risk": [-0.03408948339942652],
        "Alpha": [""],
        "Beta": [""],
        "Daily Returns": [0.0014099107095734977],
        "Annual Returns": [0.35529749881252143],
        "Cumulative Returns": [494.51629810162615],
        "Annualized Return": [0.30898398237798386],
        "Annualized Volatility": [0.4172282938279037],
        "Signal Count": [0],
        "Position Count": [109],
        "Total Period": [8410.932539682539],
        "Allocation [%]": [""],
        "Stop Loss [%]": [""],
        "Last Position Open Date": [strategy["last_position_open_date"]],
        "Last Position Close Date": [""],
    }

    df = pd.DataFrame(portfolio_data)
    df.to_csv(filepath, index=False)

    print(f"Created portfolio CSV: {filepath}")
    return filepath


def get_trade_history_filename(strategy: Dict) -> str:
    """Generate the expected trade history JSON filename for a strategy."""
    ticker = strategy["ticker"]
    strategy_type = strategy["strategy_type"]
    short_window = strategy["short_window"]
    long_window = strategy["long_window"]

    # Determine timeframe (assuming daily based on the data)
    timeframe = "D"

    if strategy["signal_window"] > 0:
        # MACD strategy
        signal_window = strategy["signal_window"]
        filename = f"{ticker}_{timeframe}_{strategy_type}_{short_window}_{long_window}_{signal_window}.json"
    else:
        # SMA/EMA strategy
        filename = (
            f"{ticker}_{timeframe}_{strategy_type}_{short_window}_{long_window}.json"
        )

    return filename


def extract_last_close_date(trade_history_path: str) -> Optional[str]:
    """Extract the last position close date from a trade history JSON file."""
    if not os.path.exists(trade_history_path):
        print(f"Trade history file not found: {trade_history_path}")
        return None

    try:
        with open(trade_history_path, "r") as f:
            data = json.load(f)

        # Get trades from the JSON structure
        trades = data.get("trades", [])
        if not trades:
            print(f"No trades found in {trade_history_path}")
            return None

        # Find the latest exit timestamp for closed trades
        closed_trades = [
            t for t in trades if t.get("Status") == "Closed" and t.get("Exit Timestamp")
        ]
        if not closed_trades:
            print(f"No closed trades found in {trade_history_path}")
            return None

        # Get the maximum exit timestamp
        exit_timestamps = [t["Exit Timestamp"] for t in closed_trades]
        last_exit = max(exit_timestamps)

        # Convert timestamp to date string (YYYY-MM-DD format)
        if isinstance(last_exit, str):
            # Parse the timestamp string and extract date
            try:
                dt = pd.to_datetime(last_exit)
                return dt.strftime("%Y-%m-%d")
            except:
                print(f"Failed to parse timestamp: {last_exit}")
                return None

        return last_exit

    except Exception as e:
        print(f"Error processing trade history file {trade_history_path}: {e}")
        return None


def run_backtest_for_strategy(portfolio_csv_path: str) -> bool:
    """Run backtest for a strategy using the concurrency review module."""
    try:
        print(f"Running backtest for: {portfolio_csv_path}")

        # Extract filename without extension
        portfolio_filename = os.path.basename(portfolio_csv_path)

        # Configuration for the concurrency analysis
        config_overrides = {
            "VISUALIZATION": False,  # Disable visualization
            "REFRESH": True,  # Force refresh of data
            "EXPORT_TRADE_HISTORY": True,  # Enable trade history export
        }

        # Run the concurrency review
        success = run_concurrency_review(portfolio_filename, config_overrides)

        if success:
            print(f"Backtest completed successfully for: {portfolio_filename}")
        else:
            print(f"Backtest failed for: {portfolio_filename}")

        return success

    except Exception as e:
        print(f"Error running backtest for {portfolio_csv_path}: {e}")
        return False


def update_live_signals_csv(csv_path: str, strategies: List[Dict]) -> None:
    """Update the live_signals.csv file with calculated close dates."""
    print(f"Updating live signals CSV: {csv_path}")

    # Read the original CSV
    df = pd.read_csv(csv_path)

    # Update each row with calculated close dates
    for strategy in strategies:
        row_idx = strategy["row_index"]
        close_date = strategy.get("calculated_close_date")

        if close_date:
            df.at[row_idx, "Last Position Close Date"] = close_date
            print(f"Updated row {row_idx + 1}: {strategy['ticker']} -> {close_date}")
        else:
            print(f"No close date found for row {row_idx + 1}: {strategy['ticker']}")

    # Save the updated CSV
    df.to_csv(csv_path, index=False)
    print(f"Updated CSV saved to: {csv_path}")


def main():
    """Main function to generate last position close dates."""
    print("Starting Last Position Close Date Generation")
    print("=" * 50)

    # Configuration
    live_signals_csv = (
        "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"
    )
    temp_portfolios_dir = "./csv/strategies/"
    trade_history_dir = "./json/trade_history/"

    try:
        # Step 1: Parse live signals
        strategies = parse_live_signals(live_signals_csv)

        # Step 2: Create portfolio CSV files and run backtests
        for i, strategy in enumerate(strategies):
            print(
                f"\nProcessing strategy {i+1}/{len(strategies)}: {strategy['ticker']} {strategy['strategy_type']}"
            )

            # Create portfolio CSV
            portfolio_csv_path = create_portfolio_csv(strategy, temp_portfolios_dir)

            # Run backtest to generate trade history
            success = run_backtest_for_strategy(portfolio_csv_path)

            if success:
                # Extract close date from trade history
                trade_history_filename = get_trade_history_filename(strategy)
                trade_history_path = os.path.join(
                    trade_history_dir, trade_history_filename
                )

                close_date = extract_last_close_date(trade_history_path)
                strategy["calculated_close_date"] = close_date

                print(f"Last position close date: {close_date}")
            else:
                print(f"Failed to generate trade history for {strategy['ticker']}")
                strategy["calculated_close_date"] = None

        # Step 3: Update the original CSV
        update_live_signals_csv(live_signals_csv, strategies)

        print("\n" + "=" * 50)
        print("Last Position Close Date Generation Completed!")

        # Summary
        successful_strategies = [
            s for s in strategies if s.get("calculated_close_date")
        ]
        print(
            f"Successfully calculated close dates for {len(successful_strategies)}/{len(strategies)} strategies"
        )

    except Exception as e:
        print(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
