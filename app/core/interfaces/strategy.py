"""Strategy execution and analysis interfaces."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl


class StrategyConfig(ABC):
    """Abstract base for strategy configuration."""


class StrategyResult(ABC):
    """Abstract base for strategy results."""

    @property
    @abstractmethod
    def metrics(self) -> Dict[str, float]:
        """Performance metrics."""

    @property
    @abstractmethod
    def signals(self) -> Union[pd.DataFrame, pl.DataFrame]:
        """Trading signals."""


class StrategyAnalyzerInterface(ABC):
    """Interface for strategy analysis operations."""

    @abstractmethod
    def analyze(
        self,
        ticker: str,
        config: StrategyConfig,
        data: Optional[Union[pd.DataFrame, pl.DataFrame]] = None,
    ) -> StrategyResult:
        """Analyze a strategy for a given ticker."""

    @abstractmethod
    def validate_config(self, config: StrategyConfig) -> bool:
        """Validate strategy configuration."""

    @abstractmethod
    def get_default_config(self) -> StrategyConfig:
        """Get default configuration for the strategy."""


class StrategyExecutorInterface(ABC):
    """Interface for strategy execution operations."""

    @abstractmethod
    async def execute(
        self,
        strategy_type: str,
        tickers: List[str],
        config: Dict[str, Any],
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Execute a strategy for multiple tickers."""

    @abstractmethod
    async def execute_with_progress(
        self,
        strategy_type: str,
        tickers: List[str],
        config: Dict[str, Any],
        task_id: str,
        progress_tracker: "ProgressTrackerInterface",
    ) -> Dict[str, Any]:
        """Execute a strategy with progress tracking."""

    @abstractmethod
    def get_supported_strategies(self) -> List[str]:
        """Get list of supported strategy types."""

    @abstractmethod
    def validate_parameters(self, strategy_type: str, config: Dict[str, Any]) -> bool:
        """Validate parameters for a specific strategy."""
