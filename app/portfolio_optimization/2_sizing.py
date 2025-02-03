"""Portfolio position sizing calculator."""

from app.tools.setup_logging import setup_logging
from app.portfolio_optimization.tools.position_sizing_types import PositionSizingConfig
from app.portfolio_optimization.tools.position_sizing import calculate_position_sizes
from app.portfolio_optimization.tools.portfolio_config import (
    load_portfolio_config
)

# Position sizing configuration - values not stored in portfolio JSON
config: PositionSizingConfig = {
    # "portfolio": "spy_qqq_btc_sol.json",
    "portfolio": "spy_qqq.json",
    "use_ema": False,     # Whether to use EMA for price calculations
    "ema_period": 35,     # Period for EMA if used
    "var_confidence_levels": [0.95, 0.99]
}

def main() -> None:
    """Calculate and display optimal position sizes for portfolio assets."""
    try:
        # Setup logging
        log, log_close, _, _ = setup_logging(
            module_name='portfolio',
            log_file='sizing.log'
        )
        
        log("Starting position sizing calculations", "info")
        
        # Load portfolio configuration
        log("Loading portfolio configuration", "info")
        portfolio_config = load_portfolio_config(config["portfolio"])
        
        # Merge portfolio config with base config
        merged_config = {**config, **portfolio_config}
        
        # Calculate position sizes and metrics
        log("Calculating position sizes and metrics", "info")
        results = calculate_position_sizes(portfolio_config["portfolio"], merged_config, log)
        
        # Calculate total leveraged value to check against target if needed
        total_leveraged_value = sum(
            metrics["leveraged_value"] for metrics in results
        )
        
        # If using target value and total leveraged value exceeds target,
        # scale down initial values proportionally
        if portfolio_config["use_target_value"] and \
           total_leveraged_value > portfolio_config["target_value"]:
            
            log("Scaling down initial values to meet target value", "info")
            scale_factor = portfolio_config["target_value"] / total_leveraged_value
            
            # Scale down initial values while keeping leverage and allocation same
            for asset, metrics in zip(portfolio_config["portfolio"], results):
                metrics["initial_value"] *= scale_factor
                metrics["leveraged_value"] = metrics["initial_value"] * asset["leverage"]
                metrics["position_size"] *= scale_factor
        
        # Print results for each asset
        log("Displaying results", "info")
        total_leveraged_value = sum(metrics["leveraged_value"] for metrics in results)
        
        for asset, metrics in zip(portfolio_config["portfolio"], results):
            # Modified print_asset_details to skip risk metrics
            print(f"\nAsset: {asset['ticker']}")
            print(f"  Initial (pre-leverage) value: ${metrics['initial_value']:.2f}")
            print(f"  Leverage: {asset['leverage']:.2f}")
            print(f"  Leveraged value: ${metrics['leveraged_value']:.2f}")
            print(f"  Position size: {metrics['position_size']:.6f}")
            print(f"  Allocation: {metrics['allocation']:.2f}%")
        
        # Print portfolio totals
        print(f"\nInitial Portfolio Value: ${portfolio_config['initial_value']:.2f}")
        print(f"Total Leveraged Portfolio Value: ${total_leveraged_value:.2f}")
        if portfolio_config["use_target_value"]:
            print(f"Target Value: ${portfolio_config['target_value']:.2f}")
            
        log("Position sizing calculations completed successfully", "info")
        log_close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        log(f"Error in position sizing: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    main()
