"""
Unified Strategy Execution Framework

This module provides a unified framework for strategy execution across all trading strategies,
consolidating the 4 different execution patterns into a single, consistent interface.

Design Principles:
- Single Responsibility: Each component has a clear, focused purpose
- Open/Closed: Extensible for new strategies without modifying existing code
- Liskov Substitution: All strategies are interchangeable through common interface
- Interface Segregation: Clean, minimal interfaces for different concerns
- Dependency Inversion: Depend on abstractions, not concrete implementations
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from app.core.interfaces.strategy import StrategyConfig, StrategyResult
from app.core.types.strategy import BacktestResult, StrategyParameters


class UnifiedStrategyConfig(BaseModel):
    """Unified configuration for all strategy types."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Core Strategy Parameters
    strategy_type: str = Field(..., description="Strategy type (MA_CROSS, MACD, RSI, etc.)")
    ticker: Union[str, List[str]] = Field(..., description="Ticker symbol(s) to analyze")
    timeframe: str = Field(default="D", description="Timeframe (D, H, etc.)")
    
    # Strategy-Specific Parameters
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy-specific parameters")
    
    # Data Parameters
    data_years: Optional[float] = Field(default=None, description="Years of historical data")
    use_synthetic: bool = Field(default=False, description="Use synthetic ticker pairs")
    
    # Risk Management
    risk_management: Dict[str, Any] = Field(default_factory=dict, description="Risk management settings")
    stop_loss: Optional[float] = Field(default=None, description="Stop loss percentage")
    allocation: Optional[float] = Field(default=None, description="Position allocation percentage")
    
    # Filtering and Selection
    filtering_criteria: Dict[str, Any] = Field(default_factory=dict, description="Portfolio filtering criteria")
    sort_by: str = Field(default="Total Return [%]", description="Metric to sort results by")
    
    # Execution Options
    use_current: bool = Field(default=False, description="Emphasize current window combinations")
    refresh_data: bool = Field(default=True, description="Refresh existing data")
    parallel_execution: bool = Field(default=True, description="Enable parallel processing")
    
    # Output Options
    output_dir: Optional[Path] = Field(default=None, description="Output directory for results")
    export_formats: List[str] = Field(default_factory=lambda: ["csv"], description="Export formats")
    
    def validate_for_strategy(self, strategy_type: str) -> bool:
        """Validate configuration for specific strategy type."""
        # Strategy-specific validation logic
        if strategy_type == "MA_CROSS":
            required_params = ["short_window", "long_window"]
            return all(param in self.parameters for param in required_params)
        elif strategy_type == "MACD":
            required_params = ["short_period", "long_period", "signal_period"]
            return all(param in self.parameters for param in required_params)
        elif strategy_type == "RSI":
            required_params = ["rsi_window", "oversold", "overbought"]
            return all(param in self.parameters for param in required_params)
        return True


