"""Portfolio position sizing calculator."""

import json
from pathlib import Path
from typing import List
from app.tools.setup_logging import setup_logging
from app.portfolio_optimization.tools.position_sizing_types import Asset, PositionSizingConfig
from app.portfolio_optimization.tools.position_sizing import calculate_position_sizes

# Position sizing configuration
config: PositionSizingConfig = {
    "portfolio": "spy_qqq_btc_sol.json",
    "total_value": 22958.68,  # Initial portfolio value
    "use_ema": False,     # Whether to use EMA for price calculations
    "ema_period": 35,     # Period for EMA if used
    "var_confidence_levels": [0.95, 0.99]  # Required by position_sizing.py
}

def load_portfolio(portfolio: str) -> List[Asset]:
    """Load portfolio configuration from JSON file.
    
    Returns:
        List[Asset]: List of assets with their configurations
    """
    portfolio_path = Path(__file__).parent / "portfolios" / portfolio
    with open(portfolio_path) as f:
        return json.load(f)

def main() -> None:
    """Calculate and display optimal position sizes for portfolio assets."""
    try:
        # Setup logging
        log, log_close, _, _ = setup_logging(
            module_name='position',
            log_file='sizing.log'
        )
        
        log("Starting position sizing calculations", "info")
        
        # Load portfolio configuration
        log("Loading portfolio configuration", "info")
        assets = load_portfolio(config["portfolio"])
        
        # Calculate position sizes and metrics
        log("Calculating position sizes and metrics", "info")
        results = calculate_position_sizes(assets, config, log)
        
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
        print(f"\nInitial Portfolio Value: ${config['total_value']:.2f}")
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
