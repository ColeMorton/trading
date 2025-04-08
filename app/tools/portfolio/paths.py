"""
Portfolio Path Resolution Module

This module provides functions for resolving paths to portfolio files
across different modules in the application.
"""

from pathlib import Path
from typing import Optional, Union

def resolve_portfolio_path(
    portfolio_name: str,
    base_dir: Optional[str] = None,
    file_type: Optional[str] = None
) -> Path:
    """
    Resolve the path to a portfolio file.

    Args:
        portfolio_name: Name of the portfolio file (with or without extension)
        base_dir: Base directory (defaults to current working directory)
        file_type: Force specific file type ('csv' or 'json')

    Returns:
        Path: Resolved path to the portfolio file

    Raises:
        FileNotFoundError: If portfolio file cannot be found
    """
    # Use provided base_dir or default to current directory
    base = Path(base_dir) if base_dir else Path('.')
    
    # If file_type is specified, force that extension
    if file_type:
        if file_type.lower() not in ['csv', 'json']:
            raise ValueError(f"Unsupported file type: {file_type}. Must be 'csv' or 'json'")
        
        # Ensure portfolio_name has the correct extension
        name = portfolio_name
        if '.' in name:
            name = name.split('.')[0]
        
        portfolio_path = base / "csv" / "portfolios" / f"{name}.{file_type.lower()}"
        if portfolio_path.exists():
            return portfolio_path
        
        # For JSON files, also check json/portfolios directory
        if file_type.lower() == 'json':
            portfolio_path = base / "json" / "portfolios" / f"{name}.json"
            if portfolio_path.exists():
                return portfolio_path
                
        raise FileNotFoundError(f"Portfolio file not found: {portfolio_path}")
    
    # Try to find the file with any supported extension
    # First check if the name already has an extension
    if '.' in portfolio_name:
        name, ext = portfolio_name.split('.', 1)
        if ext.lower() in ['csv', 'json']:
            # Check CSV directory first
            if ext.lower() == 'csv':
                portfolio_path = base / "csv" / "portfolios" / portfolio_name
                if portfolio_path.exists():
                    return portfolio_path
            
            # Check JSON directory for JSON files
            if ext.lower() == 'json':
                portfolio_path = base / "json" / "portfolios" / portfolio_name
                if portfolio_path.exists():
                    return portfolio_path
    else:
        # Try CSV first
        portfolio_path = base / "csv" / "portfolios" / f"{portfolio_name}.csv"
        if portfolio_path.exists():
            return portfolio_path
            
        # Then try JSON in portfolios directory
        portfolio_path = base / "json" / "portfolios" / f"{portfolio_name}.json"
        if portfolio_path.exists():
            return portfolio_path
            
        # Check concurrency-specific paths
        concurrency_path = base / "json" / "concurrency" / f"{portfolio_name}.json"
        if concurrency_path.exists():
            return concurrency_path
    
    # If we get here, the file wasn't found
    raise FileNotFoundError(f"Portfolio file not found: {portfolio_name}")

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path: Project root directory
    """
    # This assumes the function is called from within the project
    # and that the project structure has 'app' at the top level
    current_file = Path(__file__)
    # Go up three levels: file -> portfolio -> tools -> app -> project_root
    return current_file.parent.parent.parent.parent