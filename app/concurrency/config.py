"""Configuration management for concurrency analysis.

This module provides configuration types and validation functions for the concurrency
analysis system, supporting multiple portfolio formats and configurations.
"""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, NotRequired, TypedDict

from app.concurrency.error_handling import ValidationError as BaseValidationError
from app.concurrency.error_handling import (
    handle_concurrency_errors,
    track_error,
    validate_inputs,
)


class ReportIncludesConfig(TypedDict):
    """Configuration for report content inclusion.

    Required Fields:
        STRATEGY_RELATIONSHIPS (bool): Whether to include strategy relationships in the report
        STRATEGIES (bool): Whether to include the strategies object in the report
        TICKER_METRICS (bool): Whether to include ticker-level metrics in the report
    """

    STRATEGY_RELATIONSHIPS: bool
    STRATEGIES: bool
    TICKER_METRICS: NotRequired[bool]


class ConcurrencyConfig(TypedDict):
    """Configuration for concurrency analysis.

    Required Fields:
        PORTFOLIO (str): Portfolio configuration file name
        BASE_DIR (str): Base directory for file operations
        REFRESH (bool): Whether to refresh cached data

    Optional Fields:
        SL_CANDLE_CLOSE (NotRequired[bool]): Use candle close for stop loss
        RATIO_BASED_ALLOCATION (NotRequired[bool]): Enable ratio-based allocation
        CSV_USE_HOURLY (NotRequired[bool]): Use hourly timeframe for CSV strategies
                                           (True for hourly, False for daily)
        REPORT_INCLUDES (NotRequired[ReportIncludesConfig]): Configuration for report content inclusion
        OPTIMIZE (NotRequired[bool]): Whether to run permutation analysis
        OPTIMIZE_MIN_STRATEGIES (NotRequired[int]): Minimum strategies per permutation
        OPTIMIZE_MAX_PERMUTATIONS (NotRequired[int]): Maximum permutations to analyze
    """

    PORTFOLIO: str
    BASE_DIR: str
    REFRESH: bool
    SL_CANDLE_CLOSE: NotRequired[bool]
    RATIO_BASED_ALLOCATION: NotRequired[bool]
    CSV_USE_HOURLY: NotRequired[bool]
    REPORT_INCLUDES: NotRequired[ReportIncludesConfig]
    OPTIMIZE: NotRequired[bool]
    OPTIMIZE_MIN_STRATEGIES: NotRequired[int]
    OPTIMIZE_MAX_PERMUTATIONS: NotRequired[int]


class CsvStrategyRow(TypedDict):
    """CSV strategy row format.

    Required Fields:
        Ticker (str): Trading symbol
        Use SMA (bool): Whether to use SMA (vs EMA)
        Short Window (int): Short moving average period
        Long Window (int): Long moving average period
        Signal Window (int): Signal line period (for MACD)

    Optional Fields:
        strategy_id (NotRequired[str]): Unique strategy identifier
        Allocation [%] (NotRequired[float]): Allocation percentage for the strategy
        Stop Loss [%] (NotRequired[float]): Stop loss percentage for the strategy
    """

    Ticker: str
    Use_SMA: bool
    Short_Window: int
    Long_Window: int
    Signal_Window: int
    strategy_id: NotRequired[str]
    Allocation: NotRequired[float]  # Allocation [%] in CSV header
    Stop_Loss: NotRequired[float]  # Stop Loss [%] in CSV header


class JsonMaStrategy(TypedDict):
    """JSON MA strategy format.

    Required Fields:
        ticker (str): Trading symbol
        timeframe (str): Trading timeframe
        type (str): Strategy type (SMA/EMA)
        direction (str): Trading direction
        short_window (int): Short moving average period
        long_window (int): Long moving average period

    Optional Fields:
        allocation (NotRequired[float]): Allocation percentage for the strategy
        stop_loss (NotRequired[float]): Stop loss percentage
        rsi_period (NotRequired[int]): RSI calculation period
        rsi_threshold (NotRequired[int]): RSI signal threshold
        strategy_id (NotRequired[str]): Unique strategy identifier
    """

    ticker: str
    timeframe: str
    type: str
    direction: str
    short_window: int
    long_window: int
    allocation: NotRequired[float]
    stop_loss: NotRequired[float]
    rsi_period: NotRequired[int]
    rsi_threshold: NotRequired[int]
    strategy_id: NotRequired[str]


