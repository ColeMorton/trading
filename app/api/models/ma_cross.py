"""
MA Cross API Models

This module defines Pydantic models for MA Cross strategy API requests and responses.
"""

from typing import Dict, Any, Optional, Union, List, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum

class DirectionEnum(str, Enum):
    """Trading direction enumeration."""
    LONG = "Long"
    SHORT = "Short"

class StrategyTypeEnum(str, Enum):
    """Strategy type enumeration."""
    SMA = "SMA"
    EMA = "EMA"

class MinimumCriteria(BaseModel):
    """
    Minimum criteria for portfolio filtering.
    
    Matches the MinimumConfig TypedDict from app.tools.strategy.types
    """
    trades: Optional[int] = Field(None, description="Minimum number of trades", alias="TRADES")
    win_rate: Optional[float] = Field(None, description="Minimum win rate (0-1)", alias="WIN_RATE", ge=0, le=1)
    expectancy_per_trade: Optional[float] = Field(None, description="Minimum expectancy per trade", alias="EXPECTANCY_PER_TRADE")
    profit_factor: Optional[float] = Field(None, description="Minimum profit factor", alias="PROFIT_FACTOR", ge=0)
    score: Optional[float] = Field(None, description="Minimum score", alias="SCORE")
    sortino_ratio: Optional[float] = Field(None, description="Minimum Sortino ratio", alias="SORTINO_RATIO")
    beats_bnh: Optional[float] = Field(None, description="Minimum percentage to beat Buy and Hold", alias="BEATS_BNH")
    
    model_config = {
        "populate_by_name": True
    }
    
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
        ..., 
        description="Trading symbol or list of symbols to analyze",
        alias="TICKER"
    )
    
    # Optional fields with defaults matching StrategyConfig
    windows: int = Field(
        89, 
        description="Maximum window size for parameter analysis",
        alias="WINDOWS",
        ge=2,
        le=200
    )
    
    direction: DirectionEnum = Field(
        DirectionEnum.LONG,
        description="Trading direction",
        alias="DIRECTION"
    )
    
    strategy_types: List[StrategyTypeEnum] = Field(
        [StrategyTypeEnum.SMA, StrategyTypeEnum.EMA],
        description="List of strategy types to analyze",
        alias="STRATEGY_TYPES"
    )
    
    use_hourly: bool = Field(
        False,
        description="Whether to use hourly data instead of daily",
        alias="USE_HOURLY"
    )
    
    use_years: bool = Field(
        False,
        description="Whether to limit data by years",
        alias="USE_YEARS"
    )
    
    years: float = Field(
        15,
        description="Number of years of data to use (if use_years is True)",
        alias="YEARS",
        gt=0,
        le=50
    )
    
    use_synthetic: bool = Field(
        False,
        description="Whether to use synthetic pair trading",
        alias="USE_SYNTHETIC"
    )
    
    ticker_1: Optional[str] = Field(
        None,
        description="First ticker for synthetic pair",
        alias="TICKER_1"
    )
    
    ticker_2: Optional[str] = Field(
        None,
        description="Second ticker for synthetic pair",
        alias="TICKER_2"
    )
    
    refresh: bool = Field(
        True,
        description="Whether to refresh cached data",
        alias="REFRESH"
    )
    
    minimums: Optional[MinimumCriteria] = Field(
        None,
        description="Minimum criteria for portfolio filtering",
        alias="MINIMUMS"
    )
    
    sort_by: str = Field(
        "Score",
        description="Field to sort results by",
        alias="SORT_BY"
    )
    
    sort_asc: bool = Field(
        False,
        description="Whether to sort in ascending order",
        alias="SORT_ASC"
    )
    
    use_gbm: bool = Field(
        False,
        description="Whether to use Geometric Brownian Motion simulation",
        alias="USE_GBM"
    )
    
    # API-specific fields (not in StrategyConfig)
    async_execution: bool = Field(
        False,
        description="Whether to execute analysis asynchronously"
    )
    
    # MA window parameters for API convenience
    fast_period: Optional[int] = Field(
        None,
        description="Fast moving average period",
        ge=2,
        le=200
    )
    
    slow_period: Optional[int] = Field(
        None,
        description="Slow moving average period",
        ge=2,
        le=200
    )
    
    # Additional parameters
    allocation_pct: Optional[float] = Field(
        None,
        description="Allocation percentage for portfolio",
        ge=0.0,
        le=1.0
    )
    
    stop_loss_pct: Optional[float] = Field(
        None,
        description="Stop loss percentage",
        ge=0.0,
        le=1.0
    )
    
    # Convenience properties
    @property 
    def short_window(self) -> Optional[int]:
        """Alias for fast_period."""
        return self.fast_period or 20  # Default to 20 if not specified
    
    @property
    def long_window(self) -> Optional[int]:
        """Alias for slow_period."""
        return self.slow_period or 50  # Default to 50 if not specified
    
    model_config = {
        "populate_by_name": True,
        "use_enum_values": True
    }
        
    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v):
        """Validate ticker format."""
        if isinstance(v, str):
            if not v or len(v) > 10:
                raise ValueError("Ticker must be between 1 and 10 characters")
        elif isinstance(v, list):
            if not v:
                raise ValueError("Ticker list cannot be empty")
            for ticker in v:
                if not ticker or len(ticker) > 10:
                    raise ValueError(f"Each ticker must be between 1 and 10 characters: {ticker}")
        return v
    
    @field_validator('use_synthetic')
    @classmethod
    def validate_synthetic_config(cls, v, info):
        """Validate synthetic pair configuration."""
        if v:
            ticker = info.data.get('ticker')
            if isinstance(ticker, list):
                raise ValueError("Cannot use synthetic pairs with multiple tickers")
        return v
    
    @field_validator('ticker_1', 'ticker_2')
    @classmethod
    def validate_synthetic_tickers(cls, v, info):
        """Validate synthetic ticker requirements."""
        use_synthetic = info.data.get('use_synthetic', False)
        if use_synthetic and not v:
            raise ValueError(f"{info.field_name} is required when use_synthetic is True")
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
            "STRATEGY_TYPES": self.strategy_types,
            "USE_HOURLY": self.use_hourly,
            "USE_YEARS": self.use_years,
            "YEARS": self.years,
            "USE_SYNTHETIC": self.use_synthetic,
            "REFRESH": self.refresh,
            "SORT_BY": self.sort_by,
            "SORT_ASC": self.sort_asc,
            "USE_GBM": self.use_gbm,
            "USE_CURRENT": False,  # Default from original config
            "USE_SCANNER": False,  # API doesn't support scanner mode
        }
        
        # Add optional fields
        if self.ticker_1:
            config["TICKER_1"] = self.ticker_1
        if self.ticker_2:
            config["TICKER_2"] = self.ticker_2
        if self.minimums:
            config["MINIMUMS"] = self.minimums.to_dict()
        if self.fast_period:
            config["SHORT_WINDOW"] = self.fast_period
        if self.slow_period:
            config["LONG_WINDOW"] = self.slow_period
            
        return config

