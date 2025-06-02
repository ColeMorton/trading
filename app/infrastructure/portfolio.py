"""Concrete implementation of portfolio management interface."""

import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
import pandas as pd
import polars as pl

from app.core.interfaces import (
    PortfolioManagerInterface,
    DataAccessInterface,
    LoggingInterface,
    Portfolio,
    PortfolioFilter
)
from app.core.types import PortfolioMetrics


class ConcretePortfolio(Portfolio):
    """Concrete implementation of portfolio."""
    
    def __init__(
        self,
        ticker: str,
        strategy: str,
        metrics: Dict[str, float],
        created_at: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._ticker = ticker
        self._strategy = strategy
        self._metrics = metrics
        self._created_at = created_at
        self._metadata = metadata or {}
    
    @property
    def ticker(self) -> str:
        return self._ticker
    
    @property
    def strategy(self) -> str:
        return self._strategy
    
    @property
    def metrics(self) -> Dict[str, float]:
        return self._metrics
    
    @property
    def created_at(self) -> datetime:
        return self._created_at


class MetricFilter(PortfolioFilter):
    """Filter portfolios by metric thresholds."""
    
    def __init__(self, metric_name: str, min_value: Optional[float] = None, max_value: Optional[float] = None):
        self.metric_name = metric_name
        self.min_value = min_value
        self.max_value = max_value
    
    def apply(self, portfolio: Portfolio) -> bool:
        """Apply filter to portfolio."""
        value = portfolio.metrics.get(self.metric_name)
        if value is None:
            return False
        
        if self.min_value is not None and value < self.min_value:
            return False
        
        if self.max_value is not None and value > self.max_value:
            return False
        
        return True


class PortfolioManager(PortfolioManagerInterface):
    """Concrete implementation of portfolio manager."""
    
    def __init__(
        self,
        data_access: DataAccessInterface,
        logger: Optional[LoggingInterface] = None
    ):
        self._data_access = data_access
        self._logger = logger
    
    def load_portfolio(self, path: Path) -> Portfolio:
        """Load a portfolio from file."""
        if not path.exists():
            raise FileNotFoundError(f"Portfolio file not found: {path}")
        
        if path.suffix == '.json':
            with open(path, 'r') as f:
                data = json.load(f)
        elif path.suffix == '.csv':
            # Load CSV and convert to portfolio format
            df = pd.read_csv(path)
            data = self._csv_to_portfolio_dict(df)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        return self._dict_to_portfolio(data)
    
    def save_portfolio(self, portfolio: Portfolio, path: Path) -> None:
        """Save a portfolio to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self._portfolio_to_dict(portfolio)
        
        if path.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif path.suffix == '.csv':
            df = self._portfolio_to_dataframe(portfolio)
            df.to_csv(path, index=False)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        if self._logger:
            self._logger.get_logger(__name__).info(f"Saved portfolio to {path}")
    
    def list_portfolios(
        self,
        directory: Path,
        pattern: Optional[str] = None
    ) -> List[Portfolio]:
        """List all portfolios in a directory."""
        if not directory.exists():
            return []
        
        portfolios = []
        
        # Search for portfolio files
        for ext in ['.json', '.csv']:
            glob_pattern = pattern + ext if pattern else f"*{ext}"
            for file_path in directory.glob(glob_pattern):
                try:
                    portfolio = self.load_portfolio(file_path)
                    portfolios.append(portfolio)
                except Exception as e:
                    if self._logger:
                        self._logger.get_logger(__name__).warning(
                            f"Failed to load portfolio {file_path}: {e}"
                        )
        
        return portfolios
    
    def filter_portfolios(
        self,
        portfolios: List[Portfolio],
        filters: List[PortfolioFilter]
    ) -> List[Portfolio]:
        """Filter portfolios based on criteria."""
        result = portfolios
        
        for filter_obj in filters:
            if hasattr(filter_obj, 'apply'):
                result = [p for p in result if filter_obj.apply(p)]
        
        return result
    
    def aggregate_portfolios(
        self,
        portfolios: List[Portfolio]
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """Aggregate multiple portfolios into a summary."""
        if not portfolios:
            return pd.DataFrame()
        
        # Convert to list of dictionaries
        data = []
        for portfolio in portfolios:
            row = {
                'ticker': portfolio.ticker,
                'strategy': portfolio.strategy,
                'created_at': portfolio.created_at,
                **portfolio.metrics
            }
            data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Convert to polars if configured
        if self._use_polars():
            df = pl.from_pandas(df)
        
        return df
    
    def get_best_portfolios(
        self,
        portfolios: List[Portfolio],
        metric: str = "sharpe_ratio",
        top_n: int = 10
    ) -> List[Portfolio]:
        """Get best performing portfolios by metric."""
        # Sort portfolios by metric
        sorted_portfolios = sorted(
            portfolios,
            key=lambda p: p.metrics.get(metric, float('-inf')),
            reverse=True
        )
        
        return sorted_portfolios[:top_n]
    
    def validate_portfolio(self, portfolio: Portfolio) -> bool:
        """Validate portfolio data integrity."""
        # Check required fields
        if not portfolio.ticker or not portfolio.strategy:
            return False
        
        # Check metrics
        required_metrics = ['total_return', 'sharpe_ratio', 'max_drawdown']
        for metric in required_metrics:
            if metric not in portfolio.metrics:
                return False
        
        # Validate metric values
        if portfolio.metrics['max_drawdown'] > 0:
            return False  # Max drawdown should be negative
        
        return True
    
    def _use_polars(self) -> bool:
        """Check if we should use polars."""
        # Access through data access service config
        return False  # Default to pandas for now
    
    def _dict_to_portfolio(self, data: Dict[str, Any]) -> Portfolio:
        """Convert dictionary to portfolio."""
        return ConcretePortfolio(
            ticker=data['ticker'],
            strategy=data['strategy'],
            metrics=data.get('metrics', {}),
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
            metadata=data.get('metadata', {})
        )
    
    def _portfolio_to_dict(self, portfolio: Portfolio) -> Dict[str, Any]:
        """Convert portfolio to dictionary."""
        return {
            'ticker': portfolio.ticker,
            'strategy': portfolio.strategy,
            'metrics': portfolio.metrics,
            'created_at': portfolio.created_at.isoformat(),
            'metadata': getattr(portfolio, '_metadata', {})
        }
    
    def _csv_to_portfolio_dict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Convert CSV DataFrame to portfolio dictionary."""
        # Assume first row contains portfolio data
        row = df.iloc[0].to_dict()
        
        # Extract known fields
        ticker = row.pop('ticker', 'UNKNOWN')
        strategy = row.pop('strategy', 'UNKNOWN')
        created_at = row.pop('created_at', datetime.now().isoformat())
        
        # Remaining fields are metrics
        return {
            'ticker': ticker,
            'strategy': strategy,
            'metrics': row,
            'created_at': created_at
        }
    
    def _portfolio_to_dataframe(self, portfolio: Portfolio) -> pd.DataFrame:
        """Convert portfolio to DataFrame."""
        data = {
            'ticker': [portfolio.ticker],
            'strategy': [portfolio.strategy],
            'created_at': [portfolio.created_at],
            **{k: [v] for k, v in portfolio.metrics.items()}
        }
        return pd.DataFrame(data)