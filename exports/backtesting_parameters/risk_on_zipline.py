"""
Zipline Algorithm Template
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-06T12:09:04.587101
Confidence Level: 0.9
Total Strategies: 6
"""

import numpy as np
import pandas as pd
import zipline
from zipline.api import cancel_order, get_open_orders, order_target, record, symbol

# Statistical parameters
exit_parameters = {
    "MA_SMA_78_82_MA_D": {
        "take_profit_pct": 20.47,
        "stop_loss_pct": 0.5,
        "max_holding_days": 180,
        "min_holding_days": 26,
        "trailing_stop_pct": 2.63,
        "confidence_level": 0.9,
        "sample_size": 4807,
        "statistical_validity": "HIGH",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.0847856380472413,
        "trend_exit_threshold": 0.003062615153630616,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-06T12:09:04.633478",
    },
    "RJF_SMA_68_77_RJF_D": {
        "take_profit_pct": 16.3,
        "stop_loss_pct": 5.04,
        "max_holding_days": 179,
        "min_holding_days": 20,
        "trailing_stop_pct": 2.57,
        "confidence_level": 0.9,
        "sample_size": 10585,
        "statistical_validity": "HIGH",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.07138174575888816,
        "trend_exit_threshold": 0.0030626151536306168,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-06T12:09:04.684091",
    },
    "QCOM_SMA_49_66_QCOM_D": {
        "take_profit_pct": 18.87,
        "stop_loss_pct": 2.03,
        "max_holding_days": 160,
        "min_holding_days": 16,
        "trailing_stop_pct": 3.26,
        "confidence_level": 0.9,
        "sample_size": 8448,
        "statistical_validity": "HIGH",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.07945265224572311,
        "trend_exit_threshold": 0.0030626151536306207,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-06T12:09:04.730001",
    },
    "DOV_SMA_45_86_DOV_D": {
        "take_profit_pct": 12.73,
        "stop_loss_pct": 8.49,
        "max_holding_days": 180,
        "min_holding_days": 23,
        "trailing_stop_pct": 2.94,
        "confidence_level": 0.9,
        "sample_size": 11418,
        "statistical_validity": "HIGH",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.06272246754747343,
        "trend_exit_threshold": 0.0030626151536306176,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-06T12:09:04.778842",
    },
    "GME_SMA_53_61_GME_D": {
        "take_profit_pct": 20.21,
        "stop_loss_pct": 1.05,
        "max_holding_days": 88,
        "min_holding_days": 9,
        "trailing_stop_pct": 9.14,
        "confidence_level": 0.9,
        "sample_size": 5885,
        "statistical_validity": "HIGH",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.08950364298628286,
        "trend_exit_threshold": 0.0030626151536306207,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-06T12:09:04.823085",
    },
    "SCHW_SMA_20_26_SCHW_D": {
        "take_profit_pct": 17.3,
        "stop_loss_pct": 3.74,
        "max_holding_days": 154,
        "min_holding_days": 18,
        "trailing_stop_pct": 2.21,
        "confidence_level": 0.9,
        "sample_size": 9518,
        "statistical_validity": "HIGH",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.07463739297460953,
        "trend_exit_threshold": 0.003062615153630621,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-06T12:09:04.869868",
    },
}


def initialize(context):
    """Initialize algorithm with statistical parameters"""
    # Set strategy parameters
    context.strategy_key = "your_strategy_key"  # Set this to your specific strategy

    if context.strategy_key not in exit_parameters:
        raise ValueError(f"No parameters found for strategy: {context.strategy_key}")

    context.params = exit_parameters[context.strategy_key]

    # Position tracking
    context.entry_price = None
    context.entry_date = None
    context.highest_price = None
    context.days_held = 0

    # Validate parameters
    if context.params["statistical_validity"] == "LOW":
        print(f"Warning: Low reliability parameters for {context.strategy_key}")

    print(f"Initialized with parameters: {context.params}")


def handle_data(context, data):
    """Main algorithm logic"""
    asset = symbol("SPY")  # Replace with your asset
    current_price = data.current(asset, "price")

    # Check if we have a position
    if context.portfolio.positions[asset].amount != 0:
        context.days_held += 1
        check_exit_conditions(context, data, asset, current_price)
    else:
        # Entry logic (implement your entry signals here)
        if should_enter_position(context, data, asset):
            enter_position(context, data, asset, current_price)


def should_enter_position(context, data, asset):
    """Implement your entry logic here"""
    # Placeholder - replace with your entry signals
    return False


def enter_position(context, data, asset, current_price):
    """Enter position and track entry details"""
    order_target(asset, 100)  # Adjust position size as needed

    context.entry_price = current_price
    context.entry_date = data.current_dt
    context.highest_price = current_price
    context.days_held = 0


def check_exit_conditions(context, data, asset, current_price):
    """Check statistical exit conditions"""
    if context.entry_price is None:
        return

    current_return = (current_price - context.entry_price) / context.entry_price * 100

    # Update highest price for trailing stop
    if current_price > context.highest_price:
        context.highest_price = current_price

    # Take profit condition
    if current_return >= context.params["take_profit_pct"]:
        order_target(asset, 0)
        record(exit_reason="take_profit", exit_return=current_return)
        reset_position_tracking(context)
        return

    # Stop loss condition
    if current_return <= -context.params["stop_loss_pct"]:
        order_target(asset, 0)
        record(exit_reason="stop_loss", exit_return=current_return)
        reset_position_tracking(context)
        return

    # Time-based exit
    # Statistical failsafe time exit (after primary dynamic criteria)
    if context.days_held >= context.params["max_holding_days"]:
        order_target(asset, 0)
        record(exit_reason="time_exit", exit_return=current_return)
        reset_position_tracking(context)
        return

    # Trailing stop (only after minimum holding period)
    if context.days_held >= context.params[
        "min_holding_days"
    ] and current_price <= context.highest_price * (
        1 - context.params["trailing_stop_pct"] / 100
    ):
        order_target(asset, 0)
        record(exit_reason="trailing_stop", exit_return=current_return)
        reset_position_tracking(context)
        return


def reset_position_tracking(context):
    """Reset position tracking variables"""
    context.entry_price = None
    context.entry_date = None
    context.highest_price = None
    context.days_held = 0
