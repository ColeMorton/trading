"""
Unified Metrics Calculation Module.

This module provides standardized functions for calculating metrics
across both signals and trades, eliminating duplicate calculation logic.
"""

from typing import Dict, Any, List, Optional, Callable, Tuple, Union
import numpy as np
import pandas as pd
import polars as pl
from pathlib import Path

from app.tools.setup_logging import setup_logging
from app.tools.expectancy import calculate_expectancy


class MetricsCalculator:
    """Class for calculating unified metrics for both signals and trades."""
    
    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        """Initialize the MetricsCalculator class.
        
        Args:
            log: Optional logging function. If not provided, a default logger will be created.
        """
        if log is None:
            # Create a default logger if none provided
            self.log, _, _, _ = setup_logging("metrics_calculator", Path("./logs"), "metrics_calculator.log")
        else:
            self.log = log
    
    def calculate_return_metrics(
        self,
        returns: np.ndarray,
        positions: Optional[np.ndarray] = None,
        annualization_factor: int = 252
    ) -> Dict[str, Any]:
        """Calculate return-based metrics.
        
        Args:
            returns: Array of returns
            positions: Optional array of positions (1 for long, -1 for short, 0 for no position)
            annualization_factor: Number of periods in a year (default: 252 for daily data)
            
        Returns:
            Dict[str, Any]: Dictionary of return metrics
        """
        try:
            self.log("Calculating return metrics", "info")
            
            # If positions are provided, filter returns to only include when positions are active
            if positions is not None:
                active_returns = returns[positions != 0]
            else:
                active_returns = returns
            
            if len(active_returns) == 0:
                self.log("No active returns to calculate metrics", "warning")
                return self._get_empty_return_metrics()
            
            # Basic return metrics
            avg_return = float(np.mean(active_returns))
            median_return = float(np.median(active_returns))
            std_return = float(np.std(active_returns))
            
            # Win rate using standardized calculation
            from app.concurrency.tools.win_rate_calculator import WinRateCalculator
            win_calc = WinRateCalculator()
            win_components = win_calc.calculate_trade_win_rate(active_returns, include_zeros=False)
            win_rate = win_components.win_rate
            
            # Traditional components for compatibility
            positive_returns = active_returns[active_returns > 0]
            negative_returns = active_returns[active_returns < 0]
            
            # Average win and loss
            avg_win = float(np.mean(positive_returns)) if len(positive_returns) > 0 else 0.0
            avg_loss = float(np.mean(negative_returns)) if len(negative_returns) > 0 else 0.0
            
            # Risk-reward ratio
            risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            # Profit factor
            profit_factor = 1.0
            if len(negative_returns) > 0 and np.sum(np.abs(negative_returns)) > 0:
                profit_factor = float(np.sum(positive_returns) / np.sum(np.abs(negative_returns)))
            
            # Expectancy per trade using standardized calculation
            expectancy_per_trade = calculate_expectancy(win_rate, avg_win, abs(avg_loss))
            
            # Annualized metrics
            annualized_return = float(avg_return * annualization_factor)
            annualized_volatility = float(std_return * np.sqrt(annualization_factor))
            
            # Sharpe ratio (assuming risk-free rate of 0)
            sharpe_ratio = float(annualized_return / annualized_volatility) if annualized_volatility > 0 else 0.0
            
            # Maximum drawdown
            cumulative_returns = np.cumsum(active_returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = running_max - cumulative_returns
            max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0
            
            # Sortino ratio (downside deviation)
            negative_returns_for_sortino = active_returns[active_returns < 0]
            downside_deviation = float(np.std(negative_returns_for_sortino)) if len(negative_returns_for_sortino) > 0 else 0.0
            sortino_ratio = float(annualized_return / (downside_deviation * np.sqrt(annualization_factor))) if downside_deviation > 0 else 0.0
            
            # Calmar ratio (return / max drawdown)
            calmar_ratio = float(annualized_return / max_drawdown) if max_drawdown > 0 else 0.0
            
            # Value at Risk (VaR)
            var_95 = float(np.percentile(active_returns, 5))
            
            # Return metrics dictionary
            return {
                "avg_return": avg_return,
                "median_return": median_return,
                "std_return": std_return,
                "win_rate": win_rate,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "risk_reward_ratio": risk_reward_ratio,
                "profit_factor": profit_factor,
                "expectancy_per_trade": expectancy_per_trade,
                "annualized_return": annualized_return,
                "annualized_volatility": annualized_volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "sortino_ratio": sortino_ratio,
                "calmar_ratio": calmar_ratio,
                "value_at_risk_95": var_95
            }
        except Exception as e:
            self.log(f"Error calculating return metrics: {str(e)}", "error")
            return self._get_empty_return_metrics()
    
    def calculate_frequency_metrics(
        self,
        data: Union[pl.DataFrame, pd.DataFrame],
        signal_column: str = "Signal",
        date_column: str = "Date"
    ) -> Dict[str, Any]:
        """Calculate signal frequency metrics.
        
        Args:
            data: DataFrame containing signal data
            signal_column: Name of the signal column
            date_column: Name of the date column
            
        Returns:
            Dict[str, Any]: Dictionary of frequency metrics
        """
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
            return self._get_empty_frequency_metrics()
            
        except Exception as e:
            self.log(f"Error calculating signal frequency metrics: {str(e)}", "error")
            return self._get_empty_frequency_metrics()
    
    def calculate_horizon_metrics(
        self,
        signals: np.ndarray,
        returns: np.ndarray,
        horizons: List[int] = None,
        min_sample_size: int = 20
    ) -> Dict[str, Dict[str, float]]:
        """Calculate performance metrics for different time horizons.
        
        Args:
            signals: Array of signals
            returns: Array of returns
            horizons: List of horizon periods to calculate (default: [1, 3, 5, 10])
            min_sample_size: Minimum sample size for valid horizon metrics
            
        Returns:
            Dict[str, Dict[str, float]]: Dictionary of horizon metrics
        """
        try:
            if horizons is None:
                horizons = [1, 3, 5, 10]
                
            self.log(f"Calculating horizon metrics for periods: {horizons}", "info")
            
            # Validate inputs
            if len(signals) != len(returns):
                self.log(f"Signal and return arrays must be the same length: {len(signals)} vs {len(returns)}", "error")
                return {}
                
            # Create a position array from signals
            positions = np.zeros_like(signals)
            for i in range(1, len(signals)):
                if signals[i-1] != 0:
                    positions[i] = signals[i-1]
            
            # Calculate base data once for all horizons
            results = {}
            
            for horizon in horizons:
                # Skip if we don't have enough data
                if len(returns) <= horizon:
                    self.log(f"Insufficient data for horizon {horizon}", "warning")
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
                    self.log(f"No active positions for horizon {horizon}", "warning")
                    continue
                
                # Convert to numpy array for calculations
                horizon_returns_np = np.array(horizon_returns)
                
                # Skip if insufficient sample size
                if len(horizon_returns_np) < min_sample_size:
                    self.log(f"Insufficient sample size for horizon {horizon}: {len(horizon_returns_np)} < {min_sample_size}", "warning")
                    continue
                
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
        except Exception as e:
            self.log(f"Error calculating horizon metrics: {str(e)}", "error")
            return {}
    
    def find_best_horizon(
        self,
        horizon_metrics: Dict[str, Dict[str, float]],
        min_sample_size: int = 20
    ) -> Optional[int]:
        """Find the best performing time horizon.
        
        Args:
            horizon_metrics: Dictionary of horizon metrics
            min_sample_size: Minimum sample size for valid horizon metrics
            
        Returns:
            Optional[int]: Best horizon period or None if no valid horizons
        """
        try:
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
        except Exception as e:
            self.log(f"Error finding best horizon: {str(e)}", "error")
            return None
    
    def calculate_quality_score(
        self,
        win_rate: float,
        profit_factor: float,
        avg_return: float,
        avg_loss: float
    ) -> float:
        """Calculate an overall signal quality score.
        
        Args:
            win_rate: Win rate as a decimal (0-1)
            profit_factor: Profit factor
            avg_return: Average return
            avg_loss: Average loss (as a negative value)
            
        Returns:
            float: Quality score (0-10 scale)
        """
        try:
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
        except Exception as e:
            self.log(f"Error calculating quality score: {str(e)}", "error")
            return 0.0
    
    def calculate_signal_quality_metrics(
        self,
        signals_df: Union[pl.DataFrame, pd.DataFrame],
        returns_df: Union[pl.DataFrame, pd.DataFrame],
        strategy_id: str,
        signal_column: str = "signal",
        return_column: str = "return",
        date_column: str = "Date"
    ) -> Dict[str, Any]:
        """Calculate signal quality metrics.
        
        Args:
            signals_df: DataFrame containing signal data
            returns_df: DataFrame containing return data
            strategy_id: Identifier for the strategy
            signal_column: Name of the signal column
            return_column: Name of the return column
            date_column: Name of the date column
            
        Returns:
            Dict[str, Any]: Dictionary of signal quality metrics
        """
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
            
            # Calculate return metrics
            return_metrics = self.calculate_return_metrics(returns_np, signals_np)
            
            # Calculate horizon metrics
            horizon_metrics = self.calculate_horizon_metrics(signals_np, returns_np)
            
            # Find best horizon
            best_horizon = self.find_best_horizon(horizon_metrics)
            
            # Calculate signal quality score
            signal_quality_score = self.calculate_quality_score(
                return_metrics["win_rate"],
                return_metrics["profit_factor"],
                return_metrics["avg_return"],
                return_metrics["avg_loss"]
            )
            
            # Combine metrics
            metrics = {
                "signal_count": signal_count,
                "signal_quality_score": signal_quality_score,
                "best_horizon": best_horizon,
                "horizon_metrics": horizon_metrics
            }
            
            # Add return metrics
            metrics.update(return_metrics)
            
            self.log(f"Calculated signal quality metrics for {strategy_id}: score={signal_quality_score:.2f}, win_rate={return_metrics['win_rate']:.2f}", "info")
            
            return metrics
        except Exception as e:
            self.log(f"Error calculating signal quality metrics for {strategy_id}: {str(e)}", "error")
            # Return a more complete default dictionary with all expected fields
            default_metrics = {
                "signal_count": 0,
                "signal_quality_score": 0.0,
                "best_horizon": None,
                "horizon_metrics": {}
            }
            # Add default return metrics
            default_metrics.update(self._get_empty_return_metrics())
            return default_metrics
    
    def calculate_portfolio_metrics(
        self,
        data_list: List[Union[pl.DataFrame, pd.DataFrame]],
        strategy_ids: List[str],
        signal_column: str = "Signal",
        date_column: str = "Date"
    ) -> Dict[str, Any]:
        """Calculate portfolio-level signal metrics.
        
        Args:
            data_list: List of DataFrames containing signal data
            strategy_ids: List of strategy identifiers
            signal_column: Name of the signal column
            date_column: Name of the date column
            
        Returns:
            Dict[str, Any]: Dictionary of portfolio-level metrics
        """
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
    
    def _get_empty_return_metrics(self) -> Dict[str, Any]:
        """Get empty return metrics dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary with default values for return metrics
        """
        return {
            "avg_return": 0.0,
            "median_return": 0.0,
            "std_return": 0.0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "risk_reward_ratio": 0.0,
            "profit_factor": 1.0,
            "expectancy_per_trade": 0.0,
            "annualized_return": 0.0,
            "annualized_volatility": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "sortino_ratio": 0.0,
            "calmar_ratio": 0.0,
            "value_at_risk_95": 0.0
        }
    
    def _get_empty_frequency_metrics(self) -> Dict[str, Any]:
        """Get empty frequency metrics dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary with default values for frequency metrics
        """
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


# Convenience functions for backward compatibility

def calculate_metrics_for_strategy(
    returns: np.ndarray,
    signals: np.ndarray,
    strategy_id: str,
    log: Optional[Callable] = None
) -> Dict[str, Any]:
    """Calculate metrics for a strategy (unified function).
    
    Args:
        returns: Array of returns
        signals: Array of signals
        strategy_id: Identifier for the strategy
        log: Optional logging function
        
    Returns:
        Dict[str, Any]: Dictionary of strategy metrics
    """
    calculator = MetricsCalculator(log)
    
    # Calculate return metrics
    return_metrics = calculator.calculate_return_metrics(returns, signals)
    
    # Calculate horizon metrics
    horizon_metrics = calculator.calculate_horizon_metrics(signals, returns)
    
    # Find best horizon
    best_horizon = calculator.find_best_horizon(horizon_metrics)
    
    # Calculate signal quality score
    signal_quality_score = calculator.calculate_quality_score(
        return_metrics["win_rate"],
        return_metrics["profit_factor"],
        return_metrics["avg_return"],
        return_metrics["avg_loss"]
    )
    
    # Combine metrics
    metrics = {
        "strategy_id": strategy_id,
        "signal_count": int(np.sum(signals != 0)),
        "signal_quality_score": signal_quality_score,
        "best_horizon": best_horizon,
        "horizon_metrics": horizon_metrics
    }
    
    # Add return metrics
    metrics.update(return_metrics)
    
    return metrics


def calculate_signal_metrics(
    aligned_data: List[pl.DataFrame],
    log: Optional[Callable] = None
) -> Dict[str, Any]:
    """Calculate signal metrics for all strategies (legacy function).
    
    Args:
        aligned_data: List of DataFrames containing signal data
        log: Optional logging function
        
    Returns:
        Dict[str, Any]: Dictionary of signal metrics
    """
    calculator = MetricsCalculator(log)
    
    # Extract strategy IDs
    strategy_ids = [f"strategy_{i+1}" for i in range(len(aligned_data))]
    
    # Calculate portfolio metrics
    return calculator.calculate_portfolio_metrics(aligned_data, strategy_ids, "Position", "Date")


def calculate_signal_quality_metrics(
    signals_df: pl.DataFrame,
    returns_df: pl.DataFrame,
    strategy_id: str,
    log: Callable[[str, str], None]
) -> Dict[str, Any]:
    """Calculate signal quality metrics for a strategy (legacy function).
    
    Args:
        signals_df: DataFrame containing signal data
        returns_df: DataFrame containing return data
        strategy_id: Identifier for the strategy
        log: Logging function
        
    Returns:
        Dict[str, Any]: Dictionary of signal quality metrics
    """
    calculator = MetricsCalculator(log)
    return calculator.calculate_signal_quality_metrics(signals_df, returns_df, strategy_id)