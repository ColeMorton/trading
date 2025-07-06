"""
Equity Data Export Module

This module handles the export of equity curve data to CSV files with proper
directory structure and file naming conventions according to the specification.
"""

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from app.tools.equity_data_extractor import EquityData
from app.tools.exceptions import ExportError, TradingSystemError
from app.tools.project_utils import get_project_root


def generate_equity_filename(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: Optional[int] = None,
) -> str:
    """
    Generate equity data filename according to specification.

    Args:
        ticker: Trading symbol (e.g., "AAPL", "BTC-USD")
        strategy_type: Strategy type ("SMA", "EMA", "MACD")
        short_window: Short period parameter
        long_window: Long period parameter
        signal_window: Signal period (optional, defaults to 0)

    Returns:
        Filename string in format:
        - MACD: {Ticker}_{Strategy_Type}_{Short}_{Long}_{Signal}.csv
        - SMA/EMA: {Ticker}_{Strategy_Type}_{Short}_{Long}.csv
    """
    # Clean ticker for filename (replace invalid characters)
    clean_ticker = ticker.replace("/", "-").replace("\\", "-").replace(":", "-")

    if strategy_type == "MACD":
        # MACD strategies require signal window
        signal = signal_window if signal_window is not None else 0
        filename = (
            f"{clean_ticker}_{strategy_type}_{short_window}_{long_window}_{signal}.csv"
        )
    else:
        # SMA/EMA strategies don't use signal window
        filename = f"{clean_ticker}_{strategy_type}_{short_window}_{long_window}.csv"

    return filename


def get_equity_file_path(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: Optional[int] = None,
) -> Path:
    """
    Get the full file path for equity data export.

    Args:
        ticker: Trading symbol (e.g., "AAPL", "BTC-USD")
        strategy_type: Strategy type ("SMA", "EMA", "MACD")
        short_window: Short period parameter
        long_window: Long period parameter
        signal_window: Signal period (optional, defaults to 0)

    Returns:
        Path object for the equity data file
    """
    export_dir = get_equity_export_directory(strategy_type)
    filename = generate_equity_filename(
        ticker, strategy_type, short_window, long_window, signal_window
    )
    return export_dir / filename


def equity_file_exists(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: Optional[int] = None,
) -> bool:
    """
    Check if equity data file already exists for the given strategy.

    Args:
        ticker: Trading symbol (e.g., "AAPL", "BTC-USD")
        strategy_type: Strategy type ("SMA", "EMA", "MACD")
        short_window: Short period parameter
        long_window: Long period parameter
        signal_window: Signal period (optional, defaults to 0)

    Returns:
        True if equity file exists, False otherwise
    """
    try:
        file_path = get_equity_file_path(
            ticker, strategy_type, short_window, long_window, signal_window
        )
        return file_path.exists() and file_path.is_file()
    except Exception:
        return False


def get_equity_export_directory(strategy_type: str) -> Path:
    """
    Get the export directory path for the given strategy type.

    Args:
        strategy_type: Strategy type ("SMA", "EMA", "MACD")

    Returns:
        Path object for the export directory

    Raises:
        TradingSystemError: If strategy type is invalid
    """
    project_root = Path(get_project_root())

    if strategy_type in ["SMA", "EMA"]:
        # SMA and EMA strategies export to ma_cross/equity_data/
        export_dir = project_root / "csv" / "ma_cross" / "equity_data"
    elif strategy_type == "MACD":
        # MACD strategies export to macd_cross/equity_data/
        export_dir = project_root / "csv" / "macd_cross" / "equity_data"
    else:
        raise TradingSystemError(
            f"Invalid strategy type for equity export: {strategy_type}"
        )

    return export_dir


def ensure_export_directory_exists(
    export_dir: Path, log: Callable[[str, str], None]
) -> None:
    """
    Ensure the export directory exists, creating it if necessary.

    Args:
        export_dir: Path to the export directory
        log: Logging function

    Raises:
        ExportError: If directory cannot be created
    """
    try:
        export_dir.mkdir(parents=True, exist_ok=True)
        log(f"Ensured export directory exists: {export_dir}", "debug")
    except Exception as e:
        error_msg = f"Failed to create export directory {export_dir}: {str(e)}"
        log(error_msg, "error")
        raise ExportError(error_msg) from e


def export_equity_data_to_csv(
    equity_data: EquityData,
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: Optional[int],
    log: Callable[[str, str], None],
    overwrite: bool = True,
) -> bool:
    """
    Export equity data to CSV file with proper naming and directory structure.

    Args:
        equity_data: EquityData object containing equity metrics
        ticker: Trading symbol
        strategy_type: Strategy type ("SMA", "EMA", "MACD")
        short_window: Short period parameter
        long_window: Long period parameter
        signal_window: Signal period parameter (optional)
        log: Logging function
        overwrite: Whether to overwrite existing files (default: True)

    Returns:
        True if export successful, False otherwise

    Raises:
        ExportError: If export fails
    """
    try:
        # Generate filename and directory
        filename = generate_equity_filename(
            ticker, strategy_type, short_window, long_window, signal_window
        )
        export_dir = get_equity_export_directory(strategy_type)
        file_path = export_dir / filename

        # Ensure directory exists
        ensure_export_directory_exists(export_dir, log)

        # Check if file exists and handle overwrite policy
        if file_path.exists() and not overwrite:
            log(f"File already exists and overwrite disabled: {file_path}", "warning")
            return False

        # Convert equity data to DataFrame
        df = equity_data.to_dataframe()

        # Validate DataFrame has data
        if df.empty:
            log(f"No equity data to export for {ticker} {strategy_type}", "warning")
            return False

        # Export to CSV
        df.to_csv(file_path, index=False)

        log(f"Successfully exported equity data: {file_path}", "info")
        log(f"Exported {len(df)} data points for {ticker} {strategy_type}", "info")

        return True

    except Exception as e:
        error_msg = (
            f"Failed to export equity data for {ticker} {strategy_type}: {str(e)}"
        )
        log(error_msg, "error")
        raise ExportError(error_msg) from e


