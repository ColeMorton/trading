"""CSV generation utilities for portfolio data.

This module provides functions for generating CSV output from portfolio data.
"""

from typing import Any

import pandas as pd


def generate_csv_output_for_portfolios(portfolios: list[dict[str, Any]]) -> str:
    """Generate CSV string output ready for copy/paste.

    Args:
        portfolios: List of portfolio dictionaries

    Returns:
        CSV-formatted string representation of the portfolios
    """
    if not portfolios:
        return "No Entry strategies found"

    df = pd.DataFrame(portfolios)
    return df.to_csv(index=False, lineterminator="\n").strip()
