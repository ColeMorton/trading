"""Portfolio type definitions."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics."""

    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    expectancy: float
    volatility: float
    trades_count: int
    avg_trade_duration: float
    risk_adjusted_return: float
    calmar_ratio: float
    value_at_risk: float
    conditional_value_at_risk: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PortfolioConfig:
    """Portfolio configuration."""

    name: str
    tickers: List[str]
    weights: Optional[Dict[str, float]] = None
    rebalance_frequency: str = "monthly"
    start_date: Optional[datetime] | None = None
    end_date: Optional[datetime] | None = None
    initial_capital: float = 100000
    commission: float = 0.001
    slippage: float = 0.001
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AllocationConfig:
    """Position allocation configuration."""

    method: str  # equal, risk_parity, kelly, fixed
    max_position_size: float = 0.25
    min_position_size: float = 0.01
    risk_per_trade: float = 0.02
    use_stop_loss: bool = True
    stop_loss_percent: float = 0.05
    use_position_sizing: bool = True
    metadata: Optional[Dict[str, Any]] = None
