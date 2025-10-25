"""
COMP (Compound) Strategy Module

This module implements a compound strategy that aggregates multiple component
strategies and generates signals based on the percentage of strategies in position.
"""

from .strategy import run

__all__ = ["run"]

