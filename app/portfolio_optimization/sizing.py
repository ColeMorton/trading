"""Portfolio position sizing calculator."""

import json
from pathlib import Path
from typing import List
from app.tools.setup_logging import setup_logging
from app.portfolio_optimization.tools.position_sizing_types import Asset, PositionSizingConfig
from app.portfolio_optimization.tools.position_sizing import calculate_position_sizes, print_asset_details

# Position sizing configuration
config: PositionSizingConfig = {
    "total_value": 22958.68,  # Initial portfolio value
    "use_ema": False,     # Whether to use EMA for price calculations
    "ema_period": 35,     # Period for EMA if used
    "var_confidence_levels": [0.95, 0.99]  # Confidence levels for VaR/CVaR
}

def load_portfolio() -> List[Asset]:
    """Load portfolio configuration from JSON file.
    
    Returns:
        List[Asset]: List of assets with their configurations
    """
    portfolio_path = Path(__file__).parent / "portfolios" / "current.json"
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
        assets = load_portfolio()
        
        # Calculate position sizes and metrics
        log("Calculating position sizes and metrics", "info")
        results = calculate_position_sizes(assets, config, log)
        
        # Print results for each asset
        log("Displaying results", "info")
        total_leveraged_value = 0
        total_var_losses = {cl: 0.0 for cl in config["var_confidence_levels"]}
        total_cvar_losses = {cl: 0.0 for cl in config["var_confidence_levels"]}
        
        for asset, metrics in zip(assets, results):
            print_asset_details(asset["ticker"], metrics, asset["leverage"])
            total_leveraged_value += metrics["leveraged_value"]
            
            # Accumulate VaR and CVaR losses
            for cl, (var, cvar) in metrics["var_cvar"].items():
                var_loss = abs(var * metrics["leveraged_value"])
                cvar_loss = abs(cvar * metrics["leveraged_value"])
                total_var_losses[cl] += var_loss
                total_cvar_losses[cl] += cvar_loss
        
        # Print portfolio totals
        print(f"\nInitial Portfolio Value: ${config['total_value']:.2f}")
        print(f"Total Leveraged Portfolio Value: ${total_leveraged_value:.2f}")
        
        for cl in config["var_confidence_levels"]:
            print(f"Total VaR Monetary Loss ({cl*100:.0f}%): ${total_var_losses[cl]:.2f}")
            print(f"Total CVaR Monetary Loss ({cl*100:.0f}%): ${total_cvar_losses[cl]:.2f}")
            
        log("Position sizing calculations completed successfully", "info")
        log_close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        log(f"Error in position sizing: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    main()
