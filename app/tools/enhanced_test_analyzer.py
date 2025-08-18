"""
Test version of enhanced analyzer for quick validation.
"""

import asyncio
import logging
from typing import Any, Dict

from .parameter_parser import ParameterType, ParsedParameter
from .simplified_analysis_result import convert_to_standard_result, create_simple_result


class TestAssetDistributionAnalyzer:
    """Test version of asset distribution analyzer."""

    def __init__(self, parsed_param: ParsedParameter, logger=None):
        self.parsed_param = parsed_param
        self.ticker = parsed_param.ticker
        self.logger = logger or logging.getLogger(__name__)

    async def analyze(self) -> Dict[str, Any]:
        """Test analysis that always works."""
        strategy_name = f"{self.ticker}_ASSET_DISTRIBUTION"

        # Create a simple test result
        simple_result = create_simple_result(
            strategy_name=strategy_name,
            ticker=self.ticker,
            exit_signal="HOLD",
            confidence_level=0.75,
            p_value=0.15,
            sample_size=30,
            data_source="TEST_ASSET_DISTRIBUTION",
            analysis_mode="ASSET_ONLY",
            test_mode=True,
            distribution_type="NORMAL",
        )

        # Convert to standard format
        result = convert_to_standard_result(simple_result)

        return {strategy_name: result}


class TestStrategyAnalyzer:
    """Test version of strategy analyzer."""

    def __init__(self, parsed_param: ParsedParameter, logger=None):
        self.parsed_param = parsed_param
        self.ticker = parsed_param.ticker
        self.strategy_type = parsed_param.strategy_type
        self.fast_period = parsed_param.fast_period
        self.slow_period = parsed_param.slow_period
        self.logger = logger or logging.getLogger(__name__)

    async def analyze(self) -> Dict[str, Any]:
        """Test analysis that always works."""
        strategy_name = (
            f"{self.ticker}_{self.strategy_type}_{self.fast_period}_{self.slow_period}"
        )

        # Create a simple test result
        simple_result = create_simple_result(
            strategy_name=strategy_name,
            ticker=self.ticker,
            exit_signal="SELL",
            confidence_level=0.85,
            p_value=0.12,
            sample_size=50,
            data_source="TEST_STRATEGY_ANALYSIS",
            analysis_mode="STRATEGY_SPECIFIC",
            test_mode=True,
            strategy_type=self.strategy_type,
            fast_period=self.fast_period,
            slow_period=self.slow_period,
        )

        # Convert to standard format
        result = convert_to_standard_result(simple_result)

        return {strategy_name: result}


class TestPositionAnalyzer:
    """Test version of position analyzer."""

    def __init__(self, parsed_param: ParsedParameter, logger=None):
        self.parsed_param = parsed_param
        self.ticker = parsed_param.ticker
        self.strategy_type = parsed_param.strategy_type
        self.fast_period = parsed_param.fast_period
        self.slow_period = parsed_param.slow_period
        self.entry_date = parsed_param.entry_date
        self.logger = logger or logging.getLogger(__name__)

    async def analyze(self) -> Dict[str, Any]:
        """Test analysis that always works."""
        position_uuid = f"{self.ticker}_{self.strategy_type}_{self.fast_period}_{self.slow_period}_{self.entry_date.replace('-', '')}"

        # Create a simple test result
        simple_result = create_simple_result(
            strategy_name=position_uuid,
            ticker=self.ticker,
            exit_signal="STRONG_SELL",
            confidence_level=0.92,
            p_value=0.08,
            sample_size=1,
            data_source="TEST_POSITION_ANALYSIS",
            analysis_mode="POSITION_SPECIFIC",
            test_mode=True,
            entry_date=self.entry_date,
            strategy_type=self.strategy_type,
            current_pnl=0.15,
            mfe=0.20,
            mae=0.05,
        )

        # Convert to standard format
        result = convert_to_standard_result(simple_result)

        return {position_uuid: result}


def create_test_analyzer(parsed_param: ParsedParameter, logger=None):
    """Create test analyzer based on parameter type."""
    if parsed_param.parameter_type == ParameterType.TICKER_ONLY:
        return TestAssetDistributionAnalyzer(parsed_param, logger)
    elif parsed_param.parameter_type == ParameterType.STRATEGY_SPEC:
        return TestStrategyAnalyzer(parsed_param, logger)
    elif parsed_param.parameter_type == ParameterType.POSITION_UUID:
        return TestPositionAnalyzer(parsed_param, logger)
    else:
        raise ValueError(f"Unsupported parameter type: {parsed_param.parameter_type}")
