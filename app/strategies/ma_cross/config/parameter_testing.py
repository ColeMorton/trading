"""
Parameter Testing Configuration

Centralized configuration management for MA Cross parameter testing.
Provides comprehensive validation and type-safe configuration handling.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationSeverity(Enum):
    """Validation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    is_valid: bool
    messages: list[dict[str, str]] = field(default_factory=list)

    def add_error(self, message: str, field: str = ""):
        """Add an error message."""
        self.is_valid = False
        self.messages.append(
            {
                "severity": ValidationSeverity.ERROR.value,
                "message": message,
                "field": field,
            },
        )

    def add_warning(self, message: str, field: str = ""):
        """Add a warning message."""
        self.messages.append(
            {
                "severity": ValidationSeverity.WARNING.value,
                "message": message,
                "field": field,
            },
        )

    def add_info(self, message: str, field: str = ""):
        """Add an info message."""
        self.messages.append(
            {
                "severity": ValidationSeverity.INFO.value,
                "message": message,
                "field": field,
            },
        )


@dataclass
class FilterCriteria:
    """Portfolio filtering criteria."""

    min_win_rate: float | None = None
    min_trades: int | None = None
    min_expectancy_per_trade: float | None = None
    min_profit_factor: float | None = None
    min_sortino_ratio: float | None = None
    min_score: float | None = None
    min_beats_bnh: float | None = None
    max_drawdown: float | None = None
    min_annual_return: float | None = None
    min_sharpe_ratio: float | None = None
    require_signal_entry: bool = False
    exclude_open_trades: bool = False
    metric_types: list[str] = field(default_factory=list)

    def validate(self) -> ValidationResult:
        """Validate filter criteria."""
        result = ValidationResult(is_valid=True)

        # Validate win rate
        if self.min_win_rate is not None:
            if self.min_win_rate < 0 or self.min_win_rate > 1:
                result.add_error("Win rate must be between 0 and 1", "min_win_rate")

        # Validate trades
        if self.min_trades is not None and self.min_trades < 0:
            result.add_error("Minimum trades must be non-negative", "min_trades")

        # Validate profit factor
        if self.min_profit_factor is not None and self.min_profit_factor < 0:
            result.add_error(
                "Minimum profit factor must be non-negative",
                "min_profit_factor",
            )

        # Validate Sortino ratio
        if self.min_sortino_ratio is not None and self.min_sortino_ratio < -10:
            result.add_warning("Very low Sortino ratio threshold", "min_sortino_ratio")

        # Validate max drawdown
        if self.max_drawdown is not None:
            if self.max_drawdown > 0:
                result.add_warning(
                    "Max drawdown should typically be negative",
                    "max_drawdown",
                )
            if abs(self.max_drawdown) > 100:
                result.add_error("Max drawdown cannot exceed 100%", "max_drawdown")

        return result


@dataclass
class ExportOptions:
    """Export configuration options."""

    export_csv: bool = True
    export_json: bool = False
    include_summary: bool = True
    max_results: int = 100
    filename_prefix: str = "ma_cross_analysis"
    export_directory: str | None = None

    def validate(self) -> ValidationResult:
        """Validate export options."""
        result = ValidationResult(is_valid=True)

        # Validate max results
        if self.max_results <= 0:
            result.add_error("Max results must be positive", "max_results")
        elif self.max_results > 10000:
            result.add_warning(
                "Large result sets may impact performance",
                "max_results",
            )

        # Validate filename prefix
        if not self.filename_prefix or not self.filename_prefix.strip():
            result.add_error("Filename prefix cannot be empty", "filename_prefix")

        return result


@dataclass
class ExecutionOptions:
    """Execution configuration options."""

    use_concurrent: bool | None = None  # Auto-detect based on ticker count
    max_workers: int = 4
    timeout_seconds: int = 3600
    enable_progress_tracking: bool = True
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600

    def validate(self) -> ValidationResult:
        """Validate execution options."""
        result = ValidationResult(is_valid=True)

        # Validate max workers
        if self.max_workers <= 0:
            result.add_error("Max workers must be positive", "max_workers")
        elif self.max_workers > 16:
            result.add_warning(
                "High worker count may not improve performance",
                "max_workers",
            )

        # Validate timeout
        if self.timeout_seconds <= 0:
            result.add_error("Timeout must be positive", "timeout_seconds")
        elif self.timeout_seconds > 7200:  # 2 hours
            result.add_warning(
                "Very long timeout may cause resource issues",
                "timeout_seconds",
            )

        # Validate cache TTL
        if self.cache_ttl_seconds < 0:
            result.add_error("Cache TTL cannot be negative", "cache_ttl_seconds")

        return result