class UnifiedStrategyResult(BaseModel):
    """Unified result structure for all strategy types."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Execution Metadata
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    strategy_type: str = Field(..., description="Strategy type executed")
    ticker: str = Field(..., description="Ticker symbol analyzed")
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_time: float = Field(..., description="Execution time in seconds")
    
    # Core Results
    metrics: Dict[str, float] = Field(..., description="Performance metrics")
    signals: Union[pd.DataFrame, pl.DataFrame, Dict[str, Any]] = Field(..., description="Trading signals")
    
    # Backtest Results
    equity_curve: Optional[Union[pd.DataFrame, pl.DataFrame]] = Field(default=None)
    trades: Optional[Union[pd.DataFrame, pl.DataFrame]] = Field(default=None)
    
    # Portfolio Analysis (for multi-parameter strategies)
    best_parameters: Optional[Dict[str, Any]] = Field(default=None)
    all_results: Optional[List[Dict[str, Any]]] = Field(default=None)
    
    # Risk Analysis
    risk_metrics: Optional[Dict[str, float]] = Field(default=None)
    drawdown_analysis: Optional[Dict[str, float]] = Field(default=None)
    
    # Export Information
    export_paths: Optional[Dict[str, Path]] = Field(default=None)
    
    @property
    def sharpe_ratio(self) -> Optional[float]:
        """Get Sharpe ratio from metrics."""
        return self.metrics.get("Sharpe Ratio")
    
    @property
    def total_return(self) -> Optional[float]:
        """Get total return from metrics."""
        return self.metrics.get("Total Return [%]")
    
    @property
    def win_rate(self) -> Optional[float]:
        """Get win rate from metrics."""
        return self.metrics.get("Win Rate [%]")


class AbstractStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    This class defines the unified interface that all strategies must implement,
    enabling consistent execution across different strategy types while preserving
    the unique characteristics of each strategy.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """Initialize strategy with name and version."""
        self.name = name
        self.version = version
        self._performance_tracker = None
    
    @property
    @abstractmethod
    def strategy_type(self) -> str:
        """Return the strategy type identifier."""
        pass
    
    @property
    @abstractmethod
    def required_parameters(self) -> List[str]:
        """Return list of required parameters for this strategy."""
        pass
    
    @property
    @abstractmethod
    def default_parameters(self) -> Dict[str, Any]:
        """Return default parameters for this strategy."""
        pass
    
    @abstractmethod
    def validate_config(self, config: UnifiedStrategyConfig) -> bool:
        """Validate configuration for this strategy."""
        pass
    
    @abstractmethod
    async def execute_single(
        self, 
        ticker: str, 
        config: UnifiedStrategyConfig,
        data: Optional[Union[pd.DataFrame, pl.DataFrame]] = None
    ) -> UnifiedStrategyResult:
        """Execute strategy for a single ticker with specific parameters."""
        pass
    
    @abstractmethod
    async def execute_optimization(
        self,
        ticker: str,
        config: UnifiedStrategyConfig,
        parameter_ranges: Dict[str, List[Any]]
    ) -> UnifiedStrategyResult:
        """Execute parameter optimization for a single ticker."""
        pass
    
    async def execute_portfolio(
        self,
        tickers: List[str],
        config: UnifiedStrategyConfig,
        progress_callback: Optional[callable] = None
    ) -> List[UnifiedStrategyResult]:
        """Execute strategy for multiple tickers (portfolio analysis)."""
        results = []
        
        for i, ticker in enumerate(tickers):
            if progress_callback:
                progress = (i / len(tickers)) * 100
                await progress_callback(ticker, progress)
            
            try:
                result = await self.execute_single(ticker, config)
                results.append(result)
            except Exception as e:
                # Log error and continue with next ticker
                self._log_error(f"Error executing {ticker}: {str(e)}")
                continue
        
        return results
    
    def get_config_template(self) -> UnifiedStrategyConfig:
        """Get a configuration template for this strategy."""
        return UnifiedStrategyConfig(
            strategy_type=self.strategy_type,
            ticker="EXAMPLE",
            parameters=self.default_parameters
        )
    
    def _log_error(self, message: str) -> None:
        """Log error message (to be enhanced with proper logging)."""
        print(f"[ERROR] {self.name}: {message}")
    
    def _log_info(self, message: str) -> None:
        """Log info message (to be enhanced with proper logging)."""
        print(f"[INFO] {self.name}: {message}")


class StrategyFactory:
    """Factory for creating strategy instances."""
    
    _strategies: Dict[str, type] = {}
    
    @classmethod
    def register_strategy(cls, strategy_type: str, strategy_class: type) -> None:
        """Register a strategy class."""
        cls._strategies[strategy_type] = strategy_class
    
    @classmethod
    def create_strategy(cls, strategy_type: str) -> AbstractStrategy:
        """Create a strategy instance."""
        if strategy_type not in cls._strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        strategy_class = cls._strategies[strategy_type]
        return strategy_class()
    
    @classmethod
    def get_supported_strategies(cls) -> List[str]:
        """Get list of supported strategy types."""
        return list(cls._strategies.keys())
    
    @classmethod
    def list_strategies(cls) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about all strategies."""
        strategies = {}
        
        for strategy_type, strategy_class in cls._strategies.items():
            instance = strategy_class()
            strategies[strategy_type] = {
                "name": instance.name,
                "version": instance.version,
                "required_parameters": instance.required_parameters,
                "default_parameters": instance.default_parameters
            }
        
        return strategies


class UnifiedStrategyExecutor:
    """
    Unified executor for all strategy types.
    
    This class provides a single entry point for executing any strategy,
    handling the routing to appropriate strategy implementations while
    maintaining consistent behavior across all execution patterns.
    """
    
    def __init__(self):
        """Initialize the unified executor."""
        self.factory = StrategyFactory()
    
    async def execute(
        self,
        strategy_type: str,
        config: UnifiedStrategyConfig,
        progress_callback: Optional[callable] = None
    ) -> Union[UnifiedStrategyResult, List[UnifiedStrategyResult]]:
        """
        Execute a strategy with unified configuration.
        
        Args:
            strategy_type: Type of strategy to execute
            config: Unified configuration
            progress_callback: Optional progress callback
            
        Returns:
            Strategy result(s)
        """
        # Create strategy instance
        strategy = self.factory.create_strategy(strategy_type)
        
        # Validate configuration
        if not strategy.validate_config(config):
            raise ValueError(f"Invalid configuration for strategy {strategy_type}")
        
        # Determine execution mode
        if isinstance(config.ticker, str):
            # Single ticker execution
            return await strategy.execute_single(config.ticker, config)
        else:
            # Portfolio execution
            return await strategy.execute_portfolio(config.ticker, config, progress_callback)
    
    async def optimize(
        self,
        strategy_type: str,
        ticker: str,
        config: UnifiedStrategyConfig,
        parameter_ranges: Dict[str, List[Any]]
    ) -> UnifiedStrategyResult:
        """Execute parameter optimization for a strategy."""
        strategy = self.factory.create_strategy(strategy_type)
        return await strategy.execute_optimization(ticker, config, parameter_ranges)
    
    def get_strategy_info(self, strategy_type: str) -> Dict[str, Any]:
        """Get information about a specific strategy."""
        strategies = self.factory.list_strategies()
        if strategy_type not in strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        return strategies[strategy_type]
    
    def list_supported_strategies(self) -> Dict[str, Dict[str, Any]]:
        """List all supported strategies with their information."""
        return self.factory.list_strategies()


# Global executor instance
unified_executor = UnifiedStrategyExecutor()