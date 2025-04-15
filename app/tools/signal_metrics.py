"""
Standardized Signal Metrics Module.

This module provides a unified framework for calculating signal metrics,
combining frequency, distribution, and quality metrics in a consistent manner.
"""

from typing import Dict, Any, List, Optional, Callable, Tuple, Union
import polars as pl
import pandas as pd
import numpy as np
from pathlib import Path

from app.tools.setup_logging import setup_logging
from app.tools.expectancy import calculate_expectancy


class SignalMetrics:
    """Class for calculating comprehensive signal metrics."""
    
    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        """Initialize the SignalMetrics class."""
        if log is None:
            # Create a default logger if none provided
            self.log, _, _, _ = setup_logging("signal_metrics", Path("./logs"), "signal_metrics.log")
        else:
            self.log = log
    
    def calculate_frequency_metrics(
        self,
        data: Union[pl.DataFrame, pd.DataFrame],
        signal_column: str = "Signal",
        date_column: str = "Date"
    ) -> Dict[str, Any]:
        """Calculate signal frequency metrics."""
        try:
            self.log("Calculating signal frequency metrics", "info")
            
            # Convert to pandas if polars
            if isinstance(data, pl.DataFrame):
                df = data.to_pandas()
            else:
                df = data
                
            # Set date as index
            if date_column in df.columns:
                df = df.set_index(date_column)
                
            # Extract signals (non-zero values indicate signals)
            signals = df[df[signal_column] != 0].copy()
            
            # Calculate monthly signal counts
            if len(signals) > 0:
                signals.loc[:, 'month'] = signals.index.to_period('M')
                monthly_counts = signals.groupby('month').size()
                
                # Calculate metrics
                if len(monthly_counts) > 0:
                    mean_signals = float(monthly_counts.mean())
                    median_signals = float(monthly_counts.median())
                    signal_volatility = float(monthly_counts.std()) if len(monthly_counts) > 1 else 0.0
                    max_monthly = int(monthly_counts.max())
                    min_monthly = int(monthly_counts.min())
                    total_signals = int(len(signals))
                    
                    # Calculate standard deviation bounds
                    std_below_mean = float(max(0, mean_signals - signal_volatility))
                    std_above_mean = float(mean_signals + signal_volatility)
                    
                    # Calculate signal consistency
                    if mean_signals > 0:
                        signal_consistency = float(1.0 - min(1.0, signal_volatility / mean_signals))
                    else:
                        signal_consistency = 0.0
                    
                    # Calculate signal density
                    trading_days = len(df)
                    signal_density = float(total_signals / trading_days) if trading_days > 0 else 0.0
                    
                    return {
                        "mean_signals_per_month": mean_signals,
                        "median_signals_per_month": median_signals,
                        "signal_volatility": signal_volatility,
                        "max_monthly_signals": max_monthly,
                        "min_monthly_signals": min_monthly,
                        "total_signals": total_signals,
                        "std_below_mean": std_below_mean,
                        "std_above_mean": std_above_mean,
                        "signal_consistency": signal_consistency,
                        "signal_density": signal_density
                    }
            
            # Default values if no signals or monthly counts
            return {
                "mean_signals_per_month": 0.0,
                "median_signals_per_month": 0.0,
                "signal_volatility": 0.0,
                "max_monthly_signals": 0,
                "min_monthly_signals": 0,
                "total_signals": 0,
                "std_below_mean": 0.0,
                "std_above_mean": 0.0,
                "signal_consistency": 0.0,
                "signal_density": 0.0
            }
            
        except Exception as e:
            self.log(f"Error calculating signal frequency metrics: {str(e)}", "error")
            return {
                "mean_signals_per_month": 0.0,
                "median_signals_per_month": 0.0,
                "signal_volatility": 0.0,
                "max_monthly_signals": 0,
                "min_monthly_signals": 0,
                "total_signals": 0,
                "std_below_mean": 0.0,
                "std_above_mean": 0.0,
                "signal_consistency": 0.0,
                "signal_density": 0.0
            }
    
    def calculate_quality_metrics(
        self,
        signals_df: Union[pl.DataFrame, pd.DataFrame],
        returns_df: Union[pl.DataFrame, pd.DataFrame],
        strategy_id: str,
        signal_column: str = "signal",
        return_column: str = "return",
        date_column: str = "Date"
    ) -> Dict[str, Any]:
        """Calculate signal quality metrics."""
        try:
            self.log(f"Calculating signal quality metrics for {strategy_id}", "info")
            
            # Convert to polars if pandas
            if isinstance(signals_df, pd.DataFrame):
                signals_pl = pl.from_pandas(signals_df)
            else:
                signals_pl = signals_df
                
            if isinstance(returns_df, pd.DataFrame):
                returns_pl = pl.from_pandas(returns_df)
            else:
                returns_pl = returns_df
            
            # Ensure dataframes have required columns
            if date_column not in signals_pl.columns or signal_column not in signals_pl.columns:
                self.log(f"Missing required columns in signals_df for {strategy_id}", "error")
                return {"signal_count": 0, "signal_quality_score": 0.0}
                
            if date_column not in returns_pl.columns or return_column not in returns_pl.columns:
                self.log(f"Missing required columns in returns_df for {strategy_id}", "error")
                return {"signal_count": 0, "signal_quality_score": 0.0}
                
            # Join signals and returns on Date
            joined_df = signals_pl.join(returns_pl, on=date_column, how="inner")
            
            # Extract signals and returns as numpy arrays
            signals_np = joined_df[signal_column].fill_null(0).to_numpy()
            returns_np = joined_df[return_column].fill_null(0).to_numpy()
            
            # Count signals
            signal_count = int(np.sum(signals_np != 0))
            
            if signal_count == 0:
                self.log(f"No signals found for {strategy_id}", "warning")
                return {
                    "signal_count": 0,
                    "signal_quality_score": 0.0
                }
            
            # Calculate signal returns (only when signal is active)
            signal_returns = returns_np[signals_np != 0]
            
            # Basic return metrics
            avg_return = float(np.mean(signal_returns))
            win_rate = float(np.mean(signal_returns > 0))
            
            # Profit factor
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
            expectancy_per_signal = calculate_expectancy(win_rate, avg_win, abs(avg_loss))
            
            # Calculate time horizons performance
            horizon_metrics = self._calculate_horizon_metrics(signals_np, returns_np)
            
            # Find best horizon
            best_horizon = self._find_best_horizon(horizon_metrics)
            
            # Calculate signal quality score
            signal_quality_score = self._calculate_quality_score(
                win_rate, profit_factor, avg_return, avg_loss
            )
            
            self.log(f"Calculated signal quality metrics for {strategy_id}: score={signal_quality_score:.2f}, win_rate={win_rate:.2f}", "info")
            
            return {
                "signal_count": signal_count,
                "avg_return": avg_return,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "risk_reward_ratio": risk_reward_ratio,
                "expectancy_per_signal": expectancy_per_signal,
                "expectancy_components": {
                    "win_rate": win_rate,
                    "avg_win": avg_win,
                    "avg_loss": avg_loss
                },
                "signal_quality_score": signal_quality_score,
                "best_horizon": best_horizon,
                "horizon_metrics": horizon_metrics
            }
        except Exception as e:
            self.log(f"Error calculating signal quality metrics for {strategy_id}: {str(e)}", "error")
            return {"signal_count": 0, "signal_quality_score": 0.0}
    
    def calculate_portfolio_metrics(
        self,
        data_list: List[Union[pl.DataFrame, pd.DataFrame]],
        strategy_ids: List[str],
        signal_column: str = "Signal",
        date_column: str = "Date"
    ) -> Dict[str, Any]:
        """Calculate portfolio-level signal metrics."""
        try:
            self.log("Calculating portfolio-level signal metrics", "info")
            
            # Initialize metrics dictionary
            metrics = {}
            
            # Calculate strategy-specific metrics
            for i, (df, strategy_id) in enumerate(zip(data_list, strategy_ids), 1):
                strategy_metrics = self.calculate_frequency_metrics(df, signal_column, date_column)
                
                # Store strategy-specific metrics with strategy ID prefix
                for key, value in strategy_metrics.items():
                    metrics[f"{strategy_id}_{key}"] = value
            
            # Calculate portfolio-level metrics
            if data_list:
                # Convert all dataframes to pandas
                pandas_dfs = []
                for df in data_list:
                    if isinstance(df, pl.DataFrame):
                        pandas_dfs.append(df.to_pandas())
                    else:
                        pandas_dfs.append(df)
                
                # Combine all signals
                all_signals = []
                for df in pandas_dfs:
                    if date_column in df.columns:
                        df_copy = df.copy()
                        df_copy = df_copy.set_index(date_column)
                        signals = df_copy[df_copy[signal_column] != 0].copy()
                        all_signals.append(signals)
                
                if all_signals:
                    # Combine all signals
                    combined_signals = pd.concat(all_signals).copy()
                    
                    # Ensure index is properly set
                    if not isinstance(combined_signals.index, pd.DatetimeIndex):
                        self.log("Warning: Combined signals index is not a DatetimeIndex", "warning")
                        for col in combined_signals.columns:
                            if col.lower() == 'date':
                                combined_signals = combined_signals.set_index(col)
                                break
                    
                    combined_signals.loc[:, 'month'] = combined_signals.index.to_period('M')
                    
                    # Calculate monthly counts
                    portfolio_monthly_counts = combined_signals.groupby('month').size()
                    
                    if len(portfolio_monthly_counts) > 0:
                        mean_signals = float(portfolio_monthly_counts.mean())
                        median_signals = float(portfolio_monthly_counts.median())
                        signal_volatility = float(portfolio_monthly_counts.std()) if len(portfolio_monthly_counts) > 1 else 0.0
                        max_monthly = int(portfolio_monthly_counts.max())
                        min_monthly = int(portfolio_monthly_counts.min())
                        total_signals = int(len(combined_signals))
                        
                        # Store portfolio metrics
                        metrics["portfolio_mean_signals_per_month"] = mean_signals
                        metrics["portfolio_median_signals_per_month"] = median_signals
                        metrics["portfolio_signal_volatility"] = signal_volatility
                        metrics["portfolio_max_monthly_signals"] = max_monthly
                        metrics["portfolio_min_monthly_signals"] = min_monthly
                        metrics["portfolio_total_signals"] = total_signals
            
            self.log("Portfolio-level signal metrics calculation completed", "info")
            return metrics
            
        except Exception as e:
            self.log(f"Error calculating portfolio-level signal metrics: {str(e)}", "error")
            return {
                "portfolio_mean_signals_per_month": 0.0,
                "portfolio_median_signals_per_month": 0.0,
                "portfolio_signal_volatility": 0.0,
                "portfolio_max_monthly_signals": 0,
                "portfolio_min_monthly_signals": 0,
                "portfolio_total_signals": 0
            }
    
    def _calculate_horizon_metrics(
        self,
        signals: np.ndarray,
        returns: np.ndarray
    ) -> Dict[str, Dict[str, float]]:
        """Calculate performance metrics for different time horizons."""
        horizons = [1, 3, 5, 10]
        results = {}
        
        # Create a position array from signals
        positions = np.zeros_like(signals)
        for i in range(1, len(signals)):
            if signals[i-1] != 0:
                positions[i] = signals[i-1]
        
        for horizon in horizons:
            # Skip if we don't have enough data
            if len(returns) <= horizon:
                continue
            
            # Initialize arrays to store horizon returns
            horizon_returns = []
            
            # For each position, calculate the return over the horizon
            for i in range(len(positions) - horizon):
                if positions[i] != 0:  # If there's an active position
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
            sharpe = float(avg_return / np.std(horizon_returns_np)) if np.std(horizon_returns_np) > 0 else 0.0
            
            results[str(horizon)] = {
                "avg_return": avg_return,
                "win_rate": win_rate,
                "sharpe": sharpe,
                "sample_size": len(horizon_returns_np)
            }
        
        return results
    
    def _find_best_horizon(
        self,
        horizon_metrics: Dict[str, Dict[str, float]],
        min_sample_size: int = 20
    ) -> Optional[int]:
        """Find the best performing time horizon."""
        if not horizon_metrics:
            return None
            
        best_horizon = None
        best_score = -float('inf')
        
        for horizon_str, metrics in horizon_metrics.items():
            # Get metrics with defaults
            sharpe = metrics.get("sharpe", 0)
            win_rate = metrics.get("win_rate", 0)
            sample_size = metrics.get("sample_size", 0)
            
            # Skip horizons with insufficient data
            if sample_size < min_sample_size:
                continue
            
            # Calculate a combined score
            sample_size_factor = min(1.0, sample_size / 100)
            combined_score = (0.6 * sharpe) + (0.3 * win_rate) + (0.1 * sample_size_factor)
            
            if combined_score > best_score:
                best_score = combined_score
                best_horizon = int(horizon_str)
        
        return best_horizon
    
    def _calculate_quality_score(
        self,
        win_rate: float,
        profit_factor: float,
        avg_return: float,
        avg_loss: float
    ) -> float:
        """Calculate an overall signal quality score."""
        # Normalize profit factor (cap at 5.0)
        norm_profit_factor = min(profit_factor, 5.0) / 5.0
        
        # Calculate weighted score (0-10 scale)
        score = 10.0 * (
            0.4 * win_rate +
            0.3 * norm_profit_factor +
            0.2 * (avg_return / max(abs(avg_loss), 0.001)) +
            0.1 * (1.0 if avg_return > 0 else 0.0)
        )
        
        return float(score)


# Convenience functions for backward compatibility

def calculate_signal_metrics(
    aligned_data: List[pl.DataFrame],
    log: Optional[Callable] = None
) -> Dict[str, Any]:
    """Calculate signal metrics for all strategies (legacy function)."""
    metrics = SignalMetrics(log)
    
    # Extract strategy IDs
    strategy_ids = [f"strategy_{i+1}" for i in range(len(aligned_data))]
    
    # Calculate portfolio metrics
    return metrics.calculate_portfolio_metrics(aligned_data, strategy_ids, "Position", "Date")


def calculate_signal_quality_metrics(
    signals_df: pl.DataFrame,
    returns_df: pl.DataFrame,
    strategy_id: str,
    log: Callable[[str, str], None]
) -> Dict[str, Any]:
    """Calculate signal quality metrics for a strategy (legacy function)."""
    metrics = SignalMetrics(log)
    return metrics.calculate_quality_metrics(signals_df, returns_df, strategy_id)
