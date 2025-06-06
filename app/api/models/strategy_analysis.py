"""
MA Cross API Models

This module defines Pydantic models for MA Cross strategy API requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class DirectionEnum(str, Enum):
    """Trading direction enumeration."""

    LONG = "Long"
    SHORT = "Short"


class StrategyTypeEnum(str, Enum):
    """Strategy type enumeration."""

    SMA = "SMA"
    EMA = "EMA"
    MACD = "MACD"


class MinimumCriteria(BaseModel):
    """
    Minimum criteria for portfolio filtering.

    Matches the MinimumConfig TypedDict from app.tools.strategy.types
    """

    trades: Optional[int] = Field(
        None, description="Minimum number of trades", alias="TRADES"
    )
    win_rate: Optional[float] = Field(
        None, description="Minimum win rate (0-1)", alias="WIN_RATE", ge=0, le=1
    )
    expectancy_per_trade: Optional[float] = Field(
        None, description="Minimum expectancy per trade", alias="EXPECTANCY_PER_TRADE"
    )
    profit_factor: Optional[float] = Field(
        None, description="Minimum profit factor", alias="PROFIT_FACTOR", ge=0
    )
    score: Optional[float] = Field(None, description="Minimum score", alias="SCORE")
    sortino_ratio: Optional[float] = Field(
        None, description="Minimum Sortino ratio", alias="SORTINO_RATIO"
    )
    beats_bnh: Optional[float] = Field(
        None, description="Minimum percentage to beat Buy and Hold", alias="BEATS_BNH"
    )

    model_config = {"populate_by_name": True}

    @property
    def tickers(self) -> List[str]:
        """Get tickers as a list for compatibility."""
        # Don't duplicate - this is for when ticker is already a list
        return []  # Return empty list to avoid duplication with ticker field

    def to_dict(self) -> Dict[str, Union[int, float]]:
        """Convert to dictionary format expected by StrategyConfig."""
        result = {}
        if self.trades is not None:
            result["TRADES"] = self.trades
        if self.win_rate is not None:
            result["WIN_RATE"] = self.win_rate
        if self.expectancy_per_trade is not None:
            result["EXPECTANCY_PER_TRADE"] = self.expectancy_per_trade
        if self.profit_factor is not None:
            result["PROFIT_FACTOR"] = self.profit_factor
        if self.score is not None:
            result["SCORE"] = self.score
        if self.sortino_ratio is not None:
            result["SORTINO_RATIO"] = self.sortino_ratio
        if self.beats_bnh is not None:
            result["BEATS_BNH"] = self.beats_bnh
        return result


class MACrossRequest(BaseModel):
    """
    Request model for MA Cross strategy analysis.

    This model provides a Pydantic interface to the StrategyConfig TypedDict
    used by the MA Cross module.
    """

    # Required fields
    ticker: Union[str, List[str]] = Field(
        ..., description="Trading symbol or list of symbols to analyze", alias="TICKER"
    )

    # Optional fields with defaults matching StrategyConfig
    windows: int = Field(
        89,
        description="Maximum window size for parameter analysis",
        alias="WINDOWS",
        ge=2,
        le=200,
    )

    direction: DirectionEnum = Field(
        DirectionEnum.LONG, description="Trading direction", alias="DIRECTION"
    )

    strategy_types: List[StrategyTypeEnum] = Field(
        [StrategyTypeEnum.SMA, StrategyTypeEnum.EMA],
        description="List of strategy types to analyze",
        alias="STRATEGY_TYPES",
    )

    use_hourly: bool = Field(
        False,
        description="Whether to use hourly data instead of daily",
        alias="USE_HOURLY",
    )

    use_years: bool = Field(
        False, description="Whether to limit data by years", alias="USE_YEARS"
    )

    years: float = Field(
        15,
        description="Number of years of data to use (if use_years is True)",
        alias="YEARS",
        gt=0,
        le=50,
    )

    use_synthetic: bool = Field(
        False,
        description="Whether to use synthetic pair trading",
        alias="USE_SYNTHETIC",
    )

    ticker_1: Optional[str] = Field(
        None, description="First ticker for synthetic pair", alias="TICKER_1"
    )

    ticker_2: Optional[str] = Field(
        None, description="Second ticker for synthetic pair", alias="TICKER_2"
    )

    refresh: bool = Field(
        True, description="Whether to refresh cached data", alias="REFRESH"
    )

    minimums: Optional[MinimumCriteria] = Field(
        None, description="Minimum criteria for portfolio filtering", alias="MINIMUMS"
    )

    sort_by: str = Field(
        "Score", description="Field to sort results by", alias="SORT_BY"
    )

    sort_asc: bool = Field(
        False, description="Whether to sort in ascending order", alias="SORT_ASC"
    )

    use_gbm: bool = Field(
        False,
        description="Whether to use Geometric Brownian Motion simulation",
        alias="USE_GBM",
    )

    use_current: bool = Field(
        False, description="Whether to use current market data", alias="USE_CURRENT"
    )

    use_scanner: bool = Field(
        False, description="Whether to use scanner mode", alias="USE_SCANNER"
    )

    # MACD-specific parameters (optional for backward compatibility)
    short_window_start: Optional[int] = Field(
        None,
        description="MACD short EMA window start",
        alias="SHORT_WINDOW_START",
        ge=2,
        le=50,
    )
    short_window_end: Optional[int] = Field(
        None,
        description="MACD short EMA window end",
        alias="SHORT_WINDOW_END",
        ge=3,
        le=100,
    )
    long_window_start: Optional[int] = Field(
        None,
        description="MACD long EMA window start",
        alias="LONG_WINDOW_START",
        ge=4,
        le=100,
    )
    long_window_end: Optional[int] = Field(
        None,
        description="MACD long EMA window end",
        alias="LONG_WINDOW_END",
        ge=5,
        le=200,
    )
    signal_window_start: Optional[int] = Field(
        None,
        description="MACD signal window start",
        alias="SIGNAL_WINDOW_START",
        ge=2,
        le=50,
    )
    signal_window_end: Optional[int] = Field(
        None,
        description="MACD signal window end",
        alias="SIGNAL_WINDOW_END",
        ge=3,
        le=100,
    )
    step: Optional[int] = Field(
        1, description="Parameter increment step", alias="STEP", ge=1, le=10
    )

    # API-specific fields (not in StrategyConfig)
    async_execution: bool = Field(
        False, description="Whether to execute analysis asynchronously"
    )

    model_config = {"populate_by_name": True, "use_enum_values": True}

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v):
        """Validate ticker format."""
        if isinstance(v, str):
            # Check if it's a comma-separated string
            if "," in v:
                # Split and clean the tickers
                tickers = [t.strip() for t in v.split(",") if t.strip()]
                if not tickers:
                    raise ValueError("Ticker list cannot be empty")
                for ticker in tickers:
                    if not ticker or len(ticker) > 10:
                        raise ValueError(
                            f"Each ticker must be between 1 and 10 characters: {ticker}"
                        )
                return tickers
            else:
                # Single ticker
                if not v or len(v) > 10:
                    raise ValueError("Ticker must be between 1 and 10 characters")
        elif isinstance(v, list):
            if not v:
                raise ValueError("Ticker list cannot be empty")
            for ticker in v:
                if not ticker or len(ticker) > 10:
                    raise ValueError(
                        f"Each ticker must be between 1 and 10 characters: {ticker}"
                    )
        return v

    @field_validator("use_synthetic")
    @classmethod
    def validate_synthetic_config(cls, v, info):
        """Validate synthetic pair configuration."""
        if v:
            ticker = info.data.get("ticker")
            if isinstance(ticker, list):
                raise ValueError("Cannot use synthetic pairs with multiple tickers")
        return v

    @field_validator("ticker_1", "ticker_2")
    @classmethod
    def validate_synthetic_tickers(cls, v, info):
        """Validate synthetic ticker requirements."""
        use_synthetic = info.data.get("use_synthetic", False)
        if use_synthetic and not v:
            raise ValueError(
                f"{info.field_name} is required when use_synthetic is True"
            )
        return v

    @field_validator("short_window_end")
    @classmethod
    def validate_short_window_range(cls, v, info):
        """Validate MACD short window range."""
        if v is not None:
            short_start = info.data.get("short_window_start")
            if short_start is not None and v <= short_start:
                raise ValueError(
                    "short_window_end must be greater than short_window_start"
                )
        return v

    @field_validator("long_window_end")
    @classmethod
    def validate_long_window_range(cls, v, info):
        """Validate MACD long window range."""
        if v is not None:
            long_start = info.data.get("long_window_start")
            if long_start is not None and v <= long_start:
                raise ValueError(
                    "long_window_end must be greater than long_window_start"
                )

            # Validate that long window is larger than short window (minimum start value check)
            short_start = info.data.get("short_window_start")
            if (
                short_start is not None
                and long_start is not None
                and long_start <= short_start
            ):
                raise ValueError(
                    "long_window_start must be greater than short_window_start"
                )
        return v

    @field_validator("signal_window_end")
    @classmethod
    def validate_signal_window_range(cls, v, info):
        """Validate MACD signal window range."""
        if v is not None:
            signal_start = info.data.get("signal_window_start")
            if signal_start is not None and v <= signal_start:
                raise ValueError(
                    "signal_window_end must be greater than signal_window_start"
                )
        return v

    @field_validator("strategy_types")
    @classmethod
    def validate_macd_parameters(cls, v, info):
        """Validate MACD parameters when MACD strategy is selected."""
        if StrategyTypeEnum.MACD in v:
            # Check if at least some MACD parameters are provided
            macd_params = [
                "short_window_start",
                "short_window_end",
                "long_window_start",
                "long_window_end",
                "signal_window_start",
                "signal_window_end",
            ]

            provided_params = [
                param for param in macd_params if info.data.get(param) is not None
            ]

            # If any MACD params are provided, we should validate their completeness
            # But for flexibility, we'll allow defaults to be used
            if len(provided_params) > 0 and len(provided_params) < 6:
                # Only require all parameters if some are provided
                missing_params = [
                    param for param in macd_params if info.data.get(param) is None
                ]
                if len(missing_params) > 3:  # Allow some flexibility
                    raise ValueError(
                        f"When providing MACD parameters, please provide all window ranges. Missing: {missing_params}"
                    )
        return v

    @property
    def tickers(self) -> List[str]:
        """Get tickers as a list for compatibility."""
        # Don't duplicate - this is for when ticker is already a list
        return []  # Return empty list to avoid duplication with ticker field

    def to_strategy_config(self) -> Dict[str, Any]:
        """
        Convert to StrategyConfig format expected by MA Cross module.

        Returns:
            Dictionary matching the StrategyConfig TypedDict structure
        """
        config = {
            "TICKER": self.ticker,
            "WINDOWS": self.windows,
            "DIRECTION": self.direction,
            "STRATEGY_TYPES": [
                strategy.value if hasattr(strategy, "value") else strategy
                for strategy in self.strategy_types
            ],  # Convert enum to string value
            "USE_HOURLY": self.use_hourly,
            "USE_YEARS": self.use_years,
            "YEARS": self.years,
            "USE_SYNTHETIC": self.use_synthetic,
            "REFRESH": self.refresh,
            "SORT_BY": self.sort_by,
            "SORT_ASC": self.sort_asc,
            "USE_GBM": self.use_gbm,
            "USE_CURRENT": self.use_current,
            "USE_SCANNER": self.use_scanner,
        }

        # Add optional fields
        if self.ticker_1:
            config["TICKER_1"] = self.ticker_1
        if self.ticker_2:
            config["TICKER_2"] = self.ticker_2
        if self.minimums:
            config["MINIMUMS"] = self.minimums.to_dict()

        # Add MACD-specific parameters
        if self.short_window_start is not None:
            config["SHORT_WINDOW_START"] = self.short_window_start
        if self.short_window_end is not None:
            config["SHORT_WINDOW_END"] = self.short_window_end
        if self.long_window_start is not None:
            config["LONG_WINDOW_START"] = self.long_window_start
        if self.long_window_end is not None:
            config["LONG_WINDOW_END"] = self.long_window_end
        if self.signal_window_start is not None:
            config["SIGNAL_WINDOW_START"] = self.signal_window_start
        if self.signal_window_end is not None:
            config["SIGNAL_WINDOW_END"] = self.signal_window_end
        if self.step is not None:
            config["STEP"] = self.step

        return config


class StrategyAnalysisRequest(BaseModel):
    """
    Unified request model for all strategy analysis types.

    This model provides a flexible interface supporting different strategy types
    with strategy-specific parameters.
    """

    # Required fields
    strategy_type: StrategyTypeEnum = Field(
        ..., description="Type of strategy to analyze"
    )
    ticker: Union[str, List[str]] = Field(
        ..., description="Trading symbol or list of symbols to analyze"
    )

    # Common optional fields
    direction: DirectionEnum = Field(
        DirectionEnum.LONG, description="Trading direction"
    )

    use_hourly: bool = Field(
        False, description="Whether to use hourly data instead of daily"
    )

    use_years: bool = Field(False, description="Whether to limit data by years")

    years: float = Field(
        15,
        description="Number of years of data to use (if use_years is True)",
        gt=0,
        le=50,
    )

    refresh: bool = Field(True, description="Whether to refresh cached data")

    # Strategy-specific parameters (flexible dictionary)
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Strategy-specific parameters"
    )

    # API-specific fields
    async_execution: bool = Field(
        False, description="Whether to execute analysis asynchronously"
    )

    model_config = {"populate_by_name": True, "use_enum_values": True}

    def to_strategy_config(self) -> Dict[str, Any]:
        """Convert to strategy config format."""
        config = {
            "TICKER": self.ticker,
            "DIRECTION": self.direction,
            "USE_HOURLY": self.use_hourly,
            "USE_YEARS": self.use_years,
            "YEARS": self.years,
            "REFRESH": self.refresh,
        }

        # Add strategy-specific parameters
        config.update(self.parameters)

        return config


# MACrossRequest is defined above and remains unchanged for backward compatibility


class PortfolioMetrics(BaseModel):
    """Metrics for a single portfolio result."""

    ticker: str = Field(..., description="Ticker symbol")
    strategy_type: str = Field(..., description="Strategy type (SMA/EMA/MACD)")
    short_window: int = Field(..., description="Short moving average window")
    long_window: int = Field(..., description="Long moving average window")

    # Performance metrics
    total_return: float = Field(..., description="Total return percentage")
    annual_return: float = Field(..., description="Annualized return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")

    # Trade metrics
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: float = Field(..., description="Win rate (0-1)")
    profit_factor: float = Field(..., description="Profit factor")
    expectancy: float = Field(..., description="Expectancy value")
    expectancy_per_trade: float = Field(..., description="Expectancy per trade")
    avg_trade_duration: Optional[str] = Field(
        None, description="Average trade duration"
    )

    # Additional metrics
    score: float = Field(..., description="Overall portfolio score")
    beats_bnh: float = Field(
        ..., description="Percentage by which strategy beats Buy and Hold"
    )

    # Trade status
    has_open_trade: bool = Field(False, description="Whether there's an open trade")
    has_signal_entry: bool = Field(
        False, description="Whether there's a signal for entry"
    )

    # Additional fields from CSV data
    metric_type: Optional[str] = Field(
        default="", description="Metric type classification"
    )

    model_config = {"from_attributes": True}


class MACrossResponse(BaseModel):
    """
    Response model for MA Cross strategy analysis.

    Contains the analysis results and metadata.
    """

    status: Literal["success", "error"] = Field(..., description="Response status")

    # Request metadata
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(..., description="Response timestamp")

    # Analysis configuration
    ticker: Union[str, List[str]] = Field(..., description="Analyzed ticker(s)")
    strategy_types: List[str] = Field(..., description="Strategy types analyzed")

    # Portfolio results
    portfolios: Optional[List[PortfolioMetrics]] = Field(
        None, description="List of portfolio analysis results"
    )

    # Export paths
    portfolio_exports: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Paths to exported portfolio CSV files",
        example={
            "portfolios": ["csv/portfolios/BTC-USD_D_SMA.csv"],
            "portfolios_filtered": ["csv/portfolios_filtered/BTC-USD_D_SMA.csv"],
        },
    )

    # Summary statistics
    total_portfolios_analyzed: int = Field(
        0, description="Total number of portfolios analyzed"
    )

    total_portfolios_filtered: int = Field(
        0, description="Number of portfolios after filtering"
    )

    # Execution metadata
    execution_time: float = Field(..., description="Analysis execution time in seconds")

    # Error information (if applicable)
    error: Optional[str] = Field(None, description="Error message if status is 'error'")
    error_details: Optional[Dict[str, Any]] = Field(
        None, description="Detailed error information"
    )

    model_config = {"from_attributes": True}


class MACrossAsyncResponse(BaseModel):
    """
    Response model for asynchronous MA Cross execution.

    Returned when the analysis is started asynchronously.
    """

    status: Literal["accepted"] = Field(..., description="Response status")
    execution_id: str = Field(..., description="Unique execution identifier")
    message: str = Field(..., description="Status message")

    # Endpoints for checking status and results
    status_url: str = Field(..., description="URL to check execution status")
    stream_url: str = Field(..., description="URL for real-time updates via SSE")

    # Request metadata
    timestamp: datetime = Field(..., description="Request timestamp")
    estimated_time: Optional[float] = Field(
        None, description="Estimated execution time in seconds"
    )


class MACrossStatusResponse(BaseModel):
    """
    Response model for checking MA Cross execution status.

    Provides current status and progress information for async executions.
    """

    status: Literal["pending", "running", "completed", "failed"] = Field(
        ..., description="Current execution status"
    )

    # Timestamps
    started_at: str = Field(..., description="Execution start time (ISO format)")
    completed_at: Optional[str] = Field(
        None, description="Execution completion time (ISO format)"
    )

    # Progress information
    progress: str = Field(..., description="Current progress message")

    # Results (when completed)
    results: Optional[List[PortfolioMetrics]] = Field(
        None, description="Analysis results when completed"
    )

    # Error information (when failed)
    error: Optional[str] = Field(None, description="Error message if failed")

    # Execution metadata
    execution_time: Optional[float] = Field(
        None, description="Total execution time in seconds (when completed)"
    )


class MACrossMetricsResponse(BaseModel):
    """
    Response model for available MA Cross metrics information.

    Provides details about what metrics are calculated.
    """

    available_metrics: List[Dict[str, str]] = Field(
        ..., description="List of available metrics with descriptions"
    )

    metric_categories: Dict[str, List[str]] = Field(
        ..., description="Metrics grouped by category"
    )


class MACrossStatus(BaseModel):
    """Status model for MA Cross execution tracking."""

    execution_id: str = Field(..., description="Unique execution identifier")
    status: str = Field(..., description="Current status")
    progress: int = Field(0, description="Progress percentage")
    message: str = Field("", description="Status message")
    result: Optional[Dict[str, Any]] = Field(None, description="Result when completed")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class MACrossMetrics(BaseModel):
    """Aggregated metrics for MA Cross analysis."""

    avg_return: float = Field(..., description="Average return across portfolios")
    avg_sharpe: float = Field(..., description="Average Sharpe ratio")
    avg_max_drawdown: float = Field(..., description="Average maximum drawdown")
    avg_win_rate: float = Field(..., description="Average win rate")
    total_final_balance: float = Field(..., description="Total final balance")
    total_roi: float = Field(..., description="Total ROI")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field("1.0.0", description="API version")
    dependencies: Dict[str, str] = Field(
        default_factory=dict, description="Dependency statuses"
    )
