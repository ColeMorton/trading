"""Portfolio loading and processing utilities.

This module provides utilities for loading and processing portfolio data,
with standardized error handling and logging.
"""
from typing import Dict, Any, List, Callable, Optional
from contextlib import contextmanager
from pathlib import Path
import os
import csv
import json

from app.tools.exceptions import PortfolioLoadError
from app.concurrency.tools.strategy_id import generate_strategy_id

def process_portfolio_strategies(strategies: List[Dict[str, Any]], log: Callable) -> List[Dict[str, Any]]:
    """Process portfolio strategies and assign strategy IDs.
    
    Args:
        strategies (List[Dict[str, Any]]): List of strategy configurations
        log (Callable): Logging function
        
    Returns:
        List[Dict[str, Any]]: Processed strategies with strategy IDs
    """
    processed_strategies = []
    
    for i, strategy in enumerate(strategies):
        # Create a copy to avoid modifying the original
        processed_strategy = strategy.copy()
        
        # Generate and assign strategy ID if not already present
        if 'strategy_id' not in processed_strategy:
            try:
                strategy_id = generate_strategy_id(processed_strategy)
                processed_strategy['strategy_id'] = strategy_id
                log(f"Generated strategy ID for strategy {i+1}: {strategy_id}", "debug")
            except ValueError as e:
                log(f"Could not generate strategy ID for strategy {i+1}: {str(e)}", "warning")
        
        processed_strategies.append(processed_strategy)
    
    return processed_strategies


def resolve_portfolio_path(portfolio_name: str, base_dir: str = '.') -> str:
    """Resolve the full path to a portfolio file.
    
    Args:
        portfolio_name: Name of the portfolio file
        base_dir: Base directory for portfolio files
        
    Returns:
        Full path to the portfolio file
        
    Raises:
        PortfolioLoadError: If the portfolio file cannot be found
    """
    # Check if the portfolio name already has a path
    if os.path.dirname(portfolio_name):
        # If it has a path, use it directly
        portfolio_path = portfolio_name
    else:
        # Try different locations
        possible_paths = [
            os.path.join(base_dir, 'csv', 'strategies', portfolio_name),
            os.path.join(base_dir, 'csv', 'portfolios', portfolio_name),
            os.path.join(base_dir, 'json', 'portfolios', portfolio_name),
            os.path.join(base_dir, portfolio_name)
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                portfolio_path = path
                break
        else:
            raise PortfolioLoadError(f"Portfolio file not found: {portfolio_name}")
    
    return portfolio_path


def load_csv_portfolio(file_path: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Load portfolio data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        config: Configuration dictionary
        
    Returns:
        List of portfolio entries
        
    Raises:
        PortfolioLoadError: If the CSV file cannot be loaded
    """
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        raise PortfolioLoadError(f"CSV file not found: {file_path}")
    except PermissionError:
        raise PortfolioLoadError(f"Permission denied when accessing CSV file: {file_path}")
    except csv.Error as e:
        raise PortfolioLoadError(f"CSV parsing error: {str(e)}")
    except Exception as e:
        raise PortfolioLoadError(f"Unexpected error loading CSV file: {str(e)}")


def load_json_portfolio(file_path: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Load portfolio data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        config: Configuration dictionary
        
    Returns:
        List of portfolio entries
        
    Raises:
        PortfolioLoadError: If the JSON file cannot be loaded
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle different JSON formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'strategies' in data:
                return data['strategies']
            else:
                raise PortfolioLoadError(f"Unsupported JSON format in {file_path}")
    except FileNotFoundError:
        raise PortfolioLoadError(f"JSON file not found: {file_path}")
    except PermissionError:
        raise PortfolioLoadError(f"Permission denied when accessing JSON file: {file_path}")
    except json.JSONDecodeError as e:
        raise PortfolioLoadError(f"JSON parsing error: {str(e)}")
    except Exception as e:
        raise PortfolioLoadError(f"Unexpected error loading JSON file: {str(e)}")


def load_portfolio_with_logging(
    portfolio_name: str,
    log: Callable[[str, Optional[str]], None],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Load portfolio data with logging.
    
    Args:
        portfolio_name: Name of the portfolio file
        log: Logging function
        config: Configuration dictionary
        
    Returns:
        List of portfolio entries
        
    Raises:
        PortfolioLoadError: If the portfolio cannot be loaded
    """
    try:
        log(f"Loading portfolio: {portfolio_name}", "info")
        
        # Resolve portfolio path
        portfolio_path = resolve_portfolio_path(
            portfolio_name,
            config.get("BASE_DIR", ".")
        )
        
        log(f"Resolved portfolio path: {portfolio_path}", "info")
        
        # Load portfolio based on file extension
        if portfolio_path.endswith('.csv'):
            portfolio_data = load_csv_portfolio(portfolio_path, config)
        elif portfolio_path.endswith('.json'):
            portfolio_data = load_json_portfolio(portfolio_path, config)
        else:
            raise PortfolioLoadError(f"Unsupported portfolio format: {portfolio_path}")
        
        log(f"Successfully loaded portfolio with {len(portfolio_data)} entries", "info")
        
        # Process strategies to assign strategy IDs
        processed_data = process_portfolio_strategies(portfolio_data, log)
        
        return processed_data
    except PortfolioLoadError as e:
        log(f"Portfolio load error: {str(e)}", "error")
        raise
    except Exception as e:
        error_msg = f"Unexpected error loading portfolio: {str(e)}"
        log(error_msg, "error")
        raise PortfolioLoadError(error_msg)


@contextmanager
def portfolio_context(
    portfolio_name: str,
    log: Callable[[str, Optional[str]], None],
    config: Dict[str, Any]
):
    """Context manager for portfolio loading and error handling.
    
    Args:
        portfolio_name: Name of the portfolio file
        log: Logging function
        config: Configuration dictionary
        
    Yields:
        Loaded portfolio data
        
    Raises:
        PortfolioLoadError: If the portfolio cannot be loaded
    """
    try:
        # Resolve portfolio path
        portfolio_path = resolve_portfolio_path(
            portfolio_name,
            config.get("BASE_DIR", ".")
        )
        
        log(f"Loading portfolio from {portfolio_path}", "info")
        
        # Load portfolio based on file extension
        if portfolio_path.endswith('.csv'):
            portfolio_data = load_csv_portfolio(portfolio_path, config)
        elif portfolio_path.endswith('.json'):
            portfolio_data = load_json_portfolio(portfolio_path, config)
        else:
            raise PortfolioLoadError(f"Unsupported portfolio format: {portfolio_path}")
        
        log(f"Successfully loaded portfolio with {len(portfolio_data)} entries", "info")
        
        # Process strategies to assign strategy IDs
        processed_data = process_portfolio_strategies(portfolio_data, log)
        
        # Yield the processed portfolio data
        yield processed_data
    except FileNotFoundError as e:
        raise PortfolioLoadError(f"Portfolio file not found: {str(e)}")
    except PermissionError as e:
        raise PortfolioLoadError(f"Permission denied when accessing portfolio: {str(e)}")
    except ValueError as e:
        raise PortfolioLoadError(f"Invalid portfolio data: {str(e)}")
    except Exception as e:
        raise PortfolioLoadError(f"Unexpected error loading portfolio: {str(e)}")