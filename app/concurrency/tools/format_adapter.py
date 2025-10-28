"""Portfolio format adapters for concurrency analysis.

This module provides functionality for converting between different portfolio formats
and a standardized internal representation.
"""

import csv
import json
from pathlib import Path
from typing import Any, cast

from app.concurrency.config import (
    CsvStrategyRow,
    FileFormatError,
    JsonMacdStrategy,
    JsonMaStrategy,
    detect_portfolio_format,
)


class UnifiedStrategy(dict[str, Any]):
    """Unified internal representation of a trading strategy."""


def convert_csv_strategy(row: CsvStrategyRow) -> UnifiedStrategy:
    """Convert CSV strategy row to unified format.

    Args:
        row (CsvStrategyRow): CSV strategy row data

    Returns:
        UnifiedStrategy: Strategy in unified format
    """
    strategy: UnifiedStrategy = {
        "ticker": row["Ticker"],
        "timeframe": "Daily",  # CSV format assumes daily
        "type": "SMA" if row["Use_SMA"] else "EMA",
        "direction": "Long",  # CSV format assumes long
        "fast_period": row["Fast_Period"],
        "slow_period": row["Slow_Period"],
    }

    # Add signal period for MACD if present
    if "Signal_Period" in row and row["Signal_Period"] > 0:
        strategy["type"] = "MACD"
        strategy["signal_period"] = row["Signal_Period"]

    # Add optional parameters if present
    optional_fields = {
        "Stop Loss": "stop_loss",
        "RSI Window": "rsi_window",
        "RSI Threshold": "rsi_threshold",
    }

    for csv_field, unified_field in optional_fields.items():
        if row.get(csv_field):
            strategy[unified_field] = row[csv_field]

    return strategy


def convert_ma_strategy(strategy: JsonMaStrategy) -> UnifiedStrategy:
    """Convert JSON MA strategy to unified format.

    Args:
        strategy (JsonMaStrategy): JSON MA strategy data

    Returns:
        UnifiedStrategy: Strategy in unified format
    """
    unified: UnifiedStrategy = {
        "ticker": strategy["ticker"],
        "timeframe": strategy["timeframe"],
        "type": strategy["type"],
        "direction": strategy["direction"],
        "fast_period": strategy["fast_period"],
        "slow_period": strategy["slow_period"],
    }

    # Add optional parameters if present
    optional_fields = ["stop_loss", "rsi_period", "rsi_threshold"]
    for field in optional_fields:
        if field in strategy:
            unified[field] = strategy[field]

    return unified


def convert_macd_strategy(strategy: JsonMacdStrategy) -> UnifiedStrategy:
    """Convert JSON MACD strategy to unified format.

    Args:
        strategy (JsonMacdStrategy): JSON MACD strategy data

    Returns:
        UnifiedStrategy: Strategy in unified format
    """
    unified: UnifiedStrategy = {
        "ticker": strategy["ticker"],
        "timeframe": strategy["timeframe"],
        "type": strategy["type"],
        "direction": strategy["direction"],
        "fast_period": strategy["fast_period"],
        "slow_period": strategy["slow_period"],
        "signal_period": strategy["signal_period"],
    }

    # Add optional parameters if present
    optional_fields = ["stop_loss", "rsi_period", "rsi_threshold"]
    for field in optional_fields:
        if field in strategy:
            unified[field] = strategy[field]

    return unified


def load_portfolio(file_path: str) -> list[UnifiedStrategy]:
    """Load and convert a portfolio file to unified format.

    Args:
        file_path (str): Path to portfolio file

    Returns:
        List[UnifiedStrategy]: List of strategies in unified format

    Raises:
        FileFormatError: If file format is invalid or unsupported
    """
    format_info = detect_portfolio_format(file_path)

    if format_info.extension == ".csv":
        with open(file_path, newline="") as f:
            reader = csv.DictReader(f)
            return [convert_csv_strategy(cast(CsvStrategyRow, row)) for row in reader]

    elif format_info.extension == ".json":
        with open(file_path) as f:
            data = json.load(f)

            if format_info.content_type == "application/json+macd":
                return [
                    convert_macd_strategy(cast(JsonMacdStrategy, strategy))
                    for strategy in data
                ]
            # application/json+ma
            return [
                convert_ma_strategy(cast(JsonMaStrategy, strategy)) for strategy in data
            ]

    msg = f"Unsupported format: {format_info.content_type}"
    raise FileFormatError(msg)


def save_portfolio(strategies: list[UnifiedStrategy], file_path: str) -> None:
    """Save strategies in unified format to a portfolio file.

    Args:
        strategies (List[UnifiedStrategy]): List of strategies to save
        file_path (str): Path to save the portfolio file

    Raises:
        FileFormatError: If file format is unsupported
    """
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".json":
        # Save as JSON MA/MACD format
        with open(file_path, "w") as f:
            json.dump(strategies, f, indent=4)

    elif extension == ".csv":
        # Convert to CSV format
        fieldnames = [
            "Ticker",
            "Use SMA",
            "Fast Period",
            "Slow Period",
            "Signal Period",
            "Stop Loss",
            "RSI Window",
            "RSI Threshold",
        ]

        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for strategy in strategies:
                row = {
                    "Ticker": strategy["ticker"],
                    "Use SMA": strategy["type"] == "SMA",
                    "Fast Period": strategy["fast_period"],
                    "Slow Period": strategy["slow_period"],
                    "Signal Period": strategy.get("signal_period", 0),
                    "Stop Loss": strategy.get("stop_loss", ""),
                    "RSI Window": strategy.get("rsi_window", ""),
                    "RSI Threshold": strategy.get("rsi_threshold", ""),
                }
                writer.writerow(row)

    else:
        msg = f"Unsupported file extension: {extension}"
        raise FileFormatError(msg)
