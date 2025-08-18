"""
Trade History Export Module

This module provides trade history extraction and export functionality for VectorBT portfolios.
It exports comprehensive trade data including trades, orders, positions, and metadata in a single JSON file.

IMPORTANT: Trade history export is only available through app/concurrency/review.py to prevent
generating thousands of files from parameter sweep strategies like MA Cross analysis.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import vectorbt as vbt

from app.tools.export_csv import ExportConfig


def extract_trade_history(portfolio: "vbt.Portfolio") -> pd.DataFrame:
    """
    Extract comprehensive trade history from VectorBT portfolio.

    Args:
        portfolio: VectorBT Portfolio object

    Returns:
        DataFrame containing trade history with entry/exit dates and performance metrics
    """
    try:
        # Get trades data
        trades = portfolio.trades
        trades_df = trades.records_readable

        if len(trades_df) == 0:
            return pd.DataFrame()

        # Extract basic trade information
        trade_history = trades_df[
            [
                "Entry Timestamp",
                "Exit Timestamp",
                "Avg Entry Price",
                "Avg Exit Price",
                "Size",
                "PnL",
                "Return",
                "Direction",
                "Status",
            ]
        ].copy()

        # Add enriched metrics
        trade_history = _enrich_trade_data(trade_history, portfolio)

        return trade_history

    except Exception as e:
        print(f"Warning: Could not extract trade history: {e}")
        return pd.DataFrame()


def extract_orders_history(portfolio: "vbt.Portfolio") -> pd.DataFrame:
    """
    Extract order history from VectorBT portfolio.

    Args:
        portfolio: VectorBT Portfolio object

    Returns:
        DataFrame containing order history with timestamps
    """
    try:
        # Get orders data
        orders = portfolio.orders
        orders_df = orders.records_readable

        if len(orders_df) == 0:
            return pd.DataFrame()

        # Extract order information
        order_history = orders_df[
            ["Order Id", "Column", "Timestamp", "Size", "Price", "Fees", "Side"]
        ].copy()

        return order_history

    except Exception as e:
        print(f"Warning: Could not extract order history: {e}")
        return pd.DataFrame()


def extract_positions_history(portfolio: "vbt.Portfolio") -> pd.DataFrame:
    """
    Extract position history from VectorBT portfolio.

    Args:
        portfolio: VectorBT Portfolio object

    Returns:
        DataFrame containing position history with entry/exit dates
    """
    try:
        # Get positions data
        positions = portfolio.positions
        positions_df = positions.records_readable

        if len(positions_df) == 0:
            return pd.DataFrame()

        # Extract position information
        position_history = positions_df[
            [
                "Position Id",
                "Column",
                "Size",
                "Entry Timestamp",
                "Avg Entry Price",
                "Entry Fees",
                "Exit Timestamp",
                "Avg Exit Price",
                "Exit Fees",
                "PnL",
                "Return",
                "Direction",
                "Status",
            ]
        ].copy()

        # Add enriched metrics for positions
        position_history = _enrich_position_data(position_history)

        return position_history

    except Exception as e:
        print(f"Warning: Could not extract position history: {e}")
        return pd.DataFrame()


def _enrich_trade_data(
    trade_df: pd.DataFrame, portfolio: "vbt.Portfolio"
) -> pd.DataFrame:
    """
    Add enriched metrics to trade data.

    Args:
        trade_df: Base trade DataFrame
        portfolio: VectorBT Portfolio object for additional metrics

    Returns:
        Enhanced DataFrame with additional metrics
    """
    if len(trade_df) == 0:
        return trade_df

    enriched_df = trade_df.copy()

    # Calculate trade duration
    if (
        "Entry Timestamp" in enriched_df.columns
        and "Exit Timestamp" in enriched_df.columns
    ):
        # VectorBT returns integer indices that need to be mapped to actual dates
        try:
            # Get the original data's datetime index
            portfolio_data = portfolio._data_pd

            # Check if we have a proper datetime index in the portfolio data
            if hasattr(portfolio_data, "columns") and "Date" in portfolio_data.columns:
                # Use the Date column to map indices to actual dates
                date_column = portfolio_data["Date"]

                # Map integer indices to actual dates
                entry_indices = enriched_df["Entry Timestamp"].astype(int)
                exit_indices = enriched_df["Exit Timestamp"].astype(int)

                # Convert indices to actual dates using the Date column
                enriched_df["Entry Timestamp"] = date_column.iloc[entry_indices].values
                enriched_df["Exit Timestamp"] = date_column.iloc[exit_indices].values

                # Ensure they are datetime objects
                enriched_df["Entry Timestamp"] = pd.to_datetime(
                    enriched_df["Entry Timestamp"]
                )
                enriched_df["Exit Timestamp"] = pd.to_datetime(
                    enriched_df["Exit Timestamp"]
                )

            elif hasattr(
                portfolio_data, "index"
            ) and pd.api.types.is_datetime64_any_dtype(portfolio_data.index):
                # Use the datetime index if available
                date_index = portfolio_data.index

                entry_indices = enriched_df["Entry Timestamp"].astype(int)
                exit_indices = enriched_df["Exit Timestamp"].astype(int)

                enriched_df["Entry Timestamp"] = date_index[entry_indices]
                enriched_df["Exit Timestamp"] = date_index[exit_indices]

            else:
                print(f"Warning: Could not find datetime reference in portfolio data")
                print(
                    f"Portfolio data columns: {list(portfolio_data.columns) if hasattr(portfolio_data, 'columns') else 'No columns'}"
                )
                print(
                    f"Portfolio data index type: {type(portfolio_data.index[0]) if len(portfolio_data) > 0 else 'Empty'}"
                )
                return enriched_df

        except Exception as e:
            print(f"Warning: Could not convert timestamps: {e}")
            return enriched_df

        # Initialize Duration and Duration_Days columns
        enriched_df["Duration"] = pd.NaT
        enriched_df["Duration_Days"] = float("nan")

        # Calculate duration for closed trades only
        closed_mask = enriched_df["Status"] == "Closed"
        if closed_mask.any():
            duration_timedelta = (
                enriched_df.loc[closed_mask, "Exit Timestamp"]
                - enriched_df.loc[closed_mask, "Entry Timestamp"]
            )
            enriched_df.loc[closed_mask, "Duration"] = duration_timedelta

            # Convert to days as float (includes fractional days)
            enriched_df.loc[
                closed_mask, "Duration_Days"
            ] = duration_timedelta.dt.total_seconds() / (24 * 60 * 60)

        # For open trades, set Exit Timestamp and Duration_Days to None for JSON compatibility
        open_mask = enriched_df["Status"] == "Open"
        if open_mask.any():
            enriched_df.loc[open_mask, "Exit Timestamp"] = None
            enriched_df.loc[open_mask, "Duration"] = None
            enriched_df.loc[open_mask, "Duration_Days"] = None

        # Add entry month for analysis (only for valid timestamps)
        valid_entry_mask = pd.notnull(enriched_df["Entry Timestamp"])
        if valid_entry_mask.any():
            enriched_df.loc[valid_entry_mask, "Entry_Month"] = enriched_df.loc[
                valid_entry_mask, "Entry Timestamp"
            ].dt.to_period("M")
            enriched_df.loc[valid_entry_mask, "Entry_Year"] = enriched_df.loc[
                valid_entry_mask, "Entry Timestamp"
            ].dt.year
            enriched_df.loc[valid_entry_mask, "Entry_Quarter"] = enriched_df.loc[
                valid_entry_mask, "Entry Timestamp"
            ].dt.quarter

    # Add trade performance categorization
    enriched_df["Trade_Type"] = enriched_df["Return"].apply(
        _categorize_trade_performance
    )

    # Add cumulative metrics
    enriched_df["Cumulative_PnL"] = enriched_df["PnL"].cumsum()
    enriched_df["Trade_Number"] = range(1, len(enriched_df) + 1)

    # Add rolling statistics (5-trade window)
    window_size = min(5, len(enriched_df))
    enriched_df["Rolling_Avg_Return"] = (
        enriched_df["Return"].rolling(window=window_size, min_periods=1).mean()
    )
    enriched_df["Rolling_Win_Rate"] = (
        (enriched_df["Return"] > 0).rolling(window=window_size, min_periods=1).mean()
    )

    return enriched_df


def _enrich_position_data(position_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add enriched metrics to position data.

    Args:
        position_df: Base position DataFrame

    Returns:
        Enhanced DataFrame with additional metrics
    """
    if len(position_df) == 0:
        return position_df

    enriched_df = position_df.copy()

    # Calculate position duration
    if (
        "Entry Timestamp" in enriched_df.columns
        and "Exit Timestamp" in enriched_df.columns
    ):
        # Convert timestamps properly - handle various formats VectorBT might return
        try:
            enriched_df["Entry Timestamp"] = pd.to_datetime(
                enriched_df["Entry Timestamp"], errors="coerce"
            )
            enriched_df["Exit Timestamp"] = pd.to_datetime(
                enriched_df["Exit Timestamp"], errors="coerce"
            )
        except Exception as e:
            print(f"Warning: Could not convert position timestamps: {e}")

        # Initialize Duration and Duration_Days columns
        enriched_df["Duration"] = pd.NaT
        enriched_df["Duration_Days"] = float("nan")

        # Calculate duration for closed positions only
        closed_mask = enriched_df["Status"] == "Closed"
        if closed_mask.any():
            duration_timedelta = (
                enriched_df.loc[closed_mask, "Exit Timestamp"]
                - enriched_df.loc[closed_mask, "Entry Timestamp"]
            )
            enriched_df.loc[closed_mask, "Duration"] = duration_timedelta

            # Convert to days as float (includes fractional days)
            enriched_df.loc[
                closed_mask, "Duration_Days"
            ] = duration_timedelta.dt.total_seconds() / (24 * 60 * 60)

        # For open positions, set Exit Timestamp and Duration_Days to None for JSON compatibility
        open_mask = enriched_df["Status"] == "Open"
        if open_mask.any():
            enriched_df.loc[open_mask, "Exit Timestamp"] = None
            enriched_df.loc[open_mask, "Duration"] = None
            enriched_df.loc[open_mask, "Duration_Days"] = None

    # Add position performance categorization
    enriched_df["Position_Type"] = enriched_df["Return"].apply(
        _categorize_trade_performance
    )

    return enriched_df


