from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.utils import backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.setup_logging import setup_logging
import polars as pl

CONFIG_BTC = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "TICKER": 'BTC-USD',
    "USE_SYNTHETIC": False,
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'SPY',
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17,
    "STOP_LOSS": 3.62,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": False,
    "BASE_DIR": 'C:/Projects/trading',
    "WINDOWS": 89
}

CONFIG_SOL = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "TICKER": 'SOL-USD',
    "USE_SYNTHETIC": False,
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'SPY',
    "SHORT_WINDOW": 14,
    "LONG_WINDOW": 32,
    "STOP_LOSS": None,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": True,
    "BASE_DIR": 'C:/Projects/trading',
    "WINDOWS": 89
}

CONFIG_SUI = {
    "YEARS": 1.5369,
    "USE_YEARS": True,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "TICKER": 'SUI20947-USD',
    "USE_SYNTHETIC": False,
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'SPY',
    "SHORT_WINDOW": 38,
    "LONG_WINDOW": 59,
    "STOP_LOSS": None,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": True,
    "BASE_DIR": 'C:/Projects/trading',
    "WINDOWS": 89
}

CONFIG_SPY = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "TICKER": 'SPY',
    "USE_SYNTHETIC": False,
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'SPY',
    "SHORT_WINDOW": 10,
    "LONG_WINDOW": 30,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": False,
    "BASE_DIR": 'C:/Projects/trading',
    "WINDOWS": 89
}

CONFIG_OP = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "TICKER": 'OP-USD',
    "USE_SYNTHETIC": False,
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'SPY',
    "SHORT_WINDOW": 81,
    "LONG_WINDOW": 83,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": True,
    "BASE_DIR": 'C:/Projects/trading',
    "WINDOWS": 89
}

def run(config_dict):
    """
    Run portfolio review analysis.

    Args:
        config_dict (dict): Configuration dictionary

    Returns:
        bool: True if analysis successful
    """
    log, log_close, _, _ = setup_logging(
        module_name='portfolio_review',
        log_file='review.log'
    )

    try:
        config = get_config(config_dict)
        log(f"Starting portfolio review for {config['TICKER']}")

        data = get_data(config["TICKER"], config, log)
        
        data = calculate_ma_and_signals(
            data, 
            config["SHORT_WINDOW"], 
            config["LONG_WINDOW"], 
            config,
            log
        )

        portfolio = backtest_strategy(data, config, log)
        
        stats = portfolio.stats()
        log(f"Portfolio stats: {stats}")

        # Extract value series and convert to DataFrame
        value_series = portfolio.value()
        initial_value = value_series[0]
        equity_curve = pl.DataFrame({
            'Date': value_series.index,
            'Close': value_series.values / initial_value
        })

        # Export to CSV
        csv_path = f'csv/ma_cross/equity_curve/{config["TICKER"]}.csv'
        equity_curve.write_csv(csv_path)
        log(f"Exported equity curve to {csv_path}")

        fig = portfolio.plot(subplots=[
            'value',
            'drawdowns',
            'cum_returns',
            'assets',
            'orders',
            'trades',
            'trade_pnl',
            'asset_flow',
            'cash_flow',
            'asset_value',
            'cash',
            'underwater',
            'gross_exposure',
            'net_exposure',
        ],
        show_titles=True)

        fig.update_layout(
            width=1200,
            height=10000,
            autosize=True
        )

        fig.show()
        log("Generated and displayed portfolio plots")
        
        log_close()
        return True

    except Exception as e:
        log(f"Error during portfolio review: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run(CONFIG_OP)
        if result:
            print("Portfolio review completed successfully!")
    except Exception as e:
        print(f"Portfolio review failed: {str(e)}")
        raise
