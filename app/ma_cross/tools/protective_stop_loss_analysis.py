"""
Protective Stop Loss Analysis Module

This module serves as the main entry point for protective stop loss analysis,
coordinating the interaction between specialized submodules.
"""

from app.ma_cross.tools.psl_types import PSLConfig, AnalysisResult, HoldingPeriodResult
from app.ma_cross.tools.psl_analysis import (
    analyze_protective_stop_loss_parameters,
    analyze_holding_periods
)

__all__ = [
    'analyze_protective_stop_loss_parameters',
    'analyze_holding_periods'
]