def export_equity_data_batch(
    portfolios: List[Dict[str, Any]],
    log: Callable[[str, str], None],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Export equity data for a batch of portfolios.

    Args:
        portfolios: List of portfolio dictionaries containing strategy results
        log: Logging function
        config: Optional configuration dictionary

    Returns:
        Dictionary with export results including counts and errors
    """
    results = {
        "total_portfolios": len(portfolios),
        "exported_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "errors": [],
    }

    # Check if equity data export is enabled
    equity_config = config.get("EQUITY_DATA", {}) if config else {}
    if not equity_config.get("EXPORT", False):
        log("Equity data export is disabled, skipping batch export", "info")
        results["skipped_count"] = len(portfolios)
        return results

    log(f"Starting equity data batch export for {len(portfolios)} portfolios", "info")

    for portfolio in portfolios:
        try:
            # Check if portfolio has equity data
            equity_data = portfolio.get("_equity_data")
            if equity_data is None:
                results["skipped_count"] += 1
                continue

            # Extract strategy parameters
            ticker = portfolio.get("Ticker")
            strategy_type = portfolio.get("Strategy Type")
            short_window = portfolio.get("Short Window")
            long_window = portfolio.get("Long Window")
            signal_window = portfolio.get("Signal Window")

            # Validate required parameters
            if not all(
                [
                    ticker,
                    strategy_type,
                    short_window is not None,
                    long_window is not None,
                ]
            ):
                log(
                    f"Missing required parameters for equity export: {portfolio}",
                    "warning",
                )
                results["skipped_count"] += 1
                continue

            # Export equity data
            success = export_equity_data_to_csv(
                equity_data=equity_data,
                ticker=ticker,
                strategy_type=strategy_type,
                short_window=int(short_window),
                long_window=int(long_window),
                signal_window=int(signal_window) if signal_window is not None else None,
                log=log,
                overwrite=True,
            )

            if success:
                results["exported_count"] += 1
            else:
                results["skipped_count"] += 1

        except Exception as e:
            error_msg = f"Error exporting equity data for portfolio {portfolio.get('Ticker', 'Unknown')}: {str(e)}"
            log(error_msg, "error")
            results["errors"].append(error_msg)
            results["error_count"] += 1

    # Log summary
    log(
        f"Equity data batch export completed: {results['exported_count']} exported, "
        f"{results['skipped_count']} skipped, {results['error_count']} errors",
        "info",
    )

    return results


def validate_equity_export_requirements(
    ticker: str,
    strategy_type: str,
    short_window: Any,
    long_window: Any,
    signal_window: Any = None,
) -> bool:
    """
    Validate that all required parameters for equity export are present and valid.

    Args:
        ticker: Trading symbol
        strategy_type: Strategy type
        short_window: Short window parameter
        long_window: Long window parameter
        signal_window: Signal window parameter (optional)

    Returns:
        True if all requirements are met, False otherwise
    """
    # Check ticker
    if not ticker or not isinstance(ticker, str) or len(ticker.strip()) == 0:
        return False

    # Check strategy type
    if strategy_type not in ["SMA", "EMA", "MACD"]:
        return False

    # Check window parameters
    try:
        short_val = int(short_window) if short_window is not None else None
        long_val = int(long_window) if long_window is not None else None

        if short_val is None or long_val is None:
            return False

        if short_val <= 0 or long_val <= 0:
            return False

        # For MACD, signal window is required
        if strategy_type == "MACD":
            if signal_window is None:
                return False
            signal_val = int(signal_window)
            if signal_val <= 0:
                return False

    except (ValueError, TypeError):
        return False

    return True


def get_equity_export_file_path(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: Optional[int] = None,
) -> Path:
    """
    Get the full file path for equity data export.

    Args:
        ticker: Trading symbol
        strategy_type: Strategy type
        short_window: Short window parameter
        long_window: Long window parameter
        signal_window: Signal window parameter (optional)

    Returns:
        Path object for the export file
    """
    filename = generate_equity_filename(
        ticker, strategy_type, short_window, long_window, signal_window
    )
    export_dir = get_equity_export_directory(strategy_type)
    return export_dir / filename


def cleanup_old_equity_files(
    strategy_type: str, max_age_days: int, log: Callable[[str, str], None]
) -> int:
    """
    Clean up old equity data files beyond specified age.

    Args:
        strategy_type: Strategy type to clean up
        max_age_days: Maximum age in days for files to keep
        log: Logging function

    Returns:
        Number of files deleted
    """
    try:
        import time
        from datetime import datetime, timedelta

        export_dir = get_equity_export_directory(strategy_type)

        if not export_dir.exists():
            return 0

        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        deleted_count = 0

        for file_path in export_dir.glob("*.csv"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    log(f"Deleted old equity file: {file_path}", "debug")
                except Exception as e:
                    log(
                        f"Failed to delete old equity file {file_path}: {str(e)}",
                        "warning",
                    )

        if deleted_count > 0:
            log(
                f"Cleaned up {deleted_count} old equity files for {strategy_type}",
                "info",
            )

        return deleted_count

    except Exception as e:
        log(f"Error during equity file cleanup for {strategy_type}: {str(e)}", "error")
        return 0