def _categorize_trade_performance(return_value: float) -> str:
    """
    Categorize trade performance based on return value.

    Args:
        return_value: Trade return as decimal

    Returns:
        Performance category string
    """
    if pd.isna(return_value):
        return "Unknown"
    elif return_value > 0.05:  # > 5%
        return "Big Winner"
    elif return_value > 0.01:  # 1-5%
        return "Winner"
    elif return_value > -0.01:  # -1% to 1%
        return "Breakeven"
    elif return_value > -0.05:  # -5% to -1%
        return "Loser"
    else:  # < -5%
        return "Big Loser"


def generate_trade_filename(config: Dict[str, Any], extension: str = "json") -> str:
    """
    Generate standardized filename for trade history exports following existing conventions.

    Args:
        config: Strategy configuration dictionary
        extension: File extension ("json" or "csv")

    Returns:
        Filename following pattern: {TICKER}_{TIMEFRAME}_{STRATEGY}_{PARAMS}.{extension}
    """
    components = []

    # Add ticker prefix
    ticker = config.get("TICKER", "")
    if isinstance(ticker, list):
        ticker = ticker[0] if ticker else ""
    if ticker:
        # Handle synthetic tickers (replace / with _)
        ticker = ticker.replace("/", "_")
        components.append(ticker)

    # Add timeframe
    timeframe = "H" if config.get("USE_HOURLY", False) else "D"
    components.append(timeframe)

    # Add strategy type
    strategy_type = config.get("STRATEGY_TYPE", "")
    if not strategy_type:
        # Fall back to SMA/EMA detection
        strategy_type = "SMA" if config.get("USE_SMA", False) else "EMA"

    # Clean up strategy type if it has enum prefix
    if isinstance(strategy_type, str) and strategy_type.startswith("StrategyTypeEnum."):
        strategy_type = strategy_type.replace("StrategyTypeEnum.", "")

    components.append(strategy_type)

    # Add strategy parameters
    params = _extract_strategy_parameters(config, strategy_type)
    components.extend(params)

    # Add optional suffixes
    if config.get("DIRECTION") == "Short":
        components.append("SHORT")

    # Add stop loss if present
    if config.get("STOP_LOSS") is not None:
        stop_loss = config["STOP_LOSS"]
        if isinstance(stop_loss, float):
            components.append(f"SL_{stop_loss:.4f}")

    # Join components and add extension (no redundant trade_history suffix)
    filename = "_".join(str(c) for c in components if c) + f".{extension}"

    return filename


