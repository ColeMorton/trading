"""
Portfolio Export Module

This module handles the export of portfolio data to CSV files using the
centralized export functionality.
"""

from typing import List, Dict, Tuple, Callable, Optional
import polars as pl
from app.tools.export_csv import export_csv, ExportConfig

class PortfolioExportError(Exception):
    """Custom exception for portfolio export errors."""
    pass

VALID_EXPORT_TYPES = {
    'portfolios',
    'portfolios_scanner',
    'portfolios_filtered',
    'portfolios_best'
}

def export_portfolios(
    portfolios: List[Dict],
    config: ExportConfig,
    export_type: str,
    csv_filename: Optional[str] = None,
    log: Optional[Callable] = None
) -> Tuple[pl.DataFrame, bool]:
    """Convert portfolio dictionaries to Polars DataFrame and export to CSV.

    Args:
        portfolios (List[Dict]): List of portfolio dictionaries to export
        config (ExportConfig): Export configuration dictionary
        export_type (str): Type of export (must be one of: portfolios, portfolios_scanner, portfolios_filtered, portfolios_best)
        csv_filename (Optional[str]): Optional custom filename for the CSV
        log (Optional[Callable]): Optional logging function

    Returns:
        Tuple[pl.DataFrame, bool]: (DataFrame of exported data, success status)

    Raises:
        PortfolioExportError: If export fails or invalid export type provided
        ValueError: If portfolios list is empty
    """
    if not portfolios:
        if log:
            log("No portfolios to export", "warning")
        raise ValueError("Cannot export empty portfolio list")

    if export_type not in VALID_EXPORT_TYPES:
        error_msg = f"Invalid export type: {export_type}. Must be one of: {', '.join(VALID_EXPORT_TYPES)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg)

    if log:
        log(f"Exporting {len(portfolios)} portfolios as {export_type}...", "info")

    try:
        # Convert portfolios to DataFrame
        df = pl.DataFrame(portfolios)
        
        # Apply consistent column ordering for portfolio exports
        if export_type in ["portfolios", "portfolios_best"]:
            # Define column order with strategy-specific columns first
            ordered_columns = [
                "Ticker",
                "Range Length",
                "Candle Lookback",
                "Total Trades",
                "Total Return [%]",
                "Benchmark Return [%]",
                "Max Gross Exposure [%]",
                "Total Fees Paid",
                "Max Drawdown [%]",
                "Max Drawdown Duration",
                "Total Closed Trades",
                "Total Open Trades",
                "Open Trade PnL",
                "Win Rate [%]",
                "Best Trade [%]",
                "Worst Trade [%]",
                "Avg Winning Trade [%]",
                "Avg Losing Trade [%]",
                "Avg Winning Trade Duration",
                "Avg Losing Trade Duration",
                "Profit Factor",
                "Expectancy",
                "Sharpe Ratio",
                "Calmar Ratio",
                "Omega Ratio",
                "Sortino Ratio",
                "Score",
                "Trades Per Day",
                "Trades per Month",
                "Signals per Month",
                "Expectancy per Month"
            ]
            
            # Add any remaining columns in their original order
            remaining_columns = [col for col in df.columns if col not in ordered_columns]
            ordered_columns.extend(remaining_columns)
            
            # Reorder columns
            df = df.select(ordered_columns)
            
            # Get ticker from config
            ticker = config["TICKER"]
            if isinstance(ticker, list):
                if len(ticker) == 1:
                    ticker = ticker[0]
                else:
                    # For multiple tickers, each portfolio should already have its ticker
                    if "Ticker" not in df.columns:
                        raise PortfolioExportError("Missing Ticker column for multiple ticker export")
            
            # Add or update Ticker column if it's a single ticker
            if isinstance(ticker, str):
                if "Ticker" in df.columns:
                    df = df.drop("Ticker")
                df = df.with_columns(pl.lit(ticker).alias("Ticker"))
                # Move Ticker to first column
                cols = df.columns
                df = df.select(["Ticker"] + [col for col in cols if col != "Ticker"])
        
        # Use empty feature1 for 'portfolios' and 'portfolios_scanner' export types
        # to export directly to csv/portfolios/ instead of csv/range/portfolios/ or csv/range/portfolios_scanner/
        feature1 = "" if export_type in ["portfolios", "portfolios_scanner"] else "range"
        
        return export_csv(
            data=df,
            feature1=feature1,
            config=config,
            feature2=export_type,
            filename=csv_filename,
            log=log
        )
    except Exception as e:
        error_msg = f"Failed to export portfolios: {str(e)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg) from e