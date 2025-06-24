"""
Trade History CSV Exporter

Specialized exporter for generating position-level trade history CSV files.
Each row represents a single position with unique UUID identification.

Focus: Individual position data only (no strategy-level aggregates)
Output: CSV format optimized for position analysis and risk management
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import polars as pl


def generate_position_uuid(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: int,
    entry_date: str,
) -> str:
    """Generate unique position identifier."""
    # Clean entry date to YYYY-MM-DD format
    if isinstance(entry_date, str):
        if " " in entry_date:
            entry_date = entry_date.split(" ")[0]

    return f"{ticker}_{strategy_type}_{short_window}_{long_window}_{signal_window}_{entry_date}"


def extract_position_data(trade_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract individual position data from trade history JSON."""
    positions = []

    metadata = trade_data.get("metadata", {})
    strategy_config = metadata.get("strategy_config", {})
    parameters = strategy_config.get("parameters", {})

    # Strategy identification
    ticker = strategy_config.get("ticker", "")
    strategy_type = strategy_config.get("strategy_type", "")
    short_window = parameters.get("short_window", 0)
    long_window = parameters.get("long_window", 0)
    signal_window = parameters.get("signal_window", 0)

    # Process trades (individual positions)
    trades = trade_data.get("trades", [])

    for trade in trades:
        entry_timestamp = trade.get("Entry Timestamp", "")
        exit_timestamp = trade.get("Exit Timestamp", "")

        # Generate position UUID
        position_uuid = generate_position_uuid(
            ticker,
            strategy_type,
            short_window,
            long_window,
            signal_window,
            entry_timestamp,
        )

        # Calculate days since entry for open positions
        days_since_entry = None
        current_unrealized_pnl = None
        current_excursion_status = None

        # Calculate MFE/MAE using price data
        mfe, mae, mfe_mae_ratio, exit_efficiency = calculate_mfe_mae(
            ticker,
            entry_timestamp,
            exit_timestamp or "",
            trade.get("Avg Entry Price", 0),
            trade.get("Direction", "Long"),
        )

        # Calculate exit efficiency for closed positions
        if exit_timestamp and trade.get("PnL") and mfe and mfe > 0:
            position_return = trade.get("Return", 0)
            exit_efficiency = position_return / mfe if mfe > 0 else None

        if not exit_timestamp or exit_timestamp == "":
            # Open position
            if entry_timestamp:
                try:
                    entry_date = datetime.strptime(
                        entry_timestamp.split(" ")[0], "%Y-%m-%d"
                    )
                    days_since_entry = (datetime.now() - entry_date).days
                    current_excursion_status = "Open"
                except:
                    days_since_entry = None

        position = {
            "Position_UUID": position_uuid,
            "Ticker": ticker,
            "Strategy_Type": strategy_type,
            "Short_Window": short_window,
            "Long_Window": long_window,
            "Signal_Window": signal_window,
            "Entry_Timestamp": entry_timestamp,
            "Exit_Timestamp": exit_timestamp if exit_timestamp else None,
            "Avg_Entry_Price": trade.get("Avg Entry Price", None),
            "Avg_Exit_Price": trade.get("Avg Exit Price", None),
            "Position_Size": trade.get("Size", None),
            "Direction": trade.get("Direction", ""),
            "PnL": trade.get("PnL", None),
            "Return": trade.get("Return", None),
            "Duration_Days": trade.get("Duration_Days", None),
            "Trade_Type": trade.get("Trade_Type", ""),
            "Status": trade.get("Status", ""),
            "Max_Favourable_Excursion": mfe,
            "Max_Adverse_Excursion": mae,
            "MFE_MAE_Ratio": mfe_mae_ratio,
            "Exit_Efficiency": exit_efficiency,
            "Days_Since_Entry": days_since_entry,
            "Current_Unrealized_PnL": current_unrealized_pnl,
            "Current_Excursion_Status": current_excursion_status,
        }

        positions.append(position)

    return positions


def export_single_trade_history_to_csv(
    json_file_path: str, output_dir: str = None
) -> str:
    """Export single JSON trade history file to position-level CSV."""

    if output_dir is None:
        output_dir = "/Users/colemorton/Projects/trading/csv/trade_history"

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load JSON data
    with open(json_file_path, "r") as f:
        trade_data = json.load(f)

    # Extract position data
    positions = extract_position_data(trade_data)

    if not positions:
        logging.warning(f"No positions found in {json_file_path}")
        return None

    # Create DataFrame
    df = pd.DataFrame(positions)

    # Generate output filename based on strategy
    strategy_config = trade_data.get("metadata", {}).get("strategy_config", {})
    ticker = strategy_config.get("ticker", "UNKNOWN")
    strategy_type = strategy_config.get("strategy_type", "UNKNOWN")
    params = strategy_config.get("parameters", {})

    output_filename = f"{ticker}_{strategy_type}"
    if params:
        for key, value in params.items():
            if value != 0:  # Skip signal_window if 0
                output_filename += f"_{value}"
    output_filename += "_positions.csv"

    output_path = Path(output_dir) / output_filename

    # Save to CSV
    df.to_csv(output_path, index=False)

    logging.info(f"Exported {len(positions)} positions to {output_path}")
    return str(output_path)