class JsonMacdStrategy(TypedDict):
    """JSON MACD strategy format.

    Required Fields:
        ticker (str): Trading symbol
        timeframe (str): Trading timeframe
        type (str): Strategy type (MACD)
        direction (str): Trading direction
        short_window (int): Fast line period
        long_window (int): Slow line period
        signal_window (int): Signal line period

    Optional Fields:
        allocation (NotRequired[float]): Allocation percentage for the strategy
        stop_loss (NotRequired[float]): Stop loss percentage
        rsi_period (NotRequired[int]): RSI calculation period
        rsi_threshold (NotRequired[int]): RSI signal threshold
        strategy_id (NotRequired[str]): Unique strategy identifier
    """

    ticker: str
    timeframe: str
    type: str
    direction: str
    short_window: int
    long_window: int
    signal_window: int
    allocation: NotRequired[float]
    stop_loss: NotRequired[float]
    rsi_period: NotRequired[int]
    rsi_threshold: NotRequired[int]
    strategy_id: NotRequired[str]


class JsonAtrStrategy(TypedDict):
    """JSON ATR Trailing Stop strategy format.

    Required Fields:
        ticker (str): Trading symbol
        timeframe (str): Trading timeframe
        type (str): Strategy type (ATR)
        direction (str): Trading direction
        length (int): ATR calculation period
        multiplier (float): ATR multiplier for stop distance

    Optional Fields:
        allocation (NotRequired[float]): Allocation percentage for the strategy
        stop_loss (NotRequired[float]): Stop loss percentage
        rsi_period (NotRequired[int]): RSI calculation period
        rsi_threshold (NotRequired[int]): RSI signal threshold
        strategy_id (NotRequired[str]): Unique strategy identifier
    """

    ticker: str
    timeframe: str
    type: str
    direction: str
    length: int
    multiplier: float
    allocation: NotRequired[float]
    stop_loss: NotRequired[float]
    rsi_period: NotRequired[int]
    rsi_threshold: NotRequired[int]
    strategy_id: NotRequired[str]


@dataclass
class PortfolioFormat:
    """Portfolio file format information."""

    extension: str
    content_type: str
    validator: callable


class ConfigurationError(BaseValidationError):
    """Base class for configuration-related errors."""


class FileFormatError(ConfigurationError):
    """Raised when file format is invalid or unsupported."""


class ValidationError(ConfigurationError):
    """Raised when configuration validation fails."""


@handle_concurrency_errors("portfolio format detection")
@validate_inputs(file_path=lambda x: isinstance(x, str) and len(x) > 0)
def detect_portfolio_format(file_path: str) -> PortfolioFormat:
    """Detect the format of a portfolio file.

    Args:
        file_path (str): Path to the portfolio file

    Returns:
        PortfolioFormat: Format information for the file

    Raises:
        FileFormatError: If file format is not supported or cannot be detected
    """
    path = Path(file_path)
    if not path.exists():
        error = FileFormatError(f"File not found: {file_path}")
        track_error(error, "portfolio format detection", {"file_path": file_path})
        raise error

    extension = path.suffix.lower()

    if extension == ".csv":
        return PortfolioFormat(
            extension=".csv", content_type="text/csv", validator=validate_csv_portfolio
        )
    elif extension == ".json":
        # Detect JSON subtype by content
        try:
            with open(path) as f:
                data = json.load(f)
                if not isinstance(data, list) or not data:
                    error = FileFormatError("JSON file must contain a non-empty array")
                    track_error(
                        error, "portfolio format detection", {"file_path": file_path}
                    )
                    raise error

                # Use MA validator for all JSON files since it handles both MA and MACD
                return PortfolioFormat(
                    extension=".json",
                    content_type="application/json+mixed",
                    validator=validate_ma_portfolio,
                )
        except json.JSONDecodeError as e:
            error = FileFormatError(f"Invalid JSON file: {str(e)}")
            track_error(
                error,
                "portfolio format detection",
                {"file_path": file_path, "json_error": str(e)},
            )
            raise error
    else:
        error = FileFormatError(f"Unsupported file extension: {extension}")
        track_error(
            error,
            "portfolio format detection",
            {"file_path": file_path, "extension": extension},
        )
        raise error


