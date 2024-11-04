import numpy as np
import vectorbt as vbt

def calculate_expectancy(portfolio: vbt.Portfolio) -> float:
    """Calculate the expectancy of the trading strategy."""
    trades = portfolio.trades
    
    if len(trades.records_arr) == 0:
        return 0
    
    returns = trades.returns.values  # Get the numpy array of returns
    
    winning_trades = returns[returns > 0]
    losing_trades = returns[returns <= 0]
    
    win_rate = len(winning_trades) / len(returns)
    avg_win = np.mean(winning_trades) if len(winning_trades) > 0 else 0
    avg_loss = abs(np.mean(losing_trades)) if len(losing_trades) > 0 else 0
    
    if avg_loss == 0:
        return 0  # Avoid division by zero
    
    r_ratio = avg_win / avg_loss
    expectancy = (win_rate * r_ratio) - (1 - win_rate)
    return expectancy