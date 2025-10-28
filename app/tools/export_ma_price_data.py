"""
SMA/EMA Price Data Export Script

This script exports moving average data as synthetic price data for given ticker and period.
The output format matches the standard price data format: Date,Open,High,Low,Close,Volume
where the Close price is the moving average value.

Usage:
    python app/tools/export_ma_price_data.py TICKER PERIOD [--ma-type {SMA,EMA}]

Example:
    python app/tools/export_ma_price_data.py AAPL 20
    python app/tools/export_ma_price_data.py BTC-USD 50 --ma-type EMA
"""

import argparse
from collections.abc import Callable
import os
import sys

import polars as pl


# Add the project root to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from app.tools.calculate_mas import calculate_mas
from app.tools.data_types import DataConfig
from app.tools.get_data import get_data


def create_logger() -> Callable[[str, str], None]:
    """Create a simple logging function."""

    def log(message: str, level: str = "info") -> None:
        prefix = {
            "debug": "[DEBUG]",
            "info": "[INFO]",
            "warning": "[WARNING]",
            "error": "[ERROR]",
        }.get(level, "[INFO]")
        print(f"{prefix} {message}")

    return log


def create_synthetic_ohlc(data: pl.DataFrame, ma_column: str) -> pl.DataFrame:
    """
    Create synthetic OHLC data from moving average values.

    Args:
        data: DataFrame with moving average column
        ma_column: Name of the moving average column

    Returns:
        DataFrame with synthetic OHLC format
    """
    # Filter out null MA values
    filtered_data = data.filter(pl.col(ma_column).is_not_null())

    if len(filtered_data) == 0:
        msg = f"No valid data found for {ma_column}"
        raise ValueError(msg)

    # Create synthetic OHLC where:
    # - Close = Moving Average value
    # - Open = Previous Close (lag by 1)
    # - High = Max(Open, Close)
    # - Low = Min(Open, Close)
    # - Volume = 0 (synthetic data marker)

    return (
        filtered_data.with_columns(
            [
                # Close = Moving Average
                pl.col(ma_column).alias("Close"),
                # Open = Previous Close (use first MA value for first row)
                pl.col(ma_column)
                .shift(1)
                .fill_null(pl.col(ma_column).first())
                .alias("Open"),
                # Volume = 0 for synthetic data
                pl.lit(0.0).alias("Volume"),
            ],
        )
        .with_columns(
            [
                # High = Max(Open, Close)
                pl.max_horizontal(["Open", "Close"]).alias("High"),
                # Low = Min(Open, Close)
                pl.min_horizontal(["Open", "Close"]).alias("Low"),
            ],
        )
        .select(["Date", "Open", "High", "Low", "Close", "Volume"])
    )


def export_ma_price_data(ticker: str, period: int, ma_type: str = "SMA") -> None:
    """
    Export moving average data as synthetic price data.

    Args:
        ticker: Ticker symbol (e.g., 'AAPL', 'BTC-USD')
        period: Moving average period
        ma_type: Type of moving average ('SMA' or 'EMA')
    """
    log = create_logger()

    log(f"Starting MA price data export for {ticker} with {period}-period {ma_type}")

    # Create configuration for data loading
    config: DataConfig = {
        "BASE_DIR": os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ),
        "REFRESH": False,  # Use existing data if available
        "STRATEGY_TYPE": ma_type,
    }

    try:
        # Load price data
        log(f"Loading price data for {ticker}")
        price_data = get_data(ticker, config, log)

        if price_data is None or len(price_data) == 0:
            msg = f"No price data found for {ticker}"
            raise ValueError(msg)

        log(f"Loaded {len(price_data)} price data points")

        # Calculate moving average
        log(f"Calculating {ma_type} with period {period}")
        use_sma = ma_type.upper() == "SMA"

        # For single MA calculation, use the same period for both fast and slow
        # We'll only use the "slow" MA which corresponds to our desired period
        ma_data = calculate_mas(price_data, period, period, use_sma, log)

        # Create synthetic OHLC data from the moving average
        log("Creating synthetic OHLC data from moving average")
        synthetic_data = create_synthetic_ohlc(ma_data, "MA_SLOW")

        log(f"Generated {len(synthetic_data)} synthetic OHLC data points")

        # Create output directory
        output_dir = os.path.join(
            config["BASE_DIR"],
            "data",
            "raw",
            "ma_cross",
            "prices",
        )
        os.makedirs(output_dir, exist_ok=True)

        # Create output filename
        output_filename = f"{ticker}_{period}.csv"
        output_path = os.path.join(output_dir, output_filename)

        # Export to CSV
        log(f"Exporting to {output_path}")
        synthetic_data.write_csv(output_path)

        log(f"Successfully exported {ma_type} price data to {output_path}")
        log(
            f"Data range: {synthetic_data['Date'].min()} to {synthetic_data['Date'].max()}",
        )

    except Exception as e:
        log(f"Error exporting MA price data: {e}", "error")
        raise


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Export moving average data as synthetic price data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("ticker", help="Ticker symbol (e.g., AAPL, BTC-USD)")
    parser.add_argument("period", type=int, help="Moving average period")
    parser.add_argument(
        "--ma-type",
        choices=["SMA", "EMA"],
        default="SMA",
        help="Type of moving average (default: SMA)",
    )

    args = parser.parse_args()

    try:
        export_ma_price_data(args.ticker, args.period, args.ma_type)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