@handle_concurrency_errors("configuration validation")
@validate_inputs(config=lambda x: isinstance(x, dict))
def validate_config(config: Dict[str, Any]) -> ConcurrencyConfig:
    """Validate concurrency configuration.

    Args:
        config (Dict[str, Any]): Configuration dictionary

    Returns:
        ConcurrencyConfig: Validated configuration

    Raises:
        ValidationError: If configuration is invalid
    """
    required_fields = {"PORTFOLIO", "BASE_DIR", "REFRESH"}
    missing_fields = required_fields - set(config.keys())
    if missing_fields:
        error = ValidationError(f"Missing required fields: {missing_fields}")
        track_error(
            error,
            "configuration validation",
            {
                "missing_fields": list(missing_fields),
                "provided_fields": list(config.keys()),
            },
        )
        raise error

    # Validate types
    if not isinstance(config["PORTFOLIO"], str):
        error = ValidationError("PORTFOLIO must be a string")
        track_error(
            error,
            "configuration validation",
            {"field": "PORTFOLIO", "type": type(config["PORTFOLIO"]).__name__},
        )
        raise error
    if not isinstance(config["BASE_DIR"], str):
        error = ValidationError("BASE_DIR must be a string")
        track_error(
            error,
            "configuration validation",
            {"field": "BASE_DIR", "type": type(config["BASE_DIR"]).__name__},
        )
        raise error
    if not isinstance(config["REFRESH"], bool):
        error = ValidationError("REFRESH must be a boolean")
        track_error(
            error,
            "configuration validation",
            {"field": "REFRESH", "type": type(config["REFRESH"]).__name__},
        )
        raise error

    if "SL_CANDLE_CLOSE" in config and not isinstance(config["SL_CANDLE_CLOSE"], bool):
        error = ValidationError("SL_CANDLE_CLOSE must be a boolean if provided")
        track_error(
            error,
            "configuration validation",
            {
                "field": "SL_CANDLE_CLOSE",
                "type": type(config["SL_CANDLE_CLOSE"]).__name__,
            },
        )
        raise error

    if "RATIO_BASED_ALLOCATION" in config and not isinstance(
        config["RATIO_BASED_ALLOCATION"], bool
    ):
        error = ValidationError("RATIO_BASED_ALLOCATION must be a boolean if provided")
        track_error(
            error,
            "configuration validation",
            {
                "field": "RATIO_BASED_ALLOCATION",
                "type": type(config["RATIO_BASED_ALLOCATION"]).__name__,
            },
        )
        raise error

    if "CSV_USE_HOURLY" in config and not isinstance(config["CSV_USE_HOURLY"], bool):
        error = ValidationError("CSV_USE_HOURLY must be a boolean if provided")
        track_error(
            error,
            "configuration validation",
            {
                "field": "CSV_USE_HOURLY",
                "type": type(config["CSV_USE_HOURLY"]).__name__,
            },
        )
        raise error

    # Validate OPTIMIZE flag (default to False if not present)
    if "OPTIMIZE" in config and not isinstance(config["OPTIMIZE"], bool):
        error = ValidationError("OPTIMIZE must be a boolean")
        track_error(
            error,
            "configuration validation",
            {"field": "OPTIMIZE", "type": type(config["OPTIMIZE"]).__name__},
        )
        raise error
    elif "OPTIMIZE" not in config:
        config["OPTIMIZE"] = False

    # Validate OPTIMIZE_MIN_STRATEGIES (default to 3 if not present)
    if "OPTIMIZE_MIN_STRATEGIES" in config:
        if (
            not isinstance(config["OPTIMIZE_MIN_STRATEGIES"], int)
            or config["OPTIMIZE_MIN_STRATEGIES"] < 2
        ):
            error = ValidationError("OPTIMIZE_MIN_STRATEGIES must be an integer >= 2")
            track_error(
                error,
                "configuration validation",
                {
                    "field": "OPTIMIZE_MIN_STRATEGIES",
                    "value": config["OPTIMIZE_MIN_STRATEGIES"],
                },
            )
            raise error
    else:
        config["OPTIMIZE_MIN_STRATEGIES"] = 3

    # Validate OPTIMIZE_MAX_PERMUTATIONS (default to None if not present)
    if "OPTIMIZE_MAX_PERMUTATIONS" in config:
        if (
            not isinstance(config["OPTIMIZE_MAX_PERMUTATIONS"], int)
            or config["OPTIMIZE_MAX_PERMUTATIONS"] < 1
        ):
            error = ValidationError(
                "OPTIMIZE_MAX_PERMUTATIONS must be a positive integer"
            )
            track_error(
                error,
                "configuration validation",
                {
                    "field": "OPTIMIZE_MAX_PERMUTATIONS",
                    "value": config["OPTIMIZE_MAX_PERMUTATIONS"],
                },
            )
            raise error
    else:
        config["OPTIMIZE_MAX_PERMUTATIONS"] = None

    return config


