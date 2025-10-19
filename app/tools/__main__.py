#!/usr/bin/env python3
"""
Entry point for running the Statistical Performance Divergence System CLI

Usage:
    python -m app.tools [OPTIONS]

This module provides a convenient entry point for the statistical analysis CLI.
"""

import sys

from .statistical_analysis_cli import main


if __name__ == "__main__":
    sys.exit(main())
