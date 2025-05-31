"""
Signal Quality Metrics Module.

This module provides functions to calculate various signal quality metrics
for trading strategies, helping to quantify the value of each signal.
"""

import os
from typing import Dict, Any, Optional, Callable, List
import numpy as np
from app.tools.expectancy import calculate_expectancy
from app.tools.stop_loss_simulator import apply_stop_loss_to_signal_quality_metrics
import polars as pl
from .signal_processor import SignalProcessor, SignalDefinition

# Get configuration
USE_FIXED_SIGNAL_PROC = os.getenv('USE_FIXED_SIGNAL_PROC', 'true').lower() == 'true'

def calculate_signal_quality_metrics(
    signals_df: pl.DataFrame,
    returns_df: pl.DataFrame,
    strategy_id: str,
    log: Callable[[str, str], None],
    stop_loss: Optional[float] = None
) -> Dict[str, Any]:
    """Calculate signal quality metrics for a strategy.
    
    Args:
        signals_df (pl.DataFrame): DataFrame with Date and signal columns
        returns_df (pl.DataFrame): DataFrame with Date and return columns
        strategy_id (str): Strategy identifier
        log (Callable[[str, str], None]): Logging function
        
    Returns:
        Dict[str, Any]: Dictionary with signal quality metrics
    """
    try:
        # Ensure dataframes have required columns
        if "Date" not in signals_df.columns or "signal" not in signals_df.columns:
            log(f"Missing required columns in signals_df for {strategy_id}", "error")
            return {}
            
        if "Date" not in returns_df.columns or "return" not in returns_df.columns:
            log(f"Missing required columns in returns_df for {strategy_id}", "error")
            return {}
            
        # Join signals and returns on Date
        joined_df = signals_df.join(returns_df, on="Date", how="inner")
        
        # Extract signals and returns as numpy arrays
        signals_np = joined_df["signal"].fill_null(0).to_numpy()
        returns_np = joined_df["return"].fill_null(0).to_numpy()
        
        # Count signals using standardized processor
        if USE_FIXED_SIGNAL_PROC:
            signal_processor = SignalProcessor(use_fixed=True)
            signal_def = SignalDefinition(
                signal_column='signal',
                position_column='signal'  # Using signal column as position for this case
            )
            signal_counts = signal_processor.get_comprehensive_counts(joined_df, signal_def)
            signal_count = signal_counts.raw_signals
        else:
            # Legacy counting method
            signal_count = int(np.sum(signals_np != 0))
        
        if signal_count == 0:
            log(f"No signals found for {strategy_id}", "warning")
            return {
                "signal_count": 0,
                "signal_quality_score": 0.0
            }
        
        # Calculate signal returns (only when signal is active)
        signal_returns = returns_np[signals_np != 0]
        
        # Basic return metrics
        avg_return = float(np.mean(signal_returns))
        
        # Win rate using standardized signal-based calculation
        from app.concurrency.tools.win_rate_calculator import WinRateCalculator
        win_calc = WinRateCalculator()
        win_components = win_calc.calculate_signal_win_rate(returns_np, signals_np, include_zeros=False)
        win_rate = win_components.win_rate
        
        # Profit factor (sum of positive returns / abs sum of negative returns)
        positive_returns = signal_returns[signal_returns > 0]
        negative_returns = signal_returns[signal_returns < 0]
        
        profit_factor = 1.0
        if len(negative_returns) > 0 and np.sum(np.abs(negative_returns)) > 0:
            profit_factor = float(np.sum(positive_returns) / np.sum(np.abs(negative_returns)))
        
        # Average win and loss
        avg_win = float(np.mean(positive_returns)) if len(positive_returns) > 0 else 0.0
        avg_loss = float(np.mean(negative_returns)) if len(negative_returns) > 0 else 0.0
        
        # Risk-reward ratio
        risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 and avg_win != 0 else None
        
        # Expectancy per signal using standardized calculation
        # Handle the case where win_rate is 0 (all trades are losing)
        if win_rate == 0.0:
            expectancy_per_signal = -abs(avg_loss)
        else:
            expectancy_per_signal = calculate_expectancy(win_rate, avg_win, abs(avg_loss))
        
        # Handle NaN values in expectancy
        if np.isnan(expectancy_per_signal):
            expectancy_per_signal = 0.0
        
        # Risk-adjusted metrics
        std_returns = np.std(signal_returns)
        if std_returns > 0 and not np.isnan(std_returns) and not np.isnan(avg_return):
            sharpe_ratio = float(avg_return / std_returns)
        else:
            sharpe_ratio = 0.0
        
        # Sortino ratio (using downside deviation)
        downside_returns = signal_returns[signal_returns < 0]
        if len(downside_returns) > 0:
            downside_deviation = float(np.std(downside_returns))
            if downside_deviation > 0 and not np.isnan(downside_deviation) and not np.isnan(avg_return):
                sortino_ratio = float(avg_return / downside_deviation)
            else:
                sortino_ratio = 0.0
        else:
            downside_deviation = 0.001
            sortino_ratio = 0.0
        
        # Maximum drawdown
        cumulative_returns = np.cumsum(signal_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = running_max - cumulative_returns
        max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0
        
        # Calmar ratio (return / max drawdown)
        if max_drawdown > 0 and not np.isnan(max_drawdown) and not np.isnan(avg_return):
            calmar_ratio = float(avg_return / max_drawdown)
        else:
            calmar_ratio = 0.0
        
        # Signal efficiency (% of time signal is correct)
        signal_efficiency = win_rate
        
        # Signal consistency (lower standard deviation of returns is more consistent)
        return_volatility = float(np.std(signal_returns))
        signal_consistency = 1.0 / (1.0 + return_volatility) if return_volatility > 0 else 1.0
        
        # Calculate time horizons performance (1-day, 3-day, 5-day, 10-day)
        horizon_metrics = _calculate_horizon_metrics(signals_np, returns_np)
        
        # Find best horizon
        best_horizon = _find_best_horizon(horizon_metrics)
        
        # Calculate new advanced metrics
        
        # Signal Value Ratio (SVR)
        signal_value_ratio = _calculate_signal_value_ratio(
            avg_return, max_drawdown, signal_consistency
        )
        
        # Signal Conviction
        signal_conviction = _calculate_signal_conviction(signal_returns)
        
        # Signal Timing Efficiency
        signal_timing_efficiency = _calculate_signal_timing_efficiency(
            signals_np, returns_np
        )
        
        # Signal Opportunity Cost (using 0.0 as risk-free rate)
        signal_opportunity_cost = _calculate_signal_opportunity_cost(signal_returns)
        
        # Signal Reliability Index
        signal_reliability = _calculate_signal_reliability_index(signal_returns)
        
        # Calculate Risk-Adjusted Return (SRAR)
        # SRAR is a modified Sharpe that accounts for signal-specific characteristics
        if not np.isnan(sharpe_ratio) and not np.isnan(signal_efficiency) and not np.isnan(max_drawdown):
            signal_risk_adjusted_return = sharpe_ratio * (1.0 + signal_efficiency) * (1.0 - max_drawdown)
        else:
            signal_risk_adjusted_return = 0.0
        
        # Calculate overall signal quality score (weighted combination of metrics)
        signal_quality_score = _calculate_quality_score(
            win_rate, profit_factor, sharpe_ratio, sortino_ratio,
            signal_efficiency, signal_consistency,
            signal_value_ratio, signal_conviction, signal_timing_efficiency,
            signal_opportunity_cost, signal_reliability
        )
        
        # Apply stop loss adjustment if specified
        if stop_loss is not None and stop_loss > 0 and stop_loss < 1:
            # Convert signals and returns to numpy arrays for stop loss simulation
            signals_np = signals_np.copy()
            returns_np = returns_np.copy()
            
            log(f"Applying stop loss of {stop_loss*100:.2f}% to signal quality metrics for {strategy_id}", "info")
            
            # Apply stop loss to metrics
            metrics = {
                "signal_count": signal_count,
                "avg_return": avg_return,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "risk_reward_ratio": risk_reward_ratio,
                "expectancy_per_signal": expectancy_per_signal,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "calmar_ratio": calmar_ratio,
                "max_drawdown": max_drawdown,
                "signal_efficiency": signal_efficiency,
                "signal_consistency": signal_consistency,
                "signal_value_ratio": signal_value_ratio,
                "signal_conviction": signal_conviction,
                "signal_timing_efficiency": signal_timing_efficiency,
                "signal_opportunity_cost": signal_opportunity_cost,
                "signal_reliability": signal_reliability,
                "signal_risk_adjusted_return": signal_risk_adjusted_return,
                "signal_quality_score": signal_quality_score,
                "best_horizon": best_horizon,
                "horizon_metrics": horizon_metrics
            }
            
            # Apply stop loss adjustment
            adjusted_metrics = apply_stop_loss_to_signal_quality_metrics(
                metrics, returns_np, signals_np, stop_loss, log
            )
            
            log(f"Calculated stop-loss-adjusted signal quality metrics for {strategy_id}: score={adjusted_metrics['signal_quality_score']:.2f}, win_rate={adjusted_metrics['win_rate']:.2f}", "info")
            
            return adjusted_metrics
        
        log(f"Calculated signal quality metrics for {strategy_id}: score={signal_quality_score:.2f}, win_rate={win_rate:.2f}", "info")
        return {
            "signal_count": signal_count,
            "avg_return": avg_return,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "risk_reward_ratio": risk_reward_ratio,
            "expectancy_per_signal": expectancy_per_signal,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": calmar_ratio,
            "max_drawdown": max_drawdown,
            "signal_efficiency": signal_efficiency,
            "signal_consistency": signal_consistency,
            
            # New advanced metrics
            "signal_value_ratio": signal_value_ratio,
            "signal_conviction": signal_conviction,
            "signal_timing_efficiency": signal_timing_efficiency,
            "signal_opportunity_cost": signal_opportunity_cost,
            "signal_reliability": signal_reliability,
            "signal_risk_adjusted_return": signal_risk_adjusted_return,
            
            "signal_quality_score": signal_quality_score,
            "best_horizon": best_horizon,
            "horizon_metrics": horizon_metrics
        }
    except Exception as e:
        log(f"Error calculating signal quality metrics for {strategy_id}: {str(e)}", "error")
        return {}

def _calculate_metrics_for_strategy(
    signals: pl.Series,
    returns: pl.Series,
    strategy_id: str
) -> Dict[str, Any]:
    """Calculate signal quality metrics for a single strategy.
    
    Args:
        signals (pl.Series): Series of strategy signals
        returns (pl.Series): Series of strategy returns
        strategy_id (str): Strategy identifier
        
    Returns:
        Dict[str, Any]: Dictionary of signal quality metrics
    """
    # Convert to numpy for calculations
    signals_np = signals.to_numpy()
    returns_np = returns.to_numpy()
    
    # Count signals
    signal_count = int(np.sum(signals_np != 0))
    
    if signal_count == 0:
        return {
            "signal_count": 0,
            "signal_quality_score": 0.0
        }
    
    # Calculate signal returns (only when signal is active)
    signal_returns = returns_np[signals_np != 0]
    
    # Basic return metrics
    avg_return = float(np.mean(signal_returns))
    win_rate = float(np.mean(signal_returns > 0))
    
    # Profit factor (sum of positive returns / abs sum of negative returns)
    positive_returns = signal_returns[signal_returns > 0]
    negative_returns = signal_returns[signal_returns < 0]
    
    profit_factor = 1.0
    if len(negative_returns) > 0 and np.sum(np.abs(negative_returns)) > 0:
        profit_factor = float(np.sum(positive_returns) / np.sum(np.abs(negative_returns)))
    
    # Average win and loss
    avg_win = float(np.mean(positive_returns)) if len(positive_returns) > 0 else 0.0
    avg_loss = float(np.mean(negative_returns)) if len(negative_returns) > 0 else 0.0
    
    # Risk-reward ratio
    risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
    
    # Expectancy per signal using standardized calculation
    # Handle the case where win_rate is 0 (all trades are losing)
    if win_rate == 0.0:
        expectancy_per_signal = -abs(avg_loss)
    else:
        expectancy_per_signal = calculate_expectancy(win_rate, avg_win, abs(avg_loss))
    
    # Risk-adjusted metrics
    sharpe_ratio = float(avg_return / np.std(signal_returns)) if np.std(signal_returns) > 0 else 0.0
    
    # Sortino ratio (using downside deviation)
    downside_returns = signal_returns[signal_returns < 0]
    downside_deviation = float(np.std(downside_returns)) if len(downside_returns) > 0 else 0.001
    sortino_ratio = float(avg_return / downside_deviation) if downside_deviation > 0 else 0.0
    
    # Maximum drawdown
    cumulative_returns = np.cumsum(signal_returns)
    running_max = np.maximum.accumulate(cumulative_returns)
    drawdowns = running_max - cumulative_returns
    max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0
    
    # Calmar ratio (return / max drawdown)
    calmar_ratio = float(avg_return / max_drawdown) if max_drawdown > 0 else 0.0
    
    # Signal efficiency (% of time signal is correct)
    signal_efficiency = win_rate
    
    # Signal consistency (lower standard deviation of returns is more consistent)
    return_volatility = float(np.std(signal_returns))
    signal_consistency = 1.0 / (1.0 + return_volatility) if return_volatility > 0 else 1.0
    
    # Calculate time horizons performance (1-day, 3-day, 5-day, 10-day)
    horizon_metrics = _calculate_horizon_metrics(signals_np, returns_np)
    
    # Find best horizon
    best_horizon = _find_best_horizon(horizon_metrics)
    
    # Calculate new advanced metrics
    
    # Signal Value Ratio (SVR)
    signal_value_ratio = _calculate_signal_value_ratio(
        avg_return, max_drawdown, signal_consistency
    )
    
    # Signal Conviction
    signal_conviction = _calculate_signal_conviction(signal_returns)
    
    # Signal Timing Efficiency
    signal_timing_efficiency = _calculate_signal_timing_efficiency(
        signals_np, returns_np
    )
    
    # Signal Opportunity Cost (using 0.0 as risk-free rate)
    signal_opportunity_cost = _calculate_signal_opportunity_cost(signal_returns)
    
    # Signal Reliability Index
    signal_reliability = _calculate_signal_reliability_index(signal_returns)
    
    # Calculate Risk-Adjusted Return (SRAR)
    # SRAR is a modified Sharpe that accounts for signal-specific characteristics
    signal_risk_adjusted_return = sharpe_ratio * (1.0 + signal_efficiency) * (1.0 - max_drawdown)
    
    # Calculate overall signal quality score (weighted combination of metrics)
    signal_quality_score = _calculate_quality_score(
        win_rate, profit_factor, sharpe_ratio, sortino_ratio,
        signal_efficiency, signal_consistency,
        signal_value_ratio, signal_conviction, signal_timing_efficiency,
        signal_opportunity_cost, signal_reliability
    )
    
    return {
        "signal_count": signal_count,
        "avg_return": avg_return,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "risk_reward_ratio": risk_reward_ratio,
        "expectancy_per_signal": expectancy_per_signal,
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sortino_ratio,
        "calmar_ratio": calmar_ratio,
        "max_drawdown": max_drawdown,
        "signal_efficiency": signal_efficiency,
        "signal_consistency": signal_consistency,
        
        # New advanced metrics
        "signal_value_ratio": signal_value_ratio,
        "signal_conviction": signal_conviction,
        "signal_timing_efficiency": signal_timing_efficiency,
        "signal_opportunity_cost": signal_opportunity_cost,
        "signal_reliability": signal_reliability,
        "signal_risk_adjusted_return": signal_risk_adjusted_return,
        
        "signal_quality_score": signal_quality_score,
        "best_horizon": best_horizon,
        "horizon_metrics": horizon_metrics
    }

def _calculate_horizon_metrics(
    signals: np.ndarray,
    returns: np.ndarray
) -> Dict[str, Dict[str, float]]:
    """Calculate performance metrics for different time horizons using proper out-of-sample methodology.
    
    This function evaluates signal performance across different time horizons without
    introducing forward-looking bias. It uses a walk-forward approach where signals
    are evaluated only using data that would have been available at the time of the signal.
    
    Args:
        signals (np.ndarray): Array of strategy signals
        returns (np.ndarray): Array of strategy returns
        
    Returns:
        Dict[str, Dict[str, float]]: Dictionary of horizon metrics
    """
    horizons = [1, 3, 5, 10]
    results = {}
    
    # Create a position array from signals
    # A position at time t is determined by the signal at time t-1
    # and is maintained until a closing signal
    positions = np.zeros_like(signals)
    for i in range(1, len(signals)):
        if signals[i-1] != 0:
            # New signal creates a new position
            positions[i] = signals[i-1]
        elif positions[i-1] != 0 and signals[i-1] == 0:
            # Maintain position if no new signal and we have an existing position
            positions[i] = positions[i-1]
    
    for horizon in horizons:
        # Skip if we don't have enough data
        if len(returns) <= horizon:
            continue
        
        # Initialize arrays to store horizon returns for each position
        horizon_returns = []
        
        # For each position, calculate the return over the specified horizon
        # but only using data that would have been available at that time
        for i in range(len(positions) - horizon):
            if positions[i] != 0:  # If there's an active position
                # Calculate return over the horizon
                # For long positions, we want positive returns
                # For short positions, we want negative returns
                if positions[i] > 0:  # Long position
                    horizon_return = np.sum(returns[i:i+horizon])
                else:  # Short position
                    horizon_return = -np.sum(returns[i:i+horizon])
                
                horizon_returns.append(horizon_return)
        
        # Skip if no positions were active
        if len(horizon_returns) == 0:
            continue
        
        # Convert to numpy array for calculations
        horizon_returns_np = np.array(horizon_returns)
        # Calculate metrics for this horizon
        avg_return = float(np.mean(horizon_returns_np))
        win_rate = float(np.mean(horizon_returns_np > 0))
        std_dev = np.std(horizon_returns_np)
        sharpe = float(avg_return / std_dev) if std_dev > 0 else 0.0
        sharpe = float(avg_return / np.std(horizon_returns_np)) if np.std(horizon_returns_np) > 0 else 0.0
        
        results[str(horizon)] = {
            "avg_return": avg_return,
            "win_rate": win_rate,
            "sharpe": sharpe,
            "sample_size": len(horizon_returns_np)  # Add sample size for context
        }
    
    return results

def _find_best_horizon(
    horizon_metrics: Dict[str, Dict[str, float]],
    min_sample_size: int = 10  # Reduced from 20 to make it easier to find valid horizons
) -> int:
    """Find the best performing time horizon based on multiple criteria.
    
    This function selects the best horizon based on a combination of Sharpe ratio,
    win rate, and sample size. It ensures that the selected horizon has sufficient
    data points to be statistically meaningful.
    
    Args:
        horizon_metrics (Dict[str, Dict[str, float]]): Dictionary of horizon metrics
        min_sample_size (int): Minimum sample size required for a horizon to be considered
        
    Returns:
        int: Best horizon (defaults to 1 if no valid horizons)
    """
    if not horizon_metrics:
        return 1  # Default to 1-day horizon if no metrics available
        
    best_horizon = 1  # Default to 1-day horizon
    best_score = -float('inf')
    
    for horizon_str, metrics in horizon_metrics.items():
        # Get metrics with defaults
        sharpe = metrics.get("sharpe", 0)
        win_rate = metrics.get("win_rate", 0)
        sample_size = metrics.get("sample_size", 0)
        
        # Skip horizons with insufficient data
        if sample_size < min_sample_size:
            continue
        
        # Calculate a combined score that considers multiple factors
        # - Sharpe ratio (risk-adjusted return)
        # - Win rate (consistency)
        # - Sample size (statistical significance)
        sample_size_factor = min(1.0, sample_size / 100)  # Cap at 100 samples
        combined_score = (0.6 * sharpe) + (0.3 * win_rate) + (0.1 * sample_size_factor)
        
        if combined_score > best_score:
            best_score = combined_score
            best_horizon = int(horizon_str)
    
    return best_horizon  # Will return the default (1) if no valid horizons were found

def _calculate_signal_value_ratio(
    avg_return: float,
    max_drawdown: float,
    signal_consistency: float
) -> float:
    """Calculate Signal Value Ratio (SVR).
    
    SVR combines return, risk, and consistency into a single metric that
    quantifies the overall value of a signal.
    
    Args:
        avg_return (float): Average return per signal
        max_drawdown (float): Maximum drawdown
        signal_consistency (float): Signal consistency
        
    Returns:
        float: Signal Value Ratio
    """
    # Avoid division by zero
    safe_drawdown = max(max_drawdown, 0.001)
    
    # Base SVR is return / risk
    base_svr = avg_return / safe_drawdown
    
    # Adjust by consistency (higher consistency increases value)
    adjusted_svr = base_svr * (1.0 + signal_consistency)
    
    return float(adjusted_svr)

def _calculate_signal_conviction(
    signal_returns: np.ndarray,
    market_returns: np.ndarray = None
) -> float:
    """Calculate Signal Conviction.
    
    Measures the strength of signals based on their deviation from mean returns.
    Higher conviction signals tend to have more predictive power.
    
    Args:
        signal_returns (np.ndarray): Returns when signals are active
        market_returns (np.ndarray, optional): Overall market returns
        
    Returns:
        float: Signal Conviction score (0-1)
    """
    if len(signal_returns) == 0:
        return 0.0
        
    # If market returns not provided, use signal returns mean as baseline
    baseline = 0.0
    if market_returns is not None and len(market_returns) > 0:
        baseline = np.mean(market_returns)
    
    # Calculate mean signal return
    mean_signal_return = np.mean(signal_returns)
    
    # Calculate standard deviation of returns
    std_dev = np.std(signal_returns) if np.std(signal_returns) > 0 else 0.001
    
    # Calculate z-score (how many standard deviations from baseline)
    z_score = abs(mean_signal_return - baseline) / std_dev
    
    # Convert to 0-1 scale with diminishing returns for very high z-scores
    conviction = min(z_score / 3.0, 1.0)
    
    return float(conviction)

def _calculate_signal_timing_efficiency(
    signals: np.ndarray,
    returns: np.ndarray,
    lookback: int = 3,
    lookahead: int = 3
) -> float:
    """Calculate Signal Timing Efficiency.
    
    Measures how well-timed signals are relative to local price movements.
    Higher values indicate signals that capture more of the available price movement.
    
    Args:
        signals (np.ndarray): Array of strategy signals
        returns (np.ndarray): Array of strategy returns
        lookback (int): Number of periods to look back
        lookahead (int): Number of periods to look ahead
        
    Returns:
        float: Signal Timing Efficiency (0-1)
    """
    if len(signals) < (lookback + lookahead + 1) or np.sum(signals != 0) == 0:
        return 0.0
    
    total_captured = 0.0
    total_available = 0.0
    signal_count = 0
    
    for i in range(lookback, len(signals) - lookahead):
        if signals[i] != 0:  # If there's a signal
            signal_count += 1
            
            # Calculate returns around the signal
            pre_signal_returns = np.sum(returns[i-lookback:i])
            post_signal_returns = np.sum(returns[i:i+lookahead+1])
            
            # Calculate total available return in the window
            window_return = np.sum(returns[i-lookback:i+lookahead+1])
            
            # Skip if window return is zero
            if abs(window_return) < 0.0001:
                continue
                
            # For long signals, we want to enter after negative returns and exit after positive returns
            # For short signals, the opposite
            if signals[i] > 0:  # Long signal
                # Ideal timing would enter at the lowest point and capture all positive returns
                captured_return = post_signal_returns
                total_captured += captured_return
                total_available += max(0, window_return)
            else:  # Short signal
                # Ideal timing would enter at the highest point and capture all negative returns
                captured_return = -post_signal_returns
                total_captured += captured_return
                total_available += max(0, -window_return)
    
    # Calculate efficiency
    if total_available > 0 and signal_count > 0:
        return float(total_captured / total_available)
    else:
        return 0.0

def _calculate_signal_opportunity_cost(
    signal_returns: np.ndarray,
    risk_free_rate: float = 0.0
) -> float:
    """Calculate Signal Opportunity Cost.
    
    Measures the opportunity cost of taking signals vs. alternative investments.
    Positive values indicate signals outperform the risk-free rate.
    
    Args:
        signal_returns (np.ndarray): Returns when signals are active
        risk_free_rate (float): Daily risk-free rate
        
    Returns:
        float: Signal Opportunity Cost
    """
    if len(signal_returns) == 0:
        return 0.0
    
    # Calculate average signal return
    avg_signal_return = np.mean(signal_returns)
    
    # Calculate opportunity cost (signal return - risk free rate)
    opportunity_cost = avg_signal_return - risk_free_rate
    
    # Normalize to a 0-1 scale
    normalized_cost = 1.0 / (1.0 + np.exp(-10 * opportunity_cost))
    
    return float(normalized_cost)

def _calculate_signal_reliability_index(
    signal_returns: np.ndarray,
    window_size: int = 10
) -> float:
    """Calculate Signal Reliability Index.
    
    Measures the consistency of signal performance over time.
    Higher values indicate more reliable signals with consistent performance.
    
    Args:
        signal_returns (np.ndarray): Returns when signals are active
        window_size (int): Window size for rolling calculations
        
    Returns:
        float: Signal Reliability Index (0-1)
    """
    if len(signal_returns) < window_size:
        return 0.0
    
    # Calculate rolling win rates
    rolling_win_rates = []
    for i in range(len(signal_returns) - window_size + 1):
        window = signal_returns[i:i+window_size]
        win_rate = np.mean(window > 0)
        rolling_win_rates.append(win_rate)
    
    # Calculate standard deviation of rolling win rates
    # Lower standard deviation means more consistent performance
    std_dev = np.std(rolling_win_rates) if len(rolling_win_rates) > 0 else 1.0
    
    # Convert to reliability index (1 - normalized std_dev)
    # Higher reliability = lower standard deviation
    reliability = 1.0 - min(std_dev, 0.5) / 0.5
    
    return float(reliability)

def _calculate_quality_score(
    win_rate: float,
    profit_factor: float,
    sharpe_ratio: float,
    sortino_ratio: float,
    signal_efficiency: float,
    signal_consistency: float,
    signal_value_ratio: float = 0.0,
    signal_conviction: float = 0.0,
    signal_timing_efficiency: float = 0.0,
    signal_opportunity_cost: float = 0.0,
    signal_reliability: float = 0.0
) -> float:
    """Calculate an overall signal quality score.
    
    Args:
        win_rate (float): Win rate
        profit_factor (float): Profit factor
        sharpe_ratio (float): Sharpe ratio
        sortino_ratio (float): Sortino ratio
        signal_efficiency (float): Signal efficiency
        signal_consistency (float): Signal consistency
        signal_value_ratio (float): Signal Value Ratio
        signal_conviction (float): Signal Conviction
        signal_timing_efficiency (float): Signal Timing Efficiency
        signal_opportunity_cost (float): Signal Opportunity Cost
        signal_reliability (float): Signal Reliability Index
        
    Returns:
        float: Signal quality score
    """
    # Normalize profit factor (cap at 5.0)
    norm_profit_factor = min(profit_factor, 5.0) / 5.0
    
    # Normalize Sharpe (cap at 3.0)
    norm_sharpe = min(max(sharpe_ratio, 0), 3.0) / 3.0
    
    # Normalize Sortino (cap at 5.0)
    norm_sortino = min(max(sortino_ratio, 0), 5.0) / 5.0
    
    # Normalize Signal Value Ratio (cap at 2.0)
    norm_svr = min(max(signal_value_ratio, 0), 2.0) / 2.0
    
    # Weights for each component
    weights = {
        "win_rate": 0.15,
        "profit_factor": 0.15,
        "sharpe": 0.10,
        "sortino": 0.15,
        "efficiency": 0.05,
        "consistency": 0.05,
        "value_ratio": 0.10,
        "conviction": 0.05,
        "timing_efficiency": 0.10,
        "opportunity_cost": 0.05,
        "reliability": 0.05
    }
    
    # Calculate weighted score (0-10 scale)
    score = 10.0 * (
        weights["win_rate"] * win_rate +
        weights["profit_factor"] * norm_profit_factor +
        weights["sharpe"] * norm_sharpe +
        weights["sortino"] * norm_sortino +
        weights["efficiency"] * signal_efficiency +
        weights["consistency"] * signal_consistency +
        weights["value_ratio"] * norm_svr +
        weights["conviction"] * signal_conviction +
        weights["timing_efficiency"] * signal_timing_efficiency +
        weights["opportunity_cost"] * signal_opportunity_cost +
        weights["reliability"] * signal_reliability
    )
    
    return float(score)

def _calculate_aggregate_metrics(
    strategy_metrics: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate aggregate metrics across all strategies.
    
    Args:
        strategy_metrics (Dict[str, Dict[str, Any]]): Dictionary of strategy metrics
        
    Returns:
        Dict[str, Any]: Aggregate metrics
    """
    # Initialize aggregates
    total_signals = 0
    weighted_metrics = {
        "avg_return": 0.0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "risk_reward_ratio": 0.0,
        "sharpe_ratio": 0.0,
        "sortino_ratio": 0.0,
        "signal_efficiency": 0.0,
        "signal_consistency": 0.0,
        "signal_quality_score": 0.0,
        # New advanced metrics
        "signal_value_ratio": 0.0,
        "signal_conviction": 0.0,
        "signal_timing_efficiency": 0.0,
        "signal_opportunity_cost": 0.0,
        "signal_reliability": 0.0,
        "signal_risk_adjusted_return": 0.0
    }
    
    # Sum up total signals
    for strategy_id, metrics in strategy_metrics.items():
        total_signals += metrics.get("signal_count", 0)
    
    # If no signals, return empty metrics
    if total_signals == 0:
        return {
            "signal_count": 0,
            "signal_quality_score": 0.0
        }
    
    # Calculate weighted averages based on signal count
    for strategy_id, metrics in strategy_metrics.items():
        signal_count = metrics.get("signal_count", 0)
        if signal_count == 0:
            continue
            
        weight = signal_count / total_signals
        
        for metric_name in weighted_metrics.keys():
            if metric_name in metrics:
                weighted_metrics[metric_name] += weight * metrics[metric_name]
    
    # Add total signal count
    weighted_metrics["signal_count"] = total_signals
    
    return weighted_metrics

def calculate_aggregate_signal_quality(
    strategy_metrics: Dict[str, Dict[str, Any]],
    log: Callable[[str, str], None],
    stop_loss: Optional[float] = None,
    strategy_allocations: Optional[List[float]] = None,
    strategy_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Calculate aggregate signal quality metrics across all strategies.
    
    Args:
        strategy_metrics (Dict[str, Dict[str, Any]]): Dictionary of strategy metrics
        log (Callable[[str, str], None]): Logging function
        stop_loss (Optional[float]): Stop loss value
        strategy_allocations (Optional[List[float]]): List of strategy allocations
        strategy_ids (Optional[List[str]]): List of strategy IDs corresponding to allocations
        
    Returns:
        Dict[str, Any]: Aggregate metrics
    """
    try:
        log("Calculating aggregate signal quality metrics", "info")
        
        # Initialize aggregates
        total_signals = 0
        weighted_metrics = {
            "avg_return": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "risk_reward_ratio": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "signal_efficiency": 0.0,
            "signal_consistency": 0.0,
            "signal_quality_score": 0.0,
            "calmar_ratio": 0.0,
            "max_drawdown": 0.0,
            # New advanced metrics
            "signal_value_ratio": 0.0,
            "signal_conviction": 0.0,
            "signal_timing_efficiency": 0.0,
            "signal_opportunity_cost": 0.0,
            "signal_reliability": 0.0,
            "signal_risk_adjusted_return": 0.0
        }
        
        # Sum up total signals
        for strategy_id, metrics in strategy_metrics.items():
            total_signals += metrics.get("signal_count", 0)
        
        # If no signals, return empty metrics
        if total_signals == 0:
            log("No signals found across all strategies", "warning")
            return {
                "signal_count": 0,
                "signal_quality_score": 0.0
            }
        
        # Check if we have allocation information
        use_allocation_weights = False
        allocation_weights = {}
        
        if strategy_allocations and strategy_ids and len(strategy_allocations) == len(strategy_ids):
            use_allocation_weights = True
            total_allocation = sum(strategy_allocations)
            
            # Create a mapping of strategy_id to allocation weight
            for i, strategy_id in enumerate(strategy_ids):
                if total_allocation > 0:
                    allocation_weights[strategy_id] = strategy_allocations[i] / total_allocation
                else:
                    allocation_weights[strategy_id] = 1.0 / len(strategy_ids)
            
            log(f"Using allocation-weighted metrics with weights: {allocation_weights}", "info")
        
        # Calculate weighted averages based on signal count or allocations
        for strategy_id, metrics in strategy_metrics.items():
            signal_count = metrics.get("signal_count", 0)
            if signal_count == 0:
                continue
            
            # Determine weight based on allocation or signal count
            if use_allocation_weights and strategy_id in allocation_weights:
                weight = allocation_weights[strategy_id]
                log(f"Using allocation weight {weight:.4f} for strategy {strategy_id}", "info")
            else:
                weight = signal_count / total_signals
                log(f"Using signal count weight {weight:.4f} for strategy {strategy_id}", "info")
            
            for metric_name in weighted_metrics.keys():
                if metric_name in metrics:
                    weighted_metrics[metric_name] += weight * metrics[metric_name]
        
        # Add total signal count
        weighted_metrics["signal_count"] = total_signals
        
        log(f"Aggregate metrics calculated across {len(strategy_metrics)} strategies with {total_signals} total signals", "info")
        log(f"Aggregate quality score: {weighted_metrics['signal_quality_score']:.2f}", "info")
        
        return weighted_metrics
    except Exception as e:
        log(f"Error calculating aggregate signal quality metrics: {str(e)}", "error")
        return {
            "signal_count": 0,
            "signal_quality_score": 0.0,
            "error": str(e)
        }
