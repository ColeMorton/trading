"""
Backtesting Parameter Models

Pydantic models specifically for backtesting parameter generation,
export formats, and framework-specific templates.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .statistical_analysis_models import ConfidenceLevel, DataSource


class BacktestingFramework(str, Enum):
    """Supported backtesting frameworks"""

    VECTORBT = "vectorbt"
    BACKTRADER = "backtrader"
    ZIPLINE = "zipline"
    PYALGOTRADE = "pyalgotrade"
    CUSTOM = "custom"


class ParameterType(str, Enum):
    """Types of exit parameters"""

    PRICE_LEVEL = "price_level"  # Absolute price levels
    PERCENTAGE = "percentage"  # Percentage-based exits
    TIME_BASED = "time_based"  # Time-based exits
    TRAILING_STOP = "trailing_stop"  # Trailing stop mechanisms
    MULTI_CONDITION = "multi_condition"  # Complex condition combinations
    VAR_BASED = "var_based"  # VaR-based risk exits


class MarketRegime(str, Enum):
    """Market regime classifications for parameter sets"""

    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


class DeterministicExitCriteria(BaseModel):
    """Individual deterministic exit criteria"""

    criteria_type: ParameterType = Field(description="Type of exit criteria")
    description: str = Field(description="Human-readable criteria description")

    # Percentage-based criteria
    take_profit_pct: float | None = Field(
        description="Take profit percentage", default=None
    )
    stop_loss_pct: float | None = Field(
        description="Stop loss percentage", default=None
    )
    trailing_stop_pct: float | None = Field(
        description="Trailing stop percentage", default=None
    )

    # Price-level criteria (calculated from entry price)
    take_profit_price_multiplier: float | None = Field(
        description="Price multiplier for take profit", default=None
    )
    stop_loss_price_multiplier: float | None = Field(
        description="Price multiplier for stop loss", default=None
    )

    # Time-based criteria
    max_holding_days: int | None = Field(
        description="Maximum holding period", default=None
    )
    min_holding_days: int | None = Field(
        description="Minimum holding period", default=None
    )

    # VaR-based criteria
    var_threshold_pct: float | None = Field(
        description="VaR threshold percentage", default=None
    )
    var_lookback_days: int | None = Field(
        description="VaR calculation lookback", default=None
    )

    # Multi-condition logic
    condition_logic: str | None = Field(
        description="Logic for multi-condition exits", default=None
    )
    priority: int = Field(description="Exit criteria priority", ge=1, default=1)


class StrategyParameters(BaseModel):
    """Complete parameter set for a strategy"""

    strategy_name: str = Field(description="Strategy identifier")
    ticker: str = Field(description="Asset ticker")

    # Primary exit criteria
    exit_criteria: list[DeterministicExitCriteria] = Field(
        description="List of exit criteria"
    )

    # Statistical derivation metadata
    confidence_level: float = Field(description="Confidence level used", ge=0, le=1)
    sample_size: int = Field(description="Sample size for derivation", gt=0)
    statistical_validity: ConfidenceLevel = Field(description="Statistical validity")

    # Market context
    market_regime: MarketRegime | None = Field(
        description="Market regime classification", default=None
    )
    volatility_adjustment: float = Field(
        description="Volatility adjustment factor", default=1.0
    )

    # Derivation source
    derived_from_percentile: float = Field(
        description="Source percentile", ge=0, le=100
    )
    data_source: DataSource = Field(description="Primary data source")
    analysis_timeframes: list[str] = Field(description="Timeframes included")

    # Quality indicators
    parameter_stability_score: float = Field(
        description="Parameter stability across timeframes", ge=0, le=1
    )
    out_of_sample_validated: bool = Field(
        description="Out-of-sample validation status", default=False
    )

    class Config:
        use_enum_values = True


class VectorBTParameters(BaseModel):
    """VectorBT-specific parameter format"""

    strategy_name: str = Field(description="Strategy identifier")

    # Core parameters
    take_profit: float = Field(description="Take profit as decimal", gt=0)
    stop_loss: float = Field(description="Stop loss as decimal", gt=0)
    max_holding_days: int = Field(description="Maximum holding days", gt=0)
    trailing_stop: float = Field(description="Trailing stop as decimal", gt=0)
    min_holding_days: int = Field(description="Minimum holding days", ge=0)

    # VectorBT-specific settings
    size_type: str = Field(description="Position sizing type", default="percent")
    direction: str = Field(description="Trade direction", default="longonly")
    conflict_mode: str = Field(
        description="Signal conflict resolution", default="opposite"
    )

    # Fees and slippage
    fees: float = Field(description="Trading fees", ge=0, default=0.001)
    slippage: float = Field(description="Slippage assumption", ge=0, default=0.0005)

    # Additional metadata
    confidence: float = Field(description="Parameter confidence", ge=0, le=1)
    framework_version: str = Field(
        description="VectorBT version compatibility", default=">=0.25.0"
    )


class BacktraderParameters(BaseModel):
    """Backtrader-specific parameter format"""

    strategy_name: str = Field(description="Strategy class name")

    # Strategy parameters (for bt.Strategy.params)
    take_profit_pct: float = Field(description="Take profit percentage", gt=0)
    stop_loss_pct: float = Field(description="Stop loss percentage", gt=0)
    max_days: int = Field(description="Maximum holding days", gt=0)
    trailing_pct: float = Field(description="Trailing stop percentage", gt=0)
    min_days: int = Field(description="Minimum holding days", ge=0)

    # Backtrader-specific settings
    stake: int | float = Field(description="Position size", default=1000)
    commission: float = Field(description="Commission rate", ge=0, default=0.001)
    margin: float | None = Field(description="Margin requirement", default=None)
    mult: float = Field(description="Multiplier for futures", default=1.0)

    # Order execution settings
    order_type: str = Field(description="Default order type", default="Market")
    valid_days: int | None = Field(description="Order validity days", default=None)

    # Template generation
    generate_full_strategy: bool = Field(
        description="Generate complete strategy class", default=True
    )
    include_logging: bool = Field(
        description="Include logging in strategy", default=True
    )


class ZiplineParameters(BaseModel):
    """Zipline-specific parameter format"""

    strategy_name: str = Field(description="Algorithm identifier")

    # Algorithm parameters
    take_profit_threshold: float = Field(description="Take profit threshold", gt=0)
    stop_loss_threshold: float = Field(description="Stop loss threshold", gt=0)
    max_holding_period: int = Field(description="Maximum holding period", gt=0)
    trailing_stop_threshold: float = Field(description="Trailing stop threshold", gt=0)
    min_holding_period: int = Field(description="Minimum holding period", ge=0)

    # Zipline-specific settings
    capital_base: float = Field(description="Starting capital", gt=0, default=100000)
    benchmark: str = Field(description="Benchmark symbol", default="SPY")
    commission_rate: float = Field(description="Commission rate", ge=0, default=0.001)
    slippage_spread: float = Field(description="Slippage spread", ge=0, default=0.0005)

    # Universe and scheduling
    universe: list[str] = Field(description="Trading universe", default_factory=list)
    rebalance_frequency: str = Field(
        description="Rebalancing frequency", default="daily"
    )

    # Risk management
    max_leverage: float = Field(description="Maximum leverage", gt=0, default=1.0)
    max_position_size: float = Field(
        description="Maximum position size", gt=0, le=1, default=0.1
    )


class ParameterValidationResult(BaseModel):
    """Parameter validation results"""

    strategy_name: str = Field(description="Strategy identifier")
    framework: BacktestingFramework = Field(description="Target framework")

    # Validation status
    is_valid: bool = Field(description="Overall validation status")
    validation_errors: list[str] = Field(
        description="Validation error messages", default_factory=list
    )
    validation_warnings: list[str] = Field(
        description="Validation warnings", default_factory=list
    )

    # Parameter checks
    parameter_count: int = Field(description="Number of parameters", ge=0)
    required_parameters_present: bool = Field(description="Required parameters present")
    parameter_ranges_valid: bool = Field(description="Parameter ranges valid")
    logical_consistency_check: bool = Field(description="Logical consistency check")

    # Statistical validation
    sample_size_adequate: bool = Field(description="Sample size adequacy")
    confidence_level_acceptable: bool = Field(description="Confidence level acceptable")
    out_of_sample_tested: bool = Field(description="Out-of-sample testing status")

    # Framework compatibility
    framework_compatible: bool = Field(description="Framework compatibility")
    version_requirements_met: bool = Field(description="Version requirements met")


class ExportTemplate(BaseModel):
    """Template for parameter export"""

    framework: BacktestingFramework = Field(description="Target framework")
    template_type: str = Field(description="Template type (strategy, config, etc.)")

    # Template content
    template_code: str = Field(description="Generated template code")
    imports_required: list[str] = Field(
        description="Required imports", default_factory=list
    )
    dependencies: list[str] = Field(
        description="Package dependencies", default_factory=list
    )

    # Usage instructions
    usage_instructions: str = Field(description="How to use the template")
    example_usage: str | None = Field(description="Example usage code", default=None)

    # Metadata
    generated_timestamp: datetime = Field(description="Generation timestamp")
    template_version: str = Field(description="Template version", default="1.0.0")


class MultiFrameworkExport(BaseModel):
    """Export results for multiple frameworks"""

    strategy_name: str = Field(description="Strategy identifier")
    source_parameters: StrategyParameters = Field(description="Source parameters")

    # Framework-specific exports
    vectorbt_export: VectorBTParameters | None = Field(
        description="VectorBT parameters", default=None
    )
    backtrader_export: BacktraderParameters | None = Field(
        description="Backtrader parameters", default=None
    )
    zipline_export: ZiplineParameters | None = Field(
        description="Zipline parameters", default=None
    )

    # Templates
    vectorbt_template: ExportTemplate | None = Field(
        description="VectorBT template", default=None
    )
    backtrader_template: ExportTemplate | None = Field(
        description="Backtrader template", default=None
    )
    zipline_template: ExportTemplate | None = Field(
        description="Zipline template", default=None
    )

    # Validation results
    validation_results: dict[str, ParameterValidationResult] = Field(
        description="Validation results by framework", default_factory=dict
    )

    # Export summary
    successful_exports: list[BacktestingFramework] = Field(
        description="Successful exports", default_factory=list
    )
    failed_exports: list[BacktestingFramework] = Field(
        description="Failed exports", default_factory=list
    )
    export_timestamp: datetime = Field(description="Export timestamp")


class ParameterSetCollection(BaseModel):
    """Collection of parameter sets with regime classification"""

    base_strategy_name: str = Field(description="Base strategy identifier")

    # Regime-specific parameter sets
    conservative_parameters: StrategyParameters = Field(
        description="Conservative parameter set"
    )
    moderate_parameters: StrategyParameters = Field(
        description="Moderate parameter set"
    )
    aggressive_parameters: StrategyParameters = Field(
        description="Aggressive parameter set"
    )

    # Market regime parameters
    bull_market_parameters: StrategyParameters | None = Field(
        description="Bull market parameters", default=None
    )
    bear_market_parameters: StrategyParameters | None = Field(
        description="Bear market parameters", default=None
    )
    sideways_market_parameters: StrategyParameters | None = Field(
        description="Sideways market parameters", default=None
    )

    # Volatility-adjusted parameters
    high_volatility_parameters: StrategyParameters | None = Field(
        description="High volatility parameters", default=None
    )
    low_volatility_parameters: StrategyParameters | None = Field(
        description="Low volatility parameters", default=None
    )

    # Metadata
    generation_date: datetime = Field(description="Parameter set generation date")
    update_frequency: str = Field(
        description="Recommended update frequency", default="monthly"
    )
    next_review_date: datetime = Field(description="Next review date")

    # Performance tracking
    performance_baseline: dict[str, float] | None = Field(
        description="Performance baseline metrics", default=None
    )
    optimization_target: str = Field(
        description="Primary optimization target", default="exit_efficiency"
    )


class BacktestingConfigExport(BaseModel):
    """Complete backtesting configuration export"""

    export_metadata: dict[str, Any] = Field(description="Export metadata")

    # Strategy parameters
    strategy_parameters: dict[str, ParameterSetCollection] = Field(
        description="Parameters by strategy"
    )

    # Global settings
    global_settings: dict[str, Any] = Field(description="Global backtesting settings")

    # Export files
    file_exports: dict[str, str] = Field(description="Exported file paths by format")

    # Validation summary
    total_strategies: int = Field(description="Total strategies", ge=0)
    valid_strategies: int = Field(description="Valid strategies", ge=0)
    framework_compatibility: dict[str, int] = Field(
        description="Compatibility count by framework"
    )

    # Generation summary
    generation_timestamp: datetime = Field(description="Generation timestamp")
    configuration_hash: str = Field(
        description="Configuration hash for reproducibility"
    )
    spds_version: str = Field(description="SPDS version used")

    class Config:
        use_enum_values = True
