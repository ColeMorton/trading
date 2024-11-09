import logging
import os
from typing import Optional, Set, Tuple
import polars as pl

def get_current_window_combinations(filepath: str) -> Optional[Set[Tuple[int, int]]]:
    """
    Read and validate current signal combinations from a file using Polars.

    Args:
        filepath: Path to the CSV file containing signal combinations

    Returns:
        Set of tuples containing (short_window, long_window) combinations if valid,
        None if file is invalid or empty
    """
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        logging.warning(f"No current signals found at {filepath}")
        return None

    try:
        current_signals = pl.read_csv(filepath)
        if current_signals.height == 0:
            logging.warning(f"Empty signals file at {filepath}")
            return None

        return set(zip(
            current_signals.get_column('Short Window').cast(pl.Int32).to_list(),
            current_signals.get_column('Long Window').cast(pl.Int32).to_list()
        ))
    except Exception as e:
        logging.error(f"Error reading signals file: {str(e)}")
        return None