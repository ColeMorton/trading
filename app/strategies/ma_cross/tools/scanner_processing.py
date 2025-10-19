"""
Scanner Processing Module

This module handles the processing of scanner data, including loading existing results
and processing new tickers for both SMA and EMA configurations.
"""

from collections.abc import Callable
from datetime import datetime
import os

import polars as pl

from app.strategies.ma_cross.tools.signal_generation import process_ma_signals
from app.tools.file_utils import is_file_from_today
from app.utils import get_filename, get_path


def load_existing_results(config: dict, log: Callable) -> tuple[set, list[dict]]:
    """
    Load existing scanner results from today if available.

    Args:
        config (dict): Configuration dictionary
        log (Callable): Logging function

    Returns:
        Tuple[set, List[Dict]]: Tuple containing:
            - Set of already processed tickers
            - List of existing results data
    """
    existing_tickers = set()
    results_data = []

    if not config.get("USE_HOURLY", False):
        csv_path = get_path("csv", "portfolios", config)
        results_filename = get_filename("csv", config)
        full_path = os.path.join(csv_path, results_filename)

        if is_file_from_today(full_path, check_trading_day=True):
            try:
                existing_results = pl.read_csv(full_path)
                existing_tickers = set(existing_results["TICKER"].to_list())
                results_data = existing_results.to_dicts()
                log(
                    f"Found existing results from today with {len(existing_tickers)} tickers"
                )
            except Exception as e:
                log(f"Error reading existing results: {e}", "error")

    return existing_tickers, results_data


def process_ticker(ticker: str, row: dict, config: dict, log: Callable) -> dict:
    """
    Process a single ticker with both SMA and EMA configurations.

    Args:
        ticker (str): Ticker symbol to process
        row (dict): Row data containing window parameters
        config (dict): Configuration dictionary
        log (Callable): Logging function

    Returns:
        Dict: Results dictionary containing SMA and EMA signals
    """
    # Initialize signals
    sma_current = False
    ema_current = False

    # Process SMA signals if windows are provided
    if row.get("SMA_FAST") is not None and row.get("SMA_SLOW") is not None:
        sma_current = process_ma_signals(
            ticker=ticker,
            ma_type="SMA",
            config=config,
            fast_window=row["SMA_FAST"],
            slow_window=row["SMA_SLOW"],
            log=log,
        )

    # Process EMA signals if windows are provided
    if row.get("EMA_FAST") is not None and row.get("EMA_SLOW") is not None:
        ema_current = process_ma_signals(
            ticker=ticker,
            ma_type="EMA",
            config=config,
            fast_window=row["EMA_FAST"],
            slow_window=row["EMA_SLOW"],
            log=log,
        )

    return {
        "TICKER": ticker,
        "SMA": sma_current,
        "EMA": ema_current,
        "SMA_FAST": row.get("SMA_FAST"),
        "SMA_SLOW": row.get("SMA_SLOW"),
        "EMA_FAST": row.get("EMA_FAST"),
        "EMA_SLOW": row.get("EMA_SLOW"),
    }


