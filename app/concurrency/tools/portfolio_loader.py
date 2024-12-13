"""Portfolio configuration loading utilities.

This module provides functionality for loading and validating portfolio configurations
from CSV files. It handles parsing of required and optional strategy parameters with
appropriate type conversion.
"""

from pathlib import Path
from typing import List, Callable, Dict
import polars as pl
import pandas as pd  # For isna() function
from app.concurrency.tools.types import StrategyConfig

def load_portfolio_from_csv(csv_path: Path, log: Callable[[str, str], None], config: Dict) -> List[StrategyConfig]:
    """Load portfolio configuration from CSV file.

    Args:
        csv_path (Path): Path to the CSV file containing strategy configurations
        log (Callable[[str, str], None]): Logging function for status updates
        config (Dict): Configuration dictionary containing BASE_DIR and REFRESH settings

    Returns:
        List[StrategyConfig]: List of strategy configurations

    Raises:
        FileNotFoundError: If CSV file does not exist
        ValueError: If CSV file is empty or malformed
    """
    log(f"Loading portfolio configuration from {csv_path}", "info")
    
    if not csv_path.exists():
        log(f"Portfolio file not found: {csv_path}", "error")
        raise FileNotFoundError(f"Portfolio file not found: {csv_path}")
        
    # Read CSV file using Polars
    df = pl.read_csv(csv_path)
    log(f"Successfully read CSV file with {len(df)} strategies", "info")
    
    # Convert DataFrame rows to StrategyConfig objects
    portfolio = []
    for row in df.iter_rows(named=True):
        ticker = row["TICKER"]
        log(f"Processing strategy configuration for {ticker}", "info")
        
        config_entry: StrategyConfig = {
            "TICKER": ticker,
            "SHORT_WINDOW": int(row["SHORT_WINDOW"]),
            "LONG_WINDOW": int(row["LONG_WINDOW"]),
            "BASE_DIR": config["BASE_DIR"],
            "REFRESH": config["REFRESH"]
        }
        
        # Add optional fields if they exist and have non-null values
        optional_fields = [
            "SIGNAL_PERIOD", "USE_SMA", "USE_HOURLY",
            "USE_RSI", "RSI_PERIOD", "RSI_THRESHOLD", "STOP_LOSS"
        ]
        
        for field in optional_fields:
            if field in row and row[field] != "." and not pd.isna(row[field]):
                # Convert to appropriate type
                if field in ["SHORT_WINDOW", "LONG_WINDOW", "SIGNAL_PERIOD", "RSI_PERIOD"]:
                    config_entry[field] = int(row[field])
                elif field in ["STOP_LOSS", "RSI_THRESHOLD"]:
                    config_entry[field] = float(row[field])
                elif field in ["USE_SMA", "USE_HOURLY", "USE_RSI"]:
                    config_entry[field] = str(row[field]).lower() == "true"
                else:
                    config_entry[field] = row[field]
        
        # Log complete strategy configuration
        strategy_details = [
            f"TICKER: {config_entry['TICKER']}",
            f"SHORT_WINDOW: {config_entry['SHORT_WINDOW']}",
            f"LONG_WINDOW: {config_entry['LONG_WINDOW']}",
            f"BASE_DIR: {config_entry['BASE_DIR']}",
            f"REFRESH: {config_entry['REFRESH']}"
        ]
        
        # Add optional fields to log if they exist
        for field in optional_fields:
            if field in config_entry:
                strategy_details.append(f"{field}: {config_entry[field]}")
        
        log(f"Strategy Configuration:\n" + "\n".join(strategy_details), "info")
        portfolio.append(config_entry)
    
    log(f"Successfully loaded {len(portfolio)} strategy configurations", "info")
    return portfolio
