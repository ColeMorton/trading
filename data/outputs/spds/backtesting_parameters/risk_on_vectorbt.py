"""
VectorBT Strategy Parameters
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-31T12:35:16.836369
Confidence Level: 0.9
Total Strategies: 2
"""

import numpy as np
import pandas as pd
import vectorbt as vbt

# Statistical analysis-derived parameters
exit_parameters = {'AMZN_SMA_77_81_AMZN_D': {'take_profit': 0.1509, 'stop_loss': 0.0805, 'max_holding_days': 83, 'trailing_stop': 0.0316, 'min_holding_days': 11, 'momentum_exit_threshold': 0.02, 'trend_exit_threshold': 0.015, 'confidence_level': 0.9, 'sample_size': 100, 'statistical_validity': 'LOW'}, 'ASML_SMA_71_80_ASML_D': {'take_profit': 0.15, 'stop_loss': 0.08, 'max_holding_days': 454, 'trailing_stop': 0.0454, 'min_holding_days': 21, 'momentum_exit_threshold': 0.02, 'trend_exit_threshold': 0.015, 'confidence_level': 0.9, 'sample_size': 77, 'statistical_validity': 'MEDIUM'}}

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
