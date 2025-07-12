"""
VectorBT Strategy Parameters
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-12T08:47:37.495308
Confidence Level: 0.9
Total Strategies: 4
"""

import numpy as np
import pandas as pd
import vectorbt as vbt

# Statistical analysis-derived parameters
exit_parameters = {
    "RJF_SMA_68_77_RJF_D": {
        "take_profit": 0.1341,
        "stop_loss": 0.066,
        "max_holding_days": 172,
        "trailing_stop": 0.0255,
        "min_holding_days": 20,
        "momentum_exit_threshold": 0.05559767171425265,
        "trend_exit_threshold": 0.003,
        "confidence_level": 0.9,
        "sample_size": 111,
        "statistical_validity": "HIGH",
    },
    "HWM_SMA_7_9_HWM_D": {
        "take_profit": 0.11939999999999999,
        "stop_loss": 0.0796,
        "max_holding_days": 125,
        "trailing_stop": 0.0382,
        "min_holding_days": 15,
        "momentum_exit_threshold": 0.05728617357764935,
        "trend_exit_threshold": 0.0030277800981292746,
        "confidence_level": 0.9,
        "sample_size": 154,
        "statistical_validity": "HIGH",
    },
    "TPR_SMA_14_30_TPR_D": {
        "take_profit": 0.13570000000000002,
        "stop_loss": 0.0695,
        "max_holding_days": 171,
        "trailing_stop": 0.0334,
        "min_holding_days": 19,
        "momentum_exit_threshold": 0.054971648567572445,
        "trend_exit_threshold": 0.0030236480758322215,
        "confidence_level": 0.9,
        "sample_size": 107,
        "statistical_validity": "HIGH",
    },
    "SCHW_SMA_20_26_SCHW_D": {
        "take_profit": 0.1376,
        "stop_loss": 0.08109999999999999,
        "max_holding_days": 139,
        "trailing_stop": 0.0259,
        "min_holding_days": 14,
        "momentum_exit_threshold": 0.062343832597790215,
        "trend_exit_threshold": 0.003,
        "confidence_level": 0.9,
        "sample_size": 228,
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
    elif validity == "MEDIUM":
        return True, "Medium reliability parameters - use with caution"
    else:
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