def validate_csv_portfolio(file_path: str) -> None:
    """Validate CSV portfolio file format.

    Args:
        file_path (str): Path to CSV file

    Raises:
        ValidationError: If CSV format is invalid
    """
    required_fields = {"Ticker", "Use SMA", "Short Window", "Long Window"}

    try:
        with open(file_path, newline="") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])
            missing_fields = required_fields - headers
            if missing_fields:
                raise ValidationError(f"CSV missing required fields: {missing_fields}")

            # Validate first row
            first_row = next(reader, None)
            if not first_row:
                raise ValidationError("CSV file is empty")
    except csv.Error as e:
        raise ValidationError(f"Invalid CSV format: {str(e)}")


def validate_ma_portfolio(file_path: str) -> None:
    """Validate mixed MA/MACD JSON portfolio file format.

    Args:
        file_path (str): Path to JSON file

    Raises:
        ValidationError: If JSON format is invalid
    """
    ma_required_fields = {
        "ticker",
        "timeframe",
        "type",
        "direction",
        "short_window",
        "long_window",
    }
    macd_required_fields = ma_required_fields | {"signal_window"}
    atr_required_fields = {
        "ticker",
        "timeframe",
        "type",
        "direction",
        "length",
        "multiplier",
    }

    try:
        with open(file_path) as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValidationError("JSON must contain an array of strategies")

            for strategy in data:
                if "type" not in strategy:
                    raise ValidationError("Strategy missing 'type' field")

                if strategy["type"] == "MACD":
                    missing_fields = macd_required_fields - set(strategy.keys())
                    if missing_fields:
                        raise ValidationError(
                            f"MACD strategy missing required fields: {missing_fields}"
                        )
                elif strategy["type"] in ("SMA", "EMA"):
                    missing_fields = ma_required_fields - set(strategy.keys())
                    if missing_fields:
                        raise ValidationError(
                            f"MA strategy missing required fields: {missing_fields}"
                        )
                elif strategy["type"] == "ATR":
                    missing_fields = atr_required_fields - set(strategy.keys())
                    if missing_fields:
                        raise ValidationError(
                            f"ATR strategy missing required fields: {missing_fields}"
                        )
                else:
                    raise ValidationError(f"Invalid strategy type: {strategy['type']}")
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}")


def validate_macd_portfolio(file_path: str) -> None:
    """Validate MACD JSON portfolio file format.

    Args:
        file_path (str): Path to JSON file

    Raises:
        ValidationError: If JSON format is invalid
    """
    required_fields = {
        "ticker",
        "timeframe",
        "type",
        "direction",
        "short_window",
        "long_window",
        "signal_window",
    }

    try:
        with open(file_path) as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValidationError("JSON must contain an array of strategies")

            for strategy in data:
                missing_fields = required_fields - set(strategy.keys())
                if missing_fields:
                    raise ValidationError(
                        f"Strategy missing required fields: {missing_fields}"
                    )

                if strategy["type"] != "MACD":
                    raise ValidationError(f"Invalid strategy type: {strategy['type']}")
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}")
