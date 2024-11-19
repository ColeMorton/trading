import os
import polars as pl
from app.tools.get_config import get_config
from app.ema_cross.tools.process_ma_portfolios import process_ma_portfolios
from app.ema_cross.tools.convert_stats import convert_stats
from app.ema_cross.tools.export_portfolios import export_portfolios
from app.tools.setup_logging import setup_logging

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Setup logging
log_dir = os.path.join(project_root, 'logs', 'ma_cross')
log, log_close, _, _ = setup_logging('ma_cross', log_dir, '3_scanned_summary.log')

scanner_list = 'DAILY.csv'

def run() -> bool:
    try:
        # Read DAILY.csv
        daily_df = pl.read_csv(f'./app/ema_cross/scanner_lists/{scanner_list}')

        portfolios = []
        
        # Process each ticker
        for row in daily_df.iter_rows(named=True):
            ticker = row['TICKER']
            log(f"Processing {ticker}")
            
            result = process_ma_portfolios(
                ticker=ticker,
                sma_fast=row['SMA_FAST'],
                sma_slow=row['SMA_SLOW'],
                ema_fast=row['EMA_FAST'],
                ema_slow=row['EMA_SLOW']
            )
            
            if result is None:
                continue
                
            sma_portfolio, ema_portfolio, config = result

            try:
                sma_stats = sma_portfolio.stats()
                sma_stats['Ticker'] = ticker
                sma_stats['Use SMA'] = True
                sma_stats['Short Window'] = row['SMA_FAST']
                sma_stats['Long Window'] = row['SMA_SLOW']
                sma_stats['Expectancy Adjusted'] = sma_stats['Expectancy'] * min(1, 0.01 * sma_stats['Win Rate [%]'] / 0.5) * min(1, sma_stats['Total Closed Trades'] / 50)
                sma_stats['Tradability'] = sma_stats['Total Closed Trades'] / sma_stats['End'] * 1000
                sma_converted_stats = convert_stats(sma_stats)
                portfolios.append(sma_converted_stats)

                ema_stats = ema_portfolio.stats()
                ema_stats['Ticker'] = ticker
                ema_stats['Use SMA'] = False
                ema_stats['Short Window'] = row['EMA_FAST']
                ema_stats['Long Window'] = row['EMA_SLOW']
                ema_stats['Expectancy Adjusted'] = ema_stats['Expectancy'] * min(1, 0.01 * ema_stats['Win Rate [%]'] / 0.5) * min(1, ema_stats['Total Closed Trades'] / 50)
                ema_stats['Tradability'] = ema_stats['Total Closed Trades'] / ema_stats['End'] * 1000
                ema_converted_stats = convert_stats(ema_stats)
                portfolios.append(ema_converted_stats)

            except Exception as e:
                log(f"Failed to process stats for {ticker}: {e}", "error")
                continue

        # Export portfolios
        if portfolios:
            config = get_config(config)
            config["TICKER"] = None
            _, success = export_portfolios(portfolios, config, 'portfolios_summary', scanner_list)
            if not success:
                return False
        
        return True
    except Exception as e:
        log(f"Run failed: {e}", "error")
        return False

if __name__ == "__main__":
    try:
        run()
        log_close()
    except Exception as e:
        log(f"Execution failed: {e}", "error")
        raise
