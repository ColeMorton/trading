"""
VectorBT Strategy Parameters
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-22T12:35:32.609206
Confidence Level: 0.9
Total Strategies: 6
"""

import numpy as np
import pandas as pd
import vectorbt as vbt

# Statistical analysis-derived parameters
exit_parameters = {
    "MA_SMA_78_82_MA_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 454,
        "trailing_stop": 0.033,
        "min_holding_days": 21,
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 62,
        "statistical_validity": "MEDIUM",
    },
    "ASML_SMA_71_80_ASML_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 432,
        "trailing_stop": 0.0434,
        "min_holding_days": 21,
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 77,
        "statistical_validity": "MEDIUM",
    },
    "AAPL_SMA_46_56_AAPL_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 456,
        "trailing_stop": 0.0322,
        "min_holding_days": 21,
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 126,
        "statistical_validity": "HIGH",
    },
    "TSLA_SMA_23_31_TSLA_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 447,
        "trailing_stop": 0.0857,
        "min_holding_days": 21,
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 74,
        "statistical_validity": "MEDIUM",
    },
    "NI_SMA_66_81_NI_D": {
        "take_profit": 0.11789999999999999,
        "stop_loss": 0.0786,
        "max_holding_days": 180,
        "trailing_stop": 0.025699999999999997,
        "min_holding_days": 32,
        "momentum_exit_threshold": 0.04853751288732967,
        "trend_exit_threshold": 0.0030407314882599365,
        "confidence_level": 0.9,
        "sample_size": 112,
        "statistical_validity": "HIGH",
    },
    "APP_SMA_14_15_APP_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 455,
        "trailing_stop": 0.0867,
        "min_holding_days": 21,
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 61,
        "statistical_validity": "MEDIUM",
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