def _extract_strategy_parameters(
    config: Dict[str, Any], strategy_type: str
) -> List[str]:
    """
    Extract strategy parameters for filename generation.

    Args:
        config: Strategy configuration
        strategy_type: Strategy type (SMA, EMA, MACD, etc.)

    Returns:
        List of parameter strings
    """
    params = []

    if strategy_type.upper() in ["SMA", "EMA"]:
        # MA Cross parameters
        if "fast_period" in config and "slow_period" in config:
            params.extend([str(config["fast_period"]), str(config["slow_period"])])
        elif "FAST_PERIOD" in config and "SLOW_PERIOD" in config:
            params.extend([str(config["FAST_PERIOD"]), str(config["SLOW_PERIOD"])])

    elif strategy_type.upper() == "MACD":
        # MACD parameters
        if (
            "fast_window" in config
            and "slow_window" in config
            and "signal_period" in config
        ):
            params.extend(
                [
                    str(config["fast_window"]),
                    str(config["slow_window"]),
                    str(config["signal_period"]),
                ]
            )
        elif (
            "FAST_WINDOW" in config
            and "SLOW_WINDOW" in config
            and "SIGNAL_PERIOD" in config
        ):
            params.extend(
                [
                    str(config["FAST_WINDOW"]),
                    str(config["SLOW_WINDOW"]),
                    str(config["SIGNAL_PERIOD"]),
                ]
            )

    elif strategy_type.upper() == "RSI":
        # RSI parameters
        if "RSI_WINDOW" in config and "RSI_THRESHOLD" in config:
            params.extend([str(config["RSI_WINDOW"]), str(config["RSI_THRESHOLD"])])

    return params


