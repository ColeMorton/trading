"""Portfolio management interface definition."""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
import polars as pl


class Portfolio(ABC):
    """Abstract base for portfolio representation."""

    @property
    @abstractmethod
    def ticker(self) -> str:
        """Portfolio ticker symbol."""

    @property
    @abstractmethod
    def strategy(self) -> str:
        """Strategy type."""

    @property
    @abstractmethod
    def metrics(self) -> Dict[str, float]:
        """Performance metrics."""

    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Creation timestamp."""


class PortfolioFilter(ABC):
    """Abstract base for portfolio filters."""


class PortfolioManagerInterface(ABC):
    """Interface for portfolio management operations."""

    @abstractmethod
    def load_portfolio(self, path: Path) -> Portfolio:
        """Load a portfolio from file."""

    @abstractmethod
    def save_portfolio(self, portfolio: Portfolio, path: Path) -> None:
        """Save a portfolio to file."""

    @abstractmethod
    def list_portfolios(
        self, directory: Path, pattern: Optional[str] | None = None
    ) -> List[Portfolio]:
        """List all portfolios in a directory."""

    @abstractmethod
    def filter_portfolios(
        self, portfolios: List[Portfolio], filters: List[PortfolioFilter]
    ) -> List[Portfolio]:
        """Filter portfolios based on criteria."""

    @abstractmethod
    def aggregate_portfolios(
        self, portfolios: List[Portfolio]
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """Aggregate multiple portfolios into a summary."""

    @abstractmethod
    def get_best_portfolios(
        self, portfolios: List[Portfolio], metric: str = "sharpe_ratio", top_n: int = 10
    ) -> List[Portfolio]:
        """Get best performing portfolios by metric."""

    @abstractmethod
    def validate_portfolio(self, portfolio: Portfolio) -> bool:
        """Validate portfolio data integrity."""
