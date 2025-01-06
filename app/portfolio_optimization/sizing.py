"""Portfolio position sizing calculator."""

import json
from pathlib import Path
from typing import List
from app.tools.setup_logging import setup_logging
from app.portfolio_optimization.tools.position_sizing_types import Asset, PositionSizingConfig
from app.portfolio_optimization.tools.position_sizing import calculate_position_sizes

# Position sizing configuration - values not stored in portfolio JSON
config: PositionSizingConfig = {
    "portfolio": "spy_qqq_btc_sol.json",
    "use_ema": False,     # Whether to use EMA for price calculations
    "ema_period": 35,     # Period for EMA if used
    "var_confidence_levels": [0.95, 0.99]  # Required by position_sizing.py
}

def load_portfolio(portfolio: str) -> tuple[List[Asset], dict]:
    """Load portfolio configuration from JSON file.
    
    Args:
        portfolio (str): Name of the portfolio JSON file
    
    Returns:
        tuple[List[Asset], dict]: Tuple containing:
            - List of assets with their configurations
            - Dictionary of portfolio configuration values
    
    Raises:
        KeyError: If JSON file is missing required "portfolios" key
        ValueError: If JSON structure is invalid
    """
    portfolio_path = Path(__file__).parent / "portfolios" / portfolio
    with open(portfolio_path) as f:
        data = json.load(f)
        
    if "portfolios" not in data:
        raise KeyError("Portfolio JSON must contain 'portfolios' key")
    
    # Extract portfolio assets
    assets = data["portfolios"]
    
    # Extract config values, removing 'portfolios' key
    config_values = {k: v for k, v in data.items() if k != "portfolios"}
        
    return assets, config_values

def main() -> None:
    """Calculate and display optimal position sizes for portfolio assets."""
    try:
        # Setup logging
        log, log_close, _, _ = setup_logging(
            module_name='position',
            log_file='sizing.log'
        )
        
        log("Starting position sizing calculations", "info")
        
        # Load portfolio configuration and merge with base config
        log("Loading portfolio configuration", "info")
        assets, portfolio_config = load_portfolio(config["portfolio"])
        
        # Merge portfolio config with base config
        merged_config = {**config, **portfolio_config}
        
        # Calculate position sizes and metrics
        log("Calculating position sizes and metrics", "info")
        results = calculate_position_sizes(assets, merged_config, log)
        
        # Print results for each asset
        log("Displaying results", "info")
        total_leveraged_value = 0
        
        for asset, metrics in zip(assets, results):
            # Modified print_asset_details to skip risk metrics
            print(f"\nAsset: {asset['ticker']}")
            print(f"  Initial (pre-leverage) value: ${metrics['initial_value']:.2f}")
            print(f"  Leverage: {asset['leverage']:.2f}")
            print(f"  Leveraged value: ${metrics['leveraged_value']:.2f}")
            print(f"  Position size: {metrics['position_size']:.6f}")
            print(f"  Allocation: {metrics['allocation']:.2f}%")
            
            total_leveraged_value += metrics["leveraged_value"]
        
        # Print portfolio totals
        print(f"\nInitial Portfolio Value: ${merged_config['initial_value']:.2f}")
        print(f"Total Leveraged Portfolio Value: ${total_leveraged_value:.2f}")
            
        log("Position sizing calculations completed successfully", "info")
        log_close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        log(f"Error in position sizing: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    main()
