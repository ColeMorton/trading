"""
Zipline Algorithm Template
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-22T12:35:32.609206
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
        "take_profit_pct": 15.0,
        "stop_loss_pct": 8.0,
        "max_holding_days": 454,
        "min_holding_days": 21,
        "trailing_stop_pct": 3.3,
        "confidence_level": 0.9,
        "sample_size": 62,
        "statistical_validity": "MEDIUM",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-22T12:35:32.622382",
    },
    "ASML_SMA_71_80_ASML_D": {
        "take_profit_pct": 15.0,
        "stop_loss_pct": 8.0,
        "max_holding_days": 432,
        "min_holding_days": 21,
        "trailing_stop_pct": 4.34,
        "confidence_level": 0.9,
        "sample_size": 77,
        "statistical_validity": "MEDIUM",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-22T12:35:32.631406",
    },
    "AAPL_SMA_46_56_AAPL_D": {
        "take_profit_pct": 15.0,
        "stop_loss_pct": 8.0,
        "max_holding_days": 456,
        "min_holding_days": 21,
        "trailing_stop_pct": 3.22,
        "confidence_level": 0.9,
        "sample_size": 126,
        "statistical_validity": "HIGH",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-22T12:35:32.642973",
    },
    "TSLA_SMA_23_31_TSLA_D": {
        "take_profit_pct": 15.0,
        "stop_loss_pct": 8.0,
        "max_holding_days": 447,
        "min_holding_days": 21,
        "trailing_stop_pct": 8.57,
        "confidence_level": 0.9,
        "sample_size": 74,
        "statistical_validity": "MEDIUM",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-22T12:35:32.648139",
    },
    "NI_SMA_66_81_NI_D": {
        "take_profit_pct": 11.79,
        "stop_loss_pct": 7.86,
        "max_holding_days": 180,
        "min_holding_days": 32,
        "trailing_stop_pct": 2.57,
        "confidence_level": 0.9,
        "sample_size": 112,
        "statistical_validity": "HIGH",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.04853751288732967,
        "trend_exit_threshold": 0.0030407314882599365,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-22T12:35:32.668983",
    },
    "APP_SMA_14_15_APP_D": {
        "take_profit_pct": 15.0,
        "stop_loss_pct": 8.0,
        "max_holding_days": 455,
        "min_holding_days": 21,
        "trailing_stop_pct": 8.67,
        "confidence_level": 0.9,
        "sample_size": 61,
        "statistical_validity": "MEDIUM",
        "entry_signal": "STATISTICAL_DIVERGENCE",
        "momentum_exit_threshold": 0.02,
        "trend_exit_threshold": 0.015,
        "derivation_method": "advanced_quantitative_optimization",
        "generation_timestamp": "2025-07-22T12:35:32.671665",
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
