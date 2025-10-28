"""
SQLAlchemy ORM models for database tables.

This module provides ORM models for the trading strategy database,
including metric types and strategy sweep results with relationships.
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


Base = declarative_base()


class Ticker(Base):
    """
    Reference table for unique ticker symbols.

    Stores unique ticker symbols that can be referenced by strategy sweep results
    and other tables. This normalization ensures data consistency and integrity.
    """

    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(50), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationship to strategy sweep results
    sweep_results = relationship(
        "StrategySweepResult", back_populates="ticker_obj", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ticker(id={self.id}, ticker='{self.ticker}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary representation."""
        return {
            "id": self.id,
            "ticker": self.ticker,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StrategyType(Base):
    """
    Reference table for unique strategy types.

    Stores unique strategy type identifiers (e.g., SMA, EMA, MACD) that can be
    referenced by strategy sweep results and best selections. This normalization
    ensures data consistency and integrity.
    """

    __tablename__ = "strategy_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_type = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    sweep_results = relationship(
        "StrategySweepResult",
        back_populates="strategy_type_obj",
        cascade="all, delete-orphan",
    )
    best_selections = relationship(
        "SweepBestSelection",
        back_populates="strategy_type_obj",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<StrategyType(id={self.id}, strategy_type='{self.strategy_type}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary representation."""
        return {
            "id": self.id,
            "strategy_type": self.strategy_type,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MetricType(Base):
    """
    Reference table for metric type classifications.

    Stores standard metric classifications like "Most Sharpe Ratio",
    "Median Total Return [%]", etc. that can be assigned to strategy
    sweep results.
    """

    __tablename__ = "metric_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationship to junction table
    sweep_result_associations = relationship(
        "StrategySweepResultMetric",
        back_populates="metric_type",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<MetricType(id={self.id}, name='{self.name}', category='{self.category}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StrategySweepResultMetric(Base):
    """
    Junction table linking strategy sweep results to metric type classifications.

    This enables a many-to-many relationship where one sweep result can have
    multiple metric type classifications (e.g., "Most Sharpe Ratio, Most Total Return [%]").
    """

    __tablename__ = "strategy_sweep_result_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sweep_result_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("strategy_sweep_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_type_id = Column(
        Integer, ForeignKey("metric_types.id"), nullable=False, index=True
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Unique constraint to prevent duplicate assignments
    __table_args__ = (
        UniqueConstraint(
            "sweep_result_id", "metric_type_id", name="uq_sweep_result_metric"
        ),
    )

    # Relationships
    metric_type = relationship("MetricType", back_populates="sweep_result_associations")
    sweep_result = relationship(
        "StrategySweepResult", back_populates="metric_type_associations"
    )

    def __repr__(self) -> str:
        return (
            f"<StrategySweepResultMetric(id={self.id}, "
            f"sweep_result_id={self.sweep_result_id}, "
            f"metric_type_id={self.metric_type_id})>"
        )


class StrategySweepResult(Base):
    """
    Strategy sweep result with comprehensive backtest metrics.

    Stores all performance metrics from parameter sweep analysis,
    with relationships to metric type classifications.
    """

    __tablename__ = "strategy_sweep_results"

    # Primary key and metadata
    id = Column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    sweep_run_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Core strategy parameters
    ticker_id = Column(
        Integer,
        ForeignKey("tickers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strategy_type_id = Column(
        Integer,
        ForeignKey("strategy_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fast_period = Column(Integer, nullable=True)
    slow_period = Column(Integer, nullable=True)
    signal_period = Column(Integer, nullable=True)

    # Signal information
    signal_entry = Column(String(50), nullable=True)
    signal_exit = Column(String(50), nullable=True)
    signal_unconfirmed = Column(String(50), nullable=True)

    # Trade statistics
    total_open_trades = Column(Integer, nullable=True)
    total_trades = Column(Integer, nullable=True)
    score = Column(Numeric(20, 8), nullable=True)

    # Performance metrics
    win_rate_pct = Column(Numeric(10, 4), nullable=True)
    profit_factor = Column(Numeric(20, 8), nullable=True)
    expectancy_per_trade = Column(Numeric(20, 8), nullable=True)
    sortino_ratio = Column(Numeric(20, 8), nullable=True)
    beats_bnh_pct = Column(Numeric(10, 4), nullable=True)

    # Timing metrics
    avg_trade_duration = Column(String(50), nullable=True)
    trades_per_day = Column(Numeric(20, 8), nullable=True)
    trades_per_month = Column(Numeric(20, 8), nullable=True)
    signals_per_month = Column(Numeric(20, 8), nullable=True)
    expectancy_per_month = Column(Numeric(20, 8), nullable=True)

    # Period information
    start = Column(Integer, nullable=True)
    end = Column(Integer, nullable=True)
    period = Column(String(50), nullable=True)

    # Portfolio values
    start_value = Column(Numeric(20, 2), nullable=True)
    end_value = Column(Numeric(20, 2), nullable=True)
    total_return_pct = Column(Numeric(10, 4), nullable=True)
    benchmark_return_pct = Column(Numeric(10, 4), nullable=True)
    max_gross_exposure_pct = Column(Numeric(10, 4), nullable=True)

    # Risk and drawdown
    total_fees_paid = Column(Numeric(20, 2), nullable=True)
    max_drawdown_pct = Column(Numeric(10, 4), nullable=True)
    max_drawdown_duration = Column(String(50), nullable=True)
    total_closed_trades = Column(Integer, nullable=True)

    # Trade analysis
    open_trade_pnl = Column(Numeric(20, 2), nullable=True)
    best_trade_pct = Column(Numeric(10, 4), nullable=True)
    worst_trade_pct = Column(Numeric(10, 4), nullable=True)
    avg_winning_trade_pct = Column(Numeric(10, 4), nullable=True)
    avg_losing_trade_pct = Column(Numeric(10, 4), nullable=True)
    avg_winning_trade_duration = Column(String(50), nullable=True)
    avg_losing_trade_duration = Column(String(50), nullable=True)

    # Advanced metrics
    expectancy = Column(Numeric(20, 8), nullable=True)
    sharpe_ratio = Column(Numeric(20, 8), nullable=True)
    calmar_ratio = Column(Numeric(20, 8), nullable=True)
    omega_ratio = Column(Numeric(20, 8), nullable=True)

    # Risk metrics
    skew = Column(Numeric(20, 8), nullable=True)
    kurtosis = Column(Numeric(20, 8), nullable=True)
    tail_ratio = Column(Numeric(20, 8), nullable=True)
    common_sense_ratio = Column(Numeric(20, 8), nullable=True)
    value_at_risk = Column(Numeric(20, 8), nullable=True)
    daily_returns = Column(Numeric(20, 8), nullable=True)
    annual_returns = Column(Numeric(20, 8), nullable=True)
    cumulative_returns = Column(Numeric(20, 8), nullable=True)
    annualized_return = Column(Numeric(20, 8), nullable=True)
    annualized_volatility = Column(Numeric(20, 8), nullable=True)

    # Signal and position counts
    signal_count = Column(Integer, nullable=True)
    position_count = Column(Integer, nullable=True)
    total_period = Column(Numeric(20, 8), nullable=True)

    # Universal exit strategy parameters
    exit_fast_period = Column(Integer, nullable=True)
    exit_slow_period = Column(Numeric(20, 8), nullable=True)
    exit_signal_period = Column(Integer, nullable=True)

    # Extended schema fields
    allocation_pct = Column(Numeric(10, 4), nullable=True)
    stop_loss_pct = Column(Numeric(10, 4), nullable=True)
    last_position_open_date = Column(String(50), nullable=True)
    last_position_close_date = Column(String(50), nullable=True)

    # Deprecated: kept for backward compatibility
    # Use metric_type_associations relationship instead
    metric_type = Column(String(500), nullable=True)

    # Relationships
    ticker_obj = relationship("Ticker", back_populates="sweep_results")
    strategy_type_obj = relationship("StrategyType", back_populates="sweep_results")
    metric_type_associations = relationship(
        "StrategySweepResultMetric",
        back_populates="sweep_result",
        cascade="all, delete-orphan",
    )

    @property
    def ticker(self) -> str:
        """Get ticker symbol from relationship for backward compatibility."""
        return self.ticker_obj.ticker if self.ticker_obj else ""

    @property
    def strategy_type(self) -> str:
        """Get strategy type name from relationship for backward compatibility."""
        return self.strategy_type_obj.strategy_type if self.strategy_type_obj else ""

    def __repr__(self) -> str:
        return (
            f"<StrategySweepResult(id={self.id}, "
            f"ticker='{self.ticker}', "
            f"strategy_type='{self.strategy_type}', "
            f"score={self.score})>"
        )

    def get_metric_types(self) -> list[str]:
        """Get list of metric type names for this result."""
        return [assoc.metric_type.name for assoc in self.metric_type_associations]

    def get_metric_types_by_category(self) -> dict[str, list[str]]:
        """Get metric types grouped by category."""
        result: dict[str, list[str]] = {}
        for assoc in self.metric_type_associations:
            category = assoc.metric_type.category or "other"
            if category not in result:
                result[category] = []
            result[category].append(assoc.metric_type.name)
        return result


class SelectionAlgorithm(Base):
    """
    Reference table for selection algorithm definitions.

    Stores metadata about algorithms used to determine "best" portfolios
    in strategy sweep results.
    """

    __tablename__ = "selection_algorithms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    algorithm_code = Column(String(50), unique=True, nullable=False, index=True)
    algorithm_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    min_confidence = Column(Numeric(5, 2), nullable=True)
    max_confidence = Column(Numeric(5, 2), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SelectionAlgorithm(id={self.id}, "
            f"code='{self.algorithm_code}', "
            f"name='{self.algorithm_name}')>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary representation."""
        return {
            "id": self.id,
            "algorithm_code": self.algorithm_code,
            "algorithm_name": self.algorithm_name,
            "description": self.description,
            "min_confidence": (
                float(self.min_confidence) if self.min_confidence else None
            ),
            "max_confidence": (
                float(self.max_confidence) if self.max_confidence else None
            ),
        }


class SweepBestSelection(Base):
    """
    Tracks the "best" portfolio selection for each sweep run + ticker + strategy combination.

    Records which result was selected as best, along with the selection algorithm used,
    confidence score, and snapshot of key metrics at time of selection.
    """

    __tablename__ = "sweep_best_selections"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core identifiers
    sweep_run_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id"), nullable=False, index=True)
    strategy_type_id = Column(
        Integer,
        ForeignKey("strategy_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    best_result_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("strategy_sweep_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Selection algorithm metadata
    selection_algorithm = Column(String(50), nullable=False)
    selection_criteria = Column(String(100), nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    alternatives_considered = Column(Integer, nullable=True)

    # Winning parameter combination (denormalized for quick queries)
    winning_fast_period = Column(Integer, nullable=True)
    winning_slow_period = Column(Integer, nullable=True)
    winning_signal_period = Column(Integer, nullable=True)

    # Result snapshot (at time of selection)
    result_score = Column(Numeric(20, 8), nullable=True)
    result_sharpe_ratio = Column(Numeric(20, 8), nullable=True)
    result_total_return_pct = Column(Numeric(10, 4), nullable=True)
    result_win_rate_pct = Column(Numeric(10, 4), nullable=True)

    # Audit timestamp
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Unique constraint: one best per sweep + ticker + strategy
    __table_args__ = (
        UniqueConstraint(
            "sweep_run_id",
            "ticker_id",
            "strategy_type_id",
            name="uq_best_selection_per_sweep_ticker_strategy_type_id",
        ),
    )

    # Relationships
    best_result = relationship(
        "StrategySweepResult", foreign_keys=[best_result_id], backref="best_selections"
    )
    strategy_type_obj = relationship("StrategyType", back_populates="best_selections")

    @property
    def strategy_type(self) -> str:
        """Get strategy type name from relationship for backward compatibility."""
        return self.strategy_type_obj.strategy_type if self.strategy_type_obj else ""

    def __repr__(self) -> str:
        return (
            f"<SweepBestSelection(id={self.id}, "
            f"sweep_run_id={self.sweep_run_id}, "
            f"ticker_id={self.ticker_id}, "
            f"strategy_type='{self.strategy_type}', "
            f"criteria='{self.selection_criteria}')>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary representation."""
        return {
            "id": self.id,
            "sweep_run_id": str(self.sweep_run_id),
            "ticker_id": self.ticker_id,
            "strategy_type": self.strategy_type,
            "best_result_id": str(self.best_result_id),
            "selection_algorithm": self.selection_algorithm,
            "selection_criteria": self.selection_criteria,
            "confidence_score": (
                float(self.confidence_score) if self.confidence_score else None
            ),
            "alternatives_considered": self.alternatives_considered,
            "winning_fast_period": self.winning_fast_period,
            "winning_slow_period": self.winning_slow_period,
            "winning_signal_period": self.winning_signal_period,
            "result_score": float(self.result_score) if self.result_score else None,
            "result_sharpe_ratio": (
                float(self.result_sharpe_ratio) if self.result_sharpe_ratio else None
            ),
            "result_total_return_pct": (
                float(self.result_total_return_pct)
                if self.result_total_return_pct
                else None
            ),
            "result_win_rate_pct": (
                float(self.result_win_rate_pct) if self.result_win_rate_pct else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
