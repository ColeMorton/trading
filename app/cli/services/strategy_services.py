"""
Strategy Service Layer

This module provides strategy-specific service implementations that
wrap underlying strategy modules with consistent CLI-compatible interfaces.
"""

import importlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

from rich import print as rprint

from ..models.strategy import StrategyConfig


class BaseStrategyService(ABC):
    """Abstract base class for strategy services."""
    
    @abstractmethod
    def execute_strategy(self, config: StrategyConfig) -> bool:
        """
        Execute strategy analysis with the given configuration.
        
        Args:
            config: Strategy configuration model
            
        Returns:
            True if execution successful, False otherwise
        """
        pass
    
    @abstractmethod
    def convert_config_to_legacy(self, config: StrategyConfig) -> Dict[str, Any]:
        """
        Convert CLI configuration to legacy format expected by strategy module.
        
        Args:
            config: Strategy configuration model
            
        Returns:
            Legacy configuration dictionary
        """
        pass
    
    @abstractmethod
    def get_supported_strategy_types(self) -> List[str]:
        """Get list of strategy types supported by this service."""
        pass


class MAStrategyService(BaseStrategyService):
    """Service for MA Cross strategy execution."""
    
    def execute_strategy(self, config: StrategyConfig) -> bool:
        """Execute MA Cross strategy analysis."""
        try:
            # Import MA Cross module
            ma_cross_module = importlib.import_module(
                "app.strategies.ma_cross.1_get_portfolios"
            )
            run = ma_cross_module.run
            
            # Convert config to legacy format
            legacy_config = self.convert_config_to_legacy(config)
            
            # Execute strategy
            return run(legacy_config)
            
        except Exception as e:
            rprint(f"[red]Error executing MA Cross strategy: {e}[/red]")
            return False
    
    def convert_config_to_legacy(self, config: StrategyConfig) -> Dict[str, Any]:
        """Convert CLI config to MA Cross legacy format."""
        # Convert ticker to list format
        ticker_list = config.ticker if isinstance(config.ticker, list) else [config.ticker]
        
        # Base legacy config structure
        legacy_config = {
            "TICKER": ticker_list,
            "STRATEGY_TYPES": [st.value if hasattr(st, 'value') else str(st) for st in config.strategy_types],
            "USE_YEARS": config.use_years,
            "YEARS": config.years or 15,
            "MULTI_TICKER": config.multi_ticker,
            "USE_SCANNER": config.use_scanner,
            "SCANNER_LIST": config.scanner_list,
            "USE_GBM": config.use_gbm,
            "MINIMUMS": {},
        }
        
        # Add minimum criteria
        if config.minimums.win_rate is not None:
            legacy_config["MINIMUMS"]["WIN_RATE"] = config.minimums.win_rate
        if config.minimums.trades is not None:
            legacy_config["MINIMUMS"]["TRADES"] = config.minimums.trades
        if config.minimums.expectancy_per_trade is not None:
            legacy_config["MINIMUMS"]["EXPECTANCY_PER_TRADE"] = config.minimums.expectancy_per_trade
        if config.minimums.profit_factor is not None:
            legacy_config["MINIMUMS"]["PROFIT_FACTOR"] = config.minimums.profit_factor
        if config.minimums.sortino_ratio is not None:
            legacy_config["MINIMUMS"]["SORTINO_RATIO"] = config.minimums.sortino_ratio
        if config.minimums.beats_bnh is not None:
            legacy_config["MINIMUMS"]["BEATS_BNH"] = config.minimums.beats_bnh
        
        # Add synthetic ticker configuration
        if config.synthetic.use_synthetic:
            legacy_config["USE_SYNTHETIC"] = True
            legacy_config["TICKER_1"] = config.synthetic.ticker_1
            legacy_config["TICKER_2"] = config.synthetic.ticker_2
        
        # Add parameter ranges for sweeps if specified
        if config.fast_period_range:
            legacy_config["FAST_PERIOD_RANGE"] = config.fast_period_range
        if config.slow_period_range:
            legacy_config["SLOW_PERIOD_RANGE"] = config.slow_period_range
            
        # Add specific periods if provided
        if config.fast_period:
            legacy_config["FAST_PERIOD"] = config.fast_period
        if config.slow_period:
            legacy_config["SLOW_PERIOD"] = config.slow_period
        
        return legacy_config
    
    def get_supported_strategy_types(self) -> List[str]:
        """Get supported strategy types for MA Cross."""
        return ["SMA", "EMA"]


