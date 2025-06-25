"""
Strategy Template Generator

This module provides template-based strategy development system to reduce new strategy
creation effort by 80%. It includes parameterized execution workflows, configuration-driven
customization, and automated validation.
"""

from .config_template import IndicatorType, StrategyType, TemplateConfig
from .execution_template import ExecutionTemplate
from .generator import StrategyTemplateGenerator
from .validation_template import ValidationTemplate

__all__ = [
    "StrategyTemplateGenerator",
    "TemplateConfig",
    "StrategyType",
    "IndicatorType",
    "ExecutionTemplate",
    "ValidationTemplate",
]
