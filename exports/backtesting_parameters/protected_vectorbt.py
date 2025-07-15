"""
VectorBT Strategy Parameters
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-15T13:07:01.979280
Confidence Level: 0.9
Total Strategies: 7
"""

import numpy as np
import pandas as pd
import vectorbt as vbt

# Statistical analysis-derived parameters
exit_parameters = {
    "RJF_SMA_68_77_RJF_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 440,
        "trailing_stop": 0.0288,
        "min_holding_days": 21,
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 112,
        "statistical_validity": "HIGH",
    },
    "QCOM_SMA_49_66_QCOM_D": {
        "take_profit": 0.1612,
        "stop_loss": 0.086,
        "max_holding_days": 132,
        "trailing_stop": 0.0398,
        "min_holding_days": 13,
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 100,
        "statistical_validity": "LOW",
    },
    "HWM_SMA_7_9_HWM_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 456,
        "trailing_stop": 0.0358,
        "min_holding_days": 21,
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 154,
        "statistical_validity": "HIGH",
    },
    "DOV_SMA_45_86_DOV_D": {
        "take_profit": 0.1612,
        "stop_loss": 0.086,
        "max_holding_days": 180,
        "trailing_stop": 0.0291,
        "min_holding_days": 25,
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 100,
        "statistical_validity": "LOW",
    },
    "TPR_SMA_14_30_TPR_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 458,
        "trailing_stop": 0.0371,
        "min_holding_days": 21,
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 107,
        "statistical_validity": "HIGH",
    },
    "RTX_EMA_27_41_RTX_D": {
        "take_profit": 0.15,
        "stop_loss": 0.08,
        "max_holding_days": 468,
        "trailing_stop": 0.0315,
        "min_holding_days": 21,
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "confidence_level": 0.9,
        "sample_size": 100,
        "statistical_validity": "LOW",
    },
    "SCHW_SMA_20_26_SCHW_D": {
        "take_profit": 0.1376,
        "stop_loss": 0.08109999999999999,
        "max_holding_days": 136,
        "trailing_stop": 0.025699999999999997,
        "min_holding_days": 14,
        "momentum_exit_threshold": 0.06234860657481649,
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
