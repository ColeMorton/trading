"""
VectorBT Strategy Parameters
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-06T12:09:04.587101
Confidence Level: 0.9
Total Strategies: 6
"""

import numpy as np
import pandas as pd
import vectorbt as vbt

# Statistical analysis-derived parameters
exit_parameters = {
    "MA_SMA_78_82_MA_D": {
        "take_profit": 0.2047,
        "stop_loss": 0.005,
        "max_holding_days": 180,
        "trailing_stop": 0.0263,
        "min_holding_days": 26,
        "momentum_exit_threshold": 0.0847856380472413,
        "trend_exit_threshold": 0.003062615153630616,
        "confidence_level": 0.9,
        "sample_size": 4807,
        "statistical_validity": "HIGH",
    },
    "RJF_SMA_68_77_RJF_D": {
        "take_profit": 0.163,
        "stop_loss": 0.0504,
        "max_holding_days": 179,
        "trailing_stop": 0.025699999999999997,
        "min_holding_days": 20,
        "momentum_exit_threshold": 0.07138174575888816,
        "trend_exit_threshold": 0.0030626151536306168,
        "confidence_level": 0.9,
        "sample_size": 10585,
        "statistical_validity": "HIGH",
    },
    "QCOM_SMA_49_66_QCOM_D": {
        "take_profit": 0.1887,
        "stop_loss": 0.0203,
        "max_holding_days": 160,
        "trailing_stop": 0.0326,
        "min_holding_days": 16,
        "momentum_exit_threshold": 0.07945265224572311,
        "trend_exit_threshold": 0.0030626151536306207,
        "confidence_level": 0.9,
        "sample_size": 8448,
        "statistical_validity": "HIGH",
    },
    "DOV_SMA_45_86_DOV_D": {
        "take_profit": 0.1273,
        "stop_loss": 0.0849,
        "max_holding_days": 180,
        "trailing_stop": 0.0294,
        "min_holding_days": 23,
        "momentum_exit_threshold": 0.06272246754747343,
        "trend_exit_threshold": 0.0030626151536306176,
        "confidence_level": 0.9,
        "sample_size": 11418,
        "statistical_validity": "HIGH",
    },
    "GME_SMA_53_61_GME_D": {
        "take_profit": 0.2021,
        "stop_loss": 0.0105,
        "max_holding_days": 88,
        "trailing_stop": 0.09140000000000001,
        "min_holding_days": 9,
        "momentum_exit_threshold": 0.08950364298628286,
        "trend_exit_threshold": 0.0030626151536306207,
        "confidence_level": 0.9,
        "sample_size": 5885,
        "statistical_validity": "HIGH",
    },
    "SCHW_SMA_20_26_SCHW_D": {
        "take_profit": 0.17300000000000001,
        "stop_loss": 0.0374,
        "max_holding_days": 154,
        "trailing_stop": 0.022099999999999998,
        "min_holding_days": 18,
        "momentum_exit_threshold": 0.07463739297460953,
        "trend_exit_threshold": 0.003062615153630621,
        "confidence_level": 0.9,
        "sample_size": 9518,
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
