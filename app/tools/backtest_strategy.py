import polars as pl
import vectorbt as vbt
from typing import Callable, Dict, Any

def backtest_strategy(data: pl.DataFrame, config: dict, log: Callable) -> vbt.Portfolio:
    """
    Backtest the MA cross strategy.
    
    Args:
        data: Price data with signals
        config: Configuration dictionary containing:
            - USE_HOURLY (bool): Whether to use hourly data
            - DIRECTION (str): 'Long' or 'Short' for position direction
            - STOP_LOSS (float, optional): Stop loss as decimal (0-1). If not provided, no stop loss is used.
            - RSI_WINDOW (int, optional): Period for RSI calculation
            - RSI_THRESHOLD (int, optional): RSI threshold for signal filtering
            - short_window (int, optional): Short-term window size
            - long_window (int, optional): Long-term window size
            - signal_window (int, optional): Signal line window size
        log: Logging function for recording events and errors
        
    Returns:
        Portfolio object with backtest results
    """
    try:
        freq = 'h' if config.get('USE_HOURLY', False) else 'D'
        
        # Convert polars DataFrame to pandas DataFrame for vectorbt
        data_pd = data.to_pandas()
        
        # Portfolio parameters
        params = {
            'close': data_pd['Close'],
            'init_cash': 1000,
            'fees': 0.001,
            'freq': freq
        }
        
        # Handle stop loss configuration
        if "STOP_LOSS" in config and config["STOP_LOSS"] is not None:
            stop_loss = config["STOP_LOSS"]  # Already in decimal form (0-1) from app.tools.portfolio.loader
            if 0 < stop_loss <= 1:  # Validate range
                if config.get('SL_CANDLE_CLOSE', True):
                    # When using candle close, we calculate the stop price based on entry
                    # but execute at the candle's close price
                    params['sl_stop'] = stop_loss
                    log(f"Applied stop loss of {stop_loss*100:.2f}% with exit at candle close", "info")
                else:
                    # For immediate exit, use the actual stop loss price
                    params['sl_stop'] = stop_loss
                    # Use the actual stop loss price for exit
                    params['sl_price'] = data_pd['Close'] * (1 - stop_loss if config.get('DIRECTION', 'Long') == 'Long' else 1 + stop_loss)
                    log(f"Applied stop loss of {stop_loss*100:.2f}% with immediate exit", "info")
            else:
                log(f"Warning: Invalid stop loss value {stop_loss*100:.2f}% - must be between 0% and 100%", "warning")
        else:
            log("No stop loss configured for strategy - running without stop loss protection", "warning")
        
        if config.get('DIRECTION', 'Long').lower() == 'short':
            # For short positions, enter when Signal is -1 (fast MA crosses below slow MA)
            params['short_entries'] = data_pd['Signal'] == -1
            params['short_exits'] = data_pd['Signal'] == 0
        else:
            # For long positions, enter when Signal is 1 (fast MA crosses above slow MA)
            params['entries'] = data_pd['Signal'] == 1
            params['exits'] = data_pd['Signal'] == 0
        
        portfolio = vbt.Portfolio.from_signals(**params)
        
        # Create a custom stats method that includes window parameters
        def stats(self) -> Dict[str, Any]:
            original_stats = super(type(portfolio), self).stats()
            stats_dict = {k: v for k, v in original_stats.items()}
            
            # Add window parameters
            stats_dict['Short Window'] = config.get('short_window', 0)
            stats_dict['Long Window'] = config.get('long_window', 0)
            stats_dict['Signal Window'] = config.get('signal_window', 0)
            
            # Add optional parameters
            if "STOP_LOSS" in config and config["STOP_LOSS"] is not None:
                stats_dict['Stop Loss'] = config["STOP_LOSS"]
            
            if "RSI_WINDOW" in config and config["RSI_WINDOW"] is not None:
                stats_dict['RSI Window'] = config["RSI_WINDOW"]
                
            if "RSI_THRESHOLD" in config and config["RSI_THRESHOLD"] is not None:
                stats_dict['RSI Threshold'] = config["RSI_THRESHOLD"]
            
            # Add additional risk metrics from VectorBT
            try:
                # Get returns accessor
                returns_acc = self.returns_acc
                
                # Get the returns series
                returns_series = self.returns()
                
                # Calculate metrics using pandas methods on the returns series
                try:
                    stats_dict['Skew'] = returns_series.skew()
                    log(f"Calculated Skew: {stats_dict['Skew']}", "debug")
                except Exception as e:
                    log(f"Could not calculate Skew: {e}", "warning")
                
                try:
                    stats_dict['Kurtosis'] = returns_series.kurtosis()
                    log(f"Calculated Kurtosis: {stats_dict['Kurtosis']}", "debug")
                except Exception as e:
                    log(f"Could not calculate Kurtosis: {e}", "warning")
                
                # Calculate Tail Ratio manually
                try:
                    positive_returns = returns_series[returns_series > 0]
                    negative_returns = returns_series[returns_series < 0]
                    if len(negative_returns) > 0 and len(positive_returns) > 0:
                        stats_dict['Tail Ratio'] = positive_returns.mean() / abs(negative_returns.mean())
                    else:
                        stats_dict['Tail Ratio'] = None
                    log(f"Calculated Tail Ratio: {stats_dict['Tail Ratio']}", "debug")
                except Exception as e:
                    log(f"Could not calculate Tail Ratio: {e}", "warning")
                
                # Calculate Common Sense Ratio manually
                try:
                    if len(returns_series) > 0:
                        win_rate = len(returns_series[returns_series > 0]) / len(returns_series)
                        stats_dict['Common Sense Ratio'] = win_rate / (1 - win_rate) if win_rate < 1 else float('inf')
                    else:
                        stats_dict['Common Sense Ratio'] = None
                    log(f"Calculated Common Sense Ratio: {stats_dict['Common Sense Ratio']}", "debug")
                except Exception as e:
                    log(f"Could not calculate Common Sense Ratio: {e}", "warning")
                
                # Calculate Value at Risk (VaR)
                try:
                    stats_dict['Value at Risk'] = returns_series.quantile(0.05)
                    log(f"Calculated Value at Risk: {stats_dict['Value at Risk']}", "debug")
                except Exception as e:
                    log(f"Could not calculate Value at Risk: {e}", "warning")
                
                # Alpha and Beta calculation
                try:
                    # For now, set Alpha and Beta to fixed values since we don't have benchmark data
                    # In a real implementation, you would need to provide benchmark data
                    log("Setting Alpha and Beta to fixed values as benchmark data is not available", "debug")
                    stats_dict['Alpha'] = 0.0
                    stats_dict['Beta'] = 1.0
                    log(f"Set Alpha: {stats_dict['Alpha']}, Beta: {stats_dict['Beta']}", "debug")
                except Exception as e:
                    log(f"Could not calculate Alpha/Beta: {e}", "warning")
                    stats_dict['Alpha'] = None
                    stats_dict['Beta'] = None
                
                # Log the calculated risk metrics
                log(f"Calculated risk metrics: Skew={stats_dict.get('Skew')}, Kurtosis={stats_dict.get('Kurtosis')}, " +
                    f"Tail Ratio={stats_dict.get('Tail Ratio')}, Common Sense Ratio={stats_dict.get('Common Sense Ratio')}, " +
                    f"Value at Risk={stats_dict.get('Value at Risk')}, Alpha={stats_dict.get('Alpha')}, Beta={stats_dict.get('Beta')}", "debug")
                
                # Add additional return metrics
                # Convert Series/DataFrames to scalar values for CSV export
                try:
                    # Daily returns (mean of returns)
                    stats_dict['Daily Returns'] = returns_series.mean()
                    
                    # Calculate annual returns using the freq from the config
                    # Use the same freq that was used to create the portfolio
                    freq_value = 'h' if config.get('USE_HOURLY', False) else 'D'
                    periods_per_year = {'D': 252, 'h': 252*24, 'min': 252*24*60}.get(freq_value, 252)
                    log(f"Using frequency: {freq_value} with {periods_per_year} periods per year", "debug")
                    
                    stats_dict['Annual Returns'] = returns_series.mean() * periods_per_year
                    
                    # Cumulative returns
                    stats_dict['Cumulative Returns'] = (1 + returns_series).prod() - 1
                    
                    # Annualized return
                    stats_dict['Annualized Return'] = (1 + stats_dict['Cumulative Returns']) ** (periods_per_year / len(returns_series)) - 1
                    
                    # Annualized volatility
                    stats_dict['Annualized Volatility'] = returns_series.std() * (periods_per_year ** 0.5)
                    
                    log(f"Calculated return metrics: Daily Returns={stats_dict['Daily Returns']}, " +
                        f"Annual Returns={stats_dict['Annual Returns']}, Cumulative Returns={stats_dict['Cumulative Returns']}, " +
                        f"Annualized Return={stats_dict['Annualized Return']}, Annualized Volatility={stats_dict['Annualized Volatility']}", "debug")
                except Exception as e:
                    log(f"Could not calculate some return metrics: {e}", "warning")
                    # Set failed metrics to None to ensure they're included in the CSV
                    stats_dict['Daily Returns'] = None
                    stats_dict['Annual Returns'] = None
                    stats_dict['Cumulative Returns'] = None
                    stats_dict['Annualized Return'] = None
                    stats_dict['Annualized Volatility'] = None
            except Exception as e:
                log(f"Could not calculate additional risk metrics: {e}", "warning")
            
            return stats_dict
        
        # Attach the custom stats method to the portfolio instance
        portfolio.stats = stats.__get__(portfolio)
        
        return portfolio
        
    except Exception as e:
        log(f"Backtest failed: {e}", "error")
        raise
