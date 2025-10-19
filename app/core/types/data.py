"""Data type definitions."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
import polars as pl

from .common import PositionSide, SignalType


@dataclass
class PriceData:
    """Price data container."""

    ticker: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    interval: str


@dataclass
class OHLCVData:
    """OHLCV data container with DataFrame."""

    ticker: str
    data: pd.DataFrame | pl.DataFrame
    interval: str
    start_date: datetime
    end_date: datetime

    def to_pandas(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        if isinstance(self.data, pl.DataFrame):
            return self.data.to_pandas()
        return self.data

    def to_polars(self) -> pl.DataFrame:
        """Convert to polars DataFrame."""
        if isinstance(self.data, pd.DataFrame):
            return pl.from_pandas(self.data)
        return self.data


@dataclass
class Signal:
    """Trading signal."""

    timestamp: datetime
    ticker: str
    signal_type: SignalType
    price: float
    confidence: float = 1.0
    metadata: dict[str, Any] | None = None


@dataclass
class Trade:
    """Trade record."""

    id: str
    ticker: str
    entry_time: datetime
    exit_time: datetime | None
    entry_price: float
    exit_price: float | None
    quantity: float
    side: PositionSide
    pnl: float | None | None = None
    pnl_percent: float | None | None = None
    commission: float = 0.0
    metadata: dict[str, Any] | None = None
