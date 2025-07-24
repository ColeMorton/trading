"""
VectorBT Strategy Parameters
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-23T11:39:32.457188
Confidence Level: 0.9
Total Strategies: 12
"""

import numpy as np
import pandas as pd
import vectorbt as vbt

# Statistical analysis-derived parameters
exit_parameters = {
    "SPG_ASSET_DISTRIBUTION_SPG_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0269,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 7953,
        "statistical_validity": "HIGH",
    },
    "ADBE_ASSET_DISTRIBUTION_ADBE_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0398,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 9809,
        "statistical_validity": "HIGH",
    },
    "LNC_ASSET_DISTRIBUTION_LNC_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0408,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 11429,
        "statistical_validity": "HIGH",
    },
    "MTD_ASSET_DISTRIBUTION_MTD_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.04190000000000001,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 6961,
        "statistical_validity": "HIGH",
    },
    "EXR_ASSET_DISTRIBUTION_EXR_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.031400000000000004,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 5266,
        "statistical_validity": "HIGH",
    },
    "CTSH_ASSET_DISTRIBUTION_CTSH_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.029500000000000002,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 6813,
        "statistical_validity": "HIGH",
    },
    "CMA_ASSET_DISTRIBUTION_CMA_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0333,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 11429,
        "statistical_validity": "HIGH",
    },
    "HIMS_ASSET_DISTRIBUTION_HIMS_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.12,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 1470,
        "statistical_validity": "HIGH",
    },
    "MSI_ASSET_DISTRIBUTION_MSI_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.024700000000000003,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 15994,
        "statistical_validity": "HIGH",
    },
    "TEAM_ASSET_DISTRIBUTION_TEAM_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.059500000000000004,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 2416,
        "statistical_validity": "HIGH",
    },
    "HPQ_ASSET_DISTRIBUTION_HPQ_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0453,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 15994,
        "statistical_validity": "HIGH",
    },
    "LYB_ASSET_DISTRIBUTION_LYB_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0446,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 3831,
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
