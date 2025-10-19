"""
MA Cross Core Module

This module provides the core business logic for MA Cross strategy analysis,
decoupled from file I/O and execution context.
"""

from .analyzer import MACrossAnalyzer
from .models import AnalysisConfig, AnalysisResult, SignalInfo, TickerResult


__all__ = [
    "AnalysisConfig",
    "AnalysisResult",
    "MACrossAnalyzer",
    "SignalInfo",
    "TickerResult",
]
