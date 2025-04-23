"""Entry point utilities.

This module provides utilities for creating standardized entry points
for trading system modules.
"""
import sys
from typing import Dict, Any, Callable, Optional

from app.tools.error_context import error_context

def run_from_command_line(
    run_func: Callable,
    config: Dict[str, Any],
    operation_name: str,
    exit_on_failure: bool = True
) -> bool:
    """Run a function from the command line with standardized error handling.
    
    Args:
        run_func: Function to run
        config: Configuration dictionary
        operation_name: Name of the operation for error context
        exit_on_failure: Whether to exit with code 1 on failure
        
    Returns:
        True if execution successful, False otherwise
    """
    with error_context(
        f"Running {operation_name} from command line",
        lambda msg, level='info': print(f"[{level.upper()}] {msg}"),
        reraise=False
    ):
        success = run_func(config)
        if not success and exit_on_failure:
            sys.exit(1)
        return success