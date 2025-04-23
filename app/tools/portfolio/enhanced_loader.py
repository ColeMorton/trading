"""Enhanced portfolio loading utilities with standardized error handling and logging.

This module provides high-level portfolio loading functions that encapsulate
error handling, logging, and path resolution in a consistent way across the system.
It follows SOLID principles and KISS (Keep It Simple, Stupid) design philosophy.
"""

from typing import List, Dict, Any, Callable, Optional, Union
from pathlib import Path
import os
import contextlib

from app.tools.portfolio.loader import load_portfolio as base_load_portfolio
from app.tools.portfolio.paths import resolve_portfolio_path
from app.tools.portfolio.types import StrategyConfig


class PortfolioLoadError(Exception):
    """Exception raised when portfolio loading fails.
    
    This class follows the Single Responsibility Principle by focusing solely
    on representing portfolio loading errors.
    """
    pass


def load_portfolio_with_logging(
    portfolio_name: str,
    log: Callable[[str, str], None],
    config: Dict[str, Any],
    detailed_logging: bool = True
) -> List[StrategyConfig]:
    """Load a portfolio with standardized logging and error handling.
    
    This function follows:
    - Single Responsibility: Focuses only on loading portfolios with logging
    - Open/Closed: Can be extended without modification
    - Liskov Substitution: Maintains the same contract as base_load_portfolio
    - Interface Segregation: Exposes only what clients need
    - Dependency Inversion: Depends on abstractions (log function, config dict)
    - KISS: Simple, predictable error handling with minimal branching
    
    Args:
        portfolio_name: Name of the portfolio file
        log: Logging function
        config: Configuration dictionary
        detailed_logging: Whether to log detailed information
        
    Returns:
        List of strategy configurations
        
    Raises:
        PortfolioLoadError: If portfolio loading fails
    """
    # Log portfolio loading attempt
    log(f"Loading portfolio: {portfolio_name}", "info")
    
    if detailed_logging:
        # Log additional details
        log(f"Config BASE_DIR: {config.get('BASE_DIR', '.')}", "info")
        log(f"Current working directory: {os.getcwd()}", "info")
        
        # Get the project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        log(f"Project root directory: {project_root}", "info")
    
    try:
        # Resolve portfolio path
        portfolio_path = resolve_portfolio_path(portfolio_name, config.get("BASE_DIR"))
        log(f"Resolved portfolio path: {portfolio_path}", "info")
        log(f"Path exists: {portfolio_path.exists()}", "info")
    except FileNotFoundError as e:
        log(f"Portfolio not found: {portfolio_name}", "error")
        log(f"Error details: {str(e)}", "error")
        raise PortfolioLoadError(f"Portfolio not found: {portfolio_name}") from e
    
    try:
        # Load portfolio
        strategies = base_load_portfolio(portfolio_name, log, config)
        log(f"Successfully loaded portfolio with {len(strategies)} entries")
        return strategies
    except Exception as e:
        log(f"Failed to load portfolio: {str(e)}", "error")
        raise PortfolioLoadError(f"Failed to load portfolio: {str(e)}") from e


@contextlib.contextmanager
def portfolio_context(
    portfolio_name: str,
    log: Callable[[str, str], None],
    config: Dict[str, Any]
) -> List[StrategyConfig]:
    """Context manager for portfolio loading with automatic error handling.
    
    This context manager follows:
    - Single Responsibility: Focuses only on providing a context for portfolio operations
    - Open/Closed: Can be extended without modification
    - Liskov Substitution: Yields the same type as load_portfolio_with_logging returns
    - Interface Segregation: Exposes only what clients need
    - Dependency Inversion: Depends on abstractions (log function, config dict)
    - KISS: Simple, predictable flow with minimal complexity
    
    Args:
        portfolio_name: Name of the portfolio file
        log: Logging function
        config: Configuration dictionary
        
    Yields:
        List of strategy configurations
        
    Raises:
        PortfolioLoadError: If portfolio loading fails
    """
    try:
        strategies = load_portfolio_with_logging(portfolio_name, log, config)
        yield strategies
    except Exception as e:
        if not isinstance(e, PortfolioLoadError):
            # Catch and convert any non-PortfolioLoadError exceptions
            log(f"Unexpected error in portfolio context: {str(e)}", "error")
            raise PortfolioLoadError(f"Unexpected error in portfolio context: {str(e)}") from e
        # Re-raise PortfolioLoadError exceptions
        raise