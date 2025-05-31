"""
Concurrency Configuration Defaults Module.

This module provides default configuration values and validation for the
concurrency analysis system, addressing the root causes identified in the
performance discrepancy investigation.
"""

from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field
import json
from pathlib import Path

from app.tools.stop_loss_config import StopLossMode
from app.concurrency.tools.signal_definition import SignalDefinitionMode
from app.concurrency.tools.execution_timing import ExecutionMode
from app.concurrency.tools.allocation_strategy import AllocationMode
from app.concurrency.tools.correlation_filter import CorrelationFilterMode, ConcurrencyLimitMode


@dataclass
class ConcurrencyDefaults:
    """Default configuration values for concurrency analysis."""
    
    # Stop Loss Configuration - Only use values from CSV file
    STOP_LOSS_MODE: str = StopLossMode.OPTIONAL.value  # Only apply if explicitly defined in CSV
    SL_CANDLE_CLOSE: bool = True
    
    # Signal Definition Configuration
    SIGNAL_DEFINITION_MODE: str = SignalDefinitionMode.COMPLETE_TRADE.value  # Match backtest behavior
    
    # Execution Timing Configuration
    EXECUTION_MODE: str = ExecutionMode.SAME_PERIOD.value  # Reduce implementation lag
    
    # Allocation Configuration - Only use values from CSV file
    ALLOCATION_MODE: str = AllocationMode.CUSTOM.value  # Use allocations from CSV file
    
    # Correlation Filter Configuration - Disabled as requested
    CORRELATION_FILTER_MODE: str = CorrelationFilterMode.DISABLED.value
    
    # Concurrency Limit Configuration - Disabled as requested
    CONCURRENCY_LIMIT_MODE: str = ConcurrencyLimitMode.DISABLED.value
    
    # General Configuration
    # PORTFOLIO: str = "trades_20250530.csv"
    # PORTFOLIO: str = "BTC_d_20250530.csv"
    # PORTFOLIO: str = "portfolio_risk.csv"
    PORTFOLIO: str = "portfolio_d_20250530.csv"
    # PORTFOLIO: str = "QQQ_d_20250529.csv"
    BASE_DIR: str = ""  # Will be set to project root
    REFRESH: bool = True
    VISUALIZATION: bool = False
    CSV_USE_HOURLY: bool = False
    SORT_BY: str = "score"
    REPORT_INCLUDES: Dict[str, bool] = field(default_factory=lambda: {
        "TICKER_METRICS": True,
        "STRATEGIES": True,
        "STRATEGY_RELATIONSHIPS": True
    })
    ENSURE_COUNTERPART: bool = True
    INITIAL_VALUE: float = 10000.0
    TARGET_VAR: float = 0.05
    MAX_RISK: Dict[str, float] = field(default_factory=lambda: {
        "STRATEGY": 100.0
    })


def get_default_config() -> Dict[str, Any]:
    """Get default configuration as a dictionary.
    
    Returns:
        Dict[str, Any]: Default configuration dictionary
    """
    defaults = ConcurrencyDefaults()
    
    # Convert dataclass to dictionary
    config = {}
    for key, value in defaults.__dict__.items():
        config[key] = value
    
    return config


def validate_config(config: Dict[str, Any], log: Optional[Callable[[str, str], None]] = None) -> Dict[str, Any]:
    """Validate and normalize configuration.
    
    Args:
        config: Configuration dictionary
        log: Optional logging function
        
    Returns:
        Dict[str, Any]: Validated configuration dictionary
    """
    # Start with default configuration
    defaults = get_default_config()
    
    # Merge with provided configuration
    validated = defaults.copy()
    for key, value in config.items():
        if key in defaults:
            validated[key] = value
    
    # Validate specific fields
    
    # Stop Loss Mode
    if validated["STOP_LOSS_MODE"] not in [mode.value for mode in StopLossMode]:
        if log:
            log(f"Invalid STOP_LOSS_MODE: {validated['STOP_LOSS_MODE']}. Using default: {defaults['STOP_LOSS_MODE']}", "warning")
        validated["STOP_LOSS_MODE"] = defaults["STOP_LOSS_MODE"]
    
    # Default Stop Loss
    if not isinstance(validated["DEFAULT_STOP_LOSS"], (int, float)) or validated["DEFAULT_STOP_LOSS"] <= 0 or validated["DEFAULT_STOP_LOSS"] >= 1:
        if log:
            log(f"Invalid DEFAULT_STOP_LOSS: {validated['DEFAULT_STOP_LOSS']}. Using default: {defaults['DEFAULT_STOP_LOSS']}", "warning")
        validated["DEFAULT_STOP_LOSS"] = defaults["DEFAULT_STOP_LOSS"]
    
    # Signal Definition Mode
    if validated["SIGNAL_DEFINITION_MODE"] not in [mode.value for mode in SignalDefinitionMode]:
        if log:
            log(f"Invalid SIGNAL_DEFINITION_MODE: {validated['SIGNAL_DEFINITION_MODE']}. Using default: {defaults['SIGNAL_DEFINITION_MODE']}", "warning")
        validated["SIGNAL_DEFINITION_MODE"] = defaults["SIGNAL_DEFINITION_MODE"]
    
    # Execution Mode
    if validated["EXECUTION_MODE"] not in [mode.value for mode in ExecutionMode]:
        if log:
            log(f"Invalid EXECUTION_MODE: {validated['EXECUTION_MODE']}. Using default: {defaults['EXECUTION_MODE']}", "warning")
        validated["EXECUTION_MODE"] = defaults["EXECUTION_MODE"]
    
    # Allocation Mode
    if validated["ALLOCATION_MODE"] not in [mode.value for mode in AllocationMode]:
        if log:
            log(f"Invalid ALLOCATION_MODE: {validated['ALLOCATION_MODE']}. Using default: {defaults['ALLOCATION_MODE']}", "warning")
        validated["ALLOCATION_MODE"] = defaults["ALLOCATION_MODE"]
    
    # Correlation Filter Mode
    if validated["CORRELATION_FILTER_MODE"] not in [mode.value for mode in CorrelationFilterMode]:
        if log:
            log(f"Invalid CORRELATION_FILTER_MODE: {validated['CORRELATION_FILTER_MODE']}. Using default: {defaults['CORRELATION_FILTER_MODE']}", "warning")
        validated["CORRELATION_FILTER_MODE"] = defaults["CORRELATION_FILTER_MODE"]
    
    # Concurrency Limit Mode
    if validated["CONCURRENCY_LIMIT_MODE"] not in [mode.value for mode in ConcurrencyLimitMode]:
        if log:
            log(f"Invalid CONCURRENCY_LIMIT_MODE: {validated['CONCURRENCY_LIMIT_MODE']}. Using default: {defaults['CONCURRENCY_LIMIT_MODE']}", "warning")
        validated["CONCURRENCY_LIMIT_MODE"] = defaults["CONCURRENCY_LIMIT_MODE"]
    
    if log:
        log("Configuration validated successfully", "info")
    
    return validated


