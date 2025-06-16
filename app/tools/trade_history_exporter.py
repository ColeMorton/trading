"""
Trade History Export Module

This module provides trade history extraction and export functionality for VectorBT portfolios.
It extracts trade-level data including entry/exit dates, durations, and performance metrics.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import vectorbt as vbt

from app.tools.export_csv import ExportConfig


def extract_trade_history(portfolio: vbt.Portfolio) -> pd.DataFrame:
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


def extract_orders_history(portfolio: vbt.Portfolio) -> pd.DataFrame:
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


def extract_positions_history(portfolio: vbt.Portfolio) -> pd.DataFrame:
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
    trade_df: pd.DataFrame, portfolio: vbt.Portfolio
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
        enriched_df["Entry Timestamp"] = pd.to_datetime(enriched_df["Entry Timestamp"])
        enriched_df["Exit Timestamp"] = pd.to_datetime(enriched_df["Exit Timestamp"])

        # Calculate duration for closed trades only
        closed_mask = enriched_df["Status"] == "Closed"
        enriched_df.loc[closed_mask, "Duration"] = (
            enriched_df.loc[closed_mask, "Exit Timestamp"]
            - enriched_df.loc[closed_mask, "Entry Timestamp"]
        )
        enriched_df.loc[closed_mask, "Duration_Days"] = enriched_df.loc[
            closed_mask, "Duration"
        ].dt.days

        # Add entry month for analysis
        enriched_df["Entry_Month"] = enriched_df["Entry Timestamp"].dt.to_period("M")
        enriched_df["Entry_Year"] = enriched_df["Entry Timestamp"].dt.year
        enriched_df["Entry_Quarter"] = enriched_df["Entry Timestamp"].dt.quarter

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
        enriched_df["Entry Timestamp"] = pd.to_datetime(enriched_df["Entry Timestamp"])
        enriched_df["Exit Timestamp"] = pd.to_datetime(enriched_df["Exit Timestamp"])

        # Calculate duration for closed positions only
        closed_mask = enriched_df["Status"] == "Closed"
        enriched_df.loc[closed_mask, "Duration"] = (
            enriched_df.loc[closed_mask, "Exit Timestamp"]
            - enriched_df.loc[closed_mask, "Entry Timestamp"]
        )
        enriched_df.loc[closed_mask, "Duration_Days"] = enriched_df.loc[
            closed_mask, "Duration"
        ].dt.days

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


def generate_trade_filename(config: Dict[str, Any], data_type: str = "trades") -> str:
    """
    Generate standardized filename for trade history exports following existing conventions.

    Args:
        config: Strategy configuration dictionary
        data_type: Type of data ("trades", "orders", "positions")

    Returns:
        Filename following pattern: {TICKER}_{TIMEFRAME}_{STRATEGY}_{PARAMS}_{data_type}.csv
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

    # Add data type suffix
    components.append(data_type)

    # Join components and add extension
    filename = "_".join(str(c) for c in components if c) + ".csv"

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
        if "short_window" in config and "long_window" in config:
            params.extend([str(config["short_window"]), str(config["long_window"])])
        elif "SHORT_WINDOW" in config and "LONG_WINDOW" in config:
            params.extend([str(config["SHORT_WINDOW"]), str(config["LONG_WINDOW"])])

    elif strategy_type.upper() == "MACD":
        # MACD parameters
        if (
            "fast_window" in config
            and "slow_window" in config
            and "signal_window" in config
        ):
            params.extend(
                [
                    str(config["fast_window"]),
                    str(config["slow_window"]),
                    str(config["signal_window"]),
                ]
            )
        elif (
            "FAST_WINDOW" in config
            and "SLOW_WINDOW" in config
            and "SIGNAL_WINDOW" in config
        ):
            params.extend(
                [
                    str(config["FAST_WINDOW"]),
                    str(config["SLOW_WINDOW"]),
                    str(config["SIGNAL_WINDOW"]),
                ]
            )

    elif strategy_type.upper() == "RSI":
        # RSI parameters
        if "RSI_WINDOW" in config and "RSI_THRESHOLD" in config:
            params.extend([str(config["RSI_WINDOW"]), str(config["RSI_THRESHOLD"])])

    return params


def export_trade_history(
    portfolio: vbt.Portfolio,
    config: Dict[str, Any],
    export_type: str = "trades",
    base_dir: Optional[str] = None,
) -> bool:
    """
    Export trade history to CSV file.

    Args:
        portfolio: VectorBT Portfolio object
        config: Strategy configuration dictionary
        export_type: Type of export ("trades", "orders", "positions", "all")
        base_dir: Base directory for exports (defaults to config BASE_DIR)

    Returns:
        True if export was successful, False otherwise
    """
    try:
        if base_dir is None:
            base_dir = config.get("BASE_DIR", ".")

        # Create trade_history directory
        trade_history_dir = os.path.join(base_dir, "csv", "trade_history")
        os.makedirs(trade_history_dir, exist_ok=True)

        success = True

        if export_type in ["trades", "all"]:
            # Export trades
            trades_df = extract_trade_history(portfolio)
            if len(trades_df) > 0:
                filename = generate_trade_filename(config, "trades")
                filepath = os.path.join(trade_history_dir, filename)
                trades_df.to_csv(filepath, index=False)
                print(f"Exported {len(trades_df)} trades to {filepath}")
            else:
                print("No trades found to export")
                success = False

        if export_type in ["orders", "all"]:
            # Export orders
            orders_df = extract_orders_history(portfolio)
            if len(orders_df) > 0:
                filename = generate_trade_filename(config, "orders")
                filepath = os.path.join(trade_history_dir, filename)
                orders_df.to_csv(filepath, index=False)
                print(f"Exported {len(orders_df)} orders to {filepath}")

        if export_type in ["positions", "all"]:
            # Export positions
            positions_df = extract_positions_history(portfolio)
            if len(positions_df) > 0:
                filename = generate_trade_filename(config, "positions")
                filepath = os.path.join(trade_history_dir, filename)
                positions_df.to_csv(filepath, index=False)
                print(f"Exported {len(positions_df)} positions to {filepath}")

        return success

    except Exception as e:
        print(f"Error exporting trade history: {e}")
        return False


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
        "avg_trade_duration": closed_trades["Duration_Days"].mean()
        if "Duration_Days" in closed_trades.columns
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
