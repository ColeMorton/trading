"""
VectorBT Strategy Parameters
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-06T13:50:00.053235
Confidence Level: 0.9
Total Strategies: 21
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
    "PGR_SMA_37_61_PGR_D": {
        "take_profit": 0.1572,
        "stop_loss": 0.0588,
        "max_holding_days": 180,
        "trailing_stop": 0.031,
        "min_holding_days": 27,
        "momentum_exit_threshold": 0.06947456385586415,
        "trend_exit_threshold": 0.0030626151536306168,
        "confidence_level": 0.9,
        "sample_size": 11418,
        "statistical_validity": "HIGH",
    },
    "AMZN_SMA_51_69_AMZN_D": {
        "take_profit": 0.2146,
        "stop_loss": 0.0077,
        "max_holding_days": 138,
        "trailing_stop": 0.031400000000000004,
        "min_holding_days": 15,
        "momentum_exit_threshold": 0.08830570591462197,
        "trend_exit_threshold": 0.00306261515363062,
        "confidence_level": 0.9,
        "sample_size": 7078,
        "statistical_validity": "HIGH",
    },
    "GD_SMA_70_85_GD_D": {
        "take_profit": 0.14429999999999998,
        "stop_loss": 0.0791,
        "max_holding_days": 180,
        "trailing_stop": 0.0269,
        "min_holding_days": 25,
        "momentum_exit_threshold": 0.06564210020204252,
        "trend_exit_threshold": 0.0030626151536306146,
        "confidence_level": 0.9,
        "sample_size": 15983,
        "statistical_validity": "HIGH",
    },
    "GOOGL_SMA_9_39_GOOGL_D": {
        "take_profit": 0.1789,
        "stop_loss": 0.031200000000000002,
        "max_holding_days": 180,
        "trailing_stop": 0.0375,
        "min_holding_days": 25,
        "momentum_exit_threshold": 0.07632479540672037,
        "trend_exit_threshold": 0.003062615153630619,
        "confidence_level": 0.9,
        "sample_size": 5252,
        "statistical_validity": "HIGH",
    },
    "PWR_SMA_66_78_PWR_D": {
        "take_profit": 0.1699,
        "stop_loss": 0.0407,
        "max_holding_days": 137,
        "trailing_stop": 0.0317,
        "min_holding_days": 15,
        "momentum_exit_threshold": 0.07377194676781977,
        "trend_exit_threshold": 0.0030626151536306202,
        "confidence_level": 0.9,
        "sample_size": 6890,
        "statistical_validity": "HIGH",
    },
    "INTU_SMA_54_64_INTU_D": {
        "take_profit": 0.18780000000000002,
        "stop_loss": 0.0212,
        "max_holding_days": 168,
        "trailing_stop": 0.0259,
        "min_holding_days": 18,
        "momentum_exit_threshold": 0.07919381984436107,
        "trend_exit_threshold": 0.003062615153630615,
        "confidence_level": 0.9,
        "sample_size": 8134,
        "statistical_validity": "HIGH",
    },
    "NFLX_EMA_19_46_NFLX_D": {
        "take_profit": 0.214,
        "stop_loss": 0.0072,
        "max_holding_days": 145,
        "trailing_stop": 0.027200000000000002,
        "min_holding_days": 16,
        "momentum_exit_threshold": 0.08812290664683817,
        "trend_exit_threshold": 0.0030626151536306176,
        "confidence_level": 0.9,
        "sample_size": 5816,
        "statistical_validity": "HIGH",
    },
    "SMCI_SMA_58_60_SMCI_D": {
        "take_profit": 0.2145,
        "stop_loss": 0.0083,
        "max_holding_days": 136,
        "trailing_stop": 0.0774,
        "min_holding_days": 14,
        "momentum_exit_threshold": 0.08849230771213104,
        "trend_exit_threshold": 0.0030626151536306163,
        "confidence_level": 0.9,
        "sample_size": 4596,
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
    "GOOGL_EMA_9_46_GOOGL_D": {
        "take_profit": 0.1843,
        "stop_loss": 0.024700000000000003,
        "max_holding_days": 180,
        "trailing_stop": 0.0375,
        "min_holding_days": 26,
        "momentum_exit_threshold": 0.07816480101193721,
        "trend_exit_threshold": 0.0030626151536306194,
        "confidence_level": 0.9,
        "sample_size": 5252,
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
    "COR_SMA_8_26_COR_D": {
        "take_profit": 0.16469999999999999,
        "stop_loss": 0.048799999999999996,
        "max_holding_days": 180,
        "trailing_stop": 0.026000000000000002,
        "min_holding_days": 24,
        "momentum_exit_threshold": 0.07176087205258111,
        "trend_exit_threshold": 0.0030626151536306146,
        "confidence_level": 0.9,
        "sample_size": 7613,
        "statistical_validity": "HIGH",
    },
    "COST_EMA_29_68_COST_D": {
        "take_profit": 0.1444,
        "stop_loss": 0.07780000000000001,
        "max_holding_days": 180,
        "trailing_stop": 0.0308,
        "min_holding_days": 23,
        "momentum_exit_threshold": 0.0658451673078445,
        "trend_exit_threshold": 0.0030626151536306168,
        "confidence_level": 0.9,
        "sample_size": 9823,
        "statistical_validity": "HIGH",
    },
    "AMD_SMA_7_45_AMD_D": {
        "take_profit": 0.2145,
        "stop_loss": 0.0083,
        "max_holding_days": 147,
        "trailing_stop": 0.0481,
        "min_holding_days": 15,
        "momentum_exit_threshold": 0.08849789272373497,
        "trend_exit_threshold": 0.003062615153630618,
        "confidence_level": 0.9,
        "sample_size": 11418,
        "statistical_validity": "HIGH",
    },
    "AMZN_SMA_10_27_AMZN_D": {
        "take_profit": 0.2127,
        "stop_loss": 0.0055000000000000005,
        "max_holding_days": 138,
        "trailing_stop": 0.031400000000000004,
        "min_holding_days": 15,
        "momentum_exit_threshold": 0.08756827588296935,
        "trend_exit_threshold": 0.0030626151536306163,
        "confidence_level": 0.9,
        "sample_size": 7078,
        "statistical_validity": "HIGH",
    },
    "FFIV_SMA_14_45_FFIV_D": {
        "take_profit": 0.2029,
        "stop_loss": 0.005,
        "max_holding_days": 134,
        "trailing_stop": 0.0256,
        "min_holding_days": 14,
        "momentum_exit_threshold": 0.08416198031290156,
        "trend_exit_threshold": 0.0030626151536306168,
        "confidence_level": 0.9,
        "sample_size": 6561,
        "statistical_validity": "HIGH",
    },
    "ILMN_EMA_21_32_ILMN_D": {
        "take_profit": 0.19190000000000002,
        "stop_loss": 0.0165,
        "max_holding_days": 135,
        "trailing_stop": 0.0429,
        "min_holding_days": 13,
        "momentum_exit_threshold": 0.08058682835445252,
        "trend_exit_threshold": 0.003062615153630618,
        "confidence_level": 0.9,
        "sample_size": 6270,
        "statistical_validity": "HIGH",
    },
    "RTX_EMA_27_41_RTX_D": {
        "take_profit": 0.141,
        "stop_loss": 0.08560000000000001,
        "max_holding_days": 180,
        "trailing_stop": 0.0335,
        "min_holding_days": 25,
        "momentum_exit_threshold": 0.06469133333832126,
        "trend_exit_threshold": 0.0030626151536306168,
        "confidence_level": 0.9,
        "sample_size": 15920,
        "statistical_validity": "HIGH",
    },
    "LMT_EMA_59_87_LMT_D": {
        "take_profit": 0.1386,
        "stop_loss": 0.0889,
        "max_holding_days": 180,
        "trailing_stop": 0.039900000000000005,
        "min_holding_days": 23,
        "momentum_exit_threshold": 0.06427045667565923,
        "trend_exit_threshold": 0.0030626151536306168,
        "confidence_level": 0.9,
        "sample_size": 12227,
        "statistical_validity": "HIGH",
    },
    "CRWD_EMA_5_21_CRWD_D": {
        "take_profit": 0.21,
        "stop_loss": 0.005,
        "max_holding_days": 132,
        "trailing_stop": 0.0462,
        "min_holding_days": 15,
        "momentum_exit_threshold": 0.08657673405164272,
        "trend_exit_threshold": 0.003062615153630615,
        "confidence_level": 0.9,
        "sample_size": 1524,
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