def export_all_trade_histories_to_csv(
    json_dir: str = None, output_dir: str = None
) -> List[str]:
    """Export all JSON trade history files to position-level CSV files."""

    if json_dir is None:
        json_dir = "/Users/colemorton/Projects/trading/json/trade_history"

    if output_dir is None:
        output_dir = "/Users/colemorton/Projects/trading/csv/trade_history"

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Find all JSON files
    json_files = list(Path(json_dir).glob("*.json"))

    if not json_files:
        logging.warning(f"No JSON files found in {json_dir}")
        return []

    exported_files = []

    for json_file in json_files:
        try:
            output_path = export_single_trade_history_to_csv(str(json_file), output_dir)
            if output_path:
                exported_files.append(output_path)
        except Exception as e:
            logging.error(f"Failed to export {json_file}: {e}")

    logging.info(f"Exported {len(exported_files)} trade history CSV files")
    return exported_files


def calculate_mfe_mae(
    ticker: str,
    entry_date: str,
    exit_date: str,
    entry_price: float,
    direction: str = "Long",
) -> tuple:
    """Calculate Max Favourable Excursion and Max Adverse Excursion using price data."""

    try:
        # Load price data
        price_file = f"/Users/colemorton/Projects/trading/csv/price_data/{ticker}_D.csv"
        if not Path(price_file).exists():
            logging.warning(f"Price data not found for {ticker}")
            return None, None, None, None

        # Read price data
        df = pd.read_csv(price_file)
        df["Date"] = pd.to_datetime(df["Date"])

        # Convert dates
        entry_dt = pd.to_datetime(entry_date.split(" ")[0])
        exit_dt = (
            pd.to_datetime(exit_date.split(" ")[0]) if exit_date else pd.Timestamp.now()
        )

        # Filter to position period
        position_df = df[(df["Date"] >= entry_dt) & (df["Date"] <= exit_dt)].copy()

        if position_df.empty:
            logging.warning(
                f"No price data found for {ticker} between {entry_date} and {exit_date}"
            )
            return None, None, None, None

        if direction.upper() == "LONG":
            # For long positions
            # MFE = (Max High - Entry Price) / Entry Price
            max_high = position_df["High"].max()
            mfe = (max_high - entry_price) / entry_price

            # MAE = (Entry Price - Min Low) / Entry Price
            min_low = position_df["Low"].min()
            mae = (entry_price - min_low) / entry_price
        else:
            # For short positions (if applicable)
            # MFE = (Entry Price - Min Low) / Entry Price
            min_low = position_df["Low"].min()
            mfe = (entry_price - min_low) / entry_price

            # MAE = (Max High - Entry Price) / Entry Price
            max_high = position_df["High"].max()
            mae = (max_high - entry_price) / entry_price

        # Calculate ratios
        mfe_mae_ratio = mfe / mae if mae != 0 else None

        return mfe, mae, mfe_mae_ratio, None  # Exit efficiency calculated separately

    except Exception as e:
        logging.error(f"Error calculating MFE/MAE for {ticker}: {e}")
        return None, None, None, None