def save_config_to_file(config: Dict[str, Any], file_path: str, log: Optional[Callable[[str, str], None]] = None) -> bool:
    """Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        file_path: Path to save the configuration file
        log: Optional logging function
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write configuration to file
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        if log:
            log(f"Configuration saved to {file_path}", "info")
        
        return True
    
    except Exception as e:
        if log:
            log(f"Error saving configuration to {file_path}: {str(e)}", "error")
        
        return False


def load_config_from_file(file_path: str, log: Optional[Callable[[str, str], None]] = None) -> Dict[str, Any]:
    """Load configuration from a JSON file.
    
    Args:
        file_path: Path to the configuration file
        log: Optional logging function
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        # Check if file exists
        if not Path(file_path).exists():
            if log:
                log(f"Configuration file {file_path} not found. Using default configuration.", "warning")
            return get_default_config()
        
        # Read configuration from file
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        if log:
            log(f"Configuration loaded from {file_path}", "info")
        
        # Validate loaded configuration
        return validate_config(config, log)
    
    except Exception as e:
        if log:
            log(f"Error loading configuration from {file_path}: {str(e)}", "error")
        
        return get_default_config()


def get_optimized_config_for_mstr() -> Dict[str, Any]:
    """Get optimized configuration for MSTR strategies.
    
    This configuration addresses the root causes identified in the
    performance discrepancy investigation while respecting the requirement
    to only use stop losses and allocations from the CSV file.
    
    Returns:
        Dict[str, Any]: Optimized configuration dictionary
    """
    # Start with default configuration
    config = get_default_config()
    
    # Apply optimizations
    
    # 1. Stop Loss Configuration
    # Only use stop losses from CSV file
    config["STOP_LOSS_MODE"] = StopLossMode.OPTIONAL.value
    
    # 2. Signal Definition
    # Use complete trade signal definition to match backtest
    config["SIGNAL_DEFINITION_MODE"] = SignalDefinitionMode.COMPLETE_TRADE.value
    
    # 3. Execution Timing
    # Use same-period execution to reduce implementation lag
    config["EXECUTION_MODE"] = ExecutionMode.SAME_PERIOD.value
    
    # 4. Allocation Strategy
    # Only use allocations from CSV file
    config["ALLOCATION_MODE"] = AllocationMode.CUSTOM.value
    
    # 5. Correlation Filtering
    # Disabled as requested
    config["CORRELATION_FILTER_MODE"] = CorrelationFilterMode.DISABLED.value
    
    # 6. Concurrency Limits
    # Disabled as requested
    config["CONCURRENCY_LIMIT_MODE"] = ConcurrencyLimitMode.DISABLED.value
    
    # 7. Risk Calculation (always uses fixed implementation)
    # The mathematically correct implementation is now hardcoded
    
    # 8. Expectancy Calculation Fix
    # Use correct expectancy formula with proper win/loss rate calculation
    config["USE_FIXED_EXPECTANCY_CALC"] = True
    
    # 9. Win Rate Calculation Fix
    # Ensure win rate is calculated correctly based on actual trades
    config["USE_FIXED_WIN_RATE_CALC"] = True
    
    # 10. Signal Processing Fix
    # Use consistent signal processing that matches backtest behavior
    config["USE_FIXED_SIGNAL_PROC"] = True
    
    return config