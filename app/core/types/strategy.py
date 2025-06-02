"""Strategy type definitions."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import pandas as pd
import polars as pl


@dataclass
class StrategyParameters:
    """Base strategy parameters."""
    strategy_type: str
    timeframe: str
    parameters: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    risk_management: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BacktestResult:
    """Backtest result container."""
    strategy: StrategyParameters
    ticker: str
    start_date: datetime
    end_date: datetime
    metrics: Dict[str, float]
    trades: Union[pd.DataFrame, pl.DataFrame]
    equity_curve: Union[pd.DataFrame, pl.DataFrame]
    signals: Union[pd.DataFrame, pl.DataFrame]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class OptimizationResult:
    """Strategy optimization result."""
    strategy_type: str
    ticker: str
    best_params: Dict[str, Any]
    best_metrics: Dict[str, float]
    all_results: List[Dict[str, Any]]
    optimization_time: float
    metadata: Optional[Dict[str, Any]] = None