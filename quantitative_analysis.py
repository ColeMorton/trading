#!/usr/bin/env python3
"""
Quantitative Analysis Entry Point

Convenient entry point for running comprehensive quantitative analysis
on trading strategy data. This script provides easy access to the analysis
framework from the project root.

Usage:
    python quantitative_analysis.py
    python quantitative_analysis.py --export-charts
    python quantitative_analysis.py --monte-carlo-sims 50000
"""

import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

# Import and run the analysis
from analysis.run_analysis import main

if __name__ == "__main__":
    sys.exit(main())
