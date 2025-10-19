"""Portfolio management interface definition."""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

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
    def metrics(self) -> dict[str, float]:
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
        self, directory: Path, pattern: str | None | None = None
    ) -> list[Portfolio]:
        """List all portfolios in a directory."""

    @abstractmethod
    def filter_portfolios(
        self, portfolios: list[Portfolio], filters: list[PortfolioFilter]
    ) -> list[Portfolio]:
        """Filter portfolios based on criteria."""

    @abstractmethod
    def aggregate_portfolios(
        self, portfolios: list[Portfolio]
    ) -> pd.DataFrame | pl.DataFrame:
        """Aggregate multiple portfolios into a summary."""

    @abstractmethod
    def get_best_portfolios(
        self, portfolios: list[Portfolio], metric: str = "sharpe_ratio", top_n: int = 10
    ) -> list[Portfolio]:
        """Get best performing portfolios by metric."""

    @abstractmethod
    def validate_portfolio(self, portfolio: Portfolio) -> bool:
        """Validate portfolio data integrity."""