def create_comprehensive_trade_history(
    portfolio: "vbt.Portfolio", config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create comprehensive trade history data structure with all components.

    Args:
        portfolio: VectorBT Portfolio object
        config: Strategy configuration dictionary

    Returns:
        Dictionary containing all trade history data and metadata
    """
    # Extract all data components
    trades_df = extract_trade_history(portfolio)
    orders_df = extract_orders_history(portfolio)
    positions_df = extract_positions_history(portfolio)

    # Generate metadata
    metadata = {
        "export_timestamp": datetime.now().isoformat(),
        "strategy_config": {
            "ticker": config.get("TICKER", ""),
            "timeframe": "H" if config.get("USE_HOURLY", False) else "D",
            "strategy_type": config.get("STRATEGY_TYPE", ""),
            "direction": config.get("DIRECTION", "Long"),
            "parameters": _extract_all_strategy_parameters(config),
        },
        "portfolio_summary": {
            "total_return": float(portfolio.total_return())
            if hasattr(portfolio.total_return(), "iloc")
            else portfolio.total_return(),
            "total_trades": int(portfolio.trades.count())
            if hasattr(portfolio.trades.count(), "iloc")
            else portfolio.trades.count(),
            "win_rate": float(portfolio.trades.win_rate())
            if hasattr(portfolio.trades.win_rate(), "iloc")
            else portfolio.trades.win_rate(),
            "sharpe_ratio": float(portfolio.sharpe_ratio())
            if hasattr(portfolio.sharpe_ratio(), "iloc")
            else portfolio.sharpe_ratio(),
            "max_drawdown": float(portfolio.max_drawdown())
            if hasattr(portfolio.max_drawdown(), "iloc")
            else portfolio.max_drawdown(),
        },
    }

    # Handle pandas timestamp serialization
    def convert_timestamps(df):
        df_copy = df.copy()
        for col in df_copy.columns:
            if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                # Handle None values properly - convert to None instead of NaN
                df_copy[col] = df_copy[col].apply(
                    lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(x) else None
                )
            elif col in ["Duration"]:
                # Convert Duration, handling None values
                df_copy[col] = df_copy[col].apply(
                    lambda x: str(x) if x is not None else None
                )
            elif col in ["Entry_Month"]:
                # Convert Entry_Month, handling None values
                df_copy[col] = df_copy[col].apply(
                    lambda x: str(x) if pd.notnull(x) else None
                )

        # Handle specific columns that might have NaN values for JSON compatibility
        for col in ["Duration_Days", "Entry_Year", "Entry_Quarter"]:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].apply(lambda x: None if pd.isna(x) else x)

        return df_copy

    # Helper function to clean NaN values from records after pandas to_dict conversion
    def clean_nan_values(records):
        import math

        cleaned_records = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                # Convert various forms of NaN to None for JSON compatibility
                if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
                    cleaned_record[key] = None
                else:
                    cleaned_record[key] = value
            cleaned_records.append(cleaned_record)
        return cleaned_records

    # Create comprehensive data structure
    trades_records = (
        convert_timestamps(trades_df).to_dict("records") if len(trades_df) > 0 else []
    )
    orders_records = (
        convert_timestamps(orders_df).to_dict("records") if len(orders_df) > 0 else []
    )
    positions_records = (
        convert_timestamps(positions_df).to_dict("records")
        if len(positions_df) > 0
        else []
    )

    trade_history = {
        "metadata": metadata,
        "trades": clean_nan_values(trades_records),
        "orders": clean_nan_values(orders_records),
        "positions": clean_nan_values(positions_records),
        "analytics": analyze_trade_performance(trades_df) if len(trades_df) > 0 else {},
    }

    return trade_history


def _extract_all_strategy_parameters(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract all strategy parameters for metadata."""
    params = {}

    # Common parameters
    for key in [
        "fast_period",
        "slow_period",
        "FAST_PERIOD",
        "SLOW_PERIOD",
        "fast_window",
        "slow_window",
        "signal_period",
        "FAST_WINDOW",
        "SLOW_WINDOW",
        "SIGNAL_PERIOD",
        "RSI_WINDOW",
        "RSI_THRESHOLD",
        "STOP_LOSS",
    ]:
        if key in config and config[key] is not None:
            params[key.lower()] = config[key]

    return params


def _is_trade_history_current(filepath: str) -> bool:
    """
    Check if trade history file exists and was created today.

    Args:
        filepath: Path to the trade history file

    Returns:
        True if file exists and was created today, False otherwise
    """
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        return False

    try:
        # Get file modification time
        file_mtime = os.path.getmtime(filepath)
        file_date = datetime.fromtimestamp(file_mtime).date()
        today = datetime.now().date()

        return file_date == today
    except (OSError, ValueError):
        return False


def export_trade_history(
    portfolio: "vbt.Portfolio",
    config: Dict[str, Any],
    export_type: str = "json",
    base_dir: Optional[str] = None,
    force_refresh: bool = False,
) -> bool:
    """
    Export comprehensive trade history to single JSON file.

    Args:
        portfolio: VectorBT Portfolio object
        config: Strategy configuration dictionary
        export_type: Export format ("json" for comprehensive, "csv" for legacy)
        base_dir: Base directory for exports (defaults to config BASE_DIR)
        force_refresh: Force regeneration even if current file exists

    Returns:
        True if export was successful, False otherwise
    """
    try:
        if base_dir is None:
            base_dir = config.get("BASE_DIR", ".")

        # Create trade_history directory
        trade_history_dir = os.path.join(base_dir, "json", "trade_history")
        os.makedirs(trade_history_dir, exist_ok=True)

        if export_type == "json":
            filename = generate_trade_filename(config, "json")
            filepath = os.path.join(trade_history_dir, filename)

            # Check if current trade history already exists (unless forced refresh)
            if not force_refresh and _is_trade_history_current(filepath):
                print(f"Trade history file already current: {filepath}")
                print("  - Skipping regeneration (file created today)")
                return True

            # Export comprehensive JSON
            trade_history_data = create_comprehensive_trade_history(portfolio, config)

            with open(filepath, "w") as f:
                json.dump(trade_history_data, f, indent=2, default=str)

            trade_count = len(trade_history_data["trades"])
            order_count = len(trade_history_data["orders"])
            position_count = len(trade_history_data["positions"])

            print(f"Exported comprehensive trade history to {filepath}")
            print(
                f"  - {trade_count} trades, {order_count} orders, {position_count} positions"
            )

            return trade_count > 0

        else:
            # Legacy CSV export (kept for backward compatibility)
            return _export_legacy_csv(portfolio, config, trade_history_dir)

    except Exception as e:
        print(f"Error exporting trade history: {e}")
        return False


def _export_legacy_csv(
    portfolio: "vbt.Portfolio", config: Dict[str, Any], trade_history_dir: str
) -> bool:
    """Export individual CSV files (legacy format)."""
    success = True

    # Export trades
    trades_df = extract_trade_history(portfolio)
    if len(trades_df) > 0:
        base_filename = generate_trade_filename(config, "csv")
        filename = base_filename.replace(".csv", "_trades.csv")
        filepath = os.path.join(trade_history_dir, filename)
        trades_df.to_csv(filepath, index=False)
        print(f"Exported {len(trades_df)} trades to {filepath}")
    else:
        print("No trades found to export")
        success = False

    # Export orders
    orders_df = extract_orders_history(portfolio)
    if len(orders_df) > 0:
        base_filename = generate_trade_filename(config, "csv")
        filename = base_filename.replace(".csv", "_orders.csv")
        filepath = os.path.join(trade_history_dir, filename)
        orders_df.to_csv(filepath, index=False)
        print(f"Exported {len(orders_df)} orders to {filepath}")

    # Export positions
    positions_df = extract_positions_history(portfolio)
    if len(positions_df) > 0:
        base_filename = generate_trade_filename(config, "csv")
        filename = base_filename.replace(".csv", "_positions.csv")
        filepath = os.path.join(trade_history_dir, filename)
        positions_df.to_csv(filepath, index=False)
        print(f"Exported {len(positions_df)} positions to {filepath}")

    return success


def analyze_trade_performance(trade_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate trade performance analytics.

    Args:
        trade_df: Trade history DataFrame

    Returns:
        Dictionary containing performance analytics
    """
    if len(trade_df) == 0:
        return {}

    # Filter closed trades for analysis
    closed_trades = trade_df[trade_df["Status"] == "Closed"]

    if len(closed_trades) == 0:
        return {"total_trades": len(trade_df), "closed_trades": 0}

    analytics = {
        "total_trades": len(trade_df),
        "closed_trades": len(closed_trades),
        "open_trades": len(trade_df) - len(closed_trades),
        "win_rate": (closed_trades["Return"] > 0).mean() * 100,
        "avg_return": closed_trades["Return"].mean() * 100,
        "avg_winner": closed_trades[closed_trades["Return"] > 0]["Return"].mean() * 100,
        "avg_loser": closed_trades[closed_trades["Return"] < 0]["Return"].mean() * 100,
        "best_trade": closed_trades["Return"].max() * 100,
        "worst_trade": closed_trades["Return"].min() * 100,
        "total_pnl": closed_trades["PnL"].sum(),
        "avg_trade_duration": closed_trades["Duration_Days"].dropna().mean()
        if "Duration_Days" in closed_trades.columns
        and len(closed_trades["Duration_Days"].dropna()) > 0
        else None,
        "profit_factor": None,
    }

    # Calculate profit factor
    winners = closed_trades[closed_trades["PnL"] > 0]["PnL"].sum()
    losers = abs(closed_trades[closed_trades["PnL"] < 0]["PnL"].sum())
    if losers > 0:
        analytics["profit_factor"] = winners / losers

    # Trade type distribution
    if "Trade_Type" in closed_trades.columns:
        analytics["trade_type_distribution"] = (
            closed_trades["Trade_Type"].value_counts().to_dict()
        )

    return analytics
