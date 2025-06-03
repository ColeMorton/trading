"""
Protective Stop Loss Analysis Module

This module coordinates the analysis of protective stop loss strategies,
integrating signal generation, metrics calculation, and results export.
"""

from typing import Callable

import polars as pl

from app.strategies.ma_cross.tools.psl_parameter_analysis import (
    analyze_holding_periods,
    analyze_protective_stop_loss_parameters,
)
from app.strategies.ma_cross.tools.psl_types import (
    AnalysisResult,
    HoldingPeriodResult,
    PSLConfig,
)


def analyze_psl(data: pl.DataFrame, config: PSLConfig, log: Callable) -> AnalysisResult:
    """
    Coordinate protective stop loss analysis.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data
        config (PSLConfig): Configuration parameters
        log (Callable): Logging function

    Returns:
        AnalysisResult: Analysis results including metrics and holding periods
    """
    return analyze_protective_stop_loss_parameters(data, config, log)


def analyze_periods(
    data: pl.DataFrame,
    entries: pl.Series,
    exits_ema: pl.Series,
    config: PSLConfig,
    log: Callable,
) -> HoldingPeriodResult:
    """
    Coordinate holding period analysis.

    Args:
        data (pl.DataFrame): Price data
        entries (pl.Series): Entry signals
        exits_ema (pl.Series): EMA-based exit signals
        config (PSLConfig): Configuration parameters
        log (Callable): Logging function

    Returns:
        HoldingPeriodResult: Analysis results for different holding periods
    """
    return analyze_holding_periods(data, entries, exits_ema, config, log)
