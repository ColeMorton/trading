"""
Market Data Analyzer Test Suite

Comprehensive unit tests for MarketDataAnalyzer and related components
including momentum calculations, trend analysis, recommendation generation,
and enhanced parameter analysis integration.
"""

# Test modules
from . import (
    test_enhanced_parameter_analysis,
    test_market_data_analyzer,
    test_momentum_calculations,
    test_trend_calculations,
)


__all__ = [
    "test_enhanced_parameter_analysis",
    "test_market_data_analyzer",
    "test_momentum_calculations",
    "test_trend_calculations",
]
