"""
SPDS Parameter Parser for Enhanced Input Support

This module provides intelligent parameter parsing for the SPDS analyze command,
supporting multiple input types: tickers, strategies, position UUIDs, and portfolios.
"""

import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel


class ParameterType(str, Enum):
    """Types of parameters that can be analyzed by SPDS."""

    TICKER_ONLY = "ticker_only"  # AMD
    MULTI_TICKER = "multi_ticker"  # NVDA,MSFT,QCOM
    STRATEGY_SPEC = "strategy_spec"  # TSLA_SMA_15_25
    MULTI_STRATEGY_SPEC = (
        "multi_strategy_spec"  # TSLA_SMA_15_25,RJF_SMA_68_77,SMCI_SMA_58_60
    )
    POSITION_UUID = "position_uuid"  # TSLA_SMA_15_25_20250710
    MULTI_POSITION_UUID = (
        "multi_position_uuid"  # TSLA_SMA_15_25_20250710,TPR_SMA_14_30_20250506
    )
    PORTFOLIO_FILE = "portfolio_file"  # risk_on.csv (existing)
    MULTI_PORTFOLIO_FILE = "multi_portfolio_file"  # risk_on,live_signals,protected


class ParsedParameter(BaseModel):
    """Structured representation of a parsed parameter."""

    parameter_type: ParameterType
    original_input: str

    # Common fields
    ticker: Optional[str] = None
    tickers: Optional[List[str]] = None  # For multi-ticker analysis

    # Strategy-specific fields
    strategy_type: Optional[str] = None
    fast_period: Optional[int] = None
    slow_period: Optional[int] = None
    signal_period: Optional[int] = None
    strategies: Optional[
        List[Dict[str, Union[str, int]]]
    ] = None  # For multi-strategy analysis

    # Position-specific fields
    entry_date: Optional[str] = None
    positions: Optional[
        List[Dict[str, Union[str, int]]]
    ] = None  # For multi-position analysis

    # Portfolio-specific fields
    portfolio_file: Optional[str] = None
    portfolio_files: Optional[List[str]] = None  # For multi-portfolio analysis

    class Config:
        use_enum_values = True


