"""
Configuration Template System

Provides template-based configuration generation for new strategies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


def to_pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase.

    Args:
        snake_str: String in snake_case format

    Returns:
        String in PascalCase format

    Example:
        test_execution -> TestExecution
        sma -> Sma
    """
    return "".join(word.capitalize() for word in snake_str.split("_"))


def to_title_case(snake_str: str) -> str:
    """Convert snake_case to Title Case With Spaces.

    Args:
        snake_str: String in snake_case format

    Returns:
        String in Title Case format with spaces

    Example:
        test_execution -> Test Execution
        comprehensive_test -> Comprehensive Test
    """
    return " ".join(word.capitalize() for word in snake_str.split("_"))


class StrategyType(Enum):
    """Supported strategy types for template generation."""

    MOVING_AVERAGE = "moving_average"
    RSI = "rsi"
    BOLLINGER_BANDS = "bollinger_bands"
    STOCHASTIC = "stochastic"
    MACD = "macd"
    MOMENTUM = "momentum"
    CUSTOM = "custom"


class IndicatorType(Enum):
    """Supported technical indicators."""

    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER = "bollinger"
    STOCHASTIC = "stochastic"
    ATR = "atr"
    VOLUME = "volume"


@dataclass
class TemplateConfig:
    """Configuration for strategy template generation."""

    # Basic Strategy Information
    strategy_name: str
    strategy_type: StrategyType
    description: str

    # Technical Indicators
    primary_indicator: IndicatorType
    secondary_indicators: list[IndicatorType]

    # Signal Generation
    entry_conditions: list[str]
    exit_conditions: list[str]

    # Risk Management
    stop_loss_enabled: bool = True
    take_profit_enabled: bool = True
    position_sizing: str = "fixed"  # "fixed", "percentage", "kelly"

    # Backtesting Parameters
    default_ticker: str = "AAPL"
    default_timeframe: str = "daily"
    default_lookback_period: int = 252

    # Configuration Fields
    config_fields: dict[str, Any] = None

    # Advanced Options
    use_machine_learning: bool = False
    multi_asset: bool = False
    intraday_support: bool = False

    def __post_init__(self):
        """Initialize default configuration fields if not provided."""
        if self.config_fields is None:
            self.config_fields = self._generate_default_config()

    def _generate_default_config(self) -> dict[str, Any]:
        """Generate default configuration based on strategy type."""
        base_config = {
            "TICKER": [self.default_ticker],
            "BASE_DIR": "get_project_root()",
            "REFRESH": True,
            "DIRECTION": "Long",
            "USE_CURRENT": True,
            "SORT_BY": "Score",
            "SORT_ASC": False,
            "USE_YEARS": False,
            "YEARS": 5,
        }

        # Add strategy-specific parameters
        if self.strategy_type == StrategyType.MOVING_AVERAGE:
            base_config.update(
                {
                    "FAST_PERIOD": 20,
                    "SLOW_PERIOD": 50,
                    "STRATEGY_TYPES": ["SMA", "EMA"],
                },
            )
        elif self.strategy_type == StrategyType.RSI:
            base_config.update(
                {
                    "RSI_PERIOD": 14,
                    "RSI_OVERBOUGHT": 70,
                    "RSI_OVERSOLD": 30,
                },
            )
        elif self.strategy_type == StrategyType.BOLLINGER_BANDS:
            base_config.update(
                {
                    "BB_PERIOD": 20,
                    "BB_STD_DEV": 2.0,
                },
            )
        elif self.strategy_type == StrategyType.STOCHASTIC:
            base_config.update(
                {
                    "STOCH_K_PERIOD": 14,
                    "STOCH_D_PERIOD": 3,
                    "STOCH_OVERBOUGHT": 80,
                    "STOCH_OVERSOLD": 20,
                },
            )
        elif self.strategy_type == StrategyType.MACD:
            base_config.update(
                {
                    "MACD_FAST": 12,
                    "MACD_SLOW": 26,
                    "MACD_SIGNAL": 9,
                },
            )
        elif self.strategy_type == StrategyType.MOMENTUM:
            base_config.update(
                {
                    "MOMENTUM_PERIOD": 10,
                    "MOMENTUM_THRESHOLD": 0.02,
                },
            )

        # Add risk management parameters
        if self.stop_loss_enabled:
            base_config["STOP_LOSS_PCT"] = 0.05

        if self.take_profit_enabled:
            base_config["TAKE_PROFIT_PCT"] = 0.10

        # Add position sizing parameters
        if self.position_sizing == "percentage":
            base_config["POSITION_SIZE_PCT"] = 0.10
        elif self.position_sizing == "kelly":
            base_config["USE_KELLY_CRITERION"] = True

        return base_config

    def get_config_type_definition(self) -> str:
        """Generate TypedDict definition for the configuration."""
        config_lines = ["from typing import TypedDict, List, Union, Optional", ""]

        # Generate the TypedDict class
        class_name = f"{to_pascal_case(self.strategy_name)}Config"
        config_lines.append(f"class {class_name}(TypedDict):")
        config_lines.append(
            '    """Configuration for {self.strategy_name} strategy."""',
        )
        config_lines.append("")

        # Add configuration fields with type hints
        for key, value in self.config_fields.items():
            if isinstance(value, str):
                if value == "get_project_root()":
                    config_lines.append(f"    {key}: str")
                else:
                    config_lines.append(f"    {key}: str")
            elif isinstance(value, list):
                if value and isinstance(value[0], str):
                    config_lines.append(f"    {key}: List[str]")
                else:
                    config_lines.append(f"    {key}: List[Union[str, int, float]]")
            elif isinstance(value, bool):
                config_lines.append(f"    {key}: bool")
            elif isinstance(value, int):
                config_lines.append(f"    {key}: int")
            elif isinstance(value, float):
                config_lines.append(f"    {key}: float")
            else:
                config_lines.append(f"    {key}: Union[str, int, float, bool]")

        return "\n".join(config_lines)

    def get_default_config_instance(self) -> str:
        """Generate default configuration instance."""
        lines = [
            f"DEFAULT_CONFIG: {to_pascal_case(self.strategy_name)}Config = {{",
        ]

        for key, value in self.config_fields.items():
            if isinstance(value, str):
                if value == "get_project_root()":
                    lines.append(f'    "{key}": get_project_root(),')
                else:
                    lines.append(f'    "{key}": "{value}",')
            elif isinstance(value, list):
                if value and isinstance(value[0], str):
                    formatted_list = (
                        "[" + ", ".join(f'"{item}"' for item in value) + "]"
                    )
                    lines.append(f'    "{key}": {formatted_list},')
                else:
                    lines.append(f'    "{key}": {value},')
            else:
                lines.append(f'    "{key}": {value},')

        lines.append("}")
        return "\n".join(lines)

    def get_strategy_specific_imports(self) -> list[str]:
        """Get imports specific to this strategy type."""
        imports = []

        if (
            self.primary_indicator == IndicatorType.SMA
            or IndicatorType.SMA in self.secondary_indicators
        ):
            imports.append("from ta.trend import SMAIndicator")

        if (
            self.primary_indicator == IndicatorType.EMA
            or IndicatorType.EMA in self.secondary_indicators
        ):
            imports.append("from ta.trend import EMAIndicator")

        if (
            self.primary_indicator == IndicatorType.RSI
            or IndicatorType.RSI in self.secondary_indicators
        ):
            imports.append("from ta.momentum import RSIIndicator")

        if (
            self.primary_indicator == IndicatorType.MACD
            or IndicatorType.MACD in self.secondary_indicators
        ):
            imports.append("from ta.trend import MACD")

        if (
            self.primary_indicator == IndicatorType.BOLLINGER
            or IndicatorType.BOLLINGER in self.secondary_indicators
        ):
            imports.append("from ta.volatility import BollingerBands")

        if (
            self.primary_indicator == IndicatorType.STOCHASTIC
            or IndicatorType.STOCHASTIC in self.secondary_indicators
        ):
            imports.append("from ta.momentum import StochasticOscillator")

        if (
            self.primary_indicator == IndicatorType.ATR
            or IndicatorType.ATR in self.secondary_indicators
        ):
            imports.append("from ta.volatility import AverageTrueRange")

        return imports
