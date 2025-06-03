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
    def get_price_data(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """Get price data for a ticker."""
        pass

    @abstractmethod
    def save_price_data(
        self,
        data: Union[pd.DataFrame, pl.DataFrame],
        ticker: str,
        path: Optional[Path] = None,
    ) -> Path:
        """Save price data to storage."""
        pass

    @abstractmethod
    def list_available_tickers(self) -> List[str]:
        """List all available tickers in storage."""
        pass

    @abstractmethod
    def get_last_update_time(self, ticker: str) -> Optional[datetime]:
        """Get last update time for ticker data."""
        pass

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
        pass

    @abstractmethod
    def validate_data(self, data: Union[pd.DataFrame, pl.DataFrame]) -> bool:
        """Validate data integrity."""
        pass

    @abstractmethod
    def get_data_info(self, ticker: str) -> Dict[str, Any]:
        """Get metadata about ticker data."""
        pass
