"""Data access interface definition."""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl


class DataAccessInterface(ABC):
    """Interface for data access operations."""

    @abstractmethod
    def get_prices(
        self,
        ticker: str,
        start_date: Optional[datetime] | None = None,
        end_date: Optional[datetime] | None = None,
        interval: str = "1d",
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """Get price data for a ticker."""

    @abstractmethod
    def save_prices(
        self,
        data: Union[pd.DataFrame, pl.DataFrame],
        ticker: str,
        path: Optional[Path] | None = None,
    ) -> Path:
        """Save price data to storage."""

    @abstractmethod
    def list_available_tickers(self) -> List[str]:
        """List all available tickers in storage."""

    @abstractmethod
    def get_last_update_time(self, ticker: str) -> Optional[datetime]:
        """Get last update time for ticker data."""

    @abstractmethod
    def download_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
        force: bool = False,
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """Download data from external source."""

    @abstractmethod
    def validate_data(self, data: Union[pd.DataFrame, pl.DataFrame]) -> bool:
        """Validate data integrity."""

    @abstractmethod
    def get_data_info(self, ticker: str) -> Dict[str, Any]:
        """Get metadata about ticker data."""
