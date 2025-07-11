"""
Trade History CSV Exporter

Generalized exporter for creating position-level trade history CSV files from any ticker and strategy.
Each row represents a single position with unique UUID identification.

Features:
- Configuration-driven file paths for any trading system
- Generic ticker/strategy support with validation
- Modular MFE/MAE calculation for any price data format
- Reusable position extraction and migration functions

Output: CSV format optimized for position analysis and risk management
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl

from .utils.mfe_mae_calculator import get_mfe_mae_calculator
from .uuid_utils import generate_position_uuid as _generate_position_uuid


# Configuration class for flexible path management
class TradingSystemConfig:
    """Configuration for trading system file paths and settings."""

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    @property
    def price_data_dir(self) -> Path:
        return self.base_dir / "csv" / "price_data"

    @property
    def positions_dir(self) -> Path:
        return self.base_dir / "csv" / "positions"

    @property
    def strategies_dir(self) -> Path:
        return self.base_dir / "csv" / "strategies"

    @property
    def trade_history_dir(self) -> Path:
        return self.base_dir / "json" / "trade_history"

    @property
    def trade_history_csv_dir(self) -> Path:
        return self.base_dir / "csv" / "trade_history"

    def get_price_data_file(self, ticker: str, timeframe: str = "D") -> Path:
        """Get price data file path for any ticker and timeframe."""
        return self.price_data_dir / f"{ticker}_{timeframe}.csv"


# Global configuration instance
_config = None


def get_config() -> TradingSystemConfig:
    """Get or create global configuration instance."""
    global _config
    if _config is None:
        _config = TradingSystemConfig()
    return _config


def set_config(config: TradingSystemConfig):
    """Set global configuration instance."""
    global _config
    _config = config


def generate_position_uuid(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: int,
    entry_date: str,
) -> str:
    """Generate unique position identifier."""
    # Use centralized UUID generation
    return _generate_position_uuid(
        ticker=ticker,
        strategy_type=strategy_type,
        short_window=short_window,
        long_window=long_window,
        signal_window=signal_window,
        entry_date=entry_date,
    )


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

        # Calculate MFE/MAE using price data with configuration
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
                    entry_date_str = entry_timestamp.split(" ")[0]
                    # Try YYYYMMDD format first (new convention), then YYYY-MM-DD (old format)
                    if len(entry_date_str) == 8 and entry_date_str.isdigit():
                        entry_date = datetime.strptime(entry_date_str, "%Y%m%d")
                    else:
                        entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d")
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
            "Trade_Type": trade.get("Trade_Type", trade.get("Direction", "Long")),
            "Status": trade.get("Status", ""),
            "Max_Favourable_Excursion": round(mfe, 6) if mfe is not None else None,
            "Max_Adverse_Excursion": round(mae, 6) if mae is not None else None,
            "MFE_MAE_Ratio": round(mfe_mae_ratio, 6)
            if mfe_mae_ratio is not None
            else None,
            "Exit_Efficiency": round(exit_efficiency, 6)
            if exit_efficiency is not None
            else None,
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
        output_dir = "/Users/colemorton/Projects/trading/csv/positions"

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
        # For SMA and EMA strategies, omit signal_window parameter
        strategy_upper = strategy_type.upper()
        for key, value in params.items():
            # Skip signal_window for SMA/EMA strategies, regardless of value
            if key == "signal_window" and strategy_upper in ["SMA", "EMA"]:
                continue
            # For other strategies, include all non-zero parameters
            if value != 0:
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
        output_dir = "/Users/colemorton/Projects/trading/csv/positions"

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
    timeframe: str = "D",
    config: TradingSystemConfig = None,
) -> tuple:
    """Calculate Max Favourable Excursion and Max Adverse Excursion using price data.

    Args:
        ticker: Stock/asset ticker symbol
        entry_date: Position entry date (YYYY-MM-DD or datetime string)
        exit_date: Position exit date (YYYY-MM-DD or datetime string, empty for open positions)
        entry_price: Entry price for position
        direction: Position direction ('Long' or 'Short')
        timeframe: Price data timeframe ('D' for daily, 'H' for hourly, etc.)
        config: Trading system configuration (uses global if None)

    Returns:
        tuple: (mfe, mae, mfe_mae_ratio, exit_efficiency)
    """

    if config is None:
        config = get_config()

    try:
        # Load price data using configuration
        price_file = config.get_price_data_file(ticker, timeframe)
        if not price_file.exists():
            logging.warning(f"Price data not found for {ticker} at {price_file}")
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

        # Use centralized MFE/MAE calculator
        calculator = get_mfe_mae_calculator()
        mfe, mae = calculator.calculate_from_ohlc(
            entry_price=entry_price,
            ohlc_data=position_df,
            direction=direction,
            high_col="High",
            low_col="Low",
        )

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
                    # Try YYYYMMDD format first (new convention), then YYYY-MM-DD (old format)
                    if len(entry_date) == 8 and entry_date.isdigit():
                        entry_dt = datetime.strptime(entry_date, "%Y%m%d")
                    else:
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
                    # Try YYYYMMDD format first (new convention), then YYYY-MM-DD (old format)
                    if len(entry_date) == 8 and entry_date.isdigit():
                        entry_dt = datetime.strptime(entry_date, "%Y%m%d")
                    else:
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


def estimate_strategy_entry_date(
    ticker: str, strategy_type: str, short_window: int, long_window: int
) -> tuple:
    """Estimate entry date and price for a strategy by finding recent crossover signals."""

    try:
        # Load price data
        price_file = f"/Users/colemorton/Projects/trading/csv/price_data/{ticker}_D.csv"
        if not Path(price_file).exists():
            logging.warning(f"Price data not found for {ticker}")
            return None, None

        # Read price data
        df = pd.read_csv(price_file)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")

        # Calculate moving averages
        if strategy_type.upper() == "SMA":
            df[f"MA_{short_window}"] = df["Close"].rolling(window=short_window).mean()
            df[f"MA_{long_window}"] = df["Close"].rolling(window=long_window).mean()
        elif strategy_type.upper() == "EMA":
            df[f"MA_{short_window}"] = df["Close"].ewm(span=short_window).mean()
            df[f"MA_{long_window}"] = df["Close"].ewm(span=long_window).mean()
        else:
            logging.warning(f"Unknown strategy type: {strategy_type}")
            return None, None

        # Find crossover signals (short MA crossing above long MA for long entry)
        df["Signal"] = (df[f"MA_{short_window}"] > df[f"MA_{long_window}"]) & (
            df[f"MA_{short_window}"].shift(1) <= df[f"MA_{long_window}"].shift(1)
        )

        # Get most recent signal within last 200 days
        recent_signals = df[df["Signal"] == True].tail(5)  # Last 5 signals

        if recent_signals.empty:
            # No signals found, estimate based on current position being profitable
            # Use a date where the strategy would have entered (estimate 30-90 days ago)
            current_date = pd.Timestamp.now()
            estimate_days_ago = 60  # Estimate 60 days ago
            entry_date = current_date - pd.Timedelta(days=estimate_days_ago)

            # Find closest date in price data
            closest_idx = df["Date"].searchsorted(entry_date)
            if closest_idx < len(df):
                entry_row = df.iloc[closest_idx]
                return entry_row["Date"].strftime("%Y%m%d"), entry_row["Close"]
            else:
                return None, None

        # Use the most recent signal
        entry_row = recent_signals.iloc[-1]
        entry_date = entry_row["Date"].strftime("%Y%m%d")
        entry_price = entry_row["Close"]  # Use closing price as entry price

        return entry_date, entry_price

    except Exception as e:
        logging.error(f"Error estimating entry for {ticker} {strategy_type}: {e}")
        return None, None


def assess_trade_quality(
    mfe: float, mae: float, exit_efficiency: float, return_pct: float = None
) -> str:
    """Assess trade quality based on MFE/MAE and exit efficiency metrics."""

    if mfe is None or mae is None:
        return ""

    risk_reward_ratio = mfe / mae if mae > 0 else float("inf")

    # Handle edge cases with poor risk/reward setups
    if mfe < 0.02 and mae > 0.05:  # MFE < 2%, MAE > 5%
        return "Poor Setup - High Risk, Low Reward"
    elif return_pct is not None and return_pct < 0 and abs(return_pct) > mfe:
        return "Failed to Capture Upside"
    elif risk_reward_ratio >= 3.0 and (
        exit_efficiency is None or exit_efficiency >= 0.8
    ):
        return "Excellent"
    elif risk_reward_ratio >= 2.0 and (
        exit_efficiency is None or exit_efficiency >= 0.6
    ):
        return "Excellent"
    elif risk_reward_ratio >= 1.5 and (
        exit_efficiency is None or exit_efficiency >= 0.4
    ):
        return "Good"
    else:
        return "Poor"


def convert_strategy_to_trade_history(strategy_name: str):
    """Convert strategy CSV data to position-level trade history CSV."""

    strategy_file = (
        f"/Users/colemorton/Projects/trading/csv/strategies/{strategy_name}.csv"
    )
    output_file = (
        f"/Users/colemorton/Projects/trading/csv/positions/{strategy_name}.csv"
    )

    # Create output directory
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # Read strategy data
    df = pd.read_csv(strategy_file)

    positions = []

    for _, row in df.iterrows():
        if pd.isna(row["Ticker"]) or row["Ticker"] == "":
            continue

        ticker = row["Ticker"]
        strategy_type = row["Strategy Type"]
        short_window = int(row["Short Window"])
        long_window = int(row["Long Window"])
        signal_window = (
            int(row["Signal Window"]) if pd.notna(row["Signal Window"]) else 0
        )

        # Skip if no open trades
        if row["Total Open Trades"] == 0:
            continue

        # Estimate entry date and price
        entry_date, entry_price = estimate_strategy_entry_date(
            ticker, strategy_type, short_window, long_window
        )

        if entry_date is None or entry_price is None:
            logging.warning(f"Could not estimate entry for {ticker} {strategy_type}")
            continue

        # Generate Position UUID
        position_uuid = generate_position_uuid(
            ticker, strategy_type, short_window, long_window, signal_window, entry_date
        )

        # Calculate MFE/MAE for open position (no exit date)
        mfe, mae, mfe_mae_ratio, _ = calculate_mfe_mae(
            ticker, f"{entry_date} 00:00:00", "", entry_price, "Long"
        )

        # Calculate days since entry
        try:
            # Try YYYYMMDD format first (new convention), then YYYY-MM-DD (old format)
            if len(entry_date) == 8 and entry_date.isdigit():
                entry_dt = datetime.strptime(entry_date, "%Y%m%d")
            else:
                entry_dt = datetime.strptime(entry_date, "%Y-%m-%d")
            days_since_entry = (datetime.now() - entry_dt).days
        except:
            days_since_entry = None

        # Assess trade quality for open position
        trade_quality = assess_trade_quality(mfe, mae, None, None)

        position = {
            "Position_UUID": position_uuid,
            "Ticker": ticker,
            "Strategy_Type": strategy_type,
            "Short_Window": short_window,
            "Long_Window": long_window,
            "Signal_Window": signal_window,
            "Entry_Timestamp": f"{entry_date} 00:00:00",
            "Exit_Timestamp": None,  # Open position
            "Avg_Entry_Price": entry_price,
            "Avg_Exit_Price": None,  # Open position
            "Position_Size": None,  # Not available in protected.csv
            "Direction": "Long",  # Assume long positions
            "PnL": None,  # Open position
            "Return": None,  # Open position
            "Duration_Days": None,  # Open position
            "Trade_Type": "",
            "Status": "Open",
            "Max_Favourable_Excursion": mfe,
            "Max_Adverse_Excursion": mae,
            "MFE_MAE_Ratio": mfe_mae_ratio,
            "Exit_Efficiency": None,  # N/A for open positions
            "Days_Since_Entry": days_since_entry,
            "Current_Unrealized_PnL": None,  # Could be calculated
            "Current_Excursion_Status": "Open",
            "Exit_Efficiency_Fixed": None,  # N/A for open positions
            "Trade_Quality": trade_quality,
        }

        positions.append(position)

        logging.info(
            f"Created position for {ticker} {strategy_type} - Entry: {entry_date} @ ${entry_price:.2f}"
        )

    if not positions:
        logging.warning(f"No positions created from {strategy_name}.csv")
        return None

    # Create DataFrame and save
    positions_df = pd.DataFrame(positions)
    positions_df.to_csv(output_file, index=False)

    logging.info(
        f"Created {len(positions)} {strategy_name} portfolio positions in {output_file}"
    )
    return output_file


def convert_protected_to_trade_history():
    """Convert protected.csv strategy data to position-level trade history CSV."""
    return convert_strategy_to_trade_history("protected")


def convert_risk_on_to_trade_history():
    """Convert risk_on.csv strategy data to position-level trade history CSV."""
    return convert_strategy_to_trade_history("risk_on")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Convert risk_on.csv to trade history
    risk_on_file = convert_risk_on_to_trade_history()
    if risk_on_file:
        print(f"Risk On portfolio trade history created: {risk_on_file}")

    # Convert protected.csv to trade history
    # protected_file = convert_protected_to_trade_history()
    # if protected_file:
    #     print(f"Protected portfolio trade history created: {protected_file}")

    # Migrate live signals to new schema (if needed)
    # migrated_file = migrate_live_signals_to_trade_history()
    # print(f"Live signals migration complete: {migrated_file}")

    # Export all trade histories to individual CSV files (without consolidation)
    # exported_files = export_all_trade_histories_to_csv()
    # print(f"Exported {len(exported_files)} individual trade history CSV files")
