"""
VectorBT Strategy Parameters
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-17T09:09:40.576421
Confidence Level: 0.9
Total Strategies: 5
"""

import vectorbt as vbt
import pandas as pd
import numpy as np

# Statistical analysis-derived parameters
exit_parameters = {'MA_SMA_78_82_MA_D': {'take_profit': 0.15, 'stop_loss': 0.08, 'max_holding_days': 468, 'trailing_stop': 0.032799999999999996, 'min_holding_days': 21, 'momentum_exit_threshold': 0.02, 'trend_exit_threshold': 0.015, 'confidence_level': 0.9, 'sample_size': 100, 'statistical_validity': 'LOW'}, 'ASML_SMA_71_80_ASML_D': {'take_profit': 0.1432, 'stop_loss': 0.0704, 'max_holding_days': 288, 'trailing_stop': 0.0403, 'min_holding_days': 4, 'momentum_exit_threshold': 0.02, 'trend_exit_threshold': 0.015, 'confidence_level': 0.9, 'sample_size': 76, 'statistical_validity': 'MEDIUM'}, 'TSLA_SMA_20_28_TSLA_D': {'take_profit': 0.15, 'stop_loss': 0.08, 'max_holding_days': 482, 'trailing_stop': 0.0891, 'min_holding_days': 21, 'momentum_exit_threshold': 0.02, 'trend_exit_threshold': 0.015, 'confidence_level': 0.9, 'sample_size': 79, 'statistical_validity': 'MEDIUM'}, 'NI_SMA_66_81_NI_D': {'take_profit': 0.1176, 'stop_loss': 0.0784, 'max_holding_days': 180, 'trailing_stop': 0.0269, 'min_holding_days': 28, 'momentum_exit_threshold': 0.04851480882488375, 'trend_exit_threshold': 0.0030407314882599356, 'confidence_level': 0.9, 'sample_size': 112, 'statistical_validity': 'HIGH'}, 'APP_SMA_14_15_APP_D': {'take_profit': 0.15, 'stop_loss': 0.08, 'max_holding_days': 457, 'trailing_stop': 0.0897, 'min_holding_days': 21, 'momentum_exit_threshold': 0.02, 'trend_exit_threshold': 0.015, 'confidence_level': 0.9, 'sample_size': 60, 'statistical_validity': 'MEDIUM'}}

# Parameter validation function
def validate_parameters(strategy_key):
    """Validate parameter reliability for strategy"""
    if strategy_key not in exit_parameters:
        return False, "Strategy not found"

    params = exit_parameters[strategy_key]
    sample_size = params.get('sample_size', 0)
    validity = params.get('statistical_validity', 'LOW')

    if validity == 'HIGH':
        return True, "High reliability parameters"
    elif validity == 'MEDIUM':
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
    entries = data['entries']  # Your entry signals

    # Create exit conditions
    take_profit_exits = data['close'] >= data['entry_price'] * (1 + params['take_profit'])
    stop_loss_exits = data['close'] <= data['entry_price'] * (1 - params['stop_loss'])

    # Combine exit conditions
    exits = take_profit_exits | stop_loss_exits

    return entries, exits

# Framework compatibility validation
framework_compatibility = {
    'vectorbt_version': '>=0.25.0',
    'parameter_format': 'dictionary',
    'validation_status': 'PASSED'
}
