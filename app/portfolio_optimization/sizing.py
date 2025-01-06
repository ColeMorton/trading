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
    "var_confidence_levels": [0.95, 0.99]
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
            module_name='portfolio',
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
        
        # Calculate total leveraged value to check against target if needed
        total_leveraged_value = sum(
            metrics["leveraged_value"] for metrics in results
        )
        
        # If using target value and total leveraged value exceeds target,
        # scale down initial values proportionally
        if merged_config.get("use_target_value", False) and \
           "target_value" in merged_config and \
           total_leveraged_value > merged_config["target_value"]:
            
            log("Scaling down initial values to meet target value", "info")
            scale_factor = merged_config["target_value"] / total_leveraged_value
            
            # Scale down initial values while keeping leverage and allocation same
            for asset, metrics in zip(assets, results):
                metrics["initial_value"] *= scale_factor
                metrics["leveraged_value"] = metrics["initial_value"] * asset["leverage"]
                metrics["position_size"] *= scale_factor
        
        # Print results for each asset
        log("Displaying results", "info")
        total_leveraged_value = sum(metrics["leveraged_value"] for metrics in results)
        
        for asset, metrics in zip(assets, results):
            # Modified print_asset_details to skip risk metrics
            print(f"\nAsset: {asset['ticker']}")
            print(f"  Initial (pre-leverage) value: ${metrics['initial_value']:.2f}")
            print(f"  Leverage: {asset['leverage']:.2f}")
            print(f"  Leveraged value: ${metrics['leveraged_value']:.2f}")
            print(f"  Position size: {metrics['position_size']:.6f}")
            print(f"  Allocation: {metrics['allocation']:.2f}%")
        
        # Print portfolio totals
        print(f"\nInitial Portfolio Value: ${merged_config['initial_value']:.2f}")
        print(f"Total Leveraged Portfolio Value: ${total_leveraged_value:.2f}")
        if merged_config.get("use_target_value", False):
            print(f"Target Value: ${merged_config['target_value']:.2f}")
            
        log("Position sizing calculations completed successfully", "info")
        log_close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        log(f"Error in position sizing: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    main()