def migrate_live_signals_to_trade_history():
    """Migrate live_signals.csv to new trade_history schema with position-level data."""

    live_signals_file = (
        "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"
    )
    output_file = "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"

    # Read current live signals
    df = pd.read_csv(live_signals_file)

    # Create new position-level records
    positions = []

    for _, row in df.iterrows():
        if pd.isna(row["Ticker"]) or row["Ticker"] == "":
            continue

        ticker = row["Ticker"]
        strategy_type = row["Strategy Type"]
        short_window = row["Short Window"]
        long_window = row["Long Window"]
        signal_window = row["Signal Window"]
        entry_date = row["Last Position Open Date"]
        exit_date = (
            row["Last Position Close Date"]
            if pd.notna(row["Last Position Close Date"])
            else None
        )

        # Generate UUID
        position_uuid = generate_position_uuid(
            ticker, strategy_type, short_window, long_window, signal_window, entry_date
        )

        # Look for corresponding JSON data
        json_files = list(
            Path("/Users/colemorton/Projects/trading/json/trade_history").glob(
                f"{ticker}_D_{strategy_type}_*.json"
            )
        )

        trade_data = None
        matching_trade = None

        # Find matching trade data
        for json_file in json_files:
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)

                # Check if parameters match
                config = data.get("metadata", {}).get("strategy_config", {})
                params = config.get("parameters", {})

                if (
                    params.get("short_window") == short_window
                    and params.get("long_window") == long_window
                    and params.get("signal_window", 0) == signal_window
                ):
                    # Find trade matching entry date
                    trades = data.get("trades", [])
                    for trade in trades:
                        trade_entry = trade.get("Entry Timestamp", "").split(" ")[0]
                        if trade_entry == str(entry_date):
                            matching_trade = trade
                            trade_data = data
                            break

                    if matching_trade:
                        break

            except Exception as e:
                logging.warning(f"Could not read {json_file}: {e}")
                continue

        # Use trade data if found, otherwise create minimal record
        if matching_trade:
            # Calculate MFE/MAE
            mfe, mae, mfe_mae_ratio, _ = calculate_mfe_mae(
                ticker,
                matching_trade.get("Entry Timestamp", ""),
                matching_trade.get("Exit Timestamp", ""),
                matching_trade.get("Avg Entry Price", 0),
            )

            # Calculate exit efficiency
            exit_efficiency = None
            if (
                matching_trade.get("Exit Timestamp")
                and matching_trade.get("Return")
                and mfe
                and mfe > 0
            ):
                exit_efficiency = matching_trade.get("Return", 0) / mfe

            # Calculate days since entry for open positions
            days_since_entry = None
            if not matching_trade.get("Exit Timestamp"):
                try:
                    entry_dt = datetime.strptime(entry_date, "%Y-%m-%d")
                    days_since_entry = (datetime.now() - entry_dt).days
                except:
                    pass

            position = {
                "Position_UUID": position_uuid,
                "Ticker": ticker,
                "Strategy_Type": strategy_type,
                "Short_Window": short_window,
                "Long_Window": long_window,
                "Signal_Window": signal_window,
                "Entry_Timestamp": matching_trade.get(
                    "Entry Timestamp", f"{entry_date} 00:00:00"
                ),
                "Exit_Timestamp": matching_trade.get("Exit Timestamp") or None,
                "Avg_Entry_Price": matching_trade.get("Avg Entry Price"),
                "Avg_Exit_Price": matching_trade.get("Avg Exit Price"),
                "Position_Size": matching_trade.get("Size"),
                "Direction": matching_trade.get("Direction", "Long"),
                "PnL": matching_trade.get("PnL"),
                "Return": matching_trade.get("Return"),
                "Duration_Days": matching_trade.get("Duration_Days"),
                "Trade_Type": matching_trade.get("Trade_Type", ""),
                "Status": matching_trade.get(
                    "Status", "Open" if not exit_date else "Closed"
                ),
                "Max_Favourable_Excursion": mfe,
                "Max_Adverse_Excursion": mae,
                "MFE_MAE_Ratio": mfe_mae_ratio,
                "Exit_Efficiency": exit_efficiency,
                "Days_Since_Entry": days_since_entry,
                "Current_Unrealized_PnL": None,
                "Current_Excursion_Status": "Open" if not exit_date else None,
            }
        else:
            # Create minimal record without trade data
            days_since_entry = None
            if not exit_date:
                try:
                    entry_dt = datetime.strptime(entry_date, "%Y-%m-%d")
                    days_since_entry = (datetime.now() - entry_dt).days
                except:
                    pass

            position = {
                "Position_UUID": position_uuid,
                "Ticker": ticker,
                "Strategy_Type": strategy_type,
                "Short_Window": short_window,
                "Long_Window": long_window,
                "Signal_Window": signal_window,
                "Entry_Timestamp": f"{entry_date} 00:00:00",
                "Exit_Timestamp": f"{exit_date} 00:00:00" if exit_date else None,
                "Avg_Entry_Price": None,
                "Avg_Exit_Price": None,
                "Position_Size": None,
                "Direction": "Long",
                "PnL": None,
                "Return": None,
                "Duration_Days": None,
                "Trade_Type": "",
                "Status": "Open" if not exit_date else "Closed",
                "Max_Favourable_Excursion": None,
                "Max_Adverse_Excursion": None,
                "MFE_MAE_Ratio": None,
                "Exit_Efficiency": None,
                "Days_Since_Entry": days_since_entry,
                "Current_Unrealized_PnL": None,
                "Current_Excursion_Status": "Open" if not exit_date else None,
            }

        positions.append(position)

    # Create new DataFrame
    new_df = pd.DataFrame(positions)

    # Save to live_signals.csv (overwrite)
    new_df.to_csv(output_file, index=False)

    logging.info(f"Migrated {len(positions)} positions to {output_file}")
    return output_file


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Migrate live signals to new schema
    migrated_file = migrate_live_signals_to_trade_history()
    print(f"Live signals migration complete: {migrated_file}")

    # Export all trade histories to individual CSV files (without consolidation)
    exported_files = export_all_trade_histories_to_csv()
    print(f"Exported {len(exported_files)} individual trade history CSV files")
