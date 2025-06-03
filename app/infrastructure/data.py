"""Concrete implementation of data access interface."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl
import yfinance as yf

from app.core.interfaces import (
    ConfigurationInterface,
    DataAccessInterface,
    LoggingInterface,
)


class DataAccessService(DataAccessInterface):
    """Concrete implementation of data access service."""

    def __init__(
        self, config: ConfigurationInterface, logger: Optional[LoggingInterface] = None
    ):
        self._config = config
        self._logger = logger
        self._base_path = Path(config.get("data.base_path", "csv"))
        self._price_data_path = self._base_path / "price_data"

        # Ensure directories exist
        self._price_data_path.mkdir(parents=True, exist_ok=True)

    def get_price_data(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """Get price data for a ticker."""
        # Try to load from cache first
        file_path = self._get_price_file_path(ticker, interval)

        if file_path.exists():
            # Load cached data
            if self._use_polars():
                data = pl.read_csv(file_path)
            else:
                data = pd.read_csv(file_path, index_col=0, parse_dates=True)

            # Filter by date range if specified
            if start_date or end_date:
                data = self._filter_by_date(data, start_date, end_date)

            return data
        else:
            # Download if not cached
            return self.download_data(ticker, start_date, end_date, interval)

    def save_price_data(
        self,
        data: Union[pd.DataFrame, pl.DataFrame],
        ticker: str,
        path: Optional[Path] = None,
    ) -> Path:
        """Save price data to storage."""
        if path is None:
            path = self._get_price_file_path(ticker, "1d")

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, pl.DataFrame):
            data.write_csv(path)
        else:
            data.to_csv(path)

        if self._logger:
            self._logger.get_logger(__name__).info(
                f"Saved price data for {ticker} to {path}"
            )

        return path

    def list_available_tickers(self) -> List[str]:
        """List all available tickers in storage."""
        tickers = set()

        for file_path in self._price_data_path.glob("*_*.csv"):
            # Extract ticker from filename (format: TICKER_INTERVAL.csv)
            ticker = file_path.stem.split("_")[0]
            tickers.add(ticker)

        return sorted(list(tickers))

    def get_last_update_time(self, ticker: str) -> Optional[datetime]:
        """Get last update time for ticker data."""
        file_path = self._get_price_file_path(ticker, "1d")

        if file_path.exists():
            stat = file_path.stat()
            return datetime.fromtimestamp(stat.st_mtime)

        return None

    def download_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
        force: bool = False,
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """Download data from external source."""
        file_path = self._get_price_file_path(ticker, interval)

        # Check if we need to download
        if not force and file_path.exists():
            last_update = self.get_last_update_time(ticker)
            if last_update and (datetime.now() - last_update).days < 1:
                # Use cached data if updated within last day
                return self.get_price_data(ticker, start_date, end_date, interval)

        # Download from yfinance
        if self._logger:
            self._logger.get_logger(__name__).info(
                f"Downloading data for {ticker} from {start_date} to {end_date}"
            )

        try:
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False,
            )

            if data.empty:
                raise ValueError(f"No data found for ticker {ticker}")

            # Save to cache
            self.save_price_data(data, ticker, file_path)

            # Convert to polars if configured
            if self._use_polars():
                data = pl.from_pandas(data)

            return data

        except Exception as e:
            if self._logger:
                self._logger.get_logger(__name__).error(
                    f"Error downloading data for {ticker}: {e}"
                )
            raise

    def validate_data(self, data: Union[pd.DataFrame, pl.DataFrame]) -> bool:
        """Validate data integrity."""
        if isinstance(data, pl.DataFrame):
            # Polars validation
            if data.is_empty():
                return False

            required_columns = ["Open", "High", "Low", "Close", "Volume"]
            return all(col in data.columns for col in required_columns)
        else:
            # Pandas validation
            if data.empty:
                return False

            required_columns = ["Open", "High", "Low", "Close", "Volume"]
            return all(col in data.columns for col in required_columns)

    def get_data_info(self, ticker: str) -> Dict[str, Any]:
        """Get metadata about ticker data."""
        info = {
            "ticker": ticker,
            "available_intervals": [],
            "last_update": None,
            "data_range": None,
            "file_size": None,
        }

        # Check all available intervals
        for interval in ["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1mo"]:
            file_path = self._get_price_file_path(ticker, interval)
            if file_path.exists():
                info["available_intervals"].append(interval)

                if interval == "1d":
                    # Get more detailed info for daily data
                    info["last_update"] = self.get_last_update_time(ticker)
                    info["file_size"] = file_path.stat().st_size

                    # Get date range
                    try:
                        data = self.get_price_data(ticker, interval=interval)
                        if isinstance(data, pl.DataFrame):
                            info["data_range"] = {
                                "start": data.select(pl.col("Date").min())[0, 0],
                                "end": data.select(pl.col("Date").max())[0, 0],
                                "rows": len(data),
                            }
                        else:
                            info["data_range"] = {
                                "start": data.index.min(),
                                "end": data.index.max(),
                                "rows": len(data),
                            }
                    except Exception:
                        pass

        return info

    def _get_price_file_path(self, ticker: str, interval: str) -> Path:
        """Get file path for price data."""
        return self._price_data_path / f"{ticker}_{interval.upper()}.csv"

    def _use_polars(self) -> bool:
        """Check if we should use polars."""
        return self._config.get("data.use_polars", False)

    def _filter_by_date(
        self,
        data: Union[pd.DataFrame, pl.DataFrame],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """Filter data by date range."""
        if isinstance(data, pl.DataFrame):
            if start_date:
                data = data.filter(pl.col("Date") >= start_date)
            if end_date:
                data = data.filter(pl.col("Date") <= end_date)
        else:
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]

        return data
