"""Strategy type definitions."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
import polars as pl


@dataclass
class StrategyParameters:
    """Base strategy parameters."""

    strategy_type: str
    timeframe: str
    parameters: dict[str, Any]
    filters: dict[str, Any] | None = None
    risk_management: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class BacktestResult:
    """Backtest result container."""

    strategy: StrategyParameters
    ticker: str
    start_date: datetime
    end_date: datetime
    metrics: dict[str, float]
    trades: pd.DataFrame | pl.DataFrame
    equity_curve: pd.DataFrame | pl.DataFrame
    signals: pd.DataFrame | pl.DataFrame
    metadata: dict[str, Any] | None = None


@dataclass
class OptimizationResult:
    """Strategy optimization result."""

    strategy_type: str
    ticker: str
    best_params: dict[str, Any]
    best_metrics: dict[str, float]
    all_results: list[dict[str, Any]]
    optimization_time: float
    metadata: dict[str, Any] | None = None
