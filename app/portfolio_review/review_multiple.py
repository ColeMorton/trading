from typing import List, Dict
import vectorbt as vbt
import polars as pl
import pandas as pd
import numpy as np
from config import config
from app.tools.get_data import get_data
from app.tools.setup_logging import setup_logging
from app.ema_cross.tools.generate_signals import generate_signals
from app.tools.file_utils import convert_stats

# Setup logging
log, log_close, _, _ = setup_logging(
    module_name='portfolio_review',
    log_file='review_multiple.log'
)

try:
    # Get unique symbols from strategies
    symbols: List[str] = list(set(strategy['symbol'] for strategy in config['strategies'].values()))
    log(f"Processing symbols: {symbols}")

    # Download historical data for all symbols using get_data utility
    data_dict: Dict[str, pl.DataFrame] = {}
    pandas_data_dict: Dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        log(f"Downloading data for {symbol}")
        # Get data and ensure consistent datetime precision
        df = get_data(symbol, {
            'start_date': config['start_date'],
            'end_date': config['end_date']
        }).with_columns(
            pl.col('Date').cast(pl.Datetime('ns')).alias('Date')
        )
        data_dict[symbol] = df
        # Create pandas version for generate_signals
        pandas_df = df.to_pandas()
        pandas_df.set_index('Date', inplace=True)
        pandas_data_dict[symbol] = pandas_df

    # Find common date range using polars operations
    common_dates = None
    for df in data_dict.values():
        dates = df.get_column('Date').to_list()
        if common_dates is None:
            common_dates = set(dates)
        else:
            common_dates = common_dates.intersection(set(dates))
    common_dates = sorted(list(common_dates))
    log(f"Date range: {common_dates[0]} to {common_dates[-1]}")

    # Create initial price DataFrame with consistent datetime precision
    price_df = pl.DataFrame({
        'Date': pl.Series(common_dates).cast(pl.Datetime('ns'))
    })

    # Join price data for each strategy
    for strategy_name, strategy in config['strategies'].items():
        close_prices = data_dict[strategy['symbol']].select(['Date', 'Close'])
        price_df = price_df.join(
            close_prices.rename({'Close': strategy_name}),
            on='Date',
            how='left'
        )

    # Convert to pandas for vectorbt with Date as index
    price_df_pd = price_df.to_pandas().set_index('Date')
    # Ensure numeric type for all price columns
    for col in price_df_pd.columns:
        price_df_pd[col] = pd.to_numeric(price_df_pd[col], errors='coerce')

    # Generate signals using the generate_signals utility
    log("Generating trading signals")
    entries_pd, exits_pd = generate_signals(pandas_data_dict, {
        'strategies': config['strategies'],
        'USE_SMA': config.get('USE_SMA', False),
        'USE_RSI': config.get('USE_RSI', False),
        'RSI_THRESHOLD': config.get('RSI_THRESHOLD', 70),
        'SHORT': config.get('SHORT', False),
        'init_cash': config.get('init_cash', 10000),
        'fees': config.get('fees', 0.001)
    })

    # Ensure boolean type for signal arrays
    entries_pd = entries_pd.astype(bool)
    exits_pd = exits_pd.astype(bool)

    # Create size DataFrame (position sizes for each strategy)
    sizes = pl.DataFrame({
        'Date': pl.Series(common_dates).cast(pl.Datetime('ns'))
    })
    for strategy_name in price_df_pd.columns:
        sizes = sizes.with_columns(pl.lit(1.0).alias(strategy_name))
    sizes_pd = sizes.to_pandas().set_index('Date')
    # Ensure numeric type for sizes
    sizes_pd = sizes_pd.astype(float)

    # Run the portfolio simulation
    log("Running portfolio simulation")
    portfolio = vbt.Portfolio.from_signals(
        close=price_df_pd,
        entries=entries_pd,
        exits=exits_pd,
        size=sizes_pd,
        init_cash=config['init_cash'],
        fees=config['fees'],
        freq='1D',
        group_by=True,
        cash_sharing=True
    )

    # Prepare benchmark data with consistent datetime precision
    log("Preparing benchmark data")
    benchmark_close = pl.DataFrame({
        'Date': pl.Series(common_dates).cast(pl.Datetime('ns'))
    })
    for symbol in symbols:
        close_prices = data_dict[symbol].select(['Date', 'Close'])
        benchmark_close = benchmark_close.join(
            close_prices.rename({'Close': symbol}),
            on='Date',
            how='left'
        )
    benchmark_close_pd = benchmark_close.to_pandas().set_index('Date')
    # Ensure numeric type for benchmark prices
    for col in benchmark_close_pd.columns:
        benchmark_close_pd[col] = pd.to_numeric(benchmark_close_pd[col], errors='coerce')

    # Create benchmark entries (always True after first row)
    benchmark_entries = pl.DataFrame({
        'Date': pl.Series(common_dates).cast(pl.Datetime('ns'))
    })
    for symbol in symbols:
        benchmark_entries = benchmark_entries.with_columns(
            pl.Series(name=symbol, values=[False] + [True] * (len(common_dates) - 1))
        )
    benchmark_entries_pd = benchmark_entries.to_pandas().set_index('Date')
    # Ensure boolean type for benchmark entries
    benchmark_entries_pd = benchmark_entries_pd.astype(bool)

    # Create benchmark position sizes (equal weight split)
    weight = 1.0 / len(symbols)  # Equal weight for each symbol
    benchmark_sizes = pl.DataFrame({
        'Date': pl.Series(common_dates).cast(pl.Datetime('ns'))
    })
    for symbol in symbols:
        benchmark_sizes = benchmark_sizes.with_columns(pl.lit(weight).alias(symbol))
    benchmark_sizes_pd = benchmark_sizes.to_pandas().set_index('Date')
    # Ensure numeric type for benchmark sizes
    benchmark_sizes_pd = benchmark_sizes_pd.astype(float)

    # Create benchmark portfolio
    log("Creating benchmark portfolio")
    benchmark_portfolio = vbt.Portfolio.from_signals(
        close=benchmark_close_pd,
        entries=benchmark_entries_pd,
        size=benchmark_sizes_pd,
        init_cash=config['init_cash'],
        fees=config['fees'],
        freq='1D',
        group_by=True,
        cash_sharing=True
    )

    # Convert and print portfolio statistics
    stats = portfolio.stats()
    converted_stats = convert_stats(stats)
    
    print("\nStrategy Portfolio Statistics:")
    print("===================")
    for key, value in converted_stats.items():
        print(f"{key}: {value}")
        log(f"{key}: {value}")

    # Calculate and print VaR and CVaR at 99%
    returns = portfolio.returns().values
    # Calculate VaR 99%
    var_99 = np.percentile(returns, 1)  # 1st percentile for 99% VaR
    # Calculate CVaR 99%
    cvar_99 = returns[returns <= var_99].mean()
    # Calculate VaR 99%
    var_95 = np.percentile(returns, 5)  # 5th percentile for 99% VaR
    # Calculate CVaR 99%
    cvar_95 = returns[returns <= var_95].mean()

    print("\nRisk Metrics:")
    print("===================")
    print(f"VaR 95%: {var_95:.2%}")
    print(f"CVaR 95%: {cvar_95:.2%}")
    print(f"VaR 99%: {var_99:.2%}")
    print(f"CVaR 99%: {cvar_99:.2%}")
    log(f"VaR 95%: {var_95:.2%}")
    log(f"CVaR 95%: {cvar_95:.2%}")
    log(f"VaR 99%: {var_99:.2%}")
    log(f"CVaR 99%: {cvar_99:.2%}")

    # Create comparison plots
    log("Creating portfolio plots")
    benchmark_portfolio.plot_value().show()  # Plot benchmark portfolio value

    # Plot additional metrics for strategy portfolio
    portfolio.plot([
        'value',
        'cum_returns',
        'drawdowns',
        'underwater',
        'net_exposure',
    ],
    show_titles=True).show()

    # Check which strategies have open positions at the end
    print("\nStrategies with Open Positions:")
    print("===================")
    positions = portfolio.positions.values[-1]  # Get positions at the last timestamp
    for strategy_name, position in zip(price_df_pd.columns, positions):
        if position != 0:
            message = f"{strategy_name}: {position:.2f} units"
            print(message)
            log(message)

except Exception as e:
    log(f"Error in portfolio review: {str(e)}", "error")
    raise
finally:
    log_close()