class PortfolioMetrics(BaseModel):
    """Metrics for a single portfolio result."""
    ticker: str = Field(..., description="Ticker symbol")
    strategy_type: str = Field(..., description="Strategy type (SMA/EMA)")
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
    expectancy: float = Field(..., description="Expectancy per trade")
    
    # Additional metrics
    score: float = Field(..., description="Overall portfolio score")
    beats_bnh: float = Field(..., description="Percentage by which strategy beats Buy and Hold")
    
    # Optional extended schema fields
    allocation_percent: Optional[float] = Field(None, description="Portfolio allocation percentage")
    stop_loss_percent: Optional[float] = Field(None, description="Stop loss percentage")
    position_size: Optional[float] = Field(None, description="Calculated position size")
    
    # Trade status
    has_open_trade: bool = Field(False, description="Whether there's an open trade")
    has_signal_entry: bool = Field(False, description="Whether there's a signal for entry")
    
    model_config = {
        "from_attributes": True
    }

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
    
    # Results
    portfolios: List[PortfolioMetrics] = Field(
        default_factory=list,
        description="List of portfolio analysis results"
    )
    
    # Summary statistics
    total_portfolios: int = Field(..., description="Total number of portfolios analyzed")
    filtered_portfolios: int = Field(..., description="Number of portfolios after filtering")
    
    # Breadth metrics
    breadth_metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Market breadth analysis metrics"
    )
    
    # Execution metadata
    execution_time: float = Field(..., description="Analysis execution time in seconds")
    
    # Error information (if applicable)
    error: Optional[str] = Field(None, description="Error message if status is 'error'")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")
    
    model_config = {
        "from_attributes": True
    }

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
        None,
        description="Estimated execution time in seconds"
    )

class MACrossStatusResponse(BaseModel):
    """
    Response model for checking MA Cross execution status.
    
    Provides current status and progress information for async executions.
    """
    status: Literal["pending", "running", "completed", "failed"] = Field(
        ...,
        description="Current execution status"
    )
    
    # Timestamps
    started_at: str = Field(..., description="Execution start time (ISO format)")
    completed_at: Optional[str] = Field(None, description="Execution completion time (ISO format)")
    
    # Progress information
    progress: str = Field(..., description="Current progress message")
    
    # Results (when completed)
    results: Optional[List[PortfolioMetrics]] = Field(
        None,
        description="Analysis results when completed"
    )
    
    # Error information (when failed)
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Execution metadata
    execution_time: Optional[float] = Field(
        None,
        description="Total execution time in seconds (when completed)"
    )

class MACrossMetricsResponse(BaseModel):
    """
    Response model for available MA Cross metrics information.
    
    Provides details about what metrics are calculated.
    """
    available_metrics: List[Dict[str, str]] = Field(
        ...,
        description="List of available metrics with descriptions"
    )
    
    metric_categories: Dict[str, List[str]] = Field(
        ...,
        description="Metrics grouped by category"
    )

class MACrossStatus(BaseModel):
    """Status model for MA Cross execution tracking."""
    task_id: str = Field(..., description="Unique task identifier")
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
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency statuses")