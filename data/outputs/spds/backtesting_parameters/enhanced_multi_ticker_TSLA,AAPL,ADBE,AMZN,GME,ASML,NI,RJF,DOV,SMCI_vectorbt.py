"""
VectorBT Strategy Parameters
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-24T12:25:04.399805
Confidence Level: 0.9
Total Strategies: 10
"""

import numpy as np
import pandas as pd
import vectorbt as vbt

# Statistical analysis-derived parameters
exit_parameters = {
    "TSLA_ASSET_DISTRIBUTION_TSLA_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0857,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 54,
        "statistical_validity": "MEDIUM",
    },
    "AAPL_ASSET_DISTRIBUTION_AAPL_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0322,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 54,
        "statistical_validity": "MEDIUM",
    },
    "ADBE_ASSET_DISTRIBUTION_ADBE_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0403,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 54,
        "statistical_validity": "MEDIUM",
    },
    "AMZN_ASSET_DISTRIBUTION_AMZN_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.032,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 54,
        "statistical_validity": "MEDIUM",
    },
    "GME_ASSET_DISTRIBUTION_GME_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0866,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 54,
        "statistical_validity": "MEDIUM",
    },
    "ASML_ASSET_DISTRIBUTION_ASML_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0434,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 54,
        "statistical_validity": "MEDIUM",
    },
    "NI_ASSET_DISTRIBUTION_NI_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.024900000000000002,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 344,
        "statistical_validity": "HIGH",
    },
    "RJF_ASSET_DISTRIBUTION_RJF_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.028999999999999998,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 344,
        "statistical_validity": "HIGH",
    },
    "DOV_ASSET_DISTRIBUTION_DOV_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.0278,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 344,
        "statistical_validity": "HIGH",
    },
    "SMCI_ASSET_DISTRIBUTION_SMCI_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 30,
        "trailing_stop": 0.077,
        "min_holding_days": 5,
        "momentum_exit_threshold": 0.03571180555555555,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 344,
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
