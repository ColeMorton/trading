"""
Core models for MA Cross analysis.

These models define the data structures used throughout the MA Cross analysis,
independent of any specific framework or serialization format.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AnalysisConfig:
    """Configuration for MA Cross analysis."""

    ticker: str
    strategy_type: str = "SMA"  # SMA, EMA, etc.
    use_hourly: bool = False
    direction: str = "Long"

    # Window parameters
    fast_period: int | None | None = None
    slow_period: int | None | None = None
    windows: int | None | None = None  # For permutation scanning

    # Data parameters
    use_years: bool = False
    years: float = 1.0

    # Advanced features
    use_synthetic: bool = False
    ticker_1: str | None | None = None
    ticker_2: str | None | None = None
    use_gbm: bool = False

    @property
    def use_sma(self) -> bool:
        """Derive use_sma from strategy_type for backward compatibility."""
        return self.strategy_type == "SMA"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format compatible with existing tools."""
        config = {
            "TICKER": self.ticker,
            "STRATEGY_TYPE": self.strategy_type,
            "USE_HOURLY": self.use_hourly,
            "DIRECTION": self.direction,
            "USE_YEARS": self.use_years,
            "YEARS": self.years,
            "USE_SYNTHETIC": self.use_synthetic,
            "USE_GBM": self.use_gbm,
        }

        if self.fast_period is not None:
            config["FAST_PERIOD"] = self.fast_period
        if self.slow_period is not None:
            config["SLOW_PERIOD"] = self.slow_period
        if self.windows is not None:
            config["WINDOWS"] = self.windows
        if self.ticker_1 is not None:
            config["TICKER_1"] = self.ticker_1
        if self.ticker_2 is not None:
            config["TICKER_2"] = self.ticker_2

        return config


@dataclass
class SignalInfo:
    """Information about a detected signal."""

    # Support both old and new field names
    ma_type: str | None | None = None  # "SMA" or "EMA"
    fast_period: int | None | None = None
    slow_period: int | None | None = None
    signal_date: datetime | None | None = None
    signal_type: str | None | None = None  # "BUY" or "SELL"
    current: bool = False

    # Alternative fields for compatibility
    date: str | None | None = None
    signal_entry: bool | None | None = None
    signal_exit: bool | None | None = None
    current_position: int | None | None = None
    price: float | None | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        # Return new format if available
        if self.ma_type is not None:
            return {
                "ma_type": self.ma_type,
                "fast_period": self.fast_period,
                "slow_period": self.slow_period,
                "signal_date": (
                    self.signal_date.isoformat() if self.signal_date else None
                ),
                "signal_type": self.signal_type,
                "current": self.current,
            }
        # Return old format for compatibility
        return {
            "date": self.date,
            "signal_entry": self.signal_entry,
            "signal_exit": self.signal_exit,
            "current_position": self.current_position,
            "price": self.price,
        }


@dataclass
class TickerResult:
    """Result for a single ticker analysis."""

    ticker: str
    signals: list[SignalInfo] = field(default_factory=list)
    error: str | None | None = None
    processing_time: float = 0.0

    # Portfolio metrics (optional, for backtesting results)
    strategy_type: str | None | None = None
    fast_period: int | None | None = None
    slow_period: int | None | None = None
    total_trades: int = 0
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate_pct: float = 0.0
    profit_factor: float = 0.0
    expectancy_per_trade: float = 0.0
    sortino_ratio: float = 0.0
    beats_bnh_pct: float = 0.0

    @property
    def has_current_signal(self) -> bool:
        """Check if any current signals exist."""
        return any(signal.current for signal in self.signals)

    @property
    def current_signals(self) -> list[SignalInfo]:
        """Get only current signals."""
        return [s for s in self.signals if s.current]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "ticker": self.ticker,
            "signals": [s.to_dict() for s in self.signals],
            "has_current_signal": self.has_current_signal,
            "error": self.error,
            "processing_time": self.processing_time,
        }

        # Add portfolio metrics if available
        if self.strategy_type:
            result.update(
                {
                    "strategy_type": self.strategy_type,
                    "fast_period": self.fast_period,
                    "slow_period": self.slow_period,
                    "total_trades": self.total_trades,
                    "total_return_pct": self.total_return_pct,
                    "sharpe_ratio": self.sharpe_ratio,
                    "max_drawdown_pct": self.max_drawdown_pct,
                    "win_rate_pct": self.win_rate_pct,
                    "profit_factor": self.profit_factor,
                    "expectancy_per_trade": self.expectancy_per_trade,
                    "sortino_ratio": self.sortino_ratio,
                    "beats_bnh_pct": self.beats_bnh_pct,
                }
            )

        return result


@dataclass
class AnalysisResult:
    """Complete result of MA Cross analysis."""

    tickers: list[TickerResult] = field(default_factory=list)
    total_processing_time: float = 0.0
    analysis_date: datetime = field(default_factory=datetime.now)
    config: AnalysisConfig | None | None = None

    @property
    def tickers_with_signals(self) -> list[TickerResult]:
        """Get only tickers that have current signals."""
        return [t for t in self.tickers if t.has_current_signal]

    @property
    def signal_count(self) -> int:
        """Total number of current signals across all tickers."""
        return sum(len(t.current_signals) for t in self.tickers)

    @property
    def results(self) -> list[TickerResult]:
        """Backward compatibility property for tests."""
        return self.tickers

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "tickers": [t.to_dict() for t in self.tickers],
            "total_processing_time": self.total_processing_time,
            "analysis_date": self.analysis_date.isoformat(),
            "signal_count": self.signal_count,
            "config": self.config.to_dict() if self.config else None,
        }


# Type aliases for backward compatibility with existing tests
MACrossConfig = AnalysisConfig
MACrossResult = AnalysisResult
PortfolioResult = TickerResult
TradingSignal = SignalInfo
