import vectorbt as vbt
import polars as pl

def backtest_strategy(data: pl.DataFrame, short: bool) -> vbt.Portfolio:
    """Backtest the MACD cross strategy."""
    if short:
        # For short-only strategy, we need to inverse the signals
        portfolio = vbt.Portfolio.from_signals(
            close=data['Close'],
            short_entries=data['Signal'] == -1,
            short_exits=data['Signal'] == 0,
            init_cash=1000,
            fees=0.001
        )
    else:
        portfolio = vbt.Portfolio.from_signals(
            close=data['Close'],
            entries=data['Signal'] == 1,
            exits=data['Signal'] == 0,
            init_cash=1000,
            fees=0.001
        )
    return portfolio