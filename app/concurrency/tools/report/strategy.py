"""Strategy object creation utilities for concurrency analysis.

This module provides functionality for creating strategy objects from configuration and statistics.
"""

from typing import Dict, Any, TypedDict

# Import types from the parent module
from app.concurrency.tools.types import (
    StrategyParameters,
    StrategyPerformance,
    StrategyRiskMetrics,
    EfficiencyMetrics,
    SignalMetrics,
    Strategy
)

class StrategyParameter(TypedDict):
    """Parameter definition with value and description."""
    value: Any
    description: str

def create_strategy_object(
    config: Dict[str, Any],
    index: int,
    stats: Dict[str, Any]
) -> Strategy:
    """Create a strategy object with the optimized structure.

    Args:
        config (Dict[str, Any]): Strategy configuration
        index (int): Strategy index for ID generation
        stats (Dict[str, Any]): Statistics containing risk and efficiency metrics

    Returns:
        Strategy: Strategy object with parameters, performance, risk metrics, and efficiency metrics
    """
    # Determine strategy type
    strategy_type = config.get("STRATEGY_TYPE", "EMA")
    
    # Check if this is a MACD strategy based on the presence of SIGNAL_WINDOW
    if "SIGNAL_WINDOW" in config and config["SIGNAL_WINDOW"] > 0:
        strategy_type = "MACD"
    
    # Also check for explicit type field which might come from JSON portfolios
    if "type" in config:
        strategy_type = config["type"]
    strategy_id = str(index)
    
    # Create base parameters
    parameters: StrategyParameters = {
        "ticker": {
            "value": config["TICKER"],
            "description": "Ticker symbol to analyze"
        },
        "timeframe": {
            "value": "Hourly" if config.get("USE_HOURLY", False) else "Daily",
            "description": "Trading timeframe (Hourly or Daily)"
        },
        "type": {
            "value": strategy_type,
            "description": f"Strategy type ({strategy_type})"
        },
        "direction": {
            "value": config.get("DIRECTION", "Long"),
            "description": "Trading direction (Long or Short)"
        }
    }
    
    # Add strategy-specific parameters based on type
    if strategy_type == "ATR":
        # ATR strategy parameters
        if "length" in config:
            parameters["length"] = {
                "value": config["length"],
                "description": "ATR calculation period"
            }
        if "multiplier" in config:
            parameters["multiplier"] = {
                "value": config["multiplier"],
                "description": "ATR multiplier for stop distance"
            }
    else:
        # MA and MACD strategy parameters
        if "SHORT_WINDOW" in config:
            parameters["short_window"] = {
                "value": config["SHORT_WINDOW"],
                "description": "Period for short moving average or MACD fast line"
            }
        if "LONG_WINDOW" in config:
            parameters["long_window"] = {
                "value": config["LONG_WINDOW"],
                "description": "Period for long moving average or MACD slow line"
            }
        
        # Add signal_window for MACD strategies
        if strategy_type == "MACD" and "SIGNAL_WINDOW" in config:
            parameters["signal_window"] = {
                "value": config["SIGNAL_WINDOW"],
                "description": "Period for MACD signal line"
            }
    
    # Add RSI parameters if present
    if config.get("USE_RSI", False) and "RSI_WINDOW" in config:
        parameters["rsi_period"] = {
            "value": config["RSI_WINDOW"],
            "description": "Period for RSI calculation"
        }
        parameters["rsi_threshold"] = {
            "value": config["RSI_THRESHOLD"],
            "description": "RSI threshold for signal filtering"
        }
    
    # Add stop loss if present
    if "STOP_LOSS" in config:
        parameters["stop_loss"] = {
            "value": config["STOP_LOSS"],
            "description": "Stop loss percentage"
        }
    
    # Performance object removed as requested
    
    # Extract strategy-specific risk metrics
    risk_metrics_data = stats.get('risk_metrics', {})
    
    risk_metrics: StrategyRiskMetrics = {
        "var_95": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_var_95", 0.0),
            "description": "Value at Risk (95% confidence)"
        },
        "cvar_95": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_cvar_95", 0.0),
            "description": "Conditional Value at Risk (95% confidence)"
        },
        "var_99": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_var_99", 0.0),
            "description": "Value at Risk (99% confidence)"
        },
        "cvar_99": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_cvar_99", 0.0),
            "description": "Conditional Value at Risk (99% confidence)"
        },
        "risk_contribution": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_risk_contrib", 0.0),
            "description": "Contribution to portfolio risk"
        },
        "alpha_to_portfolio": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_alpha_to_portfolio", 0.0),
            "description": "Strategy alpha relative to portfolio"
        }
    }
    
    # Get strategy-specific efficiency metrics
    strategy_metrics = stats.get("strategy_efficiency_metrics", {})
    
    efficiency: EfficiencyMetrics = {
        "efficiency_score": {
            "value": strategy_metrics.get(f"strategy_{strategy_id}_efficiency_score", 0.0),
            "description": "Risk-adjusted performance score for this strategy"
        },
        "expectancy": {
            "value": strategy_metrics.get(f"strategy_{strategy_id}_expectancy", 0.0),
            "description": "Expectancy per Trade"
        },
        "multipliers": {
            "diversification": {
                "value": strategy_metrics.get(f"strategy_{strategy_id}_diversification", 0.0),
                "description": "Strategy-specific diversification effect"
            },
            "independence": {
                "value": strategy_metrics.get(f"strategy_{strategy_id}_independence", 0.0),
                "description": "Strategy-specific independence from other strategies"
            },
            "activity": {
                "value": strategy_metrics.get(f"strategy_{strategy_id}_activity", 0.0),
                "description": "Strategy-specific activity level impact"
            }
        }
    }

    # Get strategy-specific signal metrics
    signal_metrics = stats.get("signal_metrics", {})
    strategy_key = f"strategy_{index}"
    
    # Calculate mean signals per month for this strategy
    mean_signals = signal_metrics.get(f"{strategy_key}_mean_signals", 0.0)
    median_signals = signal_metrics.get(f"{strategy_key}_median_signals", 0.0)
    std_signals = signal_metrics.get(f"{strategy_key}_signal_volatility", 0.0)
    total_signals = signal_metrics.get(f"{strategy_key}_total_signals", 0.0)
    max_monthly = signal_metrics.get(f"{strategy_key}_max_monthly_signals", 0.0)
    min_monthly = signal_metrics.get(f"{strategy_key}_min_monthly_signals", 0.0)
    
    signals: SignalMetrics = {
        "monthly_statistics": {
            "mean": {
                "value": mean_signals,
                "description": "Average number of signals per month"
            },
            "median": {
                "value": median_signals,
                "description": "Median number of signals per month"
            },
            "std_below": {
                "value": max(0.0, mean_signals - std_signals),
                "description": "One standard deviation below mean signals"
            },
            "std_above": {
                "value": mean_signals + std_signals,
                "description": "One standard deviation above mean signals"
            }
        },
        "summary": {
            "volatility": {
                "value": std_signals,
                "description": "Standard deviation of monthly signals"
            },
            "max_monthly": {
                "value": max_monthly,
                "description": "Maximum signals in any month"
            },
            "min_monthly": {
                "value": min_monthly,
                "description": "Minimum signals in any month"
            },
            "total": {
                "value": total_signals,
                "description": "Total number of signals across period"
            }
        }
    }
    
    # Get strategy-specific signal quality metrics if available
    signal_quality_metrics_data = stats.get("signal_quality_metrics", {}).get(f"strategy_{strategy_id}", {})
    
    # Only include signal quality metrics if they exist
    strategy_obj: Strategy = {
        "id": f"strategy_{strategy_id}",
        "parameters": parameters,
        # Remove performance object as requested
        "risk_metrics": risk_metrics,
        "efficiency": efficiency,
        "signals": signals,
        "allocation_score": stats.get(f"strategy_{strategy_id}_allocation_score", 0.0),
        "allocation": stats.get(f"strategy_{strategy_id}_allocation", 0.0)
    }
    
    # Add signal quality metrics if available
    if signal_quality_metrics_data:
        strategy_obj["signal_quality_metrics"] = signal_quality_metrics_data
    
    # Add all portfolio metrics from the CSV file
    if hasattr(config, 'items'):  # Check if config is a dict-like object
        # Create a dictionary to store all strategy metrics
        metrics = {}
        
        # List of metrics to exclude (already included in other sections)
        exclude_metrics = [
            "TICKER", "SHORT_WINDOW", "LONG_WINDOW", "SIGNAL_WINDOW",
            "USE_HOURLY", "USE_RSI", "RSI_WINDOW", "RSI_THRESHOLD",
            "STOP_LOSS", "DIRECTION", "STRATEGY_TYPE", "EXPECTANCY_PER_MONTH",
            "BASE_DIR", "REFRESH", "USE_SMA", "SMA", "EMA", "PORTFOLIO_STATS",
            "type", "Short Window", "Long Window", "Signal Window", "EXPECTANCY",
            "EXPECTANCY_PER_TRADE", "length", "multiplier"
        ]
        
        # Add all metrics from the config
        for key, value in config.items():
            if key not in exclude_metrics and not key.startswith("_"):
                # Convert to proper format with value and description
                metrics[key] = {
                    "value": value,
                    "description": f"{key} metric from portfolio data"
                }
        
        # Add all metrics from the portfolio stats if available
        if "PORTFOLIO_STATS" in config and isinstance(config["PORTFOLIO_STATS"], dict):
            portfolio_stats = config["PORTFOLIO_STATS"]
            
            # Additional metrics to exclude
            additional_exclude = [
                "EXPECTANCY_PER_MONTH",  # Already included in other sections
                "Short Window", "Long Window", "Signal Window"  # Explicitly excluded as requested
            ]
            
            for key, value in portfolio_stats.items():
                # Skip keys that are excluded
                if key in additional_exclude:
                    continue
                
                # Convert to proper format with value and description
                metrics[key] = {
                    "value": value,
                    "description": f"{key} from strategy analysis"
                }
        
        # Only add the metrics field if there are metrics to include
        if metrics:
            strategy_obj["metrics"] = metrics
    
    return strategy_obj