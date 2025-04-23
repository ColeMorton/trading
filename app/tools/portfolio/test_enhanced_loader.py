"""
Test script for the enhanced portfolio loader.

This script tests the enhanced portfolio loader by loading a portfolio
and printing the results.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

from app.tools.setup_logging import setup_logging
from app.tools.portfolio import (
    load_portfolio_with_logging,
    portfolio_context,
    PortfolioLoadError
)

def simple_log(message, level="info"):
    """Simple logging function for testing."""
    print(f"[{level.upper()}] {message}")

def test_load_portfolio():
    """Test loading a portfolio with the enhanced loader."""
    # Set up logging
    log, log_close, _, _ = setup_logging(
        module_name='test',
        log_file='test_enhanced_loader.log'
    )
    
    try:
        # Configuration
        config = {
            "PORTFOLIO": "DAILY_test.csv",
            "BASE_DIR": project_root,
            "REFRESH": True
        }
        
        print("\n=== Testing load_portfolio_with_logging ===")
        try:
            # Load portfolio with enhanced loader
            strategies = load_portfolio_with_logging(config["PORTFOLIO"], log, config)
            print(f"Successfully loaded {len(strategies)} strategies")
            
            # Print first strategy
            if strategies:
                print("\nFirst strategy:")
                for key, value in strategies[0].items():
                    print(f"  {key}: {value}")
        except PortfolioLoadError as e:
            print(f"Failed to load portfolio: {e}")
        
        print("\n=== Testing portfolio_context ===")
        try:
            # Load portfolio with context manager
            with portfolio_context(config["PORTFOLIO"], log, config) as strategies:
                print(f"Successfully loaded {len(strategies)} strategies in context")
                
                # Print first strategy
                if strategies:
                    print("\nFirst strategy (from context):")
                    for key, value in strategies[0].items():
                        print(f"  {key}: {value}")
        except PortfolioLoadError as e:
            print(f"Failed to load portfolio in context: {e}")
            
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        log_close()

if __name__ == "__main__":
    test_load_portfolio()