@dataclass
class ParameterTestingConfig:
    """
    Comprehensive configuration for MA Cross parameter testing.

    This class provides a centralized, type-safe way to configure all aspects
    of parameter sensitivity testing including tickers, windows, strategies,
    filtering, and export options.
    """

    # Core parameters
    tickers: list[str]
    windows: int
    strategy_types: list[str]
    direction: str = "Long"

    # Optional parameters
    use_hourly: bool = False
    use_years: bool = False
    years: int | None = None
    use_synthetic: bool = False
    ticker_1: str | None = None
    ticker_2: str | None = None

    # Configuration objects
    filters: FilterCriteria = field(default_factory=FilterCriteria)
    export_options: ExportOptions = field(default_factory=ExportOptions)
    execution_options: ExecutionOptions = field(default_factory=ExecutionOptions)

    # Sorting options
    sort_by: str = "Total Return [%]"
    sort_ascending: bool = False

    # System options
    base_directory: str = "/Users/colemorton/Projects/trading"

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "ParameterTestingConfig":
        """
        Create configuration from dictionary.

        Args:
            config_dict: Dictionary with configuration values

        Returns:
            ParameterTestingConfig instance
        """
        # Extract core parameters
        tickers = config_dict.get("TICKER", [])
        if isinstance(tickers, str):
            tickers = [tickers]

        # Extract filter criteria
        minimums = config_dict.get("MINIMUMS", {})
        filters = FilterCriteria(
            min_win_rate=minimums.get("WIN_RATE"),
            min_trades=minimums.get("TRADES"),
            min_expectancy_per_trade=minimums.get("EXPECTANCY_PER_TRADE"),
            min_profit_factor=minimums.get("PROFIT_FACTOR"),
            min_sortino_ratio=minimums.get("SORTINO_RATIO"),
            min_score=minimums.get("SCORE"),
            min_beats_bnh=minimums.get("BEATS_BNH"),
        )

        # Extract export options
        export_options = ExportOptions(
            export_csv=config_dict.get("EXPORT_CSV", True),
            export_json=config_dict.get("EXPORT_JSON", False),
            max_results=config_dict.get("MAX_RESULTS", 100),
            filename_prefix=config_dict.get("FILENAME_PREFIX", "ma_cross_analysis"),
        )

        # Extract execution options
        execution_options = ExecutionOptions(
            max_workers=config_dict.get("MAX_WORKERS", 4),
            timeout_seconds=config_dict.get("TIMEOUT_SECONDS", 3600),
            enable_caching=config_dict.get("ENABLE_CACHING", True),
        )

        return cls(
            tickers=tickers,
            windows=config_dict.get("WINDOWS", 20),
            strategy_types=config_dict.get("STRATEGY_TYPES", ["SMA"]),
            direction=config_dict.get("DIRECTION", "Long"),
            use_hourly=config_dict.get("USE_HOURLY", False),
            use_years=config_dict.get("USE_YEARS", False),
            years=config_dict.get("YEARS"),
            use_synthetic=config_dict.get("USE_SYNTHETIC", False),
            ticker_1=config_dict.get("TICKER_1"),
            ticker_2=config_dict.get("TICKER_2"),
            filters=filters,
            export_options=export_options,
            execution_options=execution_options,
            sort_by=config_dict.get("SORT_BY", "Total Return [%]"),
            sort_ascending=config_dict.get("SORT_ASC", False),
            base_directory=config_dict.get(
                "BASE_DIR",
                "/Users/colemorton/Projects/trading",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to dictionary format.

        Returns:
            Dictionary representation of configuration
        """
        config_dict = {
            "TICKER": self.tickers,
            "WINDOWS": self.windows,
            "STRATEGY_TYPES": self.strategy_types,
            "DIRECTION": self.direction,
            "USE_HOURLY": self.use_hourly,
            "USE_YEARS": self.use_years,
            "YEARS": self.years,
            "USE_SYNTHETIC": self.use_synthetic,
            "TICKER_1": self.ticker_1,
            "TICKER_2": self.ticker_2,
            "SORT_BY": self.sort_by,
            "SORT_ASC": self.sort_ascending,
            "BASE_DIR": self.base_directory,
        }

        # Add minimums
        minimums = {}
        if self.filters.min_win_rate is not None:
            minimums["WIN_RATE"] = self.filters.min_win_rate
        if self.filters.min_trades is not None:
            minimums["TRADES"] = self.filters.min_trades
        if self.filters.min_expectancy_per_trade is not None:
            minimums["EXPECTANCY_PER_TRADE"] = self.filters.min_expectancy_per_trade
        if self.filters.min_profit_factor is not None:
            minimums["PROFIT_FACTOR"] = self.filters.min_profit_factor
        if self.filters.min_sortino_ratio is not None:
            minimums["SORTINO_RATIO"] = self.filters.min_sortino_ratio
        if self.filters.min_score is not None:
            minimums["SCORE"] = self.filters.min_score
        if self.filters.min_beats_bnh is not None:
            minimums["BEATS_BNH"] = self.filters.min_beats_bnh

        if minimums:
            config_dict["MINIMUMS"] = minimums

        return config_dict

    def validate(self) -> ValidationResult:
        """
        Comprehensive validation of all configuration options.

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(is_valid=True)

        # Validate tickers
        if not self.tickers:
            result.add_error("At least one ticker must be specified", "tickers")
        else:
            for ticker in self.tickers:
                if not isinstance(ticker, str) or not ticker.strip():
                    result.add_error(f"Invalid ticker: {ticker}", "tickers")
                elif len(ticker) > 10:
                    result.add_warning(
                        f"Unusually long ticker symbol: {ticker}",
                        "tickers",
                    )

        # Validate windows
        if self.windows < 2:
            result.add_error("Windows must be at least 2", "windows")
        elif self.windows > 500:
            result.add_error("Windows cannot exceed 500", "windows")
        elif self.windows > 200:
            result.add_warning(
                "Large window sizes may reduce signal frequency",
                "windows",
            )

        # Validate strategy types
        valid_strategies = {"SMA", "EMA"}
        if not self.strategy_types:
            result.add_error(
                "At least one strategy type must be specified",
                "strategy_types",
            )
        else:
            invalid_strategies = set(self.strategy_types) - valid_strategies
            if invalid_strategies:
                result.add_error(
                    f"Invalid strategy types: {invalid_strategies}",
                    "strategy_types",
                )

        # Validate direction
        if self.direction not in ["Long", "Short"]:
            result.add_error("Direction must be 'Long' or 'Short'", "direction")

        # Validate years if using years
        if self.use_years:
            if self.years is None:
                result.add_error(
                    "Years must be specified when use_years is True",
                    "years",
                )
            elif self.years <= 0:
                result.add_error("Years must be positive", "years")
            elif self.years > 20:
                result.add_warning(
                    "Large year ranges may require significant data",
                    "years",
                )

        # Validate synthetic ticker configuration
        if self.use_synthetic and (not self.ticker_1 or not self.ticker_2):
            result.add_error(
                "Both ticker_1 and ticker_2 must be specified for synthetic tickers",
                "synthetic",
            )

        # Validate sort field
        valid_sort_fields = {
            "Total Return [%]",
            "Ann. Return [%]",
            "Sharpe Ratio",
            "Sortino Ratio",
            "Win Rate [%]",
            "Profit Factor",
            "Expectancy",
            "Score",
            "Total Trades",
        }
        if self.sort_by not in valid_sort_fields:
            result.add_warning(f"Unusual sort field: {self.sort_by}", "sort_by")

        # Validate component configurations
        filter_result = self.filters.validate()
        if not filter_result.is_valid:
            result.is_valid = False
        result.messages.extend(filter_result.messages)

        export_result = self.export_options.validate()
        if not export_result.is_valid:
            result.is_valid = False
        result.messages.extend(export_result.messages)

        execution_result = self.execution_options.validate()
        if not execution_result.is_valid:
            result.is_valid = False
        result.messages.extend(execution_result.messages)

        # Add optimization suggestions
        if len(self.tickers) > 10:
            result.add_info(
                f"Large ticker set ({len(self.tickers)} tickers) will benefit from concurrent execution",
                "performance",
            )

        if len(self.strategy_types) > 2:
            result.add_info(
                f"Multiple strategies ({len(self.strategy_types)}) will increase execution time",
                "performance",
            )

        return result

    def get_execution_summary(self) -> dict[str, Any]:
        """
        Get a summary of the execution configuration.

        Returns:
            Dictionary with execution summary information
        """
        return {
            "ticker_count": len(self.tickers),
            "strategy_count": len(self.strategy_types),
            "window_size": self.windows,
            "uses_concurrent": self.execution_options.use_concurrent
            or len(self.tickers) > 2,
            "has_filters": any(
                [
                    self.filters.min_win_rate is not None,
                    self.filters.min_trades is not None,
                    self.filters.min_expectancy_per_trade is not None,
                    self.filters.min_profit_factor is not None,
                    self.filters.min_sortino_ratio is not None,
                ],
            ),
            "export_formats": [
                format_name
                for format_name, enabled in [
                    ("csv", self.export_options.export_csv),
                    ("json", self.export_options.export_json),
                ]
                if enabled
            ],
            "estimated_combinations": len(self.tickers) * len(self.strategy_types),
        }
