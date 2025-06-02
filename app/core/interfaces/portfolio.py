"""Portfolio management interface definition."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
import pandas as pd
import polars as pl


class Portfolio(ABC):
    """Abstract base for portfolio representation."""
    
    @property
    @abstractmethod
    def ticker(self) -> str:
        """Portfolio ticker symbol."""
        pass
    
    @property
    @abstractmethod
    def strategy(self) -> str:
        """Strategy type."""
        pass
    
    @property
    @abstractmethod
    def metrics(self) -> Dict[str, float]:
        """Performance metrics."""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Creation timestamp."""
        pass


class PortfolioFilter(ABC):
    """Abstract base for portfolio filters."""
    pass


class PortfolioManagerInterface(ABC):
    """Interface for portfolio management operations."""
    
    @abstractmethod
    def load_portfolio(self, path: Path) -> Portfolio:
        """Load a portfolio from file."""
        pass
    
    @abstractmethod
    def save_portfolio(self, portfolio: Portfolio, path: Path) -> None:
        """Save a portfolio to file."""
        pass
    
    @abstractmethod
    def list_portfolios(
        self,
        directory: Path,
        pattern: Optional[str] = None
    ) -> List[Portfolio]:
        """List all portfolios in a directory."""
        pass
    
    @abstractmethod
    def filter_portfolios(
        self,
        portfolios: List[Portfolio],
        filters: List[PortfolioFilter]
    ) -> List[Portfolio]:
        """Filter portfolios based on criteria."""
        pass
    
    @abstractmethod
    def aggregate_portfolios(
        self,
        portfolios: List[Portfolio]
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """Aggregate multiple portfolios into a summary."""
        pass
    
    @abstractmethod
    def get_best_portfolios(
        self,
        portfolios: List[Portfolio],
        metric: str = "sharpe_ratio",
        top_n: int = 10
    ) -> List[Portfolio]:
        """Get best performing portfolios by metric."""
        pass
    
    @abstractmethod
    def validate_portfolio(self, portfolio: Portfolio) -> bool:
        """Validate portfolio data integrity."""
        pass