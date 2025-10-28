"""
VectorBT Strategy Parameters
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-23T11:38:56.109204
Confidence Level: 0.9
Total Strategies: 2
"""


# Statistical analysis-derived parameters
exit_parameters = {
    "NVDA_ASSET_DISTRIBUTION_NVDA_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.037200000000000004,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 6664,
        "statistical_validity": "HIGH",
    },
    "MSFT_ASSET_DISTRIBUTION_MSFT_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0203,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 9915,
        "statistical_validity": "HIGH",
    },
}


# Parameter validation function
def validate_parameters(strategy_key):
    """Validate parameter reliability for strategy"""
    if strategy_key not in exit_parameters:
        return False, "Strategy not found"

    params = exit_parameters[strategy_key]
    sample_size = params.get("sample_size", 0)
    validity = params.get("statistical_validity", "LOW")

    if validity == "HIGH":
        return True, "High reliability parameters"
    if validity == "MEDIUM":
        return True, "Medium reliability parameters - use with caution"
    return False, "Low reliability parameters - not recommended"


# Example usage
def apply_exit_rules(strategy_key, data):
    """Apply statistical exit rules to VectorBT data"""
    if strategy_key not in exit_parameters:
        raise ValueError(f"No parameters found for strategy: {strategy_key}")

    params = exit_parameters[strategy_key]

    # Validate parameters
    valid, message = validate_parameters(strategy_key)
    if not valid:
        print(f"Warning: {message}")

    # Apply exit rules
    entries = data["entries"]  # Your entry signals

    # Create exit conditions
    take_profit_exits = data["close"] >= data["entry_price"] * (
        1 + params["take_profit"]
    )
    stop_loss_exits = data["close"] <= data["entry_price"] * (1 - params["stop_loss"])

    # Combine exit conditions
    exits = take_profit_exits | stop_loss_exits

    return entries, exits


# Framework compatibility validation
framework_compatibility = {
    "vectorbt_version": ">=0.25.0",
    "parameter_format": "dictionary",
    "validation_status": "PASSED",
}
