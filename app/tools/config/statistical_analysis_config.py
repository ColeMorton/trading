"""
Statistical Performance Divergence System Configuration

Provides configuration schema and validation for the SPDS with USE_TRADE_HISTORY parameter
for flexible data source selection between equity curves and trade history.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class DataSourceType(str, Enum):
    """Data source type for statistical analysis"""

    EQUITY_CURVES = "equity_curves"
    TRADE_HISTORY = "trade_history"
    HYBRID = "hybrid"


class ConfidenceLevel(str, Enum):
    """Statistical confidence levels based on sample size"""

    HIGH = "HIGH"  # n >= 30
    MEDIUM = "MEDIUM"  # 15 <= n < 30
    LOW = "LOW"  # n < 15


@dataclass
class SPDSConfig:
    """Statistical Performance Divergence System Configuration"""

    # Core Configuration - Simplified Interface
    USE_TRADE_HISTORY: bool = False
    PORTFOLIO: str = ""  # Portfolio filename (e.g., "risk_on.csv")

    # Auto-derived paths based on PORTFOLIO
    PORTFOLIO_PATH: str = "./csv/strategies/"
    TRADE_HISTORY_PATH: str = "./csv/positions/"
    FALLBACK_TO_EQUITY: bool = True

    # Data Source Paths
    EQUITY_DATA_PATHS: List[str] = field(
        default_factory=lambda: [
            "./csv/ma_cross/equity_data/",
            "./csv/macd_cross/equity_data/",
        ]
    )
    RETURN_DISTRIBUTION_PATH: str = "./json/return_distribution/"

    # Statistical Thresholds
    MIN_SAMPLE_SIZE: int = 15
    PREFERRED_SAMPLE_SIZE: int = 30
    OPTIMAL_SAMPLE_SIZE: int = 50

    # Confidence Intervals
    HIGH_CONFIDENCE_THRESHOLD: float = 0.95  # 95% for n >= 30
    MEDIUM_CONFIDENCE_THRESHOLD: float = 0.90  # 90% for 15 <= n < 30
    LOW_CONFIDENCE_THRESHOLD: float = 0.80  # 80% for n < 15

    # Divergence Detection - Complete Entry/Exit Signal System
    PERCENTILE_THRESHOLDS: Dict[str, float] = field(
        default_factory=lambda: {
            # Entry signals (low percentiles = good entry opportunities)
            "strong_buy": 10.0,  # Bottom 10% = excellent entry
            "buy": 20.0,  # Bottom 20% = good entry
            # Neutral range
            "hold": 70.0,  # 20-70% = normal conditions
            # Exit signals (high percentiles = overvalued conditions)
            "sell": 80.0,  # Top 20% = overvalued
            "strong_sell": 90.0,  # Top 10% = significantly overvalued
            "exit_immediately": 95.0,  # Top 5% = extremely overvalued
        }
    )

    # Multi-Timeframe Analysis
    TIMEFRAMES: List[str] = field(default_factory=lambda: ["D", "3D", "W", "2W"])
    CONVERGENCE_THRESHOLD: float = 0.85

    # Dual-Layer Convergence Analysis Configuration
    LAYER_CONVERGENCE_THRESHOLD: float = (
        0.7  # Minimum convergence score for reliable dual-layer analysis
    )
    LAYER_AGREEMENT_THRESHOLD: float = (
        0.75  # Asset + Strategy layer agreement threshold
    )
    SOURCE_AGREEMENT_THRESHOLD: float = (
        0.8  # Threshold for considering data sources in strong agreement
    )
    DIVERGENCE_WARNING_THRESHOLD: float = (
        0.5  # Below this, layers are considered significantly divergent
    )

    # Dual-Layer Analysis Weights
    ASSET_LAYER_WEIGHT: float = 0.5  # Weight for asset distribution analysis
    STRATEGY_LAYER_WEIGHT: float = 0.5  # Weight for strategy performance analysis

    # Data Source Quality Thresholds
    MIN_TRADE_COUNT_FOR_RELIABILITY: int = (
        20  # Minimum trades for reliable trade history analysis
    )
    MIN_EQUITY_PERIODS_FOR_RELIABILITY: int = (
        50  # Minimum periods for reliable equity analysis
    )
    CONVERGENCE_CONFIDENCE_BOOST: float = (
        0.15  # Confidence boost when layers show strong convergence
    )

    # Convergence-Based Exit Signal Adjustments
    CONVERGENCE_SIGNAL_ADJUSTMENT: bool = (
        True  # Enable signal adjustments based on layer convergence
    )
    CONSERVATIVE_MODE_ON_DIVERGENCE: bool = (
        True  # Be more conservative when layers diverge
    )
    AGGRESSIVE_MODE_ON_CONVERGENCE: bool = (
        True  # Be more aggressive when layers strongly converge
    )

    # Bootstrap Validation
    ENABLE_BOOTSTRAP: bool = True
    BOOTSTRAP_ITERATIONS: int = 1000
    BOOTSTRAP_SAMPLE_SIZE: int = 100

    # VaR Calculations
    VAR_CONFIDENCE_LEVELS: List[float] = field(default_factory=lambda: [0.95, 0.99])
    VAR_LOOKBACK_PERIODS: List[int] = field(default_factory=lambda: [30, 60, 90])

    # Performance Optimization
    ENABLE_MEMORY_OPTIMIZATION: bool = True
    CACHE_STATISTICS: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hour

    # Export Configuration
    EXPORT_FORMATS: List[str] = field(default_factory=lambda: ["csv", "json", "python"])
    BACKTESTING_FRAMEWORKS: List[str] = field(
        default_factory=lambda: ["vectorbt", "backtrader", "zipline"]
    )

    # Validation Rules
    REQUIRE_MINIMUM_TRADES: bool = True
    VALIDATE_DATA_QUALITY: bool = True
    STRICT_SAMPLE_SIZE_ENFORCEMENT: bool = False

    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_portfolio()
        self._validate_paths()
        self._validate_thresholds()
        self._validate_sample_sizes()

    def get_portfolio_file_path(self) -> Path:
        """Get full path to portfolio CSV file"""
        if not self.PORTFOLIO:
            raise ValueError("PORTFOLIO parameter must be specified")
        return Path(self.PORTFOLIO_PATH) / self.PORTFOLIO

    def get_trade_history_file_path(self) -> Path:
        """Get full path to trade history CSV file (same filename as portfolio)"""
        if not self.PORTFOLIO:
            raise ValueError("PORTFOLIO parameter must be specified")
        return Path(self.TRADE_HISTORY_PATH) / self.PORTFOLIO

    def _validate_portfolio(self):
        """Validate portfolio configuration"""
        if not self.PORTFOLIO:
            raise ValueError("PORTFOLIO parameter is required (e.g., 'risk_on.csv')")

        # Auto-append .csv extension if not present
        if not self.PORTFOLIO.endswith(".csv"):
            self.PORTFOLIO = self.PORTFOLIO + ".csv"

        # Check if portfolio file exists
        portfolio_file = self.get_portfolio_file_path()
        if not portfolio_file.exists():
            if self.VALIDATE_DATA_QUALITY:
                raise FileNotFoundError(f"Portfolio file not found: {portfolio_file}")

        # Check trade history file if USE_TRADE_HISTORY=True
        if self.USE_TRADE_HISTORY:
            trade_history_file = self.get_trade_history_file_path()
            if not trade_history_file.exists():
                if not self.FALLBACK_TO_EQUITY:
                    raise FileNotFoundError(
                        f"Trade history file not found: {trade_history_file}"
                    )
                else:
                    print(
                        f"Warning: Trade history file not found ({trade_history_file}), will fallback to equity data"
                    )

    def _validate_paths(self):
        """Validate that specified paths exist or can be created"""
        paths_to_check = [
            self.PORTFOLIO_PATH,
            self.TRADE_HISTORY_PATH,
            self.RETURN_DISTRIBUTION_PATH,
        ] + self.EQUITY_DATA_PATHS

        for path_str in paths_to_check:
            path = Path(path_str)
            if not path.exists():
                # Try to create directory if it doesn't exist
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    if self.VALIDATE_DATA_QUALITY:
                        raise ValueError(
                            f"Cannot access or create path {path_str}: {e}"
                        )

    def _validate_thresholds(self):
        """Validate threshold values are within valid ranges"""
        for threshold_name, value in self.PERCENTILE_THRESHOLDS.items():
            if not 0 <= value <= 100:
                raise ValueError(
                    f"Percentile threshold {threshold_name} must be between 0 and 100, got {value}"
                )

        # Validate threshold ranges and logical ordering
        # Entry signals should be low percentiles, exit signals should be high percentiles
        entry_thresholds = {
            k: v
            for k, v in self.PERCENTILE_THRESHOLDS.items()
            if k in ["strong_buy", "buy"]
        }
        exit_thresholds = {
            k: v
            for k, v in self.PERCENTILE_THRESHOLDS.items()
            if k in ["sell", "strong_sell", "exit_immediately"]
        }

        # Entry thresholds should be in ascending order (strong_buy < buy)
        if entry_thresholds:
            entry_values = [
                entry_thresholds.get("strong_buy", 0),
                entry_thresholds.get("buy", 0),
            ]
            if len(entry_values) > 1 and entry_values[0] > entry_values[1]:
                raise ValueError(
                    "Entry signal thresholds must be in ascending order (strong_buy <= buy)"
                )

        # Exit thresholds should be in ascending order (sell < strong_sell < exit_immediately)
        if exit_thresholds:
            exit_values = [
                exit_thresholds.get("sell", 100),
                exit_thresholds.get("strong_sell", 100),
                exit_thresholds.get("exit_immediately", 100),
            ]
            if exit_values != sorted(exit_values):
                raise ValueError(
                    "Exit signal thresholds must be in ascending order (sell <= strong_sell <= exit_immediately)"
                )

        # Ensure entry thresholds are below hold threshold and exit thresholds are above hold threshold
        hold_threshold = self.PERCENTILE_THRESHOLDS.get("hold", 70.0)
        for name, value in entry_thresholds.items():
            if value >= hold_threshold:
                raise ValueError(
                    f"Entry threshold {name} ({value}) must be below hold threshold ({hold_threshold})"
                )

        for name, value in exit_thresholds.items():
            if value <= hold_threshold:
                raise ValueError(
                    f"Exit threshold {name} ({value}) must be above hold threshold ({hold_threshold})"
                )

        # Validate confidence thresholds
        for conf_name, conf_value in [
            ("HIGH_CONFIDENCE_THRESHOLD", self.HIGH_CONFIDENCE_THRESHOLD),
            ("MEDIUM_CONFIDENCE_THRESHOLD", self.MEDIUM_CONFIDENCE_THRESHOLD),
            ("LOW_CONFIDENCE_THRESHOLD", self.LOW_CONFIDENCE_THRESHOLD),
        ]:
            if not 0 < conf_value <= 1:
                raise ValueError(
                    f"{conf_name} must be between 0 and 1, got {conf_value}"
                )

    def _validate_sample_sizes(self):
        """Validate sample size thresholds are logical"""
        if not (
            self.MIN_SAMPLE_SIZE
            <= self.PREFERRED_SAMPLE_SIZE
            <= self.OPTIMAL_SAMPLE_SIZE
        ):
            raise ValueError(
                "Sample size thresholds must be: MIN <= PREFERRED <= OPTIMAL"
            )

        if self.MIN_SAMPLE_SIZE < 5:
            raise ValueError(
                "Minimum sample size must be at least 5 for basic statistical validity"
            )

    def get_confidence_level(self, sample_size: int) -> ConfidenceLevel:
        """Determine confidence level based on sample size"""
        if sample_size >= self.PREFERRED_SAMPLE_SIZE:
            return ConfidenceLevel.HIGH
        elif sample_size >= self.MIN_SAMPLE_SIZE:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def get_confidence_threshold(self, sample_size: int) -> float:
        """Get confidence threshold based on sample size"""
        confidence_level = self.get_confidence_level(sample_size)

        if confidence_level == ConfidenceLevel.HIGH:
            return self.HIGH_CONFIDENCE_THRESHOLD
        elif confidence_level == ConfidenceLevel.MEDIUM:
            return self.MEDIUM_CONFIDENCE_THRESHOLD
        else:
            return self.LOW_CONFIDENCE_THRESHOLD

    def get_data_source_type(self) -> DataSourceType:
        """Determine the primary data source type"""
        if self.USE_TRADE_HISTORY and self.FALLBACK_TO_EQUITY:
            return DataSourceType.HYBRID
        elif self.USE_TRADE_HISTORY:
            return DataSourceType.TRADE_HISTORY
        else:
            return DataSourceType.EQUITY_CURVES

    def should_use_bootstrap(self, sample_size: int) -> bool:
        """Determine if bootstrap validation should be used"""
        return (
            self.ENABLE_BOOTSTRAP
            and sample_size < self.PREFERRED_SAMPLE_SIZE
            and sample_size >= self.MIN_SAMPLE_SIZE
        )

    def get_percentile_threshold(self, signal_type: str) -> float:
        """Get percentile threshold for a specific signal type"""
        return self.PERCENTILE_THRESHOLDS.get(
            signal_type, self.PERCENTILE_THRESHOLDS["hold"]
        )

    def validate_framework_support(self, framework: str) -> bool:
        """Check if a backtesting framework is supported"""
        return framework.lower() in [fw.lower() for fw in self.BACKTESTING_FRAMEWORKS]

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SPDSConfig":
        """Create configuration from dictionary"""
        # Filter out keys that aren't valid fields
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_fields}
        return cls(**filtered_dict)

    @classmethod
    def default_config(cls) -> "SPDSConfig":
        """Create default configuration"""
        return cls()

    @classmethod
    def for_portfolio(
        cls, portfolio: str, use_trade_history: bool = True
    ) -> "SPDSConfig":
        """Create configuration for a specific portfolio - SIMPLIFIED INTERFACE"""
        return cls(
            PORTFOLIO=portfolio,
            USE_TRADE_HISTORY=use_trade_history,
            FALLBACK_TO_EQUITY=True,
            VALIDATE_DATA_QUALITY=False,  # More lenient for ease of use
        )

    @classmethod
    def production_config(cls, portfolio: str = "") -> "SPDSConfig":
        """Create production-optimized configuration"""
        return cls(
            PORTFOLIO=portfolio,
            USE_TRADE_HISTORY=True,
            ENABLE_BOOTSTRAP=True,
            ENABLE_MEMORY_OPTIMIZATION=True,
            CACHE_STATISTICS=True,
            VALIDATE_DATA_QUALITY=True,
            STRICT_SAMPLE_SIZE_ENFORCEMENT=True,
            MIN_SAMPLE_SIZE=20,
            PREFERRED_SAMPLE_SIZE=30,
            OPTIMAL_SAMPLE_SIZE=50,
        )

    @classmethod
    def development_config(cls, portfolio: str = "test.csv") -> "SPDSConfig":
        """Create development-friendly configuration"""
        return cls(
            PORTFOLIO=portfolio,
            USE_TRADE_HISTORY=False,
            FALLBACK_TO_EQUITY=True,
            ENABLE_BOOTSTRAP=False,
            VALIDATE_DATA_QUALITY=False,
            STRICT_SAMPLE_SIZE_ENFORCEMENT=False,
            MIN_SAMPLE_SIZE=10,
            CACHE_STATISTICS=False,
        )


def load_spds_config(config_path: Optional[str] = None) -> SPDSConfig:
    """
    Load SPDS configuration from file or environment variables

    Args:
        config_path: Optional path to configuration file

    Returns:
        SPDSConfig instance
    """
    if config_path and Path(config_path).exists():
        # Load from file (JSON/YAML support could be added here)
        import json

        with open(config_path, "r") as f:
            config_dict = json.load(f)
        return SPDSConfig.from_dict(config_dict)

    # Load from environment variables
    env_config = {}

    # Boolean environment variables
    bool_vars = {
        "SPDS_USE_TRADE_HISTORY": "USE_TRADE_HISTORY",
        "SPDS_FALLBACK_TO_EQUITY": "FALLBACK_TO_EQUITY",
        "SPDS_ENABLE_BOOTSTRAP": "ENABLE_BOOTSTRAP",
        "SPDS_ENABLE_MEMORY_OPTIMIZATION": "ENABLE_MEMORY_OPTIMIZATION",
        "SPDS_CACHE_STATISTICS": "CACHE_STATISTICS",
    }

    for env_var, config_key in bool_vars.items():
        if env_var in os.environ:
            env_config[config_key] = os.environ[env_var].lower() in ("true", "1", "yes")

    # String environment variables
    str_vars = {
        "SPDS_PORTFOLIO": "PORTFOLIO",
        "SPDS_PORTFOLIO_PATH": "PORTFOLIO_PATH",
        "SPDS_TRADE_HISTORY_PATH": "TRADE_HISTORY_PATH",
        "SPDS_RETURN_DISTRIBUTION_PATH": "RETURN_DISTRIBUTION_PATH",
    }

    for env_var, config_key in str_vars.items():
        if env_var in os.environ:
            env_config[config_key] = os.environ[env_var]

    # Integer environment variables
    int_vars = {
        "SPDS_MIN_SAMPLE_SIZE": "MIN_SAMPLE_SIZE",
        "SPDS_PREFERRED_SAMPLE_SIZE": "PREFERRED_SAMPLE_SIZE",
        "SPDS_OPTIMAL_SAMPLE_SIZE": "OPTIMAL_SAMPLE_SIZE",
    }

    for env_var, config_key in int_vars.items():
        if env_var in os.environ:
            try:
                env_config[config_key] = int(os.environ[env_var])
            except ValueError:
                pass  # Use default value

    if env_config:
        return SPDSConfig.from_dict(env_config)
    else:
        return SPDSConfig.default_config()


# Global configuration instance
_spds_config: Optional[SPDSConfig] = None


def get_spds_config() -> SPDSConfig:
    """Get global SPDS configuration instance"""
    global _spds_config
    if _spds_config is None:
        _spds_config = load_spds_config()
    return _spds_config


def set_spds_config(config: SPDSConfig):
    """Set global SPDS configuration instance"""
    global _spds_config
    _spds_config = config


def reset_spds_config():
    """Reset global SPDS configuration to default"""
    global _spds_config
    _spds_config = None


# Simplified Configuration Interface
# ===================================


class StatisticalAnalysisConfig:
    """Simplified interface for Statistical Performance Divergence System"""

    @staticmethod
    def create(portfolio: str, use_trade_history: bool = True) -> SPDSConfig:
        """
        Create configuration with simplified interface.

        Args:
            portfolio: Portfolio filename (e.g., "risk_on.csv")
            use_trade_history: Whether to use trade history data (True) or equity curves (False)

        Returns:
            SPDSConfig configured for the specified portfolio

        Example:
            # Use trade history for risk_on portfolio
            config = StatisticalAnalysisConfig.create("risk_on.csv", use_trade_history=True)

            # Fallback to equity curves
            config = StatisticalAnalysisConfig.create("conservative.csv", use_trade_history=False)
        """
        return SPDSConfig.for_portfolio(portfolio, use_trade_history)


# Usage Examples
# ==============

if __name__ == "__main__":
    # Example 1: Simple portfolio with trade history
    config1 = StatisticalAnalysisConfig.create("risk_on.csv", use_trade_history=True)
    print(f"Portfolio file: {config1.get_portfolio_file_path()}")
    print(f"Trade history file: {config1.get_trade_history_file_path()}")

    # Example 2: Portfolio with equity curve fallback
    config2 = StatisticalAnalysisConfig.create(
        "conservative.csv", use_trade_history=False
    )
    print(f"Portfolio file: {config2.get_portfolio_file_path()}")
    print(f"Using trade history: {config2.USE_TRADE_HISTORY}")

    # Example 3: Production configuration
    prod_config = SPDSConfig.production_config("production_portfolio.csv")
    print(f"Production config for: {prod_config.PORTFOLIO}")
