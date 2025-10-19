"""
CLI Module entry point for `python -m app.cli` execution.

This module provides a clean entry point that avoids the RuntimeWarning
about module imports by not importing the main module in __init__.py.
"""

from .main import cli_main


if __name__ == "__main__":
    cli_main()