def export_results(
    results_data: list[dict], original_df: pl.DataFrame, config: dict, log: Callable
) -> None:
    """
    Export scanner results to CSV in a date-specific subdirectory.
    The exported CSV reflects the exact structure of the original portfolio file,
    filtered to only include rows where signals were detected.

    Args:
        results_data (List[Dict]): List of results dictionaries
        original_df (pl.DataFrame): Original scanner DataFrame (used only for column name detection)
        config (dict): Configuration dictionary
        log (Callable): Logging function
    """
    # Log signals
    log("\nSignals detected:")
    signal_configs = []  # Store specific configurations with signals

    for result in results_data:
        ticker = result["TICKER"]

        # Track SMA signals
        if result["SMA"]:
            log(
                f"SMA Signal - {ticker}: Fast={result['SMA_FAST']}, Slow={result['SMA_SLOW']}"
            )
            signal_configs.append(
                {
                    "ticker": ticker,
                    "use_sma": True,
                    "fast_period": result["SMA_FAST"],
                    "slow_period": result["SMA_SLOW"],
                }
            )

        # Track EMA signals
        if result["EMA"]:
            log(
                f"EMA Signal - {ticker}: Fast={result['EMA_FAST']}, Slow={result['EMA_SLOW']}"
            )
            signal_configs.append(
                {
                    "ticker": ticker,
                    "use_sma": False,
                    "fast_period": result["EMA_FAST"],
                    "slow_period": result["EMA_SLOW"],
                }
            )

    if not signal_configs:
        log("No signals detected.")
        return

    # Read the original portfolio file to get all columns
    portfolio_path = os.path.join("./data/raw/strategies", config["PORTFOLIO"])
    try:
        portfolio_df = pl.read_csv(
            portfolio_path,
            infer_schema_length=10000,
            try_parse_dates=True,
            ignore_errors=True,
            truncate_ragged_lines=True,  # Handle rows with different numbers of fields
            schema_overrides={  # Use same schema overrides as in scanner.py
                "Start Value": pl.Float64,
                "End Value": pl.Float64,
                "Return": pl.Float64,
                "Annual Return": pl.Float64,
                "Sharpe Ratio": pl.Float64,
                "Max Drawdown": pl.Float64,
                "Calmar Ratio": pl.Float64,
                "Recovery Factor": pl.Float64,
                "Profit Factor": pl.Float64,
                "Common Sense Ratio": pl.Float64,
                "Win Rate": pl.Float64,
                "Fast Period": pl.Int64,
                "Slow Period": pl.Int64,
            },
        )
        log(f"Read original portfolio file: {portfolio_path}")
    except Exception as e:
        log(f"Error reading portfolio file: {e}", "error")
        return

    # Determine column names in the portfolio DataFrame
    ticker_col = "Ticker" if "Ticker" in portfolio_df.columns else "TICKER"

    # Check if required columns exist
    has_use_sma = any(col in portfolio_df.columns for col in ["Use SMA", "USE_SMA"])
    use_sma_col = (
        "Use SMA"
        if "Use SMA" in portfolio_df.columns
        else "USE_SMA"
        if "USE_SMA" in portfolio_df.columns
        else None
    )

    has_short_window = any(
        col in portfolio_df.columns for col in ["Fast Period", "FAST_PERIOD"]
    )
    short_window_col = (
        "Fast Period"
        if "Fast Period" in portfolio_df.columns
        else "FAST_PERIOD"
        if "FAST_PERIOD" in portfolio_df.columns
        else None
    )

    has_long_window = any(
        col in portfolio_df.columns for col in ["Slow Period", "SLOW_PERIOD"]
    )
    long_window_col = (
        "Slow Period"
        if "Slow Period" in portfolio_df.columns
        else "SLOW_PERIOD"
        if "SLOW_PERIOD" in portfolio_df.columns
        else None
    )

    # Check if we have the new schema or old schema
    has_new_schema = has_short_window and has_long_window
    has_old_schema = any(
        col in portfolio_df.columns
        for col in ["SMA_FAST", "SMA_SLOW", "EMA_FAST", "EMA_SLOW"]
    )

    if not has_new_schema and not has_old_schema:
        log(
            f"Warning: Missing required columns in portfolio file. Found: {portfolio_df.columns}",
            "warning",
        )
        return

    # Create an empty DataFrame to store matching rows
    filtered_rows = []

    # For each signal configuration, find the matching row in the portfolio
    for signal_config in signal_configs:
        # Create filter conditions
        ticker_match = pl.col(ticker_col) == signal_config["ticker"]

        # Handle Use SMA column if it exists
        if has_use_sma and use_sma_col in portfolio_df.columns:
            use_sma_match = (
                pl.col(use_sma_col).cast(pl.Boolean) == signal_config["use_sma"]
            )
        else:
            # If Use SMA column doesn't exist, assume all rows are for EMA
            # (use_sma=False)
            use_sma_match = (
                pl.lit(True) if not signal_config["use_sma"] else pl.lit(False)
            )

        # Build filter conditions based on schema
        if has_new_schema:
            # New schema with Fast Period and Slow Period
            filter_conditions = [ticker_match]

            # Add Use SMA condition if column exists
            if has_use_sma and use_sma_col in portfolio_df.columns:
                filter_conditions.append(use_sma_match)

            # Add window matching conditions if columns exist
            if has_short_window and short_window_col in portfolio_df.columns:
                short_window_match = (
                    pl.col(short_window_col) == signal_config["fast_period"]
                )
                filter_conditions.append(short_window_match)

            if has_long_window and long_window_col in portfolio_df.columns:
                long_window_match = (
                    pl.col(long_window_col) == signal_config["slow_period"]
                )
                filter_conditions.append(long_window_match)
        else:
            # Old schema with separate SMA and EMA columns
            filter_conditions = [ticker_match]

            if signal_config["use_sma"]:
                # For SMA, check SMA_FAST and SMA_SLOW
                if (
                    "SMA_FAST" in portfolio_df.columns
                    and "SMA_SLOW" in portfolio_df.columns
                ):
                    filter_conditions.append(
                        pl.col("SMA_FAST") == signal_config["fast_period"]
                    )
                    filter_conditions.append(
                        pl.col("SMA_SLOW") == signal_config["slow_period"]
                    )
            # For EMA, check EMA_FAST and EMA_SLOW
            elif (
                "EMA_FAST" in portfolio_df.columns
                and "EMA_SLOW" in portfolio_df.columns
            ):
                filter_conditions.append(
                    pl.col("EMA_FAST") == signal_config["fast_period"]
                )
                filter_conditions.append(
                    pl.col("EMA_SLOW") == signal_config["slow_period"]
                )

        # Combine all filter conditions
        combined_filter = filter_conditions[0]
        for condition in filter_conditions[1:]:
            combined_filter = combined_filter & condition

        # Apply all filters
        matching_rows = portfolio_df.filter(combined_filter)

        if len(matching_rows) > 0:
            filtered_rows.append(matching_rows)
        else:
            log(
                f"Warning: No matching row found for {signal_config['ticker']} with "
                f"{'SMA' if signal_config['use_sma'] else 'EMA'} "
                f"{signal_config['fast_period']}/{signal_config['slow_period']}"
            )

    # Combine all matching rows
    if filtered_rows:
        filtered_df = pl.concat(filtered_rows)
    else:
        log("No matching rows found in portfolio file.")
        return

    # Create the output directory with date subdirectory
    current_date = datetime.now().strftime("%Y%m%d")
    csv_path = os.path.join(".", "csv", "ma_cross", "current_signals", current_date)
    os.makedirs(csv_path, exist_ok=True)

    # Get portfolio filename without extension for use in the output filename
    portfolio_name = os.path.splitext(os.path.basename(config["PORTFOLIO"]))[0]

    # Create the output filename using the portfolio name
    output_path = os.path.join(csv_path, f"{portfolio_name}.csv")

    # Remove file if it exists since Polars doesn't have an overwrite parameter
    if os.path.exists(output_path):
        os.remove(output_path)

    # Export the filtered DataFrame
    if len(filtered_df) > 0:
        filtered_df.write_csv(output_path)
        log(f"\nResults exported to {output_path}")
    else:
        log("\nNo rows to export after filtering.")
