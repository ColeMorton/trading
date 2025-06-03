"""
Portfolio Processing Module

This module handles the processing of portfolio data for single tickers,
including loading existing data and analyzing parameter sensitivity.
"""

import os
from typing import Callable, Optional

import numpy as np
import polars as pl

from app.mean_reversion.config_types import validate_config
from app.mean_reversion.tools.sensitivity_analysis import analyze_parameter_combinations
from app.tools.file_utils import is_file_from_today
from app.tools.get_data import get_data


def process_single_ticker(
    ticker: str, config: dict, log: Callable
) -> Optional[pl.DataFrame]:
    """
    Process portfolio analysis for a single ticker.

    Args:
        ticker (str): Ticker symbol to analyze
        config (dict): Configuration dictionary
        log (callable): Logging function for recording events and errors

    Returns:
        Optional[pl.DataFrame]: Portfolio analysis results or None if processing fails
    """
    try:
        # Validate configuration
        validate_config(config)

        config_copy = config.copy()
        config_copy["TICKER"] = ticker

        if config.get("REFRESH", True) == False:
            # Construct file path using BASE_DIR
            file_name = f'{ticker}{"_H" if config.get("USE_HOURLY", False) else "_D"}'
            directory = os.path.join(
                config["BASE_DIR"], "csv", "mean_reversion", "portfolios"
            )

            # Ensure directory exists
            os.makedirs(directory, exist_ok=True)

            file_path = os.path.join(directory, f"{file_name}.csv")

            log(f"Checking existing data from {file_path}.")

            # Check if file exists and was created today
            if os.path.exists(file_path) and is_file_from_today(file_path):
                log(f"Loading existing data from {file_path}.")
                return pl.read_csv(file_path)

        # Generate parameter ranges
        start_pct = config.get("CHANGE_PCT_START", 2.00)
        end_pct = config.get("CHANGE_PCT_END", 15.00)
        step_pct = config.get("CHANGE_PCT_STEP", 0.01)

        # Create parameter arrays
        change_pcts = np.arange(start_pct, end_pct + step_pct, step_pct)

        log("Getting data...")
        data = get_data(ticker, config_copy, log)
        if data is None:
            log(f"Failed to get data for {ticker}", "error")
            return None

        log("Beginning analysis...")
        portfolios = analyze_parameter_combinations(
            data=data, change_pcts=change_pcts, config=config_copy, log=log
        )

        if not portfolios:
            log(f"No valid portfolios generated for {ticker}", "warning")
            return None

        return pl.DataFrame(portfolios)

    except Exception as e:
        log(f"Failed to process ticker {ticker}: {str(e)}", "error")
        return None
