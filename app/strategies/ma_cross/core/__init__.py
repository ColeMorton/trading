"""
MA Cross Core Module

This module provides the core business logic for MA Cross strategy analysis,
decoupled from file I/O and execution context.
"""

from .analyzer import MACrossAnalyzer
from .models import AnalysisConfig, AnalysisResult, TickerResult

__all__ = ["MACrossAnalyzer", "AnalysisConfig", "AnalysisResult", "TickerResult"]
