import os
import sys
from pathlib import Path

import numpy as np
import vectorbt as vbt

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Import the standardized expectancy calculation
from app.tools.expectancy import calculate_expectancy_from_returns


def calculate_expectancy(portfolio: vbt.Portfolio) -> float:
    """Calculate the expectancy of the trading strategy.

    This function now uses the standardized expectancy calculation
    to fix the 596,446% variance issue caused by the R-ratio formula.
    """
    trades = portfolio.trades

    if len(trades.records_arr) == 0:
        return 0

    returns = trades.returns.values  # Get the numpy array of returns

    # Check if we should use legacy calculation (for backward compatibility)
    use_legacy = os.getenv("USE_FIXED_EXPECTANCY_CALC", "true").lower() != "true"

    if use_legacy:
        # Legacy R-ratio calculation (kept for comparison/rollback)
        winning_trades = returns[returns > 0]
        losing_trades = returns[returns <= 0]

        # Use standardized win rate calculation for consistency
        from app.concurrency.tools.win_rate_calculator import WinRateCalculator

        win_calc = WinRateCalculator()
        win_components = win_calc.calculate_trade_win_rate(returns, include_zeros=False)
        win_rate = win_components.win_rate
        avg_win = np.mean(winning_trades) if len(winning_trades) > 0 else 0
        avg_loss = abs(np.mean(losing_trades)) if len(losing_trades) > 0 else 0

        if avg_loss == 0:
            return 0  # Avoid division by zero

        r_ratio = avg_win / avg_loss
        expectancy = (win_rate * r_ratio) - (1 - win_rate)
        return expectancy

    # Use standardized expectancy calculation
    expectancy, _ = calculate_expectancy_from_returns(returns)
    return expectancy
