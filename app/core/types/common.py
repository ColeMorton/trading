"""Common type definitions used across the system."""

from enum import Enum
from typing import Literal


class TimeFrame(str, Enum):
    """Trading timeframes."""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1mo"


class SignalType(str, Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


class OrderType(str, Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class PositionSide(str, Enum):
    """Position sides."""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class StrategyType(str, Enum):
    """Available strategy types."""
    MA_CROSS = "ma_cross"
    MACD = "macd"
    RSI = "rsi"
    MEAN_REVERSION = "mean_reversion"
    RANGE = "range"
    CUSTOM = "custom"


class MetricName(str, Enum):
    """Standard metric names."""
    TOTAL_RETURN = "total_return"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    EXPECTANCY = "expectancy"
    VOLATILITY = "volatility"
    TRADES_COUNT = "trades_count"
    AVG_TRADE_DURATION = "avg_trade_duration"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Type aliases for common patterns
Ticker = str
Interval = Literal["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo"]
Currency = str
Percentage = float  # 0-100
Decimal = float  # 0-1