class MACDStrategyService(BaseStrategyService):
    """Service for MACD strategy execution."""
    
    def execute_strategy(self, config: StrategyConfig) -> bool:
        """Execute MACD strategy analysis."""
        try:
            # Import MACD module
            macd_module = importlib.import_module(
                "app.strategies.macd.1_get_portfolios"
            )
            run = macd_module.run
            
            # Convert config to legacy format
            legacy_config = self.convert_config_to_legacy(config)
            
            # Execute strategy
            return run(legacy_config)
            
        except Exception as e:
            rprint(f"[red]Error executing MACD strategy: {e}[/red]")
            return False
    
    def convert_config_to_legacy(self, config: StrategyConfig) -> Dict[str, Any]:
        """Convert CLI config to MACD legacy format."""
        # Convert ticker to list format
        ticker_list = config.ticker if isinstance(config.ticker, list) else [config.ticker]
        
        # MACD-specific legacy config structure based on config_types.py
        legacy_config = {
            "TICKER": ticker_list,
            "STRATEGY_TYPE": "MACD",  # Critical: This tells the strategy to use MACD analysis
            "SHORT_WINDOW_START": config.fast_period or 2,
            "SHORT_WINDOW_END": config.fast_period or 18, 
            "LONG_WINDOW_START": config.slow_period or 4,
            "LONG_WINDOW_END": config.slow_period or 36,
            "SIGNAL_WINDOW_START": config.signal_period or 2,
            "SIGNAL_WINDOW_END": config.signal_period or 18,
            "STEP": 1,
            "DIRECTION": "Long",
            "USE_CURRENT": False,
            "USE_HOURLY": False,
            "USE_YEARS": config.use_years,
            "YEARS": config.years or 15,
            "REFRESH": False,
            "MULTI_TICKER": config.multi_ticker,
            "MINIMUMS": {},
        }
        
        # Handle parameter ranges for MACD sweeps
        if config.fast_period_range:
            legacy_config["SHORT_WINDOW_START"] = config.fast_period_range[0]
            legacy_config["SHORT_WINDOW_END"] = config.fast_period_range[1]
        if config.slow_period_range:
            legacy_config["LONG_WINDOW_START"] = config.slow_period_range[0] 
            legacy_config["LONG_WINDOW_END"] = config.slow_period_range[1]
        
        # Add minimum criteria (same as MA Cross)
        if config.minimums.win_rate is not None:
            legacy_config["MINIMUMS"]["WIN_RATE"] = config.minimums.win_rate
        if config.minimums.trades is not None:
            legacy_config["MINIMUMS"]["TRADES"] = config.minimums.trades
        if config.minimums.expectancy_per_trade is not None:
            legacy_config["MINIMUMS"]["EXPECTANCY_PER_TRADE"] = config.minimums.expectancy_per_trade
        if config.minimums.profit_factor is not None:
            legacy_config["MINIMUMS"]["PROFIT_FACTOR"] = config.minimums.profit_factor
        if config.minimums.sortino_ratio is not None:
            legacy_config["MINIMUMS"]["SORTINO_RATIO"] = config.minimums.sortino_ratio
        if config.minimums.beats_bnh is not None:
            legacy_config["MINIMUMS"]["BEATS_BNH"] = config.minimums.beats_bnh
        
        return legacy_config
    
    def get_supported_strategy_types(self) -> List[str]:
        """Get supported strategy types for MACD."""
        return ["MACD"]