class SPDSParameterParser:
    """
    Intelligent parameter parser for SPDS analyze command.

    Detects input type and extracts relevant components for routing
    to appropriate analysis methods.
    """

    # Regex patterns for different input types
    TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}(-USD)?$")
    MULTI_TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}(-USD)?(,[A-Z]{1,5}(-USD)?)+$")
    STRATEGY_PATTERN = re.compile(
        r"^([A-Z]{1,5}(-USD)?)_(SMA|EMA|MACD)_(\d+)_(\d+)(_(\d+))?$"
    )
    MULTI_STRATEGY_PATTERN = re.compile(
        r"^([A-Z]{1,5}(-USD)?)_(SMA|EMA|MACD)_(\d+)_(\d+)(_(\d+))?(,([A-Z]{1,5}(-USD)?)_(SMA|EMA|MACD)_(\d+)_(\d+)(_(\d+))?)+$"
    )
    POSITION_UUID_PATTERN = re.compile(
        r"^([A-Z]{1,5}(-USD)?)_(SMA|EMA|MACD)_(\d+)_(\d+)(_(\d+))?_(\d{8}|\d{4}-\d{2}-\d{2})$"
    )
    MULTI_POSITION_UUID_PATTERN = re.compile(
        r"^([A-Z]{1,5}(-USD)?)_(SMA|EMA|MACD)_(\d+)_(\d+)(_(\d+))?_(\d{8}|\d{4}-\d{2}-\d{2})(,([A-Z]{1,5}(-USD)?)_(SMA|EMA|MACD)_(\d+)_(\d+)(_(\d+))?_(\d{8}|\d{4}-\d{2}-\d{2}))+$"
    )
    PORTFOLIO_FILE_PATTERN = re.compile(r"^.+\.csv$")
    MULTI_PORTFOLIO_PATTERN = re.compile(
        r"^([a-zA-Z_][a-zA-Z0-9_]*_[a-zA-Z0-9_]*|[a-zA-Z][a-zA-Z0-9]{6,})(,([a-zA-Z_][a-zA-Z0-9_]*_[a-zA-Z0-9_]*|[a-zA-Z][a-zA-Z0-9]{6,}))+$"
    )

    def __init__(self):
        """Initialize the parameter parser."""
        pass

    def detect_parameter_type(self, input_param: str) -> ParameterType:
        """
        Detect the type of input parameter.

        Args:
            input_param: Raw input parameter from command line

        Returns:
            ParameterType enum indicating the detected type
        """
        # Clean input
        param = input_param.strip()

        # Check for portfolio file (has .csv extension) - must be before multi-portfolio
        if self.PORTFOLIO_FILE_PATTERN.match(param):
            return ParameterType.PORTFOLIO_FILE

        # Check for multi-portfolio (comma-separated, no .csv)
        if self.MULTI_PORTFOLIO_PATTERN.match(param):
            return ParameterType.MULTI_PORTFOLIO_FILE

        # Check for multi-position UUID (comma-separated with dates)
        if self.MULTI_POSITION_UUID_PATTERN.match(param.upper()):
            return ParameterType.MULTI_POSITION_UUID

        # Check for position UUID (has date at end)
        if self.POSITION_UUID_PATTERN.match(param.upper()):
            return ParameterType.POSITION_UUID

        # Check for multi-strategy (comma-separated strategies)
        if self.MULTI_STRATEGY_PATTERN.match(param.upper()):
            return ParameterType.MULTI_STRATEGY_SPEC

        # Check for strategy specification (has strategy type and windows)
        if self.STRATEGY_PATTERN.match(param.upper()):
            return ParameterType.STRATEGY_SPEC

        # Check for multi-ticker (comma-separated)
        if self.MULTI_TICKER_PATTERN.match(param.upper()):
            return ParameterType.MULTI_TICKER

        # Check for ticker only
        if self.TICKER_PATTERN.match(param.upper()):
            return ParameterType.TICKER_ONLY

        # Default to portfolio file for backward compatibility
        return ParameterType.PORTFOLIO_FILE

    def parse_parameter(self, input_param: str) -> ParsedParameter:
        """
        Parse input parameter into structured components.

        Args:
            input_param: Raw input parameter from command line

        Returns:
            ParsedParameter with extracted components

        Raises:
            ValueError: If parameter cannot be parsed
        """
        param_type = self.detect_parameter_type(input_param)
        param = input_param.strip()

        if param_type == ParameterType.TICKER_ONLY:
            return self._parse_ticker(param)
        elif param_type == ParameterType.MULTI_TICKER:
            return self._parse_multi_ticker(param)
        elif param_type == ParameterType.STRATEGY_SPEC:
            return self._parse_strategy(param)
        elif param_type == ParameterType.MULTI_STRATEGY_SPEC:
            return self._parse_multi_strategy(param)
        elif param_type == ParameterType.POSITION_UUID:
            return self._parse_position_uuid(param)
        elif param_type == ParameterType.MULTI_POSITION_UUID:
            return self._parse_multi_position_uuid(param)
        elif param_type == ParameterType.PORTFOLIO_FILE:
            return self._parse_portfolio_file(param)
        elif param_type == ParameterType.MULTI_PORTFOLIO_FILE:
            return self._parse_multi_portfolio_file(param)
        else:
            raise ValueError(f"Unsupported parameter type: {param_type}")

    def _parse_ticker(self, param: str) -> ParsedParameter:
        """Parse ticker-only parameter."""
        match = self.TICKER_PATTERN.match(param.upper())
        if not match:
            raise ValueError(f"Invalid ticker format: {param}")

        return ParsedParameter(
            parameter_type=ParameterType.TICKER_ONLY,
            original_input=param,
            ticker=param.upper(),
        )

    def _parse_multi_ticker(self, param: str) -> ParsedParameter:
        """Parse multi-ticker parameter (comma-separated)."""
        match = self.MULTI_TICKER_PATTERN.match(param.upper())
        if not match:
            raise ValueError(f"Invalid multi-ticker format: {param}")

        # Split by comma and clean each ticker
        tickers = [ticker.strip().upper() for ticker in param.split(",")]

        # Validate each ticker individually
        for ticker in tickers:
            if not self.TICKER_PATTERN.match(ticker):
                raise ValueError(f"Invalid ticker in multi-ticker list: {ticker}")

        return ParsedParameter(
            parameter_type=ParameterType.MULTI_TICKER,
            original_input=param,
            tickers=tickers,
        )

    def _parse_strategy(self, param: str) -> ParsedParameter:
        """Parse strategy specification parameter."""
        match = self.STRATEGY_PATTERN.match(param.upper())
        if not match:
            raise ValueError(f"Invalid strategy format: {param}")

        ticker = match.group(1)
        strategy_type = match.group(3)
        fast_period = int(match.group(4))
        slow_period = int(match.group(5))
        signal_period = int(match.group(7)) if match.group(7) else 0

        return ParsedParameter(
            parameter_type=ParameterType.STRATEGY_SPEC,
            original_input=param,
            ticker=ticker,
            strategy_type=strategy_type,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
        )

    def _parse_position_uuid(self, param: str) -> ParsedParameter:
        """Parse position UUID parameter."""
        match = self.POSITION_UUID_PATTERN.match(param.upper())
        if not match:
            raise ValueError(f"Invalid position UUID format: {param}")

        ticker = match.group(1)
        strategy_type = match.group(3)
        fast_period = int(match.group(4))
        slow_period = int(match.group(5))
        signal_period = int(match.group(7)) if match.group(7) else 0
        entry_date = match.group(8)

        # Normalize date format to YYYY-MM-DD
        if len(entry_date) == 8:  # YYYYMMDD
            entry_date = f"{entry_date[:4]}-{entry_date[4:6]}-{entry_date[6:8]}"

        return ParsedParameter(
            parameter_type=ParameterType.POSITION_UUID,
            original_input=param,
            ticker=ticker,
            strategy_type=strategy_type,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            entry_date=entry_date,
        )

    def _parse_portfolio_file(self, param: str) -> ParsedParameter:
        """Parse portfolio file parameter."""
        return ParsedParameter(
            parameter_type=ParameterType.PORTFOLIO_FILE,
            original_input=param,
            portfolio_file=param,
        )

    def _parse_multi_strategy(self, param: str) -> ParsedParameter:
        """Parse multi-strategy parameter (comma-separated strategies)."""
        match = self.MULTI_STRATEGY_PATTERN.match(param.upper())
        if not match:
            raise ValueError(f"Invalid multi-strategy format: {param}")

        # Split by comma and parse each strategy
        strategy_specs = [spec.strip().upper() for spec in param.split(",")]
        strategies = []

        for spec in strategy_specs:
            strategy_match = self.STRATEGY_PATTERN.match(spec)
            if not strategy_match:
                raise ValueError(
                    f"Invalid strategy specification in multi-strategy: {spec}"
                )

            ticker = strategy_match.group(1)
            strategy_type = strategy_match.group(3)
            fast_period = int(strategy_match.group(4))
            slow_period = int(strategy_match.group(5))
            signal_period = (
                int(strategy_match.group(7)) if strategy_match.group(7) else 0
            )

            strategies.append(
                {
                    "ticker": ticker,
                    "strategy_type": strategy_type,
                    "fast_period": fast_period,
                    "slow_period": slow_period,
                    "signal_period": signal_period,
                }
            )

        return ParsedParameter(
            parameter_type=ParameterType.MULTI_STRATEGY_SPEC,
            original_input=param,
            strategies=strategies,
        )

    def _parse_multi_position_uuid(self, param: str) -> ParsedParameter:
        """Parse multi-position UUID parameter (comma-separated position UUIDs)."""
        match = self.MULTI_POSITION_UUID_PATTERN.match(param.upper())
        if not match:
            raise ValueError(f"Invalid multi-position UUID format: {param}")

        # Split by comma and parse each position UUID
        position_specs = [spec.strip().upper() for spec in param.split(",")]
        positions = []

        for spec in position_specs:
            position_match = self.POSITION_UUID_PATTERN.match(spec)
            if not position_match:
                raise ValueError(f"Invalid position UUID in multi-position: {spec}")

            ticker = position_match.group(1)
            strategy_type = position_match.group(3)
            fast_period = int(position_match.group(4))
            slow_period = int(position_match.group(5))
            signal_period = (
                int(position_match.group(7)) if position_match.group(7) else 0
            )
            entry_date = position_match.group(8)

            # Normalize date format to YYYY-MM-DD
            if len(entry_date) == 8:  # YYYYMMDD
                entry_date = f"{entry_date[:4]}-{entry_date[4:6]}-{entry_date[6:8]}"

            positions.append(
                {
                    "ticker": ticker,
                    "strategy_type": strategy_type,
                    "fast_period": fast_period,
                    "slow_period": slow_period,
                    "signal_period": signal_period,
                    "entry_date": entry_date,
                }
            )

        return ParsedParameter(
            parameter_type=ParameterType.MULTI_POSITION_UUID,
            original_input=param,
            positions=positions,
        )

    def _parse_multi_portfolio_file(self, param: str) -> ParsedParameter:
        """Parse multi-portfolio file parameter (comma-separated portfolio names)."""
        match = self.MULTI_PORTFOLIO_PATTERN.match(param)
        if not match:
            raise ValueError(f"Invalid multi-portfolio format: {param}")

        # Split by comma and clean each portfolio name
        portfolio_files = [name.strip() for name in param.split(",")]

        # Validate each portfolio name
        for portfolio in portfolio_files:
            if not portfolio or len(portfolio) < 1:
                raise ValueError(
                    f"Invalid portfolio name in multi-portfolio: {portfolio}"
                )

        return ParsedParameter(
            parameter_type=ParameterType.MULTI_PORTFOLIO_FILE,
            original_input=param,
            portfolio_files=portfolio_files,
        )

    def get_data_source_suggestions(self, parsed: ParsedParameter) -> Dict[str, bool]:
        """
        Get suggested data sources for the parsed parameter type.

        Args:
            parsed: Parsed parameter object

        Returns:
            Dictionary indicating which data sources are most relevant
        """
        if parsed.parameter_type == ParameterType.TICKER_ONLY:
            return {
                "market_data": True,
                "return_distributions": True,
                "equity_curves": False,
                "trade_history": False,
            }
        elif parsed.parameter_type == ParameterType.MULTI_TICKER:
            return {
                "market_data": True,
                "return_distributions": True,
                "parallel_analysis": True,
                "equity_curves": False,
                "trade_history": False,
            }
        elif parsed.parameter_type == ParameterType.STRATEGY_SPEC:
            return {
                "strategy_files": True,
                "equity_curves": True,
                "market_data": True,
                "trade_history": False,
            }
        elif parsed.parameter_type == ParameterType.MULTI_STRATEGY_SPEC:
            return {
                "strategy_files": True,
                "equity_curves": True,
                "market_data": True,
                "parallel_analysis": True,
                "trade_history": False,
            }
        elif parsed.parameter_type == ParameterType.POSITION_UUID:
            return {
                "trade_history": True,
                "equity_curves": True,
                "position_data": True,
                "market_data": True,
            }
        elif parsed.parameter_type == ParameterType.MULTI_POSITION_UUID:
            return {
                "trade_history": True,
                "equity_curves": True,
                "position_data": True,
                "market_data": True,
                "parallel_analysis": True,
            }
        elif parsed.parameter_type == ParameterType.MULTI_PORTFOLIO_FILE:
            return {
                "portfolio_files": True,
                "trade_history": True,
                "equity_curves": True,
                "parallel_analysis": True,
                "auto_detect": True,
            }
        else:  # PORTFOLIO_FILE
            return {
                "portfolio_files": True,
                "trade_history": True,
                "equity_curves": True,
                "auto_detect": True,
            }

    def validate_parameter(self, parsed: ParsedParameter) -> Tuple[bool, Optional[str]]:
        """
        Validate that the parsed parameter is valid for analysis.

        Args:
            parsed: Parsed parameter object

        Returns:
            Tuple of (is_valid, error_message)
        """
        if parsed.parameter_type == ParameterType.TICKER_ONLY:
            if not parsed.ticker or len(parsed.ticker) < 1:
                return False, "Ticker cannot be empty"

        elif parsed.parameter_type == ParameterType.MULTI_TICKER:
            if not parsed.tickers or len(parsed.tickers) < 2:
                return False, "Multi-ticker must have at least 2 tickers"

            for ticker in parsed.tickers:
                if not ticker or len(ticker) < 1:
                    return False, "All tickers must be non-empty"

        elif parsed.parameter_type in [
            ParameterType.STRATEGY_SPEC,
            ParameterType.POSITION_UUID,
        ]:
            if not all(
                [
                    parsed.ticker,
                    parsed.strategy_type,
                    parsed.fast_period,
                    parsed.slow_period,
                ]
            ):
                return False, "Strategy must have ticker, type, and windows"

            if parsed.fast_period >= parsed.slow_period:
                return False, "Fast period must be less than slow period"

            if parsed.strategy_type not in ["SMA", "EMA", "MACD"]:
                return False, f"Unsupported strategy type: {parsed.strategy_type}"

        elif parsed.parameter_type == ParameterType.MULTI_STRATEGY_SPEC:
            if not parsed.strategies or len(parsed.strategies) < 2:
                return False, "Multi-strategy must have at least 2 strategies"

            for strategy in parsed.strategies:
                if not all(
                    [
                        strategy.get("ticker"),
                        strategy.get("strategy_type"),
                        strategy.get("fast_period"),
                        strategy.get("slow_period"),
                    ]
                ):
                    return False, "All strategies must have ticker, type, and windows"

                fast_period = strategy.get("fast_period", 0)
                slow_period = strategy.get("slow_period", 1)
                if (
                    isinstance(fast_period, int)
                    and isinstance(slow_period, int)
                    and fast_period >= slow_period
                ):
                    return (
                        False,
                        "Fast period must be less than slow period for all strategies",
                    )

                if strategy.get("strategy_type") not in ["SMA", "EMA", "MACD"]:
                    return (
                        False,
                        f"Unsupported strategy type: {strategy.get('strategy_type')}",
                    )

        elif parsed.parameter_type == ParameterType.MULTI_POSITION_UUID:
            if not parsed.positions or len(parsed.positions) < 2:
                return False, "Multi-position must have at least 2 positions"

            for position in parsed.positions:
                if not all(
                    [
                        position.get("ticker"),
                        position.get("strategy_type"),
                        position.get("fast_period"),
                        position.get("slow_period"),
                        position.get("entry_date"),
                    ]
                ):
                    return (
                        False,
                        "All positions must have ticker, type, windows, and entry date",
                    )

                fast_period = position.get("fast_period", 0)
                slow_period = position.get("slow_period", 1)
                if (
                    isinstance(fast_period, int)
                    and isinstance(slow_period, int)
                    and fast_period >= slow_period
                ):
                    return (
                        False,
                        "Fast period must be less than slow period for all positions",
                    )

                if position.get("strategy_type") not in ["SMA", "EMA", "MACD"]:
                    return (
                        False,
                        f"Unsupported strategy type: {position.get('strategy_type')}",
                    )

        elif parsed.parameter_type == ParameterType.PORTFOLIO_FILE:
            if not parsed.portfolio_file:
                return False, "Portfolio file cannot be empty"

        elif parsed.parameter_type == ParameterType.MULTI_PORTFOLIO_FILE:
            if not parsed.portfolio_files or len(parsed.portfolio_files) < 2:
                return False, "Multi-portfolio must have at least 2 portfolio files"

            for portfolio in parsed.portfolio_files:
                if not portfolio or len(portfolio) < 1:
                    return False, "All portfolio files must be non-empty"

        return True, None


def create_parser() -> SPDSParameterParser:
    """Create a new SPDS parameter parser instance."""
    return SPDSParameterParser()


def parse_spds_parameter(input_param: str) -> ParsedParameter:
    """
    Convenience function to parse an SPDS parameter.

    Args:
        input_param: Raw input parameter

    Returns:
        ParsedParameter object

    Raises:
        ValueError: If parameter cannot be parsed or is invalid
    """
    parser = create_parser()
    parsed = parser.parse_parameter(input_param)

    is_valid, error_msg = parser.validate_parameter(parsed)
    if not is_valid:
        raise ValueError(f"Invalid parameter: {error_msg}")

    return parsed
