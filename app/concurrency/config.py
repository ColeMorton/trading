"""Configuration management for concurrency analysis.

This module provides configuration types and validation functions for the concurrency
analysis system, supporting multiple portfolio formats and configurations.
"""

from typing import TypedDict, NotRequired, Union, List, Dict, Any
from pathlib import Path
import json
import csv
from dataclasses import dataclass

class ReportIncludesConfig(TypedDict):
    """Configuration for report content inclusion.

    Required Fields:
        STRATEGY_RELATIONSHIPS (bool): Whether to include strategy relationships in the report
        STRATEGIES (bool): Whether to include the strategies object in the report
    """
    STRATEGY_RELATIONSHIPS: bool
    STRATEGIES: bool

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
    """
    PORTFOLIO: str
    BASE_DIR: str
    REFRESH: bool
    SL_CANDLE_CLOSE: NotRequired[bool]
    RATIO_BASED_ALLOCATION: NotRequired[bool]
    CSV_USE_HOURLY: NotRequired[bool]
    REPORT_INCLUDES: NotRequired[ReportIncludesConfig]

class CsvStrategyRow(TypedDict):
    """CSV strategy row format.

    Required Fields:
        Ticker (str): Trading symbol
        Use SMA (bool): Whether to use SMA (vs EMA)
        Short Window (int): Short moving average period
        Long Window (int): Long moving average period
        Signal Window (int): Signal line period (for MACD)
    """
    Ticker: str
    Use_SMA: bool
    Short_Window: int
    Long_Window: int
    Signal_Window: int

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
        stop_loss (NotRequired[float]): Stop loss percentage
        rsi_period (NotRequired[int]): RSI calculation period
        rsi_threshold (NotRequired[int]): RSI signal threshold
    """
    ticker: str
    timeframe: str
    type: str
    direction: str
    short_window: int
    long_window: int
    stop_loss: NotRequired[float]
    rsi_period: NotRequired[int]
    rsi_threshold: NotRequired[int]

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
        stop_loss (NotRequired[float]): Stop loss percentage
        rsi_period (NotRequired[int]): RSI calculation period
        rsi_threshold (NotRequired[int]): RSI signal threshold
    """
    ticker: str
    timeframe: str
    type: str
    direction: str
    short_window: int
    long_window: int
    signal_window: int
    stop_loss: NotRequired[float]
    rsi_period: NotRequired[int]
    rsi_threshold: NotRequired[int]

@dataclass
class PortfolioFormat:
    """Portfolio file format information."""
    extension: str
    content_type: str
    validator: callable

class ConfigurationError(Exception):
    """Base class for configuration-related errors."""
    pass

class FileFormatError(ConfigurationError):
    """Raised when file format is invalid or unsupported."""
    pass

class ValidationError(ConfigurationError):
    """Raised when configuration validation fails."""
    pass

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
        raise FileFormatError(f"File not found: {file_path}")

    extension = path.suffix.lower()
    
    if extension == '.csv':
        return PortfolioFormat(
            extension='.csv',
            content_type='text/csv',
            validator=validate_csv_portfolio
        )
    elif extension == '.json':
        # Detect JSON subtype by content
        try:
            with open(path) as f:
                data = json.load(f)
                if not isinstance(data, list) or not data:
                    raise FileFormatError("JSON file must contain a non-empty array")
                
                # Use MA validator for all JSON files since it handles both MA and MACD
                return PortfolioFormat(
                    extension='.json',
                    content_type='application/json+mixed',
                    validator=validate_ma_portfolio
                )
        except json.JSONDecodeError as e:
            raise FileFormatError(f"Invalid JSON file: {str(e)}")
    else:
        raise FileFormatError(f"Unsupported file extension: {extension}")

def validate_config(config: Dict[str, Any]) -> ConcurrencyConfig:
    """Validate concurrency configuration.

    Args:
        config (Dict[str, Any]): Configuration dictionary

    Returns:
        ConcurrencyConfig: Validated configuration

    Raises:
        ValidationError: If configuration is invalid
    """
    required_fields = {'PORTFOLIO', 'BASE_DIR', 'REFRESH'}
    missing_fields = required_fields - set(config.keys())
    if missing_fields:
        raise ValidationError(f"Missing required fields: {missing_fields}")

    # Validate types
    if not isinstance(config['PORTFOLIO'], str):
        raise ValidationError("PORTFOLIO must be a string")
    if not isinstance(config['BASE_DIR'], str):
        raise ValidationError("BASE_DIR must be a string")
    if not isinstance(config['REFRESH'], bool):
        raise ValidationError("REFRESH must be a boolean")
    
    if 'SL_CANDLE_CLOSE' in config and not isinstance(config['SL_CANDLE_CLOSE'], bool):
        raise ValidationError("SL_CANDLE_CLOSE must be a boolean if provided")
    
    if 'RATIO_BASED_ALLOCATION' in config and not isinstance(config['RATIO_BASED_ALLOCATION'], bool):
        raise ValidationError("RATIO_BASED_ALLOCATION must be a boolean if provided")
    
    if 'CSV_USE_HOURLY' in config and not isinstance(config['CSV_USE_HOURLY'], bool):
        raise ValidationError("CSV_USE_HOURLY must be a boolean if provided")

    return config

def validate_csv_portfolio(file_path: str) -> None:
    """Validate CSV portfolio file format.

    Args:
        file_path (str): Path to CSV file

    Raises:
        ValidationError: If CSV format is invalid
    """
    required_fields = {
        'Ticker', 'Use SMA', 'Short Window', 'Long Window'
    }
    
    try:
        with open(file_path, newline='') as f:
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
        'ticker', 'timeframe', 'type', 'direction',
        'short_window', 'long_window'
    }
    macd_required_fields = ma_required_fields | {'signal_window'}
    
    try:
        with open(file_path) as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValidationError("JSON must contain an array of strategies")
            
            for strategy in data:
                if 'type' not in strategy:
                    raise ValidationError("Strategy missing 'type' field")
                
                if strategy['type'] == 'MACD':
                    missing_fields = macd_required_fields - set(strategy.keys())
                    if missing_fields:
                        raise ValidationError(
                            f"MACD strategy missing required fields: {missing_fields}"
                        )
                elif strategy['type'] in ('SMA', 'EMA'):
                    missing_fields = ma_required_fields - set(strategy.keys())
                    if missing_fields:
                        raise ValidationError(
                            f"MA strategy missing required fields: {missing_fields}"
                        )
                else:
                    raise ValidationError(
                        f"Invalid strategy type: {strategy['type']}"
                    )
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
        'ticker', 'timeframe', 'type', 'direction',
        'short_window', 'long_window', 'signal_window'
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
                
                if strategy['type'] != 'MACD':
                    raise ValidationError(
                        f"Invalid strategy type: {strategy['type']}"
                    )
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}")