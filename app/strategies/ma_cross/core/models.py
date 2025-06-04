"""
Core models for MA Cross analysis.

These models define the data structures used throughout the MA Cross analysis,
independent of any specific framework or serialization format.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AnalysisConfig:
    """Configuration for MA Cross analysis."""

    ticker: str
    use_sma: bool = False
    use_hourly: bool = False
    direction: str = "Long"

    # Window parameters
    short_window: Optional[int] | None = None
    long_window: Optional[int] | None = None
    windows: Optional[int] | None = None  # For permutation scanning

    # Data parameters
    use_years: bool = False
    years: float = 1.0

    # Advanced features
    use_synthetic: bool = False
    ticker_1: Optional[str] | None = None
    ticker_2: Optional[str] | None = None
    use_gbm: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format compatible with existing tools."""
        config = {
            "TICKER": self.ticker,
            "USE_SMA": self.use_sma,
            "USE_HOURLY": self.use_hourly,
            "DIRECTION": self.direction,
            "USE_YEARS": self.use_years,
            "YEARS": self.years,
            "USE_SYNTHETIC": self.use_synthetic,
            "USE_GBM": self.use_gbm,
        }

        if self.short_window is not None:
            config["SHORT_WINDOW"] = self.short_window
        if self.long_window is not None:
            config["LONG_WINDOW"] = self.long_window
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

    ma_type: str  # "SMA" or "EMA"
    short_window: int
    long_window: int
    signal_date: datetime
    signal_type: str  # "BUY" or "SELL"
    current: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "ma_type": self.ma_type,
            "short_window": self.short_window,
            "long_window": self.long_window,
            "signal_date": self.signal_date.isoformat(),
            "signal_type": self.signal_type,
            "current": self.current,
        }


@dataclass
class TickerResult:
    """Result for a single ticker analysis."""

    ticker: str
    signals: List[SignalInfo] = field(default_factory=list)
    error: Optional[str] | None = None
    processing_time: float = 0.0

    @property
    def has_current_signal(self) -> bool:
        """Check if any current signals exist."""
        return any(signal.current for signal in self.signals)

    @property
    def current_signals(self) -> List[SignalInfo]:
        """Get only current signals."""
        return [s for s in self.signals if s.current]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "ticker": self.ticker,
            "signals": [s.to_dict() for s in self.signals],
            "has_current_signal": self.has_current_signal,
            "error": self.error,
            "processing_time": self.processing_time,
        }


@dataclass
class AnalysisResult:
    """Complete result of MA Cross analysis."""

    tickers: List[TickerResult] = field(default_factory=list)
    total_processing_time: float = 0.0
    analysis_date: datetime = field(default_factory=datetime.now)
    config: Optional[AnalysisConfig] | None = None

    @property
    def tickers_with_signals(self) -> List[TickerResult]:
        """Get only tickers that have current signals."""
        return [t for t in self.tickers if t.has_current_signal]

    @property
    def signal_count(self) -> int:
        """Total number of current signals across all tickers."""
        return sum(len(t.current_signals) for t in self.tickers)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "tickers": [t.to_dict() for t in self.tickers],
            "total_processing_time": self.total_processing_time,
            "analysis_date": self.analysis_date.isoformat(),
            "signal_count": self.signal_count,
            "config": self.config.to_dict() if self.config else None,
        }
